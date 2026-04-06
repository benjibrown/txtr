# splash screen / landing page - shown when txtr opens with no file argument
# nvim-style: rotating logo, tagline, version, recent files list
# j/k navigate recents, enter opens selected, any other key dismisses

from __future__ import annotations
import random
from typing import TYPE_CHECKING

from rich.console import Console
from rich.style import Style
from rich.text import Text
from textual.strip import Strip
from textual.widget import Widget

if TYPE_CHECKING:
    from texitor.ui.app import TxtrApp

from texitor.core.theme import theme as _t
import texitor.core.recents as _recents

_CONSOLE = Console(width=500, no_color=False, highlight=False, markup=False, emoji=False)

_ACCENT  = Style(color=_t.accent, bold=True)
_DIM     = Style(color=_t.fg_dim)
_SUB     = Style(color=_t.fg_sub)
_SEC     = Style(color=_t.accent2, bold=True)
_FG_SEL  = Style(color=_t.fg, bgcolor=_t.bg_sel, bold=True)
_ACC_SEL = Style(color=_t.accent, bgcolor=_t.bg_sel, bold=True)

_LOGO_A = [
    "  █████                 █████             ",
    " ░░███                 ░░███              ",
    " ███████   █████ █████ ███████   ████████ ",
    "░░░███░   ░░███ ░░███ ░░░███░   ░░███░░███",
    "  ░███     ░░░█████░    ░███     ░███ ░░░ ",
    "  ░███ ███  ███░░░███   ░███ ███ ░███     ",
    "  ░░█████  █████ █████  ░░█████  █████    ",
    "   ░░░░░  ░░░░░ ░░░░░    ░░░░░  ░░░░░    ",
]

_LOGO_B = [
    " _            _      ",
    "| |___  __  _| |_ _ _",
    "| __\\ \\/ /| | __| '_|",
    "|_|  >  < |_|\\__|_|  ",
    "   /_/\\_\\             ",
]

_LOGO_C = [
    "                                                                                    ",
    "                                                                                    ",
    "         tttt                                      tttt                             ",
    "      ttt:::t                                   ttt:::t                             ",
    "      t:::::t                                   t:::::t                             ",
    "      t:::::t                                   t:::::t                             ",
    "ttttttt:::::ttttttt   xxxxxxx      xxxxxxxttttttt:::::ttttttt   rrrrr   rrrrrrrrr   ",
    "t:::::::::::::::::t    x:::::x    x:::::x t:::::::::::::::::t   r::::rrr:::::::::r  ",
    "t:::::::::::::::::t     x:::::x  x:::::x  t:::::::::::::::::t   r:::::::::::::::::r ",
    "tttttt:::::::tttttt      x:::::xx:::::x   tttttt:::::::tttttt   rr::::::rrrrr::::::r",
    "      t:::::t             x::::::::::x          t:::::t          r:::::r     r:::::r",
    "      t:::::t              x::::::::x           t:::::t          r:::::r     rrrrrrr",
    "      t:::::t              x::::::::x           t:::::t          r:::::r            ",
    "      t:::::t    tttttt   x::::::::::x          t:::::t    ttttttr:::::r            ",
    "      t::::::tttt:::::t  x:::::xx:::::x         t::::::tttt:::::tr:::::r            ",
    "      tt::::::::::::::t x:::::x  x:::::x        tt::::::::::::::tr:::::r            ",
    "        tt:::::::::::ttx:::::x    x:::::x         tt:::::::::::ttr:::::r            ",
    "          ttttttttttt xxxxxxx      xxxxxxx          ttttttttttt  rrrrrrr            ",
    "                                                                                    ",
]

_LOGO_D = [
    "     s                      s                 ",
    "    :8                     :8                 ",
    "   .88       uL   ..      .88       .u    .   ",
    "  :888ooo  .@88b  @88R   :888ooo  .d88B :@8c  ",
    "-*8888888 '\"Y888k/\"*P  -*8888888 =\"8888f8888r ",
    "  8888       Y888L       8888      4888>'88\"  ",
    "  8888        8888       8888      4888> '    ",
    "  8888        `888N      8888      4888>      ",
    " .8888Lu=  .u./\"888&    .8888Lu=  .d888L .+   ",
    " ^%888*   d888\" Y888*\"  ^%888*    ^\"8888*\"    ",
    "   'Y\"    ` \"Y   Y\"       'Y\"        \"Y\"      ",
]
_LOGOS = [_LOGO_A, _LOGO_B, _LOGO_C, _LOGO_D]
_VERSION = "v1.9.8" # TODO - fetch from package metadata
_TAGLINE = "LaTeX, fast."
# this is so incredibly peak
# animation modes — picked randomly on launch
_ANIM_STATIC = "static"
_ANIM_TYPEWRITER = "typewriter"
_ANIM_GLITCH = "glitch"

_TYPEWRITER_CPS = 4    # chars revealed per tick (tick = 0.07s)
_GLITCH_CHARS   = "▓░▒▌▐╬╪┼╫▄▀■□▪▫"
_GLITCH_FRAMES  = 42   # frames before glitch settles (~3s)

_TICKER_ITEMS = [
    r"\frac{a}{b}",
    r"\int_0^\infty f(x)\,dx",
    r"\alpha + \beta = \gamma",
    r"\begin{align}",
    r"\nabla \cdot \mathbf{E} = \rho",
    r"\sum_{n=1}^{N} a_n",
    r"\forall x \in \mathbb{R}",
    r"\mathcal{L}(x, \lambda)",
    r"\partial_t u = \Delta u",
    r"\lim_{x \to 0} \frac{\sin x}{x}",
    r"\binom{n}{k} = \frac{n!}{k!(n-k)!}",
    r"\hat{H}\psi = E\psi",
    r"\text{s.t. } Ax \leq b",
    r"\oint_C \mathbf{F} \cdot d\mathbf{r}",
    r"\mathbb{P}(A \mid B)",
    r"\varepsilon \to 0^+",
]
# build a long looping plain string and a parallel list of styles per char
_SEP = "     ·     "

def _build_ticker():
    plain = (_SEP.join(_TICKER_ITEMS) + _SEP) * 3
    return plain

_TICKER_PLAIN = _build_ticker()
_TICKER_LEN = len(_TICKER_PLAIN) // 3  # one full cycle length

_HINTS = [
    ("j/k", "navigate"),
    ("enter", "open"),
    ("e", "new file"),
    (":e", "open file"),
    ("q", "quit"),
]


def _mk_strip(text, width):
    return Strip(list(text.render(_CONSOLE))).adjust_cell_length(width)


class SplashWidget(Widget):

    SCROLLABLE = False

    DEFAULT_CSS = """
    SplashWidget {
        layer: overlay;
        display: none;
        overflow: hidden hidden;
    }
    """

    def __init__(self, app_ref):
        super().__init__()
        self._app_ref = app_ref
        self._recents = []
        self._cursor = 0
        self._logo = random.choice(_LOGOS)
        self._anim_mode = random.choice([_ANIM_STATIC, _ANIM_TYPEWRITER, _ANIM_GLITCH])
        self._frame = 0
        # typewriter: total chars in logo, pre-computed
        self._tw_total = sum(len(line) for line in self._logo)
        # glitch: seeded RNG per frame so glitch is consistent within a frame
        self._glitch_rng = random.Random()

    def on_mount(self):
        self._recents = _recents.load()
        self.set_interval(0.07, self._tick)

    def _tick(self):
        if self.display:
            self._frame = (self._frame + 1) % _TICKER_LEN
            self.refresh()

    def refresh_recents(self):
        self._recents = _recents.load()
        self._cursor = 0
        self.refresh()

    def reposition(self):
        rows = self._content_lines()
        h = len(rows)
        w = max(len(line) for logo in _LOGOS for line in logo) + 4
        screenW = self.app.size.width
        screenH = self.app.size.height
        x = max(0, (screenW - w) // 2)
        y = max(0, (screenH - h) // 2)
        self.styles.width = w
        self.styles.height = h
        self.styles.offset = (x, y)

    def cursor_up(self):
        if self._recents:
            self._cursor = max(0, self._cursor - 1)
            self.refresh()

    def cursor_down(self):
        if self._recents:
            self._cursor = min(len(self._recents) - 1, self._cursor + 1)
            self.refresh()

    def selected_recent(self):
        if self._recents and 0 <= self._cursor < len(self._recents):
            return self._recents[self._cursor]
        return None

    def _content_lines(self):
        rows = []
        for line in self._logo:
            rows.append(("logo", line))
        rows.append(("blank",))
        rows.append(("tagline",))
        rows.append(("version",))
        rows.append(("blank",))
        rows.append(("rec_header",))
        rows.append(("blank_small",))
        if self._recents:
            for i, path in enumerate(self._recents):
                rows.append(("recent", i, path))
        else:
            rows.append(("no_recents",))
        rows.append(("blank",))
        rows.append(("hints",))
        rows.append(("blank_small",))
        rows.append(("ticker",))
        return rows

    def get_content_height(self, container, viewport, width):
        return len(self._content_lines())

    def get_content_width(self, container, viewport):
        return self.size.width if self.size.width else 60

    def _render_row(self, kind, data, width):
        def center(tx):
            raw = len(tx.plain)
            lpad = max(0, (width - raw) // 2)
            full = Text()
            full.append(" " * lpad)
            full.append_text(tx)
            return full

        if kind == "blank" or kind == "blank_small":
            return Text()

        if kind == "logo":
            line_text = data[0]
            if self._anim_mode == _ANIM_TYPEWRITER:
                tx = self._render_logo_typewriter(line_text)
            elif self._anim_mode == _ANIM_GLITCH:
                tx = self._render_logo_glitch(line_text)
            else:
                tx = Text()
                tx.append(line_text, style=_ACCENT)
            return center(tx)
