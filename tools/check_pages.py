#!/usr/bin/env python3
"""Browser checks for the ACTLC pages we generate or restyle. Needs a local server:
     python3 -m http.server 8899 &
     python3 tools/check_pages.py [--only layout,states,tz,motion,header,footer,panel,home,font,conference] [--shots DIR]
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
 const lum = c => { const m = c.match(/[\d.]+/g).map(Number); const f = v => { v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055,2.4) };
   return .2126*f(m[0]) + .7152*f(m[1]) + .0722*f(m[2]) };
 const bg = el => { for (let e=el; e; e=e.parentElement){ const c=getComputedStyle(e).backgroundColor; const a=(c.match(/[\d.]+/g)||[])[3];
   if (c!=='rgba(0, 0, 0, 0)' && (a===undefined||+a>0.5)) return c } return 'rgb(255,255,255)' };
 const out=[];
 document.querySelectorAll(sel).forEach(el => {
   if (!el.offsetParent && getComputedStyle(el).position!=='fixed') return;
   if (![...el.childNodes].some(n=>n.nodeType===3 && n.textContent.trim())) return;
   const cs=getComputedStyle(el), L1=lum(cs.color), L2=lum(bg(el));
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
            need = ["UAE time (GMT+4)", "Online", "Register", "Add to Calendar", "Google Calendar", "Starts in",
                    "UAE", "Saudi Arabia", "Bahrain", "Egypt", "Morocco"]
            missing = [n for n in need if n not in txt]
            check(not missing, f"{name}: every detail still present {missing or ''}")
            hrefs = pg.evaluate("[...document.querySelectorAll('.acx-when a')].map(a=>a.getAttribute('href'))")
            check(any(h.startswith("mailto:") for h in hrefs) and "event.ics" in hrefs and any("calendar.google.com" in h for h in hrefs),
                  f"{name}: Register (mailto), .ics and Google links all present")
            pg.context.close()

    if run("states"):
        print("\n== Time states (fake clock) ==")
        at = lambda s: dt.datetime.fromisoformat(s)
        pg = page(b, EVENTS["list"])
        check(pg.is_visible(".acx-tabs"), "list: segmented control shown with JS")
        check(pg.inner_text('[data-count="upcoming"]') == "8" and pg.inner_text('[data-count="past"]') == "1", "list: 8 upcoming / 1 past on 13 Oct")
        pg.click("#acx-tab-past"); check(pg.is_visible("#acx-panel-past") and not pg.is_visible("#acx-panel-up"), "list: Past tab switches panels")
        check(pg.evaluate("location.hash") == "#past", "list: #past in the URL")
        pg.keyboard.press("ArrowLeft"); check(pg.is_visible("#acx-panel-up"), "list: arrow key returns to Upcoming")
        pg.context.close()
        pg = page(b, EVENTS["list"], at=at("2026-10-16T09:00:00+04:00"))
        check(pg.inner_text('[data-count="upcoming"]') == "7" and pg.inner_text('[data-count="past"]') == "2", "list: after 15 Oct, Gamification moves to Past (7/2)")
        check(pg.evaluate("document.querySelector('#acx-panel-past .acx-ev').id") == "ev-7005", "list: newest past event first")
        check(pg.evaluate("!document.querySelector('#ev-7005 .acx-title a').hasAttribute('href')"), "list: ended mailto title is no longer a link")
        pg.context.close()
        pg = page(b, EVENTS["list"], at=at("2026-10-15T16:20:00+03:00"))
        check(pg.is_visible("#ev-7005 .acx-live"), "list: 'Live now' during Gamification"); pg.context.close()
        pg = page(b, EVENTS["list"], at=at("2027-02-01T09:00:00+04:00"))
        check(pg.is_visible("#acx-panel-up .acx-empty"), "list: empty state when nothing is upcoming"); pg.context.close()
        pg = page(b, EVENTS["designing"])
        check(pg.inner_text(".acx-status") == "Starts in 6 days", f"detail: '{pg.inner_text('.acx-status')}'"); pg.context.close()
        pg = page(b, EVENTS["designing"], at=at("2026-10-19T17:00:00+04:00"))
        check(pg.inner_text(".acx-status") == "Live now" and pg.inner_text(".acx-eyebrow-state") == "Live now", "detail: live state"); pg.context.close()
        pg = page(b, EVENTS["designing"], 390, 844, at=at("2026-10-20T09:00:00+04:00"))
        check(pg.inner_text(".acx-status") == "Ended", "detail: ended status")
        check(pg.is_visible(".acx-ended-note") and not pg.is_visible(".acx-bar") and not pg.is_visible(".acx-actions"), "detail: ended note shown, Register hidden (mobile bar too)")
        pg.context.close()

    if run("tz"):
        print("\n== Visitor timezone ==")
        for tz, cc in [("Africa/Cairo", "eg"), ("Asia/Dubai", "ae"), ("Africa/Casablanca", "ma")]:
            pg = page(b, EVENTS["designing"], tz=tz)
            got = pg.evaluate("(document.querySelector('.acx-city.is-you')||{dataset:{}}).dataset.cc")
            check(got == cc, f"detail: visitor in {tz} highlights '{cc}' ({got})"); pg.context.close()
        pg = page(b, EVENTS["designing"], tz="America/New_York")
        you = pg.evaluate("[...document.querySelectorAll('.acx-city.is-you span')].map(s=>s.textContent)")
        check(you[:3] == ["You", "New York", "08:30"], f"detail: New York visitor gets own cell {you}")
        check(pg.inner_text('[data-cc="ma"] .acx-city-t') == "12:30", "detail: Morocco 12:30 (tzdata 2026c, built server-side)")
        pg.context.close()

    if run("home"):
        print("\n== Homepage upcoming list ==")
        pg = page(b, CHROME["home"], 1920, 1080)
        ids = pg.evaluate("[...document.querySelectorAll('.acx-home-root .acx-ev')].map(e=>e.id)")
        check(ids == ["ev-7005", "ev-7002", "ev-7006"], f"home: next three sessions on 13 Oct {ids}")
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
        print("\n== Conference page on the design system ==")
        C = CHROME["conference"]
        c = b.new_context(viewport={"width": 1920, "height": 1080}, java_script_enabled=False); pg = c.new_page(); pg.goto(BASE + C)
        hidden = pg.evaluate("[...document.querySelectorAll('.conf-page [data-r], .conf-page [data-st] > *')].filter(e => getComputedStyle(e).opacity !== '1').length")
        check(hidden == 0, f"conference: all content visible without JavaScript ({hidden} hidden)"); c.close()
        for w, h in VIEWPORTS:
            pg = page(b, C, w, h)
            pg.evaluate("document.querySelectorAll('.conf-page [data-r], .conf-page [data-st]').forEach(e => e.classList.add('v'))"); pg.wait_for_timeout(900)
            tag = f"conference @{w}"
            sw = pg.evaluate("document.documentElement.scrollWidth"); check(sw <= w, f"{tag}: no horizontal scroll ({sw}px)")
            fonts = pg.evaluate("""() => [...new Set([...document.querySelectorAll('.conf-page h1, .conf-page h2, .conf-page h3, .conf-page p, .conf-page .btn, .conf-page .eyebrow, .conf-page label, .conf-page li')]
                .filter(e => e.offsetParent).map(e => getComputedStyle(e).fontFamily.split(',')[0].replace(/["']/g,'').trim()))]""")
            check(fonts == ["Inter"], f"{tag}: one typeface {fonts}")
            tiny = pg.evaluate("""() => [...document.querySelectorAll('.conf-page *')].filter(e => e.offsetParent && [...e.childNodes].some(n => n.nodeType===3 && n.textContent.trim()) && parseFloat(getComputedStyle(e).fontSize) < 13)
                .map(e => e.textContent.trim().slice(0,24)).slice(0,6)""")
            check(not tiny, f"{tag}: no text below 13px {tiny or ''}")
            bad = pg.evaluate(CONTRAST, ".conf-page *")
            check(not bad, f"{tag}: WCAG contrast {[(x['t'], x['r']) for x in bad][:8] or ''}")
            small = pg.evaluate("[...document.querySelectorAll('.conf-page .btn')].filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).length")
            check(small == 0, f"{tag}: buttons >= 44px ({small} smaller)")
            if w == 1920:
                hh = pg.evaluate("Math.round(document.querySelector('.conf-page .hero').getBoundingClientRect().height)")
                check(hh <= 860, f"{tag}: hero sized to its content ({hh}px, was 1080)")
                if A.shots: pg.screenshot(path=f"{A.shots}/conference-{w}.png", full_page=True)
            pg.context.close()
        pg = page(b, C, 1920, 1080)
        check(pg.evaluate("document.querySelectorAll('video').length") == 0, "conference: no autoplay background video (5.3 MB)")
        check(not pg.is_visible("#cd"), "conference: no per-second countdown")
        txt = pg.inner_text("body")
        check("Two campuses" not in txt and "Two Days, Two Campuses" not in txt, "conference: no stale 'two campuses' copy")
        dl = pg.evaluate("[...document.querySelectorAll('.dl-card')].map(a => a.tagName + ' ' + (a.getAttribute('href')||''))")
        check(len(dl) == 2 and all(x.startswith("A https://") for x in dl), f"conference: both download cards are real links ({len(dl)})")
        pg.hover(".mq")
        check(pg.evaluate("getComputedStyle(document.querySelector('.mq__track')).animationPlayState") == "paused", "conference: logo marquee pauses on hover")
        pg.click("#cf-btn")
        err = pg.inner_text("#cf-ok"); check("valid email" in err and "sent" not in err.lower(), f"conference form: empty submit explains what to fix ('{err[:40]}')")
        check(pg.evaluate("document.activeElement.id") == "cf-email", "conference form: focus moves to the field to fix")
        pg.fill("#cf-first", "Test"); pg.fill("#cf-email", "test@example.org"); pg.select_option("#cf-type", "Sponsorship"); pg.fill("#cf-message", "Hello")
        pg.evaluate("window.__nav=[]; const o=Object.getOwnPropertyDescriptor(window,'location');")
        pg.route("**/*", lambda r: r.continue_())
        pg.click("#cf-btn")
        url = pg.evaluate("document.getElementById('cf-btn').getAttribute('data-mailto') || ''")
        check(url.startswith("mailto:info@ac-tlc.org?subject=ACTLC%202027%20conference%3A%20Sponsorship") and "Hello" in url, "conference form: opens a real email to info@ac-tlc.org (no fake 'sent')")
        check("email app" in pg.inner_text("#cf-ok"), "conference form: says what actually happens")
        pg.context.close()
        pg = page(b, C, 1280, 800, reduced_motion="reduce")
        check(pg.evaluate("getComputedStyle(document.querySelector('.mq__track')).animationName") == "none", "conference: marquee still for reduced motion")
        check(pg.evaluate("[...document.querySelectorAll('.conf-page [data-r]')].every(e => getComputedStyle(e).opacity === '1')"), "conference: reduced motion shows content without reveal")
        pg.context.close()

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
    b.close()

print(f"\n{len(fails)} failure(s)")
print("CHECKS_PASSED" if not fails else "CHECKS_FAILED")
sys.exit(1 if fails else 0)
