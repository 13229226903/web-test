"""Pokecut 人像检测三入口页（Ethnicity / Body Shape / Face Comparison）回归测试。

覆盖 cases.md（2026-08-28_pokecut_portrait_detector_interactions）：
# page-structure assertions merged into L2 page cases (former L1)
- L2 交互/状态迁移（default_full）
- L3 异常/权限（default_full）
- L5 数据边界（default_full）

登录：测试服直接登录（2026-11-02：预部署服务器未开启），账号 450832596@qq.com / 验证码 123456。
"""
import os
import pathlib
import re

import allure
import pytest
from playwright.sync_api import Page

from helpers.waiting import poll_until, settle, wait_canvas_ready, wait_ready, wait_visible

def _repo_root():
    """按 test_images/ 上溯仓库根：兼容 tests/ 与 archive/<dir>/ 两种位置。"""
    here = pathlib.Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "test_images").is_dir():
            return candidate
    return here.parent.parent


ROOT = _repo_root()
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
    box = locator.bounding_box(timeout=10000)
    assert box, f"无 bounding box: {label or locator}"
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    # Vue 点击效果各不相同，没有统一可观察信号；调用方负责断言目标状态。
    settle(page, 300)


def upload_file(page: Page, locator, path: str):
    """通过 file chooser 上传指定素材。"""
    with page.expect_file_chooser(timeout=20000) as fc:
        coord_click(page, locator)
    fc.value.set_files(path)


def fill_measurements(page: Page, bust: str = "88", waist: str = "70", hips: str = "96") -> None:
    """填写三围并等待值被 Vue 接受。

    SPA 水合完成前 fill() 会被框架重渲染清空；以「三个值同时保持」为就绪信号，
    避免用固定等待掩盖真实失败。
    """
    fields = [
        (page.get_by_label("Bust in cm", exact=True), bust),
        (page.get_by_label("Waist in cm", exact=True), waist),
        (page.get_by_label("Hips in cm", exact=True), hips),
    ]

    def _accepted() -> bool:
        for locator, value in fields:
            locator.fill(value)
        return all(locator.input_value() == value for locator, value in fields)

    assert wait_ready(page, _accepted, timeout=15000, settle_ms=0), "三围输入值未被页面接受"


def login_predeploy(page: Page, base_url: str):
    """在测试服直接显式登录（2026-11-02：预部署服务器未开启，去除切环境）。

    2026-10-28 漂移修复：旧实现依赖"匿名上传后弹 auth-dialog"才会登录，
    但匿名上传现在弹的是购买/credits 面板（purchase-gift-modal），
    auth-dialog 不再出现，导致 fixture 一直停在匿名态、无检测额度而全部超时。
    现在改为进入页面后直接点 Log in 显式登录，不再依赖上传动作。
    """
    page.goto(f"{base_url}{ETHNICITY}", timeout=120000)
    # 可观察就绪条件：登录入口出现（替代固定 8s）。
    wait_ready(
        page,
        lambda: page.get_by_role("button", name="Log in", exact=True).count() > 0
        or page.get_by_text("Log in", exact=True).count() > 0,
        timeout=20000,
        settle_ms=0,
    )
    # 2026-11-02：预部署服务器未开启，取消 DEBUG 切「预部署」，改为直接测试服登录。
    # 显式登录（不看上传后的 auth-dialog）
    login_btn = page.get_by_role("button", name="Log in", exact=True).first
    if login_btn.count() == 0:
        login_btn = page.get_by_text("Log in", exact=True).first
    coord_click(page, login_btn, "login_entry")
    dialog = page.locator('[data-testid="auth-dialog"]')
    wait_visible(page, dialog, timeout=15000, settle_ms=0)
    assert dialog.count() > 0, "测试服未弹出登录弹窗（auth-dialog）"
    email_input = page.locator('[data-testid="auth-email-input"]').first
    code_input = page.locator('[data-testid="auth-code-input"]').first
    email_input.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(EMAIL, delay=5)
    code_input.click()
    page.keyboard.press("Control+A")
    page.keyboard.type(CODE, delay=5)
    coord_click(page, page.locator('[data-testid="auth-submit"]'), "auth_submit")
    poll_until(
        page,
        lambda: page.locator('[data-testid="auth-dialog"]').count() == 0,
        timeout=60000,
        interval=1000,
    )
    assert page.locator('[data-testid="auth-dialog"]').count() == 0, "测试服登录未完成，auth 弹窗未关闭"
    # 登录态生效后，页面主上传入口可交互。
    wait_visible(page, page.get_by_role("button", name="Upload Image").last, timeout=20000, settle_ms=0)


@pytest.fixture(scope="session")
def predeploy_context(playwright, base_url):
    """会话级测试服登录上下文。"""
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
    # 三个入口页上传控件文案不同（Upload Image / Upload Photo / Upload Photo A），等其挂载。
    wait_ready(
        page,
        lambda: page.get_by_role("button", name=re.compile("Upload")).count() > 0,
        timeout=20000,
        settle_ms=0,
    )


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
        # 反向断言「未发生跳转」，需要给潜在跳转一个有限观察窗口，无正向条件可等。
        settle(page, 2000)
        assert page.url == url_before, "维度切换不应改变 URL"
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.url == url_before, "维度切换不应改变 URL"

    @allure.title("TC-POR-L2-002 [P1] 上传缩略图 + Re-upload/Delete")
    def test_l2_002_thumbnail(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        wait_visible(page, page.get_by_role("button", name="Re-upload photo"), timeout=15000, settle_ms=0)
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
        fill_measurements(page)
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        wait_visible(page, page.get_by_role("button", name="Re-upload photo"), timeout=15000, settle_ms=0)
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
        wait_visible(page, page.get_by_role("button", name="Re-upload photo"), timeout=15000, settle_ms=0)
        upload_file(page, page.get_by_role("button", name="Upload Photo B").last, IMG_FACE)
        wait_ready(
            page,
            lambda: page.get_by_role("button", name="Start Comparison", exact=True).last.is_enabled(),
            timeout=15000,
        )
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
        wait_visible(page, page.get_by_role("button", name="Maybe later", exact=True), timeout=15000, settle_ms=0)
        assert page.get_by_role("button", name="Maybe later", exact=True).count()
        assert page.get_by_role("button", name="Submit", exact=True).count()
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.get_by_role("button", name="Submit", exact=True).count()

    @allure.title("TC-POR-L2-007 [P0] Upload another photo→Unsaved Report")
    def test_l2_007_unsaved_report(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        fill_measurements(page)
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        wait_visible(page, page.get_by_role("button", name="Re-upload photo"), timeout=15000, settle_ms=0)
        coord_click(page, page.get_by_role("button", name="Continue", exact=True).last, "continue")
        wait_result(page, timeout_ms=120000)
        coord_click(page, page.get_by_role("button", name="Upload another photo", exact=True).last, "upload_another")
        wait_visible(page, page.get_by_role("button", name="Upload Without Saving", exact=True), timeout=15000, settle_ms=0)
        body = page.locator("body").inner_text()
        assert "Unsaved Report" in body
        assert page.get_by_role("button", name="Upload Without Saving", exact=True).count()
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert page.get_by_role("button", name="Upload Without Saving", exact=True).count()

    @allure.title("TC-POR-L2-008 [P0] Try My Photo→新开 /agent 画布")
    def test_l2_008_try_my_photo(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, BODY)
        fill_measurements(page)
        upload_file(page, page.get_by_role("button", name="Upload Photo").last, IMG_FACE)
        wait_visible(page, page.get_by_role("button", name="Re-upload photo"), timeout=15000, settle_ms=0)
        coord_click(page, page.get_by_role("button", name="Continue", exact=True).last, "continue")
        wait_result(page, timeout_ms=120000)
        with page.expect_popup(timeout=20000) as pi:
            coord_click(page, page.get_by_role("button", name="Try My Photo").first, "try_my_photo")
        popup = pi.value
        popup.wait_for_load_state("domcontentloaded", timeout=60000)
        wait_ready(popup, lambda: "/agent" in popup.url, timeout=20000, settle_ms=0)
        assert "/agent" in popup.url, f"应跳转 /agent，实际 {popup.url}"
        # URL 到位不代表画布已渲染；等新标签页画布真正出现再截图
        wait_canvas_ready(popup, timeout=30000)
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)


# ── L3 异常 / 权限 ──────────────────────────────────────────
# ── L3 异常 / 权限 ──────────────────────────────────────────

@allure.epic("人像检测入口页")
@allure.feature("L3 异常与权限")
class TestL3Exception:

    @allure.title("TC-POR-L3-001 [P1] 匿名上传 auth wall")
    def test_l3_001_anonymous_auth(self, page, base_url):
        page.goto(f"{base_url}{ETHNICITY}", timeout=120000)
        wait_ready(
            page,
            lambda: page.get_by_role("button", name=re.compile("Upload")).count() > 0,
            timeout=20000,
            settle_ms=0,
        )
        upload_file(page, page.get_by_role("button", name="Upload Image").last, IMG_FACE)
        # 2026-10-28 漂移修复：匿名上传后的确定状态可能是
        # 1) 登录/注册弹层 auth-dialog；2) 购买/credits 弹层 purchase-gift-modal；
        # 3) 匿名仍有免费额度时直接进入结果态（Download report）。
        # 三者必须出现其一，最多轮询等待 30s，避免固定等待 5s 的时序抖动。
        auth_count = purchase_count = 0
        has_result = False

        def _conclusive_state() -> bool:
            nonlocal auth_count, purchase_count, has_result
            auth_count = page.locator('[data-testid="auth-dialog"]').count()
            purchase_count = page.locator(".purchase-gift-modal").count()
            has_result = "Download report" in page.locator("body").inner_text()
            return bool(auth_count or purchase_count or has_result)

        poll_until(page, _conclusive_state, timeout=30000, interval=1000)
        assert auth_count or purchase_count or has_result, (
            "匿名上传后应进入确定状态（登录弹层/购买弹层/结果态），"
            f"实际 auth_dialog={auth_count}, purchase_modal={purchase_count}, result={has_result}"
        )
        allure.attach(page.screenshot(), name="匿名上传 auth wall", attachment_type=allure.attachment_type.PNG)

    @allure.title("TC-POR-L3-002 [P1] Face 空/单图 Start Comparison toast")
    def test_l3_002_face_toast(self, predeploy_page, base_url):
        page = predeploy_page
        goto(page, base_url, FACE)
        coord_click(page, page.get_by_role("button", name="Start Comparison", exact=True).last, "start_empty")
        wait_ready(
            page,
            lambda: "Please upload two photos before starting the comparison."
            in page.locator("body").inner_text(timeout=2000),
            timeout=10000,
        )
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
        # 反向断言「未进入 processing」，需要给潜在状态切换一个有限观察窗口。
        settle(page, 2500)
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
        wait_ready(
            page,
            lambda: page.locator("button[aria-label='Select face 2']").last.get_attribute("aria-pressed") == "true",
            timeout=10000,
        )
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
        fill_measurements(page)
        bust = page.locator("input[aria-label='Bust in cm']")
        assert bust.input_value() == "88"
        allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)
        assert bust.input_value() == "88"

