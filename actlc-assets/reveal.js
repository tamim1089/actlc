/* Scroll reveal for every page: blocks fade and rise into place as they come into view,
   and fade back out once they leave it. Content is fully visible without this script and
   for visitors who ask for reduced motion. */
(function () {
  'use strict';
  if (!('IntersectionObserver' in window) || !window.matchMedia || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  var SEL = [
    '.acx-c-head', '.acx-c-2col > *', '.acx-c-track', '.acx-c-day', '.acx-c-person', '.acx-c-cta', '.acx-c-dlrow',
    '.acx-c-tl', '.acx-c-dates > li', '.acx-c-req > *', '.acx-c-plan', '.acx-c-marquee', '.acx-c-contact > div', '.acx-c-sec > .acx-c-in > .acx-c-h2',
    '.acx-list-root .acx-ev', '.acx-month > .acx-h2', '.acx-past-h', '.acx-detail > :not(.acx-bar)', '.acx-home-root .acx-ev',
    '.acx-res-root .acx-res', '.acx-res-group > .acx-h2',
    '.acx-foot-in > *'
  ].join(',');
  var els = Array.prototype.slice.call(document.querySelectorAll(SEL));
  if (!els.length) return;
  // Stagger siblings that come into view together (cards in a row): 70ms apart, at most 6 steps.
  els.forEach(function (el) {
    var i = 0, s = el.previousElementSibling;
    while (s && i < 6) { if (s.matches(SEL)) i++; s = s.previousElementSibling; }
    el.style.setProperty('--rv-i', i % 6);
    el.classList.add('acx-rv-el');
  });
  document.documentElement.classList.add('acx-rv');
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { e.target.classList.toggle('is-in', e.isIntersecting); });
  }, { rootMargin: '0px 0px -6% 0px', threshold: 0.06 });
  els.forEach(function (el) { io.observe(el); });
})();
