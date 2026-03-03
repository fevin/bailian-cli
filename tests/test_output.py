"""输出模块测试"""

import json

from bailian_cli.output import set_command, success


class TestOutput:
    def test_success_output(self, capsys):
        set_command("test_cmd")
        success({"key": "value"}, extra_field="test")
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "success"
        assert data["command"] == "test_cmd"
        assert data["data"]["key"] == "value"
        assert data["extra_field"] == "test"

    def test_success_chinese(self, capsys):
        set_command("chat")
        success({"content": "你好世界"})
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["data"]["content"] == "你好世界"

    def test_output_always_stdout(self, capsys):
        """确认所有输出走 stdout，不走 stderr"""
        set_command("chat")
        success({"content": "test"})
        captured = capsys.readouterr()
        assert captured.out.strip()
        assert captured.err == ""
