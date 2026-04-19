from texitor.core.cmdregistry import command
from texitor.core.keybinds import USER_KEYBINDS_PATH

# commands.py is too long sooo
class KeybindCommandsMixin:
    @command(":keybinds reload", "reload custom keybinds.toml", section="Config")
    def _cmd_keybindsReload(self, args):
        self._reloadUserKeybinds(notify=True)

    @command(":keybinds path", "show the custom keybinds.toml path", section="Config")
    def _cmd_keybindsPath(self, args):
        self.notify(str(USER_KEYBINDS_PATH))

