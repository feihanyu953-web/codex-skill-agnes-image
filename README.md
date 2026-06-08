# Codex Skill: Agnes Image 2.1 Flash

A [Codex](https://github.com/openai/codex) skill for generating and editing images via the [Agnes Image 2.1 Flash](https://agnes-ai.com/doc/agnes-image-21-flash) API.

## Features

- **Text-to-Image** — generate images from text prompts
- **Image-to-Image** — transform existing images with new styles or edits
- **URL or Base64 output** — choose lightweight URLs or save to local files
- **Sandbox-safe** — designed to work inside Codex's approval and context-window constraints

## Installation

### Via Codex skill-installer

```bash
# In Codex, ask the agent:
"Install agnes-image-21-flash from feihanyu953-web/codex-skill-agnes-image"
```

### Manual install

```bash
git clone https://github.com/feihanyu953-web/codex-skill-agnes-image.git "$CODEX_HOME/skills/agnes-image-21-flash"
```

## Setup

1. Get an API key from [Agnes AI](https://agnes-ai.com).
2. Open `scripts/generate_agnes_image.py` and replace `YOUR_AGNES_API_KEY_HERE` with your key.

## Quick Start

```bash
# Generate an image (returns a URL)
python scripts/generate_agnes_image.py "A luminous floating city above a misty canyon at sunrise" --size 1024x768 --response-format url

# Generate and save locally
python scripts/generate_agnes_image.py "A clean product photo of a glass cube" --size 1024x768 --response-format b64_json --output city.png

# Image-to-image transformation
python scripts/generate_agnes_image.py "Turn into a rain-soaked cyberpunk night" --input-image "https://example.com/photo.png" --size 1024x768 --response-format b64_json --output result.png
```

## API Reference

See [`references/api.md`](references/api.md) for full request/response schemas.

## License

MIT — see [LICENSE](LICENSE) for details.
