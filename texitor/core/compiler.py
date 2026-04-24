# latex compiler - runs async, streams output, supports multiple engines + custom
from __future__ import annotations

import asyncio
import re
import shutil
from dataclasses import dataclass
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
    "latexmk":     "latexmk -pdf      -interaction=nonstopmode -synctex=1 -outdir={dir} -auxdir={aux} {file}",
    "latexmk-lua": "latexmk -lualatex -interaction=nonstopmode -synctex=1 -outdir={dir} -auxdir={aux} {file}",
    "latexmk-xe":  "latexmk -xelatex  -interaction=nonstopmode -synctex=1 -outdir={dir} -auxdir={aux} {file}",

    # direct engines - PDF + aux land in aux dir; PDF copied back to source dir afterward
    "pdflatex": "pdflatex -interaction=nonstopmode -synctex=1 -output-directory={aux} {file}",
    "xelatex":  "xelatex  -interaction=nonstopmode -synctex=1 -output-directory={aux} {file}",
    "lualatex": "lualatex -interaction=nonstopmode -synctex=1 -output-directory={aux} {file}",

    # tectonic - just needs the file; manages its own cache
    "tectonic": "tectonic --synctex {file}",
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


def _buildFormatBits(filePath, auxDir):
    p = Path(filePath).resolve()
    return {
        "file": str(p),
        "dir": str(p.parent),
        "stem": p.stem,
        "aux": str(auxDir),
    }


def _normaliseHookCommands(single, many):
    cmds = []
    if isinstance(single, str) and single.strip():
        cmds.append(single.strip())
    elif isinstance(single, (list, tuple)):
        for cmd in single:
            if isinstance(cmd, str) and cmd.strip():
                cmds.append(cmd.strip())

    if isinstance(many, str) and many.strip():
        cmds.append(many.strip())
    elif isinstance(many, (list, tuple)):
        for cmd in many:
            if isinstance(cmd, str) and cmd.strip():
                cmds.append(cmd.strip())
    return cmds


async def _runShellCommand(cmd, cwd, onLine=None, prefix=None):
    lines = []
    proc = await asyncio.create_subprocess_shell()
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=str(cwd),
    )

    async def readStream(stream, isErr):
        while True:
            raw = await stream.readline()
            if not raw:
                break
            line = raw.decode("utf-8", errors="replace").rstrip("\n\r")
            if prefix:
                line = f"{prefix}{line}"
            lines.append((line, isErr))
            if onLine:
                onLine(line, isErr)

    await asyncio.gather()
        readStream(proc.stdout, False),
        readStream(proc.stderr, True),
    )
    await proc.wait()
    return proc.returncode, lines


async def _runHooks(stage, commands, fmt, cwd, onLine=None):
    # hooks are best-effort on purpose - they should help the build, not hold it hostage
    for raw in commands:
        try:
            cmd = raw.format(**fmt)
        except KeyError as e:
            if onLine:
                onLine(f"[{stage}] warning: unknown placeholder {{{e.args[0]}}} in hook", True)
            continue

        if onLine:
            onLine(f"[{stage}] $ {cmd}", False)
        rc, _ = await _runShellCommand(cmd, cwd, onLine=onLine, prefix=f"[{stage}] ")
        if rc != 0 and onLine:
            onLine(f"[{stage}] warning: command exited {rc}", True)


async def compile(
    filePath,
    engine="latexmk",
    auxConfig=".aux",
    customCmd=None,
    onLine=None,
    preBuildCmd=None,
    postBuildCmd=None,
    preBuildCmds=None,
    postBuildCmds=None,
):
    # async compile; calls onLine(line, is_stderr) for each output line
    # returns (returncode, [output_lines])
    p = Path(filePath).resolve()
    if not p.exists():
        raise FileNotFoundError(f"file not found: {p}")

    auxDir = resolveAuxDir(p, auxConfig)
    auxDir.mkdir(parents=True, exist_ok=True)

    fmt = _buildFormatBits(p, auxDir)
    preHooks = _normaliseHookCommands(preBuildCmd, preBuildCmds)
    postHooks = _normaliseHookCommands(postBuildCmd, postBuildCmds)
    if preHooks:
        await _runHooks("pre-build", preHooks, fmt, p.parent, onLine=onLine)

    cmd = buildCommand(str(p), engine, auxDir, customCmd)
    proc_rc, lines = await _runShellCommand(cmd, p.parent, onLine=onLine)

    # copy PDF + SyncTeX data back to source dir for engines that dump into aux dir
    if proc_rc == 0 and engine in _COPY_PDF_ENGINES:
        copied = []
        for suffix in (".pdf", ".synctex.gz"):
            src = auxDir / (p.stem + suffix)
            dst = p.parent / (p.stem + suffix)
            if src.exists():
                shutil.copy2(str(src), str(dst))
                copied.append(src.name)
        if copied and onLine:
            onLine(f"  → copied {', '.join(copied)} to {p.parent}", False)

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


# parsing all the logs - very peak

@dataclass
class LogEntry:
    level: str          # "error" , "warning"
    message: str
    file: str = ""
    line: int | None = None

# TODO more regex - latex font warning
# matches a file being opened by TeX: (./path/file.tex
_RE_FILE_OPEN = re.compile(r'\(\./?([\w./\-]+\.(?:tex|cls|sty|def|cfg|fd|clo))\b')
# matches l.NN  at start of line (error line number)
_RE_LNUM = re.compile(r'^l\.(\d+)\b')
# matches LaTeX / Package / Class warnings
# TODO - these 4 are still kinda buggy, they work sometimes :(
_RE_WARN = re.compile(r'(?:LaTeX|Package \w[\w@]*|Class \w[\w@]*) Warning:\s*(.*)')
# overfull / underfull boxes
_RE_BOX = re.compile(r'((?:Over|Under)full \\[hv]box.*?) at lines? (\d+)')
_RE_BOX_PARA = re.compile(r'((?:Over|Under)full \\[hv]box.*?) in paragraph at lines? (\d+)')
# "on input line N" suffix in warning messages
_RE_INPUT_LINE = re.compile(r'on input line (\d+)')


def logPath(filePath: str, engine: str, auxConfig: str = ".aux"):
    p   = Path(filePath).resolve()
    stem = p.stem
    if engine == "tectonic":
        return p.parent / f"{stem}.log"
    auxDir = resolveAuxDir(filePath, auxConfig)
    return auxDir / f"{stem}.log"


def parse_log(path: str | Path):
    # parse log file for stuff
    p = Path(path)
    if not p.exists():
        return []
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []

    raw_lines = text.splitlines()
    # TeX wraps long lines at ~80 chars; unwrap them for pattern matching.
    # Guard: never merge lines that start with structural markers.
    _NO_MERGE = ("!", "l.", "Overfull", "Underfull", "LaTeX", "Package", "Class", "(", ")")
    lines: list[str] = []
    for ln in raw_lines:
        if (lines and len(lines[-1]) >= 79
                and not ln.startswith(_NO_MERGE)
                and not lines[-1].startswith("!")):
            lines[-1] += ln
        else:
            lines.append(ln)

    entries: list[LogEntry] = []
    # simple file stack: push on '(' with a .tex/.sty path, pop on ')'
    file_stack: list[str] = []

    def current_file() -> str:
        return file_stack[-1] if file_stack else ""

    i = 0 
    while i < len(lines):
        ln = lines[i]

        # file open / close tracking 
        # skip stack tracking on overfull/underfull lines 
        # stull like (5.12pt too wide) would corrupt 
        if not ln.startswith("Overfull") and not ln.startswith("Underfull"):
            for m in _RE_FILE_OPEN.finditer(ln):
                file_stack.append(m.group(1))
            opens = ln.count("(")
            closes = ln.count(")")
            net = closes - opens 
            for _ in range(net):
                if file_stack:
                    file_stack.pop() # stacks are so peak 

        # errors - lines that begin with ! 
        if ln.startswith("!"):
            msg = ln[1:].strip()
            lnum = None 
            # scan fwd for 1.NN (line number)
            j = i + 1 
            while j < len(lines):
                nxt = lines[j] 
                m = _RE_LNUM.match(nxt)
                if m:
                    lnum = int(m.group(1))
                    j += 1
                    break 
                if nxt.startswith("!") or nxt.startswith("("):
                    break 
                # append non blank cont 
                if nxt.strip and not nxt.startswith("1."):
                    msg += " " + nxt.strip()
                j += 1 
            entries.append(LogEntry("error", msg, current_file(), lnum))
            i = j 
            continue 

        # latex pkg warnings 
        m = _RE_WARN.search(ln)
        if m:
            msg = m.group(1).rstrip(".")
            # multi line warnings 
            j = i + 1
            while j < len(lines) and lines[j].startswith(" ") and lines[j].strip():
                msg += " " + lines[j].strip()
                j += 1 
            lnum_m = _RE_INPUT_LINE.search(msg)
            lnum = int(lnum_m.group(1)) if lnum_m else None 
            entries.append(LogEntry("warning",msg, current_file(), lnum))
            i = j 
            continue 

        # overfull / underful boxes 
        for pat in (_RE_BOX_PARA, _RE_BOX):
            bm = pat.search(ln)
            if bm:
                entries.append(LogEntry("warning", bm.group(1).strip(), current_file(), int(bm.group(2))))
                break 
        i += 1
    return entries


