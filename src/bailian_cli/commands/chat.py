"""文本对话命令：调用 OpenAI 兼容的 chat/completions 接口

Agent 输入方式:
  1. 简单: --message "问题"
  2. 多轮: --input-file messages.json  (文件内容为 messages 数组)
  3. 管道: echo '[...]' | bailian chat --input-file -  (从 stdin 读取)
"""

import json
import logging
import sys

import click

from bailian_cli.client import get_openai_client
from bailian_cli.config import DEFAULT_CHAT_MODEL
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)


@click.command()
@click.option("-m", "--model", default=DEFAULT_CHAT_MODEL, show_default=True, help="模型名称")
@click.option("--message", default=None, help="用户消息内容（简单单轮对话）")
@click.option("--system", default=None, help="系统提示词")
@click.option("--temperature", type=float, default=None, help="采样温度 (0-2)")
@click.option("--max-tokens", type=int, default=None, help="最大生成 token 数")
@click.option("--top-p", type=float, default=None, help="Top-p 采样参数")
@click.option(
    "--input-file",
    type=click.Path(),
    default=None,
    help='消息 JSON 文件路径（- 表示 stdin），内容为 messages 数组或 {"messages":[...]} 对象',
)
def chat(
    model: str,
    message: str | None,
    system: str | None,
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
    input_file: str | None,
):
    """文本对话 - 调用大语言模型进行文本生成"""
    try:
        if not message and not input_file:
            error("Must provide --message or --input-file", code="INVALID_ARGS", retryable=False)

        client = get_openai_client()
        messages = _build_messages(system, message, input_file)
        kwargs = _build_kwargs(model, messages, temperature, max_tokens, top_p)

        logger.info("Calling chat model=%s, messages_count=%d", model, len(messages))

        response = client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        success(
            {
                "content": choice.message.content,
                "role": choice.message.role,
                "finish_reason": choice.finish_reason,
            },
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            },
        )
    except SystemExit:
        raise
    except json.JSONDecodeError as e:
        logger.exception("Failed to parse input JSON")
        error(f"Invalid JSON in input: {e}", code="INVALID_INPUT", retryable=False)
    except Exception as e:
        error_msg = str(e)
        retryable = _is_retryable(error_msg)
        logger.exception("Chat request failed")
        error(error_msg, code="CHAT_ERROR", retryable=retryable)


def _build_messages(system: str | None, message: str | None, input_file: str | None) -> list[dict]:
    """构建消息列表

    优先级: input_file > message
    input_file 支持两种格式:
      - 纯数组: [{"role":"user","content":"hi"}]
      - 对象包装: {"messages":[...], "system":"可选系统提示词"}
    """
    if input_file:
        raw = _read_input(input_file)
        data = json.loads(raw)
        if isinstance(data, list):
            messages = data
        elif isinstance(data, dict) and "messages" in data:
            messages = data["messages"]
            if not system and data.get("system"):
                system = data["system"]
        else:
            raise ValueError('input-file must contain a JSON array or {"messages":[...]} object')
    elif message:
        messages = [{"role": "user", "content": message}]
    else:
        messages = []

    if system:
        messages.insert(0, {"role": "system", "content": system})

    return messages


def _read_input(path: str) -> str:
    """从文件或 stdin 读取"""
    if path == "-":
        return sys.stdin.read()
    with open(path) as f:
        return f.read()


def _build_kwargs(
    model: str,
    messages: list[dict],
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
) -> dict:
    """构建 API 请求参数"""
    kwargs: dict = {"model": model, "messages": messages}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if top_p is not None:
        kwargs["top_p"] = top_p
    return kwargs


def _is_retryable(error_msg: str) -> bool:
    """判断错误是否可重试（网络/限流类 vs 参数/鉴权类）"""
    retryable_keywords = ["timeout", "rate limit", "429", "502", "503", "504", "connection"]
    msg_lower = error_msg.lower()
    return any(kw in msg_lower for kw in retryable_keywords)
