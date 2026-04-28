import typer
from dotenv import load_dotenv
import json
from jsonschema import ValidationError
from resgen.core import load_resume
from resgen.services import (
    collect_resume_stats,
    export_resume,
    validate_resume,
)

load_dotenv()

app = typer.Typer()

@app.command()
def hello():
    """Test command to verify setup."""
    typer.echo("resgen-cli is set up and ready!")

@app.command()
def validate():
    """Validates the resume JSON against the defined schema."""
    try:
        load_resume()
        typer.echo("Successfully loaded resume data (with secrets injected).")

        validate_resume()
        typer.secho("✅ Validation successful! Your resume matches the schema.", fg=typer.colors.GREEN)

    except ValueError as e:
        typer.secho(f"Configuration Error: {e}", fg=typer.colors.RED)
    except FileNotFoundError as e:
        typer.secho(f"File Error: {e}", fg=typer.colors.RED)
    except json.JSONDecodeError as e:
        typer.secho(f"JSON Parse Error at line {e.lineno}: {e.msg}", fg=typer.colors.RED)
    except ValidationError as e:
        typer.secho("❌ Validation Error!", fg=typer.colors.RED)
        typer.secho(f"Message: {e.message}", fg=typer.colors.YELLOW)
        typer.echo(f"Path: {' -> '.join(str(p) for p in e.path)}")
    except Exception as e:
        typer.secho(f"Unexpected Error: {e}", fg=typer.colors.RED)

@app.command()
def export(format: str = typer.Option(..., help="Export format: 'md', 'html', or 'pdf'")):
    """Exports the resume to the specified format."""
    try:
        output_file = export_resume(format)
        typer.secho(f"✅ Successfully exported resume to {output_file.absolute()}", fg=typer.colors.GREEN)
    except ValueError as e:
        typer.secho(f"Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except FileNotFoundError as e:
        typer.secho(f"File Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except ValidationError as e:
        typer.secho("❌ Validation Error! Please run `resume validate` to fix issues.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except RuntimeError as e:
        typer.secho(f"Configuration Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Unexpected Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def stats():
    """Calculates fun statistics from your resume."""
    try:
        stats_summary = collect_resume_stats()

        typer.secho("📊 Resume Statistics", fg=typer.colors.CYAN, bold=True)
        typer.echo("-" * 20)

        if stats_summary.total_experience_years is not None:
            typer.echo(f"💼 Total Experience: {stats_summary.total_experience_years} years")

        if stats_summary.skill_categories:
            typer.echo(
                "🛠️  Skill Categories: "
                f"{stats_summary.skill_categories} "
                f"({stats_summary.total_skill_keywords} total keywords)"
            )

        if stats_summary.project_count:
            typer.echo(f"🚀 Projects: {stats_summary.project_count}")

        if stats_summary.education_count:
            typer.echo(f"🎓 Education entries: {stats_summary.education_count}")

    except Exception as e:
        typer.secho(f"❌ Error calculating stats: {e}", fg=typer.colors.RED)

if __name__ == "__main__":
    app()
