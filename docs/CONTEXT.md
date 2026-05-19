# Context

Dynamic state for the vault. Update as you review skills.

## Status

- Vault initialized: 2026-05-19.
- Catalog version: 1 (initial).
- Verified skills: 0.
- Smoke test (10 to 15 synthetic injection skills): TODO before production use. See `docs/REVIEW_PROCEDURE.md`, section "Smoke test". Detection rate >= 95% (Claude + Codex) is the gate.

## Active reviews

None.

## Open questions

- Smoke test corpus needs to be built. Until detection rate >= 95% on it, do not trust this workflow for real installs.

## Recent decisions

- 2026-05-19: vault structure and 6-step procedure established.

## Where things live

```
README.md                       project overview
docs/REVIEW_PROCEDURE.md        the algorithm
docs/INJECTION_PATTERNS.md      the catalog (single source of truth)
docs/CLAUDE_INSTRUCTIONS.md     for the Claude reviewer
docs/CODEX_REVIEW_TEMPLATE.md   for the Codex reviewer
docs/LOCKFILE_SCHEMA.md         lockfile format
docs/CONTEXT.md                 this file
unverified/                     quarantine
verified/                       approved skills
skills-lockfile.yaml            audit trail
```
