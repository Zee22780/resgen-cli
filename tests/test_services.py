import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import resgen.core as core
from jsonschema import ValidationError

import resgen.services as services
from resgen.services import (
    collect_resume_stats,
    export_resume,
    get_resume_overview,
    get_resume_validation_report,
    validate_resume,
)


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
    "profiles": []
  },
  "work": [
    {
      "name": "Acme",
      "position": "Senior Frontend Engineer",
      "url": "https://acme.example",
      "startDate": "2021-01-01",
      "endDate": "2023-01-01",
      "summary": "Led product UI work across client and platform teams.",
      "highlights": []
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
      "courses": []
    }
  ],
  "awards": [],
  "certificates": [],
  "publications": [],
  "skills": [
    {
      "name": "Frontend",
      "level": "Master",
      "keywords": ["React", "TypeScript", "Design Systems"]
    },
    {
      "name": "AI",
      "level": "Advanced",
      "keywords": ["Prompt Engineering", "Evaluation", "RAG"]
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
      "highlights": [],
      "url": "https://projects.example/rfp"
    }
  ]
}
"""


class ResumeServicesTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_validate_resume_injects_environment_values(self) -> None:
        with self._patched_resume_env():
            data = validate_resume()

        self.assertEqual(data["basics"]["email"], "zuri@example.com")
        self.assertEqual(data["basics"]["phone"], "555-1212")

    def test_collect_resume_stats_returns_shared_dashboard_metrics(self) -> None:
        with self._patched_resume_env():
            stats = collect_resume_stats()

        self.assertEqual(stats.total_experience_years, 2.0)
        self.assertEqual(stats.skill_categories, 2)
        self.assertEqual(stats.total_skill_keywords, 6)
        self.assertEqual(stats.project_count, 1)
        self.assertEqual(stats.education_count, 1)

    def test_get_resume_overview_returns_dashboard_snapshot(self) -> None:
        with self._patched_resume_env():
            result = get_resume_overview()

        self.assertIsNone(result.error)
        self.assertIsNotNone(result.overview)
        assert result.overview is not None
        self.assertEqual(result.overview.identity.name, "Zuri Lyons")
        self.assertEqual(result.overview.validation.state, "valid")
        self.assertEqual(result.overview.section_counts["work"], 1)
        self.assertEqual(result.overview.section_counts["projects"], 1)
        self.assertEqual(result.overview.stats.total_skill_keywords, 6)

    def test_get_resume_overview_keeps_counts_when_validation_fails(self) -> None:
        with self._patched_resume_env():
            with patch.object(
                services,
                "validate_schema",
                side_effect=ValidationError("Missing required property"),
            ):
                result = get_resume_overview()

        self.assertIsNone(result.error)
        self.assertIsNotNone(result.overview)
        assert result.overview is not None
        self.assertEqual(result.overview.validation.state, "invalid")
        self.assertIn("Missing required property", result.overview.validation.message)
        self.assertEqual(result.overview.section_counts["work"], 1)
        self.assertEqual(result.overview.stats.project_count, 1)

    def test_get_resume_validation_report_returns_valid_state(self) -> None:
        with self._patched_resume_env():
            result = get_resume_validation_report()

        self.assertIsNone(result.error)
        self.assertIsNotNone(result.report)
        assert result.report is not None
        self.assertEqual(result.report.state, "valid")
        self.assertEqual(result.report.issues, [])

    def test_get_resume_validation_report_returns_structured_issues(self) -> None:
        resume_data = json.loads(RESUME_JSON)
        del resume_data["basics"]["email"]
        resume_data["skills"][0]["keywords"] = "React"
        resume_data["projects"][0]["highlights"] = "Built a UI"

        with self._patched_resume_env(resume_json=json.dumps(resume_data)):
            result = get_resume_validation_report()

        self.assertIsNone(result.error)
        self.assertIsNotNone(result.report)
        assert result.report is not None
        self.assertEqual(result.report.state, "invalid")
        self.assertGreaterEqual(len(result.report.issues), 3)

        issue_paths = {issue.json_path for issue in result.report.issues}
        self.assertIn("$.basics.email", issue_paths)
        self.assertIn("$.skills[0].keywords", issue_paths)
        self.assertIn("$.projects[0].highlights", issue_paths)

        required_issue = next(issue for issue in result.report.issues if issue.json_path == "$.basics.email")
        self.assertEqual(required_issue.validator_name, "required")
        self.assertIn("Add `email`", required_issue.likely_next_action)

        typed_issue = next(issue for issue in result.report.issues if issue.json_path == "$.skills[0].keywords")
        self.assertEqual(typed_issue.validator_name, "type")
        self.assertEqual(typed_issue.failing_value, '"React"')

    def test_export_resume_rejects_unknown_formats(self) -> None:
        with self.assertRaises(ValueError):
            export_resume("txt")

    def _patched_resume_env(self, resume_json: str = RESUME_JSON):
        resume_path = Path("resume.json")
        resume_path.write_text(resume_json, encoding="utf-8")

        env_patch = patch.dict(
            os.environ,
            {"EMAIL": "zuri@example.com", "PHONE_NUMBER": "555-1212"},
            clear=False,
        )
        resume_patch = patch.object(core, "RESUME_JSON_PATH", str(resume_path))
        schema_patch = patch.object(core, "SCHEMA_PATH", self.repo_root / "schema.json")
        themes_patch = patch.object(core, "THEMES_DIR", self.repo_root / "themes")
        export_path_patch = patch.object(services, "_LAST_EXPORT_PATH", None)

        class _PatchedContext:
            def __enter__(self_inner):
                env_patch.start()
                resume_patch.start()
                schema_patch.start()
                themes_patch.start()
                export_path_patch.start()
                return self_inner

            def __exit__(self_inner, exc_type, exc, tb):
                export_path_patch.stop()
                themes_patch.stop()
                schema_patch.stop()
                resume_patch.stop()
                env_patch.stop()
                try:
                    resume_path.unlink()
                except FileNotFoundError:
                    pass
                return False

        return _PatchedContext()
