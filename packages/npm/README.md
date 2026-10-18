# xeroemoji

A lookup library and CLI for [Xero Emoji](https://github.com/maximusmaximus/xeroemoji) by Max Infeld: 3,963 Unicode Emoji 18.0 emoji, including every skin tone. The package ships the 440 KB emoji map, the API and the browser replacer. The images are served from jsDelivr (pinned to the `v1.0.0` art tag), or from your own copy if you call `setBase()`.

```sh
npm install xeroemoji
```

```js
const xe = require('xeroemoji');
xe.get('👍🏿').svgUrl;      // https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.0/svg/1f44d-1f3ff.svg
xe.search('cat', { limit: 5 });
xe.variants('👋');          // the default + 5 skin tones
xe.setBase('/static/xeroemoji/');   // serve the images yourself
```

CLI: `npx xeroemoji get 🚀`, `npx xeroemoji search pizza`, `npx xeroemoji download 🚀 png ./emoji`.

The full image sets (SVG, PNG 512/128/72) are zips on the [latest GitHub release](https://github.com/maximusmaximus/xeroemoji/releases/latest). Demos: https://maximusmaximus.github.io/xeroemoji/

## License

CC BY-NC 4.0 (SPDX `CC-BY-NC-4.0`). Credit "Xero Emoji by Max Infeld". **Commercial use needs a separate license**, see [COMMERCIAL-LICENSE.md](https://github.com/maximusmaximus/xeroemoji/blob/main/COMMERCIAL-LICENSE.md) (also included in this package).
