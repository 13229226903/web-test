---
task_id: new_feature_detection_ui_20260901_124711
agent: ui-test-page-map-sync
status: pending_review
repair_scope: full_exploration
gate_exemption: false
inputs:
  requirement_doc: D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md
  entry_urls:
    - https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector
    - https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader
outputs:
  scanned_pages:
    - nose-shape-detector
    - ai-face-reader
  page_map_versions:
    - page_map/pokecut/nose_shape_detector_v1.yaml
    - page_map/pokecut/ai_face_reader_v1.yaml
  coverage_gates: sync_review
  state_button_coverage: 已覆盖上传前 SEO 态、分析加载态、优化等待/加载态、结果完成态
  requirement_actual_diffs:
    - {case: "上传前保持原 SEO 内容结构和文案", diff_type: covered, note: "两页上传前均保留 SEO H1/描述/FAQ，无三栏结果态"}
    - {case: "有优化结果图页面展示三栏结果态(ai-face-reader)", diff_type: covered, note: "Original/Analysis/Optimized 三栏齐全，优化区含 Download + Continue in Portrait Editor"}
    - {case: "无优化结果图页面展示模糊承接态(nose-shape-detector)", diff_type: covered, note: "优化区仅 Get It Now，无 Download，无真实优化图"}
    - {case: "结果生成中保持分析优先与优化等待态", diff_type: covered, note: "分析区 Generating analysis...，优化区 Waiting for analysis..."}
    - {case: "分析结果图完成后展示优化加载态", diff_type: covered, note: "优化区 Generating optimized result..."}
    - {case: "SEO 配置字段驱动优化结果生成", diff_type: gap, note: "需模板类/img2img 类配置页面与 extendFunType/extendPresetParams，本轮未覆盖"}
    - {case: "原图区域上传按钮恢复可用/分析图下载jpg/优化图下载jpg/Continue带入三张图", diff_type: gap, note: "按钮已见但未点击验证（避免额外 credits 消耗与不可逆跳转）"}
    - {case: "分析结果图网络错误/服务器忙/鉴黄失败/优化结果图生成失败", diff_type: gap, note: "需故障注入或特定异常素材，本轮无法可靠触发"}
    - {case: "分析/优化 credits 不足购买弹窗与模糊承接", diff_type: skipped, note: "需要 credits 不足账号态"}
    - {case: "移动端结果态纵向排版与承接差异", diff_type: gap, note: "本轮仅 PC 端 1920x1080，未做移动端实测"}
  bug_candidates: []
  skipped:
    - "credits 不足购买逻辑：需要 credits 不足账号"
  special_dependencies:
    - "登录：会员账号 450832596@qq.com + 验证码 123456"
    - "上传素材：test_images/有人脸.JPG"
  specs_updated: false
next_agent: test-case-design
created_at: 2026-09-01 13:10:00
---

# 探索结果摘要

## 已确认（covered）
- 两页上传前均保持原 SEO 内容结构与文案，未提前出现三栏结果态。
- ai-face-reader：上传后三栏 Original Image / Analysis Result / Optimized Result，优化区含 Download + Continue in Portrait Editor。
- nose-shape-detector：优化区为模糊承接态，文案 "Based on your photo and analysis, we've generated a beautifully optimized version just for you." + Get It Now，无优化图与 Download。
- 加载态顺序：分析区 "Generating analysis..."，优化区 "Waiting for analysis..." → "Generating optimized result..." → 完成。

## 未覆盖（gap / skipped）
- 失败逻辑（网络错误/服务器忙/鉴黄失败/优化失败）需故障注入。
- 购买逻辑需 credits 不足账号。
- 下载/Continue 点击行为未真实执行。
- 移动端布局未实测。

## 关键发现
- 上传控件底层为 input#img2imgFirstScreenUploadInput，label 拦截指针事件，Playwright 用 force 点击触发文件选择器最稳。
- 三栏结果态 Download 按钮有多个，需按区域区分。

## 下游注意事项
- 后续 test-writing 需为三栏结果态的多个 Download 按钮建立区域限定 selector。
- 移动端与失败/购买逻辑建议单独补一轮探索或用专用账号/故障注入环境。

## 版本差异摘要
- 本次为 nose_shape_detector 与 ai_face_reader 首版 page_map（_v1）。
