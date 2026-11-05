"""Unit tests for the Unicode watcher parsers (no network)."""
from __future__ import annotations
import importlib.util, pathlib, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
WATCH = ROOT / "tools" / "watch" / "watch_unicode.py"

def load():
    spec = importlib.util.spec_from_file_location("watch_unicode", WATCH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class WatchUnicodeTests(unittest.TestCase):
    def test_norm_strips_fe0f(self):
        w = load()
        self.assertEqual(w.norm("00a9-fe0f"), "00a9")
        self.assertEqual(w.norm("1F44D-1F3FF"), "1f44d-1f3ff")

    def test_parse_test(self):
        w = load()
        txt = (ROOT / "tools/watch/tests/fixtures/sample_emoji_test.txt").read_text()
        ver, fq = w.parse_test(txt)
        self.assertEqual(ver, "18.0")
        self.assertIn("1f600", fq)
        self.assertEqual(fq["1f600"][1], "grinning face")
        self.assertEqual(len(fq), 3)

if __name__ == "__main__":
    unittest.main()
