# txtr app package
# TxtrApp is the main application class.
# ActionsMixin  — all _action_* handler methods (actions.py)
# CommandsMixin — _action_execute_command, _cmd_* methods (commands.py)
from __future__ import annotations

from textual.app import App, ComposeResult
from textual.events import Key

from texitor.core.buffer import Buffer
from texitor.core.keybinds import KeybindRegistry
from texitor.core.modes import Mode, ModeStateMachine
from texitor.core.firstrun import ensureUserConfig
from texitor.core.config import config as cfg
from texitor.core.clipboard import copyToSystem, pasteFromSystem
from texitor.core.theme import theme as _theme, getStartupWarning
from texitor.ui.editor import EditorWidget
from texitor.ui.statusbar import StatusBar
from texitor.ui.autocomplete import AutocompleteWidget
from texitor.ui.helpmenu import HelpMenu
from texitor.ui.configpanel import ConfigPanel
from texitor.ui.buildpanel import BuildPanel
import texitor.core.compiler as _compiler
from texitor.latex.snippets import SnippetManager
from texitor.latex.completer import LatexCompleter

from texitor.ui.app.actions import ActionsMixin
from texitor.ui.app.commands import CommandsMixin
