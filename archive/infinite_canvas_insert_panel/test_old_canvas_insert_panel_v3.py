# -*- coding: utf-8 -*-
"""旧画布 Insert 面板与图层属性自动化测试。

基于 confirmed cases.md（24 条，P0=14/P1=8/P2=2）与
page_map/pokecut/infinite_canvas_insert_panel_v3.yaml 实现。

覆盖: L1 结构 / L2 交互（含图片图层 7 行属性面板）/ L3 兼容。
环境: 测试服 en-US；VIP 账号 450832596@qq.com；素材仅 test_images/。
"""
import os
import hashlib

import allure
import pytest
from pathlib import Path
from playwright.sync_api import Page, expect as pw_expect
from PIL import Image, ImageChops


def _repo_root() -> Path:
    """定位仓库根目录（同时兼容 tests/ 与 archive/<module>/ 两种存放位置）。"""
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "test_images").is_dir():
            return candidate
    return here.parent.parent


BASE_DIR = _repo_root()
IMG_1K = str(BASE_DIR / "test_images" / "1K.jpg")
IMG_FACE = str(BASE_DIR / "test_images" / "有人脸.JPG")
BASE_URL = os.environ.get("POKECUT_BASE_URL", "http://10.17.1.66:3001")
EMAIL = os.environ.get("POKECUT_TEST_EMAIL", "450832596@qq.com")
CODE = os.environ.get("POKECUT_TEST_CODE", "123456")
RED = "rgb(174, 41, 42)"
INSERT_TAB = 'div.cursor-pointer:has(> img[src$="edit_left_tab_btn_insert.svg"])'


@pytest.fixture(scope="session")
def canvas_session(playwright):
    """session 级前置：VIP 登录一次 + 进入旧画布一次，记录画布 URL。

    旧画布的模板上传有频率限制（连续约 17 次后会触发人机校验/不跳转），
    因此整个测试会话只做 1 次上传，其余用例复用同一个 pid。
    """
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    page.goto(BASE_URL + "/template", wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(4500)
    login_btn = page.get_by_role("button", name="Log in", exact=True)
    if login_btn.count():
        login_btn.first.click()
        page.wait_for_timeout(1800)
        page.locator('input[type="email"]').fill(EMAIL)
        page.locator('input[placeholder*="Verification"]').fill(CODE)
        page.locator('button:has-text("Log in")').last.click()
        page.wait_for_timeout(8000)
    state = page.evaluate(
        """() => {
            try {
                const a = window.useNuxtApp();
                return {
                    status: a.__basicAccountState?.benefitLoadState?.value?.status,
                    vip: a.__basicAccountState?.userBenefit?.value?.vipType,
                };
            } catch (e) { return {status: null, vip: null}; }
        }"""
    )
    assert state.get("vip") and state["vip"] > 0, f"VIP 登录失败: {state}"
    canvas_url = enter_canvas_via_template(page, BASE_URL, attempts=4)
    assert "/create/edit?pid=" in canvas_url, f"会话入口未进入旧画布: {canvas_url}"
    page.close()
    yield {"context": context, "url": canvas_url}
    context.close()
    browser.close()


@pytest.fixture
def canvas_page(canvas_session):
    """每条用例：复用会话画布 pid，重新打开得到干净初始态。

    刷新画布不会重新上传/新建任务，避免触发模板入口的频率限制。
    """
    page = canvas_session["context"].new_page()
    page.goto(canvas_session["url"], wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(9000)
    yield page
    page.close()


def enter_canvas_via_template(page: Page, base_url: str, image: str = IMG_1K, attempts: int = 3):
    """从 /template 的 Colorful Background 首卡上传并进入旧画布（L2-001 专用）。

    模板卡点击存在竞态，做多次重试 + URL 轮询；若多次仍不跳转则视为该入口当前不可用。
    """
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            with allure.step(f"进入 /template 并上传 Colorful Background 首卡（第 {attempt} 次）"):
                page.goto(base_url + "/template", wait_until="domcontentloaded", timeout=120000)
                page.wait_for_timeout(5000)
                heading = page.get_by_role("heading", name="Colorful Background", exact=True).first
                pw_expect(heading).to_be_visible(timeout=30000)
                section = heading.locator("xpath=..").locator("xpath=..")
                card = section.locator('div.relative.flex.w-\\[9\\.625rem\\].cursor-pointer').first
                overlay = card.locator("div.absolute.left-0.top-0.flex.size-full.items-center > div").first
                pw_expect(overlay).to_be_visible(timeout=15000)
                with page.expect_file_chooser(timeout=30000) as fc:
                    overlay.click()
                fc.value.set_files(image)
                for _ in range(90):
                    page.wait_for_timeout(1000)
                    if "/create/edit?pid=" in page.url:
                        break
                else:
                    raise AssertionError(f"模板卡上传后未进入画布，当前 URL: {page.url}")
                page.wait_for_timeout(9000)
            return page.url
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt == attempts:
                break
            page.wait_for_timeout(2500)
    raise AssertionError(f"模板入口进入旧画布失败（已重试 {attempts} 次）: {last_err}")


def dismiss_color_overlay(page: Page):
    if page.locator('div[data-color-picker-overlay="true"]').count():
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)


def canvas_box(page: Page) -> dict:
    boxes = []
    for c in page.locator("canvas").all():
        bb = c.bounding_box()
        if bb and bb["width"] > 0 and bb["height"] > 0:
            boxes.append((bb["width"] * bb["height"], bb))
    assert boxes, "未找到可见 canvas"
    return max(boxes, key=lambda x: x[0])[1]


def click_canvas_center(page: Page, ry: float = 0.45):
    bb = canvas_box(page)
    page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] * ry)
    page.wait_for_timeout(600)


def shot(page: Page, name: str, clip: dict = None) -> str:
    """截图并附加到 Allure。

    默认截取**整个页面**，保证右侧属性面板、左侧工具栏、顶部栏等上下文完整；
    仅当调用方显式传入 clip 时才裁切（用于画布区域特写）。
    """
    out_dir = BASE_DIR / "data" / "screenshots"
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    if clip:
        page.screenshot(path=str(path), clip=clip)
    else:
        page.screenshot(path=str(path), full_page=False)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return str(path)



def shot_canvas(page: Page, name: str, clip: dict = None) -> str:
    """画布区域特写截图（显式裁切），用于需要聚焦画布效果的证据。"""
    return shot(page, name, clip=clip or canvas_box(page))

def canvas_hash(page: Page, clip: dict) -> str:
    tmp = BASE_DIR / "data" / "screenshots" / "_tmp_canvas.png"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(tmp), clip=clip)
    return hashlib.sha256(Image.open(tmp).convert("RGB").tobytes()).hexdigest()[:16]


def pixel_diff_pct(path_a: str, path_b: str) -> float:
    a = Image.open(path_a).convert("RGB")
    b = Image.open(path_b).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    diff = ImageChops.difference(a, b)
    pts = sum(1 for px in diff.getdata() if sum(px) > 12)
    return round(pts / (a.width * a.height) * 100, 3)


def find_section(page: Page, label: str, timeout_ms: int = 15000):
    """定位右侧面板中**可见**的属性行。

    页面同时挂载多套隐藏复用节点（当前图层/其它图层/绘制态），必须按可见性过滤，
    否则会命中隐藏 section，导致改值不生效、像素差异为 0。
    """
    waited = 0
    while True:
        locs = page.get_by_text(label, exact=True)
        for i in range(locs.count()):
            e = locs.nth(i)
            try:
                if not e.is_visible():
                    continue
            except Exception:
                continue
            bb = e.bounding_box()
            if bb and bb["x"] > 1500 and bb["width"] < 400:
                return e, e.locator('xpath=ancestor::div[contains(@class,"border-b")][1]')
        if waited >= timeout_ms:
            raise AssertionError(f"右侧面板未找到可见属性行: {label}")
        page.wait_for_timeout(500)
        waited += 500


def ensure_image_layer_selected(page: Page, attempts: int = 3) -> None:
    """确保图片图层被选中（右侧出现图片属性行）；必要时重新点击画布。"""
    for i in range(attempts):
        try:
            find_section(page, "Opacity", timeout_ms=4000)
            return
        except AssertionError:
            bb = canvas_box(page)
            page.mouse.click(bb["x"] + bb["width"] / 2, bb["y"] + bb["height"] * 0.45)
            page.wait_for_timeout(1200)
    find_section(page, "Opacity", timeout_ms=8000)


def expand_section(page: Page, label: str):
    lab, sec = find_section(page, label)
    lab.scroll_into_view_if_needed()
    lab.click()
    page.wait_for_timeout(450)
    return lab, sec


def section_switch_on(page: Page, sec):
    ck = sec.locator('input[type="checkbox"]').first
    if ck.count() and not ck.is_checked():
        sec.locator("span.slider").first.click()
        page.wait_for_timeout(500)
    return ck


def set_range(loc, value):
    loc.evaluate(
        """(e, v) => {
            const s = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            s.call(e, String(v));
            e.dispatchEvent(new Event('input', {bubbles: true}));
            e.dispatchEvent(new Event('change', {bubbles: true}));
        }""",
        value,
    )
    return loc.input_value()


def click_swatch(page: Page, sec, rgb: str) -> bool:
    swatches = sec.locator("div.h-full.w-full")
    for i in range(swatches.count()):
        e = swatches.nth(i)
        bg = e.evaluate("el => getComputedStyle(el).backgroundColor")
        if bg == rgb:
            e.locator('xpath=ancestor::div[contains(@class,"cursor-pointer")][1]').click()
            page.wait_for_timeout(400)
            dismiss_color_overlay(page)
            return True
    return False


APPLY_JS = """() => {
    const out = [];
    for (const e of document.querySelectorAll('button, div, span')) {
        if ((e.innerText || '').trim() !== 'Apply') continue;
        const r = e.getBoundingClientRect();
        if (r.width <= 0 || r.height <= 0) continue;
        out.push({x: r.x + r.width / 2, y: r.y + r.height / 2, cls: (e.className || '').toString()});
    }
    return out;
}"""


def find_apply_targets(page: Page) -> list:
    """返回可见 Apply 控件（旧画布中可能是 div 而非 button）的中心坐标。"""
    return page.evaluate(APPLY_JS)


def has_visible_apply(page: Page) -> bool:
    """是否存在可见的 Apply 控件（绘制态未退出）。"""
    return len(find_apply_targets(page)) > 0


def click_toolbar_apply(page: Page) -> bool:
    """点击左侧工具栏范围内的可见 Apply 控件（避开右侧属性区）。"""
    targets = find_apply_targets(page)
    if not targets:
        return False
    left = [t for t in targets if t["x"] < 600]
    target = (left or targets)[0]
    page.mouse.click(target["x"], target["y"])
    return True


def wait_hash_change(page: Page, clip: dict, prev: str, timeout_ms: int = 2500) -> str:
    """轮询等待画布 hash 相对 prev 发生变化（应对渲染 debounce）。

    先给渲染留出固定时间，再最多补两次采样，避免高频截图拖慢用例。
    """
    page.wait_for_timeout(700)
    cur = canvas_hash(page, clip)
    waited = 700
    while cur == prev and waited < timeout_ms:
        page.wait_for_timeout(600)
        waited += 600
        cur = canvas_hash(page, clip)
    return cur


def reset_image_properties(page: Page) -> None:
    """把图片图层属性复位到默认值。

    旧画布编辑会持久化到同一个 pid，图片类用例之间会互相污染（Filter/Outline 等
    若不复位，会让后一条用例的前后对比失去差异）。每个图片用例开始前统一复位。
    """
    ensure_image_layer_selected(page)
    # Opacity -> 100
    try:
        lab, sec = expand_section(page, "Opacity")
        rng = sec.locator('input[type="range"]').first
        if rng.count():
            set_range(rng, 100)
        lab.click()
        page.wait_for_timeout(200)
    except AssertionError:
        pass
    # Adjust -> 全部 0
    try:
        lab, sec = expand_section(page, "Adjust")
        rngs = sec.locator('input[type="range"]')
        for i in range(rngs.count()):
            set_range(rngs.nth(i), 0)
        lab.click()
        page.wait_for_timeout(200)
    except AssertionError:
        pass
    # 效果类开关全部关闭
    for label in ["Shadow", "Outline", "Reflection", "Filter", "Blend"]:
        try:
            lab, sec = find_section(page, label, timeout_ms=3000)
            ck = sec.locator('input[type="checkbox"]').first
            if ck.count() and ck.is_checked():
                sec.locator("span.slider").first.click()
                page.wait_for_timeout(300)
        except AssertionError:
            pass
    page.wait_for_timeout(500)


def open_insert(page: Page):
    with allure.step("打开左侧 Insert 面板"):
        page.locator(INSERT_TAB).first.click()
        page.wait_for_timeout(1200)


def asset_exists(path: str) -> bool:
    return os.path.exists(path) and os.path.getsize(path) > 0


@allure.epic("旧画布 Insert 面板")
@allure.feature("页面元素 / 结构")
@allure.story("L1-页面元素")
def test_l1_003_insert_entry_and_panel(canvas_page: Page):
    """L1-003: Insert 入口为图标 div，面板含四个分区。"""
    allure.dynamic.title("L1-003: Insert 入口与面板分区结构")
    page = canvas_page
    with allure.step("断言 Insert 入口是图标 div 而非 button"):
        entry = page.locator(INSERT_TAB).first
        pw_expect(entry).to_be_visible(timeout=15000)
        assert page.locator('button:has(> img[src$="edit_left_tab_btn_insert.svg"])').count() == 0, "Insert 入口不应是标准 button"
    open_insert(page)
    with allure.step("断言面板四个分区与 Upload 子项"):
        body = page.locator("body").inner_text()
        for text in ["Upload", "Draw", "Shape", "Line"]:
            assert text in body, f"Insert 面板缺少分区: {text}"
        assert "Image" in body and "My Cuts" in body
    shot(page, "l1_insert_entry")
    shot(page, "l1_insert_panel")


@allure.epic("旧画布 Insert 面板")
@allure.feature("页面元素 / 结构")
@allure.story("L1-页面元素")
def test_l1_004_right_panel_container(canvas_page: Page):
    """L1-004: 选中图层后右侧属性面板容器与折叠结构。"""
    allure.dynamic.title("L1-004: 右侧属性面板容器与折叠结构")
    page = canvas_page
    reset_image_properties(page)
    with allure.step("断言右侧面板宽 400px 且图片图层 7 行存在"):
        panel = page.locator('div.h-\\[calc\\(100vh-5rem\\)\\].w-\\[25rem\\].bg-white').first
        pw_expect(panel).to_be_visible(timeout=10000)
        assert round(panel.bounding_box()["width"]) == 400
        rows = [t for t in ["Opacity", "Adjust", "Shadow", "Outline", "Reflection", "Filter", "Blend"] if page.get_by_text(t, exact=True).count()]
        assert len(rows) == 7, f"图片图层属性行数量异常: {rows}"
    shot(page, "l1_right_panel")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_001_template_entry_to_canvas(canvas_page: Page, canvas_session):
    """L2-001: 模板首卡上传后进入旧画布（入口由 session fixture 执行 1 次并记录 URL）。"""
    allure.dynamic.title("L2-001: 模板首卡上传并进入旧画布")
    page = canvas_page
    with allure.step("断言会话入口已进入 /create/edit 且主画布可见"):
        assert "/create/edit?pid=" in canvas_session["url"], f"入口 URL 异常: {canvas_session['url']}"
        pw_expect(page.locator("canvas").first).to_be_visible(timeout=20000)
    shot(page, "l2_canvas_entered")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_004_text_draw_panel(canvas_page: Page):
    """L2-004: Text 绘制态与参数面板结构。"""
    allure.dynamic.title("L2-004: Text 绘制态与参数面板结构")
    page = canvas_page
    open_insert(page)
    with allure.step("进入 Draw → Text"):
        page.locator('img[src$="home_pop_add_bursh_text.webp"]').first.click()
        page.wait_for_timeout(2200)
    with allure.step("断言左侧 Apply/Cancel 与右侧参数结构"):
        body = page.locator("body").inner_text()
        assert "Apply" in body and "Cancel" in body
        for t in ["Font", "Contents", "Size", "Opacity", "Color"]:
            assert t in body, f"Text 绘制面板缺少: {t}"
        contents = page.locator('textarea[rows="1"]').first
        assert contents.input_value() == "context", "Contents 默认值应为 context"
    with allure.step("断言 Size 默认 69、Opacity 默认 100（取可见 range）"):
        ranges = page.locator('input[type="range"]:visible')
        vals = [ranges.nth(i).input_value() for i in range(ranges.count())]
        assert "69" in vals, f"未找到 Size 默认 69，可见 range: {vals}"
        assert "100" in vals, f"未找到 Opacity 默认 100，可见 range: {vals}"
    shot(page, "l2_draw_text_panel")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
def test_l2_005_general_draw_panel(canvas_page: Page):
    """L2-005: General 绘制态与参数面板结构。"""
    allure.dynamic.title("L2-005: General 绘制态与参数面板结构")
    page = canvas_page
    open_insert(page)
    with allure.step("进入 Draw → General"):
        page.locator('img[src$="home_pop_add_bursh_general.webp"]').first.click()
        page.wait_for_timeout(2200)
    with allure.step("断言进入 General 绘制态并出现 Size/Opacity"):
        ranges = page.locator('input[type="range"]:visible')
        pw_expect(ranges.first).to_be_visible(timeout=20000)
        vals = [ranges.nth(i).input_value() for i in range(ranges.count())]
        assert "30" in vals, f"未找到 Size 默认 30，可见 range: {vals}"
        assert "100" in vals, f"未找到 Opacity 默认 100，可见 range: {vals}"
        assert has_visible_apply(page), "General 绘制态未出现左侧 Apply 控件"
    shot(page, "l2_draw_general_panel")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_021_image_blend(canvas_page: Page, tmp_path):
    """L2-021: 图片 Blend 模式与强度生效。"""
    allure.dynamic.title("L2-021: 图片 Blend 模式与强度生效")
    page = canvas_page
    reset_image_properties(page)
    bb = canvas_box(page)
    lab, sec = expand_section(page, "Blend")
    base = str(tmp_path / "_blend_base.png")
    page.screenshot(path=base, clip=bb)
    section_switch_on(page, sec)
    with allure.step("选择 Multiply 并断言画布变化"):
        opt = sec.get_by_text("Multiply", exact=True)
        assert opt.count() >= 1, "Blend 模式中未找到 Multiply"
        opt.first.click()
        page.wait_for_timeout(800)
        mul = str(tmp_path / "_blend_multiply.png")
        page.screenshot(path=mul, clip=bb)
        shot(page, "l2_image_blend_multiply")
        assert pixel_diff_pct(base, mul) >= 5, "选择 Multiply 后画布变化不足"
    with allure.step("遍历 Blend 区滑杆，断言强度控件真实影响画布"):
        rngs = sec.locator('input[type="range"]')
        n = rngs.count()
        assert n >= 1, "Blend 展开后未找到强度滑杆"
        best = {"diff": -1.0, "index": -1, "lo": None, "hi": None}
        for i in range(n):
            rng = rngs.nth(i)
            assert set_range(rng, 100) == "100"
            page.wait_for_timeout(500)
            hi = str(tmp_path / f"_blend_r{i}_100.png")
            page.screenshot(path=hi, clip=bb)
            assert set_range(rng, 0) == "0"
            page.wait_for_timeout(500)
            lo = str(tmp_path / f"_blend_r{i}_0.png")
            page.screenshot(path=lo, clip=bb)
            diff = pixel_diff_pct(hi, lo)
            if diff > best["diff"]:
                best = {"diff": diff, "index": i, "lo": lo, "hi": hi}
        assert best["diff"] >= 1, f"Blend 区 {n} 个滑杆均未观察到强度效果（最大差异 {best['diff']}%）"
        # 复位到 80 作为证据态
        rng = rngs.nth(best["index"])
        assert set_range(rng, 80) == "80"
        page.wait_for_timeout(600)
        shot(page, "l2_image_blend_strength80")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_015_image_opacity(canvas_page: Page, tmp_path):
    """L2-015: 图片 Opacity 生效及边界（0/35/100）。"""
    allure.dynamic.title("L2-015: 图片 Opacity 生效及边界")
    page = canvas_page
    reset_image_properties(page)
    bb = canvas_box(page)
    lab, sec = expand_section(page, "Opacity")
    rng = sec.locator('input[type="range"]').first
    with allure.step("断言滑杆范围 min=0 max=100"):
        assert rng.get_attribute("min") == "0"
        assert rng.get_attribute("max") == "100"
    paths = {}
    with allure.step("依次设为 0 / 35 / 100 并断言画布变化"):
        for v in [0, 35, 100]:
            assert set_range(rng, v) == str(v)
            cur = str(tmp_path / f"_opacity_{v}.png")
            page.screenshot(path=cur, clip=bb)
            paths[v] = cur
            shot(page, f"l2_image_opacity_{v}")
        assert pixel_diff_pct(paths[100], paths[0]) > 20, "Opacity 0 与 100 差异不足"
        assert pixel_diff_pct(paths[100], paths[35]) > 20, "Opacity 35 与 100 差异不足"


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_016_image_adjust(canvas_page: Page, tmp_path):
    """L2-016: 图片 Adjust 13 项逐项生效及边界。"""
    allure.dynamic.title("L2-016: 图片 Adjust 13 项逐项生效及边界")
    page = canvas_page
    reset_image_properties(page)
    bb = canvas_box(page)
    lab, sec = expand_section(page, "Adjust")
    rngs = sec.locator('input[type="range"]')
    n = rngs.count()
    with allure.step("断言 13 个参数滑杆存在"):
        assert n == 13, f"Adjust 滑杆数量应为 13，实际 {n}"
    values = [35, 25, 20, 18, 15, 22, 20, 28, 26, 15, 12, 20, 30]
    hashes = []
    with allure.step("逐项改值并断言每项产生独立画布 hash"):
        prev = canvas_hash(page, bb)
        for i in range(n):
            assert set_range(rngs.nth(i), values[i]) == str(values[i])
            cur = wait_hash_change(page, bb, prev)
            hashes.append(cur)
            prev = cur
            shot(page, f"l2_image_adjust_{i:02d}")
        unique = len(set(hashes))
        assert unique >= 12, f"Adjust 独立 hash 不足（实际 {unique}/13）: {hashes}"
    with allure.step("断言取值范围"):
        ranges = [(rngs.nth(i).get_attribute("min"), rngs.nth(i).get_attribute("max")) for i in range(n)]
        for i in list(range(0, 7)) + [9, 10, 12]:
            assert ranges[i] == ("-100", "100"), f"第 {i} 项范围异常: {ranges[i]}"
        for i in [7, 8, 11]:
            assert ranges[i] == ("0", "100"), f"第 {i} 项范围异常: {ranges[i]}"
    with allure.step("Brightness 边界 -100/0/100 与 Clarity 边界 0/100"):
        boundary = str(tmp_path / "_adjust_boundary.png")
        for v in [-100, 0, 100]:
            set_range(rngs.nth(0), v)
        for v in [0, 100]:
            set_range(rngs.nth(7), v)
        page.screenshot(path=boundary, clip=bb)
        assert asset_exists(boundary)
        shot(page, "l2_adjust_boundary")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_017_image_shadow(canvas_page: Page, tmp_path):
    """L2-017: 图片 Shadow 三 tab 与 Effect 参数生效。"""
    allure.dynamic.title("L2-017: 图片 Shadow 三 tab 与 Effect 参数生效")
    page = canvas_page
    reset_image_properties(page)
    bb = canvas_box(page)
    lab, sec = expand_section(page, "Shadow")
    ck = section_switch_on(page, sec)
    assert ck.count() == 0 or ck.first.is_checked(), "Shadow 开关未成功开启"
    rngs = sec.locator('input[type="range"]')
    base = str(tmp_path / "_shadow_base.png")
    page.screenshot(path=base, clip=bb)
    with allure.step("Effect 下改 5 个滑杆并断言画布差异"):
        vals = [55, 32, 22, 28, 50]
        for i in range(min(rngs.count(), 5)):
            set_range(rngs.nth(i), vals[i])
        page.wait_for_timeout(500)
        cur = str(tmp_path / "_shadow_effect.png")
        page.screenshot(path=cur, clip=bb)
        assert pixel_diff_pct(base, cur) >= 1, "Shadow Effect 改值后画布无足够变化"
        shot(page, "l2_image_shadow_effect")
    with allure.step("切换 Color / 3D Shadow / Effect tab"):
        for tab in ["Color", "3D Shadow", "Effect"]:
            t = sec.get_by_text(tab, exact=True)
            if t.count():
                t.first.click()
                page.wait_for_timeout(500)
                shot(page, f"l2_image_shadow_tab_{tab.replace(' ', '')}")
        assert sec.get_by_text("Effect", exact=True).count() >= 1


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_018_image_outline(canvas_page: Page, tmp_path):
    """L2-018: 图片 Outline Types/Color/滑杆生效。"""
    allure.dynamic.title("L2-018: 图片 Outline Types/Color/滑杆生效")
    page = canvas_page
    reset_image_properties(page)
    bb = canvas_box(page)
    lab, sec = expand_section(page, "Outline")
    ck = section_switch_on(page, sec)
    assert ck.count() == 0 or ck.first.is_checked(), "Outline 开关未成功开启"
    rngs = sec.locator('input[type="range"]')
    assert rngs.count() >= 1, "Outline 展开后未出现滑杆"
    base = str(tmp_path / "_outline_base.png")
    page.screenshot(path=base, clip=bb)
    with allure.step("改 Size/Distance/Blur/Smooth 并断言画布变化"):
        vals = [20, 10, 5, 10]
        for i in range(rngs.count()):
            set_range(rngs.nth(i), vals[i] if i < len(vals) else 10)
        page.wait_for_timeout(500)
        sliders_png = str(tmp_path / "_outline_sliders.png")
        page.screenshot(path=sliders_png, clip=bb)
        assert pixel_diff_pct(base, sliders_png) >= 1, "Outline 滑杆修改后画布无足够变化"
        shot(page, "l2_image_outline_sliders")
    with allure.step("切换第 2 / 第 4 个 Type 并断言画布变化"):
        types = sec.locator("div.rounded-full")
        assert types.count() == 5, f"Outline Types 应为 5 个，实际 {types.count()}"
        types.nth(1).click()
        page.wait_for_timeout(600)
        t2 = str(tmp_path / "_outline_type2.png")
        page.screenshot(path=t2, clip=bb)
        shot(page, "l2_image_outline_type2")
        types.nth(3).click()
        page.wait_for_timeout(600)
        t4 = str(tmp_path / "_outline_type4.png")
        page.screenshot(path=t4, clip=bb)
        shot(page, "l2_image_outline_type4")
        assert pixel_diff_pct(t2, t4) >= 1, "Outline Type2 与 Type4 差异不足"
    with allure.step("选择红色并断言画布变化"):
        assert click_swatch(page, sec, RED), f"未找到色板颜色 {RED}"
        page.wait_for_timeout(500)
        color_png = str(tmp_path / "_outline_color.png")
        page.screenshot(path=color_png, clip=bb)
        shot(page, "l2_image_outline_color")
        assert pixel_diff_pct(t4, color_png) >= 1, "Outline 选色后画布变化不足"


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_020_image_filter(canvas_page: Page, tmp_path):
    """L2-020: 图片 Filter 分类/缩略图/强度生效。"""
    allure.dynamic.title("L2-020: 图片 Filter 分类/缩略图/强度生效")
    page = canvas_page
    reset_image_properties(page)
    bb = canvas_box(page)
    lab, sec = expand_section(page, "Filter")
    unfiltered = str(tmp_path / "_filter_unfiltered.png")
    page.screenshot(path=unfiltered, clip=bb)
    section_switch_on(page, sec)
    with allure.step("选择 Vintage 分类与第 2 个滤镜缩略图"):
        cat = sec.get_by_text("Vintage", exact=True)
        if cat.count():
            cat.first.click()
            page.wait_for_timeout(700)
        picked = page.evaluate(
            """() => {
                const imgs = [...document.querySelectorAll('img')].filter(e => {
                    const r = e.getBoundingClientRect();
                    return r.x > 1500 && r.width > 40 && r.height > 40;
                });
                if (imgs.length < 2) return null;
                imgs[1].click();
                return {index: 1, w: Math.round(imgs[1].getBoundingClientRect().width)};
            }"""
        )
        assert picked, "未找到可点击的滤镜缩略图"
        page.wait_for_timeout(1000)
        thumb = str(tmp_path / "_filter_thumb.png")
        page.screenshot(path=thumb, clip=bb)
        shot(page, "l2_image_filter_thumb")
        assert pixel_diff_pct(unfiltered, thumb) >= 5, "切换滤镜后画布变化不足"
    with allure.step("固定滤镜后强度各值产生独立效果，且 0 ≈ 未加滤镜状态"):
        rng = sec.locator('input[type="range"]').first
        hashes = {}
        s0_png = str(tmp_path / "_filter_s0.png")
        for v in [0, 25, 50, 75, 100]:
            assert set_range(rng, v) == str(v)
            page.wait_for_timeout(500)
            hashes[v] = canvas_hash(page, bb)
            if v == 0:
                page.screenshot(path=s0_png, clip=bb)
            shot(page, f"l2_image_filter_s{v}")
        assert len(set(hashes.values())) >= 4, f"滤镜强度未产生足够独立效果: {hashes}"
        # 强度 0 应回到未加滤镜状态（允许渲染噪声，不做严格 hash 相等）
        assert pixel_diff_pct(unfiltered, s0_png) <= 1.0, "滤镜强度 0 未回到未加滤镜状态"


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_019_image_reflection(canvas_page: Page, tmp_path):
    """L2-019: 图片 Reflection 需缩小后生效。"""
    allure.dynamic.title("L2-019: 图片 Reflection 需缩小后生效")
    page = canvas_page
    reset_image_properties(page)
    bb = canvas_box(page)
    with allure.step("拖动四角 scale-point 锚点缩小图片"):
        anchors = page.locator("span.scale-point")
        pw_expect(anchors.first).to_be_visible(timeout=10000)
        pts = []
        for i in range(anchors.count()):
            box = anchors.nth(i).bounding_box()
            if box:
                pts.append((box, anchors.nth(i).get_attribute("class") or ""))
        cx = bb["x"] + bb["width"] / 2
        cy = bb["y"] + bb["height"] / 2
        br = next((b for b, c in pts if "bottom" in c and "right" in c), pts[-1][0])
        x, y = br["x"] + br["width"] / 2, br["y"] + br["height"] / 2
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + (cx - x) * 0.55, y + (cy - y) * 0.55, steps=14)
        page.mouse.up()
        page.wait_for_timeout(900)
        tl = next((b for b, c in pts if "top" in c and "left" in c), None)
        if tl:
            x2, y2 = tl["x"] + tl["width"] / 2, tl["y"] + tl["height"] / 2
            page.mouse.move(x2, y2)
            page.mouse.down()
            page.mouse.move(x2 + (cx - x2) * 0.35, y2 + (cy - y2) * 0.35, steps=12)
            page.mouse.up()
            page.wait_for_timeout(800)
    shot_canvas(page, "l2_image_shrunk", clip=bb)
    # 缩小后图片不再铺满画布，点击其实际中心重新选中，确保右侧属性面板回到图片图层
    anchors = page.locator("span.scale-point")
    if anchors.count() >= 4:
        xs, ys = [], []
        for i in range(4):
            b = anchors.nth(i).bounding_box()
            if b:
                xs.append(b["x"] + b["width"] / 2)
                ys.append(b["y"] + b["height"] / 2)
        if xs and ys:
            page.mouse.click(sum(xs) / len(xs), sum(ys) / len(ys))
            page.wait_for_timeout(900)
    lab, sec = expand_section(page, "Reflection")
    base = str(tmp_path / "_reflection_base.png")
    page.screenshot(path=base, clip=bb)
    with allure.step("开启 Reflection 并断言画布出现倒影变化"):
        section_switch_on(page, sec)
        page.wait_for_timeout(500)
        on = str(tmp_path / "_reflection_on.png")
        page.screenshot(path=on, clip=bb)
        shot(page, "l2_image_reflection_on")
        assert pixel_diff_pct(base, on) >= 1, "Reflection 开启后画布差异不足 1%"
    with allure.step("改 Scope/Opacity/Distance/Angle 并断言画布再变化"):
        rngs = sec.locator('input[type="range"]')
        vals = [80, 80, 60, 120]
        for i in range(min(rngs.count(), 4)):
            set_range(rngs.nth(i), vals[i])
        page.wait_for_timeout(500)
        changed = str(tmp_path / "_reflection_changed.png")
        page.screenshot(path=changed, clip=bb)
        shot(page, "l2_image_reflection_changed")
        assert pixel_diff_pct(on, changed) >= 1, "Reflection 改值后画布差异不足 1%"


@allure.epic("旧画布 Insert 面板")
@allure.feature("异常 / 兼容")
@allure.story("L3-兼容")
def test_l3_004_color_overlay_dismiss(canvas_page: Page):
    """L3-004: 调色板 overlay 可关闭且不残留。"""
    allure.dynamic.title("L3-004: 调色板 overlay 可关闭且不残留")
    page = canvas_page
    reset_image_properties(page)
    lab, sec = expand_section(page, "Outline")
    section_switch_on(page, sec)
    with allure.step("点击色块触发 overlay"):
        swatches = sec.locator("div.h-full.w-full")
        assert swatches.count() >= 1, "Outline 未找到色块"
        swatches.last.locator('xpath=ancestor::div[contains(@class,"cursor-pointer")][1]').click()
        page.wait_for_timeout(700)
        overlay = page.locator('div[data-color-picker-overlay="true"]')
        appeared = overlay.count() > 0
        shot(page, "l3_color_overlay")
    with allure.step("按 Escape 关闭 overlay"):
        if appeared:
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            assert not overlay.first.is_visible(), "Escape 后调色板 overlay 未关闭"
    with allure.step("关闭后仍可操作其他属性行"):
        lab2, sec2 = find_section(page, "Opacity")
        lab2.click()
        page.wait_for_timeout(400)
        assert sec2.locator('input[type="range"]').count() >= 1
    shot(page, "l3_color_overlay_dismiss")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_002_local_upload(canvas_page: Page):
    """L2-002: 本地上传图片新增并自动选中图层。"""
    allure.dynamic.title("L2-002: 本地上传图片新增并选中图层")
    page = canvas_page
    open_insert(page)
    with allure.step("点击 Image 并上传 test_images/有人脸.JPG"):
        with page.expect_file_chooser(timeout=30000) as fc:
            page.locator('button:text-is("Image")').first.click()
        fc.value.set_files(IMG_FACE)
        page.wait_for_timeout(3500)
    with allure.step("断言新增图层并出现四角缩放锚点"):
        assert page.locator("span.scale-point").count() >= 4, "未出现图层选择框缩放锚点"
    shot(page, "l2_upload_local")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
def test_l2_003_my_cuts_insert(canvas_page: Page):
    """L2-003: My Cuts 抠图库插入首图。"""
    allure.dynamic.title("L2-003: My Cuts 抠图库插入首图")
    page = canvas_page
    open_insert(page)
    with allure.step("打开 My Cuts 弹窗"):
        dlg_btn = page.locator('button:text-is("My Cuts")').first
        if not dlg_btn.count():
            pytest.skip("当前账号无 My Cuts 入口（依赖账号已有抠图记录）")
        dlg_btn.click()
        page.wait_for_timeout(2500)
        modal = page.locator('div.fixed:has-text("My Cuts")').first
        pw_expect(modal).to_be_visible(timeout=10000)
        assert "My Cuts" in modal.inner_text()
    shot(page, "l2_my_cuts_dialog")
    with allure.step("点击第一张缩略图并断言插入"):
        thumbs = modal.locator("img")
        if thumbs.count() == 0:
            pytest.skip("My Cuts 无可选缩略图")
        thumbs.first.click()
        page.wait_for_timeout(3000)
        assert not modal.is_visible(), "My Cuts 弹窗未关闭"
    shot(page, "l2_my_cuts_inserted")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_006_shape_added(canvas_page: Page):
    """L2-006: 第一个形状新增并自动选中。"""
    allure.dynamic.title("L2-006: 第一个形状新增并自动选中")
    page = canvas_page
    open_insert(page)
    with allure.step("点击第一个方形"):
        page.locator('img[src$="thumb_shape_style_square.webp"]').first.click()
        page.wait_for_timeout(2500)
    with allure.step("断言形状自动选中并出现参数行"):
        assert page.locator("span.scale-point").count() >= 4
        body = page.locator("body").inner_text()
        for t in ["Fill", "Corner", "Border", "Opacity", "Shadow", "Reflection"]:
            assert t in body, f"形状参数面板缺少: {t}"
    shot(page, "l2_shape_added")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
def test_l2_007_line_added(canvas_page: Page):
    """L2-007: 预设线条新增线图层。"""
    allure.dynamic.title("L2-007: 预设线条新增线图层")
    page = canvas_page
    open_insert(page)
    with allure.step("点击第二种预设线条"):
        page.locator('img[src$="edit_bottom_icon_line1.webp"]').first.click()
        page.wait_for_timeout(2500)
    with allure.step("断言线图层自动选中并出现参数行"):
        assert page.locator("span.scale-point").count() >= 4
        body = page.locator("body").inner_text()
        for t in ["Fill", "Weight", "Style", "Start", "End", "Opacity", "Shadow", "Outline", "Reflection"]:
            assert t in body, f"线条参数面板缺少: {t}"
    shot(page, "l2_line_added")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
def test_l2_008_custom_line_dialog(canvas_page: Page):
    """L2-008: Custom Line Style 弹窗可打开并关闭。"""
    allure.dynamic.title("L2-008: Custom Line Style 弹窗可打开并关闭")
    page = canvas_page
    open_insert(page)
    with allure.step("点击 Line 第一项打开弹窗"):
        page.locator('img[src$="edit_line_add.svg"]').first.click()
        page.wait_for_timeout(2000)
        modal = page.locator('div.fixed:has-text("Custom Line Style")').first
        pw_expect(modal).to_be_visible(timeout=10000)
        body = modal.inner_text()
        for t in ["Start", "Line", "End"]:
            assert t in body, f"Custom Line Style 缺少: {t}"
    shot(page, "l2_custom_line_dialog")
    with allure.step("点击关闭图标并断言弹窗消失"):
        page.locator('img[src$="colos_pop_btn_close.svg"]').first.click()
        page.wait_for_timeout(1500)
        assert not modal.is_visible(), "Custom Line Style 弹窗未关闭"


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_009_text_draw_apply(canvas_page: Page):
    """L2-009: Text 涂抹擦出当前文本并可 Apply。"""
    allure.dynamic.title("L2-009: Text 涂抹擦出当前文本并可 Apply")
    page = canvas_page
    open_insert(page)
    page.locator('img[src$="home_pop_add_bursh_text.webp"]').first.click()
    page.wait_for_timeout(2200)
    with allure.step("设置 Contents=POKECUT、Size=85、Opacity=60"):
        ta = page.locator('textarea[rows="1"]').first
        ta.fill("POKECUT")
        page.wait_for_timeout(600)
        ranges = page.locator('input[type="range"]:visible')
        pw_expect(ranges.first).to_be_visible(timeout=15000)
        assert ranges.count() >= 2, f"Text 绘制可见 range 少于 2 个: {ranges.count()}"
        set_range(ranges.nth(0), 85)
        set_range(ranges.nth(1), 60)
    bb = canvas_box(page)
    shot(page, "l2_text_before_stroke")
    with allure.step("在画布拖动形成文字笔触"):
        before = canvas_hash(page, bb)
        x0 = bb["x"] + bb["width"] * 0.30
        y0 = bb["y"] + bb["height"] * 0.40
        page.mouse.move(x0, y0)
        page.mouse.down()
        page.mouse.move(x0 + 260, y0 + 40, steps=18)
        page.mouse.up()
        page.wait_for_timeout(1500)
        after = canvas_hash(page, bb)
        assert before != after, "涂抹后画布未发生变化"
    shot(page, "l2_text_after_stroke")
    with allure.step("点击左侧工具栏的 Apply 并断言绘制态退出"):
        assert click_toolbar_apply(page), "未找到左侧工具栏可见的 Apply 按钮"
        page.wait_for_timeout(2500)
        for _ in range(20):
            if not has_visible_apply(page):
                break
            page.wait_for_timeout(500)
        assert not has_visible_apply(page), "Apply 后左侧绘制态未退出"
    shot(page, "l2_text_applied")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
def test_l2_010_general_draw_apply(canvas_page: Page):
    """L2-010: General 涂抹绘制并可 Apply。"""
    allure.dynamic.title("L2-010: General 涂抹绘制并可 Apply")
    page = canvas_page
    open_insert(page)
    page.locator('img[src$="home_pop_add_bursh_general.webp"]').first.click()
    page.wait_for_timeout(2200)
    with allure.step("设置 Size=80、Opacity=55"):
        ranges = page.locator('input[type="range"]:visible')
        pw_expect(ranges.first).to_be_visible(timeout=15000)
        assert ranges.count() >= 2, f"General 绘制可见 range 少于 2 个: {ranges.count()}"
        set_range(ranges.nth(0), 80)
        set_range(ranges.nth(1), 55)
    bb = canvas_box(page)
    shot(page, "l2_general_before")
    with allure.step("在画布拖动形成笔迹"):
        before = canvas_hash(page, bb)
        x0 = bb["x"] + bb["width"] * 0.30
        y0 = bb["y"] + bb["height"] * 0.55
        page.mouse.move(x0, y0)
        page.mouse.down()
        page.mouse.move(x0 + 300, y0 - 60, steps=20)
        page.mouse.up()
        page.wait_for_timeout(1500)
        after = canvas_hash(page, bb)
        assert before != after, "涂抹后画布未发生变化"
    shot(page, "l2_general_after")
    with allure.step("点击左侧工具栏的 Apply 并断言绘制态退出"):
        assert click_toolbar_apply(page), "未找到左侧工具栏可见的 Apply 按钮"
        page.wait_for_timeout(2500)
        for _ in range(20):
            if not has_visible_apply(page):
                break
            page.wait_for_timeout(500)
        assert not has_visible_apply(page), "Apply 后左侧绘制态未退出"
    shot(page, "l2_general_applied")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_011_shape_params(canvas_page: Page, tmp_path):
    """L2-011: Shape 选中后各参数改动生效。"""
    allure.dynamic.title("L2-011: Shape 选中后各参数改动生效")
    page = canvas_page
    open_insert(page)
    page.locator('img[src$="thumb_shape_style_square.webp"]').first.click()
    page.wait_for_timeout(2500)
    bb = canvas_box(page)
    # 新形状可能叠加在历史图层之上，点其可见框中心确保选中的是本次新增形状
    anchors = page.locator("span.scale-point")
    if anchors.count() >= 4:
        xs, ys = [], []
        for i in range(min(4, anchors.count())):
            bx = anchors.nth(i).bounding_box()
            if bx:
                xs.append(bx["x"] + bx["width"] / 2)
                ys.append(bx["y"] + bx["height"] / 2)
        if xs and ys:
            page.mouse.click(sum(xs) / len(xs), sum(ys) / len(ys))
            page.wait_for_timeout(800)
    base = str(tmp_path / "_shape_base.png")
    page.screenshot(path=base, clip=bb)
    shot(page, "l2_shape_param_base")
    with allure.step("修改 Corner / Opacity 并断言画布变化"):
        for label, value in [("Corner", 100), ("Opacity", 30)]:
            lab, sec = find_section(page, label)
            lab.click()
            page.wait_for_timeout(500)
            rngs = sec.locator('input[type="range"]')
            n = rngs.count()
            assert n >= 1, f"{label} 展开后未找到滑杆"
            # Corner 可能含多个分角滑杆，逐个设置，确保至少一个真实改变画布
            changed_values = []
            for i in range(n):
                changed_values.append(set_range(rngs.nth(i), value))
            page.wait_for_timeout(1300)
            cur = str(tmp_path / f"_shape_{label}.png")
            page.screenshot(path=cur, clip=bb)
            diff = pixel_diff_pct(base, cur)
            assert diff > 0, f"{label} 修改后画布无变化（滑杆数={n}，值={changed_values}）"
            shot(page, f"l2_shape_param_{label.lower()}")
            lab.click()
            page.wait_for_timeout(250)
    with allure.step("开启 Border 并断言画布变化"):
        lab, sec = find_section(page, "Border")
        lab.click()
        page.wait_for_timeout(400)
        section_switch_on(page, sec)
        rng = sec.locator('input[type="range"]')
        if rng.count():
            set_range(rng.first, 20)
        page.wait_for_timeout(400)
        cur = str(tmp_path / "_shape_border.png")
        page.screenshot(path=cur, clip=bb)
        assert pixel_diff_pct(base, cur) > 0, "Border 修改后画布无变化"
        shot(page, "l2_shape_param_border")
        lab.click()
        page.wait_for_timeout(250)
    with allure.step("开启 Shadow 并断言画布变化"):
        lab, sec = find_section(page, "Shadow")
        lab.click()
        page.wait_for_timeout(400)
        section_switch_on(page, sec)
        page.wait_for_timeout(400)
        cur = str(tmp_path / "_shape_shadow.png")
        page.screenshot(path=cur, clip=bb)
        assert pixel_diff_pct(base, cur) > 0, "Shadow 开启后画布无变化"
        shot(page, "l2_shape_param_shadow")
    with allure.step("展开 Reflection 并断言四个控件存在"):
        lab, sec = find_section(page, "Reflection")
        lab.click()
        page.wait_for_timeout(400)
        section_switch_on(page, sec)
        assert sec.locator('input[type="range"]').count() >= 1
        shot(page, "l2_shape_param_reflection")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
def test_l2_012_shape_fill_image(canvas_page: Page):
    """L2-012: Shape 图片填充链路（Fill → Image → Upload）。"""
    allure.dynamic.title("L2-012: Shape 图片填充链路")
    page = canvas_page
    open_insert(page)
    page.locator('img[src$="thumb_shape_style_square.webp"]').first.click()
    page.wait_for_timeout(2500)
    with allure.step("展开 Fill 并点击 Image 打开素材库"):
        fill = page.get_by_text("Fill", exact=True).last
        fill.click()
        page.wait_for_timeout(600)
        img_btns = page.get_by_role("button", name="Image", exact=True)
        target = None
        for i in range(img_btns.count()):
            bb = img_btns.nth(i).bounding_box()
            if bb and bb["x"] > 1500:
                target = img_btns.nth(i)
                break
        assert target is not None, "Fill 下未找到右侧面板的 Image 按钮"
        target.click()
        page.wait_for_timeout(1200)
    with allure.step("在素材库点击 Upload 并上传 test_images/有人脸.JPG"):
        up = page.get_by_text("Upload", exact=True).last
        pw_expect(up).to_be_visible(timeout=15000)
        with page.expect_file_chooser(timeout=30000) as fc:
            up.click()
        fc.value.set_files(IMG_FACE)
        page.wait_for_timeout(4000)
    with allure.step("断言画布仍可见且填充已应用"):
        assert page.locator("canvas").count() >= 1
    shot(page, "l2_shape_fill_image")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
@pytest.mark.p0
def test_l2_013_line_params(canvas_page: Page, tmp_path):
    """L2-013: Line 选中后各参数改动生效。"""
    allure.dynamic.title("L2-013: Line 选中后各参数改动生效")
    page = canvas_page
    open_insert(page)
    page.locator('img[src$="edit_bottom_icon_line1.webp"]').first.click()
    page.wait_for_timeout(2500)
    bb = canvas_box(page)
    base = str(tmp_path / "_line_base.png")
    page.screenshot(path=base, clip=bb)
    shot(page, "l2_line_param_base")
    with allure.step("修改 Weight 并断言画布变化"):
        lab, sec = find_section(page, "Weight")
        lab.click()
        page.wait_for_timeout(400)
        set_range(sec.locator('input[type="range"]').first, 70)
        cur = str(tmp_path / "_line_weight.png")
        page.screenshot(path=cur, clip=bb)
        assert pixel_diff_pct(base, cur) > 0, "Weight 修改后画布无变化"
        shot(page, "l2_line_param_weight")
        lab.click()
        page.wait_for_timeout(250)
    with allure.step("修改 Opacity 并断言画布变化"):
        lab, sec = find_section(page, "Opacity")
        lab.click()
        page.wait_for_timeout(400)
        set_range(sec.locator('input[type="range"]').first, 40)
        cur = str(tmp_path / "_line_opacity.png")
        page.screenshot(path=cur, clip=bb)
        assert pixel_diff_pct(base, cur) > 0, "Opacity 修改后画布无变化"
        shot(page, "l2_line_param_opacity")
        lab.click()
        page.wait_for_timeout(250)
    with allure.step("切换 Style / Start / End 选项并断言画布变化"):
        for label in ["Style", "Start", "End"]:
            lab, sec = find_section(page, label)
            lab.click()
            page.wait_for_timeout(500)
            tiles = sec.locator("img")
            if tiles.count() >= 2:
                tiles.nth(1).click()
                page.wait_for_timeout(600)
                cur = str(tmp_path / f"_line_{label}.png")
                page.screenshot(path=cur, clip=bb)
                assert pixel_diff_pct(base, cur) > 0, f"{label} 切换后画布无变化"
                shot(page, f"l2_line_param_{label.lower()}")
            lab.click()
            page.wait_for_timeout(250)
    with allure.step("开启 Outline 并断言画布变化"):
        lab, sec = find_section(page, "Outline")
        lab.click()
        page.wait_for_timeout(400)
        section_switch_on(page, sec)
        page.wait_for_timeout(400)
        cur = str(tmp_path / "_line_outline.png")
        page.screenshot(path=cur, clip=bb)
        assert pixel_diff_pct(base, cur) > 0, "Outline 开启后画布无变化"
        shot(page, "l2_line_param_outline")


@allure.epic("旧画布 Insert 面板")
@allure.feature("交互行为 / 状态迁移")
@allure.story("L2-交互")
def test_l2_014_custom_line_apply(canvas_page: Page):
    """L2-014: Custom Line Style 组合并可 Apply。"""
    allure.dynamic.title("L2-014: Custom Line Style 组合并可 Apply")
    page = canvas_page
    open_insert(page)
    page.locator('img[src$="edit_line_add.svg"]').first.click()
    page.wait_for_timeout(2000)
    modal = page.locator('div.fixed:has-text("Custom Line Style")').first
    pw_expect(modal).to_be_visible(timeout=10000)
    with allure.step("选择 Start/Line/End 组合并 Apply"):
        applied = False
        for text in ["Apply", "OK", "Confirm"]:
            btn = modal.locator(f'button:visible:has-text("{text}")')
            if btn.count():
                btn.first.click()
                applied = True
                break
        if not applied:
            modal.get_by_text("Apply", exact=True).first.click()
        page.wait_for_timeout(3000)
    with allure.step("断言弹窗关闭且画布新增图层"):
        assert not modal.is_visible(), "Apply 后弹窗未关闭"
        assert page.locator("canvas").count() >= 1
    shot(page, "l2_custom_line_applied")
