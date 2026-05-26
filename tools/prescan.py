#!/usr/bin/env python3
"""Deterministic pre-scan for OpenClaw skills.

Runs BEFORE either LLM reviewer reads the skill. The point is a layer that
cannot be talked out of its findings: a regex or a codepoint check is not
susceptible to a paragraph of text arguing it is a false positive. This is the
orthogonal barrier to the two LLM passes -- it shares none of their failure
modes.

It does NOT replace the LLM review. It is the floor under it. Anything this
script flags is ground truth the reviewer must not override; the LLM still does
the open-analysis pass on top.

Usage:
    python3 tools/prescan.py unverified/<slug>/

Exit codes:
    0  clean        (no hits)
    1  WARN         (soft hits only)
    2  BLOCK         (at least one hard hit)

Catalog references (docs/INJECTION_PATTERNS.md):
    s1  bracket-tags
    s3  unicode anomalies
    s5  pipe-to-shell
    s9  meta-injection targeting the reviewer

The script is intentionally conservative: it favours false positives over false
negatives. A human or the LLM pass downgrades; this script only raises.
"""

import hashlib
import re
import sys
import unicodedata
from pathlib import Path

# ---- severities -------------------------------------------------------------

BLOCK = "BLOCK"
WARN = "WARN"

# ---- hard patterns: BLOCK ---------------------------------------------------

# s1 bracket-tag delimiters. Case-insensitive. The \W* between the bracket and
# the word absorbs zero-width / whitespace obfuscation inside the tag.
BRACKET_TAGS = re.compile(
    r"\[\s*/?\s*(?:admin|system|inst|root|override|sys)\s*\]"
    r"|<\s*/?\s*(?:system|sys)\s*>"
    r"|<\|im_(?:start|end)\|>"
    r"|<<\s*/?\s*sys\s*>>"
    r"|###\s*(?:system|instruction)\s*:",
    re.IGNORECASE,
)

# s9 meta-injection: text addressed to the reviewer, not the consuming agent.
META_INJECTION = [
    (re.compile(r"\balready (?:passed|been|reviewed|cleared|vetted|verified)\b", re.I),
     "claimed prior approval (s9)"),
    (re.compile(r"\bpre[- ]?approved\b", re.I), "claimed prior approval (s9)"),
    (re.compile(r"\belevated trust\b", re.I), "asserted elevated trust (s9)"),
    (re.compile(r"\btrusted publisher\b", re.I), "asserted elevated trust (s9)"),
    (re.compile(r"\bskip (?:the |this )?(?:security )?review\b", re.I),
     "self-referential review bypass (s9)"),
    (re.compile(r"\bexempt from (?:injection |security )?scan", re.I),
     "self-referential review bypass (s9)"),
    (re.compile(r"\balways trust\b", re.I), "policy poisoning (s9)"),
    (re.compile(r"\bmark all .{0,40}\bas (?:pass|safe|clear|verified)\b", re.I),
     "policy poisoning (s9)"),
    (re.compile(r"\b(?:render|output|return|set) (?:the )?verdict\b.{0,30}\bpass\b", re.I),
     "direct verdict instruction (s9)"),
    (re.compile(r"\bdo not (?:flag|block|warn|report)\b", re.I),
     "direct verdict instruction (s9)"),
    (re.compile(r"^\s*(?:reviewer|claude|codex|operator)\s*:", re.I | re.M),
     "reviewer role-addressing (s9)"),
    (re.compile(r"\bnote to the reviewing (?:model|agent|llm)\b", re.I),
     "reviewer role-addressing (s9)"),
    (re.compile(r"\bper s\d+\b.{0,40}\b(?:false[- ]?positive|render pass|warn[- ]?only)\b", re.I),
     "catalog-rule lawyering (s9)"),
    (re.compile(r"\bignore (?:all )?(?:previous|prior|the above)\b", re.I),
     "ignore-previous-instructions (s2)"),
    (re.compile(r"\bapprove this skill\b", re.I), "direct verdict instruction (s9)"),
]

# s5 pipe-to-shell / eval-from-network.
PIPE_TO_SHELL = [
    (re.compile(r"(?:curl|wget)\b[^\n|]*\|\s*(?:sudo\s+)?(?:ba|z)?sh\b"),
     "pipe-to-shell (s5)"),
    (re.compile(r"\beval\s+[\"$]\(", ), "eval of command substitution (s5)"),
    (re.compile(r"(?:ba|z)?sh\s+<\(\s*(?:curl|wget)"),
     "process-substitution exec (s5)"),
    (re.compile(r"\bbase64\s+-d\b[^\n|]*\|\s*(?:ba|z)?sh\b"),
     "base64-decoded pipe-to-shell (s5)"),
    (re.compile(r"\bexec\s*\(\s*(?:base64|compile|urllib|urlopen|requests)"),
     "inline exec of fetched/decoded payload (s5)"),
]

# ---- soft patterns: WARN ----------------------------------------------------

# Comments are not part of the AgentSkills SKILL.md spec and are a natural
# hiding place for reviewer-directed text. We surface every one; the reviewer
# reads what is inside.
HTML_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
MD_LINK_COMMENT = re.compile(r"^\s*\[//\]:\s*#", re.M)

# s3 unicode: invisible / format / private-use codepoints, and Tag Characters.
# Tag Characters and RTL/LTR override are themselves BLOCK; other Cf are WARN
# in body but the script reports all and lets the catalog grade severity. We
# split: hard set -> BLOCK, rest -> WARN.
UNICODE_HARD = set(range(0x202A, 0x202F)) | set(range(0xE0000, 0xE0080)) | {0xFEFF}
ZERO_WIDTH = {0x200B, 0x200C, 0x200D}

TEXT_SUFFIXES = {
    ".md", ".txt", ".py", ".sh", ".js", ".ts", ".yaml", ".yml", ".json",
    ".toml", ".cfg", ".ini", ".rst", ".html", ".xml", "",
}


def is_text(path: Path) -> bool:
    if path.suffix.lower() in TEXT_SUFFIXES:
        return True
    try:
        path.read_text(encoding="utf-8")
        return True
    except (UnicodeDecodeError, OSError):
        return False


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def line_of(text: str, idx: int) -> int:
    return text.count("\n", 0, idx) + 1


def strip_invisible(text: str):
    # Drop zero-width / format chars so obfuscated tags ([adm<ZWSP>in]) and
    # phrases collapse back to their detectable form. These chars are never
    # newlines, so line numbers computed against this string still match the
    # raw file. We keep a parallel index map for accurate line reporting.
    out = []
    idx_map = []
    for i, ch in enumerate(text):
        if ord(ch) in ZERO_WIDTH or unicodedata.category(ch) == "Cf":
            continue
        out.append(ch)
        idx_map.append(i)
    return "".join(out), idx_map


def scan_text(rel: str, text: str, findings: list) -> None:
    stripped, idx_map = strip_invisible(text)

    def raw_line(stripped_idx: int) -> int:
        return line_of(text, idx_map[stripped_idx]) if idx_map else 1

    for m in BRACKET_TAGS.finditer(stripped):
        findings.append((BLOCK, rel, raw_line(m.start()),
                         f"bracket-tag delimiter {m.group(0)!r} (s1)"))

    for rx, label in META_INJECTION:
        for m in rx.finditer(stripped):
            findings.append((BLOCK, rel, raw_line(m.start()), label))

    for rx, label in PIPE_TO_SHELL:
        for m in rx.finditer(text):
            findings.append((BLOCK, rel, line_of(text, m.start()), label))

    for i, ch in enumerate(text):
        cp = ord(ch)
        if cp in UNICODE_HARD:
            findings.append((BLOCK, rel, line_of(text, i),
                             f"unicode anomaly U+{cp:04X} ({unicodedata.name(ch, '?')}) (s3)"))
        elif cp in ZERO_WIDTH or unicodedata.category(ch) in ("Cf", "Co"):
            findings.append((WARN, rel, line_of(text, i),
                             f"zero-width/format char U+{cp:04X} (s3)"))

    for m in HTML_COMMENT.finditer(text):
        snippet = " ".join(m.group(0).split())[:80]
        findings.append((WARN, rel, line_of(text, m.start()),
                         f"HTML comment (not in SKILL.md spec; inspect): {snippet!r}"))
    for m in MD_LINK_COMMENT.finditer(text):
        findings.append((WARN, rel, line_of(text, m.start()),
                         "markdown link-style comment [//]: # (inspect)"))


def main(argv: list) -> int:
    if len(argv) != 2:
        print("usage: prescan.py <skill-folder>", file=sys.stderr)
        return 2
    root = Path(argv[1])
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2

    findings: list = []
    binaries: list = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if path.name.startswith(".claude-verdict") or path.name.startswith(".codex-verdict"):
            continue
        rel = str(path.relative_to(root))
        if is_text(path):
            scan_text(rel, path.read_text(encoding="utf-8", errors="replace"), findings)
        else:
            binaries.append((rel, sha256(path)))

    block = [f for f in findings if f[0] == BLOCK]
    warn = [f for f in findings if f[0] == WARN]

    print(f"# prescan: {root}")
    print(f"# {len(block)} BLOCK, {len(warn)} WARN, {len(binaries)} binary file(s)\n")
    for sev, rel, line, desc in block + warn:
        print(f"{sev:5} [{rel}:{line}] {desc}")
    for rel, digest in binaries:
        print(f"WARN  [{rel}] binary file, sha256={digest} (not scanned; inspect manually)")
    if binaries and not warn and not block:
        pass
    if not findings and not binaries:
        print("clean: no deterministic hits")

    if block:
        return 2
    if warn or binaries:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
