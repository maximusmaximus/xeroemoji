"""Mocked Recraft client tests."""
from __future__ import annotations
import base64, json, pathlib, sys, unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.watch.generate import recraft_client as rc

class FakeHTTPResponse:
    def __init__(self, payload):
        self._payload = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode()
    def read(self): return self._payload
    def __enter__(self): return self
    def __exit__(self, *a): return False

class RecraftClientTests(unittest.TestCase):
    def test_missing_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(rc.RecraftError):
                rc.RecraftClient(api_key="")

    def test_vectorize_b64(self):
        client = rc.RecraftClient(api_key="rk-test")
        svg = b"<svg/>"
        payload = {"image": {"b64_json": base64.b64encode(svg).decode()}}
        with mock.patch("urllib.request.urlopen", return_value=FakeHTTPResponse(payload)):
            self.assertEqual(client.vectorize_png(b"png-bytes"), svg)

    def test_generate_svg(self):
        client = rc.RecraftClient(api_key="rk-test")
        svg = b"<svg id='x'/>"
        payload = {"data": [{"b64_json": base64.b64encode(svg).decode()}]}
        with mock.patch("urllib.request.urlopen", return_value=FakeHTTPResponse(payload)):
            self.assertEqual(client.generate_svg("lighthouse"), svg)

if __name__ == "__main__":
    unittest.main()
