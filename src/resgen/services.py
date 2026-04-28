from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from pathlib import Path
import re

from jsonschema import ValidationError

from .core import get_template_env, iter_schema_errors, load_resume, validate_schema


SUPPORTED_EXPORT_FORMATS = {"md", "html", "pdf"}
SECTION_NAMES = (
    "work",
    "volunteer",
    "education",
    "awards",
    "certificates",
    "publications",
    "languages",
    "interests",
    "references",
    "projects",
)

_LAST_EXPORT_PATH: Path | None = None


@dataclass(frozen=True)
class ResumeStats:
    total_experience_years: float | None
    skill_categories: int
    total_skill_keywords: int
    project_count: int
    education_count: int


@dataclass(frozen=True)
class DashboardIdentity:
    name: str
    label: str
    summary: str


@dataclass(frozen=True)
class DashboardValidationStatus:
    state: str
    message: str | None = None


@dataclass(frozen=True)
class DashboardOverview:
    identity: DashboardIdentity
    stats: ResumeStats
    section_counts: dict[str, int]
    validation: DashboardValidationStatus
    last_export_path: Path | None = None


@dataclass(frozen=True)
class DashboardError:
    kind: str
    message: str


@dataclass(frozen=True)
class DashboardOverviewResult:
    overview: DashboardOverview | None
    error: DashboardError | None = None


@dataclass(frozen=True)
class ValidationIssue:
    message: str
    json_path: str
    likely_next_action: str
    validator_name: str
    failing_value: str | None = None


@dataclass(frozen=True)
class ValidationReport:
    state: str
    validated_at: datetime
    issues: list[ValidationIssue]


@dataclass(frozen=True)
class ValidationReportResult:
    report: ValidationReport | None
    error: DashboardError | None = None


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
    global _LAST_EXPORT_PATH

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

    _LAST_EXPORT_PATH = destination
    return destination


def collect_resume_stats() -> ResumeStats:
    """Calculate basic statistics from validated resume data."""
    data = validate_resume()
    return _build_resume_stats(data)


def get_resume_overview() -> DashboardOverviewResult:
    """Return a dashboard-friendly summary of the active resume state."""
    data, error = _load_resume_data()
    if error is not None:
        return DashboardOverviewResult(overview=None, error=error)

    validation = DashboardValidationStatus(state="valid")
    try:
        validate_schema(data)
    except ValidationError as exc:
        path = " -> ".join(str(part) for part in exc.path) or "<root>"
        validation = DashboardValidationStatus(
            state="invalid",
            message=f"{exc.message} (path: {path})",
        )
    except FileNotFoundError as exc:
        return DashboardOverviewResult(
            overview=None,
            error=DashboardError(kind="file_error", message=str(exc)),
        )

    basics = data.get("basics", {})
    overview = DashboardOverview(
        identity=DashboardIdentity(
            name=basics.get("name", "Unknown"),
            label=basics.get("label", ""),
            summary=basics.get("summary", ""),
        ),
        stats=_build_resume_stats(data),
        section_counts={section: len(data.get(section, [])) for section in SECTION_NAMES},
        validation=validation,
        last_export_path=_LAST_EXPORT_PATH,
    )
    return DashboardOverviewResult(overview=overview)


def get_resume_validation_report() -> ValidationReportResult:
    """Return structured validation output for TUI and future CLI consumers."""
    data, error = _load_resume_data()
    if error is not None:
        return ValidationReportResult(report=None, error=error)

    try:
        schema_errors = iter_schema_errors(data)
    except FileNotFoundError as exc:
        return ValidationReportResult(
            report=None,
            error=DashboardError(kind="file_error", message=str(exc)),
        )

    issues = [_build_validation_issue(error) for error in schema_errors]
    state = "valid" if not issues else "invalid"
    return ValidationReportResult(
        report=ValidationReport(
            state=state,
            validated_at=datetime.now(),
            issues=issues,
        )
    )


def get_last_export_path() -> Path | None:
    """Return the most recent export destination for the current process."""
    return _LAST_EXPORT_PATH


def _load_resume_data() -> tuple[dict | None, DashboardError | None]:
    try:
        return load_resume(), None
    except ValueError as exc:
        return None, DashboardError(kind="config_error", message=str(exc))
    except FileNotFoundError as exc:
        return None, DashboardError(kind="file_error", message=str(exc))
    except json.JSONDecodeError as exc:
        return None, DashboardError(
            kind="json_error",
            message=f"JSON Parse Error at line {exc.lineno}: {exc.msg}",
        )


def _build_validation_issue(error: ValidationError) -> ValidationIssue:
    missing_property = _extract_missing_property(error)
    path_parts = [str(part) for part in error.path]
    if missing_property is not None:
        path_parts.append(missing_property)

    json_path = _format_json_path(path_parts)
    return ValidationIssue(
        message=error.message,
        json_path=json_path,
        likely_next_action=_suggest_next_action(error, json_path, missing_property),
        validator_name=error.validator,
        failing_value=_format_failing_value(error.instance, path_parts),
    )


def _extract_missing_property(error: ValidationError) -> str | None:
    if error.validator != "required":
        return None

    match = re.search(r"'([^']+)' is a required property", error.message)
    if match is None:
        return None
    return match.group(1)


def _format_json_path(path_parts: list[str]) -> str:
    if not path_parts:
        return "$"

    pieces = ["$"]
    for part in path_parts:
        if part.isdigit():
            pieces.append(f"[{part}]")
        else:
            pieces.append(f".{part}")
    return "".join(pieces)


def _suggest_next_action(
    error: ValidationError,
    json_path: str,
    missing_property: str | None,
) -> str:
    if error.validator == "required":
        field_name = missing_property or "field"
        return f"Add `{field_name}` at {json_path} and rerun validation."
    if error.validator == "type":
        return f"Change the value at {json_path} to the expected `{error.validator_value}` type."
    if error.validator == "enum":
        return f"Replace the value at {json_path} with one of the allowed schema values."
    if error.validator == "minItems":
        return f"Add at least {error.validator_value} item(s) at {json_path}."
    if error.validator == "additionalProperties":
        return f"Remove unsupported fields near {json_path} or update the schema intentionally."
    return f"Inspect the value at {json_path} and compare it against the schema requirements."


def _format_failing_value(instance: object, path_parts: list[str]) -> str | None:
    sensitive_parts = {"email", "phone", "phone_number"}
    if any(part.lower() in sensitive_parts for part in path_parts):
        return None

    if isinstance(instance, (dict, list)):
        return None

    rendered = json.dumps(instance)
    if len(rendered) > 120:
        return f"{rendered[:117]}..."
    return rendered


def _build_resume_stats(data: dict) -> ResumeStats:
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
