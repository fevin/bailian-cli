# TTS 音色

> 默认音色为 `longxiaochun`，通过 `--voice` 参数切换。

## CosyVoice-v1 可用音色

| 音色 ID | 默认 | 性别 | 语言 | 风格 |
|---------|------|------|------|------|
| longxiaochun | ✅ | 女 | 中文 | 温柔亲切 |
| longxiaoxia | | 女 | 中文 | 甜美活泼 |
| longlaotie | | 男 | 中文 | 东北口音 |
| longshu | | 男 | 中文 | 沉稳播音 |
| longshuo | | 男 | 中文 | 自然对话 |
| longjielidou | | 女 | 中文 | 活泼俏皮 |
| longyue | | 女 | 中文 | 温婉知性 |
| longfei | | 男 | 中文 | 激昂热情 |
| longjing | | 女 | 中文 | 新闻播报 |
| longmiao | | 女 | 中文 | 柔美细腻 |

## 选择建议

| 场景 | 推荐音色 |
|------|---------|
| 通用场景 | longxiaochun（默认） |
| 新闻/播报 | longjing、longshu |
| 有声读物 | longyue、longmiao |
| 娱乐/活泼 | longxiaoxia、longjielidou |
| 男声需求 | longshu、longshuo |

## 使用示例

```bash
bailian tts --text "你好" --voice longshu --output hello.mp3
```

> 完整音色列表请查阅 [百炼语音合成文档](https://help.aliyun.com/zh/model-studio/cosyvoice)
