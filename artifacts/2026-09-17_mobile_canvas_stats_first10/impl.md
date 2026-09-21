---
task_id: 2026-09-17_mobile_canvas_stats_first10
agent: test-writing
status: completed
inputs:
  cases: artifacts/2026-09-17_mobile_canvas_stats_first10/cases.md
  sync: artifacts/2026-09-17_mobile_canvas_stats_first10/sync.md
  page_map: page_map/pokecut/mobile_canvas_v9.yaml
  data: data/pokecut_canvas_stats_v1.yaml
outputs:
  test_file: tests/test_canvas_stats_all.py
  data_file: data/pokecut_canvas_stats_v1.yaml
  collect_only: 40 tests collected, 0 error
  self_run: 全量 40 条 = 36 passed / 2 xfailed（P-INF-01、M-NEW-04 已知埋点缺陷）/ 2 skipped（P-NEW-09、M-NEW-09 AI滤镜 URL 缺口）/ 0 failed
next_agent: null
regression_candidate:
  eligible: true
  reason: 全量 40 条执行完毕（0 failed）；4 条非 passed 均为已知埋点缺陷或外部依赖缺口，非脚本问题
  suggested_tests:
    - tests/test_canvas_stats_all.py
  suggested_archive:
    - archive/canvas_stats/test_canvas_stats_all.py
  registry_key: canvas_stats_v1
---

# 实现摘要

- Allure 顶层仅两个大类：`epic=PC端` / `epic=移动端`；二级 `feature` 为注册登录 / 无限画布（画布页）/ 新画布。
- 数据驱动：`data/pokecut_canvas_stats_v1.yaml` 维护 40 条用例维度、入口、触发动作、期望事件、截图名。
- 统计断言：`StatsRecorder` 监听 Console，`assert_event_pair` 要求目标事件 `sendGaEvent=1` 且 `debug 统计=1`；0=漏报、>=2=多报。
- 已知 bug 用例（P-INF-01、M-NEW-04）保留需求期望断言，并用 `xfail(strict=True)` 标记。
- 第 11 条（M-CORE-07）按用户口径：不要求会员账号，能正常提交任务并生成结果即可。

# 自修日志

## round 1

- 命令：`python -m pytest tests/test_canvas_stats_all.py::test_m_new_12 -q`
- 结果：1 passed（2:21）
- 结论：移动端 SEO 新画布购买出现+成功链路可跑通，0-credit 免费账号在移动端可直接触发购买弹窗。

## round 2

- 命令：`python -m pytest ...::test_p_new_13 ...::test_m_core_05 -q`
- 结果：1 failed / 1 passed（4:56）
- 失败归因：PC 新画布购买弹窗未出现 —— 新注册账号仍有免费 credits，未触发购买。
- 修复：PC 新画布与 PC 无限画布购买类改用任务登记的 0-credit 账号（`POKECUT_ZERO_CREDIT_EMAIL`，默认 `autotest202609171333@qq.com`）；`register_or_login` 支持指定邮箱登录。

## round 3

- 命令：`python -m pytest ...::test_p_new_13 -q`
- 结果：1 failed（3:04）→ 修复 → 1 failed（3:52）→ 修复 → 1 passed（2:10）
- 失败归因：购买出现断言已过，购买成功事件 0 次；Debug 面板关闭时误点页面第一个 `×`，把购买弹窗一起关掉。
- 修复：`enable_debug_skip` 改为再次点击 DEBUG 浮层按钮关闭面板；购买弹窗 `Get Started` 与 checkout 的 `Debug: 跳过真实购买` 改用 `dispatchEvent` 触发 Vue。

# 扩展自跑（超出 3 轮上限，停止等待）

- 命令：`python -m pytest ...::test_p_inf_02 ...::test_m_core_03 ...::test_m_new_01 -q`
- 结果：3 failed（12:22）

| 用例 | 环节 | 观察 | 归因 |
|---|---|---|---|
| P-INF-02 | 无限画布购买成功 | 出现 `PC端支付优化AB实验A方案paypal支付年ultra购买项成功`、`总_年ultra订阅购买成功`，未出现 `无限画布页点数用完触发购买年ultra成功` | 疑似真实事件缺口（探索期曾观察到该事件，需复核账号/AB 分流差异） |
| M-CORE-03 | 移动端画布页购买 | 仅出现画质增强购买事件；关闭弹窗后触发 AI Image Extender 未产生 `移动端画布AI扩图功能点数用完触发购买` | 自动化实现问题：关闭弹窗后第二功能入口交互需修正 |
| M-NEW-01 | 移动端新画布增强购买成功 | 出现购买出现事件与 `移动端支付优化AB实验B方案SE试用购买项checkout界面进入`，未出现购买成功事件 | 自动化实现问题：移动端 checkout 的 `Debug: 跳过真实购买` 未成功触发 |

# 下一步修复建议

1. 抽取统一 `open_checkout_and_debug_skip(page)`：等待 checkout 容器出现 → 断言 `Debug: 跳过真实购买` 可见 → `click(force=True)` + `dispatchEvent` 双通道 → 校验成功事件。
2. M-CORE-03：关闭购买弹窗后先回到一级工具列表再点 `AI Image Extender`，并等待其面板标题出现后再触发。
3. P-INF-02：复核探索期账号与当前 0-credit 账号的 AB 分流差异；若确认事件确实缺失，按 bug 处理并保留期望断言。

# 命令与产物

- collect-only：`python -m pytest tests/test_canvas_stats_all.py --collect-only -q` → `40 tests collected`
- HTML 报告：`reports/report.html`
- Allure 结果目录：`reports/allure-results`
- 截图：`data/screenshots/`（`pc_new_13_blur.png`、`pc_new_13_blur_after_debug.png` 等）


---

# 新一轮修复（用户授权重置三轮上限）

本轮只修技术性交互，不改统计断言与期望事件。三条原阻塞用例现已分别通过：

| 用例 | 结果 | 根因 | 修复 |
|---|---|---|---|
| `P-INF-02` PC 无限画布点数用完触发购买成功 | ✅ passed | `.debug-panel-wrapper` 常驻 DOM，旧逻辑误判 Debug 面板已打开，实际未点开关；后续 `force=True` 点击导致未进入 Debug 跳过链路 | 只以真实 `.debug-panel` 可见性判断面板；先真实点击 DEBUG 浮层，再回读 `跳过真实购买` checkbox |
| `M-NEW-01` 移动端新画布增强购买出现+成功 | ✅ passed | 共享 0-credit 账号已消耗 `月SE试用` 资格，实际只上报 `月SE购买成功`；且 `force=True` 坐标点击可能打到支付按钮 | 移动端新画布 SEO 用例改用随机新账号注册，恢复 `月SE试用` 内购项；优先真实点击 checkout 的 `Debug: 跳过真实购买`，DOM click 作回退 |
| `M-CORE-03` 移动端画布页点数用完触发购买与 AI 扩图购买 | ✅ passed | 关闭首个购买弹窗后，AI Image Extender 二级面板未稳定打开；探索记录的 `Estenda IA` 是葡语入口名，英文移动画布按钮为 `AI Extend` | 关闭弹窗后回到 `Trending Tools`，等待 `AI Extend` 按钮真实可见再点击 |

## 本轮验证命令与结果

- `python -m pytest tests/test_canvas_stats_all.py::test_p_inf_02 -q` → `1 passed`
- `python -m pytest tests/test_canvas_stats_all.py::test_m_new_01 -q` → `1 passed`
- `python -m pytest tests/test_canvas_stats_all.py::test_m_core_03 -q` → `1 passed`
- `python -m pytest tests/test_canvas_stats_all.py --collect-only -q` → `40 tests collected`

## 证据

- `data/screenshots/pc_inf_02_purchase_success.png`
- `data/screenshots/mobile_new_01_enhancer.png`
- `data/screenshots/mobile_new_01_enhancer_after_debug.png`
- `data/screenshots/mobile_canvas_03_purchase_appearance.png`
- `reports/allure-results/` 中对应 result / attachment

## 当前状态

- 三条原阻塞用例已修复并单独通过。
- 全量 40 条尚未在本轮重跑；未标记 `regression_candidate`。
- 停在 `impl_review`，等待用户确认后继续全量分批执行。


---

# 全量 40 条最终结果（2026-09-21）

| 批次 | 用例范围 | 结果 |
|---|---|---|
| 第 1 批 | P-INF-01 ~ P-NEW-07 | 9 passed / 1 xfailed / 0 failed |
| 第 2 批 | P-NEW-08 ~ P-NEW-16、M-CORE-01 | 9 passed / 1 skipped / 0 failed |
| 第 3 批 | M-CORE-02 ~ M-NEW-04 | 9 passed / 1 xfailed（三条修复项已分别验证，用户指示不整批复跑） |
| 第 4 批 | M-NEW-05 ~ M-NEW-14 | 9 passed / 1 skipped / 0 failed |

合计：**36 passed / 2 xfailed / 2 skipped / 0 failed**（40 条）

## 非 passed 明细

| 用例 | 标题 | 状态 | 原因 |
|---|---|---|---|
| P-INF-01 | PC 无限画布增强点数用完触发注册与注册成功 | xfailed（预期） | 真实埋点缺陷：仅上报通用注册事件，缺 `无限画布页画质增强ultra功能点数用完触发注册(成功)` |
| M-NEW-04 | 移动端新画布改图购买出现与成功 | xfailed（预期） | 真实埋点缺陷：实际 `画布页改图购买出现it_ai-replace`，缺 `新画布` 前缀 |
| P-NEW-09 | PC 新画布 AI滤镜购买出现与成功 | skipped | 依赖缺口：AI滤镜 SEO URL 未提供 |
| M-NEW-09 | 移动端新画布 AI滤镜购买出现与成功 | skipped | 同上 |

## 最终自修要点（第 3/4 批）

1. 移动端面板主提交按钮：`button.mobile-ai-generate-button`、`button.mobile-ai-expand-generate-button`（PC 为 `btn-bg-gradient1`）。
2. 促销弹窗 vs 内购弹窗语言无关区分：促销无 `li.purchase-pro-plan__card`，内购有；促销由 `colos_pop_btn_close.svg` 关闭。
3. Debug 面板关闭：`button.close-btn`；面板打开时 DEBUG 浮层被遮挡，须点面板内关闭按钮。
4. DEBUG 浮层为 `position: static`，须改 `position: fixed` 才能移开，否则遮挡结果弹窗底部下载按钮。
5. M-NEW-03 AI Delete 蒙版：仅鼠标/合成 PointerEvent 无效，须 CDP `Input.dispatchTouchEvent`；`1K.jpg` 无多余物体时 Quick Select 提示 “Did not detect” 属正常。
6. 功能级注册成功事件由打开注册弹窗的功能决定，M-CORE-02 改为两个独立匿名会话。
7. 归档副本可独立复跑：`ROOT` 改为 `_repo_root()` 逐级上溯，live 与 archive 位置均解析到仓库根。

## 归档信息

- 归档副本：`archive/canvas_stats/test_canvas_stats_all.py`
- archive collect-only：40 collected / 0 error
- archive-cleanup：`archive_cleanup_manifest.json`（删除 64 个探索中间产物，保留 105 个证据文件）
- 知识沉淀：用户确认**不沉淀**
