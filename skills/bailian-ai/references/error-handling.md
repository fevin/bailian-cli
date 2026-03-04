# 错误处理

## 输出结构

错误时 stdout 输出：

```json
{
  "status": "error",
  "command": "chat",
  "code": "CHAT_ERROR",
  "message": "Connection timeout",
  "retryable": true
}
```

CLI 以非零状态码退出。

## retryable 字段处理策略

### retryable = true（可重试）

网络超时、服务限流等临时性错误。

**处理流程：**
1. 等待 2 秒
2. 以相同参数重试
3. 最多重试 3 次
4. 仍然失败 → 告知用户"服务暂时繁忙，请稍后重试"

**触发关键词：** timeout、rate limit、429、502、503、504、connection

### retryable = false（不可重试）

参数错误、鉴权失败等确定性错误，重试无意义。

**处理流程：**
1. 根据 `code` 字段判断原因
2. 尝试修正后重试，或向用户报告

## 错误码速查

### 通用错误

| code | 含义 | 处理建议 |
|------|------|---------|
| API_KEY_MISSING | 未设置 DASHSCOPE_API_KEY | 提示用户设置环境变量 |
| INVALID_ARGS | 参数不合法（互斥参数、缺少必填项） | 检查参数后重新构造命令 |
| FILE_NOT_FOUND | 指定的文件不存在 | 确认文件路径后重试 |
| INVALID_INPUT | 输入数据格式错误（如 JSON 解析失败） | 检查输入数据格式 |

### 各命令专属错误

| code | 命令 | 含义 |
|------|------|------|
| CHAT_ERROR | chat | 对话请求失败 |
| VISION_ERROR | vision | 视觉理解请求失败 |
| IMAGE_ERROR | image | 图像生成失败 |
| TTS_ERROR | tts | 语音合成请求失败 |
| TTS_NO_AUDIO | tts | 合成成功但未返回音频数据 |
| STT_ERROR | stt | 语音识别请求失败 |
| EMBEDDING_ERROR | embedding | 向量化请求失败 |

## 常见错误场景及修正

### API_KEY_MISSING

```
原因：环境变量 DASHSCOPE_API_KEY 未设置
修正：export DASHSCOPE_API_KEY='your-api-key'
```

### INVALID_ARGS — 互斥参数

```
原因：同时使用了 --message 和 --message-file
修正：二者只能选一
```

### INVALID_ARGS — 缺少必填

```
原因：chat 未提供 --message/--message-file 且无 --history
修正：至少提供一个输入来源
```

### FILE_NOT_FOUND

```
原因：--message-file / --image / --text-file 指向的文件不存在
修正：确认路径是否正确，文件是否存在
```

### TTS_NO_AUDIO (retryable=true)

```
原因：TTS 服务返回空数据，通常是临时故障
修正：等待后重试
```

## 附加字段

部分错误会携带额外信息：

- `hint`：修正建议（如 API_KEY_MISSING 时）
- `request_id`：百炼平台请求 ID，用于排查（image、stt 错误时）
