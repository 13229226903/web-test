# 移动端统计第 11 条复核：画质增强结果弹窗下载

日期：2026-09-20  
驱动：Playwright MCP only  
设备：iPhone 13 / 390x664 / DPR 3 / pointer coarse=true / hover none=true

## 复核路径

1. 清除旧登录 session，使用可正常提交任务的登录态账号；会员非必要条件（用户补充口径）。
2. 从移动端首页 `Start Creating for Free` 上传 `test_images/1K.jpg`。
3. 进入 `/create/edit?pid=*` 移动画布。
4. 点击 `Photo Enhancer`，打开画质增强功能弹窗。
5. 选择 `Enhance`，提交画质增强任务。
6. 等待结果生成，功能弹窗底部出现下载按钮，图标为 `pmd_remodver_bg_btn_icon_download.svg`。
7. 点击结果弹窗底部下载按钮。

## 实际事件

- `移动端结果弹窗确认下载`
- `移动端画布页_画质增强ultra弹窗下载`
- `下载成功`
- 下载文件：`Pokecut_1789890738046.jpg`

## 频率断言

- 目标 `sendGaEvent 移动端画布页_画质增强ultra弹窗下载` = 1
- 目标 `debug 统计：移动端画布页_画质增强ultra弹窗下载` = 1

结论：第 11 条由 gap 修正为 covered，`xx=画质增强ultra`。用户补充：无需复核会员账号，只需能正常提交任务即可触发该统计。

## 证据

- `evidence/mobile_stat11_enhance_popup_download_baseline.log`
- `evidence/mobile_stat11_enhance_popup_download_after_full_debug.log`
- `shots/mobile_stat11_enhance_popup_download_success.png`

