---
task_id: 2026-09-15_seo_main_upload_mobile_interactions
agent: orchestrator
artifact: archive
status: completed
archived_at: 2026-09-16 14:03:33
archived_by_user: true
registry_key: pokecut/seo_main_upload_mobile_interactions
---

# 归档记录 — SEO 页面主上传按钮交互（移动端）

## 1. 归档范围

| 项 | 路径 |
|---|---|
| Feature | SEO 页面主上传按钮交互（24 个唯一页面）· 移动端 390x844 |
| URL | `http://10.17.1.66:3001` + 24 条 SEO 路径（含 `/de`、`/zh-tw`、`/th` 语言入口） |
| Task ID | `2026-09-15_seo_main_upload_mobile_interactions` |
| 源脚本 | `tests/mobile/test_seo_main_upload_mobile_v1.py` |
| 归档副本 | `archive/seo_upload_mobile/test_seo_main_upload_mobile_v1.py`（+ `archive/seo_upload_mobile/conftest.py` 移动端 fixture 载体） |
| 数据 | `data/pokecut_seo_main_upload_mobile_interactions_v1.yaml`（24 条） |
| Page Map | `page_map/pokecut/seo_upload_mobile/*_v1.yaml`（24 份，confirmed） |
| Sync | `artifacts/2026-09-15_seo_main_upload_mobile_interactions/sync.md` |
| Cases | `artifacts/2026-09-15_seo_main_upload_mobile_interactions/cases.md`（case_count=24） |
| Impl | `artifacts/2026-09-15_seo_main_upload_mobile_interactions/impl.md`（R1~R10） |
| Review | `artifacts/2026-09-15_seo_main_upload_mobile_interactions/review.md`（round 2 verdict=pass） |
| 矩阵报告 | `reports/allure-report-mobile-matrix`（23 passed + 1 xfailed，服务 `http://localhost:8125/index.html`） |

## 2. 归档副本可独立复跑校验

| 检查项 | 结果 |
|---|---|
| 公共模块位置 | 全部依赖仓库根 `conftest.py`：移动端 fixture（`mobile_context` / `mobile_session_page` / `login_mobile`）已**上收仓库根**（`rule.md` 禁止在 `archive/**` 新增 `conftest.py`，会遮蔽 root conftest） |
| 路径常量解析 | 脚本内 `_repo_root()` 按 `test_images/` 逐级上溯仓库根；`data/`、`test_images/`、`page_map/` 在 `archive/<dir>/` 位置同样解析到仓库根 |
| 归档副本 collect-only | 单文件 24 collected / 0 error；**整仓 `pytest archive --collect-only -q` = 228 collected / 0 error（exit 0）** |
| 归档后修复记录 | 归档初版曾在 `archive/seo_upload_mobile/` 放 `conftest.py`（违反 `rule.md`），导致 `pytest archive` 出现 `ImportError: cannot import name 'visual_assert' from 'conftest'`；已按方案 A 把移动端 fixture 上收仓库根并删除该 conftest |
| 归档后复跑 | 按惯例 **未复跑**（归档前刚在 `tests/mobile/` 位置全量通过：`23 passed + 1 xfailed in 253.71s`，证据 `evidence/selfrun_mobile_full13_R10.log`） |

## 3. archive-cleanup 结果

清单：`archive_cleanup_manifest.json`

| 动作 | 数量 | 说明 |
|---|---|---|
| 删除前备份到任务目录 | 123 | 根目录一次性 MCP 探针 / 时序探针 / 数据补丁脚本 → `evidence/oneoff_scripts/` 后删除 |
| 删除 | 24 | 22 张 `data/screenshots/*_failure.png`（上一轮失败残留，13:20 已先清理）+ `reports/allure-results-mobile-iso/`、`reports/allure-results-mobile-fix/` |
| 保留 | 10 类 | `sync.md` / `cases.md` / `impl.md` / `review.md` / `evidence/`（含 burst 连拍帧与功能面板扫描）/ `shots/`（被 page_map notes 引用）/ `data/screenshots/*_final.png`（24 张）/ `data/*.yaml` / `page_map/pokecut/seo_upload_mobile/` / `tests/mobile/` / `reports/allure-*-mobile-matrix` |

## 4. 知识沉淀（待用户确认）

本轮候选（尚未写入落点，等用户确认）：

| # | 候选落点 | 内容 |
|---|---|---|
| ① | `rule.md`「移动端画布链路」 | 移动端 SEO 页上传后 21/24 走 `/create/edit?pid=`（PC 多为 `/agent`）；底部主面板 `.mobile-primary-panel`（tabs: Trending Tools / AI Image / Background / Adjust / Insert）；断言与截图须按移动端口径单独写 |
| ② | `rule.md`「等待时机」 | 进入画布后底部面板先以通用 tab 渲染，工具预设 **200~900ms** 后才切工具面板；断言「默认面板」必须等预设生效 |
| ③ | `rule.md`「截图时机」 | 工具工作区是上滑浮层：截图前须等布局指纹（canvas 数 + 工作区画布/选中框/面板几何）连续两次一致，否则会截到过渡帧（同一张图出现两次） |
| ④ | `rule.md`「断言设计」 | 「打开了什么功能面板」≠ 底部 tab：多数 SEO 页会额外自动展开 `.mobile-feature-workspace` 工具工作区面板（标题=工具名），只断言底部 tab 会漏掉真实功能面板 |
| ⑤ | `PROJECT.md` | 移动端登录只有 `Sign up` 入口（弹窗内填邮箱+验证码即登录，无需点 Send） |

## 5. 最终状态

- 用例数：24（L2 × 24，去重后）
- 全量自跑：**23 passed / 0 failed / 1 xfailed**（253.71s）
- 已知缺陷：**BUG-2026-0916-01** `/tools/youtube-banner-maker`（L2-018）上传后未进入裁剪态（应为裁剪框 + `Crop` 按钮），实测停留在通用 `Trending Tools` 工具列表；用例保留断言 + `xfail(strict=True)`，修复后会转 XPASS 提醒回归
- Allure 矩阵：`reports/allure-report-mobile-matrix`（24 条，description 含「功能面板断言」；24/24 各 1 张稳定态截图）
- 维护提示：每条用例真实消耗 credits；后端 AI 任务排队/限流时会成组失败，先做单页探针复核再判定（见 `rule.md`「环境异常与代码回归的区分」）

## 6. 归档后修复（2026-09-16 17:38:09，方案 A）

| 项 | 内容 |
|---|---|
| 问题 | `archive/` 与 `tests/` 下各有子目录 `conftest.py`，其模块名 `conftest` 遮蔽 root conftest；`pytest archive --collect-only` 报 `ImportError: cannot import name 'visual_assert' from 'conftest'`，`pytest --collect-only`（整仓）报 18 个 `cannot import name 'allure_screenshot'` |
| 修复 | 移动端 fixture（`mobile_context` / `mobile_session_page` / `login_mobile`）**上收仓库根 `conftest.py`**；删除 `tests/mobile/conftest.py` 与 `archive/seo_upload_mobile/conftest.py`；live 测试与归档副本改用 `mobile_session_page`（避免与既有 PC `session_page` 重名） |
| 顺带修 | `archive/pc_batch/test_pokecut_pc_batch_v1.py` 的 `parents[1]` 写死层级 → `_repo_root()` 逐级上溯（原报 `archive/data/pokecut_pc_batch_v1.yaml` FileNotFoundError） |
| 复验 | 整仓 collect-only：**335 collected / 0 collection error**；归档 collect-only：**228 collected / 0 error（exit 0）**；移动端全量复跑：**23 passed + 1 xfailed（290.25s）**，矩阵报告重建（24 条、24/24 各 1 张附件） |
| 遗留（非本任务引入） | `tests/test_seo_ai_explore.py`（import `helpers/browser_use_explorer.py`，其第 45-46 行在 import 时 `sys.stdout = io.TextIOWrapper(...)`）会污染 pytest capture → 整仓 `collect-only` 退出码 1（`ValueError: I/O operation on closed file.`），需另行修复 |
## 7. 知识沉淀落盘（2026-09-16 19:21:10，用户确认后执行）

第 4 节候选 + 后续补充项已按确认方案落盘（24 份移动端 page_map 保持 Pixel 10 原样，仅登记为历史例外）：

| # | 落点 | 内容摘要 |
|---|---|---|
| ①②③④ | `rule.md`「画布"已渲染"的判定」 | 章首加移动端链路（`.mobile-primary-panel`）；/create/edit 小节后加布局指纹截图判据 + 「功能面板 ≠ 底部 tab」 |
| ② | `rule.md`「等待时机」 | 面板预设 200~900ms 才切专属 tab，断言默认面板前必须等预设生效 |
| ⑥ | `rule.md`「Vue 交互与文件选择器」 | 上传入口用 `button.seo-first-screen-upload-button`，不按 CTA 文案匹配 |
| ⑧ | `rule.md`「环境异常与代码回归的区分」 | 502/504、入口 20s 未挂载 → 同 URL 重试一次再判定 |
| D2/D3/D4 | `rule.md`「脚本复用与仓库资源路径」 | 逐个路径常量核对 + live/archive 同改；同名文件不能同批收集（单跑口径）；归档 collect-only 门槛（0 error 且 exit 0） |
| D1⑦ | `rule.md` 新增「Windows 执行环境」 | 禁止 import 期替换 `sys.stdout`（假绿少收用例）；三引号 `\n` 转义与 GBK print 坑 |
| ⑤⑬ | `PROJECT.md` | 移动端只有 `Sign up` 入口；移动端设备口径默认 iPhone 390x844/dpr3/touch，例外需登记 |
| ⑨⑩⑫ | `skills/ui-test-page-map-sync/SKILL.md` | 时间线采样；MCP 实操边界；移动端设备模拟生效判据（viewport guard） |
| ⑪③ | `skills/ui-test-test-writing/SKILL.md` | `xfail(strict)` 在 Allure 显示 skipped；截图前需满足布局指纹判据（交叉引用） |
| ⑫ | `scripts/mcp/README.md` | 移动端 MCP 启动需带设备模拟参数，否则静默跑成 PC 版 |
| 例外登记 | `artifacts/regression_registry.md` | SEO 移动端行 Notes 标注取证口径 Pixel 10（历史例外） |
| 防扩散 | `conftest.py` + live/归档测试 | `mobile_context`/`mobile_session_page` → `seo_mobile_context`/`seo_mobile_session_page`，标注仅 SEO 套件、Pixel 10 历史口径 |

复验：`pytest tests/mobile --collect-only` 24/0、`archive/seo_upload_mobile` 24/0、`pytest archive --collect-only` 228/0、整仓 `pytest --collect-only` 468/0（均 exit 0）。未实跑用例。
