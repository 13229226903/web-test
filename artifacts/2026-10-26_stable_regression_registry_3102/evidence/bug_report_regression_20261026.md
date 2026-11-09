# 稳定回归 Bug 报告 — regression_registry @ http://10.17.1.66:3102

> 环境基线：测试服 http://10.17.1.66:3102，PC 1920x1080 / 移动端按各脚本口径，en-US / zh-CN 按脚本登记，Chrome headless；账号按各用例前置；素材 test_images/
> 来源：`artifacts/2026-10-26_stable_regression_registry_3102/regression_report.md`
> 最终 Allure：`artifacts/2026-10-26_stable_regression_registry_3102/allure-report-final-20261026-190014/index.html`
> 续跑日志：`artifacts/2026-10-26_stable_regression_registry_3102/logs-resume/`

---

## BUG-REG-3102-001 — AI Image Text Enhancer 点数规则与需求不一致，Enhance 按钮显示 10 而非 25

- 模块：AI Image Text Enhancer / Enhance 面板点数规则
- 类型：产品缺陷候选（点数规则）
- 优先级：P0
- 对应用例：`tests/test_ai_image_text_enhancer_experiment.py::test_text_l4_cost_refresh_and_rules`
- 前置：登录具备 Pro / 单项购买态的测试账号，进入 `/tools/ai-image-text-enhancer` 上传素材并打开 Enhance 面板

[步骤]
1. 打开 AI Image Text Enhancer 页面并进入可提交 Enhance 的状态。
2. 选择对应模式 / 分辨率组合。
3. 查看 Enhance 主按钮点数与 `cost_state`。

[结果]
- 断言期望按钮点数为 `25`，实际为 `10`。
- 实际按钮文案：`Enhance 10`。
- 实际 `cost_state=paid`。
- 日志：`logs-resume/01_ai_image_text_enhancer.log`

[期望]
- 点数应严格匹配 confirmed cases 中登记的点数规则；本次预期为 `25`。

---

## BUG-REG-3102-002 — AI Image Text Enhancer 免费试用态未显示 Free，仍为 paid

- 模块：AI Image Text Enhancer / 免费试用展示
- 类型：产品缺陷候选（账号态 / 免费额度）
- 优先级：P1
- 对应用例：`tests/test_ai_image_text_enhancer_experiment.py::test_text_l4_free_trial_display_free`
- 前置：模拟 / 选择免费试用额度可用账号态，进入 AI Image Text Enhancer Enhance 面板

[步骤]
1. 进入 AI Image Text Enhancer 页面。
2. 使用免费试用额度账号态进入 Enhance 面板。
3. 查看按钮文案与 `cost_state`。

[结果]
- 断言期望 `state2 == "free"` 且按钮文案为 `Free`。
- 实际 `state2 == "paid"`。
- 日志：`logs-resume/01_ai_image_text_enhancer.log`

[期望]
- 免费试用额度可用时，按钮应显示 `Free` 且状态为 `free`。

---

## BUG-REG-3102-003 — AI Image Text Enhancer 单项购买账号点数规则显示 10，期望 25

- 模块：AI Image Text Enhancer / 单项购买账号点数规则
- 类型：产品缺陷候选（点数规则）
- 优先级：P0
- 对应用例：`tests/test_ai_image_text_enhancer_experiment.py::test_text_l4_single_purchase_cost_rules`
- 前置：登录单项购买账号，进入 AI Image Text Enhancer Enhance 面板

[步骤]
1. 登录单项购买账号。
2. 进入 AI Image Text Enhancer 并打开可提交 Enhance 状态。
3. 查看 Enhance 主按钮点数与 `cost_state`。

[结果]
- 断言期望按钮点数为 `25`，实际为 `10`。
- 实际按钮文案：`Enhance 10`。
- 实际 `cost_state=paid`。
- 日志：`logs-resume/01_ai_image_text_enhancer.log`

[期望]
- 单项购买账号点数规则应与 confirmed cases 一致；本次预期为 `25`。

---

## BUG-REG-3102-004 — PC Batch Remove Background 完成后未自动选中 Change BG

- 模块：PC Batch Edit / Remove Background 后续流程
- 类型：产品缺陷候选（状态迁移）
- 优先级：P1
- 对应用例：`tests/test_pokecut_pc_batch_v1.py::TestL2BatchInteractions::test_l2_006_changebg_colors`
- 前置：进入 Batch Edit，完成 Remove Background

[步骤]
1. 进入 `/batch-edit/edit?pid=<uuid>`。
2. 完成 Remove Background。
3. 观察完成后的默认选中项。

[结果]
- 断言 `is_text_selected(page, "Change BG")` 为 False。
- 页面完成后未自动选中 `Change BG`。
- 日志：`logs-resume/03_pc_batch_v1.log`

[期望]
- Remove Background 完成后应自动选中 `Change BG`，以便继续背景替换流程。

---

## BUG-REG-3102-005 — PC Batch Enhance 页面出现 Network error，未进入正常分辨率/提交态

- 模块：PC Batch Edit / Enhance
- 类型：环境不稳定 / 产品缺陷候选（需复现确认）
- 优先级：P1
- 对应用例：
  - `tests/test_pokecut_pc_batch_v1.py::TestL2BatchInteractions::test_l2_008_enhance_modes_submit`
  - `tests/test_pokecut_pc_batch_v1.py::TestL6BatchSmoke::test_l6_002_smoke_enhance_resize_download`
- 前置：进入 Batch Edit，打开 Enhance 面板

[步骤]
1. 进入 Batch Edit 并选择 Enhance。
2. 查看面板状态与分辨率信息。
3. 尝试提交 Enhance。

[结果]
- 页面显示 `Network error`，出现 `Cancel / Try again`。
- 断言期望页面包含 `1200px * 1600px`，实际页面上未出现该信息。
- 日志：`logs-resume/03_pc_batch_v1.log`

[期望]
- Enhance 面板应正常加载分辨率信息并允许提交；若为环境问题，后端稳定后应复跑确认。

---

## BUG-REG-3102-006 — Canvas Stats PC 新画布未触发 Yearly Ultra Debug 跳过购买流程

- 模块：Canvas Stats / PC 新画布 / 购买跳过
- 类型：产品缺陷候选 / 测试流程阻塞
- 优先级：P1
- 对应用例：
  - `tests/test_canvas_stats_all.py::test_p_new_10`
  - `tests/test_canvas_stats_all.py::test_p_new_11`
- 前置：PC 新画布场景，使用 Debug 跳过真实 purchase 流程

[步骤]
1. 进入 PC 新画布目标功能。
2. 触发购买 / 付费拦截。
3. 选择 Yearly Ultra。
4. 尝试通过 Debug 跳过真实购买以继续统计校验。

[结果]
- `debug_skip_flow(page, plan_name="Ultra")` 返回 False。
- 断言：`PC 新画布未触发 Yearly Ultra Debug 跳过购买`。
- 日志：`logs-resume/10_canvas_stats_all.log`

[期望]
- 购买拦截出现后，Yearly Ultra 应可通过 Debug 跳过真实购买，流程继续到统计校验。

---

## BUG-REG-3102-007 — Canvas Stats 移动端核心注册埋点漏报

- 模块：Canvas Stats / 移动端注册 / 埋点
- 类型：产品缺陷候选（埋点漏报）
- 优先级：P0
- 对应用例：`tests/test_canvas_stats_all.py::test_m_core_01`
- 前置：移动端画布页，触发核心注册埋点

[步骤]
1. 移动端进入画布页。
2. 触发“核心触发注册”流程。
3. 检查 `sendGaEvent`。

[结果]
- 期望 `sendGaEvent` 为 1，实际为 0。
- 当前捕获事件中缺少 `core_register` 对应事件。
- 日志：`logs-resume/10_canvas_stats_all.log`

[期望]
- 移动端核心注册触发时，应准确发送 1 次 `sendGaEvent`，不应漏报。

---

## BUG-REG-3102-008 — Canvas Stats 移动端 enhance 未弹出注册弹窗

- 模块：Canvas Stats / 移动端注册弹窗
- 类型：产品缺陷候选（弹窗未出现 / 状态迁移失败）
- 优先级：P1
- 对应用例：`tests/test_canvas_stats_all.py::test_m_core_02`
- 前置：移动端画布页，匿名态触发 enhance 注册流程

[步骤]
1. 移动端进入画布页。
2. 选择 enhance 功能并触发注册流程。
3. 检查邮箱输入框是否出现。

[结果]
- `input[type=email]` count 为 0。
- 断言：`enhance 未出现注册弹窗`。
- 日志：`logs-resume/10_canvas_stats_all.log`

[期望]
- enhance 功能触发注册时应弹出注册弹窗，并显示邮箱输入框。

---

## BUG-REG-3102-009 — Canvas Stats 移动端弹窗出现埋点缺失

- 模块：Canvas Stats / 移动端弹窗埋点
- 类型：产品缺陷候选（埋点漏报）
- 优先级：P1
- 对应用例：`tests/test_canvas_stats_all.py::test_m_core_05`
- 前置：移动端画布页，触发弹窗出现场景

[步骤]
1. 移动端进入目标画布状态。
2. 触发弹窗出现。
3. 检查预期 `sendGaEvent` 计数。

[结果]
- `assert_event_pair` 失败：预期事件计数为 1，实际缺失 / 为 0。
- 日志：`logs-resume/10_canvas_stats_all.log`

[期望]
- 弹窗出现时应准确发送对应 `sendGaEvent`，不得漏报。

---

## BUG-REG-3102-010 — Canvas Stats 已知购买埋点缺陷 XPASS，预期与实际反转需确认修复状态

- 模块：Canvas Stats / 新画布购买埋点
- 类型：已知缺陷状态变化（XPASS strict）
- 优先级：P1
- 对应用例：
  - `tests/test_canvas_stats_all.py::test_p_new_16`
  - `tests/test_canvas_stats_all.py::test_m_new_14`
- 前置：新画布换背 / 背景功能，触发购买事件采集
- 关联已知缺陷：`BUG-2026-1012-01`

[步骤]
1. 进入对应新画布功能。
2. 触发换背 / 背景流程。
3. 采集 `新画布换背购买出现en_background-changer` 事件。

[结果]
- 用例以 `XPASS(strict)` 失败，说明原预期失败条件未发生。
- 原已知缺陷为：上传进画布瞬间自动弹购买窗，事件不再发出，actions 为空。
- 本次 XPASS 表示该缺陷可能已修复或页面行为发生变更。
- 日志：`logs-resume/10_canvas_stats_all.log`

[期望]
- 若缺陷已修复，应移除 / 更新 `xfail(strict=True)` 并同步 cases；若只是环境或数据态变化，应重新确认。

---

## BUG-REG-3102-011 — Old Canvas AI Tools 预设选择组失败

- 模块：Legacy Canvas / AI Tools / 预设选择类功能
- 类型：产品缺陷候选 / selector 漂移候选
- 优先级：P1
- 对应用例：`tests/test_old_canvas_ai_tools_all.py::test_p_ait_01_preset_select_group`
- 前置：进入旧画布 AI Tools，选择预设选择类工具

[步骤]
1. 进入 `/create/edit?pid=<uuid>#`。
2. 打开左侧 AI Tools。
3. 选择预设选择类功能并执行预设 / 提交 / 结果态校验。

[结果]
- 用例失败。
- 详细断言栈见 `logs-resume/11_old_canvas_ai_tools_all.log`。

[期望]
- 预设选择组应能正常完成预设选择、提交、结果态和确认/取消态校验。

---

## BUG-REG-3102-012 — Old Canvas AI Tools 模式+分类组失败

- 模块：Legacy Canvas / AI Tools / 模式+分类类功能
- 类型：产品缺陷候选 / selector 漂移候选
- 优先级：P1
- 对应用例：`tests/test_old_canvas_ai_tools_all.py::test_p_ait_02_mode_and_category_group`
- 前置：进入旧画布 AI Tools，选择模式+分类类工具

[步骤]
1. 进入 `/create/edit?pid=<uuid>#`。
2. 打开左侧 AI Tools。
3. 选择模式+分类类功能，覆盖 Manual / Smart Auto 等路径。
4. 校验提交、结果态和结束判据。

[结果]
- 用例失败。
- 详细断言栈见 `logs-resume/11_old_canvas_ai_tools_all.log`。

[期望]
- 模式+分类组应能正常完成模式选择、分类切换、提交、结果态和确认/取消态校验。

---

## BUG-REG-3102-013 — Portrait Detector 结果等待超时

- 模块：Portrait Detector / Ethnicity / Body Shape / Face Comparison 结果态
- 类型：环境不稳定 / 后端结果异常
- 优先级：P1
- 对应用例：
  - `tests/test_pokecut_portrait_detector.py::TestL2Interaction::test_l2_003_ethnicity_result`
  - `tests/test_pokecut_portrait_detector.py::TestL2Interaction::test_l2_004_body_result`
  - `tests/test_pokecut_portrait_detector.py::TestL2Interaction::test_l2_005_face_result`
  - `tests/test_pokecut_portrait_detector.py::TestL2Interaction::test_l2_006_download_questionnaire`
  - `tests/test_pokecut_portrait_detector.py::TestL2Interaction::test_l2_007_unsaved_report`
  - `tests/test_pokecut_portrait_detector.py::TestL2Interaction::test_l2_008_try_my_photo`
- 前置：上传对应素材并触发检测类任务

[步骤]
1. 打开对应 Portrait Detector 页面。
2. 上传素材并提交检测。
3. 等待结果态函数满足。

[结果]
- `Page.wait_for_function` 超时，超时 60s / 90s / 120s / 150s 不等。
- 日志：`logs-resume/14_portrait_detector.log`

[期望]
- 检测任务应在脚本等待窗口内返回结果态；若后端任务确实失败，应提供可区分的错误态。

---

## BUG-REG-3102-014 — Portrait Detector 匿名上传未出现 auth modal

- 模块：Portrait Detector / 匿名权限
- 类型：产品缺陷候选（权限态）
- 优先级：P1
- 对应用例：`tests/test_pokecut_portrait_detector.py::TestL3Exception::test_l3_001_anonymous_auth`
- 前置：匿名态，打开 `/tools/ethnicity-guesser-ai`

[步骤]
1. 匿名打开 `/tools/ethnicity-guesser-ai`。
2. 上传素材。
3. 检查 `auth-dialog` 是否出现。

[结果]
- `[data-testid="auth-dialog"]` count 为 0。
- 断言：上传后应出现 auth modal。
- 日志：`logs-resume/14_portrait_detector.log`

[期望]
- 匿名上传检测类任务时，应按权限规则弹出登录 / 注册 auth modal。

---

## BUG-REG-3102-015 — Portrait Detector 无人脸 / 多人脸异常态未出现

- 模块：Portrait Detector / 异常态
- 类型：产品缺陷候选（异常分支）
- 优先级：P1
- 对应用例：
  - `tests/test_pokecut_portrait_detector.py::TestL3Exception::test_l3_004_noface`
  - `tests/test_pokecut_portrait_detector.py::TestL3Exception::test_l3_005_multiface`
- 前置：上传无脸图 / 多脸图并触发检测

[步骤]
1. 上传无人脸素材，等待 `No Face Found`。
2. 上传多人脸素材，等待 `Choose a Face to Analyze`。

[结果]
- 无人脸用例：`No Face Found` 未出现，90s / 60s 等待超时。
- 多人脸用例：`Choose a Face to Analyze` 未出现，90s 等待超时。
- 日志：`logs-resume/14_portrait_detector.log`

[期望]
- 无人脸时应显示 `No Face Found`；多人脸时应显示 `Choose a Face to Analyze`。

---

## 汇总

| Bug | 对应用例 / 脚本 | 模块 | 类型 | 优先级 |
|---|---|---|---|---|
| BUG-REG-3102-001 | AI Image Text Enhancer cost refresh | AI Image Text Enhancer | 点数规则 | P0 |
| BUG-REG-3102-002 | AI Image Text Enhancer free trial | AI Image Text Enhancer | 免费额度 / 账号态 | P1 |
| BUG-REG-3102-003 | AI Image Text Enhancer single purchase | AI Image Text Enhancer | 点数规则 | P0 |
| BUG-REG-3102-004 | PC Batch changebg colors | Batch Edit | 状态迁移 | P1 |
| BUG-REG-3102-005 | PC Batch enhance submit / smoke | Batch Edit | 环境 / 网络错误 | P1 |
| BUG-REG-3102-006 | Canvas Stats p_new_10 / p_new_11 | Canvas Stats | 购买跳过 | P1 |
| BUG-REG-3102-007 | Canvas Stats m_core_01 | Canvas Stats | 埋点漏报 | P0 |
| BUG-REG-3102-008 | Canvas Stats m_core_02 | Canvas Stats | 弹窗未出现 | P1 |
| BUG-REG-3102-009 | Canvas Stats m_core_05 | Canvas Stats | 埋点漏报 | P1 |
| BUG-REG-3102-010 | Canvas Stats p_new_16 / m_new_14 | Canvas Stats | 已知缺陷 XPASS | P1 |
| BUG-REG-3102-011 | Old Canvas AI Tools p_ait_01 | Legacy Canvas AI Tools | 产品 / selector | P1 |
| BUG-REG-3102-012 | Old Canvas AI Tools p_ait_02 | Legacy Canvas AI Tools | 产品 / selector | P1 |
| BUG-REG-3102-013 | Portrait Detector result waits | Portrait Detector | 环境 / 结果异常 | P1 |
| BUG-REG-3102-014 | Portrait Detector anonymous auth | Portrait Detector | 权限态 | P1 |
| BUG-REG-3102-015 | Portrait Detector noface / multiface | Portrait Detector | 异常态 | P1 |
