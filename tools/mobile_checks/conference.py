"""Leaf 1.5: the conference page on phones (actlc-assets/conference.css under 760px, conference.js, tools/conference_page.py).
Counts come from tools/conference.json, the same data the page is built from."""
import json, os
from . import CONTRAST, SMALL_TARGETS, SMALL_TEXT, WRONG_FONT, UNDER_BARS

DATA = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "conference.json"), encoding="utf-8"))
SHEET = ["Overview", "About", "Tracks", "Programme", "Speakers", "Organising committee", "Call for proposals", "Fees",
         "Founding members", "Sponsorship", "Contact"]
LEFT = "(s => Math.round(document.querySelector(s).getBoundingClientRect().left))"
BARS = "Math.round(document.querySelector('.acx-local').getBoundingClientRect().bottom)"


def touch(pg, sel):
    """Tap where the element is, like a finger; Playwright's tap() first scrolls the target into view."""
    bb = pg.query_selector(sel).bounding_box(); pg.touchscreen.tap(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] / 2)

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
    solid = pg.evaluate("(cs => [cs.backgroundColor, cs.backdropFilter])(getComputedStyle(document.querySelector('.acx-local')))")
    check(solid == ["rgb(255, 255, 255)", "none"], f"section bar: solid white, nothing shows through over the dark bands {solid}")
    # reading down slides the site top bar away (mobile.js) and the section bar moves up into the space; scrolling up brings both back
    pg.evaluate("scrollTo({top: 1600, behavior: 'instant'})"); pg.wait_for_timeout(120)
    pg.evaluate("scrollTo({top: 2000, behavior: 'instant'})"); pg.wait_for_timeout(450)
    up = pg.evaluate("Math.round(document.querySelector('.acx-local').getBoundingClientRect().top)")
    pg.evaluate("scrollTo({top: 1900, behavior: 'instant'})"); pg.wait_for_timeout(450)
    back = pg.evaluate("Math.round(document.querySelector('.acx-local').getBoundingClientRect().top)")
    pg.evaluate("scrollTo({top: 0, behavior: 'instant'})"); pg.wait_for_timeout(400)
    check(up == 0 and back == top, f"section bar: moves to the top while the top bar is slid away ({up}px) and back under it on scroll up ({back}px)")

    # One rhythm: 32px between sections (to a dark band's edge, then 32px inside it), 8px from a title to its content
    rhythm = pg.evaluate("""(() => { const R = e => e.getBoundingClientRect(), vis = e => e.getClientRects().length && R(e).height > 0 && getComputedStyle(e).visibility !== 'hidden';
        const secs = [...document.querySelectorAll('.acx-conf > header, .acx-conf > section')], out = [];
        const box = s => s.matches('.acx-c-band, .acx-c-hero') ? R(s).bottom : Math.max(...[...s.querySelectorAll('*')].filter(e => vis(e) && !e.closest('details:not([open]) > :not(summary)')).map(e => R(e).bottom));
        for (let i = 1; i < secs.length; i++) { const s = secs[i], t = s.querySelector('h2'), band = s.matches('.acx-c-band');
            const gap = Math.round((band ? R(s).top : R(t).top) - box(secs[i - 1]));
            const inner = band ? Math.round(R(t).top - R(s).top) : 32;
            const head = t.closest('.acx-c-head'), last = head ? (head.querySelector('.acx-c-lead') || t) : t;
            let nx = head ? head.nextElementSibling : t.nextElementSibling || t.parentElement.nextElementSibling; while (nx && !vis(nx)) nx = nx.nextElementSibling;
            const sub = nx && nx.matches('h3');   // a sub-heading right after the lead starts a block: 24px
            out.push([s.id, gap, inner, nx ? Math.round(R(nx).top - R(last).bottom) - (sub ? 16 : 0) : 8]); }
        return out; })()""")
    off = [r for r in rhythm if r[1:] != [32, 32, 8]]
    check(not off, f"rhythm: 32px between sections, 8px from title to content [id, gap, band inset, title->content] {off or rhythm[:3]}")
    check(not pg.is_visible(".acx-local-links") and pg.is_visible(".acx-local-sheet") and pg.is_visible(".acx-local .acx-btn"),
          "section bar: the clipped chip strip gives way to a Sections button and Register")
    cur = lambda: pg.evaluate("document.querySelector('.acx-local-cur b').textContent")
    check(cur() == "Overview", f"section bar: names the section on screen at the top ({cur()!r})")
    pg.evaluate("scrollTo({top: document.getElementById('programme').getBoundingClientRect().top + scrollY - 100, behavior: 'instant'})"); pg.wait_for_timeout(300)
    check(cur() == "Programme", f"section bar: the name follows the scroll ({cur()!r} at the programme)")
    touch(pg, ".acx-local-sheet"); pg.wait_for_timeout(400)
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
        touch(pg, ".acx-local-sheet"); pg.wait_for_timeout(350)
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
    brk = pg.evaluate("""(() => { const s = document.querySelector('.acx-c-blk:not(.is-break) .acx-c-t span'), b = document.querySelector('.acx-c-blk.is-break .acx-c-t span');
        const m = getComputedStyle(document.querySelector('.acx-conf')).getPropertyValue('--muted').trim();
        return [getComputedStyle(s).fontSize === getComputedStyle(b).fontSize, getComputedStyle(b).color]; })()""")
    check(brk == [True, "rgb(82, 98, 106)"], f"programme: break times the same size as session times, in the muted colour {brk}")
    dayh = pg.evaluate("[...document.querySelectorAll('.acx-c-dayh')].filter(e => e.getClientRects().length).length + ' ' + [...document.querySelectorAll('.acx-c-dayv')].filter(e => e.getClientRects().length).length")
    check(dayh == "0 1", f"programme: no day heading repeating the selected segment, the venue line stays [headings, venue lines] = {dayh}")

    # K5 speakers and committee
    row = "document.querySelector('#speakers .acx-c-people:not(.acx-c-team)')"
    sp = pg.evaluate(f"(r => [r.scrollWidth > r.clientWidth, getComputedStyle(r).scrollSnapType, Math.round(r.querySelector('li').getBoundingClientRect().width), r.children.length])({row})")
    check(sp[0] and sp[1].startswith("x") and 240 <= sp[2] <= 280 and sp[3] == len(DATA["speakers"]["people"]), f"speakers: swipe row of ~260px cards, snapping, every speaker [scrolls, snap, width, count] = {sp}")
    pg.evaluate("document.getElementById('speakers').scrollIntoView()"); pg.wait_for_timeout(200)
    btn = pg.evaluate("[...document.querySelectorAll('.acx-c-swb')].map(b => getComputedStyle(b).visibility + ' ' + Math.round(b.getBoundingClientRect().width) + 'x' + Math.round(b.getBoundingClientRect().height))")
    btn = pg.evaluate("""[...document.querySelectorAll('.acx-c-swb')].map(b => { const r = b.getBoundingClientRect(), h = document.getElementById('acx-h-spk').getBoundingClientRect();
        return [getComputedStyle(b).visibility, b.disabled, Math.round(r.width) + 'x' + Math.round(r.height), Math.abs((r.top + r.bottom) / 2 - (h.top + h.bottom) / 2) < 2, Math.round(r.right)]; })""")
    check([b[:4] for b in btn] == [["visible", True, "44x44", True], ["visible", False, "44x44", True]] and btn[1][4] == 374,
          f"speakers: previous / next as a pair on the title row, right, 44px; Previous greyed at the start {btn}")
    gaps = pg.evaluate(f"""(r => {{ const cards = Math.max(...[...r.children].map(c => c.getBoundingClientRect().bottom)), t = document.getElementById('acx-h-team').getBoundingClientRect().top;
        return [Math.round(r.getBoundingClientRect().bottom - cards), Math.round(t - cards), new Set([...r.children].map(c => Math.round(c.getBoundingClientRect().height))).size]; }})({row})""")
    tails = pg.evaluate(f"""(r => [...r.children].map(c => {{ const cap = c.querySelector('.acx-c-cap'); return cap ? Math.round(c.getBoundingClientRect().bottom - cap.getBoundingClientRect().bottom) : 0 }}).filter(v => v > 24))({row})""")
    check(gaps[0] <= 2 and gaps[1] == 32 and not tails, f"speakers: the row is as tall as its tallest card, each card ends with its text (no blank tail), 32px to the committee [row-cards, to title] = {gaps[:2]} tails {tails}")
    x0 = pg.evaluate(f"{row}.scrollLeft"); pg.tap(".acx-c-swb[data-dir='1']"); pg.wait_for_timeout(700)
    x1 = pg.evaluate(f"{row}.scrollLeft")
    check(x1 - x0 >= 200, f"speakers: Next scrolls the row by a card ({x0} -> {x1})")
    check(pg.evaluate("getComputedStyle(document.querySelector('.acx-c-swb[data-dir=\"-1\"]')).visibility") == "visible", "speakers: Previous appears once there is somewhere to go back to")
    pg.evaluate(f"{row}.scrollLeft = 1e5"); pg.wait_for_timeout(300)
    end = pg.evaluate("[...document.querySelectorAll('.acx-c-swb')].map(b => getComputedStyle(b).visibility + ' ' + b.disabled)")
    check(end == ["visible false", "visible true"], f"speakers: at the end Next is greyed and Previous works {end}")
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
    rel = pg.evaluate("[...document.querySelectorAll('.acx-c-dates [data-date]')].map(li => (li.classList.contains('is-next') ? 'next' : li.classList.contains('is-goal') ? 'goal' : 'step') + ':' + (li.querySelector('.acx-c-rel').getClientRects().length > 0))")
    check(rel and all(r.endswith(":false") for r in rel if not r.startswith("step")) and any(r.startswith("next") for r in rel) and any(r == "step:true" for r in rel),
          f"key dates: no 'in N days' on the next step (the card says it) or on the opening (the hero countdown says it) {rel}")
    hint = pg.evaluate("getComputedStyle(document.querySelector('.acx-c-hint')).textAlign")
    check(hint in ("left", "start"), f"proposal: the subject hint is left-aligned ({hint})")
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
    reg = pg.evaluate("document.querySelector('.acx-local .acx-btn').href")
    plans = pg.evaluate("""[...document.querySelectorAll('.acx-c-plan .acx-btn')].map(a => { const cs = getComputedStyle(a), r = a.getBoundingClientRect();
        return [a.closest('.is-hi') ? 'hi' : 'other', cs.backgroundColor, Math.round(r.height), a.href, a.textContent.trim()]; })""")
    ok = all((p[1] == "rgb(255, 255, 255)" if p[0] == "hi" else p[1] == "rgba(0, 0, 0, 0)") and p[2] >= 44 and p[3] == reg and p[4] == "Register" for p in plans)
    check(len(plans) == 3 and ok, f"fees: only the presenter card has a filled button; the others end in a quiet 44px 'Register' link to the same page {[p[:3] for p in plans]}")
    filled = pg.evaluate("""[...document.querySelectorAll('.acx-conf .acx-btn')].filter(a => a.getClientRects().length && getComputedStyle(a).backgroundColor !== 'rgba(0, 0, 0, 0)')
        .map(a => (a.closest('.acx-c-band, .acx-c-hero') ? 'dark ' : 'light ') + getComputedStyle(a).backgroundColor + ' ' + getComputedStyle(a).color)""")
    want = {"light rgb(14, 122, 131) rgb(255, 255, 255)", "dark rgb(255, 255, 255) rgb(11, 97, 106)"}
    check(filled and set(filled) <= want, f"buttons: teal with white text on light ground, white with teal text on the dark bands {sorted(set(filled))}")
    # a button must stand out from the ground behind it (WCAG 1.4.11 non-text contrast >= 3:1)
    weak = pg.evaluate("""(() => { const rgb = c => c.match(/[\\d.]+/g).slice(0, 3).map(Number);
        const L = c => { const f = v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4) }; const [r, g, b] = rgb(c); return .2126 * f(r) + .7152 * f(g) + .0722 * f(b) };
        const ground = el => { for (let e = el.parentElement; e; e = e.parentElement) { const cs = getComputedStyle(e), g = cs.backgroundImage.match(/rgba?\\([^)]+\\)/);
          if (g) return g[0]; const c = cs.backgroundColor, a = (c.match(/[\\d.]+/g) || [])[3]; if (c !== 'rgba(0, 0, 0, 0)' && (a === undefined || +a > .5)) return c } return 'rgb(255, 255, 255)' };   // skip see-through tints   // a gradient ground counts by its first colour
        return [...document.querySelectorAll('.acx-conf .acx-btn')].filter(a => a.getClientRects().length && getComputedStyle(a).backgroundColor !== 'rgba(0, 0, 0, 0)')
          .map(a => { const x = L(getComputedStyle(a).backgroundColor), y = L(ground(a)); return [a.textContent.trim().slice(0, 16), +((Math.max(x, y) + .05) / (Math.min(x, y) + .05)).toFixed(2)] }).filter(p => p[1] < 3) })()""")
    check(not weak, f"buttons: every filled button stands out from its ground by at least 3:1 {weak}")
    regs = pg.evaluate("[...document.querySelectorAll('.acx-conf .acx-btn')].filter(a => a.getClientRects().length && a.textContent.trim() === 'Register' && getComputedStyle(a).backgroundColor !== 'rgba(0, 0, 0, 0)').length")
    check(regs == 3, f"buttons: three filled Register buttons on the page (section bar, hero, presenter card), not five ({regs})")

    # K8 logos
    logos = pg.evaluate("""(() => { const im = [...document.querySelectorAll('.acx-c-logos img')].filter(i => i.getClientRects().length);
        return [im.length, new Set(im.map(i => i.getAttribute('src'))).size, new Set(im.map(i => Math.round(i.closest('li').getBoundingClientRect().left))).size,
                getComputedStyle(document.querySelector('.acx-c-mtrack')).animationName, document.documentElement.scrollWidth]; })()""")
    check(logos[:2] == [len(DATA["logos"])] * 2 and logos[2] == 2 and logos[3] == "none", f"members: a still 2-column grid, every logo once [shown, unique, columns, animation, width] = {logos}")
    pg.evaluate("document.getElementById('members').scrollIntoView()")
    pg.wait_for_function("[...document.querySelectorAll('.acx-c-logos:not([aria-hidden]) img')].every(i => i.complete && i.naturalWidth)", timeout=15000)
    tiles = pg.evaluate("""(() => { const li = [...document.querySelectorAll('.acx-c-logos:not([aria-hidden]) li')], r = e => e.getBoundingClientRect();
        return [Math.round(r(li[0]).left), Math.round(r(li[li.length - 1]).left), li.length % 2, Math.min(...li.map(l => Math.round(r(l).width))),
                Math.min(...li.map(l => Math.round(r(l.querySelector('img')).height))), getComputedStyle(li[0]).backgroundColor]; })()""")
    check(tiles[0] == 16 and (tiles[2] == 0 or tiles[1] == 16) and tiles[3] >= 160 and tiles[4] >= 20 and tiles[5] == "rgb(255, 255, 255)",
          f"members: white tiles at least 160px wide, logos at least 20px tall, an odd last tile sits left [first, last left, odd, tile w, min logo h, bg] = {tiles}")

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
    foot = pg.evaluate("""[[...document.querySelectorAll('.acx-footer a[href^="mailto:"], .acx-footer a[href^="tel:"]')].filter(a => a.getClientRects().length).length,
        (p => !!p && p.getClientRects().length > 0 && /Copyright/.test(p.textContent))(document.querySelector('.acx-footer .acx-foot-bottom p'))]""")
    check(foot == [0, True], f"footer: no second copy of the contact email and phone on this page, the copyright stays {foot}")
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
