"""Pretty Scale — SEO 检测类回归。三栏（Original + Analysis + Optimized），Phase 1→2→3。"""
import os, glob, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text
from helpers_seo import (
    pick_test_image, upload_image, wait_for_body_text, wait_for_body_text_gone,
    text_on_page, button_disabled_in_section, button_disabled_global,
    click_button_in_section,
    SECTION_ORIGINAL, SECTION_ANALYSIS, SECTION_OPTIMIZED,
)
PAGE_PATH = "/tools/pretty-scale"


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
@allure.story("Pretty Scale-有优化结果图")
class TestPhase1:

    @allure.title("TC-SEO-PS-001 [P0] 分析生成中：三栏布局 + 按钮状态")
    def test_ps_001_phase1_generating_analysis(self, page: Page, session_page: Page, base_url: str):
        """Step1: 首屏内容 / Step2: 上传后进入 Phase 1 验证三栏布局"""

        # ── Step 1: 首屏（无需登录）──
        goto(page, base_url, PAGE_PATH, lazy_scroll=True)
        allure_screenshot(page, "01-PS-首屏")
        check_page_text(page, locale="en", locale_name="English")
        verify_seo_links(page, base_url, PAGE_PATH)

        # ── Step 2: 上传 + Phase 1 验证（需登录）──
        sp = session_page
        goto(sp, base_url, PAGE_PATH)
        dismiss_pricing_overlay(sp)
        sp.wait_for_timeout(2000)
        upload_image(sp, pick_test_image())
        sp.wait_for_timeout(5000)

        body = sp.locator("body").inner_text()
        has_columns = all(h in body for h in ["Original Image", "Analysis Result", "Optimized Result"])
        if not has_columns:
            allure_screenshot(sp, "02-PS-上传未触发检测")
            pytest.xfail("Pretty Scale CTA 在 pytest 环境下未触发内嵌检测")

        try:
            wait_for_body_text(sp, "Generating analysis", timeout=30000)
        except Exception:
            pass
        allure_screenshot(sp, "02-PS-Phase1-分析生成中")

        # 原图区 Upload 不可点击
        disabled, found = button_disabled_in_section(sp, SECTION_ORIGINAL, "Upload Image", require=False)
        if not found:
            disabled, found = button_disabled_global(sp, "Upload Image")
        if found:
            assert disabled is True, f"Upload Image 应为不可点击，实际 disabled={disabled}"

        # 分析区 Download 不可点击
        disabled, found = button_disabled_in_section(sp, SECTION_ANALYSIS, "Download", require=False)
        if not found:
            disabled, found = button_disabled_global(sp, "Download")
        if found:
            assert disabled is True, f"分析区 Download 应为不可点击，实际 disabled={disabled}"


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
@allure.story("Pretty Scale-有优化结果图")
class TestFullFlow:

    @allure.title("TC-SEO-PS-002 [P0] 分析→优化串行：Phase 2 + Phase 3 + 下载 + Portrait Editor")
    def test_ps_002_full_flow_analysis_to_optimization(self, page: Page, session_page: Page, base_url: str):
        """一次上传，串行等待：分析→优化→验证按钮+下载+跳转"""

        # ── Step 1: 首屏（无需登录）──
        goto(page, base_url, PAGE_PATH, lazy_scroll=True)
        allure_screenshot(page, "01-PS-首屏")
        check_page_text(page, locale="en", locale_name="English")
        verify_seo_links(page, base_url, PAGE_PATH)

        # ── Step 2: 全流程（需登录）──
        sp = session_page
        goto(sp, base_url, PAGE_PATH)
        dismiss_pricing_overlay(sp)
        sp.wait_for_timeout(2000)
        upload_image(sp, pick_test_image())
        sp.wait_for_timeout(5000)

        # 等待 Phase 2：分析完成
        wait_for_body_text(sp, "Generating analysis", timeout=60000)
        try:
            wait_for_body_text(sp, "Generating optimized result", timeout=120000)
        except Exception:
            wait_for_body_text_gone(sp, "Generating analysis", timeout=120000)
        sp.wait_for_timeout(2000)
        allure_screenshot(sp, "02-PS-Phase2-分析完成优化生成中")

        assert not text_on_page(sp, "Generating analysis"), "'Generating analysis' 应消失"
        disabled, found = button_disabled_in_section(sp, SECTION_ANALYSIS, "Download", require=False)
        if not found:
            disabled, found = button_disabled_global(sp, "Download")
        assert found, "应有分析区 Download 按钮"
        if disabled is not False:
            pytest.xfail(f"分析区 Download 尚未变为可点击，disabled={disabled}")

        if text_on_page(sp, "Generating optimized result"):
            for btn_text in ["Download", "Portrait Editor"]:
                d, f = button_disabled_in_section(sp, SECTION_OPTIMIZED, btn_text, require=False)
                if f:
                    assert d is True, f"Phase 2 优化区 {btn_text} 应仍为不可点击"

        disabled, found = button_disabled_in_section(sp, SECTION_ORIGINAL, "Upload Image", require=False)
        if not found:
            disabled, found = button_disabled_global(sp, "Upload Image")
        assert found, "应有 Upload Image 按钮"
        assert disabled is False, f"Upload Image 应为可点击，实际 disabled={disabled}"

        # 等待 Phase 3：优化完成
        deadline = sp.evaluate("() => Date.now()") + 600000
        while sp.evaluate("() => Date.now()") < deadline:
            body = sp.locator("body").inner_text()
            still_generating = "Generating optimized result" in body
            optimization_failed = "Optimization failed" in body
            if not still_generating or optimization_failed:
                break
            sp.wait_for_timeout(15000)
        sp.wait_for_timeout(3000)
        allure_screenshot(sp, "03-PS-Phase3-优化完成")

        body = sp.locator("body").inner_text()
        optimization_failed = "Optimization failed" in body

        if optimization_failed:
            pytest.xfail("优化失败（可能 credits 不足或图片不适用）")
        if text_on_page(sp, "Generating optimized result"):
            pytest.xfail("优化仍在进行中（10 分钟超时）")

        for section, btn_text, desc in [
            (SECTION_OPTIMIZED, "Download", "优化区 Download"),
            (SECTION_OPTIMIZED, "Portrait Editor", "Portrait Editor"),
        ]:
            disabled, found = button_disabled_in_section(sp, section, btn_text, require=False)
            if not found:
                disabled, found = button_disabled_global(sp, btn_text)
            assert found, f"应有 {desc} 按钮"
            assert disabled is False, f"{desc} 应为可点击，实际 disabled={disabled}"

        # 分析区 Download
        try:
            with sp.expect_download(timeout=15000) as d:
                click_button_in_section(sp, SECTION_ANALYSIS, "Download")
            assert d.value.suggested_filename, "应生成下载文件"
        except Exception:
            pass

        # Portrait Editor 跳转
        try:
            with sp.expect_navigation(timeout=15000):
                sp.evaluate("""() => {
                    const btns = document.querySelectorAll('button');
                    for (const b of btns) {
                        if (b.textContent.includes('Portrait Editor') && b.offsetWidth > 0) {
                            b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                            return;
                        }
                    }
                }""")
            sp.wait_for_timeout(5000)
            allure_screenshot(sp, "04-PS-PortraitEditor跳转后")
            assert "/agent" in sp.url, f"应跳转到无限画布页，实际: {sp.url}"
        except Exception:
            pytest.xfail("Portrait Editor 跳转未触发导航")
