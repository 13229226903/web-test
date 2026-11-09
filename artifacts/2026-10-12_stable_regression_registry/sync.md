---
task_id: 2026-10-12_stable_regression_registry
agent: page-map-sync
status: confirmed
repair_scope: selector_drift
gate_exemption: 用户 2026-10-12 明确选择「方案 A：对 3 个疑似漂移族做局部复探，产出 sync 差异后回退修脚本」；按 ui-test-page-map-sync skill 的 selector 漂移豁免条款只产出精简 exploration_report，未做全量探索。
exploration_driver: playwright_mcp_only
diagnostic_driver: none
mcp_preflight: passed（2026-10-12 14:55 本会话 browser_navigate http://10.17.1.66:3001/ -> /create 成功）
viewport_guard: passed（PC context: innerWidth=1920 innerHeight=1080 DPR=1 UA=HeadlessChrome/154 Windows hasTouch=false；移动 context: 390x844 DPR=3 iPhone UA hasTouch=true ontouchstart=true）
inputs:
  requirement_doc: artifacts/regression_registry.md
  regression_report: artifacts/2026-10-12_stable_regression_registry/report.md
  previous_page_maps:
    - page_map/pokecut/infinite_canvas_text_layer_v2.yaml
    - page_map/pokecut/mobile_canvas_v11.yaml
    - page_map/pokecut/ai_image_text_enhancer_v3.yaml
outputs:
  scanned_pages:
    - /create（PC）
    - /agent?pid=<uuid>（PC 画布，文字图层）
    - /en（移动端首页 header + credits 面板）
    - /tools/photo-enhancer → /create/edit?pid=<uuid>（移动端 SEO 新画布）
    - /tools/ai-image-text-enhancer（PC）
  page_map_versions:
    - page_map/pokecut/infinite_canvas_text_layer_v3.yaml
    - page_map/pokecut/mobile_canvas_v12.yaml
    - page_map/pokecut/ai_image_text_enhancer_v4.yaml
  coverage_gates: 3/3 漂移族复探完成
  state_button_coverage: 见「2. 页面覆盖矩阵」
  requirement_actual_diffs: 3 项（其中 1 项为行为/计费变更，待业务确认）
  bug_candidates: 0 项（无产品缺陷级证据）
  skipped: 0
  special_dependencies:
    - 文字增强点数规则变更需业务/PRD 确认后才能改 expected（不得直接弱化断言）
  specs_updated: []
human_report: artifacts/2026-10-12_stable_regression_registry/exploration_report.md
automation_handoff: artifacts/2026-10-12_stable_regression_registry/evidence/automation_handoff.yaml
next_agent: test-writing
user_confirmation: 2026-10-12 用户确认 D3 点数规则为预期变更（授权更新 expected）；方案 A 已授权 F1/F2 回退修脚本
created_at: 2026-10-12 15:20:00
---

# sync.md — 稳定回归 3 个疑似漂移族局部复探

## 1. 探索摘要

本轮是 2026-10-12 稳定回归（12 suite / 232 用例，183 passed / 41 failed）之后按用户选择的方案 A 执行的**局部复探**，只针对 41 条失败归纳出的 3 个族，不做全量探索：

| 族 | 失败 suite | 失败数 | 复探结论 |
|---|---|---|---|
| F1 画布页文字功能入口 | tests/test_infinite_canvas_text_layer_v2.py | 6（整 suite） | **入口卡 selector + 文案漂移**，画布内元素未变 |
| F2 移动端新画布购买链路 | tests/test_canvas_stats_all.py（M-NEW-01..14 / M-CORE-03/04 + M-CORE-06/07） | 16 | **移动端注册入口漂移导致会话保持匿名**，购买弹窗链路本身正常 |
| F3 文字增强点数计费 | tests/test_ai_image_text_enhancer_experiment.py | 9 | **点数规则实测与 2026-08-29 基线不一致**（行为/计费变更，非 selector） |

结论：F1、F2 是可由 test-writing 直接修复的 selector/入口漂移；F3 属行为变更，必须业务确认后才能改断言。

## 2. 页面覆盖矩阵

| # | 用例族 / 覆盖点 | 结论 | 证据 |
|---|---|---|---|
| F1-1 | /create 入口卡（Trending Tools 第一个） | drift：`div.cursor-pointer:has-text('Start from a Photo')` → `button[data-tool-id='start-photo'][data-tool-surface='trending']`，文案 `Start from a Photo` → `Start with Photos` | shots/fam1_create_entry_card.png |
| F1-2 | /agent?pid= 左侧工具栏 7 工具 | covered：`button[data-tool-id='text']`（及 image/sticker/brush/line/shape/layer）各 1 个且可见，未变 | MCP evaluate（7 个 data-tool-id 全可见） |
| F1-3 | 文字面板 Adjust 工具栏 | covered：Adjust / Move Up / Move Down / To Top / To Bottom / Flip h / Flip v / Delete 均在，未变 | shots/pm_text_panel_2026-10-12.png（MCP 截图） |
| F1-4 | 文字面板 Basic/Adjust Tab 与折叠区 | covered：Basic / Adjust 两个 Tab 在；Basic 下 Alignment / Font / Fill 存在；折叠区 Space / Reflection / Background / Outline 存在，未变 | MCP evaluate（点击 Basic 后 Alignment/Font/Fill=true） |
| F2-1 | 移动端首页 header 注册入口 | drift：首页 header 已无 `button:has-text('Sign up')`（0 命中），只剩 credits 胶囊 + 汉堡 | shots/fam2_mobile_home_header.png、fam2_mobile_signup_entry.png |
| F2-2 | 移动端注册入口新路径 | covered：`.credits-entry__pill` 点击 → `.credits-entry__panel` → `button.credits-entry__signup`（文案 `Sign up to get more`）→ 弹窗 Email + Verification Code(123456) + `[data-testid='auth-submit']`，注册成功 | shots/fam2_mobile_signup_entry.png；实测 email autotest20261012171500@qq.com 注册成功 |
| F2-3 | 匿名态点主提交的弹窗 | covered：匿名 + 0 credits 点 `button.mobile-ai-generate-button` → 出现**注册弹窗**（auth-submit 出现、`.purchase-gift-modal` 为 0） | shots/fam2_anon_submit_register_modal.png |
| F2-4 | 注册态点主提交的弹窗链路 | covered：促销弹窗 `.purchase-gift-modal`（`mobile-sales-promotion-dialog`，`li.purchase-pro-plan__card`=0）→ 关闭按钮 `img[src*='nav_btn_pop_close.svg']` 仍有效 → 内购弹窗（`li.purchase-pro-plan__card`=3） | shots/fam2_promo_modal.png、fam2_iap_modal_after_close.png |
| F3-1 | 文字增强点数：非增强单效果 | diff：remove_glare / remove_moire / document_scanner 实测均 **5**，基线为 2 / 2 / 4 | shots/fam3_cost_paid_5.png |
| F3-2 | 文字增强点数：enhance_text | diff：2k / 4k 为 **Free**（free 态），8k 为 **10**；基线为 2 | shots/fam3_cost_enhance_free.png |
| F3-3 | 文字增强点数：组合 | diff：enhance+scanner 2k/4k=**5**、8k=**15**；enhance+glare 2k=5、8k=15；全 4 效果 4k=**15**；基线 6 / 14 | shots/fam3_cost_all_15.png |

## 3. 需求差异（requirement_actual_diffs）

### D1｜/create 入口卡文案与元素类型变更（F1）— verdict: page_drift
- 基线（page_map v2）：`div.cursor-pointer:has-text('Start from a Photo')`
- 现网：`button.create-tool-pill[data-tool-id='start-photo'][data-tool-surface='trending']`，文案 `Start with Photos`
- 影响：`enter_canvas()` 在入口卡 click 处 30s 超时，导致 `test_infinite_canvas_text_layer_v2.py` 6 条全挂（失败点均在入口，非画布逻辑）。
- 建议：selector 改为 `button[data-tool-id='start-photo']`（稳定属性），不再依赖文案与 Tailwind 工具类。

### D2｜移动端首页注册入口迁移到 credits 面板（F2）— verdict: page_drift + script_defect
- 基线（page_map v11）：`button:has-text('Sign up')`
- 现网：首页 header 无 Sign up；`button.credits-entry__signup`（需先展开 `.credits-entry__panel`）
- 叠加的脚本缺陷：`register_or_login(mobile=True)` 用 `except Exception: pass` 静默吞异常，注册失败不报错 → 会话保持匿名 → 点主提交弹**注册弹窗**而非购买弹窗 → `wait_purchase_modal()` 返回 False，报“未出现购买弹窗”。
- 影响：`test_canvas_stats_all.py` 移动端 **16** 条失败 —— 14 条购买类（`register_or_login(mobile=True)` 后断言 `wait_purchase_modal`）+ M-CORE-06/07（`register_or_login(mobile=True, pro=True)` 走同一分支，pro 登录同样静默失败后保持匿名 → 埋点缺失）。
- 建议：修复注册入口 + 取消静默吞异常（注册失败应显式失败或落 evidence）。

### D3｜文字增强点数规则与基线不一致（F3）— verdict: needs_business_confirmation
实测矩阵（测试服 http://10.17.1.66:3001，匿名/免费态，素材 test_images/文字测例.jpg）：

| 效果组合 | 2k | 4k | 8k | 旧基线 |
|---|---|---|---|---|
| remove_glare | 5（分辨率区隐藏） | — | — | 2 |
| remove_moire | 5（分辨率区隐藏） | — | — | 2 |
| document_scanner | 5（分辨率区隐藏） | — | — | 4 |
| enhance_text | Free | Free | 10 | 2 |
| enhance_text + document_scanner | 5 | 5 | 15 | 6 |
| enhance_text + remove_glare | 5 | 5 | 15 | — |
| enhance_text + remove_glare + remove_moire + document_scanner | 15 | 15 | 15 | 14 |

- 该页面本身是「文字画质增强**实验**页」，点数很可能由实验/AB 配置驱动。
- **未就地改写 expected**（共享红线：不删断言、不弱化断言）。需业务/PRD 确认新规则是预期变更还是缺陷；确认后由 test-writing 统一更新断言。
- 若业务确认非预期 → 转 bug_candidate 提缺陷，脚本不改。

## 4. 关键发现与下游注意事项

1. F1 的失败**只在入口**；画布内 `button[data-tool-id='text']`、Adjust 工具栏、Basic 下 Alignment/Font/Fill、四个折叠区全部实测存在，修完入口后原 6 条用例的后续断言预计可直接恢复，无需重写用例。
2. F2 的真正根因是**注册静默失败**，不是购买弹窗逻辑——注册态下 promo→close→IAP 全链路实测正常（3 张套餐卡）。修 selector 时务必同时去掉静默吞异常，否则同类失败会再次以“未出现购买弹窗”的假象出现。
3. F3 属行为差异，禁止为了“让测试通过”把 expected 改成 5/10/15；必须先拿到业务确认。
4. 未变项（可继续复用）：`.purchase-gift-modal` 容器、`li.purchase-pro-plan__card` 判定、`img[src*='nav_btn_pop_close.svg']` 关闭按钮、`button.mobile-ai-generate-button` 主提交按钮、`button.seo-first-screen-upload-button` 上传入口。
5. 移动端 case 的 `entry` 是**不含语言前缀**的路径（如 `/tools/photo-enhancer`）；带 `/en` 前缀会 404（复探中一度误用 `/en/tools/photo-enhancer` 得到 `Page not found`）。
6. diagnostic_limit: 无（本轮结论均可由 page 可观察行为判定，未需要 DevTools trace）。

## 5. 版本差异摘要

| page_map | 版本 | 变更 |
|---|---|---|
| infinite_canvas_text_layer | v2 → v3 | 仅修正 `/create` 入口卡 selector 与文案；其余元素沿用 v2 实测结论 |
| mobile_canvas | v11 → v12 | 修正移动端注册入口（credits 胶囊 → `.credits-entry__signup`）；补 drift 说明；购买弹窗链路沿用 v11 |
| ai_image_text_enhancer | v3 → v4 | 新增 2026-10-12 实测点数矩阵与 `rule_verdict: changed_vs_2026_08_29_baseline`；未覆盖旧 baseline，仅标注 superseded 待确认 |

> registry 的 Page Map 列需在用户确认后同步更新到 v3 / v12 / v4。

## 6. 用户确认与后续

- **2026-10-12 用户确认：D3 文字增强点数规则为预期变更**，授权 test-writing 按实测矩阵更新 expected（不得弱化为空值）。
- 方案 A 已授权 F1/F2 回退修脚本（只改 selector / 注册入口 / 异常处理，不改业务断言）。
- D3 移除 blocked 状态，`blocking_items` 清空。

## 7. 未处理失败清单（本轮复探范围之外）

| # | suite | 用例 | 现象 | 初判 |
|---|---|---|---|---|
| 1 | canvas_stats | M-CORE-02 | 期望 `移动端画布画质增强ultra功能点数用完触发注册`，实测 `移动端画布画质增强通用功能点数用完触发注册` | 疑似与 D3 同源的档位/归因变更，需复探确认 |
| 2 | canvas_stats | P-NEW-03 | `新画布消除购买出现en_magic-eraser-with-ai-detection` sendGaEvent=0 | PC 新画布埋点漏报，需复探 |
| 3 | canvas_stats | P-NEW-16 | `新画布换背购买出现en_background-changer` sendGaEvent=0 | PC 新画布埋点漏报，需复探 |
| 4 | canvas_stats | P-INF-02 | PC Enhance 面板未显示 `Ultra HD Mode` | PC 无限画布 UI 变更/漂移，需复探 |
| 5 | canvas_stats | P-INF-03 | AI Enhancer 面板未显示主 `Enhance` 提交按钮 | 同上 |
| 6 | mobile_home | L3-004 | `Locator.click` 15s 超时（证件照成功链路） | 单条链路漂移，需复探 |
| 7 | SEO 上传（PC） | L2-011 | 期望文案 `Before`，页面为 `Processing failed, please try again` + 30 分钟限流 | 环境态偶发，建议单跑复验 |
| 8 | SEO 上传（移动端） | L2-005 | 上传后未进入 `/tools/id-photo-edit?pid=` | 真实 UI 差异，需复探 |
| 9 | SEO 上传（移动端） | L2-006 | 上传后未自动展开 `.mobile-feature-workspace`（Blur Background） | 真实 UI 差异，需复探 |
| 10 | SEO 上传（移动端） | L2-011 | 同 #7（服务端限流） | 环境态偶发 |

合计 10 条未处理 = 41 − 31（F1 6 + F2 16 + F3 9）。

## 8. test-writing 修复记录（2026-10-12）

| 族 | 改动 | 验证 |
|---|---|---|
| F1 | `enter_canvas` 入口 selector → `button[data-tool-id='start-photo']`；`test_text_001` Rotate 断言由 body 文本改为 `button.rotation-button[aria-label='Rotation']` | ✅ 6 passed（原 0/6） |
| F2 | `register_or_login(mobile=True)` 注册入口 → `.credits-entry__pill` + `button.credits-entry__signup`；移除 `except Exception: pass`，新增“注册弹窗出现 + 提交后关闭”判据 | ⏳ 17 条移动端定向复跑中 |
| F3 | 15 处 expected 按用户确认的新规则更新：base 2k/4k/8k = 5/5/10，每个附加效果 +5，非增强单效果 = 5 | ✅ 15 passed / 3 skipped（原 6/9） |

未变项：购买弹窗链路、埋点断言、其余 canvas 逻辑断言均未改动。

## 9. 第二轮局部复探：A / B 组（2026-10-12）

### A 组｜PC 无限画布 Enhance（P-INF-02 / P-INF-03）— verdict: page_drift（含 2 处）

**A-1｜/create 上传不再进入画布（selector_drift）**
- `upload_on_page()` 在 `/create` 上按文案/`input[type=file].first` 兜底：命中提示框的「参考图」输入框（`multiple=true`，非画布入口），上传后 URL 仍停留在 `/create`，函数却返回 True → `wait_canvas` 静默超时。
- 现网画布入口为 `button[data-tool-id='start-photo']`（文案 `Start with Photos`）。
- 证据：`shots/grpA_*.png`；实测 `input[type=file]` 有 2 个（`multiple=true` 提示框参考图 / `multiple=false`）。

**A-2｜Enhance 面板改为顶部工具栏下拉（page_drift）**
- 旧：画布常驻 Enhance 面板，主提交按钮 `button.btn-bg-gradient1:has-text('Enhance')`。
- 新：顶部工具栏 `button.enhance-shortcut-trigger`（`aria-haspopup=menu`）→ 菜单 `[role=menu].enhance-shortcut-list` → 模式项 `button[role=menuitem].enhance-shortcut-row`（Standard Mode / Old Photo Mode / Portrait Mode / Text Mode / Ultra HD Mode）；**选中模式后**面板才出现，主提交按钮仍为 `button.btn-bg-gradient1`（文本如 `Enhance 10`）。
- 关键坑：模式项因 `role=menuitem` 覆写，`get_by_role("button", name=/Ultra HD Mode/i)` **永远取不到**，这是 P-INF-02 断言的直接失败原因。

### B 组｜PC 新画布埋点（P-NEW-03 / P-NEW-16）— verdict: 待产品确认

| 用例 | 期望事件 | 实测事件序列（关键片段） | 判定 |
|---|---|---|---|
| P-NEW-03 | `新画布消除购买出现en_magic-eraser-with-ai-detection` | `新画布抠图购买出现en_magic-eraser-with-ai-detection` 已发出，但功能词为 **抠图** 而非 消除 | 事件功能词不一致（疑似产品统一用词），需确认 |
| P-NEW-16 | `新画布换背购买出现en_background-changer` | 未发出任何 `新画布换背购买出现*`；实测为 `无限画布页换背使用` / `无限画布页背景更改功能点数用完触发购买` / `create页自动出现购买弹窗` | 事件缺失或走了无限画布链路，需复探 |

> B 组两条都不是 selector 问题，属埋点命名 / 链路差异，未在未确认前修改 expected。

## 10. 第三轮局部复探：C / D / E 组（2026-10-12）

### 关键共性发现｜匿名会话新增「Sign Up to Get Up to 30 Credits」弹窗 — verdict: page_drift（跨套件）

2026-10-12 实测：匿名 / 0 credits 会话进入画布或工具页后，会弹出新的
**「Sign Up to Get Up to 30 Credits」注册弹窗**，遮挡页面并阻断后续流程。
该弹窗同时影响 SEO 移动端与 PC 套件，是本轮多个失败的直接原因。

| 用例 | 现象 | 与弹窗的关系 |
|---|---|---|
| SEO 移动端 L2-006 | 上传后 `wsVisible=False`，`.mobile-feature-workspace` 未展开 | 弹窗遮挡 + 未自动展开工具工作区 |
| SEO 移动端 L2-005 | 上传入口点击不可达（`locator.click` 超时） | 落地页改版：入口文案变为 **`Create My CV Photo`**，被首屏轮播遮挡 |
| SEO PC L2-011 | 期望文案 `Before`，页面实测只剩注册弹窗 | 弹窗遮挡结果态（此前一次还叠加 `Processing failed, please try again`） |
| SEO 移动端 L2-011 | 同上 | 同上 |

> 说明：D 组上一轮判为「环境态限流」不成立——复跑后页面为注册弹窗而非限流提示。
> 但代理出口 IP 与免费额度/限流的相互作用仍未排除（见 §9 A 组说明），建议关代理复跑一次以隔离变量。

### C 组明细

- **L2-005**：`button.seo-first-screen-upload-button` 仍存在（1 个、可见），但文案已变为 `Create My CV Photo`；
  实测点击超时（首屏轮播层遮挡），文件选择器未唤起 → 无法进入 `/tools/id-photo-edit?pid=`。
  根因属**落地页结构改版**，需按 page-map 重新探索该页首屏入口。
- **L2-006**：上传成功并进入 `/create/edit?pid=`，但 `.mobile-feature-workspace` 未展开（`wsVisible=False`），
  页面为 Background 类目 tab + 注册弹窗；尝试用 `button[aria-label='Close']` 关闭弹窗未生效。

### E 组明细

- **mobile_home L3-004**：`Locator.click` 15s 超时（证件照成功链路），本轮未单独复探，与上面弹窗改动可能同源，待下一步确认。

### test-writing 本轮新增修复（已验证）

| 项 | 改动 | 验证 |
|---|---|---|
| M-CORE-03 | `close_purchase_modal` 改为循环关闭（促销 → 内购链式弹窗，最多 3 轮） | ✅ 1 passed（原失败） |
| 环境（方案 B） | `conftest.py` 注入宽松 `socketpair`，兼容 Proxifier 改写 loopback | ✅ 冒烟 passed |

## 11. 最终验证汇总（2026-10-12）

| 修复项 | 最终验证 | 证据 |
|---|---|---|
| F1 画布页文字功能 | ✅ 6/6（`test_text_001` 曾出现 1 次时序抖动，复跑 passed） | verify_f1_fixed.log / verify_f1_recheck.log |
| F3 文字增强点数（预期变更） | ✅ 15 passed / 3 skipped（`test_text_l6_*` 曾 1 次生成超时，复跑 passed） | verify_final_f1_f3.log / verify_l6_recheck.log |
| F2 移动端注册入口 | ✅ 15 passed（含 M-CORE-03 修复） | verify_f2_fixed.log / verify_mcore03_fixed.log |
| A 组 P-INF-02（Enhance 下拉选 Ultra） | ✅ passed | verify_grpA_fixed.log |
| A 组 P-INF-03（Enhance 下拉 + Ultra） | ✅ passed | verify_pinf03_fixed.log |
| 环境｜Proxifier loopback 兼容（方案 B） | ✅ Playwright 恢复 | conftest.py 补丁 + 冒烟 passed |

### 未处理项（最终）

| # | 类别 | 用例 | 结论 / 下一步 |
|---|---|---|---|
| 1 | 匿名注册弹窗（跨套件） | SEO 移动端 L2-006、L2-011；SEO PC L2-011 | 匿名会话进入画布/工具页弹出「Sign Up to Get Up to 30 Credits」遮挡流程；需 page-map 复探该弹窗的关闭方式，或改用登录态账号执行 |
| 2 | 落地页改版 | SEO 移动端 L2-005 | `/tools/cv-photo-editor` 首屏入口文案改为 `Create My CV Photo` 且被轮播遮挡，需重新探索该页首屏入口 |
| 3 | 埋点口径（待产品确认） | P-NEW-03 | 事件功能词为「抠图」而非期望「消除」 |
| 4 | 埋点缺失（待产品确认） | P-NEW-16、M-NEW-14 | 未发出 `新画布换背购买出现*`，PC 与移动端两侧独立复现 |
| 5 | 埋点口径（待产品确认） | M-CORE-02 | 实际为「…画质增强通用功能点数用完触发注册」，期望「ultra」档 |
| 6 | 未复探 | mobile_home L3-004 | 证件照成功链路点击超时，与 #1 可能同源 |
| 7 | 时序抖动（非缺陷） | test_text_001、test_text_l6_* | 合并执行时各失败 1 次，单独复跑均 passed |

> 说明：F3 已按用户确认的「预期变更」更新 expected；#3/#4/#5 三项埋点差异**未修改 expected**，待产品确认口径后再定是改断言还是提缺陷。

## 12. 修正：P-NEW-03 判定反转（2026-10-12 晚）

用户手动验证指出「P-NEW-03 确实发送了消除事件」。复核结论：**用户正确，此前归因为「埋点口径不一致」是误判，实际是本仓库用例点错按钮。**

### 根因

`tests/test_canvas_stats_all.py::click_text()` 的兜底分支是**子串匹配**：

```python
page.locator("button, [role=button], li, span, p").filter(has_text=re.compile(re.escape(text), re.I))
```

P-NEW-03 原 `actions: [AI Delete, All, Remove]`：

| action | 实际情况 |
|---|---|
| `AI Delete` | 页面上**不存在**该按钮（AI 消除面板是上传后自动打开的） |
| `All` | 实际是 Quick Select 里的一个 **缩略图 button**（文本恰为 `All`），子串兜底没有命中它 |
| `Remove` | 子串兜底**第一个命中元素是工具栏的 `Remove BG`**（面板按钮实际文案为 `Remove 5`） |

命中 `Remove BG` → 面板被切到「背景移除/抠图」→ 面板主提交发出
`新画布抠图购买出现en_magic-eraser-with-ai-detection` + `无限画布页背景移除通用功能点数用完触发购买`，
因此断言 `新画布消除购买出现en_magic-eraser-with-ai-detection` 失败。

MCP 实测（正确流程）：上传后 AI 消除面板自动打开并完成自动检测（`AI消除功能_AI检测成功`），
点 Quick Select 的 `All` 缩略图全选 → 主提交 `button.btn-bg-gradient1`（文案 `Remove 5`）启用 →
点击后**确实发出** `新画布消除购买出现en_magic-eraser-with-ai-detection`。产品行为正确。

### 修复

1. `run_actions` 新增 `click_exact`：按精确按钮名点击（`get_by_role("button", name=^text$)`），避免子串兜底误点。
2. `data/pokecut_canvas_stats_v1.yaml` 的 P-NEW-03 `actions` 改为 `[{click_exact: All}]`，并记录 `actions_note`。

验证：`test_p_new_03` → ✅ **1 passed**（`regression/verify_p_new_03_fix.log`）。

### 连带修正

- 原 §7/§10 把 P-NEW-03 归为「埋点功能词：抠图 vs 消除（待产品确认）」——**该结论作废**。
- 教训值得沉淀：`click_text` 的子串兜底在多控件同前缀场景会静默误点，且失败现象会伪装成「埋点口径/漏报」。
  排查此类失败时应先确认「实际被点击的是哪个元素」。

### P-NEW-16 / M-NEW-14 复查（同一思路，结论不同）

用同样方法复查「换背事件缺失」：

- MCP 实测 `/tools/background-changer`：上传进入画布后，因 0 credits + 自动「换背使用」，
  **购买弹窗在进入画布时自动弹出**（新版 `purchase-dialog__panel`：Premium Plan / Credits Purchase），
  流程根本没走到面板提交；事件序列为
  `无限画布页换背使用 → 购买界面进入 → 无限画布页点数用完触发购买 → 无限画布页背景更改功能点数用完触发购买`，
  画布内也不存在 `button.btn-bg-gradient1` 面板提交按钮。
- 即：期望的 `新画布换背购买出现en_background-changer` 在自动弹窗路径下**不产生**；
  与 P-NEW-03 不同，这里**不是误点**（actions 为空，无点击）。
- 仍需产品确认该事件在何种触发路径下产生（是否仅面板手动作业时发送），**未修改 expected**。

## 13. 第四轮核实：剩余失败逐条定性（2026-10-12 晚）

本轮又修正 2 处此前的错误归因，并用 MCP 对剩余每条做了实测定性。

### 新增修复（均为「用例自身问题」，非产品缺陷）

| 用例 | 原判定（错误） | 实测真相 | 修复 | 验证 |
|---|---|---|---|---|
| `test_p_new_03` | 埋点功能词「抠图 vs 消除」待产品确认 | `click_text` 子串兜底把 `Remove` 点成工具栏 `Remove BG`，误入抠图面板 | 新增 `click_exact`；actions 改 `[{click_exact: All}]` | ✅ passed |
| `test_m_core_02` | 埋点档位「通用 vs ultra」待产品确认 | 流程未选档位，面板默认标准档；选 `Ultra HD Mode` 后事件即为 `…画质增强ultra功能…` | enhance 分支先点 `Ultra HD Mode` | ✅ passed |
| `test_l3_004_id_photo_success` | 未复探 | 首页 `Sign up` 按钮漂移（同 F2），注册入口已迁移到 credits 胶囊面板 | `login_vip` 改用 `.credits-entry__pill` + `button.credits-entry__signup`（保留旧路径兜底） | ✅ passed |

> 更正 §12 的一句错误陈述：**不是**「口径不一致」，实为本仓库用例误点/漏点档位。

### 剩余失败逐条定性（MCP 实测）

| 用例 | 入口 | 实测现象 | 定性 |
|---|---|---|---|
| `test_l2_011`（PC SEO） | `/tools/zoom-in-photos` | 已登录 VIP（User8JY 可见）、上传成功；页面弹出 **Tips 弹窗**：「Sorry. Please try again in about 30 minutes. This feature is busy due to high demand…」；`Download HD` 在，`Before`/`After` **不在** | **环境态（服务端容量限流）**，非脚本/产品缺陷。修正 §10 中「限流不成立」的错误结论 —— 限流确实存在 |
| `test_l2_011`（移动端 SEO） | 同上 | 匿名会话 + 注册弹窗遮挡 | 环境态 + 匿名弹窗（见下） |
| `test_l2_006`（移动端 SEO） | `/tools/add-motion-blur-effect-to-photo` | 上传成功进入 `/create/edit?pid=`；激活 tab **正确**为 `Background`；但弹出 **「Sign Up to Get Up to 30 Credits」注册弹窗**，`.mobile-feature-workspace` 因此不可见（`wsVisible=false`） | **页面行为变更**：匿名进入 SEO 画布弹出注册弹窗，遮挡工具工作区。需 page-map 复探该弹窗（关闭方式 / 是否应改为登录态执行） |
| `test_l2_005`（移动端 SEO） | `/tools/cv-photo-editor` | 首屏入口 `button.seo-first-screen-upload-button` 文案已变为 **`Create My CV Photo`**；点击超时（被首屏轮播遮挡），文件选择器未唤起 | **落地页改版**。PC 版同名用例用两步引导（`upload_mode: cv_guide` + `guide_selector: p:text-is("Upload Image")`）可通过；移动端缺这个两步逻辑，需按新页面重探 |
| `test_p_new_16` / `test_m_new_14` | `/tools/background-changer` | 上传进入画布瞬间，因 0 credits + 自动「换背使用」，**购买弹窗自动弹出**（新版 `purchase-dialog__panel`）；`actions` 为空、无点击；画布内无 `button.btn-bg-gradient1`；事件仅 `无限画布页换背使用 → 购买界面进入 → 无限画布页点数用完触发购买 → 无限画布页背景更改功能点数用完触发购买` | 期望的 `新画布换背购买出现en_background-changer` 在**自动弹窗路径**下不产生。**非误点**（无点击动作）。待产品确认该事件在何种触发路径下发送；`expected` 未改 |

### 当前剩余失败清单（6 条）

1. `tests/test_canvas_stats_all.py::test_p_new_16[chromium]` — 换背事件（待产品确认）
2. `tests/test_canvas_stats_all.py::test_m_new_14[chromium]` — 换背事件（同上）
3. `tests/test_seo_main_upload_interactions_v1.py::TestL2SeoMainUploadInteractions::test_l2_011[chromium]` — 服务端容量限流（环境态）
4. `tests/mobile/test_seo_main_upload_mobile_v1.py::TestMobileSeoMainUpload::test_l2_011[chromium]` — 匿名注册弹窗 + 限流
5. `tests/mobile/test_seo_main_upload_mobile_v1.py::TestMobileSeoMainUpload::test_l2_006[chromium]` — 匿名注册弹窗遮挡工作区
6. `tests/mobile/test_seo_main_upload_mobile_v1.py::TestMobileSeoMainUpload::test_l2_005[chromium]` — 落地页改版

## 14. 第五轮：移动端登录入口修复（用户指正，2026-10-12 晚）

用户指正：**移动端注册/登录入口在顶部栏最右侧汉堡按钮弹出的右侧栏里**，且这两条用例需要**登录有积分的会员账号**执行。

### 根因（比此前判断更准确）

`conftest.py::login_mobile()` 旧实现：

```python
if page.get_by_role("button", name="Sign up").count() == 0:
    return          # ← 静默 return，整套 SEO 移动端 24 条全部跑成匿名态
```

移动端首页 header 已无独立 `Sign up` 按钮，故该函数**每次都直接 return**，`seo_mobile_context` 的登录态从未建立，
24 条用例全部匿名执行 → 画布内弹出「Sign Up to Get Up to 30 Credits」注册弹窗遮挡。

### 实测入口（MCP，Pixel 10 口径 390x844/dpr3/touch）

| 元素 | selector |
|---|---|
| 汉堡按钮 | `img[src*='nav_btn_mun.svg']` |
| 右侧抽屉 | `div.menu-tab`（展开态 `menu-tab-show absolute right-0 w-[75%]`） |
| 抽屉内登录 | `div.menu-tab button` 且文本为 `Log in` |
| 抽屉内注册 | `div.menu-tab button` 且文本为 `Sign up` |
| 弹窗输入 | `input[type=email]` + `input[placeholder*='Verification']` + `[data-testid='auth-submit']` |

抽屉内条目顺序：AI Free Tools / Portrait Editor / Discover / Pricing / **Sign up** / **Log in**。
MCP 实测：汉堡 → 抽屉 → `Log in` → 填 450832596@qq.com / 123456 → 提交 → credits 由 0 变 **11486**，登录成功。

### 修复

`conftest.py::login_mobile()` 改为：开汉堡 → 抽屉 → 点 `Log in` → 填表提交 → 等 auth 弹窗关闭；
保留旧版页面 `Sign up` 按钮兜底；不再静默 return。

### 验证结果

| 用例 | 结果 |
|---|---|
| `tests/mobile/...::TestMobileSeoMainUpload::test_l2_006` | ✅ **passed** |
| `tests/mobile/...::TestMobileSeoMainUpload::test_l2_005` | ✅ **passed**（此前误判为「落地页改版」；实际是未登录导致入口不可用） |
| `tests/mobile/...::TestMobileSeoMainUpload::test_l2_011` | ❌ 仍失败，但根因是**服务端 30 分钟容量限流**（Tips 弹窗「This feature is busy due to high demand」），非脚本问题 |

> 更正 §13：L2-005「落地页改版」结论**不成立**，实为未登录造成的假象。

### 当前剩余失败（3 条）

1. `tests/test_canvas_stats_all.py::test_p_new_16[chromium]` — 换背事件触发路径待产品确认
2. `tests/test_canvas_stats_all.py::test_m_new_14[chromium]` — 同上
3. `tests/test_seo_main_upload_interactions_v1.py::TestL2SeoMainUploadInteractions::test_l2_011[chromium]` + `tests/mobile/...::test_l2_011[chromium]` — `/tools/zoom-in-photos` 服务端容量限流（环境态，需间隔 >30 分钟后复跑）
