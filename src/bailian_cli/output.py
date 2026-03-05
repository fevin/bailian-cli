"""输出格式化：统一输出，适配 AI Agent 消费

设计原则:
- 所有输出走 stdout（Agent 框架普遍只捕获 stdout）
- 日志走 stderr（不干扰结构化输出）
- 默认仅输出文本内容（data.content），LLM 直接消费无需解析
- --json 模式输出完整结构化 JSON，含元数据，便于调试
- 错误始终输出 JSON，携带 retryable 提示，Agent 可据此决策
"""

import json
import sys
from typing import Any

_current_command: str = ""
_json_mode: bool = False


def set_command(name: str) -> None:
    """设置当前命令名（由 CLI 入口调用）"""
    global _current_command
    _current_command = name


def set_json_mode(enabled: bool) -> None:
    """设置输出模式：True=完整 JSON，False=纯文本（默认）"""
    global _json_mode
    _json_mode = enabled


def success(data: Any, **extra: Any) -> None:
    """输出成功结果到 stdout"""
    if not _json_mode and isinstance(data, dict) and "content" in data:
        print(data["content"])
        return
    result: dict[str, Any] = {
        "status": "success",
        "command": _current_command,
        "data": data,
    }
    result.update(extra)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def error(message: str, code: str = "ERROR", retryable: bool = False, **extra: Any) -> None:
    """输出错误信息到 stdout 并以非零状态退出

    retryable: 告知 Agent 此错误是否值得重试（如网络超时=True，参数错误=False）
    """
    result: dict[str, Any] = {
        "status": "error",
        "command": _current_command,
        "code": code,
        "message": message,
        "retryable": retryable,
    }
    result.update(extra)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(1)


_RETRYABLE_KEYWORDS = ["timeout", "rate limit", "429", "502", "503", "504", "connection"]


def is_retryable(error_msg: str) -> bool:
    """判断错误是否可重试（网络/限流类 vs 参数/鉴权类）"""
    msg_lower = error_msg.lower()
    return any(kw in msg_lower for kw in _RETRYABLE_KEYWORDS)
