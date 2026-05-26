# Review procedure

The 6-step algorithm for vetting an OpenClaw skill before it reaches a production agent. Self-contained: an operator without prior context should be able to follow this.

---

## Prerequisites

- This repo cloned locally.
- Claude Code (or another Claude-based CLI) available in this working directory.
- Codex CLI available (separate session).
- `git`, `python3`, `sha256sum` (or `shasum -a 256` on macOS) on PATH.

You do NOT need Docker for the default flow. Docker is an optional step 4.5 for paranoid validation of installer specs (see below).

---

## Step 0: One-time setup

Already done if you cloned this repo. The structure is:

```
unverified/                 quarantine zone
verified/                   approved skills
skills-lockfile.yaml        audit trail (starts empty)
docs/INJECTION_PATTERNS.md  the shared catalog used by both reviewers
```

Verify `skills-lockfile.yaml` starts as:

```yaml
verified_skills: []
```

---

## Step 1: FETCH

Create a review branch and pull the skill folder into quarantine.

```bash
SLUG=example-skill
DATE=$(date +%Y%m%d)
git checkout -b review/$SLUG-$DATE
```

Pull the skill folder into `unverified/$SLUG/`. Method depends on the source:

**From ClawHub:**
```bash
# Use a throwaway workspace, NOT your production agent workspace
mkdir -p /tmp/openclaw-fetch-$$ && cd /tmp/openclaw-fetch-$$
openclaw skills install $SLUG
# Copy the downloaded folder back into the vault
cp -r ./skills/$SLUG /path/to/openclaw-skills-vault/unverified/$SLUG
cd /path/to/openclaw-skills-vault
rm -rf /tmp/openclaw-fetch-$$
```

Alternative: `clawhub install $SLUG --dir ./unverified/$SLUG` if that flag is available in your `clawhub` version.

**From a GitHub repo:**
```bash
git clone --depth 1 <repo-url> unverified/$SLUG
rm -rf unverified/$SLUG/.git
```

Important:

- **Do not** run any `metadata.openclaw.install` installer spec at this stage.
- **Do not** `git add` or `git commit`. Files stay in the working tree of the review branch.

---

## Step 1.5: PRE-SCAN (deterministic, mandatory)

Before either LLM sees the skill, run the deterministic pre-scan:

```bash
python3 tools/prescan.py unverified/$SLUG/
```

Why first: a regex and a codepoint check cannot be argued out of their findings. This is the one layer in the pipeline that shares none of the LLMs' failure modes - it is the floor under the two model passes, aimed squarely at the recursive-trust problem (a skill talking the reviewer into a PASS). It catches what string/unicode rules catch: bracket-tags (including zero-width-obfuscated ones), unicode anomalies, pipe-to-shell, and meta-injection phrases addressed to the reviewer (s9).

Exit codes: `0` clean, `1` WARN-level hits, `2` BLOCK-level hits.

What to do with the result:

- **Exit 2 (BLOCK):** the skill is already disqualified on a deterministic hard hit. You may still run the LLM passes for the catalog/novel findings, but the pre-scan BLOCK stands regardless of what the models say. A reviewer cannot downgrade a deterministic BLOCK.
- **Exit 1 (WARN) / Exit 0 (clean):** proceed to the LLM passes normally. The pre-scan is a floor, not a ceiling - the LLMs still do the full catalog + open-analysis work on top. A clean pre-scan does NOT mean the skill is safe; it means no *string-level* attack was found. Semantic and behavioral attacks are the LLMs' job.

Paste the pre-scan output into the Claude and Codex sessions as ground truth. The models must treat its hits as established, not re-litigate them.

---

## Step 2: CLAUDE REVIEW

In a Claude Code session in this repo, ask Claude to read `agent/CLAUDE_INSTRUCTIONS.md` and `agent/CONTEXT.md`, then give it the task:

```
Review the skill in unverified/<slug>/ for injections.
```

Claude operates under a dual mandate (catalog + open analysis). It will:

1. Read `docs/INJECTION_PATTERNS.md` (the catalog).
2. Read `unverified/<slug>/SKILL.md` and all supporting files.
3. Apply the catalog section by section (closed checklist).
4. Run a second pass using its own judgement to spot anything suspicious that is not yet in the catalog (open analysis).
5. Write a verdict to `unverified/<slug>/.claude-verdict.md` in this format:

```markdown
# Claude review verdict

- Skill: <slug>
- Reviewed: YYYY-MM-DD
- Branch: review/<slug>-YYYYMMDD
- Catalog version: <git sha of docs/INJECTION_PATTERNS.md>

## VERDICT
PASS | WARN | BLOCK

## FINDINGS (catalog hits)
- [path:line] description (sX)
- ...
(or: none)

## NOVEL_FINDINGS (open analysis, not in catalog)
- [path:line] description + why this looks suspicious
- ...
(or: none)

## CATALOG_SUGGESTIONS (optional)
- Proposed pattern + suggested section + rationale
- ...
(or: none)

## REASONING
1-2 sentences.
```

Novel findings raise the verdict to at most WARN, never directly to BLOCK. BLOCK is reserved for explicit catalog hits.

---

## Step 3: CODEX REVIEW

Switch to a Codex CLI session in the same working directory. Use the template in `docs/CODEX_REVIEW_TEMPLATE.md` to form the request, substituting `<slug>` and the branch name. The template puts Codex under the same dual mandate (catalog + open analysis) and asks for the same output format (FINDINGS / NOVEL_FINDINGS / CATALOG_SUGGESTIONS).

Save Codex's verdict to `unverified/<slug>/.codex-verdict.md` in the same structure as the Claude verdict.

---

## Step 4: HIL DECISION

Read both verdict files. Apply the decision matrix on the **verdict line**:

| Claude verdict | Codex verdict | Action |
|---|---|---|
| PASS | PASS | proceed to Step 5 (read NOVEL_FINDINGS first, see below) |
| any BLOCK | any | drop the skill (Step 4a) |
| any other mixed (PASS+WARN, WARN+WARN, etc.) | manual review (Step 4b) |

### Read NOVEL_FINDINGS even on double-PASS

A PASS verdict can still come with `NOVEL_FINDINGS` entries (when the reviewer found something curious but not severe enough to warrant WARN). Always read the NOVEL_FINDINGS block of both verdicts before promoting. If anything there gives you pause, treat the case as mixed and go to Step 4b.

### Catalog suggestions

Both verdicts may include `CATALOG_SUGGESTIONS`. For each suggestion you find valuable:

1. Open `docs/INJECTION_PATTERNS.md`.
2. Add the pattern to the relevant section (s1 to s9) with a short example and an entry in s11 (catalog history) describing the addition and its source ("from review of <slug>, <date>").
3. Commit the catalog change separately from the skill promotion so the history is clean: `chore(catalog): add <pattern> (from <slug> review)`.

You do NOT need to re-review already-verified skills against an extended catalog; the lockfile's `catalog_version_at_review` field records which version each skill was reviewed against. If a future incident makes a specific extension load-bearing, you can decide then whether to re-review affected skills.

### Step 4a: drop a skill

```bash
git checkout main
git branch -D review/$SLUG-$DATE
rm -rf unverified/$SLUG
```

### Step 4b: mixed verdicts (manual review)

Read both `.claude-verdict.md` and `.codex-verdict.md`, including FINDINGS and NOVEL_FINDINGS blocks. Look at each finding by hand. Decide whether to approve (with documented reasoning) or drop. If you approve despite a WARN, the reasoning must be specific (which findings you dismissed and why) - this goes into `hil_reasoning` in the lockfile (Step 5).

If Claude and Codex disagree sharply on the verdict (one PASS, one WARN), the disagreement itself is information. Read both blocks; if one reviewer spotted something the other missed, that is usually a real signal worth heeding.

### Step 4.5 (optional, paranoid): sandboxed install test

Only if the skill has an `install` spec pointing at a non-whitelist domain and you want extra assurance:

```bash
# Spin up a throwaway Docker container
docker run --rm -it --network none \
  -v $PWD/unverified/$SLUG:/skill:ro \
  alpine:latest sh
# Inside: read the install spec, then re-enable network with a transparent proxy
# (mitmproxy or tcpdump) to observe what would be fetched. Do NOT execute the
# installer outside this container.
```

This is intentionally manual and rare. Default flow skips it.

---

## Step 5: PROMOTION

For an approved skill:

```bash
git mv unverified/$SLUG verified/$SLUG
```

Compute the recursive sha256 of the folder:

```bash
# macOS (shasum)
find verified/$SLUG -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}'

# Linux (sha256sum)
find verified/$SLUG -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}'
```

Append an entry to `skills-lockfile.yaml`. Use the schema in `docs/LOCKFILE_SCHEMA.md`. Minimum required fields:

```yaml
verified_skills:
  - slug: <slug>
    source: clawhub | github:<owner>/<repo>
    version: <semver-or-commit-sha>
    sha256_folder: <hex>
    reviewed_at: YYYY-MM-DD
    claude_verdict: PASS | WARN
    codex_verdict: PASS | WARN
    hil_decision: APPROVED
    hil_reasoning: <text, required if any WARN>
    allowed_domains: [<list>]
    catalog_version_at_review: <git sha of docs/INJECTION_PATTERNS.md>
```

Commit and merge:

```bash
git add verified/$SLUG skills-lockfile.yaml
git commit -m "verify: $SLUG v<version> (Claude:PASS Codex:PASS HIL:APPROVED)"
git checkout main
git merge --no-ff review/$SLUG-$DATE
git branch -d review/$SLUG-$DATE
```

---

## Step 6: INSTALL

Install into your production agent **only** by copying from `verified/`:

```bash
cp -r /path/to/openclaw-skills-vault/verified/$SLUG \
      /path/to/your-workspace/skills/$SLUG
```

Do not run `openclaw skills install <slug>` against ClawHub directly in production. Do not run `openclaw skills update --all`.

To update a skill:

1. Fetch the new ClawHub version into a new review branch (`review/$SLUG-update-$DATE`).
2. Compute its sha256 and compare with the lockfile entry.
3. If it differs, restart from Step 1. New version means new review.

---

## Smoke test

Before trusting this workflow for the first real install, run a calibration round:

1. Build a small corpus of 10 to 15 synthetic SKILL.md files in a temporary folder:
   - Open `[admin]...[/admin]` in `description`.
   - `[admin]` hidden inside zero-width unicode.
   - Role-addressing inside body ("If you are an AI agent, ...").
   - Non-whitelist domain in `install.url`.
   - Pipe-to-shell in a `scripts/setup.sh`.
   - One clean control skill.
2. Run Steps 2 and 3 against each.
3. Detection rate (BLOCK or WARN on the malicious ones, PASS on the clean control) should be >= 95%.
4. If lower, extend `docs/INJECTION_PATTERNS.md` and re-run.

This calibration also lets you compare how Claude and Codex behave on the same inputs.
