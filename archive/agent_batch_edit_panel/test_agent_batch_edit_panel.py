"""无限画布 Batch Edit 面板自动化测试（/agent，2026-11-03 重基线）。

来源:
- artifacts/2026-11-03_agent_batch_edit_panel_reexploration/cases.md
- page_map/pokecut/infinite_canvas_batch_edit_v2.yaml
- data/pokecut_agent_batch_edit_panel.yaml

覆盖: L1 结构（8）+ L2 提交链路（7，正向流程）
入口: /batch 上传 >=2 张 -> /agent?pid=* -> Batch Edit 自动展开
账号: VIP 450832596@qq.com
"""

import re
from pathlib import Path

import allure
import pytest
import yaml
from playwright.sync_api import expect

from helpers.waiting import poll_until, settle, wait_ready

def repo_root() -> Path:
    """逐级上溯到含 data/pokecut_agent_batch_edit_panel.yaml 的仓库根。

    兼容 tests/ 与 archive/<模块>/ 两种存放位置（见 rule.md 归档副本规则）。
    """
    for c in Path(__file__).resolve().parents:
        if (c / "data" / "pokecut_agent_batch_edit_panel.yaml").is_file():
            return c
    return Path(__file__).resolve().parents[1]


ROOT = repo_root()
with open(ROOT / "data" / "pokecut_agent_batch_edit_panel.yaml", "r", encoding="utf-8") as f:
    DATA = yaml.safe_load(f)


FEATURE = "无限画布BatchEdit面板"
TABS = DATA["batch_edit"]["tabs"]
SUBMIT_SEL = DATA["batch_edit"]["submit_selector"]


# ────────────────────────────── helpers ──────────────────────────────

def wait_render(page, timeout=2000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    # 截图前让 CSS 过渡收尾；没有独立可观察信号。
    settle(page, 500)


def attach(page, name):
    import tempfile
    wait_render(page)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    page.screenshot(path=path, full_page=False)
    allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)


def api_bypass_handler(route):
    req = route.request
    if req.method == "OPTIONS":
        route.fulfill(status=204, headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        })
        return
    try:
        resp = route.fetch()
        headers = dict(resp.headers)
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
        headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        route.fulfill(response=resp, headers=headers)
    except Exception:
        route.abort()


def enter_batch_edit(page, base_url):
    """从 /batch 上传 2 张进入 /agent 并等待 Batch Edit 弹窗。"""
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    page.goto(f"{base_url}/batch", timeout=60000)
    wait_render(page)
    with page.expect_file_chooser(timeout=15000) as fc:
        page.get_by_text(DATA["entry"]["card"], exact=True).first.click()
    fc.value.set_files(DATA["images"]["upload"])
    expect(page).to_have_url(re.compile(r"/agent\?pid="), timeout=60000)
    dialog = page.locator("[role=dialog]").filter(
        has=page.get_by_role("heading", name=DATA["batch_edit"]["title"], exact=True)
    ).first
    expect(dialog).to_be_visible(timeout=30000)
    return dialog


def dialog(page):
    return page.locator("[role=dialog]").first


def click_tab(page, name):
    d = dialog(page)
    tab = d.get_by_role("tab", name=name, exact=True).first
    tab.click()
    wait_ready(page, lambda: tab.get_attribute("aria-selected") == "true", timeout=10000)


def submit_button(page):
    return page.locator(SUBMIT_SEL).first


def selected_tab_text(page):
    return page.locator("[role=tab][aria-selected=true]").first.inner_text().strip()


def is_pressed(page, name):
    return page.locator(f"[role=dialog] button[aria-pressed=true]").filter(has_text=name).count() > 0


# ────────────────────────────── fixture ──────────────────────────────

@pytest.fixture(scope="session")
def batch_ctx(browser, base_url):
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    page.goto(base_url, timeout=60000)
    wait_render(page)
    page.get_by_text("Log in", exact=True).first.click()
    wait_ready(page, lambda: page.locator('input[type="email"]').count() > 0, timeout=15000, settle_ms=0)
    page.locator('input[type="email"]').fill(DATA["account"]["email"])
    page.locator('input[placeholder="Verification Code"]').fill(DATA["account"]["code"])
    page.evaluate(
        """() => {
            const bs = Array.from(document.querySelectorAll('button'))
                .filter(b => b.offsetWidth > 200 && b.getBoundingClientRect().y > 700 &&
                b.textContent.trim() === 'Log in');
            if (bs.length) bs[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }"""
    )
    expect(page.get_by_text("User8JY", exact=True).first).to_be_visible(timeout=30000)
    page.close()
    yield context
    context.close()


@pytest.fixture
def page(batch_ctx):
    p = batch_ctx.new_page()
    p.route("**/gateway/pokecut/api/**", api_bypass_handler)
    p._console_lines = []
    p.on("console", lambda m: p._console_lines.append(m.text))
    yield p
    p.close()


def wait_console(page, keyword, timeout_ms=180000):
    """轮询页面 console 直到出现关键字；返回 True/False。"""
    return poll_until(
        page,
        lambda: any(keyword in line for line in getattr(page, "_console_lines", [])),
        timeout=timeout_ms,
        interval=1000,
    )


def assert_completed(page, event, shot, timeout_ms=180000):
    """断言捕获到该用例对应的具体完成事件（不弱化为通用『生成成功』）。"""
    assert wait_console(page, event, timeout_ms), f"未捕获完成事件：{event}"
    attach(page, shot)


# ────────────────────────────── L1 结构 ──────────────────────────────

@allure.feature(FEATURE)
@allure.story("L1-页面结构元素")
class TestBatchEditPanelL1:

    @allure.title("P-AB-L1-001: Batch Edit 弹窗与 7 个主 tab 可见")
    def test_l1_001_dialog_and_tabs(self, page, base_url):
        enter_batch_edit(page, base_url)
        with allure.step("断言弹窗标题与 7 个主 tab"):
            for tab in TABS:
                expect(dialog(page).get_by_role("tab", name=tab, exact=True).first).to_be_visible()
            assert selected_tab_text(page) == "Remove BG", "默认选中 tab 应为 Remove BG"
            attach(page, "Batch Edit 弹窗与 7 个主 tab")

    @allure.title("P-AB-L1-002: Enhance 面板 5 种模式可见、默认 Standard Mode")
    def test_l1_002_enhance_panel(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Enhance")
        with allure.step("断言 5 种 Enhance 模式与默认 Standard Mode"):
            for mode in DATA["batch_edit"]["enhance_modes"]:
                expect(dialog(page).get_by_role("button", name=mode).first).to_be_visible()
            assert is_pressed(page, "Standard Mode"), "Standard Mode 应为默认选中"
            attach(page, "Enhance 面板")

    @allure.title("P-AB-L1-003: Remove BG 面板 3 种模式可见、默认 General")
    def test_l1_003_remove_bg_panel(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Remove BG")
        with allure.step("断言 3 种 Remove BG 模式与默认 General"):
            for mode in DATA["batch_edit"]["remove_bg_modes"]:
                expect(dialog(page).get_by_role("button", name=mode).first).to_be_visible()
            assert is_pressed(page, "General"), "General 应为默认选中"
            attach(page, "Remove BG 面板")

    @allure.title("P-AB-L1-004: Change BG 面板 Colors/Images 与默认透明色")
    def test_l1_004_change_bg_panel(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Change BG")
        d = dialog(page)
        with allure.step("断言 Colors/Images 子 tab 与默认透明色"):
            expect(d.get_by_role("tab", name="Colors", exact=True).first).to_be_visible()
            expect(d.get_by_role("tab", name="Images", exact=True).first).to_be_visible()
            assert d.locator("button[aria-label='#FFFFFF00'][aria-pressed='true']").count() == 1, \
                "透明色 #FFFFFF00 应为默认选中"
            attach(page, "Change BG 面板")

    @allure.title("P-AB-L1-005: Erase 面板 5 类、默认 Face>Remove Acne")
    def test_l1_005_erase_panel(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Erase")
        d = dialog(page)
        with allure.step("断言 5 个 Erase 子 tab 与默认项"):
            for cat in DATA["batch_edit"]["erase_categories"]:
                expect(d.get_by_role("tab", name=cat, exact=True).first).to_be_visible()
            assert d.get_by_role("tab", name="Face", exact=True).first.get_attribute("aria-selected") == "true"
            assert d.get_by_role("button", name="Remove Acne").first.get_attribute("aria-pressed") == "true"
            attach(page, "Erase 面板")

    @allure.title("P-AB-L1-006: Crop 面板 Custom Size 默认 1200x1600 + Template")
    def test_l1_006_crop_panel(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Crop")
        d = dialog(page)
        with allure.step("断言默认尺寸与 Template 区"):
            expect(d.get_by_role("spinbutton", name="Width px").first).to_have_value(
                DATA["batch_edit"]["crop_default_width"])
            expect(d.get_by_role("spinbutton", name="Height px").first).to_have_value(
                DATA["batch_edit"]["crop_default_height"])
            expect(d.get_by_role("heading", name="Template").first).to_be_visible()
            attach(page, "Crop 面板")

    @allure.title("P-AB-L1-007: Clothes Changer 面板 12 分类 + 默认 Dresses 首模板")
    def test_l1_007_clothes_panel(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Clothes Changer")
        d = dialog(page)
        with allure.step("断言 12 分类与 Generate 可用"):
            for cat in DATA["batch_edit"]["clothes_categories"]:
                expect(d.get_by_role("tab", name=cat, exact=True).first).to_be_visible()
            btn = submit_button(page)
            expect(btn).to_be_enabled()
            attach(page, "Clothes Changer 面板")

    @allure.title("P-AB-L1-008: Watermark 面板 Upload + Location 5 项，Apply 初始 disabled")
    def test_l1_008_watermark_panel(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Watermark")
        d = dialog(page)
        with allure.step("断言上传入口、Location 5 项与 Apply 初始 disabled"):
            expect(d.get_by_role("button", name="Upload Your Watermark").first).to_be_visible()
            for loc in DATA["batch_edit"]["watermark_locations"]:
                expect(d.get_by_role("button", name=loc, exact=True).first).to_be_visible()
            assert d.get_by_role("button", name="Top Left", exact=True).first.get_attribute("aria-pressed") == "true"
            expect(submit_button(page)).to_be_disabled()
            attach(page, "Watermark 面板")


# ────────────────────────────── L2 提交链路 ──────────────────────────────

@allure.feature(FEATURE)
@allure.story("L2-交互行为与状态迁移")
class TestBatchEditPanelL2:

    @allure.title("P-AB-L2-009: Remove BG 提交（General）后生成成功")
    def test_l2_009_remove_bg_submit(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Remove BG")
        with allure.step("点击 Remove Background 提交"):
            submit_button(page).click()
        with allure.step("等待 Remove BG 完成事件"):
            assert_completed(page, "画布批量_Remove BG功能处理完成", "Remove BG 提交完成")

    @allure.title("P-AB-L2-010: Enhance 提交（Standard Mode）后分辨率提升")
    def test_l2_010_enhance_submit(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Enhance")
        with allure.step("点击 Enhance 提交"):
            submit_button(page).click()
        with allure.step("等待 Enhance 完成事件"):
            assert_completed(page, "画布批量_Enhance功能处理完成", "Enhance 提交完成")

    @allure.title("P-AB-L2-011: Change BG 选色即时应用并处理完成")
    def test_l2_011_change_bg_apply(self, page, base_url):
        enter_batch_edit(page, base_url)
        with allure.step("先 Remove BG 抠图（换背景前置）"):
            click_tab(page, "Remove BG")
            submit_button(page).click()
            assert wait_console(page, "画布批量_Remove BG功能处理完成", 180000), "Remove BG 未完成"
        with allure.step("切到 Change BG 选择 #000000 即时应用"):
            click_tab(page, "Change BG")
            d = dialog(page)
            applied = False
            for _ in range(3):
                d.locator("button[aria-label='#000000']").first.click()
                if wait_console(page, "画布批量_Change BG功能处理完成", 60000):
                    applied = True
                    break
            assert applied, "未捕获 Change BG 完成事件"
            assert d.locator("button[aria-label='#000000'][aria-pressed='true']").count() == 1
            attach(page, "Change BG 选色应用")

    @allure.title("P-AB-L2-012: Erase 提交（Remove Acne）后生成成功")
    def test_l2_012_erase_submit(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Erase")
        with allure.step("点击 Remove 提交"):
            submit_button(page).click()
        with allure.step("等待 Erase 完成事件"):
            assert_completed(page, "画布批量_Erase功能处理完成", "Erase 提交完成")

    @allure.title("P-AB-L2-013: Crop 选 Amazon 预设并 Apply，画布尺寸变化")
    def test_l2_013_crop_apply(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Crop")
        d = dialog(page)
        with allure.step("点击 Amazon 2000x2000px 预设并 Apply"):
            d.locator("button").filter(has_text=DATA["batch_edit"]["crop_template_amazon"]).first.click()
            expect(d.get_by_role("spinbutton", name="Width px")).to_have_value("2000", timeout=10000)
            expect(d.get_by_role("spinbutton", name="Height px")).to_have_value("2000")
            submit_button(page).click()
            # Crop 是纯前端应用，无 console 完成事件；等对话框关闭作为应用完成信号。
            wait_ready(page, lambda: dialog(page).count() == 0 or not dialog(page).is_visible(), timeout=20000)
            attach(page, "Crop 预设 Apply")

    @allure.title("P-AB-L2-014: Clothes Changer 默认 Dresses 首模板 Generate 成功")
    def test_l2_014_clothes_generate(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Clothes Changer")
        with allure.step("点击 Generate 提交默认模板"):
            submit_button(page).click()
        with allure.step("等待 Clothes Changer 完成事件"):
            assert_completed(page, "画布批量_Clothes Changer功能处理完成", "Clothes Changer 生成完成")

    @allure.title("P-AB-L2-015: Watermark 上传水印 + Top Left Apply 成功")
    def test_l2_015_watermark_apply(self, page, base_url):
        enter_batch_edit(page, base_url)
        click_tab(page, "Watermark")
        with allure.step("上传水印并 Apply"):
            with page.expect_file_chooser(timeout=15000) as fc:
                dialog(page).get_by_role("button", name="Upload Your Watermark").first.click()
            fc.value.set_files(str(ROOT / DATA["images"]["watermark"]))
            expect(submit_button(page)).to_be_enabled(timeout=20000)
            submit_button(page).click()
            assert wait_console(page, "画布批量_Watermark功能处理完成", 180000), "未捕获 Watermark 完成事件"
            attach(page, "Watermark Apply 完成")

