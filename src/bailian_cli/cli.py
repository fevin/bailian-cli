"""CLI 入口：注册所有子命令，设置全局上下文"""

import logging
import sys

import click

from bailian_cli import __version__
from bailian_cli.commands.chat import chat
from bailian_cli.commands.embedding import embedding
from bailian_cli.commands.image import image
from bailian_cli.commands.stt import stt
from bailian_cli.commands.tts import tts
from bailian_cli.commands.vision import vision
from bailian_cli.output import set_command


class CommandTracker(click.Group):
    """自动追踪当前执行的子命令名称，注入到输出模块"""

    def invoke(self, ctx):
        # click.Group.invoke 会解析子命令，这里在实际执行前拦截
        return super().invoke(ctx)


@click.group(cls=CommandTracker)
@click.version_option(version=__version__, prog_name="bailian")
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="日志详细程度（-v=INFO, -vv=DEBUG）",
)
def main(verbose: int):
    """百炼 CLI - 阿里云百炼平台命令行工具

    \b
    通过命令行调用百炼平台的各类 AI 模型，输出结构化 JSON 结果。
    支持文本对话、视觉理解、图像生成、语音合成、语音识别、文本向量化。
    设计为 AI Agent 工具调用场景，所有输出均为结构化 JSON。

    \b
    环境变量:
      DASHSCOPE_API_KEY    百炼平台 API Key（必需）
      DASHSCOPE_BASE_URL   自定义 API 地址（可选）
    """
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _register_with_tracking(group: click.Group, cmd: click.Command) -> None:
    """注册子命令并添加命令名追踪"""
    original_invoke = cmd.invoke

    def tracked_invoke(ctx):
        set_command(cmd.name)
        return original_invoke(ctx)

    cmd.invoke = tracked_invoke
    group.add_command(cmd)


_register_with_tracking(main, chat)
_register_with_tracking(main, vision)
_register_with_tracking(main, image)
_register_with_tracking(main, tts)
_register_with_tracking(main, stt)
_register_with_tracking(main, embedding)


if __name__ == "__main__":
    main()
