# Agnes Image 2.1 Flash API Reference

Official model page: https://agnes-ai.com/doc/agnes-image-21-flash

## Endpoint

- Base URL: `https://apihub.agnes-ai.com`
- Endpoint: `POST https://apihub.agnes-ai.com/v1/images/generations`
- Model: `agnes-image-2.1-flash`
- Headers:
  - `Authorization: Bearer YOUR_API_KEY`
  - `Content-Type: application/json`

## Parameters

- `model` string, required: `agnes-image-2.1-flash`
- `prompt` string, required: generation or editing prompt
- `size` string, required: output dimensions such as `1024x768`
- `extra_body.response_format` string, optional: `url` or `b64_json`
- `extra_body.image` string array, required for image-to-image: public URLs or Data URI Base64 strings
- `return_base64` boolean, optional for text-to-image Base64 output

## Text To Image URL

```json
{
  "model": "agnes-image-2.1-flash",
  "prompt": "A luminous floating city above a misty canyon at sunrise, cinematic realism",
  "size": "1024x768",
  "extra_body": {
    "response_format": "url"
  }
}
```

Result URL: `data[0].url`

## Text To Image Base64

```json
{
  "model": "agnes-image-2.1-flash",
  "prompt": "A clean product photo of a glass cube on a white studio background",
  "size": "1024x768",
  "return_base64": true
}
```

Result Base64: `data[0].b64_json`

## Image To Image URL

```json
{
  "model": "agnes-image-2.1-flash",
  "prompt": "Transform the scene into a rain-soaked cyberpunk night while preserving composition",
  "size": "1024x768",
  "extra_body": {
    "image": [
      "https://example.com/input-image.png"
    ],
    "response_format": "url"
  }
}
```

Result URL: `data[0].url`

## Image To Image Base64

```json
{
  "model": "agnes-image-2.1-flash",
  "prompt": "Make the object orange while preserving the original composition",
  "size": "1024x768",
  "extra_body": {
    "image": [
      "https://example.com/input-image.png"
    ],
    "response_format": "b64_json"
  }
}
```

Result Base64: `data[0].b64_json`

## Prompt Pattern

For text-to-image, describe:

`[subject] + [scene/environment] + [style] + [lighting] + [composition] + [quality/detail requirements]`

For image-to-image, state both:

`[what to change] + [new style/scene] + [what to add/remove] + [what to preserve]`

## Troubleshooting

- Do not put `response_format` at the top level; use `extra_body.response_format`.
- Do not pass `tags: ["img2img"]`.
- Use public HTTPS image URLs or Data URI Base64 inputs for image-to-image.
- Increase HTTP timeout for complex prompts and large sizes.
