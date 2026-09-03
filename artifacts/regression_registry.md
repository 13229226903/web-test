# Regression Registry（稳定回归资产登记）

> 本文件是稳定回归资产的统一入口。只有经过 `regression-archive gate` 用户确认的脚本，才登记为 `stable_regression`。
>
> 维护规则：
> - 脚本仅 `impl.md completed` 不自动入表。
> - 必须满足：`cases.md confirmed`、`sync.md confirmed`、`impl.md completed 且 failed=0`、`review pass`、`visual-review pass/不需要`。
> - 用户确认归档后，同步 `tests/` 当前脚本与 `archive/<module>/` 副本，再追加/更新本登记。
> - 用户选择暂不归档的任务不写入 stable 条目。

## 字段说明

| 字段 | 含义 |
|---|---|
| Feature | 功能/页面名称 |
| URL | 目标 URL 或路由 |
| Status | `stable_regression` / `archived_inactive` / `pending_fix` |
| Task ID | 产出该资产的 `artifacts/<task_id>/` |
| Tests | 当前可执行回归脚本 |
| Archive | 归档副本路径 |
| Page Map | confirmed page_map 版本 |
| Sync | confirmed sync.md |
| Cases | confirmed cases.md |
| Impl / Review / Visual | 执行、静态审查、视觉审查产物 |
| Last Passed | 最近通过时间与命令 |
| Accounts / Data | 账号态、素材、环境等关键依赖 |
| Notes | 风险、跳过项、维护说明 |

## 稳定回归资产

| Feature | URL | Status | Task ID | Tests | Archive | Page Map | Sync | Cases | Impl / Review / Visual | Last Passed | Accounts / Data | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 人像检测三入口页（Ethnicity / Body Shape / Face Comparison） | http://10.17.1.66:3001/tools/ethnicity-guesser-ai 、/tools/body-shape-detector 、/tools/face-comparison | stable_regression | 2026-08-28_pokecut_portrait_detector_interactions | tests/test_pokecut_portrait_detector.py | archive/portrait_detector/test_pokecut_portrait_detector.py | artifacts/2026-08-28_pokecut_portrait_detector_interactions/portrait_detector_pages_v2.yaml | artifacts/2026-08-28_pokecut_portrait_detector_interactions/sync_v2.md | artifacts/2026-08-28_pokecut_portrait_detector_interactions/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-08-29 14 passed in 301s；`python -m pytest tests/test_pokecut_portrait_detector.py -q` | 预部署 http://10.17.1.66:3001；PC 1920x1080 en-US；登录 450832596@qq.com / 123456；素材 test_images/有人脸.JPG、多人脸.jpg、无人脸.jpg；credits 9740 | 结果态长等待 30–75s；测试服登录失败已切预部署；L1 结构断言并入 L2；14 用例 14 passed，14/14 截图 |
| 文字画质增强实验页（AI Image Text Enhancer） | http://10.17.1.66:3001/tools/ai-image-text-enhancer | stable_regression | 2026-08-29_pokecut_ai_image_text_enhancer | tests/test_ai_image_text_enhancer_experiment.py | archive/tool_pages/test_ai_image_text_enhancer_experiment.py | page_map/pokecut/ai_image_text_enhancer_v3.yaml | artifacts/2026-08-29_pokecut_ai_image_text_enhancer/sync.md | artifacts/2026-08-29_pokecut_ai_image_text_enhancer/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-08-29 15 passed, 3 skipped in 777s；python -m pytest tests/test_ai_image_text_enhancer_experiment.py -q | 预部署 http://10.17.1.66:3001；PC 1920x1080 en-US；登录 450832596@qq.com / 123456；素材 test_images/文字测例.jpg、1K/4K/4K/8K、损坏的图.png | 测试服登录 authToken 空需切预部署；会员账号预部署显示免费档（skip）；非增强模式生成 >180s 未出结果（skip）；真 8K highest clarity 缺口（skip） |
| 画布页文字功能 | http://10.17.1.66:3001/create → /agent?pid=<uuid> | stable_regression | 2026-08-30_pokecut_canvas_text_layer | tests/test_infinite_canvas_text_layer_v2.py | archive/infinite_canvas/test_infinite_canvas_text_layer_v2.py | page_map/pokecut/infinite_canvas_text_layer_v2.yaml | artifacts/2026-08-30_pokecut_canvas_text_layer/sync.md | artifacts/2026-08-30_pokecut_canvas_text_layer/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-08-31 6 passed in 296s；`python -m pytest tests/test_infinite_canvas_text_layer_v2.py -q` | 测试服 http://10.17.1.66:3001；PC 1920x1080 en-US；匿名上传可用；素材 test_images/低分辨率.JPG | 优化去重 6 用例；Reflection/Outline 像素 diff 断言效果；色盘弹窗应用后需再次点击色盘按钮关闭 |
| Pokecut 移动端首页优化（Mobile Home v3） | http://10.17.1.66:3001/ （移动端 390x844） | stable_regression | task-22_feishu_mobile_home | tests/test_mobile_home.py | archive/mobile_home/test_mobile_home.py | page_map/pokecut/mobile_home_v1.yaml | artifacts/task-22_feishu_mobile_home/sync.md | artifacts/task-22_feishu_mobile_home/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-08-31 37 passed, 1 skipped in 402s；`python -m pytest tests/test_mobile_home.py -q` | 测试服 http://10.17.1.66:3001；移动端 390x844 en-US；匿名浏览无需登录；素材 test_images/有人脸.JPG | 登录弹层提交无反应 bug（TC-MH-L3-004 skip）；21 用例 37 passed/1 skipped；Allure feature/story/class/title/severity/markers |
| 帮助中心（/help） | http://10.17.1.66:3001/help | stable_regression | 2026-08-31_pokecut_help_center | tests/test_help_page.py | archive/help_center/test_help_page.py | page_map/pokecut/help_v2.yaml | artifacts/2026-08-31_pokecut_help_center/sync.md | artifacts/2026-08-31_pokecut_help_center/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-09-01 11 passed in 188s；`python -m pytest tests/test_help_page.py -q` | 测试服 http://10.17.1.66:3001；PC 1920x1080 en-US + 移动端 375x812；匿名浏览无需登录 | 11 用例按 L1~L6 分层；AC12 `Sorted by relevance` 缺失为 gap（不进断言）；标签/分类/计数类单条内部循环，报告条数=矩阵条数 |
| 检测类功能适配 UI（AI Face Reader / Nose Shape Detector L6 E2E） | https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader 、/tools/nose-shape-detector | stable_regression | new_feature_detection_ui_20260901_124711 | tests/test_detection_ui_seo_l6.py | archive/detection_ui/test_detection_ui_seo_l6.py | page_map/pokecut/ai_face_reader_v3.yaml 、page_map/pokecut/nose_shape_detector_v3.yaml | artifacts/new_feature_detection_ui_20260901_124711/sync.md | artifacts/new_feature_detection_ui_20260901_124711/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-09-02 2 passed in 132.83s；python -m pytest tests/test_detection_ui_seo_l6.py -q --base-url=https://pokecut-dev.guangzhuiyuan.com | 预部署 https://pokecut-dev.guangzhuiyuan.com；PC 1920x1080 en-US；登录 450832596@qq.com / 123456；素材 test_images/有人脸.JPG；会员账号 | 仅 L6 两条 smoke（用户确认只保留 L6，完整 28 条矩阵归档于 cases_full_matrix.md）；成功态依赖预部署环境；BUG-NOSE-001 / BUG-FACE-MOBILE-001 用户确认 skip；face 双下载 jpg + PC Continue 三图；nose 模糊承接 Get It Now 仅原图 |
