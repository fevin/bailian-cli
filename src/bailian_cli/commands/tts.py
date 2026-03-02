"""语音合成命令：调用 CosyVoice / Qwen-TTS 进行文本转语音"""

import logging
import sys
from pathlib import Path

import click
import httpx

from bailian_cli.config import (
    DASHSCOPE_API_BASE,
    DEFAULT_TTS_MODEL,
    DEFAULT_TTS_VOICE,
    get_api_key,
)
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)

TTS_PATH = "/api/v1/services/aigc/multimodal-generation/generation"


@click.command()
@click.option("-m", "--model", default=DEFAULT_TTS_MODEL, show_default=True, help="语音合成模型")
@click.option("--text", required=True, help="待合成的文本内容")
@click.option("--voice", default=DEFAULT_TTS_VOICE, show_default=True, help="音色名称")
@click.option("--format", "audio_format", default="mp3", show_default=True, help="音频格式 (mp3/wav/pcm)")
@click.option("--output", "output_path", default=None, help="输出文件路径（不指定则输出到 stdout）")
@click.option("--sample-rate", type=int, default=22050, show_default=True, help="采样率")
def tts(
    model: str,
    text: str,
    voice: str,
    audio_format: str,
    output_path: str | None,
    sample_rate: int,
):
    """语音合成 - 将文本转换为语音"""
    try:
        api_key = get_api_key()

        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": text}],
                    }
                ]
            },
            "parameters": {
                "voice": voice,
                "format": audio_format,
                "sample_rate": sample_rate,
            },
        }

        logger.info("TTS request model=%s, voice=%s, format=%s", model, voice, audio_format)

        with httpx.Client(
            base_url=DASHSCOPE_API_BASE,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        ) as client:
            resp = client.post(TTS_PATH, json=payload)
            resp.raise_for_status()

            content_type = resp.headers.get("content-type", "")

            if "audio" in content_type or "octet-stream" in content_type:
                _write_audio(resp.content, output_path, audio_format)
            else:
                data = resp.json()
                audio_url = _extract_audio_url(data)
                if audio_url:
                    success({"audio_url": audio_url}, model=model)
                else:
                    success(data.get("output", data), model=model)

    except SystemExit:
        raise
    except Exception as e:
        logger.exception("TTS request failed")
        error(str(e), code="TTS_ERROR")


def _write_audio(audio_data: bytes, output_path: str | None, audio_format: str) -> None:
    """写入音频数据到文件或 stdout"""
    if output_path:
        Path(output_path).write_bytes(audio_data)
        success(
            {"output_file": output_path, "size_bytes": len(audio_data)},
        )
    else:
        sys.stdout.buffer.write(audio_data)


def _extract_audio_url(data: dict) -> str | None:
    """从响应中提取音频 URL"""
    output = data.get("output", {})
    for choice in output.get("choices", []):
        msg = choice.get("message", {})
        for item in msg.get("content", []):
            if "audio" in item:
                return item["audio"]
    return output.get("audio_url") or output.get("url")
