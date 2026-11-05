"""Mocked Venice client tests."""
from __future__ import annotations
import base64, json, pathlib, sys, unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.watch.generate import venice_client as vc

class FakeHTTPResponse:
    def __init__(self, payload, status=200):
        self._payload = payload if isinstance(payload, (bytes, bytearray)) else json.dumps(payload).encode()
        self.status = status
    def read(self): return self._payload
    def __enter__(self): return self
    def __exit__(self, *a): return False

class VeniceClientTests(unittest.TestCase):
    def test_missing_key(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(vc.VeniceError):
                vc.VeniceClient(api_key="")

    def test_chat(self):
        client = vc.VeniceClient(api_key="test-key")
        payload = {"choices": [{"message": {"content": "  hello prompt  "}}]}
        with mock.patch("urllib.request.urlopen", return_value=FakeHTTPResponse(payload)):
            self.assertEqual(client.chat([{"role": "user", "content": "hi"}]), "hello prompt")

    def test_generate_image_png(self):
        client = vc.VeniceClient(api_key="test-key")
        raw = b"PNGDATA"
        b64 = base64.b64encode(raw).decode()
        payload = {"images": [b64]}
        with mock.patch("urllib.request.urlopen", return_value=FakeHTTPResponse(payload)):
            self.assertEqual(client.generate_image_png("a prompt"), raw)

    def test_decode_data_url(self):
        raw = b"XYZ"
        out = vc._decode_image_payload({"data": [{"b64_json": base64.b64encode(raw).decode()}]})
        self.assertEqual(out, raw)

if __name__ == "__main__":
    unittest.main()
