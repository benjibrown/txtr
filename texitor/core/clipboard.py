# clipboard - system clipboard read/write for txtr
# priority order: macOS pbcopy/pbpaste, Wayland wl-copy/wl-paste, X11 xclip, X11 xsel
# no third party deps - just subprocess calls

import subprocess
import sys


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
