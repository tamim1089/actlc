"""Conference page generator: tools/conference.json -> conference/index.html body.
   Follows tools/DESIGN-RULES.md. Called from tools/build_events.py."""
import html, json, os, re
from urllib.parse import quote

esc = lambda s: html.escape(s or "", quote=True)

I_LINKEDIN = ('<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="currentColor"><path d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 '
              '4.88 0 3.5 1.12 1 2.5 1 4.98 2.12 4.98 3.5zM.22 8.02h4.56V23H.22zM8.34 8.02h4.37v2.05h.06c.61-1.15 2.1-2.37 4.32-2.37 4.62 0 '
              '5.47 3.04 5.47 6.99V23h-4.56v-7.27c0-1.73-.03-3.96-2.41-3.96-2.42 0-2.79 1.89-2.79 3.84V23H8.34z"/></svg>')

CONTACT_LABELS = {"Conference Email": "Conference email", "Abu Dhabi University — CDLI": "ADU Centre (CFDLI) email",
                  "Abu Dhabi University — CDLI Address": "Postal address", "Website": "Website", "Phone": "Phone",
                  "WhatsApp": "WhatsApp", "Venue": "Venue"}

I_DL = '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5M5 19.5h14"/></svg>'

def download(href, label, meta):
    return ('<a class="acx-c-dl" href="%s" target="_blank" rel="noopener" download>%s<span><b>%s</b><small>%s</small></span></a>'
            % (esc(href), I_DL, esc(label), esc(meta)))


NAV = [("tracks", "Tracks"), ("programme", "Programme"), ("speakers", "Speakers"),
       ("call-for-papers", "Proposals"), ("registration", "Fees"), ("contact", "Contact")]


def head(d, hid):
    lead = '<p class="acx-c-lead">%s</p>' % esc(d["lead"]) if d.get("lead") else ""
    return '<div class="acx-c-head"><h2 class="acx-c-h2" id="%s">%s</h2>%s</div>' % (hid, esc(d["title"]), lead)


def rows(items):
    return '<ul class="acx-c-rows">' + "".join(
        "<li><b>%s</b><span>%s</span></li>" % (esc(i["title"]), esc(i["text"])) for i in items) + "</ul>"


def bullets(items, extra=""):
    return '<ul class="acx-c-list"%s>' % extra + "".join("<li>%s</li>" % esc(x) for x in items) + "</ul>"


def person(p):
    line = ", ".join(x for x in (p["role"], p["org"]) if x)
    link = ""
    if p["linkedin"]:
        link = ('<a class="acx-c-lnk" href="%s" target="_blank" rel="noopener" aria-label="%s on LinkedIn">%s</a>'
                % (esc(p["linkedin"]), esc(p["name"]), I_LINKEDIN))
    return ('<li class="acx-c-person"><img class="acx-c-photo" src="%s" alt="" width="400" height="500" loading="lazy" decoding="async"/>'
            '<p class="acx-c-pn"><span>%s</span>%s</p><p class="acx-c-pr">%s</p></li>' % (esc(p["photo"]), esc(p["name"]), link, esc(line)))


def member(m):
    return ('<li class="acx-c-person"><img class="acx-c-photo" src="%s" alt="" width="400" height="500" loading="lazy" decoding="async"/>'
            '<p class="acx-c-pn"><span>%s</span></p><p class="acx-c-pr">%s · %s</p></li>' % (esc(m["photo"]), esc(m["name"]), esc(m["badge"]), esc(m["org"])))


def conference_html(c, email):
    reg = esc(c["hero"]["register"])
    o = []
    o.append('<div class="acx acx-conf">')
    o.append('<nav class="acx-local" aria-label="Conference sections"><div class="acx-local-in">'
             '<a class="acx-local-title" href="#overview">ACTLC 2027</a><div class="acx-local-links">'
             + "".join('<a href="#%s">%s</a>' % (i, t) for i, t in NAV)
             + '</div><a class="acx-btn" href="%s" target="_blank" rel="noopener">Register</a></div></nav>' % reg)

    h = c["hero"]
    facts = " · ".join("%s %s" % (f["n"], f["label"].lower()) for f in c["facts"])
    o.append('<header class="acx-c-hero" id="overview"><div class="acx-c-in acx-c-herogrid"><div>'
             '<p class="acx-c-kicker">ACTLC inaugural conference</p>'
             '<h1 class="acx-c-h1">%s</h1><p class="acx-c-sub">%s</p><p class="acx-c-when">%s</p><p class="acx-c-facts">%s</p>'
             '<div class="acx-c-actions"><a class="acx-btn acx-btn-light" href="%s" target="_blank" rel="noopener">Register</a>'
             '<a class="acx-link" href="#call-for-papers">Submit a proposal &rarr;</a></div></div>'
             '<div class="acx-c-count" data-start="2027-02-02T09:00:00+04:00" role="timer" aria-label="Time until the conference opens" hidden>'
             '<p class="acx-c-count-h">Conference opens in</p><div class="acx-c-count-n">'
             '<div><b data-u="d">0</b><span>days</span></div><div><b data-u="h">0</b><span>hours</span></div><div><b data-u="m">0</b><span>minutes</span></div>'
             '</div></div></div></header>'
             % (esc(h["title"]), esc(h["sub"]), esc(h["when_where"]), esc(facts), reg))

    ab = c["about"]
    o.append('<section class="acx-c-sec" aria-labelledby="acx-h-about"><div class="acx-c-in acx-c-2col">'
             '<div class="acx-c-prose"><h2 class="acx-c-h2" id="acx-h-about">%s</h2>%s</div>'
             '<div><h3 class="acx-c-h3">What to expect</h3>%s%s</div></div></section>'
             % (esc(ab["title"]), "<p>%s</p>" % esc(ab["body"][0]), rows(ab["formats"]), ""))

    th = c["themes"]
    tracks = "".join(
        '<details class="acx-c-track"><summary><span class="acx-c-tn">Track %d</span><span class="acx-c-tt">%s</span>'
        '<span class="acx-c-ts">%s</span></summary><ul>%s</ul></details>'
        % (int(t["n"]), esc(t["title"]), esc(t["short"]), "".join("<li>%s</li>" % esc(x) for x in t["points"]))
        for t in th["items"])
    o.append('<section class="acx-c-sec" id="tracks" aria-labelledby="acx-h-tracks"><div class="acx-c-in">%s'
             '<div class="acx-c-tracks">%s</div></div></section>' % (head(th, "acx-h-tracks"), tracks))

    pr = c["programme"]; tabs, days = [], []
    for i, d in enumerate(pr["days"], 1):
        tabs.append('<button class="acx-tab" type="button" role="tab" id="acx-daytab-%d" aria-controls="acx-day-%d" aria-selected="%s"%s>%s</button>'
                    % (i, i, "true" if i == 1 else "false", "" if i == 1 else ' tabindex="-1"', esc(d["tab"])))
        items = []
        for it in d["items"]:
            note = ' <span class="acx-c-note">%s</span>' % esc(it["note"]) if it["note"] else ""
            detail = '<span class="acx-c-sd">%s</span>' % esc(it["detail"]) if it["detail"] else ""
            items.append('<li%s><time class="acx-c-t">%s</time><div><span class="acx-c-st">%s</span>%s%s</div></li>'
                         % (' class="is-break"' if it["break"] else "", esc(it["time"]), esc(it["title"]), note, detail))
        days.append('<div class="acx-c-day" id="acx-day-%d" aria-labelledby="acx-daytab-%d"><h3 class="acx-c-dayh">%s</h3>'
                    '<p class="acx-c-dayv">%s</p><ol class="acx-c-sched">%s</ol></div>' % (i, i, esc(d["date"]), esc(d["venue"]), "".join(items)))
    o.append('<section class="acx-c-sec" id="programme" aria-labelledby="acx-h-prog"><div class="acx-c-in">%s'
             '<div class="acx-tabs acx-c-tabs" role="tablist" aria-label="Programme day" hidden>%s</div><div class="acx-c-days">%s</div></div></section>'
             % (head(pr, "acx-h-prog"), "".join(tabs), "".join(days)))

    sp, cm = c["speakers"], c["committee"]
    o.append('<section class="acx-c-sec" id="speakers" aria-labelledby="acx-h-spk"><div class="acx-c-in">%s'
             '<ul class="acx-c-people">%s</ul>'
             '<div class="acx-c-head acx-c-subhead"><h2 class="acx-c-h2" id="acx-h-team">%s</h2><p class="acx-c-lead">%s</p></div>'
             '<ul class="acx-c-people" aria-labelledby="acx-h-team">%s</ul></div></section>'
             % (head(sp, "acx-h-spk"), "".join(person(p) for p in sp["people"]), esc(cm["title"]), esc(cm["lead"]),
                "".join(member(m) for m in cm["people"])))

    cf = c["cfp"]; dl = {d["title"]: d for d in c["downloads"]}
    mail = "mailto:%s?subject=%s" % (email, quote(cf["subject"].replace(" #", " ")))
    dates = "".join('<li><time>%s</time><div><b>%s</b></div></li>' % (esc(d["date"]), esc(d["title"])) for d in cf["dates"])
    blocks = "".join('<h3 class="acx-c-h3">%s</h3>%s' % (esc(b["title"]), bullets(b["items"])) for b in cf["blocks"])
    o.append('<section class="acx-c-sec" id="call-for-papers" aria-labelledby="acx-h-cfp"><div class="acx-c-in">%s'
             '<div class="acx-c-cta"><a class="acx-btn" href="%s">Email your proposal</a>'
             '<p class="acx-c-hint">The subject is filled in for you; add your track number.</p></div><div class="acx-c-dlrow">%s</div>'
             '<h3 class="acx-c-h3 acx-c-datesh">Key dates</h3><ol class="acx-c-dates">%s</ol>'
             '<details class="acx-c-more"><summary>Submission requirements</summary><div class="acx-c-reqs">%s</div></details>'
             '</div></section>'
             % (head(cf, "acx-h-cfp"), esc(mail), download(dl["Call for Best Practices"]["href"], "Download the full call for best practices", "PDF · 1.9 MB"), dates,
                "".join('<div><h3 class="acx-c-h3">%s</h3>%s</div>' % (esc(b["title"]), bullets(b["items"])) for b in cf["blocks"])))

    fe = c["fees"]
    lines = {"Regular Delegate": "Delegates from non-member institutions", "Presenter": "Includes your presentation slot",
             "Founding Member Delegate": "After the 5 free places each founding member receives"}
    tiers = "".join('<div class="acx-c-fee%s"><h3>%s</h3><p class="acx-c-price"><span>AED</span>%s</p><p class="acx-c-q">%s</p></div>'
                    % (" is-hi" if t["highlight"] else "", esc(t["name"]), esc(t["price"]), esc(lines.get(t["name"], t["qualifier"])))
                    for t in fe["tiers"])
    o.append('<section class="acx-c-sec" id="registration" aria-labelledby="acx-h-fees"><div class="acx-c-in">'
             '<div class="acx-c-head"><h2 class="acx-c-h2" id="acx-h-fees">%s</h2>'
             '<p class="acx-c-lead">Every ticket includes all sessions and materials. Prices exclude 5%% VAT.</p></div>'
             '<div class="acx-c-fees">%s</div>'
             '<div class="acx-c-feecta"><a class="acx-btn" href="%s" target="_blank" rel="noopener">Register</a></div></div></section>'
             % (esc(fe["title"]), tiers, reg))

    logos = "".join('<li><img src="../%s" alt="%s" width="%d" height="%d" loading="lazy" decoding="async"/>%s</li>'
                    % (esc(l["logo"]), esc(l["name"]), l["w"], l["h"],
                       '<span class="acx-c-lb">%s</span>' % esc(l["badge"]) if l["badge"] else "")
                    for l in c["logos"])
    o.append('<section class="acx-c-sec" id="members" aria-labelledby="acx-h-mem"><div class="acx-c-in">'
             '<h2 class="acx-c-h2" id="acx-h-mem">Founding member institutions</h2><ul class="acx-c-logos">%s</ul></div></section>' % logos)

    so = c["sponsorship"]
    o.append('<section class="acx-c-sec" id="sponsorship" aria-labelledby="acx-h-spo"><div class="acx-c-in">%s'
             '<h3 class="acx-c-h3">%s</h3>%s'
             '<div class="acx-c-actions acx-c-spcta"><a class="acx-btn" href="mailto:%s?subject=%s">Email about sponsorship</a>'
             '</div>%s</div></section>'
             % (head(so, "acx-h-spo"), esc(so["who_title"]), bullets(so["who"], ' style="columns:2;column-gap:2.5em"'),
                email, quote("ACTLC 2027 sponsorship"), download(dl["Sponsorship Package"]["href"], "Download the sponsorship package", "PDF · 4.0 MB")))

    ct = c["contact"]

    def value(i):
        v = "Centre page on adu.ac.ae" if i["label"] == "Website" else re.sub(r"\s*\d+–\d+ \w+ \d{4}$", "", i["value"])
        if not i["href"]:
            return esc(v)
        ext = ' target="_blank" rel="noopener"' if i["href"].startswith("http") else ""
        return '<a href="%s"%s>%s</a>' % (esc(i["href"]), ext, esc(v))
    keep = ("Conference Email", "Phone", "WhatsApp", "Venue")
    items = "".join("<div><dt>%s</dt><dd>%s</dd></div>" % (esc(CONTACT_LABELS.get(i["label"], i["label"]).replace("Conference email", "Email")), value(i))
                    for i in ct["items"] if i["label"] in keep)
    o.append('<section class="acx-c-sec" id="contact" aria-labelledby="acx-h-con"><div class="acx-c-in">%s'
             '<dl class="acx-c-contact">%s</dl><div class="acx-c-contactcta">'
             '<a class="acx-btn" href="mailto:%s?subject=%s">Email the organisers</a></div></div></section>'
             % (head(ct, "acx-h-con"), items, email, quote("ACTLC 2027 conference")))
    o.append("</div>")
    return "\n".join(o)


def build_conference(root, block_span, asset_version, email):
    c = json.load(open(os.path.join(root, "tools", "conference.json"), encoding="utf-8"))
    p = os.path.join(root, "conference", "index.html")
    h = open(p, encoding="utf-8").read()
    m = re.search(r'<div class="acx acx-conf">', h)
    if m:
        s0, e0 = block_span(h, m.start())
    else:  # first run: old <style>, progress bar, floating CTA, .conf-page markup and its scripts
        cp = h.find('<div class="conf-page')
        assert cp > 0, "conf-page not found"
        s0 = h.rfind("<style", 0, cp)
        assert ".conf-page" in h[s0:h.find("</style>", s0)], "conference style block not found"
        mk = h.find("<!-- /.conf-page -->", cp)
        js = h.find("<script>", mk)
        assert mk > 0 and "handleConferenceForm" in h[js:h.find("</script>", js)], "conference script not found"
        e0 = h.find("</script>", js) + len("</script>")
    h = h[:s0] + conference_html(c, email) + h[e0:]
    h = re.sub(r'<(?:link|script)\b[^>]*\bid="acx-(?:conf|conf-js|motion)"[^>]*>(?:[^<]*</script>)?\n?', "", h)
    tags = ['<link rel="stylesheet" id="acx-conf" href="../actlc-assets/conference.css?v=%s"/>' % asset_version("conference.css"),
            '<script id="acx-conf-js" src="../actlc-assets/conference.js?v=%s" defer></script>' % asset_version("conference.js")]
    h = h.replace("</head>", "\n".join(tags) + "\n</head>", 1)
    open(p, "w", encoding="utf-8").write(h)
    return p
