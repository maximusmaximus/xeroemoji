'use strict';
const assert = require('assert'), fs = require('fs');
if (!fs.existsSync(__dirname + '/emoji-map.json')) fs.copyFileSync(__dirname + '/../../demos/emoji-map.json', __dirname + '/emoji-map.json');
const xe = require('./index.js');
const m = xe.map(); assert.strictEqual(Object.keys(m).length, 3963);
assert.strictEqual(xe.get('👍🏿').file, '1f44d-1f3ff');
assert.strictEqual(xe.get('U+1F469 U+1F3FD U+200D U+1F680').name, 'woman astronaut: medium skin tone');
assert.strictEqual(xe.get('🏳️‍🌈').file, '1f3f3-200d-1f308');
assert.strictEqual(xe.get('🏳‍🌈').file, '1f3f3-200d-1f308');            // without FE0F
assert.strictEqual(xe.get('#️⃣').file, '0023-20e3');
assert.strictEqual(xe.get('red heart').file, '2764');
assert.strictEqual(xe.get('1F600').emoji, '😀');
assert.strictEqual(xe.get('Flag: Japan').file, '1f1ef-1f1f5');
assert.strictEqual(xe.search('flag japan')[0].file, '1f1ef-1f1f5');
assert.strictEqual(xe.get('nope-not-an-emoji'), null);
assert.strictEqual(xe.search('cat')[0].emoji, '🐈');
assert.strictEqual(xe.variants('👋🏾').length, 6);
assert.strictEqual(xe.categories().reduce((s, c) => s + c.count, 0), 3963);
for (const k in m) assert.strictEqual(xe.get(m[k][1]).file, m[k][0], k);   // every emoji round-trips
assert.ok(xe.url('🚀').startsWith('https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.2/svg/1f680.svg'));
console.log('npm package tests OK (' + Object.keys(m).length + ' emoji round-trip)');
