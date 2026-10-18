'use strict';
/* xeroemoji - Xero Emoji lookup for Node and bundlers. Artwork CC BY-NC 4.0; commercial use needs a license (COMMERCIAL-LICENSE.md).
 *   const xe = require('xeroemoji');
 *   xe.get('👍🏿').svgUrl   // https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.0/svg/1f44d-1f3ff.svg
 */
const VERSION = '1.0.0';
let MAP = null;
function map() {
  if (!MAP) MAP = require('./emoji-map.json');   // bundled by `npm pack` (prepack copies ../../demos/emoji-map.json)
  return MAP;
}
const TONES = { '1f3fb': 'light', '1f3fc': 'medium-light', '1f3fd': 'medium', '1f3fe': 'medium-dark', '1f3ff': 'dark' };
const TONE_RE = /-1f3f[b-f]/g;
let BASE = `https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v${VERSION}/`;

/** '👍🏿' -> '1f44d-1f3ff' (FE0F dropped, at least 4 hex digits): the emoji-map.json key. */
function key(emoji) { return Array.from(emoji).map(c => c.codePointAt(0)).filter(c => c !== 0xfe0f).map(c => c.toString(16).padStart(4, '0')).join('-'); }
function entry(k, e) {
  const tones = k.split('-').filter(t => TONES[t]).map(t => TONES[t]);
  return { emoji: e[1], name: e[2], group: e[3], subgroup: e[4], file: e[0], key: k, order: e[5],
    codepoints: Array.from(e[1]).map(c => 'U+' + c.codePointAt(0).toString(16).toUpperCase().padStart(4, '0')).join(' '),
    skinTone: tones.length ? tones.join(', ') : null,
    svgUrl: `${BASE}svg/${e[0]}.svg`, pngUrl: `${BASE}png/${e[0]}.png`, svgPath: `svg/${e[0]}.svg`, pngPath: `png/${e[0]}.png` };
}
/** Look up by emoji ('🚀'), codepoints ('1f680', 'U+1F680'), file name or exact CLDR name. */
function get(q) {
  const m = map(); q = String(q || '').trim(); if (!q) return null;
  const cands = [key(q)];
  if (/^(u\+)?[0-9a-f]{2,6}([\s_+-]+(u\+)?[0-9a-f]{2,6})*$/i.test(q))
    cands.push(q.toLowerCase().replace(/u\+/g, ' ').split(/[\s_+-]+/).filter(Boolean).filter(p => p !== 'fe0f').map(p => p.padStart(4, '0')).join('-'));
  cands.push(q.toLowerCase().replace(/\.(svg|png)$/, '').replace(/-fe0f/g, ''));
  for (const k of cands) if (m[k]) return entry(k, m[k]);
  const ql = q.toLowerCase();
  for (const k in m) if (m[k][2].toLowerCase() === ql) return entry(k, m[k]);
  return null;
}
/** Name search, best first. opts: {group, limit=20, includeTones=false} */
function search(query, opts = {}) {
  const m = map(), q = String(query || '').trim().toLowerCase(), words = q.split(/\s+/).filter(Boolean), out = [];
  for (const k in m) {
    const e = m[k];
    if (opts.group && e[3].toLowerCase() !== opts.group.toLowerCase()) continue;
    if (!opts.includeTones && /-1f3f[b-f]/.test(k) && !q.includes('tone')) continue;
    const n = e[2].toLowerCase(), ws = n.split(/[^a-z0-9]+/);
    let s;
    if (!q) s = 9; else if (n === q) s = 0; else if (words.every(w => ws.includes(w))) s = 1;
    else if (n.startsWith(q)) s = 2; else if (words.every(w => n.includes(w))) s = 3;
    else if (e[4].includes(q)) s = 4; else continue;
    out.push([s, e[5], k]);
  }
  out.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  return out.slice(0, Math.max(1, opts.limit || 20)).map(([, , k]) => entry(k, m[k]));
}
/** Default + every skin-tone variant. */
function variants(q) {
  const e = get(q); if (!e) return [];
  const base = e.key.replace(TONE_RE, ''), m = map();
  return Object.keys(m).filter(k => k.replace(TONE_RE, '') === base).sort((a, b) => m[a][5] - m[b][5]).map(k => entry(k, m[k]));
}
function categories() {
  const m = map(), res = new Map();
  Object.values(m).sort((a, b) => a[5] - b[5]).forEach(e => {
    if (!res.has(e[3])) res.set(e[3], { group: e[3], count: 0, subgroups: {} });
    const g = res.get(e[3]); g.count++; g.subgroups[e[4]] = (g.subgroups[e[4]] || 0) + 1;
  });
  return [...res.values()];
}
/** URL of the file for an emoji. format 'svg' | 'png'. */
function url(q, format = 'svg') { const e = get(q); return e ? (format === 'png' ? e.pngUrl : e.svgUrl) : null; }
/** Point URLs at your own host (e.g. '/static/xeroemoji/') after copying svg/ and png/ there. */
function setBase(b) { BASE = b.endsWith('/') ? b : b + '/'; }
const LICENSE = 'Artwork CC BY-NC 4.0 (credit "Xero Emoji by Max Infeld"); commercial use needs a license: https://github.com/maximusmaximus/xeroemoji/blob/main/COMMERCIAL-LICENSE.md';
module.exports = { VERSION, LICENSE, key, get, search, variants, categories, url, setBase, map };
