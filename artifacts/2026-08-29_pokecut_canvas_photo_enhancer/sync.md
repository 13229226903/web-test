---
task_id: 2026-08-29_pokecut_canvas_photo_enhancer
agent: page-map-sync
status: pending_review
repair_scope: full_exploration
gate_exemption: false
inputs:
  - D:\Test\web-test\飞书文档_ 文字画质增强实验优化(安国)-AI分析后的CheckBox.md
  - D:\Test\web-test\artifacts\2026-08-29_pokecut_canvas_photo_enhancer\requirement_draft.md
  - D:\Test\web-test\page_map\pokecut\create_ai_tools.yaml
  - D:\Test\web-test\page_map\pokecut\infinite_canvas.yaml
outputs:
  scanned_pages: [/create, /agent?pid=<uuid>]
  page_map_versions: [infinite_canvas_enhance_v1]
  coverage_gates:
    create_trending_tools_start_from_photo: covered
    canvas_upload_and_toolbar: covered
    canvas_enhance_panel: covered
    prd_text_enhancer_four_effects: gap
    prd_resolution_2k_4k_8k: gap
    prd_cost_and_free_quota: gap
    prd_result_compare_and_badges: gap
    prd_mobile: gap
    prd_paywall: gap
  state_button_coverage: covered
  requirement_actual_diffs: 29
  bug_candidates: 1
  skipped:
    - Enhance 面板主按钮未点击：点击会触发真实生成并消耗 credits/免费次数，未授权，不执行
    - 登录/付费/生成/免费额度/账号态未验证：目标入口下未出现对应功能，且真实生成有配额/账号影响
  special_dependencies: [test_images/文字测例.jpg, PC 1920x1080 en-US, 测试服 http://10.17.1.66:3001]
  specs_updated: false
next_agent: test-case-design
created_at: 2026-08-29 22:40:00 +08:00
---

# sync.md — 无限画布 Enhance 面板（用户指定 /create → Start from a Photo）

## 1. 探索摘要
- /create 可访问，Trending Tools 下第一个按钮 Start from a Photo 可点击并触发文件选择器。
- 上传 	est_images/文字测例.jpg 后进入 http://10.17.1.66:3001/agent?pid=<uuid>，页面顶部工具栏出现 Enhance。
- 点击顶部 Enhance 后打开右侧 AI Enhancer 面板，包含 5 个互斥模式：Standard Mode、Old Photo Mode、Portrait Mode、Text Mode、Ultra HD Mode。
- 该面板内**未出现** PRD 要求的 Choose the Effect、*Supports multiple selections、Upscale to、Enhance Text / Remove Glare / Remove Moire / Document Scanner、2k / 4k / 8k 分辨率区、点数/credits 展示。
- 页面实际是画布内 AI 图片增强（模式 + 固定放大尺寸），与 PRD「Text 页改为页内处理」的文字画质增强四效果实验不是同一套 UI/状态。

## 2. 页面覆盖矩阵
| 状态 | 覆盖 | 证据 |
|---|---|---|
| /create Trending Tools 入口 | covered | explore_canvas_enhance_v1.json step 01 |
| 上传后进入 /agent 画布 | covered | 同上 |
| 顶部工具栏 Enhance 入口 | covered | 同上 |
| AI Enhancer 面板默认态 | covered | step 02/03 |
| 五种模式选择与输出尺寸 | covered | step 04 |
| 各模式 tooltip | covered | explore_enhance_tooltips_v2.json |
| PRD 四效果/分辨率/点数/结果态 | gap | 页面 body 与 DOM 均无相关文案 |

## 3. 需求差异（requirement_actual_diffs）
> 判定口径：以用户指定入口 /create → Start from a Photo → Enhance 为验证对象，PRD 为正确答案。

| AC ID | 差异类型 | 说明 |
|---|---|---|
| AC-01 | gap | 未进入 Text 页内处理区；实际进入 /agent 画布，无 Enhance Text/Remove Glare/Remove Moire/Document Scanner 四入口 |
| AC-02 | gap | 无 Choose the Effect、Supports multiple selections、Upscale to；默认态是 Standard Mode，不是 Enhance Text |
| AC-03 | gap | 无多效果勾选/分辨率区；模式为互斥单选，没有“未选任何模式置灰”状态 |
| AC-04 | gap | 无四效果问号 tooltip；实际 tooltip 为 Standard/Old Photo/Portrait/Text/Ultra HD 五个模式说明 |
| AC-05 | gap | 无 Enhance Text 2k/4k/8k 提交入口与对应请求，无法命中 pkweb_textenhance_251118 等链路 |
| AC-06 | gap | 无 2k/4k/8k 自动选下一档/低档置灰/over 2K 提示；实际展示固定输入→输出尺寸 |
| AC-07 | gap | 无 Remove Glare 入口及去反光链路 |
| AC-08 | gap | 无 Remove Moire 入口及去摩尔纹链路 |
| AC-09 | gap | 无 Document Scanner 入口及图生图扫描参数 |
| AC-10 | gap | 无四效果多选与执行顺序 UI/请求 |
| AC-11 | gap | 主按钮右侧无组合总点数展示 |
| AC-12 | gap | 无按分辨率/账号态展示 Enhance Text 点数 |
| AC-13 | gap | 无组合扣点总价展示 |
| AC-14 | gap | 未进入对应结果态，无法验证 before/after 与“非 Enhance Text 结果不展示分辨率” |
| AC-15 | gap | 无 HD 结果态默认勾选/按钮文案可对照 |
| AC-16 | gap | 无“已处理过的非增强模式”重复选择提示 |
| AC-17 | gap | 无结果缩略图角标优先级状态 |
| AC-18 | gap | 无 8K highest clarity 置灰态 |
| AC-19 | gap | 无 8K 非增强追加工作流入口 |
| AC-20 | gap | 用户指定入口未覆盖 Text 页首页首屏；需在 /tools/ai-image-text-enhancer 验证 |
| AC-21 | gap | 同 AC-20，指定入口未覆盖 |
| AC-22 | gap | 未验证移动端；且指定入口下无四模式多选结构 |
| AC-23 | gap | 未验证移动端；且指定入口下无 2k/4k/8k 滑杆 |
| AC-24 | gap | 未进入对应结果态 |
| AC-25 | gap | 指定入口下无四模式使用/免费次数 UI |
| AC-26 | gap | 无免费次数抵扣状态可验证 |
| AC-27 | gap | 无 Text 专门购买拦截入口 |
| AC-28 | gap | 无对应付费拦截入口 |
| AC-29 | covered | /create → Start from a Photo → 上传 → 画布 → 选中图片后顶部工具栏出现 Enhance 这一导航链路可走通 |

## 4. bug_candidates
| ID | 严重度 | 说明 | recommended_action |
|---|---|---|---|
| BUG-CAND-001 | P0/阻塞 | 用户指定入口的 Enhance 面板与 PRD 不符：实际为画布 AI Enhancer（Standard/Old Photo/Portrait/Text/Ultra HD + 固定输出尺寸），缺少 PRD 的 Text 页内四效果处理区。按用户“结合测例探索是否符合需求”的口径，该入口未实现需求功能；若入口应指向 /tools/ai-image-text-enhancer，则属于入口/路由错误 | blocked / file_bug，需用户确认正确入口或确认该入口为未实现 |

## 5. 关键发现与下游注意事项
- 已有 page_map i_image_text_enhancer_v3.yaml 证明 PRD 四效果功能在 /tools/ai-image-text-enhancer 可访问；本次指定入口 /create → Start from a Photo → Enhance 进入的是另一套功能。
- 不建议在当前 gap 未解决前进入 test-case-design(final) 或 test-writing。
- 如用户确认入口应改为 /tools/ai-image-text-enhancer，则可复用已有 v3 资产做回归；如确认入口就是画布 Enhance，则需要重新提供与该画布 Enhance 对应的 PRD/AC，当前文档不匹配。

## 6. 版本差异摘要
- 新增 page_map/pokecut/infinite_canvas_enhance_v1.yaml；未改动历史 page_map。

> 本 sync 处于 pending_review，需用户确认入口/需求匹配关系后才能继续。
