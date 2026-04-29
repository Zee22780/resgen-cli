from rich.panel import Panel
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static


class HelpScreen(ModalScreen[None]):
    """Simple shortcut overlay for global and screen-level help."""

    BINDINGS = [
        Binding("question_mark", "close_help", "Close"),
        Binding("escape", "close_help", "Close"),
        Binding("q", "close_help", "Close"),
    ]

    def compose(self) -> ComposeResult:
        body = Text()
        body.append("Global Navigation\n", style="bold")
        body.append("d: Dashboard\n")
        body.append("v: Validation\n")
        body.append("e: Export\n")
        body.append("s: Settings\n")
        body.append("q: Quit\n")
        body.append("?: Toggle this help overlay\n\n")
        body.append("Screen Shortcuts\n", style="bold")
        body.append("ctrl+r: Refresh the current workflow screen\n")
        body.append("ctrl+x: Run export from the Export screen\n")
        body.append("enter: Confirm the export path when the path input is focused\n\n")
        body.append("Notes\n", style="bold")
        body.append("The Settings screen never renders secret values, only presence and asset health.")
        yield Static(
            Panel(body, title="Keyboard Help", border_style="blue"),
            id="help-dialog",
        )

    def action_close_help(self) -> None:
        self.app.pop_screen()
