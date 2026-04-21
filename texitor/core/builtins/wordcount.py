import re
from texitor.core.plugins import PluginBase
from texitor.core.cmdregistry import registry
from texitor.core.theme import theme as _theme

# I HATE REGEX
_COMMENT_RE = re.compile(r"(?<!\\)%.*$")
_COMMAND_ARG_RE = re.compile(r"\\[a-zA-Z]+\*?\s*(?:\[[^\]]*\])?")
_BEGIN_END_RE = re.compile(r"\\(?:begin|end)\{[^}]+\}")
_INLINE_MATH_RE = re.compile(r"\$\$.*?\$\$|\$[^$\n]*?\$", re.DOTALL)
_DISPLAY_MATH_RE = re.compile(r"\\\[(.*?)\\\]", re.DOTALL)
_WORD_RE = re.compile(r"[A-Za-z0-9]+(?:['’-][A-Za-z0-9]+)*")


def _stripLatex(text, count_math=False):
    lines = []
    for raw in text.splitlines():
        lines.append(_COMMENT_RE.sub("", raw))
    text = "\n".join(lines)
    if not count_math:
        text = _INLINE_MATH_RE.sub(" ", text)
        text = _DISPLAY_MATH_RE.sub(" ", text)
    text = _BEGIN_END_RE.sub(" ", text)
    text = _COMMAND_ARG_RE.sub(" ", text)
    text = text.replace("\\", " ")
    text = text.translate(str.maketrans({
        "{": " ",
        "}": " ",
        "[": " ",
        "]": " ",
        "&": " ",
        "_": " ",
        "^": " ",
        "~": " ",
    }))
    return re.sub(r"\s+", " ", text).strip()


def _latexWordStats(text, count_math=False):
    plain = _stripLatex(text, count_math=count_math)
    words = _WORD_RE.findall(plain)
    return {
        "words": len(words),
        "chars": len(plain.replace(" ", "")),
        "lines": len(text.splitlines()) or 1,
    }


class WordCountPlugin(PluginBase):
    name = "wordcount"
    description = "latex-aware word count in statusbar + :wordcount command"
    version = "1.1.0"
    author = "benji brown (txtr dev)"
    commands = [
        (":wordcount", "show word count for current buffer"),
    ]
    config_options = [
        {"key": "statusbar", "default": True, "description": "show the current word count in the statusbar"},
        {"key": "count_math", "default": False, "description": "include math regions in the word count instead of ignoring them"},
    ]

    def on_load(self, app):
        registry.register(
            ":wordcount",
            "show word count for current buffer",
            section="Plugin: wordcount",
            handler=self._cmd_wordcount,
        )

    def on_unload(self, app):
        registry.unregisterSection("Plugin: wordcount")

    def statusbar_segment(self, app):
        try:
            if not self.config("statusbar", True):
                return None
            stats = _latexWordStats("\n".join(app.buffer.lines), count_math=self.config("count_math", False))
            return (f"{stats['words']}w", _theme.fg_dim)
        except Exception:
            return None

    def _cmd_wordcount(self, app, args):
        try:
            text = "\n".join(self.context(app).selected_lines or app.buffer.lines)
            stats = _latexWordStats(text, count_math=self.config("count_math", False))
            # just for you aditya - smh
            plural = "word" if int(stats['words']) == 1 else "words"
            charsp = "char" if int(stats['chars']) == 1 else "chars"
            linesp = "line" if int(stats['lines']) == 1 else "lines"
            self.notify(app, f"{stats['words']} {plural}  {stats['chars']} {charsp} {stats['lines']} {linesp}", timeout=5)
        except Exception as e:
            self.notify(app, f"wordcount error: {e}", severity="error")


plugin = WordCountPlugin
