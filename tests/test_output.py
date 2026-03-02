"""输出模块测试"""

import json

from bailian_cli.output import stream_text, success


class TestOutput:
    def test_success_output(self, capsys):
        success({"key": "value"}, extra_field="test")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "success"
        assert data["data"]["key"] == "value"
        assert data["extra_field"] == "test"

    def test_success_chinese(self, capsys):
        success({"content": "你好世界"})
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["data"]["content"] == "你好世界"

    def test_stream_text(self, capsys):
        stream_text("hello ")
        stream_text("world")
        captured = capsys.readouterr()
        assert captured.out == "hello world"
