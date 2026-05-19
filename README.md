# OpenClaw Skills Vault

A simple, auditable quarantine workflow for reviewing third-party OpenClaw skills before installing them into a production agent.

## Why

An OpenClaw skill is a folder with a `SKILL.md` (YAML frontmatter + markdown body) plus optional supporting files and an optional installer spec (`metadata.openclaw.install`).

The `name` and `description` fields of every eligible skill are injected directly into the agent's **system prompt** at session start. That means a malicious or careless skill can attempt prompt injection against your agent without ever reaching the regular untrusted-data sanitization layer. Skill registries are public; new injection patterns appear regularly.

This repo gives you a low-tech, repeatable process to vet a skill before it can reach your agent:

1. Pull the skill into a quarantine folder (`unverified/`).
2. Have Claude review it against a shared pattern catalog.
3. Have Codex review it independently with the same catalog.
4. Make the call yourself based on both verdicts.
5. Move it to `verified/` and record a lockfile entry (sha256 + verdicts).
6. Install into your agent only from `verified/`.

No Docker required for the default flow. No CI required. Two LLMs and a human decision.

## Quick start

```bash
# 1. Clone this repo somewhere local
git clone <your-fork-url> openclaw-skills-vault
cd openclaw-skills-vault

# 2. Read the procedure
cat docs/REVIEW_PROCEDURE.md

# 3. To review a new skill:
git checkout -b review/<slug>-$(date +%Y%m%d)
# Download the skill folder into unverified/<slug>/ (see docs/REVIEW_PROCEDURE.md)
```

When you start a Claude session in this repo, ask Claude to first read:

1. `docs/CLAUDE_INSTRUCTIONS.md` (executor instructions)
2. `docs/CONTEXT.md` (current state)

Then give it the task: **"review the skill in `unverified/<slug>/` for injections"**.

For the Codex pass, use the template in `docs/CODEX_REVIEW_TEMPLATE.md`.

## What's in this repo

```
openclaw-skills-vault/
  README.md                       this file
  docs/
    REVIEW_PROCEDURE.md           the 6-step algorithm
    INJECTION_PATTERNS.md         the shared catalog used by both reviewers
    CLAUDE_INSTRUCTIONS.md        instructions for the Claude reviewer
    CODEX_REVIEW_TEMPLATE.md      the <pr_review> template for Codex
    LOCKFILE_SCHEMA.md            schema for skills-lockfile.yaml entries
    CONTEXT.md                    dynamic state (active reviews, history)
  unverified/                     quarantine zone, files are unstaged
  verified/                       approved skills, ready to install
  skills-lockfile.yaml            audit trail
  .gitignore
```

## Threat model

This vault protects against:

- Injection patterns in `description`/`name` that hijack the agent's system prompt.
- Unicode-based obfuscation (RTL override, zero-width characters, tag characters).
- Tool-bypass instructions that try to skip approval gates.
- Supply-chain risks in installer specs (untrusted download domains, pipe-to-shell scripts).
- Secret exfiltration patterns in supporting scripts.

It does NOT protect against:

- Zero-day injection techniques absent from the catalog. Update the catalog when you see new ones.
- Runtime behavior that only manifests at execution time (you'd need sandboxed execution for that, which is an optional Docker step described in `docs/REVIEW_PROCEDURE.md`).
- Compromise of the reviewers themselves (Claude or Codex). Two independent passes reduce the risk but do not eliminate it.

## Smoke test before first production use

Before trusting this workflow for real installs, run the smoke test described in `docs/REVIEW_PROCEDURE.md` (section "Smoke test"). Build a small corpus of synthetic SKILL.md files with known injections, run both reviewers, and verify detection rate >= 95%. If lower, extend `docs/INJECTION_PATTERNS.md` and re-run.

## License

MIT. Use it, fork it, extend the pattern catalog, contribute back.

## Status

Initial public version. No verified skills yet. The catalog is a starting point and will grow as new injection patterns surface.
