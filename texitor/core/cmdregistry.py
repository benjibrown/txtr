# command registry - central place where all : commands register themselves
# the help menu reads from here so it always reflects reality
# plugins use the same api - no need to touch helpmenu.py
#
# usage:
#   from texitor.core.cmdregistry import registry
#   registry.register("w", "save file", section="File")
#   registry.register("build <engine>", "build with specific engine", section="Compiler", aliases=["compile", "b"])
#
# the registry stores entries in insertion order within each section
# sections appear in the order they first receive an entry

from __future__ import annotations
from collections import OrderedDict


class CommandRegistry:

    def __init__(self):
        # sections: OrderedDict of section_name -> list of (syntax, description)
        self._sections = OrderedDict()

    def register(self, syntax, description, section="General", aliases=None):
        # register a command with optional aliases shown as "cmd / alias1 / alias2"
        if section not in self._sections:
            self._sections[section] = []
        if aliases:
            display = syntax + "  /  " + "  /  ".join(aliases)
        else:
            display = syntax
        self._sections[section].append((display, description))

    def registerSection(self, section, entries):
        # bulk register a list of (syntax, description) tuples under a section
        # entries: list of (syntax, description) or (syntax, description, [aliases])
        for entry in entries:
            if len(entry) == 3:
                syntax, description, aliases = entry
            else:
                syntax, description = entry
                aliases = None
            self.register(syntax, description, section=section, aliases=aliases)

    def sections(self):
        # returns list of (section_name, [(syntax, description), ...])
        return list(self._sections.items())

    def allCommands(self):
        # flat list of (syntax, description) across all sections
        out = []
        for entries in self._sections.values():
            out.extend(entries)
        return out


# singleton - import this everywhere
registry = CommandRegistry()


# register all built-in commands up front so the registry is populated at import time
# order within each section = order they appear in help menu

registry.registerSection("File", [
    (":w",                  "save file"),
    (":w <file>",           "save as file"),
    (":wq",                 "save and quit",            [":x"]),
    (":q",                  "quit (fails if unsaved)"),
    (":q!",                 "force quit"),
    (":e <file>",           "open file"),
])

registry.registerSection("View", [
    (":help",               "open help menu",           [":h"]),
    (":snippets",           "open snippets tab",        [":snips"]),
    (":config",             "open config panel",        [":config show"]),
])

registry.registerSection("Config", [
    (":config set <section.key> <value>", "set a config value"),
    (":config get <section.key>",         "print a config value"),
])

registry.registerSection("Compiler", [
    (":build",          "build with configured engine",          [":compile", ":b"]),
    (":build <engine>", "build with specific engine (overrides config)"),
    (":clean",          "delete aux dir contents (.log, .aux, etc.)"),
    (":buildlog",       "reopen last build output panel"),
    (":buildstop",      "cancel running build"),
    (":engines",        "list available engines and current setting", [":compilers"]),
])


