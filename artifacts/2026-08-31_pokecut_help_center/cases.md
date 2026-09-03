---
task_id: 2026-08-31_pokecut_help_center
agent: test-case-design
phase: final_after_sync
status: pending_review
inputs:
  - D:\Test\web-test\help 页优化需求文档.md
  - artifacts/2026-08-31_pokecut_help_center/sync.md (confirmed)
  - page_map/pokecut/help_v2.yaml
outputs:
  case_count: 11
  priority_breakdown: {P0: 5, P1: 5, P2: 1}
next_agent: test-writing
created_at: 2026-08-31 12:10:00 +08:00
updated_at: 2026-09-01 10:30:00 +08:00
---

# 用例矩阵 — Pokecut 帮助中心（/help，去重后，按 L1~L6 分层）

> 阶段 final_after_sync。环境：测试服 http://10.17.1.66:3001，PC 1920x1080 en-US，移动端 375x812 en-US。
> 帮助页为匿名可访问内容页，不涉及登录/购买/credits；工单弹窗只验证打开承接，不真实提交。
> 去重原则：合并同路径重复断言，不删除任何 AC 覆盖；标签/分类/计数类在单条用例内循环，不参数化展开，报告用例数与矩阵一致。

## 需求理解

- 帮助页沿用 `/help` 路径，主体为帮助中心布局：Hero 搜索区、5 个热门搜索词、6 张分类卡片、Popular 热门问题（11 条）、联系支持 CTA。
- 6 个分类的问题列表与答案文案以需求为准；搜索为页内客户端过滤，命中/空态均留在 `/help`。
- 顶部 `Contact us` 深链自动定位并展开支持 FAQ；底部 `Contact us` 打开工单弹窗。
- 差异：需求要求 `Sorted by relevance` 排序标识，页面未渲染（sync gap，非阻断）。

## L1 页面元素 / 结构（regression）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---:|---|---|---|---|---|
| TC-HELP-L1-001 | P0 | /help 路径、整体布局与 Hero 文案 | help_v2.yaml: elements / category_cards / faq_nav | 1. goto /help 等待 H1；2. 断言 Hero 文案与控件；3. 断言标签/卡片/导航/CTA | 8s | URL 以 /help 结尾；eyebrow 含 Pokecut Help Center；h1 含 How can we help you create faster?；描述含 Search guides for account；placeholder 含 Search by keyword；Search 按钮可见；5 标签可见；6 卡片；7 导航项；底部 Still have questions? 可见 | 01整体布局与Hero |

## L2 交互行为 / 状态迁移（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---:|---|---|---|---|---|
| TC-HELP-L2-001 | P1 | 热门标签点击触发搜索并留在 /help（5 标签） | help_v2.yaml: states.desktop_initial.buttons.btn_popular_tag_credits | 1. goto /help；2. 逐个点击 5 个标签 | 每项 2s | 点击后 URL 仍 /help；搜索框 value=标签；出现 results for 计数文案 | 03标签搜索 |
| TC-HELP-L2-002 | P0 | 分类切换：高亮 + 列表切换 + 默认展开第一条（6 分类） | help_v2.yaml: states.desktop_initial.buttons.btn_faq_nav_item / category_questions | 1. goto /help；2. 逐个点击 6 个左侧分类导航 | 每项 1.5s | 被点导航含 --active；问题列表与该分类 category_questions 一致；open 数 1 且第一条 open=true | 04分类切换 |
| TC-HELP-L2-003 | P0 | FAQ 单条展开/同类只保留一条 | help_v2.yaml: states.desktop_faq_accordion.buttons.btn_faq_question | 1. 切 Getting Started；2. 点第一条→第二条→第二条 | 每步 0.8s | 点第一条仅第一条 open；点第二条仅第二条 open；再点第二条全部收起且标题保留 | 05FAQ展开收起 |
| TC-HELP-L2-004 | P0 | 搜索命中结果列表 + 计数 + PC 竖向滚动 | help_v2.yaml: states.desktop_search_results / elements.search_panel | 1. goto /help；2. 搜索 credits；3. 滚动结果容器到底 | 2.5s | URL 仍 /help；`13 results for`；`button.help-v2-search-panel__result` 计数 13；第一条含 credits；容器 scrollHeight>clientHeight；滚动后第 13 条可见 | 06搜索命中与PC滚动 |
| TC-HELP-L2-005 | P1 | 搜索无结果空态 + Submit a ticket | help_v2.yaml: states.desktop_search_empty.buttons.btn_submit_ticket | 1. 搜索 pokecut-unmatched-000；2. 截图空态；3. 点 Submit a ticket | 2.5s/1s | `0 results for` 与 No answer found?；Submit a ticket 可见；点击后 purchase-order-dialog 弹窗出现 | 07搜索空态、07b工单弹窗 |
| TC-HELP-L2-006 | P1 | 顶部 Contact us 深链自动定位并展开支持 FAQ | help_v2.yaml: elements.topnav_contact_us | 1. 首页定位 Contact us 链接 href；2. goto 深链 | 8s | 深链后 active 导航=Commercial, Safety & Support；展开问题=How do I contact Pokecut support? | 08Contact深链 |
| TC-HELP-L2-007 | P1 | 底部 Contact us 弹工单弹窗 | help_v2.yaml: states.contact_ticket_dialog / elements.bottom_cta_section | 1. 滚动到底部；2. 点击 Contact us | 1.2s | Still have questions? 与 Contact us 可见；点击后 purchase-order-dialog 含 Email/Subject/Description/Submit | 09工单弹窗 |

## L3 异常 / 权限 / 兼容（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---:|---|---|---|---|---|
| TC-HELP-L3-001 | P1 | 移动端窄屏布局 + 移动搜索滚动 | help_v2.yaml: states.mobile_initial / states.mobile_faq_category / states.mobile_search_results | 1. 移动视口 goto /help；2. 点 Getting Started；3. 搜索 credits | 8s/1s/2.5s | 6 移动卡片 2 列；分类标签容器可横向滑动且当前 --active；无 PC 左侧栏；移动 FAQ 5 条且第一条 --open；移动结果容器 scrollHeight>clientHeight | 11移动布局与搜索 |

## L4 PRD AC 逐条映射（regression）

| AC | 摘要 | 覆盖用例 | 期望 / 缺口 |
|---|---|---|---|
| AC1 沿用 /help 路径并切换帮助中心布局 | Hero/热门词/分类卡片/Popular/CTA | TC-HELP-L1-001 | Popular 以左侧 `Popular`(11) 导航呈现 |
| AC2 Hero 区文案与热门搜索词标签 | eyebrow/h1/desc/placeholder/Search + 5 标签 | TC-HELP-L1-001 / TC-HELP-L2-001 | 标签点击页内刷新 |
| AC3 分类卡片六主题及动态文章数量 | 6 卡片副文案 + 动态数量 | TC-HELP-L1-001 / TC-HELP-L2-002 | 数量 5/5/7/5/7/5 与导航一致 |
| AC4 点击分类留在当前页并切换列表 | 卡片/导航高亮 + 列表切换 + 默认展开第一条 | TC-HELP-L2-002 / TC-HELP-L6-001 | L2-002 覆盖左侧导航入口，L6 覆盖分类卡片入口 |
| AC5 FAQ 单条展开/同类一条 | 展开收起 + 标题保留 | TC-HELP-L2-003 | covered |
| AC6 Getting Started 分类内容 | 5 问与答案 | TC-HELP-L2-002 | covered |
| AC7 Account & Access 分类内容 | 5 问与答案 | TC-HELP-L2-002 | covered |
| AC8 Plans, Credits & Billing 分类内容 | 7 问与答案 | TC-HELP-L2-002 | covered |
| AC9 AI Tools & Editing 分类内容 | 5 问与答案 | TC-HELP-L2-002 | covered |
| AC10 Batch, Download & Projects 分类内容 | 7 问与答案 | TC-HELP-L2-002 | covered |
| AC11 Commercial, Safety & Support 分类内容 | 5 问与答案 | TC-HELP-L2-002 | covered |
| AC12 搜索命中结果列表（含 Sorted by relevance） | 标题/摘要/分类/计数/排序标识 | TC-HELP-L2-004 / TC-HELP-L5-001 | gap: 页面未渲染 `Sorted by relevance` |
| AC13 搜索 >5 条 PC+移动滚动 | 竖向滚动查看全部 | TC-HELP-L2-004 / TC-HELP-L3-001 | covered |
| AC14 搜索无结果空态与工单入口 | No answer found? + Submit a ticket | TC-HELP-L2-005 | covered |
| AC15 顶部 Contact us 跳转并自动展开支持 FAQ | 深链定位 + 自动展开 | TC-HELP-L2-006 | covered |
| AC16 底部支持区 Contact us 弹工单 | Still have questions? + Contact us 弹窗 | TC-HELP-L2-007 | covered |
| AC17 移动端窄屏布局 | 2 列卡片/横向标签/单列 FAQ/无左侧栏/搜索滚动 | TC-HELP-L3-001 | covered |

## L5 数据边界与等价类（default_full）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---:|---|---|---|---|---|
| TC-HELP-L5-001 | P2 | 搜索数量等价类（1/4 条，0/13 已由 L2 覆盖） | help_v2.yaml: elements.search_panel | 1. 依次搜索 language / download | 每项 2.5s | 计数文案分别 `1 results for`/`4 results for` | 13搜索计数 |

## L6 核心 Happy Path / E2E（smoke）

| ID | P | 测试点 | page_ref | 步骤 | 等待 | 断言 | 截图点 |
|---|---|---:|---|---|---|---|---|
| TC-HELP-L6-001 | P0 | 核心链路 smoke（分类卡片入口） | help_v2.yaml: states.desktop_initial.buttons.btn_category_card / elements | 1. goto /help 断言 H1；2. 点 Getting Started 卡片；3. 搜索 download；4. 滚动到底部 CTA | 8s/1.5s/2.5s/1s | Hero H1 可见；卡片入口后 Getting Started 高亮且第一条 FAQ 展开；`4 results for`；底部 Still have questions? 可见 | 14smoke |

## page_ref 与 selector 表

| 元素 | selector |
|---|---|
| Hero 标识 | `p[class*="eyebrow"]`（textContent 重复，用包含匹配） |
| Hero H1 | `h1` |
| 描述 | `p:has-text("Search guides for account")` |
| 搜索输入 | `input[placeholder*="Search by keyword"]` |
| 搜索按钮 | `button:has-text("Search")` |
| 热门标签 | `button:has-text("Credits|Subscription|Download|Batch|Project")` |
| 分类卡片（PC） | `button.help-v2-category-card` |
| 分类卡片（移动） | `button.help-v2-mobile-category-card` |
| 分类导航（PC） | `button.help-v2-faq-section__nav-item`（active: `--active`） |
| FAQ 条目（PC） | `article.help-v2-faq-item`；问题 `button.help-v2-faq-item__question`；答案 `div.help-v2-faq-item__answer`；open `--open` |
| 搜索面板（PC） | `div.help-v2-search-panel`；结果 `button.help-v2-search-panel__result`；计数 `div.help-v2-search-panel__header-inner` |
| 空态工单按钮 | `button:has-text("Submit a ticket")` |
| 底部 CTA | `section.help-v2-support-cta-section`；按钮 `button.help-v2-support-cta-section__button` |
| 工单弹窗 | `div.purchase-order-dialog` |
| 顶部 Contact us | `a[href*="/help?category=commercial-safety-support"]` |
| 移动 Hero | `section.help-v2-mobile-hero` |
| 移动搜索面板 | `div.help-v2-mobile-search-panel`；结果 `button.help-v2-mobile-search-panel__result` |
| 移动分类标签 | `div.help-v2-mobile-faq-section__tabs`；tab `button.help-v2-mobile-faq-section__tab`（active: `--active`） |
| 移动 FAQ 条目 | `button.help-v2-mobile-faq-item__question`（容器 `[class~="help-v2-mobile-faq-item"]`） |

## 依赖缺口与风险

- AC12 `Sorted by relevance` 排序标识缺失（sync gap），不进自动化断言；若产品确认需补实现，再回退补断言。
- 分类卡片「文章数量不使用写死值」仅验证展示值与导航一致，接口/配置级证据未取证。
- 工单弹窗只验证打开承接，不真实提交工单（红线：不执行不可逆提交/对外通知）。
- 帮助页为匿名内容页，不涉及登录/购买/credits，无账号态依赖。

## 待用户确认

- 本文档 confirmed 后进入 test-writing；自动化脚本按本矩阵 11 条生成（L2-001 5 标签、L2-002 6 分类、L5-001 2 关键词在单条用例内循环覆盖，不参数化展开）。

