/* Phone chrome (tools/mobile_chrome.py): the More sheet as a native dialog, and the search button once search can run.
   Without this script the More tab still opens the sheet through #acx-more (:target) and the search button stays hidden. */
(function () {
  var sheet = document.getElementById('acx-more');
  var root = document.documentElement;
  // Pages with their own sticky bar (conference sections, session Register bar): the top bar slides away while
  // reading down and comes back on any scroll up, so fixed chrome never takes a fifth of the screen.
  if (document.querySelector('.acx-local, .acx-detail')) {
    var last = window.scrollY, hidden = false;
    window.addEventListener('scroll', function () {
      var y = window.scrollY;
      if (Math.abs(y - last) < 8) return;
      var hide = y > last && y > 120;
      if (hide !== hidden) { hidden = hide; root.classList.toggle('acx-m-hidebar', hide); }
      last = y;
    }, { passive: true });
  }
  var search = document.querySelector('.acx-m-search');
  if (search && window.fetch && window.HTMLDialogElement) search.hidden = false;   // search.js needs both
  if (!sheet || typeof sheet.showModal !== 'function') return;

  var open = function (e) { if (e) e.preventDefault(); if (!sheet.open) sheet.showModal(); };
  var close = function (e) { if (e) e.preventDefault(); sheet.close(); };
  Array.prototype.forEach.call(document.querySelectorAll('.acx-m-more-open'), function (a) { a.addEventListener('click', open); });
  sheet.querySelector('.acx-m-close').addEventListener('click', close);
  sheet.addEventListener('click', function (e) { if (e.target === sheet) sheet.close(); });   // tap on the dimmed backdrop
  if (location.hash === '#acx-more') { history.replaceState(null, '', location.pathname + location.search); open(); }
})();
