"""配置模块测试"""

import json
from unittest.mock import patch

import pytest

from bailian_cli.config import get_api_key


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
