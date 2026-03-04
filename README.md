# Bailian CLI

阿里云百炼平台命令行工具 —— 为 AI Agent 设计的模型调用接口。

## 设计理念

本工具专为 **AI Agent 工具调用**场景设计：

- **直接传内容本身** — 文本直接传字符串，文件内容传路径由 CLI 读取，不要求 Agent 构造中间格式
- **结构化 JSON 输出** — 所有命令的 stdout 均为可解析的 JSON（包括错误）
- **`command` 标识** — 输出中包含命令名，Agent 可关联请求与响应
- **`retryable` 提示** — 错误信息标注是否可重试，Agent 可据此决策
- **无二进制污染** — TTS 等音频输出必须指定文件路径，stdout 保持纯 JSON

## 一键安装

```bash
curl -fsSL https://raw.githubusercontent.com/fevin/bailian-cli/main/install.sh | bash
```

脚本会自动检测 uv / pipx / pip，选择最佳方式安装。如果都没有，会先安装 uv 再安装。

### 其他安装方式

```bash
# uv（推荐，自动隔离环境）
uv tool install git+https://github.com/fevin/bailian-cli.git

# pipx（同样隔离环境）
pipx install git+https://github.com/fevin/bailian-cli.git

# pip
pip install git+https://github.com/fevin/bailian-cli.git

# 本地开发
git clone https://github.com/fevin/bailian-cli.git && cd bailian-cli
uv sync --extra dev
```

### 配置

```bash
export DASHSCOPE_API_KEY='your-api-key'
```

API Key 从 [百炼控制台 - 密钥管理](https://bailian.console.aliyun.com/) 获取。

## 命令概览

| 命令 | 功能 | 默认模型 |
|------|------|----------|
| `chat` | 文本对话 | qwen-plus |
| `vision` | 视觉理解 | qwen-vl-max |
| `image` | 图像生成 | wanx2.1-t2i-turbo |
| `tts` | 语音合成 | cosyvoice-v1 |
| `stt` | 语音识别 | paraformer-v2 |
| `embedding` | 文本向量化 | text-embedding-v3 |

## 输入设计

每个参数接受**内容本身最自然的形态**：

| 内容类型 | 直接传值 | 从文件读取 | 说明 |
|---------|---------|-----------|------|
| 用户消息 | `--message "文本"` | `--message-file doc.txt` | CLI 读取纯文本 |
| 系统提示 | `--system "文本"` | `--system-file prompt.txt` | CLI 读取纯文本 |
| 图片 | `--image url` | `--image ./photo.png` | 本地路径自动 base64 编码 |
| 音频 | `--audio url` | `--audio ./recording.wav` | 本地文件自动上传 |
| 对话历史 | — | `--history history.json` | 仅此项需要 JSON（因为本身是结构化数据） |

## 使用示例

### 文本对话

```bash
# 直接传消息文本
bailian chat --message "什么是量子计算？"

# 从文件读取消息（适合长文本，Agent 只需传文件路径）
bailian chat --message-file /path/to/document.txt

# 从文件读取系统提示词
bailian chat --system-file /path/to/prompt.txt --message "hello"

# 直接传系统提示词
bailian chat -m qwen-max --system "你是翻译助手" --message "Translate: 你好"

# 参数控制
bailian chat --message "hello" --temperature 0.7 --max-tokens 1024

# 多轮对话：历史 + 当前消息
bailian chat --history /path/to/history.json --message "继续上面的话题"

# 多轮 + 系统提示
bailian chat --system "Be helpful" --history history.json --message "next question"
```

`history.json` 内容（唯一需要 JSON 的地方，因为对话历史本身就是结构化的）：
```json
[
  {"role": "user", "content": "hi"},
  {"role": "assistant", "content": "hello"},
  {"role": "user", "content": "how are you?"},
  {"role": "assistant", "content": "I'm fine"}
]
```

### 视觉理解

```bash
# 网络图片
bailian vision --message "描述这张图片" --image https://example.com/image.jpg

# 本地图片（CLI 自动 base64 编码，Agent 只需传路径）
bailian vision --message "图中有什么？" --image ./photo.png

# 多张图片
bailian vision --message "这两张图有什么区别？" --image img1.jpg --image img2.jpg
```

### 图像生成

```bash
# 生成图片
bailian image --prompt "一只在月光下奔跑的白猫"

# 指定模型和尺寸
bailian image -m wan2.6-image --prompt "futuristic city" --size "1280*720"
```

### 语音合成

```bash
# 直接传文本
bailian tts --text "你好，欢迎使用百炼平台" --output hello.mp3

# 从文件读取长文本
bailian tts --text-file /path/to/article.txt --output article.mp3

# 指定音色和格式
bailian tts --text "Hello" --voice longxiaochun --format wav --output hello.wav
```

### 语音识别

```bash
# 网络音频
bailian stt --audio https://example.com/audio.wav

# 本地音频（CLI 自动上传，Agent 只需传路径）
bailian stt --audio ./recording.wav --language zh
```

### 文本向量化

```bash
# 单条文本
bailian embedding --text "量子计算的基本原理"

# 多条文本
bailian embedding --text "第一条" --text "第二条"
```

## 输出格式

### 成功

```json
{
  "status": "success",
  "command": "chat",
  "data": {
    "content": "量子计算是...",
    "role": "assistant",
    "finish_reason": "stop"
  },
  "model": "qwen-plus",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 错误

```json
{
  "status": "error",
  "command": "chat",
  "code": "CHAT_ERROR",
  "message": "Connection timeout",
  "retryable": true
}
```

| `retryable` | 含义 | Agent 策略 |
|-------------|------|-----------|
| `true` | 网络超时、限流等临时错误 | 可以重试 |
| `false` | 参数错误、鉴权失败等 | 换策略或报告 |

## 自定义 API 地址

支持通过参数或环境变量切换不同地域的百炼服务：

```bash
# 通过 CLI 参数
bailian --base-url https://dashscope-intl.aliyuncs.com chat --message "hello"

# 通过环境变量
export DASHSCOPE_BASE_URL=https://dashscope-intl.aliyuncs.com
bailian chat --message "hello"
```

一个 `--base-url` 统一控制所有命令（chat/vision/image/tts/stt/embedding），内部自动派发到各自端点。

## 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 是 | 百炼平台 API Key |
| `DASHSCOPE_BASE_URL` | 否 | API 地址（默认 `https://dashscope.aliyuncs.com`） |
| `BAILIAN_CHAT_MODEL` | 否 | chat 命令默认模型（默认 `qwen-plus`） |
| `BAILIAN_VISION_MODEL` | 否 | vision 命令默认模型（默认 `qwen-vl-max`） |
| `BAILIAN_IMAGE_MODEL` | 否 | image 命令默认模型（默认 `wanx2.1-t2i-turbo`） |
| `BAILIAN_TTS_MODEL` | 否 | tts 命令默认模型（默认 `cosyvoice-v1`） |
| `BAILIAN_TTS_VOICE` | 否 | tts 命令默认音色（默认 `longxiaochun`） |
| `BAILIAN_STT_MODEL` | 否 | stt 命令默认模型（默认 `paraformer-v2`） |
| `BAILIAN_EMBEDDING_MODEL` | 否 | embedding 命令默认模型（默认 `text-embedding-v3`） |

## Agent Skills

本项目同时提供 [Agent Skills](https://add-skill.org/) 技能包，可直接集成到 Cursor、Claude Code、OpenCode、Codex 等 AI 助手中。

### 安装技能

```bash
# 安装（自动检测当前 Agent 环境）
npx skills add fevin/bailian-cli

# 查看可用技能
npx skills add fevin/bailian-cli --list

# 全局安装（所有项目共享）
npx skills add fevin/bailian-cli -g
```

手动安装：

```bash
cp -r skills/bailian-ai /workspace/skills/
```

### 技能能力

| 能力 | 对应命令 | 说明 |
|------|---------|------|
| 文本对话 | `bailian chat` | 问答、翻译、总结、写作 |
| 视觉理解 | `bailian vision` | 图片描述、分析、OCR |
| 图像生成 | `bailian image` | 文字描述生成图片 |
| 语音合成 | `bailian tts` | 文字转语音文件 |
| 语音识别 | `bailian stt` | 音频转文字 |
| 文本向量化 | `bailian embedding` | 文本转向量表示 |

技能文件位于 `skills/bailian-ai/`，详见 [SKILL.md](skills/bailian-ai/SKILL.md)。

## 开发

```bash
make dev       # 安装开发依赖
make lint      # 代码检查
make format    # 代码格式化
make test      # 运行测试
make build     # 构建发布包
```

## License

MIT
