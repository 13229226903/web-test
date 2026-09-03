# Shared Contract（角色与主控共享）

> 本文件只放所有角色都要遵守的共享约束；主控专属规则（任务声明 / 状态机 / Gate / 上下文控制）见 `artifacts/runtime/orchestrator.md`。

## 共享红线

- 不删断言、不弱化断言、不把 expected 改成空 / `0` / `-` 来让测试通过。
- selector 优先 ID、role、稳定属性、文本；禁用 hash class、`:nth-child`、位置 XPath。
- 按钮交互必须引用 `page_map.states.<state>.buttons.<button_id>`。
- 不把需求实现错误记为 `skipped`；`skipped` 仅用于环境、数据、权限、授权或不可逆风险。
- 不执行未授权的删除、清空、注销、覆盖业务数据、对外通知、影响真实用户或不可逆提交。
- 生成 / 购买 / 订阅 / credits 探索遵守项目账号和环境规则，并记录实际环境与状态变化。
- 上传素材只能使用 `test_images/` 现有文件。
- `seo-new-pages` 仅在用户明确要求 SEO 新页检测时使用。

## Artifact 接力

- 角色之间只通过版本化 artifact 传递上下文；历史版本不覆盖、不删除，新产物用下一版本号。
- 归档确认后，允许按 orchestrator 的 archive-cleanup 规则清理未被引用的截图、snapshot、临时下载等中间产物；被引用证据与版本化正式 artifact 仍不得删除。
- 产物路径 `artifacts/<task_id>/...`；长输出先落盘，对话只留不超过 50 行的摘要和路径。
- 上一个 artifact 未达 `completed` / `confirmed` 不得接力；`pending_review` 必停等待用户。
- 同一 artifact 单写者；其他角色只读或创建新版本文件，不得并发修改。
- review / visual-review 只读，结论以 verdict / review note 写回独立文件。
- pytest / Allure 报告按用例矩阵输出：测试标题、参数化 id、labels 至少带 `case_id`。

## Progress 与 Journal

- 每次 append：`[YYYY-MM-DD HH:MM:SS] <actor> <event>`；至少记录 start、route/step、wrote artifact、gate、done/blocked。
- journal 叙事层：`scripts/journal.py log --actor <actor> --action <action> --target <target> --why "<reason>"`，只增不改；任务起手写 `artifacts/.current_task` 指针，终态清除。

## 知识沉淀规则

- 沉淀对象：本项目**反复出现、可复用、能帮后续任务避开坑直接走正确路径**的技术经验；一次性探索产物、纯业务事实、已过时经验、未复现的一次性观察均不沉淀。
- 沉淀条件（同时满足）：
  1. 反复出现：同一坑出现 ≥2 次；或仅 1 次但高成本（长时间排查 / 大量返工）。
  2. 可复用：后续新任务大概率还会遇到。
  3. 避坑导向：给出正确路径 / 规避方式，而非纯事实描述。
  4. 有证据：有 stable_regression 资产或实际运行结果背书；无则标注「待验证」。
- 沉淀落点：跨页面通用 → `rule.md`；项目事实（账号/素材/环境）→ `PROJECT.md`；页面专属 → 对应 `page_map/<模块>/<页面>.yaml` 的 `notes`；角色执行规则 → 对应 `skills/<role>/SKILL.md`；数据 → `data/*.yaml`。
- 触发时机：**归档前**。踩坑角色收集候选沉淀项，由 orchestrator 在 regression-archive gate 前汇总并向用户询问「是否需要沉淀」；用户确认后才写落点。
- 写入要求：标注来源（task_id / 验证方式 / 日期）；与 `regression_registry.md` 冲突时以 registry 为准，旧经验降级为「待验证」，不得当默认正确路径。

## 项目级约束指针

- Base URL、验证码、账号、素材白名单、DEBUG 开关文案等固定值不在此重复固化；全局账号 / 验证码 / 素材 / DEBUG 以 `PROJECT.md` 为准，通用编码与技术规则以 `rule.md` 为准。
- 账号态由探索结果（confirmed `sync.md` / `cases.md`）决定并写入任务级 `data/*.yaml`，探索与脚本阶段都据此取值，`conftest.py` 默认值仅兜底，不作为选账号依据。
- 任务级覆盖以对应任务的 `state.md`、`data/*.yaml` 和已确认 artifact 为准。
