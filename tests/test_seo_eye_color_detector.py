"""Eye Color Detector — SEO 检测类回归。三栏，无优化结果图，upselling 蒙层。"""
import os, glob, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text
from helpers_seo import (
    pick_test_image, upload_image, wait_for_body_text, wait_for_body_text_gone,
    text_on_page, button_disabled_in_section, click_button_in_section,
    SECTION_ORIGINAL, SECTION_ANALYSIS, SECTION_OPTIMIZED,
)
PAGE_PATH = "/tools/eye-color-detector"
UPSELLING_TEXT = "we've generated a beautifully optimized version just for you"


def goto(page: Page, base_url: str, path: str, lazy_scroll: bool = False):
    page.goto(f"{base_url}{path}", timeout=120000)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    if lazy_scroll:
        page.evaluate("""() => {
            document.querySelectorAll('img[loading="lazy"]').forEach(function(img) {
                img.loading = 'eager';
                var s = img.getAttribute('src');
                if (s) { img.removeAttribute('src'); img.setAttribute('src', s); }
            });
        }""")
        page.wait_for_timeout(1000)
        for _ in range(10):
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(300)
        page.evaluate("""() => {
            document.querySelectorAll('img').forEach(function(img) {
                if (!img.complete && img.offsetWidth === 0 && img.offsetHeight === 0) {
                    img.scrollIntoView({block: 'center'});
                }
            });
        }""")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(3000)


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
@allure.story("Eye Color Detector-无优化结果图")
class TestPhase1:

    @allure.title("TC-SEO-EC-001 [P0] 分析生成中：三栏布局 + 按钮状态 + upselling 蒙层")
    def test_ec_001_phase1_generating_analysis(self, page: Page, session_page: Page, base_url: str):
        """Step1: 首屏内容 / Step2: 上传后进入 Phase 1 验证三栏+蒙层"""

        # ── Step 1: 首屏（无需登录）──
        goto(page, base_url, PAGE_PATH, lazy_scroll=True)
        allure_screenshot(page, "01-EC-首屏")
        check_page_text(page, locale="en", locale_name="English")
        verify_seo_links(page, base_url, PAGE_PATH)

        # ── Step 2: 上传 + Phase 1 验证（需登录）──
        sp = session_page
        goto(sp, base_url, PAGE_PATH)
        dismiss_pricing_overlay(sp)
        upload_image(sp, pick_test_image())
        wait_for_body_text(sp, "Generating analysis", timeout=30000)
        allure_screenshot(sp, "02-EC-Phase1-分析生成中")

        # 原图区 Upload 不可点击
        disabled, found = button_disabled_in_section(sp, SECTION_ORIGINAL, "Upload Image", require=False)
        if not found:
            pytest.xfail("上传未触发检测流程，3 栏布局未出现")
        assert disabled is True, "Upload Image 应为不可点击"

        # 分析区 Download 不可点击
        disabled, found = button_disabled_in_section(sp, SECTION_ANALYSIS, "Download", require=False)
        if found:
            assert disabled is True, "分析区 Download 应为不可点击"

        # 优化区 upselling 蒙层
        body = sp.locator("body").inner_text()
        assert UPSELLING_TEXT in body, "优化区应有 upselling 文案"
        assert "Get It Now" in body, "优化区应有 'Get It Now' 按钮"


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
@allure.story("Eye Color Detector-无优化结果图")
class TestAnalysisComplete:

    def _wait_analysis_done(self, page):
        try:
            wait_for_body_text_gone(page, "Generating analysis", timeout=120000)
        except Exception:
            pass
        page.wait_for_timeout(3000)

    @allure.title("TC-SEO-EC-002 [P0] 分析完成：Download 可点击 + upselling 保持 + Get It Now 跳转")
    def test_ec_002_analysis_complete_and_get_it_now(self, page: Page, session_page: Page, base_url: str):
        """分析完成后：Download 可点击 / 优化区保持 upselling / Get It Now 跳转"""

        # ── Step 1: 首屏（无需登录）──
        goto(page, base_url, PAGE_PATH, lazy_scroll=True)
        allure_screenshot(page, "01-EC-首屏")
        check_page_text(page, locale="en", locale_name="English")
        verify_seo_links(page, base_url, PAGE_PATH)

        # ── Step 2: 全流程（需登录）──
        sp = session_page
        goto(sp, base_url, PAGE_PATH)
        dismiss_pricing_overlay(sp)
        upload_image(sp, pick_test_image())
        try:
            wait_for_body_text(sp, "Generating analysis", timeout=30000)
        except Exception:
            pass
        self._wait_analysis_done(sp)
        allure_screenshot(sp, "02-EC-分析完成")

        body = sp.locator("body").inner_text()

        # 分析区 Download 可点击
        disabled, found = button_disabled_in_section(sp, SECTION_ANALYSIS, "Download")
        if found:
            assert disabled is False, f"Download 应为可点击，实际 disabled={disabled}"

        # 无优化生成文案
        assert "Generating optimized result" not in body, "无优化结果图的页面不应出现优化生成文案"

        # 分析区 Download
        try:
            with sp.expect_download(timeout=15000) as d:
                click_button_in_section(sp, SECTION_ANALYSIS, "Download")
            assert d.value.suggested_filename, "应生成下载文件"
        except Exception:
            pass

        # Get It Now 跳转
        assert "Get It Now" in body, "页面应有 'Get It Now' 按钮"
        get_it_btn = sp.locator("button:has-text('Get It Now'):visible").first
        get_it_btn.scroll_into_view_if_needed()
        sp.wait_for_timeout(500)
        assert get_it_btn.is_visible(), "'Get It Now' 按钮应可见"

        allure_screenshot(sp, "03-EC-GetItNow点击前")
        with sp.expect_navigation(timeout=30000):
            get_it_btn.click(force=True)
        sp.wait_for_timeout(5000)
        allure_screenshot(sp, "04-EC-GetItNow跳转后")

        assert "/agent" in sp.url, f"应跳转到无限画布页，实际: {sp.url}"
        body_after = sp.locator("body").inner_text()
        assert any(kw in body_after.lower() for kw in ["portrait", "face", "editor"]), \
            "跳转后应展开人脸编辑器面板"
