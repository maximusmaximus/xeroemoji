/*! xero-emoji.js - swap Unicode emoji in text for Xero Emoji images. No dependencies.
 *  Xero Emoji (c) Max Infeld - artwork CC BY 4.0 ("Xero Emoji by Max Infeld, CC BY 4.0"), see LICENSE / LICENSING.md.
 *
 *  await XeroEmoji.load({ base: '../', map: 'emoji-map.json', format: 'svg' });
 *  XeroEmoji.parse(element);          // replace emoji in all text nodes under element
 *  XeroEmoji.toHTML('hi 👋🏽!');       // -> 'hi <img class="xero-emoji" ...>!' (input is HTML-escaped)
 *  XeroEmoji.find('👍🏿');            // -> {file, emoji, name, group, subgroup, order, src} or null
 */
(function (global) {
  'use strict';
  var MAP = null, OPT = { base: '../', map: 'emoji-map.json', format: 'svg', className: 'xero-emoji' };
  // Anything that can start an emoji: pictographs, regional indicators (flags), keycap bases followed by U+20E3.
  var MAYBE = /[\u00a9\u00ae\u203c-\u3299\ud83c-\ud83e]|[#*0-9]\ufe0f?\u20e3/;
  var segmenter = (typeof Intl !== 'undefined' && Intl.Segmenter) ? new Intl.Segmenter(undefined, { granularity: 'grapheme' }) : null;

  function key(str) {               // '👍🏿' -> '1f44d-1f3ff', '©️' -> '00a9' (FE0F removed, 4+ hex digits, like the map keys)
    var out = [];
    for (var ch of str) { var cp = ch.codePointAt(0); if (cp !== 0xfe0f) out.push(cp.toString(16).padStart(4, '0')); }
    return out.join('-');
  }
  function graphemes(text) {
    if (segmenter) return Array.from(segmenter.segment(text), function (s) { return s.segment; });
    // Fallback: greedy longest match of up to 10 code points against the map.
    var cps = Array.from(text), res = [], i = 0;
    while (i < cps.length) {
      var hit = 1;
      for (var n = Math.min(10, cps.length - i); n > 1; n--) { if (MAP[key(cps.slice(i, i + n).join(''))]) { hit = n; break; } }
      res.push(cps.slice(i, i + hit).join('')); i += hit;
    }
    return res;
  }
  // A lone character such as (c) U+00A9 or U+2122 is text unless it carries U+FE0F; its fully-qualified form in the map
  // has FE0F, so a bare one is left alone (set {textStyle: true} to replace those as well).
  function textStyle(g, e) { return !OPT.textStyle && Array.from(g).length === 1 && e[1].indexOf('\ufe0f') >= 0; }
  function find(g) {
    var e = MAP && MAP[key(g)];
    if (!e || textStyle(g, e)) return null;
    return { file: e[0], emoji: e[1], name: e[2], group: e[3], subgroup: e[4], order: e[5], src: OPT.base + OPT.format + '/' + e[0] + '.' + OPT.format };
  }
  function img(e, g) {
    var el = document.createElement('img');
    el.className = OPT.className; el.src = e.src; el.alt = g; el.title = e.name; el.draggable = false;
    el.setAttribute('loading', 'lazy'); el.setAttribute('decoding', 'async');
    return el;
  }
  function esc(s) { return s.replace(/[&<>"']/g, function (c) { return '&#' + c.charCodeAt(0) + ';'; }); }

  var XeroEmoji = {
    load: function (opt) {
      for (var k in (opt || {})) OPT[k] = opt[k];
      return fetch(OPT.base + 'demos/' + OPT.map).then(function (r) { if (!r.ok) throw new Error('emoji-map ' + r.status); return r.json(); })
        .then(function (m) { MAP = m; return XeroEmoji; });
    },
    find: find,
    get map() { return MAP; },
    get options() { return OPT; },
    toHTML: function (text) {
      if (!MAYBE.test(text)) return esc(text);
      return graphemes(text).map(function (g) {
        var e = find(g);
        return e ? '<img class="' + OPT.className + '" src="' + esc(e.src) + '" alt="' + esc(g) + '" title="' + esc(e.name) + '" loading="lazy">' : esc(g);
      }).join('');
    },
    parse: function (root) {
      var walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
        acceptNode: function (n) {
          var p = n.parentNode && n.parentNode.nodeName;
          if (p === 'SCRIPT' || p === 'STYLE' || p === 'TEXTAREA' || p === 'INPUT') return NodeFilter.FILTER_REJECT;
          return MAYBE.test(n.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
        }
      });
      var nodes = []; while (walker.nextNode()) nodes.push(walker.currentNode);
      nodes.forEach(function (n) {
        var frag = document.createDocumentFragment(), buf = '', changed = false;
        graphemes(n.nodeValue).forEach(function (g) {
          var e = find(g);
          if (e) { if (buf) frag.appendChild(document.createTextNode(buf)); buf = ''; frag.appendChild(img(e, g)); changed = true; }
          else buf += g;
        });
        if (!changed) return;
        if (buf) frag.appendChild(document.createTextNode(buf));
        n.parentNode.replaceChild(frag, n);
      });
      return root;
    }
  };
  global.XeroEmoji = XeroEmoji;
})(typeof window !== 'undefined' ? window : this);
