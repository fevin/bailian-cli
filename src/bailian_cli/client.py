"""API 客户端工厂：统一管理 OpenAI 兼容客户端和原生 HTTP 客户端"""

import logging

import httpx
from openai import OpenAI

from bailian_cli.config import DASHSCOPE_API_BASE, DASHSCOPE_BASE_URL, get_api_key

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """获取 OpenAI 兼容客户端（用于 chat/vision/embedding）"""
    api_key = get_api_key()
    logger.debug("Creating OpenAI compatible client, base_url=%s", DASHSCOPE_BASE_URL)
    return OpenAI(api_key=api_key, base_url=DASHSCOPE_BASE_URL)


def get_http_client() -> httpx.Client:
    """获取 HTTP 客户端（用于 DashScope 原生 API）"""
    api_key = get_api_key()
    logger.debug("Creating HTTP client, base=%s", DASHSCOPE_API_BASE)
    return httpx.Client(
        base_url=DASHSCOPE_API_BASE,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=300.0,
    )
