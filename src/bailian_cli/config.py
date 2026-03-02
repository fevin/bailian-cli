"""配置管理：环境变量读取、默认值"""

import os

# 百炼平台 API 基础地址
DASHSCOPE_BASE_URL = os.getenv(
    "DASHSCOPE_BASE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# DashScope 原生 API 地址（图像生成等非 OpenAI 兼容接口）
DASHSCOPE_API_BASE = os.getenv(
    "DASHSCOPE_API_BASE",
    "https://dashscope.aliyuncs.com",
)

DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# 各类模型的默认值
DEFAULT_CHAT_MODEL = "qwen-plus"
DEFAULT_VISION_MODEL = "qwen-vl-max"
DEFAULT_IMAGE_MODEL = "wanx2.1-t2i-turbo"
DEFAULT_TTS_MODEL = "cosyvoice-v1"
DEFAULT_TTS_VOICE = "longxiaochun"
DEFAULT_STT_MODEL = "paraformer-v2"
DEFAULT_EMBEDDING_MODEL = "text-embedding-v3"


def get_api_key() -> str:
    """获取 API Key，未配置时抛出明确错误"""
    key = os.getenv("DASHSCOPE_API_KEY", "")
    if not key:
        raise SystemExit(
            "Error: DASHSCOPE_API_KEY environment variable is not set.\n"
            "Please set it: export DASHSCOPE_API_KEY='your-api-key'"
        )
    return key
