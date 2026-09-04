# web-test

一套 UI 自动化测试编排骨架：主控（orchestrator）负责路由、状态机与门禁，5 个角色以 skill 形式承载「探索页面 → 设计用例 → 写脚本 → 审查」，各阶段用版本化 artifact 接力，关键节点停下等人确认。

## 目录结构

```
AGENTS.md                        # 项目级启动路由
artifacts/
  runtime/
    orchestrator.md              # 主控卡：任务声明 / 路由 / 状态机 / 派发 / 上限 / Gate / 上下文
    common.md                    # 共享契约：红线 / Artifact 接力 / progress / 项目约束
  regression_registry.md         # 稳定回归资产登记表
  .current_task                  # 当前任务指针（journal 用）
skills/
  ui-test-page-map-sync/SKILL.md
  ui-test-test-case-design/SKILL.md
  ui-test-test-writing/SKILL.md
  ui-test-review/SKILL.md
  ui-test-visual-review/SKILL.md
tests/  data/  page_map/  test_images/  scripts/  config/  archive/
```

## 环境准备（新机器 ）

在 Codex 里跑本项目前，先按下面准备好环境（版本为本机验证过的组合）。

### 1. 基础软件

| 软件 | 要求 | 用途 |
|---|---|---|
| Python | 3.12+（3.12.10 验证） | 跑 pytest / Playwright 脚本与 Allure 报告生成 |
| Node.js + npm | 18+（v24 验证） | 启动 Playwright MCP、安装全局命令行工具 |
| Git | 较新版本即可 | 拉取 / 推送仓库 |

### 2. Python 依赖（跑回归脚本必需）

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

- `requirements.txt` 核心：`pytest`、`pytest-playwright`、`playwright`、`pyyaml`、`allure-pytest`、`pytest-html`。
- `python -m playwright install chromium` 会装 chromium 与 headless shell；回归默认 headless，调试可加 `--headed`。
- `conftest.py` 会自动读取根目录 `.env`（无需额外依赖），并自动创建 `reports/`、`data/screenshots/` 等目录。

### 3. 全局命令行工具（npm）

```bash
npm install -g @playwright/mcp allure-commandline
```

- `allure-commandline`：执行 `allure generate` 生成 Allure 报告（本机验证 2.43.0）。
- `@playwright/mcp`：探索阶段的 Playwright MCP server，Codex CLI / 非桌面端接入时需要（见下节）。

### 4. 需要的 MCP（只需要一个）

本项目页面探索固定走 **Playwright MCP**（`exploration_driver: playwright_mcp_only`），不需要 Chrome DevTools MCP 或其它业务 MCP。

- **Codex 桌面端**：已内置 Playwright MCP（`browser_navigate` / `browser_snapshot` / `browser_click` / `browser_type` / `browser_upload` / `browser_take_screenshot` 等），无需额外配置。
- **Codex CLI / 其它 agent**：给 agent 注册一个 MCP server，例如：

  ```toml
  [mcp_servers.playwright]
  command = "npx"
  args = ["@playwright/mcp@latest", "--browser", "chromium"]
  ```

  需要跨会话保留登录态时，可追加 `--storage-state <路径>`（可选）。
- 探索过程的本地 MCP 会话证据落在 `.playwright-mcp/`，已 gitignore、不入库。

### 5. 访问与密钥

- 被测站点为内网测试服，默认 `http://10.17.1.66:3001`（见 `pytest.ini` 的 `base_url`），需要能访问该内网；验证码固定 `123456`，测试账号见 `PROJECT.md`。
- 根目录 `.env`（已 gitignore、不入库）按需配置 AI 视觉 / AI 审查用密钥，模板见 `.env.example`：

  ```
  VISUAL_REVIEW_API_KEY=
  DEEPSEEK_API_KEY=
  OPENAI_API_KEY=
  OPENAI_BASE_URL=
  OPENAI_MODEL=
  ```

  纯 pytest 回归不依赖这些 key，缺省不影响 collect / 执行；只有 visual-review / AI 审查步骤才需要配置。

### 6. 常用命令速查

```bash
python -m pytest tests/<file>.py -q            # 跑单个归档脚本（headless）
python -m pytest --headed tests/<file>.py      # 有头模式调试
python -m pytest --collect-only -q             # 只收集用例，检查无 error / warning
allure generate reports/allure-results -o reports/allure-report-regression --clean
python -m http.server 8123 --directory reports/allure-report-regression
# 浏览器打开 http://localhost:8123/index.html
```

更完整的执行流程与报告规范见 `artifacts/runtime/orchestrator.md` 与 `skills/ui-test-test-writing/SKILL.md`。

## 流程总览

```
你下达任务（自然语言或任务声明）
  ↓
主控读 AGENTS.md + orchestrator.md + common.md
  → 判定 task_type，自动选择 M1/M2，建/恢复 artifacts/<task_id>/state.md、progress.log、shots/
  ↓
按 task_type 路由，每个阶段加载对应 skills/<role>/SKILL.md 执行
  ↓
在三个人工 gate 停下等你确认
  ↓
state.md=completed，收工
```

## 角色与 skill

| 角色 | skill | 产出 |
|---|---|---|
| page-map-sync | ui-test-page-map-sync | Playwright MCP 探索 → page_map_vN.yaml + sync.md |
| test-case-design | ui-test-test-case-design | requirement_draft / cases.md |
| test-writing | ui-test-test-writing | tests/ + data/*.yaml + impl.md |
| review | ui-test-review | review.md |
| visual-review | ui-test-visual-review | visual_review.md |

## 任务类型与路由

| task_type | 流程 |
|---|---|
| new_feature_test | test-case-design(requirement_draft) → page-map-sync → sync gate → test-case-design(final_after_sync) → cases gate → test-writing → review → report-output → regression-archive gate |
| existing_feature_first_exploration | page-map-sync → sync gate → test-case-design(final_after_sync) → cases gate → test-writing → review → report-output → regression-archive gate |
| stable_regression | 优先跑 regression_registry 登记脚本；仅漂移 / 差异 / 需求变更才局部回退 |
| single_agent | 只加载对应一个角色 skill |

## 怎么下达任务

自然语言即可。主控会判定 task_type、自动选择 M1/M2，并补齐 scope / stop_at / 账号态等写进 state.md 的 assumptions；只有 PRD 路径与入口 URL 缺失时才问。

### 场景一：走全流程
- 新功能首次提测：举例：用例文档在：D:\downloads\用例\task-22-飞书文档_ v3.0\移动端首页优化大纲（安国）.md，移动端首页入口：http://10.17.1.66:3001/，新功能首次提测，需要按照用例去执行测试，与用例不符的按规则列出。
- 功能已上线但缺资产：`<url>` 这个功能已经上线了，帮我补页面地图、用例、脚本，走完整流程到 Allure 报告。（**举例**：用例文档：D:\downloads\用例\task-22-飞书文档_ v3.0\移动端首页优化大纲（安国）.md，移动端首页入口：http://10.17.1.66:3001/，存量功能首次探索，结合用例去探索页面交互）

### 场景二：已有脚本的功能有改动，改脚本
- `<url>` 这个功能最近有改动（比如按钮文案变了），更新一下已归档的回归脚本，跑通并更新 Allure 报告。

### 场景三：回归已有归档脚本
- 回归一下「<功能名>」已登记的脚本。
- 跑一下regression_registry.md里的已归档脚本。
- 或：跑一下 `tests/<file>.py` 回归并出 Allure 报告。

### 单角色
- 只更新 xxx 页面地图 / 只写用例 / 只审查这次改动。

完整字段与执行模式选择见 `artifacts/runtime/orchestrator.md` 的「任务声明」和「执行模式自动选择」。

## 关键概念

- **artifact 接力**：阶段之间只靠版本化文档接力；`pending_review` 必停，`confirmed` 才能继续。
- **三个人工 gate**：sync_review、cases_review、regression-archive。
- **执行模式**：`codex_single_context`（单上下文） / `codex_subagent`（子代理隔离），由主控按 task_type 自动选择。
- **探索驱动**：`page-map-sync` 固定使用 `exploration_driver: playwright_mcp_only`；Chrome DevTools MCP 不作为默认诊断工具。
- **共享红线**：selector / 断言 / skipped / 上传素材等见 `artifacts/runtime/common.md`。


## Playwright MCP 探索试用

当前框架的探索阶段已切换为 Playwright MCP only：`page-map-sync` 通过 Playwright MCP 进行页面打开、accessibility snapshot、点击、输入、hover、滚动、上传和截图留证；最终仍按既有 schema 写入版本化 `page_map` 与 `sync.md`，并停在 sync gate 等人工确认。后续 `test-writing` 仍生成 pytest / Playwright 可复跑脚本与 Allure 报告，不以 MCP 会话替代正式回归资产。

如 Playwright MCP 无法定位深层网络、性能或 JS 根因，探索阶段只在 `sync.md` 记录诊断边界与 `bug_candidate` / `blocked`，不默认引入 Chrome DevTools MCP。

## 项目约定

本项目对接 Pokecut：站点 / 账号 / 素材白名单 / DEBUG 切换等见 `PROJECT.md`；编码与技术避坑见 `rule.md`，不在此重复。

