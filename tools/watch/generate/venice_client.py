"""OpenAI-compatible Venice.ai client (stdlib only)."""
from __future__ import annotations
import base64, json, os, urllib.error, urllib.request
from typing import Any, Optional

DEFAULT_BASE = "https://api.venice.ai/api/v1"
IMAGE_MODEL = "gpt-image-2-5-flare"
IMAGE_EDIT_MODEL = "gpt-image-2-5-flare-edit"
TEXT_MODEL = "z-ai-glm-5-3-flash"

class VeniceError(RuntimeError):
    pass

class VeniceClient:
    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key if api_key is not None else os.environ.get("VENICE_API_KEY", "")
        self.base_url = (base_url or os.environ.get("VENICE_BASE_URL") or DEFAULT_BASE).rstrip("/")
        if not self.api_key:
            raise VeniceError("VENICE_API_KEY is not set")

    def _request(self, method: str, path: str, body: Optional[dict] = None, timeout: int = 180) -> Any:
        data = None if body is None else json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "xeroemoji-unicode-pipeline/1.0",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
                if not raw:
                    return {}
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:2000]
            raise VeniceError(f"Venice {method} {path} -> HTTP {e.code}: {detail}") from e

    def chat(self, messages: list[dict], model: str = TEXT_MODEL, max_tokens: int = 800) -> str:
        out = self._request("POST", "/chat/completions", {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.4,
        })
        try:
            return out["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError, AttributeError) as e:
            raise VeniceError(f"unexpected chat response: {out!r}") from e

    def generate_image_png(
        self,
        prompt: str,
        *,
        model: str = IMAGE_MODEL,
        resolution: str = "1K",
        quality: str = "medium",
        aspect_ratio: str = "1:1",
    ) -> bytes:
        """Native /image/generate with transparent background; returns PNG bytes."""
        body = {
            "model": model,
            "prompt": prompt,
            "format": "png",
            "transparent_background": True,
            "resolution": resolution,
            "quality": quality,
            "aspect_ratio": aspect_ratio,
            "return_binary": False,
        }
        out = self._request("POST", "/image/generate", body, timeout=300)
        return _decode_image_payload(out)

    def multi_edit_png(
        self,
        prompt: str,
        reference_pngs: list[bytes],
        *,
        model: str = IMAGE_EDIT_MODEL,
        resolution: str = "1K",
        quality: str = "medium",
    ) -> bytes:
        """Style-lock via /image/multi-edit with reference PNGs (base64 data URLs)."""
        if not reference_pngs:
            return self.generate_image_png(prompt, resolution=resolution, quality=quality)
        # multi-edit is multipart in the public docs; use JSON with data URLs when possible
        images = [
            f"data:image/png;base64,{base64.b64encode(b).decode('ascii')}"
            for b in reference_pngs[:4]
        ]
        body = {
            "modelId": model,
            "prompt": prompt,
            "images": images,
            "format": "png",
            "transparent_background": True,
            "resolution": resolution,
            "quality": quality,
        }
        try:
            out = self._request("POST", "/image/multi-edit", body, timeout=300)
            return _decode_image_payload(out)
        except VeniceError:
            # Fall back to plain generate if multi-edit shape differs on the account
            return self.generate_image_png(prompt, resolution=resolution, quality=quality)

def _decode_image_payload(out: Any) -> bytes:
    if isinstance(out, dict):
        images = out.get("images") or out.get("data") or []
        if images:
            item = images[0]
            if isinstance(item, str):
                raw = item
            elif isinstance(item, dict):
                raw = item.get("b64_json") or item.get("base64") or item.get("image") or ""
            else:
                raw = ""
            if raw.startswith("data:"):
                raw = raw.split(",", 1)[1]
            if raw:
                return base64.b64decode(raw)
        # some Venice responses put a single field
        for key in ("image", "b64_json", "base64"):
            if key in out and isinstance(out[key], str):
                raw = out[key]
                if raw.startswith("data:"):
                    raw = raw.split(",", 1)[1]
                return base64.b64decode(raw)
    raise VeniceError(f"could not decode image payload keys={list(out)!r}" if isinstance(out, dict) else type(out))
