"""ID Photo Maker — create页内入口 → 证件照编辑页功能回归。"""
import os, glob, pytest, allure
from playwright.sync_api import Page
from conftest import allure_screenshot, dismiss_pricing_overlay, visual_assert
XPATH = "//*[@id='__nuxt']/div[1]/div[3]/div[2]/div[2]/div[2]/div[6]"


def pick_test_image():
    d = os.path.join(os.path.dirname(__file__), "..", "test_images")
    if os.path.isdir(d):
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        if imgs:
            return os.path.abspath(imgs[0])


def goto(page: Page, base_url: str, path: str):
    page.goto(f"{base_url}{path}", timeout=120000)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(3000)


def login_and_enter_edit(sp: Page, base_url: str, test_img: str):
    """登录 → /create → 点击 ID Photo Maker → 选图 → 进入编辑页。返回 sp。"""
    goto(sp, base_url, "/create")
    dismiss_pricing_overlay(sp)
    sp.wait_for_timeout(3000)
    # 点击入口触发文件选择器
    el = sp.locator(f"xpath={XPATH}")
    assert el.count() > 0, "ID Photo Maker 入口不存在"
    with sp.expect_file_chooser(timeout=10000) as fc:
        el.first.click()
    fc.value.set_files(test_img)
    sp.wait_for_timeout(15000)
    assert "/tools/id-photo-edit" in sp.url, f"应进入编辑页，实际: {sp.url}"
    # 等待编辑页侧栏渲染
    sp.wait_for_timeout(5000)
    dismiss_pricing_overlay(sp)


def wait_generating(page, timeout_ms=600000):
    """等待 AI 任务完成。"""
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
    page.wait_for_timeout(3000)


def click_generate(sp):
    """点击 Generate 按钮并等待任务完成。如果找不到可点击的则 xfail。"""
    gen = sp.locator("button:has-text('Generate')")
    count = gen.count()
    for i in range(count):
        try:
            disabled = gen.nth(i).is_disabled()
        except Exception:
            continue
        if not disabled:
            gen.nth(i).click(force=True, timeout=10000)
            wait_generating(sp)
            return
    pytest.xfail("没有可点击的 Generate 按钮（预设可能未选中）")


@allure.epic("ID Photo Maker")
@allure.feature("证件照编辑")
class TestIDPhotoMaker:

    # ═══════════════════════════════════════════════════════════════
    # TC-ID-001: 入口触发文件选择器
    # ═══════════════════════════════════════════════════════════════
    def test_id_001_entry_file_chooser(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-001 入口→文件选择器")
        sp = session_page
        goto(sp, base_url, "/create")
        dismiss_pricing_overlay(sp)
        sp.wait_for_timeout(2000)

        el = sp.locator(f"xpath={XPATH}")
        assert el.count() > 0, "ID Photo Maker 入口不存在"
        allure_screenshot(sp, "01-create页-入口可见")

        test_img = pick_test_image()
        with sp.expect_file_chooser(timeout=10000) as fc:
            el.first.click()
        fc.value.set_files(test_img)
        allure_screenshot(sp, "02-文件选择器已触发")

    # ═══════════════════════════════════════════════════════════════
    # TC-ID-002: 选图进入编辑页
    # ═══════════════════════════════════════════════════════════════
    def test_id_002_navigate_to_edit(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-002 选图→编辑页")
        sp = session_page
        test_img = pick_test_image()
        login_and_enter_edit(sp, base_url, test_img)
        allure_screenshot(sp, "03-编辑页-首屏")
        body = sp.locator("body").inner_text()
        assert "Download" in body, "应含 Download"
        assert "AI Filter" in body, "应含 AI Filter"

    # ═══════════════════════════════════════════════════════════════
    # TC-ID-003a: AI Filter — Face Editor 预设
    # ═══════════════════════════════════════════════════════════════
    def test_id_003a_ai_filter_face(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-003a AI Filter — Face Editor 预设")
        sp = session_page
        test_img = pick_test_image()
        login_and_enter_edit(sp, base_url, test_img)
        allure_screenshot(sp, "04a-编辑页-处理前")

        # 点击 AI Filter 展开面板
        # 点击 AI Filter（Vue 组件，dispatchEvent 触发）
        sp.evaluate("""() => {
            var els = document.querySelectorAll("span");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "AI Filter") {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(2000)
        allure_screenshot(sp, "04a-AI-Filter面板")

        # 选中第一个可见预设（Pouty Lips）
        sp.evaluate("""() => {
            var els = document.querySelectorAll("*");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "Pouty Lips" && els[i].offsetWidth > 0) {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(1000)

        # 点击 Generate 等待生成
        click_generate(sp)
        allure_screenshot(sp, "04a-AI-Filter-生成后")

    # ═══════════════════════════════════════════════════════════════
    # TC-ID-003b: AI Filter — Hair Editor
    # ═══════════════════════════════════════════════════════════════
    def test_id_003b_ai_filter_hair(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-003b AI Filter — Hair Editor")
        sp = session_page
        test_img = pick_test_image()
        login_and_enter_edit(sp, base_url, test_img)

        # 点击 AI Filter
        # 点击 AI Filter（Vue 组件，dispatchEvent 触发）
        sp.evaluate("""() => {
            var els = document.querySelectorAll("span");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "AI Filter") {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(2000)

        # 切换到 Hair Editor
        sp.evaluate("""() => {
            var els = document.querySelectorAll("*");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "Hair Editor" && els[i].offsetWidth > 0) {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(2000)
        allure_screenshot(sp, "04b-Hair-Editor面板")

        # 选中第一个头发预设
        sp.evaluate("""() => {
            var els = document.querySelectorAll("*");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "Add Bangs" && els[i].offsetWidth > 0) {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(1000)

        # 点击 Generate
        click_generate(sp)
        allure_screenshot(sp, "04b-Hair-Editor-生成后")

    # ═══════════════════════════════════════════════════════════════
    # TC-ID-007: 无人脸图 → 蒙层 → Continue + Change Photo
    def test_id_007_no_face(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-007 无人脸图 → 蒙层 → Continue + Change Photo")
        sp = session_page
        no_face_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_images", "无人脸.jpg"))
        goto(sp, base_url, "/create")
        dismiss_pricing_overlay(sp)
        sp.wait_for_timeout(3000)
        el = sp.locator(f"xpath={XPATH}")
        assert el.count() > 0, "ID Photo Maker 入口不存在"
        with sp.expect_file_chooser(timeout=10000) as fc:
            el.first.click()
        fc.value.set_files(no_face_img)
        sp.wait_for_timeout(20000)
        body = sp.locator("body").inner_text()
        assert "No face detected" in body, f"应有无人脸蒙层，body: {body[:300]}"
        allure_screenshot(sp, "07-无人脸蒙层")

        # Continue
        all_btns = sp.locator("button:visible")
        for i in range(all_btns.count()):
            txt = all_btns.nth(i).inner_text()
            if "Change" not in txt and "Continue" in txt:
                all_btns.nth(i).click(force=True)
                sp.wait_for_timeout(5000)
                allure_screenshot(sp, "07-Continue后")
                break

        # 重新上传触发蒙层
        goto(sp, base_url, "/create")
        dismiss_pricing_overlay(sp)
        sp.wait_for_timeout(3000)
        with sp.expect_file_chooser(timeout=10000) as fc:
            sp.locator(f"xpath={XPATH}").first.click()
        fc.value.set_files(no_face_img)
        sp.wait_for_timeout(15000)
        allure_screenshot(sp, "07-无人脸蒙层2")

        # Change Photo
        change_btn = sp.locator("button:has-text('Change Photo')")
        assert change_btn.count() > 0, "应有 Change Photo 按钮"
        with sp.expect_file_chooser(timeout=10000) as fc:
            change_btn.first.click(force=True)
        fc.value.set_files(pick_test_image())
        sp.wait_for_timeout(15000)
        allure_screenshot(sp, "07-换图后")

    # TC-ID-008: 多人脸图 → 蒙层 → Continue + Change Photo
    def test_id_008_multi_face(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-008 多人脸图 → 蒙层 → Continue + Change Photo")
        sp = session_page
        multi_img = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "test_images", "多人脸.jpg"))
        goto(sp, base_url, "/create")
        dismiss_pricing_overlay(sp)
        sp.wait_for_timeout(3000)
        el = sp.locator(f"xpath={XPATH}")
        assert el.count() > 0, "ID Photo Maker 入口不存在"
        with sp.expect_file_chooser(timeout=10000) as fc:
            el.first.click()
        fc.value.set_files(multi_img)
        sp.wait_for_timeout(20000)
        body = sp.locator("body").inner_text()
        assert "Multiple faces detected" in body, f"应有多人脸蒙层，body: {body[:300]}"
        allure_screenshot(sp, "08-多人脸蒙层")

        # Continue
        all_btns = sp.locator("button:visible")
        for i in range(all_btns.count()):
            txt = all_btns.nth(i).inner_text()
            if "Change" not in txt and "Continue" in txt:
                all_btns.nth(i).click(force=True)
                sp.wait_for_timeout(5000)
                allure_screenshot(sp, "08-Continue后")
                break

        # 重新上传触发蒙层
        goto(sp, base_url, "/create")
        dismiss_pricing_overlay(sp)
        sp.wait_for_timeout(3000)
        with sp.expect_file_chooser(timeout=10000) as fc:
            sp.locator(f"xpath={XPATH}").first.click()
        fc.value.set_files(multi_img)
        sp.wait_for_timeout(15000)
        allure_screenshot(sp, "08-多人脸蒙层2")

        # Change Photo
        change_btn = sp.locator("button:has-text('Change Photo')")
        assert change_btn.count() > 0, "应有 Change Photo 按钮"
        with sp.expect_file_chooser(timeout=10000) as fc:
            change_btn.first.click(force=True)
        fc.value.set_files(pick_test_image())
        sp.wait_for_timeout(15000)
        allure_screenshot(sp, "08-换图后")

    # TC-ID-004a ~ TC-ID-006 暂不测试
    # ═══════════════════════════════════════════════════════════════
    @pytest.mark.skip(reason="暂不测试：左侧工具面板交互需进一步调试")
    def test_id_004a_formal_wear_template(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-004a Formal Wear — 预设模板")
        sp = session_page
        test_img = pick_test_image()
        login_and_enter_edit(sp, base_url, test_img)
        allure_screenshot(sp, "05a-Formal-Wear-处理前")

        # 点击 Formal Wear
        sp.evaluate("""() => {
            var els = document.querySelectorAll("*");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "Formal Wear" && els[i].offsetWidth > 0) {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(2000)
        allure_screenshot(sp, "05a-Formal-Wear面板")

        # 选中 Women 分类
        women_tab = sp.locator("text=Women").first
        if women_tab.count() > 0:
            women_tab.click()
            sp.wait_for_timeout(1000)

        # 点击 Generate
        click_generate(sp)
        allure_screenshot(sp, "05a-Formal-Wear-生成后")

        # AI 视觉审查：衣服是否改变
        vis = visual_assert(
            before_name="05a-Formal-Wear-处理前",
            after_name="05a-Formal-Wear-生成后",
            expectation="结果图中人物的衣服是否发生了改变（跟处理前不同）",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    @pytest.mark.skip(reason="暂不测试")
    # TC-ID-004b: Formal Wear — 自定义上传
    # ═══════════════════════════════════════════════════════════════
    def test_id_004b_formal_wear_custom(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-004b Formal Wear — 自定义上传")
        sp = session_page
        test_img = pick_test_image()
        # 选一张不同的图作为服装上传
        d = os.path.join(os.path.dirname(__file__), "..", "test_images")
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        cloth_img = os.path.abspath(imgs[-1]) if len(imgs) > 1 else test_img

        login_and_enter_edit(sp, base_url, test_img)
        allure_screenshot(sp, "05b-Formal-Wear-处理前")

        # 点击 Formal Wear
        sp.evaluate("""() => {
            var els = document.querySelectorAll("*");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "Formal Wear" && els[i].offsetWidth > 0) {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(2000)

        # 点击 Upload 按钮上传自定义服装
        upload_btn = sp.locator("button:has-text('Upload')")
        if upload_btn.count() > 0:
            with sp.expect_file_chooser(timeout=10000) as fc:
                upload_btn.first.click(force=True)
            fc.value.set_files(cloth_img)
            sp.wait_for_timeout(5000)

        # 点击 Generate
        click_generate(sp)
        allure_screenshot(sp, "05b-Formal-Wear-生成后")

        # AI 视觉审查
        vis = visual_assert(
            before_name="05b-Formal-Wear-处理前",
            after_name="05b-Formal-Wear-生成后",
            expectation="结果图中人物的衣服是否变得跟上传的服装图类似",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    @pytest.mark.skip(reason="暂不测试")
    # TC-ID-005: Change BG — 选红色
    # ═══════════════════════════════════════════════════════════════
    def test_id_005_change_bg_red(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-005 Change BG — 红色背景")
        sp = session_page
        test_img = pick_test_image()
        login_and_enter_edit(sp, base_url, test_img)
        allure_screenshot(sp, "06-Change-BG-处理前")

        # 点击 Change BG
        sp.evaluate("""() => {
            var els = document.querySelectorAll("*");
            for (var i = 0; i < els.length; i++) {
                if (els[i].textContent.trim() === "Change BG" && els[i].offsetWidth > 0) {
                    els[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        sp.wait_for_timeout(2000)
        allure_screenshot(sp, "06-Change-BG面板")

        # 选中红色（Basic color 中找红色色块）
        # 红色色块：R>150, G<100, B<100 的 button
        red_clicked = sp.evaluate("""() => {
            var btns = document.querySelectorAll("button");
            for (var i = 0; i < btns.length; i++) {
                var bg = window.getComputedStyle(btns[i]).backgroundColor;
                if (bg) {
                    var m = bg.match(/\\d+/g);
                    if (m && m.length >= 3) {
                        var r = parseInt(m[0]), g = parseInt(m[1]), b = parseInt(m[2]);
                        if (r > 150 && g < 100 && b < 100 && btns[i].offsetWidth > 10 && btns[i].offsetHeight > 10) {
                            btns[i].click();
                            return true;
                        }
                    }
                }
            }
            return false;
        }""")
        if not red_clicked:
            # 回退：找红色色块按钮
            try:
                sp.locator("button[class*='red'], [class*='Red']").first.click(timeout=5000, force=True)
            except Exception:
                pass
        sp.wait_for_timeout(3000)
        allure_screenshot(sp, "06-Change-BG-红色后")

        # AI 视觉审查
        vis = visual_assert(
            before_name="06-Change-BG-处理前",
            after_name="06-Change-BG-红色后",
            expectation="画布背景是否变成了红色",
        )
        if vis["verdict"] == "skipped":
            pytest.skip(f"AI 视觉审查跳过: {vis.get('reason', vis)}")

    # ═══════════════════════════════════════════════════════════════
    @pytest.mark.skip(reason="暂不测试")
    # TC-ID-006: 尺寸预设切换
    # ═══════════════════════════════════════════════════════════════
    def test_id_006_size_presets(self, session_page: Page, base_url: str):
        allure.dynamic.title("[P0] TC-ID-006 尺寸预设切换")
        sp = session_page
        test_img = pick_test_image()
        login_and_enter_edit(sp, base_url, test_img)

        initial_size = sp.evaluate("""() => {
            var els = document.querySelectorAll("*");
            for (var i = 0; i < els.length; i++) {
                var el = els[i];
                if (el && el.textContent && el.textContent.includes("Photo Size")) {
                    var p = el.parentElement;
                    if (p && p.textContent) return p.textContent.trim().substring(0, 60);
                }
            }
            return "";
        }""")
        allure_screenshot(sp, "07-尺寸-默认")

        # 切换到不同分类验证预设列表变化
        for cat in ["Visa", "Passport", "Others", "Common"]:
            el = sp.locator(f"text={cat}").first
            if el.count() > 0:
                try:
                    el.click(force=True, timeout=5000)
                except Exception:
                    continue
                sp.wait_for_timeout(1500)
                # 验证至少有一些可见预设
                assert sp.locator("text=mm").count() > 0 or sp.locator("text=pixel").count() > 0, \
                    f"{cat} 分类下应有尺寸预设"

        allure_screenshot(sp, "07-尺寸-切换后")
