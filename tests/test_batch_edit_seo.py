"""批量编辑SEO — 4 页面参数化：首屏无试用图 + 上传跳转 + tab 高亮 AI 审查。"""
import os, glob, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay, visual_assert
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text


def pick_test_image():
    d = os.path.join(os.path.dirname(__file__), "..", "test_images")
    if os.path.isdir(d):
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        if imgs:
            return os.path.abspath(imgs[0])


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


# (path, title_kw, tab_name)
PAGES = [
    pytest.param("/batch-edit/bulk-background-remover", "Background Remove", "背景移除tab", id="bulk-background-remover"),
    pytest.param("/batch-edit/bulk-background-changer", "Background Change", "背景更改tab", id="bulk-background-changer"),
    pytest.param("/batch-edit/bulk-image-enhancer", "Image Enhancer", "画质增强tab", id="bulk-image-enhancer"),
    pytest.param("/batch-edit/bulk-image-resizer", "Image Resizer", "resizer tab", id="bulk-image-resizer"),
]


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
class TestBatchEditSEO:

    @pytest.mark.parametrize("path,title_kw,tab_name", PAGES)
    def test_batch_edit_seo(self, page: Page, session_page: Page, base_url: str, path, title_kw, tab_name):
        allure.dynamic.title(f"[P0] {tab_name} — 首屏无试用图 + 上传跳转 + tab高亮AI审查")

        # ── Step 1: 首屏验证（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, f"01-{path.split('/')[-1]}-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert title_kw in page.title(), f"Title 应含 '{title_kw}'，实际: {page.title()[:60]}"
        # 断言无试用图区域
        body = page.locator("body").inner_text()
        # 试用图区域通常有 "Try It Now" / "Try for Free" / "Demo" 等文案
        has_try_area = any(kw in body for kw in ["Try It Now", "Try for Free", "Demo Image", "Try Demo"])
        if has_try_area:
            if "image-enhancer" in path:
                pytest.xfail("bulk-image-enhancer 页面有试用图区域，与其他批量编辑页不同")
            pytest.fail(f"首屏不应有试用图区域，body[:300]: {body[:300]}")
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 上传 → 跳转画布页（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        sp.locator("input[type=file]").first.set_input_files(pick_test_image())
        sp.wait_for_timeout(15000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, f"02-{path.split('/')[-1]}-上传后")
        assert "/batch-edit/edit" in sp.url, f"上传后应进入批量编辑页，实际: {sp.url}"
        assert "pid=" in sp.url, f"URL 应含 pid 参数，实际: {sp.url}"

        # ── Step 3: AI 视觉审查 tab 是否高亮 ──
        vis = visual_assert(
            before_name=f"01-{path.split('/')[-1]}-首屏",
            after_name=f"02-{path.split('/')[-1]}-上传后",
            expectation=f"批量编辑画布页中，{tab_name}是否处于蓝色高亮选中状态",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")
        assert vis["verdict"] == "pass", \
            f"AI 视觉审查未通过({tab_name}): {vis.get('reason', vis)}"
