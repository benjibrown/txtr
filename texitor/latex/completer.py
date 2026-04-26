# latex completion source
# loads commands from commands.toml - user config takes priority over bundled default
# plugins can call registerCommands() to add extra completions at runtime

import tomllib
from pathlib import Path

defaultPath = Path(__file__).parent / "commands.toml"
userPath = Path.home() / ".config" / "txtr" / "commands.toml"


class LatexCompleter:

    def __init__(self):
        self._commands = []  # list of (cmd, desc)

    def load(self, path=None):
        self._commands = []
        data = {}

        # bundled defaults first, then user overrides - same vibe as snippets now
        for target in [defaultPath, Path(path) if path else userPath]:
            if not target.exists():
                continue
            with open(target, "rb") as f:
                loaded = tomllib.load(f)
            for sectionName, section in loaded.items():
                if not isinstance(section, dict):
                    continue
                merged = dict(data.get(sectionName, {}))
                merged.update(section)
                data[sectionName] = merged

        # each section is a category - flatten all into one list
        for section in data.values():
            for cmd, desc in section.items():
                if isinstance(desc, str):
                    self._commands.append((cmd, desc))

    def registerCommands(self, commands):
        # commands: list of (cmd_str, desc_str) - for plugin use
        self._commands.extend(commands)

    def getCompletions(self, prefix):
        # prefix should include the backslash eg "\\fra"
        # returns list of (cmd, desc) ranked: exact > startsWith > contains
        if not prefix.startswith("\\"):
            return []
        prefixLower = prefix.lower()
        exact = []
        startsWith = []
        contains = []
        for cmd, desc in self._commands:
            cmdLower = cmd.lower()
            if cmdLower == prefixLower:
                exact.append((cmd, desc))
            elif cmdLower.startswith(prefixLower):
                startsWith.append((cmd, desc))
            elif prefixLower[1:] in cmdLower[1:]:  # skip backslash for contains
                contains.append((cmd, desc))
        return exact + startsWith + contains
