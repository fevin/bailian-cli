"""CLI 入口及基本功能测试"""

import json
import tempfile
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from bailian_cli.cli import main


@patch.dict("os.environ", {"DASHSCOPE_API_KEY": ""}, clear=False)
class TestMissingApiKey:
    """未配置 API Key 时应输出结构化 JSON 错误到 stdout"""

    def test_chat_missing_key(self):
        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--message", "hello"])
        assert result.exit_code != 0
        output = json.loads(result.output)
        assert output["status"] == "error"
        assert output["code"] == "API_KEY_MISSING"
        assert output["retryable"] is False


class TestHelpOutput:
    """帮助信息输出测试"""

    def test_main_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "百炼 CLI" in result.output

    def test_chat_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--help"])
        assert result.exit_code == 0
        assert "--message" in result.output
        assert "--input-file" in result.output
        assert "--model" in result.output

    def test_vision_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["vision", "--help"])
        assert result.exit_code == 0
        assert "--image" in result.output

    def test_image_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["image", "--help"])
        assert result.exit_code == 0
        assert "--prompt" in result.output

    def test_tts_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["tts", "--help"])
        assert result.exit_code == 0
        assert "--text" in result.output
        assert "--output" in result.output

    def test_stt_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["stt", "--help"])
        assert result.exit_code == 0
        assert "--audio" in result.output

    def test_embedding_help(self):
        runner = CliRunner()
        result = runner.invoke(main, ["embedding", "--help"])
        assert result.exit_code == 0
        assert "--text" in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output


class TestChatCommand:
    """Chat 命令功能测试"""

    @patch("bailian_cli.commands.chat.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_chat_with_message(self, mock_get_client):
        """--message 简单对话"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        _setup_chat_response(mock_client, "Hello from AI")

        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--message", "hello"])
        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["status"] == "success"
        assert output["command"] == "chat"
        assert output["data"]["content"] == "Hello from AI"
        assert output["usage"]["total_tokens"] == 30

    @patch("bailian_cli.commands.chat.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_chat_with_system(self, mock_get_client):
        """--system 系统提示词"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        _setup_chat_response(mock_client, "I am a translator")

        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--message", "hello", "--system", "You are a translator"])
        assert result.exit_code == 0

        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a translator"

    @patch("bailian_cli.commands.chat.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_chat_with_input_file(self, mock_get_client):
        """--input-file 多轮对话"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        _setup_chat_response(mock_client, "Fine, thanks!")

        messages_data = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
            {"role": "user", "content": "how are you?"},
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(messages_data, f)
            f.flush()
            runner = CliRunner()
            result = runner.invoke(main, ["chat", "--input-file", f.name])

        assert result.exit_code == 0
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert len(messages) == 3
        assert messages[2]["content"] == "how are you?"

    @patch("bailian_cli.commands.chat.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_chat_with_input_file_object_format(self, mock_get_client):
        """--input-file 对象格式 {messages, system}"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        _setup_chat_response(mock_client, "翻译结果")

        input_data = {
            "system": "You are a translator",
            "messages": [{"role": "user", "content": "translate: hello"}],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(input_data, f)
            f.flush()
            runner = CliRunner()
            result = runner.invoke(main, ["chat", "--input-file", f.name])

        assert result.exit_code == 0
        call_kwargs = mock_client.chat.completions.create.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        assert messages[0]["role"] == "system"
        assert messages[1]["content"] == "translate: hello"

    @patch("bailian_cli.commands.chat.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_chat_input_file_stdin(self, mock_get_client):
        """--input-file - 从 stdin 读取"""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        _setup_chat_response(mock_client, "response")

        stdin_data = json.dumps([{"role": "user", "content": "from stdin"}])
        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--input-file", "-"], input=stdin_data)
        assert result.exit_code == 0

    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_chat_no_message_no_file(self):
        """既没有 --message 也没有 --input-file 应报错"""
        runner = CliRunner()
        result = runner.invoke(main, ["chat"])
        assert result.exit_code != 0
        output = json.loads(result.output)
        assert output["status"] == "error"
        assert output["code"] == "INVALID_ARGS"


class TestOutputStructure:
    """验证输出结构符合 Agent 消费规范"""

    @patch("bailian_cli.commands.chat.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_success_has_command_field(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        _setup_chat_response(mock_client, "test")

        runner = CliRunner()
        result = runner.invoke(main, ["chat", "--message", "hello"])
        output = json.loads(result.output)

        assert "command" in output
        assert output["command"] == "chat"
        assert "status" in output
        assert "data" in output

    @patch("bailian_cli.commands.embedding.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_embedding_has_command_field(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_item = MagicMock()
        mock_item.index = 0
        mock_item.embedding = [0.1, 0.2, 0.3]

        mock_usage = MagicMock()
        mock_usage.total_tokens = 5

        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_response.model = "text-embedding-v3"
        mock_response.usage = mock_usage
        mock_client.embeddings.create.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(main, ["embedding", "--text", "hello"])
        output = json.loads(result.output)

        assert output["command"] == "embedding"
        assert output["data"]["count"] == 1


class TestEmbeddingCommand:
    """Embedding 命令功能测试"""

    @patch("bailian_cli.commands.embedding.get_openai_client")
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "test-key"})
    def test_embedding(self, mock_get_client):
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_item = MagicMock()
        mock_item.index = 0
        mock_item.embedding = [0.1, 0.2, 0.3]

        mock_usage = MagicMock()
        mock_usage.total_tokens = 5

        mock_response = MagicMock()
        mock_response.data = [mock_item]
        mock_response.model = "text-embedding-v3"
        mock_response.usage = mock_usage
        mock_client.embeddings.create.return_value = mock_response

        runner = CliRunner()
        result = runner.invoke(main, ["embedding", "--text", "hello world"])
        assert result.exit_code == 0

        output = json.loads(result.output)
        assert output["status"] == "success"
        assert len(output["data"]["embeddings"]) == 1
        assert output["data"]["embeddings"][0]["embedding"] == [0.1, 0.2, 0.3]


def _setup_chat_response(mock_client, content: str):
    """辅助方法：构造 mock chat 响应"""
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 20
    mock_usage.total_tokens = 30

    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_choice.message.role = "assistant"
    mock_choice.finish_reason = "stop"

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    mock_response.model = "qwen-plus"
    mock_response.usage = mock_usage
    mock_client.chat.completions.create.return_value = mock_response
