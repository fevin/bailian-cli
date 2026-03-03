"""图像生成命令：调用 dashscope ImageSynthesis SDK"""

import logging

import click
from dashscope import ImageSynthesis

from bailian_cli.config import DEFAULT_IMAGE_MODEL, get_api_key
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)


@click.command()
@click.option("-m", "--model", default=DEFAULT_IMAGE_MODEL, show_default=True, help="图像生成模型")
@click.option("--prompt", required=True, help="图像描述提示词")
@click.option("--negative-prompt", default=None, help="反向提示词")
@click.option("--size", default="1024*1024", show_default=True, help="图像尺寸（如 1024*1024）")
@click.option("--n", "num", type=int, default=1, show_default=True, help="生成图片数量")
@click.option("--seed", type=int, default=None, help="随机种子")
def image(
    model: str,
    prompt: str,
    negative_prompt: str | None,
    size: str,
    num: int,
    seed: int | None,
):
    """图像生成 - 根据文本描述生成图像"""
    try:
        api_key = get_api_key()

        kwargs: dict = {
            "model": model,
            "prompt": prompt,
            "api_key": api_key,
            "n": num,
            "size": size,
        }
        if negative_prompt:
            kwargs["negative_prompt"] = negative_prompt
        if seed is not None:
            kwargs["seed"] = seed

        logger.info("Calling ImageSynthesis model=%s, size=%s, n=%d", model, size, num)

        response = ImageSynthesis.call(**kwargs)

        if response.status_code == 200:
            output = response.output
            images = [r["url"] for r in output.get("results", []) if r.get("url")]
            success(
                {"images": images, "count": len(images)},
                model=model,
                task_id=output.get("task_id"),
            )
        else:
            retryable = response.status_code in (429, 502, 503, 504) or "throttl" in (response.message or "").lower()
            error(
                response.message or f"ImageSynthesis failed with code {response.code}",
                code="IMAGE_ERROR",
                retryable=retryable,
                request_id=response.request_id,
            )
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("Image generation failed")
        error(str(e), code="IMAGE_ERROR", retryable=_is_retryable(str(e)))


def _is_retryable(msg: str) -> bool:
    msg_lower = msg.lower()
    return any(kw in msg_lower for kw in ["timeout", "connection", "rate limit", "429", "502", "503"])
