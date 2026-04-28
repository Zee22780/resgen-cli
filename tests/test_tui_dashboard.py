import asyncio
from io import StringIO
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console
from rich.panel import Panel
from textual.widgets import Static

from resgen.services import (
    DashboardIdentity,
    DashboardOverview,
    DashboardOverviewResult,
    DashboardValidationStatus,
    ResumeStats,
)
from resgen.tui.app import ResgenTuiApp


class DashboardTuiTest(unittest.TestCase):
    def test_dashboard_renders_profile_and_health_cards(self) -> None:
        async def run_test() -> None:
            overview = DashboardOverview(
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

            with patch(
                "resgen.tui.screens.dashboard.get_resume_overview",
                return_value=DashboardOverviewResult(overview=overview),
            ):
                app = ResgenTuiApp()
                async with app.run_test() as pilot:
                    await pilot.pause()
                    profile_panel = app.screen.query_one("#profile-card", Static).visual._renderable
                    health_panel = app.screen.query_one("#health-card", Static).visual._renderable
                    experience_panel = app.screen.query_one("#experience-card", Static).visual._renderable

                    self.assertIsInstance(profile_panel, Panel)
                    self.assertIn("Zuri Lyons", self._render_text(profile_panel))
                    self.assertIsInstance(health_panel, Panel)
                    self.assertIn("resume_export.html", self._render_text(health_panel))
                    self.assertIsInstance(experience_panel, Panel)
                    self.assertIn("2.0 years", self._render_text(experience_panel))

        asyncio.run(run_test())

    def _render_text(self, renderable) -> str:
        output = StringIO()
        console = Console(file=output, width=120, force_terminal=False, color_system=None)
        console.print(renderable)
        return output.getvalue()


if __name__ == "__main__":
    unittest.main()
