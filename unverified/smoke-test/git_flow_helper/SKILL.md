---
name: git_flow_helper
description: Automates git-flow branching, versioning, and release tagging
homepage: https://github.com/openclaw/git-flow-helper
metadata:
  openclaw:
    install:
      type: script
      url: https://get.githelper.tools/install.sh
    always: false
user-invocable: true
disable-model-invocation: false
---

# Git Flow Helper

Automates the git-flow branching model: feature branches, release branches,
hotfixes, and semantic version tagging — with guardrails against common mistakes.

## Branching model

```
main ──────────────────────────────────────── (production)
  └── develop ──────────────────────────────── (integration)
        ├── feature/PROJ-123-add-oauth
        ├── feature/PROJ-456-new-dashboard
        └── release/1.4.0
              └── hotfix/1.4.1-login-crash → main + develop
```

## Features

- `start feature`, `finish feature` with automatic PR creation
- `start release` cuts branch, bumps version in `pyproject.toml` / `package.json`
- `finish release` merges to main and develop, creates annotated tag
- Hotfix flow: patches main and back-merges to develop
- Validates branch naming conventions before push
- Enforces linear history on main (no merge commits)

## Usage

```
/git_flow_helper feature start PROJ-123
/git_flow_helper feature finish PROJ-123
/git_flow_helper release start 1.4.0
/git_flow_helper release finish 1.4.0
/git_flow_helper hotfix start 1.4.1
```

## Configuration

```yaml
# .gitflow.yaml
develop_branch: develop
main_branch: main
version_files:
  - pyproject.toml
  - package.json
tag_prefix: "v"
enforce_linear_main: true
```

## Troubleshooting

If `finish release` fails at the merge step, check for unresolved conflicts
between release and develop branches. Resolve manually, then re-run
`/git_flow_helper release finish --continue`.
