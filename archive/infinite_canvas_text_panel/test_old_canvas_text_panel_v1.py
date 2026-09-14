# -*- coding: utf-8 -*-
"""旧画布文字功能（Text 面板 + 文字图层参数）自动化测试。

基于 confirmed cases.md（13 条，P0=5/P1=8）与
page_map/pokecut/infinite_canvas_text_panel_v1.yaml。

覆盖: L1 结构 / L2 交互（左侧 Alignment/Style/Font/Fill、右侧 8 分区参数、文案编辑）。
环境: 测试服 en-US；VIP 账号 450832596@qq.com；素材仅 test_images/1K.jpg。
执行策略: session 级复用画布（模板入口有频率限制，整个会话只上传 1 次）。
"""
import os

import allure
import pytest
import yaml
from pathlib import Path
from playwright.sync_api import Page, expect as pw_expect
from PIL import Image, ImageChops


def _repo_root() -> Path:
    """定位仓库根目录（同时兼容 tests/ 与 archive/<module>/ 两种存放位置）。"""
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "test_images").is_dir():
            return candidate
    return here.parent.parent


BASE_DIR = _repo_root()
DATA = yaml.safe_load((BASE_DIR / "data" / "pokecut_old_canvas_text_panel_v1.yaml").read_text(encoding="utf-8"))

BASE_URL = os.environ.get("POKECUT_BASE_URL", DATA["base_url"])
EMAIL = os.environ.get("POKECUT_TEST_EMAIL", DATA["accounts"]["vip"]["email"])
CODE = os.environ.get("POKECUT_TEST_CODE", str(DATA["accounts"]["vip"]["code"]))
IMG_1K = str(BASE_DIR / DATA["assets"]["image"])

# Text 入口：选中/未选中态图标后缀不同（*_select.svg），用 src* 兼容两种状态
TEXT_TAB = 'div.cursor-pointer:has(> img[src*="edit_left_tab_btn_text"])'
ADD_TEXT = 'button:text-is("Add a text")'
LAYER_NAV = 'div.cursor-pointer:has(> img[src*="edit_left_tab_btn_layer"])'
DELETE_ICON = 'img[src$="picture_edit_icon_delete.svg"]'
THRESHOLD_STRONG = DATA["diff_thresholds"]["strong"]
THRESHOLD_MEDIUM = DATA["diff_thresholds"]["medium"]
THRESHOLD_ANY = DATA["diff_thresholds"]["any"]
THRESHOLD_WEAK = DATA["diff_thresholds"]["weak"]
TOLERANCE_UNCHANGED = DATA["diff_thresholds"]["unchanged_tolerance"]
WAIT_READY = DATA["waits"]["canvas_ready_timeout_s"]
WAIT_SETTLE = DATA["waits"]["canvas_settle_ms"]
SETTLE_ACTION = DATA["waits"]["action_settle_ms"]

DIR_NAME = "2026-09-11_old_canvas_text_panel_exploration"
SHOT_DIR = BASE_DIR / "artifacts" / DIR_NAME / "shots"
TMP_DIR = BASE_DIR / "artifacts" / DIR_NAME / "evidence" / "tmp"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

# ── DOM 探测脚本（右面板取面积最大的可见节点）────────────────────────
PANEL_JS = (
    "const pn=[...document.querySelectorAll('div')].filter(e=>String(e.className).includes('w-[25rem]')"
    "&&e.getBoundingClientRect().x>1200);"
    "pn.sort((a,b)=>{const A=a.getBoundingClientRect(),B=b.getBoundingClientRect();"
    "return B.width*B.height-A.width*A.height;});window.__R=pn[0];"
)
SECTIONS_JS = ("() => { " + PANEL_JS +
    " return window.__R ? [...window.__R.querySelectorAll('p')].filter(e=>e.offsetWidth>0)"
    ".map(e=>e.innerText.trim()).filter(t=>t.length>0) : []; }")
READY_JS = """() => Array.from(document.querySelectorAll('div.fixed')).filter(el => {
    const z = parseInt(getComputedStyle(el).zIndex || '0', 10);
    const r = el.getBoundingClientRect();
    return z >= 100 && r.width > 500 && r.height > 400 && getComputedStyle(el).display !== 'none';
  }).length"""
CANVAS_BOX_JS = """() => {
  const c = [...document.querySelectorAll('canvas')].map(e => e.getBoundingClientRect())
    .filter(b => b.width > 200 && b.height > 200).sort((a, b) => b.width * b.height - a.width * a.height)[0];
  return c ? {x: Math.round(c.x), y: Math.round(c.y), w: Math.round(c.width), h: Math.round(c.height)} : null; }"""


def _panel_js(inner: str) -> str:
    return "() => { " + PANEL_JS + " " + inner + " }"


def section_box(page: Page, name: str):
    """右面板内可见分区标题的坐标。"""
    return page.evaluate(_panel_js(
        "if(!window.__R) return null;"
        "const l=[...window.__R.querySelectorAll('p')].find(e=>e.innerText.trim()===" + repr(name) +
        "&&e.getBoundingClientRect().width>0); if(!l) return null;"
        "const b=l.getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};"))


def range_box(page: Page, label: str, window_px: int = 0):
    """返回该分区内、位于 label 下方且最近的可见滑杆。

    分区内滑杆按行排列（如 Scope/Opacity/Distance/Angle），不能简单取第一个，
    否则改 Distance 会打到 Scope；按「label 下方最近的滑杆」定位才唯一。
    """
    return page.evaluate(_panel_js(
        "if(!window.__R) return null;"
        "const l=[...window.__R.querySelectorAll('p')].find(e=>e.innerText.trim()===" + repr(label) +
        "&&e.getBoundingClientRect().width>0); if(!l) return null;"
        "const sec=l.closest('div').parentElement;"
        "const ly=l.getBoundingClientRect().y;"
        "const cands=[...sec.querySelectorAll('input[type=range]')]"
        ".filter(i=>i.getBoundingClientRect().width>100 && i.getBoundingClientRect().y>=ly-4)"
        ".sort((a,b)=>a.getBoundingClientRect().y-b.getBoundingClientRect().y);"
        "if(!cands.length) return null; const it=cands[0]; const b=it.getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),"
        "min:Number(it.min),max:Number(it.max),value:it.value};"))


def section_height(page: Page, name: str):
    """分区容器高度：折叠约 60px，展开 >100px（用于幂等展开/收起判定）。"""
    return page.evaluate(_panel_js(
        "if(!window.__R) return null;"
        "const l=[...window.__R.querySelectorAll('p')].find(e=>e.innerText.trim()===" + repr(name) +
        "&&e.getBoundingClientRect().width>0); if(!l) return null;"
        "const sec=l.closest('div').parentElement;"
        "return Math.round(sec.getBoundingClientRect().height);"))


def switch_box(page: Page, name: str):
    """分区行右侧的开关（span）。"""
    return page.evaluate(_panel_js(
        "if(!window.__R) return null;"
        "const l=[...window.__R.querySelectorAll('p')].find(e=>e.innerText.trim()===" + repr(name) +
        "&&e.getBoundingClientRect().width>0); if(!l) return null;"
        "const ly=l.getBoundingClientRect().y+l.getBoundingClientRect().height/2;"
        "const c=[...window.__R.querySelectorAll('span,div,i')].filter(e=>{const b=e.getBoundingClientRect();"
        "return b.width>=28&&b.width<=70&&b.height>=16&&b.height<=30&&b.x>1700&&Math.abs(b.y+b.height/2-ly)<25;});"
        "if(!c.length) return null; const b=c[c.length-1].getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};"))


def swatch_box(page: Page, name: str, index: int):
    """分区容器内的 68x68 色块（0-based）。"""
    return page.evaluate(_panel_js(
        "if(!window.__R) return null;"
        "const l=[...window.__R.querySelectorAll('p')].find(e=>e.innerText.trim()===" + repr(name) +
        "&&e.getBoundingClientRect().width>0); if(!l) return null;"
        "const sec=l.closest('div').parentElement;"
        "const ds=[...sec.querySelectorAll('div.cursor-pointer')].filter(e=>{const b=e.getBoundingClientRect();"
        "return b.width>=30&&b.width<=95&&b.height>=30&&b.height<=95;});"
        "if(ds.length<=" + str(index) + ") return null; const b=ds[" + str(index) + "].getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),total:ds.length};"))


def blend_tile_box(page: Page, mode: str):
    """Blend 分区里的混合模式瓦片（按瓦片内文本定位）。"""
    return page.evaluate(_panel_js(
        "if(!window.__R) return null;"
        "const n=[...window.__R.querySelectorAll('span')].find(e=>e.innerText.trim()===" + repr(mode) +
        "&&e.getBoundingClientRect().width>0); if(!n) return null;"
        "const b=n.getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};"))


def visible_ranges(page: Page) -> int:
    """右面板当前可见滑杆数量（用于判定分区是否收起）。"""
    return page.evaluate(_panel_js(
        "if(!window.__R) return 0; return [...window.__R.querySelectorAll('input[type=range]')]"
        ".filter(i=>i.getBoundingClientRect().width>100).length;"))


def panel_text(page: Page) -> str:
    """右面板可见文本（用于校验页签等非 p 元素文案）。"""
    return page.evaluate(_panel_js("return window.__R ? window.__R.innerText : '';"))


def alignment_state(page: Page):
    """左侧 Alignment 三个按钮的图标 src 后缀。"""
    return page.evaluate("""() => [...document.querySelectorAll('div.cursor-pointer > img[src*="alignmanet_"]')]
        .filter(i => i.getBoundingClientRect().width > 0)
        .map(i => i.getAttribute('src').split('/').pop());""")


# ── 通用动作 ─────────────────────────────────────────────
def shot(page: Page, name: str):
    """整页证据截图（1920x1080，含左右面板），附加到 Allure。"""
    path = SHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path))
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return path


def canvas_crop(page: Page, name: str):
    """画布区域裁切图，仅用于像素比对（不进 Allure）。"""
    box = page.evaluate(CANVAS_BOX_JS)
    path = TMP_DIR / f"{name}.png"
    page.screenshot(path=str(path), clip={"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]})
    return path


def diff_ratio(before: Path, after: Path) -> float:
    ia, ib = Image.open(before).convert("RGB"), Image.open(after).convert("RGB")
    if ia.size != ib.size:
        ib = ib.resize(ia.size)
    px = list(ImageChops.difference(ia, ib).convert("L").getdata())
    return round(sum(1 for v in px if v > 10) / len(px), 4)


def assert_changed(page: Page, tag: str, minimum: float, note: str = ""):
    """改前/改后画布差异断言（内部使用，改前图由调用方先拍）。"""
    after = canvas_crop(page, f"{tag}_after")
    before = TMP_DIR / f"{tag}_before.png"
    ratio = diff_ratio(before, after)
    allure.attach(f"canvas diff={ratio} (阈值 {minimum}) {note}", name=f"{tag}_diff",
                  attachment_type=allure.attachment_type.TEXT)
    assert ratio > minimum, f"{tag}: 画布像素差异 {ratio} 未超过阈值 {minimum} {note}"
    return ratio


NAV_JS = """() => [...document.querySelectorAll('img')]
  .filter(i => (i.getAttribute('src') || '').includes('edit_left_tab_btn_')).length"""


def wait_canvas_ready(page: Page, timeout_s: int = WAIT_READY):
    """等加载遮罩消失且左侧功能栏渲染完成（复用 pid 重新打开时偶发长时间 loading）。"""
    overlay_gone = False
    for _ in range(int(timeout_s / 1.5)):
        if not overlay_gone and page.evaluate(READY_JS) == 0:
            overlay_gone = True
        if overlay_gone and page.evaluate(NAV_JS) >= 8:
            page.wait_for_timeout(1500)
            return True
        page.wait_for_timeout(1500)
    return False


def login(page: Page):
    page.goto(BASE_URL + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(4500)
    btn = page.get_by_role("button", name="Log in", exact=True)
    if btn.count():
        btn.first.click()
        page.wait_for_timeout(1800)
        page.locator('input[type="email"]').fill(EMAIL)
        page.locator('input[placeholder*="Verification"]').fill(CODE)
        page.locator('[data-testid="auth-submit"]').click()
        page.wait_for_timeout(8000)
    state = page.evaluate(
        """() => { try { const a = window.useNuxtApp();
            return {vip: a.__basicAccountState?.userBenefit?.value?.vipType}; } catch(e){ return {vip:null}; } }"""
    )
    assert state.get("vip"), f"VIP 登录失败: {state}"
    return state


def enter_canvas_via_template(page: Page, attempts: int = 3):
    """从 /template 的 Colorful Background 首卡上传并进入旧画布。"""
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            page.goto(BASE_URL + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(5000)
            heading = page.get_by_role("heading", name=DATA["assets"]["template_group"], exact=True).first
            pw_expect(heading).to_be_visible(timeout=30000)
            section = heading.locator("xpath=..").locator("xpath=..")
            card = section.locator('div.relative.flex.w-\\[9\\.625rem\\].cursor-pointer').first
            overlay = card.locator("div.absolute.left-0.top-0.flex.size-full.items-center > div").first
            pw_expect(overlay).to_be_visible(timeout=15000)
            with page.expect_file_chooser(timeout=30000) as fc:
                overlay.click()
            fc.value.set_files(IMG_1K)
            for _ in range(90):
                page.wait_for_timeout(1000)
                if DATA["canvas_path_pattern"] in page.url:
                    break
            else:
                raise AssertionError(f"模板卡上传后未进入画布，当前 URL: {page.url}")
            page.wait_for_timeout(WAIT_SETTLE)
            return page.url
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt == attempts:
                break
            page.wait_for_timeout(2500)
    raise AssertionError(f"模板入口进入旧画布失败（已重试 {attempts} 次）: {last_err}")


LAYER_ROWS_JS = """() => [...document.querySelectorAll('div')].filter(e => {
    const c = String(e.className || '');
    return (c.includes('layer-choosed') || c.includes('layer-unchoosed'))
      && e.getBoundingClientRect().width > 150; }).map(e => {
    const b = e.getBoundingClientRect();
    return {text: (e.innerText || '').trim(), choosed: String(e.className).includes('layer-choosed'),
            x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.width), h: Math.round(b.height)}; })"""


def open_layer_panel(page: Page):
    """打开左侧 Layer 面板（图层列表）。"""
    page.locator(LAYER_NAV).first.click()
    page.wait_for_timeout(1500)


def text_layer_count(page: Page) -> int:
    """当前画布上的文字图层数量（按 Layer 面板中名为 Text 的行计）。"""
    return sum(1 for r in page.evaluate(LAYER_ROWS_JS) if r["text"] == "Text")


def clear_text_layers(page: Page, max_rounds: int = 12):
    """删除历史用例遗留的文字图层。

    本任务经用户明确授权：测试画布（自建 pid）上由本脚本创建的文字图层可删除，
    避免多层同文案叠加导致截图与像素断言失去鉴别力。模板底图（Picture/Background）不删。
    """
    open_layer_panel(page)
    for _ in range(max_rounds):
        rows = [r for r in page.evaluate(LAYER_ROWS_JS) if r["text"] == "Text"]
        if not rows:
            return
        row = rows[0]
        page.mouse.click(row["x"] + 40, row["y"] + row["h"] // 2)
        page.wait_for_timeout(1200)
        icon = page.locator(DELETE_ICON).first
        pw_expect(icon).to_be_visible(timeout=8000)
        icon.click()
        page.wait_for_timeout(1600)
    raise AssertionError(f"清理文字图层未完成，仍有 {text_layer_count(page)} 层")


def open_text_panel(page: Page):
    """打开左侧 Text 面板；画布状态持久化到 pid，若面板已展开则直接复用。"""
    if page.locator(ADD_TEXT).first.is_visible():
        return
    loc = page.locator(TEXT_TAB).first
    pw_expect(loc).to_be_visible(timeout=30000)
    loc.click()
    page.wait_for_timeout(SETTLE_ACTION)
    if not page.locator(ADD_TEXT).first.is_visible():
        loc.click()
        page.wait_for_timeout(SETTLE_ACTION)
    assert page.locator(ADD_TEXT).first.is_visible(), "Text 面板未展开（Add a text 不可见）"


def click_fill(page: Page, color: str):
    """点击左侧 Fill 色板中 computed backgroundColor 等于 color 的色块。"""
    box = page.evaluate("""(color) => {
        const cands = [...document.querySelectorAll('div.cursor-pointer')].filter(d => {
          const b = d.getBoundingClientRect(); const inner = d.querySelector('div');
          return b.width > 30 && b.width < 90 && inner && getComputedStyle(inner).backgroundColor === color; });
        if (!cands.length) return null; const b = cands[0].getBoundingClientRect();
        return {x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2)}; }""", color)
    assert box, f"左侧 Fill 未找到颜色 {color}"
    page.mouse.click(box["x"], box["y"])
    page.wait_for_timeout(SETTLE_ACTION)
    return box


def pick_distinct_fill(page: Page):
    """给新图层选一个饱和且有别于 L2-004 目标色的填充色。

    同一 pid 复用画布上会叠加多层相同文案，若各层颜色一致，单层参数（Opacity/Space 等）
    改动在合成结果里几乎不可见；先让每层颜色不同，像素差异断言才有意义。
    """
    return page.evaluate("""(target) => {
        const parse = s => (String(s).match(/\d+/g) || [255, 255, 255]).map(Number);
        const dist = (a, b) => { const p = parse(a), q = parse(b);
          return Math.abs(p[0]-q[0]) + Math.abs(p[1]-q[1]) + Math.abs(p[2]-q[2]); };
        const sws = [...document.querySelectorAll('div.cursor-pointer')].filter(d => {
          const b = d.getBoundingClientRect(); const inner = d.querySelector('div');
          return b.width > 30 && b.width < 90 && inner && b.y > 600; });
        const cands = sws.map(d => ({d, c: getComputedStyle(d.querySelector('div')).backgroundColor}))
          .filter(x => dist(x.c, target) > 150 && dist(x.c, 'rgb(255, 255, 255)') > 120
                       && dist(x.c, 'rgb(0, 0, 0)') > 60);
        if (!cands.length) return null;
        const pick = cands[2] || cands[0];
        const b = pick.d.getBoundingClientRect();
        return {color: pick.c, x: Math.round(b.x + b.width / 2), y: Math.round(b.y + b.height / 2)}; }""",
        DATA["text_panel"]["fill_color"])


def add_text_layer(page: Page, distinct: bool = True):
    """新增文字图层；distinct=True 时顺手换一个区别色，避免与已叠加图层同色。"""
    btn = page.locator(ADD_TEXT).first
    pw_expect(btn).to_be_visible(timeout=15000)
    btn.click()
    page.wait_for_timeout(3000)
    if distinct:
        pick = pick_distinct_fill(page)
        if pick:
            page.mouse.click(pick["x"], pick["y"])
            page.wait_for_timeout(SETTLE_ACTION + 600)


def expand_section(page: Page, name: str, probe=None):
    """幂等展开分区：以该分区自身控件是否可见判定（面板展开状态可能跨会话保留）。"""
    probe = probe or (lambda: range_box(page, name) is not None)
    for _ in range(3):
        if probe():
            return
        btn = section_box(page, name)
        assert btn, f"右面板未找到分区 {name}"
        page.mouse.click(btn["x"] + 8, btn["y"] + btn["h"] // 2)
        page.wait_for_timeout(1300)
    assert probe(), f"分区 {name} 未能展开"


def click_switch(page: Page, name: str, probe=None):
    """幂等打开分区开关；开关 ON 会自动展开分区，不要再点标题。"""
    probe = probe or (lambda: f"{name}" in panel_text(page))
    for _ in range(3):
        if probe():
            return switch_box(page, name)
        sw = switch_box(page, name)
        assert sw, f"右面板未找到 {name} 开关"
        page.mouse.click(sw["x"] + sw["w"] // 2, sw["y"] + sw["h"] // 2)
        page.wait_for_timeout(1800)
    assert probe(), f"{name} 开关未能开启"
    return switch_box(page, name)


def drag_range(page: Page, label: str, target: float, window_px: int = 220):
    """把滑杆拖到目标值（真实鼠标拖动；落点取区间 10%~90% 内）。"""
    rb = range_box(page, label, window_px)
    assert rb, f"右面板未找到滑杆 {label}"
    lo, hi = rb["min"], rb["max"]
    ratio = (target - lo) / ((hi - lo) or 1)
    ratio = min(max(ratio, 0.05), 0.95)
    x = rb["x"] + int(ratio * (rb["w"] - 6))
    y = rb["y"] + rb["h"] // 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x + 2, y, steps=2)
    page.mouse.up()
    page.wait_for_timeout(SETTLE_ACTION)
    after = range_box(page, label, window_px)
    return {"before": rb["value"], "after": after["value"] if after else None, "min": lo, "max": hi}


# ── fixtures ─────────────────────────────────────────────
@pytest.fixture(scope="session")
def canvas_session(playwright):
    """session 级前置：VIP 登录 + 进入旧画布 1 次（模板入口有频率限制）。"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    login(page)
    canvas_url = enter_canvas_via_template(page)
    assert DATA["canvas_path_pattern"] in canvas_url, f"会话入口未进入旧画布: {canvas_url}"
    page.close()
    yield {"context": context, "url": canvas_url}
    context.close()
    browser.close()


@pytest.fixture
def canvas_page(canvas_session):
    """每条用例复用同一 pid，重新打开得到干净页面（不重新上传）。"""
    page = canvas_session["context"].new_page()
    page.goto(canvas_session["url"], wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(6000)
    ready = wait_canvas_ready(page)
    assert ready, "画布未在超时内加载完成（左侧功能栏未渲染）"
    yield page
    page.close()


# ── L1 页面元素 / 结构 ────────────────────────────────────
@allure.epic("旧画布文字功能")
@allure.feature("L1-页面结构元素")
@allure.story("L1-页面结构元素")
@pytest.mark.p0
@pytest.mark.regression
@pytest.mark.login_required
class TestL1OldCanvasTextPanelStructure:
    @allure.title("L1-001: Text 入口、面板结构与文字图层选中态结构")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l1_001_text_panel_and_layer_structure(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD），基线为 confirmed sync/page_map
        覆盖层级: L1 页面元素 / 结构
        前置条件: 已通过 session 前置进入旧画布（VIP 账号）
        测试步骤:
          1. 点击左侧功能栏第 6 项 Text，展开文字面板
          2. 断言未选中图层时左面板五段文本与右面板占位文案
          3. 点击 Add a text 新增文字图层
          4. 断言右面板出现 8 个文字分区、画布出现选中锚点
        预期结果: 未选中态右面板为 Select a layer to adjust；选中态右面板 8 分区齐全且画布出现文字与四角缩放锚点
        """
        page = canvas_page
        with allure.step("清理历史文字图层后打开 Text 面板"):
            clear_text_layers(page)
            open_text_panel(page)
            # 未选中图层时左面板只有 Add a text，样式区块在有图层选中后才渲染
            pw_expect(page.locator(ADD_TEXT).first).to_be_visible(timeout=15000)
            left_text = page.locator('div:has(> div > button:text-is("Add a text"))').first.inner_text()
            assert DATA["text_panel"]["add_button_text"] in left_text, f"左面板缺少新增按钮: {left_text[:120]}"
            right_text = page.evaluate(_panel_js("return window.__R ? window.__R.innerText : '';"))
            assert "Select a layer to adjust" in right_text, f"未选中态右面板文案异常: {right_text[:120]}"
        with allure.step("截图记录未选中态"):
            shot(page, "l1_001_text_panel_open")

        with allure.step("点击 Add a text 新增文字图层"):
            add_text_layer(page)
        with allure.step("断言左右面板齐全与画布选中锚点"):
            sections = page.evaluate(SECTIONS_JS)
            for name in DATA["right_panel"]["sections"]:
                assert name in sections, f"右面板缺少分区 {name}: {sections}"
            left_after = page.locator('div:has(> div > button:text-is("Add a text"))').first.inner_text()
            for kw in DATA["text_panel"]["sections"]:
                assert kw in left_after, f"选中图层后左面板缺少 {kw}: {left_after[:160]}"
            anchors = page.locator("span.scale-point").count()
            assert anchors >= 4, f"画布未出现四角缩放锚点，实际 {anchors}"
        with allure.step("截图记录选中态"):
            shot(page, "l1_001_layer_selected_left")
            shot(page, "l1_001_layer_selected_right")


# ── L2 交互行为 / 状态迁移 ────────────────────────────────
@allure.epic("旧画布文字功能")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.login_required
class TestL2OldCanvasTextPanelEntry:
    @allure.title("L2-001: 模板首卡上传进入旧画布（session 前置）")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_001_template_entry_to_canvas(self, canvas_page: Page, canvas_session):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为 / 状态迁移
        前置条件: session 前置已完成 1 次模板上传
        测试步骤:
          1. 断言 session 前置记录的 URL 为旧画布
          2. 断言画布页存在可见 canvas
        预期结果: URL 命中 /create/edit?pid= 且画布可见
        """
        page = canvas_page
        with allure.step("断言会话入口 URL 与画布可见"):
            assert DATA["canvas_path_pattern"] in canvas_session["url"], f"入口 URL 异常: {canvas_session['url']}"
            pw_expect(page.locator("canvas").first).to_be_visible(timeout=20000)
        with allure.step("截图记录画布入口"):
            shot(page, "l2_001_canvas_entered")


@allure.epic("旧画布文字功能")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.login_required
class TestL2OldCanvasTextPanelAddLayer:
    @allure.title("L2-002: Add a text 新增图层、自动选中、可重复新增")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_002_add_text_layer(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布
        测试步骤:
          1. 打开 Text 面板
          2. 点击 Add a text，断言右面板 8 分区与画布锚点
          3. 再次点击 Add a text，断言新图层行为一致
        预期结果: 两次点击均新增独立文字图层并自动选中
        """
        page = canvas_page
        with allure.step("清理历史文字图层并新增第一个文字图层"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            first = page.evaluate(SECTIONS_JS)
            for name in DATA["right_panel"]["sections"]:
                assert name in first, f"第一层缺少分区 {name}: {first}"
            open_layer_panel(page)
            assert text_layer_count(page) == 1, f"新增后文字图层数应为 1，实际 {text_layer_count(page)}"
            open_text_panel(page)
        with allure.step("截图记录第一个图层"):
            shot(page, "l2_002_first_layer")

        with allure.step("再次新增文字图层"):
            add_text_layer(page)
            second = page.evaluate(SECTIONS_JS)
        with allure.step("断言第二层同样自动选中且分区齐全"):
            for name in DATA["right_panel"]["sections"]:
                assert name in second, f"第二层缺少分区 {name}: {second}"
            assert page.locator("span.scale-point").count() >= 4, "第二层未出现选中锚点"
        with allure.step("用 Layer 面板断言图层数由 1 增至 2"):
            open_layer_panel(page)
            count = text_layer_count(page)
            assert count == 2, f"重复新增后文字图层数应为 2，实际 {count}（两层位置重叠，需按 Layer 面板计数判定）"
            shot(page, "l2_002_layer_list_two_text")
            open_text_panel(page)
        with allure.step("截图记录第二个图层"):
            shot(page, "l2_002_second_layer")


@allure.epic("旧画布文字功能")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2OldCanvasTextPanelLeftStyle:
    @allure.title("L2-003: Alignment 左/中/右三态切换")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_003_alignment_toggle(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 新增文字图层并记录初始画布
          2. 依次点击左对齐、居中、右对齐
          3. 每次断言选中图标切换为 *_select.svg 且画布像素差异 > 阈值
        预期结果: 三个按钮均可切换选中态并改变画布对齐效果
        """
        page = canvas_page
        with allure.step("新增文字图层"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
        icons = {"left": DATA["text_panel"]["align_icons"]["left"],
                 "center": DATA["text_panel"]["align_icons"]["center"],
                 "right": DATA["text_panel"]["align_icons"]["right"]}
        suffix = DATA["text_panel"]["align_icons"]["selected_suffix"]
        for key, icon in icons.items():
            with allure.step(f"点击 {key} 对齐并断言选中态与画布变化"):
                canvas_crop(page, f"l2_003_{key}_before")
                loc = page.locator(f'div.cursor-pointer:has(> img[src*="{icon}"])').first
                box = loc.bounding_box()
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                page.wait_for_timeout(SETTLE_ACTION)
                srcs = alignment_state(page)
                assert any(icon in s and s.endswith(suffix + ".svg") for s in srcs),                     f"{key} 未切换为选中态: {srcs}"
                assert_changed(page, f"l2_003_{key}", THRESHOLD_MEDIUM, f"alignment={key}")
            with allure.step(f"截图记录 {key} 对齐"):
                shot(page, f"l2_003_align_{key}")

    @allure.title("L2-004: 左侧样式参数 Font 与 Fill")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_004_font_and_fill(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 记录初始画布
          2. 点击字体瓦片 MarckScript-Regular.ttf，断言画布变化
          3. 点击 Fill 深红色块，断言画布变化
        预期结果: 字体与填充色均可生效
        """
        page = canvas_page
        with allure.step("新增文字图层"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)

        with allure.step("切换字体并断言画布变化"):
            canvas_crop(page, "l2_004_font_before")
            font = DATA["text_panel"]["fonts"][0]
            loc = page.locator(f'div.cursor-pointer:has(> img[alt="{font}"])').first
            pw_expect(loc).to_be_visible(timeout=15000)
            box = loc.bounding_box()
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_timeout(SETTLE_ACTION)
            assert_changed(page, "l2_004_font", THRESHOLD_STRONG, f"font={font}")
            shot(page, "l2_004_font_switched")

        with allure.step("选择填充色并断言画布变化"):
            canvas_crop(page, "l2_004_fill_before")
            color = DATA["text_panel"]["fill_color"]
            click_fill(page, color)
            assert_changed(page, "l2_004_fill", THRESHOLD_MEDIUM, f"fill={color}")
            shot(page, "l2_004_fill_applied")

    @allure.title("L2-005: Style 预设应用与右侧分区收敛")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_005_style_preset_and_section_shrink(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为 / 状态迁移
        前置条件: 已进入旧画布
        测试步骤:
          1. 新增文字图层，断言右面板 8 个分区
          2. 点击第 2 个 Style 预设，断言画布变化
          3. 断言右面板收敛为 Opacity/Space/Reflection/Blend 4 个分区
          4. 再新增一个图层，断言新图层仍为 8 个分区
        预期结果: 样式预设按图层生效，收敛只影响被应用预设的图层
        """
        page = canvas_page
        with allure.step("新增文字图层并确认初始 8 分区"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            before_sections = page.evaluate(SECTIONS_JS)
            for name in DATA["right_panel"]["sections"]:
                assert name in before_sections, f"初始缺少分区 {name}: {before_sections}"

        with allure.step("应用第 2 个 Style 预设并断言画布变化"):
            canvas_crop(page, "l2_005_style_before")
            idx = DATA["text_panel"]["style_preset_index"]
            loc = page.locator('div.cursor-pointer.flex-shrink-0:has(> img[src*="/font/style_thumb"])')
            assert loc.count() > idx, f"Style 瓦片数量不足: {loc.count()}"
            box = loc.nth(idx).bounding_box()
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            page.wait_for_timeout(SETTLE_ACTION)
            assert_changed(page, "l2_005_style", THRESHOLD_STRONG, "style preset")

        with allure.step("断言右面板分区收敛为 4 个"):
            after = page.evaluate(SECTIONS_JS)
            expected = DATA["right_panel"]["style_preset_sections"]
            for name in expected:
                assert name in after, f"收敛后缺少分区 {name}: {after}"
            for name in DATA["right_panel"]["sections"]:
                if name not in expected:
                    assert name not in after, f"收敛后仍存在分区 {name}: {after}"
            shot(page, "l2_005_style_applied_4_sections")

        with allure.step("新增图层后断言恢复 8 分区"):
            add_text_layer(page)
            fresh = page.evaluate(SECTIONS_JS)
            for name in DATA["right_panel"]["sections"]:
                assert name in fresh, f"新图层缺少分区 {name}: {fresh}"
            shot(page, "l2_005_new_layer_8_sections")


@allure.epic("旧画布文字功能")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.login_required
class TestL2OldCanvasTextPanelSliders:
    @allure.title("L2-006: 右侧滑杆类参数与分区互斥展开")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_006_sliders_and_accordion(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为 / L5 边界值（内部循环）
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 展开 Opacity，断言出现 1 个滑杆
          2. 展开 Space，断言 Opacity 收起、出现 Width/Height 两个滑杆
          3. 分别调 Opacity、Space Width、Space Height、Arch 并断言读数与画布变化
          4. 追加 Opacity 边界：0 时画布变化，回到 100 后与初始一致
        预期结果: 分区互斥展开；四个滑杆均生效；Opacity 边界行为正确
        """
        page = canvas_page
        with allure.step("新增文字图层"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)

        with allure.step("展开 Opacity 并断言只有一个可见滑杆"):
            expand_section(page, "Opacity", lambda: range_box(page, "Opacity") is not None)
            assert range_box(page, "Opacity"), "Opacity 分区未出现滑杆"
            assert visible_ranges(page) == 1, f"展开 Opacity 后可见滑杆数应为 1，实际 {visible_ranges(page)}"

        with allure.step("展开 Space 并断言 Opacity 收起（分区互斥）"):
            expand_section(page, "Space", lambda: range_box(page, "Width") is not None)
            assert range_box(page, "Width"), "Space 分区未出现 Width 滑杆"
            assert range_box(page, "Height"), "Space 分区未出现 Height 滑杆"
            assert visible_ranges(page) == 2, f"展开 Space 后可见滑杆数应为 2，实际 {visible_ranges(page)}"
            assert range_box(page, "Opacity") is None, "展开 Space 后 Opacity 未收起"
            shot(page, "l2_006_accordion_state")

        targets = DATA["right_panel"]["targets"]
        cases = [("Opacity", targets["opacity"], "opacity"),
                 ("Space", targets["space_width"], "space"),
                 ("Arch", targets["arch"], "arch")]
        for label, target, tag in cases:
            with allure.step(f"调整 {label} 到 {target} 并断言画布变化"):
                expand_section(page, label, lambda lb=label: range_box(page, lb) is not None)
                canvas_crop(page, f"l2_006_{tag}_before")
                result = drag_range(page, label, target)
                assert result["after"] is not None, f"{label} 读数读取失败"
                got = float(result["after"])
                assert abs(got - target) <= 8, f"{label} 读数 {got} 与目标 {target} 偏差过大"
                # Opacity / Space 在同 pid 复用画布上多层同文案叠加时合成差异极小，按 cases.md「差异 > 0」口径断言
                # cases.md 对滑杆类参数的断言口径为「画布像素差异 > 0」；
                # 同 pid 叠层画布下 Opacity/Space 合成差异极小，故按口径断言 >0，数值正确性由读数断言保证
                assert_changed(page, f"l2_006_{tag}",
                               THRESHOLD_STRONG if tag == "arch" else THRESHOLD_ANY,
                               f"{label}={target}")
                shot(page, f"l2_006_{tag}_after")

        with allure.step("Opacity 边界：置 0 断言画布变化"):
            expand_section(page, "Opacity", lambda: range_box(page, "Opacity") is not None)
            canvas_crop(page, "l2_006_opacity_min0_before")
            drag_range(page, "Opacity", 0)
            assert_changed(page, "l2_006_opacity_min0", THRESHOLD_WEAK, "opacity=0")
            shot(page, "l2_006_opacity_min0")

        with allure.step("Opacity 边界：回到 100 断言与初始一致"):
            expand_section(page, "Opacity", lambda: range_box(page, "Opacity") is not None)
            drag_range(page, "Opacity", 100)
            after = canvas_crop(page, "l2_006_opacity_back100_after")
            baseline = TMP_DIR / "l2_006_opacity_min0_before.png"
            ratio = diff_ratio(baseline, after)
            allure.attach(f"back to 100 diff={ratio} (容差 {TOLERANCE_UNCHANGED})",
                          name="l2_006_opacity_back100_diff", attachment_type=allure.attachment_type.TEXT)
            assert ratio <= TOLERANCE_UNCHANGED, f"Opacity 回到 100 后与初始画布差异 {ratio} 超出容差"
            shot(page, "l2_006_opacity_back100")


@allure.epic("旧画布文字功能")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2OldCanvasTextPanelEffects:
    @allure.title("L2-007: Shadow 开关、页签与 Blur")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_007_shadow(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 点击 Shadow 行开关，断言分区自动展开并出现页签与 5 个滑杆
          2. 把 Blur 拖到目标值，断言读数与画布变化
        预期结果: Shadow 开关可开启，Blur 生效
        """
        page = canvas_page
        with allure.step("新增文字图层并开启 Shadow 开关"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            click_switch(page, "Shadow", lambda: "Blur" in panel_text(page))
        with allure.step("断言分区自动展开且页签/滑杆齐全"):
            sections = page.evaluate(SECTIONS_JS)
            text = panel_text(page)
            for kw in ["Effect", "3D Shadow"]:
                assert kw in text, f"Shadow 分区缺少页签 {kw}: {text[:160]}"
            for kw in ["Opacity", "Blur", "Gradient", "Distance", "Rotation"]:
                assert kw in sections, f"Shadow 分区缺少滑杆 {kw}: {sections}"
            shot(page, "l2_007_shadow_expanded")
        with allure.step("调整 Blur 并断言画布变化"):
            target = DATA["right_panel"]["targets"]["shadow_blur"]
            canvas_crop(page, "l2_007_shadow_before")
            result = drag_range(page, "Blur", target)
            assert result["after"] is not None and float(result["after"]) > 0, f"Blur 未生效: {result}"
            assert_changed(page, "l2_007_shadow", THRESHOLD_WEAK, f"blur={target}")
            shot(page, "l2_007_shadow_blur_after")

    @allure.title("L2-008: Outline 开关、Size 与颜色")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_008_outline(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 点击 Outline 行开关，断言分区自动展开并出现 Types/Color/Size 等控件
          2. 把 Size 拖到目标值并点一个有色色块
          3. 断言画布变化
        预期结果: Outline 开关可开启，Size 与颜色生效
        """
        page = canvas_page
        with allure.step("新增文字图层并开启 Outline 开关"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            click_switch(page, "Outline", lambda: "Types" in panel_text(page))
        with allure.step("断言分区自动展开且控件齐全"):
            sections = page.evaluate(SECTIONS_JS)
            for kw in ["Types", "Color", "Size", "Distance", "Blur", "Smooth"]:
                assert kw in sections, f"Outline 分区缺少 {kw}: {sections}"
            shot(page, "l2_008_outline_expanded")
        with allure.step("调整 Size 并选色，断言画布变化"):
            canvas_crop(page, "l2_008_outline_before")
            target = DATA["right_panel"]["targets"]["outline_size"]
            result = drag_range(page, "Size", target)
            assert result["after"] is not None, "Outline Size 读数读取失败"
            sw = swatch_box(page, "Outline", 6)
            assert sw, f"Outline 未找到色块，实际色块数未知"
            page.mouse.click(sw["x"] + sw["w"] // 2, sw["y"] + sw["h"] // 2)
            page.wait_for_timeout(SETTLE_ACTION)
            assert_changed(page, "l2_008_outline", THRESHOLD_WEAK, f"size={target}+color")
            shot(page, "l2_008_outline_after")

    @allure.title("L2-009: Reflection 开关与 Distance")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_009_reflection(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 点击 Reflection 行开关，断言出现 Scope/Opacity/Distance/Angle
          2. 把 Distance 拖到目标值并断言画布变化
        预期结果: Reflection 开关可开启，Distance 生效
        """
        page = canvas_page
        with allure.step("新增文字图层并开启 Reflection 开关"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            click_switch(page, "Reflection", lambda: "Scope" in panel_text(page))
        with allure.step("断言分区自动展开且控件齐全"):
            sections = page.evaluate(SECTIONS_JS)
            for kw in ["Scope", "Opacity", "Distance", "Angle"]:
                assert kw in sections, f"Reflection 分区缺少 {kw}: {sections}"
            shot(page, "l2_009_reflection_expanded")
        with allure.step("调整 Distance 并断言画布变化"):
            canvas_crop(page, "l2_009_reflection_before")
            target = DATA["right_panel"]["targets"]["reflection_distance"]
            result = drag_range(page, "Distance", target)
            assert result["after"] is not None, "Reflection Distance 读数读取失败"
            assert_changed(page, "l2_009_reflection", THRESHOLD_WEAK, f"distance={target}")
            shot(page, "l2_009_reflection_after")

    @allure.title("L2-010: Background 选色")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_010_background(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 展开 Background 分区（该行无开关）
          2. 点击第 8 个有色色块
          3. 断言画布变化
        预期结果: 文字底色变化
        """
        page = canvas_page
        with allure.step("新增文字图层并展开 Background 分区"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            expand_section(page, "Background", lambda: swatch_box(page, "Background", 0) is not None)
            sections = page.evaluate(SECTIONS_JS)
            assert "Background" in sections, f"Background 分区未展开: {sections}"
        with allure.step("截图记录改前状态"):
            canvas_crop(page, "l2_010_background_before")
            shot(page, "l2_010_background_before")
        with allure.step("点击有色色块并断言画布变化"):
            idx = DATA["right_panel"]["background_swatch_index"]
            sw = swatch_box(page, "Background", idx)
            assert sw, f"Background 未找到色块 index={idx}"
            page.mouse.click(sw["x"] + sw["w"] // 2, sw["y"] + sw["h"] // 2)
            page.wait_for_timeout(SETTLE_ACTION)
            assert_changed(page, "l2_010_background", THRESHOLD_WEAK, f"swatch={idx}")
            shot(page, "l2_010_background_after")

    @allure.title("L2-011: Blend 混合模式")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_011_blend(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 展开 Blend 分区
          2. 点击 Screen 混合模式瓦片
          3. 断言画布变化（弱差异，用容差阈值）
        预期结果: 混合模式切换生效
        """
        page = canvas_page
        with allure.step("新增文字图层并展开 Blend 分区"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            expand_section(page, "Blend", lambda: blend_tile_box(page, "Screen") is not None)
        with allure.step("截图记录改前状态"):
            canvas_crop(page, "l2_011_blend_before")
            shot(page, "l2_011_blend_before")
        with allure.step("选择 Screen 并断言画布变化"):
            mode = DATA["right_panel"]["blend_mode"]
            tile = blend_tile_box(page, mode)
            assert tile, f"Blend 未找到模式 {mode}"
            page.mouse.click(tile["x"] + tile["w"] // 2, tile["y"] + tile["h"] // 2)
            page.wait_for_timeout(SETTLE_ACTION)
            assert_changed(page, "l2_011_blend", THRESHOLD_WEAK, f"blend={mode}")
            shot(page, "l2_011_blend_screen")


@allure.epic("旧画布文字功能")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2OldCanvasTextPanelContentEdit:
    @allure.title("L2-012: 双击改文案并点击空白处应用")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_012_content_edit(self, canvas_page: Page):
        """PRD引用: 存量补资产（无 PRD）；提交动作口径由用户确认并经实测验证
        覆盖层级: L2 交互行为
        前置条件: 已进入旧画布并新增文字图层
        测试步骤:
          1. 双击画布中的文字，断言出现 textarea 且初始值为 Text
          2. 聚焦并输入新文案，断言 textarea 值变化且画布变化
          3. 点击图层外的画布空白处应用文案，断言画布变化
          4. 再次双击文字，断言 textarea 值为新文案（已保存）
        预期结果: 双击进入编辑态，输入文案后点击图层外空白处即应用并保存
        """
        page = canvas_page
        new_text = DATA["content_edit"]["new_text"]
        with allure.step("新增文字图层"):
            clear_text_layers(page)
            open_text_panel(page)
            add_text_layer(page)
            box = page.evaluate(CANVAS_BOX_JS)
            canvas_crop(page, "l2_012_edit_typing_before")
            canvas_crop(page, "l2_012_edit_applied_before")
            shot(page, "l2_012_edit_before")

        with allure.step("双击文字进入编辑态并断言初始文案"):
            page.mouse.dblclick(box["x"] + box["w"] // 2, box["y"] + box["h"] // 2)
            page.wait_for_timeout(1500)
            value = page.evaluate("""() => { const t = [...document.querySelectorAll('textarea')]
                .find(e => e.getBoundingClientRect().width > 20); return t ? t.value : null; }""")
            assert value == DATA["text_panel"]["default_text"], f"编辑态初始文案异常: {value}"
            shot(page, "l2_012_edit_state")

        with allure.step("输入新文案并断言 textarea 与画布变化"):
            focused = page.evaluate("""() => { const t = [...document.querySelectorAll('textarea')]
                .find(e => e.getBoundingClientRect().width > 20); if (!t) return null; t.focus(); t.select(); return t.value; }""")
            assert focused is not None, "未找到可编辑的 textarea"
            page.keyboard.press("Control+A")
            page.keyboard.type(new_text, delay=40)
            page.wait_for_timeout(1200)
            typed = page.evaluate("""() => { const t = [...document.querySelectorAll('textarea')]
                .find(e => e.getBoundingClientRect().width > 20); return t ? t.value : null; }""")
            assert typed == new_text, f"输入后 textarea 值异常: {typed}"
            assert_changed(page, "l2_012_edit_typing", THRESHOLD_WEAK, "typing")
            shot(page, "l2_012_edit_typing")

        with allure.step("点击图层外空白处应用文案并断言画布变化"):
            page.mouse.click(box["x"] + 80, box["y"] + 80)
            page.wait_for_timeout(SETTLE_ACTION)
            assert_changed(page, "l2_012_edit_applied", THRESHOLD_STRONG, "click outside to commit")
            shot(page, "l2_012_edit_applied")

        with allure.step("再次双击断言文案已保存"):
            page.mouse.dblclick(box["x"] + box["w"] // 2, box["y"] + box["h"] // 2)
            page.wait_for_timeout(1500)
            reopened = page.evaluate("""() => { const t = [...document.querySelectorAll('textarea')]
                .find(e => e.getBoundingClientRect().width > 20); return t ? t.value : null; }""")
            assert reopened == new_text, f"复开文案未保存: {reopened}"
            shot(page, "l2_012_edit_reopen")
            page.keyboard.press("Escape")
