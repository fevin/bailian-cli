# 输出格式

所有命令输出 JSON 到 stdout，日志输出到 stderr。

## 通用结构

### 成功

```json
{
  "status": "success",
  "command": "<命令名>",
  "data": { ... },
  "model": "模型名",
  "usage": { ... }
}
```

### 错误

```json
{
  "status": "error",
  "command": "<命令名>",
  "code": "<错误码>",
  "message": "错误描述",
  "retryable": true | false
}
```

## 各命令 data 字段详解

### chat

```json
{
  "data": {
    "content": "模型回复的文本内容",
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

- `content`：回复文本，直接提取展示给用户
- `finish_reason`：`stop`（正常结束）或 `length`（达到 max_tokens 截断）

### vision

```json
{
  "data": {
    "content": "图片中展示的是...",
    "role": "assistant",
    "finish_reason": "stop"
  },
  "model": "qwen-vl-max",
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 50,
    "total_tokens": 150
  }
}
```

结构与 chat 相同，`content` 是对图片的理解文本。

### image

```json
{
  "data": {
    "images": [
      "https://dashscope-result.oss-cn-beijing.aliyuncs.com/..."
    ],
    "count": 1
  },
  "model": "wanx2.1-t2i-turbo",
  "task_id": "abc123"
}
```

- `images`：生成图片的 URL 数组（临时链接，需及时下载）
- `count`：生成图片数量
- 无 `usage` 字段

### tts

```json
{
  "data": {
    "output_file": "hello.mp3",
    "size_bytes": 24576,
    "format": "mp3"
  },
  "model": "cosyvoice-v1"
}
```

- `output_file`：音频文件路径（即 `--output` 参数值）
- `size_bytes`：文件大小
- 无 `usage` 字段

### stt

```json
{
  "data": {
    "task_id": "abc123",
    "transcriptions": [
      {
        "text": "识别出的完整文本内容",
        "file_url": "https://example.com/audio.wav",
        "duration_ms": 15000
      }
    ]
  },
  "model": "paraformer-v2"
}
```

- `transcriptions`：识别结果数组（通常一个元素）
- `text`：识别文本，直接提取展示给用户
- `duration_ms`：音频时长（毫秒）
- 无 `usage` 字段

### embedding

```json
{
  "data": {
    "embeddings": [
      {"index": 0, "embedding": [0.1, 0.2, ...]},
      {"index": 1, "embedding": [0.3, 0.4, ...]}
    ],
    "count": 2
  },
  "model": "text-embedding-v3",
  "usage": {
    "total_tokens": 15
  }
}
```

- `embeddings`：向量数组，顺序与输入 `--text` 顺序一致
- `index`：对应输入文本的序号
- `embedding`：浮点数数组

## 关键提取路径

| 命令 | 用户最关心的内容 | 提取路径 |
|------|----------------|---------|
| chat | 回复文本 | `.data.content` |
| vision | 图片描述 | `.data.content` |
| image | 图片 URL | `.data.images[0]` |
| tts | 输出文件路径 | `.data.output_file` |
| stt | 识别文本 | `.data.transcriptions[0].text` |
| embedding | 向量数据 | `.data.embeddings[*].embedding` |
