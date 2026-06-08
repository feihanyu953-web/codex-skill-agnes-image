#!/usr/bin/env python3
"""Call Agnes Image 2.1 Flash for text-to-image or image-to-image generation.

SAFETY NOTES (for Codex agents):
- Always prefer --response-format url. URLs are short strings that won't flood
  the context window; raw Base64 output can be megabytes and will instantly
  exhaust your token budget.
- When you must use b64_json, ALWAYS pair it with --output to save to a file.
  The script will print only the file path instead of the raw Base64 data.
- The script makes outbound HTTPS calls. If you hit a URLError / sandbox
  failure, request a prefix-rule approval for the full script path.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_KEY = "YOUR_AGNES_API_KEY_HERE"
ENDPOINT = "https://apihub.agnes-ai.com/v1/images/generations"
MODEL = "agnes-image-2.1-flash"
MAX_ERROR_OUTPUT = 500  # safety: never dump full API responses into context


def build_payload(args: argparse.Namespace) -> dict:
    payload = {
        "model": MODEL,
        "prompt": args.prompt,
        "size": args.size,
    }

    extra_body = {}
    if args.input_image:
        extra_body["image"] = [resolve_input_image(img) for img in args.input_image]
        extra_body["response_format"] = args.response_format
    elif args.response_format == "b64_json":
        payload["return_base64"] = True
    else:
        extra_body["response_format"] = "url"

    if extra_body:
        payload["extra_body"] = extra_body

    return payload


def call_api(payload: dict, timeout: int) -> dict:
    if API_KEY == "YOUR_AGNES_API_KEY_HERE":
        raise SystemExit(
            "Replace API_KEY in scripts/generate_agnes_image.py before making live API calls."
        )

    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if len(detail) > MAX_ERROR_OUTPUT:
            detail = detail[:MAX_ERROR_OUTPUT] + '... [TRUNCATED]'
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        msg = (
            f"Request failed: {exc}\n"
            "This is likely a sandbox / network restriction. If running inside Codex,\n"
            "request a prefix-rule approval for this script so outbound HTTPS to\n"
            f"{ENDPOINT} is allowed without repeated escalation."
        )
        raise SystemExit(msg) from exc


def save_base64_image(b64_json: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(b64_json))


def download_image(url: str, output_path: Path) -> None:
    """Download an image URL to a local file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, output_path)



def resolve_input_image(image_input: str) -> str:
    """Resolve --input-image: URL/Data-URI pass through; local file -> Data URI."""
    if image_input.startswith(("http://", "https://", "data:")):
        return image_input
    p = Path(image_input)
    if not p.is_file():
        raise SystemExit(f"Input image not found: {image_input}")
    ext = p.suffix.lower().lstrip(".")
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp"}
    mime = mime_map.get(ext, "image/png")
    b64 = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{b64}"
def handle_result(result: dict, output: str | None) -> None:
    data = result.get("data") or []
    if not data:
        sys.stderr.write('[ERROR] API returned empty data array. Response (truncated):\n')
        sys.stderr.flush()
        result_str = json.dumps(result, ensure_ascii=False, indent=2)
        print(result_str[:MAX_ERROR_OUTPUT])
        if len(result_str) > MAX_ERROR_OUTPUT:
            print('... [TRUNCATED]')
        raise SystemExit("No image data returned.")

    first_image = data[0]
    image_url = first_image.get("url")
    image_base64 = first_image.get("b64_json")

    # URL + --output: download from remote to local (zero base64 in context!)
    if image_url and output:
        download_image(image_url, Path(output))
        print(output)
        return

    if image_base64 and output:
        save_base64_image(image_base64, Path(output))
        print(output)
        return

    # URL only (no --output): print remote URL
    if image_url:
        print(image_url)
        return

    if image_base64:
        # Raw Base64 output will flood the calling agent's context window.
        # Emit a prominent warning to stderr so the agent can intercept it.
        b64_len = len(image_base64)
        sys.stderr.write(
            f"[WARNING] About to print {b64_len:,}-char Base64 image to stdout.\n"
            "This will likely exhaust your context window. Next time use:\n"
            "  --response-format url       (preferred - short URL string)\n"
            "  --response-format b64_json --output image.png  (saves to file, prints path only)\n"
        )
        sys.stderr.flush()
        print(image_base64)
        return

    # Neither url nor b64_json in data[0] — unexpected API response format
    sys.stderr.write(
        "[ERROR] API returned data[0] but neither 'url' nor 'b64_json' was present.\n"
        "Full response dumped below. The API may have changed its output schema,\n"
        "or the request may have triggered an error inside 'data'.\n"
    )
    sys.stderr.flush()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(1)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or edit images with Agnes Image 2.1 Flash."
    )
    parser.add_argument("prompt", help="Text prompt describing the image or edit.")
    parser.add_argument("--size", default="1024x768", help="Output size, e.g. 1024x768.")
    parser.add_argument(
        "--input-image",
        action="append",
        help="Image input: URL, Data URI, or local file path (auto-converted). Repeat for multiple images.",
    )
    parser.add_argument(
        "--response-format",
        choices=("url", "b64_json"),
        default="url",
        help="url (recommended: pair with --output for local save) or b64_json (pair with --output).",
    )
    parser.add_argument(
        "--output",
        help="Save image to this local file path. Works with both url and b64_json. Prints only the path, never raw data.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="HTTP timeout in seconds. Official docs suggest 60-360 seconds.",
    )
    parser.add_argument(
        "--print-payload",
        action="store_true",
        help="Print request JSON without calling the API.",
    )
    return parser.parse_args(argv)


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    payload = build_payload(args)

    if args.print_payload:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    result = call_api(payload, args.timeout)
    handle_result(result, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
