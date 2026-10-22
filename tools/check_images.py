#!/usr/bin/env python3
"""Image checks. Needs a local server for --weight:
     python3 -m http.server 8899 &
     python3 tools/check_images.py --weight [--base URL]   # image bytes a phone downloads; prints WEIGHT_OK
     python3 tools/check_images.py --markup                # <picture> markup on disk; prints PICTURES_OK
     python3 tools/check_images.py --sizes                 # rendered widths at 1440 and 390 (feeds SHOWN in images.py)"""
import argparse, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
from images import PAGES, EAGER, local_file

ap = argparse.ArgumentParser()
ap.add_argument("--weight", action="store_true"); ap.add_argument("--markup", action="store_true"); ap.add_argument("--sizes", action="store_true")
ap.add_argument("--base", default="http://localhost:8899")
A = ap.parse_args()
LIMIT = {"index.html": 900, "conference/index.html": 900}           # KB; every other page 400
BEFORE = {"index.html": 640, "events/index.html": 209, "events-main/designing-ai-ready-graduates/index.html": 209,
          "events-main/teaching-the-learner-not-the-label/index.html": 209, "conference/index.html": 7400,
          "resources/index.html": 261, "registration/index.html": 70}   # KB, measured the same way on main 5c16896 (before images.py)

SCROLL = """async () => { for (let y = 0; y < document.body.scrollHeight; y += 400) { scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
  scrollTo(0, document.body.scrollHeight); await new Promise(r => setTimeout(r, 300)); }"""

def weight():
    from playwright.sync_api import sync_playwright
    bad = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for page in PAGES:
            c = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=3, is_mobile=True, has_touch=True)
            got = {}
            def on(r):
                if not r.headers.get("content-type", "").startswith("image/"): return
                try: got[r.url] = len(r.body())
                except Exception: got[r.url] = int(r.headers.get("content-length", 0))
            pg = c.new_page(); pg.on("response", on)
            pg.goto(f"{A.base}/{page}", wait_until="load"); pg.evaluate(SCROLL)
            try: pg.wait_for_load_state("networkidle", timeout=15000)
            except Exception: pass
            pg.wait_for_timeout(500); c.close()
            kb, lim = sum(got.values()) / 1024, LIMIT.get(page, 400)
            ok = kb <= lim; bad += [] if ok else [page]
            before = f"  (before {BEFORE[page]} KB)" if BEFORE.get(page) else ""
            print(f"  {'ok  ' if ok else 'FAIL'} {page}: {kb:.0f} KB in {len(got)} images (limit {lim} KB){before}")
            for u, n in sorted(got.items(), key=lambda x: -x[1])[:int(os.environ.get("TOP", 3))]: print(f"         {n/1024:6.0f} KB {u.replace(A.base, '')}")
        b.close()
    print("WEIGHT_OK" if not bad else "WEIGHT_FAILED"); return not bad

def markup():
    bad = []
    rules, path = {}, None                       # _headers: path -> its header lines
    for line in open(os.path.join(ROOT, "_headers")).read().splitlines():
        if line.strip().startswith("#") or not line.strip(): continue
        if not line[0].isspace(): path = line.strip(); rules[path] = []
        elif path: rules[path].append(line.strip())
    hit = lambda pat, u: re.fullmatch(re.sub(r":\w+", "[^/]+", re.escape(pat).replace(r"\*", ".*").replace(r"\:", ":")), u)
    cc = [p for p, hs in rules.items() if hit(p, "/actlc-assets/img/0123abcd-300.avif") and any(x.lower().startswith("cache-control") for x in hs)]
    if cc != ["/actlc-assets/img/*"] or not re.fullmatch(r"cache-control:\s*public,\s*max-age=31536000,\s*immutable", rules[cc[0]][0], re.I):
        bad.append(f"_headers: Cache-Control rules matching /actlc-assets/img/* are {cc} (want only the immutable one)")
    n = 0
    for page in PAGES:
        h = open(os.path.join(ROOT, page), encoding="utf-8").read()
        h = re.sub(r"<noscript>[\s\S]*?</noscript>|<script\b[\s\S]*?</script>|<template\b[\s\S]*?</template>", "", h)
        d = os.path.dirname(page)
        pics = [(m.start(), m.end(), m.group(0)) for m in re.finditer(r"<picture\b[\s\S]*?</picture>", h)]
        hi = len(re.findall(r'<img\b[^>]*\bfetchpriority="high"', h))
        if hi != 1: bad.append(f"{page}: {hi} images with fetchpriority=high (want 1)")
        for m in re.finditer(r"<img\b[^>]*>", h):
            tag = m.group(0); src = re.search(r'\bsrc="([^"]*)"', tag)
            if not src or not local_file(src.group(1), page): continue
            where = f"{page}: {src.group(1)[:70]}"; n += 1
            if not re.search(r'\bwidth="\d+"', tag) or not re.search(r'\bheight="\d+"', tag): bad.append(where + " has no width/height")
            if "fetchpriority" not in tag and 'loading="lazy"' not in tag and not re.search(EAGER, tag): bad.append(where + " neither lazy nor high priority")
            pic = next((p for p in pics if p[0] < m.start() < p[1]), None)
            if not pic: bad.append(where + " not in a <picture>"); continue
            for t in ("avif", "webp"):
                s = re.search(rf'<source\b[^>]*type="image/{t}"[^>]*srcset="([^"]*)"|<source\b[^>]*srcset="([^"]*)"[^>]*type="image/{t}"', pic[2])
                if not s: bad.append(where + f" has no {t} source"); continue
                for u in (c.split()[0] for c in (s.group(1) or s.group(2)).split(",") if c.strip()):
                    if not os.path.isfile(os.path.normpath(os.path.join(ROOT, d, u.split("?")[0]))): bad.append(where + f" missing {u}")
    for x in bad: print("  FAIL", x)
    print(f"  {n} local raster images checked on {len(PAGES)} pages")
    print("PICTURES_OK" if not bad else "PICTURES_FAILED"); return not bad

SIZES_JS = """() => [...document.images].filter(i => i.getAttribute('src') && !i.closest('noscript')).map(i => {
  const r = i.getBoundingClientRect(); return [i.getAttribute('src'), Math.round(r.width), i.className, i.naturalWidth] })"""

def sizes():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        for page in PAGES:
            for w in (1440, 390):
                c = b.new_context(viewport={"width": w, "height": 900}, is_mobile=w < 500, has_touch=w < 500)
                pg = c.new_page(); pg.goto(f"{A.base}/{page}", wait_until="load"); pg.evaluate(SCROLL); pg.wait_for_timeout(800)
                for src, rw, cls, nw in pg.evaluate(SIZES_JS): print(f"{w}\t{page}\t{rw}\t{nw}\t{src}\t{cls}")
                c.close()
        b.close()

ok = True
if A.sizes: sizes()
if A.weight: ok &= weight()
if A.markup: ok &= markup()
sys.exit(0 if ok else 1)
