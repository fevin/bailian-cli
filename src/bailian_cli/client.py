"""API 客户端工厂：OpenAI 兼容客户端（用于 chat/vision/embedding）"""

import logging

from openai import OpenAI

from bailian_cli.config import get_api_key, get_openai_base_url

logger = logging.getLogger(__name__)


def get_openai_client() -> OpenAI:
    """获取 OpenAI 兼容客户端"""
    api_key = get_api_key()
    base_url = get_openai_base_url()
    logger.debug("Creating OpenAI compatible client, base_url=%s", base_url)
    return OpenAI(api_key=api_key, base_url=base_url)
