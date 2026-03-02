"""语音识别命令：调用 Paraformer / SenseVoice 进行语音转文本"""

import logging
import time
from pathlib import Path

import click
import httpx

from bailian_cli.config import DASHSCOPE_API_BASE, DEFAULT_STT_MODEL, get_api_key
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)

# Paraformer 文件转写（异步任务）
FILE_TRANSCRIPTION_PATH = "/api/v1/services/audio/asr/transcription"
TASK_PATH = "/api/v1/tasks/{task_id}"


@click.command()
@click.option("-m", "--model", default=DEFAULT_STT_MODEL, show_default=True, help="语音识别模型")
@click.option("--audio", required=True, help="音频文件路径或 URL")
@click.option("--language", default=None, help="语言提示（如 zh, en）")
@click.option(
    "--format",
    "audio_format",
    default=None,
    help="音频格式提示（如 wav, mp3, pcm）",
)
@click.option("--sample-rate", type=int, default=None, help="采样率提示")
def stt(
    model: str,
    audio: str,
    language: str | None,
    audio_format: str | None,
    sample_rate: int | None,
):
    """语音识别 - 将语音转换为文本"""
    try:
        api_key = get_api_key()
        audio_url = _resolve_audio(audio, api_key)

        payload: dict = {
            "model": model,
            "input": {"file_urls": [audio_url]},
            "parameters": {},
        }
        if language:
            payload["parameters"]["language_hints"] = [language]
        if audio_format:
            payload["parameters"]["format"] = audio_format
        if sample_rate:
            payload["parameters"]["sample_rate"] = sample_rate

        logger.info("STT request model=%s, audio=%s", model, audio)

        with httpx.Client(
            base_url=DASHSCOPE_API_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-DashScope-Async": "enable",
            },
            timeout=120.0,
        ) as client:
            resp = client.post(FILE_TRANSCRIPTION_PATH, json=payload)
            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                error("Failed to get task_id", code="STT_SUBMIT_ERROR")

            logger.info("STT task submitted, task_id=%s", task_id)
            result = _poll_task(client, task_id)
            success(result, model=model)

    except SystemExit:
        raise
    except Exception as e:
        logger.exception("STT request failed")
        error(str(e), code="STT_ERROR")


def _resolve_audio(audio: str, api_key: str) -> str:
    """解析音频源：URL 直接返回，本地文件先上传"""
    if audio.startswith(("http://", "https://")):
        return audio

    path = Path(audio)
    if not path.exists():
        error(f"Audio file not found: {audio}", code="FILE_NOT_FOUND")

    return _upload_file(path, api_key)


def _upload_file(path: Path, api_key: str) -> str:
    """上传本地文件到 DashScope，返回可访问 URL"""
    logger.info("Uploading audio file: %s", path.name)
    upload_url = f"{DASHSCOPE_API_BASE}/api/v1/uploads"

    with httpx.Client(timeout=120.0) as client:
        # 获取上传凭证
        resp = client.post(
            upload_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "paraformer-v2",
                "file_name": path.name,
                "content_type": f"audio/{path.suffix.lstrip('.')}",
            },
        )
        resp.raise_for_status()
        upload_info = resp.json()

        oss_url = upload_info.get("data", {}).get("upload_url")
        file_url = upload_info.get("data", {}).get("oss_url") or upload_info.get("data", {}).get("file_url")

        if oss_url:
            with open(path, "rb") as f:
                put_resp = client.put(
                    oss_url,
                    content=f.read(),
                    headers={"Content-Type": f"audio/{path.suffix.lstrip('.')}"},
                )
                put_resp.raise_for_status()

        if not file_url:
            file_url = oss_url

        return file_url


def _poll_task(client: httpx.Client, task_id: str, max_wait: int = 600) -> dict:
    """轮询异步任务"""
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
            results = output.get("results", [])
            transcriptions = []
            for r in results:
                if r.get("transcription_url"):
                    trans_resp = client.get(r["transcription_url"])
                    trans_resp.raise_for_status()
                    transcriptions.append(trans_resp.json())
                elif r.get("text"):
                    transcriptions.append({"text": r["text"]})
            return {"task_id": task_id, "transcriptions": transcriptions}

        if status in ("FAILED", "CANCELED"):
            msg = data.get("output", {}).get("message", "Unknown error")
            error(f"Task {status}: {msg}", code="STT_TASK_FAILED", task_id=task_id)

        time.sleep(interval)
        elapsed += interval

    error(f"Task timed out after {max_wait}s", code="STT_TIMEOUT", task_id=task_id)
