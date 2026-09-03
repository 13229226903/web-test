"""Pokecut 首页多语言回归。"""

import glob
import json
import os
from urllib.parse import urlparse

import allure
import pytest
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect as pw_expect

from conftest import allure_screenshot
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text


BASE_URL = "http://10.17.1.66:3001"

LOCALES = [
    ("en", "English", "/"),
    ("zh", "简体中文", "/zh"),
    ("zh-tw", "繁体中文", "/zh-tw"),
    ("es", "Español", "/es"),
    ("pt", "Português", "/pt"),
    ("ru", "Русский", "/ru"),
    ("id", "Indonesia", "/id"),
    ("th", "ไทย", "/th"),
    ("ja", "日本語", "/ja"),
    ("fr", "Français", "/fr"),
    ("it", "Italiano", "/it"),
    ("vi", "Tiếng Việt", "/vi"),
    ("tr", "Türkçe", "/tr"),
    ("de", "Deutsch", "/de"),
]
LOCALE_IDS = [item[0] for item in LOCALES]

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

TEST_PANEL_LINKS = [
    "/tools/pretty-scale",
    "/tools/ethnicity-guesser-ai",
    "/tools/eye-color-detector",
    "/tools/body-shape-detector",
]

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


def pick_test_image() -> str:
    root = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(root, "*")), key=lambda f: os.path.getsize(f))
    if not imgs:
        raise FileNotFoundError("找不到 test_images")
    return os.path.abspath(imgs[0])


def goto_home(page: Page, path: str):
    page.goto(f"{BASE_URL}{path}", timeout=120000)
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(5000)


def watch_resource_failures(page: Page):
    failed_responses = []
    request_failures = []

    def on_response(response):
        try:
            status = response.status
            if 400 <= status < 600:
                failed_responses.append(
                    {
                        "status": status,
                        "type": response.request.resource_type,
                        "url": response.url,
                    }
                )
        except Exception:
            pass

    def on_request_failed(request):
        try:
            request_failures.append(
                {
                    "type": request.resource_type,
                    "url": request.url,
                    "failure": str(request.failure or ""),
                }
            )
        except Exception:
            pass

    page.on("response", on_response)
    page.on("requestfailed", on_request_failed)

    def stop():
        try:
            page.remove_listener("response", on_response)
            page.remove_listener("requestfailed", on_request_failed)
        except Exception:
            pass

    return failed_responses, request_failures, stop


def assert_first_viewport_images_loaded(page: Page, failed_responses: list, request_failures: list, locale: str):
    ignored_hosts = [
        "google",
        "facebook",
        "analytics",
        "gtm",
        "pixel",
        "clarity",
        "hotjar",
        "doubleclick",
        "googletagmanager",
    ]

    try:
        page.wait_for_function(
            """() => {
                const visibleInViewport = (img) => {
                    const rect = img.getBoundingClientRect();
                    const style = window.getComputedStyle(img);
                    return rect.width >= 16 && rect.height >= 16
                        && rect.bottom > 0 && rect.right > 0
                        && rect.top < window.innerHeight && rect.left < window.innerWidth
                        && style.display !== 'none'
                        && style.visibility !== 'hidden'
                        && style.opacity !== '0';
                };
                return Array.from(document.images)
                    .filter(visibleInViewport)
                    .every((img) => img.complete);
            }""",
            timeout=8000,
        )
    except PlaywrightTimeoutError:
        pass

    viewport_resources = page.evaluate(
        """() => {
            const urls = [];
            const visibleInViewport = (el) => {
                const rect = el.getBoundingClientRect();
                const style = window.getComputedStyle(el);
                return rect.width >= 16 && rect.height >= 16
                    && rect.bottom > 0 && rect.right > 0
                    && rect.top < window.innerHeight && rect.left < window.innerWidth
                    && style.display !== 'none'
                    && style.visibility !== 'hidden'
                    && style.opacity !== '0';
            };
            document.querySelectorAll('img, [style]').forEach((el) => {
                if (!visibleInViewport(el)) return;
                if (el.currentSrc) urls.push(el.currentSrc);
                if (el.src) urls.push(el.src);
                const bg = window.getComputedStyle(el).backgroundImage || '';
                bg.replace(/url\\(["']?([^"')]+)["']?\\)/g, (_, url) => {
                    urls.push(new URL(url, window.location.href).href);
                    return '';
                });
            });
            return Array.from(new Set(urls.filter(Boolean)));
        }"""
    )

    broken_images = page.evaluate(
        """() => {
            const visibleInViewport = (img) => {
                const rect = img.getBoundingClientRect();
                const style = window.getComputedStyle(img);
                return rect.width >= 16 && rect.height >= 16
                    && rect.bottom > 0 && rect.right > 0
                    && rect.top < window.innerHeight && rect.left < window.innerWidth
                    && style.display !== 'none'
                    && style.visibility !== 'hidden'
                    && style.opacity !== '0';
            };
            return Array.from(document.images)
                .filter(visibleInViewport)
                .filter((img) => !img.complete || img.naturalWidth === 0 || img.naturalHeight === 0)
                .map((img) => {
                    const rect = img.getBoundingClientRect();
                    return {
                        src: img.currentSrc || img.src || img.getAttribute('data-src') || '',
                        alt: img.alt || '',
                        complete: img.complete,
                        naturalWidth: img.naturalWidth,
                        naturalHeight: img.naturalHeight,
                        rect: {
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        }
                    };
                });
        }"""
    )

    image_response_failures = [
        item
        for item in failed_responses
        if item.get("type") == "image"
        and not any(host in item.get("url", "").lower() for host in ignored_hosts)
    ]
    image_request_failures = [
        item
        for item in request_failures
        if item.get("type") == "image"
        and not any(host in item.get("url", "").lower() for host in ignored_hosts)
    ]
    viewport_resource_paths = {
        urlparse(url).path
        for url in viewport_resources
        if urlparse(url).path
    }
    failed_viewport_image_responses = [
        item
        for item in image_response_failures
        if urlparse(item.get("url", "")).path in viewport_resource_paths
    ]
    failed_viewport_image_requests = [
        item
        for item in image_request_failures
        if urlparse(item.get("url", "")).path in viewport_resource_paths
    ]
    detail = {
        "locale": locale,
        "first_viewport_resources": viewport_resources,
        "broken_first_viewport_images": broken_images,
        "failed_first_viewport_image_responses": failed_viewport_image_responses,
        "failed_first_viewport_image_requests": failed_viewport_image_requests,
        "failed_image_responses": image_response_failures,
        "failed_image_requests": image_request_failures,
    }
    allure.attach(
        json.dumps(detail, ensure_ascii=False, indent=2),
        name=f"i18n-01-{locale}-首屏图片资源检查",
        attachment_type=allure.attachment_type.JSON,
    )

    if broken_images:
        allure.attach(
            page.screenshot(full_page=False),
            name=f"i18n-01-{locale}-首屏裂图",
            attachment_type=allure.attachment_type.PNG,
        )

    assert not broken_images, f"首屏存在未正常加载的可见图片: {broken_images}"
    assert not failed_viewport_image_responses, f"首屏图片资源返回 4xx/5xx: {failed_viewport_image_responses}"
    assert not failed_viewport_image_requests, f"首屏图片资源请求失败: {failed_viewport_image_requests}"


def section(page: Page, index: int):
    return page.locator("section").nth(index)


def localized_path(locale: str, path: str) -> str:
    return path if locale == "en" else f"/{locale}{path}"


def visible_controls(locator):
    return locator.locator("button, a, [role='button']")


def click_with_optional_upload(page: Page, control, expected_path: str, test_img: str | None = None, expect_upload: bool = False):
    control.scroll_into_view_if_needed()
    chooser_opened = False
    try:
        with page.expect_file_chooser(timeout=4000) as fc_info:
            control.click(force=True)
        chooser_opened = True
        if test_img:
            fc_info.value.set_files(test_img)
    except PlaywrightTimeoutError:
        pass

    assert chooser_opened == expect_upload, (
        f"点击行为与预期不符，expected_upload={expect_upload}, "
        f"actual_upload={chooser_opened}, url={page.url}"
    )
    page.wait_for_function(
        f"() => window.location.pathname === '{expected_path}'",
        timeout=30000,
    )
    assert urlparse(page.url).path == expected_path, f"点击后应进入 {expected_path}，实际: {page.url}"


def assert_top_layout(page: Page):
    header_items = page.evaluate(
        """() => {
            const items = [];
            const seen = new Set();
            document.querySelectorAll('a, button').forEach((el) => {
                const r = el.getBoundingClientRect();
                const text = (el.innerText || el.textContent || el.getAttribute('aria-label') || '').replace(/\\s+/g, ' ').trim();
                if (!text || r.width <= 0 || r.height <= 0) return;
                if (r.top < 5 || r.top > 150) return;
                const key = `${text}|${Math.round(r.left)}`;
                if (seen.has(key)) return;
                seen.add(key);
                items.push({text, x: Math.round(r.left), y: Math.round(r.top)});
            });
            return items.sort((a, b) => a.x - b.x);
        }"""
    )
    assert len(header_items) >= 5, f"顶部栏可见入口不足: {header_items}"
    left = header_items[:3]
    right = header_items[-2:]
    assert left[0]["x"] < left[1]["x"] < left[2]["x"], f"顶部左侧入口顺序异常: {header_items}"
    assert right[0]["x"] < right[1]["x"], f"顶部右侧入口顺序异常: {header_items}"


def assert_hero_controls(page: Page):
    for selector in [
        "button[aria-label='Upload image']",
        "button:has-text('Pokecut Pro')",
        "button[aria-label='Prompt settings']",
        "button[aria-label='Generate']",
    ]:
        pw_expect(page.locator(selector).first).to_be_visible(timeout=10000)


def assert_model_order(page: Page):
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


def assert_test_panel(page: Page, locale: str):
    panel = section(page, 11)
    panel.scroll_into_view_if_needed()
    links = panel.locator("a[href]")
    assert links.count() == 4, f"Test 板块链接数量不对: {links.count()}"
    for idx, expected_path in enumerate(TEST_PANEL_LINKS):
        href = links.nth(idx).get_attribute("href") or ""
        assert urlparse(href).path == expected_path, f"Test 板块第 {idx + 1} 个链接应为 {expected_path}，实际 {href}"


def assert_review_cards(page: Page):
    review_section = section(page, 16)
    review_section.scroll_into_view_if_needed()
    for label, expected_href in REVIEW_LINKS.items():
        link = review_section.locator(f"a:has-text('{label}')").first
        pw_expect(link).to_be_visible(timeout=10000)
        assert link.get_attribute("href") == expected_href
        assert link.get_attribute("target") == "_blank"
        assert "nofollow" in (link.get_attribute("rel") or "")

    srcs = page.evaluate(
        """() => {
            const values = [];
            document.querySelectorAll('img, source, [style]').forEach((el) => {
                const attrs = el.attributes || [];
                for (const attr of attrs) {
                    if (['src', 'srcset', 'data-src', 'data-srcset'].includes(attr.name)) values.push(attr.value);
                }
                const bg = window.getComputedStyle(el).backgroundImage;
                if (bg && bg !== 'none') values.push(bg);
                if (el.currentSrc) values.push(el.currentSrc);
            });
            return values.filter(Boolean);
        }"""
    )
    missing_images = {
        name: suffix
        for name, suffix in REVIEW_IMAGE_SUFFIXES.items()
        if not any(suffix in src for src in srcs)
    }
    assert not missing_images, f"评价卡资源图不符合需求: {missing_images}"


def assert_footer(page: Page, locale: str):
    copyright = page.get_by_text("Copyright", exact=False).first
    pw_expect(copyright).to_be_visible(timeout=10000)
    assert page.locator(f"a[href='{localized_path(locale, '/pricing')}']").count() > 0, "页脚缺少 /pricing"
    assert page.locator(f"a[href='{localized_path(locale, '/term-of-use')}']").count() > 0, "页脚缺少 /term-of-use"
    assert page.locator('[data-submit-ticket="refund"]').count() > 0, "页脚缺少退款工单入口"


def assert_homepage_text_review(page: Page, locale: str, locale_name: str):
    """首页多语言 AI 文案审查必须与用例状态一致。"""
    prompt = (
        f"这是 Pokecut 首页的 {locale_name}（语言代码: {locale}）页面截图。"
        "请检查主要页面文案是否符合当前语言、是否有乱码、未翻译 key、明显截断或错误语言混入。"
        "只检查首页主体内容、导航、区块标题、CTA 和说明文案。"
        "以下内容属于预期噪声或产品专有名词，必须忽略，不要因此判 fail："
        "1) 测试服 DEBUG 浮标；"
        "2) 浏览器语言提示条，例如 'You are browsing ... web pages' 和 'Change to English'；"
        "3) 品牌名、用户姓名、Product Hunt、模型名和英文专有名词，例如 Pokecut、ChatGPT、Seedream、Nano Banana；"
        "4) Prompt 组件的系统控件文案，例如 Upload image、Prompt settings、Generate；"
        "5) $1 USD 倒计时优惠文案及数字倒计时。"
        "如果排除上述噪声后，主要页面文案符合预期语言且无乱码/未翻译 key，则返回 pass；"
        "否则返回 fail。"
    )
    result = check_page_text(
        page,
        locale=locale,
        locale_name=locale_name,
        fail_on_error=False,
        custom_prompt=prompt,
    )
    assert result.get("verdict") == "pass", (
        f"AI 文案审查未通过 [{locale_name}]: "
        f"{result.get('reason', result)}"
    )


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("首页 v3.0 i18n")
class TestHomePageI18n:

    @pytest.mark.parametrize("locale,locale_name,path", LOCALES, ids=LOCALE_IDS)
    def test_home_i18n_001_header_hero_models(self, page: Page, locale, locale_name, path):
        allure.dynamic.story(locale_name)
        allure.dynamic.title(f"[P0] [{locale_name}] 首页首屏与模型区")
        failed_responses, request_failures, stop_resource_watch = watch_resource_failures(page)
        goto_home(page, path)
        assert_first_viewport_images_loaded(page, failed_responses, request_failures, locale)
        stop_resource_watch()
        verify_seo_links(page, BASE_URL, path, max_links=10)
        assert_homepage_text_review(page, locale, locale_name)
        allure_screenshot(page, f"i18n-01-{locale}-首屏")

        assert_top_layout(page)
        assert_hero_controls(page)

        hero_cta = section(page, 6).locator("button").nth(0)
        file_chooser_opened = False
        try:
            with page.expect_file_chooser(timeout=1000):
                hero_cta.click(force=True)
            file_chooser_opened = True
        except PlaywrightTimeoutError:
            pass
        assert not file_chooser_opened, "首屏主按钮不应唤起系统上传弹窗"
        page.wait_for_timeout(2000)
        assert urlparse(page.url).path == localized_path(locale, "/agent"), f"首屏主按钮应直接跳转 /agent，实际: {page.url}"
        page.go_back()
        page.wait_for_timeout(3000)

        assert_model_order(page)

    @pytest.mark.parametrize("locale,locale_name,path", LOCALES, ids=LOCALE_IDS)
    def test_home_i18n_002_popular_templates_test_panel(self, page: Page, locale, locale_name, path):
        allure.dynamic.story(locale_name)
        allure.dynamic.title(f"[P0] [{locale_name}] 热门功能、模板与 Test 板块")
        goto_home(page, path)

        popular = section(page, 8)
        popular.scroll_into_view_if_needed()
        buttons = visible_controls(popular)
        assert buttons.count() >= 4, f"热门功能区按钮数量不足: {buttons.count()}"

        test_img = pick_test_image()
        popular_flow = [
            (0, "/agent", True),
            (1, "/tools/ai-image-text-enhancer", False),
            (2, "/agent", True),
            (3, "/tools", False),
        ]
        for idx, expected_path, expect_upload in popular_flow:
            click_with_optional_upload(
                page,
                buttons.nth(idx),
                expected_path if idx == 1 else localized_path(locale, expected_path),
                test_img=test_img if expect_upload else None,
                expect_upload=expect_upload,
            )
            if idx != 3:
                goto_home(page, path)
                popular = section(page, 8)
                popular.scroll_into_view_if_needed()
                buttons = visible_controls(popular)

        goto_home(page, path)
        templates = section(page, 10)
        templates.scroll_into_view_if_needed()
        pw_expect(templates).to_be_visible(timeout=15000)
        cards = templates.locator("div.cursor-pointer")
        assert cards.count() == 24, f"模板区卡片数量异常: {cards.count()}"
        see_more = templates.locator("button").first
        pw_expect(see_more).to_be_visible(timeout=10000)
        see_more.click(force=True)
        page.wait_for_timeout(1500)
        assert urlparse(page.url).path == localized_path(locale, "/create"), f"查看更多作品应进入 /create，实际: {page.url}"

        goto_home(page, path)
        assert_test_panel(page, locale)
        allure_screenshot(page, f"i18n-02-{locale}-test-panel")

        # 再做一次文本审查，确保多语言正文没有乱码或未翻译 key。
        page.wait_for_timeout(500)
        assert_homepage_text_review(page, locale, locale_name)

    @pytest.mark.parametrize("locale,locale_name,path", LOCALES, ids=LOCALE_IDS)
    def test_home_i18n_003_portrait_batch_enhance_footer(self, page: Page, locale, locale_name, path):
        allure.dynamic.story(locale_name)
        allure.dynamic.title(f"[P0] [{locale_name}] 人像、Batch、Enhance、底部")
        goto_home(page, path)
        test_img = pick_test_image()

        portrait = section(page, 12)
        portrait.scroll_into_view_if_needed()
        pw_expect(portrait).to_be_visible(timeout=15000)
        category_buttons = portrait.locator("button")
        assert category_buttons.count() == 4, f"人像分类按钮数量异常: {category_buttons.count()}"
        for idx in range(4):
            category_buttons.nth(idx).click(force=True)
            page.wait_for_timeout(1000)
            cards = portrait.locator("a[href]")
            assert cards.count() == 8, f"人像分类模板数量异常: {cards.count()}"
            hrefs = [cards.nth(i).get_attribute("href") or "" for i in range(cards.count())]
            assert len(set(hrefs)) == 8, f"人像分类模板 href 重复: {hrefs}"
            for card_idx in [0, 7]:
                href = cards.nth(card_idx).get_attribute("href") or ""
                cards.nth(card_idx).click(force=True)
                page.wait_for_timeout(1500)
                assert urlparse(page.url).path == urlparse(href).path, f"模板点击后路径不对，实际: {page.url}"
                page.go_back()
                page.wait_for_timeout(2500)
                portrait.scroll_into_view_if_needed()
                category_buttons = portrait.locator("button")
                category_buttons.nth(idx).click(force=True)
                page.wait_for_timeout(1000)
        allure_screenshot(page, f"i18n-03-{locale}-portrait")

        goto_home(page, path)
        batch = section(page, 13)
        batch.scroll_into_view_if_needed()
        batch_buttons = batch.locator("button")
        assert batch_buttons.count() == 4, f"Batch 按钮数量异常: {batch_buttons.count()}"
        click_with_optional_upload(page, batch_buttons.nth(0), localized_path(locale, "/batch-edit/edit"), test_img=test_img, expect_upload=True)
        goto_home(page, path)
        batch = section(page, 13)
        batch.scroll_into_view_if_needed()
        batch_buttons = batch.locator("button")
        click_with_optional_upload(page, batch_buttons.nth(1), localized_path(locale, "/batch-edit/edit"), test_img=test_img, expect_upload=True)
        goto_home(page, path)
        batch = section(page, 13)
        batch.scroll_into_view_if_needed()
        batch_buttons = batch.locator("button")
        click_with_optional_upload(page, batch_buttons.nth(2), localized_path(locale, "/batch-edit/edit"), test_img=test_img, expect_upload=True)
        goto_home(page, path)
        batch = section(page, 13)
        batch.scroll_into_view_if_needed()
        batch_buttons = batch.locator("button")
        click_with_optional_upload(page, batch_buttons.nth(3), localized_path(locale, "/batch-edit/edit"), test_img=test_img, expect_upload=True)

        goto_home(page, path)
        enhance = section(page, 14)
        enhance.scroll_into_view_if_needed()
        enhance_buttons = enhance.locator("button")
        assert enhance_buttons.count() == 4, f"Enhance 按钮数量异常: {enhance_buttons.count()}"
        click_with_optional_upload(page, enhance_buttons.nth(0), "/tools/hd-pic-converter", expect_upload=False)
        goto_home(page, path)
        enhance = section(page, 14)
        enhance.scroll_into_view_if_needed()
        enhance_buttons = enhance.locator("button")
        click_with_optional_upload(page, enhance_buttons.nth(1), "/tools/ai-image-text-enhancer", expect_upload=False)
        goto_home(page, path)
        enhance = section(page, 14)
        enhance.scroll_into_view_if_needed()
        enhance_buttons = enhance.locator("button")
        click_with_optional_upload(page, enhance_buttons.nth(2), localized_path(locale, "/agent"), test_img=test_img, expect_upload=True)
        goto_home(page, path)
        enhance = section(page, 14)
        enhance.scroll_into_view_if_needed()
        enhance_buttons = enhance.locator("button")
        click_with_optional_upload(page, enhance_buttons.nth(3), localized_path(locale, "/agent"), test_img=test_img, expect_upload=True)
        allure_screenshot(page, f"i18n-03-{locale}-enhance")

        goto_home(page, path)
        assert_review_cards(page)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        assert_footer(page, locale)
        assert_homepage_text_review(page, locale, locale_name)
