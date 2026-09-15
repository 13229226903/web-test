# 稳定回归 Bug 报告 — registry 全量 @ http://10.17.1.66:3001

> 环境基线：测试服 http://10.17.1.66:3001，PC 1920x1080 / 移动端 390x844，en-US，Chrome headless；VIP 450832596@qq.com / 123456；素材 test_images/
> 来源：`artifacts/2026-09-14_stable_regression_all_archived/report.md`（174 用例：161 passed / 10 failed / 3 skipped）
> 截图目录：`artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/`

---

## BUG-REG-001 — 移动端首页 hero 模型入口由 “Pokecut Pro” 变为新模型 “Auto”，默认模型被改变

- 模块：Pokecut 移动端首页（390x844）→ hero 区 AI 生成卡片
- 类型：产品变更未同步（新增模型导致默认模型变化）→ 需确认是否设计如此
- 优先级：P1（首页主入口文案/默认模型变更，影响入口一致性与存量用例）
- 对应用例：`test_mobile_home.py::TestL1PageStructure::test_l1_002_hero_copy`
- 前置：无登录，移动端视口打开首页

[步骤]
1. 移动端（390x844）打开 http://10.17.1.66:3001/
2. 定位 hero 区 AI 生成卡片，查看模型下拉入口的文案与默认选中项

[结果]
- `section.mobile-home-agent-hero button` 中 **不存在** 文案为 “Pokecut Pro” 的按钮；断言 5s 超时（element not found）。
- hero 区按钮实测为：`["Start Creating for Free", "", "Auto", "", "Generate"]`；模型下拉默认显示 **Auto**。
- 页面上 “Pokecut Pro” 仅作为 AI 生成模型列表中的一项存在（同列表另有 Seedream 5.0 Pro / Nano Banana 2 Lite / Nano Banana Pro / ChatGPT Image 2.0 / Nano Banana 2 / Seedream 5.0 Lite / Seedream4.0）。
- 结论与用户反馈一致：**新增模型后默认模型变为 “Auto”**，hero 入口不再固定展示 Pokecut Pro。

[期望]
- 明确默认模型策略：若 “Auto” 为设计默认，需同步更新 hero 入口文案与存量用例预期（L1-002 / L2-003）；若非预期，应恢复默认模型展示。
- 首页 hero 模型入口应保持稳定可定位（建议给入口稳定的 id / data-testid，而非依赖模型名文案）。

![BUG-REG-001 移动端首页 hero：模型入口默认 Auto，无 Pokecut Pro 按钮](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/mobile_home_hero_section.png)

---

## BUG-REG-002 — 移动端首页 hero 模型入口点击后弹层无法打开

- 模块：Pokecut 移动端首页 → hero 模型下拉
- 类型：产品缺陷/用例漂移（依赖 BUG-REG-001 的入口文案）
- 优先级：P1
- 对应用例：`test_mobile_home.py::TestL2Interactions::test_l2_003_model_popover`
- 前置：移动端视口打开首页

[步骤]
1. 移动端打开首页
2. 点击 hero 区 “Pokecut Pro” 模型按钮，期望弹出模型选择弹层

[结果]
- 按钮定位失败，`Locator.click` 15s 超时（waiting for `section.mobile-home-agent-hero button`.filter(has_text="Pokecut Pro")）。
- 弹层未打开，无法验证模型切换交互。

[期望]
- 模型入口点击后应正常弹出模型选择弹层；入口文案/默认模型按 BUG-REG-001 结论统一后，本用例的模型切换验证应可执行。

![BUG-REG-002 移动端首页 hero 区现状（模型入口为 Auto 下拉，点击后无 Pokecut Pro 弹层）](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/mobile_home_model_entry_clicked.png)

---

## BUG-REG-003 — 移动端首页效果模板入口 “Butt” 按钮不存在

- 模块：Pokecut 移动端首页 → 效果模板/工具入口区
- 类型：用例漂移 / 产品入口变更（待确认）
- 优先级：P2
- 对应用例：`test_mobile_home.py::TestL2Interactions::test_l2_010_effect_template`
- 前置：移动端视口打开首页

[步骤]
1. 移动端打开首页
2. 定位 `get_by_role("button", name="Butt")` 并点击以进入效果模板上传

[结果]
- 页面上匹配 “Butt” 的按钮数为 **0**，`Locator.click` 15s 超时。
- 首页实测按钮集合：`Start Creating for Free / Auto / Generate / AI Replace / All Tools / Background / Body / Body Editor / Clothes Changer / Face / HD Enhance / HD Photo Coverter / Hair / Home / ID Photo Maker / More Pokecut Tools / Portrait AI / Pricing / Remove Background / Text Enhance / Ultra Enhance` 等，无 “Butt”。

[期望]
- 确认该入口当前正式名称（疑似 “Body”/“Body Editor” 或已下线）；确认后同步用例 locator，或恢复入口。

![BUG-REG-003 移动端首页工具区现状（无 Butt 入口）](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/mobile_home_scrolled_tools.png)

---

## BUG-REG-004 — PC 首页 “Pokecut Pro” 按钮不存在，提示弹窗无法验证

- 模块：Pokecut PC 首页（1920x1080）
- 类型：产品变更未同步（同 BUG-REG-001 默认模型变更的 PC 侧表现）
- 优先级：P1
- 对应用例：`test_pokecut_pc_home_v6.py::TestL2Interactions::test_l2_008_prompt_popups`
- 前置：无登录，PC 打开首页

[步骤]
1. PC 打开 http://10.17.1.66:3001/
2. 定位 `button:has-text("Pokecut Pro")` 并滚动到可视区后点击，检查提示弹窗

[结果]
- `Locator.scroll_into_view_if_needed` 30s 超时（waiting for `locator("button").filter(has_text="Pokecut Pro").first`），按钮不存在。
- /create 页实测模型列表为：**Auto（默认）**、Seedream 5.0 Pro、Nano Banana 2 Lite、Pokecut Pro、Nano Banana Pro、ChatGPT Image 2.0、Nano Banana 2、Seedream 5.0 Lite、Seedream4.0 —— “Pokecut Pro” 已不是首页默认模型按钮。

[期望]
- 确认默认模型从 “Pokecut Pro” 改为 “Auto” 是否为设计；是则同步更新首页入口与用例，否则恢复。

![BUG-REG-004 PC 首页失败现场（找不到 Pokecut Pro 按钮）](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/tests-test-pokecut-pc-home-v6-py-testl2interactions-test-l2-008-prompt-popups-chromium/test-failed-1.png)

---

## BUG-REG-005 — Batch 编辑页删除控件无 “Delect/Delete” 文案（可访问名缺失）

- 模块：Pokecut PC 批量编辑页 → /batch-edit/edit 顶部工具栏
- 类型：产品缺陷（registry 已登记已知项：删除按钮文案 “Delect” 拼写错误）
- 优先级：P1（删除动作文案/可访问性，影响批量编辑主流程）
- 对应用例：`test_pokecut_pc_batch_v1.py::TestL1BatchStructure::test_l1_007_delete_label_bug`
- 前置：VIP 登录，上传 2 张图进入 /batch-edit/edit?pid=`<uuid>`

[步骤]
1. VIP 登录后进入 /batch
2. 点击 “Upload Images” 上传 test_images/1K.jpg、test_images/无人脸.jpg，进入批量编辑页
3. 在顶部工具栏查看删除按钮文案（用例按 role=button, name="Delect" 定位）

[结果]
- `get_by_role("button", name="Delect").last.inner_text()` 30s 超时，页面不存在可访问名含 “Delect” 的按钮。
- 全页检索：body 文本既不含 “Delect” 也不含 “Delete”；顶部工具栏的删除是**纯图标按钮（垃圾桶图标）**，`aria-label` / `title` 均为空，`<button>` 集合中也无该项（顶部图标为非 button 元素）。
- 因此用例既无法断言文案为 “Delete”，也无法证明拼写已修复。

[期望]
- 删除控件应提供明确的可见文案或 `aria-label`（“Delete”）；若已从文案按钮改为图标按钮，需同步更新用例定位并补充可访问名，保证批量删除流程可自动化验证。

![BUG-REG-005 Batch 编辑页删除控件（顶部垃圾桶图标，无可访问名）](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/batch_edit_with_images.png)

---

## BUG-REG-006 — Batch 删除流程无法执行

- 模块：Pokecut PC 批量编辑页 → 删除流程
- 类型：产品缺陷（与 BUG-REG-005 同源）
- 优先级：P1
- 对应用例：`test_pokecut_pc_batch_v1.py::TestL2BatchInteractions::test_l2_011_delete_flow`
- 前置：VIP 登录，批量编辑页已载入图片

[步骤]
1. 进入 /batch 并上传图片进入批量编辑页
2. 选中图片，点击删除按钮
3. 确认弹窗后校验图片数量减少

[结果]
- `session_page.get_by_role("button", name="Delect").click()` 30s 超时，删除流程无法进入，图片数量校验未执行。

[期望]
- 删除按钮可定位、可点击，弹出二次确认并正确删除所选图片。

![BUG-REG-006 Batch 编辑页（含删除控件）失败现场](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/batch_reopen_pid.png)

---

## BUG-REG-007 — Batch 下载流程被删除控件阻塞

- 模块：Pokecut PC 批量编辑页 → 下载流程
- 类型：产品缺陷（前置步骤复用删除控件，与 BUG-REG-005 同源）
- 优先级：P1
- 对应用例：`test_pokecut_pc_batch_v1.py::TestL2BatchInteractions::test_l2_012_download_flow`
- 前置：VIP 登录，批量编辑页已载入图片

[步骤]
1. 进入 /batch 并上传图片进入批量编辑页
2. 点击删除按钮（清理后再下载）
3. 点击 Download 校验下载

[结果]
- `session_page.get_by_role("button", name="Delect").click()` 30s 超时，用例在第 2 步中断，下载分支未执行。

[期望]
- 删除控件可定位后，下载分支可正常执行；或将该用例与删除动作解耦，避免被同源问题阻塞。

![BUG-REG-007 Batch 编辑页下载入口（下载分支被删除控件阻塞）](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/batch_landing.png)

---

## BUG-REG-008 — /create 首页 VIP 限时优惠弹窗遮挡 “Start from a Photo” 入口，导致入口点击被拦截

- 模块：Pokecut PC /create 首页 → Trending Tools 入口卡片
- 类型：产品缺陷（营销弹窗遮挡主入口，自动化与真实用户点击均被拦截）
- 优先级：P0（核心入口不可点，直接影响创建流程）
- 对应用例：`test_infinite_canvas_enhance_v4.py::TestL5ResolutionBoundaries::test_l5_001_resolution_default_matrix_and_8k_uncompressed`
- 前置：无登录（匿名）打开 /create

[步骤]
1. PC 打开 http://10.17.1.66:3001/create
2. 在 Trending Tools 区点击 “Start from a Photo” 卡片进入上传流程（用例执行 `upload_via_create`）

[结果]
- 目标卡片 DOM 存在（`div.cursor-pointer:has(p:text-is("Start from a Photo"))` 命中 1 个），但 `card.click(timeout=20000)` 20s 超时，点击始终不可完成。
- 现场截图显示：页面中央弹出 **“你是限时优惠：Unlock Pokecut VIP for just $1 USD”** 弹窗（Basic vs VIP 对比 + Get Started 按钮），**遮罩覆盖住 “Start from a Photo” 卡片**，点击被弹窗拦截。
- 该用例上一轮（2026-09-14 归档复跑）为 passed，本轮 12 脚本连续回归中出现，属新暴露的阻塞。

[期望]
- 营销弹窗不应拦截主入口点击：要么在弹窗出现时不阻塞底层入口，要么入口点击应先关闭弹窗后继续；或为弹窗提供可稳定关闭/跳过的处理。
- 自动化侧建议在进入 /create 后显式处理该弹窗（关闭后再点击入口），避免用例被营销弹窗随机阻塞。

![BUG-REG-008 /create 页 VIP 限时优惠弹窗遮挡 Start from a Photo 入口](D:/Test/web-test/artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/create_start_from_photo_card.png)

---

## BUG-REG-009 — Enhance Standard 4K 提交返回 -1002，任务未生成结果

- 模块：PC 无限画布 → Enhance 面板 → Standard(4K) 提交
- 类型：环境类（测试服后端临时问题，已于 2026-09-14 由用户确认为非产品缺陷）
- 优先级：P1（核心生成链路失败）
- 对应用例：`test_infinite_canvas_enhance_v4.py::TestL6EnhanceWorkflow::test_l6_002_standard_portrait_text_matrix`
- 前置：VIP(Pro) 登录，上传 test_images/低分辨率.JPG 进入画布

[步骤]
1. /create → Trending Tools → 上传图片进入无限画布
2. 打开 Enhance 面板，模式选 Standard，分辨率选 4k，提交
3. 等待结果图层生成

[结果]
- 提交后 Console 出现 `errorCode: -1002, errorMsg: 任务提交请求失败`、`task fail. e= Error: -1002`、`[CanvasTaskQueue] queued task failed: Error: Canvas Enhance TaskFlow failed`。
- 路由：`styleId=pkweb_comfyui_enhance_normal`，`resourceCode=picenhance_normal_4k`；未生成结果图层，用例 fail-fast 失败。

[期望]
- 测试服后端恢复后，Standard 4K 提交应正常返回任务结果；若仍为 -1002 则按真实缺陷处理。

![BUG-REG-009 Standard 4K 提交失败现场](D:/Test/web-test/artifacts/2026-09-09_task-33_canvas_enhance_optimization/shots/enhance_task_failure_long_4096.png)

---

## BUG-REG-010 — Enhance Standard 8K 链式提交返回 -1002

- 模块：PC 无限画布 → Enhance 面板 → Standard(8K) 链式提交
- 类型：环境类（测试服后端临时问题，与 BUG-REG-009 同源）
- 优先级：P1
- 对应用例：`test_infinite_canvas_enhance_v4.py::TestL6EnhanceWorkflow::test_l6_003_8k_routes`
- 前置：VIP(Pro) 登录，上传 test_images/8K.jpg 进入画布

[步骤]
1. 进入无限画布，打开 Enhance 面板
2. 模式 Standard，分辨率选 8k（链式），提交
3. 等待结果

[结果]
- Console：`styleId=pkweb_chain_comfyui_enhance_normal`，`resourceCode=picenhance_normal_8k`，`errorCode: -1002`（同 BUG-REG-009）。
- 未生成结果图层。

[期望]
- 测试服恢复后复跑应通过；否则按真实缺陷提单并附后端任务 id（`jobId` 已在 console 中记录）。

![BUG-REG-010 Standard 8K 链式提交失败现场](D:/Test/web-test/artifacts/2026-09-09_task-33_canvas_enhance_optimization/shots/enhance_task_failure_long_8192.png)

---

## 汇总

| Bug | 用例 | 模块 | 类型 | 优先级 |
|---|---|---|---|---|
| BUG-REG-001 | mobile_home L1-002 | 移动端首页 hero 模型入口 | 产品变更未同步 | P1 |
| BUG-REG-002 | mobile_home L2-003 | 移动端首页模型弹层 | 同源用例漂移 | P1 |
| BUG-REG-003 | mobile_home L2-010 | 移动端首页效果模板入口 | 用例漂移/入口变更 | P2 |
| BUG-REG-004 | pc_home L2-008 | PC 首页 Pokecut Pro 入口 | 产品变更未同步 | P1 |
| BUG-REG-005 | batch L1-007 | Batch 删除控件文案/可访问名 | 产品缺陷（已知项） | P1 |
| BUG-REG-006 | batch L2-011 | Batch 删除流程 | 产品缺陷（同源） | P1 |
| BUG-REG-007 | batch L2-012 | Batch 下载流程 | 产品缺陷（同源） | P1 |
| BUG-REG-008 | enhance L5-001 | /create 入口被 VIP 弹窗遮挡 | 产品缺陷 | P0 |
| BUG-REG-009 | enhance L6-002 | Standard 4K 提交 -1002 | 环境（测试服） | P1 |
| BUG-REG-010 | enhance L6-003 | Standard 8K 链式 -1002 | 环境（测试服） | P1 |

截图与原始数据：`artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture/`（含 `mobile_home_capture.json`、`batch_capture.json`、`batch_top_buttons.json`、`create_entry_body.txt`）。
