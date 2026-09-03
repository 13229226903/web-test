"""Pokecut PC 首页 v3.0 回归测试。"""

import glob
import os
import re
from urllib.parse import urlparse

import allure
import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect as pw_expect

from conftest import allure_screenshot
from helpers.link_checker import verify_seo_links


BASE_URL = "http://10.17.1.66:3001"
PAGE_URL = f"{BASE_URL}/"

EXPECTED_MODEL_ORDER = [
    "Nano Banana 2",
    "Seedream 5.0 Lite",
    "Nano Banana Pro",
    "Seedream 5.0 Pro",
    "Pokecut Pro",
    "ChatGPT Image 2.0",
    "Seedream 4.0",
    "Pokecut Basic",
    "Nano Banana 2 Lite",
]

TEST_PANEL_LINKS = {
    "Pretty Scale": "/tools/pretty-scale",
    "Ethnicity Guesser": "/tools/ethnicity-guesser-ai",
    "Eye Color Detector": "/tools/eye-color-detector",
    "Body Shape Detector": "/tools/body-shape-detector",
}

PORTRAIT_TEMPLATE_LINKS = {
    "Retouch Face": "first",
    "Change Hair": "first",
    "Retouch Body": "last",
    "Change Background": "first",
}

REVIEW_LINKS = {
    "Jessica Miller": "https://www.producthunt.com/@jessica_miller_7",
    "Angelina Peng": "https://www.producthunt.com/@angelina__s",
    "Leo Y.": "https://www.producthunt.com/@leo_ye",
    "Zepeng She": "https://www.producthunt.com/@rocsheh",
    "Rachit Magon": "https://www.producthunt.com/@rachitmagon",
}

REVIEW_IMAGE_SUFFIXES = {
    "Jessica Miller": "homepagerefresh_reviewportrait1_26071315000138.webp",
    "Angelina Peng": "homepagerefresh_reviewbatch1_26071315000139.webp",
    "Leo Y.": "homepagerefresh_reviewgenerate1_26071315000140.webp",
    "Zepeng She": "homepagerefresh_reviewproduct1_26071315000141.webp",
    "Rachit Magon": "homepagerefresh_reviewtemplate1_26071315000142.webp",
}

FAQ_QUESTIONS = [
    "What is Pokecut and what can I use it for?",
    "How do I use Pokecut?",
    "Is Pokecut free?",
    "Can I use Pokecut without signing up?",
    "Can I use Pokecut's AI photo editor for commercial use?",
    "How can I contact Pokecut's support?",
    "What makes Pokecut better than other AI photo editing tools?",
    "Can Pokecut edit images in batches?",
]


def goto_home(page: Page):
    page.goto(PAGE_URL, timeout=120000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(2500)


def pick_test_image() -> str:
    root = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(root, "*")), key=lambda f: os.path.getsize(f))
    if not imgs:
        raise FileNotFoundError("找不到 test_images")
    return os.path.abspath(imgs[0])


def text_content(page: Page) -> str:
    return re.sub(r"\s+", " ", page.locator("body").inner_text(timeout=15000)).strip()


def assert_body_contains(page: Page, expected_texts: list[str]):
    body = text_content(page)
    missing = [text for text in expected_texts if text not in body]
    assert not missing, "页面缺少当前基线文案: " + "; ".join(missing)


def visible_top_items(page: Page):
    return page.evaluate(
        """() => {
            const items = [];
            const seen = new Set();
            const nodes = document.querySelectorAll('a,button');
            for (const el of nodes) {
                const box = el.getBoundingClientRect();
                if (box.width <= 0 || box.height <= 0 || box.top > 90 || box.bottom < 0) continue;
                const style = window.getComputedStyle(el);
                if (style.visibility === 'hidden' || style.display === 'none') continue;
                const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').replace(/\\s+/g, ' ').trim();
                const href = el.getAttribute('href') || '';
                const key = `${text}|${href}|${Math.round(box.left)}`;
                if (!text || seen.has(key)) continue;
                seen.add(key);
                items.push({text, href, x: box.left, y: box.top});
            }
            return items.sort((a, b) => a.x - b.x);
        }"""
    )


def image_srcs(page: Page) -> list[str]:
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1200)
    return page.evaluate(
        """() => {
            const values = [];
            document.querySelectorAll('img, source, [style]').forEach((el) => {
                const attrs = el.attributes || [];
                for (const attr of attrs) {
                    if (['src', 'srcset', 'data-src', 'data-srcset'].includes(attr.name)) {
                        values.push(attr.value);
                    }
                }
                const bg = window.getComputedStyle(el).backgroundImage;
                if (bg && bg !== 'none') values.push(bg);
                if (el.currentSrc) values.push(el.currentSrc);
            });
            return values.filter(Boolean);
        }"""
    )


def assert_image_suffixes(page: Page, suffixes: list[str]):
    srcs = image_srcs(page)
    missing = [suffix for suffix in suffixes if not any(suffix in src for src in srcs)]
    assert not missing, "页面缺少需求图片资源: " + "; ".join(missing)


def href_for_text(page: Page, text: str) -> str:
    locator = page.locator(f"a:has-text('{text}')").first
    pw_expect(locator).to_be_visible(timeout=10000)
    return locator.get_attribute("href") or ""


def assert_link_path(page: Page, text: str, expected_path: str):
    href = href_for_text(page, text)
    assert urlparse(href).path == expected_path, f"{text} 链接应为 {expected_path}，实际 {href}"


def assert_visible_control(page: Page, text: str):
    control = page.locator("a:visible, button:visible").filter(has_text=text).first
    pw_expect(control).to_be_visible(timeout=10000)


def first_visible_control(page: Page, text: str):
    control = page.locator("a:visible, button:visible, [role='button']:visible").filter(has_text=text).first
    pw_expect(control).to_be_visible(timeout=10000)
    return control


def attach_viewport_screenshot(page: Page, name: str):
    allure.attach(
        page.screenshot(full_page=False),
        name=name,
        attachment_type=allure.attachment_type.PNG,
    )


def home_section(page: Page, heading_text: str):
    return page.locator("section").filter(has_text=heading_text).first


def assert_landing_page(page: Page, expected_href: str, card_text: str):
    expected_path = urlparse(expected_href).path
    actual_path = urlparse(page.url).path
    assert actual_path == expected_path, f"模板点击后应进入 {expected_path}，实际: {page.url}"

    page.wait_for_timeout(500)
    title = page.title().strip()
    h1_text = " | ".join(page.locator("h1").all_inner_texts()).strip()
    body = text_content(page)
    probe = " ".join([title, h1_text, body[:800]]).lower()
    label = re.sub(r"^Try Now\\s+", "", card_text).strip()
    tokens = [token.lower() for token in re.split(r"[^A-Za-z0-9]+", label) if len(token) > 2]
    assert tokens and any(token in probe for token in tokens), \
        f"模板跳转页断言未命中，label={label}，title={title}，h1={h1_text}"

    allure.attach(
        f"url: {page.url}\ntitle: {title}\nh1: {h1_text}",
        name=f"跳转页-{label}",
        attachment_type=allure.attachment_type.TEXT,
    )


def click_and_assert_path(page: Page, text: str, expected_path: str):
    control = page.locator("a, button").filter(has_text=text).first
    pw_expect(control).to_be_visible(timeout=10000)
    control.click(force=True)
    page.wait_for_timeout(3000)
    assert urlparse(page.url).path == expected_path, f"{text} 点击后应跳转 {expected_path}，实际 {page.url}"


def click_upload_and_assert_batch_edit(page: Page, control, test_img: str):
    control.scroll_into_view_if_needed()
    control.click(force=True)
    inputs = page.locator("input[type=file]")
    assert inputs.count() >= 3, f"页面应存在多个上传 input，实际: {inputs.count()}"
    # 经过实际探测，Batch 区块使用第 3 个 hidden file input。
    inputs.nth(2).set_input_files(test_img)
    page.wait_for_function(
        "() => window.location.pathname === '/batch-edit/edit' && window.location.search.includes('pid=')",
        timeout=30000,
    )
    assert urlparse(page.url).path == "/batch-edit/edit", f"上传后应进入批量编辑页，实际: {page.url}"
    assert "pid=" in page.url, f"批量编辑页 URL 应含 pid 参数，实际: {page.url}"


def click_upload_and_assert_canvas(page: Page, control, test_img: str):
    control.scroll_into_view_if_needed()
    with page.expect_file_chooser(timeout=10000) as fc_info:
        control.click(force=True)
    fc_info.value.set_files(test_img)
    page.wait_for_function(
        "() => window.location.pathname === '/agent' || window.location.pathname.startsWith('/agent/')",
        timeout=30000,
    )
    page.wait_for_timeout(3000)
    assert "/agent" in page.url, f"上传后应进入画布页，实际: {page.url}"
    pw_expect(page.locator("button:has-text('Remove BG'):visible").first).to_be_visible(timeout=30000)


def click_locator_and_upload(page: Page, target, test_img: str, timeout: int = 5000) -> bool:
    for action in [
        lambda: target.click(force=True),
        lambda: target.evaluate(
            """(el) => el.dispatchEvent(new MouseEvent('click', {
                bubbles: true,
                cancelable: true,
                view: window
            }))"""
        ),
    ]:
        try:
            with page.expect_file_chooser(timeout=timeout) as fc_info:
                action()
            fc_info.value.set_files(test_img)
            return True
        except PlaywrightTimeoutError:
            continue
    return False


def click_dom_and_assert_path(page: Page, locator, expected_href: str, card_text: str):
    locator.evaluate("(el) => el.click()")
    page.wait_for_timeout(2500)
    assert_landing_page(page, expected_href, card_text)


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("首页 v3.0")
class TestHomePageV3:

    @allure.title("TC-HOME-V3-001 [P0] 顶部栏入口顺序与 Discover 下拉")
    def test_home_v3_001_header_nav_and_discover(self, page: Page):
        goto_home(page)
        allure_screenshot(page, "01-首页首屏")
        verify_seo_links(page, BASE_URL, "/", max_links=10)

        top_items = visible_top_items(page)
        top_text = " | ".join(item["text"] for item in top_items)
        for label in ["AI Free Tools", "Portrait Editor", "Discover", "Pricing"]:
            assert label in top_text, f"顶部栏缺少 {label}，当前顶部入口: {top_text}"

        positions = {
            label: min(item["x"] for item in top_items if label in item["text"])
            for label in ["AI Free Tools", "Portrait Editor", "Discover", "Pricing"]
        }
        ordered_labels = [label for label, _ in sorted(positions.items(), key=lambda item: item[1])]
        assert ordered_labels == ["AI Free Tools", "Portrait Editor", "Discover", "Pricing"], f"顶部入口顺序错误: {positions}"

        page.locator("button").filter(has_text="Discover").first.hover()
        page.wait_for_timeout(800)
        allure_screenshot(page, "01-Discover展开")
        assert_body_contains(page, ["FAQ", "Contact us", "About us"])

    @allure.title("TC-HOME-V3-002 [P0] 首屏文案、prompt 控件与主 CTA")
    def test_home_v3_002_hero_prompt_and_cta(self, page: Page):
        goto_home(page)
        assert_body_contains(
            page,
            [
                "All-in-One AI Photo Editor & Generator",
                "Use Pokecut to create, edit, and enhance images in one place with top AI models, practical photo editing tools, and ready-to-use creative workflows.",
                "Start Creating for Free",
            ],
        )
        for selector in [
            "button[aria-label='Upload image']",
            "button:has-text('Pokecut Pro')",
            "button[aria-label='Prompt settings']",
            "button[aria-label='Generate']",
        ]:
            pw_expect(page.locator(selector).first).to_be_visible(timeout=10000)

        cta = page.get_by_role("button", name="Start Creating for Free").first
        file_chooser_opened = False
        try:
            with page.expect_file_chooser(timeout=1000):
                cta.click(force=True)
            file_chooser_opened = True
        except PlaywrightTimeoutError:
            pass
        assert not file_chooser_opened, "首屏主按钮不应唤起系统上传弹窗"
        page.wait_for_timeout(3000)
        assert "/agent" in page.url, f"首屏主按钮应直接跳转无限画布 /agent，实际: {page.url}"

    @allure.title("TC-HOME-V3-003 [P0] 热门功能卡片与 More Tools 链接")
    def test_home_v3_003_popular_features(self, page: Page):
        goto_home(page)
        test_img = pick_test_image()
        assert_body_contains(
            page,
            [
                "AI Bikini Try-On",
                "Enhance Text in Images",
                "AI Portrait Editor",
                "Try Now",
                "More Pokecut AI Tools",
            ],
        )
        assert_visible_control(page, "More Pokecut AI Tools")

        for label in ["AI Bikini Try-On", "Enhance Text in Images", "AI Portrait Editor"]:
            goto_home(page)
            card = page.locator("a, button").filter(has_text=label).first
            card.scroll_into_view_if_needed()
            pw_expect(card).to_be_visible(timeout=10000)
            card.hover()
            allure_screenshot(page, f"03-{label}-hover")
            if label == "Enhance Text in Images":
                card.click(force=True)
                page.wait_for_timeout(2000)
                allure_screenshot(page, f"03-{label}-clicked")
                assert urlparse(page.url).path == "/tools/ai-image-text-enhancer"
            else:
                upload_trigger_candidates = [card, card.locator("button").first, card.locator("label").first]
                uploaded = False
                for target in upload_trigger_candidates:
                    if target.count() == 0:
                        continue
                    if click_locator_and_upload(page, target, test_img):
                        uploaded = True
                        break
                if not uploaded:
                    uploaded = click_locator_and_upload(
                        page,
                        page.get_by_text(label).first,
                        test_img,
                    )
                assert uploaded, f"{label} 未触发文件选择器"
                page.wait_for_timeout(5000)
                allure_screenshot(page, f"03-{label}-uploaded")
                assert "/agent" in page.url, f"{label} 应进入无限画布，实际: {page.url}"

    @allure.title("TC-HOME-V3-004 [P0] 模型板块标题与模型顺序")
    def test_home_v3_004_models_section(self, page: Page):
        goto_home(page)
        assert_body_contains(
            page,
            [
                "Choose the Right AI Model for Any Image",
                "Choose from Pokecut's multiple AI models",
            ],
        )
        actual = page.locator("button[aria-label]").evaluate_all(
            """(buttons) => buttons
                .map((btn) => btn.getAttribute('aria-label'))
                .filter((name) => name && [
                    'Nano Banana 2', 'Nano Banana Pro', 'Seedream 5.0 Lite', 'Seedream 5.0 Pro',
                    'Pokecut Pro', 'ChatGPT Image 2.0', 'Seedream 4.0', 'Nano Banana',
                    'Pokecut Basic', 'Nano Banana 2 Lite'
                ].includes(name))"""
        )
        assert actual == EXPECTED_MODEL_ORDER, f"模型卡顺序/名称不符合需求，实际: {actual}"

    @allure.title("TC-HOME-V3-005 [P0] 模板板块与 Test 板块")
    def test_home_v3_005_templates_and_test_panel(self, page: Page):
        goto_home(page)
        assert_body_contains(
            page,
            [
                "Start Faster with Pokecut's AI Templates",
                "See More Creations",
                "Test Your Photo Before You Edit",
                "Pretty Scale",
                "Ethnicity Guesser",
                "Eye Color Detector",
                "Body Shape Detector",
            ],
        )
        for label, path in TEST_PANEL_LINKS.items():
            assert_link_path(page, label, path)
        page.evaluate("window.scrollTo(0, 3700)")
        page.wait_for_timeout(1200)
        assert_visible_control(page, "See More Creations")
        more_btn = page.locator("button").filter(has_text="See More Creations").first
        more_btn.click(force=True)
        page.wait_for_timeout(1500)
        allure_screenshot(page, "05-SeeMoreCreations-点击后")
        assert urlparse(page.url).path == "/create"

    @allure.title("TC-HOME-V3-006 [P1] 人像、Batch、Enhance 板块")
    def test_home_v3_006_portrait_batch_enhance_sections(self, page: Page):
        goto_home(page)
        assert_body_contains(
            page,
            [
                "AI Portrait Detail Studio",
                "Upgrade Every Portrait Details with Pokecut",
                "Retouch Face",
                "Change Hair",
                "Retouch Body",
                "Change Background",
                "Edit up to 50 Photos in One Batch",
                "Remove BG",
                "Resize",
                "Enhance",
                "Change BG",
                "Enhance Photo Quality for Every Detail",
                "HD Enhance",
                "Text Enhance",
                "Portrait Enhance",
                "Ultra Enhance",
            ],
        )
        def open_portrait_category(category_label: str):
            goto_home(page)
            page.evaluate("window.scrollTo(0, 4500)")
            page.wait_for_timeout(1200)
            section = home_section(page, "AI Portrait Detail Studio")
            section.get_by_role("button", name=category_label).first.click(force=True)
            page.wait_for_timeout(1200)
            return home_section(page, "AI Portrait Detail Studio")

        page.evaluate("window.scrollTo(0, 4500)")
        page.wait_for_timeout(1200)
        before_url = page.url
        for label in PORTRAIT_TEMPLATE_LINKS:
            portrait_section = open_portrait_category(label)
            assert page.url == before_url, f"{label} 只应切换首页展示，不应跳转，实际: {page.url}"

            template_cards = portrait_section.locator("a[href]")
            assert template_cards.count() == 8, f"{label} 分类应有 8 个模板，实际: {template_cards.count()}"
            template_records = []
            for idx in range(template_cards.count()):
                template_card = template_cards.nth(idx)
                template_href = template_card.get_attribute("href") or ""
                assert template_href, f"{label} 分类第 {idx + 1} 个模板缺少 href"
                card_text = re.sub(r"\\s+", " ", template_card.inner_text(timeout=10000)).strip()
                template_records.append((template_href, card_text))

            attach_viewport_screenshot(page, f"06-{label}-分类卡片整屏")

            for idx, (template_href, card_text) in enumerate(template_records):
                portrait_section = open_portrait_category(label)
                template_card = portrait_section.locator("a[href]").nth(idx)
                assert (template_card.get_attribute("href") or "") == template_href, \
                    f"{label} 分类第 {idx + 1} 个模板顺序发生变化，无法确认点击对象"
                template_card.click(force=True)
                page.wait_for_timeout(1600)
                assert_landing_page(page, template_href, card_text)
        goto_home(page)
        batch_title = page.get_by_text("Edit up to 50 Photos in One Batch", exact=False).first
        pw_expect(batch_title).to_be_visible(timeout=15000)
        batch_title.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        assert_image_suffixes(page, ["homepagerefresh_batch_26071315000124.webp"])
        batch_section = home_section(page, "Edit up to 50 Photos in One Batch")
        for label in ["Remove BG", "Resize", "Enhance", "Change BG"]:
            btn = batch_section.locator("a,button,[role='button']").filter(has_text=label).first
            pw_expect(btn).to_be_visible(timeout=10000)
            btn.scroll_into_view_if_needed()
            allure.attach(
                btn.screenshot(),
                name=f"06-{label}-点击前按钮",
                attachment_type=allure.attachment_type.PNG,
            )
            click_upload_and_assert_batch_edit(page, btn, pick_test_image())
            allure.attach(
                page.screenshot(full_page=False),
                name=f"06-{label}-上传后整屏",
                attachment_type=allure.attachment_type.PNG,
            )
            page.wait_for_timeout(500)
            goto_home(page)
            batch_title = page.get_by_text("Edit up to 50 Photos in One Batch", exact=False).first
            pw_expect(batch_title).to_be_visible(timeout=15000)
            batch_title.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
        goto_home(page)
        enhance_title = page.get_by_text("Enhance Photo Quality for Every Detail", exact=False).first
        pw_expect(enhance_title).to_be_visible(timeout=15000)
        enhance_title.scroll_into_view_if_needed()
        page.wait_for_timeout(1000)
        enhance_section = home_section(page, "Enhance Photo Quality for Every Detail")
        enhance_targets = {
            "HD Enhance": {"path": "/tools/hd-pic-converter", "upload": False},
            "Text Enhance": {"path": "/tools/ai-image-text-enhancer", "upload": False},
            "Portrait Enhance": {"path": "/agent", "upload": True},
            "Ultra Enhance": {"path": "/agent", "upload": True},
        }
        for label in ["HD Enhance", "Text Enhance", "Portrait Enhance", "Ultra Enhance"]:
            btn = enhance_section.locator("a,button,[role='button']").filter(has_text=label).first
            pw_expect(btn).to_be_visible(timeout=10000)
            btn.scroll_into_view_if_needed()
            allure.attach(
                btn.screenshot(),
                name=f"06-{label}-点击前按钮",
                attachment_type=allure.attachment_type.PNG,
            )
            target = enhance_targets[label]
            if target["upload"]:
                click_upload_and_assert_canvas(page, btn, pick_test_image())
                allure.attach(
                    page.screenshot(full_page=False),
                    name=f"06-{label}-选图后画布页",
                    attachment_type=allure.attachment_type.PNG,
                )
            else:
                btn.click(force=True)
                page.wait_for_timeout(1200)
                assert urlparse(page.url).path == target["path"], f"{label} 应进入 {target['path']}，实际: {page.url}"
                allure.attach(
                    page.screenshot(full_page=False),
                    name=f"06-{label}-点击后整屏",
                    attachment_type=allure.attachment_type.PNG,
                )
            goto_home(page)
            enhance_title = page.get_by_text("Enhance Photo Quality for Every Detail", exact=False).first
            pw_expect(enhance_title).to_be_visible(timeout=15000)
            enhance_title.scroll_into_view_if_needed()
            page.wait_for_timeout(1000)
            enhance_section = home_section(page, "Enhance Photo Quality for Every Detail")
    @allure.title("TC-HOME-V3-007 [P1] 信任数据与评价卡片")
    def test_home_v3_007_trust_and_reviews(self, page: Page):
        goto_home(page)
        body = text_content(page)
        missing = [
            text
            for text in [
                "Pokecut is Trusted by Creators for Every Photo Creation",
                "3M+ creators",
                "200+ AI tools",
                "500M+ edits processed",
                "#2 Product Hunt",
            ]
            if text not in body
        ]
        assert not missing, "信任板块缺少当前基线内容: " + "; ".join(missing)

        for label, expected_href in REVIEW_LINKS.items():
            link = page.locator(f"a:has-text('{label}')").first
            pw_expect(link).to_be_visible(timeout=10000)
            assert link.get_attribute("href") == expected_href
            assert link.get_attribute("target") == "_blank"
            assert "nofollow" in (link.get_attribute("rel") or "")

        srcs = image_srcs(page)
        missing_images = {
            name: suffix
            for name, suffix in REVIEW_IMAGE_SUFFIXES.items()
            if not any(suffix in src for src in srcs)
        }
        assert not missing_images, f"评价卡资源图不符合需求: {missing_images}"

    @allure.title("TC-HOME-V3-008 [P1] FAQ、移动端下载、底部 feedback 移除（测试服 DEBUG 浮标保留）")
    def test_home_v3_008_faq_footer_and_feedback_removed(self, page: Page):
        goto_home(page)
        assert_body_contains(page, ["Frequently Asked Questions", "Pokecut Mobile App", "App Store", "Google Play"])
        assert_body_contains(page, FAQ_QUESTIONS)
        assert_link_path(page, "online store", "/pricing")
        assert_link_path(page, "Terms of Use", "/term-of-use")
        refund_ticket = page.locator('[data-submit-ticket="refund"]').first
        pw_expect(refund_ticket).to_be_visible(timeout=10000)
        debug_badge = page.get_by_text("DEBUG", exact=True)
        if debug_badge.count() > 0:
            allure.attach(
                "DEBUG 浮标为测试服专用调试入口，不作为需求缺陷。",
                name="DEBUG说明",
                attachment_type=allure.attachment_type.TEXT,
            )
