# -*- coding: utf-8 -*-
import os

OUT = os.path.abspath("artifacts/new_feature_detection_ui_20260901_124711")
os.makedirs(OUT, exist_ok=True)

nose_yaml = r'''page: NoseShapeDetector
url: https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector
source_prd: D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md
landmark:
  selector: 'h1:text-is("Free AI Nose Shape Detector: Find Your Nose Type Online")'
  description: 上传前 SEO Hero 主标题，页面唯一标识
entry:
  from: DirectUrl
  trigger: 直接打开 /tools/nose-shape-detector
  selector: 'a[href*="/tools/nose-shape-detector"]'
exploration:
  task_id: new_feature_detection_ui_20260901_124711
  tested_url: https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector
  viewport_pc: 1920x1080
  driver: playwright_mcp_only
  environment_strategy: 测试服 guangzhuiyuan；需登录（会员账号）才能上传生成；上传素材 test_images/有人脸.JPG

elements:
  upload_input:
    selector: '#img2imgFirstScreenUploadInput'
    type: file
    note: 上传前可见 "Choose File" 文案；label 拦截指针事件，需 force/坐标点击触发文件选择器
  seo_h1:
    selector: 'h1'
    text: Free AI Nose Shape Detector: Find Your Nose Type Online
  seo_desc:
    selector: 'p:has-text("smart nose shape analyzer")'
  upload_button:
    selector: 'button:has-text("Choose File")'
    note: 点击由 label 触发，Playwright 用 #img2imgFirstScreenUploadInput force click 更稳
  result_col_original:
    selector: 'text=Original Image'
  result_col_analysis:
    selector: 'text=Analysis Result'
  result_col_optimized:
    selector: 'text=Optimized Result'

states:
  seo_initial:
    description: 上传前 SEO 首屏，无三栏结果态
    trigger: 打开页面等待 H1 可见
    url_or_state_key: /tools/nose-shape-detector
    buttons:
      btn_choose_file:
        selector: '#img2imgFirstScreenUploadInput'
        role_or_text: 'Choose File'
        action_result: 触发系统文件选择器
        reversible: true
  result_analysis_loading:
    description: 上传后分析生成中，三栏出现，分析区 Generating analysis...
    trigger: 上传有人脸图后立即
    url_or_state_key: /tools/nose-shape-detector（页内状态切换，不跳转）
    buttons:
      btn_upload_image:
        selector: 'text=Upload Image'
        visible_condition: 结果态可见
        enabled_condition: 分析生成中置灰不可点
      btn_analysis_download:
        selector: 'text=Download >> nth=0'
        enabled_condition: 分析生成中置灰
  result_complete_placeholder:
    description: 分析完成，优化结果区为模糊承接态（无真实优化图）
    trigger: 分析生成完成后
    url_or_state_key: /tools/nose-shape-detector（页内）
    buttons:
      btn_analysis_download_done:
        selector: 'text=Download'
        action_result: 下载分析结果图 jpg
      btn_get_it_now:
        selector: 'text=Get It Now'
        action_result: 进入 Portrait Editor 承接（选中原图，不选模板）
        reversible: false

selector_semantic_gaps:
  - 优化结果区无 Download 按钮，仅 Get It Now（符合无优化结果图需求）
  - 上传按钮底层为 input#img2imgFirstScreenUploadInput，label 拦截点击

prd_only_or_unverified_states:
  - 点击 Get It Now 后的 Portrait Editor 承接未点击验证
  - 点击 Download 未真实验证下载文件格式

notes:
  - 优化结果区文案为 "Based on your photo and analysis, we've generated a beautifully optimized version just for you."
  - 三栏从上到下/从左到右：Original Image / Analysis Result / Optimized Result
'''

face_yaml = r'''page: AiFaceReader
url: https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader
source_prd: D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md
landmark:
  selector: 'h1:text-is("AI Face Reader: Read Your Expressions Online for Free")'
  description: 上传前 SEO Hero 主标题，页面唯一标识
entry:
  from: DirectUrl
  trigger: 直接打开 /tools/ai-face-reader
  selector: 'a[href*="/tools/ai-face-reader"]'
exploration:
  task_id: new_feature_detection_ui_20260901_124711
  tested_url: https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader
  viewport_pc: 1920x1080
  driver: playwright_mcp_only
  environment_strategy: 测试服 guangzhuiyuan；需登录（会员账号）才能上传生成；上传素材 test_images/有人脸.JPG

elements:
  upload_input:
    selector: '#img2imgFirstScreenUploadInput'
    type: file
    note: 同 nose-shape-detector，label 拦截点击，需 force/坐标点击
  seo_h1:
    selector: 'h1'
    text: AI Face Reader: Read Your Expressions Online for Free
  seo_desc:
    selector: 'p:has-text("Unlock the secrets of your soul")'
  upload_button:
    selector: 'button:has-text("Choose File")'
  result_col_original:
    selector: 'text=Original Image'
  result_col_analysis:
    selector: 'text=Analysis Result'
  result_col_optimized:
    selector: 'text=Optimized Result'

states:
  seo_initial:
    description: 上传前 SEO 首屏，无三栏结果态
    trigger: 打开页面等待 H1 可见
    url_or_state_key: /tools/ai-face-reader
    buttons:
      btn_choose_file:
        selector: '#img2imgFirstScreenUploadInput'
        role_or_text: 'Choose File'
        action_result: 触发系统文件选择器
        reversible: true
  result_analysis_waiting:
    description: 分析生成中 + 优化等待态（Waiting for analysis...）
    trigger: 上传有人脸图后立即
    url_or_state_key: /tools/ai-face-reader（页内状态切换）
    buttons:
      btn_upload_image:
        selector: 'text=Upload Image'
        enabled_condition: 生成中置灰
      btn_analysis_download:
        selector: 'text=Download'
        enabled_condition: 生成中置灰
      btn_continue:
        selector: 'text=Continue in Portrait Editor'
        enabled_condition: 生成中置灰
  result_optimized_loading:
    description: 分析完成，优化结果生成中（Generating optimized result...）
    trigger: 分析结果图展示后
    url_or_state_key: /tools/ai-face-reader（页内）
    buttons:
      btn_continue_loading:
        selector: 'text=Continue in Portrait Editor'
        enabled_condition: 优化生成中置灰
  result_complete_optimized:
    description: 分析+优化均完成，三栏结果态
    trigger: 优化结果图生成完成后
    url_or_state_key: /tools/ai-face-reader（页内）
    buttons:
      btn_analysis_download_done:
        selector: 'text=Download'
        action_result: 下载分析结果图 jpg
      btn_optimized_download:
        selector: 'text=Download >> nth=1'
        action_result: 下载优化结果图 jpg
      btn_continue_done:
        selector: 'text=Continue in Portrait Editor'
        action_result: 带原图/分析图/优化图进入 Portrait Editor（选中优化图）
        reversible: false

selector_semantic_gaps:
  - 三栏结果态 Download 按钮有多个，需按区域 nth 区分
  - 上传按钮底层为 input#img2imgFirstScreenUploadInput，label 拦截点击

prd_only_or_unverified_states:
  - Continue in Portrait Editor 带入三张图未点击验证
  - Download 未真实验证下载文件格式

notes:
  - 加载态文案：分析区 "Generating analysis..."，优化区 "Waiting for analysis..." → "Generating optimized result..."
  - 三栏：Original Image / Analysis Result / Optimized Result
'''

sync = r'''---
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
'''

import pathlib
p = pathlib.Path("page_map/pokecut")
p.mkdir(parents=True, exist_ok=True)
pathlib.Path("page_map/pokecut/nose_shape_detector_v1.yaml").write_text(nose_yaml, encoding="utf-8")
pathlib.Path("page_map/pokecut/ai_face_reader_v1.yaml").write_text(face_yaml, encoding="utf-8")
pathlib.Path(os.path.join(OUT, "sync.md")).write_text(sync, encoding="utf-8")
print("written page_map + sync.md")
