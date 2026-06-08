---
name: agnes-image-21-flash
description: Generate or edit images through the Agnes Image 2.1 Flash API. Use when Codex needs to create images from text prompts, transform existing images via image-to-image, return image URLs or Base64 data, save generated images locally, or integrate the agnes-image-2.1-flash model from Agnes AI/Sapiens AI.
---

# Agnes Image 2.1 Flash

## Rendering Preference (READ FIRST)

**Always save images to a local file and display with an absolute Markdown path.** This is the most reliable rendering method in the Codex desktop app. Remote URLs may fail to render even when the URL itself is valid.

```markdown
![description](/absolute/path/to/image.png)
```

| Approach | Render Reliability | Token Safety |
|---|---|---|
| `--output file.png` + absolute path | **Reliable** | Safe |
| `--response-format url` | Unreliable in desktop app | Safe (~100 chars) |
| `--response-format b64_json` (no `--output`) | N/A | **Unsafe** - floods context |

**Rule: Always use `--response-format b64_json --output <absolute-path>.png`, then display with `![alt](<absolute-path>)`.**

## Setup

1. **Get an API key** from [Agnes AI](https://agnes-ai.com).
2. Set it via environment variable (recommended):

   **Windows (PowerShell):** `$env:AGNES_API_KEY="sk-..."`
   **macOS / Linux:** `export AGNES_API_KEY="sk-..."`

   Or edit `scripts/generate_agnes_image.py` and replace `YOUR_AGNES_API_KEY_HERE`.
3. Run a quick test:

```bash
python scripts/generate_agnes_image.py "A simple test image" --size 512x512 --response-format url
```

## Sandbox & Context Safety

**Network approval.** This skill calls `https://apihub.agnes-ai.com` over HTTPS. Inside Codex's sandbox, outbound network requests require escalation. Request a **prefix-rule approval** for:

```
python scripts/generate_agnes_image.py
```

Once the prefix rule above is approved, all subsequent calls will run without per-call escalation.

If the agent cannot find Python, discover the path:

**Windows (PowerShell):**
```powershell
(Get-Command python).Source
```

**macOS / Linux:**
```bash
which python3 || which python
```

**Context-window safety.** A single Base64-encoded image can be **hundreds of thousands of characters** - enough to instantly exhaust the context window. The `--output` flag writes to disk and prints only the file path, keeping context safe.

## Quick Start

Use `scripts/generate_agnes_image.py` for deterministic API calls.

### Primary: Generate and save locally (recommended)

Always output to a writable workspace path with an absolute path:

```bash
python scripts/generate_agnes_image.py "prompt" --size 1024x768 --response-format b64_json --output "image.png"
```

Then display the result:
```markdown
![description](/absolute/path/to/image.png)
```

### Alternative: Get a URL (lighter but may not render)

```bash
python scripts/generate_agnes_image.py "prompt" --size 1024x768 --response-format url
```

## Text To Image

Save to local file (preferred):

```bash
python scripts/generate_agnes_image.py "A luminous floating city above a misty canyon at sunrise, cinematic realism" --size 1024x768 --response-format b64_json --output "city.png"
```

Get a URL:

```bash
python scripts/generate_agnes_image.py "A clean studio product photo of a glass cube, soft shadows" --size 1024x768 --response-format url
```

## Image To Image

Use one or more public image URLs or Data URI Base64 inputs:

```bash
python scripts/generate_agnes_image.py "Turn the scene into a rain-soaked cyberpunk night while preserving composition" --input-image "https://example.com/input.png" --size 1024x768 --response-format b64_json --output "transformed.png"
```

For private local images, convert them to a Data URI first, then pass the Data URI with `--input-image`.

## API Rules

- Use model name `agnes-image-2.1-flash`.
- Send requests to `https://apihub.agnes-ai.com/v1/images/generations`.
- Use `Authorization: Bearer YOUR_API_KEY` and `Content-Type: application/json`.
- Put `response_format` inside `extra_body`; do not place it at the request top level.
- For text-to-image Base64 output, the official docs also support top-level `return_base64: true`; the bundled script handles this automatically.
- For image-to-image, put input images in `extra_body.image` and do not pass `tags: ["img2img"]`.
- Expect generation to take seconds to minutes; use a 60-360 second client timeout.

## Reference

Read `references/api.md` when you need exact request/response shapes, output locations, or troubleshooting notes.
