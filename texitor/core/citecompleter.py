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


class CiteCompleter:

    def __init__(self):
        self._entries = []

    def loadDir(self, dir_path, extra_paths=None):
        self._entries = []
        seen = set()
        dirs_to_scan = [Path(dir_path)]

        for bib_path in (extra_paths or []):
            p = Path(bib_path).expanduser()
            if p.is_file():
                if p not in seen:
                    seen.add(p)
                    self._entries.extend(_bib.parse(p))
            elif p.is_dir():
