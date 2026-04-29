from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

from resgen.services import DashboardOverview, DashboardOverviewResult, get_resume_overview


class DashboardScreen(Screen[None]):
    """Read-only dashboard landing screen."""

    BINDINGS = [Binding("ctrl+r", "refresh_dashboard", "Refresh")]

    def compose(self) -> ComposeResult:
        with Vertical(id="dashboard-root"):
            yield Header(show_clock=True)
            with Horizontal(classes="dashboard-row"):
                yield Static(classes="card", id="profile-card")
                yield Static(classes="card", id="health-card")
            with Horizontal(classes="dashboard-row"):
                yield Static(classes="card", id="experience-card")
                yield Static(classes="card", id="skills-card")
                yield Static(classes="card", id="projects-card")
                yield Static(classes="card", id="education-card")
            yield Static(id="section-counts")
            yield Footer()

    def on_mount(self) -> None:
        self.refresh_dashboard()

    def action_refresh_dashboard(self) -> None:
        self.refresh_dashboard()

    def refresh_dashboard(self) -> None:
        self._render_loading_state()
        result = get_resume_overview()
        if result.error is not None:
            self._render_error_state(result)
            return

        assert result.overview is not None
        self._render_overview(result.overview)

    def _render_loading_state(self) -> None:
        loading_panel = Panel(Text("Loading resume overview..."), title="Loading", border_style="cyan")
        self.query_one("#profile-card", Static).update(loading_panel)
        self.query_one("#health-card", Static).update(loading_panel)
        for widget_id in (
            "#experience-card",
            "#skills-card",
            "#projects-card",
            "#education-card",
            "#section-counts",
        ):
            self.query_one(widget_id, Static).update(loading_panel)

    def _render_error_state(self, result: DashboardOverviewResult) -> None:
        assert result.error is not None
        error_message = Text(result.error.message, style="bold red")
        self.query_one("#profile-card", Static).update(
            Panel(error_message, title="Resume Unavailable", border_style="red")
        )
        self.query_one("#health-card", Static).update(
            Panel(
                Text(f"State: {result.error.kind.replace('_', ' ')}"),
                title="Health",
                border_style="red",
            )
        )
        for widget_id, title in (
            ("#experience-card", "Experience"),
            ("#skills-card", "Skills"),
            ("#projects-card", "Projects"),
            ("#education-card", "Education"),
        ):
            self.query_one(widget_id, Static).update(
                self._stat_panel(title=title, value="n/a", subtitle="Dashboard data unavailable")
            )
        self.query_one("#section-counts", Static).update(
            Panel(
                Text("Section counts are unavailable until the resume loads."),
                title="Section Inventory",
                border_style="red",
            )
        )

    def _render_overview(self, overview: DashboardOverview) -> None:
        self.query_one("#profile-card", Static).update(self._profile_panel(overview))
        self.query_one("#health-card", Static).update(self._health_panel(overview))
        self.query_one("#experience-card", Static).update(
            self._stat_panel(
                title="Experience",
                value=(
                    f"{overview.stats.total_experience_years:.1f} years"
                    if overview.stats.total_experience_years is not None
                    else "n/a"
                ),
                subtitle="Calculated from work history",
            )
        )
        self.query_one("#skills-card", Static).update(
            self._stat_panel(
                title="Skills",
                value=str(overview.stats.total_skill_keywords),
                subtitle=f"{overview.stats.skill_categories} categories",
            )
        )
        self.query_one("#projects-card", Static).update(
            self._stat_panel(
                title="Projects",
                value=str(overview.stats.project_count),
                subtitle="Portfolio-ready entries",
            )
        )
        self.query_one("#education-card", Static).update(
            self._stat_panel(
                title="Education",
                value=str(overview.stats.education_count),
                subtitle="Recorded education entries",
            )
        )
        self.query_one("#section-counts", Static).update(self._section_inventory_panel(overview))

    def _profile_panel(self, overview: DashboardOverview) -> Panel:
        identity = overview.identity
        body = Text()
        body.append(identity.name or "Unknown", style="bold")
        if identity.label:
            body.append(f"\n{identity.label}", style="cyan")
        if identity.summary:
            body.append(f"\n\n{identity.summary}")
        return Panel(body, title="Profile", border_style="blue")

    def _health_panel(self, overview: DashboardOverview) -> Panel:
        validation_state = overview.validation.state.upper()
        validation_style = "green" if overview.validation.state == "valid" else "yellow"
        last_export = (
            str(overview.last_export_path)
            if overview.last_export_path is not None
            else "No exports in this session"
        )

        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=3)
        grid.add_row("Validation", f"[{validation_style}]{validation_state}[/{validation_style}]")
        grid.add_row("Last export", last_export)
        if overview.validation.message:
            grid.add_row("Details", overview.validation.message)

        border_style = "green" if overview.validation.state == "valid" else "yellow"
        return Panel(grid, title="Health", border_style=border_style)

    def _stat_panel(self, title: str, value: str, subtitle: str) -> Panel:
        body = Text()
        body.append(f"{value}\n", style="bold")
        body.append(subtitle, style="dim")
        return Panel(body, title=title, border_style="magenta")

    def _section_inventory_panel(self, overview: DashboardOverview) -> Panel:
        table = Table(expand=True)
        table.add_column("Section", style="bold")
        table.add_column("Count", justify="right")
        for section_name, count in overview.section_counts.items():
            table.add_row(section_name.replace("_", " ").title(), str(count))
        return Panel(table, title="Section Inventory", border_style="blue")
