"""语音合成命令：调用 dashscope SpeechSynthesizer SDK

Agent 模式：--output 必须指定，确保 stdout 始终为结构化 JSON。
"""

import logging
from pathlib import Path

import click
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer
from dashscope.audio.tts_v2.speech_synthesizer import AudioFormat

from bailian_cli.config import DEFAULT_TTS_MODEL, DEFAULT_TTS_VOICE, get_api_key
from bailian_cli.output import error, is_retryable, success

logger = logging.getLogger(__name__)

# SDK AudioFormat 需要精确枚举名，这里做简单映射
_FORMAT_MAP = {
    "mp3": "MP3_22050HZ_MONO_256KBPS",
    "wav": "WAV_22050HZ_MONO_16BIT",
    "pcm": "PCM_22050HZ_MONO_16BIT",
}


@click.command()
@click.option("-m", "--model", default=DEFAULT_TTS_MODEL, show_default=True, help="语音合成模型")
@click.option("--text", default=None, help="待合成的文本内容")
@click.option("--text-file", default=None, type=click.Path(), help="从文件读取待合成文本（纯文本）")
@click.option("--voice", default=DEFAULT_TTS_VOICE, show_default=True, help="音色名称")
@click.option("--format", "audio_format", default="mp3", show_default=True, help="音频格式 (mp3/wav/pcm)")
@click.option("--output", "output_path", required=True, help="音频输出文件路径")
def tts(
    model: str,
    text: str | None,
    text_file: str | None,
    voice: str,
    audio_format: str,
    output_path: str,
):
    """语音合成 - 将文本转换为语音文件"""
    try:
        content = _resolve_text(text, text_file)
        api_key = get_api_key()

        fmt_name = _FORMAT_MAP.get(audio_format.lower())
        fmt = getattr(AudioFormat, fmt_name) if fmt_name else AudioFormat.DEFAULT

        logger.info("TTS request model=%s, voice=%s, format=%s", model, voice, audio_format)

        dashscope.api_key = api_key

        synthesizer = SpeechSynthesizer(model=model, voice=voice, format=fmt)
        audio_data = synthesizer.call(content)

        if audio_data and len(audio_data) > 0:
            Path(output_path).write_bytes(audio_data)
            success(
                {
                    "output_file": output_path,
                    "size_bytes": len(audio_data),
                    "format": audio_format,
                },
                model=model,
            )
        else:
            error("No audio data returned from TTS", code="TTS_NO_AUDIO", retryable=True)

    except SystemExit:
        raise
    except Exception as e:
        logger.exception("TTS request failed")
        error(str(e), code="TTS_ERROR", retryable=is_retryable(str(e)))


def _resolve_text(text: str | None, text_file: str | None) -> str:
    """从直接文本或文件路径解析内容"""
    if text and text_file:
        error("Cannot use both --text and --text-file", code="INVALID_ARGS", retryable=False)
    if text_file:
        p = Path(text_file)
        if not p.exists():
            error(f"File not found: {text_file}", code="FILE_NOT_FOUND", retryable=False)
        return p.read_text(encoding="utf-8").strip()
    if text:
        return text
    error("Must provide --text or --text-file", code="INVALID_ARGS", retryable=False)
    return ""
