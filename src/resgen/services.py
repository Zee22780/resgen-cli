from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .core import get_template_env, load_resume, validate_schema


SUPPORTED_EXPORT_FORMATS = {"md", "html", "pdf"}


@dataclass(frozen=True)
class ResumeStats:
    total_experience_years: float | None
    skill_categories: int
    total_skill_keywords: int
    project_count: int
    education_count: int


def validate_resume() -> dict:
    """Load resume data and validate it against the configured schema."""
    data = load_resume()
    validate_schema(data)
    return data


def render_resume_template(template_name: str) -> str:
    """Render a resume template after loading and validating resume data."""
    data = validate_resume()
    env = get_template_env()
    template = env.get_template(template_name)
    return template.render(**data)


def export_resume(format_name: str, output_file: Path | None = None) -> Path:
    """Export the resume in the requested format and return the written path."""
    if format_name not in SUPPORTED_EXPORT_FORMATS:
        supported_formats = ", ".join(sorted(SUPPORTED_EXPORT_FORMATS))
        raise ValueError(
            f"Unsupported format '{format_name}'. Please use one of: {supported_formats}."
        )

    destination = output_file or Path(f"resume_export.{format_name}")
    if format_name == "pdf":
        _export_pdf(destination)
    else:
        rendered_output = render_resume_template(f"default.{format_name}")
        _write_text_output(destination, rendered_output)

    return destination


def collect_resume_stats() -> ResumeStats:
    """Calculate basic statistics from validated resume data."""
    data = validate_resume()

    work = data.get("work", [])
    min_start = None
    max_end = None
    for job in work:
        start_str = job.get("startDate")
        end_str = job.get("endDate")

        if start_str:
            try:
                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                if min_start is None or start_date < min_start:
                    min_start = start_date
            except ValueError:
                pass

        if end_str:
            try:
                end_date = datetime.strptime(end_str, "%Y-%m-%d")
                if max_end is None or end_date > max_end:
                    max_end = end_date
            except ValueError:
                max_end = datetime.now()
        else:
            max_end = datetime.now()

    total_experience_years = None
    if min_start and max_end:
        total_experience_years = round((max_end - min_start).days / 365.25, 1)

    skills = data.get("skills", [])
    education = data.get("education", [])
    projects = data.get("projects", [])

    return ResumeStats(
        total_experience_years=total_experience_years,
        skill_categories=len(skills),
        total_skill_keywords=sum(len(skill.get("keywords", [])) for skill in skills),
        project_count=len(projects),
        education_count=len(education),
    )


def _export_pdf(output_file: Path) -> None:
    """Render the HTML theme to PDF using WeasyPrint when available."""
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise RuntimeError(
            "PDF export requires the optional 'weasyprint' dependency. "
            "Install it with `pip install weasyprint`."
        ) from exc

    rendered_html = render_resume_template("default.html")
    HTML(string=rendered_html, base_url=str(Path.cwd())).write_pdf(output_file)


def _write_text_output(output_file: Path, rendered_output: str) -> None:
    with open(output_file, "w") as file:
        file.write(rendered_output)
