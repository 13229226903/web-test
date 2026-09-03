"""Pokecut 人像检测三入口页（Ethnicity / Body Shape / Face Comparison）回归测试。

覆盖 cases.md（2026-08-28_pokecut_portrait_detector_interactions）：
# page-structure assertions merged into L2 page cases (former L1)
- L2 交互/状态迁移（default_full）
- L3 异常/权限（default_full）
- L5 数据边界（default_full）

登录：预部署（测试服失败后按 rule.md 切换），账号 450832596@qq.com / 验证码 123456。
"""
import os
import pathlib

import allure
import pytest
from playwright.sync_api import Page

ROOT = pathlib.Path(__file__).resolve().parents[1]
IMG_FACE = str(ROOT / "test_images" / "有人脸.JPG")
IMG_MULTI = str(ROOT / "test_images" / "多人脸.jpg")
IMG_NOFACE = str(ROOT / "test_images" / "无人脸.jpg")

EMAIL = os.environ.get("POKECUT_TEST_EMAIL", "450832596@qq.com")
CODE = os.environ.get("POKECUT_TEST_CODE", "123456")

ETHNICITY = "/tools/ethnicity-guesser-ai"
BODY = "/tools/body-shape-detector"
FACE = "/tools/face-comparison"


def coord_click(page: Page, locator, label: str = ""):
    """Vue 控件优先坐标点击。"""
    locator.scroll_into_view_if_needed(timeout=10000)
    page.wait_for_timeout(200)
    box = locator.bounding_box(timeout=10000)
    assert box, f"无 bounding box: {label or locator}"
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.wait_for_timeout(300)


def upload_file(page: Page, locator, path: str):
    """通过 file chooser 上传指定素材。"""
    with page.expect_file_chooser(timeout=20000) as fc:
        coord_click(page, locator)
    fc.value.set_files(path)


def login_predeploy(page: Page, base_url: str):
    """DEBUG 面板切「预部署」并登录（测试服失败回退路径）。"""
    page.goto(f"{base_url}{ETHNICITY}", timeout=120000)
    page.wait_for_timeout(8000)
    coord_click(page, page.locator(".debug-float-btn"), "debug")
    page.wait_for_timeout(1500)
    predeploy = page.locator(".debug-panel").get_by_text("预部署", exact=True).first
    coord_click(page, predeploy, "predeploy")
    page.wait_for_timeout(10000)
    upload_file(page, page.get_by_role("button", name="Upload Image").last, IMG_FACE)
    page.wait_for_timeout(5000)
    if page.locator('[data-testid="auth-dialog"]').count():
        auth = page.locator('[data-testid="auth-dialog"]')
        coord_click(page, auth.get_by_text("Log in", exact=True).first, "login_tab")
        page.wait_for_timeout(1000)
        page.locator('[data-testid="auth-email-input"]').click()
        page.keyboard.press("Control+A")
        page.keyboard.type(EMAIL, delay=5)
        page.locator('[data-testid="auth-code-input"]').click()
        page.keyboard.press("Control+A")
        page.keyboard.type(CODE, delay=5)
        coord_click(page, page.locator('[data-testid="auth-submit"]'), "auth_submit")
        for _ in range(60):
            page.wait_for_timeout(1000)
            if page.locator('[data-testid="auth-dialog"]').count() == 0:
                break
    page.wait_for_timeout(5000)


@pytest.fixture(scope="session")
def predeploy_context(playwright, base_url):
    """会话级预部署登录上下文。"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
        accept_downloads=True,
    )
    page = context.new_page()
    login_predeploy(page, base_url)
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


def goto(page: Page, base_url: str, path: str):
    page.goto(f"{base_url}{path}", timeout=120000)
    page.wait_for_timeout(6000)


def wait_result(page: Page, timeout_ms: int = 150000):
    """等待结果态：Download report 按钮出现。"""
    page.wait_for_function(
        "() => document.body.innerText.includes('Download report')",
        timeout=timeout_ms,
    )


def _assert_result_state(page: Page):
    """结果态稳定信号：Download report / Upload another photo 出现，处理态文案消失。"""
    body = page.locator("body").inner_text()
    assert "Download report" in body, "结果态应出现 Download report"
    assert "Upload another photo" in body, "结果态应出现 Upload another photo"
    assert "Uploading Image" not in body, "结果态不应残留 Uploading Image"
    assert "Detecting Image" not in body, "结果态不应残留 Detecting Image"
    assert "Building Report" not in body, "结果态不应残留 Building Report"


# ==== L2 interaction / state transitions (default_full) ====
@allure.epic("人像检测入口页")
@allure.feature("L2 交互与状态迁移")
class TestL2Interaction:

    @allure.title("TC-POR-L2-001 [P1] 维度切换")
    def test_l2_001_dimension_switch(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, ETHNICITY)
        url_before = page.url
        trigger = page.locator("button[aria-expanded]:has-text('Ethnicity Guesser')").first
        coord_click(page, trigger, "open")
        body = page.locator("body").inner_text()
        dims = ["Ethnicity Guesser", "Pretty Scale", "Face Attractiveness Test", "Eye Color Detector",
                "Rate My Photo", "Face Comparison", "Animal Face Test", "Golden Ratio Face Calculator",
                "Palm Reading", "Body Shape Detector"]
        for d in dims:
            assert d in body, f"dimension dropdown should include {d}"
        body_shape = page.locator("button:has-text('Body Shape Detector')").last
        coord_click(page, body_shape, "switch_body")
        page.wait_for_timeout(2000)
        assert page.url == url_before, "维度切换不应改变 URL"
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.url == url_before, "维度切换不应改变 URL"

    @allure.title("TC-POR-L2-002 [P1] 上传缩略图 + Re-upload/Delete")
    def test_l2_002_thumbnail(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        page.wait_for_timeout(3000)
        assert page.get_by_role("button", name="Re-upload photo").count()
        assert page.get_by_role("button", name="Delete uploaded photo").count()
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.get_by_role("button", name="Delete uploaded photo").count()

    @allure.title("TC-POR-L2-003 [P0] Ethnicity 上传自动出结果")
    def test_l2_003_ethnicity_result(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, ETHNICITY)
        body = page.locator("body").inner_text()
        assert "Free Online AI Ethnicity Guesser From Photo" in body
        assert "Upload Image" in body
        assert "Private by default" in body
        assert page.locator("button[aria-expanded]:has-text('Ethnicity Guesser')").count()
        upload_file(page, page.get_by_role("button", name="Upload Image").last, IMG_FACE)
        wait_result(page)
        _assert_result_state(page)
        allure.attach(page.screenshot(), name="L2-003 结果态", attachment_type=allure.attachment_type.PNG)

    @allure.title("TC-POR-L2-004 [P0] Body 上传+Continue 出结果")
    def test_l2_004_body_result(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        body = page.locator("body").inner_text()
        assert "AI Body Shape Detector by Photo Free Online" in body
        assert page.locator("input[aria-label='Bust in cm']").count()
        assert page.locator("input[aria-label='Waist in cm']").count()
        assert page.locator("input[aria-label='Hips in cm']").count()
        page.get_by_label("Bust in cm", exact=True).fill("88")
        page.get_by_label("Waist in cm", exact=True).fill("70")
        page.get_by_label("Hips in cm", exact=True).fill("96")
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        page.wait_for_timeout(1500)
        coord_click(page, page.get_by_role("button", name="Continue", exact=True).last, "continue")
        wait_result(page, timeout_ms=120000)
        _assert_result_state(page)
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        _assert_result_state(page)

    @allure.title("TC-POR-L2-005 [P0] Face 双图+Start 出结果")
    def test_l2_005_face_result(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, FACE)
        body = page.locator("body").inner_text()
        assert "Face Comparison Tool to Check Face Similarity Online for Free" in body
        assert page.get_by_role("button", name="Upload Photo A").count()
        assert page.get_by_role("button", name="Upload Photo B").count()
        assert page.get_by_role("button", name="Start Comparison").count()
        upload_file(page, page.get_by_role("button", name="Upload Photo A").last, IMG_FACE)
        page.wait_for_timeout(4000)
        upload_file(page, page.get_by_role("button", name="Upload Photo B").last, IMG_FACE)
        page.wait_for_timeout(1500)
        coord_click(page, page.get_by_role("button", name="Start Comparison", exact=True).last, "start")
        wait_result(page, timeout_ms=150000)
        _assert_result_state(page)
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        _assert_result_state(page)

    @allure.title("TC-POR-L2-006 [P0] Download report→下载+问卷")
    def test_l2_006_download_questionnaire(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, ETHNICITY)
        upload_file(page, page.get_by_role("button", name="Upload Image").last, IMG_FACE)
        wait_result(page)
        with page.expect_download(timeout=30000) as dl:
            coord_click(page, page.get_by_role("button", name="Download report", exact=True).last, "download")
        assert dl.value.suggested_filename
        page.wait_for_timeout(2500)
        assert page.get_by_role("button", name="Maybe later", exact=True).count()
        assert page.get_by_role("button", name="Submit", exact=True).count()
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.get_by_role("button", name="Submit", exact=True).count()

    @allure.title("TC-POR-L2-007 [P0] Upload another photo→Unsaved Report")
    def test_l2_007_unsaved_report(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        page.get_by_label("Bust in cm", exact=True).fill("88")
        page.get_by_label("Waist in cm", exact=True).fill("70")
        page.get_by_label("Hips in cm", exact=True).fill("96")
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        page.wait_for_timeout(1500)
        coord_click(page, page.get_by_role("button", name="Continue", exact=True).last, "continue")
        wait_result(page, timeout_ms=120000)
        coord_click(page, page.get_by_role("button", name="Upload another photo", exact=True).last, "upload_another")
        page.wait_for_timeout(2500)
        body = page.locator("body").inner_text()
        assert "Unsaved Report" in body
        assert page.get_by_role("button", name="Upload Without Saving", exact=True).count()
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.get_by_role("button", name="Upload Without Saving", exact=True).count()

    @allure.title("TC-POR-L2-008 [P0] Try My Photo→新开 /agent 画布")
    def test_l2_008_try_my_photo(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        page.get_by_label("Bust in cm", exact=True).fill("88")
        page.get_by_label("Waist in cm", exact=True).fill("70")
        page.get_by_label("Hips in cm", exact=True).fill("96")
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        page.wait_for_timeout(1500)
        coord_click(page, page.get_by_role("button", name="Continue", exact=True).last, "continue")
        wait_result(page, timeout_ms=120000)
        with page.expect_popup(timeout=20000) as pi:
            coord_click(page, page.get_by_role("button", name="Try My Photo").first, "try_my_photo")
        popup = pi.value
        popup.wait_for_load_state("domcontentloaded", timeout=60000)
        popup.wait_for_timeout(5000)
        assert "/agent" in popup.url, f"应跳转 /agent，实际 {popup.url}"
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)


# ── L3 异常 / 权限 ──────────────────────────────────────────
# ── L3 异常 / 权限 ──────────────────────────────────────────

@allure.epic("人像检测入口页")
@allure.feature("L3 异常与权限")
class TestL3Exception:

    @allure.title("TC-POR-L3-001 [P1] 匿名上传 auth wall")
    def test_l3_001_anonymous_auth(self, page, base_url):
        page.goto(f"{base_url}{ETHNICITY}", timeout=120000)
        page.wait_for_timeout(6000)
        upload_file(page, page.get_by_role("button", name="Upload Image").last, IMG_FACE)
        page.wait_for_timeout(5000)
        assert page.locator('[data-testid="auth-dialog"]').count(), "匿名上传应弹 auth modal"
        allure.attach(page.screenshot(), name="匿名上传 auth wall", attachment_type=allure.attachment_type.PNG)

    @allure.title("TC-POR-L3-002 [P1] Face 空/单图 Start Comparison toast")
    def test_l3_002_face_toast(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, FACE)
        coord_click(page, page.get_by_role("button", name="Start Comparison", exact=True).last, "start_empty")
        page.wait_for_timeout(500)
        body = page.locator("body").inner_text()
        assert "Please upload two photos before starting the comparison." in body
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert "Please upload two photos before starting the comparison." in body

    @allure.title("TC-POR-L3-003 [P2] Body 无照片点 Continue")
    def test_l3_003_body_no_photo_continue(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        page.get_by_label("Bust in cm", exact=True).fill("88")
        coord_click(page, page.get_by_role("button", name="Continue", exact=True).last, "continue")
        page.wait_for_timeout(2500)
        body = page.locator("body").inner_text()
        assert "Uploading Image" not in body, "无照片不应进入 processing"
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert "Uploading Image" not in body, "无照片不应进入 processing"

    @allure.title("TC-POR-L3-004 [P1] 无人脸 → No Face Found 弹层")
    def test_l3_004_noface(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, ETHNICITY)
        upload_file(page, page.get_by_role("button", name="Upload Image").last, IMG_NOFACE)
        page.wait_for_function("() => document.body.innerText.includes('No Face Found')", timeout=60000)
        body = page.locator("body").inner_text()
        assert "Please choose another photo with a clear single face." in body
        assert page.get_by_role("button", name="Change Photo", exact=True).count()
        assert page.get_by_role("button", name="Cancel", exact=True).count()
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.get_by_role("button", name="Cancel", exact=True).count()

    @allure.title("TC-POR-L3-005 [P1] 多人脸 → Choose a Face 弹层 + 提交")
    def test_l3_005_multiface(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, ETHNICITY)
        upload_file(page, page.get_by_role("button", name="Upload Image").last, IMG_MULTI)
        page.wait_for_function("() => document.body.innerText.includes('Choose a Face to Analyze')", timeout=90000)
        assert page.get_by_role("button", name="Select face 1").count()
        face_btn = page.locator("button[aria-label='Select face 1']").first
        assert face_btn.get_attribute("aria-pressed") == "true"
        coord_click(page, page.locator("button[aria-label='Select face 2']").last, "select_face2")
        page.wait_for_timeout(1000)
        assert page.locator("button[aria-label='Select face 2']").last.get_attribute("aria-pressed") == "true"
        coord_click(page, page.get_by_role("button", name="Continue", exact=True).last, "continue")
        page.wait_for_function("() => document.body.innerText.includes('Detecting Image')", timeout=30000)
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)


# ── L5 数据边界 ──────────────────────────────────────────────
# ── L5 数据边界 ──────────────────────────────────────────────

@allure.epic("人像检测入口页")
@allure.feature("L5 数据边界")
class TestL5Boundary:

    @allure.title("TC-POR-L5-001 [P1] 三围完整 88/70/96")
    def test_l5_001_measurements_full(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        bust = page.locator("input[aria-label='Bust in cm']")
        bust.fill("88")
        page.get_by_label("Waist in cm", exact=True).fill("70")
        page.get_by_label("Hips in cm", exact=True).fill("96")
        assert bust.input_value() == "88"
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert bust.input_value() == "88"

