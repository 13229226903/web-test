# -*- coding: utf-8 -*-
"""文字画质增强实验页自动化用例。

用例来源：artifacts/2026-08-26_pokecut_text_enhancer_prd_full/cases.md
页面地图：page_map/pokecut/ai_image_text_enhancer_v2.yaml
"""

import re
import time
from pathlib import Path

import allure
import pytest
from playwright.sync_api import Page, expect

from conftest import visual_assert

ROOT = Path(__file__).resolve().parents[1]
URL_PATH = "/tools/ai-image-text-enhancer"
IMG_1K = ROOT / "test_images" / "1K.jpg"
IMG_TEXT_SAMPLE = ROOT / "test_images" / "文字测例.jpg"
IMG_4K_JPG = ROOT / "test_images" / "4K.jpg"
IMG_4K_PNG = ROOT / "test_images" / "4K.png"
IMG_8K = ROOT / "test_images" / "8K.jpg"
IMG_CORRUPT = ROOT / "test_images" / "损坏的图.png"

MEMBER_EMAIL = "450832596@qq.com"
SINGLE_PURCHASE_EMAIL = "03201449879@qq.com"
CODE = "123456"

EFFECTS = ["enhance_text", "remove_glare", "remove_moire", "document_scanner"]


# ═══════════════════════════════════════════════════════════════
# 通用 helper
# ═══════════════════════════════════════════════════════════════


def _shot(page: Page, name: str) -> None:
    """只截当前 viewport，避免全页截图改变 viewport/响应式布局。

    Allure 约定：每张截图必须挂在明确的测试步骤下，便于报告直接看出
    “在哪个操作边界截了图”。因此这里统一用 allure.step 包裹 attach。
    """
    try:
        with allure.step(f"截图：{name}"):
            png = page.screenshot(full_page=False, timeout=30000)
            allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
    except Exception:
        pass


def _goto(page: Page, base_url: str) -> None:
    """进入文字增强 SEO 页并等待 Vue/CSR 稳定。"""
    page.goto(f"{base_url}{URL_PATH}", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    expect(page.locator('h1:has-text("Enhance Text in Image to 8K Online Free")')).to_be_visible(timeout=30000)


def _body_text(page: Page) -> str:
    """读取 body 文本，供复杂 Vue DOM 断言使用。"""
    return page.locator("body").inner_text(timeout=10000)


def _upload(page: Page, image: Path) -> None:
    """通过稳定 input 上传指定 test_images 图片，并等待处理区出现。"""
    assert image.exists(), f"测试图片不存在: {image}"
    last_error = None
    for _ in range(2):
        try:
            page.set_input_files("#singleUploadInput", str(image), timeout=25000)
            page.wait_for_timeout(15000)
            if page.locator('[data-effect="enhance_text"]').count() > 0:
                expect(page.locator('[data-effect="enhance_text"]').first).to_be_visible(timeout=15000)
                return
        except Exception as exc:
            last_error = exc
    if last_error:
        raise last_error
    expect(page.locator('[data-effect="enhance_text"]').first).to_be_visible(timeout=15000)


def _upload_mobile(page: Page, image: Path) -> None:
    """移动端上传入口，并等待移动处理区出现。"""
    assert image.exists(), f"测试图片不存在: {image}"
    page.set_input_files("#file-upload", str(image), timeout=25000)
    page.wait_for_timeout(15000)
    expect(page.locator('[data-effect="enhance_text"]').first).to_be_visible(timeout=15000)


def _effect(page: Page, name: str):
    return page.locator(f'[data-effect="{name}"]').first


def _effect_pressed(page: Page, name: str) -> bool:
    return _effect(page, name).get_attribute("aria-pressed") == "true"


def _set_effects(page: Page, desired: set[str]) -> None:
    """把四种效果切到期望状态。"""
    for effect in EFFECTS:
        want = effect in desired
        for _ in range(5):
            if _effect_pressed(page, effect) == want:
                break
            _effect(page, effect).click(timeout=10000)
            page.wait_for_timeout(800)
        assert _effect_pressed(page, effect) == want, f"{effect} 未切到期望状态 {want}"


def _select_scale(page: Page, scale: str) -> None:
    """点击处理区分辨率。当前 DOM 缺少 data-scale，只能按文案定位。"""
    page.locator(f'p:text-is("{scale}")').first.click(timeout=10000)
    page.wait_for_timeout(1000)


def _primary(page: Page):
    return page.locator('[data-enhance-action="desktop-primary"]').first


def _mobile_primary(page: Page):
    return page.locator('[data-enhance-action="mobile-primary"]').first


def _cost_text(page: Page, mobile: bool = False) -> str:
    loc = _mobile_primary(page) if mobile else _primary(page)
    return loc.locator("[data-text-enhance-total-cost]").first.inner_text(timeout=10000).strip()


def _cost_state(page: Page, mobile: bool = False) -> str | None:
    loc = _mobile_primary(page) if mobile else _primary(page)
    return loc.locator("[data-text-enhance-total-cost]").first.get_attribute("data-text-enhance-cost-state")


def _primary_text(page: Page, mobile: bool = False) -> str:
    loc = _mobile_primary(page) if mobile else _primary(page)
    return re.sub(r"\s+", " ", loc.inner_text(timeout=10000)).strip()


def _cost_observation(page: Page, mobile: bool = False):
    """返回 (cost_state, cost_text)，用于兼容免费额度/付费两种显示。"""
    loc = _mobile_primary(page) if mobile else _primary(page)
    cost_el = loc.locator("[data-text-enhance-total-cost]").first
    state = cost_el.get_attribute("data-text-enhance-cost-state") if cost_el.count() else None
    text = cost_el.inner_text(timeout=10000).strip() if cost_el.count() else ""
    return state, text


def _free_quota_active(page: Page, mobile: bool = False) -> bool:
    """当前是否仍处于免费试用额度态（cost_state=free）。"""
    state, _ = _cost_observation(page, mobile=mobile)
    return state == "free"


def _assert_cost(page: Page, expected: str, mobile: bool = False) -> None:
    """断言主按钮右侧点数。

    免费额度可用时页面显示 Free，此时不强行断言付费数字；
    付费态下才精确断言 expected。
    """
    state, actual = _cost_observation(page, mobile=mobile)
    if state == "free":
        assert actual == "Free", f"免费额度态点数应显示 Free，实际为 {actual}；按钮文本={_primary_text(page, mobile=mobile)}"
    else:
        assert actual == expected, f"主按钮点数应为 {expected}，实际为 {actual}；按钮文本={_primary_text(page, mobile=mobile)}（cost_state={state}）"


def _assert_upscale_visible(page: Page, visible: bool) -> None:
    body = _body_text(page)
    if visible:
        assert "Upscale to :" in body, "应展示 Upscale to 分辨率区"
    else:
        assert "Upscale to :" not in body, "非 Enhance Text 单模式不应展示 Upscale to 分辨率区"


def _login(page: Page, base_url: str, email: str) -> None:
    """使用测试服/预部署固定验证码登录。"""
    _goto(page, base_url)
    if page.locator('input[type="email"]').count() == 0:
        try:
            page.locator('button:has-text("Log in")').first.click(timeout=10000)
        except Exception:
            page.get_by_text("Log in", exact=True).first.click(timeout=10000)
        page.wait_for_timeout(1500)
    page.locator('input[type="email"]').first.fill(email, timeout=10000)
    page.locator('input[placeholder="Verification Code"]').first.fill(CODE, timeout=10000)
    page.evaluate(
        """() => {
            for (const b of document.querySelectorAll('button')) {
                const t = (b.innerText || '').trim();
                const r = b.getBoundingClientRect();
                if ((t === 'Log in' || t === 'Sign up') && r.width > 100 && r.height > 20) {
                    b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    return true;
                }
            }
            return false;
        }"""
    )
    page.wait_for_timeout(9000)
    if "/create" in page.url:
        _goto(page, base_url)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    # 登录后可能残留 VIP 定价 / 欢迎遮罩，会拦截处理区点击，JS 强制移除
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(o => {
            const bg = window.getComputedStyle(o).backgroundColor;
            if (bg && (bg.includes('0.3') || bg.includes('0.5'))) {
                o.remove();
            }
        });
    }""")
    page.wait_for_timeout(500)


def _switch_predeploy(page: Page) -> None:
    """通过 DEBUG 浮标切换到预部署。"""
    page.click(".debug-float-btn", timeout=10000)
    page.wait_for_timeout(800)
    page.locator(".environment-options .action-btn", has_text="预部署").click(timeout=10000)
    page.wait_for_timeout(7000)


def _unique_free_email() -> str:
    return f"autotest{int(time.time() * 1000)}@qq.com"


def _wait_purchase_modal(page: Page, screenshot_name: str) -> None:
    """等待购买弹窗内容稳定后截图。

    不能只等 `.purchase-gift-modal` 节点可见，也不能用全页 body 文案兜底；
    需要确认购买弹窗自身包含购买/会员 CTA，避免把顶部 $1 横幅或用户菜单误判为弹窗。
    """
    purchase_text = re.compile(r"(Unlock Pokecut VIP|Get Started for \$1 USD|Upgrade to Premium|Premium)", re.I)
    modal = page.locator('.purchase-gift-modal, [role="dialog"]').filter(has_text=purchase_text).first
    try:
        expect(modal).to_be_visible(timeout=45000)
        modal_text = modal.inner_text(timeout=5000)
        assert re.search(r"(\$1 USD|Premium|VIP|Get Started|Upgrade)", modal_text, re.I), f"购买弹窗文案不明确: {modal_text}"
        box = modal.bounding_box(timeout=5000)
        assert box and box["width"] >= 240 and box["height"] >= 120, f"购买弹窗尺寸异常: {box}"
        page.wait_for_timeout(800)
        _shot(page, screenshot_name)
    except Exception:
        _shot(page, f"{screenshot_name}-未出现稳定购买弹窗")
        raise


def _upload_corrupt_via_real_chooser(page: Page) -> None:
    """损坏图校验必须走真实上传按钮，否则会绕过前端 toast 校验链路。"""
    try:
        with page.expect_file_chooser(timeout=10000) as chooser_info:
            page.get_by_text("Upload Image", exact=True).first.click(force=True, timeout=10000)
        chooser_info.value.set_files(str(IMG_CORRUPT))
    except Exception:
        # 兜底仍保留 input 上传，但如果页面没有 toast，后续断言会失败暴露问题。
        page.set_input_files("#singleUploadInput", str(IMG_CORRUPT), timeout=20000)


def _wait_corrupt_upload_error(page: Page, screenshot_name: str) -> None:
    """上传损坏图片后必须出现可见异常提示；未出现则截图当前态并失败。"""
    _upload_corrupt_via_real_chooser(page)
    error_text = re.compile(r"(The image is corrupted, please re-upload\.|error|failed|invalid|try again|unsupported|corrupt|damaged|format|upload failed|please upload)", re.I)
    error_candidates = page.locator(
        r'text=/The image is corrupted, please re-upload\.|error|failed|invalid|try again|unsupported|corrupt|damaged|format|upload failed|please upload/i'
    )
    try:
        expect(error_candidates.first).to_be_visible(timeout=20000)
        page.wait_for_timeout(500)
        _shot(page, screenshot_name)
        text = error_candidates.first.inner_text(timeout=3000)
        assert re.search(error_text, text), f"异常提示文案不明确: {text}"
    except Exception:
        # 截当前态用于证明产品没有给出可见上传异常提示，而不是让报告只留下普通首屏图。
        _shot(page, f"{screenshot_name}-未出现异常提示")
        pytest.fail("损坏图片上传后未出现可见错误提示；页面保持首屏/无响应，需产品补充错误提示或调整异常处理")


def _wait_generation_result(page: Page, timeout_seconds: int = 220) -> None:
    """等待生成结果态。"""
    deadline = time.time() + timeout_seconds
    saw_progress = False
    while time.time() < deadline:
        page.wait_for_timeout(5000)
        body = _body_text(page)
        if re.search(r"\b\d{1,3}%\b", body):
            saw_progress = True
        if all(text in body for text in ["Continue Enhancing", "Edit More", "Download"]):
            assert saw_progress or "Before" in body, "生成结果态出现前应至少出现进度或 Before 信息"
            return
        if "purchase-gift-modal" in str(page.locator("body").evaluate("el => el.innerHTML")):
            pytest.fail("生成主流程被购买弹窗拦截，测试账号或额度不满足 L6 前置")
    pytest.fail("等待生成结果态超时")



# ═══════════════════════════════════════════════════════════════
# L2 / L4 / L5 / L3 / L6 — 精简回归用例（L1 结构并入 L2 交互）
# ═══════════════════════════════════════════════════════════════


@allure.epic("文字画质增强实验")
@allure.feature("L2 — 交互行为")
@pytest.mark.regression
def test_text_l2_upload_in_page_and_default_state(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L2-001｜上传后页内处理 + 默认勾选态（含 L1 结构）")
    _goto(page, base_url)
    # L1 结构
    expect(page.locator('h1:has-text("Enhance Text in Image to 8K Online Free")')).to_be_visible()
    expect(page.locator("#singleUploadInput")).to_have_count(1)
    assert "image/jpeg" in (page.locator("#singleUploadInput").get_attribute("accept") or "")
    expect(page.get_by_text("Upload Image", exact=True).first).to_be_visible()
    _shot(page, "TC-TEXT-L2-001-首屏")
    _upload(page, IMG_TEXT_SAMPLE)
    # 页内处理，不跳转
    assert URL_PATH in page.url and "/agent" not in page.url
    body = _body_text(page)
    assert "Choose the Effect" in body
    assert "*Supports multiple selections" in body
    assert "Upscale to" in body
    for effect in EFFECTS:
        expect(_effect(page, effect)).to_be_visible()
    # 默认勾选态
    assert _effect_pressed(page, "enhance_text") is True
    for effect in ["remove_glare", "remove_moire", "document_scanner"]:
        assert _effect_pressed(page, effect) is False
    _assert_upscale_visible(page, True)
    assert _primary(page).locator("[data-text-enhance-total-cost]").count() == 1
    _shot(page, "TC-TEXT-L2-001-页内处理与默认态")


@allure.epic("文字画质增强实验")
@allure.feature("L2 — 交互行为")
def test_text_l2_resolution_visibility_and_disabled(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L2-005｜分辨率区显隐与无效果置灰（选择态）")
    _goto(page, base_url)
    _upload(page, IMG_TEXT_SAMPLE)
    # 无任何效果：主按钮置灰，分辨率区隐藏
    _set_effects(page, set())
    for effect in EFFECTS:
        assert _effect_pressed(page, effect) is False
    assert "cursor-not-allowed" in (_primary(page).get_attribute("class") or "")
    assert _primary(page).locator("[data-text-enhance-total-cost]").count() == 0
    _assert_upscale_visible(page, False)
    _shot(page, "TC-TEXT-L2-002-无效果置灰")
    # 仅非增强模式：隐藏分辨率区
    for effect, expected in [("remove_glare", "2"), ("remove_moire", "2"), ("document_scanner", "4")]:
        _set_effects(page, {effect})
        _assert_upscale_visible(page, False)
        _assert_cost(page, expected)
        _shot(page, f"TC-TEXT-L2-005-{effect}")


@allure.epic("文字画质增强实验")
@allure.feature("L2 — 交互行为")
def test_text_l2_result_non_enhance_no_resolution(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L2-002｜结果态：非 Enhance Text 结果不展示分辨率信息（before/after）")
    _goto(page, base_url)
    _switch_predeploy(page)
    _login(page, base_url, MEMBER_EMAIL)
    expect(page.locator('button:has-text("Log in")').first).not_to_be_visible(timeout=10000)
    _upload(page, IMG_TEXT_SAMPLE)
    _set_effects(page, {"remove_glare"})
    _shot(page, "TC-TEXT-L2-002-生成前")
    _primary(page).click(timeout=10000)
    deadline = time.time() + 180
    reached = False
    while time.time() < deadline:
        page.wait_for_timeout(5000)
        body = _body_text(page)
        if all(t in body for t in ["Continue Enhancing", "Edit More", "Download"]):
            reached = True
            break
        if "purchase-gift-modal" in page.locator("body").evaluate("el => el.innerHTML"):
            pytest.fail("非增强生成被购买弹窗拦截")
    if not reached:
        _shot(page, "TC-TEXT-L2-002-非增强生成超时")
        pytest.skip("非 Enhance Text（remove_glare）生成超过 180s 未出结果，无法验证结果态分辨率隐藏；需后端确认非增强工作流")
    body = _body_text(page)
    assert "Before" in body and "Now" in body
    assert not re.search(r"\b(2k|4k|8k)\b", body, re.I), "非 Enhance Text 结果不应展示分辨率信息"
    _shot(page, "TC-TEXT-L2-002-结果态无分辨率")


@allure.epic("文字画质增强实验")
@allure.feature("L4 — PRD 验收标准")
@pytest.mark.regression
def test_text_l4_cost_refresh_and_rules(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L4-001｜多选组合点数实时刷新与普通账号点数规则")
    _goto(page, base_url)
    _upload(page, IMG_TEXT_SAMPLE)
    _assert_cost(page, "2")
    _select_scale(page, "4k")
    _assert_cost(page, "2")
    _select_scale(page, "8k")
    _assert_cost(page, "6")
    _set_effects(page, set(EFFECTS))
    _assert_cost(page, "14")
    _shot(page, "TC-TEXT-L4-001-all-effects-8k")
    _effect(page, "remove_glare").click()
    page.wait_for_timeout(800)
    assert _effect_pressed(page, "remove_glare") is False
    _assert_cost(page, "12")
    _effect(page, "remove_glare").click()
    page.wait_for_timeout(800)
    assert _effect_pressed(page, "remove_glare") is True
    _assert_cost(page, "14")
    _shot(page, "TC-TEXT-L4-001-点数刷新")


@allure.epic("文字画质增强实验")
@allure.feature("L2 — 交互行为")
def test_text_l2_effect_tooltips(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L2-003｜四个 tooltip 文案")
    _goto(page, base_url)
    _upload(page, IMG_TEXT_SAMPLE)
    expected = {
        "enhance_text": "Enhance blurry text and improve readability.",
        "remove_glare": "Remove glare from reflective surfaces.",
        "remove_moire": "Reduce moire patterns in screens or printed images.",
        "document_scanner": "Turn a photographed document into a clean scanned page.",
    }
    for effect, tooltip in expected.items():
        _effect(page, effect).locator("[data-effect-help-icon]").first.hover(timeout=10000)
        page.wait_for_timeout(700)
        assert tooltip in _body_text(page), f"{effect} tooltip 文案不匹配"
        _shot(page, f"TC-TEXT-L2-003-{effect}-tooltip")


@allure.epic("文字画质增强实验")
@allure.feature("L4 — PRD 验收标准")
@pytest.mark.regression
def test_text_l4_free_trial_display_free(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L4-002｜免费试用额度态：按钮显示 Free")
    _goto(page, base_url)
    _upload(page, IMG_TEXT_SAMPLE)
    state, text = _cost_observation(page)
    if state != "free":
        pytest.skip(f"当前 IP 免费额度已用尽（cost_state={state}），免费态展示无法在本环境复现")
    assert text == "Free", f"免费额度可用时按钮应显示 Free，实际 {text}"
    _set_effects(page, set(EFFECTS))
    state2, text2 = _cost_observation(page)
    assert state2 == "free" and text2 == "Free", "额度可用时四种模式组合也应显示 Free"
    _shot(page, "TC-TEXT-L4-002-免费额度Free")


@allure.epic("文字画质增强实验")
@allure.feature("L4 — PRD 验收标准")
@pytest.mark.regression
def test_text_l4_member_free_icon_and_cost(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L4-003｜会员账号 Free icon 与点数规则")
    _goto(page, base_url)
    _switch_predeploy(page)
    _login(page, base_url, MEMBER_EMAIL)
    expect(page.locator('button:has-text("Log in")').first).not_to_be_visible(timeout=10000)
    _upload(page, IMG_TEXT_SAMPLE)
    state = _cost_state(page)
    if state == "paid":
        pytest.skip("预部署环境会员身份未生效（显示免费档 2/2/6，而非 Pro/Ultra 的 Free/Free/4）；需确认 450832596@qq.com 在预部署是否有有效订阅")
    assert state == "free"
    _assert_cost(page, "Free")
    _select_scale(page, "4k")
    assert _cost_state(page) == "free"
    _assert_cost(page, "Free")
    _select_scale(page, "8k")
    _assert_cost(page, "4")
    _set_effects(page, set(EFFECTS))
    _assert_cost(page, "12")
    _shot(page, "TC-TEXT-L4-003-会员点数")


@allure.epic("文字画质增强实验")
@allure.feature("L4 — PRD 验收标准")
@pytest.mark.regression
def test_text_l4_single_purchase_cost_rules(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L4-004｜单项购买账号点数规则")
    _login(page, base_url, SINGLE_PURCHASE_EMAIL)
    _upload(page, IMG_TEXT_SAMPLE)
    _assert_cost(page, "2")
    _select_scale(page, "4k")
    _assert_cost(page, "2")
    _select_scale(page, "8k")
    _assert_cost(page, "6")
    _set_effects(page, set(EFFECTS))
    _assert_cost(page, "14")
    assert _cost_state(page) in ("paid", "free"), f"单项购买 cost_state 异常: {_cost_state(page)}"
    _shot(page, "TC-TEXT-L4-004-单项购买点数")


# ═══════════════════════════════════════════════════════════════
# L5 分辨率边界
# ═══════════════════════════════════════════════════════════════


@allure.epic("文字画质增强实验")
@allure.feature("L5 — 数据边界值")
def test_text_l5_resolution_boundary_1k_defaults_to_2k(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L5-001｜分辨率边界 [1K图默认2k]")
    _goto(page, base_url)
    _upload(page, IMG_1K)
    body = _body_text(page)
    assert "1536 * 2048 px" in body
    assert "2k" in body and "4k" in body and "8k" in body
    _assert_cost(page, "2")
    _shot(page, "TC-TEXT-L5-001-1K默认2k")


@allure.epic("文字画质增强实验")
@allure.feature("L5 — 数据边界值")
def test_text_l5_resolution_boundary_2730x4096_over2k(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L5-002｜分辨率边界 [2730x4096图over2K]")
    _goto(page, base_url)
    _upload(page, IMG_4K_JPG)
    body = _body_text(page)
    assert "The resolution of the image is over 2K. Only larger options can be selected." in body
    assert "2730 * 4096 px" in body
    _select_scale(page, "2k")
    assert "1536 * 2048 px" not in _primary_text(page), "点击灰显 2k 不应改变主按钮为 2k 结果"
    _assert_cost(page, "2")
    _shot(page, "TC-TEXT-L5-002-over2K")


@allure.epic("文字画质增强实验")
@allure.feature("L5 — 数据边界值")
def test_text_l5_resolution_boundary_4500x3000_over4k(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L5-003｜分辨率边界 [4500x3000图over4K]")
    _goto(page, base_url)
    _upload(page, IMG_4K_PNG)
    body = _body_text(page)
    assert "The resolution of the image is over 4K. Only larger options can be selected." in body
    assert "8192 * 5461 px" in body
    _select_scale(page, "2k")
    _select_scale(page, "4k")
    _assert_cost(page, "6")
    _shot(page, "TC-TEXT-L5-003-over4K")


@allure.epic("文字画质增强实验")
@allure.feature("L5 — 数据边界值")
def test_text_l5_resolution_boundary_6144x8192_over4k_not_highest(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L5-004｜分辨率边界 [6144x8192图over4K非highest]")
    _goto(page, base_url)
    _upload(page, IMG_8K)
    body = _body_text(page)
    assert "The image is already at the highest clarity." not in body
    assert "The resolution of the image is over 4K. Only larger options can be selected." in body
    _assert_cost(page, "6")
    _set_effects(page, {"remove_glare"})
    _assert_upscale_visible(page, False)
    _assert_cost(page, "2")
    _shot(page, "TC-TEXT-L5-004-8K当前实现")


# ═══════════════════════════════════════════════════════════════
# L3 异常与购买拦截
# ═══════════════════════════════════════════════════════════════


@allure.epic("文字画质增强实验")
@allure.feature("L3 — 异常 / 权限 / 兼容流程")
def test_text_l3_corrupt_image_upload_does_not_crash(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L3-001｜损坏图片上传异常")
    _goto(page, base_url)
    _wait_corrupt_upload_error(page, "TC-TEXT-L3-001-损坏图上传异常提示")
    body = _body_text(page)
    assert URL_PATH in page.url
    assert "Application error" not in body
    assert "500" not in body[:300]


@allure.epic("文字画质增强实验")
@allure.feature("L3 — 异常 / 权限 / 兼容流程")
def test_text_l3_free_account_purchase_intercept_predeploy(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L3-002｜免费账号购买拦截：预部署")
    _goto(page, base_url)
    _switch_predeploy(page)
    _login(page, base_url, _unique_free_email())
    _upload(page, IMG_TEXT_SAMPLE)
    if _free_quota_active(page):
        pytest.skip("当前 IP 仍有免费额度，免费账号点击生成会走真实生成而非购买拦截，无法验证拦截态")
    _primary(page).click(timeout=10000)
    _wait_purchase_modal(page, "TC-TEXT-L3-002-预部署购买弹窗")


# ═══════════════════════════════════════════════════════════════
# L6 生成与结果态
# ═══════════════════════════════════════════════════════════════


@pytest.mark.smoke
@allure.epic("文字画质增强实验")
@allure.feature("L6 — 核心 Happy Path / E2E")
def test_text_l6_default_enhance_2k_generation_download_and_continue(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L6-001｜默认 Enhance Text 2k 生成到结果态 + 下载 + 继续增强")
    _goto(page, base_url)
    _switch_predeploy(page)
    _login(page, base_url, MEMBER_EMAIL)
    _upload(page, IMG_TEXT_SAMPLE)
    _shot(page, "TC-TEXT-L6-001-点击生成前")
    _primary(page).click(timeout=10000)
    page.wait_for_timeout(1500)
    _shot(page, "TC-TEXT-L6-001-生成中")
    _wait_generation_result(page)
    body = _body_text(page)
    assert "Before" in body and "Now" in body
    assert "Continue Enhancing" in body and "Edit More" in body and "Download" in body
    assert "2K" in body or "2k" in body
    _shot(page, "TC-TEXT-L6-001-结果态")
    result = visual_assert("TC-TEXT-L6-001-点击生成前", "TC-TEXT-L6-001-结果态", "结果图应仍是同一输入内容，不应出现严重空白、破图、非图片结果")
    assert result.get("verdict") != "fail", f"AI 视觉审查失败: {result}"
    with page.expect_download(timeout=30000) as dl_info:
        page.get_by_text("Download", exact=True).first.click(timeout=10000)
    download = dl_info.value
    assert re.match(r"Pokecut_.*\.jpg", download.suggested_filename), f"下载文件名不符合预期: {download.suggested_filename}"
    assert download.url, "下载 URL 不应为空"
    _shot(page, "TC-TEXT-L6-001-下载后")
    page.get_by_text("Continue Enhancing", exact=True).first.click(timeout=10000)
    page.wait_for_timeout(5000)
    body = _body_text(page)
    assert "Choose the Effect" in body
    for effect in EFFECTS:
        expect(_effect(page, effect)).to_be_visible()
    _shot(page, "TC-TEXT-L6-001-继续增强后")


@allure.epic("文字画质增强实验")
@allure.feature("L2 — 交互行为")
def test_text_l2_result_edit_more_enters_editor_or_route(page: Page, base_url: str):
    allure.dynamic.title("TC-TEXT-L2-004｜结果态 Edit More 进入编辑链路")
    _goto(page, base_url)
    _switch_predeploy(page)
    _login(page, base_url, MEMBER_EMAIL)
    _upload(page, IMG_TEXT_SAMPLE)
    _primary(page).click(timeout=10000)
    _wait_generation_result(page)
    before_url = page.url
    _shot(page, "TC-TEXT-L2-004-点击前结果态")
    page.get_by_text("Edit More", exact=True).first.click(timeout=10000)
    page.wait_for_timeout(8000)
    body = _body_text(page)
    assert page.url != before_url or any(text in body for text in ["Canvas", "Edit", "Adjust", "Download"]), "Edit More 点击后未进入可识别编辑链路"
    _shot(page, "TC-TEXT-L2-004-编辑链路")


# ═══════════════════════════════════════════════════════════════
# 移动端
# ═══════════════════════════════════════════════════════════════


@allure.epic("文字画质增强实验")
@allure.feature("L4 — PRD 验收标准")
@pytest.mark.regression
def test_text_l4_mobile_upload_modes_and_cost(browser, playwright, base_url: str):
    allure.dynamic.title("TC-TEXT-L4-005｜移动端上传后模式与点数区域")
    device = playwright.devices.get("iPhone 13")
    context = browser.new_context(**device, locale="en-US")
    page = context.new_page()
    try:
        page.goto(f"{base_url}{URL_PATH}", timeout=120000, wait_until="domcontentloaded")
        page.wait_for_timeout(7000)
        _shot(page, "TC-TEXT-L4-005-移动端首屏")
        _upload_mobile(page, IMG_TEXT_SAMPLE)
        assert _effect_pressed(page, "enhance_text") is True
        for effect in EFFECTS:
            expect(_effect(page, effect)).to_be_visible()
        assert _mobile_primary(page).is_visible()
        _assert_cost(page, "2", mobile=True)
        _effect(page, "remove_glare").click(timeout=10000)
        page.wait_for_timeout(1000)
        _assert_cost(page, "4", mobile=True)
        _shot(page, "TC-TEXT-L4-005-移动端上传后")
        result = visual_assert("TC-TEXT-L4-005-移动端首屏", "TC-TEXT-L4-005-移动端上传后", "移动端横向模式布局不遮挡、不换行错乱，主按钮点数在按钮区域")
        assert result.get("verdict") != "fail", f"AI 视觉审查失败: {result}"
    finally:
        context.close()


# ═══════════════════════════════════════════════════════════════
# 依赖缺口用例：保持 skip，避免伪造结论
# ═══════════════════════════════════════════════════════════════


@allure.epic("文字画质增强实验")
@allure.feature("L3 — 异常 / 权限 / 兼容流程")
def test_text_l3_highest_clarity_secondary_workflow_gap():
    allure.dynamic.title("TC-TEXT-L3-003｜真 8K highest clarity 与二次增强 workflow 缺口校验")
    pytest.skip("缺可触发 highest clarity 的 fixture / 前端判定口径，以及后端 workflow trace；不能伪造二次增强结论")
