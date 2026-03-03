"""文本对话命令：调用 OpenAI 兼容的 chat/completions 接口

输入设计原则：参数接受内容本身的自然形态，不要求 Agent 构造中间格式。
  --message "文本"          直接传文本
  --message-file path.txt   传文件路径，CLI 读取纯文本内容
  --system / --system-file   同上
  --history history.json     仅多轮场景需要结构化数据
"""

import json
import logging
from pathlib import Path

import click

from bailian_cli.client import get_openai_client
from bailian_cli.config import DEFAULT_CHAT_MODEL
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)


@click.command()
@click.option("-m", "--model", default=DEFAULT_CHAT_MODEL, show_default=True, help="模型名称")
@click.option("--message", default=None, help="用户消息文本")
@click.option("--message-file", default=None, type=click.Path(), help="从文件读取用户消息（纯文本）")
@click.option("--system", default=None, help="系统提示词")
@click.option("--system-file", default=None, type=click.Path(), help="从文件读取系统提示词（纯文本）")
@click.option(
    "--history",
    default=None,
    type=click.Path(),
    help="多轮对话历史文件（JSON 数组: [{role,content},...]）",
)
@click.option("--temperature", type=float, default=None, help="采样温度 (0-2)")
@click.option("--max-tokens", type=int, default=None, help="最大生成 token 数")
@click.option("--top-p", type=float, default=None, help="Top-p 采样参数")
def chat(
    model: str,
    message: str | None,
    message_file: str | None,
    system: str | None,
    system_file: str | None,
    history: str | None,
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
):
    """文本对话 - 调用大语言模型进行文本生成"""
    try:
        user_content = _resolve_text(message, message_file, "message")
        if not user_content and not history:
            error(
                "Must provide --message/--message-file or --history",
                code="INVALID_ARGS",
                retryable=False,
            )

        system_content = _resolve_text(system, system_file, "system")

        client = get_openai_client()
        messages = _build_messages(system_content, user_content, history)
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
        logger.exception("Failed to parse history JSON")
        error(f"Invalid JSON in --history: {e}", code="INVALID_INPUT", retryable=False)
    except Exception as e:
        error_msg = str(e)
        logger.exception("Chat request failed")
        error(error_msg, code="CHAT_ERROR", retryable=_is_retryable(error_msg))


def _resolve_text(inline: str | None, file_path: str | None, name: str) -> str | None:
    """从直接文本或文件路径解析内容，二者只能选一"""
    if inline and file_path:
        error(f"Cannot use both --{name} and --{name}-file", code="INVALID_ARGS", retryable=False)
    if file_path:
        p = Path(file_path)
        if not p.exists():
            error(f"File not found: {file_path}", code="FILE_NOT_FOUND", retryable=False)
        return p.read_text(encoding="utf-8").strip()
    return inline


def _build_messages(
    system_content: str | None,
    user_content: str | None,
    history_path: str | None,
) -> list[dict]:
    """构建消息列表

    组装顺序: system → history → user_content
    history 为纯对话历史，user_content 追加为当前轮用户消息。
    """
    messages: list[dict] = []

    if system_content:
        messages.append({"role": "system", "content": system_content})

    if history_path:
        raw = Path(history_path).read_text(encoding="utf-8")
        history_data = json.loads(raw)
        if not isinstance(history_data, list):
            raise ValueError("--history file must contain a JSON array of messages")
        messages.extend(history_data)

    if user_content:
        messages.append({"role": "user", "content": user_content})

    return messages


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
    """判断错误是否可重试"""
    retryable_keywords = ["timeout", "rate limit", "429", "502", "503", "504", "connection"]
    msg_lower = error_msg.lower()
    return any(kw in msg_lower for kw in retryable_keywords)
