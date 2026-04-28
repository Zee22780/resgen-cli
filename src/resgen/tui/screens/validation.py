from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, OptionList, Static

from resgen.services import (
    ValidationIssue,
    ValidationReport,
    ValidationReportResult,
    get_resume_validation_report,
)


class ValidationScreen(Screen[None]):
    """Run schema validation in-app and browse structured issues."""

    def __init__(self) -> None:
        super().__init__()
        self._report: ValidationReport | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="validation-root"):
            yield Header(show_clock=True)
            with Horizontal(id="validation-toolbar"):
                yield Button("Run Validation", variant="primary", id="run-validation")
                yield Static(id="validation-status")
            with Horizontal(id="validation-results"):
                yield OptionList(id="validation-issues")
                yield Static(id="validation-detail")
            yield Footer()

    def on_mount(self) -> None:
        self.run_validation()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run-validation":
            self.run_validation()

    def on_option_list_option_highlighted(
        self,
        event: OptionList.OptionHighlighted,
    ) -> None:
        self._show_issue_detail(event.option_index)

    def on_option_list_option_selected(
        self,
        event: OptionList.OptionSelected,
    ) -> None:
        self._show_issue_detail(event.option_index)

    def run_validation(self) -> None:
        result = get_resume_validation_report()
        if result.error is not None:
            self._report = None
            self._render_error_state(result)
            return

        assert result.report is not None
        self._report = result.report
        self._render_report(result.report)

    def _render_report(self, report: ValidationReport) -> None:
        issues_widget = self.query_one("#validation-issues", OptionList)
        detail_widget = self.query_one("#validation-detail", Static)

        self.query_one("#validation-status", Static).update(self._status_panel(report))

        if report.state == "valid":
            issues_widget.disabled = True
            issues_widget.set_options(["No validation issues found."])
            detail_widget.update(self._success_panel(report))
            return

        issues_widget.disabled = False
        issues_widget.set_options(
            [
                f"{index + 1}. {issue.json_path}\n{self._truncate(issue.message, 56)}"
                for index, issue in enumerate(report.issues)
            ]
        )
        if report.issues:
            issues_widget.highlighted = 0
            self._show_issue_detail(0)
        else:
            detail_widget.update(self._success_panel(report))

    def _render_error_state(self, result: ValidationReportResult) -> None:
        assert result.error is not None
        issues_widget = self.query_one("#validation-issues", OptionList)
        issues_widget.disabled = True
        issues_widget.set_options(["Validation could not run."])

        self.query_one("#validation-status", Static).update(
            Panel(
                Text(result.error.message, style="bold red"),
                title="Validation Error",
                border_style="red",
            )
        )
        self.query_one("#validation-detail", Static).update(
            Panel(
                Text(
                    "Fix the configuration or file problem shown above, then run validation again.",
                ),
                title="Next Step",
                border_style="red",
            )
        )

    def _show_issue_detail(self, issue_index: int) -> None:
        if self._report is None or not self._report.issues:
            return

        issue = self._report.issues[issue_index]
        self.query_one("#validation-detail", Static).update(self._issue_panel(issue))

    def _status_panel(self, report: ValidationReport) -> Panel:
        state_style = "green" if report.state == "valid" else "yellow"
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=3)
        grid.add_row("Status", f"[{state_style}]{report.state.upper()}[/{state_style}]")
        grid.add_row("Checked", report.validated_at.strftime("%Y-%m-%d %H:%M:%S"))
        grid.add_row("Issues", str(len(report.issues)))
        return Panel(
            grid,
            title="Validation Status",
            border_style="green" if report.state == "valid" else "yellow",
        )

    def _success_panel(self, report: ValidationReport) -> Panel:
        body = Text()
        body.append("Resume schema is valid.\n", style="bold green")
        body.append(
            f"Checked at {report.validated_at.strftime('%Y-%m-%d %H:%M:%S')} with no issues found.",
            style="dim",
        )
        return Panel(body, title="Validation Result", border_style="green")

    def _issue_panel(self, issue: ValidationIssue) -> Panel:
        body = Text()
        body.append("Message\n", style="bold")
        body.append(f"{issue.message}\n\n")
        body.append("JSON Path\n", style="bold")
        body.append(f"{issue.json_path}\n\n")
        body.append("Schema Rule\n", style="bold")
        body.append(f"{issue.validator_name}\n\n")
        if issue.failing_value is not None:
            body.append("Failing Value\n", style="bold")
            body.append(f"{issue.failing_value}\n\n")
        body.append("Likely Next Fix\n", style="bold")
        body.append(issue.likely_next_action)
        return Panel(body, title="Issue Detail", border_style="yellow")

    def _truncate(self, value: str, width: int) -> str:
        if len(value) <= width:
            return value
        return f"{value[: width - 3]}..."
