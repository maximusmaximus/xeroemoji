"""Tests for issue body builder pieces and UTS candidate audit."""
from __future__ import annotations
import importlib.util, json, pathlib, sys, tempfile, unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

class IssueAndUtsTests(unittest.TestCase):
    def test_body_from_report(self):
        mod = load("issue_from_report", ROOT / "tools/watch/issue_from_report.py")
        report = json.loads((ROOT / "tools/watch/tests/fixtures/sample_report.json").read_text())
        body = mod.body_from_report(report)
        self.assertIn("NEW_EMOJI", body)
        self.assertIn("unicode-watch.yml", body)

    def test_uts_audit_ok_and_bad(self):
        mod = load("run_uts_audit", ROOT / "tools/watch/run_uts_audit.py")
        fixture = ROOT / "tools/watch/tests/fixtures/sample_emoji_test.txt"
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td)
            (d / "1f600.svg").write_text("<svg/>")
            (d / "1f600.png").write_bytes(b"x")
            self.assertEqual(mod.main(["--candidates", str(d), "--emoji-test", str(fixture)]), 0)
            (d / "not-a-cp.svg").write_text("<svg/>")
            self.assertEqual(mod.main(["--candidates", str(d), "--emoji-test", str(fixture)]), 1)

if __name__ == "__main__":
    unittest.main()
