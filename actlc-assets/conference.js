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
    // On the hero nothing is current yet.
    var hero = document.getElementById('overview');
    if (hero) new IntersectionObserver(function (es) { if (es[0].isIntersecting) links.forEach(function (a) { a.removeAttribute('aria-current'); }); }, { rootMargin: '-40% 0px -55% 0px' }).observe(hero);
  }

  // 3. Countdown to the opening session: days, hours, minutes; updates once a minute, no ticking seconds.
  var cd = root.querySelector('.acx-c-count');
  if (cd) {
    var start = Date.parse(cd.getAttribute('data-start'));
    var tick = function () {
      var ms = start - Date.now();
      if (isNaN(start) || ms <= 0) { cd.hidden = true; return; }
      var m = Math.floor(ms / 6e4), v = { d: Math.floor(m / 1440), h: Math.floor(m / 60) % 24, m: m % 60 };
      ['d', 'h', 'm'].forEach(function (u) { cd.querySelector('[data-u="' + u + '"]').textContent = v[u]; });
      cd.hidden = false;
    };
    tick(); setInterval(tick, 30000);
  }

  // 3b. Key dates: how far away each date is (calendar days, UAE time), the next one large, and the rail filled up to today.
  var kd = root.querySelector('.acx-c-kd');
  if (kd) {
    var uae = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Dubai', year: 'numeric', month: '2-digit', day: '2-digit' });
    var today = Date.parse(uae.format(Date.now())), DAY = 864e5;
    var rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    var steps = Array.prototype.slice.call(kd.querySelectorAll('.acx-c-dates [data-date]'));
    var at = steps.map(function (li) { return Date.parse(li.getAttribute('data-date')); });
    var next = -1;
    steps.forEach(function (li, i) {
      var d = Math.round((at[i] - today) / DAY), rel = li.querySelector('.acx-c-rel');
      rel.textContent = d < 0 ? 'Done' : d === 0 ? 'Today' : rtf.format(d, 'day');
      rel.hidden = false;
      li.classList.toggle('is-done', d < 0);
      if (d >= 0 && next < 0) { next = i; li.classList.add('is-next'); li.setAttribute('aria-current', 'step'); }
    });
    // rail: dots sit evenly, so fill by step index plus the share of the gap already behind us
    var p = next < 0 ? 1 : next === 0 ? 0 : (next - 1 + (today - at[next - 1]) / (at[next] - at[next - 1])) / (steps.length - 1);
    kd.querySelector('.acx-c-dates').style.setProperty('--p', Math.max(0, Math.min(1, p)).toFixed(4));
    var card = kd.querySelector('.acx-c-kd-next');
    if (next >= 0) {
      var li = steps[next], d = Math.round((at[next] - today) / DAY);
      card.querySelector('.acx-c-kd-k').textContent = li.classList.contains('is-goal') ? 'Next' : 'Next deadline';
      card.querySelector('.acx-c-kd-days').textContent = d === 0 ? 'Today' : d === 1 ? '1 day left' : d + ' days left';
      card.querySelector('.acx-c-kd-n').hidden = false;
      card.querySelector('.acx-c-kd-t b').textContent = Array.prototype.map.call(li.querySelectorAll('b'), function (b) { return b.textContent; }).join(' · ');
      var t = card.querySelector('.acx-c-kd-t time'); t.setAttribute('datetime', li.getAttribute('data-date'));
      t.textContent = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }).format(at[next]);
    } else card.hidden = true;
  }

  // 4. Programme: Day 1 / Day 2 segmented control (WAI-ARIA tabs, automatic activation).
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
