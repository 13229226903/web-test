# PC 端第 1 批（前 10 条）执行结果（2026-09-21）

命令：`python -m pytest tests/test_canvas_stats_all.py::test_p_inf_01 ... ::test_p_new_07 -q`

结果：4 passed / 5 failed / 1 xfailed / 共 10 条，耗时 39:00。

| # | 用例 | 标题 | 结果 | 结论/原因 |
|---|---|---|---|---|
| 1 | P-INF-01 | PC 无限画布增强点数用完触发注册与注册成功 | xfailed（预期） | 已知埋点缺陷：功能级注册/注册成功事件缺失；严格 xfail 符合预期 |
| 2 | P-INF-02 | PC 无限画布点数用完触发购买成功 | passed | `无限画布页点数用完触发购买年ultra成功` send=1/debug=1 |
| 3 | P-INF-03 | PC 无限画布结果图下载保存 | failed | 下载的是/作用于原图，只出现 `无限画布页单图下载`、`下载成功`；未出现目标结果图事件，自动化执行路径问题 |
| 4 | P-NEW-01 | PC 新画布增强购买出现与成功 | failed | 未出现购买弹窗，未到统计断言；疑似 Enhance 按钮选择/提交流程未命中正确的生成提交，自动化问题 |
| 5 | P-NEW-02 | PC 新画布抠图购买出现与成功 | failed | 购买出现事件已出现；但弹窗默认落到 `SE + 3-Day Free`，按钮为 `Try Free Trial`，自动化未固定 Yearly Ultra 且未适配试用按钮，导致成功事件未触发 |
| 6 | P-NEW-03 | PC 新画布消除购买出现与成功 | passed | 购买出现+成功事件均 send=1/debug=1 |
| 7 | P-NEW-04 | PC 新画布改图购买出现与成功 | failed | 未出现购买弹窗，未到统计断言；AI Replace 的绘制/提示词/生成动作未真正提交，自动化问题 |
| 8 | P-NEW-05 | PC 新画布扩图购买出现与成功 | failed | 未出现购买弹窗，未到统计断言；扩图生成提交未命中，自动化问题 |
| 9 | P-NEW-06 | PC 新画布脸部购买出现与成功 | passed | 购买出现+成功事件均 send=1/debug=1 |
| 10 | P-NEW-07 | PC 新画布身材购买出现与成功 | passed | 购买出现+成功事件均 send=1/debug=1 |

## 失败证据

- `data/screenshots/pc_inf_03_result_download.png`：画布仍显示增强面板和原图选中态，说明下载动作未定位结果图。
- `data/screenshots/pc_new_02_remove_bg.png`：购买弹窗。
- `data/screenshots/pc_new_02_remove_bg_after_debug.png`：弹窗显示 `SE` 与 `3-Day Free`，按钮为 `Try Free Trial`。
- Allure：`reports/allure-results/` 中对应 result/attachment。

## 当前结论

- 本批 4 条统计用例通过，1 条按预期 xfail。
- 5 条失败均为自动化路径/按钮与套餐选择问题，尚未证明为新增真实埋点缺陷。
- 未继续执行第 2 批；按规则停下来等待用户确认。
