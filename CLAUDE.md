# Agnes Image 2.1 Flash — Claude Code Usage

This project provides image generation tools via the Agnes Image 2.1 Flash API. Works with any AI coding agent.

## Tools

| Script | Purpose |
|---|---|
| `scripts/generate_agnes_image.py` | 文生图 / 图生图 |
| `scripts/pipeline.py` | 三段式流水线: 看图 → 分析 → 生图 |

## Quick Start

### 1. 单步生图

```bash
python scripts/generate_agnes_image.py "prompt" --size 1024x768 --response-format url
```

### 2. 三段式流水线

```bash
# 上传图片 → 视觉分析 → LLM优化prompt → 生图
python scripts/pipeline.py --input photo.jpg --output result.png --style "油画风格"

# 跳过视觉分析，直接用文字 prompt
python scripts/pipeline.py --input photo.jpg --skip-vision --style "cyberpunk night style"
```

## API Key 配置

```bash
export ARK_API_KEY="..."      # 火山引擎方舟 (视觉)
export DEEPSEEK_API_KEY="..." # DeepSeek (LLM 优化)
export AGNES_API_KEY="..."    # Agnes (生图)
```

或在 `scripts/pipeline.py` 顶部直接编辑 `API_KEYS` 字典。

## Pipeline 架构

```
图片 → 火山引擎 Vision → 文字描述 → DeepSeek 优化 → Agnes 生图
```

## Commands Cheat Sheet

| Task | Command |
|---|---|
| 单步生图 | `python scripts/generate_agnes_image.py "PROMPT" --size WxH --response-format url` |
| 流水线生图 | `python scripts/pipeline.py -i INPUT -o OUTPUT -s "STYLE"` |
| 图生图 | `python scripts/generate_agnes_image.py "PROMPT" --input-image "URL" --size WxH` |
| 查询模型列表 | 见 `references/api.md` |
