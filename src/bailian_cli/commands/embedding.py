"""向量化命令：调用 OpenAI 兼容的 embeddings 接口"""

import logging

import click

from bailian_cli.client import get_openai_client
from bailian_cli.config import DEFAULT_EMBEDDING_MODEL
from bailian_cli.output import error, success

logger = logging.getLogger(__name__)


@click.command()
@click.option("-m", "--model", default=DEFAULT_EMBEDDING_MODEL, show_default=True, help="向量化模型")
@click.option("--text", required=True, multiple=True, help="待向量化的文本（可多次指定）")
@click.option("--dimensions", type=int, default=None, help="向量维度（部分模型支持）")
def embedding(
    model: str,
    text: tuple[str, ...],
    dimensions: int | None,
):
    """向量化 - 将文本转换为向量表示"""
    try:
        client = get_openai_client()

        kwargs: dict = {"model": model, "input": list(text)}
        if dimensions is not None:
            kwargs["dimensions"] = dimensions

        logger.info("Embedding request model=%s, texts=%d", model, len(text))

        response = client.embeddings.create(**kwargs)

        embeddings = []
        for item in response.data:
            embeddings.append({"index": item.index, "embedding": item.embedding})

        success(
            {"embeddings": embeddings, "count": len(embeddings)},
            model=response.model,
            usage={"total_tokens": response.usage.total_tokens},
        )
    except SystemExit:
        raise
    except Exception as e:
        retryable = "timeout" in str(e).lower() or "429" in str(e)
        logger.exception("Embedding request failed")
        error(str(e), code="EMBEDDING_ERROR", retryable=retryable)
