# 移动端首页漂移修复报告

- 任务: `2026-09-21_mobile_home_drift_fix`
- 环境: `http://10.17.1.66:3001/`，390x844 移动端
- 执行对象: `archive/mobile_home/test_mobile_home.py`
- 结果: **38 passed / 0 failed / 0 skipped**，耗时 460.92s
- Allure: `reports/allure-report-mobile-home-drift-final/` → `http://localhost:8123/index.html`

## 修复项

1. 默认模型入口：`Auto` → `Nano Banana 2 Lite`，同步修复 L1-002、L2-003、L2-020 Generate。
2. AI Templates `Slim` 卡片：`img[alt='Slim']` → `div[role='button'][aria-label='Slim']`，恢复 L2-010 上传进画布链路。
3. 比例列表：按“不同模型不同比例”处理；当前默认模型 `Nano Banana 2 Lite` 实际 8 项为 `1:1 / 3:4 / 4:5 / 4:3 / 9:16 / 16:9 / 2:3 / 3:2`，不再保留失效的 `9:21` 预期。

## 产物

- `artifacts/2026-09-21_mobile_home_drift_fix/sync.md`
- `artifacts/2026-09-21_mobile_home_drift_fix/impl.md`
- `artifacts/2026-09-21_mobile_home_drift_fix/review.md`
- `page_map/pokecut/mobile_home_v3.yaml`
- `artifacts/2026-09-21_mobile_home_drift_fix/selfrun_full_final.log`
- `artifacts/regression_registry.md` 已更新 Last Passed 与 page_map 版本。