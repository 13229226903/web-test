# -*- coding: utf-8 -*-
"""Pokecut PC 首页 v6 自动化用例。

用例来源:
- artifacts/2026-09-07_pokecut_pc_home_dev_interactions/cases.md
- page_map/pokecut/home_v6.yaml
- data/pokecut_pc_home_v6.yaml
"""

import re
from pathlib import Path
from urllib.parse import urlparse

import allure
import pytest
import yaml
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "pokecut_pc_home_v6.yaml"


def _repo_root():
    """归档副本位于 archive/<dir>/，需按 test_images/ 上溯仓库根（原 parents[1] 解析到 archive/ 会找不到素材）。"""
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / "test_images").is_dir():
            return c
    return Path(__file__).resolve().parent.parent


TEST_IMAGE = _repo_root() / "test_images" / "1K.jpg"


@pytest.fixture(scope="module")
def home_data():
    """读取 PC 首页测试数据。"""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


# ─────────────────────────── 公共工具 ───────────────────────────

def goto_home(page: Page, base_url: str):
    """打开 PC 首页并等待 SPA 水合完成。"""
    page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)


def wait_for_render(page: Page, timeout: int = 2000):
    """等待页面渲染完成后再截图。"""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except PlaywrightTimeoutError:
        pass
    page.wait_for_timeout(500)


def shot(page: Page, name: str):
    """给 Allure 附加当前视口截图。"""
    wait_for_render(page)
    allure.attach(
        page.screenshot(full_page=False),
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


def body_text(page: Page) -> str:
    """返回规整后的页面正文。"""
    return re.sub(r"\s+", " ", page.locator("body").inner_text(timeout=15000)).strip()


def assert_body_contains(page: Page, expected_texts):
    """断言页面正文包含指定文案。"""
    body = body_text(page)
    missing = [text for text in expected_texts if text not in body]
    assert not missing, "页面缺少当前基线文案: " + "; ".join(missing)


def section_by_text(page: Page, heading: str):
    """按标题文本定位首页板块，并滚动到可见。"""
    locator = page.locator("section").filter(has_text=heading).first
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(800)
    return locator


def control_by_text(page: Page, text: str):
    """按文本定位可见的 a/button 控件。"""
    locator = page.locator("a, button").filter(has_text=text).first
    locator.scroll_into_view_if_needed()
    page.wait_for_timeout(300)
    return locator


def wait_for_path(page: Page, expected_path: str, timeout: int = 30000):
    """等待 URL path 精确等于预期值。"""
    page.wait_for_function(
        "expected => window.location.pathname === expected",
        arg=expected_path,
        timeout=timeout,
    )
    assert urlparse(page.url).path == expected_path, f"URL path 应为 {expected_path}，实际: {page.url}"


def wait_for_pid_path(page: Page, expected_paths, timeout: int = 45000):
    """等待进入带 pid 参数的画布或批量编辑页。"""
    page.wait_for_function(
        "paths => paths.includes(window.location.pathname) && window.location.search.includes('pid=')",
        arg=list(expected_paths),
        timeout=timeout,
    )
    assert urlparse(page.url).path in expected_paths, f"URL path 应为 {expected_paths} 之一，实际: {page.url}"
    assert "pid=" in page.url, f"URL 应包含 pid 参数，实际: {page.url}"


def upload_via_file_chooser(page: Page, control, image_path: Path):
    """通过真实控件触发系统文件选择器并上传图片。"""
    control.scroll_into_view_if_needed()
    with page.expect_file_chooser(timeout=15000) as chooser:
        control.click()
    chooser.value.set_files(str(image_path))
    page.wait_for_timeout(3000)


def click_and_assert_path(page: Page, control, expected_path: str):
    """点击控件并断言跳转 path。"""
    control.scroll_into_view_if_needed()
    control.click()
    wait_for_path(page, expected_path)


def actual_model_order(page: Page):
    """从页面按钮 aria-label 中提取模型顺序。"""
    return page.locator("button[aria-label]").evaluate_all(
        """buttons => buttons
            .map(button => button.getAttribute('aria-label'))
            .filter(name => name && [
                'Nano Banana 2', 'Nano Banana Pro', 'Seedream 5.0 Lite', 'Seedream 5.0 Pro',
                'Pokecut Pro', 'ChatGPT Image 2.0', 'Seedream 4.0', 'Pokecut Basic',
                'Nano Banana 2 Lite'
            ].includes(name))"""
    )


# ─────────────────────────── L1：页面结构 ───────────────────────────

@allure.epic("PC 首页")
@allure.feature("PC 首页")
@allure.story("L1-页面结构元素")
class TestL1PageStructure:
    """Layer 1: PC 首页页面元素 / 结构"""

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("PC-HOME-L1-001: 英文首页 Hero 标题与描述可见")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l1_001_hero_title_and_description(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L1-001
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 访问 /
          2. 确认语言为 English
        预期结果: Hero 标题与描述按基线展示
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("确认英文 Hero 标题与描述"):
            assert urlparse(page.url).path == "/", f"英文首页应落在 /，实际: {page.url}"
            expect(page.locator("h1").first).to_have_text(home_data["hero"]["title"], timeout=15000)
            expect(page.locator("p").filter(has_text=home_data["hero"]["description"]).first).to_be_visible(timeout=15000)
        with allure.step("截图记录 Hero"):
            shot(page, "PC-HOME-L1-001_hero")

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("PC-HOME-L1-002: 顶部导航与匿名认证入口可见")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l1_002_top_navigation_and_auth(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L1-002
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 访问 /
          2. 检查顶部导航
        预期结果: Logo、AI Free Tools、Portrait Editor、Discover、Pricing、Sign up、Log in 均可见
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("检查顶部导航与匿名认证入口"):
            expect(page.locator("a[href='/']").first).to_be_visible(timeout=15000)
            for label in home_data["navigation"]["buttons"]:
                expect(page.get_by_role("button", name=label, exact=True).first).to_be_visible(timeout=15000)
            expect(page.get_by_role("link", name=home_data["navigation"]["pricing"]).first).to_be_visible(timeout=15000)
            expect(page.get_by_role("button", name=home_data["navigation"]["signup"], exact=True).first).to_be_visible(timeout=15000)
            expect(page.get_by_role("button", name=home_data["navigation"]["login"], exact=True).first).to_be_visible(timeout=15000)
        with allure.step("截图记录顶部导航"):
            shot(page, "PC-HOME-L1-002_nav")

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("PC-HOME-L1-003: Popular Pokecut AI tools 卡片与模型列表可见")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_003_popular_tools_and_models(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L1-003
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 滚动到 Popular Pokecut AI tools
          2. 滚动到 AI Models
        预期结果: 3 张工具卡可见，9 个模型按钮按 expected_order 依次显示
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("检查 Popular Pokecut AI tools 卡片"):
            scroll_to = page.get_by_role("region", name=home_data["popular_tools"]["heading"]).first
            scroll_to.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            for label in home_data["popular_tools"]["cards"]:
                expect(control_by_text(page, label)).to_be_visible(timeout=15000)
            expect(control_by_text(page, home_data["popular_tools"]["more_tools"])).to_be_visible(timeout=15000)
        with allure.step("检查 AI Models 顺序"):
            models_heading = page.get_by_text(home_data["models"]["heading"], exact=False).first
            models_heading.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            assert actual_model_order(page) == home_data["models"]["order"], \
                f"模型顺序应为 {home_data['models']['order']}，实际: {actual_model_order(page)}"
        with allure.step("截图记录工具卡与模型列表"):
            shot(page, "PC-HOME-L1-003_tools_models")
    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("PC-HOME-L1-004: Templates 与 Test 面板结构及跳转")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_004_templates_and_test_links(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L1-004
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 滚动到 Templates
          2. 点击 See More Creations
          3. 返回首页并滚动到 Test 面板
          4. 依次点击 4 个 Test 链接
        预期结果: See More Creations 跳转 /create；4 个 Test 链接分别跳转对应工具页
        """
        with allure.step("导航到 PC 首页并检查 Templates"):
            goto_home(page, base_url)
            templates_heading = page.get_by_text(home_data["templates"]["heading"], exact=False).first
            templates_heading.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            expect(control_by_text(page, home_data["templates"]["cta"])).to_be_visible(timeout=15000)
        with allure.step("点击 See More Creations 并断言 /create"):
            click_and_assert_path(page, control_by_text(page, home_data["templates"]["cta"]), "/create")
            shot(page, "PC-HOME-L1-004_see_more_creations")
        with allure.step("依次点击 4 个 Test 链接并断言目标 path"):
            for label, expected_path in home_data["templates"]["links"].items():
                goto_home(page, base_url)
                test_heading = page.get_by_text(home_data["templates"]["test_panel"], exact=False).first
                test_heading.scroll_into_view_if_needed()
                page.wait_for_timeout(800)
                link = page.locator("a").filter(has_text=label).first
                click_and_assert_path(page, link, expected_path)
                shot(page, f"PC-HOME-L1-004_{label.replace(' ', '_')}")

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("PC-HOME-L1-005: Portrait、Batch、Enhance 板块结构与交互")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_005_portrait_batch_enhance(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L1-005
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 匿名访问 PC 首页，使用 test_images/1K.jpg
        测试步骤:
          1. 滚动到 Portrait 并依次点击 4 个 tab
          2. 在每个 tab 下检查模板数量并点击一个模板
          3. 滚动到 Batch 并依次点击 4 个按钮，上传有效图片
          4. 滚动到 Enhance 并依次点击 4 个按钮；Portrait/Ultra 需上传有效图片
        预期结果: Portrait tab 仅切换展示；Batch 上传后进入 /batch-edit/edit?pid=；Enhance 直接或上传后进入目标页
        """
        with allure.step("检查 Portrait 4 个 tab、模板数量与模板跳转"):
            for tab in home_data["portrait"]["tabs"]:
                goto_home(page, base_url)
                portrait_section = section_by_text(page, home_data["portrait"]["heading"])
                tab_button = portrait_section.get_by_role("button", name=tab, exact=True).first
                tab_button.click()
                page.wait_for_timeout(1200)
                template_cards = portrait_section.locator("a[href]")
                expect(template_cards).to_have_count(home_data["portrait"]["template_count"], timeout=15000)
                first_card = template_cards.first
                href = first_card.get_attribute("href") or ""
                assert href, f"{tab} 分类第一个模板缺少 href"
                first_card.click()
                page.wait_for_timeout(2000)
                assert urlparse(page.url).path == urlparse(href).path, \
                    f"{tab} 模板应跳转 {urlparse(href).path}，实际: {page.url}"
                shot(page, f"PC-HOME-L1-005_portrait_{tab.replace(' ', '_')}")
        with allure.step("检查 Batch 4 个上传入口"):
            for label in home_data["batch"]["buttons"]:
                goto_home(page, base_url)
                batch_section = section_by_text(page, home_data["batch"]["heading"])
                button = batch_section.locator("a, button, [role='button']").filter(has_text=label).first
                upload_via_file_chooser(page, button, TEST_IMAGE)
                wait_for_pid_path(page, ["/batch-edit/edit"])
                shot(page, f"PC-HOME-L1-005_batch_{label.replace(' ', '_')}")
        with allure.step("检查 Enhance 4 个按钮"):
            for label, expected_path in home_data["enhance"]["direct"].items():
                goto_home(page, base_url)
                enhance_section = section_by_text(page, home_data["enhance"]["heading"])
                button = enhance_section.locator("a, button, [role='button']").filter(has_text=label).first
                click_and_assert_path(page, button, expected_path)
                shot(page, f"PC-HOME-L1-005_enhance_{label.replace(' ', '_')}")
            for label in home_data["enhance"]["upload"]:
                goto_home(page, base_url)
                enhance_section = section_by_text(page, home_data["enhance"]["heading"])
                button = enhance_section.locator("a, button, [role='button']").filter(has_text=label).first
                upload_via_file_chooser(page, button, TEST_IMAGE)
                wait_for_pid_path(page, ["/agent", "/create/edit"])
                shot(page, f"PC-HOME-L1-005_enhance_{label.replace(' ', '_')}")

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("PC-HOME-L1-006: Trust 数据与用户评论结构可见")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_006_trust_and_reviews(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L1-006
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 滚动到 Trust
          2. 滚动到 Reviews
        预期结果: 4 项统计与 5 位用户评论可见
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("检查 Trust 与 Reviews"):
            trust_heading = page.get_by_text(home_data["trust"]["heading"], exact=False).first
            trust_heading.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            assert_body_contains(page, home_data["trust"]["stats"])
            reviews_heading = page.get_by_text(home_data["reviews"]["heading"], exact=False).first
            reviews_heading.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            assert_body_contains(page, home_data["reviews"]["users"])
        with allure.step("截图记录 Trust 与 Reviews"):
            shot(page, "PC-HOME-L1-006_trust_reviews")

    @pytest.mark.no_login
    @pytest.mark.regression
    @allure.title("PC-HOME-L1-007: FAQ、Mobile App 与页脚结构可见")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l1_007_faq_mobile_footer(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L1-007
        覆盖层级: Layer 1 — 页面元素 / 结构
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 滚动到 FAQ
          2. 滚动到页脚
        预期结果: 8 组 FAQ、Mobile App 标题、页脚语言按钮与链接组可见
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("检查 FAQ、Mobile App 与页脚"):
            faq_heading = page.get_by_text(home_data["faq"]["heading"], exact=False).first
            faq_heading.scroll_into_view_if_needed()
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
            actual_questions = [text.strip() for text in page.locator("h3").all_inner_texts()]
            assert actual_questions == home_data["faq"]["questions"], f"FAQ 问题应完全匹配，实际: {actual_questions}"
            mobile_heading = page.get_by_text(home_data["mobile_app"]["heading"], exact=False).first
            mobile_heading.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            assert_body_contains(page, [home_data["mobile_app"]["app_store"], home_data["mobile_app"]["google_play"]])
            copyright = page.get_by_text(home_data["footer"]["copyright"], exact=False).last
            footer = copyright.locator("xpath=..")
            footer.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            footer_text = footer.inner_text(timeout=15000)
            for group in home_data["footer"]["groups"]:
                assert group in footer_text, f"页脚缺少链接组: {group}"
            assert home_data["footer"]["copyright"] in footer_text, "页脚缺少版权文案"
            expect(page.get_by_role("button", name="Language: English").first).to_be_visible(timeout=15000)
        with allure.step("截图记录 FAQ、Mobile App 与页脚"):
            shot(page, "PC-HOME-L1-007_faq_footer")


# ─────────────────────────── L2：交互行为 ───────────────────────────

@allure.epic("PC 首页")
@allure.feature("PC 首页")
@allure.story("L2-交互行为元素")
class TestL2Interactions:
    """Layer 2: PC 首页交互行为 / 状态迁移"""

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-001: 顶部导航下拉可展开并展示分组链接")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_001_nav_dropdowns(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-001
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 访问 /
          2. 点击 AI Free Tools 并检查下拉
          3. 关闭后点击 Portrait Editor 并检查下拉
        预期结果: 两个下拉均展开并显示对应分组与链接
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("展开 AI Free Tools 下拉"):
            button = page.get_by_role("button", name=home_data["navigation"]["buttons"][0], exact=True).first
            button.click()
            page.wait_for_timeout(1000)
            assert button.get_attribute("aria-expanded") == "true", "AI Free Tools 展开后 aria-expanded 应为 true"
        with allure.step("检查 AI Free Tools 下拉分组与链接"):
            assert_body_contains(page, ["Popular Tools", "Photo Editor", "AI Filter"])
            expect(page.get_by_role("link", name="All Tools").first).to_be_visible(timeout=15000)
            expect(page.get_by_role("link", name="Batch Photo Edit").first).to_be_visible(timeout=15000)
            expect(page.get_by_role("link", name="AI Background Remover").first).to_be_visible(timeout=15000)
        with allure.step("关闭 AI Free Tools 并展开 Portrait Editor 下拉"):
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            portrait_button = page.get_by_role("button", name=home_data["navigation"]["buttons"][1], exact=True).first
            portrait_button.click()
            page.wait_for_timeout(1000)
            assert portrait_button.get_attribute("aria-expanded") == "true", "Portrait Editor 展开后 aria-expanded 应为 true"
        with allure.step("检查 Portrait Editor 下拉分组与链接"):
            assert_body_contains(page, ["Face Editor", "Body Editor", "Hair Editor"])
            expect(page.get_by_role("link", name="AI Makeup Photo Editor").first).to_be_visible(timeout=15000)
            expect(page.get_by_role("link", name="Body Sculpt").first).to_be_visible(timeout=15000)
        with allure.step("截图记录两个下拉"):
            shot(page, "PC-HOME-L2-001_nav_dropdowns")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-004: 页脚语言菜单可切换 English / 简体中文")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_004_language_switch(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-004
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 访问 /zh
          2. 点击页脚语言按钮
          3. 点击 English 并确认英文态
          4. 再次打开语言菜单
          5. 点击简体中文并确认中文态
        预期结果: URL 分别变为 / 与 /zh，标题与主要文案随语言切换
        """
        with allure.step("先进入中文页"):
            page.goto(f"{base_url.rstrip('/')}/zh", wait_until="domcontentloaded", timeout=60000)
            page.wait_for_timeout(4000)
        with allure.step("打开语言菜单并切换 English"):
            language_button = page.get_by_role("button", name=re.compile("Language|语言")).first
            language_button.click()
            page.wait_for_timeout(800)
            english_option = page.get_by_text(home_data["language"]["english"], exact=True).first
            english_option.click()
            wait_for_path(page, "/")
        with allure.step("确认英文标题并截图"):
            expect(page.locator("h1").first).to_have_text(home_data["language"]["english_heading"], timeout=15000)
            page.evaluate("window.scrollTo(0, 0)")
            shot(page, "PC-HOME-L2-004_language_switch_english")
        with allure.step("再次打开语言菜单并切换简体中文"):
            language_button = page.get_by_role("button", name="Language: English").first
            language_button.click()
            page.wait_for_timeout(800)
            chinese_option = page.get_by_text(home_data["language"]["simplified_chinese"], exact=True).first
            chinese_option.click()
            wait_for_path(page, "/zh")
        with allure.step("确认中文标题并截图"):
            expect(page.locator("h1").first).to_have_text(home_data["language"]["chinese_heading"], timeout=15000)
            page.evaluate("window.scrollTo(0, 0)")
            shot(page, "PC-HOME-L2-004_language_switch_chinese")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-006: Hero Prompt 输入文本后 Generate 变为可用并跳转画布")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_006_prompt_text_generate(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-006
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 访问 /
          2. 确认 Generate 默认 disabled
          3. 点击 AI image prompt 输入框，确认变为可编辑并清空默认示例文案
          4. 输入文本
          5. 等待 Generate 变为 enabled
          6. 点击 Generate
        预期结果: 输入文本后 Generate enabled，点击后 URL 包含 /agent?pid=
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("确认 Prompt 初始 readonly 且 Generate disabled"):
            textbox = page.get_by_role("textbox", name=home_data["hero"]["prompt_label"]).first
            generate = page.locator("button[aria-label='Generate']").first
            expect(textbox).to_be_visible(timeout=15000)
            expect(generate).to_be_visible(timeout=15000)
            assert textbox.get_attribute("readonly") is not None, "Prompt 输入框初始应为 readonly"
            expect(generate).to_be_disabled()
        with allure.step("点击输入框并输入文本"):
            textbox.click()
            page.wait_for_timeout(500)
            assert textbox.get_attribute("readonly") is None, "点击后 Prompt 输入框应变为可编辑"
            assert textbox.input_value() == "", "点击后 Prompt 输入框应清空默认示例文案"
            textbox.fill(home_data["hero"]["prompt_text"])
            expect(generate).to_be_enabled()
            shot(page, "PC-HOME-L2-006_generate_enabled")
        with allure.step("点击 Generate 并断言 /agent?pid="):
            generate.click()
            wait_for_pid_path(page, ["/agent"])
            shot(page, "PC-HOME-L2-006_agent_canvas")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-007: Hero Prompt 上传图片并生成后进入画布")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_007_prompt_upload_generate(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-007
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页，使用 test_images/1K.jpg
        测试步骤:
          1. 点击 Upload image
          2. 选择 test_images/1K.jpg
          3. 等待图片加载
          4. 输入文本
          5. 点击 Generate
        预期结果: 图片加载到输入框；Generate 可点击；点击后 URL 包含 pid 参数
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("上传 1K.jpg 并确认图片加载到输入框"):
            upload_button = page.locator("button[aria-label='Upload image']").first
            upload_via_file_chooser(page, upload_button, TEST_IMAGE)
            uploaded_thumb = page.locator(".cinematic-uploaded-image").first
            expect(uploaded_thumb).to_be_visible(timeout=15000)
            background = uploaded_thumb.evaluate("element => getComputedStyle(element).backgroundImage")
            assert "blob:" in background, f"上传缩略图应使用 blob 图片，实际: {background}"
        with allure.step("输入文本并点击 Generate"):
            textbox = page.get_by_role("textbox", name=home_data["hero"]["prompt_label"]).first
            generate = page.locator("button[aria-label='Generate']").first
            textbox.fill(home_data["hero"]["prompt_text"])
            expect(generate).to_be_enabled()
            shot(page, "PC-HOME-L2-007_upload_and_generate_enabled")
            generate.click()
            wait_for_pid_path(page, ["/agent", "/create/edit"])
            shot(page, "PC-HOME-L2-007_upload_and_generate")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-008: Hero Prompt 模型与设置弹层可打开")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_008_prompt_popups(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-008
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 访问 /
          2. 点击 AI image prompt 输入框
          3. 点击 Pokecut Pro 并检查模型菜单
          4. 关闭后点击 Prompt settings 并检查设置面板
        预期结果: 模型菜单与设置面板均可打开并显示可配置项
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("点击 Prompt 后打开模型菜单"):
            page.get_by_role("textbox", name=home_data["hero"]["prompt_label"]).first.click()
            page.wait_for_timeout(300)
            model_button = page.locator("button.cinematic-model").first
            model_button.scroll_into_view_if_needed()
            # 2026-09-14 复探（page_map home_v7）：模型入口为 button.cinematic-model（文案 Auto），
            # 普通 click 不展开菜单（元素在视口下方 + Vue 绑定），需 dispatchEvent 触发。
            # 2026-09-14 复探：等模型入口可交互（SPA 水合）后再触发；菜单是 toggle，
            # 仅在未展开时 dispatch，循环兜底避免水合未完成导致首次点击无效。
            model_button.wait_for(state="visible", timeout=15000)
            page.wait_for_timeout(1500)
            for _ in range(3):
                if page.locator(".cinematic-popup").count():
                    break
                model_button.dispatch_event("click")
                page.wait_for_timeout(1500)
            popup = page.locator(".cinematic-popup").first
            expect(popup).to_be_visible(timeout=15000)
            popup_text = popup.inner_text(timeout=15000)
            for option in home_data["models"]["menu_options"]:
                assert option in popup_text, f"模型菜单缺少选项: {option}"
            shot(page, "PC-HOME-L2-008_prompt_model_menu")
        with allure.step("关闭模型菜单并打开设置面板"):
            page.keyboard.press("Escape")
            page.wait_for_timeout(500)
            settings_button = page.locator("button[aria-label='Prompt settings']").first
            settings_button.scroll_into_view_if_needed()
            settings_button.click()
            page.wait_for_timeout(1000)
            popup = page.locator(".cinematic-popup").first
            expect(popup).to_be_visible(timeout=15000)
            popup_text = popup.inner_text(timeout=15000)
            for option in home_data["enhance"]["settings_options"]:
                assert option in popup_text, f"设置面板缺少配置项: {option}"
            shot(page, "PC-HOME-L2-008_prompt_settings")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-010: Start Creating for Free 可进入创作页")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_010_start_creating(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-010
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 点击 Start Creating for Free
        预期结果: 跳转到创作页（/agent 或 /create），URL 携带 pid
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("点击 Start Creating for Free"):
            button = page.get_by_role("button", name=home_data["hero"]["cta"], exact=True).first
            button.click()
            wait_for_pid_path(page, ["/agent", "/create"])
        with allure.step("截图记录创作页"):
            shot(page, "PC-HOME-L2-010_start_creating")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-011: Popular tools 三张卡片交互与跳转")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_011_popular_tools_interactions(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-011
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页，使用 test_images/1K.jpg
        测试步骤:
          1. 点击 AI Clothes Changer
          2. 上传有效图片
          3. 返回首页
          4. 点击 Enhance Text in Images
          5. 返回首页
          6. 点击 AI Portrait Editor
          7. 上传有效图片
        预期结果: 上传入口进入 /agent 或 /create/edit?pid=；文字增强直接跳转工具页
        """
        with allure.step("检查 AI Clothes Changer 上传入口"):
            goto_home(page, base_url)
            card = control_by_text(page, home_data["popular_tools"]["cards"][0])
            upload_via_file_chooser(page, card, TEST_IMAGE)
            wait_for_pid_path(page, ["/agent", "/create/edit"])
            shot(page, "PC-HOME-L2-011_clothes_changer")
        with allure.step("检查 Enhance Text in Images 直接跳转"):
            goto_home(page, base_url)
            card = control_by_text(page, home_data["popular_tools"]["cards"][1])
            click_and_assert_path(page, card, "/tools/ai-image-text-enhancer")
            shot(page, "PC-HOME-L2-011_text_enhance")
        with allure.step("检查 AI Portrait Editor 上传入口"):
            goto_home(page, base_url)
            card = control_by_text(page, home_data["popular_tools"]["cards"][2])
            upload_via_file_chooser(page, card, TEST_IMAGE)
            wait_for_pid_path(page, ["/agent", "/create/edit"])
            shot(page, "PC-HOME-L2-011_portrait_editor")

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L2-012: More Pokecut AI Tools 可跳转工具列表")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_012_more_tools(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L2-012
        覆盖层级: Layer 2 — 交互行为 / 状态迁移
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 点击 More Pokecut AI Tools
        预期结果: 跳转到 /tools
        """
        with allure.step("导航到 PC 首页"):
            goto_home(page, base_url)
        with allure.step("点击 More Pokecut AI Tools"):
            button = control_by_text(page, home_data["popular_tools"]["more_tools"])
            click_and_assert_path(page, button, "/tools")
        with allure.step("截图记录工具列表"):
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)
            shot(page, "PC-HOME-L2-012_more_tools")


# ─────────────────────────── L3：异常 / 权限 / 兼容 ───────────────────────────

@allure.epic("PC 首页")
@allure.feature("PC 首页")
@allure.story("L3-异常与权限")
class TestL3Exceptions:
    """Layer 3: PC 首页异常 / 权限 / 兼容"""

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L3-002: 中文 locale 默认路由为 /zh")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l3_002_chinese_locale_route(self, browser, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L3-002
        覆盖层级: Layer 3 — 异常 / 权限 / 兼容
        前置条件: 使用 zh-CN locale 匿名访问 PC 首页
        测试步骤:
          1. 以中文 locale 访问根路径
        预期结果: URL 变为 /zh，页面主要文案为中文
        """
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
        page = context.new_page()
        try:
            with allure.step("以 zh-CN locale 访问根路径"):
                page.goto(f"{base_url.rstrip('/')}/", wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)
                wait_for_path(page, "/zh")
            with allure.step("确认中文标题"):
                expect(page.locator("h1").first).to_have_text(home_data["language"]["chinese_heading"], timeout=15000)
            with allure.step("截图记录中文路由"):
                shot(page, "PC-HOME-L3-002_zh_route")
        finally:
            context.close()

    @pytest.mark.no_login
    @pytest.mark.full
    @allure.title("PC-HOME-L3-003: 外部链接在新标签页打开")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l3_003_external_link_new_tab(self, page: Page, base_url: str, home_data):
        """
        PRD引用: PC-HOME-L3-003
        覆盖层级: Layer 3 — 异常 / 权限 / 兼容
        前置条件: 匿名访问 PC 首页
        测试步骤:
          1. 点击用户评论外链
        预期结果: 打开 Product Hunt 用户页，不替换首页标签
        """
        with allure.step("导航到 PC 首页并定位 Jessica Miller 外链"):
            goto_home(page, base_url)
            link = page.locator("a").filter(has_text=home_data["reviews"]["users"][0]).first
            link.scroll_into_view_if_needed()
            page.wait_for_timeout(800)
            assert link.get_attribute("target") == "_blank", "用户评论外链应 target=_blank"
        with allure.step("点击外链并确认新标签页"):
            with page.expect_popup(timeout=30000) as popup_info:
                link.click()
            new_page = popup_info.value
            new_page.wait_for_load_state("domcontentloaded", timeout=30000)
            assert new_page.url.startswith(home_data["external"]["jessica_miller"]), \
                f"新标签页应打开 Product Hunt 用户页，实际: {new_page.url}"
            assert urlparse(page.url).path == "/", "原首页标签不应被外链替换"
            new_page.evaluate("window.scrollTo(0, 0)")
            new_page.wait_for_timeout(2000)
            shot(new_page, "PC-HOME-L3-003_external_link")
            new_page.close()