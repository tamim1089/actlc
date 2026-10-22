/* ACTLC conference page: section bar under the site header, current-section highlight, countdown, key dates,
   and on phones (max 760px) the Sections sheet, folded tracks, the Day 1 / Day 2 control and the speakers' swipe buttons.
   Without JS the page is complete: tracks open, both days listed, the sheet opens through #acx-secs. */
(function () {
  'use strict';
  var root = document.querySelector('.acx-conf'); if (!root) return;
  var phone = window.matchMedia('(max-width: 760px)');
  var onPhoneChange = function (fn) { if (phone.addEventListener) phone.addEventListener('change', fn); else if (phone.addListener) phone.addListener(fn); };
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  var all = function (sel, el) { return Array.prototype.slice.call((el || root).querySelectorAll(sel)); };

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

  // 4. Phones: Day 1 / Day 2 segmented control (WAI-ARIA tabs, automatic activation). The CSS hides the other day only
  //    at phone width, so wider screens keep both days side by side; roles follow the width.
  var seg = root.querySelector('.acx-c-seg'), days = root.querySelector('.acx-c-days');
  if (seg && days) {
    var tabBtns = all('[role="tab"]', seg);
    var panels = tabBtns.map(function (b) { return document.getElementById(b.getAttribute('aria-controls')); });
    var select = function (i, focus) {
      tabBtns.forEach(function (b, j) { var on = i === j; b.setAttribute('aria-selected', on ? 'true' : 'false'); b.tabIndex = on ? 0 : -1; panels[j].classList.toggle('is-on', on); });
      if (focus) tabBtns[i].focus();
    };
    tabBtns.forEach(function (b, i) {
      b.addEventListener('click', function () { select(i, false); });
      b.addEventListener('keydown', function (e) {
        var n = tabBtns.length, j = e.key === 'ArrowRight' ? (i + 1) % n : e.key === 'ArrowLeft' ? (i - 1 + n) % n : e.key === 'Home' ? 0 : e.key === 'End' ? n - 1 : null;
        if (j !== null) { e.preventDefault(); select(j, true); }
      });
    });
    var segMode = function () {
      days.classList.toggle('is-seg', phone.matches);
      panels.forEach(function (p, j) {
        if (phone.matches) { p.setAttribute('role', 'tabpanel'); p.setAttribute('aria-labelledby', tabBtns[j].id); }
        else { p.removeAttribute('role'); p.removeAttribute('aria-labelledby'); }
      });
    };
    seg.hidden = false; select(0, false); segMode(); onPhoneChange(segMode);
  }

  // 5. Phones: tracks fold into disclosure rows (open in the HTML, so wider screens and no-JS phones show every topic).
  var tracks = all('.acx-c-tdet');
  var openTarget = function () {
    var t = location.hash.length > 1 && document.getElementById(decodeURIComponent(location.hash.slice(1)));
    var d = t && t.querySelector && t.querySelector('.acx-c-tdet'); if (d) d.open = true;
  };
  var trackMode = function () {
    tracks.forEach(function (d) { d.open = !phone.matches; d.querySelector('summary').tabIndex = phone.matches ? 0 : -1; });
    openTarget();
  };
  tracks.forEach(function (d) { d.querySelector('summary').addEventListener('click', function (e) { if (!phone.matches) e.preventDefault(); }); });
  if (tracks.length) { trackMode(); onPhoneChange(trackMode); window.addEventListener('hashchange', openTarget); }

  // 6. Phones: the Sections sheet (a modal dialog; without JS it opens through #acx-secs) and the current section's name in the bar.
  var sheet = document.getElementById('acx-secs'), opener = root.querySelector('.acx-local-sheet');
  if (sheet && opener && typeof sheet.showModal === 'function') {
    opener.addEventListener('click', function (e) { e.preventDefault(); if (!sheet.open) sheet.showModal(); });
    sheet.querySelector('.acx-m-close').addEventListener('click', function (e) { e.preventDefault(); sheet.close(); });
    sheet.addEventListener('click', function (e) { if (e.target === sheet) sheet.close(); });   // tap on the dimmed backdrop
    all('.acx-m-row', sheet).forEach(function (a) { a.addEventListener('click', function () { sheet.close(); }); });   // then the link scrolls to its section
    if (location.hash === '#acx-secs') { history.replaceState(null, '', location.pathname + location.search); sheet.showModal(); }
  }
  var cur = root.querySelector('.acx-local-cur'), rows = sheet ? all('.acx-m-row[data-sec]', sheet) : [];
  if (cur && rows.length) {
    var marks = rows.map(function (r) { return document.getElementById(r.getAttribute('data-sec')); });
    var shown = -1, queued = false;
    var mark = function () {
      queued = false;
      var line = window.innerHeight * 0.35, i = 0, de = document.documentElement;
      marks.forEach(function (m, j) { if (m && m.getBoundingClientRect().top <= line) i = j; });
      if (window.innerHeight + window.scrollY >= de.scrollHeight - 2) i = rows.length - 1;   // the last section may never reach the line
      if (i === shown) return;
      shown = i;
      cur.querySelector('.acx-local-k').textContent = 'ACTLC 2027';
      cur.querySelector('b').textContent = rows[i].getAttribute('data-short') || rows[i].textContent;
      rows.forEach(function (r, j) { if (j === i) r.setAttribute('aria-current', 'location'); else r.removeAttribute('aria-current'); });
    };
    window.addEventListener('scroll', function () { if (!queued) { queued = true; requestAnimationFrame(mark); } }, { passive: true });
    window.addEventListener('resize', mark); mark();
  }

  // 7. Phones: the speakers' swipe row gets previous / next buttons, shown only while there is somewhere to go.
  var row = root.querySelector('#speakers .acx-c-people:not(.acx-c-team)'), swnav = root.querySelector('.acx-c-swnav');
  if (row && swnav) {
    var prev = swnav.querySelector('[data-dir="-1"]'), next = swnav.querySelector('[data-dir="1"]'), swQueued = false;
    var swState = function () {
      swQueued = false;
      var max = row.scrollWidth - row.clientWidth;
      swnav.hidden = !(phone.matches && max > 2);
      prev.disabled = row.scrollLeft <= 2; next.disabled = row.scrollLeft >= max - 2;
    };
    swnav.addEventListener('click', function (e) {
      var b = e.target.closest('.acx-c-swb'); if (!b) return;
      var card = row.querySelector('li'), gap = parseFloat(getComputedStyle(row).columnGap) || 0;
      row.scrollBy({ left: (card.getBoundingClientRect().width + gap) * Number(b.getAttribute('data-dir')), behavior: reduce.matches ? 'auto' : 'smooth' });
    });
    row.addEventListener('scroll', function () { if (!swQueued) { swQueued = true; requestAnimationFrame(swState); } }, { passive: true });
    window.addEventListener('resize', swState); onPhoneChange(swState); swState();
  }
})();
