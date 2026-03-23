# floating search bar widget

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.containers import Container
from textual.widget import Widget
from textual.strip import Strip

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

searchBg = "#313244"
searchFg = "#cdd6f4"
searchPrompt = "#89b4fa"   # blue for /


class SearchBar(Widget):

    DEFAULT_CSS = """
    SearchBar {
        width: 40;
        height: 1;
        dock: top;
    }
    """

    def __init__(self):
        super().__init__()
        self.searchInput = ""
        self.isBackward = False

    def showForward(self):
        self.isBackward = False
        self.searchInput = ""
        self.display = True
        self.refresh()

    def showBackward(self):
        self.isBackward = True
        self.searchInput = ""
        self.display = True
        self.refresh()

    def hide(self):
        self.display = False
        self.searchInput = ""

    def render_line(self, y):
        if y != 0:
            return Strip.blank(self.size.width)

        prompt = "?" if self.isBackward else "/"
        text = Text(no_wrap=True)
        text.append(prompt, style=Style(color=searchPrompt, bold=True, bgcolor=searchBg))
        text.append(self.searchInput, style=Style(color=searchFg, bgcolor=searchBg))
        text.append(" ", style=Style(bgcolor=searchPrompt))  # cursor block

        return Strip(list(text.render(_CONSOLE))).adjust_cell_length(self.size.width)
