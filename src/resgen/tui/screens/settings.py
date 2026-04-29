from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Static

from resgen.services import (
    ConfigStatus,
    ConfigStatusResult,
    get_config_status,
)


class SettingsScreen(Screen[None]):
    """Show safe runtime configuration diagnostics."""

    BINDINGS = [Binding("ctrl+r", "refresh_settings", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical(id="settings-root"):
            yield Header(show_clock=True)
            with Horizontal(id="settings-toolbar"):
                yield Button("Refresh Settings", variant="primary", id="refresh-settings")
                yield Static(id="settings-status")
            with Horizontal(classes="settings-row"):
                yield Static(classes="settings-card", id="settings-paths")
                yield Static(classes="settings-card", id="settings-env")
            with Horizontal(classes="settings-row"):
                yield Static(classes="settings-card", id="settings-assets")
                yield Static(classes="settings-card", id="settings-notes")
            yield Footer()

    def on_mount(self) -> None:
        self.refresh_settings()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-settings":
            self.refresh_settings()

    def action_refresh_settings(self) -> None:
        self.refresh_settings()

    def refresh_settings(self) -> None:
        refresh_button = self.query_one("#refresh-settings", Button)
        refresh_button.loading = True
        self.query_one("#settings-status", Static).update(
            Panel(Text("Checking runtime configuration..."), title="Settings Status", border_style="cyan")
        )

        result = get_config_status()
        refresh_button.loading = False
        if result.error is not None:
            self._render_error_state(result)
            return

        assert result.status is not None
        self._render_status(result.status)
        self._render_paths(result.status)
        self._render_env_vars(result.status)
        self._render_assets(result.status)
        self._render_notes()

    def _render_error_state(self, result: ConfigStatusResult) -> None:
        assert result.error is not None
        error_message = Text(result.error.message, style="bold red")
        self.query_one("#settings-status", Static).update(
            Panel(error_message, title="Settings Error", border_style="red")
        )
        for widget_id, title in (
            ("#settings-paths", "Paths"),
            ("#settings-env", "Environment"),
            ("#settings-assets", "Assets"),
        ):
            self.query_one(widget_id, Static).update(
                Panel(Text("Diagnostics unavailable until the error is resolved."), title=title, border_style="red")
            )
        self._render_notes()

    def _render_status(self, status: ConfigStatus) -> None:
        table = Table.grid(expand=True)
        table.add_column(ratio=1)
        table.add_column(ratio=3)
        table.add_row(
            "State",
            "[green]HEALTHY[/green]" if status.overall_state == "healthy" else "[yellow]ATTENTION[/yellow]",
        )
        table.add_row("Checked", status.checked_at.strftime("%Y-%m-%d %H:%M:%S"))
        table.add_row("Env Vars", str(len(status.env_vars)))
        table.add_row("Assets", str(len(status.assets)))
        self.query_one("#settings-status", Static).update(
            Panel(
                table,
                title="Settings Status",
                border_style="green" if status.overall_state == "healthy" else "yellow",
            )
        )

    def _render_paths(self, status: ConfigStatus) -> None:
        table = Table(expand=True)
        table.add_column("Path", style="bold")
        table.add_column("State", justify="center")
        table.add_column("Location")
        for path_status in status.paths:
            state = "OK" if path_status.exists else ("Unset" if not path_status.configured else "Missing")
            table.add_row(path_status.name, state, path_status.path)
        self.query_one("#settings-paths", Static).update(
            Panel(table, title="Configured Paths", border_style="blue")
        )

    def _render_env_vars(self, status: ConfigStatus) -> None:
        table = Table(expand=True)
        table.add_column("Variable", style="bold")
        table.add_column("Present", justify="center")
        table.add_column("Detail")
        for env_var in status.env_vars:
            table.add_row(
                env_var.name,
                "Yes" if env_var.present else "No",
                env_var.detail,
            )
        self.query_one("#settings-env", Static).update(
            Panel(table, title="Secret Presence", border_style="blue")
        )

    def _render_assets(self, status: ConfigStatus) -> None:
        table = Table(expand=True)
        table.add_column("Asset", style="bold")
        table.add_column("Available", justify="center")
        table.add_column("Detail")
        for asset in status.assets:
            table.add_row(
                asset.name,
                "Yes" if asset.available else "No",
                asset.detail,
            )
        self.query_one("#settings-assets", Static).update(
            Panel(table, title="Template & PDF Assets", border_style="blue")
        )

    def _render_notes(self) -> None:
        body = Text()
        body.append("Settings Notes\n", style="bold")
        body.append("Secret values are never shown here.\n")
        body.append("Use ctrl+r or the refresh button to re-check paths, env vars, and assets.\n")
        body.append("Missing WeasyPrint means PDF export will fail even if Markdown and HTML are healthy.")
        self.query_one("#settings-notes", Static).update(
            Panel(body, title="Notes", border_style="blue")
        )
