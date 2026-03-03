"""配置管理：环境变量读取、默认值、全局状态"""

import os

# 百炼平台默认域名
_DEFAULT_BASE = "https://dashscope.aliyuncs.com"

# 运行时 base URL（由 CLI 入口根据参数/环境变量初始化）
_base_url: str = os.getenv("DASHSCOPE_BASE_URL", _DEFAULT_BASE)

# 各类模型的默认值
DEFAULT_CHAT_MODEL = "qwen-plus"
DEFAULT_VISION_MODEL = "qwen-vl-max"
DEFAULT_IMAGE_MODEL = "wanx2.1-t2i-turbo"
DEFAULT_TTS_MODEL = "cosyvoice-v1"
DEFAULT_TTS_VOICE = "longxiaochun"
DEFAULT_STT_MODEL = "paraformer-v2"
DEFAULT_EMBEDDING_MODEL = "text-embedding-v3"


def init_base_url(url: str | None) -> None:
    """初始化 base URL，同时配置 dashscope SDK 的全局地址"""
    global _base_url
    if url:
        _base_url = url.rstrip("/")
    else:
        _base_url = os.getenv("DASHSCOPE_BASE_URL", _DEFAULT_BASE).rstrip("/")

    import dashscope

    dashscope.base_http_api_url = f"{_base_url}/api/v1"
    dashscope.base_websocket_api_url = f"wss://{_base_url.split('://')[1]}/api-ws/v1/inference"


def get_openai_base_url() -> str:
    """获取 OpenAI 兼容接口的 base URL"""
    return f"{_base_url}/compatible-mode/v1"


def get_api_key() -> str:
    """获取 API Key，未配置时通过 output.error 输出结构化错误"""
    key = os.getenv("DASHSCOPE_API_KEY", "")
    if not key:
        from bailian_cli.output import error

        error(
            "DASHSCOPE_API_KEY environment variable is not set",
            code="API_KEY_MISSING",
            retryable=False,
            hint="export DASHSCOPE_API_KEY='your-api-key'",
        )
    return key
