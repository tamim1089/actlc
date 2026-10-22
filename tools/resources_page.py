"""Resources page generator: tools/resources.json + resources/files/*.pdf -> resources/index.html.
The mirrored page was only the WordPress members login, so the first run takes the header and
footer from the events page; later runs replace the generated block in place."""
import html, json, os, re, subprocess

esc = lambda s: html.escape(s, quote=True)
ROOT_CLASS = '<div class="acx acx-res-root"'
THUMB_W = 260   # px; shown at about 110-125 CSS px, so 2x for sharp screens


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def size_label(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{round(n / 1e3)} KB"


def thumb(root, name):
    """First page of the PDF as a WebP, made once and remade only when the PDF changes."""
    from PIL import Image
    pdf = os.path.join(root, "resources", "files", name)
    out = os.path.join(root, "resources", "files", "thumbs", name[:-4] + ".webp")
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(pdf):
        os.makedirs(os.path.dirname(out), exist_ok=True)
        png = out[:-5]
        subprocess.run(["pdftoppm", "-f", "1", "-l", "1", "-singlefile", "-png",
                        "-scale-to-x", str(THUMB_W), "-scale-to-y", "-1", pdf, png], check=True)
        Image.open(png + ".png").convert("RGB").save(out, "WEBP", quality=80, method=6)
        os.remove(png + ".png")
    w, h = Image.open(out).size
    return f"files/thumbs/{name[:-4]}.webp", w, h


def item(root, r):
    pdf = f"files/{r['file']}"
    src, w, h = thumb(root, r["file"])
    size = size_label(os.path.getsize(os.path.join(root, "resources", pdf)))
    source = ""
    if r.get("source") or r.get("doi"):
        doi = f'<a href="https://doi.org/{esc(r["doi"])}">doi.org/{esc(r["doi"])}</a>' if r.get("doi") else ""
        cite = f'<span class="acx-res-cite">{esc(r["source"])}</span>' if r.get("source") else ""
        sep = '<span class="acx-res-sep"> · </span>'
        source = f'<p class="acx-res-src">{sep.join(x for x in (cite, doi) if x)}</p>'
    return f"""<li class="acx-res" id="res-{slug(r['file'][:-4])}">
<a class="acx-res-thumb" href="{pdf}" tabindex="-1" aria-hidden="true"><img src="{src}" width="{w}" height="{h}" alt="" loading="lazy" decoding="async"/></a>
<div class="acx-res-body">
<p class="acx-res-kind">{esc(r['kind'])}</p>
<h3 class="acx-title"><a href="{pdf}">{esc(r['title'])}</a></h3>
<p class="acx-res-by">{esc(r['authors'])}</p>
{source}
<p class="acx-res-sum">{esc(r['summary'])}</p>
</div>
<div class="acx-act"><a class="acx-btn" href="{pdf}">Open PDF</a><a class="acx-res-dl" href="{pdf}" download>Download<span class="acx-res-meta"> · <span class="acx-res-pages">{r['pages']} pages, </span>{size}</span></a></div>
</li>"""


def resources_html(root, data, email):
    groups = {}
    for r in data["items"]:
        groups.setdefault(r["institution"], []).append(r)
    out = []
    for inst in sorted(groups):
        gid = "acx-res-" + slug(inst)
        out.append(f'<section class="acx-res-group" aria-labelledby="{gid}"><h2 class="acx-h2" id="{gid}">{esc(inst)}</h2>\n'
                   f'<ol class="acx-list acx-res-list">\n' + "\n".join(item(root, r) for r in groups[inst]) + "\n</ol></section>")
    return f"""<div class="acx acx-res-root" id="acx-resources">
<p class="acx-res-lead">{esc(data['lead'])}</p>
{chr(10).join(out)}
<p class="acx-res-more">To share your institution's practice, email <a href="mailto:{email}">{email}</a>.</p>
</div>"""


def shell(root):
    """Header and footer from the events page, with the head and menu pointed at Resources."""
    h = open(os.path.join(root, "events", "index.html"), encoding="utf-8").read()
    a, b = h.find('<div class="site-content" id="content">'), h.find('<div class="acx acx-footer">')
    assert a > 0 and b > a, "events page shell not found"
    head, tail = h[:a], h[b:]
    head = re.sub(r"<title>[^<]*</title>", "<title>Resources | Arab Consortium</title>", head, 1)
    head = re.sub(r'<meta content="[^"]*" property="og:title"/>', '<meta content="Resources | Arab Consortium" property="og:title"/>', head)
    head = re.sub(r'<meta content="[^"]*" property="og:description"/>', "", head)
    head = re.sub(r'<meta content="[^"]*" name="description"/>\n?', "", head)
    head = head.replace('content="https://www.ac-tlc.org/events/" property="og:url"', 'content="https://www.ac-tlc.org/resources/" property="og:url"')
    head = re.sub(r'<script class="yoast-schema-graph"[^>]*>[\s\S]*?</script>\n?', "", head)
    head = re.sub(r'<script type="application/ld\+json" id="acx-events-jsonld">[\s\S]*?</script>\n?', "", head)
    head = re.sub(r'\b(?:page-id|elementor-page)-5110\b ?| ?\bacx-page-list\b', "", head)
    head = head.replace(" current-menu-item", "").replace(' aria-current="page"', "")
    head = re.sub(r'(<li class="[^"]*\bmenu-item-4722\b)', r"\1 current-menu-item", head)
    head = head.replace('</head>', '<meta content="Teaching and learning practice shared by ACTLC member universities." name="description"/>\n</head>', 1)
    return head + f"""<div class="site-content" id="content">
<div class="bb-yoast-breadcrumbs" id="breadcrumbs"><span><span><a href="../index.html">Home</a></span> » <span aria-current="page" class="breadcrumb_last">Resources</span></span></div>
<div class="container">
<div class="bb-grid site-content-grid">
<div class="content-area bb-grid-cell" id="primary">
<main class="site-main" id="main">
<article class="page type-page status-publish hentry" id="post-resources">
<header class="entry-header"><h1 class="entry-title">Resources</h1></header>
<div class="entry-content">
{ROOT_CLASS}></div>
</div><!-- .entry-content -->
</article>
</main><!-- #main -->
</div><!-- #primary -->
</div><!-- .bb-grid -->
</div><!-- .container -->
</div><!-- #content -->
""" + tail


def build_resources(root, block_span, email):
    data = json.load(open(os.path.join(root, "tools", "resources.json"), encoding="utf-8"))
    p = os.path.join(root, "resources", "index.html")
    h = open(p, encoding="utf-8").read()
    if ROOT_CLASS not in h:      # first run: the mirrored members-login page
        assert "wp-login" in h or "Log In" in h, "unexpected resources page"
        h = shell(root)
    s, e = block_span(h, h.find(ROOT_CLASS))
    h = h[:s] + resources_html(root, data, email) + h[e:]
    open(p, "w", encoding="utf-8").write(h)
    return p
