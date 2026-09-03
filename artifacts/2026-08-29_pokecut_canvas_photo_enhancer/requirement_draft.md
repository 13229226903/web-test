---
task_id: 2026-08-29_pokecut_canvas_photo_enhancer
agent: test-case-design
phase: requirement_draft
status: completed
inputs:
  - D:\Test\web-test\飞书文档_ 文字画质增强实验优化(安国)-AI分析后的CheckBox.md
outputs:
  case_count: 29
  priority_breakdown: {P0: 6, P1: 21, P2: 2}
next_agent: page-map-sync
created_at: 2026-08-29 22:15:00 +08:00
---

# requirement_draft — 文字画质增强实验优化（Canvas 入口）

> 说明：PRD 标题与正文主要描述「Text 页（/tools/ai-image-text-enhancer）改为页内处理」；用户指定探索入口为 /create → Trending Tools → Start from a Photo → 上传 → 无限画布 → 选中图片 → Enhance。本 draft 以 PRD 为正确答案，先把 AC 拆成测试点；页面入口差异作为待验证项在 page-map-sync 阶段记录到 requirement_actual_diffs。

## 需求理解（PRD 追溯）
- PRD 文件名：飞书文档_ 文字画质增强实验优化(安国)-AI分析后的CheckBox.md
- PRD 版本未单独提供；以 2026-08-29 提供的 CheckBox 文件为准。
- 核心范围：文字画质增强（Enhance Text）从跳转工具页改为当前页内处理区；四种效果（Enhance Text / Remove Glare / Remove Moire / Document Scanner）支持多选；点数按模式与分辨率实时计算；免费试用 4 次按 IP；结果区 before/after 与角标；移动端横向结构；付费拦截承接。

## AC 映射与测试点初稿

| AC ID | 需求 AC | 预计状态 | 测试点 |
|---|---|---|---|
| AC-01 | SEO/上传后在当前页内进入处理区，不跳转；承接 HD 实验页结构；入口仅 Enhance Text/Remove Glare/Remove Moire/Document Scanner | 待提测 | 进入目标处理区，页面不跳转；四种效果入口可见 |
| AC-02 | 效果区 Choose the Effect + Supports multiple selections；分辨率区 Upscale to；Enhance Text 默认勾选，其他默认不勾选；无裸 key/旧文案 | 待提测 | 默认态文案与勾选 |
| AC-03 | 非 Enhance Text 单选时隐藏 2k/4k/8k；未选任何模式时按钮置灰不可触发 | 待提测 | 组合勾选状态与按钮禁用态 |
| AC-04 | 四效果问号 tooltip 文案 + Remove Glare/Moire/Document Scanner 视频资源命名 | 待提测 | 四 tooltip 文案与资源名（视频资源需 DOM/网络证据） |
| AC-05 | Enhance Text 2k/4k/8k 分别走 pkweb_textenhance_251118 / pkweb_comfyui_enhance_text_260625 / pkweb_chain_comfyui_enhance_text | 待提测 | 发起处理，抓任务请求/工作流 ID |
| AC-06 | 上传后自动选中下一档可用分辨率；已达到档位置灰且只能选更高；≥2K 提示 over 2K | 待提测 | 分辨率自动预选与置灰规则 |
| AC-07 | Remove Glare 加入 pkweb_comfyui_remove_reflection_glass，消耗 2 credits | 待提测 | 勾选后请求链路与点数 |
| AC-08 | Remove Moire 加入 pkweb_comfyui_remove_moire，消耗 2 credits | 待提测 | 勾选后请求链路与点数 |
| AC-09 | Document Scanner 用图生图参数：model nano banana pro、ratio none、文档扫描 prompt；保留文字/数字/公式/标注/表格版式并校正透视；消耗 4 credits | 待提测 | 勾选后请求参数与结果视觉 |
| AC-10 | 多效果按 文本扫描 → 去反光 → 去摩尔纹 → 文字增强 顺序执行 | 待提测 | 四选全部，抓请求/任务顺序 |
| AC-11 | 主按钮右侧实时展示组合总点数，随勾选/分辨率切换刷新 | 待提测 | 组合点数计算与刷新 |
| AC-12 | Enhance Text 点数按分辨率与用户身份计算：免费/SE/单项购买 2k=2、4k=2、8k=6；Pro/Ultra 2k/4k Free、8k=4（PRD 原文） | 待提测 | 不同账号态点数规则 |
| AC-13 | 组合模式总点数按实际消耗累加并扣除 | 待提测 | 组合扣点总价 |
| AC-14 | 处理后展示 before/after；非 Enhance Text 结果不展示分辨率信息 | 待提测 | 结果态对比与分辨率信息有无 |
| AC-15 | 结果态默认勾选与按钮文案复用 HD 结果态 | 待提测 | 结果态默认选中与按钮文案 |
| AC-16 | 再次选择已处理过的非增强模式时先提示（this image has been processed these effect），当次不选中；第二次点击可选中 | 待提测 | 二次选择提示交互 |
| AC-17 | 缩略图右下角角标优先级：含 Enhance Text 显示文字增强角标+分辨率；单选非增强仅对应角标；多选非增强按 去反光→去摩尔纹→文本扫描 顺序 | 待提测 | 结果缩略图角标 |
| AC-18 | 当前图达 8K 时 Enhance Text 与分辨率整体置灰；提示 The image is already at the highest clarity. | 待提测 | 8K highest clarity 置灰态 |
| AC-19 | 8K 图执行非增强模式后追加 pkweb_chain_comfyui_enhance_text，最终为二次增强结果 | 待提测 | 8K 非增强工作流追加 |
| AC-20 | Text 页首页首屏切换为画质实验样式并使用运营配置内容 | 待提测 | 首屏样式与运营内容 |
| AC-21 | 首屏对比图片取消 1.8.3 放大效果 | 待提测 | 对比图视觉 |
| AC-22 | 移动端四种模式横向展示且支持多选，Enhance Text 默认选中 | 待提测 | 移动端模式区 |
| AC-23 | 移动端分辨率滑杆展示与置灰规则同 PC | 待提测 | 移动端分辨率区 |
| AC-24 | 移动端结果态按钮：主按钮 Continue Enhancing，Edit More/Download 并排；下载拦截复用既有购买链路 | 待提测 | 移动端结果态 |
| AC-25 | 所有用户在 Text 页共有 4 次免费模式机会并按 IP 刷新；未登录/登录均按 IP 计数 | 待提测 | 免费额度态 |
| AC-26 | 剩余免费次数不足时按 文本扫描→去反光→去摩尔纹→文字增强 顺序计算需扣 credits 模式 | 待提测 | 免费次数抵扣顺序 |
| AC-27 | B 方案点数不足触发 Text 专门购买拦截，商品配置按 2.8 规则 | 待提测 | B 方案购买拦截 |
| AC-28 | 非 B 方案点数不足沿用既有付费拦截 | 待提测 | 非 B 方案拦截 |
| AC-29 | （补充）Canvas 工具栏 Enhance 入口可打开处理面板，且功能入口符合用户描述的选中图片后出现 | 待提测 | 入口可见性与状态 |

## 预计状态与待提测清单
- 页面可访问性、四种效果选择、分辨率区、点数计算、tooltip、默认勾选：可直接探索。
- 生成工作流/请求链路/免费次数/购买拦截：需要登录、DEBUG 切预部署、真实生成或配额口径。
- 移动端、真 8K highest clarity、B 方案专属拦截、运营首屏：需专用账号/设备或后端日志口径。

## 风险与授权请求
- 真实生成会消耗 credits/免费次数，探索时优先测试服、失败再预部署，并记录环境状态变化。
- 不执行删除/清空/注销/不可逆提交；购买拦截只观察到弹窗，不真实下单。
