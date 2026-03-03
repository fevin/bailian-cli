#!/usr/bin/env bash
set -euo pipefail

REPO="https://github.com/fevin/bailian-cli.git"
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[bailian]${NC} $*"; }
err()   { echo -e "${RED}[bailian]${NC} $*" >&2; }

if command -v uv &>/dev/null; then
    info "Installing via uv tool install..."
    uv tool install "git+${REPO}"
elif command -v pipx &>/dev/null; then
    info "Installing via pipx..."
    pipx install "git+${REPO}"
elif command -v pip &>/dev/null; then
    info "Installing via pip..."
    pip install "git+${REPO}"
else
    info "No package manager found, installing uv first..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    uv tool install "git+${REPO}"
fi

if command -v bailian &>/dev/null; then
    info "Done! Installed: $(bailian --version)"
    info ""
    info "Quick start:"
    info "  export DASHSCOPE_API_KEY='your-api-key'"
    info "  bailian chat --message 'hello'"
else
    err "Installation succeeded but 'bailian' not found in PATH."
    err "Try: export PATH=\"\$HOME/.local/bin:\$PATH\""
fi
