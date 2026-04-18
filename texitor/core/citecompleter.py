# bib citation completer
# scans a directory for .bib files, parses them, provides key completions
# also accepts extra paths from config bib_files list

from pathlib import Path
import texitor.core.bibparser as _bib


def _first_author_last(author_str):
    first = author_str.split(" and ")[0].strip()
    if "," in first:
        return first.split(",")[0].strip()
    parts = first.rsplit(" ", 1)
    return parts[-1] if len(parts) > 1 else first


def _entry_desc(e):
    parts = []
    if e["author"]:
        parts.append(_first_author_last(e["author"]))
    if e["year"]:
        parts.append(e["year"])
    if e["title"]:
        t = e["title"]
        parts.append(t[:45] + "…" if len(t) > 45 else t)
    return "  ".join(parts) if parts else e["key"]


def _entryScore(entry):
    filled = sum(1 for field in ("author", "year", "title") if entry.get(field))
    detail = sum(len(entry.get(field, "")) for field in ("author", "year", "title"))
    return (filled, detail)


def _iterBibPaths(dir_path, extra_paths=None, include_dir=True):
    seen = set()
    dirs_to_scan = [Path(dir_path)] if include_dir else []

    for bib_path in (extra_paths or []):
        p = Path(bib_path).expanduser()
        if p.is_file():
            try:
                resolved = p.resolve()
            except OSError:
                continue
            if resolved not in seen:
                seen.add(resolved)
                yield resolved
        elif p.is_dir():
            dirs_to_scan.append(p)

    for d in dirs_to_scan:
        try:
            resolved_dir = d.expanduser().resolve()
        except OSError:
            continue
        for bib_file in sorted(resolved_dir.glob("*.bib")):
            try:
                resolved = bib_file.resolve()
            except OSError:
                continue
            if resolved not in seen:
                seen.add(resolved)
                yield resolved


class CiteCompleter:

    def __init__(self):
        self._entries = []
        self._sources = []
        self._signature = ()

    def loadDir(self, dir_path, extra_paths=None, include_dir=True):
        self._entries = []
        self._sources = []
        deduped = {}
        for bib_file in _iterBibPaths(dir_path, extra_paths=extra_paths, include_dir=include_dir):
            self._sources.append(bib_file)
            for entry in _bib.parse(bib_file):
                key = entry.get("key", "")
                if not key:
                    continue
                dedupe_key = key.lower()
                existing = deduped.get(dedupe_key)
                if existing is None or _entryScore(entry) > _entryScore(existing):
                    deduped[dedupe_key] = dict(entry)
        self._entries = list(deduped.values())
        self._signature = self.scanSignature(dir_path, extra_paths=extra_paths, include_dir=include_dir)
        return self._entries

    def clear(self):
        self._entries = []
        self._sources = []
        self._signature = ()

    def signature(self):
        return self._signature

    def sourceFiles(self):
        return list(self._sources)

    def scanSignature(self, dir_path, extra_paths=None, include_dir=True):
        out = []
        for bib_file in _iterBibPaths(dir_path, extra_paths=extra_paths, include_dir=include_dir):
            try:
                stat = bib_file.stat()
            except OSError:
                continue
            out.append((str(bib_file), stat.st_mtime_ns, stat.st_size))
        return tuple(out)

    def getCompletions(self, prefix):
        pl = prefix.lower()
        exact, starts, contains = [], [], []
        for e in self._entries:
            kl = e["key"].lower()
            desc = _entry_desc(e)
            if kl == pl:
                exact.append((e["key"], desc))
            elif kl.startswith(pl):
                starts.append((e["key"], desc))
            elif pl and pl in kl:
                contains.append((e["key"], desc))
        return exact + starts + contains

    def isEmpty(self):
        return not self._entries

    def entryCount(self):
        return len(self._entries)
