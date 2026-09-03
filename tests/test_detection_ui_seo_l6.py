"""检测类功能适配 UI —— L6 核心 Happy Path / E2E 冒烟测试。

覆盖 cases.md（new_feature_detection_ui_20260901_124711，仅 L6）：
- L6-001 face 全流程：登录→上传→双图生成→双下载→PC Continue
- L6-002 nose 全流程：登录→上传→分析成功→模糊承接→Get It Now

环境：测试服失败时按 PROJECT.md 通过 DEBUG 面板切「预部署」并重新登录，
账号 450832596@qq.com / 验证码 123456；素材 test_images/有人脸.JPG。
用户已确认 skip：BUG-NOSE-001、BUG-FACE-MOBILE-001。
"""
import os
import pathlib
import re

import allure
import pytest
from playwright.sync_api import Page

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG_FACE = str(ROOT / "test_images" / "有人脸.JPG")

EMAIL = os.environ.get("POKECUT_TEST_EMAIL", "450832596@qq.com")
CODE = os.environ.get("POKECUT_TEST_CODE", "123456")

PAGE_NOSE = "/tools/nose-shape-detector"
PAGE_FACE = "/tools/ai-face-reader"


# ── Vue 交互辅助 ───────────────────────────────────────────────

def coord_click(page: Page, locator, label: str = ""):
    """Vue 控件优先坐标点击。"""
    locator.scroll_into_view_if_needed(timeout=10000)
    page.wait_for_timeout(200)
    box = locator.bounding_box(timeout=10000)
    assert box, f"无 bounding box: {label or locator}"
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(300)


def upload_file(page: Page, locator, path: str):
    """通过真实按钮 + file chooser 上传素材。"""
    with page.expect_file_chooser(timeout=20000) as fc:
        coord_click(page, locator, "upload")
    fc.value.set_files(path)


def close_modal_if_present(page: Page):
    """关闭登录后可能出现的限时优惠/购买浮层。"""
    for _ in range(3):
        page.wait_for_timeout(800)
        try:
            close_btn = page.locator(".purchase-gift-modal img.cursor-pointer").first
            if close_btn.count() and close_btn.is_visible():
                coord_click(page, close_btn, "close_purchase_gift")
                continue
            close_btn2 = page.locator(".purchase-dialog__close").first
            if close_btn2.count() and close_btn2.is_visible():
                coord_click(page, close_btn2, "close_purchase_dialog")
                continue
        except Exception:
            pass
        break


def goto(page: Page, base_url: str, path: str):
    page.goto(f"{base_url}{path}", timeout=120000)
    page.wait_for_timeout(6000)
    close_modal_if_present(page)


def switch_predeploy_and_login(page: Page, base_url: str):
    """DEBUG 面板切「预部署」并登录（测试服失败回退路径）。"""
    goto(page, base_url, PAGE_FACE)
    debug_btn = page.locator("button:has-text('DEBUG')").first
    coord_click(page, debug_btn, "debug")
    page.wait_for_timeout(1500)
    predeploy = page.locator(".debug-panel").get_by_text("预部署", exact=True).first
    coord_click(page, predeploy, "predeploy")
    # 切换环境会刷新页面，等待 DEBUG 按钮重新出现
    page.locator("button:has-text('DEBUG')").first.wait_for(state="visible", timeout=60000)
    page.wait_for_timeout(5000)

    # 已登录则直接返回
    if page.locator("text=Log in").count() == 0 and page.locator("text=User").count():
        return

    coord_click(page, page.get_by_text("Log in", exact=True).first, "login")
    page.wait_for_timeout(2000)
    email_input = page.locator('[data-testid="auth-email-input"]').first
    code_input = page.locator('[data-testid="auth-code-input"]').first
    submit = page.locator('[data-testid="auth-submit"]').first
    email_input.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(EMAIL, delay=5)
    code_input.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(CODE, delay=5)
    coord_click(page, submit, "auth_submit")
    # 等待登录弹窗消失或用户菜单出现
    for _ in range(60):
        page.wait_for_timeout(1000)
        if page.locator('[data-testid="auth-dialog"]').count() == 0 or page.locator("text=User").count():
            break
    close_modal_if_present(page)
    page.wait_for_timeout(3000)


def _column_ready(needle_text: str, require_img: bool):
    """沿 h3 标题向上找包含 Download 按钮的列容器并判断就绪。"""
    return f"""() => {{
        const sections = Array.from(document.querySelectorAll('h3'));
        const heading = sections.find(h => h.textContent.includes('{needle_text}'));
        if (!heading) return false;
        let node = heading;
        for (let i = 0; i < 8 && node; i++) {{
            node = node.parentElement;
            if (!node) continue;
            const dl = Array.from(node.querySelectorAll('button')).find(b => b.textContent.includes('Download'));
            if (!dl) continue;
            if (dl.disabled) return false;
            if ({'true' if require_img else 'false'} && node.querySelectorAll('img').length === 0) return false;
            return true;
        }}
        return false;
    }}"""


def wait_analysis_success(page: Page, timeout_ms: int = 150000):
    """等待分析结果图成功：Analysis Result 列内 Download 恢复可用。"""
    page.wait_for_function(_column_ready("Analysis Result", False), timeout=timeout_ms)


def wait_optimized_success(page: Page, timeout_ms: int = 180000):
    """等待优化结果图成功：Optimized Result 列内真实 img + Download 恢复可用。"""
    page.wait_for_function(_column_ready("Optimized Result", True), timeout=timeout_ms)


def wait_blur_placeholder(page: Page, timeout_ms: int = 150000):
    """等待 nose 无优化结果图页模糊承接位出现（Get It Now 可点）。"""
    page.wait_for_function(
        """() => {
            const sections = Array.from(document.querySelectorAll('h3'));
            const heading = sections.find(h => h.textContent.includes('Optimized Result'));
            if (!heading) return false;
            let node = heading;
            for (let i = 0; i < 8 && node; i++) {
                node = node.parentElement;
                if (!node) continue;
                const btn = Array.from(node.querySelectorAll('button')).find(b => b.textContent.includes('Get It Now'));
                if (btn) return true;
            }
            return false;
        }""",
        timeout=timeout_ms,
    )


def wait_agent_canvas(page: Page, timeout_ms: int = 60000):
    """等待无限画布 /agent 加载并返回 URL。"""
    page.wait_for_url(re.compile(r"/agent\?pid="), timeout=timeout_ms)
    page.wait_for_timeout(6000)


@pytest.fixture(scope="session")
def predeploy_context(playwright, base_url):
    """会话级预部署登录上下文（复用登录态）。"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        accept_downloads=True,
    )
    page = context.new_page()
    page.set_default_timeout(30000)
    switch_predeploy_and_login(page, base_url)
    page.close()
    yield context
    context.close()
    browser.close()


@pytest.fixture
def predeploy_page(predeploy_context):
    """从会话上下文开新页（复用登录态）。"""
    page = predeploy_context.new_page()
    page.set_default_timeout(30000)
    yield page
    try:
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
    except Exception:
        pass
    page.close()


def _assert_canvas_face(page: Page):
    """PC Continue 后画布：三张图 + Portrait Editor/Face 面板 + Generate disabled。"""
    assert "/agent?pid=" in page.url, f"应跳转 /agent，实际 {page.url}"
    for alt in ["图片 1", "图片 2", "图片 3"]:
        assert page.locator(f"img[alt='{alt}']").count(), f"画布应包含 {alt}"
    assert page.get_by_role("button", name="Portrait Editor").count(), "应存在 Portrait Editor 按钮"
    assert page.get_by_text("Smile Lines").count(), "应打开 Portrait Editor/Face 面板（Smile Lines 特征可见）"
    generate = page.get_by_role("button", name="Generate").first
    assert generate.count(), "应存在 Generate 按钮"
    assert generate.is_disabled(), "未选择模板时 Generate 应 disabled"


def _assert_canvas_nose(page: Page):
    """nose Get It Now 后画布：仅原图 + Portrait Editor/Face 面板 + Generate disabled。"""
    assert "/agent?pid=" in page.url, f"应跳转 /agent，实际 {page.url}"
    assert page.locator("img[alt='图片 1']").count(), "画布应包含原图 图片 1"
    assert page.locator("img[alt='图片 2']").count() == 0, "nose 承接应仅带原图，不应出现 图片 2"
    assert page.locator("img[alt='图片 3']").count() == 0, "nose 承接应仅带原图，不应出现 图片 3"
    assert page.get_by_role("button", name="Portrait Editor").count(), "应存在 Portrait Editor 按钮"
    assert page.get_by_text("Smile Lines").count(), "应打开 Portrait Editor/Face 面板（Smile Lines 特征可见）"
    generate = page.get_by_role("button", name="Generate").first
    assert generate.count(), "应存在 Generate 按钮"
    assert generate.is_disabled(), "未选择模板时 Generate 应 disabled"


# ==== L6 核心 Happy Path / E2E（smoke） ====
@allure.epic("检测类功能适配UI")
@allure.feature("L6 核心 Happy Path / E2E")
@allure.story("L6-检测类SEO页全流程")
@pytest.mark.smoke
@pytest.mark.login_required
class TestL6DetectionUiSmoke:

    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("case_id", "L6-001")
    @allure.label("layer", "L6")
    @allure.title("L6-001: face 全流程 登录→上传→双图生成→双下载→PC Continue")
    def test_l6_001_face_full_flow(self, predeploy_page, base_url):
        """PRD引用: 检测类功能适配UI需求文档（交互及UI/图片上传后生成逻辑/购买逻辑）
        覆盖层级: L6 核心 Happy Path / E2E（smoke）
        前置条件: 预部署环境已登录会员账号 450832596@qq.com
        测试步骤:
            1. 打开 /tools/ai-face-reader
            2. 上传 test_images/有人脸.JPG
            3. 等待分析结果成功
            4. 等待优化结果成功
            5. 下载分析结果图 jpg
            6. 下载优化结果图 jpg
            7. 点击 Continue in Portrait Editor
            8. 检查画布三图与面板
        预期结果: 三栏成功态；两张 jpg 下载；Continue 后 /agent?pid= 带三图、优化图选中、
            Portrait Editor/Face 面板打开、Generate disabled。
        """
        page = predeploy_page
        with allure.step("导航到 /tools/ai-face-reader"):
            goto(page, base_url, PAGE_FACE)
            assert "AI Face Reader" in page.locator("body").inner_text()

        with allure.step("上传 test_images/有人脸.JPG"):
            upload_file(page, page.get_by_text("Try Image to Image AI Now").first, IMG_FACE)
            page.wait_for_timeout(3000)

        with allure.step("等待分析结果成功"):
            wait_analysis_success(page, timeout_ms=150000)
            assert page.locator("h3:has-text('Analysis Result')").count(), "应出现 Analysis Result 标题"

        with allure.step("等待优化结果成功"):
            wait_optimized_success(page, timeout_ms=180000)
            assert page.locator("h3:has-text('Optimized Result')").count(), "应出现 Optimized Result 标题"
            allure.attach(page.screenshot(), name="face_e2e_success.png", attachment_type=allure.attachment_type.PNG)

        with allure.step("下载分析结果图 jpg"):
            dl_btns = page.get_by_role("button", name="Download")
            assert dl_btns.count() >= 2, "成功态应至少有两个 Download 按钮"
            with page.expect_download(timeout=30000) as dl1:
                coord_click(page, dl_btns.nth(0), "analysis_download")
            assert dl1.value.suggested_filename, "分析图应触发下载"
            assert dl1.value.suggested_filename.startswith("pokecut-analysis-result-"), (
                f"分析图下载文件名应匹配 pokecut-analysis-result-*，实际 {dl1.value.suggested_filename}"
            )
            assert dl1.value.suggested_filename.lower().endswith(".jpg"), "分析图下载应为 jpg"

        with allure.step("下载优化结果图 jpg"):
            dl_btns = page.get_by_role("button", name="Download")
            with page.expect_download(timeout=30000) as dl2:
                coord_click(page, dl_btns.nth(1), "optimized_download")
            assert dl2.value.suggested_filename, "优化图应触发下载"
            assert dl2.value.suggested_filename.startswith("pokecut-optimized-result-"), (
                f"优化图下载文件名应匹配 pokecut-optimized-result-*，实际 {dl2.value.suggested_filename}"
            )
            assert dl2.value.suggested_filename.lower().endswith(".jpg"), "优化图下载应为 jpg"

        with allure.step("点击 Continue in Portrait Editor"):
            coord_click(page, page.get_by_role("button", name="Continue in Portrait Editor").first, "continue")
            wait_agent_canvas(page)
            allure.attach(page.screenshot(), name="face_e2e_canvas.png", attachment_type=allure.attachment_type.PNG)

        with allure.step("检查画布三图与面板"):
            _assert_canvas_face(page)

    @allure.severity(allure.severity_level.CRITICAL)
    @allure.label("case_id", "L6-002")
    @allure.label("layer", "L6")
    @allure.title("L6-002: nose 全流程 登录→上传→分析成功→模糊承接→Get It Now")
    def test_l6_002_nose_full_flow(self, predeploy_page, base_url):
        """PRD引用: 检测类功能适配UI需求文档（交互及UI/无优化结果图页面展示模糊承接态）
        覆盖层级: L6 核心 Happy Path / E2E（smoke）
        前置条件: 预部署环境已登录会员账号 450832596@qq.com
        测试步骤:
            1. 打开 /tools/nose-shape-detector
            2. 上传 test_images/有人脸.JPG
            3. 等待分析结果成功
            4. 检查 Optimized Result 模糊承接（Get It Now，无 Download）
            5. 点击 Get It Now
            6. 检查画布承接（仅原图）
        预期结果: 分析结果图成功；Optimized 模糊承接 + Get It Now；画布仅原图、原图选中、
            Portrait Editor/Face 面板打开、Generate disabled。
        """
        page = predeploy_page
        with allure.step("导航到 /tools/nose-shape-detector"):
            goto(page, base_url, PAGE_NOSE)
            assert "Nose Shape Detector" in page.locator("body").inner_text()

        with allure.step("上传 test_images/有人脸.JPG"):
            upload_file(page, page.get_by_text("Try Image to Image AI Now").first, IMG_FACE)
            page.wait_for_timeout(3000)

        with allure.step("等待分析结果成功"):
            wait_analysis_success(page, timeout_ms=150000)

        with allure.step("检查 Optimized Result 模糊承接"):
            wait_blur_placeholder(page, timeout_ms=120000)
            body = page.locator("body").inner_text()
            assert "Based on your photo and analysis, we've generated a beautifully optimized version just for you." in body, (
                "Optimized Result 应显示模糊承接文案"
            )
            assert page.get_by_role("button", name="Get It Now").count(), "Optimized Result 应存在 Get It Now"
            assert page.get_by_role("button", name="Download").count() == 1, "nose 模糊承接态应只有分析区一个 Download，不应有优化图 Download"
            allure.attach(page.screenshot(), name="nose_e2e_blur.png", attachment_type=allure.attachment_type.PNG)

        with allure.step("点击 Get It Now"):
            coord_click(page, page.get_by_role("button", name="Get It Now").first, "get_it_now")
            wait_agent_canvas(page)
            allure.attach(page.screenshot(), name="nose_e2e_canvas.png", attachment_type=allure.attachment_type.PNG)

        with allure.step("检查画布承接"):
            _assert_canvas_nose(page)
