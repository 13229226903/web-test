---
task_id: 2026-09-21_mobile_home_drift_fix
agent: test-writing
status: completed
inputs:
  sync: artifacts/2026-09-21_mobile_home_drift_fix/sync.md (confirmed)
  page_map: page_map/pokecut/mobile_home_v3.yaml
  cases: artifacts/task-22_feishu_mobile_home/cases.md + 用户 2026-09-21 漂移确认
outputs:
  test_file: tests/test_mobile_home.py
  archive_file: archive/mobile_home/test_mobile_home.py
  data_file: null
  collect_only:
    command: python -m pytest archive/mobile_home/test_mobile_home.py --collect-only -q --base-url=http://10.17.1.66:3001
    result: 38 collected, 0 error
  self_run:
    command: python -m pytest archive/mobile_home/test_mobile_home.py -q --base-url=http://10.17.1.66:3001
    result: 38 passed in 460.92s
    log: artifacts/2026-09-21_mobile_home_drift_fix/selfrun_full_final.log
regression_candidate:
  eligible: true
  reason: 归档副本 38/38 通过；四项用户确认漂移已按 page_map v3 修订
  suggested_tests: tests/test_mobile_home.py
  suggested_archive: archive/mobile_home/test_mobile_home.py
  registry_key: task-22_feishu_mobile_home
next_agent: review
---

# impl.md — 移动端首页漂移修复

## 实现摘要

按 `page_map/pokecut/mobile_home_v3.yaml` 与用户确认的实际行为，同步修改当前脚本和归档副本：

1. `DEFAULT_MODEL` 更新为页面实际默认值 `Nano Banana 2 Lite`。
2. `L1-002` 默认模型入口可见性断言改为 `Nano Banana 2 Lite`。
3. `L2-003` 模型弹层用例改为点击 `Nano Banana 2 Lite` 入口；原模型选项断言保持不变。
4. `L2-004` 按“比例随模型变化”处理：绑定默认模型 `Nano Banana 2 Lite`，断言实际 8 项比例完整集合 `1:1 / 3:4 / 4:5 / 4:3 / 9:16 / 16:9 / 2:3 / 3:2`，不再使用旧 `9:21` 固定预期。
5. `L2-010` `Slim` 模板卡从失效的 `img[alt='Slim']` 改为稳定定位 `div[role='button'][aria-label='Slim']`；保留 file chooser 与 `/create/edit?pid=*` 断言，移除不必要的 `force=True`。
6. `L2-020 Generate` 默认模型断言改为实际值 `Nano Banana 2 Lite`；URL 跳转断言保持不变。

`tests/test_mobile_home.py` 与 `archive/mobile_home/test_mobile_home.py` 修改后 SHA256 一致。

## 自修与验证

- `py_compile`：通过。
- collect-only：38 collected / 0 error。
- 定向运行修复项：4 passed in 52.29s。
- `L2-004` 定向复跑：1 passed in 9.55s。
- 最终归档副本全量复跑：**38 passed in 460.92s**。
- 无 failed、无 skipped；本轮不保留任何已知失败或降级预期。

## 命令与日志

```powershell
python -m py_compile tests/test_mobile_home.py archive/mobile_home/test_mobile_home.py
python -m pytest archive/mobile_home/test_mobile_home.py --collect-only -q --base-url=http://10.17.1.66:3001
python -m pytest <L1-002/L2-003/L2-004/L2-010/L2-020-generate> -q --base-url=http://10.17.1.66:3001
python -m pytest archive/mobile_home/test_mobile_home.py -q --base-url=http://10.17.1.66:3001
```

- `selfrun_full_final.log`：38 passed。
- `evidence/ratio_options_nano_banana_2_lite.png`：默认模型对应比例弹层证据。
- `evidence/effect_slim_card.png`：`Slim` 卡片存在证据。

## 失败归因与边界

- 本轮未发现产品缺陷；5 条原失败均归因为脚本 selector / expected 漂移。
- `L2-004` 只覆盖当前默认模型对应的比例集合，不假设不同模型共享同一组比例。
- 未修改上传素材、账号态、截图逻辑或无关断言。