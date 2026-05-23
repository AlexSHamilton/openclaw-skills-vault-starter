---
name: markdown_linter
description: Lints markdown files and reports style violations
homepage: https://github.com/openclaw/markdown-linter
metadata:
  openclaw:
    install:
      type: pip
      package: openclaw-markdown-linter
    always: false
user-invocable: true
disable-model-invocation: false
---

# Markdown Linter

Checks markdown files against a configurable style guide and reports violations.

## Usage

Point this skill at a file or directory. It will produce a list of style
violations with line numbers and suggested fixes.

## Supported rules

- Heading hierarchy (no skipped levels)
- Line length limits
- Consistent list markers
- Trailing whitespace
- Blank lines around headings and code blocks

## Configuration

Create a `.markdownlint.yaml` in your project root to customize rules.
