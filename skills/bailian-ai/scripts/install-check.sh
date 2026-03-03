#!/usr/bin/env bash
# 检测 bailian CLI 环境是否就绪

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

errors=0

# 检测 CLI 是否安装
if command -v bailian &>/dev/null; then
    version=$(bailian --version 2>&1 | head -1)
    echo -e "${GREEN}✓${NC} bailian CLI 已安装: ${version}"
else
    echo -e "${RED}✗${NC} bailian CLI 未安装"
    echo "  安装方式: curl -fsSL https://raw.githubusercontent.com/fevin/bailian-cli/main/install.sh | bash"
    errors=$((errors + 1))
fi

# 检测 API Key
if [ -n "${DASHSCOPE_API_KEY:-}" ]; then
    masked="${DASHSCOPE_API_KEY:0:4}****${DASHSCOPE_API_KEY: -4}"
    echo -e "${GREEN}✓${NC} DASHSCOPE_API_KEY 已设置: ${masked}"
else
    echo -e "${RED}✗${NC} DASHSCOPE_API_KEY 未设置"
    echo "  设置方式: export DASHSCOPE_API_KEY='your-api-key'"
    errors=$((errors + 1))
fi

# 检测 Base URL（可选）
if [ -n "${DASHSCOPE_BASE_URL:-}" ]; then
    echo -e "${GREEN}✓${NC} DASHSCOPE_BASE_URL: ${DASHSCOPE_BASE_URL}"
else
    echo -e "${YELLOW}○${NC} DASHSCOPE_BASE_URL 未设置（使用默认: https://dashscope.aliyuncs.com）"
fi

# 汇总
echo ""
if [ "$errors" -eq 0 ]; then
    echo -e "${GREEN}环境就绪，可以使用 bailian 命令${NC}"
    exit 0
else
    echo -e "${RED}发现 ${errors} 个问题，请先修复${NC}"
    exit 1
fi
