/* ACTLC site search. Runs in the browser from a prebuilt index (search-index.json, made by
   tools/search_index.py): webinars, conference speakers, sessions, tracks and dates, member
   documents and the text of every PDF page. The index is fetched the first time a visitor shows
   intent to search (pointer or focus on the search button, "/" or Ctrl+K), so pages load nothing extra.
   Ranking: BM25 over title, subtitle and text; the word being typed matches as a prefix; words of four
   letters or more forgive one typo (two from eight letters). Every word must match, else the best
   partial matches are shown and labelled as such. */
(function () {
  'use strict';
  var me = document.currentScript;
  if (!me || !window.fetch || !window.HTMLDialogElement) return;
  var ROOT = me.src.replace(/actlc-assets\/search\.js.*$/, ''), INDEX = me.getAttribute('data-index');

  // ---------------------------------------------------------------- text
  var MARKS = /[̀-ͯؐ-ًؚ-ٰٟۖ-ۭ]/g, APOS = /['’]/g;
  var WORD = /[\p{L}\p{N}]+(?:['’][\p{L}\p{N}]+)*/gu;
  function norm(s) {   // case, accents and Arabic letter variants fold together: "María" = "maria"
    return s.normalize('NFKD').replace(MARKS, '').toLowerCase()
      .replace(/[آأإٱ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي');
  }
  // Index side: "O'Mahony" is stored as "omahony", "o" and "mahony"; query side keeps the joined form only.
  function terms(s, forIndex) {
    var out = [], m = norm(s).match(WORD) || [];
    for (var i = 0; i < m.length; i++) {
      var w = m[i];
      if (APOS.test(w)) { out.push(w.replace(APOS, '')); if (forIndex) out.push.apply(out, w.split(APOS)); }
      else out.push(w);
      APOS.lastIndex = 0;
    }
    return out;
  }

  // Optimal string alignment distance (insert, delete, substitute, swap neighbours); stops above k.
  function dist(a, b, k) {
    var m = a.length, n = b.length, i, j;
    if (Math.abs(m - n) > k) return k + 1;
    var pp = null, p = [], c;
    for (j = 0; j <= n; j++) p[j] = j;
    for (i = 1; i <= m; i++) {
      c = [i]; var best = i;
      for (j = 1; j <= n; j++) {
        var v = Math.min(p[j] + 1, c[j - 1] + 1, p[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
        if (pp && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) v = Math.min(v, pp[j - 2] + 1);
        c[j] = v; if (v < best) best = v;
      }
      if (best > k) return k + 1;
      pp = p; p = c;
    }
    return p[n];
  }

  // ---------------------------------------------------------------- engine
  var FIELDS = ['t', 's', 'b'], WEIGHT = [4, 2, 1], K1 = 1.2, B = 0.75;

  function Engine(data) {
    var docs = data.docs, post = Object.create(null), lens = [], sum = 0;
    docs.forEach(function (d, i) {
      var tf = Object.create(null), len = 0;
      FIELDS.forEach(function (f, j) {
        var ws = terms(d[f] || '', true);
        len += ws.length * WEIGHT[j];
        for (var x = 0; x < ws.length; x++) tf[ws[x]] = (tf[ws[x]] || 0) + WEIGHT[j];
      });
      for (var t in tf) (post[t] || (post[t] = [])).push(i, tf[t]);   // flat: doc, weighted count, doc, ...
      lens[i] = len; sum += len;
      d.nt = terms(d.t).join(' ');
    });
    var avg = sum / docs.length, N = docs.length;
    this.docs = docs; this.post = post; this.quick = data.quick || [];
    this.vocab = Object.keys(post).sort();
    this.norm = lens.map(function (l) { return K1 * (1 - B + B * l / avg); });
    this.idf = function (t) { var n = post[t].length / 2; return Math.log(1 + (N - n + 0.5) / (n + 0.5)); };
  }

  // Vocabulary terms that answer one query word, each with how much it counts.
  Engine.prototype.expand = function (q, typing) {
    var v = this.vocab, out = [], i, lo = 0, hi = v.length;
    if (this.post[q]) out.push([q, 1]);
    if (q.length >= (typing ? 2 : 3)) {                 // prefix: the word being typed, or a stem like "assess"
      while (lo < hi) { i = (lo + hi) >> 1; if (v[i] < q) lo = i + 1; else hi = i; }
      for (i = lo; i < v.length && v[i].lastIndexOf(q, 0) === 0 && out.length < 60; i++)
        if (v[i] !== q) out.push([v[i], typing ? 0.8 : 0.6]);
    }
    if (!out.length && q.length >= 4) {                // typo tolerance, only when nothing matched as typed
      var k = q.length >= 8 ? 2 : 1;
      for (i = 0; i < v.length; i++) {
        var w = v[i];
        if (dist(q, w, k) <= k) out.push([w, 0.5]);
        else if (typing && w.length > q.length && dist(q, w.slice(0, q.length), 1) <= 1) out.push([w, 0.4]);
      }
    }
    return out;
  };

  Engine.prototype.search = function (input) {
    var qs = terms(input, false);
    if (!qs.length || (qs.length === 1 && qs[0].length < 2)) return null;   // one letter: keep the suggestions
    var open = !/\s$/.test(input), self = this, hits = Object.create(null);
    var per = qs.map(function (q, wi) {
      var best = new Map();
      self.expand(q, open && wi === qs.length - 1).forEach(function (c) {
        var p = self.post[c[0]], idf = self.idf(c[0]);
        hits[c[0]] = wi;
        for (var x = 0; x < p.length; x += 2) {
          var d = p[x], tf = p[x + 1], s = c[1] * idf * tf * (K1 + 1) / (tf + self.norm[d]);
          if (!(best.get(d) >= s)) best.set(d, s);
        }
      });
      return best;
    });
    var scores = new Map(), partial = false;
    per.slice().sort(function (a, b) { return a.size - b.size; })[0].forEach(function (s, d) {
      var t = 0;
      for (var i = 0; i < per.length; i++) { var v = per[i].get(d); if (v === undefined) return; t += v; }
      scores.set(d, t);
    });
    if (!scores.size && per.length > 1) {              // nothing has every word: rank by how many words match
      partial = true;
      per.forEach(function (m) { m.forEach(function (s, d) { var o = scores.get(d) || [0, 0]; scores.set(d, [o[0] + s, o[1] + 1]); }); });
      scores.forEach(function (o, d) { scores.set(d, o[0] * Math.pow(o[1] / per.length, 2)); });
    }
    var phrase = qs.join(' '), now = Date.now(), seen = Object.create(null), list = [];
    scores.forEach(function (s, d) {
      var doc = self.docs[d], at = doc.nt.indexOf(phrase);
      if (at === 0) s *= 2; else if (at > 0) s *= 1.5;  // the whole query in the title
      if (doc.e && Date.parse(doc.e) > now) s *= 1.15;  // upcoming before past
      list.push([s, d]);
    });
    list.sort(function (a, b) { return b[0] - a[0] || a[1] - b[1]; });
    var out = [];
    for (var i = 0; i < list.length && out.length < 20; i++) {
      var doc = self.docs[list[i][1]], g = doc.g || 'd' + list[i][1];
      if (seen[g]) continue;                           // one row per document: its best page wins
      seen[g] = 1; out.push(doc);
    }
    return { list: out, partial: partial, hits: hits, count: qs.length };
  };

  // ---------------------------------------------------------------- results
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function keyOf(w) { return norm(w).replace(APOS, ''); }
  function which(hits, w) {     // index of the query word this text word answers, or -1
    var k = keyOf(w);
    if (k in hits) return hits[k];
    var parts = norm(w).split(APOS);
    for (var i = 0; i < parts.length; i++) if (parts[i] in hits) return hits[parts[i]];
    return -1;
  }
  function mark(text, hits) {
    var out = '', last = 0, m; WORD.lastIndex = 0;
    while ((m = WORD.exec(text))) {
      out += esc(text.slice(last, m.index)) + (which(hits, m[0]) >= 0 ? '<mark>' + esc(m[0]) + '</mark>' : esc(m[0]));
      last = m.index + m[0].length;
    }
    return out + esc(text.slice(last));
  }
  // The stretch of text (about LEN characters) that holds the most different query words.
  var LEN = 150;
  function snippet(text, hits, count) {
    var pos = [], m; WORD.lastIndex = 0;
    while ((m = WORD.exec(text))) { var q = which(hits, m[0]); if (q >= 0) pos.push([m.index, q]); }
    var start = 0;
    if (pos.length) {
      var best = -1;
      for (var i = 0; i < pos.length && best < count; i++) {
        var got = {}, n = 0;
        for (var j = i; j < pos.length && pos[j][0] - pos[i][0] < LEN - 40; j++) if (!got[pos[j][1]]) { got[pos[j][1]] = 1; n++; }
        if (n > best) { best = n; start = pos[i][0]; }
      }
      start = Math.max(0, start - 40);
      if (start > 0) start = text.indexOf(' ', start) + 1;
    }
    var end = Math.min(text.length, start + LEN);
    if (end < text.length) { var sp = text.lastIndexOf(' ', end); if (sp > start) end = sp; }
    return (start > 0 ? '…' : '') + text.slice(start, end) + (end < text.length ? '…' : '');
  }
  function kind(d) { return d.e ? (Date.parse(d.e) > Date.now() ? 'Upcoming webinar' : 'Past webinar') : d.k; }
  function href(u) { return /^https?:/.test(u) ? u : ROOT + u; }

  // ---------------------------------------------------------------- dialog
  var ICON = '<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>';
  var engine = null, loading = null, dlg, input, list, status, rows = [], active = -1;

  function load() {
    return loading || (loading = fetch(INDEX).then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (data) { engine = new Engine(data); if (dlg && dlg.open) render(); })
      .catch(function () { loading = null; if (status) status.textContent = 'Search could not load. Check your connection and try again.'; }));
  }

  function build() {
    dlg = document.createElement('dialog');
    dlg.className = 'acx acx-sd';
    dlg.setAttribute('aria-label', 'Search this site');
    dlg.innerHTML = '<div class="acx-sd-bar">' + ICON +
      '<input class="acx-sd-q" type="search" placeholder="Search webinars, speakers, sessions, documents" autocomplete="off" autocorrect="off" spellcheck="false"' +
      ' enterkeyhint="go" role="combobox" aria-expanded="true" aria-controls="acx-sd-list" aria-autocomplete="list" aria-label="Search"/>' +
      '<button type="button" class="acx-sd-x">Close</button></div>' +
      '<p class="acx-sd-status" role="status" aria-live="polite"></p>' +
      '<div class="acx-sd-list" id="acx-sd-list" role="listbox" aria-label="Results"></div>' +
      '<p class="acx-sd-keys"><kbd>↑</kbd> <kbd>↓</kbd> to choose · <kbd>Enter</kbd> to open · <kbd>Esc</kbd> to close</p>';
    document.body.appendChild(dlg);
    input = dlg.querySelector('.acx-sd-q'); list = dlg.querySelector('.acx-sd-list'); status = dlg.querySelector('.acx-sd-status');
    input.addEventListener('input', render);
    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
        e.preventDefault();
        if (rows.length) select((active + (e.key === 'ArrowDown' ? 1 : -1) + rows.length) % rows.length);
      } else if (e.key === 'Enter' && rows[active]) { e.preventDefault(); rows[active].click(); }
      else if (e.key === 'Escape') { e.preventDefault(); dlg.close(); }   // a search box would only clear its text
    });
    dlg.querySelector('.acx-sd-x').addEventListener('click', function () { dlg.close(); });
    dlg.addEventListener('click', function (e) {      // a click on the dimmed page outside the panel closes it
      if (e.target !== dlg) return;
      var r = dlg.getBoundingClientRect();
      if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) dlg.close();
    });
    list.addEventListener('mousemove', function (e) { var a = e.target.closest('.acx-sd-r'); if (a && rows.indexOf(a) !== active) select(rows.indexOf(a), true); });
    list.addEventListener('click', function (e) {
      var a = e.target.closest('a'); if (!a || e.ctrlKey || e.metaKey || e.shiftKey) return;
      var u = new URL(a.href, location.href);
      dlg.close();
      if (u.origin === location.origin && u.pathname === location.pathname && u.hash) {   // same page: just scroll
        e.preventDefault();
        if (location.hash !== u.hash) location.hash = u.hash;
        else { var t = document.getElementById(decodeURIComponent(u.hash.slice(1))); if (t) t.scrollIntoView({ block: 'start' }); }
      }
    });
  }

  function select(i, fromMouse) {
    if (rows[active]) rows[active].setAttribute('aria-selected', 'false');
    active = i;
    if (!rows[i]) { input.removeAttribute('aria-activedescendant'); return; }
    rows[i].setAttribute('aria-selected', 'true');
    input.setAttribute('aria-activedescendant', rows[i].id);
    if (!fromMouse) rows[i].scrollIntoView({ block: 'nearest' });
  }

  function row(i, k, title, sub, text, u) {
    return '<a class="acx-sd-r" role="option" id="acx-sd-o' + i + '" aria-selected="false" href="' + esc(href(u)) + '">' +
      '<span class="acx-sd-k">' + esc(k) + '</span><span class="acx-sd-t">' + title + '</span>' +
      (sub ? '<span class="acx-sd-s">' + sub + '</span>' : '') + (text ? '<span class="acx-sd-b">' + text + '</span>' : '') + '</a>';
  }

  function render() {
    if (!engine) { status.textContent = 'Loading search…'; list.innerHTML = ''; rows = []; return; }
    var q = input.value, r = engine.search(q), html = '';
    if (!r) {
      status.textContent = 'Popular';
      html = engine.quick.map(function (x, i) { return row(i, 'Go to', esc(x.t), '', '', x.u); }).join('');
    } else {
      r.list.forEach(function (d, i) {
        html += row(i, kind(d), mark(d.t, r.hits), mark(d.s || '', r.hits), mark(snippet(d.b || '', r.hits, r.count), r.hits), d.u);
      });
      status.textContent = r.list.length
        ? r.list.length + (r.list.length === 20 ? '+' : '') + ' result' + (r.list.length === 1 ? '' : 's') + (r.partial ? ' · no page has every word, closest matches first' : '')
        : 'No results for “' + q.trim() + '”. Try fewer or different words.';
    }
    list.innerHTML = html;
    rows = Array.prototype.slice.call(list.querySelectorAll('.acx-sd-r'));
    active = -1; select(rows.length ? 0 : -1);
    list.scrollTop = 0;
  }

  function open(q) {
    if (!dlg) build();
    load();
    if (typeof q === 'string') input.value = q;
    if (!dlg.open) dlg.showModal();
    input.focus(); input.select();
    render();
  }

  // ---------------------------------------------------------------- hooks
  // The theme's search buttons (desktop and phone) open this dialog instead of the WordPress search.
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('.header-search-link');
    if (!a) return;
    e.preventDefault(); e.stopImmediatePropagation(); open();
  }, true);
  document.addEventListener('submit', function (e) {
    if (!e.target.matches || !e.target.matches('form.search-form')) return;
    e.preventDefault(); e.stopImmediatePropagation();
    var f = e.target.querySelector('input[name="s"]'); open(f ? f.value : '');
  }, true);
  ['pointerover', 'focusin', 'touchstart'].forEach(function (t) {
    document.addEventListener(t, function (e) { if (e.target.closest && e.target.closest('.header-search-link')) load(); }, { passive: true, capture: true });
  });
  document.addEventListener('keydown', function (e) {
    var t = e.target, k = (e.key || '').toLowerCase(), typing = t.isContentEditable || /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName);
    if (((e.ctrlKey || e.metaKey) && k === 'k') || (k === '/' && !typing && !e.ctrlKey && !e.metaKey && !e.altKey)) {
      if (dlg && dlg.open) return;
      e.preventDefault(); open();
    }
  });

  window.acxSearch = { open: open, load: load, engine: function () { return engine; } };   // for tests
})();
