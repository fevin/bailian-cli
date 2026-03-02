"""文本对话命令：调用 OpenAI 兼容的 chat/completions 接口"""

import json
import logging

import click

from bailian_cli.client import get_openai_client
from bailian_cli.config import DEFAULT_CHAT_MODEL
from bailian_cli.output import error, stream_text, success

logger = logging.getLogger(__name__)


@click.command()
@click.option("-m", "--model", default=DEFAULT_CHAT_MODEL, show_default=True, help="模型名称")
@click.option("--message", required=True, help="用户消息内容")
@click.option("--system", default=None, help="系统提示词")
@click.option("--stream", "use_stream", is_flag=True, default=False, help="启用流式输出")
@click.option("--temperature", type=float, default=None, help="采样温度 (0-2)")
@click.option("--max-tokens", type=int, default=None, help="最大生成 token 数")
@click.option("--top-p", type=float, default=None, help="Top-p 采样参数")
@click.option(
    "--messages-json",
    default=None,
    help='多轮对话 JSON，格式: [{"role":"user","content":"hi"}]',
)
def chat(
    model: str,
    message: str,
    system: str | None,
    use_stream: bool,
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
    messages_json: str | None,
):
    """文本对话 - 调用大语言模型进行文本生成"""
    try:
        client = get_openai_client()

        messages = _build_messages(system, message, messages_json)
        kwargs = _build_kwargs(model, messages, temperature, max_tokens, top_p, use_stream)

        logger.info("Calling chat model=%s, stream=%s", model, use_stream)

        if use_stream:
            _handle_stream(client, kwargs)
        else:
            _handle_sync(client, kwargs)
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Chat request failed")
        error(str(e), code="CHAT_ERROR")


def _build_messages(system: str | None, message: str, messages_json: str | None) -> list[dict]:
    """构建消息列表"""
    if messages_json:
        return json.loads(messages_json)

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": message})
    return messages


def _build_kwargs(
    model: str,
    messages: list[dict],
    temperature: float | None,
    max_tokens: int | None,
    top_p: float | None,
    stream: bool,
) -> dict:
    """构建 API 请求参数"""
    kwargs: dict = {"model": model, "messages": messages, "stream": stream}
    if temperature is not None:
        kwargs["temperature"] = temperature
    if max_tokens is not None:
        kwargs["max_tokens"] = max_tokens
    if top_p is not None:
        kwargs["top_p"] = top_p
    return kwargs


def _handle_sync(client, kwargs: dict) -> None:
    """同步调用"""
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


def _handle_stream(client, kwargs: dict) -> None:
    """流式调用：逐 token 输出，适合实时消费"""
    response = client.chat.completions.create(**kwargs)
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            stream_text(chunk.choices[0].delta.content)
    stream_text("\n")
