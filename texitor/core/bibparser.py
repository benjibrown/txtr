# minimal .bib parser - extracts key, type, title, author, year from bibtex files
# handles nested braces in field values, both {val} and "val" syntax

import re
from pathlib import Path

_ENTRY_START = re.compile(r'@(\w+)\s*\{\s*([^,\s]+)\s*,', re.IGNORECASE)
_FIELD = re.compile(
    r'(\w+)\s*=\s*'
    r'(?:\{((?:[^{}]|\{[^{}]*\})*)\}'   # {value} or {nested {braces}})'
    r'|"([^"]*)"'                         # "value"
    r'|(\d+))',                            # bare number (year)
    re.IGNORECASE | re.DOTALL
)


def parse(path):
    entries = []
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return entries

    for m in _ENTRY_START.finditer(text):
        entry_type = m.group(1).lower()
        key = m.group(2)

        # find matching closing brace for this entry
        start = m.end()
        depth = 1
        i = start
        while i < len(text) and depth > 0:
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
            i += 1
        body = text[start : i - 1]

        fields = {}
        for fm in _FIELD.finditer(body):
            name = fm.group(1).lower()
            val = fm.group(2) or fm.group(3) or fm.group(4) or ""
            fields[name] = val.strip()

        entries.append({
            "key": key,
            "type": entry_type,
            "title": fields.get("title", ""),
            "author": fields.get("author", ""),
            "year": fields.get("year", ""),
        })

    return entries
