import typer
from dotenv import load_dotenv
import json
from jsonschema import ValidationError
from resgen.core import load_resume, validate_schema, get_template_env
from pathlib import Path
from datetime import datetime

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
        data = load_resume()
        typer.echo("Successfully loaded resume data (with secrets injected).")
        
        validate_schema(data)
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
def export(format: str = typer.Option(..., help="Export format: 'md' or 'html'")):
    """Exports the resume to the specified format."""
    if format not in ["md", "html"]:
        typer.secho(f"Error: Unsupported format '{format}'. Please use 'md' or 'html'.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
        
    try:
        data = load_resume()
        validate_schema(data)
        
        env = get_template_env()
        template = env.get_template(f"default.{format}")
        
        rendered_output = template.render(**data)
        
        output_file = Path(f"resume_export.{format}")
        with open(output_file, "w") as f:
            f.write(rendered_output)
            
        typer.secho(f"✅ Successfully exported resume to {output_file.absolute()}", fg=typer.colors.GREEN)
        
    except FileNotFoundError as e:
        typer.secho(f"File Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except ValidationError as e:
        typer.secho("❌ Validation Error! Please run `resume validate` to fix issues.", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.secho(f"Unexpected Error: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

@app.command()
def stats():
    """Calculates fun statistics from your resume."""
    try:
        data = load_resume()
        # Optionally validate, though for stats it might be fine without strict schema check.
        # Still good to make sure data structure is roughly sound.
        validate_schema(data)
        
        typer.secho("📊 Resume Statistics", fg=typer.colors.CYAN, bold=True)
        typer.echo("-" * 20)
        
        # 1. Total Years of Experience
        work = data.get("work", [])
        if work:
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
            
            if min_start and max_end:
                years = round((max_end - min_start).days / 365.25, 1)
                typer.echo(f"💼 Total Experience: {years} years")
        
        # 2. Total Skills / Keywords
        skills = data.get("skills", [])
        if skills:
            total_skills = len(skills)
            total_keywords = sum(len(skill.get("keywords", [])) for skill in skills)
            typer.echo(f"🛠️  Skill Categories: {total_skills} ({total_keywords} total keywords)")
        
        # 3. Total Projects
        projects = data.get("projects", [])
        if projects:
            typer.echo(f"🚀 Projects: {len(projects)}")
            
        # 4. Education
        education = data.get("education", [])
        if education:
            typer.echo(f"🎓 Education entries: {len(education)}")
            
    except Exception as e:
        typer.secho(f"❌ Error calculating stats: {e}", fg=typer.colors.RED)

if __name__ == "__main__":
    app()
