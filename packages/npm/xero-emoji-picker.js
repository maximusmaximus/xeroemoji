/*! xero-emoji-picker.js - tiny dependency-free emoji picker for Xero Emoji (artwork and code CC BY 4.0: "Xero Emoji by Max Infeld, CC BY 4.0")
 * Usage:
 *   <script src="https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@main/packages/npm/xero-emoji-picker.js"></script>
 *   const picker = XeroEmojiPicker.attach(buttonEl, { onSelect: e => input.value += e.emoji });
 *   // or XeroEmojiPicker.create({ container: el, onSelect }) for an inline picker
 * Options: base (where svg/ lives; default jsDelivr v1.0.0), map (URL of emoji-map.json), onSelect({emoji,name,file,url}),
 *          tone ('' | '1f3fb'..'1f3ff'), perRow (default 8), size (px, default 32)
 */
(function (root) {
  'use strict';
  var CDN = 'https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.0/';
  var TONE = /-1f3f[b-f]/g, cache = {};
  var CSS = '.xep{font:14px system-ui,sans-serif;background:#fff;color:#1d1b18;border:1px solid #e6e2da;border-radius:14px;box-shadow:0 10px 32px rgba(0,0,0,.15);width:var(--w);padding:8px;box-sizing:border-box}' +
    '.xep input{width:100%;box-sizing:border-box;font:inherit;padding:7px 10px;border:1px solid #e6e2da;border-radius:9px;margin-bottom:6px}' +
    '.xep .xep-bar{display:flex;gap:2px;overflow-x:auto;margin-bottom:6px}.xep .xep-bar button{flex:none;border:0;background:none;cursor:pointer;padding:3px 5px;border-radius:7px;opacity:.55}' +
    '.xep .xep-bar button.on{opacity:1;background:#f3f0ea}.xep .xep-bar img{width:20px;height:20px;display:block}' +
    '.xep .xep-grid{display:grid;grid-template-columns:repeat(var(--n),minmax(0,1fr));gap:2px;height:260px;overflow-y:auto;overflow-x:hidden}' +
    '.xep .xep-grid button{border:0;background:none;padding:3px;border-radius:8px;cursor:pointer}.xep .xep-grid button:hover,.xep .xep-grid button:focus{background:#f3f0ea;outline:none}' +
    '.xep .xep-grid img{width:var(--s);height:var(--s);display:block}.xep .xep-h{grid-column:1/-1;font-size:11px;text-transform:uppercase;color:#6b665e;margin:6px 2px 2px}' +
    '.xep .xep-tones{display:flex;gap:2px;margin-top:6px}.xep .xep-tones button{border:1px solid transparent;background:none;border-radius:7px;cursor:pointer;width:24px;height:24px;padding:0}' +
    '.xep .xep-tones button.on{border-color:#1d1b18}';
  var TONES = ['', '1f3fb', '1f3fc', '1f3fd', '1f3fe', '1f3ff'], SW = ['#ffc83d', '#f7dece', '#f3d2a2', '#d5ab88', '#af7e57', '#7c533e'];
  function el(tag, cls, html) { var e = document.createElement(tag); if (cls) e.className = cls; if (html != null) e.innerHTML = html; return e; }
  function css() { if (document.getElementById('xep-css')) return; var s = el('style'); s.id = 'xep-css'; s.textContent = CSS; document.head.appendChild(s); }
  function load(url) {
    return cache[url] || (cache[url] = fetch(url).then(function (r) { return r.json(); }).then(function (m) {
      var all = Object.keys(m).map(function (k) { var e = m[k], t = k.match(TONE);
        return { k: k, f: e[0], e: e[1], n: e[2], g: e[3], sg: e[4], o: e[5], tn: t ? t.map(function (x) { return x.slice(1); }) : null,
          base: t ? k.replace(TONE, '') : k, s: (e[2] + ' ' + e[4] + ' ' + k).toLowerCase() }; }).sort(function (a, b) { return a.o - b.o; });
      var toned = {}; all.forEach(function (x) { if (x.tn) toned[x.base + '|' + x.tn.join(',')] = x; });
      return { all: all, toned: toned };
    }));
  }
  function create(opt) {
    opt = opt || {}; css();
    var base = opt.base || CDN, mapUrl = opt.map || base + 'demos/emoji-map.json', tone = opt.tone || '', group = null, q = '';
    var box = el('div', 'xep'); box.style.setProperty('--n', opt.perRow || 8); box.style.setProperty('--s', (opt.size || 32) + 'px');
    box.style.setProperty('--w', ((opt.perRow || 8) * ((opt.size || 32) + 8) + 24) + 'px');
    box.setAttribute('role', 'dialog'); box.setAttribute('aria-label', 'Emoji picker');
    var input = el('input'); input.type = 'search'; input.placeholder = 'Search emoji'; input.setAttribute('aria-label', 'Search emoji');
    var bar = el('div', 'xep-bar'), grid = el('div', 'xep-grid'), tones = el('div', 'xep-tones');
    box.appendChild(input); box.appendChild(bar); box.appendChild(grid); box.appendChild(tones);
    TONES.forEach(function (t, i) { var b = el('button'); b.style.background = SW[i]; b.title = t ? 'skin tone ' + i : 'default skin tone';
      b.className = t === tone ? 'on' : ''; b.onclick = function () { tone = t; [].forEach.call(tones.children, function (c) { c.className = c === b ? 'on' : ''; }); draw(); };
      tones.appendChild(b); });
    if (opt.container) opt.container.appendChild(box);
    var data = null, timer = 0;
    function src(x) { return base + 'svg/' + x.f + '.svg'; }
    function shown(x) {
      if (x.tn) return false; // base list only; tone applied on render
      if (group && x.g !== group) return false;
      if (!q) return true; return q.split(/\s+/).every(function (w) { return x.s.indexOf(w) >= 0; }) || x.e === q;
    }
    function toned(x) { if (!tone) return x; var n = (x.k.match(/1f9d1|1f468|1f469|1f9d2/g) || []).length || 1, keys = [];
      for (var i = 0; i < Math.max(1, n); i++) keys.push(tone); return data.toned[x.k + '|' + keys.join(',')] || data.toned[x.k + '|' + tone] || x; }
    function draw() {
      if (!data) return; var html = '', sg = '', list = data.all.filter(shown);
      list.forEach(function (x) { var y = toned(x); if (!q && x.sg !== sg) { sg = x.sg; html += '<div class="xep-h">' + sg + '</div>'; }
        html += '<button type="button" data-k="' + y.k + '" title="' + y.n + '"><img loading="lazy" src="' + src(y) + '" alt="' + y.e + '"></button>'; });
      grid.innerHTML = html || '<div class="xep-h">No match</div>';
    }
    grid.onclick = function (ev) { var b = ev.target.closest('button[data-k]'); if (!b) return;
      var x = data.all.filter(function (y) { return y.k === b.dataset.k; })[0];
      if (opt.onSelect) opt.onSelect({ emoji: x.e, name: x.n, file: x.f, url: src(x) });
      if (api.onPick) api.onPick(x); };
    input.oninput = function () { clearTimeout(timer); timer = setTimeout(function () { q = input.value.trim().toLowerCase(); draw(); }, 80); };
    load(mapUrl).then(function (d) { data = d; var seen = {};
      var gs = d.all.filter(function (x) { if (seen[x.g]) return false; seen[x.g] = 1; return true; });
      bar.innerHTML = '<button type="button" class="on" data-g="" title="All">★</button>' + gs.map(function (x) {
        return '<button type="button" data-g="' + x.g + '" title="' + x.g + '"><img src="' + src(x) + '" alt=""></button>'; }).join('');
      bar.onclick = function (ev) { var b = ev.target.closest('button'); if (!b) return; group = b.dataset.g || null;
        [].forEach.call(bar.children, function (c) { c.className = c === b ? 'on' : ''; }); grid.scrollTop = 0; draw(); };
      draw(); });
    var api = { element: box, focus: function () { input.focus(); }, destroy: function () { box.remove(); } };
    return api;
  }
  function attach(button, opt) {
    opt = opt || {}; var p = create(opt), b = p.element; b.style.position = 'absolute'; b.style.zIndex = 9999; b.hidden = true;
    document.body.appendChild(b);
    function close() { b.hidden = true; document.removeEventListener('mousedown', out); }
    function out(ev) { if (!b.contains(ev.target) && ev.target !== button) close(); }
    button.addEventListener('click', function () { if (!b.hidden) return close(); var r = button.getBoundingClientRect();
      b.style.left = Math.max(4, r.left + scrollX) + 'px'; b.style.top = (r.bottom + scrollY + 6) + 'px'; b.hidden = false; p.focus();
      document.addEventListener('mousedown', out); });
    b.addEventListener('keydown', function (ev) { if (ev.key === 'Escape') { close(); button.focus(); } });
    if (opt.closeOnSelect !== false) p.onPick = close;
    p.open = function () { if (b.hidden) button.click(); }; p.close = close; return p;
  }
  var X = { create: create, attach: attach, version: '1.1.0' };
  if (typeof module === 'object' && module.exports) module.exports = X; else root.XeroEmojiPicker = X;
})(typeof self !== 'undefined' ? self : this);
