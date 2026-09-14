"""Pokecut PC 批量编辑页自动化测试。

PRD引用：用户提供的批量编辑页交互说明 + confirmed sync.md
覆盖层级：L1 / L2 / L3 / L5 / L6
前置条件：VIP 账号已登录（session_page）；匿名用例使用 page
"""

import io
import re
from pathlib import Path

import allure
import pytest
import yaml
from PIL import Image, ImageChops
from playwright.sync_api import expect

ROOT = Path(__file__).resolve().parents[1]
with open(ROOT / "data" / "pokecut_pc_batch_v1.yaml", "r", encoding="utf-8") as f:
    DATA = yaml.safe_load(f)

FEATURE = "PC批量编辑页"


# ────────────────────────────── 公共 helper ──────────────────────────────

def wait_render(page, timeout=2000):
    """等待页面渲染完成后再截图或断言。"""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    page.wait_for_timeout(500)


def attach(page, name):
    """等待渲染完成并附加当前视口截图（使用文件附件，确保 Allure 报告可展开）。"""
    import tempfile
    wait_render(page)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    page.screenshot(path=path, full_page=False)
    allure.attach.file(
        path,
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


def attach_png_bytes(data, name):
    """将 PNG bytes 写入临时文件并作为 Allure 文件附件，确保报告可展开。"""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(data)
        path = f.name
    allure.attach.file(
        path,
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )

def api_bypass_handler(route):
    """拦截 pokecut gateway API，绕过内网 origin 的 CORS 限制。"""
    req = route.request
    if req.method == "OPTIONS":
        route.fulfill(
            status=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )
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


def goto_batch(page, base_url):
    with allure.step("导航到批量编辑页 /batch"):
        # 内网镜像的页面 origin 会被 gateway CORS 拦截；在页面级拦截 API 并补 CORS 响应头
        page.route("**/gateway/pokecut/api/**", api_bypass_handler)
        page.goto(f"{base_url}/batch", timeout=60000)
        wait_render(page)


def upload_from_landing(page, files):
    """通过落地页主按钮上传图片并进入编辑页。"""
    with allure.step("点击 Upload Images 并选择测试图片"):
        with page.expect_file_chooser(timeout=15000) as fc:
            page.get_by_role("button", name="Upload Images").click()
        fc.value.set_files(files)
    with allure.step("等待进入批量编辑页"):
        expect(page).to_have_url(re.compile(r"/batch-edit/edit\?pid="), timeout=45000)
        attach(page, "等待进入批量编辑页_1")
        wait_render(page)


def upload_from_card(page, card_text, file_path):
    """通过功能卡片上传图片并进入编辑页。"""
    with allure.step(f"点击 {card_text} 卡片并选择测试图片"):
        with page.expect_file_chooser(timeout=15000) as fc:
            page.get_by_text(card_text, exact=True).first.click()
        fc.value.set_files(file_path)
    with allure.step("等待进入批量编辑页"):
        expect(page).to_have_url(re.compile(r"/batch-edit/edit\?pid="), timeout=45000)
        wait_render(page)


def is_text_selected(page, text):
    """判断主 tab / 子 tab / 模式文本是否处于选中态（含父级 class）。"""
    return page.evaluate(
        """text => Array.from(document.querySelectorAll('div,span')).some(e => {
            if ((e.textContent || '').trim() !== text) return false;
            let node = e;
            while (node) {
                const cls = String(node.className || '');
                if (cls.includes('text-c-theme') || cls.includes('bg-[--bc-blue-2]')) return true;
                node = node.parentElement;
            }
            return false;
        })""",
        text,
    )


def image_tile_count(page):
    return page.evaluate("document.querySelectorAll('.grid.grid-cols-6 > div').length")


def click_largest_canvas(page):
    """优先点击图片缩略图 canvas；无缩略图时回退到最大 canvas。"""
    box = page.evaluate(
        """() => {
            const visible = Array.from(document.querySelectorAll('canvas'))
                .filter(c => c.offsetWidth > 0 && c.offsetHeight > 0);
            const thumbnail = visible.find(c => String(c.className || '').includes('pk-opacity-bg-16'));
            const target = thumbnail || visible
                .sort((a, b) => b.offsetWidth * b.offsetHeight - a.offsetWidth * a.offsetHeight)[0];
            if (!target) return null;
            const r = target.getBoundingClientRect();
            return {x: r.x, y: r.y, width: r.width, height: r.height};
        }"""
    )
    assert box, "页面中未找到可见 canvas"
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    wait_render(page)


def drag_largest_canvas(page, start_x_ratio, start_y_ratio, end_x_ratio, end_y_ratio):
    """在最大 canvas 上拖拽，用于 Refine 涂抹。"""
    box = page.evaluate(
        """() => {
            const canvases = Array.from(document.querySelectorAll('canvas'))
                .filter(c => c.offsetWidth > 0 && c.offsetHeight > 0)
                .sort((a, b) => b.offsetWidth * b.offsetHeight - a.offsetWidth * a.offsetHeight);
            if (!canvases.length) return null;
            const r = canvases[0].getBoundingClientRect();
            return {x: r.x, y: r.y, width: r.width, height: r.height};
        }"""
    )
    assert box, "Refine 弹窗中未找到可涂抹 canvas"
    sx = box["x"] + box["width"] * start_x_ratio
    sy = box["y"] + box["height"] * start_y_ratio
    ex = box["x"] + box["width"] * end_x_ratio
    ey = box["y"] + box["height"] * end_y_ratio
    page.mouse.move(sx, sy)
    page.mouse.down()
    for i in range(1, 11):
        page.mouse.move(sx + (ex - sx) * i / 10, sy + (ey - sy) * i / 10)
    page.mouse.up()
    wait_render(page)


def screenshot_bytes(page):
    wait_render(page)
    return page.screenshot(full_page=False)


def changed_pixel_count(before, after):
    """计算两张截图的显著变化像素数。"""
    im1 = Image.open(io.BytesIO(before)).convert("RGB")
    im2 = Image.open(io.BytesIO(after)).convert("RGB")
    diff = ImageChops.difference(im1, im2)
    return sum(1 for p in diff.getdata() if sum(p) > 20)


def submit_remove_background(page):
    with allure.step("提交 Remove Background 任务"):
        page.get_by_role("button", name="Remove Background").click()
    with allure.step("等待任务完成并自动切换到 Change BG"):
        expect(page.get_by_text("Change BG", exact=True).first).to_be_visible(timeout=45000)
        attach(page, "等待任务完成并自动切换到_Change_BG_3")
        for _ in range(60):
            if is_text_selected(page, "Change BG"):
                break
            page.wait_for_timeout(500)
        assert is_text_selected(page, "Change BG"), "Remove Background 完成后未自动选中 Change BG"
        wait_render(page)


def click_color_swatch_by_rgb(page, rgb):
    """按计算后的背景色点击预设色块，避免使用位置选择器。"""
    clicked = page.evaluate(
        """rgb => {
            const swatches = Array.from(document.querySelectorAll('span.color-border'))
                .filter(e => e.offsetWidth > 0 && e.offsetHeight > 0);
            const target = swatches.find(e => getComputedStyle(e).backgroundColor === rgb);
            if (!target) return false;
            target.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            return true;
        }""",
        rgb,
    )
    assert clicked, f"未找到背景色为 {rgb} 的色块"



def download_button(page):
    """定位顶栏 Download 容器；通过文本节点的父级获取，避免依赖样式 class。"""
    return page.get_by_text("Download", exact=True).last.locator("xpath=..")

# ────────────────────────────── 登录 fixture（覆盖 conftest 的 session_page） ──────────────────────────────

@pytest.fixture(scope="session")
def batch_session_context(browser, base_url):
    """创建批量编辑页专用登录上下文；登录请求经 API bypass 处理 CORS。"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )
    page = context.new_page()
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    page.goto(base_url, timeout=60000)
    wait_render(page)
    page.get_by_text("Log in", exact=True).first.click()
    page.wait_for_timeout(2000)
    page.locator('input[type="email"]').fill(DATA["account"]["email"])
    page.locator('input[placeholder="Verification Code"]').fill(DATA["account"]["code"])
    page.evaluate(
        """() => {
            const bs = Array.from(document.querySelectorAll('button'))
                .filter(b => b.offsetWidth > 200 && b.getBoundingClientRect().y > 700 && b.textContent.trim() === 'Log in');
            if (bs.length) bs[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }"""
    )
    page.wait_for_timeout(15000)
    expect(page.get_by_text("User8JY", exact=True).first).to_be_visible(timeout=15000)
    page.close()
    yield context
    context.close()


@pytest.fixture
def session_page(batch_session_context):
    """为每个用例创建已登录页面，并继续拦截 gateway API 的 CORS。"""
    page = batch_session_context.new_page()
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    yield page
    page.close()

# ────────────────────────────── L1 结构 ──────────────────────────────

@pytest.mark.regression
@allure.feature(FEATURE)
@allure.story("L1-页面结构元素")
class TestL1BatchStructure:
    """Layer 1: PC批量编辑页页面结构"""

    @pytest.mark.no_login
    @allure.title("L1-001: 落地页主上传入口与四个功能卡片可见")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l1_001_landing_structure(self, page, base_url):
        """PRD引用：AC-001/002；覆盖层级：L1；前置条件：匿名访问。

        测试步骤：
        1. 匿名访问 /batch
        2. 检查主按钮与四个卡片

        预期结果：Upload Images 与四个功能卡片均可见。
        """
        goto_batch(page, base_url)
        with allure.step("检查落地页主按钮与四个功能卡片"):
            expect(page.get_by_role("button", name="Upload Images")).to_be_visible()
            attach(page, "检查落地页主按钮与四个功能卡片_5")
            for card in DATA["landing"]["cards"].values():
                expect(page.get_by_text(card, exact=True).first).to_be_visible()

    @pytest.mark.login_required
    @allure.title("L1-007: 删除按钮文案应为 Delete（Delect 已修复）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_007_delete_label_bug(self, session_page, base_url):
        """PRD引用：AC-010；覆盖层级：L1；前置条件：VIP 登录并上传单图。

        测试步骤：
        1. 上传单图
        2. 进入删除态
        3. 检查删除按钮文案

        预期结果：按钮文案为 Delete。历史缺陷「Delect」已于 2026-09-14 复探确认修复，本用例改为回归断言文案为 Delete。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        session_page.locator("img[src*='remodver_bg_btn_icon.svg']").click()
        wait_render(session_page)
        with allure.step("断言删除按钮正确文案"):
            actual = session_page.get_by_role("button", name="Delete").last.inner_text()
            assert actual == DATA["bugs"]["delete_button_expected"]
            attach(session_page, "断言删除按钮正确文案_7")


# ────────────────────────────── L2 交互 ──────────────────────────────

@pytest.mark.full
@allure.feature(FEATURE)
@allure.story("L2-交互行为与状态迁移")
class TestL2BatchInteractions:
    """Layer 2: PC批量编辑页交互行为"""

    @pytest.mark.login_required
    @allure.title("L2-001: 主按钮上传单图进入编辑页")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_001_single_upload(self, session_page, base_url):
        """PRD引用：AC-001；覆盖层级：L2；前置条件：VIP 登录。

        测试步骤：
        1. 点击 Upload Images
        2. 选择 1K.jpg
        3. 检查 URL 与默认 tab

        预期结果：进入编辑页，默认 Background > Remove BG > General。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        with allure.step("断言单图上传后的默认状态"):
            assert "/batch-edit/edit?pid=" in session_page.url
            attach(session_page, "断言单图上传后的默认状态_8")
            assert image_tile_count(session_page) == 2
            assert is_text_selected(session_page, "Background")
            assert is_text_selected(session_page, "Remove BG")
            assert is_text_selected(session_page, "General")

    @pytest.mark.login_required
    @allure.title("L2-002: 主按钮多图上传与 + 号继续上传")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_002_multi_plus_upload(self, session_page, base_url):
        """PRD引用：AC-001/009；覆盖层级：L2；前置条件：VIP 登录。

        测试步骤：
        1. 上传两张图片
        2. 点击 + 号
        3. 上传第三张图片

        预期结果：图片数量从 2 增加到 3，+ 号仍可见。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["multi"])
        assert image_tile_count(session_page) == 3
        with allure.step("点击 + 号继续上传第三张图片"):
            with session_page.expect_file_chooser(timeout=15000) as fc:
                session_page.locator("div.bg-c-light-purple").click()
            fc.value.set_files(DATA["images"]["third"])
            wait_render(session_page)
        with allure.step("断言图片数量与 + 号可见"):
            assert image_tile_count(session_page) == 4
            attach(session_page, "断言图片数量与_号可见_13")
            expect(session_page.locator("div.bg-c-light-purple")).to_be_visible()

    @pytest.mark.login_required
    @allure.title("L2-003: 四个功能卡片默认 tab 映射")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_003_entry_cards_default_tabs(self, session_page, base_url):
        """PRD引用：AC-002；覆盖层级：L2；前置条件：VIP 登录。

        测试步骤：
        1. 依次点击四个功能卡片
        2. 每次上传 1K.jpg
        3. 记录默认选中 tab

        预期结果：Remove BG 卡片进入 Remove BG；Resizer 进入 Resize；Change BG 实际进入 Remove BG；Enhancer 进入 Enhance。
        """
        expected = {
            "remove_bg": ["Background", "Remove BG", "General"],
            "resizer": ["Resize"],
            "change_bg": ["Background", "Remove BG", "General"],
            "enhancer": ["Enhance", "Standard Mode"],
        }
        seen_states = set()
        for key, card in DATA["landing"]["cards"].items():
            with allure.step(f"验证 {card} 卡片默认 tab"):
                goto_batch(session_page, base_url)
                upload_from_card(session_page, card, DATA["images"]["single"])
                for text in expected[key]:
                    assert is_text_selected(session_page, text), f"{card} 后未选中 {text}"
                state = tuple(expected[key])
                if state not in seen_states:
                    attach(session_page, f"验证 {card} 卡片默认 tab")
                    seen_states.add(state)

    @pytest.mark.login_required
    @allure.title("L2-004: Remove BG 三种模式切换与提交后自动切 Change BG")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_004_removebg_modes_submit(self, session_page, base_url):
        """PRD引用：AC-004；覆盖层级：L2；前置条件：VIP 登录并上传单图。

        测试步骤：
        1. 依次切换 Head&Face、Text、General
        2. 提交 Remove Background

        预期结果：三种模式均可切换；提交后自动选中 Change BG。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        with allure.step("依次切换 Remove BG 三种模式"):
            for mode in ["Head&Face", "Text", "General"]:
                session_page.get_by_text(mode, exact=True).first.click()
                wait_render(session_page)
                assert is_text_selected(session_page, mode), f"{mode} 未选中"
                attach(session_page, "依次切换_Remove_BG_三种模式_15")
        submit_remove_background(session_page)
        assert is_text_selected(session_page, "Change BG")

    @pytest.mark.login_required
    @allure.title("L2-005: 预览与 Refine 的擦除 / 恢复 / 应用 / 取消")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_005_refine_flow(self, session_page, base_url):
        """PRD引用：AC-004；覆盖层级：L2；前置条件：完成抠图。

        测试步骤：
        1. 打开预览与 Refine
        2. Eraser 涂抹
        3. Keep 涂抹
        4. Go Edit
        5. Cancel
        6. 关闭预览

        预期结果：涂抹产生像素差异；Go Edit 应用；Cancel 不应用；关闭后预览消失。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        submit_remove_background(session_page)
        click_largest_canvas(session_page)

        with allure.step("打开 Refine 并执行 Eraser 涂抹"):
            session_page.get_by_role("button", name="Refine").click()
            wait_render(session_page)
            before = screenshot_bytes(session_page)
            drag_largest_canvas(session_page, 0.25, 0.35, 0.75, 0.65)
            after = screenshot_bytes(session_page)
            assert changed_pixel_count(before, after) > 100, "Eraser 涂抹后画面无变化"
            attach(session_page, "打开_Refine_并执行_Eraser_涂抹_16")
            attach_png_bytes(before, "refine_eraser_before")
            attach_png_bytes(after, "refine_eraser_after")

        with allure.step("切换 Keep 并涂抹"):
            session_page.get_by_role("button", name="Keep").click()
            wait_render(session_page)
            before_keep = screenshot_bytes(session_page)
            drag_largest_canvas(session_page, 0.35, 0.65, 0.65, 0.35)
            after_keep = screenshot_bytes(session_page)
            assert changed_pixel_count(before_keep, after_keep) > 100, "Keep 涂抹后画面无变化"
            attach(session_page, "切换_Keep_并涂抹_17")

        with allure.step("点击 Go Edit 应用结果"):
            session_page.get_by_role("button", name=re.compile("Go Edit|Confirm")).last.click()
            session_page.wait_for_timeout(3000)
            expect(session_page.get_by_role("button", name="Refine")).to_be_visible()
            attach(session_page, "点击_Go_Edit_应用结果_18")
            assert not session_page.get_by_role("button", name="Keep").last.is_visible()
            assert not session_page.get_by_role("button", name="Eraser").last.is_visible()

        with allure.step("重新打开 Refine 并点击 Cancel"):
            session_page.get_by_role("button", name="Refine").click()
            wait_render(session_page)
            session_page.get_by_role("button", name="Cancel").last.click()
            wait_render(session_page)
            expect(session_page.get_by_role("button", name="Refine")).to_be_visible()
            attach(session_page, "重新打开_Refine_并点击_Cancel_21")
            assert not session_page.get_by_role("button", name="Keep").last.is_visible()

        with allure.step("关闭预览弹窗"):
            session_page.locator("img[src*='colos_pop_btn_close.svg']").click()
            wait_render(session_page)
            assert not session_page.get_by_role("button", name="Refine").is_visible()
            attach(session_page, "关闭预览弹窗_23")

    @pytest.mark.login_required
    @allure.title("L2-006: Change BG Colors 默认透明色、色块与 HEX 选色")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_006_changebg_colors(self, session_page, base_url):
        """PRD引用：AC-005；覆盖层级：L2；前置条件：完成抠图。

        测试步骤：
        1. 检查默认透明色
        2. 点击色块
        3. 打开色盘并输入 HEX

        预期结果：默认透明色 active；色块应用；HEX 输入后背景更新。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        submit_remove_background(session_page)
        with allure.step("断言默认透明色 active"):
            active = session_page.evaluate(
                """() => Array.from(document.querySelectorAll('span.color-border'))
                    .filter(e => String(e.className).includes('active-color-border'))
                    .map(e => ({cls: String(e.className), bg: getComputedStyle(e).backgroundColor}))"""
            )
            assert active, "未找到默认选中的透明色"
            attach(session_page, "断言默认透明色_active_24")
        before = screenshot_bytes(session_page)
        with allure.step("点击预设色块"):
            click_color_swatch_by_rgb(session_page, DATA["change_bg"]["sample_color_rgb"])
            wait_render(session_page)
            active = session_page.evaluate(
                """() => Array.from(document.querySelectorAll('span.color-border'))
                    .filter(e => String(e.className).includes('active-color-border'))
                    .map(e => getComputedStyle(e).backgroundColor)"""
            )
            assert DATA["change_bg"]["sample_color_rgb"] in active
            attach(session_page, "点击预设色块_25")
        after = screenshot_bytes(session_page)
        assert changed_pixel_count(before, after) > 100, "点击色块后背景无变化"

        with allure.step("打开色盘并输入 HEX"):
            session_page.locator("img[src*='edit_icon_color_picker.png']").click()
            wait_render(session_page)
            hex_input = session_page.locator("input.hexInput")
            expect(hex_input).to_be_visible()
            attach(session_page, "打开色盘并输入_HEX_26")
            hex_input.fill(DATA["change_bg"]["custom_hex"])
            session_page.keyboard.press("Enter")
            wait_render(session_page)
            assert hex_input.input_value() == DATA["change_bg"]["custom_hex"]

    @pytest.mark.login_required
    @allure.title("L2-007: Change BG Images 预设背景与本地上传")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_007_changebg_images(self, session_page, base_url):
        """PRD引用：AC-005；覆盖层级：L2；前置条件：完成抠图。

        测试步骤：
        1. 切换 Images
        2. 点击预设背景
        3. 上传本地背景

        预期结果：预设与本地上传均改变背景。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        submit_remove_background(session_page)
        session_page.get_by_text("Images", exact=True).first.click()
        wait_render(session_page)

        with allure.step("记录 Images 默认背景状态"):
            before = screenshot_bytes(session_page)
            attach_png_bytes(before, "Images 默认背景状态")

        with allure.step("点击预设背景"):
            session_page.locator(f"img[src*='{DATA['change_bg']['image_preset_src']}']").click()
            wait_render(session_page)
            after_preset = screenshot_bytes(session_page)
            attach_png_bytes(after_preset, "预设背景应用后")
            assert changed_pixel_count(before, after_preset) > 100, "预设背景未应用"

        with allure.step("上传本地背景"):
            with session_page.expect_file_chooser(timeout=15000) as fc:
                session_page.get_by_text("Upload", exact=True).first.click()
            fc.value.set_files(DATA["images"]["custom_background"])
            wait_render(session_page)
            after_upload = screenshot_bytes(session_page)
            attach_png_bytes(after_upload, "本地上传背景应用后")
            assert changed_pixel_count(after_preset, after_upload) > 100, "本地上传背景未应用"

    @pytest.mark.login_required
    @allure.title("L2-008: Enhance 三种模式切换与提交后分辨率对比")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_008_enhance_modes_submit(self, session_page, base_url):
        """PRD引用：AC-006；覆盖层级：L2；前置条件：VIP 登录并上传单图。

        测试步骤：
        1. 切换三种增强模式
        2. 提交 AI Enhancer
        3. 点击图片查看对比

        预期结果：模式可切换；对比弹窗显示 Before/After 分辨率。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        session_page.get_by_text("Enhance", exact=True).first.click()
        wait_render(session_page)
        with allure.step("依次切换 Enhance 三种模式"):
            for mode in ["Portrait Mode", "Text Mode", "Standard Mode"]:
                session_page.get_by_text(mode, exact=True).first.click()
                wait_render(session_page)
                assert is_text_selected(session_page, mode), f"{mode} 未选中"
                attach(session_page, "依次切换_Enhance_三种模式_28")
        with allure.step("提交 AI Enhancer 并查看分辨率对比"):
            session_page.get_by_role("button", name="AI Enhancer").click()
            session_page.wait_for_timeout(35000)
            click_largest_canvas(session_page)
            session_page.wait_for_timeout(3000)
            body = session_page.locator("body").inner_text()
            assert DATA["enhance"]["before_resolution"] in body
            attach(session_page, "提交_AI_Enhancer_并查看分辨率对比_29")
            assert DATA["enhance"]["after_resolution"] in body

    @pytest.mark.login_required
    @allure.title("L2-009: Resize 模板与自定义尺寸")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_009_resize_template_custom(self, session_page, base_url):
        """PRD引用：AC-007；覆盖层级：L2；前置条件：VIP 登录并上传单图。

        测试步骤：
        1. 点击 Amazon 模板
        2. 输入自定义 800x600

        预期结果：模板宽高为 2000/2000；自定义后画布比例变化。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        session_page.get_by_text("Resize", exact=True).first.click()
        wait_render(session_page)
        with allure.step("点击 Amazon 模板"):
            session_page.get_by_text(DATA["resize"]["template_name"], exact=True).first.click()
            wait_render(session_page)
            assert session_page.locator("#width").input_value() == DATA["resize"]["template_width"]
            attach(session_page, "点击_Amazon_模板_31")
            assert session_page.locator("#height").input_value() == DATA["resize"]["template_height"]
        with allure.step("输入自定义尺寸 800x600"):
            session_page.locator("#width").fill(DATA["resize"]["custom_width"])
            session_page.locator("#height").fill(DATA["resize"]["custom_height"])
            session_page.keyboard.press("Enter")
            wait_render(session_page)
            box = session_page.evaluate(
                """() => {
                    const c = Array.from(document.querySelectorAll('canvas'))
                        .filter(e => e.offsetWidth > 0 && e.offsetHeight > 0)[0];
                    return {w: c.offsetWidth, h: c.offsetHeight};
                }"""
            )
            assert box["w"] / box["h"] == pytest.approx(4 / 3, abs=0.05)
            attach(session_page, "输入自定义尺寸_800x600_33")

    @pytest.mark.login_required
    @allure.title("L2-010: 撤销与重做状态迁移")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_010_undo_redo(self, session_page, base_url):
        """PRD引用：AC-008；覆盖层级：L2；前置条件：VIP 登录并上传单图。

        测试步骤：
        1. 执行 Resize
        2. 点击撤销
        3. 点击重做

        预期结果：撤销回退，重做恢复，图标状态正确切换。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        assert "top_btn_undo_disabled" in session_page.locator("img[src*='top_btn_undo']").get_attribute("src")
        assert "top_btn_redo_disabled" in session_page.locator("img[src*='top_btn_redo']").get_attribute("src")

        session_page.get_by_text("Resize", exact=True).first.click()
        wait_render(session_page)
        session_page.get_by_text(DATA["resize"]["template_name"], exact=True).first.click()
        wait_render(session_page)
        assert "top_btn_undo.svg" in session_page.locator("img[src*='top_btn_undo']").get_attribute("src")
        assert "top_btn_redo_disabled" in session_page.locator("img[src*='top_btn_redo']").get_attribute("src")

        with allure.step("点击撤销"):
            box = session_page.locator("img[src*='top_btn_undo']").bounding_box()
            session_page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            wait_render(session_page)
            assert "top_btn_undo_disabled" in session_page.locator("img[src*='top_btn_undo']").get_attribute("src")
            attach(session_page, "点击撤销_34")
            assert "top_btn_redo.svg" in session_page.locator("img[src*='top_btn_redo']").get_attribute("src")

        with allure.step("点击重做"):
            box = session_page.locator("img[src*='top_btn_redo']").bounding_box()
            session_page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            wait_render(session_page)
            assert "top_btn_undo.svg" in session_page.locator("img[src*='top_btn_undo']").get_attribute("src")
            attach(session_page, "点击重做_36")
            assert "top_btn_redo_disabled" in session_page.locator("img[src*='top_btn_redo']").get_attribute("src")

    @pytest.mark.login_required
    @allure.title("L2-011: 删除模式单选、全选、取消与确认删除")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_011_delete_flow(self, session_page, base_url):
        """PRD引用：AC-010；覆盖层级：L2；前置条件：VIP 登录并上传两张图片。

        测试步骤：
        1. 进入删除态并单选
        2. Select All
        3. Cancel
        4. 重新 Select All 并确认删除

        预期结果：selected 计数正确；全部删除后回到默认上传态。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["multi"])
        session_page.locator("img[src*='remodver_bg_btn_icon.svg']").click()
        wait_render(session_page)

        with allure.step("单选一张图片"):
            session_page.locator("label.select-checkbox").first.click()
            wait_render(session_page)
            assert "selected 1" in session_page.locator("body").inner_text()
            attach(session_page, "单选一张图片_38")

        with allure.step("点击 Select All"):
            session_page.get_by_role("button", name="Select All").click()
            wait_render(session_page)
            assert "selected 2" in session_page.locator("body").inner_text()
            attach(session_page, "点击_Select_All_39")

        with allure.step("点击 Cancel 退出删除态"):
            session_page.get_by_role("button", name="Cancel").last.click()
            wait_render(session_page)
            assert not session_page.get_by_role("button", name="Select All").is_visible()
            attach(session_page, "点击_Cancel_退出删除态_40")

        with allure.step("重新进入删除态并删除全部图片"):
            session_page.locator("img[src*='remodver_bg_btn_icon.svg']").click()
            wait_render(session_page)
            session_page.get_by_role("button", name="Select All").click()
            wait_render(session_page)
            session_page.get_by_role("button", name="Delete").click()
            wait_render(session_page)
            session_page.get_by_role("button", name="Delete completely").click()
            wait_render(session_page)
            assert image_tile_count(session_page) == 0
            attach(session_page, "重新进入删除态并删除全部图片_41")
            expect(session_page.get_by_role("button", name="Upload Images")).to_be_visible()

    @pytest.mark.login_required
    @allure.title("L2-012: 无图片时 Download 禁用，有图片时可下载")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_012_download_flow(self, session_page, base_url):
        """PRD引用：AC-011；覆盖层级：L2；前置条件：VIP 登录。

        测试步骤：
        1. 删除所有图片后检查 Download
        2. 重新上传图片
        3. 选择 PNG 并下载

        预期结果：无图片时禁用；有图片时触发 zip 下载。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        session_page.locator("img[src*='remodver_bg_btn_icon.svg']").click()
        wait_render(session_page)
        session_page.get_by_role("button", name="Select All").click()
        wait_render(session_page)
        session_page.get_by_role("button", name="Delete").click()
        wait_render(session_page)
        session_page.get_by_role("button", name="Delete completely").click()
        wait_render(session_page)

        with allure.step("断言无图片时 Download 禁用"):
            cls = download_button(session_page).last.get_attribute("class")
            assert "cursor-not-allowed" in cls
            attach(session_page, "断言无图片时_Download_禁用_43")
            download_button(session_page).last.click()
            wait_render(session_page)
            assert not session_page.get_by_role("button", name="PNG").last.is_visible()

        with allure.step("重新上传图片并提交 Remove Background 后下载 PNG"):
            goto_batch(session_page, base_url)
            upload_from_landing(session_page, DATA["images"]["single"])
            submit_remove_background(session_page)
            download_button(session_page).last.click()
            wait_render(session_page)
            session_page.get_by_role("button", name="PNG").click()
            wait_render(session_page)
            with session_page.expect_download(timeout=45000) as dl:
                session_page.get_by_role("button", name="Download").last.click()
            download = dl.value
            assert download.suggested_filename.startswith(DATA["download"]["zip_prefix"])
            attach(session_page, "重新上传图片并提交_Remove_Background_后下载_PNG_45")
            assert download.suggested_filename.endswith(DATA["download"]["zip_suffix"])


# ────────────────────────────── L3 异常 / 权限 ──────────────────────────────

@pytest.mark.full
@allure.feature(FEATURE)
@allure.story("L3-异常与权限")
class TestL3BatchException:
    """Layer 3: PC批量编辑页异常与权限"""

@pytest.mark.full
@allure.feature(FEATURE)
@allure.story("L5-数据边界与等价类")
class TestL5BatchBoundaries:
    """Layer 5: PC批量编辑页数据边界"""

@pytest.mark.smoke
@allure.feature(FEATURE)
@allure.story("L6-核心HappyPath")
class TestL6BatchSmoke:
    """Layer 6: PC批量编辑页核心 Happy Path"""

    @pytest.mark.login_required
    @allure.title("L6-001: 登录 -> 上传 -> Remove BG -> Change BG 颜色 -> 下载")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l6_001_smoke_removebg_download(self, session_page, base_url):
        """PRD引用：AC-001/004/005/011；覆盖层级：L6；前置条件：VIP 登录。

        测试步骤：
        1. 上传单图
        2. 提交 Remove Background
        3. 选择色块
        4. 下载 PNG

        预期结果：抠图后进入 Change BG；背景变化；下载 zip。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        submit_remove_background(session_page)
        before = screenshot_bytes(session_page)
        click_color_swatch_by_rgb(session_page, DATA["change_bg"]["sample_color_rgb"])
        wait_render(session_page)
        after = screenshot_bytes(session_page)
        assert changed_pixel_count(before, after) > 100
        download_button(session_page).last.click()
        wait_render(session_page)
        session_page.get_by_role("button", name="PNG").click()
        wait_render(session_page)
        with session_page.expect_download(timeout=45000) as dl:
            session_page.get_by_role("button", name="Download").last.click()
        assert dl.value.suggested_filename.endswith(".zip")

    @pytest.mark.login_required
    @allure.title("L6-002: 登录 -> 上传 -> Enhance -> Resize -> 下载")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l6_002_smoke_enhance_resize_download(self, session_page, base_url):
        """PRD引用：AC-001/006/007/011；覆盖层级：L6；前置条件：VIP 登录。

        测试步骤：
        1. 上传单图
        2. 提交 AI Enhancer
        3. Resize 为 Amazon 模板
        4. 下载 JPG

        预期结果：分辨率对比可见；宽高为 2000/2000；下载 zip。
        """
        goto_batch(session_page, base_url)
        upload_from_landing(session_page, DATA["images"]["single"])
        session_page.get_by_text("Enhance", exact=True).first.click()
        wait_render(session_page)
        session_page.get_by_role("button", name="AI Enhancer").click()
        session_page.wait_for_timeout(35000)
        click_largest_canvas(session_page)
        session_page.wait_for_timeout(3000)
        body = session_page.locator("body").inner_text()
        assert DATA["enhance"]["before_resolution"] in body
        assert DATA["enhance"]["after_resolution"] in body
        session_page.locator("img[src*='colos_pop_btn_close.svg']").click()
        wait_render(session_page)
        session_page.get_by_text("Resize", exact=True).first.click()
        wait_render(session_page)
        session_page.get_by_text(DATA["resize"]["template_name"], exact=True).first.click()
        wait_render(session_page)
        assert session_page.locator("#width").input_value() == "2000"
        assert session_page.locator("#height").input_value() == "2000"
        download_button(session_page).last.click()
        wait_render(session_page)
        session_page.get_by_role("button", name="JPG").click()
        wait_render(session_page)
        with session_page.expect_download(timeout=45000) as dl:
            session_page.get_by_role("button", name="Download").last.click()
        assert dl.value.suggested_filename.endswith(".zip")









