task_id: 2026-11-04_regression_report_governance
task_type: single_agent
execution_mode: codex_single_context
scope: P0_baseline_result_contract_reporting_quarantine_compatibility
status: p3_completed
current_step: p3_all_20_suites_converted_verified_awaiting_regression_run
created_at: '2026-11-04'
updated_at: '2026-11-08'
base_commit: a747b97a4b126ecc55b6bab181b345d9cb774f0d
artifacts:
  state: artifacts/2026-11-04_regression_report_governance/state.md
  progress: artifacts/2026-11-04_regression_report_governance/progress.log
  case_id_audit: artifacts/2026-11-04_regression_report_governance/evidence/case_id_audit.json
  quarantine_registry: artifacts/regression_quarantine.yaml
deliverables:
  - regression_governance.py
  - scripts/regression_summary.py
  - scripts/regression_runner.py
  - scripts/audit_case_ids.py
  - tests/test_regression_governance.py
  - run_regression_3001.py
  - run_regression_3002.py
  - artifacts/regression_quarantine.yaml
  - artifacts/runtime/common.md
  - artifacts/runtime/orchestrator.md
  - README.md
review_round_1:
  verdict: changes_required
  blocking_found: 3
  resolved:
    - B1 teardown/setup failure must classify as broken, never clean_pass
    - B2 case_id coverage must be computed from a real resolved flag
    - B3 case_id must come from an authoritative source, not title/name guessing
post_review_fixes:
  - regression_governance._case_id narrowed to @allure.label("case_id") only
  - regression_summary._classify added setup/teardown failed -> broken branch
  - regression_summary.case_id_resolved flag + honest coverage
  - regression_summary recovers ALLURE case_id label at runtime (dynamic label gap)
  - audit_case_ids distinguishes static marker / dynamic runtime / true debt
  - tests/test_regression_governance.py expanded to 7 checks
verification:
  self_check: 11 passed
  collect_only: 571 collected
  validate_skills: 5/5 PASS
  case_id_audit:
    label_marker: 56
    dynamic_runtime: 47
    title_derivable: 204
    missing: 264
  registry_20_suites:
    total_cases: 314
    resolvable: 314
    note: 02/10 suites use dynamic titles; resolved at runtime from Allure JSON
deliverables_p1:
  - scripts/case_id_rules.py
  - scripts/regression_summary.py (case_id_source + title extraction)
  - scripts/audit_case_ids.py (title_derivable classification)
  - tests/test_infinite_canvas_text_layer_v2.py (6 explicit TC-TEXT labels)
  - tests/test_regression_governance.py (11 checks)
design:
  case_id_precedence: label marker > Allure case_id label > strict title extraction > MISSING
  namespacing: short ids (L2-001) become <SUITE>-L2-001 (e.g. MH-L2-001)
  guardrail: unknown titles stay MISSING, never guessed
known_issues:
  - PC SEO and mobile SEO both use L2-001..L2-024 as label values (pre-existing collision, not fixed)
next_steps:
  - P1 gate wiring into release flow
  - P2 failure triage / flaky registry
  - P3 replace fixed waits
  - P4 parallel only after isolation metadata

deliverables_p2:
  - scripts/flaky_report.py
  - scripts/quarantine.py
  - artifacts/runtime/common.md (失败分流与 flaky 治理)
  - artifacts/runtime/orchestrator.md (flaky classification + --)
  - tests/test_regression_governance.py (13 checks)
p3_batch2_completed:
  note: user asked to stop after these two suites and report progress
  suites:
    - tests/test_agent_batch_edit_panel.py (8 -> 0, 15 passed in 322.14s)
    - tests/test_infinite_canvas_sticker_v1.py (18 -> 0, 4 passed / 1 pre-existing fail; failure reproduced on unfixed archive copy and matches registry-known missing thumbnails)
    - tests/test_infinite_canvas_text_layer_v2.py (36 -> 0, 3 representative cases passed; full suite not run)
    - tests/test_old_canvas_text_panel_v1.py (31 -> 0, 13 passed in 151.95s)
    - tests/test_old_canvas_sticker_panel_v1.py (39 -> 0, 9 passed in 207.25s)
p3_remaining:
  count_scripts: 8
  count_fixed_waits: 317
  scripts:
    - tests/test_ai_image_text_enhancer_experiment.py (26)
    - tests/test_detection_ui_seo_l6.py (10)
    - tests/test_old_canvas_insert_panel_v3.py (88)
    - tests/test_infinite_canvas_enhance_v4.py (18)
    - tests/test_create_chat_to_edit_auto_v1.py (9)
    - tests/test_canvas_stats_all.py (102)
    - tests/test_old_canvas_ai_tools_all.py (40)
    - tests/test_create_chat_to_edit_model_matrix_v1.py (24)
p3_completion:
  scope: registry 20 suites, fixed wait_for_timeout replacement only
  total_before: 557
  total_after: 21
  remaining_note: all 21 are bounded poll/retry intervals or CDP touch-stream framing, each annotated
  verification:
    py_compile: 40/40 OK (20 live + 20 archive)
    collect_only: live 314 / archive 314
    validate_skills: 5/5 PASS
    governance_self_check: 13 passed
  archive_sync: 18/20 byte-identical; 2 differ only by intended _repo_root block
p3_progress:
  scope: registry 20 suites, fixed wait_for_timeout replacement only
  batch1_no_credits:
    - tests/test_help_page.py (9 -> 0, 11 passed in 78.11s before this session)
    - tests/test_pokecut_pc_batch_v1.py (4 -> 0, 10 passed in 57.21s)
    - tests/test_pokecut_pc_home_v6.py (33 -> 0, 17 passed in 152.76s)
    - tests/test_pokecut_portrait_detector.py (23 -> 0, 14 passed in 132.70s on rerun)
    - tests/test_mobile_home.py (33 -> 0, anonymous subset 35 passed/1 failed; the 1 failure L2-008/reproduced on unfixed archive copy = pre-existing baseline drift)
    - tests/test_seo_main_upload_interactions_v1.py (7 -> 0, NOT executed: registry marks every case as credit-consuming)
    - tests/mobile/test_seo_main_upload_mobile_v1.py (8 -> 0, NOT executed: registry marks every case as credit-consuming)
  helper:
    - helpers/waiting.py: wait_ready / wait_visible / wait_attached / wait_url_contains / wait_network_quiet / settle / poll_until
  notes:
    - archive copies resynced for all 7 batch-1 suites that have archive dirs
    - settle() only used for reverse assertions (no positive observable) and login/gateway backoff, each commented
p2_verification:
  flaky_verdicts: stable_pass / flaky / new_fail / fixed / stable_fail / insufficient
  quarantine_lifecycle: add / list / extend / release / audit all verified
  needs_action: excludes fixed cases

p3_followup_remediation:
  date: '2026-11-08'
  scope: ai_image_text + old_canvas_ai_tools (regressions introduced/exposed by P3)
  ai_image_text: 8F/5P/1S/4E -> 16 passed / 2 skipped (all green)
  old_canvas_ai_tools: 4P/2F -> 6/6 reachable pass (P-AIT-01 1157s PASS, P-AIT-02 incl Manual PASS)
  fixed_root_causes:
    - _goto lost fixed-7s slack -> DEBUG panel / upload readiness raced (P3-introduced)
    - _upload waited data-effect but not image-size parse (NaN transition) (P3-introduced)
    - preset click swallowed -> main button still disabled at submit (P3-amplified)
    - wait_done_settled discarded wait_preview_stable return -> false-end in 0.5s (pre-existing, amplified by P3)
    - Manual Mode completion uses console 生成成功; main button stays disabled after generate (pre-existing)
    - dismiss_blockers now covers server-busy / network-error dialogs (pre-existing)
  verification:
    governance_self_check: 13 passed
    validate_skills: 5/5 PASS
    py_compile: OK
    live_archive_identical: true
  summary_doc: reports/p3_full_regression/SUMMARY_P3_FOLLOWUP_2026-11-08.md

p3_followup_round2:
  date: '2026-11-08'
  scope: 产品漂移修脚本 + 门禁可用性增强 + flaky 自动分类
  product_drift_fixes:
    seo_l2_008: 22 个 SEO 页仅此页改版（seo-first-screen-upload-button -> Change Clothes in Photo）；只改该条 main_selector；验证 1 passed
    enhance_l1: 产品新增 Low-Res Mode（面板行 5->6）；Low-Res/Old Photo 不展示分辨率控件；L1-001/L1-002 passed
    enhance_pro_context: 修登录判据假阳性（/Credits|User/ 未登录首页即命中，0.9s 误判）-> 改「登录入口消失 + User8JY」
  credit_rule_change_2026_11_08_user_confirmed:
    matrix_vip: "Standard/Portrait/Text 2k=Free 4k=Free 8k=10; Ultra 2k=10 4k=10 8k=15; 4K图 Ultra 8k=15"
    data_changes: ultra_4k 4->10, standard_8k 2->10, portrait_8k 2->10, text_8k 4->10, ultra_8k 6->15, ultra_8k_from_4k 6->15
    availability: 所有原图尺寸 2k/4k/8k 均可用（不再有禁用档 + over N K toast）；data controls 全 false + 用例 disabled_res 全 None
  runner_enhancements:
    per_suite_verdict: 每套件跑完立即打印 VERDICT [ok|BLOCKING] + 状态计数 + 阻塞清单（复用 _classify 保持口径一致）
    fail_fast: --fail-fast 触线即停，结束打印 NOT RUN 清单
    auto_flaky_retry: --auto-flaky-retry（默认开）失败用例自动定向复跑一次；全过=>FLAKY，否则=>稳定失败
    isolation: 复跑用独立 run_id + attempt log，避免污染主判定
    verified: VERDICT 行 / fail-fast / 全过不触发复跑 三项均验证通过
  enhance_v4_final_state:
    result: 4 passed / 2 failed（L1 + L5 + L6-001 通过）
    remaining_failures: L6-002 / L6-003 = 产品侧模型失败（console: 画质增强XXX模型失败 / 处理失败_网络错误），复跑仍失败 -> 稳定失败，非脚本问题，非 flaky
    note: 扣点断言问题已修复（不再出现「扣点不符」）
  decision_log:
    ci_gate: 用户确认当前是「手动在 agent 里让 AI 跑脚本」，不接 CI 门禁；改为增强 runner 的逐套件结论 + fail-fast + flaky 自动分类
