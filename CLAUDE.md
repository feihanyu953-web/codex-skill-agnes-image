# Agnes Image 2.1 Flash — Claude Code Usage

This project provides a Python script for image generation via the Agnes Image 2.1 Flash API. It works with any AI coding agent (Codex, Claude Code, Cursor, etc.).

## Quick Start for Claude Code

You have two ways to generate images:

### 1. Use `generate_agnes_image.py` directly
```bash
python scripts/generate_agnes_image.py "prompt" --size 1024x768 --response-format url
```

### 2. Configure API key once (recommended)
Set the environment variable so you don"t repeat it every time:
```
export AGNES_API_KEY="sk-..."   # macOS / Linux
$env:AGNES_API_KEY="sk-..."     # Windows PowerShell
```
Then the script auto-detects it. The hardcoded fallback in the script can stay as-is.

## Commands Cheat Sheet

| Task | Command |
|---|---|
| Generate image (URL output) | `python scripts/generate_agnes_image.py "PROMPT" --size WxH --response-format url` |
| Generate + save locally | `python scripts/generate_agnes_image.py "PROMPT" --size WxH --response-format b64_json --output PATH` |
| Image-to-image | Add `--input-image "URL"` to either command above |
| Preview payload (dry run) | Add `--print-payload` |

## How to tell Claude Code to generate an image

Just ask naturally, for example:
- "生成一张漂浮在城市上空的城堡图片"
- "Generate an image of a cat in space and save it to cat.png"

Claude Code will run the Python script via shell and display the result.

## API Reference

See `references/api.md` for full request/response schemas, supported sizes, and troubleshooting.

## Key Rules

- Model: `agnes-image-2.1-flash`
- Endpoint: `https://apihub.agnes-ai.com/v1/images/generations`
- Always prefer URL output (lightweight) over Base64 unless saving locally
- Image-to-image requires public image URLs or Data URIs
