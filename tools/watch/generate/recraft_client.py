"""Recraft.ai client for SVG vectorization (stdlib only)."""
from __future__ import annotations
import base64, json, os, urllib.error, urllib.request
from typing import Any, Optional

DEFAULT_BASE = "https://external.api.recraft.ai/v1"

class RecraftError(RuntimeError):
    pass

class RecraftClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        # Max's secret name is RECRAFT_API_KEY; also accept RECRAFT_API_TOKEN for local runs
        self.api_key = api_key if api_key is not None else (
            os.environ.get("RECRAFT_API_KEY") or os.environ.get("RECRAFT_API_TOKEN") or ""
        )
        self.base_url = (base_url or os.environ.get("RECRAFT_BASE_URL") or DEFAULT_BASE).rstrip("/")
        if not self.api_key:
            raise RecraftError("RECRAFT_API_KEY is not set")

    def _request_json(self, path: str, body: dict, timeout: int = 180) -> Any:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "xeroemoji-unicode-pipeline/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:2000]
            raise RecraftError(f"Recraft POST {path} -> HTTP {e.code}: {detail}") from e

    def vectorize_png(self, png_bytes: bytes, *, shape_stacking: str = "hierarchical") -> bytes:
        """POST /images/vectorize with a data URL; returns SVG bytes."""
        data_url = "data:image/png;base64," + base64.b64encode(png_bytes).decode("ascii")
        out = self._request_json("/images/vectorize", {
            "image_url": data_url,
            "shape_stacking": shape_stacking,
            "response_format": "b64_json",
        })
        image = out.get("image") or {}
        if image.get("b64_json"):
            return base64.b64decode(image["b64_json"])
        url = image.get("url")
        if not url:
            # url response_format fallback
            out2 = self._request_json("/images/vectorize", {
                "image_url": data_url,
                "shape_stacking": shape_stacking,
            })
            url = (out2.get("image") or {}).get("url")
        if not url:
            raise RecraftError(f"vectorize response missing svg: {out!r}")
        return _download(url)

    def generate_svg(self, prompt: str, *, style_reference_data_urls: Optional[list[str]] = None) -> bytes:
        """Text-to-SVG via recraftv4_vector (optional style refs)."""
        body: dict[str, Any] = {
            "prompt": prompt,
            "model": "recraftv4_vector",
            "size": "1:1",
            "response_format": "b64_json",
        }
        if style_reference_data_urls:
            body["style_reference_urls"] = style_reference_data_urls[:10]
        out = self._request_json("/images/generations", body)
        data = out.get("data") or []
        if data and data[0].get("b64_json"):
            return base64.b64decode(data[0]["b64_json"])
        if data and data[0].get("url"):
            return _download(data[0]["url"])
        raise RecraftError(f"generate svg missing payload: {out!r}")

def _download(url: str, timeout: int = 120) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "xeroemoji-unicode-pipeline/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()
