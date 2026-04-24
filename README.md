# Resgen CLI: Personal Career Data Engine

A Python-based CLI tool built with **Typer** to dynamically generate and manage professional resumes from a central `resume.json` file. 

The goal of this project is to maintain a single source of truth for career data and securely transform it into various professional artifacts (Markdown, HTML, PDF) using **Jinja2** templates.

## Features (Planned)

* **Secure Ingest**: Loads `resume.json` and securely injects sensitive data (like phone numbers/emails) from a `.env` file during generation.
* **Schema Validation**: Ensures your resume data conforms to a strict `schema.json` format.
* **Dynamic Export**: Renders your data into different themes and formats:
  * Markdown (for GitHub/Portfolios)
  * HTML (precursor for React Dashboards)
  * PDF (using WeasyPrint and the HTML theme)
* **Career Stats**: Utility commands to quickly calculate metrics like total years of experience or skill occurrences.

## Tech Stack

* [Typer](https://typer.tiangolo.com/) - CLI Framework
* [Jinja2](https://jinja.palletsprojects.com/) - Templating Engine
* [jsonschema](https://python-jsonschema.readthedocs.io/) - Data Validation
* [python-dotenv](https://saurabh-kumar.com/python-dotenv/) - Secret Management

## Installation

To install the CLI locally from the repo:

1. Clone the repository: `git clone <your-repo-url>`
2. Enter the project: `cd resgen-cli`
3. Create a virtual environment: `python3 -m venv venv`
4. Activate it: `source venv/bin/activate`
5. Install the package: `pip install -e .`

This installs the `resume` and `resgen` commands inside the virtual environment.

## Configuration

The CLI expects a `.env` file for runtime configuration.

1. Copy the example file: `cp .env.example .env`
2. Update `RESUME_JSON_PATH` to point to your actual resume JSON file
3. Update any secret-backed values such as `EMAIL` and `PHONE_NUMBER`

Example `.env`:

```env
RESUME_JSON_PATH="resume_example.json"
EMAIL="your-email@example.com"
PHONE_NUMBER="555-555-5555"
```

If your resume JSON uses Jinja placeholders like `{{ env.EMAIL }}`, those values will be injected at runtime from `.env`.

## Example Resume JSON

Your resume source file can reference values from `.env` directly. For example:

```json
{
  "basics": {
    "name": "Jane Doe",
    "label": "Frontend Engineer",
    "image": "",
    "email": "{{ env.EMAIL }}",
    "phone": "{{ env.PHONE_NUMBER }}",
    "url": "https://janedoe.dev",
    "summary": "Builds polished product experiences.",
    "location": {
      "address": "123 Main St",
      "postalCode": "10001",
      "city": "New York",
      "countryCode": "US",
      "region": "New York"
    },
    "profiles": [
      {
        "network": "GitHub",
        "username": "janedoe",
        "url": "https://github.com/janedoe"
      }
    ]
  },
  "work": [],
  "volunteer": [],
  "education": [],
  "awards": [],
  "certificates": [],
  "publications": [],
  "skills": [],
  "languages": [],
  "interests": [],
  "references": [],
  "projects": []
}
```

At runtime, `{{ env.EMAIL }}` and `{{ env.PHONE_NUMBER }}` will be replaced with the values from your `.env` file before schema validation and export.

For a full working sample, see [resume_example.json](/Users/zurilyons/code/resgen-cli/resume_example.json).

## Usage

After installation and configuration:

```bash
resume --help
resume validate
resume export --format md
resume export --format html
resume export --format pdf
resume stats
```

## Export Formats

Use `resume export --format md` for Markdown, `resume export --format html` for HTML, and `resume export --format pdf` for print-ready PDF output.

If PDF export fails because `WeasyPrint` is missing, install it in your active environment with `pip install weasyprint`. Some platforms also require native rendering libraries; follow the WeasyPrint installation guide for your OS if the Python package alone is not enough.

On macOS, `WeasyPrint` may also require native libraries. If needed:

```bash
brew install glib pango gdk-pixbuf cairo libffi
```
