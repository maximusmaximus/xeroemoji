"""Build image prompts for new emoji (template + optional Venice text model)."""
from __future__ import annotations
from typing import Optional, Protocol

HOUSE_STYLE = (
    "Xero Emoji / Xerographer house style: thick black outline, glossy yellow gradient faces when applicable, "
    "big white eyes with dark pupils, open mouth with red tongue when smiling, flat vector sticker look, "
    "centered on a transparent background, square emoji glyph, no text, no watermark, no drop shadow floor."
)

class ChatClient(Protocol):
    def chat(self, messages: list[dict], model: str = ..., max_tokens: int = ...) -> str: ...

def template_prompt(name: str, seq: str, group: str = "", subgroup: str = "") -> str:
    bits = [f"Single emoji glyph of: {name}."]
    if group:
        bits.append(f"Unicode group: {group}.")
    if subgroup:
        bits.append(f"Subgroup: {subgroup}.")
    bits.append(f"Codepoints: {seq}.")
    bits.append(HOUSE_STYLE)
    bits.append("Die-cut sticker, isolated subject, transparent background, high contrast, readable at 32px.")
    return " ".join(bits)

def refine_prompt(client: ChatClient, *, name: str, seq: str, group: str = "", subgroup: str = "") -> str:
    base = template_prompt(name, seq, group, subgroup)
    try:
        out = client.chat([
            {"role": "system", "content": (
                "You write concise text-to-image prompts for a locked emoji art style. "
                "Return ONLY the prompt text, no quotes or commentary."
            )},
            {"role": "user", "content": (
                f"Refine this prompt so a diffusion model matches the Xero Emoji house style "
                f"for the Unicode emoji '{name}' ({seq}). Keep transparent background and no text.\n\n{base}"
            )},
        ], max_tokens=400)
        return out.strip() or base
    except Exception:
        return base

def vision_qa_messages(name: str, seq: str, candidate_data_url: str, ref_data_urls: list[str]) -> list[dict]:
    content: list[dict] = [
        {"type": "text", "text": (
            f"You are QA for Xero Emoji. Candidate is Unicode '{name}' ({seq}). "
            "Compare it to the style reference images. Reply with exactly one line: "
            "PASS: <reason> or FAIL: <reason>. Fail if outline is missing, background is opaque, "
            "style is photorealistic, or meaning does not match the name."
        )},
        {"type": "image_url", "image_url": {"url": candidate_data_url}},
    ]
    for u in ref_data_urls[:3]:
        content.append({"type": "image_url", "image_url": {"url": u}})
    return [{"role": "user", "content": content}]
