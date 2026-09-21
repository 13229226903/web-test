---
task_id: 2026-09-17_create_auto_intent_recognition
agent: page-map-sync
status: confirmed
repair_scope: full_exploration
gate_exemption: none
inputs:
  entry_url: http://10.17.1.66:3001/create
  target_feature: Chat to Edit Auto intent recognition
  prompts: 10
  reference_image: test_images/1K.jpg
  account: 450832596@qq.com (member, User8JY)
outputs:
  scanned_pages:
    - /create
    - /agent?pid=<uuid>
  page_map_versions:
    - page_map/pokecut/create_chat_to_edit_auto_v1.yaml
  coverage_gates:
    prompt_style_id: 10/10
    task_id: 10/10
    result_resolution: 9/9 applicable
  state_button_coverage:
    create_initial: covered
    model_dropdown_open: covered
    image_uploaded: covered
    prompt_filled: covered
    agent_processing: covered
    agent_result_ready: covered
  requirement_actual_diffs: []
  bug_candidates: []
  skipped: []
  special_dependencies:
    - Member account required for generation credits.
    - Playwright MCP only; no DevTools MCP.
    - Reference image must come from test_images/.
  specs_updated: []
next_agent: test-case-design
created_at: 2026-09-17 03:00:00
---

# sync.md — Create Chat to Edit Auto Intent Recognition

## 1. 探索摘要

- 入口：`http://10.17.1.66:3001/create`
- 功能：`Chat to Edit` + `Auto` 模型 + 1 张参考图 + 10 条 prompt
- 账号：`450832596@qq.com`，页面显示 `User8JY`，会员态
- 参考图：`test_images/1K.jpg`，原始分辨率 `1200x1600`
- 探索驱动：`playwright_mcp_only`
- 结果：10/10 条 prompt 均完成提交并记录 `taskId`；9 条适用分辨率验证的用例全部符合预期；第 10 条按需求只记录 `taskId`，`styleId` 为空
- 产物：
  - 页面地图：`page_map/pokecut/create_chat_to_edit_auto_v1.yaml`
  - 结果证据：`artifacts/2026-09-17_create_auto_intent_recognition/evidence/auto_intent_results.yaml`
  - 控制台与快照证据：`artifacts/2026-09-17_create_auto_intent_recognition/evidence/`

## 2. 页面覆盖矩阵

| # | 用例或覆盖点 | 结论 | 证据 |
|---|---|---|---|
| 1 | prompt `enhance` → styleId `pkweb_comfyui_enhance_natural`，结果 4K | covered | `evidence/auto_intent_results.yaml` case 1；`evidence/console_case1_enhance.log`；`evidence/snapshot_case1_result.yml` |
| 2 | prompt `人像增强` → styleId `pkweb_comfyui_enhance_portrait`，结果 4K | covered | `evidence/auto_intent_results.yaml` case 2；`evidence/console_cases2_10.log`；`evidence/snapshot_case2_result.yml` |
| 3 | prompt `文字增强` → styleId `pkweb_comfyui_enhance_text`，结果 4K | covered | `evidence/auto_intent_results.yaml` case 3；`evidence/console_cases2_10.log`；`evidence/snapshot_case3_result.yml` |
| 4 | prompt `老照片修复` → styleId `photoenhance_oldphoto`，结果 ×2 | covered | `evidence/auto_intent_results.yaml` case 4；`evidence/console_cases2_10.log`；`evidence/snapshot_case4_result.yml` |
| 5 | prompt `去水印` → styleId `pc_remove_watermark`，结果同原图 | covered | `evidence/auto_intent_results.yaml` case 5；`evidence/console_cases2_10.log`；`evidence/snapshot_case5_result.yml` |
| 6 | prompt `穿上比基尼` → styleId `aireplace_bikini_1`，结果同原图 | covered | `evidence/auto_intent_results.yaml` case 6；`evidence/console_cases2_10.log`；`evidence/snapshot_case6_result.yml` |
| 7 | prompt `去除眼袋` → styleId `pkweb_comfyui_removeeyebag`，结果同原图 | covered | `evidence/auto_intent_results.yaml` case 7；`evidence/console_cases2_10.log`；`evidence/snapshot_case7_result.yml` |
| 8 | prompt `增肌` → styleId `pkweb_comfyui_male_strongabs`，结果同原图 | covered | `evidence/auto_intent_results.yaml` case 8；`evidence/console_cases2_10.log`；`evidence/snapshot_case8_result.yml` |
| 9 | prompt `变成光头` → styleId `pkweb_comfyui_baldhead`，结果同原图 | covered | `evidence/auto_intent_results.yaml` case 9；`evidence/console_cases2_10.log`；`evidence/snapshot_case9_result.yml` |
| 10 | prompt `背景换成沙滩` → styleId 为空，仅记录 taskId | covered | `evidence/auto_intent_results.yaml` case 10；`evidence/console_cases2_10.log` |

## 3. 需求差异

- 无 `gap`
- 无 `bug_candidate`
- 无 `skipped`
- 第 10 条 `背景换成沙滩` 的 `AutoIntentRecognition` 返回 `unmatched` 且 `styleId` 为空，符合需求；后续 fallback 使用 `fallback-pro-img2img`，`taskId` 已记录

## 4. 关键发现与下游注意事项

- `/create` 的 Chat to Edit 输入框、上传按钮、模型选择器和提交按钮均可通过稳定 selector 定位：
  - prompt：`textarea[placeholder='What do you want to design today?']`
  - 上传：`div[title='Upload reference images']`
  - 模型：`div[title='Model']`
  - Auto 选项：`div.cursor-pointer:has(img[src*='model_icon_auto.svg'])`
  - 提交：`div.cursor-pointer:has(img[src*='create_chat_send_btn.svg'])`
- 提交后跳转 `/agent?pid=<uuid>`； taskId 需从控制台 `AutoIntentRecognition`、`taskflow-result-file` 或 `AutoCanvasSuccess` 提取
- 结果分辨率在画布页选中结果图后显示，格式为 `<width> x <height>`
- 生成需要可用 credits；本次使用会员账号 `450832596@qq.com`
- 匿名/0 credits 账号提交会触发注册或购买弹窗，不能完成生成；这属于账号态依赖，不是产品缺陷

## 5. 版本差异摘要

- 新增页面地图：`page_map/pokecut/create_chat_to_edit_auto_v1.yaml`
- 该地图覆盖 `/create` Chat to Edit 主流程和 `/agent` 结果态
- 未修改历史 page_map；`create_ai_tools_v2.yaml` 等既有资产保持不变

## 6. 状态化按钮覆盖摘要

| 状态 | 覆盖情况 | 说明 |
|---|---|---|
| `create_initial` | covered | 初始输入框、上传、模型入口 |
| `model_dropdown_open` | covered | Auto 选项可见且可选 |
| `image_uploaded` | covered | 缩略图、计数、删除入口 |
| `prompt_filled` | covered | 提交按钮可用 |
| `agent_processing` | covered | 进度与控制台任务流 |
| `agent_result_ready` | covered | 结果图与分辨率显示 |

