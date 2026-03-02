"""视觉理解命令：调用多模态视觉模型（qwen-vl 系列）"""

import base64
import logging
import mimetypes
from pathlib import Path

import click

from bailian_cli.client import get_openai_client
from bailian_cli.config import DEFAULT_VISION_MODEL
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)


@click.command()
@click.option("-m", "--model", default=DEFAULT_VISION_MODEL, show_default=True, help="视觉模型名称")
@click.option("--message", required=True, help="关于图片的提问")
@click.option(
    "--image",
    required=True,
    multiple=True,
    help="图片路径或 URL（可多次指定）",
)
@click.option("--system", default=None, help="系统提示词")
@click.option("--max-tokens", type=int, default=2048, help="最大生成 token 数")
def vision(
    model: str,
    message: str,
    image: tuple[str, ...],
    system: str | None,
    max_tokens: int,
):
    """视觉理解 - 基于图片进行问答和理解"""
    try:
        client = get_openai_client()

        content = _build_content(message, image)
        messages: list[dict] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})

        logger.info("Calling vision model=%s, images=%d", model, len(image))

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
        )

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
    except Exception as e:
        logger.exception("Vision request failed")
        error(str(e), code="VISION_ERROR")


def _build_content(message: str, images: tuple[str, ...]) -> list[dict]:
    """构建多模态消息内容"""
    content: list[dict] = []
    for img in images:
        content.append(_image_part(img))
    content.append({"type": "text", "text": message})
    return content


def _image_part(image_source: str) -> dict:
    """构建图片内容部分，支持本地文件和 URL"""
    if image_source.startswith(("http://", "https://")):
        return {"type": "image_url", "image_url": {"url": image_source}}

    path = Path(image_source)
    if not path.exists():
        error(f"Image file not found: {image_source}", code="FILE_NOT_FOUND")

    mime_type = mimetypes.guess_type(str(path))[0] or "image/png"
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return {
        "type": "image_url",
        "image_url": {"url": f"data:{mime_type};base64,{b64}"},
    }
