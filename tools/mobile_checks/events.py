"""Leaf 1.4: events on phones. Homepage "Upcoming Events" rows, the events list (date tiles, month groups, past webinars
behind a disclosure row) and the session pages (status pill, grouped times elsewhere, Register bar above the tab bar)."""
import datetime as dt, json, os
from zoneinfo import ZoneInfo
from . import CONTRAST, SMALL_TARGETS, SMALL_TEXT, WRONG_FONT, UNDER_BARS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = json.load(open(os.path.join(ROOT, "tools", "events.json"), encoding="utf-8"))
CLOCK = dt.datetime(2026, 10, 22, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=4)))   # same fixed clock as check_mobile.py


def _ev(e):
    z = ZoneInfo(e["tz"])
    return dict(e, s=dt.datetime.fromisoformat(e["start"]).replace(tzinfo=z), e=dt.datetime.fromisoformat(e["end"]).replace(tzinfo=z))


EVENTS = [_ev(e) for e in DATA["events"]]
UPCOMING = [e for e in EVENTS if e["e"] > CLOCK]
PAST = [e for e in EVENTS if e["e"] <= CLOCK]


def expected_status(slug):
    """What events.js should print on the session page at CLOCK for a visitor in Dubai (statusText)."""
    e = next(x for x in EVENTS if x["detail"] == slug)
    if CLOCK >= e["e"]: return "Ended"
    if CLOCK >= e["s"]: return "Live now"
    m = (e["s"] - CLOCK).total_seconds() / 60
    if m < 60: return f"Starts in {max(1, round(m))} minutes"
    if m < 720: return f"Starts in {round(m / 60)} hours"
    dubai = ZoneInfo("Asia/Dubai")
    d = (e["s"].astimezone(dubai).date() - CLOCK.astimezone(dubai).date()).days
    return "Starts tomorrow" if d == 1 else f"Starts in {d} days"


# Weekday or any text in a hairline weight (the old thin uppercase weekday)
THIN = r"""(sel) => [...document.querySelectorAll(sel)].filter(e => e.getClientRects().length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
  .filter(e => +getComputedStyle(e).fontWeight < 300 || (getComputedStyle(e).textTransform === 'uppercase' && /day$/i.test(e.textContent.trim())))
  .map(e => e.textContent.trim().slice(0, 24))"""

# Rows: left edge, tile size and colours, and how much of the text column each wrapped title uses (balance leaves half empty)
ROWS = r"""(sel) => [...document.querySelectorAll(sel)].filter(li => li.getClientRects().length).map(li => {
  const r = li.getBoundingClientRect(), tile = li.querySelector('.acx-date'), body = li.querySelector('.acx-body'), t = li.querySelector('.acx-title');
  const range = document.createRange(); range.selectNodeContents(t);
  const lines = {}; [...range.getClientRects()].forEach(q => { const k = Math.round(q.top); lines[k] = Math.max(lines[k] || 0, q.right); });
  const tops = Object.keys(lines), widest = Math.max(...Object.values(lines)) - body.getBoundingClientRect().left;
  const ts = getComputedStyle(tile);
  return { left: Math.round(r.left), right: Math.round(r.right), tileW: Math.round(tile.getBoundingClientRect().width), tileRadius: parseFloat(ts.borderTopLeftRadius),
           tileBg: ts.backgroundColor, lines: tops.length, use: +(widest / body.getBoundingClientRect().width).toFixed(2),
           title: t.textContent.trim().slice(0, 30), wrap: getComputedStyle(t).textWrap || getComputedStyle(t).textWrapStyle || '',
           titlePx: parseFloat(getComputedStyle(t).fontSize), wd: (li.querySelector('.acx-wd') || {}).textContent || '' } })"""


def _rows_ok(check, where, rows, past=False):
    check(rows and all(r["left"] >= 16 and r["right"] <= 390 - 16 for r in rows), f"{where}: rows sit inside the 16px gutter {[(r['left'], r['right']) for r in rows][:3]}")
    check(all(48 <= r["tileW"] <= 60 and r["tileRadius"] >= 10 for r in rows), f"{where}: every row has a rounded date tile {[(r['tileW'], r['tileRadius']) for r in rows][:3]}")
    want = "rgb(231, 238, 240)" if past else "rgb(232, 246, 247)"
    check(all(r["tileBg"] == want for r in rows), f"{where}: tile background is {'--track (past)' if past else '--teal-tint'} {sorted({r['tileBg'] for r in rows})}")
    check(all(17 <= r["titlePx"] <= 18 for r in rows), f"{where}: titles 17-18px {sorted({r['titlePx'] for r in rows})}")
    check(all("balance" not in r["wrap"] for r in rows), f"{where}: titles are not balanced {sorted({r['wrap'] for r in rows})}")
    narrow = [(r["title"], r["use"]) for r in rows if r["lines"] > 1 and r["use"] < 0.7]
    check(not narrow, f"{where}: wrapped titles use at least 70% of the text column {narrow[:3]}")
    check(all(r["wd"].strip().endswith("·") and len(r["wd"].split()[0]) == 3 for r in rows), f"{where}: weekday is text in the time line {[r['wd'] for r in rows][:3]}")


def _common(check, pg, where, sel):
    for name, helper in (("targets at least 44px", SMALL_TARGETS), ("text at least 13px", SMALL_TEXT), ("Inter only", WRONG_FONT),
                         ("contrast AA", CONTRAST), ("no hairline-weight or uppercase weekday", THIN)):
        bad = pg.evaluate(helper, sel)
        check(not bad, f"{where}: {name} {bad[:4]}")
    sw = pg.evaluate("document.documentElement.scrollWidth")
    check(sw == 390, f"{where}: no sideways scroll ({sw}px)")


def events(ctx):
    check = ctx.check

    print("\n== Events: homepage rows ==")
    pg = ctx.phone(ctx.PAGES["home"])
    rows = pg.evaluate(ROWS, ".acx-home-root .acx-ev")
    check(len(rows) == min(3, len(UPCOMING)), f"home: shows the next {min(3, len(UPCOMING))} webinars ({len(rows)})")
    _rows_ok(check, "home", rows)
    grp = pg.evaluate("(r => [Math.round(r.left), Math.round(r.right), parseFloat(getComputedStyle(document.querySelector('.acx-home-root')).borderTopLeftRadius)])(document.querySelector('.acx-home-root').getBoundingClientRect())")
    check(grp[0] == 16 and grp[1] == 374 and grp[2] >= 10, f"home: rows form one inset group with a 16px gutter {grp}")
    more = pg.evaluate("""(a => { const r = a.getBoundingClientRect(); return [a.innerText.trim(), Math.round(r.height), getComputedStyle(a, '::after').content !== 'none'] })(document.querySelector('.acx-home-more a'))""")
    check(more[0] == "See all webinars" and more[1] >= 44 and more[2], f"home: 'See all webinars' row with a chevron, at least 44px {more}")
    _common(check, pg, "home", ".acx-home-root, .acx-home-root *")
    pg.context.close()

    print("\n== Events: list page ==")
    pg = ctx.phone(ctx.PAGES["events"])
    h1 = pg.evaluate("(h => [h.textContent.trim(), parseFloat(getComputedStyle(h).fontSize), +getComputedStyle(h).fontWeight, Math.round(h.getBoundingClientRect().left)])(document.querySelector('.entry-title'))")
    check(h1[0] == "Events" and h1[1] == 30 and h1[2] == 700 and h1[3] == 16, f"list: large title 'Events' 30px/700 at the gutter {h1}")
    heads = pg.evaluate("[...document.querySelectorAll('.acx-month > .acx-h2')].map(h => [h.textContent, parseFloat(getComputedStyle(h).fontSize), +getComputedStyle(h).fontWeight, getComputedStyle(h).textTransform])")
    check(heads and all(13 <= h[1] <= 15 and h[2] == 600 and h[3] == "none" for h in heads), f"list: month headers 13-15px/600 sentence case {heads[:2]}")
    months = sorted({e["s"].strftime("%B %Y") for e in UPCOMING}, key=lambda m: dt.datetime.strptime(m, "%B %Y"))
    check([h[0] for h in heads] == months, f"list: one group per month {[h[0] for h in heads]}")
    up = pg.evaluate(ROWS, "[data-panel=upcoming] .acx-ev")
    check(len(up) == len(UPCOMING), f"list: {len(UPCOMING)} upcoming rows, as in events.json ({len(up)})")
    _rows_ok(check, "list upcoming", up)
    tog = pg.evaluate("""(b => b && [b.innerText.replace(/\\s+/g, ' ').trim(), b.getAttribute('aria-expanded'), Math.round(b.getBoundingClientRect().height),
        document.getElementById(b.getAttribute('aria-controls')).getClientRects().length])(document.querySelector('.acx-past-toggle'))""")
    check(tog and tog[0] == f"Past webinars {len(PAST)}" and tog[1] == "false" and tog[2] >= 44 and tog[3] == 0,
          f"list: past webinars folded behind one row 'Past webinars {len(PAST)}' {tog}")
    pg.tap(".acx-past-toggle"); pg.wait_for_timeout(350)
    past = pg.evaluate(ROWS, "[data-panel=past] .acx-ev")
    check(pg.get_attribute(".acx-past-toggle", "aria-expanded") == "true" and len(past) == len(PAST),
          f"list: a tap opens all {len(PAST)} past webinars ({len(past)})")
    _rows_ok(check, "list past", past, past=True)
    ended = pg.evaluate("[...document.querySelectorAll('[data-panel=past] .acx-ended')].filter(e => e.getClientRects().length).map(e => [getComputedStyle(e).color, parseFloat(getComputedStyle(e).fontSize)])")
    check(len(ended) == len(PAST) and all(c != "rgb(180, 35, 24)" and s <= 15 for c, s in ended), f"list: past rows carry a small neutral 'Ended' label, not red {ended[:1]}")
    years = pg.evaluate("[...document.querySelectorAll('[data-panel=past] .acx-w')].filter(e => e.getClientRects().length).map(e => e.textContent)")
    check(len(years) == len(PAST) and all(y.isdigit() for y in years), f"list: past tiles show the year {years[:3]}")
    _common(check, pg, "list", ".acx-list-root, .acx-list-root *, .entry-title")
    pg.evaluate("document.documentElement.style.scrollBehavior = 'auto'")   # the theme scrolls smoothly; measure where scrollIntoView lands
    under = pg.evaluate(UNDER_BARS, ".acx-list-root h2, .entry-title")
    check(not under, f"list: headings land below the top bar {under}")
    pg.tap(".acx-past-toggle"); pg.wait_for_timeout(300)
    check(pg.get_attribute(".acx-past-toggle", "aria-expanded") == "false" and not pg.is_visible("#acx-past-list"), "list: a second tap folds them again")
    pg.context.close()

    pg = ctx.phone(ctx.PAGES["events"] + "#past")
    check(pg.get_attribute(".acx-past-toggle", "aria-expanded") == "true" and pg.is_visible("#acx-past-list"), "list: a link to #past opens the past webinars")
    pg.context.close()

    pg = ctx.phone(ctx.PAGES["events"], java_script_enabled=False)
    n = pg.evaluate("[...document.querySelectorAll('[data-panel=past] .acx-ev')].filter(e => e.getClientRects().length).length")
    check(n == len(PAST) and not pg.query_selector(".acx-past-toggle") and pg.is_visible(".acx-past-h"),
          f"list without JS: all {len(PAST)} past webinars stay visible under their heading ({n})")
    pg.context.close()

    for key in ("designing", "teaching"):
        slug = ctx.PAGES[key].split("/")[2]
        e = next(x for x in EVENTS if x["detail"] == slug)
        is_past = e["e"] <= CLOCK
        want = expected_status(slug)
        print(f"\n== Events: session page {key} (expect '{want}') ==")
        pg = ctx.phone(ctx.PAGES[key])
        st = pg.evaluate("""(s => [s.textContent, getComputedStyle(s, '::before').content, parseFloat(getComputedStyle(s).borderTopLeftRadius),
            getComputedStyle(s).backgroundColor, Math.round(s.getBoundingClientRect().top) < Math.round(document.querySelector('.acx-dateline time').getBoundingClientRect().top)])(document.querySelector('.acx-status'))""")
        check(st[0] == want, f"{key}: status says '{want}' ({st[0]})")
        check(st[1] in ("none", "normal") and st[2] >= 10 and st[3] != "rgba(0, 0, 0, 0)" and st[4],
              f"{key}: status is a pill above the date, no stray dot {st[1:]}")
        h1 = pg.evaluate("(h => [parseFloat(getComputedStyle(h).fontSize), +getComputedStyle(h).fontWeight, getComputedStyle(h).textWrap || ''])(document.querySelector('.acx-h1'))")
        check(h1[0] == 28 and h1[1] == 700 and "balance" not in h1[2], f"{key}: title 28px/700, wraps naturally {h1}")
        by = pg.evaluate("[...document.querySelectorAll('.acx-byline .acx-pname, .acx-byline .acx-borg')].map(s => Math.round(s.getBoundingClientRect().top))")
        check(len(by) == 2 and by[1] > by[0] and not pg.is_visible(".acx-bsep"), f"{key}: byline on two lines, speaker then organisation {by}")
        n_else = len([1 for _, tz in DATA["member_countries"] if tz != e["tz"]])
        rows = pg.evaluate("[...document.querySelectorAll('.acx-elsewhere-m .acx-m-row')].map(r => r.innerText.replace(/\\s+/g, ' ').trim())")
        check(len(rows) == n_else and all(":" in r for r in rows), f"{key}: {n_else} member-country rows ({rows[:2]})")
        check(not pg.is_visible(".acx-elsewhere"), f"{key}: the run-on sentence of times is gone on phones")
        if is_past:
            check(not pg.is_visible(".acx-elsewhere-m") and not pg.is_visible(".acx-bar"), f"{key}: ended, so no Register bar and no times elsewhere")
            note = pg.evaluate("""(n => { const a = n.querySelector('a'), r = a.getBoundingClientRect(), c = n.closest('.acx-when-main').querySelector('.acx-when-info').getBoundingClientRect();
                return [a.innerText.trim(), Math.round(r.height), Math.round(n.getBoundingClientRect().top) >= Math.round(c.bottom)] })(document.querySelector('.acx-ended-note'))""")
            check(note[0] == "See upcoming events" and note[1] >= 44 and note[2], f"{key}: ended note sits below the card, its link at least 44px {note}")
        else:
            check(pg.is_visible(".acx-elsewhere-m"), f"{key}: times elsewhere shown as a grouped list")
            bars = pg.evaluate("""[document.querySelector('.acx-detail .acx-bar').getBoundingClientRect(), document.querySelector('.acx-m-tabs').getBoundingClientRect()].map(r => [Math.round(r.top), Math.round(r.bottom)])""")
            check(bars[0][1] <= bars[1][0] and bars[0][1] - bars[0][0] >= 50, f"{key}: Register bar sits on top of the tab bar, not over it {bars}")
            btn = pg.evaluate("[...document.querySelectorAll('.acx-bar .acx-btn')].map(b => Math.round(b.getBoundingClientRect().height))")
            check(btn and min(btn) >= 44, f"{key}: bar buttons at least 44px {btn}")
        _common(check, pg, key, ".acx-detail, .acx-detail *")
        pg.evaluate("document.documentElement.style.scrollBehavior = 'auto'")
        under = pg.evaluate(UNDER_BARS, ".acx-detail h1, .acx-detail h2")
        check(not under, f"{key}: headings land below the top bar {under}")
        clear = pg.evaluate("""(() => { document.documentElement.style.scrollBehavior = 'auto'; scrollTo(0, document.body.scrollHeight);
            const last = [...document.querySelectorAll('.acx-foot-bottom p, .acx-detail .acx-about > *')].filter(e => e.getClientRects().length).pop();
            const bar = document.querySelector('.acx-detail .acx-bar'), tabs = document.querySelector('.acx-m-tabs').getBoundingClientRect().top;
            const limit = bar && bar.getClientRects().length ? bar.getBoundingClientRect().top : tabs;
            return [Math.round(last.getBoundingClientRect().bottom), Math.round(limit)] })()""")
        check(clear[0] <= clear[1], f"{key}: the last line clears the bars at the bottom {clear}")
        pg.context.close()

    print("\n== Events: 320px wide ==")
    for key in ("home", "events", "designing", "teaching"):
        c = ctx.b.new_context(viewport={"width": 320, "height": 640}, device_scale_factor=2, is_mobile=True, has_touch=True, timezone_id="Asia/Dubai")
        pg = c.new_page(); pg.clock.install(time=CLOCK); pg.goto(ctx.BASE + ctx.PAGES[key], wait_until="load"); pg.wait_for_timeout(400)
        if key == "events": pg.tap(".acx-past-toggle"); pg.wait_for_timeout(300)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        over = pg.evaluate("[...document.querySelectorAll('.acx-home-root *, .acx-list-root *, .acx-detail *')].filter(e => e.getClientRects().length && e.getBoundingClientRect().right > 320.5 && !e.closest('.acx-bar')).map(e => e.className || e.tagName).slice(0, 4)")
        check(sw == 320 and not over, f"320px {key}: nothing overflows ({sw}px) {over}")
        c.close()


SECTIONS = {"events": events}
