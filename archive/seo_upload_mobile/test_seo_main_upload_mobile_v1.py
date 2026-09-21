# -*- coding: utf-8 -*-
"""24 个 SEO 页面移动端主上传按钮交互自动化。

数据源: data/pokecut_seo_main_upload_mobile_interactions_v1.yaml
用例源: artifacts/2026-09-15_seo_main_upload_mobile_interactions/cases.md
驱动: Playwright pytest；移动端设备模拟（390x844 / Pixel 10 口径，历史例外；规则默认 iPhone 390x844）。
"""

import re
from pathlib import Path

import allure
import pytest
import yaml
from playwright.sync_api import expect, Page


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for c in [here.parent, *here.parents]:
        if (c / "test_images").is_dir():
            return c
    return Path(__file__).resolve().parents[1]


ROOT = _repo_root()
DATA_FILE = ROOT / "data/pokecut_seo_main_upload_mobile_interactions_v1.yaml"
SCREENSHOT_DIR = ROOT / "data/screenshots"
_DATA = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
CASES = {c["id"]: c for c in _DATA["cases"]}
TEST_IMAGE = (ROOT / _DATA["image"]).resolve()

BUSY_RE = re.compile(r"Thinking\.\.\.|Denke nach|Optimizing image|AI model is processing")
# 测试服偶发网关错误（非业务态）：命中则重试一次打开页面
GATEWAY_ERROR_RE = re.compile(r"502 Bad Gateway|504 Gateway Time-out|500 Internal Server Error", re.I)
URL_PATTERNS = {
    "legacy_canvas": r"/(?:[a-z]{2}(?:-[a-z]{2})?/)?create/edit\?pid=[0-9a-f\-]+#?$",
    "id_photo": r"/tools/id-photo-edit\?pid=[0-9a-f\-]+#?$",
}


def _wait_networkidle(page: Page, timeout: int = 3000) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass


def _open_target(page: Page, base_url: str, case: dict) -> None:
    """打开目标页；测试服偶发 502/504 网关错误、或首屏上传入口渲染慢时重试一次。

    证据：evidence/selfrun_mobile_full8.log（L2-004 失败截图为 nginx 502）、
    evidence/landing_selector_scan.json（首次进入偶发 >3s 才挂载上传入口）。
    """
    for attempt in range(2):
        page.goto(f"{base_url}{case['page_path']}", timeout=60000, wait_until="domcontentloaded")
        _wait_networkidle(page)
        page.wait_for_timeout(1800)
        body = page.evaluate("() => (document.body && document.body.innerText) || ''")[:4000]
        if GATEWAY_ERROR_RE.search(body):
            page.wait_for_timeout(3000)
            continue
        try:
            page.wait_for_function(
                """() => !!document.querySelector('button.seo-first-screen-upload-button')
                         || !!document.querySelector('input[type=file]')""",
                timeout=20000,
            )
            return
        except Exception:
            page.wait_for_timeout(1500)
    # 两次都未就绪：交给 _start_upload 的定位失败给出明确报错


def _start_upload(page: Page, case: dict) -> None:
    """移动端主上传：优先 page_map 记录的真实按钮 → file chooser，再回退文案点击 → file input。

    实测（evidence/landing_selector_scan.json）24 页中 22 页有可见的
    `button.seo-first-screen-upload-button`（文案随页面/语言变化：Upload Image / Get Clean Image Now /
    Create My CV Photo / Bild hochladen / 上傳圖片 / อัปโหลดรูปภาพ），2 页（hd-pic-converter、
    photo-restoration）无该按钮，主入口即 `input[type=file]`；故采用「数据里的主 selector →
    文案候选点击 → input 兜底」三级策略，避免只靠文案匹配导致漏点。
    """
    selector = case.get("upload_selector") or "input[type=file]"
    if selector != "input[type=file]":
        primary = page.locator(selector).first
        try:
            if primary.count():
                primary.scroll_into_view_if_needed(timeout=5000)
                with page.expect_file_chooser(timeout=15000) as chooser:
                    primary.click()
                chooser.value.set_files(str(TEST_IMAGE))
                return
        except Exception:
            pass

    patterns = [
        re.compile(r"Upload Image", re.I),
        re.compile(r"Create My CV Photo", re.I),
        re.compile(r"^Upload$", re.I),
        re.compile(r"Bild hochladen", re.I),
        re.compile(r"上传图片|上传照片|上傳圖片", re.I),
    ]
    for pat in patterns:
        loc = page.get_by_text(pat).first
        if loc.count() == 0:
            continue
        try:
            loc.scroll_into_view_if_needed(timeout=5000)
            with page.expect_file_chooser(timeout=10000) as chooser:
                loc.click()
            chooser.value.set_files(str(TEST_IMAGE))
            return
        except Exception:
            continue

    # 回退：直接给 file input 赋值（探索阶段实测 24/24 可用）
    inputs = page.locator(case.get("upload_fallback_selector") or "input[type=file]")
    expect(inputs.first).to_be_attached(timeout=20000)
    inputs.first.set_input_files(str(TEST_IMAGE))


def _wait_processing_done(page: Page, timeout_ms: int) -> None:
    try:
        page.wait_for_function(
            """() => {
                const t = (document.body && document.body.innerText) || "";
                return !/Thinking\\.\\.\\.|Denke nach|Optimizing image|AI model is processing/.test(t);
            }""",
            timeout=timeout_ms,
        )
    except Exception:
        pass


def _mobile_panel_tabs(page: Page) -> list:
    """底部主面板可见 tab 文本列表。"""
    return page.evaluate("""() => [...document.querySelectorAll('.mobile-primary-panel__tab-text')]
        .map(e => { const r = e.getBoundingClientRect();
            return r.width > 0 && r.height > 0 ? (e.innerText || '').trim() : null; })
        .filter(Boolean)""")


def _mobile_panel_active_tab(page: Page) -> str | None:
    return page.evaluate("""() => {
        const el = document.querySelector('.mobile-primary-panel__tab-text--active');
        return el ? (el.innerText || '').trim() : null;
    }""")


def _drawn_sizes(page: Page) -> list:
    """移动端编辑器渲染证据：可见 canvas 或 >200x200 的图层图片。"""
    return page.evaluate("""() => {
        const vis = el => { const s = getComputedStyle(el), r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
        const canvases = [...document.querySelectorAll('canvas')].filter(vis)
            .map(c => { const r = c.getBoundingClientRect(); return ['canvas', Math.round(r.width), Math.round(r.height)]; });
        const imgs = [...document.querySelectorAll('img')].filter(vis)
            .map(im => { const r = im.getBoundingClientRect(); return ['img', Math.round(r.width), Math.round(r.height)]; })
            .filter(([, w, h]) => w > 200 && h > 200);
        return [...canvases, ...imgs];
    }""")


def _canvas_sizes(page: Page) -> list:
    return page.evaluate("""() => [...document.querySelectorAll('canvas')]
        .map(c => { const s = getComputedStyle(c), r = c.getBoundingClientRect();
            if (s.display === 'none' || s.visibility === 'hidden' || r.width === 0) return null;
            return [Math.round(r.width), Math.round(r.height)]; })
        .filter(Boolean)""")


def _selected_layer_state(page: Page) -> dict:
    """图片图层默认选中证据（对照 cases.md「选择框/拖拽手柄可见」）。

    selector 取自 page_map `states.after_upload.elements`：
    - `selected_layer_frame` = `.choose-boder`（2px 虚线选中框，与主画布同尺寸）
    - `selected_layer_handles` = `.choose-boder .scale-point`（四角缩放手柄 20x20 / radius 100%）
    证据：evidence/layer_selected_probe3.json（样式+手柄几何）、layer_selected_probe4.json（跨页/跨语种 5 页复核）。
    """
    return page.evaluate("""() => {
        const vis = el => { if (!el) return false; const s = getComputedStyle(el), r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
        const frame = document.querySelector('.choose-boder');
        const fr = frame ? frame.getBoundingClientRect() : null;
        const handles = [...document.querySelectorAll('.choose-boder .scale-point')].filter(vis)
            .map(h => { const r = h.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height)]; });
        return { frame: vis(frame),
                 frameSize: fr ? [Math.round(fr.width), Math.round(fr.height)] : null,
                 borderStyle: frame ? getComputedStyle(frame).borderStyle : null,
                 handles };
    }""")


def _wait_for_selected_layer(page: Page, timeout_ms: int) -> dict:
    """轮询等待图层选中态渲染完成（选中框 + 四角手柄同时可见）。"""
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    state = {}
    while page.evaluate("() => Date.now()") < deadline:
        state = _selected_layer_state(page)
        if state.get("frame") and len(state.get("handles") or []) >= 4:
            return state
        page.wait_for_timeout(500)
    return state


def _function_panel_state(page: Page) -> dict:
    """上传后「自动打开的功能面板」快照。

    - `.mobile-feature-workspace`（工具工作区面板，含标题如 Magic Eraser / Clothes Changer / Photo Enhancer）
    - 可见 `Crop` 按钮（PC 端 page_map 记录 youtube-banner-maker 上传后进入裁剪态：裁剪框 + Crop 按钮）
    """
    return page.evaluate("""() => {
        const vis = el => { if (!el) return false; const s = getComputedStyle(el), r = el.getBoundingClientRect();
            return s.display !== 'none' && s.visibility !== 'hidden' && r.width > 0 && r.height > 0; };
        const ws = document.querySelector('.mobile-feature-workspace');
        const wsCanvas = document.querySelector('.mobile-feature-workspace__canvas');
        const crops = [...document.querySelectorAll('button, [role=button], div, span')].filter(vis)
            .map(e => (e.innerText || '').trim()).filter(t => t === 'Crop');
        return { wsVisible: vis(ws), wsCanvasVisible: vis(wsCanvas),
                 wsText: ws ? (ws.innerText || '').replace(/\\n+/g, '|').slice(0, 220) : '',
                 cropButtonCount: crops.length };
    }""")


def _wait_for_function_panel(page: Page, title: str, timeout_ms: int) -> dict:
    """轮询等待工具功能面板出现并带上预期标题。"""
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    state = {}
    while page.evaluate("() => Date.now()") < deadline:
        state = _function_panel_state(page)
        if state.get("wsVisible") and title in (state.get("wsText") or ""):
            return state
        page.wait_for_timeout(500)
    return state


def _wait_for_crop_state(page: Page, timeout_ms: int) -> dict:
    """轮询等待裁剪态（可见 Crop 按钮）。"""
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    state = {}
    while page.evaluate("() => Date.now()") < deadline:
        state = _function_panel_state(page)
        if state.get("cropButtonCount", 0) >= 1:
            return state
        page.wait_for_timeout(500)
    return state


def _assert_function_panel(page: Page, case: dict) -> None:
    """断言「上传后自动打开了哪个功能面板」——用户要求的核心断言之一。"""
    kind = case.get("expected_function_panel_kind") or "none"
    title = case.get("expected_function_panel")
    timeout_ms = min(int(case.get("timeout_ms") or 20000), 20000)
    if kind == "workspace":
        state = _wait_for_function_panel(page, title, timeout_ms)
        assert title in (state.get("wsText") or ""), (
            f"{case['id']} 上传后应自动打开工具功能面板 {title!r}（.mobile-feature-workspace 标题匹配），"
            f"实测 wsVisible={state.get('wsVisible')} wsText={state.get('wsText')!r}"
        )
    elif kind == "crop":
        state = _wait_for_crop_state(page, timeout_ms)
        assert state.get("cropButtonCount", 0) >= 1, (
            f"{case['id']} 上传后应进入裁剪态（画布出现裁剪框 + 可见 Crop 按钮），"
            f"实测 cropButtonCount={state.get('cropButtonCount')} wsText={state.get('wsText')!r}"
        )
    else:
        state = _function_panel_state(page)
        assert not state.get("wsCanvasVisible"), (
            f"{case['id']} 该页上传后不应自动展开工具功能面板（预期为通用画布 + 底部面板），"
            f"实测 wsCanvasVisible={state.get('wsCanvasVisible')} wsText={state.get('wsText')!r}"
        )


def _wait_for_drawn(page: Page, timeout_ms: int) -> list:
    """轮询等待编辑器真正渲染：可见 canvas 或 >200x200 图层图片（移动端存在无文案 spinner 阶段）。"""
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    drawn = []
    while page.evaluate("() => Date.now()") < deadline:
        drawn = _drawn_sizes(page)
        if drawn:
            return drawn
        page.wait_for_timeout(1000)
    return drawn


def _wait_for_expected_panel(page: Page, expected: str, timeout_ms: int = 15000) -> None:
    """等工具预设生效：底部主面板的激活 tab 切到该工具专属面板。

    移动端进入 /create/edit 后，底部主面板先以通用 tab 渲染（实测首现时激活 Trending Tools），
    随后工具预设才切到该工具对应面板（如 Background 类页面切到 Background），实测差 200~900ms。
    面板一可见就读激活 tab 会读到过渡态，表现为同一页面在 Background / Trending Tools 间「波动」。
    """
    try:
        page.wait_for_function(
            """(want) => {
                const el = document.querySelector('.mobile-primary-panel__tab-text--active');
                return !!el && (el.innerText || '').trim() === want;
            }""",
            arg=expected,
            timeout=timeout_ms,
        )
    except Exception:
        pass


def _wait_for_stable_state(page: Page, case: dict) -> None:
    timeout = case["timeout_ms"]
    route = case["route"]
    if route in URL_PATTERNS:
        expect(page).to_have_url(re.compile(URL_PATTERNS[route]), timeout=timeout)
    _wait_processing_done(page, timeout)

    for keyword in case.get("required_keywords") or []:
        expect(page.locator("body")).to_contain_text(keyword, ignore_case=True, timeout=timeout)

    if route == "legacy_canvas":
        panel = page.locator(".mobile-primary-panel")
        expect(panel).to_be_visible(timeout=timeout)
        # 面板可见 != 工具预设已生效：先等默认面板激活，再断言（证据 panel_timing_probe_v3.json）
        expected_panel = case.get("default_panel")
        if expected_panel:
            _wait_for_expected_panel(page, expected_panel, timeout_ms=min(timeout, 15000))
        tabs = _mobile_panel_tabs(page)
        active = _mobile_panel_active_tab(page)
        assert tabs, f"{case['id']} 底部主面板应存在可识别 tab，实测 {tabs}"
        assert active, f"{case['id']} 底部主面板应有激活 tab（tab 列表 {tabs}）"
        assert active in tabs, (
            f"{case['id']} 激活 tab {active!r} 必须属于该页 tab 集合 {tabs}"
        )
        assert len(tabs) >= 3, f"{case['id']} 底部主面板 tab 数应 >=3，实测 {tabs}"
        if expected_panel:
            assert active == expected_panel, (
                f"{case['id']} 进入画布页后默认激活面板应为 {expected_panel!r}，"
                f"实测 {active!r}（tab 集合 {tabs}）"
            )

        # 图片图层默认选中（cases.md 预期：选择框/拖拽手柄可见）
        layer = _wait_for_selected_layer(page, timeout_ms=min(timeout, 15000))
        fsize = layer.get("frameSize") or [0, 0]
        assert layer.get("frame") and fsize[0] > 200 and fsize[1] > 200, (
            f"{case['id']} 上传后图片图层应默认选中（选择框 .choose-boder 可见且与画布同尺寸），"
            f"实测 frame={layer.get('frame')} frameSize={layer.get('frameSize')} "
            f"borderStyle={layer.get('borderStyle')!r} handles={layer.get('handles')}"
        )
        assert len(layer.get("handles") or []) >= 4, (
            f"{case['id']} 图片图层默认选中应显示四角缩放手柄（.choose-boder .scale-point ≥4），"
            f"实测 handles={layer.get('handles')} frameSize={layer.get('frameSize')}"
        )

    if route in ("legacy_canvas", "id_photo", "same_page_config", "same_page_result"):
        drawn = _wait_for_drawn(page, timeout)
        assert drawn, f"{case['id']} 应出现可见画布/图层（canvas 或大图），实测 {drawn}"

    if case.get("expected_canvas") and route == "legacy_canvas" and drawn:
        want = case["expected_canvas"][0]
        assert any(abs(d[1] - want[0]) <= 60 and abs(d[2] - want[1]) <= 60 for d in drawn), (
            f"{case['id']} 画布/图层尺寸应接近 {want}，实测 {drawn}"
        )

    _wait_networkidle(page, timeout=3000)


def _layout_signature(page: Page) -> dict:
    """布局指纹：canvas 总数 + 工作区画布/选中框/底部面板几何。"""
    return page.evaluate("""() => {
        const box = el => { if (!el) return null; const r = el.getBoundingClientRect();
            return [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)]; };
        return { canvases: document.querySelectorAll('canvas').length,
                 workspaceCanvas: box(document.querySelector('.mobile-feature-workspace__canvas')),
                 selection: box(document.querySelector('.choose-boder')),
                 panel: box(document.querySelector('.mobile-primary-panel')) };
    }""")


def _wait_for_layout_stable(page: Page, timeout_ms: int = 20000, quiet_ms: int = 800) -> dict:
    """等布局稳定：连续两次采样指纹一致才算稳定。

    证据（evidence/l2_008_trace.json）：进入 /create/edit 后主编辑器画布约 0.7s 出现、
    工具工作区画布（AI 换装 .mobile-feature-workspace__canvas）约 1.4s 才挂载；
    两者同时可见的过渡帧会让同一张照片在视口里出现两次（L2-008 截图曾如此），
    因此截图前必须等布局指纹稳定。
    """
    deadline = page.evaluate("() => Date.now()") + timeout_ms
    prev = None
    while page.evaluate("() => Date.now()") < deadline:
        cur = _layout_signature(page)
        if prev is not None and cur == prev:
            return cur
        prev = cur
        page.wait_for_timeout(quiet_ms)
    return prev or {}


def _capture(page: Page, case: dict, name_suffix: str = "final") -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    shot = SCREENSHOT_DIR / f"{case['id']}_{name_suffix}.png"
    page.screenshot(path=str(shot), full_page=False)
    allure.attach.file(str(shot), name=case["screenshot"] if name_suffix == "final" else f"{case['id']}_failure.png",
                       attachment_type=allure.attachment_type.PNG)
    return shot


def _run_case(page: Page, base_url: str, case: dict) -> None:
    try:
        with allure.step("打开移动端目标 SEO 页（复用会话级登录态）"):
            _open_target(page, base_url, case)
        with allure.step("点击移动端主上传按钮并选择 test_images/1K.jpg"):
            _start_upload(page, case)
        with allure.step("等待上传后稳定态（处理态结束 + 路由 + 面板 + 画布）"):
            _wait_for_stable_state(page, case)
        with allure.step("校验上传后自动打开的功能面板（工具面板 / 通用画布 / 裁剪态）"):
            _assert_function_panel(page, case)
        with allure.step("等待画布/面板布局稳定（避免截到工具工作区上滑入场过渡帧）"):
            _wait_for_layout_stable(page)
        with allure.step("截图记录"):
            _capture(page, case)
    except Exception:
        _capture(page, case, name_suffix="failure")
        raise


class TestMobileSeoMainUpload:
    """24 条移动端 SEO 主上传交互用例。"""


def _make_test(case_id: str):
    case = CASES[case_id]

    def _test(self, seo_mobile_session_page, base_url):
        _run_case(seo_mobile_session_page, base_url, case)

    _test.__name__ = "test_" + case_id.lower().replace("-", "_")
    _test.__doc__ = (
        f"PRD引用: cases.md {case_id}\n"
        "覆盖层级: L2\n"
        "前置条件: 移动端 390x844；会员账号 450832596@qq.com / 验证码 123456；素材 test_images/1K.jpg\n"
        "测试步骤:\n"
        f"1. 移动端打开 {case['page_path']}\n"
        "2. 点 Sign up → 填邮箱+验证码 123456 提交登录\n"
        "3. 点击主上传按钮\n"
        "4. 在 file chooser 选择 test_images/1K.jpg\n"
        "5. 等待上传后稳定态\n"
        f"等待策略: 处理态结束 + 路由到位 + 工具预设激活（等默认面板出现）；最多 {case['timeout_ms'] // 1000}s\n"
        f"预期结果: 路由={case['route']}；"
        f"功能面板断言={case.get('expected_function_panel') or '不自动展开工具面板'}"
        f"（kind={case.get('expected_function_panel_kind')}）；"
        f"底部激活 tab={case['default_panel']}（必须等于该值）；"
        "画布图片图层默认选中（选择框 .choose-boder + 四角缩放手柄）；"
        f"画布尺寸≈{case['expected_canvas']}；关键词={case['required_keywords']}\n"
        f"截图点: {case['screenshot']}"
    )
    bug = case.get("known_bug")
    if bug:
        _test = pytest.mark.xfail(
            strict=True,
            reason=(f"{bug.get('id')} {bug.get('summary')}（需求预期：{bug.get('requirement_expected')}）"),
        )(_test)
        _test = allure.label("known_bug", bug.get("id"))(_test)
        _test = allure.label("bug_status", str(bug.get("status")))(_test)
    _test = pytest.mark.login_required(_test)
    _test = pytest.mark.full(_test)
    _test = allure.feature("SEO 移动端主上传交互")(_test)
    _test = allure.story("移动端交互行为")(_test)
    _test = allure.severity(allure.severity_level.NORMAL)(_test)
    _test = allure.title(str(case.get("title") or case_id))(_test)
    _test = allure.label("case_id", case_id)(_test)
    _test = allure.label("layer", "L2")(_test)
    _test = allure.label("platform", "mobile")(_test)
    return _test


for _cid in CASES:
    setattr(TestMobileSeoMainUpload, "test_" + _cid.lower().replace("-", "_"), _make_test(_cid))
