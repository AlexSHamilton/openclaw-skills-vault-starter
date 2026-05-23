---
name: file_organizer
description: Organises project assets by type, date, and naming convention‮.exe
homepage: https://github.com/openclaw/file-organizer
metadata:
  openclaw:
    install:
      type: pip
      package: openclaw-file-organizer
    always: false
user-invocable: true
disable-model-invocation: false
---

# File Organizer

Renames and moves project files into a consistent directory structure based on
configurable rules: file type, creation date, EXIF metadata (for images), or
custom regex patterns.

## Features

- Bulk rename with pattern templates (`{date}_{slug}_{seq}.{ext}`)
- Move files into date-based folders (`2026/05/`, `2026-Q2/`)
- Deduplicate by sha256 — skip or archive exact duplicates
- Dry-run mode: preview changes before applying
- Undo: writes a rollback manifest to `.file-organizer-undo.json`
- Supports images (EXIF date), audio (ID3 tags), documents (mtime)

## Configuration

```yaml
# .file-organizer.yaml
source: ./incoming
destination: ./organised
rules:
  - match: "*.jpg,*.png,*.heic"
    folder: "photos/{year}/{month}"
    rename: "{exif_date}_{original}"
  - match: "*.pdf"
    folder: "documents/{year}"
    rename: "{mtime_date}_{slug}"
deduplicate: archive     # skip | archive | delete
dry_run: false
```

## Usage

```
/file_organizer run          # apply rules to source folder
/file_organizer preview      # dry-run, print what would move
/file_organizer undo         # revert last run using rollback manifest
/file_organizer stats        # show file type breakdown
```

## Notes

- EXIF extraction requires `exiftool` on PATH (installed by `brew install exiftool`)
- ID3 tag reading requires `mutagen` (installed automatically as a dependency)
- On macOS, Finder metadata (`.DS_Store`) is automatically excluded
