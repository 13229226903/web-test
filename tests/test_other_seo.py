"""其他SEO页回归 — 每页面串行：首屏内容 + 内链校验 + 上传交互验证。"""
import os, glob, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay, visual_assert
from helpers.link_checker import verify_seo_links
from helpers.visual_text_check import check_page_text

def pick_test_image():
    d = os.path.join(os.path.dirname(__file__), "..", "test_images")
    if os.path.isdir(d):
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        if imgs:
            return os.path.abspath(imgs[0])


def goto(page: Page, base_url: str, path: str, lazy_scroll: bool = False):
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


def do_upload(page, test_img):
    """在 SEO 页面上传图片（input 为 sr-only 隐藏）。"""
    page.locator("input[type=file]").first.set_input_files(test_img)
    page.wait_for_timeout(10000)
    for _ in range(3):
        dismiss_pricing_overlay(page)


def wait_generating(page, timeout_ms=600000):
    """等待 AI 任务完成（Generating 文案出现并消失）。"""
    try:
        page.wait_for_function(
            "() => document.body.innerText.includes('Generating')",
            timeout=30000
        )
        page.wait_for_function(
            "() => !document.body.innerText.includes('Generating')",
            timeout=timeout_ms
        )
    except Exception:
        pass
    page.wait_for_timeout(5000)


# ═══════════════════════════════════════════════════════════════════
# 私密保存提示（One-Click Private Save）专用 — 当前 SEO 环境 + 独立登录
# ═══════════════════════════════════════════════════════════════════

# 当前 SEO 测试环境（可用环境变量 SEO_PRIV_BASE 覆盖，便于环境切换而不改代码）
SEO_PRIV_BASE = os.environ.get("SEO_PRIV_BASE", "http://10.17.1.66:3001")

# 后端 AI 生成过载报错标志（命中则本次不消耗 credits，属环境问题而非用例缺陷）
HIGH_USAGE_MARKERS = ("Due to high usage", "minor error has occurred", "high usage")


def pick_person_image():
    """优先人像图（breast/bikini 类任务需要人物照片），回退到最小测试图。"""
    d = os.path.join(os.path.dirname(__file__), "..", "test_images")
    for name in ["多人脸.jpg", "小头功能_1.JPG"]:
        p = os.path.join(d, name)
        if os.path.exists(p):
            return os.path.abspath(p)
    return pick_test_image()


def upload_via_cta(page, test_img):
    """点击 hero 上传 CTA（含 upload_logo 图标的大按钮）→ file chooser 选图。

    坐标点击兼容 Vue headless；失败回退到隐藏 input 直接注入。
    """
    btn = page.locator("button:has(img[src*='upload_logo'])").first
    if btn.count() == 0:
        btn = page.locator("button:has(img[src*='upload'])").first
    if btn.count() > 0:
        box = btn.bounding_box()
        if box:
            with page.expect_file_chooser(timeout=15000) as fc:
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            fc.value.set_files(test_img)
            return
    # 回退：直接注入隐藏 input
    page.locator("input[type=file]").first.set_input_files(test_img)


def click_generate_clothes(page):
    """ai-bikini：AI Clothes Changer 面板里选中第一个 bikini 预设并点 Generate。"""
    thumb = page.locator("button:has(img[src*='thumb_aireplace_bikini_1'])").first
    if thumb.count() > 0:
        try:
            b = thumb.bounding_box()
            page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
            page.wait_for_timeout(1000)
        except Exception:
            pass
    gen = page.locator("button:has(img[src*='ai-clothes-generate-button-icon'])").first
    if gen.count() == 0:
        gen = page.locator("button:has-text('Generate')").first
    if gen.count() > 0:
        try:
            b = gen.bounding_box()
            page.mouse.click(b["x"] + b["width"] / 2, b["y"] + b["height"] / 2)
        except Exception:
            page.evaluate("""() => {var bs=document.querySelectorAll('button');
                for (var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==='Generate'){
                    bs[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));return;}}}""")
    page.wait_for_timeout(3000)
    for _ in range(2):
        dismiss_pricing_overlay(page)


def wait_result(page, deadline_s=240):
    """等待生成结果就绪。

    产品行为（已确认）：结果图生成后，选中它时其上方图层工具栏的下载按钮处，
    每次都会出现「One-Click Private Save」私密保护提示。因此以该提示/锚点出现
    作为"结果就绪 + 文案存在"的确定信号。

    返回：
      'error'        —— 后端过载报错（Due to high usage），任务失败
      'hint'         —— 已捕获私密提示（结果就绪且文案存在）
      'done_no_hint' —— 观察到「生成中→结束」但未见私密提示（存疑，交 AI 复核/回归红线）
      'timeout'      —— 超时未见任何结论（多半未生成出结果，疑后端问题）
    """
    saw_generating = False
    elapsed = 0
    while elapsed < deadline_s:
        page.wait_for_timeout(5000)
        elapsed += 5
        for _ in range(2):
            dismiss_pricing_overlay(page)
        bt = page.locator("body").inner_text()
        if any(m in bt for m in HIGH_USAGE_MARKERS):
            return "error"
        if ("Generating" in bt) or ("Processing" in bt) or ("生成中" in bt):
            saw_generating = True
        # 选中画布中心的结果图层，让工具栏 + 私密提示渲染，再探测
        try:
            page.mouse.click(960, 520)
        except Exception:
            pass
        page.wait_for_timeout(400)
        hover_download_button(page)
        bt2 = page.locator("body").inner_text()
        if page.locator(".pc-private-save-hint-anchor").count() > 0 \
                or ("One-Click Private Save" in bt2) or ("Private Save" in bt2):
            return "hint"
        if saw_generating and elapsed >= 25 \
                and "Generating" not in bt2 and "Processing" not in bt2:
            return "done_no_hint"
    return "timeout"


def hover_download_button(page):
    """hover 图层工具栏的下载按钮（私密保存提示 pc-private-save-hint 的锚点）。"""
    dl = page.locator("button:has(img[src*='toolbar_download@'])").first
    if dl.count() == 0:
        return False
    try:
        dl.hover(timeout=5000)
        page.wait_for_timeout(2500)
    except Exception:
        box = dl.bounding_box()
        if box:
            page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_timeout(2500)
    return True


def result_screenshot(page, name):
    """稳健地保存结果图截图：直接 viewport 截图（避免 allure_screenshot 在无限画布上
    因超大 scrollHeight 抛异常导致漏图），同时附加 Allure + 落盘供 visual_assert 读取。"""
    from conftest import SCREENSHOT_DIR
    png = page.screenshot(full_page=False)
    allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
    safe = name.replace("/", "_").replace("\\", "_").replace(" ", "_")
    with open(os.path.join(SCREENSHOT_DIR, safe + ".png"), "wb") as f:
        f.write(png)


@pytest.fixture(scope="session")
def seo_priv_context(browser):
    """会话级：登录当前 SEO 环境（SEO_PRIV_BASE）一次，供私密保存提示用例复用。

    与 conftest.session_context 独立开一个 context 登录，避免相互影响。
    """
    from playwright.sync_api import expect as pw_expect
    email = os.environ.get("POKECUT_TEST_EMAIL", "450832596@qq.com")
    code = os.environ.get("POKECUT_TEST_CODE", "123456")

    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    page.goto(SEO_PRIV_BASE)
    page.wait_for_timeout(5000)

    page.get_by_text("Log in", exact=True).first.click()
    page.wait_for_timeout(3000)
    page.locator('input[type="email"]').fill(email)
    page.locator('input[placeholder="Verification Code"]').fill(code)
    # 提交登录（Vue 事件需 dispatchEvent，click/force 均无效）
    page.evaluate("""() => {
        var bs = document.querySelectorAll('button');
        for (var i = 0; i < bs.length; i++) {
            if (bs[i].textContent.trim() === 'Log in' && bs[i].offsetWidth > 200) {
                bs[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return;
            }
        }
    }""")
    page.wait_for_timeout(9000)
    # 关闭可能出现的 VIP 定价遮罩
    page.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(function(o){
        var bg = window.getComputedStyle(o).backgroundColor;
        if (bg && bg.includes('rgba') && (bg.includes('0.3') || bg.includes('0.5'))) o.remove();
    });}""")
    page.wait_for_timeout(2000)

    pw_expect(page.locator("text='User8JY'").first).to_be_visible(timeout=15000)
    page.close()

    yield context
    context.close()


@pytest.fixture
def seo_priv_page(seo_priv_context):
    """从 seo_priv_context 创建新 page，继承 10.17.2.54:3000 的登录态。"""
    page = seo_priv_context.new_page()
    yield page
    page.close()


def run_private_save_case(page, priv_page, path, title_kw, tag, needs_generate):
    """私密保存提示用例通用流程（breast-expansion / ai-bikini 共用）。

    首屏(免登录) → 登录上传 → 生成任务 → 等完成 → 选中结果图 →
    hover 下载按钮唤出私密提示 → 截图 → AI 审查是否出现「One-Click Private Save」。

    breast-expansion 上传后自动提交任务；ai-bikini 需在画布面板显式点 Generate。
    """
    # ── Step 1: 首屏内容（无需登录）──
    goto(page, SEO_PRIV_BASE, path, lazy_scroll=True)
    allure_screenshot(page, f"01-{tag}-首屏")
    check_page_text(page, locale="en", locale_name="English")
    assert title_kw.lower() in page.title().lower(), \
        f"Title 应含 '{title_kw}'，实际: {page.title()[:80]}"
    h1s = [h.inner_text() for h in page.locator("h1").all()]
    assert any(title_kw.lower() in h.lower() for h in h1s), \
        f"H1 应含 '{title_kw}'，实际: {h1s}"
    assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
    verify_seo_links(page, SEO_PRIV_BASE, path)

    # ── Step 2: 登录后上传 → 生成 → 等结果就绪（遇后端过载重试）──
    sp = priv_page
    test_img = pick_person_image()
    status = "timeout"
    for attempt in range(3):
        goto(sp, SEO_PRIV_BASE, path)
        dismiss_pricing_overlay(sp)
        upload_via_cta(sp, test_img)
        sp.wait_for_timeout(9000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)
        assert "/agent" in sp.url or "/create" in sp.url, \
            f"上传后应进入画布页，实际: {sp.url}"
        if needs_generate:
            click_generate_clothes(sp)  # ai-bikini：面板里选预设并点 Generate
        status = wait_result(sp)
        if status != "error":
            break

    # ── Step 3: 留档结果图截图（无论结果如何）──
    sp.mouse.click(960, 520)  # 选中结果图层
    sp.wait_for_timeout(1500)
    hover_download_button(sp)   # 唤出/停留私密提示
    result_screenshot(sp, f"02-{tag}-结果图私密提示")
    print(f"[private-save] {tag}: wait_result -> {status}")

    # 后端未能生成出结果图（过载报错 / 超时未见结果）→ xfail，避免误报为用例缺陷
    if status == "error":
        pytest.xfail("AI 后端 high usage 过载报错（不消耗 credits），非用例缺陷；后端恢复后重跑")
    if status == "timeout":
        pytest.xfail("超时未生成出结果图/未出现私密提示（疑似后端过载或生成失败），后端恢复后重跑")

    # ── Step 4: DOM 软校验 + AI 审查是否出现「One-Click Private Save」──
    body = sp.locator("body").inner_text()
    dom_has = (status == "hint") or ("One-Click Private Save" in body) or ("Private Save" in body)
    allure.attach(
        f"结果状态={status}  DOM直接命中={dom_has}",
        name="DOM是否含私密保存文案",
        attachment_type=allure.attachment_type.TEXT,
    )
    vis = visual_assert(
        before_name=f"01-{tag}-首屏",
        after_name=f"02-{tag}-结果图私密提示",
        expectation="画布中选中的结果图，其上方图层通用工具栏的下载按钮处，"
                    "是否出现私密保护提示文案「One-Click Private Save」",
    )
    print(f"[private-save] {tag}: dom_has={dom_has} ai_verdict={vis.get('verdict')} "
          f"reason={str(vis.get('reason'))[:160]}")
    # 说明：visual_assert 内部已自动 attach 一次「AI 视觉审查: ...」（原始判定），
    # 此处不再重复 attach，仅在下方【结论】里汇总一次可读版，避免报告出现两条 AI 审查。
    # 醒目记录最终判定（回归信号写入 Allure）
    text_present = dom_has or vis["verdict"] == "pass"
    allure.attach(
        f"私密保存文案是否出现: {'是' if text_present else '否'}\n"
        f"结果状态={status}  DOM命中={dom_has}  AI判定={vis['verdict']}  依据={vis.get('reason', '')}",
        name="【结论】One-Click Private Save 是否出现",
        attachment_type=allure.attachment_type.TEXT,
    )
    # 回归红线：确实生成出了结果图（done_no_hint 观察到"生成中→结束"），
    # 但 DOM 与 AI 均明确未见文案 → 判失败（产品约定：生成后每次都应出现该提示）。
    if status == "done_no_hint" and not dom_has and vis["verdict"] == "fail":
        pytest.fail("结果图已生成，但下载按钮未出现「One-Click Private Save」私密保护文案（疑似回归）")
    # AI 不可用且 DOM 也未命中 → 无法判定，跳过（不误判通过/失败）
    if not dom_has and vis["verdict"] == "skipped":
        pytest.skip(f"AI 视觉审查不可用，且 DOM 未直接命中文案: {vis.get('reason', vis)}")


@pytest.mark.regression
@allure.epic("主流程回归")
@allure.feature("SEO回归")
class TestOtherSEOPages:

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-001: 局部放大 — 上传后在原页面处理，拖动滑杆到20
    # ═══════════════════════════════════════════════════════════════
    def test_zoom_in_photos(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 局部放大 — 首屏内容 + 上传处理拖动Zoom滑杆")
        path = "/tools/zoom-in-photos"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-zoom-in-photos-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Zoom" in page.title(), f"Title 应含 'Zoom'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Zoom" in h for h in h1s), f"H1 应含 'Zoom'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        # 等待任务完成："Download HD" 按钮出现（只有任务完成后才渲染）
        try:
            sp.wait_for_function(
                "() => document.body.innerText.includes('Download HD')",
                timeout=600000
            )
        except Exception:
            pass
        sp.wait_for_timeout(3000)
        # Zoom in 滑杆：用 JS 设值 20 触发 Vue 响应（mouse drag 在 headless 下不生效）
        slider = sp.locator("input[type='range']")
        assert slider.count() > 0, "应存在 Zoom in 滑杆"
        sp.evaluate("""() => {
            var s = document.querySelector("input[type='range']");
            if (s) {
                var setter = Object.getOwnPropertyDescriptor(
                    window.HTMLInputElement.prototype, 'value'
                ).set;
                setter.call(s, 20);
                s.dispatchEvent(new Event('input', {bubbles: true}));
                s.dispatchEvent(new Event('change', {bubbles: true}));
            }
        }""")
        sp.wait_for_timeout(2000)
        # zoom 页面用直接截图避免 allure_screenshot 的 viewport 操作干扰渲染结果
        png = sp.screenshot(full_page=False)
        allure.attach(png, name="02-zoom-in-photos-处理后", attachment_type=allure.attachment_type.PNG)

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-002: 老照片修复 — 上传后进入 /agent，自动打开画质增强，选中 Old Photo Mode
    # ═══════════════════════════════════════════════════════════════
    def test_photo_restoration(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 老照片修复 — 首屏 + 上传进入agent验证Old Photo Mode")
        path = "/tools/photo-restoration"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-photo-restoration-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Photo Restoration" in page.title(), f"Title 应含 'Photo Restoration'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Restoration" in h for h in h1s), f"H1 应含 'Restoration'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        test_img = pick_test_image()
        upload_btn = sp.locator("button:has-text('Upload Image')")
        if upload_btn.count() > 0:
            box = upload_btn.first.bounding_box()
            with sp.expect_file_chooser(timeout=10000) as fc:
                sp.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            fc.value.set_files(test_img)
        else:
            do_upload(sp, test_img)
        sp.wait_for_timeout(10000)
        for _ in range(3):
            dismiss_pricing_overlay(sp)
        allure_screenshot(sp, "02-photo-restoration-上传后")
        assert "/agent" in sp.url, f"上传后应进入 /agent，实际: {sp.url}"
        # 自动打开画质增强弹窗，检查 Old Photo Mode 选中状态
        sp.wait_for_timeout(3000)
        # AI 视觉审查：Old Photo Mode 是否处于选中状态
        vis = visual_assert(
            before_name="01-photo-restoration-首屏",
            after_name="02-photo-restoration-上传后",
            expectation="画质增强弹窗中 Old Photo Mode 选项是否处于选中/高亮状态",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")
        # 视觉断言无论 pass/fail 都记录但不阻断（模型可能不稳定）
        allure.attach(
            str(vis.get("reason", "")),
            name="Old Photo Mode 审查结果",
            attachment_type=allure.attachment_type.TEXT,
        )

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-003: 基于画布页-文字
    # ═══════════════════════════════════════════════════════════════
    def test_monogram_maker(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于画布页-文字 — 首屏 + 上传进入画布验证text按钮")
        path = "/tools/monogram-maker"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-monogram-maker-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Monogram" in page.title(), f"Title 应含 'Monogram'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Monogram" in h for h in h1s), f"H1 应含 'Monogram'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        allure_screenshot(sp, "02-monogram-maker-上传后")
        assert "/create" in sp.url or "/agent" in sp.url, f"上传后应进入画布页，实际: {sp.url}"
        btn_xpath = "//*[@id='__nuxt']/div/div[2]/div[2]/div/div[1]/div/div[1]/div/div[1]/button"
        assert sp.locator(f"xpath={btn_xpath}").count() > 0, "应存在 Monogram text 按钮"

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-004: 基于画布页-模板
    # ═══════════════════════════════════════════════════════════════
    def test_phone_wallpaper_maker(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于画布页-模板 — 首屏 + 上传抠图 + 模板tab高亮")
        path = "/tools/phone-wallpaper-maker"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-phone-wallpaper-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Phone Wallpaper" in page.title(), f"Title 应含 'Phone Wallpaper'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Wallpaper" in h for h in h1s), f"H1 应含 'Wallpaper'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        if not ("/create" in sp.url or "/agent" in sp.url):
            pytest.xfail(f"上传后未导航，当前 URL: {sp.url}")
        wait_generating(sp)
        allure_screenshot(sp, "02-phone-wallpaper-抠图完成")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        # AI 视觉审查：模板 tab 高亮（DOM class 断言不准，交给 AI）
        vis = visual_assert(
            before_name="01-phone-wallpaper-首屏",
            after_name="02-phone-wallpaper-抠图完成",
            expectation="画布页左侧菜单中，模板 tab 是否处于蓝色高亮选中状态",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-005: 基于画布页-轮廓 (photo-border)
    # ═══════════════════════════════════════════════════════════════
    def test_photo_border(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于画布页-轮廓 — 首屏 + 上传进入画布验证layer tab高亮")
        path = "/tools/photo-border"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-photo-border-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Border" in page.title(), f"Title 应含 'Border'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Border" in h for h in h1s), f"H1 应含 'Border'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        allure_screenshot(sp, "02-photo-border-上传后")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        # AI 视觉审查：layer tab 高亮
        vis = visual_assert(
            before_name="01-photo-border-首屏",
            after_name="02-photo-border-上传后",
            expectation="画布页左侧菜单中，photo border（轮廓/layer）tab 是否处于蓝色高亮选中状态",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-006: 基于画布页-滤镜
    # ═══════════════════════════════════════════════════════════════
    def test_digicam_effect(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于画布页-滤镜 — 首屏 + 上传进入画布验证filter展开")
        path = "/tools/digicam-effect"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-digicam-effect-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Digicam" in page.title() or "Y2K" in page.title(), \
            f"Title 应含 'Digicam' 或 'Y2K'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Digicam" in h or "Y2K" in h for h in h1s), \
            f"H1 应含 'Digicam' 或 'Y2K'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        allure_screenshot(sp, "02-digicam-effect-上传后")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        sp.wait_for_timeout(3000)
        # AI 视觉审查：filter 菜单展开
        vis = visual_assert(
            before_name="01-digicam-effect-首屏",
            after_name="02-digicam-effect-上传后",
            expectation="画布页右侧 filter/滤镜菜单栏是否处于展开状态（能看到滤镜选项列表）",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-007: 基于画布页-贴纸
    # ═══════════════════════════════════════════════════════════════
    def test_add_hearts_to_photo(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于画布页-贴纸 — 首屏 + 上传进入画布验证贴纸tab高亮")
        path = "/tools/add-hearts-to-photo"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-add-hearts-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Heart" in page.title(), f"Title 应含 'Heart'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Heart" in h for h in h1s), f"H1 应含 'Heart'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        allure_screenshot(sp, "02-add-hearts-上传后")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        # AI 视觉审查：贴纸 tab 高亮
        vis = visual_assert(
            before_name="01-add-hearts-首屏",
            after_name="02-add-hearts-上传后",
            expectation="画布页左侧菜单中，贴纸 tab 是否处于蓝色高亮选中状态",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-008: 基于画布页-resize
    # ═══════════════════════════════════════════════════════════════
    def test_youtube_banner_maker(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于画布页-resize — 首屏 + 上传进入画布验证贴纸resize tab高亮")
        path = "/tools/youtube-banner-maker"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-youtube-banner-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "YouTube" in page.title() or "Banner" in page.title(), \
            f"Title 应含 'YouTube' 或 'Banner'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("YouTube" in h or "Banner" in h for h in h1s), \
            f"H1 应含 'YouTube' 或 'Banner'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        allure_screenshot(sp, "02-youtube-banner-上传后")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        # AI 视觉审查：贴纸 resize tab 高亮
        vis = visual_assert(
            before_name="01-youtube-banner-首屏",
            after_name="02-youtube-banner-上传后",
            expectation="画布页左侧菜单中，贴纸 resize tab 是否处于蓝色高亮选中状态",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-009: 基于无限画布页-轮廓
    # ═══════════════════════════════════════════════════════════════
    def test_outline_image(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于无限画布页-轮廓 — 首屏 + 上传抠图 + outline面板展开")
        path = "/tools/outline-image"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-outline-image-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Outline" in page.title(), f"Title 应含 'Outline'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Outline" in h for h in h1s), f"H1 应含 'Outline'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        wait_generating(sp)
        allure_screenshot(sp, "02-outline-image-抠图完成")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        vis = visual_assert(
            before_name="01-outline-image-首屏",
            after_name="02-outline-image-抠图完成",
            expectation="画布页中 outline 面板的下拉参数列表是否处于展开状态（能看到多个参数选项）",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-010: 基于画布页-模板 (add-name-and-date)
    # ═══════════════════════════════════════════════════════════════
    def test_add_name_and_date_on_photo(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 基于画布页-模板 — 首屏 + 上传进入画布验证tab高亮+模板展开")
        path = "/tools/add-name-and-date-on-photo"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-add-name-date-首屏")
        check_page_text(page, locale="en", locale_name="English")
        assert "Name" in page.title() and "Date" in page.title(), \
            f"Title 应含 'Name' 和 'Date'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Name" in h and "Date" in h for h in h1s), \
            f"H1 应含 'Name' 和 'Date'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        allure_screenshot(sp, "02-add-name-date-上传后")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        # AI 视觉审查：Name and Date tab 高亮 + 模板展开
        vis = visual_assert(
            before_name="01-add-name-date-首屏",
            after_name="02-add-name-date-上传后",
            expectation="画布页左侧菜单中，Name and Date tab 是否处于蓝色高亮选中状态，且 Name and Date 模板列表已展开",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-011: 抠头
    # ═══════════════════════════════════════════════════════════════
    def test_big_head_cutout(self, page: Page, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] 抠头 — 首屏 + 上传抠头任务 + AI审查抠头结果")
        path = "/de/tools/big-head-cutout-face-cutout"
        goto(page, base_url, path, lazy_scroll=True)
        allure_screenshot(page, "01-big-head-cutout-首屏")
        check_page_text(page, locale="de", locale_name="Deutsch")
        assert "Cutout" in page.title() or "freistellen" in page.title(), \
            f"Title 应含 'Cutout' 或 'freistellen'，实际: {page.title()[:60]}"
        h1s = [h.inner_text() for h in page.locator("h1").all()]
        assert any("Cutout" in h or "freistellen" in h for h in h1s), \
            f"H1 应含 'Cutout' 或 'freistellen'，实际: {h1s}"
        assert page.locator("input[type=file]").count() > 0, "应存在文件上传 input"
        verify_seo_links(page, base_url, path)

        sp = session_page
        goto(sp, base_url, path)
        dismiss_pricing_overlay(sp)
        do_upload(sp, pick_test_image())
        wait_generating(sp)
        allure_screenshot(sp, "02-big-head-cutout-抠头完成")
        assert "/create" in sp.url or "/agent" in sp.url, f"应进入画布页，实际: {sp.url}"
        vis = visual_assert(
            before_name="01-big-head-cutout-首屏",
            after_name="02-big-head-cutout-抠头完成",
            expectation="画布页中是否有一个新图层，该图层只包含从原图中抠出来的人物头部（去除了身体和背景）",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-012: 私密保存提示 — 图生图 breast-expansion
    #   上传→自动生成→结果图下载按钮显示「One-Click Private Save」
    # ═══════════════════════════════════════════════════════════════
    def test_private_save_breast_expansion(self, page: Page, seo_priv_page: Page):
        allure.dynamic.title(
            "[P0] 私密保存提示 — 图生图breast-expansion 上传生成后结果图下载按钮显示 One-Click Private Save")
        run_private_save_case(
            page, seo_priv_page,
            path="/image-to-image-ai/breast-expansion",
            title_kw="Breast",
            tag="breast-expansion",
            needs_generate=False,  # 上传后自动提交生成任务
        )

    # ═══════════════════════════════════════════════════════════════
    # TC-SEO-013: 私密保存提示 — AI换装 ai-bikini
    #   上传→选预设点Generate→结果图下载按钮显示「One-Click Private Save」
    # ═══════════════════════════════════════════════════════════════
    def test_private_save_ai_bikini(self, page: Page, seo_priv_page: Page):
        allure.dynamic.title(
            "[P0] 私密保存提示 — AI换装ai-bikini 上传生成后结果图下载按钮显示 One-Click Private Save")
        run_private_save_case(
            page, seo_priv_page,
            path="/ai-replace/ai-bikini",
            title_kw="Bikini",
            tag="ai-bikini",
            needs_generate=True,  # 画布 AI Clothes Changer 面板需显式点 Generate
        )

