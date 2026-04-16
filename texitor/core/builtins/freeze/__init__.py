from __future__ import annotations

import asyncio
import shutil

from texitor.core.plugins import PluginBase
from texitor.core.cmdregistry import registry

from .helpers import buildFreezeCommand, lineRangeArg, parseFreezeArgs, parseLineArg


class FreezePlugin(PluginBase):
    name = "freeze"
    description = "capture code screenshots with the freeze CLI"
    version = "0.1.0"
    author = "benjibrown"
    config_section = "freeze"
    commands = [
        (":freeze [output]", "capture the current file or current visual selection"),
        (":freeze full [output]", "capture the whole file even if a selection is active"),
        (":freeze lines <start,end> [output]", "capture an explicit line range"),
    ]

    def on_load(self, app):
        registry.register(
            ":freeze <args>",
            "capture the current file or current visual selection",
            section="Plugin: freeze",
            aliases=[":freeze"],
            handler=self._cmd_freeze,
        )

    def on_unload(self, app):
        registry.unregisterSection("Plugin: freeze")

    def _settings(self):
        settings = self.config()
        settings.setdefault("executable", "freeze")
        settings.setdefault("config", "")
        settings.setdefault("custom_command", "")
        settings.setdefault("extra_args", [])
        settings.setdefault("show_line_numbers", True)
        return settings

    def _cmd_freeze(self, app, args):
        asyncio.create_task(self._run_freeze(app, args))

    async def _run_freeze(self, app, args):
        ctx = self.context(app)
        file_path = ctx.file_path
        if not file_path:
            self.notify(app, "save the file first before using freeze", severity="warning")
            return

        if ctx.modified:
            self.notify(app, "unsaved changes - freeze uses the last saved version", severity="warning")

        try:
            parsed = parseFreezeArgs(args)
        except ValueError as e:
            self.notify(app, str(e), severity="warning")
            return

        line_arg = ""
        if parsed["mode"] == "lines":
            try:
                parseLineArg(parsed["lines"])
            except ValueError as e:
                self.notify(app, str(e), severity="warning")
                return
            line_arg = parsed["lines"]
        elif parsed["mode"] != "full":
            line_arg = lineRangeArg(ctx.selected_line_range)

        settings = self._settings()

        try:
            cmd, output_path = buildFreezeCommand(
                settings,
                file_path,
                line_arg=line_arg,
                output_override=parsed["output"],
            )
        except Exception as e:
            self.notify(app, f"freeze config error: {e}", severity="error")
            return

        self.open_panel(
            app,
            "freeze",
            [
                ("header", "Freeze screenshot"),
                ("row", "file", file_path),
                ("row", "lines", line_arg or "full file"),
                ("row", "output", str(output_path)),
                ("gap",),
                ("text", "$ " + " ".join(cmd)),
            ],
            footer="  q close",
        )

        if shutil.which(cmd[0]) is None:
            self.append_panel_text(app, f"\nerror: executable not found: {cmd[0]}")
            self.notify(app, f"freeze executable not found: {cmd[0]}", severity="error")
            return

        proc = await asyncio.create_subprocess_exec()
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        while True:
            line = await proc.stdout.readline()
            if not line:
                break
            text = line.decode(errors="replace").rstrip()
            if text:
                self.append_panel_text(app, text)

        rc = await proc.wait()
        if rc == 0:
            self.append_panel_text(app, f"\ncreated {output_path}")
            self.notify(app, f"freeze screenshot saved to {output_path}", timeout=5)
        else:
            self.append_panel_text(app, f"\nfreeze failed with exit {rc}")
            self.notify(app, f"freeze failed (exit {rc})", severity="error")


plugin = FreezePlugin
