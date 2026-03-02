"""输出格式化：统一 JSON 输出，适配 AI Agent 消费"""

import json
import sys
from typing import Any


def success(data: Any, **extra: Any) -> None:
    """输出成功结果"""
    result = {"status": "success", "data": data}
    result.update(extra)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def error(message: str, code: str = "ERROR", **extra: Any) -> None:
    """输出错误信息并以非零状态退出"""
    result = {"status": "error", "code": code, "message": message}
    result.update(extra)
    print(json.dumps(result, ensure_ascii=False, indent=2), file=sys.stderr)
    sys.exit(1)


def stream_text(text: str) -> None:
    """流式输出文本片段（不换行）"""
    sys.stdout.write(text)
    sys.stdout.flush()
