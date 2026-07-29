---
name: test-points-to-casebook
description: Convert approved structured test points into schema-valid Casebook YAML test cases and maintain an independent REQ-to-TP-to-TC traceability matrix. Use when an AI coding agent such as Codex or Cursor needs to create, extend, revise, or validate formal cases under releases/ while preserving stable IDs and Casebook compatibility.
---

# Test Points to Casebook

Generate Casebook YAML under `releases/<version>/` and update the requirement-local `traceability.yaml`.

## Gate

1. Read `AGENTS.md`, `spec.md`, `test-points.yaml`, all four schemas, and existing release YAML.
2. Stop unless the Spec is approved and the test-points file references the same `spec_id` and `spec_version`.

## Workflow

1. Expand every test point into the minimum set of executable cases required to cover its distinct setup, action, and observable outcome.
2. Use exactly the fields allowed by `schema/test-case-schema.json`. Never add requirement or test-point IDs to a case object.
3. Assign stable globally unique `TC_<FEATURE>_<NNN>` IDs. Preserve existing IDs when revising; do not renumber after review begins.
4. Write one business action per step. Put setup in `preconditions`.
5. Make every expected result independently observable through UI, API response, stored state, event, file, audit log, or downstream effect. Avoid bare claims such as “正常”“正确”“成功”.
6. Set priority from business risk, not execution order. Set `auto: true` only for stable, deterministic checks suitable for reliable automation.
7. Build `traceability.yaml` with one mapping row for each `REQ -> TP -> TC` relationship. Add requirement exemptions only when a reviewer and reason are recorded.
8. Validate the complete requirement directory and case directory. Fix all failures before handing off to Casebook.

## Human review loop

Run `casebook serve releases/<version>`. Treat `Needs update` marks and notes as revision requests. Apply structural changes in YAML, update the traceability matrix, rerun validation, and preserve IDs for unchanged cases. Final acceptance requires no blocking marks and Git PR approval.
