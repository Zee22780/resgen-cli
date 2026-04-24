import os
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from resgen.main import app
import resgen.core as core


class ExportMarkdownTest(unittest.TestCase):
    def test_markdown_export_uses_portfolio_layout(self) -> None:
        runner = CliRunner()
        repo_root = Path(__file__).resolve().parents[1]
        resume_json = """
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

        with runner.isolated_filesystem():
            resume_path = Path("resume.json")
            resume_path.write_text(resume_json, encoding="utf-8")

            with patch.dict(
                os.environ,
                {"EMAIL": "zuri@example.com", "PHONE_NUMBER": "555-1212"},
                clear=False,
            ):
                with patch.object(core, "RESUME_JSON_PATH", str(resume_path)):
                    with patch.object(core, "SCHEMA_PATH", repo_root / "schema.json"):
                        with patch.object(core, "THEMES_DIR", repo_root / "themes"):
                            result = runner.invoke(app, ["export", "--format", "md"])

            self.assertEqual(result.exit_code, 0, result.output)

            exported = Path("resume_export.md").read_text(encoding="utf-8")

        self.assertIn("# Zuri Lyons", exported)
        self.assertIn("## Selected Projects", exported)
        self.assertIn("Projects selected to foreground AI, frontend, and product delivery work.", exported)
        self.assertIn("### [RFP Intelligence](https://projects.example/rfp)", exported)
        self.assertIn("## Experience", exported)
        self.assertIn("## Core Strengths", exported)
        self.assertIn("[GitHub](https://github.com/zuri)", exported)
        self.assertIn("`zuri@example.com`", exported)
        self.assertIn("Relevant coursework: Distributed Systems, Human Computer Interaction", exported)


if __name__ == "__main__":
    unittest.main()
