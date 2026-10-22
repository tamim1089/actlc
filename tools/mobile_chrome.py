"""Phone chrome for every public page (shown at <= 760px only; actlc-assets/mobile.css):
a top bar (logo, search), a bottom tab bar (Home, Events, Conference, Resources, More) and the More sheet.
The block sits right after <body> between <!--acx-m--> markers, so a rebuild replaces it in place."""
import re

LOGO = "actlc-assets/logos/actlc-wordmark.png"   # the logo trimmed to its art (no empty margin), 389x136

# 24px outline icons, one stroke weight; the current tab is marked by a pill behind the icon and a heavier label
ICONS = {
    "home": '<path d="M3.5 10.2 12 3.5l8.5 6.7V19a1.5 1.5 0 0 1-1.5 1.5h-4.2v-6h-5.6v6H5A1.5 1.5 0 0 1 3.5 19z"/>',
    "events": '<rect x="3.5" y="5" width="17" height="15.5" rx="3"/><path d="M3.5 10h17M8 3v4M16 3v4"/>',
    "conference": '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21M8.5 21h7"/>',
    "resources": '<path d="M6.5 3h7.5l4.5 4.5V20a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/><path d="M14 3v4.5h4.5M8.5 12.5h7M8.5 16.5h5"/>',
    "more": '<circle cx="12" cy="12" r="8.5"/><path d="M8 12h.01M12 12h.01M16 12h.01" stroke-width="2.6"/>',
}
TABS = [("home", "Home", "index.html"), ("events", "Events", "events/index.html"),
        ("conference", "Conference", "conference/index.html"), ("resources", "Resources", "resources/index.html")]
SHEET = [("Account", [("Create an account", "registration/index.html")]),
         ("Community", [("News Feed", "news-feed/index.html"), ("Groups", "groups/index.html"), ("Blog", "bolg/index.html")]),
         ("Members", [("Experts", "experts/index.html"), ("Founding Members", "founding-members/index.html")])]


def icon(name):
    return ('<svg class="acx-m-ic" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.7" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>' % ICONS[name])


def current_tab(page):
    if page == "index.html": return "home"
    if page.startswith(("events/", "events-main/")): return "events"
    if page.startswith("conference/"): return "conference"
    if page.startswith("resources/"): return "resources"
    return "more"


def chrome_html(rel, page, email, phone):
    cur = current_tab(page)
    tab = lambda key, label, href: ('<a class="acx-m-tab%s" href="%s%s"%s>%s<span>%s</span></a>'
                                    % (" is-cur" if key == cur else "", rel, href, ' aria-current="page"' if key == cur else "", icon(key), label))
    row = lambda label, href: f'<li><a class="acx-m-row" href="{rel}{href}"><span>{label}</span><span class="acx-m-chev" aria-hidden="true"></span></a></li>'
    groups = "".join(f'<h3 class="acx-m-gh">{t}</h3><ul class="acx-m-group">{"".join(row(*r) for r in rows)}</ul>' for t, rows in SHEET)
    contact = (f'<h3 class="acx-m-gh">Contact</h3><ul class="acx-m-group">'
               f'<li><a class="acx-m-row" href="mailto:{email}"><span>Email</span><span class="acx-m-val">{email}</span></a></li>'
               f'<li><a class="acx-m-row" href="tel:{re.sub(r"[^+0-9]", "", phone)}"><span>Phone</span><span class="acx-m-val">{phone}</span></a></li></ul>')
    more_cur = cur == "more"
    return f"""<!--acx-m--><div class="acx acx-m">
<header class="acx-m-top"><a class="acx-m-logo" href="{rel}index.html"><img src="{rel}{LOGO}" width="389" height="136" alt="Arab Teaching and Learning Consortium, home" decoding="async"/></a>
<a class="acx-m-search header-search-link" href="#" aria-label="Search the site" hidden><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg></a></header>
<nav class="acx-m-tabs" aria-label="Main">{"".join(tab(*t) for t in TABS)}<a class="acx-m-tab acx-m-more-open{' is-cur' if more_cur else ''}" href="#acx-more" aria-haspopup="dialog"{' aria-current="page"' if more_cur else ''}>{icon("more")}<span>More</span></a></nav>
<dialog class="acx-m-sheet" id="acx-more" aria-labelledby="acx-more-h"><div class="acx-m-sheet-in">
<div class="acx-m-sheet-top"><span class="acx-m-grab" aria-hidden="true"></span><h2 id="acx-more-h">More</h2><a class="acx-m-close" href="#" aria-label="Close">Done</a></div>
{groups}{contact}</div></dialog>
</div><!--/acx-m-->
"""


def replace_mobile_chrome(h, rel, page, email, phone):
    h = re.sub(r"<!--acx-m-->[\s\S]*?<!--/acx-m-->\n?", "", h)
    m = re.search(r"<body\b[^>]*>\n?", h)
    return h[:m.end()] + chrome_html(rel, page, email, phone) + h[m.end():] if m else h
