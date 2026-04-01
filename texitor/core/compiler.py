# latex compiler - runs async, streams output, supports latexmk/pdflatex/xelatex/custom
from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path


# default compiler presets - each entry is a format string
# available placeholders: {file} (abs path), {dir} (parent dir), {stem} (no ext), {aux} (aux dir)
PRESETS = {
    "latexmk": "latexmk -pdf -interaction=nonstopmode -aux-directory={aux} {file}",
    "pdflatex": "pdflatex -interaction=nonstopmode -output-directory={dir} -aux-directory={aux} {file}",
    "xelatex":  "xelatex  -interaction=nonstopmode -output-directory={dir} -aux-directory={aux} {file}",
    "lualatex": "lualatex -interaction=nonstopmode -output-directory={dir} -aux-directory={aux} {file}",
}

# some engines don't support -aux-directory (e.g. older texlive pdflatex on linux)
# latexmk handles it internally via -aux-directory flag
# lualatex/xelatex use -output-directory and we put aux alongside

def resolveAuxDir(filePath, auxConfig):
    # returns absolute aux dir path
    # auxConfig can be:
    #   ".aux"    -> relative to file dir  (default - keeps things clean)
    #   "."       -> same dir as file
    #   "/abs/path" -> absolute
    p = Path(filePath)
    aux = Path(auxConfig)
    if aux.is_absolute():
        return aux
    return (p.parent / aux).resolve()


def buildCommand(filePath, engine, auxDir, customCmd=None):
    # build the full shell command string
    p = Path(filePath).resolve()
    fmt = customCmd if customCmd else PRESETS.get(engine, PRESETS["latexmk"])
    return fmt.format(
        file=str(p),
        dir=str(p.parent),
        stem=p.stem,
        aux=str(auxDir),
    )


async def compile(filePath, engine="latexmk", auxConfig=".aux", customCmd=None, onLine=None):
    # async compile - calls onLine(line, is_stderr) for each output line
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
    return proc.returncode, lines


