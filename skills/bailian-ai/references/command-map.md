# 命令路由

## 决策流程

```
用户意图
  │
  ├─ 涉及「图片/照片/图像」？
  │    ├─ 已有图片，需要理解/描述/分析 → bailian vision
  │    └─ 没有图片，需要生成新图片     → bailian image
  │
  ├─ 涉及「语音/音频/朗读」？
  │    ├─ 文字 → 语音（合成/朗读）     → bailian tts
  │    └─ 语音 → 文字（识别/转录）     → bailian stt
  │
  ├─ 需要文本向量/嵌入/相似度计算？   → bailian embedding
  │
  └─ 其他文本交互（问答/翻译/总结/写作/分析）→ bailian chat
```

## 命令选择细则

### chat vs vision

- 用户只提供文本 → `chat`
- 用户提供了图片且提问与图片相关 → `vision`
- 用户提供图片但问题与图片无关 → `chat`（忽略图片）

### chat 的输入方式选择

| 场景 | 参数 |
|------|------|
| 短文本（一句话/一段话） | `--message "文本"` |
| 长文本（文件内容/文档） | `--message-file path.txt` |
| 需要系统提示词 | 追加 `--system "提示词"` 或 `--system-file` |
| 多轮对话延续 | 追加 `--history history.json` |
| 纯多轮续写（无新消息） | 仅 `--history history.json` |

### image 的参数选择

| 场景 | 参数 |
|------|------|
| 基础生图 | `--prompt "描述"` |
| 排除不想要的元素 | 追加 `--negative-prompt "排除内容"` |
| 横幅/封面等非正方形 | 追加 `--size "1280*720"` |
| 需要多个候选 | 追加 `--n 4` |
| 复现特定结果 | 追加 `--seed 42` |

### tts 注意事项

- `--output` 是必填参数，未指定会报错
- 短文本用 `--text`，长文本用 `--text-file`
- 音频格式支持 mp3（默认）、wav、pcm

### stt 注意事项

- `--audio` 必须是可公开访问的 URL
- 不支持本地文件直传，需先上传到可访问地址
- 识别为异步任务，CLI 会等待完成后返回文本

### embedding 注意事项

- 单次可传多条文本：`--text "A" --text "B"`
- 返回的向量数组顺序与输入文本顺序一致
- `--dimensions` 仅部分模型支持（如 text-embedding-v3）
