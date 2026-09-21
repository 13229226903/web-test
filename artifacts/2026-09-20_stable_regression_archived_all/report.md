# 归档回归报告

- 任务: `2026-09-20_stable_regression_archived_all`
- 目标环境: `http://10.17.1.66:3001/`
- 执行对象: `artifacts/regression_registry.md` 中 URL 登记为本环境且状态为 `stable_regression` 的 `Archive` 列归档副本，共 11 个 suite / 192 条用例
- 收集检查: 192 collected，0 error
- 命令日志: `artifacts/2026-09-20_stable_regression_archived_all/regression/`
- 汇总: `artifacts/2026-09-20_stable_regression_archived_all/regression/summary.json`
- Allure 原始结果: `reports/allure-results-archive/`
- Allure 报告: `reports/allure-report-archive/` → `http://localhost:8123/index.html`

## 简易回归报告

【回归测试报告】2026-09-20 19:22

✅ 人像检测三入口页（Ethnicity / Body Shape / Face Comparison）  14/14 · 5m12s
⚠️ 文字画质增强实验页（AI Image Text Enhancer）  15/18 · 13m07s  (3 skipped)
✅ 画布页文字功能  6/6 · 4m56s
❌ Pokecut 移动端首页优化（Mobile Home v3）  33/38 · 8m04s
   └ L1-002 hero 文案控件 — 默认模型入口未找到 `Auto` 按钮
   └ L2-003 模型入口展开模型列表 — 默认模型入口已不是 `Auto`，定位超时
   └ L2-004 比例入口展开比例列表 — 比例列表缺少 `9:21`
   └ L2-010 effect 模板卡上传进入画布 — `img[alt='Slim']` 模板卡不可见/不存在
   └ L2-020 底部导航 Generate — 生图面板实际默认模型为 `Nano Banana 2 Lite`，期望 `Auto`
✅ 帮助中心（/help）  11/11 · 3m09s
✅ 旧画布 Insert 面板与图层属性（legacy canvas）  24/24 · 9m30s
✅ 旧画布文字功能（Text 面板 + 文字图层参数）  13/13 · 6m27s
✅ 旧画布贴纸调参面板（legacy canvas，一个贴纸）  9/9 · 3m26s
✅ SEO 页面主上传按钮交互（24 个唯一 SEO 页面）  24/24 · 8m02s
⚠️ SEO 页面主上传按钮交互（24 个唯一 SEO 页面）· 移动端  23/24 · 4m32s  (1 xfailed / Allure skipped)
✅ Create / Chat to Edit / Auto 意图识别（10 条 prompt）  11/11 · 7m25s

合计: 183 通过 / 5 失败 / 3 跳过 / 1 xfailed · 总耗时 73m51s
状态: ❌ 有失败

Allure 报告: http://localhost:8123/index.html

> Allure 将 5 条失败拆分为 3 failed + 2 broken，并将 1 条 xfailed 计入 skipped；Allure 统计为 183 passed / 3 failed / 2 broken / 4 skipped / 192 total。

## 结论

- 10/11 个归档 suite 达到通过或预期跳过状态。
- 唯一失败 suite 为移动端首页：默认模型 `Auto` 相关断言连续失败，实际观察到 `Nano Banana 2 Lite`；另有 `9:21` 比例和 `Slim` effect 模板卡两个存量断言不匹配。
- 本轮按稳定回归要求未修改脚本、断言或测试数据，未执行局部复探修复。