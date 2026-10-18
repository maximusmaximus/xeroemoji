# xeroemoji (npm), prepared but not published yet

A lookup library for [Xero Emoji](https://github.com/maximusmaximus/xeroemoji): 3,963 Unicode Emoji 18.0 emoji. It ships only the 440 KB emoji map, the API and the browser replacer. The images themselves are served from jsDelivr (pinned to `v1.0.0`), or from your own copy if you call `setBase()`.

```js
const xe = require('xeroemoji');
xe.get('👍🏿').svgUrl;      // https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.0/svg/1f44d-1f3ff.svg
xe.search('cat', { limit: 5 });
xe.variants('👋');          // the default + 5 skin tones
```
CLI: `npx xeroemoji get 🚀`, `npx xeroemoji download 🚀 png ./emoji`.
Until it is published, install it from the repo: `npm install ./packages/npm` (run `npm pack` there first so the map gets bundled), or use the release asset `xeroemoji-1.0.0.tgz`.

Artwork: CC BY-NC 4.0. Credit "Xero Emoji by Max Infeld". Commercial use needs a license, see [COMMERCIAL-LICENSE.md](https://github.com/maximusmaximus/xeroemoji/blob/main/COMMERCIAL-LICENSE.md).
