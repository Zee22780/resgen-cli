import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Root directory of the project
ROOT_DIR = Path(__file__).parent.parent.parent

# Paths
# This is the path to the user's actual resume.json, loaded from .env
RESUME_JSON_PATH = os.environ.get("RESUME_JSON_PATH")

SCHEMA_PATH = ROOT_DIR / "schema.json"
THEMES_DIR = ROOT_DIR / "themes"
