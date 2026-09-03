---
task_id: 2026-08-30_pokecut_canvas_text_layer
agent: page-map-sync
status: confirmed
repair_scope: full_exploration
gate_exemption: null
inputs:
  entry_url: http://10.17.1.66:3001/create
  entry_path: /create
  target: /create → Start from a Photo → 文件弹窗选图 → /agent 文字图层全流程
  assets:
    - test_images/低分辨率.JPG
  reference_page_map: page_map/pokecut/infinite_canvas_text_layer.yaml
outputs:
  scanned_pages:
    - /create
    - /agent?pid=<uuid>
  page_map_versions:
    - page_map/pokecut/infinite_canvas_text_layer_v2.yaml
  coverage_gates:
    - 入口与上传: covered
    - 添加文字图层与选中态: covered
    - 文字编辑工具栏 9 按钮: covered
    - 右侧属性面板 Basic/Adjust: covered
    - Adjust 4 个 section: covered
    - 点击空白画布收起面板: covered
  state_button_coverage: "9/9 工具栏按钮，2/2 顶层 Tab，4/4 Adjust section"
  requirement_actual_diffs:
    - diff_type: gap
      item: "Adjust 打开面板"
      expected: "选中图层后出现功能栏，点击 Adjust 后出现功能面板"
      actual: "点击 Add Text 后图层自动选中，功能栏和右侧属性面板同时自动出现（Adjust Tab 默认激活）；面板已打开时点击工具栏 Adjust 无可见变化"
      impact: "不影响功能，但交互路径与描述不完全一致；用户描述更像是面板关闭/收起后的重开路径"
      recommended_action: "按实际 UI 写用例：添加文字后面板默认打开；面板关闭但图层仍选中时，点击 Adjust 可重开"
    - diff_type: gap
      item: "点击画布空白处收起面板"
      expected: "点击画布空白处收起面板"
      actual: "点击画布空白处会取消选中文字图层，面板关闭且顶部功能栏一起消失；重新选中图层后恢复"
      impact: "行为符合收起面板目标，但会同时失去图层选中态"
      recommended_action: "用例断言面板与功能栏同时消失；重新选中图层后面板恢复"
  bug_candidates: []
  skipped:
    - item: "Basic → Font 字体下拉内容"
      reason: "headless 下点击/hover Font 按钮未展开字体列表，无法读取具体字体选项"
      evidence: "shots/60_font_open_full.png、61_font_mouse_open.png、62_font_hover.png"
      follow_up: "下游 test-writing 可用坐标点击/JS 注入并在有头模式复验字体列表"
  special_dependencies:
    - "Vue 自定义组件：点击使用 page.mouse.click 或 dispatchEvent；原生 locator.click 可能不生效"
    - "属性面板需滚动 .panel-scroll-y 才能稳定操作 Reflection/Outline"
    - "上传前可能需 JS 关闭 /create 定价遮罩"
  specs_updated: []
created_at: 2026-08-30 00:30:00 +08:00
---

# sync.md — 画布页文字功能全流程探索

## 1. 探索摘要

- 从 `http://10.17.1.66:3001/create` 进入，点击 Trending Tools 分类下第一个按钮 **Start from a Photo**，通过 `expect_file_chooser` 选择 `test_images/低分辨率.JPG`，成功进入 `/agent?pid=<uuid>`。
- 在左侧工具栏点击 `button[data-tool-id='text']`（Add Text）后，画布上新增文字图层并自动选中。
- 选中后顶部出现 9 按钮编辑工具栏（Adjust / Move Up / Move Down / To Top / To Bottom / Flip h / Flip v / Delete / Rotation），右侧出现属性面板（Basic / Adjust 顶层 Tab，默认 Adjust）。
- 已逐一点击工具栏 9 按钮并截图记录；已探索 Basic Tab（Alignment / Font / Fill）与 Adjust Tab 4 个 section（Space / Reflection / Background / Outline）的结构与控件。
- 点击画布空白处后，面板收起且工具栏同时消失（图层取消选中）。

## 2. 页面覆盖矩阵

| 页面/状态 | 覆盖状态 | 说明 |
|---|---|---|
| /create | covered | Trending Tools 第一个按钮可见，可触发文件选择 |
| /agent 上传后画布 | covered | URL 变为 /agent?pid=<uuid>，画布加载 |
| 添加文字图层后选中态 | covered | 工具栏 + 右侧属性面板出现 |
| 工具栏 9 按钮 | covered | 逐个点击并记录面板状态变化 |
| 点击空白画布收起面板 | covered | 面板与工具栏同时消失 |
| Basic Tab | covered | Alignment / Font / Fill 结构确认 |
| Adjust Tab | covered | Space / Reflection / Background / Outline 展开与控件确认 |

## 3. 需求-实际差异

| 需求点 | 实际页面 | 结论 |
|---|---|---|
| 选中图层后出现功能栏 | 符合：Add Text 后自动选中并出现功能栏 | covered |
| 点击 Adjust 后出现功能面板 | 差异：添加文字后属性面板已自动出现，Adjust Tab 默认激活；面板已打开时点 Adjust 无可见变化 | gap |
| 点击画布空白处收起面板 | 符合：面板收起；同时功能栏消失（取消选中） | gap（附带取消选中） |
| 对面板内每个功能进行探索 | 已探索 Basic/Adjust 全部主要控件 | covered |

## 4. 关键发现

1. **面板默认打开**：点击 Add Text 后属性面板立即出现，无需先点 Adjust；面板顶部 Tab 默认在 Adjust。
2. **面板关闭路径**：点击画布空白处会关闭面板并取消选中，工具栏消失；重新点击文字图层恢复。
3. **工具栏 Adjust 的重开作用**：存在“面板关闭但工具栏仍在”的中间态（如点击 Move Up 后），此时点击 Adjust 可重新打开面板。
4. **Adjust 面板结构**：
   - Space：Width 0~100（默认 0，可调），Height -100~100（默认 0，初始禁用）。
   - Reflection：Toggle 默认关闭；展开后有 Scope 100 / Opacity 50 / Distance 0 / Angle 180 四个滑块。
   - Background：无填充 + 25 色块。
   - Outline：Toggle 默认关闭；展开后有 Types、Color、Size 20、Distance 0、Blur 0、Smooth 0。
5. **Basic 面板结构**：
   - Alignment：3 个自定义图标按钮（左/中/右）。
   - Font：按钮存在，headless 下未展开列表，需后续有头/坐标复验。
   - Fill：颜色按钮，DOM 含 25 色块 + 透明选项。

## 5. 下游注意事项

- 脚本入口复用 `/create → Start from a Photo → expect_file_chooser`，上传素材只允许 `test_images/`。
- Vue 自定义组件用 `page.mouse.click` / `dispatchEvent`；不要依赖 `locator.click()`。
- 操作 Reflection/Outline 前先滚动 `.panel-scroll-y` 到可见位置，并按“先下拉箭头展开，再点 Toggle”的顺序。
- 点击空白画布会取消选中并关闭面板，若用例要连续操作面板，需重新选中文字图层。

## 6. 证据与产物

- 页面地图：`page_map/pokecut/infinite_canvas_text_layer_v2.yaml`
- 探索截图：`artifacts/2026-08-30_pokecut_canvas_text_layer/shots/`
  - `10_canvas_loaded.png`、`11_after_add_text.png`
  - `31_*.png`（工具栏逐个点击）
  - `50_*.png`、`51_*.png`、`52_*.png`、`53_*.png`（面板探索）
  - `57_background_expanded.png`、`58_outline_expanded.png`、`59_reflection_expanded.png`
- 结构化记录：`artifacts/2026-08-30_pokecut_canvas_text_layer/explore_toolbar_isolated.json`、`explore_panel.json`


## 7. Adjust 面板控件点击前后变化（补充探索）

### 7.1 顶层 Tab
| 控件 | 操作前 | 操作后 |
|---|---|---|
| Basic → Adjust Tab | Basic 激活（渐变蓝），Adjust 灰 | Adjust 激活（渐变蓝），Basic 灰 |
| Adjust → Basic Tab | Adjust 激活 | Basic 激活 |

### 7.2 Adjust Tab 四个 section
| 控件 | 操作前 | 操作后 |
|---|---|---|
| Space 折叠按钮 | 内容 display:none | 内容 display:block；展开 Width/Height |
| Space Width 滑块 | value=0（0~100，可调） | value=40（实时更新） |
| Space Height 滑块 | value=0（-100~100，disabled） | 仍 disabled，value=0 |
| Reflection 下拉箭头 | 内容 display:none | 内容 display:block |
| Reflection Toggle | g-[#DCDDE3]（关） | g-[#232323]（开） |
| Reflection 4 滑块 | [Scope 100, Opacity 50, Distance 0, Angle 180] | [60, 30, 20, 90] |
| Background 折叠按钮 | 内容 display:none | 内容 display:block；显示无填充+25 色块 |
| Background 无填充 | 默认选中（order-[#3338EE]） | 仍选中 |
| Background 红色块 | 未选中 | 点击后选中红色 
gb(174,41,42) |
| Outline 下拉箭头 | 内容 display:none | 内容 display:block |
| Outline Toggle | g-[#DCDDE3]（关） | g-[#232323]（开） |
| Outline Types | 类型 0 选中 | 点击类型 1 后类型 1 选中（order-[#3338EE]） |
| Outline 红色块 | 未选中 | 点击后红色块选中 |
| Outline 4 滑块 | [Size 20, Distance 0, Blur 0, Smooth 0] | [70, 20, 10, 30] |

### 7.3 Basic Tab
| 控件 | 操作前 | 操作后 |
|---|---|---|
| Alignment 左/中/右 | 中（index 1）选中 | 点击左（index 0）或右（index 2）后对应按钮选中（g-[#3338EE]） |
| Font | Font 按钮可见，Fill 未露出 | 点击后 Fill 露出；字体列表未在 headless 下展开 |
| Fill | Fill 按钮可见 | 点击无文本变化；颜色网格 DOM 中存在（25 色块+透明） |

> 注意：交互后属性面板 x 坐标会从约 1132 偏移到 1043，后续脚本定位面板内元素时 x 阈值不要写死为 >=1080，建议 >=1000。

### 7.4 证据
- rtifacts/2026-08-30_pokecut_canvas_text_layer/adjust_panel_interactions.json
- rtifacts/2026-08-30_pokecut_canvas_text_layer/background_interactions.json
- rtifacts/2026-08-30_pokecut_canvas_text_layer/outline_interactions.json
- rtifacts/2026-08-30_pokecut_canvas_text_layer/basic_interactions.json
- 截图：shots/70_*.png ~ shots/115_*.png


## 8. 实际效果与补充交互（两行文字 / Reflection 效果 / 色盘 / 取色）

### 8.1 两行文字与 Space Height
- 添加文字后默认文字层内容为 Text；双击文字层出现隐藏编辑框 	extarea.fixed.h-px.w-px，填入 line1\nline2 后按 Escape 提交。
- 两行文字时 Space 的 Height slider 由 disabled 变为 nabled；设置 Height=50 后，面板尺寸从 211 x 236 变为 211 x 273。
- 断言：Height slider 的 disabled=false 且 value 变化，同时面板尺寸文本高度变化（或截图高度差）。

### 8.2 Reflection 实际效果
- Reflection Toggle 关→开：class g-[#DCDDE3] → g-[#232323]。
- 开启后截图 diff：
onzero_pixels=140160, mean_abs=0.017085，说明文字图层确实产生反射效果。
- 4 个滑块（Scope/Opacity/Distance/Angle）均能调节，每次调节都有像素 diff。
- 断言：toggle class 变化 + 4 个 slider value 变化 + 截图 diff 大于阈值（建议 
onzero_pixels > 10000）。

### 8.3 Background 色盘与取色
- Background 展开后前 3 个特殊按钮：index0 无填充、index1 色盘（img[src*='edit_icon_color_picker.png']）、index2 取色（eyedropper svg）。
- 色盘按钮：打开调色弹窗（含 HSL/RGB Tab、hexInput、RGB/HSL 滑块），切换 Tab 有 diff，hex 改 #ff0000 后应用有 diff。
- 取色按钮：点击进入取色模式（diff_mode nonzero_pixels=437532），再点击画布有色区域应用颜色，背景变化（diff_applied nonzero_pixels=423026）。
- 断言：弹窗出现（hexInput visible）、hex 变化后背景截图 diff；取色后背景截图 diff 大于阈值。

### 8.4 Outline Color 色盘与取色
- Outline Color 行：index5 色盘、index6 取色，交互与 Background 一致。
- 色盘打开调色弹窗（hexInput visible），Escape 关闭。
- 取色进入取色模式（diff_mode nonzero_pixels=444649），点击画布应用后（diff_applied nonzero_pixels=433285）。
- 断言同 Background：弹窗出现 + 应用后像素 diff。

### 8.5 断言总原则
- 不要只断言开关 class 或参数 value；必须同时断言**文字图层的实际视觉/几何变化**。
- 可用截图像素 diff（ImageChops.difference）作为效果断言：反射/背景/描边效果建议阈值 
onzero_pixels > 10000；两行高度建议断言尺寸文本或文本层 bbox 高度变化。

### 8.6 证据
- space_height_two_lines.json、
eflection_effect.json
- ackground_palette_modal.json、ackground_picker.json
- outline_color_special.json、outline_picker.json
- 截图：shots/120_*.png ~ shots/172_*.png
