"""Pipeline unit tests with mocked Venice/Recraft."""
from __future__ import annotations
import json, pathlib, sys, tempfile, unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.watch.generate import pipeline as pl
from tools.watch.generate.prompts import template_prompt

class FakeVenice:
    def chat(self, messages, model="m", max_tokens=100):
        # vision QA or prompt refine
        if isinstance(messages[0].get("content"), list):
            return "PASS: matches house style"
        return "refined prompt for emoji"
    def generate_image_png(self, prompt, **kw):
        return b"PNG"
    def multi_edit_png(self, prompt, refs, **kw):
        return b"PNG-STYLED"

class FakeRecraft:
    def vectorize_png(self, png, **kw):
        return b"<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 512 512'/>"
    def generate_svg(self, prompt, **kw):
        return b"<svg/>"

class PipelineTests(unittest.TestCase):
    def test_secrets_present(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            ok, missing = pl.secrets_present()
            self.assertFalse(ok)
            self.assertIn("VENICE_API_KEY", missing)
            self.assertIn("RECRAFT_API_KEY", missing)
        with mock.patch.dict("os.environ", {"VENICE_API_KEY": "v", "RECRAFT_API_KEY": "r"}):
            ok, missing = pl.secrets_present()
            self.assertTrue(ok)
            self.assertEqual(missing, [])

    def test_skip_without_secrets(self):
        report = json.loads((ROOT / "tools/watch/tests/fixtures/sample_report.json").read_text())
        # fix seq to a plausible hex so staging paths are fine if reached
        report["missing_from_locked_released"][0]["seq"] = "1f985"
        with mock.patch.dict("os.environ", {}, clear=True):
            out = pl.run_pipeline(ROOT, report, dry_run=False)
        self.assertEqual(out["status"], "skipped_missing_secrets")

    def test_dry_run(self):
        report = json.loads((ROOT / "tools/watch/tests/fixtures/sample_report.json").read_text())
        report["missing_from_locked_released"][0]["seq"] = "1f985"
        out = pl.run_pipeline(ROOT, report, dry_run=True, max_candidates=5)
        self.assertEqual(out["status"], "dry_run")
        self.assertEqual(len(out["candidates"]), 1)

    def test_run_with_fakes(self):
        report = json.loads((ROOT / "tools/watch/tests/fixtures/sample_report.json").read_text())
        report["missing_from_locked_released"][0]["seq"] = "1f985"
        report["missing_from_locked_released"][0]["name"] = "eagle"
        with tempfile.TemporaryDirectory() as td:
            out_dir = pathlib.Path(td) / "out"
            with mock.patch.dict("os.environ", {"VENICE_API_KEY": "v", "RECRAFT_API_KEY": "r"}):
                # Avoid reading real pngs for style refs by patching picker
                with mock.patch("tools.watch.generate.pipeline.pick_style_refs", return_value=[]):
                    summary = pl.run_pipeline(
                        ROOT, report, out_dir=out_dir, max_candidates=1,
                        venice=FakeVenice(), recraft=FakeRecraft(),
                    )
            self.assertEqual(summary["status"], "ok")
            self.assertEqual(summary["staged"], 1)
            self.assertTrue((out_dir / "1f985.svg").exists())
            self.assertTrue((out_dir / "1f985.png").exists())

    def test_template_prompt(self):
        p = template_prompt("eagle", "1f985", "Animals & Nature", "animal-bird")
        self.assertIn("eagle", p)
        self.assertIn("transparent", p.lower())

if __name__ == "__main__":
    unittest.main()
