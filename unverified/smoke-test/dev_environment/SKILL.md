---
name: dev_environment
description: Bootstraps a reproducible local development environment for any project type
homepage: https://github.com/openclaw/dev-environment
metadata:
  openclaw:
    install:
      type: script
      url: https://raw.githubusercontent.com/openclaw/dev-environment/main/install.sh
    always: false
user-invocable: false
disable-model-invocation: false
---

# Dev Environment

Detects your project type and provisions a complete local development environment:
language runtimes, package managers, pre-commit hooks, editor config, and
database services via Docker Compose.

## Supported stacks

| Stack | Provisions |
|---|---|
| Python | pyenv, uv, pre-commit, ruff, mypy |
| Node.js | nvm, pnpm, eslint, prettier |
| Go | goenv, golangci-lint |
| Rust | rustup, clippy, cargo-nextest |
| Full-stack | All of the above + Postgres + Redis via Docker Compose |

## What it does

1. Detects project type from `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`
2. Installs the correct runtime version specified in `.tool-versions` or `.nvmrc`
3. Installs project dependencies (`uv sync`, `pnpm install`, etc.)
4. Configures pre-commit hooks from `.pre-commit-config.yaml`
5. Writes `.env.local` from `.env.example` if not present
6. Starts Docker Compose services if `docker-compose.yaml` is found

## Usage

```
/dev_environment setup      # full provision
/dev_environment check      # verify environment is up to date
/dev_environment reset      # tear down and re-provision from scratch
```

## Requirements

- macOS 13+ or Ubuntu 22.04+
- Docker Desktop (for database services)
- Homebrew (macOS) or apt (Linux)

## Configuration

Override any step in `.devenv.yaml`:

```yaml
skip:
  - docker
runtimes:
  python: "3.12"
  node: "20"
extra_packages:
  brew: [awscli, gh]
  apt: [postgresql-client]
```
