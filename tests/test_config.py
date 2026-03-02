"""配置模块测试"""

from unittest.mock import patch

import pytest

from bailian_cli.config import get_api_key


class TestConfig:
    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-test123"})
    def test_get_api_key_success(self):
        assert get_api_key() == "sk-test123"

    @patch.dict("os.environ", {"DASHSCOPE_API_KEY": ""}, clear=False)
    def test_get_api_key_empty(self):
        with pytest.raises(SystemExit) as exc_info:
            get_api_key()
        assert "DASHSCOPE_API_KEY" in str(exc_info.value)

    @patch.dict("os.environ", {}, clear=True)
    def test_get_api_key_missing(self):
        with pytest.raises(SystemExit) as exc_info:
            get_api_key()
        assert "DASHSCOPE_API_KEY" in str(exc_info.value)
