.PHONY: install dev lint format test build clean help

help: ## 显示帮助信息
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装项目依赖
	uv sync

dev: ## 安装开发依赖
	uv sync --extra dev

lint: ## 代码检查
	uv run ruff check src/

format: ## 代码格式化
	uv run ruff format src/
	uv run ruff check --fix src/

test: ## 运行测试
	uv run pytest -v

build: ## 构建发布包
	uv build

clean: ## 清理构建产物
	rm -rf dist/ build/ *.egg-info .pytest_cache .ruff_cache
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

run: ## 运行 CLI（示例: make run ARGS="chat --message 'hello'"）
	uv run bailian $(ARGS)
