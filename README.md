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

## Getting Started

1. Create a virtual environment: `python3 -m venv venv`
2. Activate it: `source venv/bin/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Run the CLI: `python -m src.resgen.main --help`

## Export Formats

Use `resume export --format md` for Markdown, `resume export --format html` for HTML, and `resume export --format pdf` for print-ready PDF output.

If PDF export fails because `WeasyPrint` is missing, install it in your active environment with `pip install weasyprint`. Some platforms also require native rendering libraries; follow the WeasyPrint installation guide for your OS if the Python package alone is not enough.
