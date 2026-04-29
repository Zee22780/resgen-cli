import asyncio
from datetime import datetime
from io import StringIO
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel
from textual.widgets import Static

from resgen.services import (
    AssetStatus,
    ConfigPathStatus,
    ConfigStatus,
    ConfigStatusResult,
    DashboardIdentity,
    DashboardOverview,
    DashboardOverviewResult,
    DashboardValidationStatus,
    EnvVarStatus,
    ResumeStats,
)
from resgen.tui.app import ResgenTuiApp
from resgen.tui.screens.dashboard import DashboardScreen
from resgen.tui.screens.help import HelpScreen
from resgen.tui.screens.settings import SettingsScreen


class SettingsTuiTest(unittest.TestCase):
    def test_settings_screen_renders_safe_configuration_diagnostics(self) -> None:
        async def run_test() -> None:
            dashboard = self._dashboard_overview()
            status = ConfigStatus(
                checked_at=datetime(2026, 4, 28, 21, 15, 0),
                overall_state="attention",
                paths=[
                    ConfigPathStatus(
                        name="Resume JSON",
                        path="resume_example.json",
                        configured=True,
                        exists=True,
                        detail="Configured resume source file.",
                    ),
                    ConfigPathStatus(
                        name="Schema",
                        path="/repo/schema.json",
                        configured=True,
                        exists=True,
                        detail="File is available.",
                    ),
                    ConfigPathStatus(
                        name="Themes",
                        path="/repo/themes",
                        configured=True,
                        exists=True,
                        detail="Directory is available.",
                    ),
                ],
                env_vars=[
                    EnvVarStatus(name="EMAIL", present=True, detail="Present in environment."),
                    EnvVarStatus(name="PHONE_NUMBER", present=False, detail="Missing from environment."),
                ],
                assets=[
                    AssetStatus(name="default.md", available=True, detail="Found."),
                    AssetStatus(name="default.html", available=True, detail="Found."),
                    AssetStatus(name="WeasyPrint", available=False, detail="Missing dependency."),
                ],
            )

            with patch(
                "resgen.tui.screens.dashboard.get_resume_overview",
                return_value=DashboardOverviewResult(overview=dashboard),
            ), patch(
                "resgen.tui.screens.settings.get_config_status",
                return_value=ConfigStatusResult(status=status),
            ):
                app = ResgenTuiApp()
                async with app.run_test() as pilot:
                    await pilot.press("s")
                    await pilot.pause()

                    self.assertIsInstance(app.screen, SettingsScreen)

                    status_panel = app.screen.query_one("#settings-status", Static).visual._renderable
                    env_panel = app.screen.query_one("#settings-env", Static).visual._renderable
                    assets_panel = app.screen.query_one("#settings-assets", Static).visual._renderable

                    self.assertIsInstance(status_panel, Panel)
                    self.assertIn("ATTENTION", self._render_text(status_panel))
                    self.assertIn("PHONE_NUMBER", self._render_text(env_panel))
                    self.assertIn("No", self._render_text(env_panel))
                    self.assertIn("WeasyPrint", self._render_text(assets_panel))

        asyncio.run(run_test())

    def test_help_overlay_toggles_from_question_mark(self) -> None:
        async def run_test() -> None:
            dashboard = self._dashboard_overview()

            with patch(
                "resgen.tui.screens.dashboard.get_resume_overview",
                return_value=DashboardOverviewResult(overview=dashboard),
            ):
                app = ResgenTuiApp()
                async with app.run_test() as pilot:
                    self.assertIsInstance(app.screen, DashboardScreen)

                    await pilot.press("?")
                    await pilot.pause()
                    self.assertIsInstance(app.screen, HelpScreen)

                    help_panel = app.screen.query_one("#help-dialog", Static).visual._renderable
                    self.assertIn("Global Navigation", self._render_text(help_panel))
                    self.assertIn("ctrl+x", self._render_text(help_panel))

                    await pilot.press("?")
                    await pilot.pause()
                    self.assertIsInstance(app.screen, DashboardScreen)

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
