"""Leaf 1.1: the phone chrome on every public page (top bar, tab bar, More sheet, search, footer, buttons, overflow)."""
from . import CONTRAST, SMALL_TARGETS, SMALL_TEXT

CURRENT = {"home": "Home", "events": "Events", "designing": "Events", "teaching": "Events", "conference": "Conference",
           "resources": "Resources", "registration": "More"}
SHEET_ROWS = ["Create an account", "News Feed", "Groups", "Blog", "Experts", "Founding Members", "Email", "Phone"]


def chrome(ctx):
    check = ctx.check
    print("\n== Phone chrome on every public page ==")
    for name, path in ctx.PAGES.items():
        pg = ctx.phone(path)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(sw == 390, f"{name}: no sideways scroll ({sw}px)")
        top = pg.evaluate("(r => [Math.round(r.top), Math.round(r.height)])(document.querySelector('.acx-m-top').getBoundingClientRect())")
        tabs = pg.evaluate("(r => [Math.round(r.bottom), Math.round(r.height)])(document.querySelector('.acx-m-tabs').getBoundingClientRect())")
        check(top[0] == 0 and 44 <= top[1] <= 64 and tabs[0] == 844 and 50 <= tabs[1] <= 70,
              f"{name}: top bar pinned at the top {top}, tab bar at the bottom edge {tabs}")
        check(not pg.is_visible("#masthead") and not pg.is_visible(".bb-left-panel-mobile"), f"{name}: theme header and its menu button hidden")
        cur = pg.evaluate("[...document.querySelectorAll('.acx-m-tab[aria-current=page] span')].map(s => s.textContent)")
        check(cur == [CURRENT[name]], f"{name}: current tab {cur}")
        clipped = pg.evaluate("[...document.querySelectorAll('.acx-m-tab span')].filter(s => s.scrollWidth > s.clientWidth).map(s => s.textContent)")
        check(not clipped, f"{name}: every tab label fits {clipped or ''}")
        small = pg.evaluate(SMALL_TARGETS, ".acx-m a, .acx-footer a")
        check(not small, f"{name}: chrome and footer targets at least 44px {small[:4]}")
        tiny = pg.evaluate(SMALL_TEXT, ".acx-m *, .acx-footer *")
        check(not tiny, f"{name}: chrome and footer text at least 13px {tiny[:4]}")
        low = pg.evaluate(CONTRAST, ".acx-m *, .acx-footer *")
        check(not low, f"{name}: chrome and footer contrast {low[:3]}")
        first = pg.evaluate("""(() => { const h = [...document.querySelectorAll('h1, h2, .acx-c-hero')].find(e => e.getClientRects().length && !e.closest('.acx-m'));
            return h ? Math.round(h.getBoundingClientRect().top) : null })()""")
        check(first is not None and first >= top[1], f"{name}: the first heading starts below the top bar ({first}px vs {top[1]}px)")   # home hero: leaf 1.3
        dots = pg.evaluate("[...document.querySelectorAll('.acx-btn[data-label]')].filter(b => b.offsetParent && getComputedStyle(b, '::before').display !== 'none').length")
        check(dots == 0, f"{name}: buttons show no hover dot on touch ({dots})")
        pg.context.close()

    print("\n== More sheet, tabs, search ==")
    pg = ctx.phone(ctx.PAGES["home"])
    pg.tap(".acx-m-more-open"); pg.wait_for_timeout(400)
    rows = pg.evaluate("[...document.querySelectorAll('#acx-more .acx-m-row > span:first-child')].map(s => s.textContent)")
    check(pg.evaluate("document.getElementById('acx-more').open") and rows == SHEET_ROWS, f"More: the sheet opens with every item {rows}")
    small = pg.evaluate(SMALL_TARGETS, "#acx-more *")
    check(not small, f"More: rows and Done at least 44px {small[:4]}")
    pg.keyboard.press("Tab")
    check(pg.evaluate("!!document.activeElement.closest('#acx-more')"), "More: keyboard focus stays inside the sheet")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    check(not pg.evaluate("document.getElementById('acx-more').open"), "More: Esc closes the sheet")
    pg.tap(".acx-m-more-open"); pg.wait_for_timeout(300); pg.tap("#acx-more .acx-m-close"); pg.wait_for_timeout(200)
    check(not pg.evaluate("document.getElementById('acx-more').open"), "More: Done closes the sheet")
    with pg.expect_navigation(): pg.tap(".acx-m-tab[href$='events/index.html']")
    check(pg.url.endswith("/events/index.html"), f"tabs: Events opens the events list ({pg.url.split('8899')[-1]})")
    pg.wait_for_timeout(300); pg.tap(".acx-m-search"); pg.wait_for_selector(".acx-sd[open]", timeout=4000)
    box = pg.evaluate("(r => [Math.round(r.width), Math.round(r.height)])(document.querySelector('.acx-sd').getBoundingClientRect())")
    check(box == [390, 844], f"search: the top bar button opens full-screen search {box}")
    pg.context.close()

    pg = ctx.phone(ctx.PAGES["home"] + "#acx-more", java_script_enabled=False)
    check(pg.is_visible("#acx-more .acx-m-row") and not pg.is_visible(".acx-m-search"),
          "no JS: More still opens (#acx-more), and the search button stays hidden because search needs JS")
    pg.context.close()


SECTIONS = {"chrome": chrome}
