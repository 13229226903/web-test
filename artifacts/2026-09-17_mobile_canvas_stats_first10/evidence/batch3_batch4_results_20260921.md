# 第 3 / 第 4 批执行结果（2026-09-21）

## 第 3 批：M-CORE-02 ~ M-NEW-04

用户指示：不整批复跑，三条失败项已单独修复并通过。

| 用例 | 标题 | 结果 | 说明 |
|---|---|---|---|
| M-CORE-02 | 移动端 xx 功能点数用完触发注册与注册成功 | ✅ passed | 改为两个独立匿名会话（画质增强 / AI扩图 各注册一次），功能级注册成功事件才与打开弹窗的功能一致 |
| M-CORE-03 | 移动端点数用完触发购买与 xx 功能购买 | ✅ passed | 关闭购买弹窗后回 Trending Tools 再开 AI Image Extender |
| M-CORE-04 | 移动端 xx 功能与通用购买成功 | ✅ passed | |
| M-CORE-05 | 移动端画布页 xx 弹窗出现 | ✅ passed | |
| M-CORE-06 | 移动端画布页 xx 弹窗确认 | ✅ passed | |
| M-CORE-07 | 移动端画布页画质增强结果弹窗下载 | ✅ passed | 点面板主提交按钮生成结果；移开 DEBUG 浮层（position:fixed）避免遮挡底部下载按钮 |
| M-NEW-01 | 移动端新画布增强购买出现与成功 | ✅ passed | 随机新账号恢复“月SE试用”购买项 |
| M-NEW-02 | 移动端新画布抠图购买出现与成功 | ✅ passed | |
| M-NEW-03 | 移动端新画布消除购买出现与成功 | ✅ passed | AI Delete -> 在图片上涂抹蒙版（CDP Input.dispatchTouchEvent）-> Remove 提交 |
| M-NEW-04 | 移动端新画布改图购买出现与成功 | ⚠️ xfailed（预期） | 已知埋点缺陷：实际 `画布页改图...`，缺 `新画布` 前缀 |

## 第 4 批：M-NEW-05 ~ M-NEW-14（最终整批）

结果：**9 passed / 1 skipped / 0 failed**，耗时 9:42。

| 用例 | 标题 | 结果 |
|---|---|---|
| M-NEW-05 | 移动端新画布扩图购买出现与成功 | ✅ passed |
| M-NEW-06 | 移动端新画布脸部购买出现与成功 | ✅ passed |
| M-NEW-07 | 移动端新画布身材购买出现与成功 | ✅ passed |
| M-NEW-08 | 移动端新画布发型购买出现与成功 | ✅ passed |
| M-NEW-09 | 移动端新画布 AI滤镜购买出现与成功 | ⚠️ skipped（URL 未提供） |
| M-NEW-10 | 移动端新画布图生图购买出现与成功 | ✅ passed |
| M-NEW-11 | 移动端新画布文生图购买出现与成功 | ✅ passed |
| M-NEW-12 | 移动端新画布背景模糊购买出现与成功 | ✅ passed |
| M-NEW-13 | 移动端新画布照片修复购买出现与成功 | ✅ passed |
| M-NEW-14 | 移动端新画布换背购买出现与成功 | ✅ passed |

## 本轮关键修复

1. 移动端 SEO 画布进入后功能面板已自动打开，需点面板主提交按钮：
   - `button.mobile-ai-generate-button`（画质增强/通用生成）
   - `button.mobile-ai-expand-generate-button`（AI扩图）
2. 促销弹窗与内购弹窗语言无关识别：促销弹窗无 `li.purchase-pro-plan__card`，内购弹窗有。
3. Debug 面板关闭按钮：`button.close-btn`（移动端与 PC 通用）。
4. DEBUG 浮层为 `position: static`，需设 `position: fixed` 才能移开，避免遮挡结果弹窗底部下载按钮。
5. M-NEW-03 蒙版涂抹：仅鼠标/合成 PointerEvent 无效，必须用 CDP `Input.dispatchTouchEvent`。
