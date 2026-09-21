# PC 端第 2 批（P-NEW-08 ~ P-NEW-16 + M-CORE-01）执行结果（2026-09-21）

命令：`python -m pytest tests/test_canvas_stats_all.py::test_p_new_08 ... ::test_m_core_01 -q`

结果：9 passed / 1 skipped / 0 failed，耗时 10:43。

| # | 用例 | 标题 | 结果 | 说明 |
|---|---|---|---|---|
| 11 | P-NEW-08 | PC 新画布发型购买出现与成功 | ✅ passed | 发型购买出现+成功事件 send=1/debug=1 |
| 12 | P-NEW-09 | PC 新画布 AI滤镜购买出现与成功 | ⚠️ skipped | AI滤镜 SEO URL 未提供，依赖缺口 |
| 13 | P-NEW-10 | PC 新画布图生图购买出现与成功 | ✅ passed | 首屏上传图标 + Generate 图标进入画布，事件成对 |
| 14 | P-NEW-11 | PC 新画布文生图购买出现与成功 | ✅ passed | 首屏 Generate 图标进入画布，事件成对 |
| 15 | P-NEW-12 | PC 新画布 AI背景购买出现与成功 | ✅ passed | 事件成对 |
| 16 | P-NEW-13 | PC 新画布背景模糊购买出现与成功 | ✅ passed | 事件成对 |
| 17 | P-NEW-14 | PC 新画布照片修复购买出现与成功 | ✅ passed | 先选 Old Photo Enhance，再提交，事件成对 |
| 18 | P-NEW-15 | PC 新画布贴纸购买出现与成功 | ✅ passed | Layer 面板 + Ctrl+A 全选图层后点 Download，事件成对 |
| 19 | P-NEW-16 | PC 新画布换背购买出现与成功 | ✅ passed | 事件成对 |
| 20 | M-CORE-01 | 移动端画布点数用完触发注册与注册成功 | ✅ passed | 随机新邮箱注册，注册成功事件成对 |

## 本轮修复点

- 无文案 SEO 首屏上传/Generate 图标：`create_generate_icon_upload_image.svg` / `create_generate_icon_go.svg`。
- 本地化内购弹窗结构判定：`li.purchase-pro-plan__card`。
- 本地化 checkout 结构化按钮：`button.purchase-pro-plan__button`。
- AI Replace 蒙版绘制后再提交。
- Photo Restoration 先选 `Old Photo Enhance`。
- 贴纸：点击 VIP 贴纸按钮 → Layer 面板 → Ctrl+A 全选 → Download。
- 移动注册：弹窗已打开时不重复点顶部 Sign up；等待 Vue 状态后点 `auth-submit`。

## 证据

- Allure：`reports/allure-results/`
- 截图：`data/screenshots/pc_new_*.png`
- 前一批结果：`artifacts/2026-09-17_mobile_canvas_stats_first10/evidence/pc_batch1_first10_results_20260921.md`
