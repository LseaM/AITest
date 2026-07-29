from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml
from jsonschema import Draft7Validator

from scripts.validate_workflow import ROOT, SCHEMA_DIR, WorkflowValidator


class WorkflowValidatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.requirement_dir = self.root / "SPEC_LOGIN"
        self.case_dir = self.root / "pilot-login"
        shutil.copytree(ROOT / "docs" / "requirements" / "SPEC_LOGIN", self.requirement_dir)
        shutil.copytree(ROOT / "releases" / "pilot-login", self.case_dir)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def validate(self, spec_only: bool = False) -> list[str]:
        case_dir = None if spec_only else self.case_dir
        return WorkflowValidator(self.requirement_dir, case_dir, spec_only).validate()

    def load_yaml(self, path: Path):
        return yaml.safe_load(path.read_text(encoding="utf-8"))

    def save_yaml(self, path: Path, data) -> None:
        path.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def test_valid_example_passes_complete_validation(self) -> None:
        self.assertEqual([], self.validate())

    def test_spec_only_allows_draft_before_human_review(self) -> None:
        spec_path = self.requirement_dir / "spec.md"
        text = spec_path.read_text(encoding="utf-8")
        text = text.replace("status: approved", "status: draft")
        text = text.replace("reviewer: qa-reviewer", "reviewer: null")
        text = text.replace('reviewed_at: "2026-07-17"', "reviewed_at: null")
        spec_path.write_text(text, encoding="utf-8")
        self.assertEqual([], self.validate(spec_only=True))

    def test_full_validation_stops_unapproved_spec(self) -> None:
        spec_path = self.requirement_dir / "spec.md"
        text = spec_path.read_text(encoding="utf-8").replace("status: approved", "status: draft")
        spec_path.write_text(text, encoding="utf-8")
        errors = self.validate()
        self.assertTrue(any("状态必须为 approved" in error for error in errors))

    def test_missing_declared_source_fails(self) -> None:
        (self.requirement_dir / "sources" / "login-requirement.md").unlink()
        errors = self.validate()
        self.assertTrue(any("来源文件不存在" in error for error in errors))

    def test_broken_trace_reference_fails(self) -> None:
        fixture = ROOT / "tests" / "fixtures" / "invalid-trace-broken-reference.yaml"
        shutil.copyfile(fixture, self.requirement_dir / "traceability.yaml")
        errors = self.validate()
        self.assertTrue(any("映射引用不存在的用例" in error for error in errors))

    def test_orphan_test_point_fails(self) -> None:
        path = self.requirement_dir / "test-points.yaml"
        data = self.load_yaml(path)
        orphan = dict(data["test_points"][0])
        orphan["id"] = "TP_LOGIN_999"
        data["test_points"].append(orphan)
        self.save_yaml(path, data)
        errors = self.validate()
        self.assertTrue(any("测试点未落到任何用例：TP_LOGIN_999" in error for error in errors))

    def test_duplicate_case_id_fails(self) -> None:
        path = self.case_dir / "login.yaml"
        data = self.load_yaml(path)
        duplicate = dict(data["test_cases"][1])
        duplicate["title"] = "另一个标题"
        duplicate["id"] = data["test_cases"][0]["id"]
        data["test_cases"].append(duplicate)
        self.save_yaml(path, data)
        errors = self.validate()
        self.assertTrue(any("测试用例 ID 重复" in error for error in errors))

    def test_vague_expected_result_fails(self) -> None:
        path = self.case_dir / "login.yaml"
        data = self.load_yaml(path)
        data["test_cases"][0]["expected_results"] = ["操作成功"]
        self.save_yaml(path, data)
        errors = self.validate()
        self.assertTrue(any("模糊预期结果" in error for error in errors))

    def test_schema_invalid_top_level_returns_errors_without_crashing(self) -> None:
        (self.requirement_dir / "test-points.yaml").write_text("- invalid\n- top-level\n", encoding="utf-8")
        errors = self.validate()
        self.assertTrue(any("顶层必须是对象" in error for error in errors))

    def test_fixed_invalid_case_fixtures_fail_schema(self) -> None:
        schema = json.loads((SCHEMA_DIR / "test-case-schema.json").read_text(encoding="utf-8"))
        validator = Draft7Validator(schema)
        fixture_dir = ROOT / "tests" / "fixtures"
        for name in ("invalid-case-extra-field.yaml", "invalid-case-empty-steps.yaml"):
            with self.subTest(name=name):
                data = self.load_yaml(fixture_dir / name)
                self.assertTrue(list(validator.iter_errors(data)))


if __name__ == "__main__":
    unittest.main()
