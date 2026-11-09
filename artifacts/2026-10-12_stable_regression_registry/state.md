---
task_id: 2026-10-12_stable_regression_registry
agent: orchestrator
status: completed
current_step: archived
execution_mode: codex_single_context
task_type: stable_regression
human_gates_pending: []
knowledge_context: artifacts/2026-10-12_stable_regression_registry/knowledge-ledger.yaml
handoff_status: archived
knowledge:
  prefetch_status: completed
  prefetch_ids: [KB-RULE-0009, KB-RULE-0008, KB-RULE-0006, KB-PITFALL-0005]
  runtime_ids: []
  exception_ids: []
  unresolved_conflicts: []
  retrieval_ledger: artifacts/2026-10-12_stable_regression_registry/knowledge-ledger.yaml
  notes:
    - KB-RULE-0009 use_as=rule_candidate（工具栏只开面板，主提交按钮才发起任务）——已编码在 canvas 类 confirmed 脚本内，本轮不改断言。
    - KB-RULE-0008 use_as=expected_candidate（Magic Eraser Quick Select 未检测到物体属正常）——同上，仅作结果判读参考。
    - KB-RULE-0006 use_as=rule_candidate（新用户促销弹窗先于内购弹窗）——同上。
    - KB-PITFALL-0005 use_as=retry_hint（SEO 落地页 502/504 或入口未挂载先同 URL 重试一次）——仅在失败归因时参考。
  budget:
    init_queries_remaining: 0
    runtime_queries_remaining: 6
    exception_queries_remaining: 3
agent_call_count:
  page-map-sync: 1
  test-case-design: 0
  test-writing: 0
  review: 0
  visual-review: 0
created_at: 2026-10-12 10:00:00
requirement_doc: artifacts/regression_registry.md
target_url: http://10.17.1.66:3001/
entry_url: http://10.17.1.66:3001/
entry_path: /
scope: 复跑 regression_registry.md 中 URL 登记为 http://10.17.1.66:3001 的 stable_regression 条目 Tests 列当前脚本，共 12 个 suite
stop_at: sync_review
exploration_driver: playwright_mcp_only
diagnostic_driver: none
device_context:
  platform: desktop
  viewport: 1920x1080
  note: PC 任务按各 suite 内既有 device/viewport 配置执行；移动端 suite 使用其自身登记口径
  mcp_preflight: 2026-10-12 14:55 browser_navigate http://10.17.1.66:3001/ -> /create 成功
  verified_pc_context:
    innerWidth: 1920
    innerHeight: 1080
    devicePixelRatio: 1
    userAgent: HeadlessChrome/154 Windows
    hasTouch: false
    ontouchstart: false
viewport_guard_status: passed
forbidden: 全量探索、修改断言、弱化预期、上传 test_images/ 以外素材、自动修改脚本
assets: 账号按各任务 confirmed artifact 与 PROJECT.md；素材 test_images/；环境 http://10.17.1.66:3001/
assumptions:
  - 用户要求按 regression_registry.md 在本环境跑回归，因此执行 Tests 列当前可执行脚本。
  - 仅纳入 URL 列登记为 10.17.1.66:3001 的 stable_regression 条目；dev 域条目（detection_ui_seo_l6 / pc_home_v6 / pc_batch_v1）与 pending_fix 条目（infinite_canvas_enhance_v4）排除。
  - 串行执行，单个 suite 失败不阻断后续；仅报告结果，不自动修脚本/断言，漂移只在报告中标注候选回退。
artifacts:
  runner: artifacts/2026-10-12_stable_regression_registry/run_registry_regression.py
  builder: artifacts/2026-10-12_stable_regression_registry/build_report.py
  logs: artifacts/2026-10-12_stable_regression_registry/regression/
  manifest: artifacts/2026-10-12_stable_regression_registry/run_manifest.json
  summary: artifacts/2026-10-12_stable_regression_registry/regression/summary.json
  report: artifacts/2026-10-12_stable_regression_registry/report.md
  page_map_v3: page_map/pokecut/infinite_canvas_text_layer_v3.yaml
  page_map_v12: page_map/pokecut/mobile_canvas_v12.yaml
  page_map_v4: page_map/pokecut/ai_image_text_enhancer_v4.yaml
  sync: artifacts/2026-10-12_stable_regression_registry/sync.md
  exploration_report: artifacts/2026-10-12_stable_regression_registry/exploration_report.md
  automation_handoff: artifacts/2026-10-12_stable_regression_registry/evidence/automation_handoff.yaml
  archive: artifacts/2026-10-12_stable_regression_registry/archive.md
  archive_cleanup_manifest: artifacts/2026-10-12_stable_regression_registry/archive_cleanup_manifest.json
  allure_results: reports/allure-results-regression
  allure_report: reports/allure-report-regression
next_step: 归档完成（方案 A）。剩余 2 条未处理失败（test_l2_011 PC+移动端，/tools/zoom-in-photos 服务端容量限流，环境态，用户指示不处理）；新增 1 个已知产品缺陷 BUG-2026-1012-01（换背事件不发，P-NEW-16 / M-NEW-14 已标 xfail）。归档副本全量复跑按用户指示跳过，仅做 collect-only + 路径解析校验。
blockers:
  - id: env_playwright_socketpair_unavailable_resolved
    resolution: 用户 2026-10-12 选择方案 B；已在 conftest.py 注入宽松 socketpair（优先原生、仅 ConnectionError 时回退），冒烟用例 test_l1_001_layout_and_hero passed
    detected_at: 2026-10-12 17:25
    detail: python socket.socketpair() 全局抛 ConnectionError('Unexpected peer connection')，导致 asyncio ProactorEventLoop 无法创建，所有 Playwright pytest 用例在 setup 阶段报 ERROR；与本次代码改动无关（同一命令 17:20 前正常）。                loopback TCP connect 正常，怀疑安全软件 / VPN / 代理驱动劫持了 loopback socketpair。    impact: 无法继续执行 pytest 验证（M-CORE-03 及 B/C/D/E 组）。Playwright MCP（独立进程）不受影响。
    root_cause: Proxifier（PID 17768，C:\Program Files (x86)\Proxifier\Proxifier.exe）拦截 loopback 连接并改写源端口，
      导致 Python socket.socketpair 的身份校验 ssock.getsockname() != csock.getpeername() 失败。
      实测：服务端 accept 到 127.0.0.1:61158，客户端本地为 127.0.0.1:61156（不一致）。
      因 Windows 无 _socket.socketpair / AF_UNIX，Python 只能走 _fallback_socketpair（带校验），故必然失败。
    verified_workaround: 用宽松版 socketpair（跳过对端校验）打补丁后，ProactorEventLoop 创建成功、Playwright 启动并成功打开
      http://10.17.1.66:3001/（标题 Pokecut: Free Online AI Photo Editor & Image Generator），数据通路正常。
    side_effect_hypothesis: Proxifier 同时改变出口 IP，可能影响按 IP 判定的免费额度与限流，
      或与 SEO L2-011 的 'Processing failed / 30 分钟后再试' 及 F3 免费/付费态抖动相关（待验证，不作为断言依据）。
---
# 调度历史
- 2026-10-12 10:00:00 orchestrator route: stable_regression / run registry Tests-column scripts on http://10.17.1.66:3001
- 2026-10-12 12:24:36 orchestrator suite timeout: test_canvas_stats_all 达 5400s 上限（完成 35/40）
- 2026-10-12 14:14:00 orchestrator residual rerun: 补跑 M-NEW-10..14（5 failed），40 条结果完整
- 2026-10-12 14:20:00 orchestrator wrote artifact: report.md + summary.json
- 2026-10-12 14:22:00 orchestrator gate: 稳定回归报告输出完成，Allure 报告 http://localhost:8123/index.html
- 2026-10-12 14:55:00 orchestrator user_decision: 用户选择方案 A —— 对 3 个疑似漂移族做局部复探后回退修脚本
- 2026-10-12 14:55:00 orchestrator route: stable_regression 局部回退 -> page-map-sync (repair_scope=selector_drift)，授权来源=用户方案 A 选择
- 2026-10-12 14:55:00 page-map-sync start: MCP preflight passed (browser_navigate 成功)，viewport_guard passed
- 2026-10-12 14:55:00 page-map-sync start: driver=playwright_mcp_only, MCP preflight passed, viewport_guard passed
- 2026-10-12 15:10:00 page-map-sync step: mcp_action 复探 F1(/create 入口卡 + /agent 画布文字面板) / F2(移动端注册入口 + 购买弹窗链路) / F3(文字增强点数矩阵)
- 2026-10-12 15:20:00 page-map-sync wrote: page_map v3/v12/v4 + sync.md + exploration_report.md + evidence/automation_handoff.yaml
- 2026-10-12 15:30:00 page-map-sync gate: exploration_review（sync.md pending_review，handoff pending_review，validate_automation_handoff passed）
- 2026-10-12 15:45:00 orchestrator user_confirmation: D3 点数规则为用户确认的预期变更；sync.md -> confirmed, handoff -> ready_for_case_design
- 2026-10-12 15:45:00 orchestrator scope_update: F2 范围由 11 扩为 16（含 M-CORE-06/07 pro 登录同源失败）
- 2026-10-12 15:45:00 orchestrator recorded: 未处理失败 10 条清单写入 sync.md §7
- 2026-10-12 16:10:00 test-writing fix F1: 入口 card -> button[data-tool-id='start-photo']；Rotate 断言 -> button.rotation-button[aria-label='Rotation']
- 2026-10-12 16:20:00 test-writing verify F1: 6 passed（原 0/6）
- 2026-10-12 16:25:00 test-writing fix F2: 移动端注册 -> credits 面板 button.credits-entry__signup；取消 except Exception: pass，补注册弹窗/关闭判据
- 2026-10-12 16:40:00 test-writing fix F3: 15 处 expected 按新规则更新（base 5/5/10，附加效果 +5，非增强单效果 5）
- 2026-10-12 17:00:00 test-writing verify F3: 15 passed / 3 skipped（原 6 passed / 9 failed）
- 2026-10-12 17:05:00 test-writing verify F2: 17 条移动端定向复跑运行中
- 2026-10-12 17:20:00 test-writing fix A verified: P-INF-02 passed, P-INF-03 passed（选 Ultra HD Mode）
- 2026-10-12 17:20:00 test-writing fix M-CORE-03 attempt: 主提交按钮改 button.mobile-ai-expand-generate-button -> 仍失败（购买弹窗关闭后回到工具卡的面板状态问题，待查）
- 2026-10-12 17:25:00 orchestrator blocked: 环境 socket.socketpair 失败，Playwright pytest 无法启动，验证暂停
- 2026-10-12 17:40:00 orchestrator user_decision: 选择方案 B（保留代理 + conftest 补丁）
- 2026-10-12 17:42:00 test-writing wrote: conftest.py 注入 _install_lenient_socketpair（回环代理兼容）
- 2026-10-12 17:43:00 test-writing verify: tests/test_help_page.py::TestL1PageStructure::test_l1_001_layout_and_hero 1 passed -> Playwright 恢复
- 2026-10-12 18:10:00 test-writing fix M-CORE-03: close_purchase_modal 循环关闭促销/内购链式弹窗
- 2026-10-12 18:12:00 test-writing verify M-CORE-03: 1 passed
- 2026-10-12 18:20:00 page-map-sync 复探 C/D/E: 匿名会话新增 Sign Up 弹窗遮挡为共性根因；L2-005 落地页改版；D 组非限流
- 2026-10-12 18:25:00 orchestrator recorded: 剩余未处理项清单见 sync.md §10
- 2026-10-12 18:40:00 test-writing verify final: F1 6/6（1 次抖动复跑通过）、F3 15/3（1 次生成超时复跑通过）、F2 15 passed
- 2026-10-12 18:45:00 orchestrator done: 本轮稳定回归修复与验证收尾，未处理 7 项写入 sync.md §11
- 2026-10-12 19:20:00 page-map-sync/user_feedback: 用户指出 P-NEW-03 产品确实发消除事件 -> 复核确认是用例误点（Remove 命中 Remove BG）
- 2026-10-12 19:30:00 test-writing fix: run_actions 新增 click_exact；P-NEW-03 actions 改为 [{click_exact: All}]
- 2026-10-12 19:35:00 test-writing verify: test_p_new_03 1 passed
- 2026-10-12 19:40:00 page-map-sync recheck: P-NEW-16/M-NEW-14 非误点（actions 为空），购买弹窗在进画布时自动弹出致 新画布换背购买出现 不产生，仍待产品确认
- 2026-10-12 20:10:00 test-writing fix+verify M-CORE-02: enhance 分支补选 Ultra HD Mode -> 1 passed
- 2026-10-12 20:20:00 test-writing fix+verify L3-004: login_vip 改用 credits 胶囊注册入口 -> 1 passed
- 2026-10-12 20:40:00 page-map-sync verify: L2-011(PC) 实测为服务端容量限流 Tips 弹窗（修正 §10 结论）；L2-006 匿名注册弹窗遮挡；L2-005 落地页改版
- 2026-10-12 20:45:00 orchestrator: 剩余失败收敛为 6 条（换背 2 / L2-011 2 / L2-006 1 / L2-005 1）
- 2026-10-12 21:10:00 user_feedback: 移动端注册/登录入口在顶部栏最右侧汉堡按钮的右侧栏；两条用例需登录会员账号
- 2026-10-12 21:20:00 test-writing fix: conftest login_mobile 改为 汉堡img[nav_btn_mun.svg] -> div.menu-tab -> Log in -> 填表提交（旧 Sign up 兜底，不再静默 return）
- 2026-10-12 21:25:00 test-writing verify: L2-006 passed；L2-005 passed（更正前判「落地页改版」）
- 2026-10-12 21:30:00 test-writing verify: L2-011(移动) 仍失败 -> 服务端 30 分钟容量限流 Tips 弹窗，环境态
