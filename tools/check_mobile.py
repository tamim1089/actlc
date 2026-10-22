#!/usr/bin/env python3
"""Phone-width checks for the mobile version, and a desktop guard. Needs a local server:
     python3 -m http.server 8899 &
     python3 tools/check_mobile.py [--only chrome,home,events,conference,resources,registration] [--shots DIR]
     python3 tools/check_mobile.py --baseline DIR       # save 1440px screenshots of every public page
     python3 tools/check_mobile.py --desktop-diff DIR   # compare against them; prints DESKTOP_SAME
   Prints MOBILE_OK only when every selected check passes."""
import argparse, datetime as dt, importlib, os, pkgutil, sys, types
from playwright.sync_api import sync_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ap = argparse.ArgumentParser()
ap.add_argument("--only", default=""); ap.add_argument("--shots"); ap.add_argument("--baseline"); ap.add_argument("--desktop-diff")
ap.add_argument("--base", default="http://localhost:8899")
A = ap.parse_args(); ONLY = set(filter(None, A.only.split(",")))
run = lambda s: not ONLY or s in ONLY
BASE = A.base
PAGES = {"home": "/index.html", "events": "/events/index.html", "designing": "/events-main/designing-ai-ready-graduates/index.html",
         "teaching": "/events-main/teaching-the-learner-not-the-label/index.html", "conference": "/conference/index.html",
         "resources": "/resources/index.html", "registration": "/registration/index.html"}
CLOCK = dt.datetime(2026, 10, 22, 12, 0, tzinfo=dt.timezone(dt.timedelta(hours=4)))   # fixed, so screenshots compare
fails = []

def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond: fails.append(msg)

SETTLE = """async () => { document.documentElement.classList.remove('acx-rv');
  for (let y = 0; y < document.body.scrollHeight; y += 500) { scrollTo(0, y); await new Promise(r => setTimeout(r, 80)); }
  scrollTo(0, 0);
  const waiting = () => [...document.images].filter(i => i.getClientRects().length && getComputedStyle(i).visibility !== 'hidden')
    .filter(i => !i.complete || !i.currentSrc || !i.naturalWidth);   // a lazy image without its real source yet counts as waiting
  for (let t = 0; t < 150 && waiting().length; t++) await new Promise(r => setTimeout(r, 100));   // up to 15s
  document.querySelectorAll('.swiper, .swiper-container').forEach(e => { const s = e.swiper; if (!s) return;   // autoplaying carousels hold still on their first slide
    if (s.autoplay) s.autoplay.stop(); if (s.params && s.params.loop) s.slideToLoop(0, 0, false); else s.slideTo(0, 0, false); });
  await new Promise(r => setTimeout(r, 200));
  document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} }); }"""

def open_page(b, path, w, h, **ctx):
    c = b.new_context(viewport={"width": w, "height": h}, timezone_id="Asia/Dubai", **ctx)
    pg = c.new_page(); pg.clock.install(time=CLOCK); pg.goto(BASE + path, wait_until="load"); pg.wait_for_timeout(400)
    return pg

def phone(b, path, **ctx):
    return open_page(b, path, 390, 844, device_scale_factor=2, is_mobile=True, has_touch=True, **ctx)

def desktop_shots(b, out):
    os.makedirs(out, exist_ok=True)
    for name, path in PAGES.items():
        pg = open_page(b, path, 1440, 900); pg.evaluate(SETTLE); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(300)
        pg.screenshot(path=os.path.join(out, f"{name}.png"), full_page=True, animations="disabled"); pg.context.close()

with sync_playwright() as p:
    b = p.chromium.launch()

    if A.baseline:
        desktop_shots(b, A.baseline); print("BASELINE_SAVED", A.baseline); b.close(); sys.exit(0)

    if A.desktop_diff:
        from PIL import Image, ImageChops
        tmp = A.desktop_diff.rstrip("/") + "-now"; desktop_shots(b, tmp)
        for name in PAGES:
            a, c = Image.open(os.path.join(A.desktop_diff, f"{name}.png")).convert("RGB"), Image.open(os.path.join(tmp, f"{name}.png")).convert("RGB")
            if a.size != c.size:
                check(False, f"desktop {name}: page size changed {a.size} -> {c.size}"); continue
            diff = ImageChops.difference(a, c).convert("L").point(lambda v: 255 if v > 24 else 0)
            share = sum(diff.histogram()[255:]) / (a.size[0] * a.size[1])
            check(share <= 0.002, f"desktop {name}: {share:.4%} of pixels changed (limit 0.2%)")
        b.close(); print(f"\n{len(fails)} failure(s)"); print("DESKTOP_SAME" if not fails else "DESKTOP_CHANGED"); sys.exit(1 if fails else 0)

    import mobile_checks
    sections = {}
    for m in pkgutil.iter_modules(mobile_checks.__path__):
        sections.update(importlib.import_module(f"mobile_checks.{m.name}").SECTIONS)
    ctx = types.SimpleNamespace(b=b, check=check, PAGES=PAGES, BASE=BASE, phone=lambda path, **o: phone(b, path, **o), shots=A.shots)
    unknown = ONLY - set(sections)
    check(not unknown, f"sections exist {sorted(unknown) or ''} (have {sorted(sections)})")
    for name, fn in sections.items():
        if run(name): fn(ctx)
    b.close()

print(f"\n{len(fails)} failure(s)")
print("MOBILE_OK" if not fails else "MOBILE_FAILED")
sys.exit(1 if fails else 0)
