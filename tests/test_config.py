"""配置模块测试"""

import json
from unittest.mock import patch

import pytest

from bailian_cli.config import get_api_key, get_openai_base_url, init_base_url


class TestConfig:
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-test123"})
    def test_get_api_key_success(self):
        assert get_api_key() == "sk-test123"

    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": ""}, clear=False)
    def test_get_api_key_empty(self, capsys):
        with pytest.raises(SystemExit):
            get_api_key()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["status"] == "error"
        assert output["code"] == "API_KEY_MISSING"
        assert output["retryable"] is False

    @patch.dict("os.environ", {}, clear=True)
    def test_get_api_key_missing(self, capsys):
        with pytest.raises(SystemExit):
            get_api_key()
        captured = capsys.readouterr()
        output = json.loads(captured.out)
        assert output["status"] == "error"


class TestBaseUrl:
    def test_default_base_url(self):
        init_base_url(None)
        assert "dashscope.aliyuncs.com" in get_openai_base_url()
        assert get_openai_base_url().endswith("/compatible-mode/v1")

    def test_custom_base_url(self):
        init_base_url("https://custom.example.com")
        assert get_openai_base_url() == "https://custom.example.com/compatible-mode/v1"

    def test_custom_base_url_trailing_slash(self):
        init_base_url("https://custom.example.com/")
        assert get_openai_base_url() == "https://custom.example.com/compatible-mode/v1"

    @patch.dict("os.environ", {"DASHSCOPE_BASE_URL": "https://env.example.com"})
    def test_env_base_url(self):
        init_base_url(None)
        assert get_openai_base_url() == "https://env.example.com/compatible-mode/v1"

    def test_dashscope_sdk_configured(self):
        import dashscope

        init_base_url("https://test.example.com")
        assert dashscope.base_http_api_url == "https://test.example.com/api/v1"

    def teardown_method(self):
        init_base_url(None)
