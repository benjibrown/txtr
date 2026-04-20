# clipboard - system clipboard read/write for txtr
# v. peak but needs pbcopy or wl-copy or xclip 

import subprocess
import sys
from pathlib import Path


def _run(cmd, input=None):
    try:
        result = subprocess.run(
            cmd,
            input=input,
            capture_output=True,
            timeout=2,
        )
        return result.returncode == 0, result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False, b""


def copyToSystem(text):
    # write text to system clipboard - non-blocking via Popen so it never stalls the editor
    data = text.encode()

    # pbcopy is macOS native - try it first on darwin, fall through on other platforms
    if sys.platform == "darwin":
        try:
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            proc.stdin.write(data)
            proc.stdin.close()
            return
        except FileNotFoundError:
            pass

    for cmd in (
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
    ):
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            proc.stdin.write(data)
            proc.stdin.close()
            return
        except FileNotFoundError:
            continue


def pasteFromSystem():
    # read text from system clipboard
    if sys.platform == "darwin":
        ok, out = _run(["pbpaste"])
        if ok:
            return out.decode(errors="replace")

    ok, out = _run(["wl-paste", "--no-newline"])
    if ok: return out.decode(errors="replace")

    ok, out = _run(["xclip", "-selection", "clipboard", "-o"])
    if ok: return out.decode(errors="replace")

    ok, out = _run(["xsel", "--clipboard", "--output"])
    if ok: return out.decode(errors="replace")

    return ""

# added this just for the freeze plugin btw
def copyImageToSystem(path):
    p = Path(path).expanduser()
    try:
        data = p.read_bytes()
    except OSError:
        return False

    ext = p.suffix.lower()
    mime = {
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".svg": "image/svg+xml",
    }.get(ext, "application/octet-stream")

    if sys.platform == "darwin":
        try:
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            proc.stdin.write(data)
            proc.stdin.close()
            return True
        except FileNotFoundError:
            pass

    for cmd in (
        ["wl-copy", "--type", mime],
        ["xclip", "-selection", "clipboard", "-t", mime, "-i"],
    ):
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
            proc.stdin.write(data)
            proc.stdin.close()
            return True
        except FileNotFoundError:
            continue
    return False
