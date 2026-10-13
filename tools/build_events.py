#!/usr/bin/env python3
"""Build the ACTLC events list and session pages from tools/events.json.

Writes: events/index.html (list + JSON-LD), events-main/<slug>/index.html and
event.ics for events that have a session page. Safe to run repeatedly.
Times are stored local to each event's IANA timezone; member-country clocks are
computed here (system tz database), not in the browser, so old browser tz data
cannot show a wrong time.        Usage: python3 tools/build_events.py
"""
import datetime as dt, html, json, os, re, sys
from urllib.parse import quote
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "tools", "events.json"), encoding="utf-8"))
SITE, EMAIL = DATA["site"], DATA["register_email"]
UTC = dt.timezone.utc
NOW = dt.datetime.now(UTC)

def svg(d, sw="1.8"):
    return ('<svg aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">{d}</svg>')
I_PERSON = svg('<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>')
I_CLOCK = svg('<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>', "2")
I_CALPLUS = svg('<rect x="3" y="4.5" width="18" height="17" rx="2.5"/><path d="M3 9h18M8 2.5v4M16 2.5v4M12 13v5M9.5 15.5h5"/>')
I_CHEV = svg('<path d="m15 18-6-6 6-6"/>', "2.2")

esc = lambda s: html.escape(s, quote=True)

# ---------------------------------------------------------------- model
class Ev:
    def __init__(self, d):
        self.__dict__.update(d)
        z = ZoneInfo(self.tz)
        self.s = dt.datetime.fromisoformat(self.start).replace(tzinfo=z)
        self.e = dt.datetime.fromisoformat(self.end).replace(tzinfo=z)
        self.past = self.e <= NOW
        self.url = f"{SITE}/events-main/{self.detail}/" if self.detail else f"{SITE}/events/#ev-{self.id}"
        self.mailto = f"mailto:{EMAIL}?subject=" + quote("Registration: " + self.title)
    iso = staticmethod(lambda t: t.isoformat(timespec="seconds"))
    def gmt(self):
        h = self.s.utcoffset().total_seconds() / 3600
        return "GMT" + ("+" if h >= 0 else "−") + (f"{abs(h):g}")
    def duration(self):
        m = int((self.e - self.s).total_seconds() // 60); h, mm = divmod(m, 60)
        if mm == 0: return f"{h} hour" + ("s" if h != 1 else "")
        return (f"{h} h " if h else "") + f"{mm} min"
    def hm(self, t): return t.strftime("%H:%M")
    def long_date(self): return f"{self.s:%A}, {self.s.day} {self.s:%B %Y}"
    def initials(self):
        w = [x for x in re.split(r"\s+", self.speaker) if not re.match(r"^(Dr|Prof|Mr|Ms|Mrs)\.?$", x)]
        return (w[0][0] + w[-1][0]).upper() if w else "?"
    def lead_and_body(self):
        first, rest = self.overview[0], self.overview[1:]
        m = re.match(r"^(.+?[.?!])\s+(.*)$", first, re.S)
        lead, tail = (m.group(1), m.group(2)) if m else (first, "")
        return lead, ([tail] if tail else []) + rest

EVENTS = sorted((Ev(e) for e in DATA["events"]), key=lambda e: e.s)

# ---------------------------------------------------------------- html helpers
def block_span(h, start):
    """(start, end) of the balanced <div> beginning at index start."""
    depth = 0
    for m in re.finditer(r"<div\b|</div\s*>", h[start:]):
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0: return start, start + m.end()
    raise ValueError("unbalanced div")

def asset_version(name):
    import hashlib
    return hashlib.sha1(open(os.path.join(ROOT, "actlc-assets", name), "rb").read()).hexdigest()[:10]

INTER_CSS = "wp-content/uploads/elementor/google-fonts/css/inter-local.css"

def ensure_head(h, rel, events, body_class=None):
    """(Re)write our <head> links. Versioned by content hash so browsers never keep a stale copy."""
    h = re.sub(r'<link\b[^>]*\bid="acx-(?:css|site|inter)"[^>]*>\n?', "", h)
    h = re.sub(r'<script\b[^>]*\bid="acx-js"[^>]*></script>\n?', "", h)
    h = re.sub(r'<link\b[^>]*inter-local\.css[^>]*>\n?', "", h)          # old link at a wrong depth
    tags = [f'<link rel="stylesheet" id="acx-inter" href="{rel}{INTER_CSS}"/>',
            f'<link rel="stylesheet" id="acx-site" href="{rel}actlc-assets/site.css?v={asset_version("site.css")}"/>']
    if events:
        tags += [f'<link rel="stylesheet" id="acx-css" href="{rel}actlc-assets/events.css?v={asset_version("events.css")}"/>',
                 f'<script id="acx-js" src="{rel}actlc-assets/events.js?v={asset_version("events.js")}" defer></script>']
    h = h.replace("</head>", "\n".join(tags) + "\n</head>", 1)
    if body_class:
        m = re.search(r'<body class="([^"]*)"', h)
        if m and body_class not in m.group(1).split():
            h = h[:m.start(1)] + m.group(1) + " " + body_class + h[m.end(1):]
    return h

def fix_events_nav(h, rel):
    """Menu 'Events' links must open the events list from any depth (copied pages pointed at themselves)."""
    pat = re.compile(r'(<a\b[^>]*?\bhref=")[^"]*("[^>]*>\s*(?:<i\b[^>]*></i>\s*)?<span>Events</span>)')
    return pat.sub(lambda m: m.group(1) + rel + "events/index.html" + m.group(2), h)

def footer_html(rel):
    col = lambda title, links: (f'<div class="acx-foot-col"><h2 class="acx-foot-h">{title}</h2><ul>' +
                                "".join(f'<li><a href="{rel}{href}">{label}</a></li>' for label, href in links) + "</ul></div>")
    return f"""<div class="acx acx-footer">
<div class="acx-foot-in">
<div class="acx-foot-top">
<a class="acx-foot-brand" href="{rel}index.html"><img src="{rel}wp-content/uploads/2024/03/ACTLC-Logo-03-300x157.png" width="300" height="157" alt="Arab Teaching and Learning Consortium" loading="lazy" decoding="async"/></a>
<nav class="acx-foot-nav" aria-label="Footer">
{col("Explore", [("Home", "index.html"), ("Webinars", "events/index.html"), ("Conference", "conference/index.html"), ("Registration", "registration/index.html")])}
<div class="acx-foot-col"><h2 class="acx-foot-h">Contact</h2><ul>
<li><a href="tel:+97143487445">+971 43 487 445</a></li>
<li><a href="mailto:{EMAIL}">{EMAIL}</a></li>
</ul><address>Centre for Faculty Development and Learning Innovation<br/>Abu Dhabi University, P.O. Box 59911<br/>Khalifa City, Abu Dhabi, UAE</address></div>
</nav>
</div>
<div class="acx-foot-bottom"><p>Copyright © {NOW.year} Arab Consortium</p></div>
</div>
</div>"""

def replace_footer(h, rel):
    m = re.search(r'<div class="(?:footer-widget-area bb-footer|acx acx-footer)"', h)
    if not m: return h, False
    s, e = block_span(h, m.start())
    return h[:s] + footer_html(rel) + h[e:], True

def site_pages():
    pages = ["index.html"] + sorted(p for p in os.listdir(ROOT) if os.path.isfile(os.path.join(ROOT, p, "index.html")))
    pages = [p if p.endswith(".html") else f"{p}/index.html" for p in pages]
    pages += sorted(f"events-main/{d}/index.html" for d in os.listdir(os.path.join(ROOT, "events-main")))
    return [p for p in pages if 'id="masthead"' in open(os.path.join(ROOT, p), encoding="utf-8", errors="ignore").read()]

def cf_decode(hexstr):
    b = bytes.fromhex(hexstr); return "".join(chr(c ^ b[0]) for c in b[1:])

def fix_cloudflare_email(h):
    """Cloudflare's email obfuscation was never mirrored: turn protected addresses back into mailto links."""
    a = re.compile(r'<a\b[^>]*href="[^"]*cdn-cgi/l/email-protection[^"]*"[^>]*>\s*<span class="__cf_email__" data-cfemail="([0-9a-f]+)">[^<]*</span>\s*</a>')
    h = a.sub(lambda m: f'<a href="mailto:{cf_decode(m.group(1))}">{cf_decode(m.group(1))}</a>', h)
    h = re.sub(r'<a\b[^>]*data-cfemail="([0-9a-f]+)"[^>]*>[^<]*</a>',
               lambda m: f'<a href="mailto:{cf_decode(m.group(1))}">{cf_decode(m.group(1))}</a>', h)
    h = re.sub(r'<span class="__cf_email__" data-cfemail="([0-9a-f]+)">[^<]*</span>', lambda m: cf_decode(m.group(1)), h)
    # Buttons whose mailto: Cloudflare rewrote lose the address in the mirror; every decoded address on the site is EMAIL.
    h = re.sub(r'href="[^"]*cdn-cgi/l/email-protection[^"]*"', f'href="mailto:{EMAIL}"', h)
    return h

def drop_dead_font_links(h):
    """The theme's Google Fonts links point outside the site and always fail; Inter is served locally."""
    return re.sub(r'<link\b[^>]*href="(?:\.\./)*fonts\.googleapis\.com/[^"]*"[^>]*>\n?', "", h)

def home_html(limit=3):
    up = [e for e in EVENTS if not e.past]
    return (f'<div class="acx acx-home-root" data-limit="{limit}">\n<ol class="acx-list">\n' +
            "\n".join(row(e, "") for e in up) + "\n</ol>\n" +
            f'<p class="acx-empty"{" hidden" if up else ""}>No upcoming webinars right now.</p>\n'
            f'<p class="acx-home-more"><a class="acx-link" href="events/index.html">See all upcoming webinars &rarr;</a></p>\n</div>')

def build_home():
    p = os.path.join(ROOT, "index.html"); h = open(p, encoding="utf-8").read()
    m = re.search(r'<div class="(?:mec-wrap mec-skin-list-container" id="mec_skin_5739|acx acx-home-root")', h)
    assert m, "homepage events list not found"
    s, e = block_span(h, m.start())
    open(p, "w", encoding="utf-8").write(h[:s] + home_html() + h[e:])
    return p

def build_site():
    done = []
    for page in site_pages():
        p = os.path.join(ROOT, page)
        rel = "../" * page.count("/")
        h = open(p, encoding="utf-8").read()
        h = fix_events_nav(h, rel)
        h = fix_cloudflare_email(h)
        h = drop_dead_font_links(h)
        h, has_footer = replace_footer(h, rel)
        is_list, is_detail = page == "events/index.html", page.startswith("events-main/")
        h = ensure_head(h, rel, is_list or is_detail or page == "index.html",
                        "acx-page-list" if is_list else "acx-page-detail" if is_detail else None)
        open(p, "w", encoding="utf-8").write(h)
        done.append(f"{page}{'' if has_footer else ' (no theme footer)'}")
    return done

def replace_jsonld(h, obj, marker):
    # drop hand-written Event blocks and any previous generated block, then insert ours before </head>
    h = re.sub(r'<script type="application/ld\+json">\s*\{\s*"@context":\s*"http://schema.org",\s*"@type":\s*"Event"[\s\S]*?</script>\s*', "", h)
    h = re.sub(rf'<script type="application/ld\+json" id="{marker}">[\s\S]*?</script>\s*', "", h)
    tag = f'<script type="application/ld+json" id="{marker}">{json.dumps(obj, ensure_ascii=False)}</script>\n'
    return h.replace("</head>", tag + "</head>", 1)

def event_ld(e):
    return {"@type": "Event", "name": e.title, "startDate": Ev.iso(e.s), "endDate": Ev.iso(e.e),
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "location": {"@type": "VirtualLocation", "url": e.url},
            "organizer": {"@type": "Organization", "name": e.org},
            "performer": {"@type": "Person", "name": e.speaker},
            "description": " ".join(e.overview), "url": e.url}

# ---------------------------------------------------------------- events list
def row(e, base):
    has_page = bool(e.detail)
    link = f"{base}events-main/{e.detail}/index.html" if has_page else e.mailto
    title_href = "" if (e.past and not has_page) else f' href="{esc(link)}"'
    btn = "View details" if has_page else "Register"
    return f"""<li class="acx-ev{' is-past' if e.past else ''}" id="ev-{e.id}" data-start="{Ev.iso(e.s)}" data-end="{Ev.iso(e.e)}">
<time class="acx-date" datetime="{e.s:%Y-%m-%d}"><span class="acx-d">{e.s.day}</span><span class="acx-m">{e.s:%B}</span><span class="acx-w">{e.s:%A}</span></time>
<div class="acx-body">
<h3 class="acx-title"><a{title_href}>{esc(e.title)}</a></h3>
<ul class="acx-meta">
<li>{I_PERSON}<span><b>{esc(e.speaker)}</b> · {esc(e.org)}</span></li>
<li>{I_CLOCK}<span><span class="acx-tnum">{e.hm(e.s)} – {e.hm(e.e)}</span> {esc(e.zone_label)} · Online<span class="acx-live" hidden>Live now</span></span></li>
</ul>
</div>
<div class="acx-act"><a class="acx-btn" href="{esc(link)}">{btn}</a><span class="acx-ended">{I_CLOCK}Ended</span></div>
</li>"""

def list_html():
    up = [e for e in EVENTS if not e.past]
    past = sorted((e for e in EVENTS if e.past), key=lambda e: e.e, reverse=True)
    months, out = {}, []
    for e in up: months.setdefault(e.s.strftime("%Y%m"), []).append(e)
    for key, evs in months.items():
        label = evs[0].s.strftime("%B %Y")
        out.append(f'<section class="acx-month" aria-labelledby="acx-m-{key}"><h2 class="acx-h2" id="acx-m-{key}">{label}</h2>\n'
                   f'<ol class="acx-list">\n' + "\n".join(row(e, "../") for e in evs) + "\n</ol></section>")
    return f"""<div class="acx acx-list-root" id="acx-events">
<div class="acx-tabs" role="tablist" aria-label="Show events" hidden>
<button class="acx-tab" type="button" role="tab" id="acx-tab-up" aria-controls="acx-panel-up" aria-selected="true">Upcoming <span class="acx-count" data-count="upcoming">{len(up)}</span></button>
<button class="acx-tab" type="button" role="tab" id="acx-tab-past" aria-controls="acx-panel-past" aria-selected="false" tabindex="-1">Past <span class="acx-count" data-count="past">{len(past)}</span></button>
</div>
<section class="acx-panel" id="acx-panel-up" data-panel="upcoming" aria-labelledby="acx-tab-up">
{chr(10).join(out)}
<p class="acx-empty"{' hidden' if up else ''}>No upcoming webinars right now. <a class="acx-link" href="#past">See past webinars</a></p>
</section>
<section class="acx-panel" id="acx-panel-past" data-panel="past" aria-labelledby="acx-tab-past">
<h2 class="acx-h2 acx-past-h">Past webinars</h2>
<ol class="acx-list">
{chr(10).join(row(e, "../") for e in past)}
</ol>
</section>
</div>"""

def build_list():
    p = os.path.join(ROOT, "events", "index.html")
    h = open(p, encoding="utf-8").read()
    i = h.find('<div class="acx acx-list-root"')
    if i < 0:  # first run: replace the plugin list and the old inline override <style>
        j = h.find('<div class="mec-wrap mec-skin-list-container" id="mec_skin_5117">')
        k = h.rfind("<style>", 0, j)
        assert j > 0 and k > 0 and "Readability override" in h[k:j], "old list not found"
        _, end = block_span(h, j); i = k
    else:
        _, end = block_span(h, i)
    h = h[:i] + list_html() + h[end:]
    h = replace_jsonld(h, {"@context": "https://schema.org", "@graph": [event_ld(e) for e in EVENTS]}, "acx-events-jsonld")
    open(p, "w", encoding="utf-8").write(h)
    return p

# ---------------------------------------------------------------- session pages
def ics(e):
    def fold(line):
        b, out, first = line.encode(), [], True
        while len(b) > (75 if first else 74):
            n = 75 if first else 74
            while (b[n] & 0xC0) == 0x80: n -= 1
            out.append((b"" if first else b" ") + b[:n]); b, first = b[n:], False
        out.append((b"" if first else b" ") + b)
        return "\r\n".join(x.decode() for x in out)
    t = lambda s: s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,")
    z = lambda d: d.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ACTLC//Events//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
             "BEGIN:VEVENT", f"UID:{e.detail}@ac-tlc.org", "DTSTAMP:" + z(NOW), f"DTSTART:{z(e.s)}", f"DTEND:{z(e.e)}",
             "SUMMARY:" + t(e.title), "DESCRIPTION:" + t(f"ACTLC online webinar with {e.speaker} ({e.org}). {e.url}"),
             "LOCATION:Online", f"URL:{e.url}", "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(fold(l) for l in lines) + "\r\n"

def detail_html(e):
    z = lambda d: d.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    gcal = ("https://calendar.google.com/calendar/render?action=TEMPLATE&text=" + quote(e.title) +
            f"&dates={z(e.s)}/{z(e.e)}&details=" + quote(f"ACTLC online webinar with {e.speaker}. {e.url}") + "&location=Online")
    cities = []
    for name, tz in DATA["member_countries"]:
        lt = e.s.astimezone(ZoneInfo(tz)); dd = (lt.date() - e.s.date()).days
        mark = "Next day" if dd > 0 else "Previous day" if dd < 0 else ""
        cc = {"Asia/Dubai": "ae", "Asia/Riyadh": "sa", "Asia/Bahrain": "bh", "Africa/Cairo": "eg", "Africa/Casablanca": "ma"}[tz]
        cities.append(f'<li class="acx-city" data-cc="{cc}"><span class="acx-city-n">{name}</span>'
                      f'<span class="acx-city-t">{lt:%H:%M}</span><span class="acx-city-d">{mark}</span></li>')
    lead, body = e.lead_and_body()
    paras = "\n".join(f'<p class="acx-p">{esc(p)}</p>' for p in body)
    return f"""<div class="acx acx-detail" data-start="{Ev.iso(e.s)}" data-end="{Ev.iso(e.e)}" data-tz="{e.tz}">
<a class="acx-back" href="../../events/index.html">{I_CHEV}All events</a>
<p class="acx-eyebrow"><span class="acx-eyebrow-state">Upcoming webinar</span></p>
<h1 class="acx-h1">{esc(e.title)}</h1>
<div class="acx-presenter"><span class="acx-mono" aria-hidden="true">{e.initials()}</span><span><span class="acx-pname">{esc(e.speaker)}</span><span class="acx-porg">{esc(e.org)}</span></span></div>
<section class="acx-when" aria-label="Date and time">
<div class="acx-when-main">
<div class="acx-when-info">
<p class="acx-dateline"><time datetime="{e.s:%Y-%m-%d}">{e.long_date()}</time><span class="acx-status">Upcoming</span></p>
<p class="acx-bigtime"><time datetime="{Ev.iso(e.s)}">{e.hm(e.s)}</time> – <time datetime="{Ev.iso(e.e)}">{e.hm(e.e)}</time></p>
<p class="acx-when-sub">{esc(e.zone_label)} ({e.gmt()}) · {e.duration()} · Online</p>
</div>
<div class="acx-actions">
<div class="acx-actions-row"><a class="acx-btn acx-btn-filled" href="{esc(e.mailto)}">Register</a><a class="acx-btn" href="event.ics" download>{I_CALPLUS}Add to Calendar</a></div>
<p class="acx-note">Register opens an email to {EMAIL} · <a class="acx-link" href="{esc(gcal)}" target="_blank" rel="noopener">Google Calendar</a></p>
</div>
<div class="acx-ended-note" role="note"><strong>This session has ended</strong><span>It took place on {e.long_date()}.</span><a class="acx-link" href="../../events/index.html">See upcoming events &rarr;</a></div>
</div>
<div class="acx-when-world">
<p class="acx-world-h" id="acx-world-h">Start time in member countries</p>
<ul class="acx-world" aria-labelledby="acx-world-h">
{chr(10).join(cities)}
</ul>
</div>
</section>
<section class="acx-about" aria-labelledby="acx-about-h">
<h2 class="acx-h2" id="acx-about-h">About this session</h2>
<p class="acx-lead">{esc(lead)}</p>
{paras}
</section>
<div class="acx-bar"><a class="acx-btn acx-btn-filled" href="{esc(e.mailto)}">Register</a><a class="acx-btn" href="event.ics" download aria-label="Add to Calendar">{I_CALPLUS}</a></div>
</div>"""

def build_detail(e):
    d = os.path.join(ROOT, "events-main", e.detail); p = os.path.join(d, "index.html")
    h = open(p, encoding="utf-8").read()
    m = re.search(r'<div class="(?:ac-event-detail|acx acx-detail)"', h)
    assert m, f"detail block not found in {p}"
    s, end = block_span(h, m.start())
    h = h[:s] + detail_html(e) + h[end:]
    h = replace_jsonld(h, {"@context": "https://schema.org", **event_ld(e)}, "acx-event-jsonld")
    open(p, "w", encoding="utf-8").write(h)
    open(os.path.join(d, "event.ics"), "w", encoding="utf-8", newline="").write(ics(e))
    return p

if __name__ == "__main__":
    print("built", build_list())
    for e in EVENTS:
        if e.detail: print("built", build_detail(e))
    print("built", build_home())
    for page in build_site(): print("site chrome", page)
    print(f"{len(EVENTS)} events, {sum(not e.past for e in EVENTS)} upcoming, {sum(e.past for e in EVENTS)} past (as of {NOW:%Y-%m-%d %H:%M} UTC)")
