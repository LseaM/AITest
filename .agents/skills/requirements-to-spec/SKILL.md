---
name: requirements-to-spec
description: Convert raw PRDs, Markdown, text, Word, PDF, images, API notes, UI notes, and requirement attachments into an auditable structured Spec with atomic requirement IDs, source references, assumptions, and blocking questions. Use when an AI coding agent such as Codex or Cursor needs to ingest or revise requirement material under docs/requirements before test-point generation.
---

# Requirements to Spec

Create `docs/requirements/<spec-id>/spec.md` from the immutable files in `sources/`.

## Workflow

1. Read `AGENTS.md` and `schema/spec-frontmatter-schema.json`.
2. Inventory every source file. Extract text without modifying originals; preserve file name plus page, section, heading, table, or image reference where available.
3. If a key source is unreadable, missing, contradictory, or depends on an unconfirmed interpretation, record a blocking question and set `status: needs_clarification`.
4. Normalize confirmed facts into the required Spec sections. Split requirements into atomic, independently testable statements.
5. Assign stable IDs in the form `REQ_<FEATURE>_<NNN>`. Preserve existing IDs when revising a Spec.
6. Keep inferred but useful ideas under `假设`; never present them as confirmed requirements.
7. Set a new Spec to `draft` unless blocking questions require `needs_clarification`. Never set `approved` on behalf of the reviewer.
8. Run the workflow validator in Spec-only mode and fix structural failures.

## Required document shape

Use YAML Front Matter with `spec_id`, `version`, `title`, `status`, `source_files`, `reviewer`, and `reviewed_at`. Use these Markdown sections in order:

1. `范围`
2. `角色`
3. `主流程`
4. `原子需求`
5. `业务规则`
6. `状态流转`
7. `权限`
8. `输入校验`
9. `接口约束`
10. `异常流程`
11. `非功能要求`
12. `验收标准`
13. `假设`
14. `待确认问题`

Write each atomic requirement as a heading or list item beginning with its ID, and include a nearby `来源：` reference. Use `无` when a section is confirmed to have no applicable content; do not omit the section.

## Gate

Finish by telling the reviewer which blocking questions remain and that Git PR approval must update the metadata. Do not invoke downstream Skills until the Spec status is `approved` and reviewer fields are populated.
