---
name: dep_scanner
description: Scans project dependencies for known CVEs and outdated packages
homepage: https://github.com/openclaw/dep-scanner
metadata:
  openclaw:
    install:
      type: pip
      package: openclaw-dep-scanner
    always: false
user-invocable: false
disable-model-invocation: false
---

# Dependency Scanner

Audits `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`,
`Cargo.toml`, and `Gemfile.lock` for known CVEs, outdated packages, and
license compliance issues.

## Features

- CVE lookup via OSV, NVD, and GitHub Advisory Database
- Outdated version detection with safe upgrade suggestions
- License audit: flags packages with GPL/AGPL if your project is proprietary
- SBOM export: generates CycloneDX or SPDX bill of materials
- CI integration: exits non-zero on high-severity findings

## Usage

```
/dep_scanner scan                  # full audit of all lockfiles
/dep_scanner scan --severity high  # only high and critical CVEs
/dep_scanner upgrade               # suggest safe version bumps
/dep_scanner sbom --format cyclonedx > sbom.json
/dep_scanner licenses              # license compliance report
```

## Configuration

```yaml
# .dep-scanner.yaml
severity_threshold: medium   # low | medium | high | critical
fail_on: high                # exit non-zero on this severity or above
license_policy:
  allow: [MIT, Apache-2.0, BSD-2-Clause, BSD-3-Clause, ISC]
  deny: [GPL-3.0, AGPL-3.0]
ignore:
  - CVE-2024-12345   # false positive in test-only dependency
```

## CI example

```yaml
# .github/workflows/security.yaml
- name: Dependency audit
  run: openclaw-dep-scanner scan --severity high --fail-on high
```
