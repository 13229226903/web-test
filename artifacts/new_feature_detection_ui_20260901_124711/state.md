task_id: new_feature_detection_ui_20260901_124711
task_type: new_feature_test
status: confirmed
execution_mode: codex_single_context
agent_call_count: {}
requirement_doc: "D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md"
target_url:
  - "https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector"
  - "https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader"
entry_path: null
scope: "两个检测类 SEO 页面按用例对照探索：nose-shape-detector（无优化结果图/模糊承接）与 ai-face-reader（有优化结果图/三栏结果态）"
stop_at: cases_review
exploration_driver: playwright_mcp_only
diagnostic_driver: none
forbidden:
  - "未授权的删除/购买/订阅/对外通知/不可逆提交"
assumptions:
  - "测试服域名按用户要求改为 https://pokecut-dev.guangzhuiyuan.com/。"
  - "本次按用例文档只执行 page-map-sync 探索阶段，并停在 sync gate。"
  - "账号态与素材按 PROJECT.md：上传只用 test_images/ 现有文件；验证码固定 123456。"
  - "本轮已先验证 Playwright MCP 可通，并全程使用 Playwright MCP 探索；未启用脚本/DevTools。"
artifacts:
  sync: "artifacts/new_feature_detection_ui_20260901_124711/sync.md"
  cases: "artifacts/new_feature_detection_ui_20260901_124711/cases.md"
  impl: "artifacts/new_feature_detection_ui_20260901_124711/impl.md"
  requirement_draft: "artifacts/new_feature_detection_ui_20260901_124711/requirement_draft.md"
  page_maps:
    - "page_map/pokecut/nose_shape_detector_v3.yaml"
    - "page_map/pokecut/ai_face_reader_v3.yaml"
  evidence_dir: "artifacts/new_feature_detection_ui_20260901_124711/shots"
next_step: "archived_done"
blockers:
  - "真实购买成功、网络错误/鉴黄/优化失败/credits 扣返等故障注入未覆盖（未授权且本轮限定纯 MCP 页面探索）。"
created_at: "2026-09-01 12:47:11"
updated_at: "2026-09-02 14:02:00"







