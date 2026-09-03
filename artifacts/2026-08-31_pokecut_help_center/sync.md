---
task_id: 2026-08-31_pokecut_help_center
agent: page-map-sync
status: pending_review
repair_scope: full_exploration
gate_exemption: false
inputs:
  - D:\Test\web-test\help 页优化需求文档.md
  - page_map/pokecut/help.yaml (legacy 只读参考)
outputs:
  scanned_pages: [/help, / (首页顶部导航), /create (顶部导航), /tools/ai-photo-enhancer (顶部导航)]
  page_map_versions: [help_v2.yaml]
  coverage_gates: {desktop_initial: covered, faq_accordion: covered, desktop_search_results: covered, desktop_search_empty: covered, contact_ticket_dialog: covered, mobile_initial: covered, mobile_faq_category: covered, mobile_search_results: covered}
  state_button_coverage: covered
  requirement_actual_diffs:
    - {case: 12 搜索命中结果, diff_type: gap, detail: "结果列表含标题/摘要/所属分类且 '13 results for “credits”' 命中，但页面未渲染 'Sorted by relevance' 排序标识文案"}
  bug_candidates: []
  skipped: []
  special_dependencies: [顶部 Contact us 深链 /help?category=commercial-safety-support&question=commercial-safety-support-4#contact-us]
  specs_updated: false
next_agent: test-case-design
created_at: 2026-08-31 11:40:00 +08:00
---

# sync.md — Pokecut 帮助中心（/help）

## 1. 探索摘要
- /help 可访问，URL 保持 `/help`，Title `FAQ about Pokecut website | Pokecut`；主体为帮助中心布局：Hero 搜索区、5 个热门搜索词、6 张分类卡片、Popular（11 条）热门问题、底部联系支持 CTA。
- Hero 文案全部命中：`Pokecut Help Center`、`How can we help you create faster?`、`Search guides for account, credits, subscriptions, AI tools, downloads, refunds, and commercial use.`、placeholder `Search by keyword, for example: credits, refund, download` 与 `Search` 按钮。
- 6 个分类的问题列表与需求逐条一致；各分类默认展开第一条，同类只保留一条展开，再次点击收起且标题保留。
- 搜索命中 `credits` = `13 results for “credits”`，结果含标题/摘要/所属分类，PC 与移动端结果容器均可竖向滚动；无结果关键词命中 `No answer found?` + `Submit a ticket`。
- 顶部导航 `Contact us` 通过深链 `?category=commercial-safety-support&question=commercial-safety-support-4#contact-us` 自动定位到 Commercial, Safety & Support 并自动展开 `How do I contact Pokecut support?`。
- 底部 `Contact us` 点击后弹出工单弹窗（Email/Subject/Description/Attachments/Submit），承接正常。

## 2. 页面覆盖矩阵（对照需求 17 条 AC）
| # | 用例/覆盖点 | 结论 | 证据 |
|---|---|---|---|
| 1 | 沿用 /help 路径并切换帮助中心布局 | covered | explore_help_page.json（url/title/topnav/hero/bottom_cta）；注：Popular questions 以左侧 `Popular`(11) 导航项呈现 |
| 2 | Hero 文案与热门搜索词标签 | covered | explore_help_page.json hero/popular_tags；explore_tag_mobile_search.json tag_click |
| 3 | 分类卡片六主题及动态文章数量 | covered | explore_help_page.json category_cards（6 张，5/5/7/5/7/5 articles） |
| 4 | 点击分类留在当前页并切换问题列表 | covered | explore_help_page.json categories（6 分类各切换） |
| 5 | FAQ 单条展开/同类只保留一条 | covered | explore_help_page.json faq_accordion |
| 6 | Getting Started 分类内容 | covered | explore_help_page.json categories.Getting_Started |
| 7 | Account & Access 分类内容 | covered | explore_help_page.json categories.Account_and_Access |
| 8 | Plans, Credits & Billing 分类内容 | covered | explore_help_page.json categories.Plans_Credits_and_Billing |
| 9 | AI Tools & Editing 分类内容 | covered | explore_help_page.json categories.AI_Tools_and_Editing |
| 10 | Batch, Download & Projects 分类内容 | covered | explore_help_page.json categories.Batch_Download_and_Projects |
| 11 | Commercial, Safety & Support 分类内容 | covered | explore_help_page.json categories.Commercial_Safety_and_Support |
| 12 | 搜索命中结果列表（标题/摘要/分类/排序/X results/Sorted by relevance） | gap | explore_help_followup.json search_credits_ui：`Sorted by relevance` 未出现 |
| 13 | 搜索结果 >5 条 PC+移动滚动 | covered | explore_help_followup.json search_scroll（PC 1170>450）；explore_mobile_search_structure.json（mobile 910>350） |
| 14 | 搜索无结果空态与工单入口 | covered | explore_help_followup.json search_empty_ui |
| 15 | 顶部 Contact us 跳转并自动展开支持 FAQ | covered | explore_topnav.json + explore_deeplink.json |
| 16 | 底部支持区 Contact us 弹工单 | covered | explore_cta_mobile_category.json bottom_contact（弹窗 purchase-order-dialog） |
| 17 | 移动端窄屏布局 | covered | explore_help_page.json mobile + explore_cta_mobile_category.json mobile_category |

## 3. 需求差异
- 唯一差异（非阻断）：用例 12 预期结果要求 `结果列表显示 Sorted by relevance`，页面实际未渲染该排序标识。其余搜索能力（标题/摘要/所属分类、`X results for “keyword”`、页内刷新）均正常。

## 4. 关键发现与下游注意事项
- 顶部 `Contact us` 已实现为深链 `/help?category=commercial-safety-support&question=commercial-safety-support-4#contact-us`，用例 15 应直接断言深链跳转后的 active nav 与展开问题，而非重新模拟导航点击。
- 底部 `Contact us` 点击确实弹出工单弹窗（类名 `purchase-order-dialog`）；注意既有 `tests/test_help_page.py` 中该按钮曾写 `xfail 无响应`，本次复探证明 dispatchEvent 可触发，需在 test-writing 阶段复核并移除误判的 xfail。
- 分类卡片文章数量以 `N articles` 文本展示并与左侧导航数量一致；「不使用写死值」需接口/配置证据，探索阶段仅记录为展示值一致。
- 搜索 `Sorted by relevance` 缺失属需求-实现差异，写用例时作为 `gap` 记录，不进自动化断言（或按用户决定处理）。

## 5. 版本差异摘要
- legacy `help.yaml` → `help_v2.yaml`：补全搜索面板（命中/空态/滚动）、顶部 Contact us 深链、工单弹窗、移动端分类横向标签与搜索结果滚动，以及 6 分类问题清单与答案口径；修正底部 Contact us 点击可打开弹窗（旧地图未记录弹窗）。

> confirmed 前不得进入 test-case-design。

