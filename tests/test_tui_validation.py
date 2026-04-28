import asyncio
from datetime import datetime
from io import StringIO
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel
from textual.widgets import OptionList, Static

from resgen.services import (
    DashboardIdentity,
    DashboardOverview,
    DashboardOverviewResult,
    DashboardValidationStatus,
    ResumeStats,
    ValidationIssue,
    ValidationReport,
    ValidationReportResult,
)
from resgen.tui.app import ResgenTuiApp
from resgen.tui.screens.validation import ValidationScreen


class ValidationTuiTest(unittest.TestCase):
    def test_validation_screen_renders_issues_and_supports_navigation(self) -> None:
        async def run_test() -> None:
            dashboard = DashboardOverview(
                identity=DashboardIdentity(
                    name="Zuri Lyons",
                    label="AI Product Engineer",
                    summary="Builds AI and frontend systems for real users.",
                ),
                stats=ResumeStats(
                    total_experience_years=2.0,
                    skill_categories=2,
                    total_skill_keywords=6,
                    project_count=1,
                    education_count=1,
                ),
                section_counts={
                    "work": 1,
                    "volunteer": 0,
                    "education": 1,
                    "awards": 0,
                    "certificates": 0,
                    "publications": 0,
                    "languages": 0,
                    "interests": 0,
                    "references": 0,
                    "projects": 1,
                },
                validation=DashboardValidationStatus(state="invalid", message="See validation screen"),
                last_export_path=Path("resume_export.html"),
            )
            report = ValidationReport(
                state="invalid",
                validated_at=datetime(2026, 4, 28, 19, 30, 0),
                issues=[
                    ValidationIssue(
                        message="'email' is a required property",
                        json_path="$.basics.email",
                        likely_next_action="Add `email` at $.basics.email and rerun validation.",
                        validator_name="required",
                    ),
                    ValidationIssue(
                        message="'React' is not of type 'array'",
                        json_path="$.skills[0].keywords",
                        likely_next_action="Change the value at $.skills[0].keywords to the expected `array` type.",
                        validator_name="type",
                        failing_value='"React"',
                    ),
                ],
            )

            with patch(
                "resgen.tui.screens.dashboard.get_resume_overview",
                return_value=DashboardOverviewResult(overview=dashboard),
            ), patch(
                "resgen.tui.screens.validation.get_resume_validation_report",
                return_value=ValidationReportResult(report=report),
            ):
                app = ResgenTuiApp()
                async with app.run_test() as pilot:
                    await pilot.press("v")
                    await pilot.pause()

                    self.assertIsInstance(app.screen, ValidationScreen)

                    status_panel = app.screen.query_one("#validation-status", Static).visual._renderable
                    detail_panel = app.screen.query_one("#validation-detail", Static).visual._renderable
                    issues_widget = app.screen.query_one("#validation-issues", OptionList)

                    self.assertIsInstance(status_panel, Panel)
                    self.assertIn("INVALID", self._render_text(status_panel))
                    self.assertIn("$.basics.email", self._render_text(detail_panel))

                    issues_widget.focus()
                    await pilot.press("down")
                    await pilot.pause()

                    next_detail_panel = app.screen.query_one("#validation-detail", Static).visual._renderable
                    self.assertIn("$.skills[0].keywords", self._render_text(next_detail_panel))
                    self.assertIn('"React"', self._render_text(next_detail_panel))

        asyncio.run(run_test())

    def _render_text(self, renderable) -> str:
        output = StringIO()
        console = Console(file=output, width=120, force_terminal=False, color_system=None)
        console.print(renderable)
        return output.getvalue()


if __name__ == "__main__":
    unittest.main()
