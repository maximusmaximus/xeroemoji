#!/usr/bin/env node
'use strict';
// npx xeroemoji get 👍🏿 | search cat [limit] | variants 👋 | url 🚀 [svg|png] | download 🚀 [svg|png] [dir]
const xe = require('./index.js'), fs = require('fs'), path = require('path');
const [cmd, a, b, c] = process.argv.slice(2);
const out = o => console.log(JSON.stringify(o, null, 1));
(async () => {
  switch (cmd) {
    case 'get': { const e = xe.get(a); if (!e) { console.error('not found: ' + a); process.exit(1); } out(e); break; }
    case 'search': out(xe.search(a, { limit: Number(b) || 20 })); break;
    case 'variants': out(xe.variants(a)); break;
    case 'categories': out(xe.categories()); break;
    case 'url': { const u = xe.url(a, b || 'svg'); if (!u) process.exit(1); console.log(u); break; }
    case 'download': {
      const e = xe.get(a); if (!e) { console.error('not found: ' + a); process.exit(1); }
      const fmt = b || 'svg', dir = c || '.', r = await fetch(fmt === 'png' ? e.pngUrl : e.svgUrl);
      if (!r.ok) { console.error('HTTP ' + r.status); process.exit(1); }
      const dst = path.join(dir, `${e.file}.${fmt}`); fs.mkdirSync(dir, { recursive: true });
      fs.writeFileSync(dst, Buffer.from(await r.arrayBuffer())); console.log(dst); break;
    }
    default: console.log('usage: xeroemoji get <emoji|codepoint|name> | search <words> [limit] | variants <emoji> | categories | url <emoji> [svg|png] | download <emoji> [svg|png] [dir]\n' + xe.LICENSE);
  }
})();
