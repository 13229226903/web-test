---
task_id: 2026-08-30_pokecut_canvas_text_layer
agent: test-case-design
phase: final_after_sync
status: confirmed
inputs:
  sync: artifacts/2026-08-30_pokecut_canvas_text_layer/sync.md (confirmed)
  page_map: page_map/pokecut/infinite_canvas_text_layer_v2.yaml
  requirement_doc: null (存量功能首次探索，以实际页面为准)
outputs:
  case_count: 6
  priority_breakdown:
    P0: 6
    P1: 0
    P2: 0
next_agent: test-writing
created_at: 2026-08-30 16:00:00 +08:00
updated_at: 2026-08-30 18:00:00 +08:00
---

# 用例矩阵 — 画布页文字功能（优化去重后）

## 需求理解
- 存量功能首次探索，无独立 PRD；以 `sync.md` 第 8 节确认的实际交互为准。
- 入口：`/create` → Trending Tools 第一个按钮 `Start from a Photo` → 文件弹窗选 `test_images/低分辨率.JPG` → `/agent?pid=<uuid>`。
- 核心链路：Add Text 添加并选中文字 → 工具栏 + 属性面板出现 → 覆盖 Basic/Adjust 全部关键控件与文字实际效果。
- 优化说明：将重复的上传/进入路径合并为 6 条主用例，每条内覆盖多个强相关交互，保留真实断言与截图。

## 用例矩阵

| case_id | Layer | 策略 | 标题 | 进入方式 | 操作 | 等待 | 断言 | 截图点 | AI 审查 | page_ref |
|---|---|---|---|---|---|---|---|---|---|---|
| TC-TEXT-001 | L6 | smoke | 入口上传 + 左侧工具栏 + Add Text | /create | 点 Start from a Photo 上传低分辨率.JPG；检查 7 个左侧工具；点 Add Text | URL 变 /agent；文字层出现 | URL 含 /agent?pid=；7 个 data-tool-id 均存在；工具栏 9 按钮文案出现 | 上传后/Add Text 后 | 否 | elements.entry / elements.tool_text |
| TC-TEXT-002 | L2 | default_full | 选中/空白收起/Adjust 重开 + Tab/Alignment/Font/Fill | 画布页 | 点空白收起；点 Adjust 重开；切 Basic/Adjust；点 Alignment；查 Font/Fill | 面板/工具栏状态变化 | 空白后 Basic/工具栏消失；Adjust 重开面板；Basic 切激活；Font/Fill 可见 | 收起/重开/Basic 各 1 张 | 否 | states.text_layer_selected.buttons.adjust / states.adjust_panel_open |
| TC-TEXT-003 | L5 | default_full | Space 单行禁用 + 两行 Height 生效 | 画布页 | 单行展开 Space；双击文字层填 line1\nline2；再展开 Space 并设 Height=50 | 两行提交后 Height 启用 | 单行 Height disabled=true；两行 Height disabled=false；尺寸文本前后变化 | 单行/两行/调整后各 1 张 | 否 | elements.text_prop_adjust_space / elements.text_edit_hidden_textarea |
| TC-TEXT-004 | L5 | default_full | Reflection 四参数可调 + 实际反射效果 | 画布页 | 展开 Reflection；Toggle 开启；设 Scope=20/Opacity=20/Distance=20/Angle=45 | 参数更新与视觉变化 | 4 slider 可见；Toggle 开 class；四参数值；像素 diff nonzero>10000 | 展开/开关/调参/效果各 1 张 | 是：文字下方出现反射 | elements.text_prop_adjust_reflection / elements.text_prop_adjust_reflection_toggle |
| TC-TEXT-005 | L2 | default_full | Background 无填充/色盘弹窗/取色应用 | 画布页 | 展开 Background；点色盘弹窗，hex 填 #ff0000；Escape；点取色，点画布有色区 | 弹窗出现/应用 | 色盘 img 存在；hexInput 可见且值 #ff0000；取色后背景视觉变化截图 | 展开/色盘弹窗/应用红色/取色应用各 1 张 | 是：文字背景色变化 | elements.background_color_palette_btn / elements.background_picker_btn |
| TC-TEXT-006 | L2 | default_full | Outline Types/色盘/取色/四滑块/描边效果 | 画布页 | 展开 Outline；Toggle 开启；点 Types 第 2 个；色盘弹窗/Escape；取色点画布；设 Size=70/Distance=20/Blur=10/Smooth=30 | 状态与视觉变化 | Toggle 开；Types 选中；色盘 hexInput 可见；四滑块值；像素 diff nonzero>10000 | 展开/开关/Types/色盘/取色/滑块/效果各 1 张 | 是：文字出现描边 | elements.text_prop_adjust_outline / elements.outline_color_palette_btn / elements.outline_picker_btn |

## 依赖缺口与风险
- 像素 diff 断言依赖 PIL/截图；阈值 `nonzero_pixels > 10000`，保留截图人工复核。
- 上传仅允许 `test_images/` 现有文件；无需登录，不涉及 credits/订阅/不可逆数据。
