"""Leaf 1.5: the conference page on phones (actlc-assets/conference.css under 760px, conference.js, tools/conference_page.py).
Counts come from tools/conference.json, the same data the page is built from."""
import json, os
from . import CONTRAST, SMALL_TARGETS, SMALL_TEXT, WRONG_FONT, UNDER_BARS

DATA = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conference.json"), encoding="utf-8"))
SHEET = ["Overview", "About", "Tracks", "Programme", "Speakers", "Organising committee", "Call for proposals", "Fees",
         "Founding members", "Sponsorship", "Contact"]
LEFT = "(s => Math.round(document.querySelector(s).getBoundingClientRect().left))"
BARS = "Math.round(document.querySelector('.acx-local').getBoundingClientRect().bottom)"


def conference(ctx):
    check = ctx.check
    path = ctx.PAGES["conference"]
    print("\n== Conference on phones ==")
    pg = ctx.phone(path)
    pg.evaluate("document.documentElement.classList.remove('acx-rv')")
    sw = pg.evaluate("document.documentElement.scrollWidth")
    check(sw == 390, f"conference: no sideways scroll at 390 ({sw}px)")
    lefts = {s: pg.evaluate(LEFT + "(%r)" % s) for s in (".acx-c-h1", "#acx-h-tracks", "#tracks .acx-c-lead", "#acx-h-prog", ".acx-c-prose p", "#acx-h-con")}
    check(set(lefts.values()) == {16}, f"conference: one 16px gutter for titles and paragraphs {lefts}")

    # K1 section bar and sheet
    bar = pg.evaluate("(r => [Math.round(r.top), Math.round(r.height), Math.round(r.width)])(document.querySelector('.acx-local').getBoundingClientRect())")
    top = pg.evaluate("Math.round(document.querySelector('.acx-m-top').getBoundingClientRect().bottom)")
    check(bar[0] == top and 44 <= bar[1] <= 56 and bar[2] == 390, f"section bar: pinned under the top bar, full width, compact [top, height, width] = {bar} (top bar ends {top})")
    check(not pg.is_visible(".acx-local-links") and pg.is_visible(".acx-local-sheet") and pg.is_visible(".acx-local .acx-btn"),
          "section bar: the clipped chip strip gives way to a Sections button and Register")
    cur = lambda: pg.evaluate("document.querySelector('.acx-local-cur b').textContent")
    check(cur() == "Overview", f"section bar: names the section on screen at the top ({cur()!r})")
    pg.evaluate("scrollTo({top: document.getElementById('programme').getBoundingClientRect().top + scrollY - 100, behavior: 'instant'})"); pg.wait_for_timeout(300)
    check(cur() == "Programme", f"section bar: the name follows the scroll ({cur()!r} at the programme)")
    pg.tap(".acx-local-sheet"); pg.wait_for_timeout(400)
    rows = pg.evaluate("[...document.querySelectorAll('#acx-secs .acx-m-row > span:first-child')].map(s => s.textContent)")
    check(pg.evaluate("document.getElementById('acx-secs').open") and rows == SHEET, f"sheet: opens with every section {rows}")
    marked = pg.evaluate("[...document.querySelectorAll('#acx-secs .acx-m-row[aria-current]')].map(a => a.textContent)")
    check(marked == ["Programme"], f"sheet: the section on screen is ticked {marked}")
    small = pg.evaluate(SMALL_TARGETS, "#acx-secs *")
    check(not small, f"sheet: rows and Done at least 44px {small[:4]}")
    pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
    check(not pg.evaluate("document.getElementById('acx-secs').open"), "sheet: Esc closes it")
    bad = []
    for i, label in enumerate(SHEET):
        pg.tap(".acx-local-sheet"); pg.wait_for_timeout(350)
        pg.tap(f"#acx-secs li:nth-child({i + 1}) .acx-m-row"); pg.wait_for_timeout(700)
        got = pg.evaluate("""(i => { const a = document.querySelectorAll('#acx-secs .acx-m-row')[i], t = document.getElementById(a.dataset.sec);
            const h = t.matches('h1, h2') ? t : t.querySelector('h1, h2'), r = h.getBoundingClientRect();
            return [document.getElementById('acx-secs').open, Math.round(r.top), a.dataset.short || a.textContent,
                    document.querySelector('.acx-local-cur b').textContent]; })(%d)""" % i)
        bars = pg.evaluate(BARS)
        if got[0] or not (bars <= got[1] <= 844 / 2) or got[2] != got[3]:
            bad.append((label, got, bars))
    check(not bad, f"sheet: each row closes the sheet, lands its heading below the bars in the top half, and the bar names it {bad[:3]}")
    pg.context.close()

    pg = ctx.phone(path)
    pg.evaluate("document.documentElement.classList.remove('acx-rv')")
    # K2 hero
    h1 = pg.evaluate("(e => { const cs = getComputedStyle(e); return [Math.round(e.getBoundingClientRect().height / parseFloat(cs.lineHeight)), parseFloat(cs.fontSize), cs.fontWeight, cs.letterSpacing]; })(document.querySelector('.acx-c-h1'))")
    check(h1[0] <= 4 and 28 <= h1[1] <= 30 and h1[2] == "700", f"hero: title 28-30px/700 in at most 4 lines [lines, px, weight, tracking] = {h1}")
    cnt = pg.evaluate("(b => [getComputedStyle(b).fontWeight, getComputedStyle(b).fontVariantNumeric])(document.querySelector('.acx-c-count-n b'))")
    check(cnt == ["600", "tabular-nums"], f"hero: countdown numbers 600, tabular {cnt}")
    acts = pg.evaluate("[...document.querySelectorAll('.acx-c-hero .acx-c-actions a')].map(a => Math.round(a.getBoundingClientRect().height))")
    check(acts and min(acts) >= 44, f"hero: actions at least 44px tall {acts}")
    titles = pg.evaluate("[...document.querySelectorAll('.acx-conf .acx-c-h2')].filter(e => e.getClientRects().length).map(e => getComputedStyle(e).fontSize + '/' + getComputedStyle(e).fontWeight)")
    check(set(titles) == {"28px/700"}, f"sections: titles 28px/700 {sorted(set(titles))}")

    # K3 tracks
    n = len(DATA["themes"]["items"])
    tr = pg.evaluate("[document.querySelectorAll('#tracks details.acx-c-tdet').length, document.querySelectorAll('#tracks details.acx-c-tdet[open]').length]")
    check(tr == [n, 0] and n == 4, f"tracks: {n} disclosure rows, all folded on phones [rows, open] = {tr}")
    opened = []
    for i in range(n):
        pg.tap(f"#tracks li:nth-child({i + 1}) summary"); pg.wait_for_timeout(150)
        opened.append(pg.evaluate("(li => [li.querySelector('details').open, [...li.querySelectorAll('.acx-c-topics li')].filter(x => x.getClientRects().length).length])(document.querySelectorAll('#tracks .acx-c-track')[%d])" % i))
    want = [[True, len(t["points"])] for t in DATA["themes"]["items"]]
    check(opened == want, f"tracks: each row opens to its topics {opened}")
    rowh = pg.evaluate("Math.min(...[...document.querySelectorAll('#tracks summary')].map(s => s.getBoundingClientRect().height))")
    check(rowh >= 52, f"tracks: rows at least 52px ({rowh:.0f}px)")

    # K4 programme
    seg = pg.evaluate("[...document.querySelectorAll('.acx-c-seg [role=tab]')].map(b => [b.textContent, b.getAttribute('aria-selected'), Math.round(b.getBoundingClientRect().height)])")
    vis = lambda: pg.evaluate("[document.getElementById('acx-day-1').getClientRects().length > 0, document.getElementById('acx-day-2').getClientRects().length > 0]")
    check(len(seg) == 2 and seg[0][1] == "true" and min(s[2] for s in seg) >= 44 and vis() == [True, False], f"programme: Day 1 / Day 2 control, Day 1 shown {seg} {vis()}")
    track = pg.evaluate("Math.round(document.querySelector('.acx-c-seg').getBoundingClientRect().height)")
    check(track == 36, f"programme: segmented track 36px inside a 44px hit area ({track}px)")
    counts = []
    for d in (1, 2):
        pg.tap(f".acx-c-seg [role=tab]:nth-child({d})"); pg.wait_for_timeout(150)
        counts.append([vis(), pg.evaluate("document.querySelectorAll('#acx-day-%d .acx-c-blk').length" % d),
                       pg.evaluate("Math.max(...[...document.querySelectorAll('#acx-day-%d .acx-c-blk')].map(b => b.getBoundingClientRect().height))" % d)])
    want = [len(d["items"]) for d in DATA["programme"]["days"]]
    check(counts[0][0] == [True, False] and counts[1][0] == [False, True], f"programme: tapping a segment shows that day only {[c[0] for c in counts]}")
    check([c[1] for c in counts] == want, f"programme: one row per session in the data {[c[1] for c in counts]} vs {want}")
    check(max(c[2] for c in counts) <= 140, f"programme: no row taller than 140px, no proportional heights ({max(c[2] for c in counts):.0f}px)")
    tsz = pg.evaluate("[...new Set([...document.querySelectorAll('.acx-c-t span:not(.acx-c-to)')].filter(e => e.getClientRects().length).map(e => Math.round(parseFloat(getComputedStyle(e).fontSize))))]")
    stz = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.acx-c-blk:not(.is-break) .acx-c-st')).fontSize)")
    check(all(13 <= x <= 15 for x in tsz) and stz == 17, f"programme: times 13-15px, titles 17px {tsz} {stz}")

    # K5 speakers and committee
    row = "document.querySelector('#speakers .acx-c-people:not(.acx-c-team)')"
    sp = pg.evaluate(f"(r => [r.scrollWidth > r.clientWidth, getComputedStyle(r).scrollSnapType, Math.round(r.querySelector('li').getBoundingClientRect().width), r.children.length])({row})")
    check(sp[0] and sp[1].startswith("x") and 240 <= sp[2] <= 280 and sp[3] == len(DATA["speakers"]["people"]), f"speakers: swipe row of ~260px cards, snapping, every speaker [scrolls, snap, width, count] = {sp}")
    pg.evaluate("document.getElementById('speakers').scrollIntoView()"); pg.wait_for_timeout(200)
    btn = pg.evaluate("[...document.querySelectorAll('.acx-c-swb')].map(b => getComputedStyle(b).visibility + ' ' + Math.round(b.getBoundingClientRect().width) + 'x' + Math.round(b.getBoundingClientRect().height))")
    check(btn == ["hidden 44x44", "visible 44x44"], f"speakers: only Next shows at the start, 44px {btn}")
    x0 = pg.evaluate(f"{row}.scrollLeft"); pg.tap(".acx-c-swb[data-dir='1']"); pg.wait_for_timeout(700)
    x1 = pg.evaluate(f"{row}.scrollLeft")
    check(x1 - x0 >= 200, f"speakers: Next scrolls the row by a card ({x0} -> {x1})")
    check(pg.evaluate("getComputedStyle(document.querySelector('.acx-c-swb[data-dir=\"-1\"]')).visibility") == "visible", "speakers: Previous appears once there is somewhere to go back to")
    pg.evaluate(f"{row}.scrollLeft = 1e5"); pg.wait_for_timeout(300)
    check(pg.evaluate("getComputedStyle(document.querySelector('.acx-c-swb[data-dir=\"1\"]')).visibility") == "hidden", "speakers: Next hides at the end")
    nm = pg.evaluate("(e => [Math.round(parseFloat(getComputedStyle(e).fontSize)), getComputedStyle(e).fontWeight, Math.round(parseFloat(getComputedStyle(e.nextElementSibling).fontSize))])(document.querySelector('#speakers .acx-c-pn'))")
    check(nm == [17, "600", 15], f"speakers: name 17/600, role and org 15px {nm}")
    team = pg.evaluate("""[...document.querySelectorAll('.acx-c-team > li')].map(li => { const i = li.querySelector('img').getBoundingClientRect();
        return [Math.round(li.getBoundingClientRect().height), Math.round(i.width), Math.round(i.height)]; })""")
    check(len(team) == len(DATA["committee"]["people"]) and all(h >= 56 and w == 56 and ih == 56 for h, w, ih in team), f"committee: list rows at least 56px with a 56px photo {team[:3]}")

    # K6 call for proposals
    kd = pg.evaluate("""(k => { const cs = getComputedStyle(k); return [cs.backgroundImage, cs.backgroundColor, cs.paddingTop,
        [...k.querySelectorAll('*')].filter(e => getComputedStyle(e).backdropFilter !== 'none').length]; })(document.querySelector('.acx-c-kd'))""")
    check(kd == ["none", "rgba(0, 0, 0, 0)", "0px", 0], f"key dates: no outer glass frame around the cards [image, colour, padding, blurred] = {kd}")
    steps = pg.evaluate("[document.querySelectorAll('.acx-c-dates [data-date]').length, (d => d.getBoundingClientRect().top > document.querySelector('.acx-c-kd-next').getBoundingClientRect().bottom)(document.querySelector('.acx-c-dates'))]")
    check(steps == [4, True], f"key dates: the next-deadline card, then 4 steps [steps, below] = {steps}")
    specs = pg.evaluate("""[...document.querySelectorAll('.acx-c-specg dl > div')].map(d => { const t = d.querySelector('dt').getBoundingClientRect(), v = d.querySelector('dd').getBoundingClientRect(), r = d.getBoundingClientRect();
        return [Math.round(t.left - r.left), Math.round(r.right - v.right), Math.abs(t.top - v.top) < 4]; })""")
    nspec = sum(len(g["items"]) for g in DATA["cfp"]["specs"])
    check(len(specs) == nspec and all(a == 16 and b == 16 and same for a, b, same in specs), f"specs: {nspec} grouped rows, label left and value right {specs[:3]}")
    parts = pg.evaluate("document.querySelectorAll('.acx-c-parts > li').length")
    check(parts == len(DATA["cfp"]["parts"]), f"proposal: {parts} numbered parts")
    dlh = pg.evaluate("[...document.querySelectorAll('.acx-c-dl')].map(a => [Math.round(a.getBoundingClientRect().width), Math.round(a.getBoundingClientRect().height)])")
    check(all(w == 358 and h >= 52 for w, h in dlh), f"downloads: full-width rows at least 52px {dlh}")

    # K7 fees
    fees = pg.evaluate("""(() => { const p = [...document.querySelectorAll('.acx-c-plan')].sort((a, b) => a.getBoundingClientRect().top - b.getBoundingClientRect().top);
        const hi = document.querySelector('.acx-c-plan.is-hi'), b = hi.querySelector('.acx-c-plan-badge').getBoundingClientRect(), c = hi.getBoundingClientRect();
        return [p[0] === hi, b.top >= c.top && b.right <= c.right, document.querySelectorAll('.acx-c-plan .acx-btn-light').length]; })()""")
    check(fees == [True, True, 1], f"fees: the presenter rate first, its badge inside the card, one filled button {fees}")

    # K8 logos
    logos = pg.evaluate("""(() => { const im = [...document.querySelectorAll('.acx-c-logos img')].filter(i => i.getClientRects().length);
        return [im.length, new Set(im.map(i => i.getAttribute('src'))).size, new Set(im.map(i => Math.round(i.closest('li').getBoundingClientRect().left))).size,
                getComputedStyle(document.querySelector('.acx-c-mtrack')).animationName, document.documentElement.scrollWidth]; })()""")
    check(logos[:2] == [len(DATA["logos"])] * 2 and logos[2] == 3 and logos[3] == "none", f"members: a still 3-column grid, every logo once [shown, unique, columns, animation, width] = {logos}")

    # K9 sponsorship and contact
    mk = pg.evaluate("getComputedStyle(document.querySelector('#sponsorship .acx-c-list')).listStyleType")
    check(mk == "disc", f"sponsorship: the list has markers ({mk})")
    con = pg.evaluate("[...document.querySelectorAll('.acx-c-contact > div')].map(d => [Math.round(d.getBoundingClientRect().height), (a => a ? Math.round(a.getBoundingClientRect().height) : null)(d.querySelector('a'))])")
    check(len(con) == 4 and all(h >= 44 and (a is None or a >= 44) for h, a in con), f"contact: grouped rows and links at least 44px {con}")

    # Whole page
    small = pg.evaluate(SMALL_TARGETS, ".acx-conf *")
    check(not small, f"conference: targets at least 44px {small[:4]}")
    tiny = pg.evaluate(SMALL_TEXT, ".acx-conf *")
    check(not tiny, f"conference: text at least 13px {tiny[:4]}")
    font = pg.evaluate(WRONG_FONT, ".acx-conf *")
    check(not font, f"conference: Inter only {font[:4]}")
    low = pg.evaluate(CONTRAST, ".acx-conf *")
    check(not low, f"conference: text contrast AA {low[:3]}")
    pg.evaluate("document.documentElement.style.scrollBehavior = 'auto'")   # the theme scrolls smoothly; measure where each heading comes to rest
    under = pg.evaluate(UNDER_BARS, ".acx-conf .acx-c-h2")
    check(not under, f"conference: section headings scroll clear of the top bar {under[:3]}")
    clear = pg.evaluate("""[...document.querySelectorAll('.acx-conf [id] > .acx-c-in > .acx-c-head .acx-c-h2, .acx-conf h2[id]')].filter(e => e.getClientRects().length).filter(e => {
        const t = e.closest('[id]'); location.hash = ''; t.scrollIntoView({block: 'start', behavior: 'instant'});
        return e.getBoundingClientRect().top < document.querySelector('.acx-local').getBoundingClientRect().bottom; }).map(e => e.textContent.slice(0, 24))""")
    check(not clear, f"conference: anchored sections land below the section bar too {clear[:3]}")
    last = pg.evaluate("(() => { scrollTo(0, 1e7); const r = document.querySelector('.acx-conf').getBoundingClientRect(); return [Math.round(r.bottom), Math.round(document.querySelector('.acx-m-tabs').getBoundingClientRect().top)]; })()")
    check(last[0] <= last[1], f"conference: the last section clears the tab bar {last}")
    pg.context.close()

    # Narrow phones, reduced motion, no JavaScript
    pg = ctx.phone(path, reduced_motion="reduce")
    pg.set_viewport_size({"width": 320, "height": 640}); pg.wait_for_timeout(300)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    lab = pg.evaluate("(b => [Math.round(b.getBoundingClientRect().width), b.scrollWidth <= b.clientWidth + 1])(document.querySelector('.acx-local-cur b'))")
    check(sw == 320 and lab[0] >= 90, f"320px: no sideways scroll ({sw}px), the bar still names the section {lab}")
    small = pg.evaluate(SMALL_TARGETS, ".acx-conf *")
    check(not small, f"320px: targets at least 44px {small[:4]}")
    check(pg.evaluate("getComputedStyle(document.querySelector('.acx-c-mtrack')).animationName") == "none", "reduced motion: logos hold still")
    pg.context.close()

    pg = ctx.phone(path + "#acx-secs", java_script_enabled=False)
    rows = pg.evaluate("[...document.querySelectorAll('#acx-secs .acx-m-row')].filter(a => a.getClientRects().length).length")
    check(rows == len(SHEET), f"no JS: Sections opens the sheet through #acx-secs with every row ({rows})")
    tr = pg.evaluate("[document.querySelectorAll('#tracks details[open]').length, document.getElementById('acx-day-2').getClientRects().length > 0, !!document.querySelector('.acx-c-seg:not([hidden])')]")
    check(tr == [4, True, False], f"no JS: tracks open, both days listed, no dead day control {tr}")
    check(not pg.is_visible(".acx-c-swnav"), "no JS: no dead previous/next buttons")
    pg.context.close()


SECTIONS = {"conference": conference}
