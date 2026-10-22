"""Responsive pictures: every local raster <img> gets AVIF and WebP copies at 1x and 2x the width it is shown at.

Copies live in actlc-assets/img/<sha8 of source bytes>-<width>.<avif|webp> and are encoded once (cached by content).
A bare <img> becomes <picture class="acx-pic" style="display:contents"><source avif><source webp><img></picture>;
display:contents keeps the <img> laid out as the same child it was. Smart Slider's own <picture>s get an AVIF
twin (class acx-src) before each of their sources. The first image on the page loads with fetchpriority=high,
every other one lazily (carousel slides stay eager). Known CSS backgrounds get an image-set() rule (BG).
Safe to run repeatedly: our own markup is removed before it is rebuilt."""
import hashlib, math, os, re
from urllib.parse import unquote
from PIL import Image, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = "actlc-assets/img"
PAGES = ["index.html", "events/index.html", "events-main/designing-ai-ready-graduates/index.html",
         "events-main/teaching-the-learner-not-the-label/index.html", "conference/index.html",
         "resources/index.html", "registration/index.html"]
RASTER = (".png", ".jpg", ".jpeg", ".webp")

# CSS px each picture is shown at: (desktop at 1440, phone at 390), measured with tools/check_images.py --sizes.
# Matched against "<class> <src>"; first hit wins. Anything new falls back to its width attribute.
SHOWN = [(r"\bbb-(?:mobile-)?logo\b", 200, 150),          # header logo (one copy serves both, so it downloads once)
         (r"\bacx-c-photo\b", 333, 260),                   # conference speakers and team
         (r"uploads/2025/04/[A-Za-z]+\.webp|logos/cards/", 360, 173),   # home: member cards (desktop carousel, phone list)
         (r"\belementor-animation-grow\b", 150, 150),      # home: board photos (desktop)
         (r"\bacx-mh-ph\b", 96, 96),                       # home: board photos (phone)
         (r"\bacx-mh-role-ic\b", 40, 40),                  # home: what-we-do icons (phone)
         (r"uploads/2025/04/icon-", 114, 108),             # home: what-we-do icons (desktop)
         (r"actlc-assets/logos/", 360, 290),               # conference: member logos (small files, capped at their own width)
         (r"files/thumbs/", 114, 75),                      # resources: document covers
         (r"ACTLC-Logo-03-300x157", 154, 149),             # footer logo
         (r"ACTLC-Logo-White", 600, 220),                  # home slider layers
         (r"slider2/shape10", 102, 102),
         (r"Adobe-Express-file", 464, 464),
         (r"uploads/2025/02/(?:22|23|25|28|29|image-058)\.", 125, 125),
         (r"slider/cache/", 1440, 390)]                    # home slider backgrounds (full width)
# Autoplaying carousel slides stay eager: a lazy image off to the side of a clipped carousel only starts loading
# when its slide moves in, so the slide shows empty for a moment (seen on the home member-cards carousel).
EAGER = r'\bclass="[^"]*\bswiper-slide-image\b'
# Places whose CSS was written for a <picture> box (e.g. .acx-mh-logo > * crops the card); there the picture keeps its box.
PICTURE_BOX = [r'<li class="acx-mh-logo">']
# Pictures cropped into a fixed box (object-fit: cover), with the box's height/width at 1440 and at 390, measured.
# A wide photo fills the box by its height, so it needs more pixels across than the box is wide.
BOXED = [(r'\bclass="[^"]*\bacx-c-photo\b', 383 / 333, 260 / 260),   # 333x383 desktop, 260x260 phone
         (r'\bclass="[^"]*\bacx-mh-ph\b', 1, 1),                       # 96x96
         (r'\bsrc="[^"]*slider/cache/', 900 / 1440, 522 / 390)]       # slider 1440x900 desktop; phone hero 390x522
PHOTO_Q, GRAPHIC_Q, WEBP_Q = 65, 70, 82   # AVIF quality: opaque pictures / logos and art with transparency (kept, full chroma); WebP
# CSS backgrounds: (text the page must contain, selector of the rule that sets the picture, source file, width of the copy).
# A later rule with the same selector adds image-set(AVIF, WebP); a browser without image-set() keeps the original url().
BG = [("background-image:url(https://www.ac-tlc.org/wp-content/uploads/2024/04/ACTLC-login-page-011.png)", ".login-split",
       "wp-content/uploads/2024/04/ACTLC-login-page-011.png", 1200),       # registration: left half, 720x900 desktop, cover
      ("elementor/css/post-5659.", ".elementor-5659 .elementor-element.elementor-element-0d91c55:not(.elementor-motion-effects-element-type-background), "
       ".elementor-5659 .elementor-element.elementor-element-0d91c55 > .elementor-motion-effects-container > .elementor-motion-effects-layer",
       "wp-content/uploads/2025/02/white-abstract-curved-shape-background-vector-copy.png", 1920)]   # home: full-width section

def local_file(src, page):
    """The file on disk behind a local raster URL as written in `page`, else None."""
    if not src or "://" in src or src.startswith(("data:", "//", "/", "<")): return None
    path = unquote(src.split("?")[0].split("#")[0])
    if not path.lower().endswith(RASTER): return None
    f = os.path.normpath(os.path.join(ROOT, os.path.dirname(page), path))
    return f if os.path.isfile(f) else None

_info = {}
def info(f):
    """(sha8, width, height) of a source file; read once per build."""
    if f not in _info:
        data = open(f, "rb").read()
        with Image.open(f) as im:
            w, h = ImageOps.exif_transpose(im).size if im.getexif().get(0x0112, 1) != 1 else im.size
        _info[f] = (hashlib.sha1(data).hexdigest()[:8], w, h)
    return _info[f]

def copy(f, w, fmt):
    """Path (from the site root) of the AVIF/WebP copy of `f` at width `w`; encoded only if missing."""
    key, W, H = info(f)
    rel = f"{OUT}/{key}-{w}.{fmt}"; dst = os.path.join(ROOT, rel)
    if os.path.isfile(dst): return rel
    with Image.open(f) as src:
        icc = src.info.get("icc_profile")
        im = ImageOps.exif_transpose(src)
        alpha = im.mode in ("RGBA", "LA", "PA") or "transparency" in im.info
        im = im.convert("RGBA" if alpha else "RGB")
        if alpha and im.getchannel("A").getextrema() == (255, 255): im, alpha = im.convert("RGB"), False
        if w < W: im = im.resize((w, max(1, round(H * w / W))), Image.LANCZOS)
        os.makedirs(os.path.dirname(dst), exist_ok=True); tmp = dst + ".tmp"
        extra = {"icc_profile": icc} if icc else {}
        if fmt == "avif":
            im.save(tmp, "AVIF", quality=GRAPHIC_Q if alpha else PHOTO_Q, speed=4, subsampling="4:4:4" if alpha else "4:2:0", **extra)
        else:
            im.save(tmp, "WEBP", quality=WEBP_Q, method=6, **extra)
        os.replace(tmp, dst)
    return rel

def shown(tag, src):
    """(desktop px, phone px) the image is shown at."""
    cls = (re.search(r'\bclass="([^"]*)"', tag) or [None, ""])[1]
    for pat, d, p in SHOWN:
        if re.search(pat, cls + " " + src): return d, p
    w = re.search(r'\bwidth="(\d+)"', tag)
    w = int(w.group(1)) if w else 0
    return w, w

def fit(w, W, H):
    """A width at or a little above `w` whose whole-pixel height keeps the source's shape: once loaded, the browser
       sizes height:auto images by the copy's own width/height, so a rounded height would move the page by a pixel."""
    return min(range(w, min(W, w + w // 8) + 1), key=lambda x: abs(round(H * x / W) * W - H * x) / x)

def widths(f, d, p, boxed=False):
    """1x and 2x of the desktop and phone widths, never above the source; nudged to keep the shape unless boxed."""
    _, W, H = info(f)
    ws = sorted({min(x, W) if boxed else fit(min(x, W), W, H) for x in (p, 2 * p, d, 2 * d) if x} or {W})
    return [w for i, w in enumerate(ws) if i + 1 == len(ws) or ws[i + 1] > w * 1.08]   # drop near-duplicates

def sources(f, tag, src, rel):
    """The two <source> tags for an <img>, and (avif srcset, sizes) for a preload."""
    d, p = shown(tag, src)
    if not d: d = p = min(info(f)[1], 1440)          # unknown and no width attribute: at most page width
    box = next(((rd, rp) for pat, rd, rp in BOXED if re.search(pat, tag)), None)
    if box:                                         # pixels across the cropped picture needs (its shape no longer matters)
        _, W, H = info(f); d, p = max(d, math.ceil(d * box[0] * W / H)), max(p, math.ceil(p * box[1] * W / H))
    sizes = f"{d}px" if d == p else f"(max-width: 767px) {p}px, {d}px"
    out = {}
    for fmt in ("avif", "webp"):
        out[fmt] = ", ".join(f"{rel}{copy(f, w, fmt)} {w}w" for w in widths(f, d, p, bool(box)))
    tags = "".join(f'<source type="image/{t}" srcset="{out[t]}" sizes="{sizes}"/>' for t in ("avif", "webp"))
    return tags, (out["avif"], sizes)

def set_attr(tag, name, value):
    tag = re.sub(rf'\s{name}="[^"]*"', "", tag)
    return tag if value is None else re.sub(r"\s*/?>$", f' {name}="{value}"/>', tag)

def fix_img(tag, f, first):
    """Width/height present, and either fetchpriority=high (first image) or lazy + async decoding.
       Width/height, when missing, are the file's own size, which is the size the browser used before."""
    if not re.search(r'\bwidth="\d+"', tag) or not re.search(r'\bheight="\d+"', tag):
        _, W, H = info(f)
        tag = set_attr(set_attr(tag, "width", W), "height", H)
    eager = first or re.search(EAGER, tag)
    tag = set_attr(tag, "fetchpriority", "high" if first else None)   # removed and re-added in a fixed order: same bytes every run
    tag = set_attr(tag, "loading", None if eager else "lazy")
    return set_attr(tag, "decoding", "async")

TOKENS = re.compile(r"<(noscript|script|style|template|textarea)\b[\s\S]*?</\1>|<!--[\s\S]*?-->"
                    r"|<picture\b[^>]*>[\s\S]*?</picture>|<img\b[^>]*>", re.I)
OWN_PIC = re.compile(r'<picture class="acx-pic"[^>]*>[\s\S]*?(<img\b[^>]*>)</picture>')
OWN_SRC = re.compile(r'<source class="acx-src"[^>]*/>')

def picture_images(h, page):
    rel = "../" * page.count("/")
    state = {"first": None}

    def img(m, before):
        tag = m.group(0); src = (re.search(r'\bsrc="([^"]*)"', tag) or [None, ""])[1]
        f = local_file(src, page)
        if not f: return tag
        first = state["first"] is None
        tags, pre = sources(f, tag, src, rel)
        if first: state["first"] = (src, pre)
        # sources hidden too: under display:contents they would count as flex/grid items and add a gap before the image
        tags = tags.replace("<source ", '<source style="display:none" ')
        box = any(re.search(p + "$", before) for p in PICTURE_BOX)
        return f'<picture class="acx-pic"{"" if box else ' style="display:contents"'}>{tags}{fix_img(tag, f, first)}</picture>'

    def foreign(pic):
        """Smart Slider <picture>: an AVIF twin before each of its sources; ours too if every source has a media query."""
        pic = OWN_SRC.sub("", pic)
        im = re.search(r"<img\b[^>]*>", pic); tag = im.group(0) if im else ""
        src = (re.search(r'\bsrc="([^"]*)"', tag) or [None, ""])[1]
        f = local_file(src, page)
        if not f: return pic
        def twin(s):
            t = s.group(0); u = re.search(r'\bsrcset="([^"\s,]+)"', t); sf = u and local_file(u.group(1), page)
            if not sf: return t
            media = re.search(r'\smedia="[^"]*"', t); media = media.group(0) if media else ""
            add = [("avif", copy(sf, info(sf)[1], "avif"))]
            if 'type="image/webp"' not in t: add.append(("webp", copy(sf, info(sf)[1], "webp")))
            return "".join(f'<source class="acx-src"{media} type="image/{x}" srcset="{rel}{u}"/>' for x, u in add) + t
        head = re.sub(r"<source\b[^>]*>", twin, pic[:im.start()])
        first = state["first"] is None
        tags, pre = "", None
        if not re.search(r"<source\b(?![^>]*\smedia=)(?![^>]*acx-src)[^>]*>", head):   # no catch-all source of its own
            tags, pre = sources(f, tag, src, rel); tags = tags.replace("<source ", '<source class="acx-src" ')
        if first: state["first"] = (src, pre)
        return head + tags + fix_img(tag, f, first) + pic[im.end():]

    def tok(m):
        t = m.group(0)
        if m.group(1) or t.startswith("<!--"): return t
        if t.startswith("<picture"):
            own = OWN_PIC.fullmatch(t)
            return img(re.match(r"<img\b[^>]*>", own.group(1)), m.string[max(0, m.start() - 80):m.start()]) if own else foreign(t)
        return img(m, m.string[max(0, m.start() - 80):m.start()])

    h = TOKENS.sub(tok, h)
    h = preload(h, state["first"])
    return backgrounds(h, rel)

def preload(h, first):
    """WP Rocket's logo preload pointed at the live site's PNGs: point it at the AVIF the logo <picture> picks."""
    def sub(m):
        if not first or not first[1]: return ""
        src, (srcset, sizes) = first
        return (f'<link as="image" data-rocket-preload="" fetchpriority="high" href="{src}" imagesizes="{sizes}" '
                f'imagesrcset="{srcset}" rel="preload" type="image/avif"/>')
    return re.sub(r'<link\b[^>]*\bdata-rocket-preload=""[^>]*\bas="image"[^>]*>|<link as="image" data-rocket-preload=""[^>]*>', sub, h)

def backgrounds(h, rel):
    """One <style id="acx-img-bg"> before </head> with AVIF/WebP versions of the known CSS backgrounds."""
    h = re.sub(r'<style id="acx-img-bg">[^<]*</style>\n?', "", h)
    rules = []
    for mark, sel, src, w in BG:
        f = os.path.join(ROOT, src)
        if mark not in h or not os.path.isfile(f): continue
        w = min(w, info(f)[1]); a, b = rel + copy(f, w, "avif"), rel + copy(f, w, "webp")
        rules.append(f'{sel}{{background-image:image-set(url({a}) type("image/avif"),url({b}) type("image/webp"))}}')
    return h.replace("</head>", f'<style id="acx-img-bg">{"".join(rules)}</style>\n</head>', 1) if rules else h
