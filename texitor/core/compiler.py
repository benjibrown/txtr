# latex compiler - runs async, streams output, supports multiple engines + custom
from __future__ import annotations

import asyncio
import shutil
from pathlib import Path


# engine presets
# notes on flags:
#   latexmk   - best choice; -outdir/-auxdir separate PDF from aux on TexLive
#   pdflatex  - no -aux-directory on TexLive; -output-directory puts PDF+aux together
#               we direct output to aux dir then copy PDF back to source dir
#   xelatex   - same limitation as pdflatex; same workaround
#   lualatex  - same limitation; via latexmk-lua is cleaner
#   latexmk-lua  - latexmk driving lualatex; gets proper outdir/auxdir separation
#   latexmk-xe   - latexmk driving xelatex; same
#   tectonic  - modern self-contained engine; auto-downloads packages; no aux mess
#
# placeholders: {file} abs path, {dir} source dir, {stem} no extension, {aux} aux dir

PRESETS = {
    # latexmk variants (recommended - proper outdir/auxdir support)
    "latexmk":     "latexmk -pdf      -interaction=nonstopmode -outdir={dir} -auxdir={aux} {file}",
    "latexmk-lua": "latexmk -lualatex -interaction=nonstopmode -outdir={dir} -auxdir={aux} {file}",
    "latexmk-xe":  "latexmk -xelatex  -interaction=nonstopmode -outdir={dir} -auxdir={aux} {file}",

    # direct engines - PDF + aux land in aux dir; PDF copied back to source dir afterward
    "pdflatex": "pdflatex -interaction=nonstopmode -output-directory={aux} {file}",
    "xelatex":  "xelatex  -interaction=nonstopmode -output-directory={aux} {file}",
    "lualatex": "lualatex -interaction=nonstopmode -output-directory={aux} {file}",

    # tectonic - just needs the file; manages its own cache
    "tectonic": "tectonic {file}",
}

# engines that dump everything into aux and need PDF copied back
_COPY_PDF_ENGINES = {"pdflatex", "xelatex", "lualatex"}

# human-readable descriptions shown in help menu
ENGINE_DESCRIPTIONS = {
    "latexmk":     "latexmk driving pdflatex (recommended)",
    "latexmk-lua": "latexmk driving lualatex",
    "latexmk-xe":  "latexmk driving xelatex",
    "pdflatex":    "pdflatex direct",
    "xelatex":     "xelatex direct",
    "lualatex":    "lualatex direct",
    "tectonic":    "tectonic (modern, auto-downloads packages)",
}


def resolveAuxDir(filePath, auxConfig):
    # resolve aux dir relative to file or as absolute path
    p = Path(filePath)
    aux = Path(auxConfig)
    if aux.is_absolute():
        return aux
    return (p.parent / aux).resolve()


def buildCommand(filePath, engine, auxDir, customCmd=None):
    p = Path(filePath).resolve()
    fmt = customCmd if customCmd else PRESETS.get(engine, PRESETS["latexmk"])
    return fmt.format(
        file=str(p),
        dir=str(p.parent),
        stem=p.stem,
        aux=str(auxDir),
    )


async def compile(filePath, engine="latexmk", auxConfig=".aux", customCmd=None, onLine=None):
    # async compile; calls onLine(line, is_stderr) for each output line
    # returns (returncode, [output_lines])
    p = Path(filePath).resolve()
    if not p.exists():
        raise FileNotFoundError(f"file not found: {p}")

    auxDir = resolveAuxDir(p, auxConfig)
    auxDir.mkdir(parents=True, exist_ok=True)

    cmd = buildCommand(str(p), engine, auxDir, customCmd)
    lines = []

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(p.parent),
    )

    async def readStream(stream, isErr):
        while True:
            raw = await stream.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\n\r")
            lines.append((line, isErr))
            if onLine:
                onLine(line, isErr)

    await asyncio.gather(
        readStream(proc.stdout, False),
        readStream(proc.stderr, True),
    )
    await proc.wait()

    # copy PDF back to source dir for engines that dump into aux dir
    if proc.returncode == 0 and engine in _COPY_PDF_ENGINES:
        src = auxDir / (p.stem + ".pdf")
        dst = p.parent / (p.stem + ".pdf")
        if src.exists():
            shutil.copy2(str(src), str(dst))
            if onLine:
                onLine(f"  → copied {src.name} to {dst.parent}", False)

    return proc.returncode, lines


def cleanAuxDir(filePath, auxConfig=".aux"):
    # delete all files in the aux dir, keep the dir itself
    auxDir = resolveAuxDir(filePath, auxConfig)
    if not auxDir.exists():
        return 0
    count = 0
    for f in auxDir.iterdir():
        if f.is_file():
            f.unlink()
            count += 1
        elif f.is_dir():
            shutil.rmtree(f)
            count += 1
    return count

