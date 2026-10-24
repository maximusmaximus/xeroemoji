"""python3 -m unittest discover -s packages/python/tests -v   (from the repo root)"""
import json, os, subprocess, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__)); PKG = os.path.dirname(HERE); ROOT = os.path.dirname(os.path.dirname(PKG))
sys.path.insert(0, PKG)
import xeroemoji as xe


class Core(unittest.TestCase):
    def test_map_complete_and_files_exist(self):
        m = xe._load(); self.assertEqual(len(m), 3963)
        for k, e in m.items():
            self.assertTrue(os.path.exists(f'{ROOT}/svg/{e[0]}.svg') and os.path.exists(f'{ROOT}/png/{e[0]}.png'), k)
            self.assertEqual(xe.get(e[1])['file'], e[0])          # every fully-qualified emoji round-trips

    def test_lookups(self):
        self.assertEqual(xe.get('👍🏿')['codepoints'], 'U+1F44D U+1F3FF')
        self.assertEqual(xe.get('1f469-1f3fd-200d-1f680')['skin_tone'], 'medium')
        self.assertEqual(xe.get('U+1F600')['emoji'], '😀')
        self.assertEqual(xe.get('🏳‍🌈')['file'], '1f3f3-200d-1f308')   # FE0F missing in input
        self.assertEqual(xe.get('#️⃣')['file'], '0023-20e3')
        self.assertEqual(xe.get('2764.svg')['name'], 'red heart')
        self.assertEqual(xe.get('Flag: Japan')['file'], '1f1ef-1f1f5')
        self.assertIsNone(xe.get('definitely not an emoji'))

    def test_search_variants_categories(self):
        self.assertEqual(xe.search('cat')[0]['emoji'], '🐈')
        self.assertEqual(xe.search('flag japan')[0]['file'], '1f1ef-1f1f5')
        self.assertTrue(all(r['group'] == 'Food & Drink' for r in xe.search('a', group='Food & Drink', limit=50)))
        self.assertEqual([v['skin_tone'] for v in xe.variants('👋🏾')], [None, 'light', 'medium-light', 'medium', 'medium-dark', 'dark'])
        self.assertEqual(len(xe.variants('🧑‍🤝‍🧑')), 26)
        self.assertEqual(xe.variants('🐈'), [xe.get('🐈')])
        self.assertEqual(sum(c['count'] for c in xe.categories()), 3963)

    def test_emojify(self):
        h = xe.emojify('a 👋🏽 <b> © ©️')
        self.assertIn('1f44b-1f3fd.svg', h); self.assertIn('&lt;b&gt;', h); self.assertIn('00a9.svg', h)
        self.assertEqual(h.count('<img'), 2)                       # bare © (text style) is left alone

    def test_cli(self):
        r = subprocess.run([sys.executable, '-m', 'xeroemoji', 'get', '🚀'], cwd=PKG, capture_output=True, text=True, check=True)
        self.assertEqual(json.loads(r.stdout)['file'], '1f680')


class MCP(unittest.TestCase):
    def rpc(self, msgs):
        p = subprocess.run([sys.executable, os.path.join(ROOT, 'mcp', 'server.py')], input='\n'.join(json.dumps(m) for m in msgs) + '\n',
                           capture_output=True, text=True, timeout=60, check=True)
        return [json.loads(l) for l in p.stdout.splitlines() if l.strip()]

    def test_protocol_flow(self):
        out = self.rpc([
            {'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {'protocolVersion': '2025-06-18', 'capabilities': {}, 'clientInfo': {'name': 't', 'version': '1'}}},
            {'jsonrpc': '2.0', 'method': 'notifications/initialized'},
            {'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list'},
            {'jsonrpc': '2.0', 'id': 3, 'method': 'tools/call', 'params': {'name': 'search_emoji', 'arguments': {'query': 'pizza', 'limit': 3}}},
            {'jsonrpc': '2.0', 'id': 4, 'method': 'tools/call', 'params': {'name': 'get_emoji', 'arguments': {'emoji': '👩🏿‍🍳', 'include_svg': True}}},
            {'jsonrpc': '2.0', 'id': 5, 'method': 'tools/call', 'params': {'name': 'list_categories', 'arguments': {}}},
            {'jsonrpc': '2.0', 'id': 6, 'method': 'tools/call', 'params': {'name': 'get_skin_tone_variants', 'arguments': {'emoji': '👍'}}},
            {'jsonrpc': '2.0', 'id': 7, 'method': 'tools/call', 'params': {'name': 'emojify_text', 'arguments': {'text': 'ship it 🚀', 'format': 'markdown'}}},
            {'jsonrpc': '2.0', 'id': 8, 'method': 'tools/call', 'params': {'name': 'get_emoji', 'arguments': {'emoji': 'zzz-not-real'}}},
            {'jsonrpc': '2.0', 'id': 9, 'method': 'nope'},
            {'jsonrpc': '2.0', 'id': 10, 'method': 'ping'}])
        r = {m['id']: m for m in out}
        self.assertEqual(len(out), 10)                               # the notification gets no reply
        self.assertEqual(r[1]['result']['serverInfo']['name'], 'xeroemoji')
        self.assertEqual({t['name'] for t in r[2]['result']['tools']}, {'search_emoji', 'get_emoji', 'list_categories', 'get_skin_tone_variants', 'emojify_text'})
        s = r[3]['result']['structuredContent']; self.assertEqual(s['results'][0]['emoji'], '🍕')
        self.assertEqual(json.loads(r[3]['result']['content'][0]['text']), s)
        g = r[4]['result']['structuredContent']; self.assertEqual(g['file'], '1f469-1f3ff-200d-1f373'); self.assertTrue(g['svg'].startswith('<svg'))
        self.assertIn('CC BY 4.0', g['license']); self.assertNotIn('NC', g['license'])
        self.assertEqual(r[5]['result']['structuredContent']['total'], 3963)
        self.assertEqual(r[6]['result']['structuredContent']['count'], 6)
        self.assertIn('![🚀](https://cdn.jsdelivr.net/gh/maximusmaximus/xeroemoji@v1.0.2/svg/1f680.svg', r[7]['result']['structuredContent']['output'])
        self.assertTrue(r[8]['result']['isError'])
        self.assertEqual(r[9]['error']['code'], -32601)
        self.assertEqual(r[10]['result'], {})


if __name__ == '__main__':
    unittest.main()
