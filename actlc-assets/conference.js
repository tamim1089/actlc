/* ACTLC conference page: section bar under the site header, current-section highlight,
   and programme day tabs. Without JS the page is complete: both days are listed. */
(function () {
  'use strict';
  var root = document.querySelector('.acx-conf'); if (!root) return;

  // 1. Sit the section bar under the theme header when that header stays on screen.
  function headerOffset() {
    var m = document.getElementById('masthead'), pos = m ? getComputedStyle(m).position : '';
    var h = m && (pos === 'fixed' || pos === 'sticky') ? Math.round(m.getBoundingClientRect().height) : 0;
    root.style.setProperty('--acx-hdr', h + 'px');
  }
  headerOffset(); window.addEventListener('resize', headerOffset);

  // 2. Mark the section in view in the bar (and keep it visible on phones).
  var links = Array.prototype.slice.call(root.querySelectorAll('.acx-local-links a'));
  if ('IntersectionObserver' in window && links.length) {
    var byId = {};
    links.forEach(function (a) { byId[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        links.forEach(function (a) { a.removeAttribute('aria-current'); });
        var a = byId[e.target.id]; if (!a) return;
        a.setAttribute('aria-current', 'true');
        var bar = a.parentNode; bar.scrollLeft = a.offsetLeft - bar.clientWidth / 2 + a.clientWidth / 2;
      });
    }, { rootMargin: '-40% 0px -55% 0px' });
    Object.keys(byId).forEach(function (id) { var s = document.getElementById(id); if (s) io.observe(s); });
  }

  // 3. Programme: Day 1 / Day 2 segmented control (WAI-ARIA tabs, automatic activation).
  var tabs = root.querySelector('.acx-c-tabs');
  if (tabs) {
    var btn = Array.prototype.slice.call(tabs.querySelectorAll('[role="tab"]'));
    var panels = btn.map(function (b) { return document.getElementById(b.getAttribute('aria-controls')); });
    var select = function (i, focus) {
      btn.forEach(function (b, j) {
        var on = i === j; b.setAttribute('aria-selected', on ? 'true' : 'false'); b.tabIndex = on ? 0 : -1; panels[j].hidden = !on;
      });
      if (focus) btn[i].focus();
    };
    btn.forEach(function (b, i) {
      b.addEventListener('click', function () { select(i, false); });
      b.addEventListener('keydown', function (e) {
        var n = btn.length, j = e.key === 'ArrowRight' ? (i + 1) % n : e.key === 'ArrowLeft' ? (i - 1 + n) % n : e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : null;
        if (j !== null) { e.preventDefault(); select(j, true); }
      });
    });
    panels.forEach(function (p) { p.setAttribute('role', 'tabpanel'); });
    root.classList.add('acx-js'); tabs.hidden = false; select(0, false);
  }
})();
