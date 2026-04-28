import asyncio
from datetime import datetime
from io import StringIO
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel
from textual.widgets import Button, Input, RadioButton, Static

from resgen.services import (
    DashboardError,
    DashboardIdentity,
    DashboardOverview,
    DashboardOverviewResult,
    DashboardValidationStatus,
    ExportArtifact,
    ExportResult,
    ResumeStats,
)
from resgen.tui.app import ResgenTuiApp
from resgen.tui.screens.export import ExportScreen


class ExportTuiTest(unittest.TestCase):
    def test_export_screen_supports_keyboard_confirmation_and_success_feedback(self) -> None:
        async def run_test() -> None:
            dashboard = self._dashboard_overview()
            artifact = ExportArtifact(
                format_name="html",
                output_path=Path("dist/resume.html"),
                file_size_bytes=2048,
                exported_at=datetime(2026, 4, 28, 20, 15, 0),
            )

            with patch(
                "resgen.tui.screens.dashboard.get_resume_overview",
                return_value=DashboardOverviewResult(overview=dashboard),
            ), patch(
                "resgen.tui.screens.export.run_resume_export",
                return_value=ExportResult(artifact=artifact),
            ) as export_mock:
                app = ResgenTuiApp()
                async with app.run_test() as pilot:
                    await pilot.press("e")
                    await pilot.pause()

                    self.assertIsInstance(app.screen, ExportScreen)

                    html_button = app.screen.query_one("#format-html", RadioButton)
                    html_button.value = True
                    await pilot.pause()

                    path_input = app.screen.query_one("#export-path", Input)
                    self.assertEqual(path_input.value, "resume_export.html")

                    path_input.focus()
                    path_input.value = "dist/resume.html"
                    await pilot.pause()
                    await pilot.press("enter")
                    await pilot.pause()

                    export_button = app.screen.query_one("#run-export", Button)
                    self.assertFalse(export_button.disabled)

                    export_button.focus()
                    await pilot.press("enter")
                    await pilot.pause()

                    export_mock.assert_called_once_with("html", Path("dist/resume.html"))

                    status_panel = app.screen.query_one("#export-status", Static).visual._renderable
                    log_panel = app.screen.query_one("#export-log", Static).visual._renderable

                    self.assertIsInstance(status_panel, Panel)
                    self.assertIn("SUCCESS", self._render_text(status_panel))
                    self.assertIn("2048", self._render_text(status_panel))
                    self.assertIn("dist/resume.html", self._render_text(log_panel))

        asyncio.run(run_test())

    def test_export_screen_surfaces_export_errors(self) -> None:
        async def run_test() -> None:
            dashboard = self._dashboard_overview()
            failure = ExportResult(
                artifact=None,
                error=DashboardError(
                    kind="dependency_error",
                    message="PDF export requires the optional 'weasyprint' dependency.",
                ),
            )

            with patch(
                "resgen.tui.screens.dashboard.get_resume_overview",
                return_value=DashboardOverviewResult(overview=dashboard),
            ), patch(
                "resgen.tui.screens.export.run_resume_export",
                return_value=failure,
            ):
                app = ResgenTuiApp()
                async with app.run_test() as pilot:
                    await pilot.press("e")
                    await pilot.pause()

                    pdf_button = app.screen.query_one("#format-pdf", RadioButton)
                    pdf_button.value = True
                    await pilot.pause()

                    path_input = app.screen.query_one("#export-path", Input)
                    path_input.focus()
                    await pilot.press("enter")
                    await pilot.pause()

                    export_button = app.screen.query_one("#run-export", Button)
                    export_button.focus()
                    await pilot.press("enter")
                    await pilot.pause()

                    status_panel = app.screen.query_one("#export-status", Static).visual._renderable
                    log_panel = app.screen.query_one("#export-log", Static).visual._renderable

                    self.assertIn("FAILED", self._render_text(status_panel))
                    self.assertIn("weasyprint", self._render_text(status_panel))
                    self.assertIn("dependency error", self._render_text(log_panel).lower())

        asyncio.run(run_test())

    def _dashboard_overview(self) -> DashboardOverview:
        return DashboardOverview(
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
            validation=DashboardValidationStatus(state="valid"),
            last_export_path=Path("resume_export.html"),
        )

    def _render_text(self, renderable) -> str:
        output = StringIO()
        console = Console(file=output, width=120, force_terminal=False, color_system=None)
        console.print(renderable)
        return output.getvalue()


if __name__ == "__main__":
    unittest.main()
