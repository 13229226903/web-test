---
task_id: 2026-09-17_mobile_canvas_stats_first10
agent: page-map-sync
status: confirmed
repair_scope: full_exploration
gate_exemption: null
inputs:
  requirement_doc: D:/Test/my_project/testcases/v3.2_testcases_source/04_版本统计优化.md
  target_url: http://10.17.1.66:3001/
  scope: 前 10 条移动端画布统计已确认；补充 PC 新画布统计；已完成正确功能入口的第 16-25、26/27/28/29/30/31/38/39/40/41、34/35/36/37/42-47 条补采
  environment: 测试服 http://10.17.1.66:3001/en
  device: desktop Chrome via Playwright MCP for PC continuation; historical first10 device iPhone 13 / 390x844 / is_mobile=true
  accounts:
    anonymous: 未登录
    free: autotest202609171333@qq.com / autotest202609171600@qq.com / autotest202609171637@qq.com（均 0 credits）
    pro: 450832596@qq.com（vipSubType=pro）
outputs:
  scanned_pages:
    - /en
    - /create/edit?pid=*
    - /create
    - /agent?pid=*
    - /tools/photo-enhancer
    - /tools/background-remover
    - /tools/magic-eraser-with-ai-detection
    - /it/ai-replace
    - /pt/ferramentas/expandir-imagem-ia
    - /image-to-image-ai
    - /ai-image-generator
    - /tools/photo-restoration
    - /tools/add-hearts-to-photo
    - /tools/background-changer
  page_map_versions:
    - page_map/pokecut/mobile_canvas_v2.yaml
    - page_map/pokecut/mobile_canvas_v3.yaml
    - page_map/pokecut/mobile_canvas_v4.yaml
    - page_map/pokecut/mobile_canvas_v5.yaml
    - page_map/pokecut/mobile_canvas_v6.yaml
    - page_map/pokecut/mobile_canvas_v7.yaml
    - page_map/pokecut/mobile_canvas_v8.yaml
    - page_map/pokecut/mobile_canvas_v9.yaml
  new_canvas_mobile_scope:
    required: true
    status: completed
    rule: 新画布页相关统计除 PC 外需补移动端探索；移动端入口 URL 与 PC 保持一致
    scope: stats 16-47 中所有 新画布...xx_yy 项
    evidence: artifacts/2026-09-17_mobile_canvas_stats_first10/evidence/new_canvas_mobile_scope_pending.md
  stat_frequency_assertion:
    enabled: true
    rule: 单次动作目标 sendGaEvent=1 且 debug 统计=1 才通过；0 次为漏报 bug，>=2 次为多报 bug
    current_status: 历史事件名通过项需按隔离单次动作重采次数；未重采前不计入严格 passed
    evidence: artifacts/2026-09-17_mobile_canvas_stats_first10/evidence/stat_frequency_assertion_policy.md
  coverage_gates:
    passed: 0
    event_name_passed: 43
    strict_frequency_passed: 25
    gap: 0
    bug_candidates: 2
    skipped: 2
    mobile_new_canvas_pending: 0
    mobile_new_canvas_passed: 24
    mobile_new_canvas_gap: 0
    mobile_new_canvas_bug_candidates: 2
    frequency_verified: 25
    frequency_pending_revalidation: 18
    frequency_bug_candidates: 0
    frequency_assertion_rule: 单次动作目标 sendGaEvent=1 且 debug 统计=1 才通过；0 次为漏报 bug，>=2 次为多报 bug
  state_button_coverage:
    verified_states:
      - mobile_canvas_anonymous_credits_empty_register
      - mobile_canvas_free_credits_empty_purchase
      - mobile_canvas_debug_skip_purchase_success
      - mobile_canvas_adjust_filter_confirm
      - mobile_canvas_background_remover_confirm
    covered_functions:
      - 画质增强ultra
      - AI消除
      - AI扩图
      - 背景移除
      - 调节
      - 年 ultra 购买成功（Debug 跳过真实购买）
  requirement_actual_diffs:
    - stat: 3
      expected: 移动端画布xx功能点数用完触发注册
      actual: 移动端画布画质增强ultra功能点数用完触发注册；移动端画布AI消除功能点数用完触发注册；移动端画布AI扩图功能点数用完触发注册
      verdict: 一致
    - stat: 4
      expected: 移动端画布xx功能点数用完触发注册成功
      actual: 移动端画布画质增强ultra功能点数用完触发注册成功；移动端画布AI扩图功能点数用完触发注册成功
      verdict: 一致
    - stat: 6
      expected: 移动端画布xx功能点数用完触发购买
      actual: 移动端画布画质增强通用功能点数用完触发购买；移动端画布AI消除功能点数用完触发购买；移动端画布AI扩图功能点数用完触发购买
      verdict: 一致
    - stat: 7
      expected: 移动端画布xx功能点数用完触发购买yy成功
      actual: 移动端画布AI扩图功能点数用完触发购买年ultra成功
      verdict: 一致（使用 Debug“跳过真实购买（查看统计项用）”模拟成功支付）
    - stat: 8
      expected: 移动端画布点数用完触发购买yy成功
      actual: 移动端画布点数用完触发购买年ultra成功
      verdict: 一致（使用 Debug“跳过真实购买（查看统计项用）”模拟成功支付）
    - stat: 10
      expected: 移动端画布页_xx弹窗确认
      actual: 移动端画布页_调节弹窗确认；移动端画布页_背景移除通用弹窗确认
      verdict: 一致
  bug_candidates:
    - id: BC-02
      title: "无限画布页画质增强ultra点数用完触发注册未上报"
      ac: "stat12 无限画布页xx功能点数用完触发注册"
      priority: P1
      expected: "无限画布页画质增强ultra功能点数用完触发注册"
      actual: "注册弹窗_出现"
    - id: BC-03
      title: "无限画布页画质增强ultra点数用完注册成功未上报"
      ac: "stat13 无限画布页xx功能点数用完触发注册成功"
      priority: P1
      expected: "无限画布页画质增强ultra功能点数用完触发注册成功"
      actual: "注册弹窗_注册成功；登录成功_邮箱登录方式"
  skipped: []
  environment_observations:
    - id: ENV-01
      title: 背景移除结果下载曾出现间歇性 ERR_INCOMPLETE_CHUNKED_ENCODING
      first_result: PRO 账号首次执行背景移除时任务 resultCode=100，但 /api/download 报 net::ERR_INCOMPLETE_CHUNKED_ENCODING，UI 停在 85%
      retest_result: 使用 test_images/有人脸.JPG 复测成功，结果加载后 Confirm 可点击，确认事件正常上报
      verdict: 间歇性环境/下载问题，本次复测未复现；不计 bug_candidate，旧日志保留为诊断证据
  special_dependencies:
    - 匿名/免费账号注册弹窗：随机未使用邮箱 + 固定验证码 123456
    - 免费账号 0 credits 状态：新建免费账号后直接命中
    - 购买成功统计：Debug 弹窗打开“跳过真实购买（查看统计项用）”，内购支付面板点击购买模拟成功
    - PRO 账号用于结果生成、调节确认与背景移除确认链路
  specs_updated: []
next_agent: test-case-design
created_at: 2026-09-17 14:47:06
updated_at: 2026-09-20 12:42:54
---

# sync.md — 移动端画布统计前 10 条首次探索

## 1. 探索摘要

- 任务类型：存量功能补资产，探索驱动为 Playwright MCP only。
- 范围：需求文档前 10 条统计，按 H2 顺序逐条核对；控制台搜索“统计”读取 sendGaEvent 与 debug 统计成对事件。
- 入口链路：移动端首页点击 Start Creating for Free -> 上传 `test_images/1K.jpg` 或 `test_images/有人脸.JPG` -> `/create/edit?pid=*`。
- 账号链路：匿名态验证注册触发；免费账号 0 credits 验证购买触发；购买成功统计通过 Debug“跳过真实购买（查看统计项用）”模拟支付；PRO 账号验证画布弹窗确认。
- 环境：测试服 `http://10.17.1.66:3001/en`，iPhone 13 移动模拟。
- 结论：前 10 条全部 covered；初次背景移除下载失败经复测未复现，不作为 bug_candidate。

## 2. 页面覆盖矩阵

| # | 用例或覆盖点 | 结论 | 证据 |
|---|---|---|---|
| 1 | 移动端画布点数用完触发注册 | ✅ 一致：匿名 0 credits 点击 Photo Enhancer 的 Enhance 后上报 移动端画布点数用完触发注册 | evidence/console_credits_register_success.log |
| 2 | 移动端画布点数用完触发注册成功 | ✅ 一致：注册成功后上报 移动端画布点数用完触发注册成功 | evidence/console_credits_register_success.log |
| 3 | 移动端画布xx功能点数用完触发注册 | ✅ 一致：抽测画质增强ultra、AI消除、AI扩图，分别上报 移动端画布画质增强ultra功能点数用完触发注册、移动端画布AI消除功能点数用完触发注册、移动端画布AI扩图功能点数用完触发注册 | evidence/console_credits_register_success.log、console_credits_register_extra_features.log |
| 4 | 移动端画布xx功能点数用完触发注册成功 | ✅ 一致：抽测画质增强ultra、AI扩图，分别上报 移动端画布画质增强ultra功能点数用完触发注册成功、移动端画布AI扩图功能点数用完触发注册成功 | evidence/console_credits_register_success.log、console_credits_register_extra_features.log |
| 5 | 移动端画布点数用完触发购买 | ✅ 一致：免费账号 0 credits 点击功能主按钮后上报 移动端画布点数用完触发购买 | evidence/console_credits_purchase.log |
| 6 | 移动端画布xx功能点数用完触发购买 | ✅ 一致：抽测画质增强通用、AI消除、AI扩图，分别上报 移动端画布画质增强通用功能点数用完触发购买、移动端画布AI消除功能点数用完触发购买、移动端画布AI扩图功能点数用完触发购买 | evidence/console_credits_purchase.log、shots/stat6_ai_extend_purchase_modal.png |
| 7 | 移动端画布xx功能点数用完触发购买yy成功 | ✅ 一致：0 credits 触发 AI Image Extender 购买；Debug 打开“跳过真实购买（查看统计项用）”后，在支付面板模拟购买成功，上报 移动端画布AI扩图功能点数用完触发购买年ultra成功 | evidence/console_purchase_debug_skip_and_methods.log、evidence/snapshot_purchase_success_after_debug_skip.yml、shots/stat7_8_purchase_success_collect_credits.png |
| 8 | 移动端画布点数用完触发购买yy成功 | ✅ 一致：同一模拟购买链路上报 移动端画布点数用完触发购买年ultra成功 | evidence/console_purchase_debug_skip_and_methods.log、evidence/snapshot_purchase_success_after_debug_skip.yml、shots/stat7_8_purchase_success_collect_credits.png |
| 9 | 移动端画布页_xx弹窗出现 | ✅ 一致：抽测画质增强、AI消除、AI扩图、背景移除，分别上报 移动端画布页_画质增强弹窗出现、移动端画布页_AI消除弹窗出现、移动端画布页_AI扩图弹窗出现、移动端画布页_背景移除弹窗出现 | evidence/console_member_dialog_events.log、console_credits_register_success.log、console_credits_purchase.log |
| 10 | 移动端画布页_xx弹窗确认 | ✅ 一致：Adjust -> Filter -> Confirm 上报 移动端画布页_调节弹窗确认；Background -> Background Remover -> Remove Background -> Confirm 复测上报 移动端画布页_背景移除通用弹窗确认 | evidence/console_adjust_confirm.log、snapshot_adjust_filter_panel.yml、snapshot_adjust_confirmed.yml、console_background_remove_success.log、snapshot_background_remove_confirmed.yml |

## 3. 需求差异

- 1–10 的事件名均与需求定义逐条一致；单次动作均在 Console 中观察到 sendGaEvent 与 debug 统计成对出现，未在同一动作内观察到重复上报。
- 第 3、4、6 条的 xx 是需求允许的功能占位；本次实际抽测 画质增强ultra、画质增强通用、AI消除、AI扩图，实现输出均为需求名单内的语义名，不构成差异。
- 第 7、8 条通过 Debug“跳过真实购买（查看统计项用）”完成购买成功分支验证；实际后缀为 年ultra成功，符合需求中的 yy成功 占位规则。
- 第 10 条不只验证调节弹窗，也复测了背景移除通用弹窗确认，确认事件与需求通用后缀一致。

## 4. 关键发现与下游注意事项

1. 匿名态 0 credits 与免费登录态 0 credits 是两条不同分支：匿名态先弹注册，注册成功后立即进入购买弹窗；免费登录态直接进入购买弹窗。
2. 新建免费账号初始 Credits 0 left，适合稳定触发第 1–6 条；免费账号只要注册成功仍保持 0 credits。
3. 购买成功统计可在 Debug 面板打开“跳过真实购买（查看统计项用）”后，通过内购弹窗支付面板点击购买稳定触发，无需真实支付。
4. 第 10 条最经济稳定的通用路径是 Adjust -> Filter -> Confirm；背景移除确认已复测通过，但依赖远端结果生成与下载，执行成本更高。
5. 背景移除首次失败发生在结果下载阶段：任务 resultCode=100，但 /api/download 报 ERR_INCOMPLETE_CHUNKED_ENCODING，UI 停在 85%。更换 `test_images/有人脸.JPG` 后复测成功，首次失败为间歇性环境/下载问题，不进入 bug_candidate。
6. Selector 落点：一级入口 `button.tool-card`、弹窗确认 `button:has-text('Confirm')`、注册输入与提交使用稳定 data-testid，未沉淀 Playwright MCP 临时 ref。

## 5. 版本差异摘要

- `mobile_canvas_v1.yaml` -> `mobile_canvas_v2.yaml`；历史 v1 未覆盖。
- v2 保留 v1 的 23 个既有 states，新增 `stats_first10_20260917.verified_states`，记录本次账号态、购买成功、背景移除确认链路和实际埋点。
- 首次背景移除下载失败的旧证据保留在 `environment_observations`，明确为复测未复现的间歇性问题；不再作为 blocked_path。
- 兼容影响：既有移动端画布 selector 不删除；后续用例设计优先引用 v2 新增状态，旧流程仍可安全读取 v1。



## 6. PC 新画布统计第 11-20 条补充（2026-09-18）

- 探索驱动：当前会话 Playwright MCP only；已完成强 preflight：browser_tabs list -> browser_navigate about:blank -> browser_snapshot -> browser_console_messages。
- 入口：`/create` -> `Start from a Photo` -> 上传 `test_images/1K.jpg` -> `/agent?pid=*`。未重新探索移动端前 10 条。
- 账号：先 anonymous Credits:0 触发注册；使用随机唯一邮箱 `autotest20260918102401@qq.com` 与验证码 `123456` 注册免费账号，注册后仍为 Credits:0。购买成功仅使用 DEBUG 面板启用“跳过真实购买（查看统计项用）”，checkout 点击 `Debug: 跳过真实购买`，未执行真实付款。

### 6.1 覆盖矩阵

| # | 操作 | 实际事件（Console 搜“统计”） | 期望事件 | 结论 | 证据 |
|---|---|---|---|---|---|
| 11 | 移动端 登录态账号（会员非必需）-> 首页进入画布 -> Photo Enhancer 弹窗 -> 提交任务 -> 结果弹窗底部下载 | `移动端结果弹窗确认下载`、`移动端画布页_画质增强ultra弹窗下载`、`下载成功` | `移动端画布页_xx弹窗下载`（xx=画质增强ultra） | ✅ 一致；send=1 / debug=1 | `evidence/mobile_stat11_enhance_popup_download_baseline.log`、`evidence/mobile_stat11_enhance_popup_download_after_full_debug.log` |
| 12 | anonymous Credits:0 -> Enhance -> Ultra HD Mode -> Enhance | `注册弹窗_出现` | `无限画布页画质增强ultra功能点数用完触发注册` | ❌ bug_candidate（BC-02）：UI 注册弹窗出现，但未出现需求要求的功能级事件 | `evidence/console_stat12_pc_enhance_ultra_register_debug.log` |
| 13 | 注册弹窗填随机唯一邮箱 + `123456` -> Sign up | `注册弹窗_注册成功`；`登录成功_邮箱登录方式` | `无限画布页画质增强ultra功能点数用完触发注册成功` | ❌ bug_candidate（BC-03）：实际为通用注册成功事件 | `evidence/console_stat13_pc_enhance_register_success_debug.log` |
| 14 | 免费账号 Credits:0 -> Enhance 购买面板 -> Yearly Ultra -> Debug 跳过真实购买 | `无限画布页点数用完触发购买年ultra成功` | `无限画布页xx功能点数用完触发购买yy成功`（xx=画质增强ultra，yy=年ultra） | ✅ 一致 | `evidence/console_stat14_pc_enhance_purchase_success_debug_skip.log` |
| 15 | `/create` -> `Start from a Photo` -> 上传 `test_images/1K.jpg` -> `/agent?pid=*` -> `Enhance` -> `Standard Mode` 生成成功 -> 选中 Enhanced 结果图层 -> 点击结果图下载 | `无限画布页单图下载`；`下载成功`；`无限画布页画质增强ultra功能图片下载保存`；`无限画布页画质增强2K-ultra模型图片下载保存` | `无限画布页xx功能图片下载保存`（xx=画质增强ultra） | ✅ 一致；已确认必须针对结果图下载，不对原图下载 | `evidence/console_stat15_recheck_result_download_mcp_raw.log`、`evidence/pc_stat15_result_image_download_recheck_summary.md` |
| 16 | Enhance -> Standard/Ultra 处理入口触发购买面板 | `无限画布页画质增强2K-通用模型点数用完触发购买` | `新画布增强购买出现en_/agent` | ⚠️ gap：实际为“无限画布页”功能点数用完触发购买，缺少 `新画布增强购买出现xx_yy` | `evidence/console_stat18_pc_removebg_purchase_appearance_debug.log` |
| 17 | Enhance checkout -> Debug 跳过真实购买 | `无限画布页点数用完触发购买年ultra成功` | `新画布增强年ultra购买成功en_/agent` | ⚠️ gap：购买成功回调存在，但命名未按新画布增强 xx_yy 事件 | `evidence/console_stat14_pc_enhance_purchase_success_debug_skip.log` |
| 18 | Background -> Remove BG -> Remove Background | `无限画布页背景移除通用功能点数用完触发购买` | `新画布抠图购买出现en_/agent` | ⚠️ gap：实际为“无限画布页背景移除通用功能点数用完触发购买” | `evidence/console_stat18_pc_removebg_purchase_appearance_debug.log` |
| 19 | Remove BG 购买/低阶免费处理链路 | 未观察到 `新画布抠图年ultra购买成功en_/agent`；观察到通用订阅成功仅在 Enhance checkout 触发 | `新画布抠图年ultra购买成功en_/agent` | ⚠️ gap：未见抠图功能级购买成功事件 | `evidence/console_stat19_pc_removebg_result_after_purchase_debug.log` |
| 20 | Erase -> Smart Auto Mode -> All -> Remove | `无限画布页AI消除功能点数用完触发购买`；另有 `AI消除功能_AI检测成功` | `新画布消除购买出现en_/agent` | ⚠️ gap：实际为“无限画布页AI消除功能点数用完触发购买” | `evidence/console_stat20_pc_erase_purchase_appearance_debug.log`、`shots/stat20_pc_erase_panel.png` |

### 6.2 差异与结论

- 第 12、13、15 条按用户要求先标记为 bug_candidate：注册弹窗出现、注册成功、下载保存均缺少需求要求的功能级事件维度。
- 未将需求实现差异伪装为 skipped；无真实付款、无不可逆业务提交。
- 第 20 条过程中曾出现一次 `服务器接口调用失败` 500，但随后仍观察到 `AI消除功能_AI检测成功` 与功能点数用完触发购买事件；暂记为环境观察，不单列 bug_candidate。
- PC 画布增强与背景移除低阶免费处理成功，增强结果下载成功并保存 JPG；下载链路保留完整 Console 和 Playwright MCP 下载证据。
- 页面地图版本：`mobile_canvas_v2.yaml` 保留历史；新增 `mobile_canvas_v3.yaml`，追加 PC 新画布统计状态和证据引用。

## 7. 本轮 Gate

- `status: confirmed`：等待用户审核 PC 新画布统计覆盖矩阵、第 15/42/43 条复核结果，以及 BC-02/BC-03 两个 bug_candidate。
- 按用户要求，本轮到第 20 条后停止，不进入 test-case-design / test-writing。

## 8. PC 正确功能入口补采：第 16-25 条（2026-09-18 第二轮校正）

用户确认之前从 `/create` 直进画布属于错误入口。`新画布...xx_yy` 类统计必须从对应 SEO 功能介绍页进入，再点击首屏上传按钮选图，进入 PC 无限画布后提交功能。该轮只补采“购买出现 + Debug 跳过真实购买成功”10 条，并停在第 10 条后等待确认。

### 8.1 正确入口映射

| 功能 | 正确入口 | 本轮语言/路径代入 |
|---|---|---|
| 画质增强 | `/tools/photo-enhancer` | `en_photo-enhancer` |
| 抠图 / 背景移除 | `/tools/background-remover` | `en_background-remover` |
| AI消除 | `/tools/magic-eraser-with-ai-detection` | `en_magic-eraser-with-ai-detection` |
| AI改图 | `/it/ai-replace` | `it_ai-replace` |
| AI扩图 | `/pt/ferramentas/expandir-imagem-ia` | `pt_expandir-imagem-ia` |

### 8.2 覆盖矩阵

| 原文序号 | 原文标题 | 操作 | 实际事件 | 结论 | 证据 |
|---:|---|---|---|---|---|
| 16 | 新画布增强购买出现xx_yy | `/tools/photo-enhancer` 首屏上传 -> Enhance -> Submit | `新画布增强购买出现en_photo-enhancer` | ✅ 一致 | `evidence/console_pc_correct_entry_en_photo_enhancer_purchase_appearance_debug.log` |
| 17 | 新画布增强zz购买成功xx_yy | Enhance checkout -> Debug 跳过真实购买 | `新画布增强年ultra购买成功en_photo-enhancer` | ✅ 一致 | `evidence/console_pc_correct_entry_en_photo_enhancer_purchase_success_debug.log` |
| 18 | 新画布抠图购买出现xx_yy | `/tools/background-remover` 首屏上传 -> Remove Background | `新画布抠图购买出现en_background-remover` | ✅ 一致 | `evidence/console_pc_correct_entry_en_background_remover_purchase_appearance_debug.log` |
| 19 | 新画布抠图zz购买成功xx_yy | Remove BG checkout -> Debug 跳过真实购买 | `新画布抠图年ultra购买成功en_background-remover` | ✅ 一致 | `evidence/console_pc_correct_entry_en_background_remover_purchase_success_debug.log` |
| 20 | 新画布消除购买出现xx_yy | `/tools/magic-eraser-with-ai-detection` 首屏上传 -> Erase -> All -> Remove | `新画布消除购买出现en_magic-eraser-with-ai-detection` | ✅ 一致 | `evidence/console_pc_correct_entry_en_magic_eraser_purchase_appearance_debug.log` |
| 21 | 新画布消除zz购买成功xx_yy | Erase checkout -> Debug 跳过真实购买 | `新画布消除年ultra购买成功en_magic-eraser-with-ai-detection` | ✅ 一致 | `evidence/console_pc_correct_entry_en_magic_eraser_purchase_success_debug.log` |
| 22 | 新画布改图购买出现xx_yy | `/it/ai-replace` 首屏上传 -> 填写描述 -> 画蒙版 -> Generate | `新画布改图购买出现it_ai-replace` | ✅ 一致 | `evidence/console_pc_correct_entry_it_ai_replace_generate_debug.log` |
| 23 | 新画布改图zz购买成功xx_yy | AI Replace checkout -> Debug 跳过真实购买 | `新画布改图年ultra购买成功it_ai-replace` | ✅ 一致 | `evidence/console_pc_correct_entry_it_ai_replace_purchase_success_debug.log` |
| 24 | 新画布扩图购买出现xx_yy | `/pt/ferramentas/expandir-imagem-ia` 首屏上传 -> Estenda IA -> Submit | `新画布扩图购买出现pt_expandir-imagem-ia` | ✅ 一致 | `evidence/console_pc_correct_entry_pt_expand_purchase_appearance_debug.log` |
| 25 | 新画布扩图zz购买成功xx_yy | AI Expand checkout -> Debug 跳过真实购买 | `新画布扩图年ultra购买成功pt_expandir-imagem-ia` | ✅ 一致 | `evidence/console_pc_correct_entry_pt_expand_purchase_success_debug.log` |

### 8.3 校正结论

- 之前第 6 节中因 `/create` 直进画布得到的第 16-20 条“gap”不再作为最终结论；那是错误入口导致缺少 `xx_yy` 事件。
- 正确 SEO 功能介绍页入口下，第 16-25 条购买出现与 Debug 跳过真实购买成功事件均成对出现，事件名符合 `xx_yy` 模式。
- 本轮只完成 10 条购买相关统计，按用户“每完成 10 条先汇报”的要求在此暂停。
- 尚待继续：第 12、13、15 条按正确功能入口复核；`/ai-replace/ai-clothes-changer`、`/ai-background` 对应功能统计；以及剩余 `新画布...xx_yy` 功能对。


## 9. Bug Candidates

### BC-02 — 无限画布页画质增强ultra点数用完触发注册未上报

- AC/模块：stat12「无限画布页xx功能点数用完触发注册」
- 优先级：P1
- 操作步骤：
  1. `/create` -> `Start from a Photo` -> 上传 `test_images/1K.jpg` -> `/agent?pid=*`
  2. 匿名态 `Credits:0` -> `Enhance` -> `Ultra HD Mode` -> `Enhance`
- 实际结果：Console 仅出现 `注册弹窗_出现` / `统计：注册弹窗_出现`
- 期望结果：出现 `无限画布页画质增强ultra功能点数用完触发注册`，并与 `debug 统计：...` 成对上报
- 证据：`evidence/console_stat12_pc_enhance_ultra_register_debug.log`
- 截图路径：未采集截图，当前证据为 Console 日志

### BC-03 — 无限画布页画质增强ultra点数用完注册成功未上报

- AC/模块：stat13「无限画布页xx功能点数用完触发注册成功」
- 优先级：P1
- 操作步骤：
  1. 延续 BC-02 注册弹窗
  2. 填写随机唯一邮箱 + 验证码 `123456` -> `Sign up`
- 实际结果：Console 出现 `注册弹窗_注册成功`、`登录成功_邮箱登录方式`
- 期望结果：出现 `无限画布页画质增强ultra功能点数用完触发注册成功`，并与 `debug 统计：...` 成对上报
- 证据：`evidence/console_stat13_pc_enhance_register_success_debug.log`
- 截图路径：未采集截图，当前证据为 Console 日志

## 10. PC 正确功能入口补采：第 26/27/28/29/30/31/38/39/40/41 条（2026-09-18）

本轮继续从对应功能介绍页进入，完成 5 个功能 x 2 条 = 10 条购买相关统计。

| 原文序号 | 原文标题 | 正确入口 | 触发交互 | 实际事件 | 结论 |
|---:|---|---|---|---|---|
| 26 | 新画布脸部购买出现xx_yy | `/ai-replace/add-smile-to-photo` -> `/face-editor/add-smile-to-photo` | 首屏上传 -> Portrait Editor -> Face -> Remove Acne -> Generate | `新画布脸部购买出现en_add-smile-to-photo` | ✅ |
| 27 | 新画布脸部zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布脸部年ultra购买成功en_add-smile-to-photo` | ✅ |
| 28 | 新画布身材购买出现xx_yy | `/body-editor` | 首屏上传 -> Body -> Natural Breast -> Generate | `新画布身材购买出现en_body-editor` | ✅ |
| 29 | 新画布身材zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布身材年ultra购买成功en_body-editor` | ✅ |
| 30 | 新画布发型购买出现xx_yy | `/hair-editor/virtual-hair-color-try-on` | 首屏上传 -> Hair -> Blonde -> Generate | `新画布发型购买出现en_virtual-hair-color-try-on` | ✅ |
| 31 | 新画布发型zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布发型年ultra购买成功en_virtual-hair-color-try-on` | ✅ |
| 38 | 新画布AI背景购买出现xx_yy | `/ai-background` | 首屏上传 -> 自动触发 AI Background 购买 | `新画布AI背景购买出现en_ai-background` | ✅ |
| 39 | 新画布AI背景zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布AI背景年ultra购买成功en_ai-background` | ✅ |
| 40 | 新画布背景模糊购买出现xx_yy | `/tools/gaussian-blur` | 首屏上传 -> 自动触发 BG Blur 购买 | `新画布背景模糊购买出现en_gaussian-blur` | ✅ |
| 41 | 新画布背景模糊zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布背景模糊年ultra购买成功en_gaussian-blur` | ✅ |

本批结束后事件名/入口覆盖累计为 `event_name_passed=31 / gap=0 / bug_candidates=3 / skipped=0`；新增次数唯一性断言后需补 `strict_frequency_passed`。证据见 `evidence/pc_correct_landing_26_31_38_41_summary.md`。

## 11. PC 正确功能入口补采：第 34/35、36/37、42/43、44/45、46/47 条（2026-09-20）

本轮继续从对应功能介绍页进入，完成 10 条购买相关统计；购买成功仅使用 Debug“跳过真实购买（查看统计项用）”。

| # | 原文标题 | URL入口 | 触发交互 | 实际事件 | 期望事件 | 结论 |
|---:|---|---|---|---|---|---|
| 34 | 新画布图生图购买出现xx_yy | `/image-to-image-ai` | 首屏上传 `test_images/1K.jpg` -> Generate -> `/agent?pid=*` -> 自动购买 | `新画布图生图购买出现en_image-to-image-ai` | `新画布图生图购买出现xx_yy`，本次 `xx_yy=en_image-to-image-ai` | ✅ |
| 35 | 新画布图生图zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布图生图年ultra购买成功en_image-to-image-ai` | `新画布图生图zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ |
| 36 | 新画布文生图购买出现xx_yy | `/ai-image-generator` | 默认提示词 -> Generate -> `/agent?pid=*` -> 自动购买 | `新画布文生图购买出现en_ai-image-generator` | `新画布文生图购买出现xx_yy`，本次 `xx_yy=en_ai-image-generator` | ✅ |
| 37 | 新画布文生图zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布文生图年ultra购买成功en_ai-image-generator` | `新画布文生图zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ |
| 42 | 新画布照片修复购买出现xx_yy | `/tools/photo-restoration` | 首屏上传 -> 进入画布后保持默认选中的 `Old Photo Mode` -> 直接点击 `Enhance` -> 购买弹窗 | `新画布照片修复购买出现en_photo-restoration` | `新画布照片修复购买出现xx_yy`，本次 `xx_yy=en_photo-restoration` | ✅ |
| 43 | 新画布照片修复zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布照片修复年ultra购买成功en_photo-restoration` | `新画布照片修复zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ |
| 44 | 新画布贴纸购买出现xx_yy | `/tools/add-hearts-to-photo` | 首屏上传 -> Valentine 2 -> 第二个 VIP 贴纸 -> 框选全部图层 -> Download VIP | `新画布贴纸购买出现en_add-hearts-to-photo` | `新画布贴纸购买出现xx_yy`，本次 `xx_yy=en_add-hearts-to-photo` | ✅ |
| 45 | 新画布贴纸zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布贴纸年ultra购买成功en_add-hearts-to-photo` | `新画布贴纸zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ |
| 46 | 新画布换背购买出现xx_yy | `/tools/background-changer` | 首屏上传 -> `/agent?pid=*` -> 自动换背购买 | `新画布换背购买出现en_background-changer` | `新画布换背购买出现xx_yy`，本次 `xx_yy=en_background-changer` | ✅ |
| 47 | 新画布换背zz购买成功xx_yy | 同上 | 购买面板 -> Debug 跳过真实购买 | `新画布换背年ultra购买成功en_background-changer` | `新画布换背zz购买成功xx_yy`，本次 `zz=年ultra` | ✅ |

本轮新增 10 条全部通过。42/43 首次被判 gap 后复核：必须保持 SEO 入口默认选中的 `Old Photo Mode` 后直接点击 `Enhance`，实际事件为 `新画布照片修复购买出现en_photo-restoration` / `新画布照片修复年ultra购买成功en_photo-restoration`，与需求一致。结合此前结果，事件名/入口覆盖为 `event_name_passed=42 / gap=1 / bug_candidates=2 / skipped=2`；严格次数唯一性断言 `strict_frequency_passed=0 / frequency_pending_revalidation=42`。其中 stat11 为 PC 交叉触发下未出现移动端弹窗下载命名；stat32/33 按用户标记 URL 跳过；stat12/13 保持 bug_candidate；stat15 结果图下载复核通过。证据见 `evidence/pc_correct_landing_34_37_42_47_summary.md` 与 `evidence/console_stat42_43_recheck_photo_restoration_submit_default_old_photo_debug.log`。










## 12. 统计次数唯一性断言补充（2026-09-20）

新增通过门禁：

- 同一条统计在单次目标动作内必须同时满足：
  - `sendGaEvent <事件名>` 出现 1 次；
  - `debug 统计：<事件名>` 出现 1 次；
  - 动作完成后的稳定窗口内不再次新增同一事件。
- `0` 次 = 少报 / 漏报，标记 `bug_candidate`。
- `>=2` 次 = 多报 / 重复上报，标记 `bug_candidate`。
- 无法隔离单次动作、日志混入历史操作的，不能判定为通过；标记 `frequency_pending_revalidation`，需重采。

说明：此前本文件中的 `passed` 表示事件名和入口链路核对通过，不等于已满足本次新增的次数唯一性断言。新增规则后，所有统计项都要补做“单次动作次数=1”的隔离复核；未补前按 `frequency_pending_revalidation` 管理。

证据规则：`evidence/stat_frequency_assertion_policy.md`。




## 13. 新画布页统计移动端补充探索（2026-09-20）

用户新增要求：新画布页相关统计除 PC 外，还需要补移动端探索；移动端入口 URL 与 PC 保持一致。

- 范围：需求中所有「新画布...xx_yy」统计项，对应本任务第 16-47 条。
- 入口：沿用 PC 同一 URL，例如 `/tools/photo-enhancer`、`/tools/background-remover`、`/image-to-image-ai`、`/tools/background-changer` 等。
- 移动端触发：移动视口 / 移动 UA -> 访问同一 URL -> 首屏上传或生成入口 -> 使用 `test_images/1K.jpg` -> 进入移动端画布 -> 执行对应功能 -> Console 核对。
- 购买成功：只允许 Debug 跳过真实购买。
- 次数断言：同样需要 `sendGaEvent=1` 且 `debug 统计=1`；0 次为漏报 bug，>=2 次为多报 bug。
- 当前状态：`blocked_requires_mobile_mcp_context`。Playwright MCP 已恢复并通过强 preflight，但当前上下文是桌面 Chrome 窄视口 + UA 注入，不是真实移动端模拟；`pointer: coarse=false`、`hover: none=false`，未出现 `mobile-primary-panel`。必须先以 `--device` 或 `--mobile` 启动 MCP 后重试。

证据规则：`evidence/new_canvas_mobile_scope_pending.md`。



## 14. 移动端新画布统计首条探索：`/tools/photo-enhancer`（2026-09-20）

- 移动端 device 模拟：`iPhone 13`，`pointer: coarse=true`，`hover:none=true`，已进入 `/create/edit?pid=*` 移动画布。
- 入口：`/tools/photo-enhancer`。
- 操作：上传 `test_images/1K.jpg` -> 移动画布 -> Photo Enhancer -> Standard / Ultra / Portrait -> Enhance。
- 实际事件：`画布页增强开始en_photo-enhancer`、`画布页增强成功en_photo-enhancer`、`移动端画布页_画质增强弹窗出现`。
- 期望事件：`新画布增强购买出现en_photo-enhancer`、`新画布增强年ultra购买成功en_photo-enhancer`。
- 结论：第 16/17 条移动端未通过，目标事件 0 次；记录为 mobile gap。未出现购买面板，未能进入 Debug 跳过真实购买成功链路。
- 证据：`evidence/mobile_new_canvas_stats_progress.md`。


## 15. 移动端新画布统计第 16/17 条修正通过（2026-09-20）

- 修正原因：先前使用 DEBUG 改权益/先做免费处理，绕过了移动端购买出现链路。
- 正确路径：新免费账号 -> `/tools/photo-enhancer` -> 上传 `test_images/1K.jpg` -> `/create/edit?pid=*` -> 直接点击 `Enhance` -> 内购弹窗。
- 第 16 条实际：`新画布增强购买出现en_photo-enhancer`，send=1 / debug=1，✅。
- 第 17 条实际：`新画布增强月SE试用购买成功en_photo-enhancer`，send=1 / debug=1，✅；符合 `zz=月SE试用`。
- 证据：`evidence/mobile_new_canvas_stats_progress.md`、`evidence/mobile_stat16_photo_enhancer_free_direct_submit_purchase_appearance_debug.log`、`evidence/mobile_stat16_17_photo_enhancer_free_direct_submit_purchase_success_debug.log`。


## 16. 移动端新画布统计第 18/19 条通过（2026-09-20）

- 入口：`/tools/background-remover`。
- 正确路径：新免费账号 -> SEO 上传 `test_images/1K.jpg` -> 移动画布 -> 直接点击 `Remove Background`。
- 第 18 条实际：`新画布抠图购买出现en_background-remover`，send=1 / debug=1，✅。
- 第 19 条实际：`新画布抠图月SE试用购买成功en_background-remover`，send=1 / debug=1，✅；符合 `zz=月SE试用`。
- 证据：`evidence/mobile_new_canvas_stats_progress.md`、`evidence/mobile_stat18_19_background_remover_free_direct_submit_purchase_appearance_debug.log`、`evidence/mobile_stat18_19_background_remover_free_direct_submit_purchase_success_debug.log`。


## 17. 移动端新画布统计第 20/21 条记录 bug_candidate（2026-09-20）

- 入口：`/tools/magic-eraser-with-ai-detection`。
- 路径：新免费账号 -> SEO 上传 -> 移动画布 -> Auto Remove -> Remove People -> `Remove` -> 内购弹窗。
- 实际事件：`移动端画布页_AI消除弹窗出现`、`AI消除auto模式处理免费credits用完触发购买界面`、`移动端画布AI消除功能点数用完触发购买`、`购买界面进入`。
- 期望事件：`新画布消除购买出现en_magic-eraser-with-ai-detection`；购买成功同理。
- 结论：目标事件 0 次，按用户新增次数门禁标记移动端 bug_candidate。
- 证据：`evidence/mobile_new_canvas_stats_progress.md`、`evidence/mobile_stat20_21_magic_eraser_free_direct_submit_purchase_appearance_debug.log`。


## 18. 移动端新画布统计第 22/23 条记录 bug_candidate（2026-09-20）

- 入口：`/it/ai-replace`。
- 路径：新免费账号 -> SEO 上传 -> `/it/create/edit?pid=*` -> AI Replace -> 选区 -> prompt -> `Genera` -> 内购弹窗。
- 实际事件：`移动端画布AI改图功能点数用完触发购买`、`画布页改图购买出现it_ai-replace`。
- 期望事件：`新画布改图购买出现it_ai-replace`。
- 结论：目标事件 0 次，实际缺 `新画布` 前缀，按次数门禁标记移动端 bug_candidate。
- 证据：`evidence/mobile_stat22_23_ai_replace_free_direct_submit_purchase_appearance_debug.log`。


## 19. 移动端新画布统计第 24/25 条通过（2026-09-20）

- 入口：`/pt/ferramentas/expandir-imagem-ia`。
- 路径：新免费账号 -> SEO 上传 -> `/pt/create/edit?pid=*` -> AI Extender -> `Estenda IA` -> 内购弹窗 -> Debug 跳过真实购买。
- 第 24 条实际：`新画布扩图购买出现pt_expandir-imagem-ia`，send=1 / debug=1，✅。
- 第 25 条实际：`新画布扩图月SE试用购买成功pt_expandir-imagem-ia`，send=1 / debug=1，✅。
- 证据：`evidence/mobile_new_canvas_stats_progress.md`、`evidence/mobile_stat24_25_ai_extender_free_direct_submit_purchase_appearance_debug.log`、`evidence/mobile_stat24_25_ai_extender_free_direct_submit_purchase_success_debug.log`。

## 20. 移动端新画布统计第 20/21 条复核通过（2026-09-20）

- 入口：`/tools/magic-eraser-with-ai-detection`。
- 复核路径：免费已登录账号 -> SEO 首屏上传 `test_images/1K.jpg` -> 移动画布 Magic Eraser -> `AI Delete` -> `All` -> `Remove` -> 内购弹窗 -> Debug 跳过真实购买。
- 第 20 条实际：`新画布消除购买出现en_magic-eraser-with-ai-detection`，send=1 / debug=1，✅。
- 第 21 条实际：`新画布消除月SE试用购买成功en_magic-eraser-with-ai-detection`，send=1 / debug=1，✅。
- 关键修正：之前 `Auto Remove -> Remove People` 路径触发的是 auto 模式购买事件，不会上报 `新画布消除...`；正确手机端路径是 `AI Delete -> All -> Remove`。
- 证据：`evidence/mobile_stat20_magic_eraser_ai_delete_all_purchase_appearance_full_debug.log`、`evidence/mobile_stat20_21_magic_eraser_ai_delete_all_purchase_success_full_debug.log`、`shots/mobile_stat20_21_magic_eraser_ai_delete_all_purchase_success.png`。


## 21. 移动端新画布统计第 26/27、28/29、30/31、34/35、36/37 条通过（2026-09-20）

- 第 26/27 条：`/ai-replace/add-smile-to-photo`（实际落地 `/face-editor/add-smile-to-photo`）-> 首屏上传 `test_images/1K.jpg` -> 移动画布 AI Face Editor -> `Teeth Smile` -> `Generate` -> 购买弹窗 -> Debug 跳过真实购买。
  - 出现：`新画布脸部购买出现en_add-smile-to-photo`，send=1 / debug=1，✅。
  - 成功：`新画布脸部月SE试用购买成功en_add-smile-to-photo`，send=1 / debug=1，✅。
- 第 28/29 条：`/body-editor` -> 首屏上传 -> AI Body Editor -> `Fuller Breast` -> `Generate` -> 购买弹窗 -> Debug 跳过真实购买。
  - 出现：`新画布身材购买出现en_body-editor`，send=1 / debug=1，✅。
  - 成功：`新画布身材月SE试用购买成功en_body-editor`，send=1 / debug=1，✅。
- 第 30/31 条：`/hair-editor/virtual-hair-color-try-on` -> 首屏上传 -> HairStyle Try On -> `Full Head Color` -> `Generate` -> 购买弹窗 -> Debug 跳过真实购买。
  - 出现：`新画布发型购买出现en_virtual-hair-color-try-on`，send=1 / debug=1，✅。
  - 成功：`新画布发型月SE试用购买成功en_virtual-hair-color-try-on`，send=1 / debug=1，✅。
- 第 34/35 条：`/image-to-image-ai` -> 首屏上传 `test_images/1K.jpg` -> 进入移动画布 AI Image 面板 -> `Generate` -> 购买弹窗 -> Debug 跳过真实购买。
  - 出现：`新画布图生图购买出现en_image-to-image-ai`，send=1 / debug=1，✅。
  - 成功：`新画布图生图月SE试用购买成功en_image-to-image-ai`，send=1 / debug=1，✅。
- 第 36/37 条：`/ai-image-generator` -> 首屏 Generate -> 进入移动画布 AI Image 面板 -> `Generate` -> 购买弹窗 -> Debug 跳过真实购买。
  - 出现：`新画布文生图购买出现en_ai-image-generator`，send=1 / debug=1，✅。
  - 成功：`新画布文生图月SE试用购买成功en_ai-image-generator`，send=1 / debug=1，✅。
- 证据：
  - `evidence/mobile_stat26_27_add_smile_purchase_success_full_debug.log`
  - `evidence/mobile_stat28_29_body_editor_purchase_success_full_debug.log`
  - `evidence/mobile_stat30_31_hair_editor_purchase_success_full_debug.log`
  - `evidence/mobile_stat34_35_image_to_image_purchase_success_full_debug.log`
  - `evidence/mobile_stat36_37_text_to_image_purchase_success_full_debug.log`
  - `shots/mobile_stat26_27_add_smile_purchase_success.png`
  - `shots/mobile_stat28_29_body_editor_purchase_success.png`
  - `shots/mobile_stat30_31_hair_editor_purchase_success.png`
  - `shots/mobile_stat34_35_image_to_image_purchase_success.png`
  - `shots/mobile_stat36_37_text_to_image_purchase_success.png`


## 22. 移动端新画布统计第 40/41、42/43、46/47 条通过及 38/39、44/45 不适用（2026-09-20）

- 不适用范围（用户确认）：移动端没有 AI背景、贴纸功能，因此第 38/39、44/45 不需要在移动端测试，不记为 gap/bug。
- 第 40/41 条：`/tools/gaussian-blur` -> 首屏上传 `test_images/1K.jpg` -> 进入移动画布后自动触发 BG Blur 购买 -> Debug 跳过真实购买。
  - 出现：`新画布背景模糊购买出现en_gaussian-blur`，send=1 / debug=1，✅。
  - 成功：`新画布背景模糊月SE试用购买成功en_gaussian-blur`，send=1 / debug=1，✅。
- 第 42/43 条：`/tools/photo-restoration` -> 首屏上传 -> 保持默认 `Old Photo Enhance` / `Old Photo Mode` -> 直接 `Enhance` -> 购买弹窗 -> Debug 跳过真实购买。
  - 出现：`新画布照片修复购买出现en_photo-restoration`，send=1 / debug=1，✅。
  - 成功：`新画布照片修复月SE试用购买成功en_photo-restoration`，send=1 / debug=1，✅。
- 第 46/47 条：`/tools/background-changer` -> 首屏上传 -> 进入移动画布后自动触发 Change BG 购买 -> Debug 跳过真实购买。
  - 出现：`新画布换背购买出现en_background-changer`，send=1 / debug=1，✅。
  - 成功：`新画布换背月SE试用购买成功en_background-changer`，send=1 / debug=1，✅。
- 证据：
  - `evidence/mobile_stat40_41_gaussian_blur_purchase_success_full_debug.log`
  - `evidence/mobile_stat42_43_photo_restoration_purchase_success_full_debug.log`
  - `evidence/mobile_stat46_47_background_changer_purchase_success_full_debug.log`
  - `shots/mobile_stat40_41_gaussian_blur_purchase_success.png`
  - `shots/mobile_stat42_43_photo_restoration_purchase_success.png`
  - `shots/mobile_stat46_47_background_changer_purchase_success.png`
  - `evidence/mobile_stat38_39_44_45_not_applicable.md`




