"""Phone versions of the legacy home sections, parsed from index.html itself, so editing the page once updates both.

Each block goes inside its legacy Elementor container, as the first child, between <!--acx-mh:NAME--> markers; a rebuild
strips the old blocks first and parses the legacy markup again. actlc-assets/mobile-home.css shows the blocks and hides
the legacy widgets at <= 760px only (the containers stay, so #founding-members and CSS `order` keep working).
Every parser raises when it finds nothing, so a changed page fails the build instead of shipping an empty section.

Blocks: hero (tagline + two actions on a plain teal gradient), objectives (disclosure rows), mission & vision (segmented
control) and values (disclosure rows), founding members (roles as a grouped list, logos as a grid), board (list rows of
people, like the conference committee), FAQ (disclosure rows), and one small script for the segmented control."""
import html
import re
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
MARK = re.compile(r"<!--acx-mh:([a-z]+)-->[\s\S]*?<!--/acx-mh:\1-->")


# ---------------------------------------------------------------- a small tree from the stdlib parser
class Node:
    def __init__(self, tag, attrs, parent=None):
        self.tag, self.attrs, self.parent, self.kids = tag, dict(attrs), parent, []

    def cls(self):
        return (self.attrs.get("class") or "").split()

    def walk(self):
        for k in self.kids:
            if isinstance(k, Node):
                yield k
                yield from k.walk()

    def all(self, tag=None, cls=None, **attrs):
        return [n for n in self.walk() if (tag is None or n.tag == tag) and (cls is None or cls in n.cls())
                and all(n.attrs.get(a.replace("_", "-")) == v for a, v in attrs.items())]

    def first(self, tag=None, cls=None, **attrs):
        r = self.all(tag, cls, **attrs)
        return r[0] if r else None

    def text(self):
        out = []
        for k in self.kids:
            out.append(k.text() if isinstance(k, Node) else k)
            if isinstance(k, Node) and k.tag == "br": out.append("\n")
        return "".join(out)


class _Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = self.cur = Node("#root", {})

    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur); self.cur.kids.append(n)
        if tag not in VOID: self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.kids.append(Node(tag, attrs, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag: n = n.parent
        if n is not self.root: self.cur = n.parent          # stray end tags are ignored

    def handle_data(self, data):
        self.cur.kids.append(data)


def parse(fragment):
    t = _Tree(); t.feed(fragment); t.close(); return t.root


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def esc(s):
    return html.escape(s, quote=True)


def need(items, what):
    if not items: raise ValueError(f"home_mobile: found no {what} in index.html (did the page markup change?)")
    return items


# ---------------------------------------------------------------- locating the legacy containers
def open_tag(h, eid):
    """(start, end) of the opening tag of the Elementor element with data-id eid."""
    m = re.search(r'<div\b[^>]*\bclass="[^"]*\belementor-element-%s\b[^"]*"[^>]*>' % re.escape(eid), h)
    if not m: raise ValueError(f"home_mobile: Elementor element {eid} not found in index.html")
    return m.start(), m.end()


def element(h, eid):
    start, _ = open_tag(h, eid)
    depth = 0
    for m in re.finditer(r"<div\b|</div\s*>", h[start:]):
        depth += 1 if m.group(0).startswith("<div") else -1
        if depth == 0: return parse(h[start:start + m.end()])
    raise ValueError(f"home_mobile: unbalanced markup in element {eid}")


def strip_v(src):
    return re.sub(r"\?v=[0-9a-f]+$", "", src or "")


def pick_src(img, at_least):
    """The smallest srcset candidate at least `at_least` px wide (the shown size at 2x), else src."""
    best = None
    for part in (img.attrs.get("srcset") or "").split(","):
        bits = part.split()
        if len(bits) == 2 and bits[1].endswith("w") and bits[1][:-1].isdigit():
            w = int(bits[1][:-1])
            if w >= at_least and (best is None or w < best[0]): best = (w, bits[0])
    return strip_v(best[1] if best else img.attrs.get("src"))


# ---------------------------------------------------------------- shared pieces
NOTAB = ' tabindex="-1"'


def title(tag, text, hid):
    return f'<{tag} class="acx-mh-title" id="{hid}">{esc(text)}</{tag}>'


def disclosure(cls, items):
    """A grouped list of <details> rows: the summary is the item title, the body its full text (works without JS)."""
    lis = "".join(f'<li><details class="acx-mh-qa"><summary><span>{esc(t)}</span><span class="acx-mh-qchev" aria-hidden="true"></span></summary>'
                  f'<div class="acx-mh-ans">{body}</div></details></li>' for t, body in items)
    return f'<ul class="acx-m-group acx-mh-dis {cls}">{lis}</ul>'


def block(name, inner, label_id=None, extra=""):
    lab = f' aria-labelledby="{label_id}"' if label_id else ""
    return (f'<!--acx-mh:{name}--><section class="acx acx-mh acx-mh-{name}"{lab}{extra}>{inner}</section><!--/acx-mh:{name}-->')


def insert(h, eid, markup):
    _, end = open_tag(h, eid)
    return h[:end] + markup + h[end:]


# ---------------------------------------------------------------- the sections
def hero(h):
    root = element(h, "11da066")
    sl = need(root.all(id="n2-ss-2"), "hero slider #n2-ss-2")[0]
    before, hi = sl.first(cls="n2-ss-highlighted-heading-before"), sl.first(cls="n2-ss-highlighted-heading-highlighted-text")
    tagline = squash((before.text() if before else "") + " " + (hi.text() if hi else ""))
    need(tagline, "hero tagline (.n2-ss-highlighted-heading-before)")
    # the subline: the first sentence of the slider's introduction paragraph
    paras = [squash(p.text()) for p in sl.all("p") if len(squash(p.text())) > 80]
    sub = re.match(r"^(.+?[.!?])(\s|$)", need(paras, "hero introduction paragraph")[0]).group(1)
    return block("hero", f"""<div class="acx-mh-hero-in">
<h1 class="acx-mh-hero-t" id="acx-mh-hero-t">{esc(tagline)}</h1>
<p class="acx-mh-hero-sub">{esc(sub)}</p>
<div class="acx-mh-hero-act"><a class="acx-mh-cta acx-mh-cta-1" href="events/index.html">Webinars</a><a class="acx-mh-cta acx-mh-cta-2" href="conference/index.html">Conference 2027</a></div>
</div>""", "acx-mh-hero-t")


def objectives(h):
    root = element(h, "0ccfaf6")
    sl = need(root.all(id="n2-ss-4"), "objectives slider #n2-ss-4")[0]
    slides = need([s for s in sl.all("div", "n2-ss-slide") if s.attrs.get("data-slide-public-id")], "objective slides")
    eyebrow, items = "", []
    for s in slides:
        texts = [squash(t.text()) for t in s.all(cls="n2-ss-text")]
        eyebrow = eyebrow or next((t for t in texts if t.lower() == "our objectives"), "")
        head = next((t for t in texts if t and t.lower() != "our objectives"), "") or squash(s.attrs.get("data-title", ""))
        points = []
        for li in s.all("li"):
            t = squash(li.text())
            if not t: continue
            if t.startswith("•") or not points: points.append(t.lstrip("• ").strip())
            else: points[-1] += " " + t                     # a line the editor broke off the bullet above
        need(points, f"points in objective '{head}'")
        items.append((head, '<ul class="acx-mh-points">' + "".join(f"<li>{esc(p)}</li>" for p in points) + "</ul>"))
    name = eyebrow.title() if eyebrow else "Our Objectives"
    return block("objectives", title("h2", name, "acx-mh-obj-t") + disclosure("acx-mh-objs", items), "acx-mh-obj-t")


def mission_values(h):
    root = element(h, "0d91c55")
    head = squash(need(root.all("h2"), "Mission & Vision heading")[0].text())
    tabs = root.first(cls="bb-tabs")
    names = need([squash(t.text()) for t in tabs.all(cls="bb-tabs__nav-title")] if tabs else [], "Mission/Vision tab names")
    texts = [" ".join(squash(p.text()) for p in e.all("p")) or squash(e.text()) for e in tabs.all(cls="bb-tabs__excerpt")]
    need(texts, "Mission/Vision panel texts")
    if len(names) != len(texts): raise ValueError("home_mobile: Mission/Vision tab and panel counts differ")
    seg = "".join(f'<button type="button" role="tab" class="acx-mh-seg-b" id="acx-mh-tab-{i}" aria-controls="acx-mh-pan-{i}" '
                  f'aria-selected="{"true" if i == 0 else "false"}"{"" if i == 0 else NOTAB}>{esc(n)}</button>'
                  for i, n in enumerate(names))
    pans = "".join(f'<div class="acx-mh-pan" role="tabpanel" id="acx-mh-pan-{i}" aria-labelledby="acx-mh-tab-{i}">'
                   f'<h3 class="acx-mh-pan-h">{esc(n)}</h3><p>{esc(t)}</p></div>' for i, (n, t) in enumerate(zip(names, texts)))
    # Values: the nested carousel's icon boxes (title + paragraph); the decorative icons stay out
    car = need(root.all(cls="elementor-widget-n-carousel"), "Values carousel")[0]
    vhead = squash(root.all("h2")[-1].text())             # the heading above the carousel ("Values")
    vals = []
    for box in car.all(cls="elementor-icon-box-content"):
        t, d = box.first(cls="elementor-icon-box-title"), box.first(cls="elementor-icon-box-description")
        if t is None or d is None: continue
        vals.append((squash(t.text()), f"<p>{esc(squash(d.text()))}</p>"))
    need(vals, "values (icon boxes in the Values carousel)")
    inner = (title("h2", head, "acx-mh-mv-t") +
             f'<div class="acx-mh-seg"><div class="acx-mh-seg-l" role="tablist" aria-label="{esc(head)}" hidden>{seg}</div>'
             f'<div class="acx-mh-sheet">{pans}</div></div>' +
             title("h2", vhead, "acx-mh-val-t") + disclosure("acx-mh-vals", vals))
    return block("mission", inner, "acx-mh-mv-t")


def founding(h):
    root = element(h, "b863369")
    head = squash(need(root.all("h2"), "Founding Members heading")[0].text())
    intro = need(root.all(cls="elementor-widget-text-editor"), "Founding Members intro")[0]
    intro_html = "".join(f"<p>{inline(p)}</p>" for p in intro.all("p")) or f"<p>{esc(squash(intro.text()))}</p>"
    grid = need(root.all(cls="e-grid"), "founding roles grid")[0]
    rows = []
    for box in grid.all(cls="elementor-widget-image-box"):
        d = box.first(cls="elementor-image-box-description")      # the line-art icon beside it stays out
        if d is None or not squash(d.text()): continue
        rows.append(f'<li><div class="acx-m-row acx-mh-role"><p>{esc(squash(d.text()))}</p></div></li>')
    need(rows, "founding member roles (image boxes)")
    car = need(root.all(cls="elementor-widget-image-carousel"), "member logo carousel")[0]
    seen, logos = set(), []
    for img in car.all("img"):
        src = strip_v(img.attrs.get("src") or img.attrs.get("data-src"))
        if not src or src in seen: continue                    # Swiper's loop clones repeat slides
        seen.add(src)
        logos.append(f'<li class="acx-mh-logo"><img src="{esc(src)}" width="595" height="331" alt="{esc(img.attrs.get("alt", ""))}" '
                     f'loading="lazy" decoding="async"/></li>')
    need(logos, "member logos")
    inner = (title("h2", head, "acx-mh-fm-t") + f'<div class="acx-mh-lead">{intro_html}</div>' +
             f'<ul class="acx-m-group acx-mh-roles">{"".join(rows)}</ul>' +
             f'<h3 class="acx-m-gh acx-mh-gh" id="acx-mh-logos-h">Member institutions</h3>'
             f'<ul class="acx-mh-logos" aria-labelledby="acx-mh-logos-h">{"".join(logos)}</ul>')
    return block("founding", inner, "acx-mh-fm-t")


def board(h):
    root = element(h, "a24525e")
    head = squash(need(root.all("h2"), "Board heading")[0].text())
    intro = next((squash(w.text()) for w in root.all(cls="elementor-widget-heading") if w.first("h2") is None), "")
    people = []
    for d in root.all(cls="director"):
        name, desc, img = d.first(cls="elementor-image-box-title"), d.first(cls="elementor-image-box-description"), d.first("img")
        if name is None: continue
        b = desc.first("b") if desc is not None else None
        role = squash(b.text()) if b is not None else ""
        lines = [squash(l).rstrip(",") for l in (desc.text() if desc is not None else "").split("\n")]
        lines = [l for l in lines if l and l != role]
        ph = (f'<img class="acx-mh-ph" src="{esc(pick_src(img, 112))}" width="72" height="90" alt="" loading="lazy" decoding="async"/>'
              if img is not None else '<span class="acx-mh-ph" aria-hidden="true"></span>')
        people.append(f'<li class="acx-mh-person">{ph}<div class="acx-mh-who"><h3 class="acx-mh-name">{esc(squash(name.text()))}</h3>'
                      + (f'<p class="acx-mh-role-t">{esc(role)}</p>' if role else "")
                      + "".join(f'<p class="acx-mh-org">{esc(l)}</p>' for l in lines) + "</div></li>")
    need(people, "board members (.director)")
    inner = (title("h2", head, "acx-mh-bd-t") + (f'<p class="acx-mh-lead">{esc(intro)}</p>' if intro else "") +
             f'<ul class="acx-m-group acx-mh-people" aria-labelledby="acx-mh-bd-t">{"".join(people)}</ul>')
    return block("board", inner, "acx-mh-bd-t")


ALLOWED = {"p", "ul", "ol", "li", "strong", "b", "em", "i", "br", "a"}


def inline(node):
    """Inner HTML of node with only plain text formatting and links kept."""
    out = []
    for k in node.kids:
        if not isinstance(k, Node): out.append(html.escape(k, quote=False)); continue
        inner = inline(k)
        if k.tag not in ALLOWED: out.append(inner)
        elif k.tag == "br": out.append("<br/>")
        elif k.tag == "a":
            href = k.attrs.get("href")
            out.append(f'<a href="{esc(href)}">{inner}</a>' if href else inner)
        else: out.append(f"<{k.tag}>{inner}</{k.tag}>")
    return "".join(out)


def faq(h):
    root = element(h, "a40434b")
    head = squash(need(root.all("h2"), "FAQ heading")[0].text())
    rows = []
    for item in root.all(cls="elementor-toggle-item"):
        q, a = item.first(cls="elementor-toggle-title"), item.first(cls="elementor-tab-content")
        if q is None or a is None: continue
        qt = re.sub(r"^\d+\.\s*", "", squash(q.text()))        # the list order already numbers them
        ans = re.sub(r"\s+", " ", inline(a)).strip()
        rows.append((qt, ans))
    need(rows, "FAQ items (.elementor-toggle-item)")
    inner = title("h2", head, "acx-mh-faq-t") + disclosure("acx-mh-faqs", rows)
    return block("faq", inner, "acx-mh-faq-t")


# Segmented control (tabs with arrow keys). Without it Mission and Vision simply stack.
JS = r"""(function(){
[].forEach.call(document.querySelectorAll('.acx-mh-seg'),function(seg){
 var list=seg.querySelector('[role=tablist]'),tabs=[].slice.call(seg.querySelectorAll('[role=tab]'));if(!list||!tabs.length)return;
 function pick(i,focus){tabs.forEach(function(t,k){var on=k===i;t.setAttribute('aria-selected',on?'true':'false');t.tabIndex=on?0:-1;
  document.getElementById(t.getAttribute('aria-controls')).hidden=!on;});if(focus)tabs[i].focus();}
 tabs.forEach(function(t,i){t.addEventListener('click',function(){pick(i)});
  t.addEventListener('keydown',function(e){var n=tabs.length,j={ArrowRight:i+1,ArrowLeft:i-1+n,Home:0,End:n-1}[e.key];
   if(j===undefined)return;e.preventDefault();pick(j%n,true);});});
 list.hidden=false;seg.classList.add('is-js');pick(0);
});
})();"""


def home_mobile(h):
    h = MARK.sub("", h)
    h = insert(h, "11da066", hero(h))
    h = insert(h, "0ccfaf6", objectives(h))
    h = insert(h, "0d91c55", mission_values(h))
    h = insert(h, "b863369", founding(h))
    h = insert(h, "a24525e", board(h))
    h = insert(h, "a40434b", faq(h) + f'<!--acx-mh:js--><script id="acx-mh-js">{JS}</script><!--/acx-mh:js-->')
    return h
