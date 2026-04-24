import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from resgen.main import app
import resgen.core as core


RESUME_JSON = """
{
  "basics": {
    "name": "Zuri Lyons",
    "label": "AI Product Engineer",
    "image": "",
    "email": "{{ env.EMAIL }}",
    "phone": "{{ env.PHONE_NUMBER }}",
    "url": "https://example.com",
    "summary": "Builds AI and frontend systems for real users.",
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
        "username": "zuri",
        "url": "https://github.com/zuri"
      },
      {
        "network": "LinkedIn",
        "username": "zuri-lyons",
        "url": "https://linkedin.com/in/zuri-lyons"
      }
    ]
  },
  "work": [
    {
      "name": "Acme",
      "position": "Senior Frontend Engineer",
      "url": "https://acme.example",
      "startDate": "2021-01-01",
      "endDate": "2023-01-01",
      "summary": "Led product UI work across client and platform teams.",
      "highlights": [
        "Shipped complex workflows for enterprise customers"
      ]
    }
  ],
  "volunteer": [],
  "education": [
    {
      "institution": "State University",
      "url": "https://university.example",
      "area": "Computer Science",
      "studyType": "Bachelor",
      "startDate": "2012-01-01",
      "endDate": "2016-01-01",
      "score": "3.9",
      "courses": [
        "Distributed Systems",
        "Human Computer Interaction"
      ]
    }
  ],
  "awards": [],
  "certificates": [],
  "publications": [],
  "skills": [
    {
      "name": "Frontend",
      "level": "Master",
      "keywords": [
        "React",
        "TypeScript",
        "Design Systems"
      ]
    },
    {
      "name": "AI",
      "level": "Advanced",
      "keywords": [
        "Prompt Engineering",
        "Evaluation",
        "RAG"
      ]
    }
  ],
  "languages": [],
  "interests": [],
  "references": [],
  "projects": [
    {
      "name": "RFP Intelligence",
      "startDate": "2024-01-01",
      "endDate": "2024-12-31",
      "description": "An AI system for proposal search and drafting.",
      "highlights": [
        "Used LLM workflows to speed up proposal generation",
        "Built a UI for analysts to review results"
      ],
      "url": "https://projects.example/rfp"
    }
  ]
}
"""


class ExportCommandTest(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.repo_root = Path(__file__).resolve().parents[1]

    def _invoke_export(self, format_name: str, read_output=None):
        with self.runner.isolated_filesystem():
            resume_path = Path("resume.json")
            resume_path.write_text(RESUME_JSON, encoding="utf-8")

            with patch.dict(
                os.environ,
                {"EMAIL": "zuri@example.com", "PHONE_NUMBER": "555-1212"},
                clear=False,
            ):
                with patch.object(core, "RESUME_JSON_PATH", str(resume_path)):
                    with patch.object(core, "SCHEMA_PATH", self.repo_root / "schema.json"):
                        with patch.object(core, "THEMES_DIR", self.repo_root / "themes"):
                            result = self.runner.invoke(app, ["export", "--format", format_name])

            rendered_output = read_output() if read_output is not None else None

        return result, rendered_output

    def test_markdown_export_uses_portfolio_layout(self) -> None:
        result, exported = self._invoke_export(
            "md",
            read_output=lambda: Path("resume_export.md").read_text(encoding="utf-8"),
        )
        self.assertEqual(result.exit_code, 0, result.output)

        self.assertIn("# Zuri Lyons", exported)
        self.assertIn("## Selected Projects", exported)
        self.assertIn("Projects selected to foreground AI, frontend, and product delivery work.", exported)
        self.assertIn("### [RFP Intelligence](https://projects.example/rfp)", exported)
        self.assertIn("## Experience", exported)
        self.assertIn("## Core Strengths", exported)
        self.assertIn("[GitHub](https://github.com/zuri)", exported)
        self.assertIn("`zuri@example.com`", exported)
        self.assertIn("Relevant coursework: Distributed Systems, Human Computer Interaction", exported)

    def test_pdf_export_uses_weasyprint_when_available(self) -> None:
        captured = {}
        fake_module = types.ModuleType("weasyprint")

        class FakeHTML:
            def __init__(self, string: str, base_url: str) -> None:
                captured["string"] = string
                captured["base_url"] = base_url

            def write_pdf(self, output_file: Path) -> None:
                captured["output_file"] = str(output_file)
                Path(output_file).write_bytes(b"%PDF-1.7 fake pdf")

        fake_module.HTML = FakeHTML

        with patch.dict(sys.modules, {"weasyprint": fake_module}):
            result, exported_bytes = self._invoke_export(
                "pdf",
                read_output=lambda: Path("resume_export.pdf").read_bytes(),
            )

        self.assertEqual(result.exit_code, 0, result.output)
        self.assertEqual(exported_bytes, b"%PDF-1.7 fake pdf")
        self.assertIn("<!DOCTYPE html>", captured["string"])
        self.assertIn("Zuri Lyons", captured["string"])
        self.assertEqual(captured["output_file"], "resume_export.pdf")

    def test_pdf_export_reports_missing_weasyprint_dependency(self) -> None:
        with patch.dict(sys.modules, {"weasyprint": None}):
            result, _ = self._invoke_export("pdf")

        self.assertNotEqual(result.exit_code, 0)
        self.assertIn("PDF export requires the optional 'weasyprint' dependency", result.output)


if __name__ == "__main__":
    unittest.main()
