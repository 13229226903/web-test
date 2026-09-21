# -*- coding: utf-8 -*-
"""SEO 页面主上传按钮交互自动化。

数据源: data/pokecut_seo_main_upload_interactions_v1.yaml
用例源: artifacts/2026-09-14_seo_main_upload_interactions/cases.md
驱动: Playwright pytest；上传使用真实 file chooser。
"""

import re
from pathlib import Path

import allure
import pytest
import yaml
from playwright.sync_api import expect, Page

def _repo_root() -> Path:
    """按 test_images/ 上溯仓库根：兼容 tests/ 与 archive/<dir>/ 两种位置。"""
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / "test_images").is_dir():
            return c
    return Path(__file__).resolve().parents[1]


ROOT = _repo_root()
DATA_FILE = ROOT / "data/pokecut_seo_main_upload_interactions_v1.yaml"
SCREENSHOT_DIR = ROOT / "data/screenshots"
_DATA = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
CASES = {case["id"]: case for case in _DATA["cases"]}
TEST_IMAGE = (ROOT / _DATA["image"]).resolve()

def _wait_networkidle(page: Page, timeout: int = 5000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass

def _has_visible_canvas(page: Page) -> bool:
    """画布可见性：优先真实 canvas（有像素尺寸），其次编辑器大图层 img（CSS 缩放）。"""
    return page.evaluate("""() => {
        const vis = (el, minW, minH) => {
            const s = getComputedStyle(el), r = el.getBoundingClientRect();
            if (s.display === "none" || s.visibility === "hidden" || Number(s.opacity) === 0) return false;
            return r.width >= minW && r.height >= minH && r.bottom > 0 && r.top < innerHeight + 400;
        };
        if ([...document.querySelectorAll("canvas")].some(c => vis(c, 200, 150))) return true;
        const imgs = [...document.querySelectorAll("img")].filter(im => vis(im, 300, 250));
        return imgs.some(im => {
            const r = im.getBoundingClientRect();
            return r.x >= 0 && r.x + r.width <= innerWidth + 10;
        });
    }""")

def _wait_processing_done(page: Page, timeout_ms: int) -> None:
    """等待 AI 处理态（Thinking... / Denke nach...）消失，最长 timeout_ms。"""
    try:
        page.wait_for_function(
            """() => {
                const t = (document.body && document.body.innerText) || "";
                return !/Thinking\\.\\.\\.|Denke nach/.test(t);
            }""",
            timeout=timeout_ms,
        )
    except Exception:
        pass

def _wait_editor_ready(page: Page, timeout_ms: int) -> None:
    """在 timeout_ms 内轮询编辑器画布；超时后由断言失败给出明确证据。"""
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    while page.evaluate("() => Date.now()") < deadline:
        if _has_visible_canvas(page):
            return
        page.wait_for_timeout(1000)

def _has_right_panel(page: Page) -> bool:
    return page.evaluate("""() => {
        const vw = innerWidth;
        return [...document.querySelectorAll("aside,div")].some(el => {
            const s = getComputedStyle(el), r = el.getBoundingClientRect();
            return s.display !== "none" && s.visibility !== "hidden" && r.x > vw - 650 && r.width > 280 && r.height > 300 && r.x + r.width <= vw + 20;
        });
    }""")


def _wait_editor_settled(page: Page, timeout_ms: int) -> None:
    """旧画布 /create/edit 编辑器异步加载：画布尺寸连续两次不变且图片图层已渲染。"""
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    prev = None
    while page.evaluate("() => Date.now()") < deadline:
        page.wait_for_timeout(1200)
        cur = page.evaluate("""() => {
            const big = [...document.querySelectorAll("canvas")]
                .map(c => { const r = c.getBoundingClientRect();
                            return [Math.round(r.width), Math.round(r.height)]; })
                .filter(([w, h]) => w > 200 && h > 200);
            const imgs = [...document.querySelectorAll("img")]
                .filter(im => { const r = im.getBoundingClientRect(); return r.width > 200 && r.height > 200; }).length;
            return { big, imgs };
        }""")
        if prev is not None and cur["big"] == prev and cur["imgs"] > 0 and cur["big"]:
            return
        prev = cur["big"]

def _blue_pixel_ratio(page: Page, box: dict, region: str = "top") -> float:
    """截图采样，统计目标蓝色 rgb(47,156,238) 的像素占比（背景是整片纯色，容差 ±18）。"""
    from PIL import Image
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SCREENSHOT_DIR / "_blue_probe.png"
    page.screenshot(path=str(tmp), clip={
        "x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"],
    })
    img = Image.open(tmp).convert("RGB")
    w, h = img.size
    if region == "top":
        strip = img.crop((0, 0, w, max(1, int(h * 0.10))))
    else:
        strip = img
    target = (47, 156, 238)
    total = 0
    hit = 0
    for r, g, b in strip.get_flattened_data() if hasattr(strip, "get_flattened_data") else strip.getdata():
        total += 1
        if abs(r - target[0]) <= 18 and abs(g - target[1]) <= 18 and abs(b - target[2]) <= 18:
            hit += 1
    return hit / total if total else 0.0

def _assert_blue_background(page: Page) -> None:
    """蓝色背景已应用：优先画布叠加层 fill 标记；缺失时用截图采样验证背景确为蓝色。"""
    applied = page.evaluate("""() => {
        const marks = ['rgba(47,156,238,1.000)', 'rgba(47, 156, 238, 1)', 'rgba(47,156,238,1)'];
        return [...document.querySelectorAll('svg')].some(s => {
            const h = s.outerHTML || '';
            return marks.some(m => h.includes(m));
        });
    }""")
    if applied:
        return
    box = _right_result_region(page)
    assert box is not None, "L2-002 上传后应出现可采样的画布区域"
    for attempt in range(4):
        ratio = _blue_pixel_ratio(page, box)
        if ratio >= 0.35:
            return
        page.wait_for_timeout(1500)
    assert ratio >= 0.35, (
        f"L2-002 上传后画布背景应为蓝色 rgb(47,156,238)（顶部 10% 区域蓝色占比>=35%），"
        f"实测 ratio={ratio:.3f} region={box}"
    )

def _assert_crop_overlay(page: Page) -> None:
    """上传后进入裁剪态：存在 Crop 按钮 + 裁剪框/网格 + 画布图层。"""
    crop_btn = page.locator("button", has_text="Crop")
    assert crop_btn.count() > 0, "L2-018 上传后应出现 Crop 按钮"
    overlay = page.evaluate("""() => {
        const marker = document.querySelector('[class*=crop-select],[class*=crop-box],[class*=crop-frame],[class*=crop-overlay]');
        const bigCanvas = [...document.querySelectorAll('canvas')].some(c => {
            const r = c.getBoundingClientRect();
            return r.width > 300 && r.height > 300;
        });
        return !!marker || bigCanvas;
    }""")
    assert overlay, "L2-018 上传后图片上应出现裁剪框（crop 标记或裁剪画布）"

def _right_result_region(page: Page) -> dict | None:
    """定位 /agent 右侧结果画布的屏幕区域（大图层元素）。"""
    boxes = page.evaluate("""() => [...document.querySelectorAll("img")].map(im => {
        const r = im.getBoundingClientRect();
        return { x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height) };
    }).filter(b => b.w > 300 && b.h > 300 && b.y > 40 && b.y + b.h < innerHeight + 20)""")
    if not boxes:
        return None
    return max(boxes, key=lambda b: b["x"])

def _checkerboard_ratio(page: Page, box: dict) -> float:
    """截取结果区域，统计"棋盘格/近白"像素占比；透明背景抠图结果该占比应显著偏高。"""
    from PIL import Image
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = SCREENSHOT_DIR / "_cutout_probe.png"
    page.screenshot(path=str(tmp), clip={
        "x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"],
    })
    img = Image.open(tmp).convert("RGB")
    data = img.get_flattened_data() if hasattr(img, 'get_flattened_data') else img.getdata()
    px = list(data)
    total = len(px)
    light = 0
    for r, g, b in px:
        if r >= 228 and g >= 228 and b >= 228 and max(r, g, b) - min(r, g, b) <= 8:
            light += 1
    return light / total if total else 0.0

def _assert_cutout_result(page: Page) -> None:
    """头部抠图任务完成：处理态结束后结果图层被重绘，且结果区出现透明背景棋盘格。"""
    page.wait_for_function(
        "() => !/Denke nach|Thinking\\.\\.\\./.test(document.body.innerText || '')",
        timeout=90000,
    )
    page.wait_for_timeout(1200)
    box = _right_result_region(page)
    assert box is not None, "L2-021 头部抠图完成后应在画布区显示结果图层"
    ratio = _checkerboard_ratio(page, box)
    assert ratio >= 0.25, (
        f"L2-021 头部抠图结果应呈现透明背景（棋盘格/近白占比>=25%），"
        f"实测 result_region={box} light_ratio={ratio:.3f}"
    )

def _capture(page: Page, case: dict, name_suffix: str = "final") -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shot = SCREENSHOT_DIR / f"{case['id']}_{name_suffix}.png"
    page.screenshot(path=str(shot), full_page=False)
    allure.attach.file(str(shot), name=case["screenshot"] if name_suffix == "final" else f"{case['id']}_failure.png", attachment_type=allure.attachment_type.PNG)
    return shot

def _open_target(page: Page, base_url: str, case: dict) -> None:
    page.goto(f"{base_url}{case['page_path']}", timeout=60000, wait_until="domcontentloaded")
    _wait_networkidle(page)
    page.wait_for_timeout(1800)

def _start_upload(page: Page, case: dict) -> None:
    mode = case["upload_mode"]
    if mode == "cv_guide":
        page.locator(case["main_selector"]).click()
        page.locator(case["guide_selector"]).wait_for(state="visible", timeout=15000)
        return
    with page.expect_file_chooser(timeout=15000) as chooser:
        page.locator(case["main_selector"]).click()
    chooser.value.set_files(str(TEST_IMAGE))

def _select_file(page: Page, case: dict) -> None:
    if case["upload_mode"] != "cv_guide":
        return
    with page.expect_file_chooser(timeout=15000) as chooser:
        page.locator(case["guide_selector"]).click()
    chooser.value.set_files(str(TEST_IMAGE))

def _wait_for_stable_state(page: Page, case: dict) -> None:
    timeout = case["timeout_ms"]
    kind = case["expected_kind"]
    url_pattern = {
        "agent": r"/(?:[a-z]{2}(?:-[a-z]{2})?/)?agent\?pid=[0-9a-f\-]+#?$",
        "legacy": r"/create/edit\?pid=[0-9a-f\-]+#?$",
        "id_photo": r"/tools/id-photo-edit\?pid=[0-9a-f\-]+#?$",
        "same_url": re.escape(case["page_path"]) + r"/?$",
    }[kind]
    polling_kinds = {"agent", "legacy", "id_photo"}
    deadline = page.evaluate("() => Date.now()") + timeout
    panel_ready = False
    while page.evaluate("() => Date.now()") < deadline:
        # 先给处理态出现的时间窗，再等其结束，避免抢在指示器挂载前判定
        page.wait_for_timeout(2500)
        _wait_processing_done(page, 120000)
        if case.get("processing_text_gone"):
            try:
                page.wait_for_function(
                    "text => !document.body.innerText.includes(text)",
                    arg=case["processing_text_gone"], timeout=5000,
                )
            except Exception:
                pass
        keywords = case.get("required_keywords") or []
        matched = True
        for keyword in keywords:
            try:
                expect(page.locator("body")).to_contain_text(keyword, ignore_case=True, timeout=800)
            except AssertionError:
                matched = False
                break
        if matched:
            panel_ready = True
            break
        if not keywords:
            break
    # 落定点：目标页 URL 必须到位
    expect(page).to_have_url(re.compile(url_pattern), timeout=timeout)
    if case.get("processing_text_gone"):
        page.wait_for_function(
            "text => !document.body.innerText.includes(text)",
            arg=case["processing_text_gone"], timeout=timeout,
        )
    for keyword in case.get("required_keywords", []):
        expect(page.locator("body")).to_contain_text(keyword, ignore_case=True, timeout=timeout)
    if case.get("assert_blue_background"):
        _assert_blue_background(page)
    if case.get("assert_crop_overlay"):
        _assert_crop_overlay(page)
    if case.get("assert_editor_settled"):
        _wait_editor_settled(page, timeout)
    if case.get("assert_cutout_result"):
        _assert_cutout_result(page)
    _wait_networkidle(page, timeout=3000)
    _wait_editor_ready(page, timeout)
    assert _has_visible_canvas(page), f"{case['id']} 应出现可见画布"
    if case.get("assert_no_right_panel"):
        assert not _has_right_panel(page), f"{case['id']} 不应自动展开右侧属性面板"

def _run_case(page: Page, base_url: str, case: dict) -> None:
    try:
        with allure.step("登录测试服 VIP 账号并打开目标 SEO 页"):
            _open_target(page, base_url, case)
            expect(page.locator("body")).to_contain_text("User8JY", timeout=15000)
        with allure.step("点击主上传按钮"):
            _start_upload(page, case)
        with allure.step("在 file chooser 选择 test_images/1K.jpg"):
            _select_file(page, case)
        with allure.step("等待上传后稳定状态"):
            _wait_for_stable_state(page, case)
        with allure.step("截图记录"):
            _capture(page, case)
    except Exception:
        _capture(page, case, name_suffix="failure")
        raise

class TestL2SeoMainUploadInteractions:
    """SEO 主上传交互自动化用例。"""

    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/hd-pic-converter 上传 1K.jpg 后到达 Enhance 配置面板")
    @allure.label("case_id", "L2-001")
    @allure.label("layer", "L2")
    def test_l2_001(self, session_page, base_url):
        """PRD引用: cases.md L2-001\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传区域 `Upload Image`。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待原页出现 Enhance 配置控件\n预期结果: URL 保持 `/tools/hd-pic-converter`；原页配置态可见；关键词/按钮包含 `Enhance 配置面板`。\n用例标题: /tools/hd-pic-converter 上传 1K.jpg 后到达 Enhance 配置面板\n截图点: `L2-001_final.png`"""
        _run_case(session_page, base_url, CASES["L2-001"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/change-passport-to-blue-background 上传 1K.jpg 后到达 Background 且自动应用蓝色背景")
    @allure.label("case_id", "L2-002")
    @allure.label("layer", "L2")
    def test_l2_002(self, session_page, base_url):
        """PRD引用: cases.md L2-002\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待 `Thinking...` 处理态结束；最多 120s\n预期结果: URL 匹配 `/*/agent?pid=<uuid>#`；画布可见；`Background`/`Colors`/`Confirm` 可见；**蓝色背景已应用**（画布叠加层 `fill=rgba(47,156,238,1.000)`，缺失时以截图采样校验顶部 10% 区域蓝色占比 ≥35%）。\n用例标题: /tools/change-passport-to-blue-background 上传 1K.jpg 后到达 Background 且自动应用蓝色背景\n截图点: `L2-002_final.png`"""
        _run_case(session_page, base_url, CASES["L2-002"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/landscape-to-portrait-converter 上传 1K.jpg 后到达 AI Extend")
    @allure.label("case_id", "L2-003")
    @allure.label("layer", "L2")
    def test_l2_003(self, session_page, base_url):
        """PRD引用: cases.md L2-003\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `AI Extend` 作为默认面板/激活内容可见。\n用例标题: /tools/landscape-to-portrait-converter 上传 1K.jpg 后到达 AI Extend\n截图点: `L2-003_final.png`"""
        _run_case(session_page, base_url, CASES["L2-003"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/watermark-remover 上传 1K.jpg 后到达 Erase")
    @allure.label("case_id", "L2-004")
    @allure.label("layer", "L2")
    def test_l2_004(self, session_page, base_url):
        """PRD引用: cases.md L2-004\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Erase` 作为默认面板/激活内容可见。\n用例标题: /tools/watermark-remover 上传 1K.jpg 后到达 Erase\n截图点: `L2-004_final.png`"""
        _run_case(session_page, base_url, CASES["L2-004"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/cv-photo-editor 上传 1K.jpg 后到达 Photo Size")
    @allure.label("case_id", "L2-005")
    @allure.label("layer", "L2")
    def test_l2_005(self, session_page, base_url):
        """PRD引用: cases.md L2-005\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开 `/tools/cv-photo-editor`。\n3. 点击 `Create My CV Photo`，等待引导弹窗。\n4. 点击弹窗内 `Upload Image`。\n5. 在 file chooser 选择 `test_images/1K.jpg`。\n6. 等待原页处理完成并进入证件照画布。\n等待策略: 等待原页处理成功并进入 /tools/id-photo-edit；最多 60s\n预期结果: URL 匹配 `/tools/id-photo-edit?pid=`；`Photo Size`、`United States Passport`、`1200*1200`、`2inch*2inch` 均可见。\n用例标题: /tools/cv-photo-editor 上传 1K.jpg 后到达 Photo Size\n截图点: `L2-005_final.png`"""
        _run_case(session_page, base_url, CASES["L2-005"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/add-motion-blur-effect-to-photo 上传 1K.jpg 后到达 Motion Blur")
    @allure.label("case_id", "L2-006")
    @allure.label("layer", "L2")
    def test_l2_006(self, session_page, base_url):
        """PRD引用: cases.md L2-006\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Motion Blur` 作为默认面板/激活内容可见。\n用例标题: /tools/add-motion-blur-effect-to-photo 上传 1K.jpg 后到达 Motion Blur\n截图点: `L2-006_final.png`"""
        _run_case(session_page, base_url, CASES["L2-006"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/ai-beard-remover 上传 1K.jpg 后到达 Enhance 顶部面板（Manual Mode / Smart Auto Mode）")
    @allure.label("case_id", "L2-007")
    @allure.label("layer", "L2")
    def test_l2_007(self, session_page, base_url):
        """PRD引用: cases.md L2-007\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `AI Enhancer` 作为默认面板/激活内容可见。\n用例标题: /tools/ai-beard-remover 上传 1K.jpg 后到达 AI Enhancer\n截图点: `L2-007_final.png`"""
        _run_case(session_page, base_url, CASES["L2-007"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/ai-replace/ai-clothes-changer 上传 1K.jpg 后到达 AI Clothes Changer")
    @allure.label("case_id", "L2-008")
    @allure.label("layer", "L2")
    def test_l2_008(self, session_page, base_url):
        """PRD引用: cases.md L2-008\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `AI Clothes Changer` 作为默认面板/激活内容可见。\n用例标题: /ai-replace/ai-clothes-changer 上传 1K.jpg 后到达 AI Clothes Changer\n截图点: `L2-008_final.png`"""
        _run_case(session_page, base_url, CASES["L2-008"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/relight-photo 上传 1K.jpg 后到达 AI Enhancer")
    @allure.label("case_id", "L2-009")
    @allure.label("layer", "L2")
    def test_l2_009(self, session_page, base_url):
        """PRD引用: cases.md L2-009\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `AI Enhancer` 作为默认面板/激活内容可见。\n用例标题: /tools/relight-photo 上传 1K.jpg 后到达 AI Enhancer\n截图点: `L2-009_final.png`"""
        _run_case(session_page, base_url, CASES["L2-009"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/photo-restoration 上传 1K.jpg 后到达 AI Enhancer / Old Photo Mode")
    @allure.label("case_id", "L2-010")
    @allure.label("layer", "L2")
    def test_l2_010(self, session_page, base_url):
        """PRD引用: cases.md L2-010\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `AI Enhancer / Old Photo Mode` 作为默认面板/激活内容可见。\n用例标题: /tools/photo-restoration 上传 1K.jpg 后到达 AI Enhancer / Old Photo Mode\n截图点: `L2-010_final.png`"""
        _run_case(session_page, base_url, CASES["L2-010"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/zoom-in-photos 上传 1K.jpg 后到达放大结果态（Before/After + Download HD）")
    @allure.label("case_id", "L2-011")
    @allure.label("layer", "L2")
    def test_l2_011(self, session_page, base_url):
        """PRD引用: cases.md L2-011\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待原页出现 Enhance 配置控件\n预期结果: URL 保持 `/tools/zoom-in-photos`；原页配置态可见；关键词/按钮包含 `Enhance 配置面板`。\n用例标题: /tools/zoom-in-photos 上传 1K.jpg 后到达 Enhance 配置面板\n截图点: `L2-011_final.png`"""
        _run_case(session_page, base_url, CASES["L2-011"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/monogram-maker 上传 1K.jpg 后到达 Text / Basic")
    @allure.label("case_id", "L2-012")
    @allure.label("layer", "L2")
    def test_l2_012(self, session_page, base_url):
        """PRD引用: cases.md L2-012\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Text / Basic` 作为默认面板/激活内容可见。\n用例标题: /tools/monogram-maker 上传 1K.jpg 后到达 Text / Basic\n截图点: `L2-012_final.png`"""
        _run_case(session_page, base_url, CASES["L2-012"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/photo-background-editor 上传 1K.jpg 后到达 Background")
    @allure.label("case_id", "L2-013")
    @allure.label("layer", "L2")
    def test_l2_013(self, session_page, base_url):
        """PRD引用: cases.md L2-013\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Background` 作为默认面板/激活内容可见。\n用例标题: /tools/photo-background-editor 上传 1K.jpg 后到达 Background\n截图点: `L2-013_final.png`"""
        _run_case(session_page, base_url, CASES["L2-013"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/phone-wallpaper-maker 上传 1K.jpg 后到达 Template（编辑器加载完成态）")
    @allure.label("case_id", "L2-014")
    @allure.label("layer", "L2")
    def test_l2_014(self, session_page, base_url):
        """PRD引用: cases.md L2-014\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待 URL 到 `/create/edit?pid=`，并等编辑器画布尺寸**连续两次不变**且图片图层已渲染；最多 120s\n预期结果: URL 匹配 `/*/create/edit?pid=<uuid>#`；画布可见（稳定后约 696×928，非加载中的 300×150）；文本 `Template` 可见。\n用例标题: /tools/phone-wallpaper-maker 上传 1K.jpg 后到达 Template（编辑器加载完成态）\n截图点: `L2-014_final.png`（稳定态；不得为加载中 spinner）"""
        _run_case(session_page, base_url, CASES["L2-014"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/photo-border 上传 1K.jpg 后到达 Border")
    @allure.label("case_id", "L2-015")
    @allure.label("layer", "L2")
    def test_l2_015(self, session_page, base_url):
        """PRD引用: cases.md L2-015\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Border` 作为默认面板/激活内容可见。\n用例标题: /tools/photo-border 上传 1K.jpg 后到达 Border\n截图点: `L2-015_final.png`"""
        _run_case(session_page, base_url, CASES["L2-015"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/silhouette-maker 上传 1K.jpg 后到达 Adjust")
    @allure.label("case_id", "L2-016")
    @allure.label("layer", "L2")
    def test_l2_016(self, session_page, base_url):
        """PRD引用: cases.md L2-016\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Adjust` 作为默认面板/激活内容可见。\n用例标题: /tools/silhouette-maker 上传 1K.jpg 后到达 Adjust\n截图点: `L2-016_final.png`"""
        _run_case(session_page, base_url, CASES["L2-016"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/add-hearts-to-photo 上传 1K.jpg 后到达 Sticker")
    @allure.label("case_id", "L2-017")
    @allure.label("layer", "L2")
    def test_l2_017(self, session_page, base_url):
        """PRD引用: cases.md L2-017\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Sticker` 作为默认面板/激活内容可见。\n用例标题: /tools/add-hearts-to-photo 上传 1K.jpg 后到达 Sticker\n截图点: `L2-017_final.png`"""
        _run_case(session_page, base_url, CASES["L2-017"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/youtube-banner-maker 上传 1K.jpg 后出现裁剪框与 Crop 按钮")
    @allure.label("case_id", "L2-018")
    @allure.label("layer", "L2")
    def test_l2_018(self, session_page, base_url):
        """PRD引用: cases.md L2-018\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与裁剪态出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid>#`；画布可见；**出现裁剪框/裁剪画布**（`crop-select-arrow` 或 >300×300 裁剪 canvas）；**顶部出现 `Crop` 按钮**，并有 `Width`/`Height`/`Template(3:4)`。\n用例标题: /tools/youtube-banner-maker 上传 1K.jpg 后出现裁剪框与 Crop 按钮\n截图点: `L2-018_final.png`"""
        _run_case(session_page, base_url, CASES["L2-018"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/car-photo-editor 上传 1K.jpg 后到达 AI Background")
    @allure.label("case_id", "L2-019")
    @allure.label("layer", "L2")
    def test_l2_019(self, session_page, base_url):
        """PRD引用: cases.md L2-019\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `AI Background` 作为默认面板/激活内容可见。\n用例标题: /tools/car-photo-editor 上传 1K.jpg 后到达 AI Background\n截图点: `L2-019_final.png`"""
        _run_case(session_page, base_url, CASES["L2-019"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/add-name-and-date-on-photo 上传 1K.jpg 后到达 Name and Date")
    @allure.label("case_id", "L2-020")
    @allure.label("layer", "L2")
    def test_l2_020(self, session_page, base_url):
        """PRD引用: cases.md L2-020\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/create/edit?pid=<uuid>#`；画布可见；文本 `Name and Date` 作为默认面板/激活内容可见。\n用例标题: /tools/add-name-and-date-on-photo 上传 1K.jpg 后到达 Name and Date\n截图点: `L2-020_final.png`"""
        _run_case(session_page, base_url, CASES["L2-020"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/de/tools/big-head-cutout-face-cutout 上传 1K.jpg 后生成头部抠图结果图")
    @allure.label("case_id", "L2-021")
    @allure.label("layer", "L2")
    def test_l2_021(self, session_page, base_url):
        """PRD引用: cases.md L2-021\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待头部抠图任务完成。\n等待策略: 等待 `Denke nach…` 处理态结束（实测约 16s）；最多 180s\n预期结果: URL 匹配 `/*/agent?pid=<uuid>#`；画布可见；**任务完成后结果图层被替换为头部抠图结果**（透明背景）：截图采样结果区「棋盘格/近白」像素占比 ≥25%。\n用例标题: /de/tools/big-head-cutout-face-cutout 上传 1K.jpg 后生成头部抠图结果图\n截图点: `L2-021_final.png`"""
        _run_case(session_page, base_url, CASES["L2-021"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/tools/christmas-card-maker 上传 1K.jpg 后到达 Template / Christmas Story")
    @allure.label("case_id", "L2-022")
    @allure.label("layer", "L2")
    def test_l2_022(self, session_page, base_url):
        """PRD引用: cases.md L2-022\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/create/edit?pid=<uuid>#`；画布可见；文本 `Template / Christmas Story` 作为默认面板/激活内容可见。\n用例标题: /tools/christmas-card-maker 上传 1K.jpg 后到达 Template / Christmas Story\n截图点: `L2-022_final.png`"""
        _run_case(session_page, base_url, CASES["L2-022"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/zh-tw/tools/motion-blur 上传 1K.jpg 后到达 Motion Blur")
    @allure.label("case_id", "L2-023")
    @allure.label("layer", "L2")
    def test_l2_023(self, session_page, base_url):
        """PRD引用: cases.md L2-023\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `Motion Blur` 作为默认面板/激活内容可见。\n用例标题: /zh-tw/tools/motion-blur 上传 1K.jpg 后到达 Motion Blur\n截图点: `L2-023_final.png`"""
        _run_case(session_page, base_url, CASES["L2-023"])
    @pytest.mark.login_required
    @pytest.mark.full
    @allure.feature("SEO 主上传交互")
    @allure.story("L2 交互行为")
    @allure.severity(allure.severity_level.NORMAL)
    @allure.title("/th/tools/hd-pic-converter 上传 1K.jpg 后到达 AI Enhancer / Ultra HD Mode")
    @allure.label("case_id", "L2-024")
    @allure.label("layer", "L2")
    def test_l2_024(self, session_page, base_url):
        """PRD引用: cases.md L2-024\n覆盖层级: L2\n前置条件: 测试服 VIP 已登录，素材 test_images/1K.jpg\n测试步骤:\n1. 登录测试服 VIP 账号。\n2. 打开目标 SEO 页。\n3. 点击主上传按钮。\n4. 在 file chooser 选择 `test_images/1K.jpg`。\n5. 等待上传后稳定状态。\n等待策略: 等待画布 URL 与默认面板出现；最多 60s\n预期结果: URL 匹配 `/*/agent?pid=<uuid># 或 /agent?pid=<uuid>#`；画布可见；文本 `AI Enhancer / Ultra HD Mode` 作为默认面板/激活内容可见。\n用例标题: /th/tools/hd-pic-converter 上传 1K.jpg 后到达 AI Enhancer / Ultra HD Mode\n截图点: `L2-024_final.png`"""
        _run_case(session_page, base_url, CASES["L2-024"])
