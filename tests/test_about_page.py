"""About 页面回归测试 — 12 条用例覆盖六板块：SEO 标题、首屏 Hero、CTA 按钮、
图文内容板块、功能卡片、视频属性、多语言。

页面所有交互元素均为 <a> 标签（非 Vue 组件按钮），pytest-playwright 可直接 click()。
两个 CTA 按钮文案相同 ("Start creating now")，用 .first / .last 区分 Hero/底部。
"""
import pytest
import allure
from playwright.sync_api import Page, expect as pw_expect
from conftest import allure_screenshot


# ── 工具函数 ──────────────────────────────────────────────────

def goto_about(page: Page, base_url: str, lang: str = "en"):
    """导航到 About 页面并等待客户端渲染完成。"""
    path = "/zh/about" if lang == "zh" else "/about"
    page.goto(f"{base_url}{path}", timeout=120000)
    # SPA 页面：先等网络空闲，再给 Vue 水合留出时间
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(5000)


# ── 测试数据 ──────────────────────────────────────────────────

# 信任数据板块 4 项数据
TRUST_VALUES = ["1M+", "50+", "100M+", "#2"]
TRUST_LABELS = ["Users Worldwide", "AI Tools", "Photos Processed", "Product Hun"]

# 功能展示卡片
FEATURE_CARDS = ["AI Images", "Photo Enhancer", "Portrait Editing"]

# CTA 按钮文案
CTA_TEXT = "Start creating now"

# Pixl Concerto 外链
PIXL_CONCERTO_HREF = "https://www.pixlconcerto.com/"

# SEO 标题
TITLE_EN = "About Pokecut - AI Photo Editor for Effortless Visual Creation"
TITLE_ZH_FRAGMENT = "关于 Pokecut"


# ═══════════════════════════════════════════════════════════════
# 测试类
# ═══════════════════════════════════════════════════════════════

@allure.epic("主流程回归")
@allure.feature("功能回归")
@allure.story("about页")
@pytest.mark.regression
class TestAboutPage:

    # ── 一、SEO 与首屏 Hero ──────────────────────────────────

    def test_about_001_seo_title(self, page: Page, base_url: str):
        """TC-ABOUT-001 [P0] 页面 SEO 标题正确"""
        allure.dynamic.title("[P0] 页面 SEO 标题 — /about 标题包含完整英文 SEO 文案")
        goto_about(page, base_url)
        allure_screenshot(page, "01-SEO标题-EN")

        title = page.title()
        assert TITLE_EN in title, \
            f"页面标题应包含 '{TITLE_EN}'，实际标题: {title}"

    def test_about_002_hero_content(self, page: Page, base_url: str):
        """TC-ABOUT-002 [P0] 首屏 Hero 文案存在：标签/标题/描述"""
        allure.dynamic.title("[P0] 首屏 Hero 文案 — 标签/标题/描述均可见")
        goto_about(page, base_url)
        allure_screenshot(page, "02-首屏Hero")

        body = page.locator("body").inner_text()

        # 标签: "About Pokecut"
        assert "About Pokecut" in body, \
            f"页面应包含标签文案 'About Pokecut'，页面文本前300字符: {body[:300]}"

        # H1: "Creative images, made effortless."
        assert "Creative images, made effortless." in body, \
            f"页面应包含 H1 标题 'Creative images, made effortless.'，页面文本前300字符: {body[:300]}"

        # 描述: 包含关键片段
        desc_found = ("Pokecut helps anyone turn everyday photos into polished visuals" in body or
                      "turn everyday photos" in body)
        assert desc_found, \
            f"页面应包含描述文案（'turn everyday photos into polished visuals'），页面文本前500字符: {body[:500]}"

    def test_about_003_hero_cta_click(self, page: Page, base_url: str):
        """TC-ABOUT-003 [P0] 首屏 Hero CTA 按钮点击跳转 /create"""
        allure.dynamic.title("[P0] 首屏 Hero CTA 点击 — 跳转 /create")
        goto_about(page, base_url)

        cta = page.locator(f"a:has-text('{CTA_TEXT}')").first
        pw_expect(cta).to_be_visible(timeout=10000)
        allure_screenshot(page, "03-HeroCTA-点击前")

        cta.click()
        page.wait_for_timeout(5000)
        allure_screenshot(page, "03-HeroCTA-点击后")

        assert "/create" in page.url, \
            f"点击 Hero CTA 后应跳转到 /create，实际 URL: {page.url}"

    # ── 二、信任数据板块 ──────────────────────────────────

    def test_about_004_trust_data(self, page: Page, base_url: str):
        """TC-ABOUT-004 [P0] 信任数据板块 4 项数据存在"""
        allure.dynamic.title("[P0] 信任数据板块 — 4 项数据与标签均存在")
        goto_about(page, base_url)
        allure_screenshot(page, "04-信任数据板块")

        body = page.locator("body").inner_text()

        # 验证 4 项数值
        for val in TRUST_VALUES:
            assert val in body, \
                f"信任数据板块应包含数值 '{val}'，页面文本前500字符: {body[:500]}"

        # 验证 4 项标签
        for label in TRUST_LABELS:
            assert label in body, \
                f"信任数据板块应包含标签 '{label}'，页面文本前500字符: {body[:500]}"

    # ── 三、图文内容板块 ──────────────────────────────────

    def test_about_005_image_text_section_1(self, page: Page, base_url: str):
        """TC-ABOUT-005 [P1] 图文板块 1：标题与正文存在"""
        allure.dynamic.title("[P1] 图文板块 1 — 'Built for the moments' 标题与正文")
        goto_about(page, base_url)
        allure_screenshot(page, "05-图文板块1")

        body = page.locator("body").inner_text()

        # 标题
        assert "Built for the moments you need a better image." in body, \
            f"图文板块 1 应包含标题 'Built for the moments you need a better image.'，页面文本前800字符: {body[:800]}"

        # 正文片段
        body_found = ("product listings" in body or "profile photos" in body)
        assert body_found, \
            f"图文板块 1 正文应包含 'product listings' 或 'profile photos'，页面文本前800字符: {body[:800]}"

    def test_about_006_pixl_concerto_link(self, page: Page, base_url: str):
        """TC-ABOUT-006 [P1] 图文板块 2：标题/正文 + Pixl Concerto 外链"""
        allure.dynamic.title("[P1] 图文板块 2 — Pixl Concerto 外链 href/target 验证")
        goto_about(page, base_url)
        allure_screenshot(page, "06-PixlConcerto外链")

        body = page.locator("body").inner_text()

        # 标题
        assert "Powered by Pixl Concerto's imaging expertise." in body, \
            f"图文板块 2 应包含标题 'Powered by Pixl Concerto's imaging expertise.'，页面文本前800字符: {body[:800]}"

        # Pixl Concerto 链接
        pixl_link = page.locator("a:has-text('Pixl Concerto')").first
        pw_expect(pixl_link).to_be_visible(timeout=10000)

        href = pixl_link.get_attribute("href") or ""
        assert href == PIXL_CONCERTO_HREF, \
            f"Pixl Concerto 链接 href 应为 '{PIXL_CONCERTO_HREF}'，实际值: {href}"

        target = pixl_link.get_attribute("target") or ""
        assert target == "_blank", \
            f"Pixl Concerto 链接 target 应为 '_blank'，实际值: {target}"

    def test_about_007_image_text_section_3(self, page: Page, base_url: str):
        """TC-ABOUT-007 [P1] 图文板块 3：标题与正文存在（移动端可用）"""
        allure.dynamic.title("[P1] 图文板块 3 — 'Create anywhere with Pokecut on mobile' 标题与正文")
        goto_about(page, base_url)
        allure_screenshot(page, "07-图文板块3")

        body = page.locator("body").inner_text()

        # 标题
        assert "Create anywhere with Pokecut on mobile." in body, \
            f"图文板块 3 应包含标题 'Create anywhere with Pokecut on mobile.'，页面文本前1000字符: {body[:1000]}"

        # 正文片段：iOS 或 Android
        mobile_found = ("iOS" in body or "Android" in body)
        assert mobile_found, \
            f"图文板块 3 正文应包含 'iOS' 或 'Android'，页面文本前1000字符: {body[:1000]}"

    def test_about_008_image_text_section_4(self, page: Page, base_url: str):
        """TC-ABOUT-008 [P1] 图文板块 4：标题与正文存在（网站更新历程）"""
        allure.dynamic.title("[P1] 图文板块 4 — 'A web experience that keeps evolving' 时间线内容")
        goto_about(page, base_url)
        allure_screenshot(page, "08-图文板块4")

        body = page.locator("body").inner_text()

        # 标题
        assert "A web experience that keeps evolving." in body, \
            f"图文板块 4 应包含标题 'A web experience that keeps evolving.'，页面文本前1200字符: {body[:1200]}"

        # 时间线内容
        timeline_found = ("November 2024" in body or "Pokecut officially launched" in body)
        assert timeline_found, \
            f"图文板块 4 应包含时间线内容 'November 2024' 或 'Pokecut officially launched'，页面文本前1200字符: {body[:1200]}"

    # ── 四、功能展示卡片 ──────────────────────────────────

    def test_about_009_feature_cards(self, page: Page, base_url: str):
        """TC-ABOUT-009 [P0] 功能展示 3 张卡片均可点击 → /create"""
        allure.dynamic.title("[P0] 功能展示卡片 — 3 张卡片标题/href 验证（不实际点击）")
        goto_about(page, base_url)
        allure_screenshot(page, "09-功能展示卡片")

        body = page.locator("body").inner_text()

        for card_title in FEATURE_CARDS:
            # 卡片标题可见
            assert card_title in body, \
                f"功能卡片标题 '{card_title}' 应存在于页面文本中"

            # 卡片的外层 <a> href 为 /create
            # 通过 h3 文本定位卡片，再取父级 <a> 的 href
            card_link = page.locator(f"a:has(h3:has-text('{card_title}'))").first
            # 如果上述选择器找不到，回退到直接用文本定位包含标题的 <a>
            if card_link.count() == 0:
                card_link = page.locator(f"a:has-text('{card_title}')").first
            pw_expect(card_link).to_be_visible(timeout=5000)

            href = card_link.get_attribute("href") or ""
            assert href == "/create", \
                f"功能卡片 '{card_title}' 的 href 应为 '/create'，实际值: {href}"

    # ── 五、底部 CTA ──────────────────────────────────────

    def test_about_010_bottom_cta_click(self, page: Page, base_url: str):
        """TC-ABOUT-010 [P0] 底部 CTA 按钮点击跳转 /create"""
        allure.dynamic.title("[P0] 底部 CTA 点击 — 跳转 /create")
        goto_about(page, base_url)

        cta = page.locator(f"a:has-text('{CTA_TEXT}')").last
        pw_expect(cta).to_be_visible(timeout=10000)

        # 先滚动到底部 CTA 可见
        cta.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        allure_screenshot(page, "10-底部CTA-点击前")

        cta.click()
        page.wait_for_timeout(5000)
        allure_screenshot(page, "10-底部CTA-点击后")

        assert "/create" in page.url, \
            f"点击底部 CTA 后应跳转到 /create，实际 URL: {page.url}"

    # ── 六、视频属性 ──────────────────────────────────────

    def test_about_011_video_attributes(self, page: Page, base_url: str):
        """TC-ABOUT-011 [P1] 首屏视频属性：autoplay/loop/muted/无controls/封面图"""
        allure.dynamic.title("[P1] 首屏视频属性 — autoplay/loop/muted/controls/封面图完整检查")
        goto_about(page, base_url)
        allure_screenshot(page, "11-视频属性")

        # (1) <video> 元素存在
        video = page.locator("video").first
        pw_expect(video).to_be_visible(timeout=10000)

        # (2) video.loop 为 true
        loop = page.evaluate("document.querySelector('video').loop")
        assert loop is True, f"视频 loop 属性应为 true，实际值: {loop}"

        # (3) video.muted 为 true
        muted = page.evaluate("document.querySelector('video').muted")
        assert muted is True, f"视频 muted 属性应为 true，实际值: {muted}"

        # (4) video.controls 为 false（属性缺失）
        controls = page.evaluate("document.querySelector('video').controls")
        assert controls is False, f"视频 controls 属性应为 false（不显示控制条），实际值: {controls}"

        # (5) video.autoplay JS 属性（通过 evaluate 检查，因为 Vue 可能通过 JS 动态设置）
        autoplay = page.evaluate("document.querySelector('video').autoplay")
        if not autoplay:
            # ISSUE #2: <video> 缺少 autoplay HTML 属性，JS 属性也可能为 false
            pytest.xfail(
                "ISSUE #2: 视频 autoplay JS 属性为 false，"
                "HTML 属性缺失且 Vue 可能未动态设置。"
            )
        assert autoplay is True, f"视频 autoplay JS 属性应为 true，实际值: {autoplay}"

        # (6) 存在封面图 img[src*="abouthandle.webp"]
        cover_img = page.locator('img[src*="abouthandle.webp"]')
        pw_expect(cover_img.first).to_be_visible(timeout=5000)

    # ── 七、多语言 (i18n) ──────────────────────────────────

    def test_about_012_zh_i18n(self, page: Page, base_url: str):
        """TC-ABOUT-012 [P1] 中文版 /zh/about i18n 正确渲染"""
        allure.dynamic.title("[P1] 中文版 i18n — /zh/about 标题/CJK/标签")
        goto_about(page, base_url, lang="zh")
        page.wait_for_timeout(3000)
        allure_screenshot(page, "12-ZH中文版")

        # (1) document.title 包含中文关键片段
        title = page.title()
        assert TITLE_ZH_FRAGMENT in title, \
            f"中文版页面标题应包含 '{TITLE_ZH_FRAGMENT}'，实际标题: {title}"

        # (2) 页面可见文本包含中文内容（CJK 字符）
        body = page.locator("body").inner_text()
        has_cjk = any('一' <= c <= '鿿' or '㐀' <= c <= '䶿'
                      for c in body)
        assert has_cjk, \
            f"中文版页面应包含 CJK 字符（中文内容），页面文本前500字符: {body[:500]}"

        # (3) 关键中文标签可见（中文版标签无空格："关于Pokecut"）
        assert "关于Pokecut" in body or "关于 Pokecut" in body, \
            f"中文版页面应包含标签 '关于Pokecut' 或 '关于 Pokecut'，页面文本前500字符: {body[:500]}"
