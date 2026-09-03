---
task_id: new_feature_detection_ui_20260901_124711
agent: test-case-design
phase: requirement_draft
status: completed
inputs:
  requirement_doc: "D:/downloads/用例/task-39-飞书文档_ 检测类功能适配UI需求文档 (1)/检测类功能适配UI需求文档.md"
  target_pages:
    - https://pokecut-dev.guangzhuiyuan.com/tools/nose-shape-detector
    - https://pokecut-dev.guangzhuiyuan.com/tools/ai-face-reader
outputs:
  ac_count: 21
  prd_only_gaps: ["SEO 配置字段 extendFunType/extendPresetParams 的具体取值未在 PRD 给出", "credits 扣减数值未在 PRD 给出"]
next_agent: page-map-sync (待提测后 final_after_sync)
created_at: 2026-09-02 10:20:00 +08:00
---

# requirement_draft — 检测类功能适配 UI

## 需求理解
PRD 目标：检测类 SEO 工具页（有优化结果图 / 无优化结果图两种）在上传后展示统一结果编辑三栏，并区分成功态、生成中、失败态、购买不足、移动端布局与承接逻辑。用户指定测试服域名 `https://pokecut-dev.guangzhuiyuan.com/`，本次限定纯 Playwright MCP 探索已确认页面行为。

## AC 映射（PRD 逐条）
| # | AC 摘要 | 预计测试点 | 预计状态 |
|---|---|---|---|
| 1 | 上传前保持原 SEO 内容结构和文案，不出现三栏承接 UI | L1 SEO 首屏结构 | 待提测验证 |
| 2 | 有优化结果图页面成功态展示 Original/Analysis/Optimized 三栏 | L1/L6 三栏结构 | 待提测验证 |
| 3 | 无优化结果图页面展示模糊承接态（缩略图/蒙层/文案/Get It Now，无下载） | L1/L2 模糊承接 | 待提测验证 |
| 4 | 点击 Get It Now 进入无限画布 Portrait Editor 承接，选中原图，不选模板 | L2/L6 画布承接 | 待提测验证 |
| 5 | 生成中原图缩略图 + Upload Image 不可点击 | L2 生成中状态 | 待提测验证 |
| 6 | 分析生成中：灰色蒙层/加载 icon/Generating analysis...，Download 置灰 | L2 生成中状态 | 待提测验证 |
| 7 | 分析未成功前优化区保持 Waiting for analysis...，不跳画布 | L2 等待态 | 待提测验证 |
| 8 | 分析成功后优化区 Generating optimized result...，按钮置灰 | L2 优化生成中 | 待提测验证 |
| 9 | SEO 配置字段驱动优化结果生成并按配置扣 credits | L2/L5 credits | 需配置证据 |
| 10 | 成功态 Upload Image 恢复可用，重传走生成流程 | L2 重传 | 待提测验证 |
| 11 | 分析结果图 Download 下载 jpg | L2 下载 | 待提测验证 |
| 12 | 优化结果图 Download 下载 jpg | L2 下载 | 待提测验证 |
| 13 | PC Continue in Portrait Editor 带入三张图，选中优化图，打开功能弹窗，不选模板 | L2/L6 画布 | 待提测验证 |
| 14 | 分析网络错误：Network error + Change Image/Try again | L3 异常 | 需故障注入 |
| 15 | 分析服务器忙：Server busy 文案 + Change Image/Try again，不扣 credits | L3 异常 | 待提测验证 |
| 16 | 分析鉴黄失败：Policy violation + 仅 Change Image | L3 异常 | 需故障注入 |
| 17 | 优化结果图生成失败：Optimization failed + Portrait Editor，返还 credits | L3 异常 | 需故障注入 |
| 18 | 分析 credits 不足：购买弹窗 → 购买成功回结果页继续生成 | L3 购买 | 需授权支付 |
| 19 | 优化 credits 不足：模糊承接 + Get It Now 进入后续链路 | L3/L2 承接 | 需授权扣减 |
| 20 | 移动端结果态纵向排版，文案与 PC 一致 | L2 移动布局 | 待提测验证 |
| 21 | 移动端成功态 Continue 仅带优化结果图；失败态仅带原图 | L2/L3 移动承接 | 待提测验证 |

## 测试点初稿（Layer 分布）
- L1 页面元素/结构：SEO 首屏、三栏标题、失败态文案、模糊承接结构。
- L2 交互/状态迁移：上传→生成中→成功；重传；下载；PC/移动 Continue/Get It Now 画布承接；Try again / Change Image。
- L3 异常/权限/兼容：网络错误、服务器忙、鉴黄、优化失败、credits 不足购买、移动失败承接。
- L4 PRD AC 逐条映射。
- L5 数据边界/等价类：图片格式、人脸数量、分辨率。
- L6 核心 Happy Path / E2E：face 与 nose 两条全流程。

## 待提测清单
- 页面已提测，已通过预部署环境补充确认成功态（见 sync.md）。
- 需后端/配置证据：extendFunType、extendPresetParams、credits 扣减数值。
- 需故障注入/授权：网络错误、鉴黄、优化失败、购买链路。
