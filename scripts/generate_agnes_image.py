#!/usr/bin/env python3
"""Call Agnes Image 2.1 Flash for text-to-image or image-to-image generation.

Set your API key in API_KEY below before running.
Get a key at: https://agnes-ai.com

Usage:
  python generate_agnes_image.py "prompt" --size 1024x768 --response-format url
  python generate_agnes_image.py "prompt" --size 1024x768 --response-format b64_json --output image.png
  python generate_agnes_image.py "prompt" --input-image "https://..." --size 1024x768 --response-format url
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


def build_payload(args: argparse.Namespace) -> dict:
    payload = {
        "model": MODEL,
        "prompt": args.prompt,
        "size": args.size,
    }

    extra_body = {}
    if args.input_image:
        extra_body["image"] = args.input_image
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
            "Replace API_KEY in scripts/generate_agnes_image.py with your Agnes AI API key.\n"
            "Get one at: https://agnes-ai.com"
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
        raise SystemExit(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Request failed: {exc}") from exc


def save_base64_image(b64_json: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(base64.b64decode(b64_json))


def handle_result(result: dict, output: str | None) -> None:
    data = result.get("data") or []
    if not data:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        raise SystemExit("No image data returned.")

    first_image = data[0]
    image_url = first_image.get("url")
    image_base64 = first_image.get("b64_json")

    if image_base64 and output:
        save_base64_image(image_base64, Path(output))
        print(output)
        return

    if image_url:
        print(image_url)
        return

    if image_base64:
        print(image_base64)
        return

    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit("API returned data but no url or b64_json field found.")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate or edit images with Agnes Image 2.1 Flash."
    )
    parser.add_argument("prompt", help="Text prompt describing the image or edit.")
    parser.add_argument("--size", default="1024x768", help="Output size, e.g. 1024x768.")
    parser.add_argument(
        "--input-image",
        action="append",
        help="Public image URL or Data URI Base64 input. Repeat for multiple images.",
    )
    parser.add_argument(
        "--response-format",
        choices=("url", "b64_json"),
        default="url",
        help="url (short) or b64_json (use with --output to save to file).",
    )
    parser.add_argument(
        "--output",
        help="Save Base64 image to this file path.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=180,
        help="HTTP timeout in seconds (60-360 recommended).",
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
