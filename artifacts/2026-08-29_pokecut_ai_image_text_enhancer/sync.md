---
task_id: 2026-08-29_pokecut_ai_image_text_enhancer
agent: page-map-sync
status: pending_review
repair_scope: full_exploration
gate_exemption: false
inputs:
  - D:\Test\web-test\飞书文档_ 文字画质增强实验优化(安国)-AI分析后的CheckBox.md
  - page_map/pokecut/ai_image_text_enhancer_v2.yaml
outputs:
  scanned_pages: [/tools/ai-image-text-enhancer]
  page_map_versions: [v3]
  coverage_gates: {default_state: covered, upload_state: covered, tooltip: covered, free_quota: covered, paid_cost: covered_predeploy, generation_result: covered_predeploy}
  state_button_coverage: covered
  requirement_actual_diffs: []
  bug_candidates: []
  skipped:
    - 测试服登录失败（authToken empty / gateway 404），生成与账号态改用预部署复试
    - 免费 4 次按 IP 刷新、剩余次数抵扣顺序、B 方案专属拦截、真 8K highest clarity、多效果后端执行顺序需配额/账号/日志口径，未伪造
  special_dependencies: [预部署 DEBUG 面板切换, 会员账号 450832596@qq.com, 素材 1K.jpg/4K.jpg/4K.png/8K.jpg]
  specs_updated: false
next_agent: test-case-design
created_at: 2026-08-29 16:20:00 +08:00
---

# sync.md — 文字画质增强实验页（AI Image Text Enhancer）

## 1. 探索摘要
- 页面 /tools/ai-image-text-enhancer 可访问，H1 为 Enhance Text in Image to 8K Online Free，上传入口 #singleUploadInput 稳定。
- 上传 1K 后页内进入处理区，不跳转；效果区/分辨率区/主按钮/点数区均存在，选择器与 v2 一致。
- 四条 effect 均可用 [data-effect] 与 ria-pressed 定位；tooltip 文案四条全部命中需求。
- 免费额度刷新已上线：当前测试服 IP 命中 4 次免费，cost_state=free，按钮显示 Free；数字点数仅在付费态/预部署可见。
- 测试服登录失败（authToken empty，gateway 404）；DEBUG 面板切预部署后登录成功，生成结果态约 10s 出现。

## 2. 页面覆盖矩阵
| 状态 | 覆盖 | 证据 |
|---|---|---|
| 匿名首屏 | covered | explore_page_v3.json 00_initial |
| 上传后默认态 | covered | explore_page_v3.json 01/02 |
| tooltip 四条 | covered | explore_page_v3.json 03_tooltips |
| 非增强隐藏分辨率区 / 无效果禁用 | covered | explore_page_v3.json 04/05 |
| 免费额度态 | covered | explore_cost_v3.json |
| 付费态与生成结果态 | covered（预部署） | explore_generation_predeploy_v3.json |

## 3. 需求差异
- 无阻断性 gap/bug_candidate。付费点数数值规则需在付费态（预部署）断言，免费额度态下按钮正确显示 Free。

## 4. 关键发现与下游注意事项
- 环境策略：生成/登录/账号态类用例必须先 _goto 再 DEBUG 切预部署再登录；测试服登录会 authToken empty。
- cost 断言需区分 data-text-enhance-cost-state：free 态断言 Free，paid 态断言具体数字。
- L3 购买拦截：测试服当前 IP 免费额度仍可用会走真实生成，测试服购买拦截跳过；预部署购买拦截可复现。
- 免费 4 次按 IP 刷新、剩余次数按执行顺序抵扣、B 方案专属购买、真 8K highest clarity、多效果后端执行顺序、tooltip 视频资源名仍为不可自动化或需额外口径项，在 cases.md 记录为 gap/skip。

## 5. 版本差异摘要
- v2 -> v3：新增免费额度态（cost_state=free/Free）与预部署付费态/结果态证据；记录测试服登录失败与预部署切换；其余 selector 不变。

> confirmed 前不得进入 test-case-design。

## 6. 复探补充（用户指正后）
- L2-002 修正为「结果态非 Enhance Text 结果不展示分辨率」：预部署 remove_glare 单模式生成超过 180s 未出结果（enhance_text 约 10s 出结果），疑似非增强工作流慢/失败，证据 investigate_l2_002b_v3.json。
- L4-003 修正为预部署真实登录会员：账号 450832596@qq.com 登录成功但显示免费档 2k/4k/8k=2/2/6，非需求 Pro/Ultra 的 Free/Free/4；疑似预部署未同步会员订阅或账号非会员，证据 investigate_member_v3.json。
- 结论：两处均为环境/账号数据问题，非需求描述错误；需求中 Pro/Ultra=Free/Free/4 与结果态无分辨率信息的要求明确。
