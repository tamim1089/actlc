"""Leaf 1.3 / 2.3: the home page on phones (tools/home_mobile.py, actlc-assets/mobile-home.css).
Every count is read from the legacy markup on the same page, so the check follows the page when it is edited."""
from . import CONTRAST, SMALL_TARGETS, SMALL_TEXT, WRONG_FONT, UNDER_BARS

BLOCKS = ["hero", "objectives", "mission", "board", "founding", "faq"]
# legacy widgets that the phone blocks replace (each must be hidden on phones and shown on desktop)
LEGACY = {"hero": "#n2-ss-2", "objectives": "#n2-ss-4", "mission": ".elementor-element-5e398a3", "values": ".elementor-element-4414361",
          "roles": ".elementor-element-b0b1572", "logos": ".elementor-element-600ad7a", "board": ".director",
          "faq": ".elementor-element-635f609"}
ORDER = [".acx-mh-hero", ".elementor-element-a36dfb9", ".acx-mh-objectives", ".acx-mh-mission", ".acx-mh-board", ".acx-mh-founding", ".acx-mh-faq"]
VISIBLE = "(s) => [...document.querySelectorAll(s)].filter(e => e.getClientRects().length && getComputedStyle(e).visibility !== 'hidden').length"
TEXTS = "(s) => [...document.querySelectorAll(s)].map(e => e.textContent.replace(/\\s+/g, ' ').trim())"
UNIQUE_SRC = "(s) => new Set([...document.querySelectorAll(s)].map(i => (i.getAttribute('src') || '').replace(/\\?.*$/, ''))).size"
MINE = ".acx-mh *:not(.acx-mh-ans a)"      # inline links inside answer text are exempt from the 44px rule (WCAG 2.5.8)
EV_TITLE = ".elementor-element-72ac8a3 .elementor-heading-title"
# Section rhythm. Each entry: (title, the first content under it, the end of that section's content).
# The end is the lowest visible box inside the section that paints something (text, image or a filled background).
RHYTHM = [(EV_TITLE, ".acx-home-root", ".elementor-element-a36dfb9"),
          ("#acx-mh-obj-t", ".acx-mh-objs", ".acx-mh-objectives"),
          ("#acx-mh-mv-t", ".acx-mh-seg-l", ".acx-mh-sheet"),
          ("#acx-mh-val-t", ".acx-mh-vals", ".acx-mh-mission"),
          ("#acx-mh-bd-t", ".acx-mh-board .acx-mh-lead", ".acx-mh-board"),
          ("#acx-mh-fm-t", ".acx-mh-founding .acx-mh-lead", ".acx-mh-founding"),
          ("#acx-mh-faq-t", ".acx-mh-faqs", ".acx-mh-faq")]
INK_BOTTOM = """(s) => { const root = document.querySelector(s); let b = 0;
  const ground = getComputedStyle(document.querySelector('.acx-mh')).backgroundColor;
  for (const e of [root, ...root.querySelectorAll('*')]) {
    const r = e.getBoundingClientRect(); if (!r.height || !e.getClientRects().length) continue;
    const cs = getComputedStyle(e); if (cs.visibility === 'hidden') continue;
    const d = e.closest('details'); if (d && !d.open && !e.closest('summary')) continue;     // closed rows keep a box for their text
    const bg = cs.backgroundColor, paints = e.tagName === 'IMG' || (!e.children.length && e.textContent.trim())
      || (bg !== 'rgba(0, 0, 0, 0)' && bg !== ground);
    let bot = r.bottom;                                       // clipped by an ancestor that hides overflow (the logo tiles)
    for (let a = e.parentElement; a && a !== root.parentElement; a = a.parentElement)
      if (getComputedStyle(a).overflow !== 'visible') bot = Math.min(bot, a.getBoundingClientRect().bottom);
    if (paints) b = Math.max(b, bot + scrollY);
  } return Math.round(b) }"""
BOX = "(s) => { const r = document.querySelector(s).getBoundingClientRect(); return [Math.round(r.top + scrollY), Math.round(r.bottom + scrollY)] }"


def _top(pg, sel):
    return pg.evaluate("(s) => { const e = document.querySelector(s); return e ? Math.round(e.getBoundingClientRect().top + scrollY) : null }", sel)


def home(ctx):
    check, path = ctx.check, ctx.PAGES["home"]
    print("\n== Home on phones (390x844) ==")
    pg = ctx.phone(path)
    pg.evaluate("document.documentElement.classList.remove('acx-rv')")
    sw = pg.evaluate("document.documentElement.scrollWidth")
    check(sw == 390, f"home: no sideways scroll ({sw}px)")
    for b in BLOCKS:
        check(pg.evaluate(VISIBLE, f".acx-mh-{b}") == 1, f"home: the phone {b} block shows")
    for name, sel in LEGACY.items():
        n = pg.evaluate(VISIBLE, sel)
        check(n == 0, f"home: legacy {name} ({sel}) hidden on phones ({n} visible)")
    for sel in (".elementor-element-6722f73", ".elementor-element-977cad5", ".elementor-element-c6deef7", ".elementor-element-80ff783", ".elementor-element-d86410b"):
        check(pg.evaluate(VISIBLE, sel) == 0, f"home: decorative section icon {sel} hidden")
    tops = [_top(pg, s) for s in ORDER]
    check(None not in tops and tops == sorted(tops), f"home: phone order hero, events, objectives, mission & values, board, founding, FAQ {tops}")
    check(pg.evaluate(VISIBLE, ".acx-mh-swipe, .acx-mh-track, .acx-mh-nav") == 0, "home: no swipe rows left on the home page")

    # hero: compact, plain gradient, the first event on the first screen
    bar = pg.evaluate("Math.round(document.querySelector('.acx-m-top').getBoundingClientRect().bottom)")
    tabs_top = pg.evaluate("Math.round(document.querySelector('.acx-m-tabs').getBoundingClientRect().top)")
    hr = pg.evaluate("(r => [Math.round(r.top), Math.round(r.height)])(document.querySelector('.acx-mh-hero').getBoundingClientRect())")
    check(hr[0] >= bar - 1, f"hero: starts below the top bar (hero top {hr[0]}px, bar bottom {bar}px)")
    check(pg.evaluate("document.querySelectorAll('.acx-mh-hero img').length") == 0 and
          "gradient" in pg.evaluate("getComputedStyle(document.querySelector('.acx-mh-hero')).backgroundImage"),
          "hero: no backdrop picture, a plain teal gradient")
    h1 = pg.evaluate("(e => { const cs = getComputedStyle(e); return [parseFloat(cs.fontSize), Math.round(e.getBoundingClientRect().height / parseFloat(cs.lineHeight))] })(document.querySelector('.acx-mh-hero-t'))")
    check(h1[0] == 28 and h1[1] <= 3, f"hero: headline 28px on at most 3 lines ({h1[0]}px, {h1[1]} lines)")
    sub = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.acx-mh-hero-sub')).fontSize)")
    check(abs(sub - 17) < 0.2, f"hero: subline 17px ({sub})")
    acts = pg.evaluate("[...document.querySelectorAll('.acx-mh-hero-act a')].map(a => { const r = a.getBoundingClientRect(); return [a.textContent.trim(), a.getAttribute('href'), Math.round(r.height), Math.round(r.top), Math.round(r.width)] })")
    check(len(acts) == 2 and acts[0][1] == "events/index.html" and acts[1][1] == "conference/index.html" and all(a[2] >= 44 for a in acts),
          f"hero: two actions, webinars then conference, each at least 44px {acts}")
    check(len(acts) == 2 and acts[0][3] == acts[1][3] and abs(acts[0][4] - acts[1][4]) <= 1, f"hero: at 390px the two actions sit side by side, equal width {acts}")
    ev_t = pg.evaluate(f"Math.round(document.querySelector('{EV_TITLE}').getBoundingClientRect().bottom)")
    ev1 = pg.evaluate("Math.round(document.querySelector('.acx-home-root .acx-ev').getBoundingClientRect().top)")
    check(ev_t <= tabs_top and ev1 + 40 <= tabs_top,
          f"hero: 'Upcoming Events' and the top of the first event show on the first screen (title ends {ev_t}px, first row {ev1}px, tab bar {tabs_top}px)")

    # one rhythm: 32px between sections, 8px from a title to its content
    prev_end = pg.evaluate(BOX, ".acx-mh-hero")[1]
    for t, first, end in RHYTHM:
        tt, tb = pg.evaluate(BOX, t)
        ft = pg.evaluate(BOX, first)[0]
        check(abs(tt - prev_end - 32) <= 1, f"rhythm: {t} sits 32px below the section above ({tt - prev_end}px)")
        check(abs(ft - tb - 8) <= 1, f"rhythm: {t} to its content is 8px ({ft - tb}px)")
        prev_end = pg.evaluate(INK_BOTTOM, end)
        box_end = pg.evaluate(BOX, end)[1]
        if end != ".acx-mh-faq":
            check(box_end - prev_end <= 1, f"rhythm: no blank space at the end of {end} ({box_end - prev_end}px)")

    # surfaces: borderless white on the grey ground
    deco = pg.evaluate("""[...document.querySelectorAll('.acx-mh-sheet, .acx-mh-logo, .acx-mh .acx-m-group, .acx-mh .acx-m-group > li')]
        .filter(e => { const cs = getComputedStyle(e); return cs.boxShadow !== 'none' || parseFloat(cs.borderTopWidth) || parseFloat(cs.borderLeftWidth) })
        .map(e => e.className || e.tagName).slice(0, 4)""")
    check(not deco, f"surfaces: no borders or shadows on content cards {deco}")

    # counts against the legacy markup on the same page
    legacy_board = pg.evaluate(TEXTS, ".director .elementor-image-box-title")
    board = pg.evaluate(TEXTS, ".acx-mh-people .acx-mh-name")
    check(len(board) == 7 and board == legacy_board, f"board: {len(board)} people in the page's order {board}")
    ph = pg.evaluate("[...document.querySelectorAll('.acx-mh-people > li')].map(li => { const i = li.querySelector('.acx-mh-ph'); const r = i.getBoundingClientRect();"
                     " return [Math.round(r.width), Math.round(r.height), getComputedStyle(i).borderRadius] })")
    check(len(ph) == 7 and all(p[0] == 72 and p[1] == 90 and p[2] == "14px" for p in ph), f"board: list rows with a 72x90 portrait photo {ph[:2]}")
    sizes = pg.evaluate("[...document.querySelectorAll('.acx-mh-name, .acx-mh-role-t, .acx-mh-org')].map(e => [e.className, parseFloat(getComputedStyle(e).fontSize), getComputedStyle(e).fontWeight])")
    check(all((c == "acx-mh-name" and abs(s - 17) < .2 and w == "600") or (c != "acx-mh-name" and abs(s - 15) < .2) for c, s, w in sizes),
          "board: name 17px/600, role and organisation 15px")
    check(pg.evaluate("!!document.querySelector('.acx-mh-board .acx-mh-lead') && document.querySelector('.acx-mh-board .acx-mh-lead').textContent.length > 100"),
          "board: the intro paragraph stays")
    nfaq = pg.evaluate("document.querySelectorAll('.elementor-element-635f609 .elementor-toggle-item').length")
    qs = pg.evaluate(TEXTS, ".acx-mh-faqs .acx-mh-qa summary")
    lq = [q.split(". ", 1)[-1] for q in pg.evaluate(TEXTS, ".elementor-element-635f609 .elementor-toggle-title")]
    check(nfaq == 11 and qs == lq, f"FAQ: {len(qs)} questions, same text and order as the toggle ({nfaq})")
    nroles = pg.evaluate("document.querySelectorAll('.elementor-element-b0b1572 .elementor-image-box-description').length")
    roles = pg.evaluate("document.querySelectorAll('.acx-mh-roles > li').length")
    check(roles == nroles == 6, f"founding: {roles} roles (legacy {nroles})")
    check(pg.evaluate("document.querySelectorAll('.acx-mh-roles img, .acx-mh-roles svg').length") == 0, "founding: no line-art icons beside the roles")
    rw = pg.evaluate("[...document.querySelectorAll('.acx-mh-role p')].map(p => Math.round(p.getBoundingClientRect().width))")
    gw = pg.evaluate("Math.round(document.querySelector('.acx-mh-roles').getBoundingClientRect().width)")
    check(rw and all(w >= gw - 32 - 1 for w in rw), f"founding: role text uses the full row width ({rw[:2]} of {gw})")
    # the live carousel adds loop clones and reorders slides; "N of 5" labels keep the authored order
    lv = pg.evaluate("""[...new Map([...document.querySelectorAll('.elementor-element-4414361 .swiper-slide')]
        .map(s => [s.querySelector('.elementor-icon-box-title').textContent.replace(/\\s+/g, ' ').trim(), parseInt(s.getAttribute('aria-label'))])
        .sort((a, b) => a[1] - b[1])).keys()]""")
    vals = pg.evaluate(TEXTS, ".acx-mh-vals summary")
    check(len(vals) == 5 and vals == lv, f"values: {len(vals)} disclosure rows in order {vals}")
    nobj = pg.evaluate("document.querySelectorAll('#n2-ss-4 .n2-ss-slide[data-slide-public-id]').length")
    obj = pg.evaluate("document.querySelectorAll('.acx-mh-objs > li > details').length")
    check(obj == nobj == 6, f"objectives: {obj} disclosure rows (slider has {nobj} slides)")
    pts = pg.evaluate("[...document.querySelectorAll('.acx-mh-objs details')].map(d => d.querySelectorAll('.acx-mh-points li').length)")
    check(all(p > 0 for p in pts), f"objectives: each keeps its bullet list {pts}")
    nlogo = pg.evaluate(UNIQUE_SRC, ".elementor-element-600ad7a img")
    logos = pg.evaluate("document.querySelectorAll('.acx-mh-logos img').length")
    check(logos == nlogo and logos > 0, f"founding: {logos} member logos (legacy carousel has {nlogo} unique)")
    grid = pg.evaluate("""(() => { const g = document.querySelector('.acx-mh-logos').getBoundingClientRect();
        return [...document.querySelectorAll('.acx-mh-logo')].map(l => { const r = l.getBoundingClientRect(); return [Math.round(r.left - g.left), Math.round(r.width)] }) })()""")
    cols = [x for x, _ in grid[:2]]
    check(len(cols) == 2 and cols[0] == 0 and all(x == cols[i % 2] for i, (x, _) in enumerate(grid)) and len({w for _, w in grid}) == 1,
          f"founding: logos in two left-aligned columns of equal tiles, the last one not centred {grid[-2:]}")
    tabs = pg.evaluate(TEXTS, ".acx-mh-seg [role=tab]")
    check(tabs == pg.evaluate(TEXTS, ".elementor-element-5e398a3 .bb-tabs__nav-title"), f"mission: segments {tabs} match the legacy tabs")

    # measurements on the phone blocks
    small = pg.evaluate(SMALL_TARGETS, MINE)
    check(not small, f"home: targets at least 44px {small[:4]}")
    tiny = pg.evaluate(SMALL_TEXT, ".acx-mh *")
    check(not tiny, f"home: text at least 13px {tiny[:4]}")
    font = pg.evaluate(WRONG_FONT, ".acx-mh *")
    check(not font, f"home: everything in Inter {font[:3]}")
    low = pg.evaluate(CONTRAST, ".acx-mh *")
    check(not low, f"home: contrast {low[:3]}")
    under = pg.evaluate(UNDER_BARS, ".acx-mh-title, .acx-mh-hero-t")
    check(not under, f"home: section titles land below the top bar {under[:3]}")
    pg.evaluate("scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})"); pg.wait_for_timeout(200)
    clear = pg.evaluate("document.querySelector('.acx-mh-faqs').getBoundingClientRect().bottom <= document.querySelector('.acx-m-tabs').getBoundingClientRect().top")
    check(clear, "home: the FAQ list clears the tab bar at the end of the page")

    # behaviour: segmented control, disclosure rows
    pg.evaluate("document.querySelector('.acx-mh-mission').scrollIntoView()")
    check(pg.is_visible(".acx-mh-seg [role=tablist]") and pg.is_visible("#acx-mh-pan-0") and not pg.is_visible("#acx-mh-pan-1"),
          "mission: segmented control shows, Mission panel first")
    pg.tap("#acx-mh-tab-1"); pg.wait_for_timeout(150)
    check(pg.is_visible("#acx-mh-pan-1") and not pg.is_visible("#acx-mh-pan-0") and pg.get_attribute("#acx-mh-tab-1", "aria-selected") == "true",
          "mission: tapping Vision shows the Vision panel")
    pg.focus("#acx-mh-tab-1"); pg.keyboard.press("ArrowLeft"); pg.wait_for_timeout(100)
    check(pg.is_visible("#acx-mh-pan-0") and pg.evaluate("document.activeElement.id") == "acx-mh-tab-0", "mission: arrow keys move between segments")
    seg = pg.evaluate("(r => Math.round(r.height))(document.querySelector('#acx-mh-tab-0').getBoundingClientRect())")
    check(seg >= 44, f"mission: segments are 44px tall ({seg})")
    for lst in (".acx-mh-objs", ".acx-mh-vals", ".acx-mh-faqs"):
        first = f"{lst} > li:first-child"
        pg.evaluate(f"document.querySelector('{lst}').scrollIntoView({{block: 'center'}})"); pg.wait_for_timeout(100)
        check(not pg.is_visible(f"{first} .acx-mh-ans"), f"{lst}: rows start closed")
        pg.tap(f"{first} summary"); pg.wait_for_timeout(300)
        opened = pg.evaluate(f"document.querySelector('{first} details').open")
        check(opened and pg.is_visible(f"{first} .acx-mh-ans"), f"{lst}: tapping a row opens its full text")
        rot = pg.evaluate(f"getComputedStyle(document.querySelector('{first} .acx-mh-qchev')).transform")
        check(rot != pg.evaluate(f"getComputedStyle(document.querySelector('{lst} > li:nth-child(2) .acx-mh-qchev')).transform"), f"{lst}: the open row's chevron turns")
        st = pg.evaluate(f"(e => [parseFloat(getComputedStyle(e).fontSize), getComputedStyle(e).fontWeight])(document.querySelector('{first} summary'))")
        check(abs(st[0] - 17) < .2 and st[1] == "600", f"{lst}: row titles 17px/600 {st}")
        body = pg.evaluate(f"[...document.querySelectorAll('{first} .acx-mh-ans p, {first} .acx-mh-ans li')].map(e => parseFloat(getComputedStyle(e).fontSize)).filter(s => s < 16.9)")
        check(not body, f"{lst}: open text at 17px {body[:3]}")
        rows = pg.evaluate(f"[...document.querySelectorAll('{lst} summary')].map(s => Math.round(s.getBoundingClientRect().height)).filter(h => h < 52)")
        check(not rows, f"{lst}: rows at least 52px {rows}")
    if ctx.shots:
        pg.screenshot(path=f"{ctx.shots}/home-phone.png", full_page=True)
    pg.context.close()

    print("\n== Home on phones: anchors, no JS, reduced motion, 320px, desktop ==")
    # (the first jump happens before Inter loads, so text above can still shift it a little; a later jump is exact)
    pg = ctx.phone(path + "#founding-members"); pg.wait_for_timeout(300)
    t = pg.evaluate("Math.round(document.querySelector('.acx-mh-founding').getBoundingClientRect().top)")
    pg.evaluate("location.hash = ''; location.hash = '#founding-members'"); pg.wait_for_timeout(300)
    t2 = pg.evaluate("Math.round(document.querySelector('.acx-mh-founding').getBoundingClientRect().top)")
    check(56 <= t <= 250 and 56 <= t2 <= 80, f"#founding-members lands on the phone founding block below the top bar (on load {t}px, on a jump {t2}px)")
    pg.context.close()

    pg = ctx.phone(path, java_script_enabled=False)
    check(pg.is_visible("#acx-mh-pan-0") and pg.is_visible("#acx-mh-pan-1") and not pg.is_visible(".acx-mh-seg [role=tablist]"),
          "no JS: Mission and Vision both show, no dead segmented control")
    pg.click(".acx-mh-vals > li:first-child summary"); pg.wait_for_timeout(100)
    check(pg.is_visible(".acx-mh-vals > li:first-child .acx-mh-ans"), "no JS: disclosure rows still open")
    pg.context.close()

    pg = ctx.phone(path, reduced_motion="reduce")
    dur = pg.evaluate("getComputedStyle(document.querySelector('.acx-mh-qchev')).transitionDuration")
    check(dur in ("0s", ""), f"reduced motion: no chevron animation ({dur})")
    pg.context.close()

    c = ctx.b.new_context(viewport={"width": 320, "height": 640}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = c.new_page(); pg.goto(ctx.BASE + path, wait_until="load"); pg.wait_for_timeout(400)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    wide = pg.evaluate("[...document.querySelectorAll('.acx-mh *')].filter(e => e.getClientRects().length && !e.closest('.acx-mh-logo') && e.getBoundingClientRect().right > 321).map(e => e.className || e.tagName).slice(0, 4)")
    check(sw == 320 and not wide, f"320px: no sideways scroll ({sw}px) and nothing sticks out {wide}")
    acts = pg.evaluate("[...document.querySelectorAll('.acx-mh-hero-act a')].map(a => Math.round(a.getBoundingClientRect().height))")
    check(all(a >= 44 for a in acts), f"320px: hero actions at least 44px each {acts}")
    c.close()

    c = ctx.b.new_context(viewport={"width": 1440, "height": 900})
    pg = c.new_page(); pg.goto(ctx.BASE + path, wait_until="load"); pg.wait_for_timeout(400)
    n = pg.evaluate(VISIBLE, ".acx-mh, .acx-mh *")
    legacy = all(pg.evaluate(VISIBLE, s) > 0 for s in LEGACY.values())
    check(n == 0 and legacy, f"desktop 1440: no phone block shows ({n}) and the legacy sections stay ({legacy})")
    c.close()


SECTIONS = {"home": home}
