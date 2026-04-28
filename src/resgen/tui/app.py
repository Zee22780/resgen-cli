from textual.app import App
from textual.binding import Binding

from .screens.dashboard import DashboardScreen
from .screens.validation import ValidationScreen


class ResgenTuiApp(App[None]):
    """Textual shell for browsing resume workflows."""

    TITLE = "resgen-cli"
    SUB_TITLE = "Dashboard"
    CSS = """
    Screen {
        background: $surface;
    }

    #dashboard-root {
        padding: 1 2;
    }

    .dashboard-row {
        height: auto;
        margin: 0 0 1 0;
    }

    .card {
        width: 1fr;
        min-height: 9;
        margin-right: 1;
    }

    .card:last-child {
        margin-right: 0;
    }

    #section-counts {
        height: 1fr;
    }

    #validation-root {
        padding: 1 2;
    }

    #validation-toolbar {
        height: auto;
        margin: 0 0 1 0;
    }

    #validation-status {
        width: 1fr;
        margin-left: 1;
    }

    #validation-results {
        height: 1fr;
    }

    #validation-issues {
        width: 38;
        margin-right: 1;
    }

    #validation-detail {
        width: 1fr;
    }
    """
    BINDINGS = [
        Binding("d", "show_dashboard", "Dashboard"),
        Binding("r", "show_resume_summary", "Resume"),
        Binding("v", "show_validation", "Validation"),
        Binding("e", "show_export", "Export"),
        Binding("s", "show_settings", "Settings"),
        Binding("question_mark", "toggle_help", "Help"),
        Binding("q", "quit", "Quit"),
    ]

    def on_mount(self) -> None:
        self.install_screen(DashboardScreen(), name="dashboard")
        self.install_screen(ValidationScreen(), name="validation")
        self.sub_title = "Dashboard"
        self.push_screen("dashboard")

    def action_show_dashboard(self) -> None:
        self._show_screen("dashboard", "Dashboard")

    def action_show_resume_summary(self) -> None:
        self.notify("Resume Summary is planned for a later phase.")

    def action_show_validation(self) -> None:
        self._show_screen("validation", "Validation")

    def action_show_export(self) -> None:
        self.notify("Export flow is planned for a later phase.")

    def action_show_settings(self) -> None:
        self.notify("Settings screen is planned for a later phase.")

    def action_toggle_help(self) -> None:
        self.notify("Use d, r, v, e, s, q, and ? for navigation.")

    def _show_screen(self, screen_name: str, subtitle: str) -> None:
        self.sub_title = subtitle
        self.switch_screen(screen_name)
