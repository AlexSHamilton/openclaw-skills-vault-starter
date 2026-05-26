# Context

Dynamic state for the vault. Update as you review skills.

## Status

- Vault initialized: 2026-05-19.
- Catalog version: 2 (added s9 meta-injection 2026-05-26; old s9 verdict-format -> s10, history -> s11, TODO -> s12).
- Verified skills: 0.
- Smoke test: calibration round DONE 2026-05-19 on the 16-skill corpus (Claude Sonnet 4.6 + Codex medium); results in `unverified/smoke-test/smoke-test-results.md`. Zero false negatives; the single WARN on the clean control was a corpus artifact (name/folder mismatch), not a pipeline flaw. Re-run on the expanded 19-skill corpus (now incl. 3 adaptive meta-injection skills) before the first real install.
- Deterministic pre-scan: `tools/prescan.py` runs before the LLM passes (Step 1.5 of the procedure). It is the regex/unicode floor under the two model passes.

## Active reviews

None.

## Open questions

- Re-run the smoke test on the expanded 19-skill corpus (incl. the 3 adaptive meta-injection skills) and confirm all 3 adaptive skills reach BLOCK before the first real install.

## Recent decisions

- 2026-05-19: vault structure and 6-step procedure established.
- 2026-05-26: added defense against meta-injection on the reviewer (recursive-trust hardening): catalog s9, deterministic pre-scan `tools/prescan.py` as a pre-LLM floor, and 3 adaptive smoke-test skills. Motivated by external feedback on the two-LLM trust model.

## Where things live

```
README.md                       project overview
docs/REVIEW_PROCEDURE.md        the algorithm
docs/INJECTION_PATTERNS.md      the catalog (single source of truth)
docs/CODEX_REVIEW_TEMPLATE.md   for the Codex reviewer
docs/LOCKFILE_SCHEMA.md         lockfile format
tools/prescan.py                deterministic pre-scan (runs before the LLM passes)
agent/CLAUDE_INSTRUCTIONS.md    executor instructions for the Claude reviewer
agent/CONTEXT.md                this file
unverified/                     quarantine
verified/                       approved skills
skills-lockfile.yaml            audit trail
```
