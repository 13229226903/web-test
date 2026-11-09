---
task_id: 2026-10-16_stable_regression_run
agent: test-writing
status: completed
inputs:
  registry: artifacts/regression_registry.md
  target: old_canvas_ai_tools_all
outputs:
  test_file: tests/test_old_canvas_ai_tools_all.py
  archive_copy: archive/old_canvas_ai_tools/test_old_canvas_ai_tools_all.py
  base_url_fix: "fixture prefers --base-url; YAML base_url is fallback only"
self_run:
  command: python -m pytest tests/test_old_canvas_ai_tools_all.py -q --base-url=http://10.17.1.66:3102
  result: 6 passed in 2123.09s
next_agent: null
---

## 背景
3102 回归中 `test_old_canvas_ai_tools_all.py` 6 条全部 setup error，
错误信息显示当前 URL 为 `http://10.17.1.66:3001/template`，
即脚本未使用 CLI 传入的 `--base-url`。

## 根因
`canvas_session` fixture 直接读取 `DATA["base_url"]`
（`data/old_canvas_ai_tools_v1.yaml` 中为 `http://10.17.1.66:3001`），
绕过了 pytest `--base-url` 的解析，导致指定 3102 时仍打向 3001。

## 修复
1. `canvas_session(playwright)` -> `canvas_session(playwright, base_url)`，注入 pytest 的 `base_url` fixture。
2. `base_url = (base_url or DATA["base_url"]).rstrip("/")`：CLI 优先，YAML 仅作默认值。
3. 同步更新 `archive/old_canvas_ai_tools/test_old_canvas_ai_tools_all.py` 归档副本。
4. 未改动入口、selector、等待与断言（未弱化任何 expected）。

## 验证
- py_compile：通过。
- collect-only：6 tests collected。
- 单条 smoke（test_p_ait_05_navigate_only）：1 passed。
- 全量复跑：6 passed in 2123.09s。
- 说明：第一次全量复跑因入口点击偶发未弹 file chooser 报 6 error（同一环境连续 3 次独立探测均成功），
  第二次全量 6/6 通过，判定为入口 flaky，与本次修复无关。

## 遗留
- 入口点击偶发不弹 filechooser 属 flaky，建议后续在 `enter_canvas_via_template` 增加点击后短轮询/
  重试判定（本轮未改，避免扩大改动面）。
