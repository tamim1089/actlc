#!/usr/bin/env python3
"""Browser checks for the ACTLC pages we generate or restyle. Needs a local server:
     python3 -m http.server 8899 &
     python3 tools/check_pages.py [--only layout,states,tz,motion,header,footer,panel,home,font,conference,resources,search] [--shots DIR]
   Prints CHECKS_PASSED only when every selected check passes."""
import argparse, datetime as dt, sys
from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser(); ap.add_argument("--only", default=""); ap.add_argument("--shots")
A = ap.parse_args(); ONLY = set(filter(None, A.only.split(",")))
run = lambda s: not ONLY or s in ONLY

BASE = "http://localhost:8899"
EVENTS = {"list": "/events/index.html",
          "designing": "/events-main/designing-ai-ready-graduates/index.html",
          "teaching": "/events-main/teaching-the-learner-not-the-label/index.html"}
CHROME = {"home": "/index.html", "conference": "/conference/index.html", **EVENTS}
VIEWPORTS = [(1920, 1080), (1280, 800), (390, 844)]
UAE = dt.timezone(dt.timedelta(hours=4))
TODAY = dt.datetime(2026, 10, 13, 14, 0, tzinfo=UAE)
fails = []

def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond: fails.append(msg)

CONTRAST = r"""(sel) => {
  document.documentElement.classList.remove("acx-rv");  // measure revealed content, not mid-fade
 document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });   // measure the page at rest
 const rgba = c => { const m = c.match(/[\d.]+/g).map(Number); return [m[0], m[1], m[2], m[3] === undefined ? 1 : m[3]] };
 const lum = m => { const f = v => { v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055,2.4) };
   return .2126*f(m[0]) + .7152*f(m[1]) + .0722*f(m[2]) };
 const bg = el => { for (let e=el; e; e=e.parentElement){ const c=getComputedStyle(e).backgroundColor; const a=(c.match(/[\d.]+/g)||[])[3];
   if (c!=='rgba(0, 0, 0, 0)' && (a===undefined||+a>0.5)) return c } return 'rgb(255,255,255)' };
 const out=[];
 document.querySelectorAll(sel).forEach(el => {
   if (!el.getClientRects().length || (!el.offsetParent && getComputedStyle(el).position!=='fixed')) return;
   if (![...el.childNodes].some(n=>n.nodeType===3 && n.textContent.trim())) return;
   // blend semi-transparent text (and faded ancestors) over its real background before measuring
   const cs=getComputedStyle(el), B=rgba(bg(el)), F=rgba(cs.color);
   let a=F[3]; for (let e=el; e; e=e.parentElement) a*=+getComputedStyle(e).opacity;
   const mix=[0,1,2].map(i => a*F[i] + (1-a)*B[i]);
   const L1=lum(mix), L2=lum(B);
   const r=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05), px=parseFloat(cs.fontSize), w=+cs.fontWeight;
   out.push({t:el.textContent.trim().slice(0,28), cls:String(el.className), r:+r.toFixed(2), need:(px>=24||(px>=18.66&&w>=700))?3:4.5});
 }); return out.filter(c => c.r < c.need) }"""

def page(b, path, w=1280, h=900, tz="Asia/Dubai", at=TODAY, **ctx):
    c = b.new_context(viewport={"width": w, "height": h}, timezone_id=tz, **ctx)
    pg = c.new_page(); pg.clock.install(time=at); pg.goto(BASE + path, wait_until="load"); return pg

with sync_playwright() as p:
    b = p.chromium.launch()

    if run("layout"):
        print("\n== Layout, targets, type size, contrast ==")
        for name, path in EVENTS.items():
            for w, h in VIEWPORTS:
                pg = page(b, path, w, h); tag = f"{name} @{w}"
                sw = pg.evaluate("document.documentElement.scrollWidth"); check(sw <= w, f"{tag}: no horizontal scroll ({sw}px)")
                small = pg.evaluate("""() => [...document.querySelectorAll('.acx .acx-btn, .acx .acx-tab, .acx .acx-back, .acx .acx-ended')]
                     .filter(e => e.offsetParent || getComputedStyle(e).position==='fixed').map(e => [e.textContent.trim().slice(0,20), Math.round(e.getBoundingClientRect().height)]).filter(x => x[1] < 44)""")
                check(not small, f"{tag}: controls >= 44px tall {small or ''}")
                body = pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.acx-list-root, .acx-detail')).fontSize)")
                check(body >= 17, f"{tag}: base text {body}px (>= 17)")
                bad = [c for c in pg.evaluate(CONTRAST, ".acx-list-root *, .acx-detail *") if "acx-d" not in c["cls"].split()]
                check(not bad, f"{tag}: WCAG contrast {[(c['t'], c['r']) for c in bad] or ''}")
                if name == "list":
                    gap = pg.evaluate("""() => Math.min(...[...document.querySelectorAll('#acx-panel-up .acx-ev')].map(li => {
                        const d = li.querySelector('.acx-date'), b = li.querySelector('.acx-body');
                        const right = Math.max(...[...d.children].map(c => c.getBoundingClientRect().right));
                        const db = d.getBoundingClientRect(), bb = b.getBoundingClientRect();
                        return bb.top >= db.bottom - 1 ? 99 : bb.left - right }))""")
                    check(gap >= 12, f"{tag}: date never touches the title (min gap {round(gap)}px)")
                    off = pg.evaluate("Math.abs(document.querySelector('.entry-title').getBoundingClientRect().left - document.querySelector('.acx-list-root').getBoundingClientRect().left)")
                    check(off <= 1, f"{tag}: heading aligned with list ({round(off)}px)")
                if A.shots: pg.screenshot(path=f"{A.shots}/{name}-{w}.png", full_page=True)
                pg.context.close()

    if run("panel"):
        print("\n== Session panel: compact and complete ==")
        for name in ("designing", "teaching"):
            pg = page(b, EVENTS[name], 1920, 1080)
            hgt = pg.evaluate("Math.round(document.querySelector('.acx-when').getBoundingClientRect().height)")
            check(hgt <= 300, f"{name}: date/time panel is compact ({hgt}px tall at 1920, limit 300)")
            txt = pg.inner_text(".acx-when")
            need = ["UAE time (GMT+4)", "Online", "Register", "Add to Calendar", "Starts in", "Saudi Arabia", "Lebanon", "Morocco"]
            missing = [n for n in need if n not in txt]
            check(not missing, f"{name}: every detail still present {missing or ''}")
            hrefs = pg.evaluate("[...document.querySelectorAll('.acx-when a')].map(a=>a.getAttribute('href'))")
            check(any(h.startswith("mailto:") for h in hrefs) and "event.ics" in hrefs, f"{name}: Register (mailto) and .ics present")
            check(pg.evaluate("document.querySelectorAll('.acx-when li, .acx-when details').length") == 0, f"{name}: member times are one line of text (no pills, no dropdown)")
            pg.context.close()

    if run("states"):
        print("\n== Time states (fake clock) ==")
        at = lambda s: dt.datetime.fromisoformat(s)
        pg = page(b, EVENTS["list"])
        check(not pg.query_selector(".acx-tabs") and pg.is_visible("#past .acx-ev"), "list: no tabs; past webinars are visible below upcoming")
        n = pg.evaluate("[document.querySelectorAll('#acx-panel-up .acx-ev').length, +document.querySelector('[data-count=\"past\"]').textContent]")
        check(sum(n) == 21 and n[1] == pg.evaluate("document.querySelectorAll('#past .acx-ev').length"), f"list: all 21 webinars listed, past count matches its rows {n}")
        old = pg.evaluate("['5678','5683','5686','5697','5695','5702','5704','6727','5706','5708','5710','5712'].filter(i => document.querySelector('#past #ev-' + i)).length")
        check(old == 12, f"list: the 12 earlier webinars are back under Past ({old}/12)")
        yrs = pg.evaluate("[...document.querySelectorAll('#past .acx-w')].map(e => e.textContent.trim())")
        check(yrs and all(len(y) == 4 and y.isdigit() for y in yrs), f"list: past rows show the year {sorted(set(yrs))}")
        pg.context.close()
        pg = page(b, EVENTS["list"], at=at("2026-10-16T09:00:00+04:00"))
        check(pg.evaluate("document.querySelectorAll('#acx-panel-up .acx-ev').length") == 7 and pg.inner_text('[data-count="past"]') == "14", "list: after 15 Oct, Gamification moves to Past (7/14)")
        check(pg.inner_text("#ev-7005 .acx-w") == "2026", "list: a row moved to Past shows its year")
        check(pg.evaluate("document.querySelector('#past .acx-ev').id") == "ev-7005", "list: newest past event first")
        check(pg.evaluate("!document.querySelector('#ev-7005 .acx-title a').hasAttribute('href')"), "list: ended mailto title is no longer a link")
        pg.context.close()
        pg = page(b, EVENTS["list"], at=at("2026-10-19T17:00:00+04:00"))
        check(pg.is_visible("#ev-7002 .acx-live"), "list: 'Live now' during Designing AI-Ready Graduates"); pg.context.close()
        pg = page(b, EVENTS["list"], at=at("2027-02-01T09:00:00+04:00"))
        check(pg.is_visible("#acx-panel-up .acx-empty"), "list: empty state when nothing is upcoming"); pg.context.close()
        pg = page(b, EVENTS["designing"])
        check(pg.inner_text(".acx-status") == "Starts in 6 days", f"detail: '{pg.inner_text('.acx-status')}'"); pg.context.close()
        pg = page(b, EVENTS["designing"], at=at("2026-10-19T17:00:00+04:00"))
        check(pg.inner_text(".acx-status") == "Live now", "detail: live state"); pg.context.close()
        pg = page(b, EVENTS["designing"], 390, 844, at=at("2026-10-20T09:00:00+04:00"))
        check(pg.inner_text(".acx-status") == "Ended", "detail: ended status")
        check(pg.is_visible(".acx-ended-note") and not pg.is_visible(".acx-bar") and not pg.is_visible(".acx-actions"), "detail: ended note shown, Register hidden (mobile bar too)")
        pg.context.close()

    if run("tz"):
        print("\n== Visitor timezone ==")
        for tz, cc in [("Africa/Cairo", "eg"), ("Asia/Dubai", "ae"), ("Africa/Casablanca", "ma")]:  # cc kept for readability
            pg = page(b, EVENTS["designing"], tz=tz)
            yt = pg.evaluate("(e => e.hidden ? '' : e.textContent)(document.querySelector('.acx-yourtime'))")
            want = {"Africa/Cairo": "Your time: 15:30 – 17:00 · Cairo", "Asia/Dubai": "", "Africa/Casablanca": "Your time: 12:30 – 14:00 · Casablanca"}[tz]
            if tz == "Africa/Casablanca" and yt.startswith("Your time: 13:30"): want = yt   # browser with pre-2026c tz data
            check(yt == want, f"detail: your-time line for {tz} ('{yt}')"); pg.context.close()
        pg = page(b, EVENTS["designing"], tz="America/New_York")
        yt = pg.inner_text(".acx-yourtime"); check(yt == "Your time: 08:30 – 10:00 · New York", f"detail: New York visitor sees own time ('{yt}')")
        el = pg.inner_text(".acx-elsewhere"); check(el == "15:30 in Saudi Arabia, Bahrain, Lebanon and Egypt · 12:30 in Morocco", f"detail: member times grouped, Morocco 12:30 from tzdata 2026c ('{el}')")
        pg.context.close()

    if run("home"):
        print("\n== Homepage upcoming list ==")
        pg = page(b, CHROME["home"], 1920, 1080)
        ids = pg.evaluate("[...document.querySelectorAll('.acx-home-root .acx-ev')].map(e=>e.id)")
        check(ids == ["ev-7002", "ev-7006", "ev-7007"], f"home: next three sessions {ids}")
        check("24" not in pg.inner_text(".acx-home-root .acx-d") if pg.query_selector(".acx-home-root .acx-d") else False, "home: stale '24 September' date gone")
        pg.context.close()
        pg = page(b, CHROME["home"], 1920, 1080, at=dt.datetime(2026, 10, 16, 9, 0, tzinfo=UAE))
        ids = pg.evaluate("[...document.querySelectorAll('.acx-home-root .acx-ev')].map(e=>e.id)")
        check(ids == ["ev-7002", "ev-7006", "ev-7007"], f"home: ended session drops off by itself {ids}")
        pg.context.close()

    if run("header"):
        print("\n== Header: refined, not broken ==")
        for name, path in CHROME.items():
            pg = page(b, path, 1920, 1080)
            bad = pg.evaluate(CONTRAST, "#primary-menu > li > a span, .bb-header-buttons .button")
            check(not bad, f"{name}: header text contrast {[(c['t'], c['r']) for c in bad] or ''}")
            fs = pg.evaluate("getComputedStyle(document.querySelector('#primary-menu > li > a')).fontSize")
            check(fs == "15px", f"{name}: menu labels 15px ({fs})")
            ev = pg.evaluate("""() => { const a=[...document.querySelectorAll('#primary-menu a')].find(a=>a.textContent.trim()==='Events'); return a && new URL(a.href).pathname }""")
            check(ev == "/events/index.html", f"{name}: Events menu opens the list ({ev})")
            pg.hover("#primary-menu > li.menu-item-has-children > a")
            check(pg.is_visible("#primary-menu > li.menu-item-has-children .bb-sub-menu"), f"{name}: dropdown still opens on hover")
            hh = pg.evaluate("Math.round(document.querySelector('#masthead').getBoundingClientRect().height)")
            check(60 <= hh <= 90, f"{name}: header height unchanged range ({hh}px)")
            if A.shots and name in ("list", "home"):
                pg.screenshot(path=f"{A.shots}/header-{name}.png", clip={"x": 0, "y": 0, "width": 1920, "height": 380})
            pg.context.close()
        pg = page(b, CHROME["list"], 390, 844)
        check(pg.is_visible(".bb-left-panel-mobile"), "mobile: menu button still present"); pg.context.close()

    if run("footer"):
        print("\n== Footer on every page ==")
        for name, path in CHROME.items():
            for w in (1920, 390):
                pg = page(b, path, w, 900)
                f = pg.query_selector(".acx-footer")
                check(f is not None, f"{name} @{w}: Apple-style footer present")
                if not f: pg.context.close(); continue
                hrefs = pg.evaluate("[...document.querySelectorAll('.acx-footer a')].map(a=>a.getAttribute('href'))")
                check("mailto:info@ac-tlc.org" in hrefs and "tel:+97143487445" in hrefs, f"{name} @{w}: tappable email and phone")
                check(not [h for h in hrefs if h in ("#", "") or "email-protection" in h], f"{name} @{w}: no dead links in footer")
                check(pg.evaluate("document.querySelector('.acx-foot-brand img').alt.length > 0"), f"{name} @{w}: logo has alt text")
                pg.locator(".acx-foot-brand img").scroll_into_view_if_needed(); pg.wait_for_timeout(500)
                check(pg.evaluate("(i => i.complete && i.naturalWidth > 0)(document.querySelector('.acx-foot-brand img'))"), f"{name} @{w}: footer logo actually loads")
                bad = pg.evaluate(CONTRAST, ".acx-footer *"); check(not bad, f"{name} @{w}: footer contrast {[(c['t'], c['r']) for c in bad] or ''}")
                if w == 390:
                    small = pg.evaluate("[...document.querySelectorAll('.acx-footer a')].filter(a=>a.getBoundingClientRect().height<44).length")
                    check(small == 0, f"{name} @390: footer links >= 44px tall ({small} smaller)")
                if A.shots and name == "list": f.screenshot(path=f"{A.shots}/footer-{w}.png")
                pg.context.close()

    if run("font"):
        print("\n== Inter served from the site ==")
        for name, path in CHROME.items():
            pg = page(b, path, 1280, 800); pg.wait_for_timeout(400)
            ok = pg.evaluate("[...document.fonts].some(f => f.family.replace(/\"/g,'') === 'Inter' && f.status === 'loaded')")
            check(ok, f"{name}: local Inter webfont loaded"); pg.context.close()

    if run("conference"):
        print("\n== Conference page (tools/DESIGN-RULES.md) ==")
        C = CHROME["conference"]
        for w, h in VIEWPORTS:
            pg = page(b, C, w, h); tag = f"conference @{w}"
            sw = pg.evaluate("document.documentElement.scrollWidth"); check(sw <= w, f"{tag}: no horizontal scroll ({sw}px)")
            fonts = pg.evaluate("""() => [...new Set([...document.querySelectorAll('.acx-conf *')].filter(e => e.offsetParent && [...e.childNodes].some(n => n.nodeType===3 && n.textContent.trim()))
                .map(e => getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g,'').trim()))]""")
            check(fonts == ["Inter"], f"{tag}: one typeface {fonts}")
            tiny = pg.evaluate("""() => [...document.querySelectorAll('.acx-conf *')].filter(e => e.offsetParent && [...e.childNodes].some(n => n.nodeType===3 && n.textContent.trim()) && parseFloat(getComputedStyle(e).fontSize) < 13).map(e => e.textContent.trim().slice(0,20)).slice(0,5)""")
            check(not tiny, f"{tag}: no text below 13px {tiny or ''}")
            bad = pg.evaluate(CONTRAST, ".acx-conf *"); check(not bad, f"{tag}: WCAG contrast {[(x['t'], x['r']) for x in bad][:6] or ''}")
            small = pg.evaluate("[...document.querySelectorAll('.acx-conf .acx-btn, .acx-conf .acx-tab, .acx-conf .acx-link, .acx-local-links a')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 40).length")
            check(small == 0, f"{tag}: controls >= 40px tall ({small} smaller)")
            if w == 1920:
                ht = pg.evaluate("document.documentElement.scrollHeight"); check(ht <= 11500, f"{tag}: page shorter than before ({ht}px, was 14242)")
                bar = pg.evaluate("(e => e.scrollWidth <= e.clientWidth)(document.querySelector('.acx-local-links'))"); check(bar, f"{tag}: section bar fits, nothing cut off")
                wrap = pg.evaluate("[...document.querySelectorAll('.acx-c-t')].filter(t => (e => new Set([...(r => (r.selectNodeContents(e), r))(document.createRange()).getClientRects()].map(x => Math.round(x.top))).size)(t) > 1).length")
                check(wrap == 0, f"{tag}: programme times on one line ({wrap} wrapped)")
            pg.context.close()
        pg = page(b, C, 1920, 1080)
        regs = pg.evaluate("[...document.querySelectorAll('a')].filter(a => /^Register$/.test(a.textContent.trim()) && a.closest('.acx-conf')).length")
        check(regs == 5, f"conference: Register appears {regs}x (bar, hero, one per price card)")
        plans = pg.evaluate("[document.querySelectorAll('.acx-c-plan').length, document.querySelectorAll('.acx-c-plan.is-hi .acx-c-plan-badge').length, document.querySelectorAll('.acx-c-plan .acx-btn-light').length]")
        check(plans == [3, 1, 1], f"conference: 3 price cards, one raised with a badge and the only filled button {plans}")
        big = pg.evaluate("(() => { const p = [...document.querySelectorAll('#speakers > div > .acx-c-people > li')]; const w = e => e.getBoundingClientRect().width; return [p.filter(e => e.classList.contains('is-lg')).length, Math.round(w(p[0]) / w(p[4]) * 10) / 10]; })()")
        check(big[0] == 4 and 1.15 <= big[1] <= 1.35, f"conference: top row of four speakers at about 1.25x, no strong hierarchy {big}")
        cover = pg.evaluate("[...document.querySelectorAll('.acx-c-person')].filter(li => { const p = li.querySelector('.acx-c-photo').getBoundingClientRect(), c = li.querySelector('.acx-c-cap').getBoundingClientRect(); return c.top < p.bottom - 1; }).length")
        check(cover == 0, f"conference: names sit under the photos, never on a face ({cover} overlap)")
        lg = pg.evaluate("Math.round(document.querySelector('.acx-c-logos img[alt=\"CLICKS\"], .acx-c-logos img').getBoundingClientRect().height)")
        mq = pg.evaluate("[getComputedStyle(document.querySelector('.acx-c-mtrack')).animationName, document.querySelectorAll('.acx-c-logos[aria-hidden=true]').length]")
        check(lg >= 80 and mq == ["acx-marquee", 1], f"conference: logos move in a strip, {lg}px tall, copy hidden from screen readers {mq}")
        check(pg.evaluate("document.querySelectorAll('video, #cd, .conf-page, .acx-conf form').length") == 0, "conference: no video, countdown, old template or fake form")
        venue = pg.evaluate("[document.querySelector('.acx-c-when').textContent, [...document.querySelectorAll('.acx-c-dayv')].map(e => e.textContent)]")
        check("Abu Dhabi University, Abu Dhabi Campus" in venue[0] and all(v == "Abu Dhabi University, Abu Dhabi Campus" for v in venue[1]), f"conference: venue is ADU Abu Dhabi Campus in hero and agenda {venue}")
        stray = pg.evaluate("[...document.querySelectorAll('.acx-conf *')].filter(e => !e.closest('.acx-c-pr') && [...e.childNodes].some(n => n.nodeType === 3 && /Al Ain|UAEU|United Arab Emirates University \\(/.test(n.textContent))).map(e => e.textContent.trim().slice(0, 60))")
        check(not stray, f"conference: no UAEU or Al Ain venue left (job titles excepted) {stray}")
        hp = pg.evaluate("fetch('../index.html').then(r => r.text()).then(t => [t.includes('logos/cards/ADU.webp'), t.includes('logos/cards/UAEU')])")
        check(hp == [True, False], f"home: the host strip is on the ADU card, not UAEU {hp}")
        txt = pg.inner_text("body"); check("Two campuses" not in txt and "Message sent" not in txt and "Targeted Speakers" not in txt, "conference: no stale or invented claims")
        check(pg.is_visible("#acx-day-1") and pg.is_visible("#acx-day-2"), "conference: wide screens show both days side by side")
        pg.context.close()
        pg = page(b, C, 1000, 900)
        check(pg.is_visible("#acx-day-1") and pg.is_visible("#acx-day-2") and not pg.query_selector(".acx-c-tabs"), "conference: both days shown at every width, no tabs")
        hidden = pg.evaluate("document.querySelectorAll('.acx-conf details:not([open])').length")
        check(hidden == 0, f"conference: nothing important behind a click ({hidden} closed disclosures)")
        prop = pg.evaluate("(() => { const b = [...document.querySelectorAll('#acx-day-1 .acx-c-blk')]; const h = e => e.getBoundingClientRect().height; return Math.round(h(b.find(x => x.classList.contains('is-par'))) / h(b[1]) * 10) / 10; })()")
        check(prop >= 3, f"conference: programme block height follows session length (180 vs 25 min -> {prop}x)")
        tl = pg.evaluate("[!document.querySelector('.acx-c-tl-now').hidden, document.querySelectorAll('.acx-c-rel:not([hidden])').length]")
        check(tl == [True, 4], f"conference: key dates show today and how far away each date is {tl}")
        wrapped = pg.evaluate("[...document.querySelectorAll('.acx-c-dates time, .acx-c-t, .acx-c-tabs .acx-tab')].filter(e => e.offsetParent && (e => new Set([...(r => (r.selectNodeContents(e), r))(document.createRange()).getClientRects()].map(x => Math.round(x.top))).size)(e) > 1).length")
        check(wrapped == 0, f"conference: dates and times never split across lines ({wrapped})")
        pg.context.close()
        c2 = b.new_context(viewport={"width": 1280, "height": 900}, java_script_enabled=False); pg = c2.new_page(); pg.goto(BASE + C)
        check(pg.is_visible("#acx-day-1") and pg.is_visible("#acx-day-2"), "conference: without JavaScript both days are listed"); c2.close()

    if run("motion"):
        print("\n== Reduced motion ==")
        pg = page(b, EVENTS["list"], reduced_motion="reduce")
        check(pg.evaluate("getComputedStyle(document.querySelector('.acx .acx-btn')).transitionDuration") == "0s", "reduced motion: no transitions")
        check(pg.evaluate("getComputedStyle(document.querySelector('.acx .acx-ev')).animationName") == "none", "reduced motion: no entrance animation")
        pg.context.close()
        pg = page(b, EVENTS["list"])
        check(pg.evaluate("getComputedStyle(document.querySelector('.acx .acx-ev')).animationName") == "acx-rise", "motion: list rows rise in")
        pg.hover("#menu-item-5079 > a")
        check(pg.evaluate("getComputedStyle(document.querySelector('#menu-item-5079 .bb-sub-menu')).animationName") == "acx-menu", "motion: dropdown pops open")
        check(pg.evaluate("getComputedStyle(document.querySelector('#menu-item-5079 .ab-submenu')).backgroundColor") == "rgba(0, 0, 0, 0)", "dropdown: no second background behind the menu")
        pg.context.close()
    if run("resources"):
        print("\n== Resources ==")
        R = "/resources/index.html"
        for w, h in VIEWPORTS:
            pg = page(b, R, w, h); tag = f"resources @{w}"
            sw = pg.evaluate("document.documentElement.scrollWidth"); check(sw <= w, f"{tag}: no horizontal scroll ({sw}px)")
            low = pg.evaluate(CONTRAST, ".acx-res-root *"); check(not low, f"{tag}: text contrast {low[:3]}")
            split = pg.evaluate("[...document.querySelectorAll('.acx-res-src a')].filter(e => e.getClientRects().length > 1).length")
            check(split == 0, f"{tag}: DOIs never split across lines ({split})")
            pg.context.close()
        pg = page(b, R)
        docs = pg.evaluate("[...document.querySelectorAll('.acx-res')].map(li => [li.querySelector('.acx-title a').getAttribute('href'), li.querySelector('.acx-res-thumb img').naturalWidth > 0])")
        check(len(docs) == 4 and all(ok for _, ok in docs), f"resources: 4 documents, each with its first page shown {docs}")
        codes = [pg.request.get(BASE + "/resources/" + href).status for href, _ in docs]
        types = [pg.request.get(BASE + "/resources/" + href).headers.get("content-type") for href, _ in docs]
        check(codes == [200] * 4 and all(t == "application/pdf" for t in types), f"resources: every PDF is served {codes} {set(types)}")
        heads = pg.evaluate("[...document.querySelectorAll('.acx-res-group > .acx-h2')].map(e => e.textContent)")
        check(heads == ["American University of Bahrain", "American University of Sharjah"], f"resources: grouped by university {heads}")
        check(pg.evaluate("document.querySelector('#primary-menu > li.current-menu-item a span').textContent") == "Resources", "resources: menu marks Resources as the current page")
        check(pg.evaluate("!document.querySelector('form[action*=\"wp-login\"], #loginform')"), "resources: no dead WordPress login form")
        pg.context.close()
    if run("search"):
        print("\n== Site search ==")
        pg = page(b, EVENTS["list"], 1440, 900); reqs = []
        pg.on("request", lambda r: reqs.append(r.url))
        pg.wait_for_timeout(300)
        check(not any("search-index" in u for u in reqs), "search: index is not loaded until someone goes to search")
        pg.click(".header-search-link >> visible=true"); pg.wait_for_selector(".acx-sd[open]")
        check(pg.evaluate("document.activeElement.classList.contains('acx-sd-q')"), "search: the search button opens the panel with the cursor in the box")
        pg.wait_for_function("acxSearch.engine()")
        def top(q):
            return pg.evaluate("""(q) => { const r = acxSearch.engine().search(q); return r ? r.list.slice(0, 3).map(d => [d.t, d.u]) : []; }""", q)
        for q, want in [("barry", "Prof. Barry O'Mahony"), ("bary", "Prof. Barry O'Mahony"), ("omahony", "Prof. Barry O'Mahony"),
                        ("ghasan aouad", "Prof. Ghassan Aouad"), ("deadline", "Proposal Submission Deadline"), ("gamification", "Gamification in the University Classroom")]:
            r = top(q); check(r and r[0][0] == want, f"search: '{q}' finds {want} first ({r[0][0] if r else None})")
        r = top("maria"); check(r and "de Fez Laso" in pg.evaluate("(q) => acxSearch.engine().search(q).list[0].s", "maria"), "search: 'maria' (no accent) finds Prof. María del Mar de Fez Laso")
        r = top("toolkit dashboard"); check(r and r[0][1].endswith(".pdf#page=20"), f"search: words inside a PDF open that PDF at the right page ({r[0][1] if r else None})")
        speed = pg.evaluate("""() => { const e = acxSearch.engine(), qs = ['a', 'as', 'ass', 'asse', 'asses', 'assess', 'assessm', 'assessment', 'assessment rei', 'bary', 'zzzz'];
            const t0 = performance.now(); for (let i = 0; i < 20; i++) qs.forEach(q => e.search(q)); return (performance.now() - t0) / (20 * qs.length); }""")
        check(speed < 5, f"search: under 5 ms per keystroke ({speed:.3f} ms)")
        pg.keyboard.type("assessment"); pg.wait_for_timeout(100)
        n = pg.evaluate("document.querySelectorAll('.acx-sd-r').length"); check(n >= 5, f"search: results appear as you type ({n})")
        pg.keyboard.press("ArrowDown")
        check(pg.evaluate("document.querySelector('.acx-sd-q').getAttribute('aria-activedescendant')") == "acx-sd-o1", "search: arrow keys move through results")
        low = pg.evaluate(CONTRAST, ".acx-sd *"); check(not low, f"search: text contrast {low[:3]}")
        pg.keyboard.press("Escape"); check(not pg.is_visible(".acx-sd"), "search: Esc closes the panel")
        pg.keyboard.press("/"); pg.wait_for_selector(".acx-sd[open]"); pg.keyboard.press("Control+a"); pg.keyboard.type("barry"); pg.wait_for_timeout(100)
        pg.keyboard.press("Enter"); pg.wait_for_load_state("load"); pg.wait_for_timeout(600)
        check(pg.url.endswith("/conference/index.html#p-prof-barry-o-mahony"), f"search: '/' opens search, Enter goes to the result ({pg.url.split('8899')[-1]})")
        IN_VIEW = "(t => t && t.getBoundingClientRect().top >= document.getElementById('masthead').getBoundingClientRect().bottom && t.getBoundingClientRect().top < innerHeight / 2)(document.querySelector(':target'))"
        try: pg.wait_for_function(IN_VIEW, timeout=3000); ok = True
        except Exception: ok = False
        tgt = pg.evaluate("(t => t && [Math.round(t.getBoundingClientRect().top), innerHeight])(document.querySelector(':target'))")
        check(ok, f"search: the result settles in the top half of the screen, below the sticky header [top, height] = {tgt}")
        check(not any("ac-tlc.org/?s=" in u or "admin-ajax" in u for u in reqs), "search: nothing is sent to the WordPress site")
        pg.context.close()
        pg = page(b, CHROME["home"], 390, 844, has_touch=True, is_mobile=True)
        pg.tap(".header-search-link >> visible=true"); pg.wait_for_selector(".acx-sd[open]"); pg.wait_for_function("acxSearch.engine()")
        pg.keyboard.type("assessment"); pg.wait_for_timeout(100)
        box = pg.evaluate("(r => [r.width, r.height])(document.querySelector('.acx-sd').getBoundingClientRect())")
        check(box == [390, 844] and pg.evaluate("document.documentElement.scrollWidth") <= 390, f"search @390: full-screen panel, no sideways scroll {box}")
        check(pg.evaluate("parseFloat(getComputedStyle(document.querySelector('.acx-sd-q')).fontSize)") >= 16, "search @390: box text 16px or more, so iOS does not zoom")
        pg.context.close()
    b.close()

print(f"\n{len(fails)} failure(s)")
print("CHECKS_PASSED" if not fails else "CHECKS_FAILED")
sys.exit(1 if fails else 0)
