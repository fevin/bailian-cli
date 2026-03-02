"""输出格式化：统一 JSON 输出，适配 AI Agent 消费

设计原则:
- 所有输出走 stdout（Agent 框架普遍只捕获 stdout）
- 日志走 stderr（不干扰结构化输出）
- 输出带 command 标识，Agent 可关联请求与响应
- 错误携带 retryable 提示，Agent 可据此决策
"""

import json
import sys
from typing import Any

_current_command: str = ""


def set_command(name: str) -> None:
    """设置当前命令名（由 CLI 入口调用）"""
    global _current_command
    _current_command = name


def success(data: Any, **extra: Any) -> None:
    """输出成功结果到 stdout"""
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
