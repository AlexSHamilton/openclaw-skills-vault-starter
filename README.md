# OpenClaw Skills Vault

A simple, auditable quarantine workflow for reviewing third-party OpenClaw skills before installing them into a production agent.

## Why

An OpenClaw skill is a folder with a `SKILL.md` (YAML frontmatter + markdown body) plus optional supporting files and an optional installer spec (`metadata.openclaw.install`).

The `name` and `description` fields of every eligible skill are injected directly into the agent's **system prompt** at session start. That means a malicious or careless skill can attempt prompt injection against your agent without ever reaching the regular untrusted-data sanitization layer. Skill registries are public; new injection patterns appear regularly.

This repo gives you a low-tech, repeatable process to vet a skill before it can reach your agent:

1. Pull the skill into a quarantine folder (`unverified/`).
2. Have Claude review it (see "How the review works" below).
3. Have Codex review it independently with the same rules.
4. Make the call yourself based on both verdicts.
5. Move it to `verified/` and record a lockfile entry (sha256 + verdicts).
6. Install into your agent only from `verified/`.

No Docker required for the default flow. No CI required. Two LLMs and a human decision.

## How the review works

Each LLM reviewer (Claude and Codex) runs under a **dual mandate** on the same skill folder:

1. **Closed checklist - against the catalog.** The reviewer walks `docs/INJECTION_PATTERNS.md` section by section and flags every match: bracket-tag patterns, role-addressing phrases, Unicode anomalies, tool-bypass wording, shell and supply-chain risks, secret exfiltration, install-domain whitelist, structural red flags. This part is deterministic and reproducible. The catalog is the floor: anything in it must be detected.

2. **Open analysis - the reviewer's own judgement.** After the catalog pass, the reviewer does a second read with no checklist and looks for anything else that smells wrong: novel injection techniques the catalog has not seen yet, paraphrased attacks, suspicious combinations of innocuous-looking elements, inconsistencies between what the skill claims and what its code does. This is why the system uses LLMs instead of regex: catalog rules can only catch attacks people have already named.

The verdict format separates the two cleanly:

- `FINDINGS` - catalog hits, each with a section reference (s1..s8).
- `NOVEL_FINDINGS` - anything the reviewer spotted through open analysis. The operator reads these on every review, even when both verdicts say PASS.
- `CATALOG_SUGGESTIONS` - proposed catalog additions. The operator decides whether to merge them, which means the catalog grows from real findings rather than only what was anticipated up front.

**Asymmetry on severity.** A novel finding raises the verdict to at most WARN, never directly to BLOCK. BLOCK is reserved for explicit catalog hits where the rule has been pre-agreed. This keeps free analysis useful without making it scary: surface anything that looks off; the operator decides what to do with it.

Two reviewers, two independent passes, the same dual mandate, one human decision. The catalog stays the floor; the reviewers can always raise the ceiling.

## Fetching skills into unverified/

Before you can review a skill you need its files locally. OpenClaw has two categories of skills and they come from different places. Do not install anything into your live agent yet - that happens only after the review passes.

### Category 1: registry skills (ClawHub)

Most third-party and community skills live in the ClawHub registry. The recommended way to fetch them is the `clawhub` CLI, which downloads the zip, unpacks it, and writes provenance metadata - without touching your OpenClaw installation at all.

**One-time setup:**

```bash
npm i -g clawhub
```

No login required for public skills.

**Fetch a skill into the quarantine folder:**

```bash
VAULT=/path/to/openclaw-skills-vault/unverified

clawhub --workdir "$VAULT" --dir . install <slug>
```

Result:

```
unverified/
  <slug>/
    SKILL.md
    scripts/          (if the skill includes any)
    .clawhub/
      origin.json     (registry, version, installed timestamp)
```

**Find the correct slug before downloading:**

```bash
clawhub search "keyword"
clawhub inspect <slug>          # shows metadata and file list without downloading
clawhub inspect <slug> --files  # lists every file that will be unpacked
```

The slug is a flat identifier with no slashes (e.g. `apollo`, not `author/apollo`). The search output shows `slug  @owner  Display Name  (score)` - use the first column.

**Fetch a specific version:**

```bash
clawhub --workdir "$VAULT" --dir . install <slug> --version 1.2.3
```

**If the registry is unreachable** (`fetch failed` / DNS not resolving):

The registry runs on Vercel. If your machine uses a custom DNS resolver (Tailscale, corporate VPN, etc.) it may not resolve `clawhub.ai`. Quick fix:

```bash
# Resolve the IP once via a public resolver
dig clawhub.ai @8.8.8.8 +short   # should return something like 216.150.1.1

# Pin it in /etc/hosts so your system resolver uses it
sudo sh -c 'echo "216.150.1.1 clawhub.ai" >> /etc/hosts'
```

You can remove the line from `/etc/hosts` after downloading.

### Category 2: bundled skills

A small set of skills ships bundled with OpenClaw itself (examples: `wacli`, `discord`, `slack`, `github`). These are not in the ClawHub registry. Their source is the `openclaw/openclaw` GitHub repository.

Fetch with the `gh` CLI (requires `gh auth login` first):

```bash
SLUG=wacli   # or discord, slack, github, etc.
DEST=/path/to/openclaw-skills-vault/unverified/$SLUG

mkdir -p "$DEST"
gh api "repos/openclaw/openclaw/contents/skills/$SLUG/SKILL.md" \
  --jq '.content' | base64 -d > "$DEST/SKILL.md"
```

Bundled skills typically contain only `SKILL.md` - their runtime support lives inside the OpenClaw package itself, not in separate script files.

### What NOT to do

- Do not run `openclaw skills install <slug>` - that puts the skill directly into your active agent workspace, bypassing this review process entirely.
- Do not execute any file from `unverified/` before the review passes.
- Do not copy a skill from `unverified/` to `verified/` manually - follow the promotion step in `docs/REVIEW_PROCEDURE.md` so the lockfile entry gets written.

---

## Quick start

```bash
# 1. Clone this repo somewhere local
git clone <your-fork-url> openclaw-skills-vault
cd openclaw-skills-vault

# 2. Read the procedure
cat docs/REVIEW_PROCEDURE.md

# 3. To review a new skill:
git checkout -b review/<slug>-$(date +%Y%m%d)
# Download the skill folder into unverified/<slug>/ (see "Fetching skills" above)
```

When you start a Claude session in this repo, ask Claude to first read its executor files in `agent/`:

1. `agent/CLAUDE_INSTRUCTIONS.md` (executor instructions for the Claude reviewer)
2. `agent/CONTEXT.md` (current state of the vault)

You can also ask Claude to fetch a skill for you before reviewing it. Just say something like **"download the skill `<slug>` from the registry into unverified/ following the instructions in CLAUDE_INSTRUCTIONS.md"** and Claude will handle the `clawhub` command, slug lookup, and DNS quirks for you.

Then give it the task: **"review the skill in `unverified/<slug>/` for injections"**.

For the Codex pass, use the template in `docs/CODEX_REVIEW_TEMPLATE.md`.

## What's in this repo

The repo separates two audiences:

- `docs/` is for the human operator: procedure, shared pattern catalog, Codex prompt template, lockfile schema.
- `agent/` is for the Claude reviewer agent: its self-contained executor instructions and the dynamic context file. The agent reads these at session start.

The shared pattern catalog (`docs/INJECTION_PATTERNS.md`) is referenced by both audiences and by both LLM reviewers; it intentionally lives in `docs/` so people can read it directly without digging into `agent/`.

```
openclaw-skills-vault/
  README.md                       this file
  docs/                           for the human operator
    REVIEW_PROCEDURE.md           the 6-step algorithm
    INJECTION_PATTERNS.md         the shared catalog used by both reviewers and humans
    CODEX_REVIEW_TEMPLATE.md      the <pr_review> template for Codex
    LOCKFILE_SCHEMA.md            schema for skills-lockfile.yaml entries
  agent/                          for the Claude reviewer agent
    CLAUDE_INSTRUCTIONS.md        executor instructions (read first)
    CONTEXT.md                    dynamic state (active reviews, history)
  unverified/                     quarantine zone, files are unstaged
  verified/                       approved skills, ready to install
  skills-lockfile.yaml            audit trail
  .gitignore
```

## Threat model

Catalog coverage (closed checklist, deterministic):

- Injection patterns in `description`/`name` that hijack the agent's system prompt.
- Unicode-based obfuscation (RTL override, zero-width characters, tag characters).
- Tool-bypass instructions that try to skip approval gates.
- Supply-chain risks in installer specs (untrusted download domains, pipe-to-shell scripts).
- Secret exfiltration patterns in supporting scripts.

Open-analysis coverage (each reviewer's own judgement, non-deterministic):

- Novel injection wording that does not match catalog phrases verbatim.
- Combinations of individually innocent elements that together create risk.
- Behavioral requests that functionally skip a gate without matching catalog language.
- Inconsistencies between a skill's stated purpose and its actual code.

It does NOT protect against:

- Runtime behavior that only manifests at execution time. The optional Docker step in `docs/REVIEW_PROCEDURE.md` exists for that and stays off by default.
- Compromise of the reviewers themselves (Claude or Codex). Two independent passes reduce the risk but do not eliminate it.
- Attacks that both reviewers fail to recognize even with open analysis. The dual-pass design narrows this window; it does not close it. Extend the catalog whenever a real incident teaches you a new pattern.

## Smoke test

> ⚠️ **WARNING - intentional injections present.** The folder `unverified/smoke-test/` contains 16 synthetic skills with deliberately embedded prompt-injection payloads (bracket-tags, Unicode anomalies, pipe-to-shell scripts, credential exfiltration, and more). They exist solely as a calibration corpus for the dual-review pipeline. Do not install or execute any file from that folder.

A pre-built calibration corpus lives in `unverified/smoke-test/` - 15 malicious skills covering every catalog section (§1–8) plus novel semantic attacks, and 1 clean control. Before relying on this pipeline for real installs, run both reviewers against all 16 skills yourself and check that you hit ≥ 95% detection (BLOCK or WARN on malicious, PASS on the clean control).

**Reference results** from an independent calibration round (Claude Sonnet 4.6 + GPT Codex medium) are recorded in `unverified/smoke-test/smoke-test-results.md`. That file explains what each skill tests, the verdicts both models produced, and why the one apparent miss (`docstring_linter` → WARN instead of PASS) is a corpus artifact rather than a pipeline flaw.

You are encouraged to run the smoke test yourself and reach your own conclusions before deciding whether this pipeline meets your trust bar. Do not rely solely on the reference results - model behaviour varies across versions and prompting styles.

## License

MIT. Use it, fork it, extend the pattern catalog, contribute back.

## Status

Initial public version. No verified skills yet. The catalog is a starting point; expect it to grow as the open-analysis pass surfaces new patterns and operators promote good `CATALOG_SUGGESTIONS` into the catalog.
