# clipboard - system clipboard read/write for txtr
# tries wl-copy/wl-paste (wayland) first, then xclip, then xsel
# no third party deps - just subprocess calls
#
# TODO: add windows support (win32clipboard or ctypes) if ever needed
# TODO: add macOS support (pbcopy/pbpaste) - easy addition

import subprocess


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
    # write text to system clipboard - tries wayland then x11
    # uses Popen (non-blocking) so it doesn't stall the editor
    data = text.encode()
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
    # read text from system clipboard - tries wayland then x11
    ok, out = _run(["wl-paste", "--no-newline"])
    if ok: return out.decode(errors="replace")

    ok, out = _run(["xclip", "-selection", "clipboard", "-o"])
    if ok: return out.decode(errors="replace")

    ok, out = _run(["xsel", "--clipboard", "--output"])
    if ok: return out.decode(errors="replace")

    return ""
