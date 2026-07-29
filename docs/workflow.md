# Codex / Cursor 智能测试工作流使用说明

## 一次完整运行

1. 新建 `docs/requirements/<spec-id>/sources/`，放入原始需求和附件。
2. 在 Codex 中执行：`使用 $requirements-to-spec 整理 <spec-id> 的原始需求。`；在 Cursor Agent 中执行：`使用 /requirements-to-spec 整理 <spec-id> 的原始需求。`
3. 通过 Git PR 评审 `spec.md`。确认需求理解无误后，将 `status` 更新为 `approved`，填写评审人和日期。
4. Codex 使用 `$spec-to-test-points`，Cursor 使用 `/spec-to-test-points`，为 `<spec-id>` 生成测试点。
5. Codex 使用 `$test-points-to-casebook`，Cursor 使用 `/test-points-to-casebook`，生成 `<version>` 的 Casebook 用例和追踪矩阵。
6. 运行校验：

   ```powershell
   python scripts/validate_workflow.py `
     --requirement-dir docs/requirements/<spec-id> `
     --case-dir releases/<version>
   ```

7. 安装固定版本并启动 Casebook：

   ```powershell
   python -m pip install casebook==0.7.0
   casebook serve releases/<version>
   ```

8. 处理 `Needs update` 标记和备注，重新校验；完成最终 PR 审批后归档。

## 分阶段运行

- 只检查 Spec：`python scripts/validate_workflow.py --requirement-dir <目录> --spec-only`
- 检查完整闭环：同时传入 `--requirement-dir` 和 `--case-dir`。
- 校验器返回 `0` 表示通过，返回 `1` 表示存在门禁或质量错误。

## 评审约定

- `draft` 表示尚未人工确认；`needs_clarification` 表示存在阻塞问题；`approved` 只能由人工评审产生。
- Spec 评审关注需求理解、来源和假设；Casebook 评审关注风险覆盖、可执行性和预期结果。
- Casebook 标记用于提出修改，Git PR 用于形成最终审批和审计记录。
- 评审后不得重排 ID。新增内容使用新的尾号，删除内容通过 Git 历史追踪。

## 固定依赖

首期按 `casebook.lock` 固定 Casebook 版本和上游提交。升级时必须重新验证 Schema、示例用例、Web UI 加载和评审标记行为。

## 双端约定

- Codex 和 Cursor 必须从仓库根目录打开任务，确保能读取 `AGENTS.md`。
- 三个 Skill 的唯一来源是 `.agents/skills/`；不要复制到个人目录后单独修改。
- Cursor 使用 Agent 模式并通过 `/skill-name` 调用。更新或首次拉取 Skill 后，新建 Agent 对话；如果未显示，执行 `Developer: Reload Window`。
- Skill 未被自动发现时，两端都可以显式要求 Agent 读取 `AGENTS.md` 和对应 `SKILL.md` 后继续。
