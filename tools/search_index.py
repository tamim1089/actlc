"""Site search index: tools/*.json + resources/files/*.pdf -> actlc-assets/search-index.json.
One record per thing a visitor looks for (a webinar, a speaker, a session, a key date, a document,
one page of a PDF). Fields: k kind, t title, s subtitle, b body text, u url from the site root,
g group (results of one group collapse to the best one), e end time (webinars; the page decides
upcoming or past), p PDF page number. The browser builds its inverted index from this on first use."""
import json, os, re, subprocess, unicodedata

slug = lambda s: re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()).strip("-")
clean = lambda s: re.sub(r"\s+", " ", s or "").strip()


def pdf_pages(path):
    """Text of each PDF page. Line-end hyphens are joined only when the joined word occurs elsewhere
       in the document ('transfor-/mative' -> 'transformative', 'knowing-/doing' stays)."""
    raw = subprocess.run(["pdftotext", "-enc", "UTF-8", path, "-"], capture_output=True, text=True, check=True).stdout
    raw = unicodedata.normalize("NFKC", raw)
    vocab = set(re.findall(r"\w+", raw.lower()))
    join = lambda m: m.group(1) + m.group(2) if (m.group(1) + m.group(2)).lower() in vocab else m.group(1) + "-" + m.group(2)
    pages = []
    for pg in raw.split("\f"):
        pg = re.sub(r"(\w+)-\n\s*(\w+)", join, pg)
        pages.append(clean(pg))
    while pages and not pages[-1]: pages.pop()
    return pages


def cut_references(pages):
    """Drop the reference list of a journal article: author names in it are noise for site search."""
    for i, pg in enumerate(pages):
        m = re.search(r"\b(References|REFERENCES)\b(?!.*\b(References|REFERENCES)\b)", pg)
        if m and i >= len(pages) // 2:
            return pages[:i] + [pg[:m.start()].strip()]
    return pages


def webinars(events):
    out = []
    for e in events:
        url = f"events-main/{e.detail}/index.html" if e.detail else f"events/index.html#ev-{e.id}"
        out.append({"k": "Webinar", "t": e.title, "s": f"{e.speaker} · {e.org} — {e.s.day} {e.s:%B %Y}",
                    "b": clean(" ".join(e.overview)), "u": url, "e": e.e.isoformat(timespec="minutes")})
    return out


def conference(root):
    c = json.load(open(os.path.join(root, "tools", "conference.json"), encoding="utf-8"))
    C = "conference/index.html"
    h, ab = c["hero"], c["about"]
    out = [{"k": "Conference", "t": "ACTLC Conference 2027", "s": clean(h["when_where"]),
            "b": clean(" ".join([h.get("title", ""), h.get("sub", "")] + ab["body"]) + " " + " · ".join(f"{x['title']}: {x['text']}" for x in ab["formats"] + ab["goals"])),
            "u": C + "#overview"}]
    for t in c["themes"]["items"]:
        n = int(t["n"])
        out.append({"k": "Conference track", "t": f"Track {n}: {t['title']}", "s": t["short"], "b": clean(" · ".join(t["points"])), "u": f"{C}#track-{n}"})
    for i, d in enumerate(c["programme"]["days"], 1):
        for it in d["items"]:
            if it["break"]: continue
            out.append({"k": "Conference session", "t": it["title"], "s": f"{d['date'].replace('—', '·')} · {it['time']}",
                        "b": clean(" · ".join(x for x in (it.get("detail", ""), it.get("note", ""), d["venue"]) if x)), "u": f"{C}#acx-day-{i}"})
            for w in it.get("workshops", []):
                out.append({"k": "Conference workshop", "t": w["title"], "s": f"{w['by']} · {d['date'].replace('—', '·')} · {it['time']}",
                            "b": clean(it["title"]), "u": f"{C}#acx-day-{i}"})
    for key, kind in (("speakers", "Speaker"), ("committee", "Organising committee")):
        for p in c[key]["people"]:
            out.append({"k": kind, "t": p["name"], "s": ", ".join(x for x in (p.get("role"), p.get("org")) if x),
                        "b": clean(p.get("country", "")), "u": f"{C}#p-{slug(p['name'])}"})
    cf = c["cfp"]
    out.append({"k": "Call for best practices", "t": cf["title"], "s": "Submit a proposal",
                "b": clean(" · ".join([cf.get("lead", ""), cf.get("submit_text", "")] + [f"{p['name']}: {p['text']}" for p in cf["parts"]]
                                    + [" ".join(it) if isinstance(it, list) else it for b in cf["blocks"] for it in b["items"]]
                                    + [" ".join(" ".join(x).strip() for x in s["items"]) + " " + s.get("note", "") for s in cf["specs"]])),
                "u": C + "#call-for-papers"})
    for d in cf["dates"]:
        out.append({"k": "Key date", "t": d["title"], "s": d["date"], "b": clean(d.get("text", "")), "u": C + "#call-for-papers"})
    fe = c["fees"]
    for t in fe["tiers"]:
        out.append({"k": "Registration fee", "t": f"{t['name'].title()}: {c['fees']['currency']} {t['price']}", "s": t.get("qualifier", ""),
                    "b": clean(f"{t.get('includes', '')} {t.get('vat', '')} {fe.get('note', '')} register registration fee price cost"), "u": C + "#registration"})
    sp = c["sponsorship"]
    out.append({"k": "Conference", "t": sp["title"], "s": "Sponsorship opportunities",
                "b": clean(" · ".join([sp.get("lead", ""), sp.get("why_text", "")] + sp["why"] + sp["who"])), "u": C + "#sponsorship"})
    out.append({"k": "Conference", "t": "Member universities", "s": f"{len(c['logos'])} founding members",
                "b": clean(" · ".join(f"{m['name']}, {m['country']}" for m in c["logos"])), "u": C + "#members"})
    out.append({"k": "Conference", "t": c["contact"]["title"], "s": "Contact the organisers",
                "b": clean(" · ".join(f"{i['label']}: {i['value']}" for i in c["contact"]["items"])), "u": C + "#contact"})
    for d in c["downloads"]:
        out.append({"k": "Download", "t": d["title"], "s": "PDF", "b": clean(d.get("text", "")), "u": "conference/" + d["href"]})
    return out


def resources(root):
    data = json.load(open(os.path.join(root, "tools", "resources.json"), encoding="utf-8"))
    out = []
    for r in data["items"]:
        g, pdf = slug(r["file"][:-4]), f"resources/files/{r['file']}"
        out.append({"k": r["kind"], "t": r["title"], "s": f"{r['authors']} · {r['institution']}",
                    "b": clean(" ".join([r["summary"], r.get("source") or ""])), "u": f"resources/index.html#res-{g}", "g": g})
        pages = pdf_pages(os.path.join(root, pdf))
        if r["kind"] == "Journal article": pages = cut_references(pages)
        for n, text in enumerate(pages, 1):
            if text:
                out.append({"k": r["kind"], "t": r["title"], "s": f"Page {n} of {r['pages']} · {r['institution']}",
                            "b": text, "u": f"{pdf}#page={n}", "g": g, "p": n})
    return out


def pages():
    return [
        {"k": "Page", "t": "Webinars", "s": "Upcoming and past ACTLC webinars", "b": "events calendar sessions online schedule", "u": "events/index.html"},
        {"k": "Page", "t": "Resources", "s": "Documents shared by member universities", "b": "best practices research publications PDF library", "u": "resources/index.html"},
        {"k": "Page", "t": "Create an account", "s": "Join the ACTLC community", "b": "registration register sign up join account member email designation country", "u": "registration/index.html"},
        {"k": "Page", "t": "Arab Teaching and Learning Consortium", "s": "Home",
         "b": "ACTLC about consortium community educators scholars professional development networking advocacy Arab region workshops webinars training", "u": "index.html"},
    ]


QUICK = [("Upcoming webinars", "events/index.html"), ("Conference programme", "conference/index.html#programme"),
         ("Speakers", "conference/index.html#speakers"), ("Call for best practices", "conference/index.html#call-for-papers"),
         ("Resources", "resources/index.html")]


def build_index(root, events):
    docs = webinars(events) + conference(root) + resources(root) + pages()
    out = {"v": 1, "quick": [{"t": t, "u": u} for t, u in QUICK], "docs": docs}
    p = os.path.join(root, "actlc-assets", "search-index.json")
    open(p, "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    return p, len(docs)
