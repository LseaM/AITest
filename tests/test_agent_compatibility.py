from __future__ import annotations

import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAMES = (
    "requirements-to-spec",
    "spec-to-test-points",
    "test-points-to-casebook",
)


class AgentCompatibilityTests(unittest.TestCase):
    def test_shared_skills_are_valid_for_codex_and_cursor(self) -> None:
        for name in SKILL_NAMES:
            with self.subTest(skill=name):
                path = ROOT / ".agents" / "skills" / name / "SKILL.md"
                text = path.read_text(encoding="utf-8")
                self.assertTrue(text.startswith("---\n"))
                frontmatter = yaml.safe_load(text.split("---", 2)[1])
                self.assertEqual(name, frontmatter["name"])
                self.assertIn("Codex or Cursor", frontmatter["description"])

    def test_cursor_always_applies_shared_workflow_rule(self) -> None:
        path = ROOT / ".cursor" / "rules" / "testing-workflow.mdc"
        text = path.read_text(encoding="utf-8")
        frontmatter = yaml.safe_load(text.split("---", 2)[1])
        self.assertTrue(frontmatter["alwaysApply"])
        self.assertIn("AGENTS.md", text)
        for name in SKILL_NAMES:
            self.assertIn(f"/{name}", text)

    def test_readme_documents_both_invocation_styles(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        for name in SKILL_NAMES:
            self.assertIn(f"${name}", text)
            self.assertIn(f"/{name}", text)

    def test_cursor_does_not_duplicate_shared_skills(self) -> None:
        self.assertFalse((ROOT / ".cursor" / "skills").exists())


if __name__ == "__main__":
    unittest.main()
