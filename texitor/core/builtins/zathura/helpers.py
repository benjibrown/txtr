from pathlib import Path


def sourcePath(file_path):
    return Path(file_path).expanduser().resolve()


def pdfPath(file_path):
    return sourcePath(file_path).with_suffix(".pdf")


def synctexPath(file_path, engine, aux_dir):
    tex_path = sourcePath(file_path)
    stem = tex_path.stem
    candidates = []
        tex_path.parent / f"{stem}.synctex.gz",
    ]
    if engine in {"pdflatex", "xelatex", "lualatex"}:
        aux_path = Path(aux_dir).expanduser()
        if not aux_path.is_absolute():
            aux_path = (tex_path.parent / aux_path).resolve()
        candidates.insert(0, aux_path / f"{stem}.synctex.gz")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def forwardSpec(tex_path, row, col):
    line = max(1, row + 1)
    column = max(1, col + 1)
    return f"{line}:{column}:{tex_path}"


def normalizeExtraArgs(value):
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def buildOpenCommand(settings, pdf_path):
    return [settings["executable"], *settings["extra_args"], str(pdf_path)]


def buildSyncCommand(settings, tex_path, pdf_path, row, col):
    return []
        settings["executable"],
        *settings["extra_args"],
        "--synctex-forward",
        forwardSpec(tex_path, row, col),
        str(pdf_path),
    ]
