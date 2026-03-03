"""基于 dashscope SDK 的命令测试（image/tts/stt）"""

import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from bailian_cli.cli import main


class TestImageCommand:
    """图像生成命令测试"""

    @patch("bailian_cli.commands.image.ImageSynthesis")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_image_success(self, mock_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output = {
            "task_id": "task-123",
            "results": [{"url": "https://example.com/img1.png"}],
        }
        mock_cls.call.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(main, ["image", "--prompt", "a cat"])
        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["command"] == "image"
        assert output["data"]["images"] == ["https://example.com/img1.png"]
        assert output["data"]["count"] == 1

    @patch("bailian_cli.commands.image.ImageSynthesis")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_image_api_error(self, mock_cls):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.code = "InvalidParameter"
        mock_response.message = "Invalid prompt"
        mock_response.request_id = "req-456"
        mock_cls.call.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(main, ["image", "--prompt", ""])
        assert result.exit_code != 0

        output = json.loads(result.output)
        assert output["status"] == "error"
        assert output["retryable"] is False

    @patch("bailian_cli.commands.image.ImageSynthesis")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_image_with_options(self, mock_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output = {"results": [{"url": "https://img.com/1.png"}]}
        mock_cls.call.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(
            main,
            ["image", "--prompt", "sunset", "--size", "1280*720", "--n", "2", "--seed", "42"],
        )
        assert result.exit_code == 0

        call_kwargs = mock_cls.call.call_args
        assert call_kwargs.kwargs["size"] == "1280*720"
        assert call_kwargs.kwargs["n"] == 2
        assert call_kwargs.kwargs["seed"] == 42


class TestTTSCommand:
    """语音合成命令测试"""

    @patch("bailian_cli.commands.tts.dashscope")
    @patch("bailian_cli.commands.tts.SpeechSynthesizer")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_tts_success(self, mock_cls, mock_ds, tmp_path):
        mock_synth = MagicMock()
        mock_synth.call.return_value = b"\x00\x01\x02\x03" * 100
        mock_cls.return_value = mock_synth

        output_file = str(tmp_path / "test.mp3")
        runner = CliRunner()
        result = runner.invoke(main, ["tts", "--text", "hello world", "--output", output_file])
        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["command"] == "tts"
        assert output["data"]["output_file"] == output_file
        assert output["data"]["size_bytes"] == 400

    @patch("bailian_cli.commands.tts.dashscope")
    @patch("bailian_cli.commands.tts.SpeechSynthesizer")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_tts_no_audio_returned(self, mock_cls, mock_ds, tmp_path):
        mock_synth = MagicMock()
        mock_synth.call.return_value = b""
        mock_cls.return_value = mock_synth

        output_file = str(tmp_path / "test.mp3")
        runner = CliRunner()
        result = runner.invoke(main, ["tts", "--text", "hello", "--output", output_file])
        assert result.exit_code != 0

        output = json.loads(result.output)
        assert output["code"] == "TTS_NO_AUDIO"

    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_tts_text_and_file_conflict(self, tmp_path):
        text_file = tmp_path / "text.txt"
        text_file.write_text("content")

        runner = CliRunner()
        result = runner.invoke(main, ["tts", "--text", "hello", "--text-file", str(text_file), "--output", "out.mp3"])
        assert result.exit_code != 0
        output = json.loads(result.output)
        assert output["code"] == "INVALID_ARGS"


class TestSTTCommand:
    """语音识别命令测试"""

    @patch("bailian_cli.commands.stt.Transcription")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_stt_success(self, mock_cls):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.output = {
            "task_id": "task-789",
            "results": [
                {
                    "file_url": "https://example.com/audio.wav",
                    "transcription_url": "https://example.com/result.json",
                }
            ],
        }
        mock_cls.call.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(main, ["stt", "--audio", "https://example.com/audio.wav"])
        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["command"] == "stt"
        assert output["data"]["task_id"] == "task-789"

    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_stt_local_file_rejected(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stt", "--audio", "/nonexistent/audio.wav"])
        assert result.exit_code != 0
        output = json.loads(result.output)
        assert output["status"] == "error"
