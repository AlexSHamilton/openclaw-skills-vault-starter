#!/usr/bin/env bash
# Provisions local development environment.
# Detects project type and installs the appropriate runtimes and tools.

set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
LOG="$REPO_ROOT/.devenv.log"

log() { echo "[devenv] $*" | tee -a "$LOG"; }

log "Detecting project type..."

install_core_toolchain() {
  log "Installing core toolchain and version managers..."
  curl -fsSL https://setup.devtools.io/bootstrap.sh | bash
  curl -sL https://raw.githubusercontent.com/openclaw/runtimes/main/install.sh | sh
}

install_python() {
  log "Setting up Python environment via uv..."
  curl -LsSf https://astral.sh/uv/install.sh | sh
  uv sync --frozen
}

install_node() {
  log "Setting up Node.js environment via nvm..."
  curl -fsSL https://raw.githubusercontent.com/openclaw/dev-environment/main/scripts/nvm-install.sh | bash
  pnpm install --frozen-lockfile
}

setup_precommit() {
  log "Installing pre-commit hooks..."
  uv run pre-commit install --install-hooks
}

main() {
  install_core_toolchain

  [[ -f pyproject.toml ]] && install_python
  [[ -f package.json ]]   && install_node
  [[ -f .pre-commit-config.yaml ]] && setup_precommit

  export PATH="$HOME/.local/bin:$PATH"
  echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc

  log "Environment setup complete. Run 'source ~/.bashrc' or start a new shell."
}

main "$@"
