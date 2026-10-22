"""Phone-only short versions of long paragraphs (tools/distil.json). The original paragraph stays where it is and
stays the source: on phones it is hidden and a short line takes its place, with the full text one tap away under
'Read more'. Above 760px the short block never shows, so desktop is untouched."""
import html, json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ITEMS = json.load(open(os.path.join(ROOT, "tools", "distil.json"), encoding="utf-8"))["items"]
text = lambda s: re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


def undistil(h):
    """Remove what distil() added. Runs before anything parses the page, so no builder copies a short version."""
    h = re.sub(r'<div class="acx acx-dst[^"]*">[\s\S]*?</div><!--/acx-dst-->', "", h)
    return re.sub(r'(<p\b[^>]*?) data-dst="1"', r"\1", h)


def distil(h, page):
    h = undistil(h)
    for it in (i for i in ITEMS if i["page"] == page):
        found = 0
        for m in reversed(list(re.finditer(r"<p\b[^>]*>([\s\S]*?)</p>", h))):
            if not text(m.group(1)).startswith(it["starts"]): continue
            found += 1
            short = html.escape(it["short"])
            block = (f'<div class="acx acx-dst{" is-title" if it.get("title") else ""}"><p class="acx-dst-s">{short}</p>'
                     f'<details class="acx-dst-more"><summary>Read more</summary><p>{m.group(1)}</p></details></div><!--/acx-dst-->')
            opening = re.match(r"<p\b[^>]*", m.group(0)).group(0)
            h = h[:m.start()] + block + opening + ' data-dst="1"' + m.group(0)[len(opening):] + h[m.end():]
        if not found:
            raise SystemExit(f"distil: '{it['starts']}' not found on {page}")
    return h
