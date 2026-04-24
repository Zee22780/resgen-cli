import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from jsonschema import validate, ValidationError
from .config import RESUME_JSON_PATH, SCHEMA_PATH, THEMES_DIR

def load_resume() -> dict:
    """Loads the resume.json file with secrets injected."""
    if not RESUME_JSON_PATH:
        raise ValueError("RESUME_JSON_PATH is not set in the environment (.env)")
        
    resume_path = Path(RESUME_JSON_PATH)
    if not resume_path.exists():
        raise FileNotFoundError(f"Resume file not found at {RESUME_JSON_PATH}")

    # Read the raw JSON content
    with open(resume_path, 'r') as f:
        raw_content = f.read()

    # Inject secrets using Jinja2 template rendering
    # This replaces {{ env.SECRET_NAME }} with os.environ["SECRET_NAME"]
    template = Template(raw_content)
    rendered_content = template.render(env=os.environ)

    # Parse back into a Python dictionary
    return json.loads(rendered_content)

def validate_schema(data: dict) -> None:
    """Validates the resume dictionary against the central schema.json."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_PATH}")
        
    with open(SCHEMA_PATH, 'r') as f:
        schema = json.load(f)
        
    # Validates data against the schema
    # Will raise jsonschema.exceptions.ValidationError if invalid
    validate(instance=data, schema=schema)

def get_template_env() -> Environment:
    """Returns a Jinja2 Environment configured for the themes directory."""
    if not THEMES_DIR.exists():
        raise FileNotFoundError(f"Themes directory not found at {THEMES_DIR}")
        
    return Environment(
        loader=FileSystemLoader(searchpath=THEMES_DIR),
        autoescape=False # Resumes might need raw HTML injection, adjust as needed
    )
