/* ACTLC events: time-aware states for the events list and the session pages.
   The HTML is complete without this script; it only updates what depends on the
   current time and the visitor's timezone. Pure functions are exported for tests. */
(function () {
  'use strict';

  var MIN = 6e4, DAY = 864e5;
  var MEMBER_TZ = {
    'Asia/Dubai': 'ae', 'Asia/Riyadh': 'sa', 'Asia/Bahrain': 'bh', 'Asia/Beirut': 'lb',
    'Africa/Cairo': 'eg', 'Africa/Casablanca': 'ma', 'Africa/El_Aaiun': 'ma'
  };

  function phase(now, start, end) {
    if (now >= end) return 'past';
    if (now >= start) return 'live';
    return 'upcoming';
  }

  // Whole calendar days between two instants, counted in the given timezone.
  function dayDiff(now, start, tz) {
    var f = new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' });
    return Math.round((Date.parse(f.format(start)) - Date.parse(f.format(now))) / DAY);
  }

  // "in 20 minutes", "in 3 hours", "tomorrow", "in 6 days"
  function relativeStart(now, start, tz) {
    var rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
    var m = (start - now) / MIN;
    if (m < 60) return rtf.format(Math.max(1, Math.round(m)), 'minute');
    if (m < 12 * 60) return rtf.format(Math.round(m / 60), 'hour');
    return rtf.format(dayDiff(now, start, tz), 'day');
  }

  function statusText(now, start, end, tz) {
    var p = phase(now, start, end);
    if (p === 'past') return 'Ended';
    if (p === 'live') return 'Live now';
    return 'Starts ' + relativeStart(now, start, tz);
  }

  function memberCode(tz) { return MEMBER_TZ[tz] || null; }

  function cityFromTz(tz) {
    var c = (tz || '').split('/').pop() || '';
    return c.replace(/_/g, ' ');
  }

  function clock(t, tz) {
    return new Intl.DateTimeFormat('en-GB', { timeZone: tz, hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).format(t);
  }

  // Apple World Clock style day marker: '' | 'Next day' | 'Previous day'
  function dayMarker(start, eventTz, viewerTz) {
    var f = function (tz) { return new Intl.DateTimeFormat('en-CA', { timeZone: tz, year: 'numeric', month: '2-digit', day: '2-digit' }).format(start); };
    var d = Math.round((Date.parse(f(viewerTz)) - Date.parse(f(eventTz))) / DAY);
    return d > 0 ? 'Next day' : d < 0 ? 'Previous day' : '';
  }

  var api = { phase: phase, dayDiff: dayDiff, relativeStart: relativeStart, statusText: statusText,
              memberCode: memberCode, cityFromTz: cityFromTz, clock: clock, dayMarker: dayMarker };

  if (typeof module !== 'undefined' && module.exports) { module.exports = api; return; }

  // ---------------------------------------------------------------- browser
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function times(el) { return [Date.parse(el.getAttribute('data-start')), Date.parse(el.getAttribute('data-end'))]; }
  function viewerTz() { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'; } catch (e) { return 'UTC'; } }

  function initList(root) {
    var now = Date.now(), tz = viewerTz();
    var upPanel = $('[data-panel="upcoming"]', root), pastPanel = $('[data-panel="past"]', root);
    var pastList = $('.acx-list', pastPanel), moved = [];

    $$('.acx-ev', upPanel).forEach(function (li) {
      var t = times(li), p = phase(now, t[0], t[1]);
      if (p === 'past') { moved.push(li); }
      else if (p === 'live') { li.classList.add('is-live'); var s = $('.acx-live', li); if (s) s.hidden = false; }
    });
    moved.sort(function (a, b) { return times(a)[1] - times(b)[1]; }) // oldest first, each goes on top
         .forEach(function (li) {
           li.classList.add('is-past');
           var w = $('.acx-w', li), d = $('.acx-date', li); // past rows show the year instead of the weekday
           if (w && d) w.textContent = d.getAttribute('datetime').slice(0, 4);
           var a = $('.acx-title a[href^="mailto:"]', li); if (a) a.removeAttribute('href');
           pastList.insertBefore(li, pastList.firstChild);
         });
    $$('.acx-month', upPanel).forEach(function (sec) { if (!$('.acx-ev', sec)) sec.remove(); });

    var nUp = $$('.acx-ev', upPanel).length, nPast = $$('.acx-ev', pastPanel).length;
    var empty = $('.acx-empty', upPanel); if (empty) empty.hidden = nUp > 0;
    $$('[data-count="past"]', root).forEach(function (c) { c.textContent = nPast; });

    // Segmented control: Upcoming | Past (WAI-ARIA tabs, automatic activation)
    var tabs = $('.acx-tabs', root); if (!tabs) return;
    var btn = $$('[role="tab"]', tabs);
    $('[data-count="upcoming"]', tabs).textContent = nUp;
    $('[data-count="past"]', tabs).textContent = nPast;
    function select(i, focus) {
      btn.forEach(function (b, j) {
        var on = i === j;
        b.setAttribute('aria-selected', on ? 'true' : 'false');
        b.tabIndex = on ? 0 : -1;
        document.getElementById(b.getAttribute('aria-controls')).hidden = !on;
      });
      if (focus) btn[i].focus();
      var h = i === 1 ? '#past' : ' ';
      if (history.replaceState) history.replaceState(null, '', h === ' ' ? location.pathname + location.search : h);
    }
    btn.forEach(function (b, i) {
      b.addEventListener('click', function () { select(i, false); });
      b.addEventListener('keydown', function (e) {
        var k = e.key, n = btn.length, j = null;
        if (k === 'ArrowRight') j = (i + 1) % n; else if (k === 'ArrowLeft') j = (i - 1 + n) % n;
        else if (k === 'Home') j = 0; else if (k === 'End') j = n - 1;
        if (j !== null) { e.preventDefault(); select(j, true); }
      });
    });
    var goPast = $('.acx-empty a[href="#past"]', upPanel);
    if (goPast) goPast.addEventListener('click', function (e) { e.preventDefault(); select(1, true); });
    [upPanel, pastPanel].forEach(function (p) { p.setAttribute('role', 'tabpanel'); });
    root.classList.add('acx-js');
    tabs.hidden = false;
    select(location.hash === '#past' ? 1 : 0, false);
  }

  function initDetail(root) {
    var now = Date.now(), t = times(root), evTz = root.getAttribute('data-tz'), tz = viewerTz();
    var p = phase(now, t[0], t[1]);
    root.classList.add('is-' + p);
    var st = $('.acx-status', root); if (st) st.textContent = statusText(now, t[0], t[1], tz);

    // One line with the visitor's own time, only when it differs from the event's zone.
    var yt = $('.acx-yourtime', root);
    if (yt && clock(t[0], tz) !== clock(t[0], evTz)) {
      var mark = dayMarker(t[0], evTz, tz);
      yt.textContent = 'Your time: ' + clock(t[0], tz) + ' \u2013 ' + clock(t[1], tz) + ' \u00b7 ' + cityFromTz(tz) + (mark ? ' (' + mark.toLowerCase() + ')' : '');
      yt.hidden = false;
    }
  }

  // Homepage: the next few upcoming sessions; ended ones disappear on their own.
  function initHome(root) {
    var now = Date.now(), limit = parseInt(root.getAttribute('data-limit'), 10) || 3, shown = 0;
    $$('.acx-ev', root).forEach(function (li) {
      var t = times(li), p = phase(now, t[0], t[1]);
      if (p === 'past' || shown >= limit) { li.remove(); return; }
      if (p === 'live') { li.classList.add('is-live'); var s = $('.acx-live', li); if (s) s.hidden = false; }
      shown++;
    });
    var empty = $('.acx-empty', root); if (empty) empty.hidden = shown > 0;
  }

  function boot() {
    $$('.acx-home-root').forEach(initHome);
    $$('.acx-list-root').forEach(initList);
    $$('.acx-detail[data-start]').forEach(initDetail);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
