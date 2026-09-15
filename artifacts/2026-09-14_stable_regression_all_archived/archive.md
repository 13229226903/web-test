---
task_id: 2026-09-14_stable_regression_all_archived
agent: orchestrator
status: archived
archived_at: 2026-09-14 20:58:03
---

# archive.md — registry 全量稳定回归 + 漂移修复（2026-09-14）

## 1. 交付物

| 类型 | 路径 |
|---|---|
| 回归报告（Allure） | `reports/allure-report-regression`（http://localhost:8123/index.html） |
| 结果聚合 | `artifacts/2026-09-14_stable_regression_all_archived/regression/summary.json` |
| 逐脚本日志 | `artifacts/.../regression/*.log`、`runner_rerun.log` |
| 回归报告说明 | `artifacts/.../report.md` |
| 漂移复探 sync | `artifacts/.../sync.md`（confirmed） |
| 实现与审查 | `artifacts/.../impl.md`（completed）、`review.md`（pass，0 blocking / 4 suggestions） |
| 页面地图增量 | `page_map/pokecut/{mobile_home_v2,home_v7,batch_v3,create_ai_tools_v2}.yaml` |
| MCP 复探证据 | `artifacts/.../evidence/mcp_drift_20260914/` |
| 清理 | `archive_cleanup_manifest.md` / `archive_cleanup_result.md`（0 删除，全部被引用保留） |

## 2. 运行结果

- 首次全量回归（修复前）：174 用例 **161 passed / 10 failed / 3 skipped**
- 修复后全量复跑：174 用例 **167 passed / 3 failed / 4 skipped**（≈76 分钟，12 脚本串行）
- 剩余 3 条失败全部为**测试服后端/GPU 环境问题**：`L6-001`（GPU `-112/-108` 排队繁忙）、`L6-002`/`L6-003`（提交 `-1002`）

## 3. 覆盖范围与关键结论

- 4 类脚本漂移全部修复并在真实回归中验证：默认模型 `Pokecut Pro→Auto`（mobile/pc 首页）、移动端模板卡 `Butt→Slim`、Batch 删除文案 `Delect→Delete`（缺陷已修复，断言方向同步）、`/create` 全新会话促销弹窗需连点两次关闭。
- **产品缺陷 0 个**：此前 bug 草稿（BUG-REG-001~008）经 page-map-sync 复探全部修正为脚本漂移；BUG-REG-009/010 为环境问题。

## 4. 关键技术决策

1. `/create` 促销弹窗兜底：`tests/helpers_create_entry.py::dismiss_create_promo`，`.purchase-gift-modal` 可见时循环点 `img[src*="colos_pop_btn_close"]`（实测需 2 次，第 2 次关定价层）。
2. pc_home 模型菜单：入口 `button.cinematic-model`，最小序列 `textbox → scrollIntoView → dispatchEvent("click")`；**菜单是 toggle**，仅未展开时才 dispatch。
3. 移动端模板卡缩略图为 `invisible` 叠加层，需 `expect_file_chooser` + `force=True` 点击。
4. 稳定回归先按 registry「当前可执行」列执行；归档副本中 7 个早期脚本素材路径按脚本目录解析、不能独立复跑（待修）。

## 5. 已知问题与风险

- `pending_fix`：PC 无限画布 Enhance（`L6-001/002/003` 依赖测试服 GPU/后端恢复；脚本已就绪，恢复后直接复跑）。
- `ai_image_text_enhancer` 3 条 skip（会员档位/环境限制，沿用基线结论）。
- review 4 条 suggestion：tests/data/page_map 大量文件 untracked（git diff 无法核对）、模板卡依赖实现细节、`dismiss_create_promo` 未覆盖旧画布 3 个 zh-CN 脚本、模型菜单 toggle 语义需随改版复查。

## 6. 知识沉淀状态

- 本次**未新增** `rule.md` / `PROJECT.md` / `skills/*`；候选经验已写入 4 份 page_map 的 `drift_20260914` 段与 sync.md 第 4 节。

## 7. 归档信息

- 归档时间：2026-09-14 20:58:03
- 执行模式：`codex_single_context`
- registry：`artifacts/regression_registry.md` 已更新（mobile/pc_home/batch 行 Page Map + Last Passed；batch 升 stable_regression；enhance 保持 pending_fix）
- 归档副本：5 个脚本 + `helpers_create_entry.py` 同目录副本已同步