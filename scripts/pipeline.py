#!/usr/bin/env python3
"""
pipeline.py  —— 三段式流水线

流程:
  输入图片 → 火山引擎视觉模型(看图描述) → LLM(分析优化prompt) → Agnes(生图)

用法:
  python scripts/pipeline.py --input photo.jpg --output result.png
  python scripts/pipeline.py --input https://example.com/photo.jpg --style "油画风格"

环境变量 (也可直接编辑下方 API_KEYS):
  ARK_API_KEY       火山引擎方舟 API Key (Vision)
  AGNES_API_KEY     Agnes Image API Key
  LLM_BASE_URL      LLM API 地址 (默认: 本地 DeepSeek http://127.0.0.1:57321/v1)
  LLM_MODEL         LLM 模型名 (默认: deepseek-v4-pro)
  LLM_API_KEY       LLM API Key (本地服务无需设置)

注意: 在 Codex 中使用时，prompt 优化由 Codex 内置大模型完成，
无需额外配置 LLM 步骤。本脚本的 LLM 步骤仅用于独立运行场景。
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


# ───────────────────────────────────────────────────────────
# API 配置
# ───────────────────────────────────────────────────────────
API_KEYS = {
    # 火山引擎方舟 → https://console.volcengine.com/ark
    "ark": os.environ.get("ARK_API_KEY", "YOUR_ARK_API_KEY_HERE"),
    # Agnes Image
    "agnes": os.environ.get("AGNES_API_KEY", "YOUR_AGNES_API_KEY_HERE"),
}

# LLM 配置 (用于 prompt 优化步骤，支持任意 OpenAI 兼容 API)
# 默认指向本地 DeepSeek 代理，可通过环境变量覆盖
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "http://127.0.0.1:57321/v1")
LLM_MODEL    = os.environ.get("LLM_MODEL", "deepseek-v4-pro")
LLM_API_KEY  = os.environ.get("LLM_API_KEY", "no-key-needed")

# 火山引擎
ARK_BASE     = "https://ark.cn-beijing.volces.com/api/v3"
ARK_MODEL    = "doubao-seed-2-0-lite-260215"

# Agnes
AGNES_ENDPOINT = "https://apihub.agnes-ai.com/v1/images/generations"
AGNES_MODEL    = "agnes-image-2.1-flash"
MAX_ERROR_OUTPUT = 500  # safety: never dump full API responses into context


# ───────────────────────────────────────────────────────────
# 第一步: 视觉理解 (火山引擎 Ark)
# ───────────────────────────────────────────────────────────
def describe_image(image_input: str) -> str:
    """用火山引擎视觉模型描述图片内容。"""
    image_url = _resolve_image_url(image_input)

    payload = {
        "model": ARK_MODEL,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": image_url}},
                {"type": "text", "text": (
                    "请用一段连续的文字详细描述这张图片，包括："
                    "1) 画面主体和构图 2) 色彩和光线 3) 风格和氛围 4) 细节特征。"
                    "不需要序号，直接输出流畅的描述段落。"
                )},
            ],
        }],
        "max_tokens": 500,
    }

    result = _call_api(
        f"{ARK_BASE}/chat/completions", API_KEYS["ark"], payload
    )
    msg = result["choices"][0]["message"]; return (msg.get("content") or msg.get("reasoning_content") or "").strip()


# ───────────────────────────────────────────────────────────
# 第二步: Prompt 优化 (LLM — 默认本地 DeepSeek，可配置)
# ───────────────────────────────────────────────────────────
def optimize_prompt(description: str, user_instruction: str) -> str:
    """用 LLM 根据图片描述和用户指令，生成优化的图片生成 prompt。"""
    system_prompt = (
        "你是一个专业的 AI 绘图提示词工程师。用户会提供一张图片的文字描述和修改需求，
        "你需要生成一个用于 AI 图片生成的英文 prompt。要求：
        "1) 用英文输出 2) 包含主体、环境、风格、光照、构图、质量关键词 "
        "3) 长度 50-150 词 4) 只输出 prompt 本身，不要加任何解释。"
    )

    user_text = (
        f"图片描述:\n{description}\n\n"
        f"用户需求: {user_instruction or '保持原图风格，提升画面质量'}"
    )

    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    result = _call_api(
        f"{LLM_BASE_URL}/chat/completions",
        LLM_API_KEY,
        payload,
    )
    msg = result["choices"][0]["message"]; return (msg.get("content") or msg.get("reasoning_content") or "").strip()


# ───────────────────────────────────────────────────────────
# 第三步: 图片生成 (Agnes)
# ───────────────────────────────────────────────────────────
def generate_image(prompt: str, size: str, output_path: str | None = None) -> str:
    """调用 Agnes API 生成图片。"""
    payload = {
        "model": AGNES_MODEL,
        "prompt": prompt,
        "size": size,
        "extra_body": {"response_format": "url"},
    }

    print(f"  Generating (prompt length: {len(prompt)} chars)...")
    result = _call_api(
        AGNES_ENDPOINT, API_KEYS["agnes"], payload, timeout=300
    )

    data = result.get("data", [])
    if not data:
        raise SystemExit("Agnes returned no image data.")

    image_url = data[0].get("url")
    if not image_url:
        raise SystemExit("No image URL in Agnes response.")

    if output_path:
        _download_image(image_url, output_path)
        return output_path
    return image_url


# ───────────────────────────────────────────────────────────
# 工具函数
# ───────────────────────────────────────────────────────────
def _resolve_image_url(image_input: str) -> str:
    """本地文件路径 → Base64 Data URI；URL 直接返回。"""
    if image_input.startswith(("http://", "https://", "data:")):
        return image_input

    path = Path(image_input)
    if not path.is_file():
        raise SystemExit(f"Image not found: {image_input}")

    ext = path.suffix.lower().lstrip(".")
    mime_map = {
        "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp",
    }
    mime = mime_map.get(ext, "image/png")
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _call_api(url: str, api_key: str, payload: dict,
              timeout: int = 60) -> dict:
    """调用 OpenAI 兼容 API。"""
    headers = {"Content-Type": "application/json"}
    if api_key and api_key != "no-key-needed":
        headers["Authorization"] = f"Bearer {api_key}"

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} from {url}: {detail[:MAX_ERROR_OUTPUT]}{'... [TRUNCATED]' if len(detail) > MAX_ERROR_OUTPUT else ''}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"Network error ({url}): {exc}")


def _download_image(url: str, output_path: str) -> None:
    """下载图片到本地。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, path)


# ───────────────────────────────────────────────────────────
# 主入口
# ───────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Image → Vision → LLM → Image Gen pipeline",
    )
    parser.add_argument("--input", "-i", required=True,
                        help="Input image (local path or HTTP URL)")
    parser.add_argument("--output", "-o", default="pipeline_output.png",
                        help="Output image path (default: pipeline_output.png)")
    parser.add_argument("--style", "-s", default="",
                        help="Custom style/instruction (CN or EN)")
    parser.add_argument("--size", default="1024x768",
                        help="Output size (default: 1024x768)")
    parser.add_argument("--skip-vision", action="store_true",
                        help="Skip vision analysis, use --style directly")
    args = parser.parse_args()

    sep = "=" * 50

    if args.skip_vision:
        description = args.style or "A beautiful high-quality image"
        print(f"\n{sep}\n Step 1: Skip vision analysis\n{sep}")
        print(f"  Using: {description[:80]}...")
    else:
        print(f"\n{sep}\n Step 1: Vision analysis (Volcengine Ark)\n{sep}")
        print(f"  Analyzing: {args.input}")
        description = describe_image(args.input)
        print(f"  Description: {description[:200]}...")

    print(f"\n{sep}\n Step 2: Prompt optimization (LLM: {LLM_MODEL})\n{sep}")
    optimized = optimize_prompt(description, args.style)
    print(f"  Optimized:\n  {optimized}")

    print(f"\n{sep}\n Step 3: Image generation (Agnes)\n{sep}")
    output = generate_image(optimized, args.size, args.output)
    print(f"  Output: {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

