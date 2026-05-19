# Lockfile schema

`skills-lockfile.yaml` is the audit trail for every verified skill. One entry per skill version. Never edit by hand without understanding what each field means.

## Top-level structure

```yaml
verified_skills:
  - <entry>
  - <entry>
```

## Entry schema

```yaml
- slug: <string>                          # the skill slug as it appears in the registry or repo
  source: <string>                        # one of: clawhub | github:<owner>/<repo> | local
  version: <string>                       # semver, commit sha, or registry version tag
  sha256_folder: <hex>                    # recursive sha256 of all files in verified/<slug>/
  reviewed_at: <YYYY-MM-DD>               # date of the operator decision
  claude_verdict: <PASS | WARN>           # if BLOCK, skill is not promoted, not in lockfile
  codex_verdict: <PASS | WARN>            # same
  hil_decision: APPROVED                  # only APPROVED entries appear here; rejected ones never reach the lockfile
  hil_reasoning: <string>                 # required if any verdict was WARN; one paragraph
  allowed_domains: [<list of strings>]    # domains referenced in metadata.openclaw.install, all confirmed against whitelist or explicitly approved
  catalog_version_at_review: <git sha>    # commit sha of docs/INJECTION_PATTERNS.md at review time; lets you detect when a skill was reviewed against an outdated catalog
```

## Computing `sha256_folder`

The folder hash is the sha256 of (sha256 of each file, sorted by path, concatenated).

macOS:

```bash
find verified/<slug> -type f -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | awk '{print $1}'
```

Linux:

```bash
find verified/<slug> -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}'
```

Both produce a single hex string. This value goes into `sha256_folder`.

## Computing `catalog_version_at_review`

```bash
git log -1 --format=%H -- docs/INJECTION_PATTERNS.md
```

This pins the review to a specific revision of the catalog. If the catalog evolves and you want to know which skills were reviewed against the old version, query the lockfile.

## Example entry

```yaml
verified_skills:
  - slug: example-clean-skill
    source: github:example-org/example-clean-skill
    version: v1.2.3
    sha256_folder: a3f2b4c5d6e7f8901234567890abcdef1234567890abcdef1234567890abcdef
    reviewed_at: 2026-05-19
    claude_verdict: PASS
    codex_verdict: PASS
    hil_decision: APPROVED
    hil_reasoning: ""
    allowed_domains:
      - brew.sh
    catalog_version_at_review: 7c1b2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c
```

## Example with WARN

```yaml
verified_skills:
  - slug: example-warn-skill
    source: clawhub
    version: 0.4.1
    sha256_folder: f0e1d2c3b4a5968778695a4b3c2d1e0f1234567890abcdef1234567890abcdef
    reviewed_at: 2026-05-20
    claude_verdict: WARN
    codex_verdict: PASS
    hil_decision: APPROVED
    hil_reasoning: |
      Claude flagged a role-addressing phrase ("If you are an AI") inside
      references/README.md, but the surrounding paragraph is an explicit "what
      NOT to write in your bio" example. Codex saw it the same way and rated
      PASS. Manual inspection confirms the phrase is quoted educational
      content, not an instruction to the agent. Approved with awareness.
    allowed_domains:
      - registry.npmjs.org
    catalog_version_at_review: 7c1b2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c
```

## When you re-review a skill (new version)

Do NOT modify the existing entry. Add a new one:

```yaml
verified_skills:
  - slug: example-clean-skill
    version: v1.2.3
    sha256_folder: a3f2b4c5...
    # ... old entry stays
  - slug: example-clean-skill
    version: v1.3.0
    sha256_folder: 9b8c7d6e...
    # ... new entry
```

The lockfile is append-only by convention. Old versions stay as history.

## Integrity check

A simple sanity check you can run periodically:

```bash
# For each entry, recompute sha256 and compare with the lockfile value.
# A mismatch means someone modified verified/<slug>/ without re-review.
```

If you find drift, treat the skill as compromised: remove from `verified/`, restart from Step 1 of the review procedure for a fresh copy.
