---
name: spec-to-test-points
description: Generate structured, risk-based, traceable YAML test points from an approved Spec. Use when an AI coding agent such as Codex or Cursor needs to convert atomic REQ items into normal, negative, boundary, permission, state-transition, data-consistency, or explicitly required non-functional coverage before writing Casebook test cases.
---

# Spec to Test Points

Create or update `test-points.yaml` beside an approved `spec.md`.

## Gate

1. Read `AGENTS.md`, the full Spec, and `schema/test-points-schema.json`.
2. Stop without producing or modifying test points unless `status` is `approved`, both reviewer fields are present, every declared source exists, and no unresolved blocking question remains.

## Workflow

1. Extract the complete set of atomic `REQ_*` IDs and their confirmed behavior.
2. Build a coverage map across `normal`, `negative`, `boundary`, `permission`, `state`, `data-consistency`, and `non-functional` categories. Include non-functional points only when the Spec establishes a measurable requirement or material risk.
3. Create focused test points with stable `TP_<FEATURE>_<NNN>` IDs. Preserve existing IDs and extend from the highest suffix.
4. Link every point to one or more `requirement_ids`; do not reference assumptions as requirements.
5. Set `risk` to `high`, `medium`, or `low`; set `priority` to `P0`, `P1`, or `P2`. Use P0 for release-blocking business, money, data, security, destructive, authentication, or authorization risk.
6. Explain `design_basis` using the requirement rule, boundary, state, permission, failure mode, or historical evidence that justifies the point.
7. Deduplicate points that exercise the same precondition, action, and observable outcome. Keep separate points when risk or setup materially differs.
8. Run the validator and resolve schema, duplicate, and reference errors.

## Output rules

- Keep scenarios implementation-neutral and testable.
- Do not invent numeric limits, error copy, permissions, API behavior, or state transitions absent from the approved Spec.
- If approved requirements remain untestable, stop and return the Spec to clarification rather than guessing.
- Do not write Casebook cases in this stage.
