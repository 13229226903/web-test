# archive.md — new_feature_detection_ui_20260901_124711

- 归档状态：archived
- 用户确认：归档
- 模块：detection_ui（AI Face Reader / Nose Shape Detector 检测类功能适配 UI）
- Tests：\	ests/test_detection_ui_seo_l6.py\（仅 L6 两条 smoke）
- Data：\data/pokecut_detection_ui.yaml\
- Archive：\rchive/detection_ui/test_detection_ui_seo_l6.py\、\rchive/detection_ui/pokecut_detection_ui.yaml\
- Registry：\rtifacts/regression_registry.md\
- 复跑命令：\python -m pytest tests/test_detection_ui_seo_l6.py -q --base-url=https://pokecut-dev.guangzhuiyuan.com\
- Allure 归档快照：\eports/allure-results-archive\ / \eports/allure-report-archive\
- 归档日期：2026-09-02
- 备注：成功态依赖预部署环境（测试服 Server busy 时切预部署并登录会员账号）；L6-001 face 三栏双下载 + PC Continue 带三图；L6-002 nose 模糊承接 + Get It Now 仅带原图；BUG-NOSE-001 / BUG-FACE-MOBILE-001 用户确认 skip（未进断言）
