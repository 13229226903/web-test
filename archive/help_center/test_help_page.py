# -*- coding: utf-8 -*-
"""Pokecut 帮助中心（/help）回归测试 — 去重后 10 条用例（报告呈现 10 条）。

对照 artifacts/2026-08-31_pokecut_help_center/cases.md 与 page_map/pokecut/help_v2.yaml。
Vue 组件交互统一使用 dispatchEvent(MouseEvent) 触发点击；帮助页为匿名内容页，无需登录。
标签/分类/计数类用例在单条用例内部循环覆盖，不再参数化展开，保证 Allure 报告用例数与 cases.md 一致。
"""
import pytest
import allure
from playwright.sync_api import Page, expect as pw_expect


# ── 工具函数 ──────────────────────────────────────────────────

def goto_help(page: Page, base_url: str):
    """导航到 /help 并等待 Vue SPA 渲染完成。"""
    page.goto(f"{base_url}/help", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(8000)


def goto_help_mobile(page: Page, base_url: str):
    """移动端窄屏打开 /help。"""
    page.set_viewport_size({"width": 375, "height": 812})
    page.goto(f"{base_url}/help", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(8000)


def vue_click(page: Page, locator):
    """点击 Vue 组件：滚动到可见后 dispatchEvent(MouseEvent)。"""
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    handle = locator.element_handle()
    if handle:
        handle.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
    page.wait_for_timeout(900)


def do_search(page: Page, keyword: str):
    """在 Hero 搜索框输入关键词并回车触发搜索。"""
    inp = page.locator('input[placeholder*="Search by keyword"]').first
    inp.scroll_into_view_if_needed()
    inp.fill(keyword)
    page.wait_for_timeout(400)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2500)


def shot(page: Page, name: str):
    """在对应步骤内附加截图到 Allure。"""
    allure.attach(page.screenshot(), name=name, attachment_type=allure.attachment_type.PNG)


CASE_PRIORITY = {
    "L1-001": "P0",
    "L2-001": "P1", "L2-002": "P0", "L2-003": "P0", "L2-004": "P0",
    "L2-005": "P1", "L2-006": "P1", "L2-007": "P1",
    "L3-001": "P1",
    "L5-001": "P2",
    "L6-001": "P0",
}


def matrix_meta(serial: str):
    """写入与 cases.md 一致的 case_id/layer/priority 元数据。"""
    layer, _num = serial.split("-", 1)
    allure.dynamic.epic("帮助中心")
    allure.dynamic.label("case_id", f"TC-HELP-{serial}")
    allure.dynamic.label("layer", layer)
    allure.dynamic.label("priority", CASE_PRIORITY[serial])


# ── 测试数据 ──────────────────────────────────────────────────

POPULAR_TAGS = ["Credits", "Subscription", "Download", "Batch", "Project"]

CATEGORY_QUESTIONS = {
    "Getting Started": [
        "What is Pokecut?",
        "What can I use Pokecut for?",
        "Is Pokecut free?",
        "Can I use Pokecut without signing up?",
        "How do I start editing a photo?",
    ],
    "Account & Access": [
        "How do I change the language in Pokecut?",
        "Where can I see my remaining credits?",
        "Where can I see my orders?",
        "Can I use my web account to log in to the mobile app?",
        "Where can I unsubscribe from Pokecut emails?",
    ],
    "Plans, Credits & Billing": [
        "What are credits?",
        "What is the difference between a Premium Plan and Credits Purchase?",
        "Do purchased credits expire?",
        "Can I cancel my Premium Plan?",
        "Can I get a refund?",
        "Why did my payment or renewal fail?",
        "Can website credits be used in the Pokecut app?",
    ],
    "AI Tools & Editing": [
        "Which AI tools does Pokecut provide?",
        "What image formats can I upload?",
        "How can I upload an image?",
        "Why did my AI task fail?",
        "What if I am not satisfied with the AI result?",
    ],
    "Batch, Download & Projects": [
        "Can Pokecut edit images in batches?",
        "Which batch tools are available?",
        "Which marketplace sizes are supported in Batch Edit?",
        "How do I download my edited image?",
        "Why can’t I download in HD?",
        "Where can I find my previous projects?",
        "What should I do if download or project recovery fails?",
    ],
    "Commercial, Safety & Support": [
        "Can I use Pokecut images commercially?",
        "What content is not allowed?",
        "How does Pokecut protect privacy?",
        "How do I contact Pokecut support?",
        "How long does support take to reply?",
    ],
}

# 搜索结果数量等价类（0 由 L2-005、13 由 L2-004 覆盖，此处仅补 1/4）
SEARCH_COUNTS = [
    ("language", "1 results for"),
    ("download", "4 results for"),
]


# ═══════════════════════════════════════════════════════════════
# L1 页面元素 / 结构
# ═══════════════════════════════════════════════════════════════

@allure.feature("帮助中心")
@allure.epic("帮助中心")
@allure.story("L1-页面结构元素")
class TestL1PageStructure:

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("L1-001: /help 路径、整体布局与 Hero 文案")
    def test_l1_001_layout_and_hero(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 页面整体结构改版 / Hero 区展示帮助中心文案与热门搜索词标签
        覆盖层级: L1
        前置条件: 打开 /help 页面
        测试步骤:
        1. 导航到 /help 并等待渲染
        2. 断言 Hero 文案与控件
        3. 断言热门标签/分类卡片/FAQ 导航/底部 CTA
        预期结果: URL 停留 /help；整体为帮助中心布局；Hero 文案命中需求
        """
        matrix_meta("L1-001")
        with allure.step("导航到 /help 并等待渲染"):
            goto_help(page, base_url)

        with allure.step("断言 URL 与 Hero 文案"):
            assert page.url.rstrip("/").endswith("/help"), f"URL 应停留 /help，实际 {page.url}"
            eyebrow = page.locator("p[class*='eyebrow']").first
            pw_expect(eyebrow).to_be_visible()
            assert "Pokecut Help Center" in eyebrow.inner_text()
            pw_expect(page.locator("h1").first).to_contain_text("How can we help you create faster?")
            desc = page.locator("p:has-text('Search guides for account')").first
            pw_expect(desc).to_be_visible()
            assert "Search guides for account" in desc.inner_text()
            inp = page.locator('input[placeholder*="Search by keyword"]').first
            pw_expect(inp).to_be_visible()
            assert "Search by keyword" in (inp.get_attribute("placeholder") or "")
            pw_expect(page.locator("button:has-text('Search')").first).to_be_visible()

        with allure.step("断言热门标签/分类卡片/FAQ 导航/底部 CTA"):
            for tag in POPULAR_TAGS:
                pw_expect(page.locator(f"button:has-text('{tag}')").first).to_be_visible()
            pw_expect(page.locator("button.help-v2-category-card")).to_have_count(6)
            pw_expect(page.locator("button.help-v2-faq-section__nav-item")).to_have_count(7)
            cta = page.locator("section.help-v2-support-cta-section").first
            cta.scroll_into_view_if_needed()
            pw_expect(page.locator("h2:has-text('Still have questions?')").first).to_be_visible()

        with allure.step("截图记录"):
            shot(page, "01整体布局与Hero")


# ═══════════════════════════════════════════════════════════════
# L2 交互行为 / 状态迁移
# ═══════════════════════════════════════════════════════════════

@allure.feature("帮助中心")
@allure.epic("帮助中心")
@allure.story("L2-交互行为元素")
class TestL2Interactions:

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("L2-001: 热门标签点击触发搜索并留在 /help（5 标签）")
    def test_l2_001_popular_tag(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - Hero 区展示帮助中心文案与热门搜索词标签
        覆盖层级: L2
        前置条件: 打开 /help
        测试步骤:
        1. 逐个点击 Credits/Subscription/Download/Batch/Project
        预期结果: 每次点击后留在 /help 且搜索按标签关键词刷新
        """
        matrix_meta("L2-001")
        for tag in POPULAR_TAGS:
            with allure.step(f"导航 /help 并点击标签 {tag}"):
                goto_help(page, base_url)
                vue_click(page, page.locator(f"button:has-text('{tag}')").first)

            with allure.step(f"断言标签 {tag} 页内刷新"):
                assert page.url.rstrip("/").endswith("/help"), f"URL 应停留 /help，实际 {page.url}"
                inp = page.locator('input[placeholder*="Search by keyword"]').first
                pw_expect(inp).to_have_value(tag)
                assert "results for" in page.locator("body").inner_text()

            with allure.step(f"截图 {tag}"):
                shot(page, f"03标签搜索-{tag}")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("L2-002: 分类切换高亮 + 列表切换 + 默认展开第一条（6 分类）")
    def test_l2_002_category_switch(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 点击分类后留在当前帮助页并切换到对应问题列表
        覆盖层级: L2
        前置条件: 打开桌面端 /help
        测试步骤:
        1. 导航到 /help
        2. 逐个点击 6 个左侧分类导航
        预期结果: 导航高亮、只展示该分类问题、默认展开第一条
        """
        matrix_meta("L2-002")
        with allure.step("导航到 /help"):
            goto_help(page, base_url)

        for cat in CATEGORY_QUESTIONS:
            with allure.step(f"点击分类 {cat}"):
                nav = page.locator(f"button.help-v2-faq-section__nav-item:has-text('{cat}')").first
                vue_click(page, nav)

            with allure.step(f"断言 {cat} 高亮与问题列表"):
                active = page.locator("button.help-v2-faq-section__nav-item--active").first
                pw_expect(active).to_contain_text(cat)
                questions = [q.strip() for q in page.locator("article.help-v2-faq-item button.help-v2-faq-item__question").all_inner_texts()]
                assert questions == CATEGORY_QUESTIONS[cat], f"{cat} 问题列表不符，实际: {questions}"
                open_states = page.evaluate("() => Array.from(document.querySelectorAll('article.help-v2-faq-item')).map(it => it.className.includes('open'))")
                assert sum(open_states) == 1 and open_states[0] is True, f"{cat} 应默认展开第一条，实际 {open_states}"

            with allure.step(f"截图 {cat}"):
                shot(page, f"04分类切换-{cat}")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("L2-003: FAQ 单条展开/同类只保留一条")
    def test_l2_003_faq_accordion(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - FAQ 行支持单条展开收起且同类只保留一条展开
        覆盖层级: L2
        前置条件: 已进入任一分类问题列表
        测试步骤:
        1. 导航 /help 并切到 Getting Started
        2. 点第一条、再点第二条、再点第二条
        预期结果: 单条展开、再点收起、标题保留
        """
        matrix_meta("L2-003")
        with allure.step("导航并切到 Getting Started"):
            goto_help(page, base_url)
            vue_click(page, page.locator("button.help-v2-faq-section__nav-item:has-text('Getting Started')").first)

        questions = page.locator("button.help-v2-faq-item__question")

        with allure.step("点击第一条"):
            vue_click(page, questions.nth(0))
        with allure.step("点击第二条"):
            vue_click(page, questions.nth(1))
        with allure.step("断言只保留第二条展开"):
            states = page.evaluate("() => Array.from(document.querySelectorAll('article.help-v2-faq-item')).map(it => it.className.includes('open'))")
            assert states == [False, True, False, False, False], f"点第二条后应只有第二条展开，实际 {states}"

        with allure.step("再次点击第二条收起"):
            vue_click(page, questions.nth(1))
            states2 = page.evaluate("() => Array.from(document.querySelectorAll('article.help-v2-faq-item')).map(it => it.className.includes('open'))")
            assert all(not s for s in states2), f"再次点击后应全部收起，实际 {states2}"
            assert "What is Pokecut?" in questions.nth(0).inner_text(), "问题标题应始终保留"

        with allure.step("截图记录"):
            shot(page, "05FAQ展开收起")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("L2-004: 搜索命中结果列表 + 计数 + PC 竖向滚动")
    def test_l2_004_search_results_and_scroll(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 搜索命中时结果列表展示标题、摘要、所属分类并按相关度排序 / 搜索超过 5 条 PC 滚动
        覆盖层级: L2
        前置条件: 桌面端 /help
        测试步骤:
        1. 搜索 credits
        2. 断言结果结构
        3. 滚动结果容器到底
        预期结果: 结果留当前页，13 条含标题/摘要/分类，容器可竖向滚动查看全部
        """
        matrix_meta("L2-004")
        with allure.step("导航到 /help 并搜索 credits"):
            goto_help(page, base_url)
            do_search(page, "credits")

        with allure.step("断言结果列表结构"):
            assert page.url.rstrip("/").endswith("/help")
            pw_expect(page.locator("div.help-v2-search-panel__header-inner").first).to_contain_text("13 results for")
            results = page.locator("button.help-v2-search-panel__result")
            pw_expect(results).to_have_count(13)
            assert "credits" in results.first.inner_text().lower()

        with allure.step("断言结果容器可滚动"):
            dims = page.evaluate("() => { const el = document.querySelector('div.help-v2-search-panel__results'); return el ? {sh: el.scrollHeight, ch: el.clientHeight} : null; }")
            assert dims and dims["sh"] > dims["ch"], f"结果容器应可滚动，实际 {dims}"

        with allure.step("滚动到底并断言最后一条"):
            page.locator("div.help-v2-search-panel__results").evaluate("el => el.scrollTop = el.scrollHeight")
            page.wait_for_timeout(500)
            pw_expect(results.nth(12)).to_be_visible()

        with allure.step("截图记录"):
            shot(page, "06搜索命中与PC滚动")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("L2-005: 搜索无结果空态 + Submit a ticket")
    def test_l2_005_search_empty(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 搜索无结果时展示空态文案和提交工单入口
        覆盖层级: L2
        前置条件: 准备明确无匹配关键词 pokecut-unmatched-000
        测试步骤:
        1. 导航 /help
        2. 搜索 pokecut-unmatched-000
        3. 点击 Submit a ticket
        预期结果: 空态文案与工单弹窗承接
        """
        matrix_meta("L2-005")
        with allure.step("导航到 /help"):
            goto_help(page, base_url)
        with allure.step("搜索无匹配关键词"):
            do_search(page, "pokecut-unmatched-000")

        with allure.step("断言空态"):
            body = page.locator("body").inner_text()
            assert "0 results for" in body and "No answer found?" in body
            ticket = page.locator("button:has-text('Submit a ticket')").first
            pw_expect(ticket).to_be_visible()

        with allure.step("截图空态"):
            shot(page, "07搜索空态")

        with allure.step("点击 Submit a ticket 并断言弹窗"):
            vue_click(page, ticket)
            pw_expect(page.locator("div.purchase-order-dialog").first).to_be_visible(timeout=5000)

        with allure.step("截图工单弹窗"):
            shot(page, "07b工单弹窗")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("L2-006: 顶部 Contact us 深链自动定位并展开支持 FAQ")
    def test_l2_006_top_contact_deeplink(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 顶部联系支持入口跳转帮助页并自动展开支持 FAQ
        覆盖层级: L2
        前置条件: 打开任一非无限画布站内页面，顶部导航可见 Contact us
        测试步骤:
        1. 打开首页定位顶部 Contact us 链接
        2. 直接访问 Contact us 深链
        预期结果: 自动定位 Commercial, Safety & Support 并展开 How do I contact Pokecut support?
        """
        matrix_meta("L2-006")
        with allure.step("打开首页定位顶部 Contact us 链接"):
            page.goto(base_url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(6000)
            link = page.locator("a[href*='/help?category=commercial-safety-support']").first
            assert link.count() >= 1, "首页应存在 Contact us 深链入口"
            href = link.get_attribute("href") or ""
            assert "category=commercial-safety-support" in href and "question=commercial-safety-support-4" in href

        with allure.step("访问 Contact us 深链"):
            page.goto(f"{base_url}{href}", wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(8000)

        with allure.step("断言自动定位并展开"):
            active = page.locator("button.help-v2-faq-section__nav-item--active").first
            pw_expect(active).to_contain_text("Commercial, Safety & Support")
            open_q = page.locator("article.help-v2-faq-item--open button.help-v2-faq-item__question").first
            pw_expect(open_q).to_contain_text("How do I contact Pokecut support?")

        with allure.step("截图记录"):
            shot(page, "08Contact深链")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("L2-007: 底部 Contact us 弹工单弹窗")
    def test_l2_007_bottom_contact_dialog(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 底部支持区显示 Still have questions? 并可通过 Contact us 弹出工单
        覆盖层级: L2
        前置条件: 打开 /help 并滚动到底部
        测试步骤:
        1. 导航 /help 并滚动到底部
        2. 点击 Contact us
        预期结果: 底部文案可见，点击弹出工单弹窗
        """
        matrix_meta("L2-007")
        with allure.step("导航 /help 并滚动到底部"):
            goto_help(page, base_url)
            cta = page.locator("section.help-v2-support-cta-section").first
            cta.scroll_into_view_if_needed()
            pw_expect(page.locator("h2:has-text('Still have questions?')").first).to_be_visible()

        with allure.step("点击底部 Contact us"):
            vue_click(page, page.locator("button.help-v2-support-cta-section__button").first)

        with allure.step("断言工单弹窗"):
            dialog = page.locator("div.purchase-order-dialog").first
            pw_expect(dialog).to_be_visible(timeout=5000)
            text = dialog.inner_text()
            assert "Email" in text and "Submit" in text

        with allure.step("截图记录"):
            shot(page, "09工单弹窗")


# ═══════════════════════════════════════════════════════════════
# L3 异常 / 权限 / 兼容
# ═══════════════════════════════════════════════════════════════

@allure.feature("帮助中心")
@allure.epic("帮助中心")
@allure.story("L3-异常与权限")
class TestL3Compat:

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("L3-001: 移动端窄屏布局 + 移动搜索滚动")
    def test_l3_001_mobile_layout_and_search(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 移动端帮助页按窄屏布局展示分类卡片、分类标签和 FAQ / 搜索超过 5 条移动滚动
        覆盖层级: L3
        前置条件: 移动端 /help
        测试步骤:
        1. 移动视口打开 /help
        2. 点击 Getting Started
        3. 搜索 credits
        预期结果: 卡片 2 列、横向标签、单列 FAQ、无左侧栏、默认展开第一条、移动搜索可滚动
        """
        matrix_meta("L3-001")
        with allure.step("移动视口打开 /help"):
            goto_help_mobile(page, base_url)

        with allure.step("断言卡片 2 列"):
            pw_expect(page.locator("button.help-v2-mobile-category-card")).to_have_count(6)
            cols = page.evaluate("() => { const g = document.querySelector('div[class*=\"category-section\"] div[class*=\"grid\"], div[class*=\"category-section__grid\"]'); return g ? getComputedStyle(g).gridTemplateColumns.trim().split(/\\s+/).length : 0; }")
            assert cols == 2, f"分类卡片应 2 列，实际列数 {cols}"

        with allure.step("点击分类并断言横向标签与单列 FAQ"):
            card = page.locator("button.help-v2-mobile-category-card:has-text('Getting Started')").first
            vue_click(page, card)
            scrollable = page.evaluate("() => { const t = document.querySelector('div.help-v2-mobile-faq-section__tabs'); return t ? t.scrollWidth > t.clientWidth + 5 : false; }")
            assert scrollable, "分类标签容器应可横向滑动"
            active_tab = page.locator("button.help-v2-mobile-faq-section__tab--active").first
            pw_expect(active_tab).to_contain_text("Getting Started")
            left_nav = page.locator("button.help-v2-faq-section__nav-item").first
            assert not left_nav.is_visible(), "移动端不应显示 PC 左侧固定分类栏"
            assert page.locator("button.help-v2-mobile-faq-item__question").count() == 5, "Getting Started 应 5 条 FAQ"
            first_open = page.locator("[class~='help-v2-mobile-faq-item']").first
            assert "--open" in (first_open.get_attribute("class") or ""), "第一条应默认展开"

        with allure.step("搜索 credits 并断言移动结果可滚动"):
            do_search(page, "credits")
            dims = page.evaluate("() => { const el = document.querySelector('div.help-v2-mobile-search-panel__results'); return el ? {sh: el.scrollHeight, ch: el.clientHeight} : null; }")
            assert dims and dims["sh"] > dims["ch"], f"移动端结果容器应可滚动，实际 {dims}"

        with allure.step("截图记录"):
            shot(page, "11移动布局与搜索")


# ═══════════════════════════════════════════════════════════════
# L5 数据边界与等价类
# ═══════════════════════════════════════════════════════════════

@allure.feature("帮助中心")
@allure.epic("帮助中心")
@allure.story("L5-数据边界元素")
class TestL5Boundary:

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("L5-001: 搜索结果数量等价类（1/4 条）")
    def test_l5_001_search_count_boundary(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 搜索命中时结果列表展示标题、摘要、所属分类并按相关度排序
        覆盖层级: L5
        前置条件: 准备不同命中数量的关键词
        测试步骤:
        1. 搜索 language（1 条）
        2. 搜索 download（4 条）
        预期结果: 计数文案精确命中对应数量
        """
        matrix_meta("L5-001")
        for keyword, expected in SEARCH_COUNTS:
            with allure.step(f"导航 /help 并搜索 {keyword}"):
                goto_help(page, base_url)
                do_search(page, keyword)

            with allure.step(f"断言 {keyword} 计数文案"):
                body = page.locator("body").inner_text()
                assert expected in body, f"应出现 {expected}，实际页面片段: {body[:300]}"

            with allure.step(f"截图 {keyword}"):
                shot(page, f"13搜索计数-{keyword}")


# ═══════════════════════════════════════════════════════════════
# L6 核心 Happy Path / E2E
# ═══════════════════════════════════════════════════════════════

@allure.feature("帮助中心")
@allure.epic("帮助中心")
@allure.story("L6-核心链路元素")
class TestL6Smoke:

    @pytest.mark.no_login
    @pytest.mark.smoke
    @allure.severity(allure.severity_level.CRITICAL)
    @allure.title("L6-001: 核心链路 smoke（分类卡片入口）")
    def test_l6_001_smoke(self, page: Page, base_url: str):
        """PRD引用: help 页优化需求文档 - 整体链路 / 点击分类后留在当前帮助页并切换到对应问题列表
        覆盖层级: L6
        前置条件: 打开 /help
        测试步骤:
        1. 导航 /help 并断言 Hero H1
        2. 点击 Getting Started 分类卡片
        3. 搜索 download
        4. 滚动到底部 CTA
        预期结果: Hero、分类卡片入口、搜索、底部 CTA 全链路正常
        """
        matrix_meta("L6-001")
        with allure.step("导航 /help 并断言 Hero H1"):
            goto_help(page, base_url)
            pw_expect(page.locator("h1").first).to_contain_text("How can we help you create faster?")

        with allure.step("点击 Getting Started 分类卡片并断言 FAQ 默认展开"):
            card = page.locator("button.help-v2-category-card:has-text('Getting Started')").first
            vue_click(page, card)
            active = page.locator("button.help-v2-faq-section__nav-item--active").first
            pw_expect(active).to_contain_text("Getting Started")
            first_item = page.locator("article.help-v2-faq-item").first
            assert "--open" in (first_item.get_attribute("class") or "")

        with allure.step("搜索 download 并断言计数"):
            do_search(page, "download")
            body = page.locator("body").inner_text()
            assert "4 results for" in body

        with allure.step("滚动到底部并断言 CTA"):
            cta = page.locator("section.help-v2-support-cta-section").first
            cta.scroll_into_view_if_needed()
            pw_expect(page.locator("h2:has-text('Still have questions?')").first).to_be_visible()

        with allure.step("截图记录"):
            shot(page, "14smoke")
