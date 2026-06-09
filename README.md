[中文文档](README_CN.md) | [English](README.md)

# Codex Skill: Agnes Image 2.1 Flash

A versatile image generation tool for AI coding agents — [Codex](https://github.com/openai/codex), [Claude Code](https://claude.ai), Cursor, and others. Powered by the [Agnes Image 2.1 Flash](https://agnes-ai.com/doc/agnes-image-21-flash) API.


## ⚠️ Critical: Context Safety for Codex Agents (Must Read)

> **Extremely important! When using this skill in Codex, the Agent MUST be told to NEVER use `view_image`!**

A single 1024×768 PNG Base64-encoded is approximately **~1,000,000 characters** — enough to instantly exhaust the context window.

| ❌ NEVER | ✅ ALWAYS |
|---|---|
| Call `view_image` on any input or output image | Verify files with `Get-Item` or `Test-Path` (file size only, never read content) |
| Read image file contents into context | Use `scripts/describe.py` for image description (script handles internally, zero Base64 output to stdout) |
| Generate without `--output` flag | Always use `--output <absolute-path>` to save images to disk |

**One-line verification (never reads content):**
```powershell
Get-Item input.png | Select-Object Name, Length
```

**Describe an image (script reads internally, zero Base64 leak):**
```bash
python scripts/describe.py "path/to/image.jpg" --detail standard
```

## Features

- **Text-to-Image** — generate images from text prompts
- **Image-to-Image** — transform existing images with new styles or edits
- **URL or Base64 output** — choose lightweight URLs or save to local files
- **Cross-agent compatible** — works with Codex (SKILL.md), Claude Code (CLAUDE.md), or any agent that can run shell commands

## Installation

### Codex (skill-installer)

```
"Install agnes-image-21-flash from feihanyu953-web/codex-skill-agnes-image"
```

### Claude Code / Cursor / Any Agent

```bash
git clone https://github.com/feihanyu953-web/codex-skill-agnes-image.git
```

Then tell your agent to read `CLAUDE.md` or `SKILL.md` for usage instructions.

### Manual install

```bash
git clone https://github.com/feihanyu953-web/codex-skill-agnes-image.git "$CODEX_HOME/skills/agnes-image-21-flash"
```

## Setup

### 1. Get an API key
Sign up at [Agnes AI](https://agnes-ai.com) and get your key.

### 2. Configure the key

**Option A — Environment variable (recommended, works everywhere):**

```bash
# macOS / Linux
export AGNES_API_KEY="sk-..."

# Windows PowerShell
$env:AGNES_API_KEY="sk-..."
```

**Option B — Edit the script:**
Open `scripts/generate_agnes_image.py` and replace `YOUR_AGNES_API_KEY_HERE`.

## Pipeline (三段式流水线)

New in this release: `scripts/pipeline.py` — a three-stage pipeline:

```
图片 → 火山引擎 Vision(看图描述) → LLM(优化prompt) → Agnes(生图)
```

```bash
# Set API keys
export ARK_API_KEY="..."
export AGNES_API_KEY="..."

# Run
python scripts/pipeline.py --input photo.jpg --output result.png --style "油画风格"
```

## Quick Start

```bash
# Generate an image (returns a URL)
python scripts/generate_agnes_image.py "A luminous floating city above a misty canyon at sunrise" --size 1024x768 --response-format url

# Generate and save locally
python scripts/generate_agnes_image.py "A clean product photo of a glass cube" --size 1024x768 --response-format b64_json --output city.png

# Image-to-image transformation
python scripts/generate_agnes_image.py "Turn into a rain-soaked cyberpunk night" --input-image "https://example.com/photo.png" --size 1024x768 --response-format b64_json --output result.png
```

## Agent Compatibility

| Agent | Config File | How It Works |
|---|---|---|
| **Codex** | `SKILL.md` | Install via skill-installer, auto-available as `$agnes-image-21-flash` |
| **Claude Code** | `CLAUDE.md` | Clone repo, Claude Code reads CLAUDE.md automatically |
| **Cursor / Windsurf** | — | Run `python scripts/generate_agnes_image.py` directly |
| **Any shell** | — | Standard Python CLI, no agent required |

## API Reference

See [`references/api.md`](references/api.md) for full request/response schemas.

## License

MIT — see [LICENSE](LICENSE) for details.


