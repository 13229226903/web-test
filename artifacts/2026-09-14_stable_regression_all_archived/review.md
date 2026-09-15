---
task_id: 2026-09-14_stable_regression_all_archived
agent: review
status: completed
inputs:
  impl: artifacts/2026-09-14_stable_regression_all_archived/impl.md
  sync: artifacts/2026-09-14_stable_regression_all_archived/sync.md
  page_maps: [mobile_home_v2.yaml, home_v7.yaml, batch_v3.yaml, create_ai_tools_v2.yaml]
  evidence: evidence/mcp_drift_20260914/（log_S/T、pc_model_sequence.png、batch_delete_mode.png、create_close_sequence.png）
outputs:
  verdict: pass
  blocking_issue_count: 0
  suggestion_count: 4
  next_agent: test-writing(report-output)
created_at: 
---

# review.md — 回归漂移修复静态审查

## Blocking Issues

- 无。

## Suggestions

1. **仓库版本管理缺口**：`tests/test_pokecut_pc_home_v6.py`、`tests/test_pokecut_pc_batch_v1.py`、`tests/test_infinite_canvas_enhance_v4.py`、`tests/helpers_create_entry.py`、`data/pokecut_pc_home_v6.yaml`、`page_map/pokecut/*_v2..v7` 等均为 **untracked**，`git diff` 只能看到 2 个文件，review 无法用 diff 交叉核对 `impl.md files_changed`。建议后续把 tests/ data/ page_map/ 纳入版本管理。
2. **`L2-010` 依赖实现细节**：模板卡缩略图 `img[alt="Slim"]` 是 `class` 含 `invisible` 的叠加层，用例用 `expect_file_chooser` + `force=True` 点击。已实测可复现，但对实现细节敏感；建议后续推动给模板卡加稳定 `data-testid`（本轮不改 selector，避免超范围）。
3. **`dismiss_create_promo` 覆盖面**：目前只接入 `test_infinite_canvas_enhance_v4.py` 与 `test_infinite_canvas_text_layer_v2.py`；旧画布三个 zh-CN 脚本（insert panel v3 / text panel v1 / sticker panel v1）未接入，建议下轮全量复跑时确认是否同样受促销弹窗影响。
4. **`pc_home L2-008` 交互依赖文档化**：模型菜单为 toggle（重复 `dispatchEvent` 会关闭），已写入 `page_map/pokecut/home_v7.yaml::drift_20260914`；建议后续页面改版时优先复查该交互。

## Checked Items

| 项 | 结论 | 说明 |
|---|---|---|
| 未删除 / 弱化断言 | 通过 | 全部改动为「locator / 文案 / 数据」重定位：L1-002 仍是可见性断言、L2-010 仍断言进入 `/create/edit?pid=`、L2-008 仍断言模型菜单与设置面板选项、batch 仍断言文案等于期望值、enhance 新增弹窗兜底后才点击入口 |
| expected 非空 / 非 0 / 非 `-` | 通过 | `data/pokecut_pc_home_v6.yaml` 只删除已不存在的旧标签 `Output Resolution:`，保留实测存在的 `Output Ratio:` 与 `Number of images`；`data/pokecut_pc_batch_v1.yaml` 期望值仍为 `Delete` |
| selector 红线 | 通过 | 使用 `button.cinematic-model`、`img[alt="Slim"]`、`button:has-text(...)`、`.purchase-gift-modal img[src*="colos_pop_btn_close"]`；无 `:nth-child`、位置 XPath、hash class、通配 `*` |
| 架构与数据外置 | 通过 | 用例在 `tests/`，模板卡/模型文案/设置项外置 `data/*.yaml`；新增 `tests/helpers_create_entry.py` 不以 `test_` 开头，不会被 pytest 收集；注释为中文并标注漂移来源（page_map 版本） |
| page_map 与实现一致 | 通过 | 4 处漂移均已在对应 page_map 的 `drift_20260914` 段记录（含实测 selector、弹窗两次关闭时序、菜单 toggle 语义、Delete 文案） |
| 引用与证据 | 通过 | `sync.md` 覆盖矩阵 7 行 ↔ MCP 证据文件一一对应；`impl.md` 记录 8 条用例修复与自跑结果 |
| 自跑结果 | 通过 | 定向自跑 8/8：mobile L1-002/L2-003/L2-010、pc_home L2-008、batch L1-007/L2-011/L2-012、enhance L5-001（`reports/allure-results-drift-fix`） |
| Allure 行为树 / 截图 | 待 report-output | 本轮为定向自跑，未生成矩阵/回归报告；下一步由 report-output 产出 |

## 结论

- `verdict: pass`（0 blocking）。
- 下一步：先由 **test-writing(report-output)** 做全量复跑并生成/打开 `allure-report-regression`，用户确认后再进 regression-archive gate（更新 registry、归档）。
