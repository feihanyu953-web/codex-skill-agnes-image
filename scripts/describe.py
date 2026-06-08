#!/usr/bin/env python3
"""describe.py — standalone image description via 火山引擎 Vision.
Use when the user asks "describe this image" or "what does this image show".
This script reads the image internally and NEVER outputs image bytes or base64.
The agent must NOT call view_image — just run this script directly.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

ARK_API_KEY = os.environ.get("ARK_API_KEY", "YOUR_ARK_API_KEY_HERE")
ARK_BASE = "https://ark.cn-beijing.volces.com/api/v3"
ARK_MODEL = "doubao-seed-2-0-lite-260215"
MAX_ERROR_OUTPUT = 500

def resolve_to_data_uri(image_input: str) -> str:
    """Local file → data URI; URL/data URI pass through."""
    if image_input.startswith(("http://", "https://", "data:")):
        return image_input
    path = Path(image_input)
    if not path.is_file():
        raise SystemExit(f"Image not found: {image_input}")
    ext = path.suffix.lower().lstrip(".")
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp"}
    mime = mime_map.get(ext, "image/png")
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"

def describe(image_input: str, detail: str) -> str:
    """Call 火山引擎 Vision to describe the image."""
    image_url = resolve_to_data_uri(image_input)

    detail_prompts = {
        "brief": "Please describe this image in one short sentence.",
        "standard": (
            "Please describe this image in detail, including: "
            "1) main subject and composition 2) colors and lighting "
            "3) style and atmosphere 4) notable details. "
            "Output as a flowing paragraph without bullet points."
        ),
        "full": (
            "Please provide an exhaustive description of this image, covering: "
            "subject, composition, colors, lighting, style, atmosphere, textures, "
            "background, foreground, spatial relationships, and any text or symbols visible. "
            "Output as a flowing paragraph."
        ),
    }
    prompt_text = detail_prompts.get(detail, detail_prompts["standard"])

    payload = {
        "model": ARK_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": prompt_text},
            ],
        }],
        "max_tokens": 500,
    }

    req = urllib.request.Request(
        f"{ARK_BASE}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {ARK_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail_err = exc.read().decode("utf-8", errors="replace")
        if len(detail_err) > MAX_ERROR_OUTPUT:
            detail_err = detail_err[:MAX_ERROR_OUTPUT] + "... [TRUNCATED]"
        raise SystemExit(f"Vision API HTTP {exc.code}: {detail_err}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Vision API network error: {exc}")

    content = result["choices"][0]["message"]["content"]
    return content.strip()

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Describe an image using 火山引擎 Vision. Zero base64 output."
    )
    parser.add_argument("image", help="Local image path or HTTP URL")
    parser.add_argument(
        "--detail", choices=("brief", "standard", "full"),
        default="standard",
        help="Description detail level (default: standard)",
    )
    args = parser.parse_args()

    description = describe(args.image, args.detail)
    print(description)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())