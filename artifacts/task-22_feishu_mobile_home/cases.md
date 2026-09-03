---
task_id: task-22_feishu_mobile_home
agent: test-case-design
phase: final_after_sync
status: confirmed
inputs:
  - D:\downloads\用例\task-22-飞书文档_ v3.0\移动端首页优化大纲（安国）.md
  - artifacts/task-22_feishu_mobile_home/sync.md (confirmed)
  - page_map/pokecut/mobile_home_v1.yaml
outputs:
  case_count: 21
  priority_breakdown: {P0: 1, P1: 15, P2: 5}
next_agent: test-writing
created_at: 2026-08-31 14:05:00 +08:00
updated_at: 2026-08-31 15:10:00 +08:00
---

# 测试用例 — Pokecut 移动端首页优化（Mobile Home v3）

> 阶段 final_after_sync。移动视口 390x844（iPhone UA、has_touch、deviceScaleFactor=3），默认英文。
> 环境：测试服 http://10.17.1.66:3001/；staging 站内 /tools/* 对应正式环境 www.pokecut.com/tools/*。
> 默认上传素材 `test_images/有人脸.JPG`；损坏图 `test_images/损坏的图.png`。
> 账号：会员 450832596@qq.com / 单项购买 03201449879@qq.com / 免费随机邮箱；验证码 123456。
> 注意：首页 Sign up 登录弹层存在「登录提交无反应」bug（file_bug），ID Photo Maker 完整抠图用例 TC-MH-L3-004 标 blocked_by_bug。

## 需求理解

- 需求：移动端首页优化大纲（安国）。存量功能首次探索，已按 confirmed sync + page_map 将用例落成可执行矩阵。
- 覆盖范围：首屏 Agent 框、功能板块、effect(AI Templates)、Test、人像、画质增强、数据展示、用户评论、FAQ、移动端展示、底部导航。
- 文案/交互以实际页面为准（sync.md 已记录差异）。
- 登录态：首页 Sign up 登录弹层提交无反应，登录态相关用例暂阻塞。

## L1 页面元素 / 结构（regression）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---:|---|---|---|---|---|
| TC-MH-L1-001 | P1 | 移动端首页首屏结构与各板块存在 | mobile_home_v1.yaml: elements | 访问 /；滚动全页 | 8s | 首屏 Agent 框单列；6 功能卡、effect、Test、人像、画质增强、数据、评论、FAQ、移动端展示、底部导航均存在；底部导航 5 项 Home/All Tools/Upload/Generate/Pricing | 首屏+各板块 |
| TC-MH-L1-002 | P1 | 首屏文案与控件排列 | mobile_home_v1.yaml: states.mobile_default.buttons | 访问 / 并定位首屏 | 6s | 主标题 "All-in-One AI Photo Editor & Generator"；主按钮 "Start Creating for Free"；textarea placeholder 命中 "Start with Pokecut's free AI image generation..."；模型 "Pokecut Pro"、比例/分辨率入口、Generate 默认 disabled | 首屏 |

## L2 交互行为 / 状态迁移（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---:|---|---|---|---|---|
| TC-MH-L2-001 | P1 | 主按钮唤起系统上传弹窗 | states.mobile_default.buttons.agent_main_cta | 点击 Start Creating for Free | 1s | 触发 file chooser（expect_file_chooser） | 弹窗前 |
| TC-MH-L2-002 | P0 | 主按钮上传有效图进入移动端画布 | states.mobile_default.buttons.agent_main_cta | 主按钮选 `有人脸.JPG` | 6s | URL 进入 /create/edit?pid=*；画布可见 | 画布 |
| TC-MH-L2-003 | P1 | 模型入口展开模型列表 | states.agent_popovers.buttons.model_entry | 点击 Pokecut Pro | 1s | 出现 8 个模型（ChatGPT Image 2.0 / Nano Banana / Nano Banana 2 / Nano Banana 2 Lite / Nano Banana Pro / Seedream 5.0 Lite / Seedream 5.0 Pro / Seedream4.0） | 模型弹层 |
| TC-MH-L2-004 | P1 | 比例入口展开比例列表 | states.agent_popovers.buttons.ratio_entry | 点击比例入口 | 1s | 出现 16:9/1:1/2:3/3:2/3:4/4:3/9:16/9:21 | 比例弹层 |
| TC-MH-L2-006 | P1 | Generate 未满足条件禁用 | states.mobile_default.buttons.agent_generate | 查看并点击 Generate | 1s | Generate disabled；点击不跳转、不发起生成 | 首屏 |
| TC-MH-L2-022 | P1 | Agent 输入框输入文本后 Generate 可点击并进入画布 | states.mobile_default.buttons.agent_generate | textarea 输入 "a studio portrait with soft light" 后点击 Generate | 1.5s/8s | 输入前 disabled；输入后 enabled；点击后 URL /create/edit?pid=*（匿名态随后弹注册/获取点数弹层） | 画布+弹层 |
| TC-MH-L2-007 | P1 | 功能卡片上传打开对应画布面板（参数化） | states.mobile_default.buttons.function_* | 分别点击 Remove Background / Clothes Changer / HD Photo Coverter / Body Editor / AI Replace 并上传 `有人脸.JPG` | 6s/项 | 每项触发 file chooser；上传后 URL /create/edit?pid=* 且展开对应面板（HD 为 Photo Enhancer） | 画布面板 |
| TC-MH-L2-008 | P1 | ID Photo Maker 匿名态上传有效图弹注册弹层 | states.mobile_default.buttons.function_id_photo | 点击 ID Photo Maker 上传 `有人脸.JPG` | 6s | 触发 file chooser；不进入画布；出现 Sign Up/Get Credits 弹层 | 注册弹层 |
| TC-MH-L2-009 | P2 | More Pokecut Tools 跳转 tools 页 | states.mobile_default.buttons.function_more_tools | 点击 More Pokecut Tools | 4s | URL /tools | tools 页 |
| TC-MH-L2-010 | P1 | effect 模板卡上传进入画布 | states.mobile_default.buttons.effect_template | 点击 effect 首个模板（Butt）并上传 | 6s | 触发 file chooser；URL /create/edit?pid=* | 画布 |
| TC-MH-L2-011 | P2 | See More Creations 跳转 create 页 | states.mobile_default.buttons.effect_see_more | 点击 See More Creations | 4s | URL /create | create 页 |
| TC-MH-L2-012 | P2 | Test 4 链接跳转站内工具页（参数化） | mobile_home_v1.yaml: elements.test_board.links | 点击 Pretty Scale / Ethnicity Guesser / Eye Color Detector / Body Shape Detector | 4s/项 | 同页跳转 /tools/pretty-scale、/tools/ethnicity-guesser-ai、/tools/eye-color-detector、/tools/body-shape-detector | 工具页 |
| TC-MH-L2-013 | P1 | 人像 tab 切换内容切换（参数化） | mobile_home_v1.yaml: tabs.portrait_tabs | 依次点击 Face/Body/Hair/Background（先 scroll_into_view） | 1.5s/项 | 选中态正确；卡片内容分别切换为 face-editor / body、hair-editor、background 相关链接 | 人像板块 |
| TC-MH-L2-014 | P1 | 画质增强 4 标签交互（参数化） | mobile_home_v1.yaml: elements.enhance_board | 点击 HD Enhance / Text Enhance / Portrait AI / Ultra Enhance | 4s/项 | HD→/tools/hd-pic-converter；Text→/tools/ai-image-text-enhancer；Portrait AI / Ultra Enhance→file chooser + /create/edit | 画质增强板块 |
| TC-MH-L2-015 | P2 | 数据卡片点击选中态 | mobile_home_v1.yaml: elements.data_board | 点击 3M+ creators 卡片 | 1s | 卡片 active 样式变化 | 数据板块 |
| TC-MH-L2-016 | P2 | Product Hunt 新标签页跳转 | mobile_home_v1.yaml: elements.data_board | 点击 #2 / Product Hunt 链接 | 2s | target=_blank，href 命中 producthunt.com/products/pokecut-ai... | 数据板块 |
| TC-MH-L2-018 | P1 | FAQ 展开收起与答案链接 | mobile_home_v1.yaml: elements.faq_board | 点击任一 FAQ 问题两次；点击 /pricing、/term-of-use、submitting a ticket | 1s/项 | 展开/收起切换；online store→/pricing；our Terms of Use→/term-of-use；submitting a ticket 触发 data-submit-ticket=refund | FAQ |
| TC-MH-L2-020 | P1 | 底部导航各入口（参数化） | mobile_home_v1.yaml: elements.bottom_nav | 点击 Home / All Tools / Upload / Generate / Pricing | 4s/项 | Home→/create；All Tools→/tools；Upload→file chooser 上传后 /create/edit；Generate→无 chooser 直接 /create/edit；Pricing→/pricing | 底部导航 |

## L3 异常 / 权限 / 兼容（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 期望 |
|---|---|---:|---|---|---|
| TC-MH-L3-004 | P1 | ID Photo Maker 抠图成功进入证件照画布 | states.mobile_default.buttons.function_id_photo | 登录具备 ID credits 的账号后上传可抠图图 | 抠图成功并进入证件照画布（blocked_by_bug：登录弹层提交无反应） |

## L4 PRD AC 逐条映射（regression）

| AC | 摘要 | 覆盖用例 | 期望 / 缺口 |
|---|---|---|---|
| AC-移动端首屏结构 | Agent 框单列、控件上下排列、无横向溢出 | TC-MH-L1-001 / TC-MH-L1-002 | 与 sync.md actual 一致 |
| AC-文案与多语言 | 首屏/板块文案按文档 key | TC-MH-L1-002 / TC-MH-L2-013 / TC-MH-L2-014 | 实际文案以 sync.md 为准（Portrait AI / Generate） |
| AC-上传后进入画布 | 主按钮/功能卡/effect/底部 Upload | TC-MH-L2-002 / L2-007 / L2-010 / L2-020 | 均进入 /create/edit?pid=* |
| AC-人像/画质增强交互 | tab 切换、4 标签跳转/上传 | TC-MH-L2-013 / L2-014 | 与 PC 同源，实际已覆盖 |
| AC-数据/评论/FAQ/移动端展示 | 展示与跳转 | TC-MH-L2-015 / L2-016 / L2-018 | 评论头像以实际资源为准 |

## L5 数据边界与等价类（default_full）

（当前无 L5 用例，用户删除后保留为空；如需补充上传格式/大小边界，再追加。）

## L6 核心 Happy Path / E2E（smoke）

（当前无 L6 用例，用户删除后保留为空；核心上传链路已由 TC-MH-L2-002 覆盖。）

## page_ref 与 selector 表

| 元素 | selector |
|---|---|
| 首屏标题 | `#home-mobile-agent-title` |
| 主按钮 | `button:has-text('Start Creating for Free')` |
| Agent 输入框 | `textarea[aria-label]` |
| Agent Generate | `section.mobile-home-agent-hero button:has-text('Generate')` |
| 模型入口 | `section.mobile-home-agent-hero button:has-text('Pokecut Pro')` |
| 比例入口 | `section.mobile-home-agent-hero button:not([aria-label])[class*='size-[2.625rem]']` |
| 功能卡片 | `button:has-text('<卡片名>')` |
| 底部导航 | `nav.home-mobile-bottom-nav button[aria-label='<item>']` |
| FAQ 展开头 | `.pk-collapse-header` |
| 人像 tab | `#home-mobile-portrait-tab-<tab>` |
| 画质增强标签 | `button[aria-label='<HD Enhance|Text Enhance|Portrait AI|Ultra Enhance>']` |

## 依赖缺口与风险

- TC-MH-L3-004 标 blocked_by_bug：首页 Sign up 登录弹层提交无反应（sync.md file_bug），无法建立登录态。
- 分辨率入口档位探索仅见 1k，当前未单独列用例，后续如需可追加。
- 多语言交叉（除英文）未覆盖；本矩阵默认英文。
- L4/L5/L6 当前为空，是按用户删除后的最终范围。

## 待用户确认

- 本文档 confirmed 后进入 test-writing；当前脚本已按本矩阵 21 条生成。
