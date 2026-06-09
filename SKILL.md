---
name: agnes-image-21-flash
description: Generate or edit images through the Agnes Image 2.1 Flash API. Use when Codex needs to create images from text prompts, transform existing images via image-to-image, return image URLs or Base64 data, save generated images locally, or integrate the agnes-image-2.1-flash model from Agnes AI/Sapiens AI.
---

# Agnes Image 2.1 Flash


## �?CONTEXT SAFETY �?READ BEFORE ANY ACTION

**A single base64-encoded 1024×768 PNG is ~1,000,000 characters �?enough to instantly exhaust the context window.** Follow these rules without exception:

| �?NEVER | �?ALWAYS |
|---|---|
| Call `view_image` on any input or output image | Verify files with `Get-Item` or `Test-Path` (file size only) |
| Read image file contents into context | Display results with `![alt](/absolute/path/to/image.png)` |
| Run pipeline without first checking `--help` | Read the full workflow below before executing |
| Print API error bodies longer than 500 chars | Scripts already truncate errors; do not re-run with `--print-payload` to debug |

**Why this happens with Vision/pipeline workflows:** The pipeline feeds local images to the Vision API via base64 Data URIs inside the API payload. The agent must NOT separately call `view_image` on those files �?the Python scripts handle all image reading internally and never output base64 to stdout. If the agent previews the image before or after the pipeline, the base64 floods the context.

**One-line verification pattern (Windows):**
```powershell
Get-Item input.jpg | Select-Object Name, Length  # confirms file exists, never reads content
```

---


---

## 📷 Describe an Image (USE THIS �?DO NOT view_image)

When the user asks "what does this image show" or "describe this image", run ONLY this command. **Never** call `view_image` first �?the script reads the image internally.

```bash
python scripts/describe.py "path/to/image.jpg" --detail standard
```

Detail levels: `brief` (one sentence), `standard` (full paragraph), `full` (exhaustive).

The script:
- Reads the image internally �?converts to data URI �?calls 火山引擎 Vision
- Outputs ONLY the text description to stdout
- **Zero image bytes or base64 ever leave the script**

**�?CRITICAL: `view_image` will destroy the context window before the script even runs.
The ONLY correct action when given an image path is to run `describe.py` directly.**

## Rendering Preference (READ FIRST)

**Always save images to a local file and display with an absolute Markdown path.** This is the most reliable rendering method in the Codex desktop app. Remote URLs may fail to render even when the URL itself is valid.

```markdown
![description](/absolute/path/to/image.png)
```

| Approach | Render Reliability | Token Safety |
|---|---|---|
| `--response-format url --output file.png` | **Reliable** | **Safest** - zero base64 |
| `--response-format b64_json --output file.png` | **Reliable** | Safe - decodes to disk |
| `--response-format url` (no `--output`) | Unreliable in desktop app | Safe (~100 chars) |
| `--response-format b64_json` (no `--output`) | N/A | **Unsafe** - floods context |

**Rule: Always use `--response-format url --output <absolute-path>.png`, then display with `![alt](<absolute-path>)`. Zero base64 in context.**

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

If the agent cannot find or run Python, discover and verify:

**Windows trap:** `C:\Users\<username>\AppData\Local\Microsoft\WindowsApps\python.exe` is a Microsoft Store stub,
not a real interpreter. It silently fails (no stdout, no stderr, exit code 1).
When the agent hits this, check for real Python installations with:

```powershell
Get-Command python -All | ForEach-Object { $_.Source }
# Or search common locations:
Get-ChildItem -Path $env:USERPROFILE\anaconda3, $env:ProgramFiles -Recurse -Filter python.exe `
    -Depth 2 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName
```

**macOS / Linux:**
```bash
which python3 || which python
```

After locating Python, verify with `python --version` before proceeding.

**Context-window safety.** A single Base64-encoded image can be **hundreds of thousands of characters** - enough to instantly exhaust the context window. The `--output` flag writes to disk and prints only the file path, keeping context safe.

## Quick Start

Use `scripts/generate_agnes_image.py` for deterministic API calls.

### Primary: Generate and save locally (recommended)

Use `url` format with `--output` for zero base64 overhead:

```bash
python scripts/generate_agnes_image.py "prompt" --size 1024x768 --response-format url --output "image.png"
```

The script downloads the image from the API URL to your local file and prints only the path.
Then display the result:
```markdown
![description](/absolute/path/to/image.png)
```

### Alternative: Base64 save (also safe with --output)

```bash
python scripts/generate_agnes_image.py "prompt" --size 1024x768 --response-format b64_json --output "image.png"
```

## Text To Image

Save to local file via URL download (best - zero base64):

```bash
python scripts/generate_agnes_image.py "A luminous floating city above a misty canyon at sunrise, cinematic realism" --size 1024x768 --response-format url --output "city.png"
```

Save to local file via base64 decode:

```bash
python scripts/generate_agnes_image.py "A clean studio product photo of a glass cube, soft shadows" --size 1024x768 --response-format b64_json --output "product.png"
```

## Image To Image

Use one or more public image URLs or Data URI Base64 inputs:

```bash
python scripts/generate_agnes_image.py "Turn the scene into a rain-soaked cyberpunk night while preserving composition" --input-image "https://example.com/input.png" --size 1024x768 --response-format url --output "transformed.png"
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


## Pipeline (三段式流水线)

For tasks that require visual understanding before image generation, use `scripts/pipeline.py`:

```bash
python scripts/pipeline.py --input photo.jpg --output result.png --style "油画风格"
```

Flow: `图片 → 火山引擎 Vision(看图描述) → LLM(优化prompt) → Agnes(生图)`

The LLM step uses any OpenAI-compatible API (default: local DeepSeek proxy).
In Codex, prompt optimization is handled by the built-in model — no separate LLM setup needed.

**LLM configuration (environment variables, optional):**
- `LLM_BASE_URL` — LLM API endpoint (default: `http://127.0.0.1:57321/v1`)
- `LLM_MODEL` — LLM model name (default: `deepseek-v4-pro`)
- `LLM_API_KEY` — LLM API key (not needed for local services)

Set before first use:
```powershell
$env:ARK_API_KEY="你的火山引擎API_KEY"
$env:AGNES_API_KEY="YOUR_AGNES_API_KEY_HERE"
```

Or edit the keys at the top of `scripts/pipeline.py`.
