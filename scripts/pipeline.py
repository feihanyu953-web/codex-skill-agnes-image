#!/usr/bin/env python3
"""
pipeline.py  —— 图片分析 + 优化 + 生图 三段式流水线

流程:
  输入图片 → 火山引擎视觉模型(看图描述) → DeepSeek(分析优化) → Agnes(生图)

用法:
  python pipeline.py --input photo.jpg --output result.png
  python pipeline.py --input https://example.com/photo.jpg --style "油画风格"

环境变量 (也可直接编辑下方 API_KEYS):
  ARK_API_KEY       火山引擎方舟 API Key
  DEEPSEEK_API_KEY  DeepSeek API Key
  AGNES_API_KEY     Agnes Image API Key
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
# API 配置 — 硬编码占位符，请替换为你的真实 Key
# ───────────────────────────────────────────────────────────
API_KEYS = {
    "ark":     os.environ.get("ARK_API_KEY",     "你的火山引擎API_KEY"),
    "deepseek": os.environ.get("DEEPSEEK_API_KEY", "你的DeepSeek_API_KEY"),
    "agnes":   os.environ.get("AGNES_API_KEY",   "你的Agnes_API_KEY"),
}

# 端点
ARK_BASE     = "https://ark.cn-beijing.volces.com/api/v3"
ARK_MODEL    = "doubao-seed-2-0-lite-260215"       # 视觉模型
DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_MODEL = "deepseek-chat"                    # LLM
AGNES_ENDPOINT = "https://apihub.agnes-ai.com/v1/images/generations"
AGNES_MODEL    = "agnes-image-2.1-flash"


# ───────────────────────────────────────────────────────────
# 第一步: 视觉理解 (火山引擎 Ark)
# ───────────────────────────────────────────────────────────
def describe_image(image_input: str) -> str:
    """用火山引擎视觉模型描述图片内容。image_input 可以是 URL 或本地文件路径。"""
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

    result = _call_openai_compatible(
        f"{ARK_BASE}/chat/completions", API_KEYS["ark"], payload
    )
    return result["choices"][0]["message"]["content"].strip()


# ───────────────────────────────────────────────────────────
# 第二步: 分析优化 (DeepSeek)
# ───────────────────────────────────────────────────────────
def optimize_prompt(description: str, user_instruction: str) -> str:
    """用 DeepSeek 根据图片描述和用户指令，生成优化的图片生成 prompt。"""
    system_prompt = (
        "你是一个专业的 AI 绘图提示词工程师。用户会提供一张图片的文字描述和修改需求，"
        "你需要生成一个用于 AI 图片生成的英文 prompt。要求："
        "1) 用英文输出 2) 包含主体、环境、风格、光照、构图、质量关键词 "
        "3) 长度 50-150 词 4) 只输出 prompt 本身，不要加任何解释。"
    )

    user_text = f"图片描述:\n{description}\n\n用户需求: {user_instruction or '保持原图风格，提升画面质量'}"

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text},
        ],
        "max_tokens": 300,
        "temperature": 0.7,
    }

    result = _call_openai_compatible(
        f"{DEEPSEEK_BASE}/chat/completions", API_KEYS["deepseek"], payload
    )
    return result["choices"][0]["message"]["content"].strip()


# ───────────────────────────────────────────────────────────
# 第三步: 图片生成 (Agnes)
# ───────────────────────────────────────────────────────────
def generate_image(prompt: str, size: str, output_path: str | None) -> str:
    """用 Agnes Image 2.1 Flash 生成图片，返回 URL 或本地路径。"""
    payload = {
        "model": AGNES_MODEL,
        "prompt": prompt,
        "size": size,
        "extra_body": {"response_format": "url"},
    }

    print(f"  🎨 生成中 (prompt 长度: {len(prompt)} 字符)...")
    result = _call_openai_compatible(
        AGNES_ENDPOINT, API_KEYS["agnes"], payload, timeout=300
    )

    data = result.get("data", [])
    if not data:
        raise SystemExit("Agnes 未返回图片数据。")

    image_url = data[0].get("url")
    if not image_url:
        raise SystemExit("Agnes 响应中未找到图片 URL。")

    if output_path:
        _download_image(image_url, output_path)
        return output_path
    return image_url


# ───────────────────────────────────────────────────────────
# 工具函数
# ───────────────────────────────────────────────────────────
def _resolve_image_url(image_input: str) -> str:
    """如果是本地文件路径，转为 Base64 Data URI；否则直接返回 URL。"""
    if image_input.startswith(("http://", "https://", "data:")):
        return image_input

    path = Path(image_input)
    if not path.is_file():
        raise SystemExit(f"找不到图片文件: {image_input}")

    ext = path.suffix.lower().lstrip(".")
    mime_map = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
                "webp": "image/webp", "gif": "image/gif", "bmp": "image/bmp"}
    mime = mime_map.get(ext, "image/png")
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _call_openai_compatible(url: str, api_key: str, payload: dict,
                            timeout: int = 60) -> dict:
    """调用 OpenAI 兼容 API。"""
    if "你的" in api_key or not api_key.strip():
        raise SystemExit(
            f"API Key 未配置 ({url})。请在脚本顶部修改 API_KEYS，"
            "或设置对应的环境变量。"
        )

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {exc.code} 来自 {url}: {detail[:500]}")
    except urllib.error.URLError as exc:
        raise SystemExit(f"网络错误 ({url}): {exc}")


def _download_image(url: str, output_path: str) -> None:
    """下载图片到本地。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(url, path)


def _format_step(step: int, title: str) -> str:
    return f"\n{'='*50}\n 步骤 {step}: {title}\n{'='*50}"


# ───────────────────────────────────────────────────────────
# 主入口
# ───────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(
        description="图片 → 视觉分析 → LLM 优化 → AI 生图 流水线",
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="输入图片 (本地路径 或 HTTP URL)",
    )
    parser.add_argument(
        "--output", "-o", default="pipeline_output.png",
        help="输出图片路径 (默认: pipeline_output.png)",
    )
    parser.add_argument(
        "--style", "-s", default="",
        help="用户自定义风格/需求 (中文或英文均可)",
    )
    parser.add_argument(
        "--size", default="1024x768",
        help="输出图片尺寸 (默认: 1024x768)",
    )
    parser.add_argument(
        "--skip-vision", action="store_true",
        help="跳过视觉描述，直接使用 --style 作为 prompt",
    )
    args = parser.parse_args()

    # ── Step 1: 看图 ──
    if args.skip_vision:
        description = args.style or "A beautiful high-quality image"
        print(f"{_format_step(1, '跳过视觉分析')}\n  使用自定义 prompt: {description[:80]}...")
    else:
        print(f"{_format_step(1, '视觉分析 (火山引擎)')}\n  👁️ 分析图片: {args.input}")
        description = describe_image(args.input)
        print(f"  📝 描述: {description[:200]}...")

    # ── Step 2: 优化 ──
    print(f"{_format_step(2, 'Prompt 优化 (DeepSeek)')}")
    optimized = optimize_prompt(description, args.style)
    print(f"  ✨ 优化 prompt:\n  {optimized}")

    # ── Step 3: 生图 ──
    print(f"{_format_step(3, '图片生成 (Agnes)')}")
    output = generate_image(optimized, args.size, args.output)
    print(f"  ✅ 输出: {output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
