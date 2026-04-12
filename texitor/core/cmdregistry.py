# command registry - central place where all : commands register themselves
# the help menu reads from here so it always reflects reality
# plugins use the same api to add commands - no changes to main code needed. - plugins are still a big TODO but this is one piece of the puzzle
#
# dispatch model:
#   each command has one or more "triggers" - exact strings or prefix patterns.
#   a trigger ending in " <...>" is a prefix trigger: matches anything starting
#   with the part before " <". plain triggers match exact strings only.
#
# plugin usage [wip]
#   from texitor.core.cmdregistry import registry
#   registry.register("mycommand", "does x", section="MyPlugin",
#                     aliases=["mc"], handler=lambda app, args: app.notify(args))
## this is how it will work eventually - plugins are not implemented yet but some of the stuff is there :)
#
# built-in commands are registered at module level with handler=None.
# handlers are bound to the app instance at runtime via bindHandlers(app).

from __future__ import annotations
from collections import OrderedDict
from typing import Callable, Optional


class CommandRegistry:

    def __init__(self):
        self._sections: OrderedDict[str, list] = OrderedDict()
        self._dispatch: dict[str, "_CmdEntry"] = {}

    def register(self, syntax: str, description: str, section: str = "General",
                 aliases: list[str] | None = None, handler: Callable | None = None):
        # syntax - form shown in help, e.g. ":build <engine>"
        # description - one-line description for help menu
        # section - section grouping in help menu
        # aliases - list of alternative trigger strings
        # handler - callable(app, args: str) or None (bound later via bindHandlers)
        # args is everything typed after the trigger word(s)
        if section not in self._sections:
            self._sections[section] = []

        triggers = [_stripLeadingColon(syntax)]
        if aliases:
            triggers += [_stripLeadingColon(a) for a in aliases]

        entry = _CmdEntry(syntax, description, triggers, handler)
        self._sections[section].append(entry)

        for t in triggers:
            key = t.split(" <")[0].strip()
            self._dispatch[key] = entry

    def registerSection(self, section: str, entries):
        # bulk-register from a list of tuples:
        # (syntax, desc) or (syntax, desc, aliases) or (syntax, desc, aliases, handler)
        for entry in entries:
            syntax = entry[0]
            description = entry[1]
            aliases = entry[2] if len(entry) > 2 else None
            handler = entry[3] if len(entry) > 3 else None
            self.register(syntax, description, section=section, aliases=aliases, handler=handler)

    def unregisterSection(self, section: str):
        entries = self._sections.pop(section, [])
        if not entries:
            return
        for entry in entries:
            for t in entry.triggers:
                key = t.split(" <")[0].strip()
                if self._dispatch.get(key) is entry:
                    self._dispatch.pop(key, None)

    def bindHandlers(self, app):
        # called once on app mount - wires up handlers to bound app methods
        for entry in self._allEntries():
            if entry.handler is None and entry._method_name:
                m = getattr(app, entry._method_name, None)
                if m:
                    entry.handler = m

    def dispatch(self, app, raw: str) -> bool:
        # parse raw typed command and call the matching handler.
        # returns True if handled, False if unknown.
        raw = raw.strip()
        parts = raw.split()
        for length in range(len(parts), 0, -1):
            key = " ".join(parts[:length])
            entry = self._dispatch.get(key)
            if entry and entry.handler:
                args = raw[len(key):].strip()
                entry.handler(app, args)
                return True
        return False

    def sections(self):
        # returns list of (section_name, [(display_syntax, description), ...]) for the help menu
        out = []
        for name, entries in self._sections.items():
            out.append((name, [(e.display, e.description) for e in entries]))
        return out

    def allCommands(self):
        # flat list of (display_syntax, description) across all sections
        return [(e.display, e.description) for e in self._allEntries()]

    def _allEntries(self):
        for entries in self._sections.values():
            yield from entries


class _CmdEntry:
    __slots__ = ("syntax", "description", "triggers", "handler", "display", "_method_name")

    def __init__(self, syntax, description, triggers, handler):
        self.syntax = syntax
        self.description = description
        self.triggers = triggers
        self.handler = handler
        self._method_name: str | None = None
        self.display = "  /  ".join(
            (":" if not t.startswith(":") else "") + t for t in triggers
        )


def _stripLeadingColon(s: str) -> str:
    return s.lstrip(":")


_cmd_counter = 0  # incremented each time @command is applied, preserves definition order


def command(syntax: str, description: str, section: str = "General",
            aliases: list[str] | None = None):
    # decorator for _cmd_* methods on CommandsMixin.
    # marks the method with metadata so _registerCommands() can wire it up at mount.
    # decorated method signature: def _cmd_foo(self, app, args: str)
    #
    # example:
    #   @command(":build", "build with configured engine",
    #            section="Compiler", aliases=[":compile", ":b"])
    #   def _cmd_build(self, app, args):
    #       engine = args or None
    #       ...
    def decorator(fn):
        global _cmd_counter
        _cmd_counter += 1
        fn._cmd_meta = {
            "syntax": syntax,
            "description": description,
            "section": section,
            "aliases": aliases or [],
            "order": _cmd_counter,
        }
        return fn
    return decorator


# singleton
registry = CommandRegistry()

