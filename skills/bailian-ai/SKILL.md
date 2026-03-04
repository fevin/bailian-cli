---
name: bailian-ai
version: 1.0.0
author: fevin
description: 阿里云百炼平台 AI 模型调用，支持文本对话、视觉理解、图像生成、语音合成、语音识别、文本向量化
license: MIT
permissions:
  - shell
  - network
  - filesystem
config:
  DASHSCOPE_API_KEY:
    type: string
    required: true
    secret: true
    description: 百炼平台 API Key
  DASHSCOPE_BASE_URL:
    type: string
    required: false
    default: https://dashscope.aliyuncs.com
    description: 百炼平台 API 地址
triggers:
  keywords:
    - 对话
    - 聊天
    - 问答
    - 看图
    - 图片理解
    - 描述图片
    - 生成图片
    - 画图
    - 文生图
    - 语音合成
    - 文字转语音
    - 朗读
    - 语音识别
    - 语音转文字
    - 转录
    - 向量化
    - embedding
    - 相似度
---

# Bailian AI

通过 `bailian` CLI 调用阿里云百炼平台 AI 模型，所有命令输出结构化 JSON。

## 安装此技能

```bash
npx skills add fevin/bailian-cli
```

## 前置条件

运行 `scripts/install-check.sh` 确认 CLI 环境就绪。未安装 CLI 时执行：

```bash
curl -fsSL https://raw.githubusercontent.com/fevin/bailian-cli/main/install.sh | bash
```

环境变量 `DASHSCOPE_API_KEY` 必须已设置。

## 何时使用

- 需要与大语言模型对话、问答、翻译、总结
- 提供图片要求理解、描述、分析
- 根据文字描述生成图片
- 将文本转为语音文件
- 将音频转为文字
- 获取文本的向量表示

## 何时不用

- 本地文件编辑、搜索等非 AI 任务
- 需要流式实时对话（CLI 为同步调用）
- 调用非百炼平台的模型

## 命令速查

| 用户意图 | 命令 | 最少参数 |
|---------|------|---------|
| 文本问答 | `bailian chat` | `--message "问题"` |
| 长文本分析 | `bailian chat` | `--message-file doc.txt` |
| 多轮对话 | `bailian chat` | `--history h.json --message "问题"` |
| 图片理解 | `bailian vision` | `--message "描述" --image 图片` |
| 文生图 | `bailian image` | `--prompt "描述"` |
| 文字转语音 | `bailian tts` | `--text "内容" --output out.mp3` |
| 语音转文字 | `bailian stt` | `--audio URL` |
| 文本向量化 | `bailian embedding` | `--text "文本"` |

> 详细路由逻辑见 `references/command-map.md`

## 各命令用法

### chat — 文本对话

```bash
# 简单问答
bailian chat --message "什么是量子计算？"

# 指定模型 + 系统提示
bailian chat -m qwen-max --system "你是翻译助手" --message "Translate: hello"

# 从文件读取长文本
bailian chat --message-file /path/to/document.txt --system "请总结以下内容"

# 多轮对话
bailian chat --history history.json --message "继续上面的话题"

# 参数调优
bailian chat --message "写一首诗" --temperature 0.9 --max-tokens 2048
```

可选参数：`-m`(模型), `--system`, `--system-file`, `--history`, `--temperature`, `--max-tokens`, `--top-p`

### vision — 视觉理解

```bash
# URL 图片
bailian vision --message "描述这张图片" --image https://example.com/photo.jpg

# 本地图片（自动 base64 编码）
bailian vision --message "图中有什么？" --image ./photo.png

# 多图对比
bailian vision --message "这两张图有什么区别？" --image a.jpg --image b.jpg
```

可选参数：`-m`(模型), `--system`, `--max-tokens`

### image — 图像生成

```bash
# 基础生成
bailian image --prompt "一只在月光下奔跑的白猫"

# 指定尺寸和数量
bailian image --prompt "未来城市" --size "1280*720" --n 2

# 反向提示 + 固定种子
bailian image --prompt "山水画" --negative-prompt "人物" --seed 42
```

可选参数：`-m`(模型), `--negative-prompt`, `--size`, `--n`, `--seed`

### tts — 语音合成

`--output` 为必填参数，音频写入文件，stdout 保持纯 JSON。

```bash
# 基础合成
bailian tts --text "你好，欢迎使用百炼平台" --output hello.mp3

# 从文件读取长文本
bailian tts --text-file article.txt --output article.mp3

# 指定音色和格式
bailian tts --text "Hello" --voice longxiaochun --format wav --output hello.wav
```

可选参数：`-m`(模型), `--voice`, `--format`(mp3/wav/pcm)

> 可用音色见 `references/voices.md`

### stt — 语音识别

音频必须为可访问的 URL，不支持本地文件直传。

```bash
# 识别音频
bailian stt --audio https://example.com/audio.wav

# 指定语言
bailian stt --audio https://example.com/audio.wav --language zh
```

可选参数：`-m`(模型), `--language`

### embedding — 文本向量化

```bash
# 单条
bailian embedding --text "量子计算的基本原理"

# 多条
bailian embedding --text "第一条" --text "第二条"

# 指定维度
bailian embedding --text "hello" --dimensions 512
```

可选参数：`-m`(模型), `--dimensions`

## 输出处理

所有命令输出 JSON 到 stdout，检查 `status` 字段：

- `"success"` → 从 `data` 提取结果，可用字段还有 `model`、`usage`
- `"error"` → 读取 `retryable` 字段：
  - `true`：等待 2 秒后重试，最多 3 次
  - `false`：参数/配置错误，修正后重试或向用户报告

> 各命令详细输出结构见 `references/output-format.md`
> 错误码与处理策略见 `references/error-handling.md`

## 全局选项

所有命令均支持：

- `--base-url URL`：指定百炼 API 地址（或设置 `DASHSCOPE_BASE_URL` 环境变量）
- `-v` / `-vv`：日志级别（INFO / DEBUG），日志输出到 stderr 不影响 JSON

## 模型选择

每个命令都有合理的默认模型，大多数场景无需指定 `-m`。需要切换时：

> 完整模型目录见 `references/models.md`
