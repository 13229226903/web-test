"""功能介绍页回归（中文版 /zh/） — 复用英文版逻辑，URL 前缀 /zh/，报告同级。"""
import os, glob, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay, visual_assert
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text

ZH = "/zh"

# ── 参数化 PAGES（与原版一致，加 /zh/ 前缀；change-passport-to-blue-background /zh/ 版 404，已排除）──
PAGES = [
    pytest.param(f"{ZH}/tools/background-remover", "Background Remover", "Background Remover",
                 ["/agent"], ["去除背景", "移除背景"], "移除背景", id="background-remover"),
    pytest.param(f"{ZH}/tools/photo-enhancer", "Photo Enhancer", "Photo Enhancer",
                 ["/agent"], ["画质增强", "增强"], "画质增强", id="photo-enhancer"),
    pytest.param(f"{ZH}/tools/background-changer", "Background Changer", "Background Changer",
                 ["/agent"], ["颜色", "色彩"], "背景更换", id="background-changer"),
    pytest.param(f"{ZH}/tools/ai-image-extender", "Image Extender", "Image Extender",
                 ["/create/edit"], ["扩展", "扩图"], "扩图", id="ai-image-extender"),
    pytest.param(f"{ZH}/tools/magic-eraser-with-ai-detection", "Magic Eraser", "Magic Eraser",
                 ["/agent"], ["擦除", "消除", "抹除"], "AI消除", id="magic-eraser"),
    pytest.param(f"{ZH}/tools/blur-background", "Background Blur", "Background Blur",
                 ["/agent"], ["模糊", "虚化"], "背景模糊", id="blur-background"),
    pytest.param(f"{ZH}/tools/id-photo-maker", "ID Photo", "ID Photo",
                 [f"{ZH}/tools/id-photo-edit"], [], "证件照", id="id-photo-maker"),
]


def pick_test_image():
    d = os.path.join(os.path.dirname(__file__), "..", "test_images")
    if os.path.isdir(d):
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        if imgs: return os.path.abspath(imgs[0])


def _check_title_h1(page, kw: str):
    """中文版页面 title/h1 可能是中文：含英文关键词或含 CJK 字符即通过。"""
    import re as _re
    page_title = page.title()
    h1s = [h.inner_text() for h in page.locator("h1").all()]
    h1_text = " ".join(h1s)
    has_kw = kw.lower() in page_title.lower() or any(kw.lower() in h.lower() for h in h1s)
    has_cjk = bool(_re.search(r'[一-鿿]', page_title + h1_text))
    if not has_kw and not has_cjk:
        return (False, page_title, h1s)
    return (True, page_title, h1s)


def goto(page: Page, base_url: str, path: str, lazy_scroll: bool = False):
    page.goto(f"{base_url}{path}", timeout=120000)
    try: page.wait_for_load_state("networkidle", timeout=30000)
    except Exception: pass
    page.wait_for_timeout(3000)
    if lazy_scroll:
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


# ═══════════════════════════════════════════════════════════════
# 与英文版同级报告：@allure.epic("SEO回归") / @allure.feature("功能介绍页")
# ═══════════════════════════════════════════════════════════════

@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
class TestToolPagesZH:

    @pytest.mark.parametrize("path,title_kw,h1_kw,url_kws,panel_kw,name_cn", PAGES)
    def test_tool_page_zh(self, page: Page, session_page: Page, base_url: str,
                           path, title_kw, h1_kw, url_kws, panel_kw, name_cn):
        allure.dynamic.title(f"[P0] [中文] {name_cn} — 首屏内容 + 上传功能流程")
        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        slug = path.split('/')[-1]
        allure_screenshot(page, f"01-zh-{slug}-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        # 中文版 title/h1 可能是中文，用包含匹配+宽限：含英文关键词或含中文即通过
        page_title = page.title()
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        h1_text = " ".join(h1s)
        has_title_kw = title_kw.lower() in page_title.lower()
        has_h1_kw = any(title_kw.lower() in h.lower() for h in h1s)
        # 含中文字符 (CJK) = 中文版页面，跳过英文关键词严格检查
        has_cjk = bool(__import__('re').search(r'[一-鿿]', page_title + h1_text))
        if not has_title_kw and not has_cjk:
            pytest.fail(f"Title 应含 '{title_kw}' 或有中文内容，实际: {page_title[:60]}")
        if not has_h1_kw and not has_cjk:
            pytest.fail(f"H1 应含 '{title_kw}' 或有中文内容，实际: {h1s}")
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 上传进入功能流程（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        try:
            with sp.expect_file_chooser(timeout=10000) as fc:
                sp.evaluate("""() => {var btns=document.querySelectorAll("button");
                    for(var i=0;i<btns.length;i++){var r=btns[i].getBoundingClientRect();
                    if(btns[i].textContent.trim()&&r.y>200&&r.y<1500&&r.width>100){btns[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            fc.value.set_files(test_img)
        except Exception:
            sp.locator("input[type=file]").first.set_input_files(test_img)
        sp.wait_for_timeout(15000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, f"02-zh-{slug}-上传后")

        assert any(kw in sp.url for kw in url_kws), f"上传后应进入编辑页，实际: {sp.url}"

        body = sp.locator("body").inner_text()
        if panel_kw:
            assert any(kw in body for kw in panel_kw), \
                f"编辑页应包含 {panel_kw} 之一，body前300: {body[:300]}"

    # ═══════════════════════════════════════════════════════════════
    # 独立 test method（/zh/ 前缀，排除 404 的 change-passport-to-blue-background）
    # ═══════════════════════════════════════════════════════════════

    def test_hd_pic_converter_zh(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] [中文] 画质增强实验页 — 首屏内容 + 上传停留当前页")
        path = f"{ZH}/tools/hd-pic-converter"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zh-hd-pic-converter-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        ok, t, h1s = _check_title_h1(page, "HD Photo")
        assert ok, f"Title/H1 应含 'HD Photo' 或有中文内容，Title: {t[:60]}, H1: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 4, f"示例图片应 ≥4 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        test_img = pick_test_image()
        try:
            with sp.expect_file_chooser(timeout=10000) as fc:
                sp.evaluate("""() => {var btns=document.querySelectorAll("button");
                    for(var i=0;i<btns.length;i++){var r=btns[i].getBoundingClientRect();
                    if(btns[i].textContent.trim()&&r.y>200&&r.y<1500&&r.width>100){btns[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            fc.value.set_files(test_img)
        except Exception:
            sp.locator("input[type=file]").first.set_input_files(test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "02-zh-hd-pic-converter-上传后")
        # 中文版上传后直接进 /agent（与英文版停留在当前页不同），不强制面板关键词
        assert (path in sp.url or "/agent" in sp.url), f"应停留当前页或进/agent，实际: {sp.url}"

    def test_add_a_person_to_a_photo_zh(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] [中文] 图生图工具 — 首屏内容 + 上传图片后点击生成进画布")
        path = f"{ZH}/tools/add-a-person-to-a-photo"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zh-add-a-person-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        ok, t, h1s = _check_title_h1(page, "Add a Person")
        assert ok, f"Title/H1 应含 'Add a Person' 或有中文内容，Title: {t[:60]}, H1: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        test_img = pick_test_image()
        upload_btn = sp.locator("button:has(img[src*='create_generate_icon_upload_image'])")
        assert upload_btn.count() > 0, "应存在上传按钮"
        box = upload_btn.first.bounding_box()
        with sp.expect_file_chooser(timeout=10000) as fc:
            sp.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        fc.value.set_files(test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "02-zh-add-a-person-上传后")
        assert path in sp.url, f"上传后应停留在当前页，实际: {sp.url}"

        gen_btn = sp.locator("button:has(img[src*='create_generate_icon_go'])")
        assert gen_btn.count() > 0, "应存在生成按钮"
        sp.evaluate("""() => {
            var btns = document.querySelectorAll("button");
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].querySelector("img[src*='create_generate_icon_go']")) {
                    btns[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(15000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "03-zh-add-a-person-进画布页")
        assert ("/create" in sp.url or "/agent" in sp.url), \
            f"点击生成按钮后应进入画布页，实际: {sp.url}"

    def test_batch_edit_zh(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] [中文] 批量编辑 — 首屏内容 + 上传进入编辑页")
        path = f"{ZH}/batch-edit"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zh-batch-edit-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        ok, t, h1s = _check_title_h1(page, "Batch Edit")
        assert ok, f"Title/H1 应含 'Batch Edit' 或有中文内容，Title: {t[:60]}, H1: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 4, f"示例图片应 ≥4 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        test_img = pick_test_image()
        upload_area = sp.locator("img[src*='upload_logo.webp']")
        assert upload_area.count() > 0, "应存在上传区域"
        with sp.expect_file_chooser(timeout=10000) as fc:
            upload_area.first.click()
        fc.value.set_files(test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "02-zh-batch-edit-上传后")
        assert "/batch-edit/edit" in sp.url, f"上传后应进入 /batch-edit/edit，实际: {sp.url}"
        assert "pid=" in sp.url, f"URL 应含 pid 参数，实际: {sp.url}"

    def test_ai_background_zh(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] [中文] AI背景 — 首屏内容 + 上传蒙层等待进入agent打开面板")
        path = f"{ZH}/ai-background"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zh-ai-background-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        ok, t, h1s = _check_title_h1(page, "AI Background")
        assert ok, f"Title/H1 应含 'AI Background' 或有中文内容，Title: {t[:60]}, H1: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        test_img = pick_test_image()
        try:
            with sp.expect_file_chooser(timeout=10000) as fc:
                sp.evaluate("""() => {var btns=document.querySelectorAll("button");
                    for(var i=0;i<btns.length;i++){var r=btns[i].getBoundingClientRect();
                    if(btns[i].textContent.trim()&&r.y>200&&r.y<1500&&r.width>100){btns[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            fc.value.set_files(test_img)
        except Exception:
            sp.locator("input[type=file]").first.set_input_files(test_img)
        sp.wait_for_timeout(5000)
        try:
            sp.wait_for_function("() => document.body.innerText.includes('Generating')", timeout=30000)
            sp.wait_for_function("() => !document.body.innerText.includes('Generating')", timeout=600000)
        except Exception: pass
        sp.wait_for_timeout(5000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        assert "/agent" in sp.url, f"上传后应进入 /agent，实际: {sp.url}"
        try:
            canvas = sp.locator("canvas").first
            if canvas.is_visible(): canvas.click(timeout=10000); sp.wait_for_timeout(2000)
        except Exception: pass
        try:
            ai_bg_btn = sp.locator("button:has-text('AI Background')")
            if ai_bg_btn.count() > 0: ai_bg_btn.first.click()
            else: sp.get_by_text("AI Background").first.click(timeout=10000)
        except Exception:
            try: sp.locator("[data-tool-id*='background']").first.click(timeout=5000)
            except Exception: pass
        sp.wait_for_timeout(3000)
        allure_screenshot(sp, "02-zh-ai-background-agent面板")
        body = sp.locator("body").inner_text()
        assert any(kw in body for kw in ["推荐", "Recommond"]), \
            f"AI 背景面板应含 '推荐' 或 'Recommond'，body前300: {body[:300]}"

    def test_ai_image_generator_zh(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] [中文] 文生图介绍页 — 首屏内容 + 点击生成按钮进入agent")
        path = f"{ZH}/ai-image-generator"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zh-ai-image-generator-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        ok, t, h1s = _check_title_h1(page, "AI Image Generator")
        assert ok, f"Title/H1 应含 'AI Image Generator' 或有中文内容，Title: {t[:60]}, H1: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        gen_btn = sp.locator("button:has(img[src*='create_generate_icon_go'])")
        assert gen_btn.count() > 0, "应存在生成按钮"
        gen_btn.first.click(timeout=10000)
        sp.wait_for_timeout(15000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "02-zh-ai-image-generator-生成后")
        assert "/agent" in sp.url, f"点击生成按钮后应进入 /agent，实际: {sp.url}"

    def test_image_to_image_ai_zh(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] [中文] 图生图介绍页 — 首屏内容 + 上传图片后点击生成进画布")
        path = f"{ZH}/image-to-image-ai"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zh-image-to-image-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        ok, t, h1s = _check_title_h1(page, "Image to Image")
        assert ok, f"Title/H1 应含 'Image to Image' 或有中文内容，Title: {t[:60]}, H1: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        test_img = pick_test_image()
        upload_btn = sp.locator("button:has(img[src*='create_generate_icon_upload_image'])")
        assert upload_btn.count() > 0, "应存在上传按钮"
        box = upload_btn.first.bounding_box()
        with sp.expect_file_chooser(timeout=10000) as fc:
            sp.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        fc.value.set_files(test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "02-zh-image-to-image-上传后")
        assert path in sp.url, f"上传后应停留在当前页，实际: {sp.url}"

        gen_btn = sp.locator("button:has(img[src*='create_generate_icon_go'])")
        assert gen_btn.count() > 0, "应存在生成按钮"
        sp.evaluate("""() => {
            var btns = document.querySelectorAll("button");
            for (var i = 0; i < btns.length; i++) {
                if (btns[i].querySelector("img[src*='create_generate_icon_go']")) {
                    btns[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(15000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "03-zh-image-to-image-进画布页")
        assert ("/create" in sp.url or "/agent" in sp.url), \
            f"点击生成按钮后应进入画布页，实际: {sp.url}"

    def test_collage_maker_zh(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] [中文] 拼图 — 首屏内容 + 点击CTA跳转，无文件选择器")
        path = f"{ZH}/collage-maker"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zh-collage-maker-首屏")
        check_page_text(page, locale="zh", locale_name="简体中文")
        ok, t, h1s = _check_title_h1(page, "Collage")
        assert ok, f"Title/H1 应含 'Collage' 或有中文内容，Title: {t[:60]}, H1: {h1s}"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        collage_img = sp.locator("img[src*='icon_collage']")
        assert collage_img.count() > 0, "应存在 Collage 入口图片"
        box = collage_img.first.bounding_box()
        sp.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        sp.wait_for_timeout(10000)
        for _ in range(3): dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "02-zh-collage-maker-跳转后")
        assert "/create" in sp.url, f"点击 CTA 后应跳转到画布页，实际: {sp.url}"
