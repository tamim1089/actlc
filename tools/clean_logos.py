#!/usr/bin/env python3
"""Cut clean member logos out of the conference marquee cards (which bake in a card frame,
   a flag and sometimes a label strip). Labels are rendered as real text instead."""
import json, os
from PIL import Image
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = json.load(open(os.path.join(ROOT, "tools", "conference.json"), encoding="utf-8"))
for l in d["logos"]:
    src = os.path.normpath(os.path.join(ROOT, "conference", l["src"]))
    a = np.asarray(Image.open(src).convert("RGB")).astype(int); H, W, _ = a.shape
    from scipy import ndimage
    mask = np.sqrt(((255 - a) ** 2).sum(axis=2)) > 38                     # anything not white
    lab, n = ndimage.label(mask)
    keep = np.zeros_like(mask); rows = []
    for i, sl in enumerate(ndimage.find_objects(lab), 1):
        y0_, y1_, x0_, x1_ = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        touches_edge = x0_ <= 1 or y0_ <= 1 or x1_ >= W - 3 or y1_ >= H - 1   # card frame, shadow, label strip
        in_flag_corner = x1_ <= 115 and y1_ <= 85                              # country flag
        px = a[lab == i]; mean = px.mean(axis=0)
        teal_strip = y0_ > 0.75 * H and mean[1] > 170 and mean[2] > 170 and mean[0] < mean[1] - 50   # cyan label-strip fragments (incl. anti-aliased edges)
        rows.append(i) if teal_strip else None
        if touches_edge or in_flag_corner or teal_strip or (lab[sl] == i).sum() < 8: continue
        keep |= lab == i
    mask = keep
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = max(ys.min() - 6, 0), min(ys.max() + 7, H), max(xs.min() - 6, 0), min(xs.max() + 7, W)
    crop = a[y0:y1, x0:x1].astype(np.uint8)
    alpha = np.clip((np.sqrt(((255 - crop.astype(int)) ** 2).sum(axis=2)) - 6) * 6, 0, 255).astype(np.uint8)
    out = Image.fromarray(np.dstack([crop, alpha]), "RGBA")
    dst = os.path.join(ROOT, "actlc-assets", "logos", l["key"] + ".png")
    out.save(dst, optimize=True); l["logo"] = f"actlc-assets/logos/{l['key']}.png"; l["w"], l["h"] = out.size
    print(f"{l['key']:7} {W}x{H} -> {out.size[0]}x{out.size[1]}  strip_removed={bool(len(rows))}  {os.path.getsize(dst)//1024} KB")
json.dump(d, open(os.path.join(ROOT, "tools", "conference.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
