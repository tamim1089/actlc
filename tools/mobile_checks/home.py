"""Leaf 1.3: the home page on phones (tools/home_mobile.py, actlc-assets/mobile-home.css).
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

    # hero
    bar = pg.evaluate("Math.round(document.querySelector('.acx-m-top').getBoundingClientRect().bottom)")
    hr = pg.evaluate("(r => [Math.round(r.top), Math.round(r.height)])(document.querySelector('.acx-mh-hero').getBoundingClientRect())")
    check(hr[0] >= bar - 1, f"hero: starts below the top bar (hero top {hr[0]}px, bar bottom {bar}px)")
    check(0.45 * 844 <= hr[1] <= 0.66 * 844, f"hero: about 55-60% of the screen ({hr[1]}px of 844)")
    acts = pg.evaluate("[...document.querySelectorAll('.acx-mh-hero-act a')].map(a => [a.textContent.trim(), a.getAttribute('href'), Math.round(a.getBoundingClientRect().height)])")
    check(len(acts) == 2 and acts[0][1] == "events/index.html" and acts[1][1] == "conference/index.html" and all(a[2] >= 44 for a in acts),
          f"hero: two actions, webinars then conference, each at least 44px {acts}")
    check(pg.evaluate(VISIBLE, ".acx-mh-hero img[src*='Logo'], .acx-mh-hero img[src*='logo']") == 0, "hero: no repeated logo")

    # counts against the legacy markup on the same page
    legacy_board = pg.evaluate(TEXTS, ".director .elementor-image-box-title")
    board = pg.evaluate(TEXTS, ".acx-mh-board .acx-mh-name")
    check(len(board) == 7 and board == legacy_board, f"board: {len(board)} people in the page's order {board}")
    nfaq = pg.evaluate("document.querySelectorAll('.elementor-element-635f609 .elementor-toggle-item').length")
    qs = pg.evaluate(TEXTS, ".acx-mh-qa summary")
    lq = [q.split(". ", 1)[-1] for q in pg.evaluate(TEXTS, ".elementor-element-635f609 .elementor-toggle-title")]
    check(nfaq == 11 and qs == lq, f"FAQ: {len(qs)} questions, same text and order as the toggle ({nfaq})")
    nroles = pg.evaluate("document.querySelectorAll('.elementor-element-b0b1572 .elementor-image-box-description').length")
    roles = pg.evaluate("document.querySelectorAll('.acx-mh-roles > li').length")
    check(roles == nroles == 6, f"founding: {roles} roles (legacy {nroles})")
    # the live carousel adds loop clones and reorders slides; "N of 5" labels keep the authored order
    lv = pg.evaluate("""[...new Map([...document.querySelectorAll('.elementor-element-4414361 .swiper-slide')]
        .map(s => [s.querySelector('.elementor-icon-box-title').textContent.replace(/\\s+/g, ' ').trim(), parseInt(s.getAttribute('aria-label'))])
        .sort((a, b) => a[1] - b[1])).keys()]""")
    vals = pg.evaluate(TEXTS, ".acx-mh-mission .acx-mh-card-t")
    check(len(vals) == 5 and vals == lv, f"values: {len(vals)} cards in order {vals}")
    nobj = pg.evaluate("document.querySelectorAll('#n2-ss-4 .n2-ss-slide[data-slide-public-id]').length")
    obj = pg.evaluate("document.querySelectorAll('.acx-mh-objectives .acx-mh-card').length")
    check(obj == nobj and obj > 0, f"objectives: {obj} cards (slider has {nobj} slides)")
    nlogo = pg.evaluate(UNIQUE_SRC, ".elementor-element-600ad7a img")
    logos = pg.evaluate("document.querySelectorAll('.acx-mh-logos img').length")
    check(logos == nlogo and logos > 0, f"founding: {logos} member logos (legacy carousel has {nlogo} unique)")
    tabs = pg.evaluate(TEXTS, ".acx-mh-seg [role=tab]")
    check(tabs == pg.evaluate(TEXTS, ".elementor-element-5e398a3 .bb-tabs__nav-title"), f"mission: segments {tabs} match the legacy tabs")

    # measurements on the phone blocks
    small = pg.evaluate(SMALL_TARGETS, MINE)
    check(not small, f"home: targets at least 44px {small[:4]}")
    tiny = pg.evaluate(SMALL_TEXT, ".acx-mh *")
    check(not tiny, f"home: text at least 13px {tiny[:4]}")
    body = pg.evaluate("[...document.querySelectorAll('.acx-mh-card-text p, .acx-mh-points li, .acx-mh-lead, .acx-mh-pan p, .acx-mh-role p, .acx-mh-qa summary')].filter(e => e.getClientRects().length && parseFloat(getComputedStyle(e).fontSize) < 16.9)"
                       ".map(e => e.textContent.trim().slice(0, 20))")
    check(not body, f"home: reading text at body size {body[:3]}")
    font = pg.evaluate(WRONG_FONT, ".acx-mh *")
    check(not font, f"home: everything in Inter {font[:3]}")
    low = pg.evaluate(CONTRAST, ".acx-mh *")
    check(not low, f"home: contrast {low[:3]}")
    under = pg.evaluate(UNDER_BARS, ".acx-mh-title, .acx-mh-hero-t")
    check(not under, f"home: section titles land below the top bar {under[:3]}")
    pg.evaluate("scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})"); pg.wait_for_timeout(200)
    clear = pg.evaluate("document.querySelector('.acx-mh-faqs').getBoundingClientRect().bottom <= document.querySelector('.acx-m-tabs').getBoundingClientRect().top")
    check(clear, "home: the FAQ list clears the tab bar at the end of the page")

    # behaviour: segmented control, swipe buttons, disclosure rows
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
    for b in ("objectives", "board"):
        row = f".acx-mh-{b} .acx-mh-track"
        pg.evaluate(f"document.querySelector('{row}').scrollIntoView({{block: 'center'}})"); pg.wait_for_timeout(150)
        prev_dis = pg.evaluate(f"document.querySelector('.acx-mh-{b} .acx-mh-prev').disabled")
        x0 = pg.evaluate(f"document.querySelector('{row}').scrollLeft")
        pg.tap(f".acx-mh-{b} .acx-mh-next"); pg.wait_for_timeout(700)
        x1 = pg.evaluate(f"document.querySelector('{row}').scrollLeft")
        cw = pg.evaluate(f"document.querySelector('{row} > li').offsetWidth")
        count = pg.evaluate(f"document.querySelector('.acx-mh-{b} .acx-mh-count').textContent")
        check(prev_dis and x0 == 0 and x1 - x0 >= cw * 0.9 and not pg.evaluate(f"document.querySelector('.acx-mh-{b} .acx-mh-prev').disabled") and count.startswith("2 of"),
              f"{b}: Next scrolls one card ({x0} -> {x1}px, card {cw}px), Previous wakes up, position '{count}'")
        pg.evaluate(f"(t => t.scrollLeft = t.scrollWidth)(document.querySelector('{row}'))"); pg.wait_for_timeout(300)
        check(pg.evaluate(f"document.querySelector('.acx-mh-{b} .acx-mh-next').disabled"), f"{b}: Next is disabled at the last card")
        peek = pg.evaluate(f"(t => {{ t.scrollLeft = 0; const c = t.children[1].getBoundingClientRect(); return Math.round(390 - c.left) }})(document.querySelector('{row}'))")
        check(16 <= peek <= 40, f"{b}: the next card peeks in ({peek}px)")
    pg.evaluate("document.querySelector('.acx-mh-faq').scrollIntoView()")
    pg.tap(".acx-mh-faqs > li:first-child summary"); pg.wait_for_timeout(300)
    opened = pg.evaluate("document.querySelector('.acx-mh-faqs > li:first-child details').open")
    check(opened and pg.is_visible(".acx-mh-faqs > li:first-child .acx-mh-ans"), "FAQ: tapping a question opens its answer")
    rot = pg.evaluate("getComputedStyle(document.querySelector('.acx-mh-faqs > li:first-child .acx-mh-qchev')).transform")
    check(rot != pg.evaluate("getComputedStyle(document.querySelector('.acx-mh-faqs > li:nth-child(2) .acx-mh-qchev')).transform"), "FAQ: the open row's chevron turns")
    rows = pg.evaluate("[...document.querySelectorAll('.acx-mh-qa summary')].map(s => Math.round(s.getBoundingClientRect().height)).filter(h => h < 52)")
    check(not rows, f"FAQ: rows at least 52px {rows}")
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
    check(pg.evaluate(VISIBLE, ".acx-mh-nav") == 0, "no JS: no dead previous/next buttons")
    scroll = pg.evaluate("[...document.querySelectorAll('.acx-mh-track')].every(t => t.scrollWidth > t.clientWidth && getComputedStyle(t).overflowX === 'auto')")
    check(scroll, "no JS: swipe rows still scroll by touch")
    pg.context.close()

    pg = ctx.phone(path, reduced_motion="reduce")
    dur = pg.evaluate("getComputedStyle(document.querySelector('.acx-mh-qchev')).transitionDuration")
    check(dur in ("0s", ""), f"reduced motion: no chevron animation ({dur})")
    pg.context.close()

    c = ctx.b.new_context(viewport={"width": 320, "height": 640}, device_scale_factor=2, is_mobile=True, has_touch=True)
    pg = c.new_page(); pg.goto(ctx.BASE + path, wait_until="load"); pg.wait_for_timeout(400)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    wide = pg.evaluate("[...document.querySelectorAll('.acx-mh *')].filter(e => e.getClientRects().length && !e.closest('.acx-mh-track') && e.getBoundingClientRect().right > 321).map(e => e.className || e.tagName).slice(0, 4)")
    check(sw == 320 and not wide, f"320px: no sideways scroll ({sw}px) and nothing sticks out {wide}")
    c.close()

    c = ctx.b.new_context(viewport={"width": 1440, "height": 900})
    pg = c.new_page(); pg.goto(ctx.BASE + path, wait_until="load"); pg.wait_for_timeout(400)
    n = pg.evaluate(VISIBLE, ".acx-mh, .acx-mh *")
    legacy = all(pg.evaluate(VISIBLE, s) > 0 for s in LEGACY.values())
    check(n == 0 and legacy, f"desktop 1440: no phone block shows ({n}) and the legacy sections stay ({legacy})")
    c.close()


SECTIONS = {"home": home}
