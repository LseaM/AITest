#!/usr/bin/env python3
"""Validate the requirement-to-Casebook workflow and its traceability gates."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schema"
REQUIRED_SECTIONS = [
    "范围",
    "角色",
    "主流程",
    "原子需求",
    "业务规则",
    "状态流转",
    "权限",
    "输入校验",
    "接口约束",
    "异常流程",
    "非功能要求",
    "验收标准",
    "假设",
    "待确认问题",
]
REQ_PATTERN = re.compile(r"\bREQ_[A-Z0-9_]{3,}_[0-9]{3}\b")
VAGUE_RESULTS = {
    "正常",
    "正确",
    "成功",
    "操作成功",
    "处理成功",
    "保存成功",
    "显示正常",
    "功能正常",
    "系统正常",
    "结果正确",
}


class WorkflowValidator:
    def __init__(self, requirement_dir: Path, case_dir: Path | None, spec_only: bool):
        self.requirement_dir = requirement_dir.resolve()
        self.case_dir = case_dir.resolve() if case_dir else None
        self.spec_only = spec_only
        self.errors: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    @staticmethod
    def load_json(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8"))

    def load_yaml(self, path: Path) -> Any:
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            self.error(f"{path}: YAML 读取失败：{exc}")
            return None

    def schema_validate(self, data: Any, schema_name: str, label: str) -> None:
        schema = self.load_json(SCHEMA_DIR / schema_name)
        validator = Draft7Validator(schema, format_checker=FormatChecker())
        for issue in sorted(validator.iter_errors(data), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path) or "<root>"
            self.error(f"{label}: Schema 错误 [{location}] {issue.message}")

    def parse_spec(self) -> tuple[dict[str, Any], str, set[str]]:
        path = self.requirement_dir / "spec.md"
        if not path.is_file():
            self.error(f"缺少 Spec：{path}")
            return {}, "", set()
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            self.error(f"{path}: 读取失败：{exc}")
            return {}, "", set()
        match = re.match(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", text, re.DOTALL)
        if not match:
            self.error(f"{path}: 缺少有效 YAML Front Matter")
            return {}, text, set()
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
        except yaml.YAMLError as exc:
            self.error(f"{path}: Front Matter 解析失败：{exc}")
            return {}, text, set()
        self.schema_validate(metadata, "spec-frontmatter-schema.json", str(path))
        if not isinstance(metadata, dict):
            self.error(f"{path}: Front Matter 顶层必须是对象")
            metadata = {}

        body = text[match.end() :]
        sections = self.extract_sections(body)
        for section in REQUIRED_SECTIONS:
            if section not in sections:
                self.error(f"{path}: 缺少二级章节“{section}”")

        req_section = sections.get("原子需求", "")
        req_ids = REQ_PATTERN.findall(req_section)
        self.check_duplicates(req_ids, "原子需求 ID")
        if not req_ids:
            self.error(f"{path}: 原子需求章节至少需要一个 REQ ID")

        declared_sources = metadata.get("source_files", []) if isinstance(metadata, dict) else []
        for relative in declared_sources:
            source = (self.requirement_dir / relative).resolve()
            try:
                source.relative_to(self.requirement_dir)
            except ValueError:
                self.error(f"{path}: 来源路径越出需求目录：{relative}")
                continue
            if not source.is_file():
                self.error(f"{path}: 声明的来源文件不存在：{relative}")

        status = metadata.get("status")
        reviewer = metadata.get("reviewer")
        reviewed_at = metadata.get("reviewed_at")
        if not self.spec_only:
            if status != "approved":
                self.error(f"{path}: Spec 状态必须为 approved，当前为 {status!r}")
            if not reviewer or not reviewed_at:
                self.error(f"{path}: approved Spec 必须填写 reviewer 和 reviewed_at")
            questions = sections.get("待确认问题", "")
            if self.has_unresolved_content(questions):
                self.error(f"{path}: approved Spec 仍包含未解决的待确认问题")
        return metadata, body, set(req_ids)

    @staticmethod
    def extract_sections(body: str) -> dict[str, str]:
        matches = list(re.finditer(r"^##\s+(.+?)\s*$", body, re.MULTILINE))
        sections: dict[str, str] = {}
        for index, match in enumerate(matches):
            name = match.group(1).strip()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
            sections[name] = body[match.end() : end].strip()
        return sections

    @staticmethod
    def has_unresolved_content(content: str) -> bool:
        normalized = re.sub(r"[\s#>*`_\-]", "", content)
        return bool(normalized and normalized not in {"无", "暂无", "无。", "暂无。"})

    def check_duplicates(self, values: list[str], label: str) -> None:
        duplicates = sorted(value for value, count in Counter(values).items() if count > 1)
        if duplicates:
            self.error(f"{label} 重复：{', '.join(duplicates)}")

    def validate(self) -> list[str]:
        if not self.requirement_dir.is_dir():
            self.error(f"需求目录不存在：{self.requirement_dir}")
            return self.errors

        spec, _, req_ids = self.parse_spec()
        if self.spec_only:
            return self.errors

        points_path = self.requirement_dir / "test-points.yaml"
        trace_path = self.requirement_dir / "traceability.yaml"
        points = self.load_yaml(points_path) if points_path.is_file() else None
        trace = self.load_yaml(trace_path) if trace_path.is_file() else None
        if points is None:
            self.error(f"缺少或无法读取测试点：{points_path}")
        if trace is None:
            self.error(f"缺少或无法读取追踪矩阵：{trace_path}")
        if points is None or trace is None:
            return self.errors

        self.schema_validate(points, "test-points-schema.json", str(points_path))
        self.schema_validate(trace, "traceability-schema.json", str(trace_path))
        if not isinstance(points, dict):
            self.error(f"{points_path}: 顶层必须是对象")
        if not isinstance(trace, dict):
            self.error(f"{trace_path}: 顶层必须是对象")
        if not isinstance(points, dict) or not isinstance(trace, dict):
            return self.errors
        point_metadata = points.get("metadata", {})
        trace_metadata = trace.get("metadata", {})
        self.check_metadata_match(
            spec,
            point_metadata if isinstance(point_metadata, dict) else {},
            trace_metadata if isinstance(trace_metadata, dict) else {},
        )

        point_items = points.get("test_points", [])
        if not isinstance(point_items, list):
            point_items = []
        point_ids = [item.get("id") for item in point_items if isinstance(item, dict)]
        self.check_duplicates([value for value in point_ids if value], "测试点 ID")
        point_by_id = {item.get("id"): item for item in point_items if isinstance(item, dict) and item.get("id")}
        for point_id, point in point_by_id.items():
            for req_id in point.get("requirement_ids", []):
                if req_id not in req_ids:
                    self.error(f"{points_path}: {point_id} 引用了不存在的需求 {req_id}")

        cases = self.load_cases()
        case_ids = set(cases)
        mappings = trace.get("mappings", [])
        exemptions = trace.get("requirement_exemptions", [])
        if not isinstance(mappings, list):
            mappings = []
        if not isinstance(exemptions, list):
            exemptions = []
        mapping_keys: list[tuple[str, str, str]] = []
        mapped_reqs: set[str] = set()
        mapped_points: set[str] = set()
        mapped_cases: set[str] = set()
        mapped_req_points: set[tuple[str, str]] = set()

        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            req_id = mapping.get("requirement_id")
            point_id = mapping.get("test_point_id")
            case_id = mapping.get("test_case_id")
            mapping_keys.append((req_id, point_id, case_id))
            if req_id not in req_ids:
                self.error(f"{trace_path}: 映射引用不存在的需求 {req_id}")
            if point_id not in point_by_id:
                self.error(f"{trace_path}: 映射引用不存在的测试点 {point_id}")
            elif req_id not in point_by_id[point_id].get("requirement_ids", []):
                self.error(f"{trace_path}: {point_id} 未声明关联需求 {req_id}")
            if case_id not in case_ids:
                self.error(f"{trace_path}: 映射引用不存在的用例 {case_id}")
            mapped_reqs.add(req_id)
            mapped_points.add(point_id)
            mapped_cases.add(case_id)
            mapped_req_points.add((req_id, point_id))
        duplicate_mappings = [key for key, count in Counter(mapping_keys).items() if count > 1]
        if duplicate_mappings:
            self.error(f"{trace_path}: 存在重复映射 {duplicate_mappings}")

        exempt_reqs: set[str] = set()
        for exemption in exemptions:
            if not isinstance(exemption, dict):
                continue
            req_id = exemption.get("requirement_id")
            if req_id not in req_ids:
                self.error(f"{trace_path}: 豁免引用不存在的需求 {req_id}")
            exempt_reqs.add(req_id)
        self.check_duplicates([item.get("requirement_id") for item in exemptions if isinstance(item, dict)], "需求豁免")

        for req_id in sorted(req_ids - mapped_reqs - exempt_reqs):
            self.error(f"需求未覆盖且未豁免：{req_id}")
        for point_id, point in point_by_id.items():
            if point_id not in mapped_points:
                self.error(f"测试点未落到任何用例：{point_id}")
            for req_id in point.get("requirement_ids", []):
                if (req_id, point_id) not in mapped_req_points:
                    self.error(f"需求与测试点的声明关系未进入追踪矩阵：{req_id} -> {point_id}")
        for case_id in sorted(case_ids - mapped_cases):
            self.error(f"用例未被任何测试点支撑：{case_id}")
        return self.errors

    def check_metadata_match(self, spec: dict[str, Any], points: dict[str, Any], trace: dict[str, Any]) -> None:
        for label, metadata in (("测试点", points), ("追踪矩阵", trace)):
            if metadata.get("spec_id") != spec.get("spec_id"):
                self.error(f"{label} spec_id 与 Spec 不一致")
            if metadata.get("spec_version") != spec.get("version"):
                self.error(f"{label} spec_version 与 Spec 不一致")

    def load_cases(self) -> dict[str, tuple[Path, dict[str, Any]]]:
        if self.case_dir is None or not self.case_dir.is_dir():
            self.error(f"用例目录不存在：{self.case_dir}")
            return {}
        cases: dict[str, tuple[Path, dict[str, Any]]] = {}
        duplicate_signatures: dict[str, str] = {}
        yaml_files = sorted([*self.case_dir.rglob("*.yaml"), *self.case_dir.rglob("*.yml")])
        if not yaml_files:
            self.error(f"用例目录没有 YAML 文件：{self.case_dir}")
        for path in yaml_files:
            data = self.load_yaml(path)
            if data is None:
                continue
            self.schema_validate(data, "test-case-schema.json", str(path))
            case_items = data.get("test_cases", []) if isinstance(data, dict) else []
            if not isinstance(case_items, list):
                case_items = []
            for case in case_items:
                if not isinstance(case, dict):
                    continue
                case_id = case.get("id")
                if case_id in cases:
                    self.error(f"测试用例 ID 重复：{case_id}（{cases[case_id][0]} 与 {path}）")
                elif case_id:
                    cases[case_id] = (path, case)
                expected_results = case.get("expected_results", [])
                if not isinstance(expected_results, list):
                    expected_results = []
                for result in expected_results:
                    if not isinstance(result, str):
                        continue
                    normalized = re.sub(r"[\s，。！？；：,.!?:;]", "", result)
                    if normalized in VAGUE_RESULTS:
                        self.error(f"{path}: {case_id} 包含模糊预期结果：{result!r}")
                signature = json.dumps(
                    [case.get("title"), case.get("preconditions", []), case.get("steps", []), case.get("expected_results", [])],
                    ensure_ascii=False,
                    sort_keys=True,
                )
                if signature in duplicate_signatures:
                    self.error(f"明显重复用例：{duplicate_signatures[signature]} 与 {case_id}")
                elif case_id:
                    duplicate_signatures[signature] = case_id
        return cases


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirement-dir", required=True, type=Path, help="包含 spec.md 的需求目录")
    parser.add_argument("--case-dir", type=Path, help="包含 Casebook YAML 的版本目录")
    parser.add_argument("--spec-only", action="store_true", help="仅校验 Spec 结构和来源，不要求 approved")
    args = parser.parse_args()
    if not args.spec_only and args.case_dir is None:
        parser.error("完整校验必须提供 --case-dir；仅校验 Spec 请使用 --spec-only")
    return args


def main() -> int:
    args = parse_args()
    validator = WorkflowValidator(args.requirement_dir, args.case_dir, args.spec_only)
    errors = validator.validate()
    if errors:
        print(f"校验失败，共 {len(errors)} 项：")
        for index, error in enumerate(errors, 1):
            print(f"{index}. {error}")
        return 1
    print("校验通过：Spec、测试点、Casebook 用例和追踪关系均满足门禁。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
