#!/usr/bin/env python3
"""Build the ACTLC events list and session pages from tools/events.json.

Writes: events/index.html (list + JSON-LD), events-main/<slug>/index.html and
event.ics for events that have a session page. Safe to run repeatedly.
Times are stored local to each event's IANA timezone; member-country clocks are
computed here (system tz database), not in the browser, so old browser tz data
cannot show a wrong time.        Usage: python3 tools/build_events.py
"""
import datetime as dt, hashlib, html, json, os, re, sys
from urllib.parse import quote
from zoneinfo import ZoneInfo
from images import picture_images
from mobile_chrome import replace_mobile_chrome
from home_mobile import home_mobile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = json.load(open(os.path.join(ROOT, "tools", "events.json"), encoding="utf-8"))
SITE, EMAIL = DATA["site"], DATA["register_email"]
PHONE = "+971 43 487 445"
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

def ensure_head(h, rel, events, body_class=None, styles=()):
    """(Re)write our <head> links. Versioned by content hash so browsers never keep a stale copy.
       styles: extra stylesheets for pages that need no script (the resources page)."""
    h = re.sub(r'<link\b[^>]*\bid="acx-(?:css|site|inter|events|resources|mobile|mobile-home|mobile-forms)"[^>]*>\n?', "", h)
    h = re.sub(r'<script\b[^>]*\bid="acx-(?:js|reveal|search|mobile-js)"[^>]*></script>\n?', "", h)
    h = re.sub(r'<link\b[^>]*inter-local\.css[^>]*>\n?', "", h)          # old link at a wrong depth
    tags = [f'<link rel="stylesheet" id="acx-inter" href="{rel}{INTER_CSS}"/>',
            f'<link rel="stylesheet" id="acx-site" href="{rel}actlc-assets/site.css?v={asset_version("site.css")}"/>',
            f'<script id="acx-reveal" src="{rel}actlc-assets/reveal.js?v={asset_version("reveal.js")}" defer></script>',
            f'<script id="acx-search" src="{rel}actlc-assets/search.js?v={asset_version("search.js")}" data-index="{rel}actlc-assets/search-index.json?v={asset_version("search-index.json")}" defer></script>',
            f'<link rel="stylesheet" id="acx-mobile" href="{rel}actlc-assets/mobile.css?v={asset_version("mobile.css")}" media="(max-width: 760px)"/>',
            f'<script id="acx-mobile-js" src="{rel}actlc-assets/mobile.js?v={asset_version("mobile.js")}" defer></script>']
    if events:
        tags += [f'<link rel="stylesheet" id="acx-css" href="{rel}actlc-assets/events.css?v={asset_version("events.css")}"/>',
                 f'<script id="acx-js" src="{rel}actlc-assets/events.js?v={asset_version("events.js")}" defer></script>']
    tags += [f'<link rel="stylesheet" id="acx-{n[:-4]}" href="{rel}actlc-assets/{n}?v={asset_version(n)}"/>' for n in styles]
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

CONF_MENU = {"Speakers": "speakers", "Registration": "registration", "Conference Themes": "tracks",
             "Sponsorship Opportunities": "sponsorship", "Contact Us": "contact"}

def fix_conference_nav(h, rel, here):
    """Conference submenu items all opened the top of the page: point each at its section."""
    target = r'(?:index\.html)?(?:#[^"]*)?' if here else r'[^"]*conference/index\.html(?:#[^"]*)?'
    pat = re.compile(r'(<a\b[^>]*?\bhref=")' + target + r'("[^>]*>\s*(?:<i\b[^>]*></i>\s*)?<span>([^<]+)</span>)')
    def sub(m):
        if m.group(3) not in CONF_MENU: return m.group(0)
        return m.group(1) + ("" if here else rel + "conference/index.html") + "#" + CONF_MENU[m.group(3)] + m.group(2)
    return pat.sub(sub, h)

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
<li><a href="tel:+97143487445">{PHONE}</a></li>
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

def build_conference():
    import sys; sys.path.insert(0, os.path.join(ROOT, "tools"))
    from conference_page import build_conference as _bc
    return _bc(ROOT, block_span, asset_version, EMAIL)

def build_resources():
    import sys; sys.path.insert(0, os.path.join(ROOT, "tools"))
    from resources_page import build_resources as _br
    return _br(ROOT, block_span, EMAIL)

def enhance_buttons(h):
    """Interactive hover button (port of the shadcn InteractiveHoverButton, in CSS): wrap each text
       button's label so it can slide out while the fill and an arrow slide in. Icon-only buttons are left alone."""
    def wrap(m):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "acx-btn-t" in inner: return m.group(0)
        label = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", inner)).strip()
        if not label: return m.group(0)
        attrs = attrs if "data-label=" in attrs else attrs + f' data-label="{esc(label)}"'
        return f'<{tag}{attrs}><span class="acx-btn-t">{inner}</span></{tag}>'
    h = re.sub(r'<(a|button)(\b[^>]*\bclass="[^"]*\bacx-btn\b[^"]*"[^>]*)>([\s\S]*?)</\1>', wrap, h)
    h = re.sub(r'<(a)(\b[^>]*\bclass="button small signup"[^>]*)>([\s\S]*?)</a>', wrap, h)
    return h

def build_site():
    done = []
    for page in site_pages():
        p = os.path.join(ROOT, page)
        rel = "../" * page.count("/")
        h = open(p, encoding="utf-8").read()
        h = fix_events_nav(h, rel)
        h = fix_conference_nav(h, rel, page == "conference/index.html")
        h = fix_cloudflare_email(h)
        # Member cards: the host label belongs to ADU, Abu Dhabi Campus (it was baked into the PSU image)
        h = h.replace("actlc-assets/logos/cards/UAEU.webp", "wp-content/uploads/2025/04/UAEU.webp")
        h = h.replace("wp-content/uploads/2025/04/PSU.webp", "actlc-assets/logos/cards/PSU.webp").replace("wp-content/uploads/2025/04/ADU.webp", "actlc-assets/logos/cards/ADU.webp")
        h = drop_dead_font_links(h)
        h = enhance_buttons(h)
        h, has_footer = replace_footer(h, rel)
        h = replace_mobile_chrome(h, rel, page, EMAIL, PHONE)
        if page == "index.html": h = home_mobile(h)
        h = version_images(h, page)
        h = picture_images(h, page)
        is_list, is_detail, is_res = page == "events/index.html", page.startswith("events-main/"), page == "resources/index.html"
        h = ensure_head(h, rel, is_list or is_detail or page == "index.html",
                        "acx-page-list" if is_list else "acx-page-detail" if is_detail else "acx-page-res" if is_res else "acx-page-reg" if page.startswith("registration/") else None,
                        ("events.css", "resources.css") if is_res else ("mobile-home.css",) if page == "index.html" else ("mobile-forms.css",) if page.startswith("registration/") else ())
        open(p, "w", encoding="utf-8").write(h)
        done.append(f"{page}{'' if has_footer else ' (no theme footer)'}")
    return done

LOCAL_IMG = re.compile(r'(?<![\w:/.-])((?:\.\./)*[\w-][\w./-]*\.(?:png|jpe?g|webp|gif|svg|avif))(?:\?v=[0-9a-f]+)?')

def version_images(h, page):
    """Every local picture URL carries its content hash, so a replaced picture gets a new URL."""
    def sub(m):
        f = os.path.normpath(os.path.join(ROOT, os.path.dirname(page), m.group(1)))
        if not os.path.isfile(f): return m.group(1)
        return m.group(1) + "?v=" + hashlib.sha1(open(f, "rb").read()).hexdigest()[:8]
    def attr(m): return m.group(1) + LOCAL_IMG.sub(sub, m.group(2)) + m.group(3)
    h = re.sub(r'(https?://[^"\s)]+\.(?:png|jpe?g|webp|gif|svg|avif))\?v=[0-9a-f]{8}\b', r"\1", h)   # remote pictures are not ours to version
    h = re.sub(r'<img\b[^>]*>', lambda m: re.sub(r'(\b(?:src|srcset|data-src|data-srcset)=")([^"]*)(")', attr, m.group(0)), h)
    return re.sub(r'url\((["\']?)([^)"\']+)', lambda m: "url(" + m.group(1) + LOCAL_IMG.sub(sub, m.group(2)), h)

FRESH_JS = ('(function(){var m=document.querySelector(\'meta[name="actlc-build"]\');if(!m||!window.fetch)return;'
            'var busy=0;function check(){if(busy)return;busy=1;fetch(m.getAttribute("data-src"),{cache:"no-store"})'
            '.then(function(r){return r.ok?r.json():null}).then(function(j){busy=0;if(!j||j.v===m.content)return;'
            'var k="actlc-reload-"+j.v;try{if(sessionStorage.getItem(k))return;sessionStorage.setItem(k,"1")}catch(e){}'
            'location.reload()}).catch(function(){busy=0})}check();'
            'addEventListener("pageshow",function(e){if(e.persisted)check()});'
            'document.addEventListener("visibilitychange",function(){if(document.visibilityState==="visible")check()})})();')

def stamp_build():
    """One stamp for the whole build. A page opened from memory (phone tab restore, back button,
       in-app browser) asks actlc-assets/version.json for the live stamp and reloads once if it changed."""
    strip = lambda h: re.sub(r'<meta name="actlc-build"[^>]*>\n?<script id="acx-fresh">[^<]*</script>\n?', "", h)
    pages = site_pages()
    texts = {p: strip(open(os.path.join(ROOT, p), encoding="utf-8").read()) for p in pages}
    sha = hashlib.sha1()
    for p in pages: sha.update(texts[p].encode())
    for n in sorted(os.listdir(os.path.join(ROOT, "actlc-assets"))):
        f = os.path.join(ROOT, "actlc-assets", n)
        if os.path.isfile(f) and n != "version.json": sha.update(open(f, "rb").read())
    v = sha.hexdigest()[:12]
    for p in pages:
        rel = "../" * p.count("/")
        tag = f'<meta name="actlc-build" content="{v}" data-src="{rel}actlc-assets/version.json"/>\n<script id="acx-fresh">{FRESH_JS}</script>\n'
        open(os.path.join(ROOT, p), "w", encoding="utf-8").write(texts[p].replace("</head>", tag + "</head>", 1))
    open(os.path.join(ROOT, "actlc-assets", "version.json"), "w").write(json.dumps({"v": v}))
    return v

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
<time class="acx-date" datetime="{e.s:%Y-%m-%d}"><span class="acx-d">{e.s.day}</span><span class="acx-m">{e.s:%B}</span><span class="acx-w">{e.s.year if e.past else format(e.s, "%A")}</span></time>
<div class="acx-body">
<h3 class="acx-title"><a{title_href}>{esc(e.title)}</a></h3>
<ul class="acx-meta">
<li>{I_PERSON}<span><b>{esc(e.speaker)}</b> · {esc(e.org)}</span></li>
<li>{I_CLOCK}<span><span class="acx-tnum">{e.hm(e.s)} – {e.hm(e.e)}</span> {esc(e.zone_label)}<span class="acx-live" hidden>Live now</span></span></li>
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
<p class="acx-list-note">All webinars are online.</p>
<section class="acx-panel" id="acx-panel-up" data-panel="upcoming" aria-label="Upcoming webinars">
{chr(10).join(out)}
<p class="acx-empty"{' hidden' if up else ''}>No upcoming webinars right now.</p>
</section>
<section class="acx-panel acx-panel-past" id="past" data-panel="past" aria-labelledby="acx-past-h">
<h2 class="acx-h2 acx-past-h" id="acx-past-h">Past webinars <span class="acx-count" data-count="past">{len(past)}</span></h2>
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
             "BEGIN:VEVENT", f"UID:{e.detail}@ac-tlc.org", "DTSTAMP:" + z(dt.datetime.fromisoformat(DATA["published"].replace("Z", "+00:00"))), f"DTSTART:{z(e.s)}", f"DTEND:{z(e.e)}",
             "SUMMARY:" + t(e.title), "DESCRIPTION:" + t(f"ACTLC online webinar with {e.speaker} ({e.org}). {e.url}"),
             "LOCATION:Online", f"URL:{e.url}", "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(fold(l) for l in lines) + "\r\n"

def detail_html(e):
    z = lambda d: d.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
    gcal = ("https://calendar.google.com/calendar/render?action=TEMPLATE&text=" + quote(e.title) +
            f"&dates={z(e.s)}/{z(e.e)}&details=" + quote(f"ACTLC online webinar with {e.speaker}. {e.url}") + "&location=Online")
    # Member-country start times as one sentence, countries sharing a time grouped (event's own zone excluded)
    groups = {}
    for name, tz in DATA["member_countries"]:
        if tz == e.tz: continue
        lt = e.s.astimezone(ZoneInfo(tz)); dd = (lt.date() - e.s.date()).days
        key = lt.strftime("%H:%M") + (" next day" if dd > 0 else " previous day" if dd < 0 else "")
        groups.setdefault(key, []).append(name)
    join = lambda n: n[0] if len(n) == 1 else ", ".join(n[:-1]) + " and " + n[-1]
    elsewhere = " · ".join(f"{k} in {join(v)}" for k, v in groups.items())
    lead, body = e.lead_and_body()
    paras = "\n".join(f'<p class="acx-p">{esc(p)}</p>' for p in body)
    return f"""<div class="acx acx-detail" data-start="{Ev.iso(e.s)}" data-end="{Ev.iso(e.e)}" data-tz="{e.tz}">
<a class="acx-back" href="../../events/index.html">{I_CHEV}All events</a>
<h1 class="acx-h1">{esc(e.title)}</h1>
<p class="acx-byline"><span class="acx-pname">{esc(e.speaker)}</span> · {esc(e.org)}</p>
<section class="acx-when" aria-label="Date and time">
<div class="acx-when-main">
<div class="acx-when-info">
<p class="acx-dateline"><time datetime="{e.s:%Y-%m-%d}">{e.long_date()}</time><span class="acx-status">Upcoming</span></p>
<p class="acx-bigtime"><time datetime="{Ev.iso(e.s)}">{e.hm(e.s)}</time> – <time datetime="{Ev.iso(e.e)}">{e.hm(e.e)}</time></p>
<p class="acx-when-sub">{esc(e.zone_label)} ({e.gmt()}) · {e.duration()} · Online</p>
<p class="acx-elsewhere">{esc(elsewhere)}</p>
<p class="acx-yourtime" hidden></p>
</div>
<div class="acx-actions">
<div class="acx-actions-row"><a class="acx-btn acx-btn-filled" href="{esc(e.mailto)}" title="Opens an email to {EMAIL}">Register</a><a class="acx-btn" href="event.ics" download>{I_CALPLUS}Add to Calendar</a></div>
</div>
<div class="acx-ended-note" role="note"><strong>This session has ended</strong><span>It took place on {e.long_date()}.</span><a class="acx-link" href="../../events/index.html">See upcoming events &rarr;</a></div>
</div>

</section>
<section class="acx-about" aria-labelledby="acx-about-h">
<h2 class="acx-h2" id="acx-about-h">About this session</h2>
<p class="acx-lead">{esc(lead)}</p>
{paras}
</section>
<div class="acx-bar"><a class="acx-btn acx-btn-filled" href="{esc(e.mailto)}" title="Opens an email to {EMAIL}">Register</a><a class="acx-btn" href="event.ics" download aria-label="Add to Calendar">{I_CALPLUS}</a></div>
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
    print("built", build_conference())
    print("built", build_resources())
    from search_index import build_index
    print("built %s (%d records)" % build_index(ROOT, EVENTS))
    for page in build_site(): print("site chrome", page)
    print("build stamp", stamp_build())
    print(f"{len(EVENTS)} events, {sum(not e.past for e in EVENTS)} upcoming, {sum(e.past for e in EVENTS)} past (as of {NOW:%Y-%m-%d %H:%M} UTC)")
