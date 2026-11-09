# 稳定回归报告

- 任务: `2026-10-12_stable_regression_registry`
- 目标环境: `http://10.17.1.66:3001/`
- 执行对象: `artifacts/regression_registry.md` 中 URL 登记为本环境的 `stable_regression` 条目 `Tests` 列当前脚本（12 个 suite）
- 规模: 12 个 suite / 232 条用例
- 日志目录: `artifacts/2026-10-12_stable_regression_registry/regression/`
- 汇总: `artifacts/2026-10-12_stable_regression_registry/regression/summary.json`
- Allure 原始结果: `reports/allure-results-regression/`
- Allure 报告: `reports/allure-report-regression/` → `http://localhost:8123/index.html`
- 执行口径: 串行、单 suite 独立进程；未修改任何脚本 / 断言 / 测试数据

## 简易回归报告

```text
【回归测试报告】2026-10-12 14:11

✅ 人像检测三入口页（Ethnicity / Body Shape / Face Comparison）  14/14 · 6m06s
❌ 文字画质增强实验页（AI Image Text Enhancer）  6/18 · 12m49s  (3 skipped)
   └ TC-TEXT-L2-005｜分辨率区显隐与无效果置灰（选择态） — 主按钮点数应为 2，实际为 5；按钮文本=Enhance 5（cost_state=paid）
   └ TC-TEXT-L4-001｜多选组合点数实时刷新与普通账号点数规则 — 主按钮点数应为 2，实际为 5；按钮文本=Enhance 5（cost_state=paid）
   └ TC-TEXT-L4-003｜会员账号 Free icon 与点数规则 — 主按钮点数应为 4，实际为 10；按钮文本=Enhance 10（cost_state=paid）
   └ TC-TEXT-L4-004｜单项购买账号点数规则 — 主按钮点数应为 2，实际为 5；按钮文本=Enhance 5（cost_state=paid）
   └ TC-TEXT-L4-005｜移动端上传后模式与点数区域 — 主按钮点数应为 2，实际为 5；按钮文本=Enhance 5（cost_state=paid）
   └ TC-TEXT-L5-001｜分辨率边界 [1K图默认2k] — 主按钮点数应为 2，实际为 5；按钮文本=Enhance 5（cost_state=paid）
   └ TC-TEXT-L5-002｜分辨率边界 [2730x4096图over2K] — 主按钮点数应为 2，实际为 5；按钮文本=Enhance 5（cost_state=paid）
   └ TC-TEXT-L5-003｜分辨率边界 [4500x3000图over4K] — 主按钮点数应为 6，实际为 10；按钮文本=Enhance 10（cost_state=paid）
   └ TC-TEXT-L5-004｜分辨率边界 [6144x8192图over4K非highest] — 主按钮点数应为 6，实际为 10；按钮文本=Enhance 10（cost_state=paid）
❌ 画布页文字功能  0/6 · 4m00s
   └ [L2][P0] Background 无填充/色盘/取色 — Locator.click: Timeout 30000ms exceeded.
   └ [L2][P0] Outline Types/色盘/取色/四滑块/描边效果 — Locator.click: Timeout 30000ms exceeded.
   └ [L2][P0] 选中/收起/重开 + Tab/Alignment/Font/Fill — Locator.click: Timeout 30000ms exceeded.
   └ [L5][P0] Reflection 四参数可调 + 实际反射效果 — Locator.click: Timeout 30000ms exceeded.
   └ [L5][P0] Space 单行禁用 + 两行 Height 生效 — Locator.click: Timeout 30000ms exceeded.
   └ [L6][P0] 入口上传 + 左侧工具栏 + Add Text — Locator.click: Timeout 30000ms exceeded.
❌ Pokecut 移动端首页优化（Mobile Home v3）  37/38 · 7m17s
   └ L3-004: ID Photo Maker 抠图成功进入证件照画布 — Locator.click: Timeout 15000ms exceeded.
✅ 帮助中心（/help）  11/11 · 3m09s
✅ 旧画布 Insert 面板与图层属性（legacy canvas）  24/24 · 10m02s
✅ 旧画布文字功能（Text 面板 + 文字图层参数）  13/13 · 6m29s
✅ 旧画布贴纸调参面板（legacy canvas，一个贴纸）  9/9 · 3m32s
❌ SEO 页面主上传按钮交互（24 个唯一 SEO 页面）  23/24 · 13m46s
   └ /tools/zoom-in-photos 上传 1K.jpg 后到达放大结果态（Before/After + Download HD） — Locator expected to contain text 'Before'
❌ SEO 页面主上传按钮交互（24 个唯一 SEO 页面）· 移动端  21/24 · 8m51s  (1 xfailed)
   └ /tools/add-motion-blur-effect-to-photo 移动端上传 1K.jpg 后进入旧画布（底部主面板） — L2-006 上传后应自动打开工具功能面板 'Blur Background'（.mobile-feature-workspace 标题匹配），实测 wsVisible=False wsText=''
   └ /tools/cv-photo-editor 移动端上传 1K.jpg 后到达证件照画布（Photo Size） — Page URL expected to be 're.compile('/tools/id-photo-edit\\?pid=[0-9a-f\\-]+#?$')'
   └ /tools/zoom-in-photos 移动端上传 1K.jpg 后到达放大结果态 — Locator expected to contain text 'Before'
✅ Create / Chat to Edit / Auto 意图识别（10 条 prompt）  11/11 · 6m17s
❌ 画布统计优化（PC 无限画布/新画布 + 移动端画布页/新画布统计埋点，40 条）  15/40 · 99m02s  (4 skipped)
   └ M-CORE-02: 移动端 xx 功能点数用完触发注册与注册成功 — 「移动端画布画质增强ultra功能点数用完触发注册」sendGaEvent 次数应为 1，实际 0（0=漏报，>=2=多报）；最近 sendGaEvent: 网站首页_进入 | 网站首页_进入_en语言版 | 移动端_底部栏upload点击 | 上传成功 | en_edit页面_
   └ M-CORE-03: 移动端点数用完触发购买与 xx 功能购买 — 未出现购买弹窗
   └ M-CORE-04: 移动端 xx 功能与通用购买成功 — 未出现购买弹窗
   └ M-CORE-06: 移动端画布页 xx 弹窗确认 — 「移动端画布页_背景移除通用弹窗确认」sendGaEvent 次数应为 1，实际 0（0=漏报，>=2=多报）；最近 sendGaEvent: 用户设备信息 | 网站首页_进入 | 网站首页_进入_en语言版 | 移动端_底部栏upload点击 | 上传成功 | en_edit页
   └ M-CORE-07: 移动端画布页画质增强结果弹窗下载 — 「移动端画布页_画质增强ultra弹窗下载」sendGaEvent 次数应为 1，实际 0（0=漏报，>=2=多报）；最近 sendGaEvent: 网站首页_进入 | 网站首页_进入_en语言版 | 移动端_底部栏upload点击 | 上传成功 | en_edit页面_进入 |
   └ M-NEW-01: 移动端新画布增强购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-02: 移动端新画布抠图购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-03: 移动端新画布消除购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-05: 移动端新画布扩图购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-06: 移动端新画布脸部购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-07: 移动端新画布身材购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-08: 移动端新画布发型购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-10: 移动端新画布图生图购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-11: 移动端新画布文生图购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-12: 移动端新画布背景模糊购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-13: 移动端新画布照片修复购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ M-NEW-14: 移动端新画布换背购买出现与成功 — 未出现购买弹窗，无法断言购买出现统计
   └ P-INF-02: PC 无限画布点数用完触发购买成功 — PC Enhance 面板未显示 Ultra HD Mode
   └ P-INF-03: PC 无限画布结果图下载保存 — AI Enhancer 面板未显示主 Enhance 提交按钮
   └ P-NEW-03: PC 新画布消除购买出现与成功 — 「新画布消除购买出现en_magic-eraser-with-ai-detection」sendGaEvent 次数应为 1，实际 0（0=漏报，>=2=多报）；最近 sendGaEvent: en_magic-eraser-with-ai-detection页面_进入 | en
   └ P-NEW-16: PC 新画布换背购买出现与成功 — 「新画布换背购买出现en_background-changer」sendGaEvent 次数应为 1，实际 0（0=漏报，>=2=多报）；最近 sendGaEvent: 购买界面进入 | create页自动出现购买弹窗 | en_background-changer页面_进入 |

合计: 183 通过 / 41 失败 / 7 跳过 / 1 xfailed · 总耗时 172m25s（含 canvas_stats 首轮超时 + 补跑）
状态: ❌ 有失败

Allure 报告: http://localhost:8123/index.html
```

## 逐 suite 结果

| # | Feature | Script | Result | Counts | Time |
|---|---|---|---|---|---|
| 1 | 人像检测三入口页（Ethnicity / Body Shape / Face Comparison） | `tests/test_pokecut_portrait_detector.py` | passed | {"passed": 14} | 6m06s |
| 2 | 文字画质增强实验页（AI Image Text Enhancer） | `tests/test_ai_image_text_enhancer_experiment.py` | failed | {"passed": 6, "failed": 9, "skipped": 3} | 12m49s |
| 3 | 画布页文字功能 | `tests/test_infinite_canvas_text_layer_v2.py` | failed | {"failed": 6} | 4m00s |
| 4 | Pokecut 移动端首页优化（Mobile Home v3） | `tests/test_mobile_home.py` | failed | {"passed": 37, "failed": 1} | 7m17s |
| 5 | 帮助中心（/help） | `tests/test_help_page.py` | passed | {"passed": 11} | 3m09s |
| 6 | 旧画布 Insert 面板与图层属性（legacy canvas） | `tests/test_old_canvas_insert_panel_v3.py` | passed | {"passed": 24} | 10m02s |
| 7 | 旧画布文字功能（Text 面板 + 文字图层参数） | `tests/test_old_canvas_text_panel_v1.py` | passed | {"passed": 13} | 6m29s |
| 8 | 旧画布贴纸调参面板（legacy canvas，一个贴纸） | `tests/test_old_canvas_sticker_panel_v1.py` | passed | {"passed": 9} | 3m32s |
| 9 | SEO 页面主上传按钮交互（24 个唯一 SEO 页面） | `tests/test_seo_main_upload_interactions_v1.py` | failed | {"passed": 23, "failed": 1} | 13m46s |
| 10 | SEO 页面主上传按钮交互（24 个唯一 SEO 页面）· 移动端 | `tests/mobile/test_seo_main_upload_mobile_v1.py` | failed | {"passed": 20, "failed": 3, "xfailed": 1} | 8m51s |
| 11 | Create / Chat to Edit / Auto 意图识别（10 条 prompt） | `tests/test_create_chat_to_edit_auto_v1.py` | passed | {"passed": 11} | 6m17s |
| 12 | 画布统计优化（PC 无限画布/新画布 + 移动端画布页/新画布统计埋点，40 条） | `tests/test_canvas_stats_all.py` | failed | {"passed": 15, "failed": 21, "skipped": 4} | 99m02s |

## 失败归因（候选分类，需局部复探确认）

> 本轮按稳定回归红线未修改脚本 / 断言 / 测试数据；以下为归因假设，未做修复。

1. **文字画质增强页 credits 计费（9 条）**：主按钮点数期望 `2/4/6`，实测文案 `Enhance 5` / `Enhance 10`（`cost_state=paid`）。
2. **画布页文字功能（6 条，整 suite 全挂）**：进入画布后左侧工具栏文字入口 `Locator.click` 30s 超时，疑似入口 / 工具栏 selector 漂移。
3. **移动端购买弹窗未出现（canvas_stats 11 条 + 移动端 SEO 相关）**：现场复核 0-credit 账号 `autotest202609171333@qq.com` credits 仍为 `0`，故更可能是移动端购买弹窗触发 / 弹窗结构变更，而非账号态问题。
4. **埋点漏报（canvas_stats 5 条）**：`sendGaEvent` 期望 1 次实际 0 次（M-CORE-02/06/07、P-NEW-03、P-NEW-16）。
5. **PC 无限画布 UI 缺失（P-INF-02/03）**：Enhance 面板未出现 `Ultra HD Mode` 与主 `Enhance` 提交按钮。
6. **环境态偶发（SEO 上传 PC/移动端 L2-011）**：页面实测 `Processing failed, please try again` 及「30 分钟内重试」限流提示。
7. **移动端首页 L3-004**：证件照成功链路点击 15s 超时（单条）。
8. **移动端 SEO L2-005/L2-006**：`L2-005` 上传后未进入 `/tools/id-photo-edit?pid=`；`L2-006` 上传后未自动展开 `.mobile-feature-workspace` 工具面板。

## 备注

- `canvas_stats` 首轮在 5400s 上限处被截断（35/40），剩余 5 条 `M-NEW-10..14` 已单独复跑补全，40 条结果完整。
- xfail 用例（移动端 SEO `L2-018` 已知缺陷 BUG-2026-0916-01）在 Allure 中计入 skipped，属预期。
- 排除项：dev 域条目（detection_ui_seo_l6 / pc_home_v6 / pc_batch_v1）与 `pending_fix` 条目（infinite_canvas_enhance_v4）本轮未执行。

---

## 修复后状态（2026-10-13 追加）

> 上方【简易回归报告】是 **2026-10-12 修复前基线**（12 suite / 232 条：183 passed / 41 failed / 7 skipped / 1 xfailed），
> Allure 报告 `reports/allure-report-regression` 亦为该基线结果，**未做全量复跑**（用户指示「不用复跑」）。

41 条失败的收敛情况：

| 分类 | 条数 | 处置 |
|---|---|---|
| 脚本漂移（F1/F2/F3/A 组）；其中 2 条转为 xfail 标记 | 39 | 已按漂移修复并逐条定向复跑通过，证据见 `regression/verify_*.log` |
| 环境态（`test_l2_011` PC + 移动端） | 2 | **未处理**（用户指示）：`/tools/zoom-in-photos` 服务端 30 分钟容量限流，间隔 12.5h 复跑仍复现 |

已知产品缺陷：`BUG-2026-1012-01`（换背事件不发，P-NEW-16 / M-NEW-14 已标 `xfail(strict=True)` + Allure 标签 `known_bug`）。

归档记录：`artifacts/2026-10-12_stable_regression_registry/archive.md`

本地查看基线报告：

```powershell
python -m http.server 8123 --directory reports/allure-report-regression
# 浏览器打开 http://localhost:8123/index.html
```
