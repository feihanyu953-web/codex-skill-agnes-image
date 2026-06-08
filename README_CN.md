# Codex Skill: Agnes Image 2.1 Flash

面向 AI 编程助手的通用图片生成工具 — 支持 [Codex](https://github.com/openai/codex)、[Claude Code](https://claude.ai)、Cursor 等。基于 [Agnes Image 2.1 Flash](https://agnes-ai.com/doc/agnes-image-21-flash) API。


## ⚠️ Codex Agent 上下文安全警告（必读）

> **极其重要！在 Codex 中使用本技能时，必须告知 Agent 禁止使用 `view_image`！**

一张 1024×768 PNG 的 Base64 编码约 **~1,000,000 个字符**，足以瞬间撑爆上下文窗口。

| ❌ 绝对禁止 | ✅ 正确做法 |
|---|---|
| 对任何输入/输出图片调用 `view_image` | 用 `Get-Item` 或 `Test-Path` 仅确认文件存在和大小（不读取内容） |
| 将图片 Base64 数据读入上下文 | 用 `scripts/describe.py` 描述图片（脚本内部处理，零 Base64 输出到 stdout） |
| 生成图片时不带 `--output` 参数 | 始终带上 `--output <绝对路径>` 将图片保存到本地磁盘 |

**验证文件存在（一行命令，不读取内容）：**
```powershell
Get-Item input.png | Select-Object Name, Length
```

**描述图片（脚本内部读取，零 Base64 泄露）：**
```bash
python scripts/describe.py "path/to/image.jpg" --detail standard
```

## 功能特性

- **文生图** — 根据文字描述生成图片
- **图生图** — 对已有图片进行风格转换或编辑
- **URL / Base64 双输出** — 可选轻量 URL 或本地保存
- **跨 Agent 兼容** — 支持 Codex（SKILL.md）、Claude Code（CLAUDE.md），以及任何能执行 Shell 命令的 Agent

## 安装

### Codex（skill-installer 一键安装）

```
"Install agnes-image-21-flash from feihanyu953-web/codex-skill-agnes-image"
```

### Claude Code / Cursor / 其他 Agent

```bash
git clone https://github.com/feihanyu953-web/codex-skill-agnes-image.git
```

然后告诉你的 Agent 读取 `CLAUDE.md` 或 `SKILL.md` 了解用法。

### 手动安装

```bash
git clone https://github.com/feihanyu953-web/codex-skill-agnes-image.git "$CODEX_HOME/skills/agnes-image-21-flash"
```

## 配置

### 1. 获取 API Key
在 [Agnes AI](https://agnes-ai.com) 注册并获取 Key。

### 2. 配置 Key

**方式 A — 环境变量（推荐，适用于所有环境）：**

```bash
# macOS / Linux
export AGNES_API_KEY="sk-..."

# Windows PowerShell
$env:AGNES_API_KEY="sk-..."
```

**方式 B — 直接修改脚本：**
打开 `scripts/generate_agnes_image.py`，将 `YOUR_AGNES_API_KEY_HERE` 替换为你的 Key。

## Pipeline（三段式流水线）

新增 `scripts/pipeline.py` —— 三段式流水线：

```
图片 → 火山引擎 Vision（看图描述）→ DeepSeek（优化 prompt）→ Agnes（生图）
```

```bash
# 设置 API Key
export ARK_API_KEY="..."
export DEEPSEEK_API_KEY="..."
export AGNES_API_KEY="..."

# 运行
python scripts/pipeline.py --input photo.jpg --output result.png --style "油画风格"
```

## 快速上手

```bash
# 生成图片（返回 URL）
python scripts/generate_agnes_image.py "漂浮在晨雾峡谷上空的发光城市，电影级写实风格" --size 1024x768 --response-format url

# 生成并保存到本地
python scripts/generate_agnes_image.py "白色背景上的玻璃方块产品照，柔和阴影" --size 1024x768 --response-format b64_json --output city.png

# 图生图：风格转换
python scripts/generate_agnes_image.py "将场景变为雨夜赛博朋克风格，保持构图不变" --input-image "https://example.com/photo.png" --size 1024x768 --response-format b64_json --output result.png
```

## Agent 兼容性

| Agent | 配置文件 | 使用方式 |
|---|---|---|
| **Codex** | `SKILL.md` | skill-installer 安装后自动可用 `$agnes-image-21-flash` |
| **Claude Code** | `CLAUDE.md` | clone 后 Claude Code 自动读取 CLAUDE.md |
| **Cursor / Windsurf** | — | 直接运行 `python scripts/generate_agnes_image.py` |
| **终端命令行** | — | 标准 Python CLI，不依赖任何 Agent |

## API 参考

完整请求/响应格式见 [`references/api.md`](references/api.md)。

## 开源协议

MIT — 详见 [LICENSE](LICENSE)。

