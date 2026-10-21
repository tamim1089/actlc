"""Conference page generator: tools/conference.json -> conference/index.html body.
   Follows tools/DESIGN-RULES.md. Called from tools/build_events.py."""
import html, json, os, re, unicodedata
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


def card(photo, name, line, link="", big=False):
    pid = re.sub(r"[^a-z0-9]+", "-", unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()).strip("-")
    return ('<li class="acx-c-person%s" id="p-%s"><img class="acx-c-photo" src="%s" alt="" width="400" height="500" loading="lazy" decoding="async"/>'
            '<div class="acx-c-cap"><p class="acx-c-pn">%s</p><p class="acx-c-pr">%s</p></div>%s</li>'
            % (" is-lg" if big else "", pid, esc(photo), esc(name), esc(line), link))


def person(p):
    link = ""
    if p["linkedin"]:
        link = ('<a class="acx-c-lnk" href="%s" target="_blank" rel="noopener" aria-label="%s on LinkedIn">%s</a>'
                % (esc(p["linkedin"]), esc(p["name"]), I_LINKEDIN))
    return card(p["photo"], p["name"], ", ".join(x for x in (p["role"], p["org"]) if x), link, p.get("featured"))


def member(m):
    return card(m["photo"], m["name"], "%s · %s" % (m["badge"], m["org"]))


I_CHECK = '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"><path d="m5 12.5 4.5 4.5L19 7.5"/></svg>'
I_STAR = '<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="currentColor"><path d="m12 2.8 2.8 5.9 6.4.8-4.7 4.4 1.2 6.4L12 17.2l-5.7 3.1 1.2-6.4-4.7-4.4 6.4-.8z"/></svg>'

# What each ticket includes, as short checklist lines (from each tier's "includes" text)
PLAN = {"Regular Delegate": ("Non-founding member institutions", ["All conference sessions", "Conference materials", "Networking events"]),
        "Presenter": ("For conference presenters", ["All conference sessions", "Your presentation slot", "Conference materials"]),
        "Founding Member Delegate": ("After your 5 free places", ["All conference sessions", "Conference materials", "Networking events"])}


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
        '<li class="acx-c-track" id="track-%d"><span class="acx-c-tn" aria-hidden="true">%d</span><div><h3 class="acx-c-tt"><span class="acx-vh">Track %d: </span>%s</h3>'
        '<p class="acx-c-ts">%s</p><ul class="acx-c-topics">%s</ul></div></li>'
        % (int(t["n"]), int(t["n"]), int(t["n"]), esc(t["title"]), esc(t["short"]), "".join("<li>%s</li>" % esc(x) for x in t["points"]))
        for t in th["items"])
    o.append('<section class="acx-c-sec" id="tracks" aria-labelledby="acx-h-tracks"><div class="acx-c-in">%s'
             '<ol class="acx-c-tracks">%s</ol></div></section>' % (head(th, "acx-h-tracks"), tracks))

    pr = c["programme"]; days = []
    mins = lambda hm: int(hm[:2]) * 60 + int(hm[3:5])
    for i, d in enumerate(pr["days"], 1):
        items, prev = [], None
        for it in d["items"]:
            a, b = (mins(x) for x in it["time"].split("–"))
            kind = "is-break" if it["break"] else "is-par" if it["title"].startswith("Parallel") else "is-ses"
            note = '<span class="acx-c-note">%s</span>' % esc(it["note"].strip("()")) if it["note"] else ""
            detail = '<span class="acx-c-sd">%s</span>' % esc(it["detail"]) if it["detail"] else ""
            items.append('<li class="acx-c-blk %s" style="--m:%d;--g:%d"><time class="acx-c-t">%s</time><span class="acx-c-st">%s</span>%s%s</li>'
                         % (kind, b - a, (a - prev) if prev is not None else 0, esc(it["time"]), esc(it["title"]), note, detail))
            prev = b
        days.append('<div class="acx-c-day" id="acx-day-%d"><h3 class="acx-c-dayh">%s</h3><p class="acx-c-dayv">%s</p>'
                    '<ol class="acx-c-cal">%s</ol></div>' % (i, esc(d["date"]), esc(d["venue"]), "".join(items)))
    o.append('<section class="acx-c-sec" id="programme" aria-labelledby="acx-h-prog"><div class="acx-c-in">%s'
             '<div class="acx-c-days">%s</div></div></section>' % (head(pr, "acx-h-prog"), "".join(days)))

    sp, cm = c["speakers"], c["committee"]
    o.append('<section class="acx-c-sec" id="speakers" aria-labelledby="acx-h-spk"><div class="acx-c-in">%s'
             '<ul class="acx-c-people">%s</ul>'
             '<div class="acx-c-head acx-c-subhead"><h2 class="acx-c-h2" id="acx-h-team">%s</h2><p class="acx-c-lead">%s</p></div>'
             '<ul class="acx-c-people acx-c-team" aria-labelledby="acx-h-team">%s</ul></div></section>'
             % (head(sp, "acx-h-spk"), "".join(person(p) for p in sp["people"]), esc(cm["title"]), esc(cm["lead"]),
                "".join(member(m) for m in cm["people"])))

    cf = c["cfp"]; dl = {d["title"]: d for d in c["downloads"]}
    mail = "mailto:%s?subject=%s" % (email, quote(cf["subject"].replace(" #", " ")))
    import datetime as _dt
    day = lambda s: _dt.datetime.strptime(s, "%d %B %Y").date()
    ds = [day(x["date"]) for x in cf["dates"]]; opens = _dt.date(2027, 2, 2)
    m0 = ds[0].year * 12 + ds[0].month - 1 - 2           # axis starts two months before the first deadline
    t0, t1 = _dt.date(m0 // 12, m0 % 12 + 1, 1), opens
    pos = lambda d: 100 * (d - t0).days / (t1 - t0).days
    ticks = "".join('<li style="left:%.2f%%"><span>%s</span></li>' % (pos(d), "%d %s" % (d.day, d.strftime("%b"))) for d in ds + [opens])
    months = "".join('<span style="left:%.2f%%">%s</span>' % (pos(m), m.strftime("%b")) for m in
                     [_dt.date(t0.year + (t0.month - 1 + k) // 12, (t0.month - 1 + k) % 12 + 1, 1) for k in range(1, 12)] if m < t1)
    dates = "".join('<li data-date="%s"><time datetime="%s">%s</time><b>%s</b><span class="acx-c-rel" hidden></span></li>'
                    % (d.isoformat(), d.isoformat(), esc(x["date"]), esc(x["title"])) for d, x in zip(ds, cf["dates"]))
    parts = "".join('<li><b>%s</b><span>%s</span></li>' % (esc(x["name"]), esc(x["text"])) for x in cf["parts"])
    def spec(g):
        return ('<div class="acx-c-specg"><h4>%s</h4><dl>%s</dl><p>%s</p></div>'
                % (esc(g["title"]), "".join('<div><dt>%s</dt><dd><b>%s</b>%s</dd></div>' % (esc(k), esc(v), (" " + esc(u)) if u else "") for k, v, u in g["items"]), esc(g["note"])))
    o.append('<section class="acx-c-sec" id="call-for-papers" aria-labelledby="acx-h-cfp"><div class="acx-c-in">%s'
             '<div class="acx-c-cta"><a class="acx-btn" href="%s">Email your proposal</a>'
             '<p class="acx-c-hint">The subject is filled in for you; add your track number.</p></div><div class="acx-c-dlrow">%s</div>'
             '<h3 class="acx-c-h3 acx-c-datesh">Key dates</h3>'
             '<div class="acx-c-tl" data-t0="%s" data-t1="%s" aria-hidden="true"><div class="acx-c-tl-m">%s</div><ol class="acx-c-tl-ticks">%s</ol>'
             '<span class="acx-c-tl-now" hidden><span>Today</span></span></div>'
             '<ol class="acx-c-dates">%s</ol>'
             '<div class="acx-c-req"><div><h3 class="acx-c-h3">Your proposal, in this order <span class="acx-c-reqm">500–1,000 words</span></h3><ol class="acx-c-parts">%s</ol></div>'
             '<div class="acx-c-specs">%s</div></div>'
             '</div></section>'
             % (head(cf, "acx-h-cfp"), esc(mail), download(dl["Call for Best Practices"]["href"], "Download the full call for best practices", dl["Call for Best Practices"]["meta"]),
                t0.isoformat(), t1.isoformat(), months, ticks, dates, parts, "".join(spec(g) for g in cf["specs"])))

    o.append(fees_section(c))
    o.append(members_section(c))

    so = c["sponsorship"]
    o.append('<section class="acx-c-sec" id="sponsorship" aria-labelledby="acx-h-spo"><div class="acx-c-in">%s'
             '<h3 class="acx-c-h3">%s</h3>%s'
             '<div class="acx-c-actions acx-c-spcta"><a class="acx-btn" href="mailto:%s?subject=%s">Email about sponsorship</a>'
             '</div>%s</div></section>'
             % (head(so, "acx-h-spo"), esc(so["who_title"]), bullets(so["who"], ' style="columns:2;column-gap:2.5em"'),
                email, quote("ACTLC 2027 sponsorship"), download(dl["Sponsorship Package"]["href"], "Download the sponsorship package", dl["Sponsorship Package"]["meta"])))

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
    for d in c["downloads"]:   # file size shown on the download links, read from the PDFs we host
        d["meta"] = "PDF · %.1f MB" % (os.path.getsize(os.path.join(root, "conference", d["href"])) / 1e6)
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


def fees_section(c):
    """Three price cards on the teal band; the presenter rate raised with its saving."""
    fe, reg = c["fees"], esc(c["hero"]["register"])
    base = max(int(t["price"]) for t in fe["tiers"])
    def plan(t):
        sub, inc = PLAN[t["name"]]
        hi = t["highlight"]
        badge = '<p class="acx-c-plan-badge">%sSave AED %d</p>' % (I_STAR, base - int(t["price"])) if hi else ""
        return ('<div class="acx-c-plan%s">%s<h3>%s</h3><p class="acx-c-plan-price"><b>AED %s</b><span>/ person</span></p>'
                '<p class="acx-c-plan-sub">%s</p><ul class="acx-c-plan-inc">%s</ul>'
                '<a class="acx-btn %s" href="%s" target="_blank" rel="noopener">Register</a></div>'
                % (" is-hi" if hi else "", badge, esc(t["name"][0] + t["name"][1:].lower()), esc(t["price"]), esc(sub),
                   "".join("<li>%s%s</li>" % (I_CHECK, esc(x)) for x in inc), "acx-btn-light" if hi else "acx-btn-ghost", reg))
    return ('<section class="acx-c-sec acx-c-band" id="registration" aria-labelledby="acx-h-fees"><div class="acx-c-in">'
            '<div class="acx-c-head"><h2 class="acx-c-h2" id="acx-h-fees">%s</h2>'
            '<p class="acx-c-lead">Prices are per person and exclude 5%% VAT.</p></div>'
            '<div class="acx-c-plans">%s</div></div></section>'
            % (esc(fe["title"]), "".join(plan(t) for t in fe["tiers"])))


def members_section(c):
    """Founding members as a slow strip of large logos."""
    def logos(copy):
        # Same visual weight for wide and tall logos: scale height by sqrt(reference aspect / aspect)
        return "".join('<li><img src="../%s" alt="%s" width="%d" height="%d" style="--k:%.2f" loading="lazy" decoding="async"/></li>'
                       % (esc(l["logo"]), "" if copy else esc(l["name"]), l["w"], l["h"],
                          min(1.15, max(.5, (1.5 / (l["w"] / l["h"])) ** .5))) for l in c["logos"])
    return ('<section class="acx-c-sec" id="members" aria-labelledby="acx-h-mem"><div class="acx-c-in">'
            '<h2 class="acx-c-h2" id="acx-h-mem">Founding member institutions</h2></div>'
            '<div class="acx-c-marquee"><div class="acx-c-mtrack"><ul class="acx-c-logos">%s</ul>'
            '<ul class="acx-c-logos" aria-hidden="true">%s</ul></div></div></section>' % (logos(False), logos(True)))


# The page keeps its original (September) design. Today's information is applied on top of it:
# venue is ADU's Abu Dhabi Campus only, the contact form opens the visitor's email app instead of
# pretending to send, and the fees and member-logo sections are the new ones.
LEGACY_FIXES = [
    ("Abu Dhabi University- Abu Dhabi Campus, Al Ain", "Abu Dhabi University, Abu Dhabi Campus"),
    ("Abu Dhabi University, Al Ain Campus", "Abu Dhabi University, Abu Dhabi Campus"),
    ("<span>2 Feb 2027 · Abu Dhabi University- Abu Dhabi Campus</span>", "<span>2 Feb 2027 · Abu Dhabi University, Abu Dhabi Campus</span>"),
    ("hosted by Abu Dhabi University- Abu Dhabi Campus and Abu Dhabi University at their Al Ain campuses.", "hosted by Abu Dhabi University at its Abu Dhabi Campus."),
    ("2–3 February 2027 · Al Ain, UAE", "2–3 February 2027 · Abu Dhabi, UAE"),
    ("Two days. Two campuses. One goal:", "Two days. One campus. One goal:"),
    ("Two Days, Two Campuses", "Two Days in Abu Dhabi"),
    ('''    btn.textContent = 'Sending…';
    btn.disabled = true;
    setTimeout(function(){
      btn.style.display = 'none';
      document.getElementById('cf-ok').style.display = 'block';
    }, 700);''',
     '''    // No server behind this form: open the visitor's email app with the message filled in.
    var f = w.querySelectorAll('input,textarea,select'), v = function(n){ return f[n].value.trim(); };
    location.href = 'mailto:info@ac-tlc.org?subject=' + encodeURIComponent('ACTLC 2027 – ' + v(4)) +
      '&body=' + encodeURIComponent(v(5) + '\\n\\n' + v(0) + ' ' + v(1) + '\\n' + v(3) + '\\n' + v(2));
    document.getElementById('cf-ok').style.display = 'block';'''),
    ("Message sent — we'll be in touch shortly.", "Your email app has opened with this message. Press Send there to reach us at info@ac-tlc.org."),
    ('onclick="handleConferenceForm(this)" type="button">Send Message →</button>', 'onclick="handleConferenceForm(this)" type="button">Email this message →</button>'),
]


def build_legacy_conference(root, asset_version):
    c = json.load(open(os.path.join(root, "tools", "conference.json"), encoding="utf-8"))
    p = os.path.join(root, "conference", "index.html")
    h = open(p, encoding="utf-8").read()
    for old, new in LEGACY_FIXES:
        h = h.replace(old, new)
    def between(h, a, b, new):
        i = h.index(a) + len(a); j = h.index(b, i)
        return h[:i] + "\n" + new + "\n" + h[j:]
    # The new sections sit in the old page's own content column (.wrap)
    fees = fees_section(c).replace('<div class="acx-c-in">', '<div class="wrap"><div class="acx-c-in">', 1)
    fees = fees[: fees.rindex("</div></section>")] + "</div></div></section>"
    mem = members_section(c).replace('<div class="acx-c-in">', '<div class="wrap"><div class="acx-c-in">', 1).replace("</h2></div>", "</h2></div></div>", 1)
    h = between(h, "<!-- ══ REGISTRATION ══ -->", "<!-- ══ DOWNLOADS ══ -->", '<div class="acx acx-conf">%s</div>' % fees)
    h = between(h, "<!-- ══ FOUNDING MEMBERS MARQUEE ══ -->", "<!-- ══ SPONSORSHIP ══ -->", '<div class="acx acx-conf">%s</div>' % mem)
    h = re.sub(r'<(?:link|script)\b[^>]*\bid="acx-(?:conf|conf-js)"[^>]*>(?:[^<]*</script>)?\n?', "", h)
    h = h.replace("</head>", '<link rel="stylesheet" id="acx-conf" href="../actlc-assets/conference.css?v=%s"/>\n</head>' % asset_version("conference.css"), 1)
    open(p, "w", encoding="utf-8").write(h)
    return p
