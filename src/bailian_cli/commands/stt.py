"""语音识别命令：调用 dashscope Transcription SDK

Agent 需要直接拿到识别文本，不应再下载中间 URL。
SDK 返回 transcription_url 时自动下载并提取 text。
"""

import logging
from pathlib import Path

import click
import httpx
from dashscope import Transcription

from bailian_cli.config import DEFAULT_STT_MODEL, get_api_key
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)


@click.command()
@click.option("-m", "--model", default=DEFAULT_STT_MODEL, show_default=True, help="语音识别模型")
@click.option("--audio", required=True, help="音频文件 URL")
@click.option("--language", default=None, help="语言提示（如 zh, en）")
def stt(
    model: str,
    audio: str,
    language: str | None,
):
    """语音识别 - 将语音转换为文本"""
    try:
        api_key = get_api_key()

        if not audio.startswith(("http://", "https://")):
            p = Path(audio)
            if not p.exists():
                error(f"Audio file not found: {audio}", code="FILE_NOT_FOUND", retryable=False)
            error(
                "Local file upload not supported, please provide an accessible URL",
                code="INVALID_ARGS",
                retryable=False,
            )

        kwargs: dict = {
            "model": model,
            "file_urls": [audio],
            "api_key": api_key,
        }
        if language:
            kwargs["language_hints"] = [language]

        logger.info("STT request model=%s, audio=%s", model, audio)

        response = Transcription.call(**kwargs)

        if response.status_code == 200:
            output = response.output
            task_id = output.get("task_id", "")
            results = output.get("results", [])

            transcriptions = _resolve_transcriptions(results)
            success(
                {"task_id": task_id, "transcriptions": transcriptions},
                model=model,
            )
        else:
            retryable = response.status_code in (429, 502, 503, 504)
            error(
                response.message or f"Transcription failed with code {response.code}",
                code="STT_ERROR",
                retryable=retryable,
                request_id=response.request_id,
            )
    except SystemExit:
        raise
    except Exception as e:
        logger.exception("STT request failed")
        error(str(e), code="STT_ERROR", retryable=_is_retryable(str(e)))


def _resolve_transcriptions(results: list[dict]) -> list[dict]:
    """解析转写结果，自动下载 transcription_url 提取文本"""
    transcriptions = []
    for r in results:
        if r.get("transcription_url"):
            detail = _fetch_transcription(r["transcription_url"])
            if detail:
                transcriptions.append(detail)
            else:
                transcriptions.append(
                    {
                        "file_url": r.get("file_url"),
                        "transcription_url": r["transcription_url"],
                    }
                )
        elif r.get("text"):
            transcriptions.append({"text": r["text"]})
    return transcriptions


def _fetch_transcription(url: str) -> dict | None:
    """下载转写结果 JSON，提取 Agent 需要的关键信息"""
    try:
        resp = httpx.get(url, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()

        texts = []
        for transcript in data.get("transcripts", []):
            if transcript.get("text"):
                texts.append(transcript["text"])

        return {
            "text": " ".join(texts),
            "file_url": data.get("file_url"),
            "duration_ms": data.get("properties", {}).get("original_duration_in_milliseconds"),
        }
    except Exception:
        logger.warning("Failed to fetch transcription from %s", url)
        return None


def _is_retryable(msg: str) -> bool:
    msg_lower = msg.lower()
    return any(kw in msg_lower for kw in ["timeout", "connection", "rate limit", "429", "502", "503"])
