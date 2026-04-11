# wordcount builtin plugin
# shows word count in the statusbar and registers :wordcount command
#
# enable in config:
#   [plugins]
#   enabled = ["wordcount"]
#
# or at runtime:
#   :plugin enable wordcount

from texitor.core.plugins import PluginBase
from texitor.core.cmdregistry import registry
from texitor.core.theme import theme as _theme


class WordCountPlugin(PluginBase):
    name = "wordcount"
    description = "word count in statusbar + :wordcount command"
    version = "1.0.0"
    author = "benji brown (txtr dev)"

    def on_load(self, app):
        registry.register(
            ":wordcount",
            "show word count for current buffer",
            section="Plugins",
            handler=self._cmd_wordcount,
        )
        app.notify("wordcount plugin loaded")

    def on_unload(self, app):
        pass

    def statusbar_segment(self, app):
        try:
            text = "\n".join(app.buffer.lines)
            count = len(text.split())
            return (f"{count}w", _theme.fg_dim)
        except Exception:
            return None

    def _cmd_wordcount(self, app, args):
        try:
            text = "\n".join(app.buffer.lines)
            words = len(text.split())
            chars = len(text.replace("\n", ""))
            lines = len(app.buffer.lines)
            app.notify(f"{words} words  {chars} chars  {lines} lines", timeout=5)
        except Exception as e:
            app.notify(f"wordcount error: {e}", severity="error")


plugin = WordCountPlugin

