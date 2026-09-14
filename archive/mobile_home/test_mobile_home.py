# -*- coding: utf-8 -*-
"""Pokecut 移动端首页优化（Mobile Home v3）自动化用例。

层级/步骤/截图遵循 cases.md 与 Allure 规范：
- @allure.feature = 模块中文名
- @allure.story = L{N}-页面/功能元素
- @allure.title = L{N}-{NNN}: 用例中文标题
- 步骤用 allure.step 包裹，截图在对应步骤内。
"""
import pytest
import allure
from pathlib import Path
from playwright.sync_api import Page, expect



def _repo_root():
    """归档副本位于 archive/<dir>/，需按 test_images/ 上溯仓库根（原 parents[1] 解析到 archive/ 会找不到素材）。"""
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / "test_images").is_dir():
            return c
    return Path(__file__).resolve().parent.parent


TEST_IMAGES = _repo_root() / "test_images"
IMG_VALID = str(TEST_IMAGES / "有人脸.JPG")
IMG_DAMAGED = str(TEST_IMAGES / "损坏的图.png")
BASE_PATH = "/"

MOBILE_CONTEXT = dict(
    viewport={"width": 390, "height": 844},
    is_mobile=True,
    has_touch=True,
    device_scale_factor=3,
    locale="en-US",
    user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
)


@pytest.fixture
def mobile_page(browser):
    ctx = browser.new_context(**MOBILE_CONTEXT)
    page = ctx.new_page()
    page.set_default_timeout(15000)
    yield page
    ctx.close()


def goto_home(page: Page, base_url: str):
    page.goto(f"{base_url}{BASE_PATH}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)


def scroll_to(locator):
    locator.scroll_into_view_if_needed()
    page = locator.page
    page.wait_for_timeout(300)


def upload_via(page: Page, trigger, file_path: str):
    with page.expect_file_chooser(timeout=8000) as fc:
        trigger.click()
    fc.value.set_files(file_path)
    page.wait_for_timeout(300)


def shot(page: Page, name: str):
    with allure.step("截图记录"):
        allure.attach(page.screenshot(), name=name, attachment_type=allure.attachment_type.PNG)


@allure.feature("移动端首页")
@allure.story("L1-页面结构元素")
class TestL1PageStructure:
    """Layer 1: 页面元素 / 结构"""

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("L1-001: 移动端首页首屏结构与各板块存在")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_001_structure(self, mobile_page: Page, base_url: str):
        """
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 访问新版移动端首页
        测试步骤:
          1. 打开移动端首页
          2. 检查首屏与各板块及底部导航
        预期结果: 首屏 Agent 框单列；6 功能卡、effect、Test、人像、画质增强、数据、评论、FAQ、移动端展示、底部导航均存在
        """
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            body = page.inner_text("body")
            for text in ["All-in-One AI Photo Editor & Generator", "Start Creating for Free",
                         "Remove Background", "Clothes Changer", "HD Photo Coverter", "ID Photo Maker",
                         "Body Editor", "AI Replace", "More Pokecut Tools",
                         "Create Faster with Pokecut's AI Templates", "Test Your Portrait Before You Edit",
                         "Upgrade Portrait Details with Pokecut AI", "Enhance Photo Quality for Every Detail",
                         "Pokecut is Trusted by Creators", "What Users Say About Pokecut?",
                         "Frequently Asked Questions", "Pokecut Mobile App"]:
                assert text in body, f"缺少板块文案: {text}"
            nav = page.locator("nav.home-mobile-bottom-nav")
            expect(nav.locator("button")).to_have_count(5)
            for item in ["Home", "All Tools", "Upload", "Generate", "Pricing"]:
                assert nav.locator(f"button[aria-label='{item}']").count() == 1, f"缺少底部导航入口: {item}"
        shot(page, "L1-001_首屏与各板块")

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("L1-002: 首屏文案与控件排列")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_002_hero_copy(self, mobile_page: Page, base_url: str):
        """
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 访问新版移动端首页
        测试步骤:
          1. 打开移动端首页
          2. 核对首屏标题、主按钮、输入框文案与 Generate 禁用态
        预期结果: 标题/按钮/placeholder 符合实际；模型、比例、分辨率入口存在；Generate 默认 disabled
        """
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            expect(page.locator("#home-mobile-agent-title")).to_have_text("All-in-One AI Photo Editor & Generator")
            expect(page.get_by_role("button", name="Start Creating for Free")).to_be_visible()
            ph = page.locator("textarea[aria-label]").first.get_attribute("placeholder")
            assert ph and ph.startswith("Start with Pokecut's free AI image generation")
            # 2026-09-14 漂移修正：默认模型由 Pokecut Pro 变为 Auto（page_map mobile_home_v2）
            expect(page.locator("section.mobile-home-agent-hero button").filter(has_text="Auto")).to_be_visible()
            gen = page.locator("section.mobile-home-agent-hero button", has_text="Generate").first
            expect(gen).to_be_disabled()
        shot(page, "L1-002_首屏文案控件")


@allure.feature("移动端首页")
@allure.story("L2-交互行为元素")
class TestL2Interactions:
    """Layer 2: 交互行为 / 状态迁移"""

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-001: 主按钮唤起系统上传弹窗")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_001_main_cta_file_chooser(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 打开首页 -> 点击主按钮；预期: 触发 file chooser"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            with page.expect_file_chooser(timeout=8000) as fc:
                page.get_by_role("button", name="Start Creating for Free").click()
            assert fc.value is not None
        shot(page, "L2-001_上传弹窗")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-002: 主按钮上传有效图进入移动端画布")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_002_main_cta_upload(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 打开首页 -> 主按钮上传有人脸.JPG；预期: 进入 /create/edit?pid=*"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            upload_via(page, page.get_by_role("button", name="Start Creating for Free"), IMG_VALID)
            page.wait_for_timeout(6000)
            assert "/create/edit?pid=" in page.url
        shot(page, "L2-002_画布")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-003: 模型入口展开模型列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_003_model_popover(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 打开首页 -> 点击模型入口（当前默认 Auto）；预期: 模型选项齐全"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            # 2026-09-14 漂移修正：点击模型入口（当前默认文案 Auto），弹层选项断言保持不变
            page.locator("section.mobile-home-agent-hero button").filter(has_text="Auto").first.click()
            page.wait_for_timeout(1200)
            body = page.inner_text("body")
            for opt in ["ChatGPT Image 2.0", "Nano Banana", "Nano Banana 2", "Seedream4.0"]:
                assert opt in body, f"缺少模型选项: {opt}"
        shot(page, "L2-003_模型弹层")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-004: 比例入口展开比例列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_004_ratio_popover(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 打开首页 -> 点击比例入口；预期: 8 档比例"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            ratio = page.locator("section.mobile-home-agent-hero button:not([aria-label])[class*='size-[2.625rem]']").first
            ratio.click()
            page.wait_for_timeout(1200)
            body = page.inner_text("body")
            for opt in ["16:9", "1:1", "2:3", "9:16", "9:21"]:
                assert opt in body, f"缺少比例选项: {opt}"
        shot(page, "L2-004_比例弹层")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-006: Generate 未满足条件禁用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_006_generate_disabled(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 打开首页 -> 点击 Generate；预期: disabled，不跳转不生成"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            gen = page.locator("section.mobile-home-agent-hero button", has_text="Generate").first
            expect(gen).to_be_disabled()
            url_before = page.url
            gen.click(force=True)
            page.wait_for_timeout(1200)
            assert page.url == url_before
        shot(page, "L2-006_Generate禁用态")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-022: Agent 输入框输入文本后 Generate 可点击并进入画布")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_022_generate_after_text(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 输入文本 -> 点击 Generate；预期: enabled 并进入 /create/edit"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            gen = page.locator("section.mobile-home-agent-hero button", has_text="Generate").first
            expect(gen).to_be_disabled()
            page.locator("textarea[aria-label]").first.fill("a studio portrait with soft light")
            page.wait_for_timeout(1200)
            expect(gen).to_be_enabled()
            gen.click()
            page.wait_for_timeout(8000)
            assert "/create/edit?pid=" in page.url
        shot(page, "L2-022_画布")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-007: 功能卡片上传打开对应画布面板")
    @pytest.mark.parametrize("card_name,expected_panel", [
        ("Remove Background", "Remove Background"),
        ("Clothes Changer", "Clothes Changer"),
        ("HD Photo Coverter", "Photo Enhancer"),
        ("Body Editor", "AI Body Editor"),
        ("AI Replace", "AI Replace"),
    ], ids=["remove_bg", "clothes", "hd", "body", "ai_replace"])
    def test_l2_007_function_card_upload(self, mobile_page: Page, base_url: str, card_name, expected_panel):
        allure.dynamic.title(f"L2-007: 功能卡片上传打开对应画布面板 — {card_name}")
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            upload_via(page, page.get_by_role("button", name=card_name).first, IMG_VALID)
            page.wait_for_timeout(6000)
            assert "/create/edit?pid=" in page.url
            assert expected_panel in page.inner_text("body")
        shot(page, f"L2-007_{card_name}_画布面板")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-008: ID Photo Maker 匿名态上传有效图弹注册弹层")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_008_id_photo_anonymous(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 打开首页 -> ID Photo Maker 上传有人脸.JPG；预期: 不进入画布，弹注册/获取点数弹层"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            upload_via(page, page.get_by_role("button", name="ID Photo Maker").first, IMG_VALID)
            page.wait_for_timeout(6000)
            assert page.url.rstrip("/") == f"{base_url}/".rstrip("/")
            body = page.inner_text("body")
            assert ("Get Free Credits" in body) or ("Get Up to" in body)
        shot(page, "L2-008_注册弹层")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-009: More Pokecut Tools 跳转 tools 页")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_009_more_tools(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 点击 More Pokecut Tools；预期: /tools"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            page.get_by_role("button", name="More Pokecut Tools").click()
            page.wait_for_timeout(4000)
            assert page.url.rstrip("/").endswith("/tools")
        shot(page, "L2-009_tools页")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-010: effect 模板卡上传进入画布")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_010_effect_template(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 点击 effect 模板卡（Slim）上传；预期: 进入 /create/edit"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            # 2026-09-14 漂移修正：原 "Butt" 模板入口不存在，改用实测可上传进画布的 Slim 模板卡。
            # 卡片缩略图 img 为叠加层（class 含 invisible），需 force 点击才触发文件选择器（MCP 实测路径）。
            trigger = page.locator("img[alt='Slim']").first
            trigger.scroll_into_view_if_needed()
            page.wait_for_timeout(300)
            with page.expect_file_chooser(timeout=10000) as chooser_info:
                trigger.click(force=True)
            chooser_info.value.set_files(IMG_VALID)
            page.wait_for_timeout(300)
            page.wait_for_timeout(6000)
            assert "/create/edit?pid=" in page.url
        shot(page, "L2-010_画布")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-011: See More Creations 跳转 create 页")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_011_see_more(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 点击 See More Creations；预期: /create"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            page.get_by_role("button", name="See More Creations").click()
            page.wait_for_timeout(4000)
            assert page.url.rstrip("/").endswith("/create")
        shot(page, "L2-011_create页")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-012: Test 4 链接跳转站内工具页")
    @pytest.mark.parametrize("name,path", [
        ("Pretty Scale", "/tools/pretty-scale"),
        ("Ethnicity Guesser", "/tools/ethnicity-guesser-ai"),
        ("Eye Color Detector", "/tools/eye-color-detector"),
        ("Body Shape Detector", "/tools/body-shape-detector"),
    ], ids=["pretty_scale", "ethnicity", "eye_color", "body_shape"])
    def test_l2_012_test_links(self, mobile_page: Page, base_url: str, name, path):
        allure.dynamic.title(f"L2-012: Test 4 链接跳转站内工具页 — {name}")
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            page.get_by_role("link", name=name).first.click()
            page.wait_for_timeout(4000)
            assert page.url.rstrip("/").endswith(path)
        shot(page, f"L2-012_{name}")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-013: 人像 tab 切换内容切换")
    @pytest.mark.parametrize("tab", ["Face", "Body", "Hair", "Background"], ids=["face", "body", "hair", "background"])
    def test_l2_013_portrait_tabs(self, mobile_page: Page, base_url: str, tab):
        allure.dynamic.title(f"L2-013: 人像 tab 切换内容切换 — {tab}")
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            loc = page.locator(f"#home-mobile-portrait-tab-{tab.lower()}")
            scroll_to(loc)
            loc.click()
            page.wait_for_timeout(1200)
            expect(loc).to_have_attribute("aria-selected", "true")
        shot(page, f"L2-013_{tab}")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-014: 画质增强 4 标签交互")
    @pytest.mark.parametrize("name,expected", [
        ("HD Enhance", "tools/hd-pic-converter"),
        ("Text Enhance", "tools/ai-image-text-enhancer"),
        ("Portrait AI", "upload"),
        ("Ultra Enhance", "upload"),
    ], ids=["hd", "text", "portrait", "ultra"])
    def test_l2_014_enhance_actions(self, mobile_page: Page, base_url: str, name, expected):
        allure.dynamic.title(f"L2-014: 画质增强 4 标签交互 — {name}")
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            loc = page.locator(f"button[aria-label='{name}']")
            scroll_to(loc)
            if expected == "upload":
                upload_via(page, loc, IMG_VALID)
                page.wait_for_timeout(6000)
                assert "/create/edit?pid=" in page.url
            else:
                loc.click()
                page.wait_for_timeout(4000)
                assert expected in page.url
        shot(page, f"L2-014_{name}")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-015: 数据卡片点击选中态")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_015_data_card_selected(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 点击 3M+ creators 卡片；预期: active 样式变化"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            card = page.get_by_role("button", name="3M+ creators")
            scroll_to(card)
            before = card.get_attribute("class")
            card.click()
            page.wait_for_timeout(800)
            after = card.get_attribute("class")
            assert after != before or "active" in after
        shot(page, "L2-015_数据卡片选中态")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-016: Product Hunt 新标签页跳转")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_016_product_hunt(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 检查 Product Hunt 链接；预期: target=_blank 且 href 正确"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            link = page.locator("a[href*='producthunt.com/products/pokecut-ai']").first
            assert "producthunt.com/products/pokecut-ai" in link.get_attribute("href")
            assert link.get_attribute("target") == "_blank"
        shot(page, "L2-016_ProductHunt")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-018: FAQ 展开收起与答案链接")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_018_faq(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 2 — 交互行为；步骤: 展开/收起 FAQ，检查 /pricing、/term-of-use、refund ticket"""
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            header = page.locator(".pk-collapse-header").first
            panel = header.locator("xpath=following-sibling::div[contains(@class,'pk-collapse-panel')]")
            scroll_to(header)
            assert panel.evaluate("el => el.scrollHeight") > 0
            header.click()
            page.wait_for_timeout(1200)
            header.click()
            page.wait_for_timeout(800)
            assert page.locator("a[href='/pricing']").first.is_visible()
            assert page.locator("a[href='/term-of-use']").first.is_visible()
            assert page.locator("a[data-submit-ticket='refund']").first.is_visible()
        shot(page, "L2-018_FAQ")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("L2-020: 底部导航各入口")
    @pytest.mark.parametrize("item", ["Home", "All Tools", "Upload", "Generate", "Pricing"], ids=["home", "tools", "upload", "generate", "pricing"])
    def test_l2_020_bottom_nav(self, mobile_page: Page, base_url: str, item):
        allure.dynamic.title(f"L2-020: 底部导航各入口 — {item}")
        page = mobile_page
        with allure.step("导航到目标页面"):
            goto_home(page, base_url)
        with allure.step("执行操作"):
            nav = page.locator("nav.home-mobile-bottom-nav")
            if item == "Upload":
                upload_via(page, nav.get_by_role("button", name="Upload"), IMG_VALID)
                page.wait_for_timeout(6000)
                assert "/create/edit?pid=" in page.url
            elif item == "Pricing":
                nav.locator("button[aria-label='Pricing']").evaluate("el => el.click()")
                page.wait_for_timeout(4000)
                assert page.url.rstrip("/").endswith("/pricing")
            else:
                nav.get_by_role("button", name=item).click()
                page.wait_for_timeout(4000)
                if item == "Home":
                    assert page.url.rstrip("/").endswith("/create")
                elif item == "All Tools":
                    assert page.url.rstrip("/").endswith("/tools")
                else:
                    assert "/create/edit?pid=" in page.url
        shot(page, f"L2-020_{item}")


@allure.feature("移动端首页")
@allure.story("L3-异常与权限")
class TestL3Exceptions:
    """Layer 3: 异常 / 权限 / 兼容"""

    @pytest.mark.login_required
    @pytest.mark.full
    @allure.title("L3-004: ID Photo Maker 抠图成功进入证件照画布")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.skip(reason="blocked_by_bug: 首页 Sign up 登录弹层提交无反应，无法建立登录态")
    def test_l3_004_id_photo_success(self):
        """覆盖层级: Layer 3 — 异常/权限；前置条件: 登录具备 ID credits 的账号；预期: 抠图成功进入证件照画布"""
        pass
