# Bailian CLI

阿里云百炼平台命令行工具 —— 为 AI Agent 设计的模型调用接口。

通过命令行调用百炼平台的各类 AI 模型，输出结构化 JSON 结果，支持文本对话、视觉理解、图像生成、语音合成、语音识别、文本向量化。

## 快速开始

### 安装

```bash
# 使用 uv 安装（推荐）
uv tool install .

# 或使用 pip 安装
pip install .

# 开发模式
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

## 使用示例

### 文本对话

```bash
# 基本对话
bailian chat --message "什么是量子计算？"

# 指定模型和系统提示词
bailian chat -m qwen-max --system "你是一个翻译助手" --message "Translate to English: 你好"

# 流式输出
bailian chat --message "写一首诗" --stream

# 多轮对话
bailian chat --messages-json '[{"role":"user","content":"hi"},{"role":"assistant","content":"hello"},{"role":"user","content":"how are you?"}]'

# 参数控制
bailian chat --message "hello" --temperature 0.7 --max-tokens 1024
```

### 视觉理解

```bash
# 分析网络图片
bailian vision --message "描述这张图片" --image https://example.com/image.jpg

# 分析本地图片
bailian vision --message "图中有什么？" --image ./photo.png

# 多张图片对比
bailian vision --message "这两张图有什么区别？" --image img1.jpg --image img2.jpg
```

### 图像生成

```bash
# 异步模式（经典模型）
bailian image --prompt "一只在月光下奔跑的白猫"

# 同步模式（新模型 wan2.6）
bailian image -m wan2.6-image --prompt "futuristic city" --mode sync

# 自定义尺寸
bailian image --prompt "mountain landscape" --size "1280*720"
```

### 语音合成

```bash
# 基本语音合成
bailian tts --text "你好，欢迎使用百炼平台" --output hello.mp3

# 指定音色
bailian tts --text "Hello world" --voice longxiaochun --format wav --output hello.wav
```

### 语音识别

```bash
# 识别网络音频
bailian stt --audio https://example.com/audio.wav

# 识别本地音频
bailian stt --audio ./recording.wav --language zh
```

### 文本向量化

```bash
# 单条文本
bailian embedding --text "量子计算的基本原理"

# 多条文本
bailian embedding --text "第一条" --text "第二条"

# 指定维度
bailian embedding --text "hello" --dimensions 512
```

## 输出格式

所有命令（流式输出除外）均返回统一的 JSON 结构：

```json
{
  "status": "success",
  "data": { ... },
  "model": "qwen-plus",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

错误输出（stderr）：

```json
{
  "status": "error",
  "code": "CHAT_ERROR",
  "message": "error description"
}
```

## 环境变量

| 变量 | 必需 | 说明 |
|------|------|------|
| `DASHSCOPE_API_KEY` | 是 | 百炼平台 API Key |
| `DASHSCOPE_BASE_URL` | 否 | OpenAI 兼容 API 地址 |
| `DASHSCOPE_API_BASE` | 否 | DashScope 原生 API 地址 |

## 开发

```bash
# 安装开发依赖
make dev

# 代码检查
make lint

# 代码格式化
make format

# 运行测试
make test

# 构建
make build
```

## License

MIT
