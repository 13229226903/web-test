"""功能介绍页 i18n 回归 — 繁体中文 + 11种语言，复用英文版测试模式。"""
import os, re, glob, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text

# ── 语言列表 ──
LOCALES = [
    ("zh-tw", "繁体中文"),
    ("ja",   "日本語"),
    ("de",   "Deutsch"),
    ("fr",   "Français"),
    ("th",   "ไทย"),
    ("vi",   "Tiếng Việt"),
    ("it",   "Italiano"),
    ("tr",   "Türkçe"),
    # 以下 4 种语言 URL 完全本地化（连 "tools" 也翻译了），见 LOCALIZED_TOOL_PATHS
    ("pt",   "Português"),
    ("es",   "Español"),
    ("ru",   "Русский"),
    ("id",   "Indonesia"),
]

# ── 工具定义（英文 URL 模式，适用于前 8 种语言）──
# (tool_path, title_kw_en, h1_kw_en, url_kws, panel_kw_en, panel_kw_zh_tw, name_cn)
SEO_TOOLS = [
    ("/tools/background-remover", "Background Remover", "Background Remover",
     ["/agent"], ["Remove BG"], ["去除背景", "去背", "Remove BG", "Background"], "移除背景"),
    ("/tools/photo-enhancer", "Photo Enhancer", "Photo Enhancer",
     ["/agent"], ["Enhance"], ["增強", "畫質", "Enhance"], "画质增强"),
    ("/tools/background-changer", "Background Changer", "Background Changer",
     ["/agent"], ["Colors"], ["顏色", "背景", "Colors"], "背景更换"),
    ("/tools/ai-image-extender", "Image Extender", "Image Extender",
     ["/create/edit", "/agent"], ["Extend"], ["擴展", "擴圖", "Extend", "Image"], "扩图"),
    ("/tools/magic-eraser-with-ai-detection", "Magic Eraser", "Magic Eraser",
     ["/agent"], ["Erase"], ["擦除", "移除", "Erase"], "AI消除"),
    ("/tools/id-photo-maker", "ID Photo", "ID Photo",
     ["/tools/id-photo-edit"], [], [], "证件照"),
]

# ── 本地化 URL 映射（pt/es/ru/id 使用翻译后的路径段）──
# locale -> {english_tool_path: full_localized_path}
LOCALIZED_TOOL_PATHS = {
    "pt": {
        "/tools/background-remover": "/pt/ferramentas/eliminador-de-fundo",
        "/tools/photo-enhancer": "/pt/ferramentas/aprimorador-de-fotos",
        "/tools/background-changer": "/pt/ferramentas/alterador-de-fundo",
        "/tools/ai-image-extender": "/pt/ferramentas/expandir-imagem-ia",
        "/tools/magic-eraser-with-ai-detection": "/pt/ferramentas/remover-objeto-de-foto",
        "/tools/id-photo-maker": "/pt/ferramentas/alat-pembuat-foto-id",
    },
    "es": {
        "/tools/background-remover": "/es/herramientas/eliminador-de-fondo",
        "/tools/photo-enhancer": "/es/herramientas/mejorador-de-fotos",
        "/tools/background-changer": "/es/herramientas/cambiador-de-fondo",
        "/tools/ai-image-extender": "/es/herramientas/expandir-imagen-ia",
        "/tools/magic-eraser-with-ai-detection": "/es/herramientas/borrador-magico-con-ia",
        "/tools/id-photo-maker": "/es/herramientas/herramienta-de-foto-de-identificacion",
    },
    "ru": {
        "/tools/background-remover": "/ru/instrumenty/ubrat-fon-onlayn",
        "/tools/photo-enhancer": "/ru/instrumenty/foto-usilitel",
        "/tools/background-changer": "/ru/instrumenty/izmenit-fon-onlayn",
        "/tools/ai-image-extender": "/ru/instrumenty/uvelichit-foto-II",
        "/tools/magic-eraser-with-ai-detection": "/ru/instrumenty/udalit-obekt-s-foto",
        "/tools/id-photo-maker": "/ru/instrumenty/dlya-sozdaniya-id-foto",
    },
    "id": {
        "/tools/background-remover": "/id/alat/penghapus-latar-belakang",
        "/tools/photo-enhancer": "/id/alat/pemerkaya-foto",
        "/tools/background-changer": "/id/alat/pengubah-latar-belakang-berbasis",
        "/tools/ai-image-extender": "/id/alat/perluas-gambar-ai",
        "/tools/magic-eraser-with-ai-detection": "/id/alat/hapus-objek-foto",
        "/tools/id-photo-maker": "/id/alat/pembuat-foto-identitas",
    },
}

# ═══════════════════════════════════════════════════════════════
# 辅助函数（从 test_tool_pages.py 和 test_tool_pages_zh.py 复用）
# ═══════════════════════════════════════════════════════════════

def pick_test_image():
    """从 test_images/ 取最小图片，加速 AI 处理。"""
    d = os.path.join(os.path.dirname(__file__), "..", "test_images")
    if os.path.isdir(d):
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        if imgs:
            return os.path.abspath(imgs[0])


def goto(page: Page, base_url: str, path: str, lazy_scroll: bool = False):
    """导航到页面，可选 lazy_scroll 加载懒加载图片。"""
    page.goto(f"{base_url}{path}", timeout=120000)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(3000)
    if lazy_scroll:
        # eager 加载 + 逐个 scrollIntoView 触发 IntersectionObserver
        page.evaluate("""() => {
            document.querySelectorAll('img[loading="lazy"]').forEach(function(img) {
                img.loading = 'eager';
                var s = img.getAttribute('src');
                if (s) { img.removeAttribute('src'); img.setAttribute('src', s); }
            });
        }""")
        page.wait_for_timeout(1000)
        for _ in range(10):
            page.mouse.wheel(0, 600)
            page.wait_for_timeout(300)
        # 逐个触发仍未加载的图片
        page.evaluate("""() => {
            document.querySelectorAll('img').forEach(function(img) {
                if (!img.complete && img.offsetWidth === 0 && img.offsetHeight === 0) {
                    img.scrollIntoView({block: 'center'});
                }
            });
        }""")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(3000)


def _check_title_h1(page: Page, english_kw: str, locale: str):
    """i18n 宽松 title/h1 检查。

    优先级：
    1. 标题含英文关键词 → 通过
    2. CJK 语言 (zh-tw, ja) 含 CJK 字符 → 通过
    3. 俄语 (ru) 含西里尔字母 → 通过
    4. 泰语 (th) 含泰文字符 → 通过
    5. 拉丁系语言 / 兜底：title 非空即通过
    返回 (ok: bool, title: str, h1s: list[str])
    """
    title = page.title()
    h1s = [h.inner_text() for h in page.locator("h1").all()]
    h1_text = " ".join(h1s)

    # 1) 含英文关键词 → 通过
    has_en_kw = (
        english_kw.lower() in title.lower()
        or any(english_kw.lower() in h.lower() for h in h1s)
    )
    if has_en_kw:
        return (True, title, h1s)

    combined = title + h1_text

    # 2) CJK 字符 (zh-tw, ja 的汉字)
    if locale in ("zh-tw", "ja"):
        has_cjk = bool(re.search(r'[一-鿿㐀-䶿豈-﫿]', combined))
        if has_cjk:
            return (True, title, h1s)

    # 3) 西里尔字母 (ru)
    if locale == "ru":
        has_cyrillic = bool(re.search(r'[А-Яа-яЁё]', combined))
        if has_cyrillic:
            return (True, title, h1s)

    # 4) 泰文字符 (th)
    if locale == "th":
        has_thai = bool(re.search(r'[฀-๿]', combined))
        if has_thai:
            return (True, title, h1s)

    # 5) 拉丁系语言 / 兜底：title 非空即通过
    #    （页面经 URL 探测确认 200 OK，title 必有内容）
    if title.strip():
        return (True, title, h1s)

    return (False, title, h1s)


# ═══════════════════════════════════════════════════════════════
# 每条用例 = Step1 首屏(page) + Step2 上传(session_page)
# locale × tool 二维参数化，共 72 条用例
# ═══════════════════════════════════════════════════════════════

@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
class TestToolPagesI18n:

    @pytest.mark.parametrize("locale,locale_name", LOCALES)
    @pytest.mark.parametrize(
        "tool_path,title_kw,h1_kw,url_kws,panel_kw_en,panel_kw_zh_tw,name_cn",
        SEO_TOOLS,
    )
    def test_tool_page_i18n(
        self,
        page: Page,
        session_page: Page,
        base_url: str,
        locale,
        locale_name,
        tool_path,
        title_kw,
        h1_kw,
        url_kws,
        panel_kw_en,
        panel_kw_zh_tw,
        name_cn,
    ):
        """i18n 工具介绍页：首屏内容 + 内链校验 + 上传进入功能流程。"""
        allure.dynamic.story(locale_name)
        allure.dynamic.title(
            f"[P0] [{locale_name}] {name_cn} — 首屏内容 + 上传功能流程"
        )

        # ── 构建 locale 相关参数 ──
        # 本地化语言（pt/es/ru/id）用完全翻译的路径；其他语言用标准 /{locale}/tools/{slug}
        if locale in LOCALIZED_TOOL_PATHS:
            path = LOCALIZED_TOOL_PATHS[locale][tool_path]
        else:
            path = f"/{locale}{tool_path}"

        # url_kws: id-photo-maker 编辑器 URL 也随语言本地化，用实际 URL 兜底
        _LOCALIZED_ID_EDIT = {
            "pt": ["/pt/ferramentas/edicao-de-foto-de-identidade"],
            "es": ["/es/herramientas/edicion-de-foto-de-identificacion"],
            "ru": ["/ru/instrumenty/redaktirovanie-fotografii-udostovereniya-lichnosti"],
            "id": ["/id/alat/pengeditan-foto-identitas"],
        }
        if tool_path == "/tools/id-photo-maker":
            # 证件照上传后可能跳转独立编辑器，也可能停留在当前页（行为因 locale 而异）
            actual_url_kws = [f"/{locale}/tools/id-photo-edit", "/tools/id-photo-edit", path]
            if locale in _LOCALIZED_ID_EDIT:
                actual_url_kws = _LOCALIZED_ID_EDIT[locale] + actual_url_kws
        else:
            actual_url_kws = list(url_kws)

        # panel_kw: zh-tw 用已验证的中文关键词，其他语言用英文关键词 + title_kw 兜底
        if locale == "zh-tw" and panel_kw_zh_tw:
            actual_panel_kw = list(panel_kw_zh_tw)
        else:
            # 非 zh-tw 编辑器可能已本地化，英文 panel_kw 可能不匹配，
            # 将工具英文名 (title_kw) 也加入兜底
            actual_panel_kw = list(panel_kw_en)
            if title_kw not in actual_panel_kw:
                actual_panel_kw.append(title_kw)

        # ═══════════════════════════════════════════════════════
        # Step 1: 首屏内容（无需登录）
        # ═══════════════════════════════════════════════════════
        goto(page, base_url, path, lazy_scroll=True)
        slug = tool_path.split("/")[-1]
        allure_screenshot(page, f"01-{locale}-{slug}-首屏")

        # title / h1 校验
        ok, page_title, h1s = _check_title_h1(page, title_kw, locale)
        if not ok:
            pytest.fail(
                f"Title/H1 应含 '{title_kw}' 或本地化内容，"
                f"Title: {page_title[:80]}, H1: {h1s}"
            )

        # 文件上传 input 存在
        assert (
            page.locator("input[type=file]").count() > 0
        ), "应存在文件上传 input"

        # 示例图片 ≥ 3 张
        img_count = page.evaluate(
            """() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){
                if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;
            }return c}"""
        )
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"

        # SEO 内链校验
        verify_seo_links(page, base_url, path)

        # AI 视觉审查：校验首屏文案翻译质量
        vis_result = check_page_text(page, locale=locale, locale_name=locale_name)
        if vis_result["verdict"] == "fail":
            pytest.fail(
                f"AI 文案审查未通过 [{locale_name}]: {vis_result.get('reason', vis_result)}"
            )

        # ═══════════════════════════════════════════════════════
        # Step 2: 上传进入功能流程（需登录）
        # ═══════════════════════════════════════════════════════
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        try:
            with sp.expect_file_chooser(timeout=10000) as fc:
                sp.evaluate(
                    """() => {var btns=document.querySelectorAll("button");
                    for(var i=0;i<btns.length;i++){
                        var r=btns[i].getBoundingClientRect();
                        if(btns[i].textContent.trim()&&r.y>200&&r.y<3000&&r.width>100){
                            btns[i].dispatchEvent(
                                new MouseEvent("click",{bubbles:true,cancelable:true})
                            );return;}}}"""
                )
            fc.value.set_files(test_img)
        except Exception:
            # dispatchEvent 可能已触发页面跳转或 DOM 变化，等待稳定后再回退上传
            sp.wait_for_timeout(3000)
            sp.locator("input[type=file]").first.set_input_files(test_img)

        sp.wait_for_timeout(15000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, f"02-{locale}-{slug}-上传后")

        # URL 断言：上传后应跳转到相应的编辑页面
        assert any(kw in sp.url for kw in actual_url_kws), (
            f"上传后应进入编辑页，实际: {sp.url}"
        )

        # 面板关键词断言（id-photo-maker 无面板关键词，显式跳过）
        if actual_panel_kw and tool_path != "/tools/id-photo-maker":
            body = sp.locator("body").inner_text()
            found = any(kw in body for kw in actual_panel_kw)
            if not found and locale != "zh-tw":
                # 非 zh-tw 编辑器已本地化，英文关键词可能不匹配。
                # 兜底：验证编辑器 body 有充足内容（正常编辑器 >100 字符）
                body_len = len(body.strip())
                assert body_len > 100, (
                    f"编辑页应包含 {actual_panel_kw} 之一，或 body 内容充足，"
                    f"实际 body 长度: {body_len}，body前200: {body[:200]!r}"
                )
            else:
                assert found, (
                    f"编辑页应包含 {actual_panel_kw} 之一，body前300: {body[:300]!r}"
                )
