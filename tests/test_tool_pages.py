"""功能介绍页回归 — 英文版页面串行：首屏内容 + 内链校验 + 上传进入功能流程。"""
import os, glob, re, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay, visual_assert
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text

# (path, title_kw, h1_kw, url_contains, panel_kw, cta_text)
PAGES = [
    pytest.param("/tools/background-remover", "Background Remover", "Background Remover",
                 ["/agent"], ["Remove BG"], "Upload Image", "移除背景", id="background-remover"),
    pytest.param("/tools/photo-enhancer", "Photo Enhancer", "Photo Enhancer",
                 ["/agent"], ["Enhance"], "Enhance Photo Quality Now", "画质增强", id="photo-enhancer"),
    pytest.param("/tools/background-changer", "Background Changer", "Background Changer",
                 ["/agent"], ["Inspiration", "Nano Banana"], "Upload Image", "背景更换", id="background-changer"),
    pytest.param("/tools/ai-image-extender", "Image Extender", "Image Extender",
                 ["/agent", "/create/edit"], ["Inspiration", "Nano Banana"], "Upload Image", "扩图", id="ai-image-extender"),
    pytest.param("/tools/magic-eraser-with-ai-detection", "Magic Eraser", "Magic Eraser",
                 ["/agent"], ["Erase"], "Upload Image", "AI消除", id="magic-eraser"),
    pytest.param("/tools/blur-background", "Background Blur", "Background Blur",
                 ["/agent"], ["Inspiration", "Nano Banana"], "Upload Image", "背景模糊", id="blur-background"),
    pytest.param("/tools/id-photo-maker", "ID Photo", "ID Photo",
                 ["/tools/id-photo-maker", "/tools/id-photo-edit"], ["Upload Image", "Supported formats"], "Upload Image", "证件照", id="id-photo-maker"),
]

def pick_test_image():
    d = os.path.join(os.path.dirname(__file__), "..", "test_images")
    if os.path.isdir(d):
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        if imgs: return os.path.abspath(imgs[0])

def goto(page: Page, base_url: str, path: str, lazy_scroll: bool = False):
    page.goto(f"{base_url}{path}", timeout=120000)
    try: page.wait_for_load_state("networkidle", timeout=30000)
    except Exception: pass
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


def _find_visible_button_by_text(page: Page, text: str, *, exact: bool = False,
                                 min_y: int = 120, max_y: int = 1800, min_width: int = 120):
    """从当前页里挑出真正可见的主按钮，避免误点侧栏或卡片按钮。"""
    text_norm = " ".join(text.split()).lower()
    best = None
    best_rank = None
    buttons = page.locator("button")
    for idx in range(buttons.count()):
        btn = buttons.nth(idx)
        try:
            if not btn.is_visible():
                continue
            box = btn.bounding_box()
            if not box:
                continue
            if box["width"] < min_width or box["height"] < 24:
                continue
            if box["y"] < min_y or box["y"] > max_y:
                continue
            label = " ".join(btn.inner_text().split()).lower()
            if not label:
                continue
            if exact:
                if label != text_norm:
                    continue
            elif text_norm not in label:
                continue
            rank = (round(box["y"]), -round(box["width"]), idx)
            if best_rank is None or rank < best_rank:
                best = btn
                best_rank = rank
        except Exception:
            continue
    return best


def _find_visible_text_element_by_text(page: Page, text: str, *, exact: bool = False,
                                       min_y: int = 120, max_y: int = 1800, min_width: int = 50):
    """在任意可见元素里找文案节点，适合 label / p / div 这种非 button 入口。"""
    handle = page.evaluate_handle(
        """({text, exact, minY, maxY, minWidth}) => {
            const norm = s => (s || '').replace(/\\s+/g, ' ').trim();
            const needle = norm(text).toLowerCase();
            let best = null;
            for (const el of document.querySelectorAll('*')) {
                const raw = norm(el.textContent);
                if (!raw) continue;
                const hay = raw.toLowerCase();
                if (exact ? hay !== needle : !hay.includes(needle)) continue;
                const r = el.getBoundingClientRect();
                if (!r || r.width < minWidth || r.height < 20) continue;
                if (r.y < minY || r.y > maxY) continue;
                const style = window.getComputedStyle(el);
                if (!style || style.visibility === 'hidden' || style.display === 'none') continue;
                const area = r.width * r.height;
                if (!best || area < best.area || (area === best.area && r.y < best.y)) {
                    best = {el, area, y: r.y};
                }
            }
            return best ? best.el : null;
        }""",
        {"text": text, "exact": exact, "minY": min_y, "maxY": max_y, "minWidth": min_width},
    )
    try:
        return handle.as_element()
    except Exception:
        return None


def _click_upload_cta(page: Page, cta_text: str, test_img: str):
    el = _find_visible_text_element_by_text(page, cta_text, exact=True)
    if el is None:
        el = _find_visible_button_by_text(page, cta_text)
    if el is None:
        try:
            buttons = page.locator("button")
            for idx in range(buttons.count()):
                btn = buttons.nth(idx)
                if not btn.is_visible():
                    continue
                box = btn.bounding_box()
                if not box:
                    continue
                if box["x"] < 200 or box["y"] < 220 or box["y"] > 650:
                    continue
                if box["width"] < 30 or box["width"] > 120 or box["height"] < 30 or box["height"] > 120:
                    continue
                if btn.inner_text().strip():
                    continue
                el = btn
                break
        except Exception:
            pass
    assert el is not None, f"应存在主 CTA 按钮: {cta_text}"
    try:
        with page.expect_file_chooser(timeout=15000) as fc:
            el.click(force=True)
        fc.value.set_files(test_img)
    except Exception:
        page.locator("input[type=file]").first.set_input_files(files=[test_img])


def _click_nav_cta(page: Page, cta_text: str):
    el = _find_visible_text_element_by_text(page, cta_text, exact=True)
    if el is None:
        el = _find_visible_button_by_text(page, cta_text, exact=True)
    assert el is not None, f"应存在跳转按钮: {cta_text}"
    el.click(force=True)

# ═══════════════════════════════════════════════════════════════
# 每条用例 = Step1 首屏(pag) + Step2 上传(session_pag)
# ═══════════════════════════════════════════════════════════════

@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
class TestToolPages:

    @pytest.mark.parametrize("path,title_kw,h1_kw,url_kws,panel_kw,cta_text,name_cn", PAGES)
    def test_tool_page(self, page: Page, session_page: Page, base_url: str, path, title_kw, h1_kw, url_kws, panel_kw, cta_text, name_cn):
        allure.dynamic.title(f"[P0] {name_cn} — 首屏内容 + 上传功能流程")
        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, f"01-{path.split('/')[-1]}-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert title_kw in page.title(), f"Title 应含 '{title_kw}'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any(title_kw in h for h in h1_texts), f"H1 应含 '{title_kw}'，实际: {h1_texts}"
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
        _click_upload_cta(sp, cta_text, test_img)
        sp.wait_for_timeout(15000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, f"02-{path.split('/')[-1]}-上传后")

        # URL 断言
        assert any(kw in sp.url for kw in url_kws), f"上传后应进入编辑页，实际: {sp.url}"

        # 面板关键词断言
        body = sp.locator("body").inner_text()
        for kw in panel_kw:
            assert kw in body, f"编辑页应包含 '{kw}'，body前300: {body[:300]}"

    # ═══════════════════════════════════════════════════════════════
    # TC-TOOL-008 ~ TC-TOOL-015: 独立测试方法
    # 这些页面的上传流程行为不同于通用 test_tool_page（不跳转/两阶段/蒙层等待等）
    # ═══════════════════════════════════════════════════════════════

    def test_hd_pic_converter(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-008: 画质增强实验页 — 首屏内容 + 上传停留在当前页，含 Standard/Portrait Mode"""
        allure.dynamic.title("[P0] 画质增强实验页 — 首屏内容 + 上传停留当前页")
        path = "/tools/hd-pic-converter"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-hd-pic-converter-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "HD Photo" in page.title(), f"Title 应含 'HD Photo'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("HD Photo" in h for h in h1_texts), f"H1 应含 'HD Photo'，实际: {h1_texts}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 4, f"示例图片应 ≥4 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 上传并验证停留在当前页（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        _click_upload_cta(sp, "Upload Image", test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "02-hd-pic-converter-上传后")

        # 上传后停留在当前页（不跳转到 /agent 或 /create）
        assert "/tools/hd-pic-converter" in sp.url, f"应停留在当前页，实际: {sp.url}"
        body = sp.locator("body").inner_text()
        assert "Standard Mode" in body, f"应含 'Standard Mode'，body前300: {body[:300]}"
        assert "Portrait Mode" in body, f"应含 'Portrait Mode'，body前300: {body[:300]}"

    def test_add_a_person_to_a_photo(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-009: 图生图工具 — 首屏 + 上传图片 + 点击生成进入画布页"""
        allure.dynamic.title("[P0] 图生图工具 — 首屏内容 + 上传图片后点击生成进画布")
        path = "/tools/add-a-person-to-a-photo"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-add-a-person-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Add a Person" in page.title(), f"Title 应含 'Add a Person'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("Add a Person" in h for h in h1_texts), f"H1 应含 'Add a Person'，实际: {h1_texts}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"

        # ── Step 2a: 点击上传按钮选择图片 → 停留在当前页（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        _click_upload_cta(sp, "Upload Image", test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "02-add-a-person-上传后")
        # 上传后停留在当前页
        assert "/tools/add-a-person-to-a-photo" in sp.url, f"上传后应停留在当前页，实际: {sp.url}"

        # ── Step 2b: 点击生成按钮 → 进入画布页 ──
        gen_btn = _find_visible_button_by_text(sp, "Generate", exact=True, min_y=220, min_width=80)
        if gen_btn is None:
            gen_btn = sp.locator("button:has(img[src*='create_generate_icon_go'])").first
        assert gen_btn, "应存在生成按钮"
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
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "03-add-a-person-进画布页")
        # 进入画布页（/create 或 /agent）
        current_url = sp.url
        assert ("/create" in current_url or "/agent" in current_url), \
            f"点击生成按钮后应进入画布页，实际: {current_url}"

    def test_change_passport_to_blue_background(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-010: 背景变蓝色 — 首屏 + 上传进入 /agent，等待任务生成完成并截图供 AI 审查"""
        allure.dynamic.title("[P0] 背景变蓝色 — 首屏内容 + 上传进入agent等待生成")
        path = "/tools/change-passport-to-blue-background"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-change-passport-blue-首屏")
        check_page_text(page, locale="en", locale_name="English", fail_on_error=False)
        assert "Blue Background" in page.title(), f"Title 应含 'Blue Background'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("Blue Background" in h for h in h1_texts), f"H1 应含 'Blue Background'，实际: {h1_texts}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 上传进入 /agent 并等待任务完成（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        _click_upload_cta(sp, "Upload Image", test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        # 断言进入 /agent
        sp.wait_for_timeout(5000)
        assert "/agent" in sp.url, f"上传后应进入 /agent，实际: {sp.url}"

        # 等待任务生成完成（轮询检测 "Generating" 文案消失，最长等 10 分钟）
        # 注意：此页先断言 URL 再等 Generating，因为导航后才触发任务；
        # ai_background 页相反（先等 Generating 再断言 URL），因为上传即触发任务
        try:
            sp.wait_for_function(
                "() => document.body.innerText.includes('Generating')",
                timeout=30000
            )
            # 检测到 "Generating" 文案，继续等待完成
            sp.wait_for_function(
                "() => !document.body.innerText.includes('Generating')",
                timeout=600000
            )
        except Exception:
            pass  # 可能任务很快完成，未捕获到 "Generating" 文案

        sp.wait_for_timeout(5000)
        allure_screenshot(sp, "02-change-passport-blue-任务完成后")
        # AI 视觉审查：判断当前画布图层是否为蓝色背景的图
        vis_result = visual_assert(
            before_name="01-change-passport-blue-首屏",
            after_name="02-change-passport-blue-任务完成后",
            expectation="画布图层是否为蓝色背景的图",
        )
        if os.getenv("OPENAI_API_KEY"):
            assert vis_result["verdict"] == "pass", \
                f"AI 视觉审查未通过: {vis_result.get('reason', vis_result)}"
        else:
            assert vis_result["verdict"] == "skipped", \
                f"未配置 OPENAI_API_KEY 时应跳过 AI 视觉审查，实际: {vis_result}"

    def test_batch_edit(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-011: 批量编辑 — 首屏 + 点击上传区域选图进入批量编辑页"""
        allure.dynamic.title("[P0] 批量编辑 — 首屏内容 + 上传进入编辑页")
        path = "/batch-edit"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-batch-edit-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Batch Edit" in page.title(), f"Title 应含 'Batch Edit'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("Batch Edit" in h for h in h1_texts), f"H1 应含 'Batch Edit'，实际: {h1_texts}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 4, f"示例图片应 ≥4 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 点击上传区域 → 文件选择器 → 进入批量编辑页（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        _click_upload_cta(sp, "Upload Image", test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "02-batch-edit-上传后")
        # 断言进入批量编辑页 /batch-edit/edit?pid=xxxx
        assert "/batch-edit/edit" in sp.url, f"上传后应进入 /batch-edit/edit，实际: {sp.url}"
        assert "pid=" in sp.url, f"URL 应含 pid 参数，实际: {sp.url}"

    def test_ai_background(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-012: AI背景 — 首屏 + 蒙层等待 → 进入 /agent 选中图层打开 AI 背景面板含 Recommend"""
        allure.dynamic.title("[P0] AI背景 — 首屏内容 + 上传蒙层等待进入agent打开面板")
        path = "/ai-background"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-ai-background-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "AI Background" in page.title(), f"Title 应含 'AI Background'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("AI Background" in h for h in h1_texts), f"H1 应含 'AI Background'，实际: {h1_texts}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 上传 → 蒙层等待 → 进入 /agent（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        _click_upload_cta(sp, "Upload Image", test_img)

        # 蒙层等待任务处理完成
        # 注意：此页先等 Generating 再断言 URL，因为上传即触发任务；
        # change_passport_to_blue_background 页相反（先断言 URL 再等 Generating），因为导航后才触发
        sp.wait_for_timeout(5000)
        try:
            sp.wait_for_function(
                "() => document.body.innerText.includes('Generating')",
                timeout=30000
            )
            sp.wait_for_function(
                "() => !document.body.innerText.includes('Generating')",
                timeout=600000
            )
        except Exception:
            pass

        sp.wait_for_timeout(5000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        # 断言进入 /agent 页面
        assert "/agent" in sp.url, f"上传后应进入 /agent，实际: {sp.url}"

        # 选中图片图层：点击画布区域（canvas 可能在任务完成后默认为 0x0 不可见，fallback 跳过）
        try:
            canvas = sp.locator("canvas").first
            if canvas.is_visible():
                canvas.click(timeout=10000)
                sp.wait_for_timeout(2000)
        except Exception:
            pass  # 图层可能已默认选中，或 canvas 未渲染

        # 打开 AI 背景面板：用 get_by_text（页面按钮文本为 "Recommond"，用包含匹配）
        try:
            ai_bg_btn = sp.locator("button:has-text('AI Background')")
            if ai_bg_btn.count() > 0:
                ai_bg_btn.first.click()
            else:
                sp.get_by_text("AI Background").first.click(timeout=10000)
        except Exception:
            # 回退：尝试通过 data-tool-id 属性查找
            try:
                sp.locator("[data-tool-id*='background']").first.click(timeout=5000)
            except Exception:
                pass
        sp.wait_for_timeout(3000)

        allure_screenshot(sp, "02-ai-background-agent面板")
        # 新版面板以底部 prompt + 预设按钮为主，不再使用旧的 "Recommond" 文案
        body = sp.locator("body").inner_text()
        assert "Inspiration" in body, f"AI 背景面板应包含预设入口，body前300: {body[:300]}"
        assert "Nano Banana" in body, f"AI 背景面板应包含模型选择，body前300: {body[:300]}"

    def test_ai_image_generator(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-013: 文生图介绍页 — 首屏 + 点击生成按钮进入 /agent"""
        allure.dynamic.title("[P0] 文生图介绍页 — 首屏内容 + 点击生成按钮进入agent")
        path = "/ai-image-generator"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-ai-image-generator-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "AI Image Generator" in page.title(), f"Title 应含 'AI Image Generator'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("AI Image Generator" in h for h in h1_texts), f"H1 应含 'AI Image Generator'，实际: {h1_texts}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 点击生成按钮进入 /agent（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        # 点击生成按钮（create_generate_icon_go.svg）
        gen_btn = _find_visible_button_by_text(sp, "Generate", exact=True, min_y=220, min_width=80)
        if gen_btn is None:
            gen_btn = sp.locator("button:has(img[src*='create_generate_icon_go'])").first
        assert gen_btn, "应存在生成按钮"
        gen_btn.click(timeout=10000)
        sp.wait_for_timeout(15000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "02-ai-image-generator-生成后")
        # 断言进入 /agent 页面
        assert "/agent" in sp.url, f"点击生成按钮后应进入 /agent，实际: {sp.url}"

    def test_image_to_image_ai(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-014: 图生图介绍页 — 首屏 + 上传图片 + 点击生成进入画布页"""
        allure.dynamic.title("[P0] 图生图介绍页 — 首屏内容 + 上传图片后点击生成进画布")
        path = "/image-to-image-ai"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-image-to-image-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Image to Image" in page.title(), f"Title 应含 'Image to Image'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("Image to Image" in h for h in h1_texts), f"H1 应含 'Image to Image'，实际: {h1_texts}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"

        # ── Step 2a: 点击上传按钮选择图片 → 停留在当前页（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        test_img = pick_test_image()
        _click_upload_cta(sp, "Upload Image", test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "02-image-to-image-上传后")
        # 上传后停留在当前页
        assert "/image-to-image-ai" in sp.url, f"上传后应停留在当前页，实际: {sp.url}"

        # ── Step 2b: 点击生成按钮 → 进入画布页 ──
        gen_btn = _find_visible_button_by_text(sp, "Generate", exact=True, min_y=220, min_width=80)
        if gen_btn is None:
            gen_btn = sp.locator("button:has(img[src*='create_generate_icon_go'])").first
        assert gen_btn, "应存在生成按钮"
        # Vue 组件用 dispatchEvent 触发（click/mouse.click 在 headless 下不生效）
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
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "03-image-to-image-进画布页")
        # 进入画布页（/create 或 /agent）
        current_url = sp.url
        assert ("/create" in current_url or "/agent" in current_url), \
            f"点击生成按钮后应进入画布页，实际: {current_url}"

    def test_collage_maker(self, page: Page, session_page: Page, base_url: str):
        """TC-TOOL-015: 拼图 — 首屏（无文件选择器）+ 点击 Get started 跳转 /create/edit"""
        allure.dynamic.title("[P0] 拼图 — 首屏内容 + 点击CTA跳转，无文件选择器")
        path = "/collage-maker"

        # ── Step 1: 首屏内容（无需登录）──
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-collage-maker-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Collage" in page.title(), f"Title 应含 'Collage'，实际: {page.title()[:60]}"
        h1s = page.locator("h1").all()
        h1_texts = [h.inner_text() for h in h1s]
        assert any("Collage" in h for h in h1_texts), f"H1 应含 'Collage'，实际: {h1_texts}"
        # 拼图页面无文件选择器，此处不检查 input[type=file]
        img_count = page.evaluate("""() => {var imgs=document.querySelectorAll('img');var c=0;
            for(var i=0;i<imgs.length;i++){if(imgs[i].offsetWidth>50&&imgs[i].offsetHeight>50)c++;}return c}""")
        assert img_count >= 3, f"示例图片应 ≥3 张，实际: {img_count}"
        verify_seo_links(page, base_url, path)

        # ── Step 2: 点击 Collage 按钮进入画布页（需登录）──
        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)

        _click_nav_cta(sp, "Get started")
        sp.wait_for_timeout(10000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)

        allure_screenshot(sp, "02-collage-maker-跳转后")
        # 断言跳转到画布页
        assert "/create" in sp.url, f"点击 CTA 后应跳转到画布页，实际: {sp.url}"
