---
title: Citation Configuration
description: BibTeX autocomplete configuration
---

## Citation section

```toml
[citations]
bib_files = []
enabled = true
autoscan = true
```

## Keys
- `bib_files` adds extra `.bib` files or directories to scan
- `enabled` turns citation loading off completely
- `autoscan` reloads citation data when `.bib` files change on disk


## How scanning works

txtr scans:

1. the current file's directory
2. any extra paths listed in `bib_files`

If multiple `.bib` files contain the same citation key, txtr now deduplicates the completion list by key.

## Examples

### Add a shared bibliography

```toml
[citations]
bib_files = ["~/tex/bib/master.bib"]
``````

### Scan a directory of bibliographies

```toml
[citations]
bib_files = ["~/tex/bib"]
```

### Disable citation loading

```toml
[citations]
enabled = false
```

- `bib_files` adds extra `.bib` files or directories to scan
- `enabled` turns citation loading off completely
- `autoscan` reloads citation data when `.bib` files change on disk

## How scanning works

txtr scans:

1. the current file's directory
2. any extra paths listed in `bib_files`

If multiple `.bib` files contain the same citation key, txtr now deduplicates the completion list by key.

## Examples

### Add a shared bibliography

```toml
[citations]
bib_files = ["~/tex/bib/master.bib"]
``````

### Scan a directory of bibliographies

```toml
[citations]
bib_files = ["~/tex/bib"]
``````

### Disable citation loading

```toml
[citations]
enabled = false
``````

