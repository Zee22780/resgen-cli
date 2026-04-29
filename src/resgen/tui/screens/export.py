from __future__ import annotations

from pathlib import Path

from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, RadioButton, RadioSet, Static

from resgen.services import (
    ExportArtifact,
    ExportResult,
    get_default_export_path,
    run_resume_export,
)


class ExportScreen(Screen[None]):
    """Run exports in-app with explicit path confirmation."""

    BINDINGS = [
        Binding("ctrl+r", "confirm_path", "Confirm Path"),
        Binding("ctrl+x", "run_export", "Export"),
    ]

    FORMAT_OPTIONS = {
        "format-md": "md",
        "format-html": "html",
        "format-pdf": "pdf",
    }

    def __init__(self) -> None:
        super().__init__()
        self._selected_format = "md"
        self._confirmed_output_path: Path | None = None
        self._last_seeded_output = str(get_default_export_path("md"))
        self._latest_result: ExportResult | None = None
        self._log_lines: list[str] = []
        self._suppress_path_change = False

    def compose(self) -> ComposeResult:
        with Vertical(id="export-root"):
            yield Header(show_clock=True)
            with Horizontal(id="export-toolbar"):
                yield RadioSet(
                    RadioButton("Markdown (.md)", value=True, id="format-md"),
                    RadioButton("HTML (.html)", id="format-html"),
                    RadioButton("PDF (.pdf)", id="format-pdf"),
                    id="export-formats",
                )
                with Vertical(id="export-controls"):
                    yield Input(
                        value=self._last_seeded_output,
                        placeholder="Output path",
                        id="export-path",
                    )
                    with Horizontal(classes="export-actions"):
                        yield Button("Confirm Path", id="confirm-path")
                        yield Button(
                            "Export Resume",
                            variant="primary",
                            id="run-export",
                            disabled=True,
                        )
            yield Static(id="export-note")
            yield Static(id="export-status")
            yield Static(id="export-log")
            yield Footer()

    def on_mount(self) -> None:
        self._render_note()
        self._render_status()
        self._render_log()

    def action_confirm_path(self) -> None:
        path_input = self.query_one("#export-path", Input)
        self._confirm_output_path(path_input.value)

    def action_run_export(self) -> None:
        self._run_export()

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        if event.radio_set.id != "export-formats":
            return

        format_name = self.FORMAT_OPTIONS.get(event.pressed.id or "")
        if format_name is None:
            return

        path_input = self.query_one("#export-path", Input)
        previous_default = self._last_seeded_output
        self._selected_format = format_name

        if path_input.value.strip() == previous_default:
            next_default = str(get_default_export_path(format_name))
            self._last_seeded_output = next_default
            self._suppress_path_change = True
            path_input.value = next_default
            self._suppress_path_change = False

        self._confirmed_output_path = None
        self._latest_result = None
        self.query_one("#run-export", Button).disabled = True
        self._render_note()
        self._render_status()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id != "export-path":
            return

        if self._suppress_path_change:
            return

        self._confirmed_output_path = None
        self._latest_result = None
        self.query_one("#run-export", Button).disabled = True
        self._render_status()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "export-path":
            self._confirm_output_path(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "confirm-path":
            self.action_confirm_path()
        elif event.button.id == "run-export":
            self.action_run_export()

    def _confirm_output_path(self, raw_value: str) -> None:
        normalized_value = raw_value.strip()
        if not normalized_value:
            self._latest_result = None
            self._append_log("Path confirmation failed: output path cannot be empty.")
            self._render_status(error_message="Output path cannot be empty.")
            return

        confirmed_path = Path(normalized_value).expanduser()
        self._confirmed_output_path = confirmed_path
        self._latest_result = None
        self.query_one("#run-export", Button).disabled = False
        self._append_log(f"Path confirmed for {self._selected_format.upper()}: {confirmed_path}")
        self._render_status()

    def _run_export(self) -> None:
        if self._confirmed_output_path is None:
            self._render_status(error_message="Confirm an output path before exporting.")
            return

        run_button = self.query_one("#run-export", Button)
        self.query_one("#confirm-path", Button).disabled = True
        run_button.disabled = True
        run_button.loading = True
        self._render_status(in_progress=True)

        result = run_resume_export(self._selected_format, self._confirmed_output_path)
        self._latest_result = result

        self.query_one("#confirm-path", Button).disabled = False
        run_button.loading = False
        if result.artifact is not None:
            self._suppress_path_change = True
            self.query_one("#export-path", Input).value = str(result.artifact.output_path)
            self._suppress_path_change = False
            self._confirmed_output_path = result.artifact.output_path
            run_button.disabled = False
            self._append_log(self._format_success_log(result.artifact))
            self._render_status()
            return

        run_button.disabled = False
        self._append_log(self._format_error_log(result))
        self._render_status()

    def _render_note(self) -> None:
        notes = {
            "md": "Markdown export writes the portfolio-oriented template for sharing or git-based review.",
            "html": "HTML export writes the themed web version and can act as the PDF source artifact.",
            "pdf": "PDF export depends on WeasyPrint. Confirm the target path before exporting to avoid shell fallback.",
        }
        self.query_one("#export-note", Static).update(
            Panel(Text(notes[self._selected_format]), title="Format Notes", border_style="blue")
        )

    def _render_status(
        self,
        *,
        in_progress: bool = False,
        error_message: str | None = None,
    ) -> None:
        status_table = Table.grid(expand=True)
        status_table.add_column(ratio=1)
        status_table.add_column(ratio=3)
        output_value = (
            str(self._confirmed_output_path)
            if self._confirmed_output_path is not None
            else self.query_one("#export-path", Input).value.strip() or "Not set"
        )

        if in_progress:
            state = "[cyan]EXPORTING[/cyan]"
            border_style = "cyan"
        elif error_message is not None:
            state = "[red]ACTION REQUIRED[/red]"
            border_style = "red"
        elif self._latest_result is not None and self._latest_result.artifact is not None:
            state = "[green]SUCCESS[/green]"
            border_style = "green"
        elif self._latest_result is not None and self._latest_result.error is not None:
            state = "[red]FAILED[/red]"
            border_style = "red"
        elif self._confirmed_output_path is not None:
            state = "[yellow]PATH CONFIRMED[/yellow]"
            border_style = "yellow"
        else:
            state = "[yellow]PATH UNCONFIRMED[/yellow]"
            border_style = "yellow"

        status_table.add_row("Format", self._selected_format.upper())
        status_table.add_row("Output", output_value)
        status_table.add_row(
            "Path State",
            "Confirmed" if self._confirmed_output_path is not None else "Waiting for confirmation",
        )
        status_table.add_row("Status", state)

        if error_message is not None:
            status_table.add_row("Details", error_message)
        elif self._latest_result is not None and self._latest_result.error is not None:
            status_table.add_row("Details", self._latest_result.error.message)
        elif self._latest_result is not None and self._latest_result.artifact is not None:
            artifact = self._latest_result.artifact
            status_table.add_row("Bytes", str(artifact.file_size_bytes))
            status_table.add_row("Written", artifact.exported_at.strftime("%Y-%m-%d %H:%M:%S"))

        self.query_one("#export-status", Static).update(
            Panel(status_table, title="Export Status", border_style=border_style)
        )

    def _render_log(self) -> None:
        if not self._log_lines:
            body = Text("No export actions yet. Choose a format, confirm a path, then export.", style="dim")
        else:
            body = Text("\n".join(self._log_lines[-8:]))
        self.query_one("#export-log", Static).update(
            Panel(body, title="Export Log", border_style="blue")
        )

    def _append_log(self, message: str) -> None:
        self._log_lines.append(message)
        self._render_log()

    def _format_success_log(self, artifact: ExportArtifact) -> str:
        return (
            f"[{artifact.exported_at.strftime('%H:%M:%S')}] "
            f"Exported {artifact.format_name.upper()} to {artifact.output_path} "
            f"({artifact.file_size_bytes} bytes)."
        )

    def _format_error_log(self, result: ExportResult) -> str:
        assert result.error is not None
        return f"[ERROR] {result.error.kind.replace('_', ' ')}: {result.error.message}"
