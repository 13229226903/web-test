---
task_id: 2026-10-12_stable_regression_registry
agent: orchestrator
artifact: archive
status: completed
archived_at: 2026-10-13 11:05:00
archived_by_user: true
registry_entries_updated: 6
execution_mode: codex_single_context
---

# 归档记录 — registry 稳定回归（12 suite）+ 漂移修复（2026-10-12 / 10-13）

## 1. 归档范围

| 项 | 路径 |
|---|---|
| 目标环境 | `http://10.17.1.66:3001/` |
| 需求文档 | `artifacts/regression_registry.md`（登记 12 个 `stable_regression` suite） |
| 执行对象 | registry `Tests` 列当前脚本（12 个 suite / 232 条用例） |
| 源脚本 | `tests/`（4 个文件本轮修改） |
| 归档副本 | `archive/<module>/`（4 个文件同步） |
| 复跑工具 | `artifacts/2026-10-12_stable_regression_registry/run_registry_regression.py` |
| 归档复跑工具 | `artifacts/2026-10-12_stable_regression_registry/run_archive_regression.py`（本轮**未完整执行**，见 §3） |
| 逐 suite 日志 | `artifacts/2026-10-12_stable_regression_registry/regression/*.log` + `verify_*.log` |
| 汇总 | `artifacts/2026-10-12_stable_regression_registry/regression/summary.json` |
| 回归报告 | `artifacts/2026-10-12_stable_regression_registry/report.md`、`reports/allure-report-regression` |
| Sync | `artifacts/2026-10-12_stable_regression_registry/sync.md`（confirmed；§11~§14 记录未处理项） |
| Exploration Report | `artifacts/2026-10-12_stable_regression_registry/exploration_report.md` |
| Automation Handoff | `artifacts/2026-10-12_stable_regression_registry/evidence/automation_handoff.yaml` |
| 页面地图增量 | `page_map/pokecut/{infinite_canvas_text_layer_v3,mobile_canvas_v12,ai_image_text_enhancer_v4}.yaml` |
| 清理清单 | `artifacts/2026-10-12_stable_regression_registry/archive_cleanup_manifest.json` |
| Registry | `artifacts/regression_registry.md`（6 行更新） |
| Review | 未执行（稳定回归口径：只在漂移范围内局部回退修脚本，不新增用例） |

## 2. 运行结果

### 2.1 全量基线（2026-10-12，修复前）

- 12 suite / 232 条：**183 passed / 41 failed / 7 skipped / 1 xfailed**，总耗时 10345.61s
- 6 个 suite 通过、6 个 suite 失败；失败全部为**脚本漂移 / 环境态**，无产品缺陷

### 2.2 漂移修复（2026-10-12 ~ 10-13，逐条定向复跑验证）

| 族 | suite | 根因 | 修复 | 复跑证据 |
|---|---|---|---|---|
| F1 | `test_infinite_canvas_text_layer_v2.py` | `/create` 入口卡改 `button[data-tool-id='start-photo']`；Rotate 变图标按钮 | 入口改稳定数据属性；Rotate 改 `button.rotation-button[aria-label='Rotation']` | `verify_f1_fixed.log` |
| F2 | `test_canvas_stats_all.py` | `/create` 入口卡、移动端注册入口迁移、PC Enhance 改顶部下拉、促销/内购链式弹窗 | `upload_on_page` 补新入口；移动端注册改 credits 胶囊；PC Enhance 开下拉选 Ultra HD Mode；`close_purchase_modal` 循环关闭 | `verify_f2_fixed.log`、`verify_mcore03_fixed.log`、`verify_m_core_02_fix.log` |
| F3 | `test_ai_image_text_enhancer_experiment.py` | 点数规则变更（用户确认属**预期变更**） | 15 处 expected 更新（base 2k/4k/8k=5/5/10，每附加效果 +5，非增强单效果=5） | `verify_f3_fixed.log` |
| A | `test_canvas_stats_all.py` | `click_text` 子串兜底静默误点（`Remove`→`Remove BG`） | 新增 `click_exact`；P-NEW-03 actions 改 `[{click_exact: All}]` | `verify_p_new_03_fix.log` |
| D | SEO 移动端（`conftest.py::login_mobile`） | 移动端 header 无独立 `Sign up` → 函数静默 `return`，24 条全部匿名态执行 | 改走顶部栏最右汉堡 `img[src*='nav_btn_mun.svg']` → `div.menu-tab` → `Log in` → 填表提交；不再静默 return | `verify_l2006_fix.log`（L2-006）、`verify_l2011_l2005_mobile.log`（L2-005） |
| — | `test_mobile_home.py` | `login_vip` 注册入口迁移到 credits 胶囊 | 改 `.credits-entry__pill` → `button.credits-entry__signup`（保留旧路径兜底） | `verify_l3_004_fix2.log` |
| — | `conftest.py` | Proxifier 改写回环致 `socket.socketpair()` 抛 `ConnectionError`，Playwright 全部 setup ERROR | 注入 `_install_lenient_socketpair()`（优先原生、仅 ConnectionError 回退） | `verify_f1_recheck.log`（用户方案 B 授权） |

### 2.3 修复后结果

- **41 条原始失败 → 39 条已修复或已标记**，剩 **2 条未处理**（用户明确指示不处理）：
  1. `tests/test_seo_main_upload_interactions_v1.py::TestL2SeoMainUploadInteractions::test_l2_011[chromium]`
  2. `tests/mobile/test_seo_main_upload_mobile_v1.py::TestMobileSeoMainUpload::test_l2_011[chromium]`
  - 原因：`/tools/zoom-in-photos` **服务端容量限流**（Tips 弹窗「This feature is busy due to high demand … about 30 minutes」）。间隔 12.5 小时后复跑仍复现（`verify_l2011_rerun.log`：`2 failed in 654.08s`），属**持续性环境故障**，非脚本/产品缺陷。
- **新增 1 个已知产品缺陷**：`BUG-2026-1012-01`（P-NEW-16 / M-NEW-14 换背），保留需求期望断言 + `xfail(strict=True)` + Allure 标签 `known_bug=BUG-2026-1012-01`（报告状态显示 skipped）。
- 未做全量复跑（用户指示「不用复跑」），修复结论以逐条定向复跑日志为证。

## 3. 归档副本可独立复跑校验

| 检查项 | 结果 |
|---|---|
| 公共模块位置 | 依赖仓库根 `conftest.py` / `helpers_create_entry.py`；未在 `archive/<module>/` 新增 conftest |
| 路径常量解析 | 4 个本轮改动副本经**智能合并**（以 `tests/` 业务修复为基础，回移 archive 专用的 `_repo_root()` 上溯逻辑）。实测 `ROOT` / `TEST_IMAGE` / `TEST_IMAGES` 均解析到仓库根 `D:\Test\web-test` |
| 归档副本 collect-only | 12/12 成功、0 error（`regression/archive_collect_check.log`）：14 / 18 / 6 / 38 / 11 / 24 / 13 / 9 / 24 / 24 / 11 / 40 |
| 归档副本全量复跑 | **跳过（用户指示「不用复跑」）**。10:39 启动后仅完成 1 个 suite 即中止（`archive/portrait_detector/...`：13 passed / 1 failed，`test_l2_008_try_my_photo` 为 `Page.wait_for_function` 超时，与归档副本路径无关）；部分产物 `regression/archive/`、`reports/allure-results-archive` 已清理 |

> 说明：归档副本可复跑校验的**实质要求**是「路径常量逐级上溯仓库根、否则归档副本假失败」。本轮以 collect-only + 路径解析实测覆盖该要求；全量复跑按用户指示免除。`reports/allure-report-archive`（2026-09-21 旧产物）未在本轮重新生成。

## 4. archive-cleanup 结果

清单：`artifacts/2026-10-12_stable_regression_registry/archive_cleanup_manifest.json`

| 动作 | 数量 | 说明 |
|---|---|---|
| 删除 | 6 | 与保留文件**二进制完全相同**的重复截图（`drawer_signup_modal` / `grpC_L2-006_afterclose` / `l2006_probe` / `grpE_mcore03_tail` / `grpE_mcore03_afterclose` / `hdr_iPhone_en`），同内容另有保留副本 |
| 保留（被引用） | 13 | `sync.md` / `exploration_report.md` 显式引用的证据截图 |
| 保守保留 | 26 | 未引用但为本次漂移判定与未处理项的原始证据（换背 `grpE_*`/`pn16_*`、L2-011 限流 `l2011_*`、L3-004 `l3004_*`、移动端登录抽屉 `drawer_*`/`pixel10_*`、各设备 header `hdr_*`），按 2026-09-17 先例保留 |

## 5. 知识沉淀

- 本轮**未新增** `rule.md` / `PROJECT.md` / `knowledge/*` 落点；`knowledge/candidates/pending.yaml` 的 `candidates` 仍为空。
- 候选经验已写入本任务 `sync.md`（§11~§14 未处理项与根因）与 3 份 page_map 的 v3/v12/v4（漂移细节、入口 selector、点数规则）。
- 高风险可沉淀候选（本轮出现 ≥2 次）供下轮评估：
  1. 移动端注册/登录入口只在顶部栏最右汉堡抽屉内（`nav_btn_mun.svg` → `div.menu-tab`），header 无独立 `Sign up`；**静默 return 式登录兜底会把整套用例跑成匿名态**（本轮致 SEO 移动端 24 条全匿名）。
  2. `click_text` 子串兜底会静默误点（`Remove`→`Remove BG`），失败现象伪装成「埋点漏报」——埋点类失败须先确认实际点击元素。
  3. 回环代理（Proxifier 等）下 `socket.socketpair()` 抛 `ConnectionError` 致 Playwright 无法启动，需在 `conftest.py` 注入宽松 socketpair。

## 6. 最终状态

- Registry：`artifacts/regression_registry.md` 已更新 6 行（Page Map 版本 + Last Passed + Notes）：ai_image_text_enhancer(v3→v4)、infinite_canvas_text_layer(v2→v3)、mobile_canvas(v10→v12)、mobile_home、SEO PC、SEO 移动
- 12 个 suite 状态：11 个 `stable_regression` 正常维护；`test_l2_011`（PC + 移动端，同属 2 条 SEO suite）保留为**已知环境问题**（服务端限流）
- 已知缺陷台账：`BUG-2026-1012-01`（换背事件不发，PC/移动端双侧），Allure 标签 `known_bug`
- 执行模式：`codex_single_context`（未使用隔离子代理）
- 维护提示：
  - 换背用例（P-NEW-16 / M-NEW-14）标 `xfail(strict=True)`：**产品修复后用例会变 xpass 并直接失败**，提醒摘掉标记
  - `test_l2_011` 复跑前需确认 `/tools/zoom-in-photos` 限流窗口已过（>30 分钟）
  - 本环境移动端画布类用例必须登录会员账号；匿名态会弹注册弹窗遮挡工作区
