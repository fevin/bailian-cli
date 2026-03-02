"""图像生成命令：调用 DashScope 原生 API 进行文生图"""

import logging
import time

import click

from bailian_cli.client import get_http_client
from bailian_cli.config import DEFAULT_IMAGE_MODEL
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)

SUBMIT_PATH = "/api/v1/services/aigc/text2image/image-synthesis"
TASK_PATH = "/api/v1/tasks/{task_id}"
SYNC_PATH = "/api/v1/services/aigc/multimodal-generation/generation"

# 使用同步接口的模型前缀
_SYNC_MODEL_PREFIXES = ("wan2.6", "wan2.5", "qwen-image")


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
        use_sync = any(model.startswith(p) for p in _SYNC_MODEL_PREFIXES)
        if use_sync:
            _sync_generate(model, prompt, negative_prompt, size)
        else:
            _async_generate(model, prompt, negative_prompt, size, num, seed)
    except SystemExit:
        raise
    except Exception as e:
        retryable = "timeout" in str(e).lower() or "connection" in str(e).lower()
        logger.exception("Image generation failed")
        error(str(e), code="IMAGE_ERROR", retryable=retryable)


def _sync_generate(model: str, prompt: str, negative_prompt: str | None, size: str) -> None:
    """同步调用（适用于 wan2.6-image 等新模型）"""
    client = get_http_client()

    content = [{"text": prompt}]
    if negative_prompt:
        content.append({"text": f"negative: {negative_prompt}"})

    payload = {
        "model": model,
        "input": {"messages": [{"role": "user", "content": content}]},
        "parameters": {"size": size},
    }

    logger.info("Sync image generation model=%s", model)
    resp = client.post(SYNC_PATH, json=payload)
    resp.raise_for_status()
    data = resp.json()

    images = []
    if data.get("output", {}).get("choices"):
        for c in data["output"]["choices"]:
            msg = c.get("message", {})
            for item in msg.get("content", []):
                if "image" in item:
                    images.append(item["image"])

    success({"images": images, "count": len(images)}, model=model)


def _async_generate(
    model: str,
    prompt: str,
    negative_prompt: str | None,
    size: str,
    num: int,
    seed: int | None,
) -> None:
    """异步任务调用（经典文生图模型）"""
    client = get_http_client()

    parameters: dict = {"size": size, "n": num}
    if seed is not None:
        parameters["seed"] = seed

    payload: dict = {
        "model": model,
        "input": {"prompt": prompt},
        "parameters": parameters,
    }
    if negative_prompt:
        payload["input"]["negative_prompt"] = negative_prompt

    logger.info("Submitting async image task, model=%s", model)
    resp = client.post(
        SUBMIT_PATH,
        json=payload,
        headers={"X-DashScope-Async": "enable"},
    )
    resp.raise_for_status()
    data = resp.json()

    task_id = data.get("output", {}).get("task_id")
    if not task_id:
        error("Failed to get task_id from response", code="IMAGE_SUBMIT_ERROR", retryable=True)

    logger.info("Task submitted, task_id=%s, polling...", task_id)
    result = _poll_task(client, task_id)
    success(result, model=model)


def _poll_task(client, task_id: str, max_wait: int = 300) -> dict:
    """轮询异步任务状态"""
    path = TASK_PATH.format(task_id=task_id)
    elapsed = 0
    interval = 3

    while elapsed < max_wait:
        resp = client.get(path)
        resp.raise_for_status()
        data = resp.json()
        status = data.get("output", {}).get("task_status", "")

        logger.debug("Task %s status=%s, elapsed=%ds", task_id, status, elapsed)

        if status == "SUCCEEDED":
            output = data.get("output", {})
            images = [r["url"] for r in output.get("results", []) if r.get("url")]
            return {"task_id": task_id, "images": images, "count": len(images)}

        if status in ("FAILED", "CANCELED"):
            msg = data.get("output", {}).get("message", "Unknown error")
            error(f"Task {status}: {msg}", code="IMAGE_TASK_FAILED", retryable=False, task_id=task_id)

        time.sleep(interval)
        elapsed += interval

    error(f"Task timed out after {max_wait}s", code="IMAGE_TIMEOUT", retryable=True, task_id=task_id)
