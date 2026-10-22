"""Phone check sections for tools/check_mobile.py. Each module in this package owns one leaf's checks and exposes
SECTIONS = {"name": fn}; fn(ctx) runs with ctx.b (browser), ctx.phone(path, **opts) -> page, ctx.check(cond, msg),
ctx.PAGES, ctx.BASE. The helpers below are the shared measurements every section uses."""

CONTRAST = r"""(sel) => {
 document.documentElement.classList.remove("acx-rv");
 document.getAnimations().forEach(a => { try { a.finish(); } catch (e) {} });
 const rgba = c => { const m = c.match(/[\d.]+/g).map(Number); return [m[0], m[1], m[2], m[3] === undefined ? 1 : m[3]] };
 const lum = m => { const f = v => { v/=255; return v<=.03928? v/12.92 : Math.pow((v+.055)/1.055,2.4) };
   return .2126*f(m[0]) + .7152*f(m[1]) + .0722*f(m[2]) };
 const bg = el => { for (let e=el; e; e=e.parentElement){ const c=getComputedStyle(e).backgroundColor; const a=(c.match(/[\d.]+/g)||[])[3];
   if (c!=='rgba(0, 0, 0, 0)' && (a===undefined||+a>0.5)) return c } return 'rgb(255,255,255)' };
 const out=[];
 document.querySelectorAll(sel).forEach(el => {
   if (!el.getClientRects().length || (!el.offsetParent && getComputedStyle(el).position!=='fixed')) return;
   if (![...el.childNodes].some(n=>n.nodeType===3 && n.textContent.trim())) return;
   const cs=getComputedStyle(el), B=rgba(bg(el)), F=rgba(cs.color);
   let a=F[3]; for (let e=el; e; e=e.parentElement) a*=+getComputedStyle(e).opacity;
   const mix=[0,1,2].map(i => a*F[i] + (1-a)*B[i]);
   const L1=lum(mix), L2=lum(B);
   const r=(Math.max(L1,L2)+.05)/(Math.min(L1,L2)+.05), px=parseFloat(cs.fontSize), w=+cs.fontWeight;
   out.push({t:el.textContent.trim().slice(0,28), r:+r.toFixed(2), need:(px>=24||(px>=18.66&&w>=700))?3:4.5});
 }); return out.filter(c => c.r < c.need) }"""

# visible interactive elements under `sel` smaller than 44px in either direction
SMALL_TARGETS = r"""(sel) => [...document.querySelectorAll(sel)].filter(e => e.matches('a[href], button, summary, input, select, textarea, [role=tab]'))
  .filter(e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0 && getComputedStyle(e).visibility !== 'hidden'; })
  .filter(e => { const r = e.getBoundingClientRect(); return r.width < 44 || r.height < 44; })
  .map(e => (e.textContent.trim() || e.getAttribute('aria-label') || e.tagName).slice(0, 24) + ' ' + Math.round(e.getBoundingClientRect().width) + 'x' + Math.round(e.getBoundingClientRect().height))"""

# visible text nodes under `sel` set smaller than 13px
SMALL_TEXT = r"""(sel) => [...document.querySelectorAll(sel)].filter(e => e.getClientRects().length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
  .filter(e => parseFloat(getComputedStyle(e).fontSize) < 12.95).map(e => e.textContent.trim().slice(0, 24) + ' ' + getComputedStyle(e).fontSize)"""

# visible text under `sel` that renders in a font other than Inter (serif fallbacks from dropped theme fonts)
WRONG_FONT = r"""(sel) => [...document.querySelectorAll(sel)].filter(e => e.getClientRects().length && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
  .filter(e => !/^\s*"?Inter/i.test(getComputedStyle(e).fontFamily)).map(e => e.textContent.trim().slice(0, 24) + ' [' + getComputedStyle(e).fontFamily.slice(0, 30) + ']')"""

# elements under `sel` whose top or bottom sits under the fixed bars, measured after scrolling each into view
UNDER_BARS = r"""(sel) => [...document.querySelectorAll(sel)].filter(e => e.getClientRects().length).filter(e => {
  e.scrollIntoView({block: 'start'}); const r = e.getBoundingClientRect();
  const top = document.querySelector('.acx-m-top').getBoundingClientRect().bottom;
  return r.top < top - 1; }).map(e => e.textContent.trim().slice(0, 24))"""
