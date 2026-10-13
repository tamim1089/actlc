#!/usr/bin/env python3
"""One-time extraction of the conference page content into tools/conference.json.
   The generated page is built from that JSON (tools/build_events.py); edit the JSON, not the HTML.
   Source: git show <rev>:conference/index.html (default: the last commit before the rebuild)."""
import json, os, re, subprocess, sys
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REV = sys.argv[1] if len(sys.argv) > 1 else "c25be0c"
html = subprocess.run(["git", "show", f"{REV}:conference/index.html"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
S = BeautifulSoup(html, "lxml")
cp = S.select_one(".conf-page")
T = lambda el: re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip() if el else ""
own = lambda el: re.sub(r"\s+", " ", "".join(x for x in el.find_all(string=True, recursive=False))).strip() if el else ""
sec = lambda i: cp.find(id=i)

def head(s):
    hd = s.select_one(".sec-hd")
    return {"eyebrow": T(hd.select_one(".eyebrow")), "title": T(hd.select_one(".h2")), "lead": T(hd.select_one(".lead"))} if hd else {}

d = {}
# Hero
h = sec("hero")
btns = [{"label": T(a).replace("→", "").strip(), "href": a.get("href")} for a in h.select(".hero__btns a")]
d["hero"] = {"title": T(h.select_one(".h1")), "sub": T(h.select_one(".hero__sub")), "when_where": T(h.select_one(".hero__tag")),
             "register": next(b["href"] for b in btns if "Register" in b["label"]),
             "proposal": next(b["href"] for b in btns if "Proposal" in b["label"])}
d["facts"] = [{"n": T(s.select_one(".stat__n")), "label": T(s.select_one(".stat__l"))} for s in cp.select(".stats .stat")
              if T(s.select_one(".stat__l")) in ("Conference Days", "Parallel Tracks")]   # decision: facts only

# About
a = sec("about")
d["about"] = {"eyebrow": T(a.select_one(".eyebrow")), "title": T(a.select_one(".h2")),
              "body": [T(p) for p in a.select(".about-body p")] or [T(a.select_one(".about-body"))],
              "formats": [{"title": T(f.select_one(".feat__t")), "text": T(f.select_one(".feat__d"))} for f in a.select(".feat")],
              "goals": [{"title": T(p.select_one(".pil__t")), "text": T(p.select_one(".pil__d"))} for p in a.select(".pillars > div")]}
# Themes
t = sec("themes")
d["themes"] = {**head(t), "items": [{"n": T(x.select_one(".theme__n")), "title": T(x.select_one(".theme__t")), "short": T(x.select_one(".theme__s")),
                                     "text": T(x.select_one(".theme__bd p")) or own(x.select_one(".theme__bd")),
                                     "points": [T(li) for li in x.select(".theme__list li")]} for x in t.select(".theme")]}
# Programme
pr = sec("programme")
days = []
for tab, panel in zip(pr.select(".prog-tab"), pr.select(".prog-panel")):
    items = []
    for li in panel.select(".tli"):
        s = li.select_one(".tl-s"); sub = s.select_one(".tl-sub") if s else None; note = None
        for sp in s.find_all("span", recursive=False) if s else []:
            if "tl-sub" not in (sp.get("class") or []): note = T(sp)
        items.append({"time": T(li.select_one(".tl-t")), "title": own(s) or T(s), "detail": T(sub) if sub else "",
                      "note": note or "", "break": "tli--br" in (li.get("class") or [])})
    days.append({"tab": T(tab), "date": T(panel.select_one(".prog-hd h3")), "venue": T(panel.select_one(".prog-hd p")), "items": items})
d["programme"] = {**head(pr), "days": days}

def person(card, pre):
    img = card.select_one("img"); li = card.select_one(f".{pre}__li") or card.select_one("a[href*='linkedin']")
    return {"name": T(card.select_one(f".{pre}__n")), "role": T(card.select_one(f".{pre}__r")), "org": T(card.select_one(f".{pre}__i")),
            "country": T(card.select_one(f".{pre}__c")), "photo": img.get("src") if img else "",
            "linkedin": li.get("href") if li and "linkedin" in (li.get("href") or "") else ""}
sp = sec("speakers")
d["speakers"] = {**head(sp), "people": [person(c, "spk") for c in sp.select(".spk-g > .spk")]}
oc = sec("organizing-committee")
d["committee"] = {**head(oc), "people": [{**person(c, "org-card"), "badge": T(c.select_one(".org-card__role-badge"))} for c in oc.select(".org-card")]}

# Call for best practices
c = sec("call-for-papers")
cta = c.select_one(".cfp-cta")
d["cfp"] = {**head(c), "dates_title": T(c.select_one(".cfp-t")),
            "dates": [{"date": T(s.select_one(".cfp-d")), "title": T(s.select_one(".cfp-step > div:not(.cfp-d):not(.cfp-sub)") or s.select_one("strong") or s.find("div", class_=lambda x: x is None)),
                       "text": T(s.select_one(".cfp-sub"))} for s in c.select(".cfp-step")],
            "blocks": [{"title": T(b.select_one(".cfp-block__t")), "items": [T(li) for li in b.select("li")]} for b in c.select(".cfp-block")],
            "submit_title": T(cta.select_one("h3, h4, .cfp-cta__t, strong")) if cta else "",
            "submit_text": T(cta.select_one("p")) if cta else ""}
# Fees
r = sec("registration")
d["fees"] = {**head(r), "tiers": [{"name": own(x.select_one(".rc__cat")) or T(x.select_one(".rc__cat")), "qualifier": T(x.select_one(".rc__cat small")).strip("()"),
                                   "price": re.sub(r"\D", "", T(x.select_one(".rc__price"))), "vat": T(x.select_one(".rc__vat")),
                                   "includes": T(x.select_one(".rc__includes")), "badge": T(x.select_one(".rc__badge")).replace("⚡", "").strip(),
                                   "highlight": "rc--hi" in (x.get("class") or [])} for x in r.select(".rc")],
             "note": T(r.select_one(".reg-note")), "cta": T(r.select_one(".reg-cta p"))}
# Downloads
d["downloads"] = [{"title": T(x.select_one(".dl-card__t")), "text": T(x.select_one(".dl-card__d")).replace(" — PDF", ""), "href": x.get("href")} for x in cp.select(".dl-card")]
# Logos (first copy only; the marquee duplicates the set to loop)
seen, logos = set(), []
for i in cp.select(".mq__track .mq-i"):
    img = i.select_one("img"); key = img.get("src") if img else ""
    if key in seen: continue
    seen.add(key); logos.append({"src": key, "alt": img.get("alt", ""), "badge": T(i).strip()})
d["logos"] = logos
# Sponsorship
s = sec("sponsorship")
d["sponsorship"] = {**head(s), "why_title": T(s.select_one(".sp-why h3, .sp-why h4")), "why_text": T(s.select_one(".sp-why p")),
                    "why": [T(x) for x in s.select(".sp-why-i")], "who_title": T(s.select_one(".sp-who h3, .sp-who h4, .sp-who strong")),
                    "who": [T(x) for x in s.select(".sp-who-i")], "cta": T(s.select_one(".sp-cta p"))}
# Contact (facts only; decision: no form)
k = sec("contact")
d["contact"] = {**head(k), "items": [{"label": T(i.select_one(".ci__lbl")), "value": T(i.select_one(".ci__val")),
                                       "href": (i.select_one(".ci__val a") or {}).get("href", "") if i.select_one(".ci__val a") else ""} for i in k.select(".ci")]}

out = os.path.join(ROOT, "tools", "conference.json")
json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps({k: (len(v) if isinstance(v, list) else {kk: (len(vv) if isinstance(vv, list) else (vv[:40] if isinstance(vv, str) else vv)) for kk, vv in v.items()}) for k, v in d.items()}, ensure_ascii=False, indent=1))
