# 智能测试工作流

本仓库同时支持 Codex 和 Cursor。AI Agent 负责把原始需求逐步转换为可评审、可追踪的测试资产。所有产物默认使用中文，字段名、枚举值和稳定 ID 使用英文。

Codex 使用 `$requirements-to-spec`、`$spec-to-test-points`、`$test-points-to-casebook` 调用 Skill；Cursor 在 Agent 模式使用 `/requirements-to-spec`、`/spec-to-test-points`、`/test-points-to-casebook`。两端共用 `.agents/skills/` 中的同一份 Skill，不得复制或维护工具专属版本。

## 固定流程

1. 将原始材料保存到 `docs/requirements/<spec-id>/sources/`，不得覆盖或改写来源文件。
2. 使用 `$requirements-to-spec` 生成或更新 `spec.md`。
3. 人工通过 Git PR 确认 Spec，将 `status` 改为 `approved`，并填写 `reviewer`、`reviewed_at`。
4. 使用 `$spec-to-test-points` 生成 `test-points.yaml`。
5. 使用 `$test-points-to-casebook` 生成 `releases/<version>/<feature>.yaml` 和 `traceability.yaml`。
6. 运行 `python scripts/validate_workflow.py --requirement-dir <需求目录> --case-dir <用例目录>`。
7. 使用 `casebook serve <用例目录>` 进行人工评审；当前使用的 AI Agent 根据 `Needs update` 标记和备注修订产物。
8. 校验通过、阻塞标记清零并完成最终 PR 审批后归档。

不得跳过 Spec 审批直接生成测试点或正式用例。存在阻塞级歧义、需求冲突、来源缺失或无法可靠解析的关键内容时，将 Spec 标记为 `needs_clarification` 并停止后续生成。

## 目录与接口

- `docs/requirements/<spec-id>/sources/`：原始 PRD、Markdown、Word、PDF、图片或附件。
- `docs/requirements/<spec-id>/spec.md`：带 YAML Front Matter 的结构化需求。
- `docs/requirements/<spec-id>/test-points.yaml`：测试点清单。
- `docs/requirements/<spec-id>/traceability.yaml`：`REQ -> TP -> TC` 独立追踪矩阵。
- `releases/<version>/<feature>.yaml`：符合 `schema/test-case-schema.json` 的 Casebook 用例。
- `evals/`：试点样本、基线和评审指标。

Schema 是结构字段的唯一事实来源。不得向 Casebook 用例添加 `requirement_ids`、`test_point_ids` 等非原生字段；追踪关系只能写入 `traceability.yaml`。

## 稳定 ID

- 原子需求：`REQ_<FEATURE>_<NNN>`
- 测试点：`TP_<FEATURE>_<NNN>`
- 测试用例：`TC_<FEATURE>_<NNN>`

已有 ID 不得因排序、插入或评审而改变。正式评审开始后禁止使用 Casebook 的 ID 重排功能。删除资产时保留 Git 历史，并同步清理或记录追踪关系。

## 质量门禁

- Spec 必须引用至少一个真实来源文件，且只有 `approved` 状态可进入后续阶段。
- 每条原子需求必须关联测试点，或在追踪矩阵中记录带理由的人工豁免。
- 每个测试点必须关联至少一个用例；每个用例必须由至少一个测试点支撑。
- P0 需求不得遗漏，不得把假设写成确认事实。
- 步骤必须是可执行动作；预期结果必须包含可观察的 UI、API、数据、事件、文件、日志或下游变化。
- 禁止空字段、重复 ID、无效枚举、断链引用、孤立资产、明显重复用例和“正常/正确/成功”等无具体观察点的模糊断言。

## 修改原则

- 修改现有需求时先读取来源、Spec、测试点、追踪矩阵和现有用例，保留仍有效的 ID。
- 需求版本变化时更新 `version` 和来源引用，重新运行完整校验。
- Casebook 页面仅做轻量编辑；新增、删除、拆分和重构用例应由 Codex 或 Cursor Agent 修改 YAML，并同步更新追踪矩阵。
- 未经人工确认，不得自动把待确认问题转为需求、测试点或用例。
