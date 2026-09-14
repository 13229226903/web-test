# -*- coding: utf-8 -*-
"""旧画布贴纸调参面板自动化测试。

基于 confirmed cases.md（9 条，L1=1/L2=8）与
page_map/pokecut/infinite_canvas_sticker_panel_v1.yaml。
环境: 测试服 zh-CN；VIP 450832596@qq.com；素材仅 test_images/1K.jpg。
执行策略: session 级复用同一个画布 pid；整个会话只上传一次，只添加一个贴纸图层。
"""
import functools
import os
from pathlib import Path

import allure
import pytest
import yaml
from PIL import Image, ImageChops, ImageStat
from playwright.sync_api import Page, expect as pw_expect


def case_meta(case_id: str, layer: str, priority: str):
    """给每条 Allure 用例写入可检索的 case_id / layer / priority label。"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            allure.dynamic.label("case_id", case_id)
            allure.dynamic.label("layer", layer)
            allure.dynamic.label("priority", priority)
            return func(*args, **kwargs)
        return wrapper
    return decorator


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "test_images").is_dir():
            return candidate
    return here.parent.parent


BASE_DIR = _repo_root()
DATA = yaml.safe_load((BASE_DIR / "data" / "pokecut_old_canvas_sticker_panel_v1.yaml").read_text(encoding="utf-8"))
BASE_URL = os.environ.get("POKECUT_BASE_URL", DATA["base_url"])
EMAIL = os.environ.get("POKECUT_TEST_EMAIL", DATA["accounts"]["vip"]["email"])
CODE = os.environ.get("POKECUT_TEST_CODE", str(DATA["accounts"]["vip"]["code"]))
IMG_1K = str(BASE_DIR / DATA["assets"]["image"])
WAIT_READY = DATA["waits"]["canvas_ready_timeout_s"]
WAIT_SETTLE = DATA["waits"]["canvas_settle_ms"]
SETTLE_ACTION = DATA["waits"]["action_settle_ms"]
MEAN_ANY = DATA["diff_thresholds"]["mean_any"]
UNCHANGED_TOLERANCE = DATA["diff_thresholds"]["unchanged_tolerance"]

TASK_DIR_NAME = "2026-09-11_old_canvas_sticker_panel_exploration"
SHOT_DIR = BASE_DIR / "artifacts" / TASK_DIR_NAME / "shots"
TMP_DIR = BASE_DIR / "artifacts" / TASK_DIR_NAME / "evidence" / "tmp"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
TMP_DIR.mkdir(parents=True, exist_ok=True)

STICKER_TAB = 'div.cursor-pointer:has(> img[src*="edit_left_tab_btn_sticker"])'
STICKER_FIRST = 'img[src$="thumb_sticker_valentine1.webp"]'
LAYER_NAV = 'div.cursor-pointer:has(> img[src*="edit_left_tab_btn_layer"])'
LAYER_ROWS_JS = """() => [...document.querySelectorAll('div')].filter(e => {
    const c = String(e.className || '');
    return (c.includes('layer-choosed') || c.includes('layer-unchoosed'))
      && e.getBoundingClientRect().width > 150;
  }).map(e => {
    const b = e.getBoundingClientRect();
    return {text:(e.innerText || '').trim(), choosed:String(e.className).includes('layer-choosed'),
            x:Math.round(b.x), y:Math.round(b.y), w:Math.round(b.width), h:Math.round(b.height)};
  })"""
READY_JS = """() => Array.from(document.querySelectorAll('div.fixed')).filter(el => {
    const z = parseInt(getComputedStyle(el).zIndex || '0', 10);
    const r = el.getBoundingClientRect();
    return z >= 100 && r.width > 500 && r.height > 400 && getComputedStyle(el).display !== 'none';
  }).length"""
CANVAS_BOX_JS = """() => {
  const c = [...document.querySelectorAll('canvas')].map(e => e.getBoundingClientRect())
    .filter(b => b.width > 200 && b.height > 200).sort((a, b) => b.width * b.height - a.width * a.height)[0];
  return c ? {x:Math.round(c.x), y:Math.round(c.y), w:Math.round(c.width), h:Math.round(c.height)} : null; }"""
NAV_JS = """() => [...document.querySelectorAll('img')]
  .filter(i => (i.getAttribute('src') || '').includes('edit_left_tab_btn_')).length"""
PANEL_JS = (
    "const pn=[...document.querySelectorAll('div')].filter(e=>String(e.className).includes('w-[25rem]')"
    "&&e.getBoundingClientRect().x>1450&&e.getBoundingClientRect().width>350);"
    "pn.sort((a,b)=>{const A=a.getBoundingClientRect(),B=b.getBoundingClientRect();"
    "return B.width*B.height-A.width*A.height;});window.__R=pn[0];"
)


def _panel_js(inner: str) -> str:
    return "() => { " + PANEL_JS + " " + inner + " }"


def _section_js(label: str, require_switch: bool, inner: str) -> str:
    selector = "ls.find(e=>e.parentElement.querySelector('input[type=checkbox]'))" if require_switch else "ls[0]"
    return _panel_js(
        "if(!window.__R) return null;"
        "const ls=[...window.__R.querySelectorAll('p')].filter(e=>e.innerText.trim()===" + repr(label) +
        "&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().x>1450);"
        "const l=" + selector + "; if(!l) return null; const row=l.parentElement; const sec=row.parentElement;" + inner
    )

def panel_text(page: Page) -> str:
    return page.evaluate(_panel_js("return window.__R ? window.__R.innerText : '';"))


def section_label_box(page: Page, label: str, require_switch: bool = False):
    return page.evaluate(_section_js(label, require_switch,
        "const b=l.getBoundingClientRect(); return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};"))


def section_is_open(page: Page, label: str, require_switch: bool = False) -> bool:
    return bool(page.evaluate(_section_js(label, require_switch,
        "return [...row.querySelectorAll('img')].some(i=>i.src.includes('top_icon_drop')&&getComputedStyle(i).display!=='none');")))


def range_items(page: Page, label: str, require_switch: bool = False):
    return page.evaluate(_section_js(label, require_switch,
        "return [...sec.querySelectorAll('input[type=range]')].filter(e=>e.getBoundingClientRect().width>100)"
        ".map(e=>({value:e.value,min:e.min,max:e.max}))"))


def set_section_range(page: Page, label: str, index: int, value, require_switch: bool = False):
    result = page.evaluate(_section_js(label, require_switch,
        "const es=[...sec.querySelectorAll('input[type=range]')].filter(e=>e.getBoundingClientRect().width>100);"
        "const e=es[" + str(index) + "]; if(!e) return null;"
        "const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;"
        "s.call(e,String(" + repr(value) + "));"
        "e.dispatchEvent(new Event('input',{bubbles:true}));"
        "e.dispatchEvent(new Event('change',{bubbles:true}));return e.value;"))
    assert result is not None, f"{label} 分区第 {index} 个滑杆不存在"
    return result


def switch_checked(page: Page, label: str):
    return page.evaluate(_section_js(label, True,
        "const ck=row.querySelector('input[type=checkbox]'); return ck ? ck.checked : null;"))


def switch_box(page: Page, label: str):
    return page.evaluate(_section_js(label, True,
        "const e=row.querySelector('span.slider'); if(!e) return null; const b=e.getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};"))


def open_section(page: Page, label: str, require_switch: bool = False):
    for _ in range(3):
        if section_is_open(page, label, require_switch):
            return
        box = section_label_box(page, label, require_switch)
        assert box, f"右侧面板未找到分区 {label}"
        page.mouse.click(box["x"] + box["w"] // 2, box["y"] + box["h"] // 2)
        page.wait_for_timeout(1000)
    assert section_is_open(page, label, require_switch), f"分区 {label} 未展开"


def set_switch(page: Page, label: str, enabled: bool):
    checked = switch_checked(page, label)
    assert checked is not None, f"右侧面板未找到 {label} 开关"
    if checked != enabled:
        box = switch_box(page, label)
        assert box, f"右侧面板未找到 {label} 开关交互点"
        page.mouse.click(box["x"] + box["w"] // 2, box["y"] + box["h"] // 2)
        page.wait_for_timeout(1100)
    if enabled:
        open_section(page, label, require_switch=True)
    assert switch_checked(page, label) is enabled, f"{label} 开关未达到预期状态 {enabled}"


def click_section_text(page: Page, section: str, text: str, require_switch: bool = False):
    box = page.evaluate(_section_js(section, require_switch,
        "const es=[...sec.querySelectorAll('p,span,div')].filter(e=>e.innerText.trim()===" + repr(text) +
        "&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0);"
        "es.sort((a,b)=>a.getBoundingClientRect().width*a.getBoundingClientRect().height-"
        "b.getBoundingClientRect().width*b.getBoundingClientRect().height);"
        "const e=es[0]; if(!e) return null; const b=e.getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};"))
    assert box, f"{section} 区未找到文本 {text}"
    page.mouse.click(box["x"] + box["w"] // 2, box["y"] + box["h"] // 2)
    page.wait_for_timeout(900)


def click_swatch(page: Page, section: str, color: str):
    clicked = page.evaluate(_section_js(section, True,
        "const es=[...sec.querySelectorAll('div.h-full.w-full')].filter(e=>e.getBoundingClientRect().width>0"
        "&&getComputedStyle(e).backgroundColor===" + repr(color) + "); if(!es.length) return false;"
        "const e=es[0].closest('.cursor-pointer')||es[0]; e.scrollIntoView({block:'center'}); e.click(); return true;"))
    assert clicked, f"{section} 区未找到颜色 {color}"
    page.wait_for_timeout(1000)


def click_type(page: Page, section: str, index: int):
    box = page.evaluate(_section_js(section, True,
        "const es=[...sec.querySelectorAll('div.rounded-full')].filter(e=>{const b=e.getBoundingClientRect();"
        "return b.width>50&&b.height>50;}); if(!es[" + str(index) + "]) return null;"
        "const b=es[" + str(index) + "].getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height),count:es.length};"))
    assert box, f"{section} 区第 {index} 个类型不存在"
    page.mouse.click(box["x"] + box["w"] // 2, box["y"] + box["h"] // 2)
    page.wait_for_timeout(1000)
    return box["count"]


def click_named_card(page: Page, section: str, name: str):
    box = page.evaluate(_section_js(section, True,
        "const es=[...sec.querySelectorAll('p,span,div')].filter(e=>e.innerText.trim()===" + repr(name) +
        "&&e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0);"
        "es.sort((a,b)=>a.getBoundingClientRect().width*a.getBoundingClientRect().height-"
        "b.getBoundingClientRect().width*b.getBoundingClientRect().height);"
        "const e=es[0]; if(!e) return null; const b=e.getBoundingClientRect();"
        "return {x:Math.round(b.x),y:Math.round(b.y),w:Math.round(b.width),h:Math.round(b.height)};"))
    assert box, f"{section} 区未找到卡片 {name}"
    page.mouse.click(box["x"] + box["w"] // 2, box["y"] + box["h"] // 2)
    page.wait_for_timeout(1200)

def shot(page: Page, name: str):
    path = SHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return path


def canvas_crop(page: Page, name: str) -> Path:
    box = page.evaluate(CANVAS_BOX_JS)
    assert box, "未找到可见 canvas"
    path = TMP_DIR / f"{name}.png"
    page.screenshot(path=str(path), clip={"x": box["x"], "y": box["y"], "width": box["w"], "height": box["h"]})
    return path


def mean_diff(before: Path, after: Path) -> float:
    a = Image.open(before).convert("RGB")
    b = Image.open(after).convert("RGB")
    if a.size != b.size:
        b = b.resize(a.size)
    stat = ImageStat.Stat(ImageChops.difference(a, b))
    return round(sum(stat.mean) / 3, 6)


def assert_mean_changed(page: Page, tag: str, note: str = "", before_tag: str | None = None) -> float:
    before = TMP_DIR / f"{(before_tag or tag)}_before.png"
    assert before.exists(), f"{tag} 缺少改前画布图"
    value = 0.0
    for attempt in range(5):
        after = canvas_crop(page, f"{tag}_after" if attempt == 0 else f"{tag}_after_retry{attempt}")
        value = mean_diff(before, after)
        if value > MEAN_ANY:
            allure.attach(f"canvas mean RGB diff={value} {note}", name=f"{tag}_diff", attachment_type=allure.attachment_type.TEXT)
            return value
        page.wait_for_timeout(400)
    allure.attach(f"canvas mean RGB diff={value} {note}", name=f"{tag}_diff", attachment_type=allure.attachment_type.TEXT)
    assert value > MEAN_ANY, f"{tag}: 画布 mean RGB 差异 {value} 未超过 {MEAN_ANY} {note}"
    return value


def assert_mean_unchanged(page: Page, tag: str, note: str = "", before_tag: str | None = None) -> float:
    before = TMP_DIR / f"{(before_tag or tag)}_before.png"
    assert before.exists(), f"{tag} 缺少改前画布图"
    after = canvas_crop(page, f"{tag}_after")
    value = mean_diff(before, after)
    allure.attach(f"canvas mean RGB diff={value} {note}", name=f"{tag}_diff", attachment_type=allure.attachment_type.TEXT)
    assert value <= UNCHANGED_TOLERANCE, f"{tag}: 默认态差异 {value} 超过容差 {UNCHANGED_TOLERANCE} {note}"
    return value


def wait_canvas_ready(page: Page, timeout_s: int = WAIT_READY) -> bool:
    overlay_gone = False
    for _ in range(int(timeout_s / 1.5)):
        if not overlay_gone and page.evaluate(READY_JS) == 0:
            overlay_gone = True
        if overlay_gone and page.evaluate(NAV_JS) >= 8:
            page.wait_for_timeout(1000)
            return True
        page.wait_for_timeout(1500)
    return False


def login(page: Page):
    last_state = None
    for attempt in range(3):
        page.goto(BASE_URL + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4500)
        btn = page.locator('button:has-text("登录"):not(:has-text("退出登录"))')
        if btn.count() and btn.first.is_visible():
            btn.first.click()
            page.wait_for_timeout(1500)
            page.locator('input[data-testid="auth-email-input"], input[type="email"]').first.fill(EMAIL)
            page.locator('input[data-testid="auth-code-input"], input[placeholder*="验证码"], input[placeholder*="Verification"]').first.fill(CODE)
            page.locator('[data-testid="auth-submit"]').first.click()
            page.wait_for_timeout(8500)
        state = page.evaluate("""() => { try { const a=window.useNuxtApp();
            return {vip:a.__basicAccountState?.userBenefit?.value?.vipType}; } catch(e) { return {vip:null}; } }""")
        last_state = state
        if state.get("vip") == DATA["accounts"]["vip"]["vip_type"]:
            return state
        page.wait_for_timeout(2500)
    raise AssertionError(f"VIP 登录失败: {last_state}")


def enter_canvas_via_template(page: Page, attempts: int = 4):
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            page.goto(BASE_URL + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
            page.wait_for_timeout(4500)
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
                raise AssertionError(f"模板上传后未进入画布，当前 URL: {page.url}")
            page.wait_for_timeout(WAIT_SETTLE)
            return page.url
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt == attempts:
                break
            page.wait_for_timeout(2500)
    raise AssertionError(f"模板入口进入旧画布失败（重试 {attempts} 次）: {last_err}")


def open_layer_panel(page: Page):
    page.locator(LAYER_NAV).first.click()
    page.wait_for_timeout(1200)


def sticker_layer_rows(page: Page):
    return page.evaluate(LAYER_ROWS_JS)


def is_sticker_row(text: str) -> bool:
    low = (text or "").lower()
    return "sticker" in low or "贴纸" in low


def sticker_layer_count(page: Page) -> int:
    return sum(1 for row in sticker_layer_rows(page) if is_sticker_row(row["text"]))


def open_sticker_panel(page: Page):
    if page.locator(STICKER_FIRST).first.is_visible():
        return
    loc = page.locator(STICKER_TAB).first
    pw_expect(loc).to_be_visible(timeout=30000)
    loc.click()
    page.wait_for_timeout(SETTLE_ACTION)
    assert page.locator(STICKER_FIRST).first.is_visible(), "Sticker 面板未展开或首张贴纸不可见"


def add_first_sticker(page: Page):
    open_sticker_panel(page)
    page.locator(STICKER_FIRST).first.click()
    page.wait_for_timeout(2400)
    assert section_label_box(page, "不透明度", require_switch=False), "贴纸添加后右侧属性面板未出现"


def select_single_sticker(page: Page):
    open_layer_panel(page)
    rows = [r for r in sticker_layer_rows(page) if is_sticker_row(r["text"])]
    if not rows:
        assert section_label_box(page, "不透明度", require_switch=False), "画布无已选中贴纸，且 Layer 面板未找到 Sticker 图层"
    else:
        row = rows[0]
        page.mouse.click(row["x"] + 45, row["y"] + row["h"] // 2)
        page.wait_for_timeout(1200)
    assert section_label_box(page, "不透明度", require_switch=False), "贴纸未选中，右侧属性面板不可用"


def ensure_single_sticker(page: Page):
    open_layer_panel(page)
    count = sticker_layer_count(page)
    if count == 0:
        open_sticker_panel(page)
        add_first_sticker(page)
        open_layer_panel(page)
        count = sticker_layer_count(page)
    assert count == 1, f"本任务要求始终只有 1 个贴纸图层，实际 {count}"
    select_single_sticker(page)


def reset_sticker_state(page: Page):
    ensure_single_sticker(page)
    for label in ["滤镜", "混合", "反射", "轮廓", "阴影"]:
        set_switch(page, label, False)
    open_section(page, "不透明度")
    assert set_section_range(page, "不透明度", 0, DATA["right_panel"]["opacity"]["values"][0]) == "100"
    open_section(page, "调整")
    for i in range(len(DATA["right_panel"]["adjust"]["labels"])):
        set_section_range(page, "调整", i, 0)
    page.wait_for_timeout(700)


@pytest.fixture(scope="session")
def canvas_session(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="zh-CN")
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
    page = canvas_session["context"].new_page()
    page.goto(canvas_session["url"], wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(5000)
    assert wait_canvas_ready(page), "画布未在超时内加载完成"
    yield page
    page.close()

@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.p0
@pytest.mark.smoke
@pytest.mark.login_required
class TestL2OldCanvasStickerEntry:
    @allure.title("L2-001: 模板首卡上传进入旧画布（session 前置）")
    @allure.severity(allure.severity_level.BLOCKER)
    @case_meta("L2-001", "L2", "P0")
    def test_l2_001_template_entry_to_canvas(self, canvas_page: Page, canvas_session):
        """覆盖层级: L2 交互行为
        前置条件: VIP 账号登录，session 上传一次 test_images/1K.jpg
        测试步骤:
          1. 断言 session 记录 URL 为旧画布
          2. 断言最大可见 canvas 存在
          3. 保存进入画布截图
        预期结果: 成功进入 /zh/create/edit?pid=<uuid>#，画布可编辑
        """
        with allure.step("断言 session 入口 URL 与画布"):
            assert DATA["canvas_path_pattern"] in canvas_session["url"], canvas_session["url"]
            assert canvas_page.evaluate("() => document.querySelectorAll('canvas').length") >= 1
            shot(canvas_page, "l2_001_canvas_entered")


@allure.epic("旧画布贴纸调参面板")
@allure.feature("L1-页面结构元素")
@allure.story("L1-页面结构元素")
@pytest.mark.p0
@pytest.mark.regression
@pytest.mark.login_required
class TestL1OldCanvasStickerStructure:
    @allure.title("L1-001: Sticker 入口、首张贴纸与 7 分区结构")
    @allure.severity(allure.severity_level.BLOCKER)
    @case_meta("L1-001", "L1", "P0")
    def test_l1_001_sticker_structure(self, canvas_page: Page):
        """覆盖层级: L1 页面元素/结构
        前置条件: 已进入旧画布，本任务尚未添加贴纸
        测试步骤:
          1. 点击左侧 Sticker 入口并断言目录
          2. 点击情人节1首张贴纸
          3. 断言画布选中态与右侧 7 分区
        预期结果: 首张贴纸新增并自动选中，右侧 7 个分区文本完整
        """
        page = canvas_page
        with allure.step("打开 Sticker 面板并断言目录"):
            open_sticker_panel(page)
            assert page.locator(STICKER_FIRST).first.is_visible()
            assert "情人节1" in page.locator("body").inner_text()
            shot(page, "l1_001_sticker_panel_open")
        with allure.step("添加首张贴纸并断言画布选中态"):
            add_first_sticker(page)
            assert page.locator("span.scale-point").count() >= 4
            shot(page, "l1_001_sticker_selected")
        with allure.step("断言右侧 7 个分区"):
            text = panel_text(page)
            for name in DATA["sticker_panel"]["sections"]:
                assert name in text, f"右侧面板缺少分区 {name}: {text}"
            shot(page, "l1_001_right_panel_sections")


@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2StickerOpacity:
    @allure.title("L2-002: 贴纸不透明度生效及 0/100 边界")
    @allure.severity(allure.severity_level.NORMAL)
    @case_meta("L2-002", "L2", "P1")
    def test_l2_002_opacity(self, canvas_page: Page):
        """覆盖层级: L2 交互行为
        前置条件: 画布中只有一个已选中贴纸
        测试步骤:
          1. 展开不透明度并设为 100，记录基线
          2. 改为 35 并断言画布变化
          3. 改为 0 并断言语义边界
          4. 恢复 100
        预期结果: range min=0 max=100，35/0 均与 100 有非零差异
        """
        page = canvas_page
        with allure.step("准备单个贴纸并展开不透明度"):
            ensure_single_sticker(page)
            open_section(page, "不透明度")
            ranges = range_items(page, "不透明度")
            assert ranges and ranges[0]["min"] == "0" and ranges[0]["max"] == "100"
        with allure.step("记录 100 基线"):
            assert set_section_range(page, "不透明度", 0, 100) == "100"
            page.wait_for_timeout(700)
            canvas_crop(page, "l2_002_opacity_100_before")
            shot(page, "l2_002_opacity_100")
        with allure.step("改为 35 并断言画布变化"):
            assert set_section_range(page, "不透明度", 0, 35) == "35"
            page.wait_for_timeout(800)
            assert_mean_changed(page, "l2_002_opacity_35", "opacity=35", before_tag="l2_002_opacity_100")
            shot(page, "l2_002_opacity_35")
        with allure.step("改为 0 并断言画布变化"):
            canvas_crop(page, "l2_002_opacity_0_before")
            assert set_section_range(page, "不透明度", 0, 0) == "0"
            page.wait_for_timeout(800)
            assert_mean_changed(page, "l2_002_opacity_0", "opacity=0", before_tag="l2_002_opacity_100")
            shot(page, "l2_002_opacity_0")
        with allure.step("恢复不透明度 100"):
            assert set_section_range(page, "不透明度", 0, 100) == "100"


@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2StickerAdjust:
    @allure.title("L2-003: 贴纸 Adjust 13 项逐项生效")
    @allure.severity(allure.severity_level.NORMAL)
    @case_meta("L2-003", "L2", "P1")
    def test_l2_003_adjust(self, canvas_page: Page):
        """覆盖层级: L2 交互行为
        前置条件: 画布中只有一个已选中贴纸
        测试步骤:
          1. 展开调整并断言 13 项
          2. 复位后记录基线
          3. 逐项设置正值并断言 mean RGB 差异 > 0
          4. 每项复位
        预期结果: 13 项全部产生非零画布变化
        """
        page = canvas_page
        cfg = DATA["right_panel"]["adjust"]
        with allure.step("准备贴纸并断言 13 个 Adjust range"):
            ensure_single_sticker(page)
            open_section(page, "调整")
            ranges = range_items(page, "调整")
            assert len(ranges) == 13, f"Adjust range 数量应为 13，实际 {len(ranges)}"
            shot(page, "l2_003_adjust_panel")
        for i, (label, value) in enumerate(zip(cfg["labels"], cfg["values"])):
            with allure.step(f"调整 {label} 为 {value} 并断言变化"):
                for j in range(13):
                    set_section_range(page, "调整", j, 0)
                page.wait_for_timeout(500)
                canvas_crop(page, f"l2_003_adjust_{i:02d}_before")
                assert set_section_range(page, "调整", i, value) == str(value)
                page.wait_for_timeout(700)
                assert_mean_changed(page, f"l2_003_adjust_{i:02d}", f"{label}={value}")
                shot(page, f"l2_003_adjust_{i:02d}")
                set_section_range(page, "调整", i, 0)

@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.p0
@pytest.mark.login_required
class TestL2StickerShadow:
    @allure.title("L2-004: 阴影开关、效果、位置与颜色生效")
    @allure.severity(allure.severity_level.CRITICAL)
    @case_meta("L2-004", "L2", "P0")
    def test_l2_004_shadow(self, canvas_page: Page):
        """覆盖层级: L2 交互行为
        前置条件: 画布中只有一个已选中贴纸
        测试步骤:
          1. 断言阴影关闭态
          2. 开启阴影并复位效果参数
          3. 改效果、位置、颜色并逐段断言画布变化
        预期结果: 效果/位置/颜色三个子页均产生非零画布差异
        """
        page = canvas_page
        cfg = DATA["right_panel"]["shadow"]
        with allure.step("准备贴纸并确认阴影关闭"):
            ensure_single_sticker(page)
            set_switch(page, "阴影", False)
            canvas_crop(page, "l2_004_shadow_off_before")
            shot(page, "l2_004_shadow_off")
        with allure.step("开启阴影并复位效果参数"):
            set_switch(page, "阴影", True)
            click_section_text(page, "阴影", "效果", require_switch=True)
            zero_count = len(range_items(page, "阴影", require_switch=True))
            for i in range(zero_count):
                set_section_range(page, "阴影", i, cfg["zero"][i] if i < len(cfg["zero"]) else 0, require_switch=True)
            page.wait_for_timeout(700)
            canvas_crop(page, "l2_004_shadow_zeroed_before")
            assert_mean_unchanged(page, "l2_004_shadow_zeroed", "shadow zero values", before_tag="l2_004_shadow_off")
            shot(page, "l2_004_shadow_zeroed")
        with allure.step("修改效果参数并断言变化"):
            effect_count = len(range_items(page, "阴影", require_switch=True))
            for i, value in enumerate(cfg["effect"][:effect_count]):
                set_section_range(page, "阴影", i, value, require_switch=True)
            page.wait_for_timeout(900)
            assert_mean_changed(page, "l2_004_shadow_effect", "shadow effect", before_tag="l2_004_shadow_zeroed")
            shot(page, "l2_004_shadow_effect")
        with allure.step("修改距离/旋转（位置类参数）并断言变化"):
            canvas_crop(page, "l2_004_shadow_position_before")
            current_ranges = range_items(page, "阴影", require_switch=True)
            if len(current_ranges) >= 5:
                for offset, value in enumerate(cfg["position"]):
                    set_section_range(page, "阴影", 3 + offset, value, require_switch=True)
            else:
                click_section_text(page, "阴影", "位置", require_switch=True)
                for offset, value in enumerate(cfg["position"]):
                    set_section_range(page, "阴影", offset, value, require_switch=True)
            page.wait_for_timeout(900)
            assert_mean_changed(page, "l2_004_shadow_position", "shadow position")
            shot(page, "l2_004_shadow_position")
        with allure.step("修改颜色并断言变化"):
            click_section_text(page, "阴影", "颜色", require_switch=True)
            click_swatch(page, "阴影", "rgb(0, 0, 0)")
            page.wait_for_timeout(700)
            shot(page, "l2_004_shadow_color_black")
            canvas_crop(page, "l2_004_shadow_color_before")
            click_swatch(page, "阴影", cfg["color"])
            shot(page, "l2_004_shadow_color_blue")
            assert_mean_changed(page, "l2_004_shadow_color", "shadow color")
            shot(page, "l2_004_shadow_color")


@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2StickerOutline:
    @allure.title("L2-005: 轮廓类型、颜色和 4 个参数生效")
    @allure.severity(allure.severity_level.NORMAL)
    @case_meta("L2-005", "L2", "P1")
    def test_l2_005_outline(self, canvas_page: Page):
        """覆盖层级: L2 交互行为
        前置条件: 画布中只有一个已选中贴纸
        测试步骤:
          1. 开启轮廓并设置默认值
          2. 修改 4 个滑杆并断言变化
          3. 切换第 4 类型并断言变化
          4. 选择红色并断言变化
        预期结果: 类型、颜色和 4 个参数均产生非零画布差异
        """
        page = canvas_page
        cfg = DATA["right_panel"]["outline"]
        with allure.step("准备贴纸并开启轮廓"):
            ensure_single_sticker(page)
            set_switch(page, "轮廓", True)
            ranges = range_items(page, "轮廓", require_switch=True)
            assert len(ranges) >= 4, f"轮廓参数少于 4 个: {ranges}"
            for i, value in enumerate(cfg["defaults"]):
                set_section_range(page, "轮廓", i, value, require_switch=True)
            shot(page, "l2_005_outline_default")
        with allure.step("修改 4 个轮廓参数并断言变化"):
            canvas_crop(page, "l2_005_outline_sliders_before")
            for i, value in enumerate(cfg["sliders"]):
                set_section_range(page, "轮廓", i, value, require_switch=True)
            page.wait_for_timeout(900)
            assert_mean_changed(page, "l2_005_outline_sliders", "outline sliders")
            shot(page, "l2_005_outline_sliders")
        with allure.step("切换第 4 个轮廓类型并断言变化"):
            canvas_crop(page, "l2_005_outline_type4_before")
            count = click_type(page, "轮廓", cfg["type_index"])
            assert count >= 5, f"轮廓类型少于 5 个: {count}"
            assert_mean_changed(page, "l2_005_outline_type4", "outline type 4")
            shot(page, "l2_005_outline_type4")
        with allure.step("选择红色并断言变化"):
            canvas_crop(page, "l2_005_outline_red_before")
            click_swatch(page, "轮廓", cfg["color"])
            assert_mean_changed(page, "l2_005_outline_red", "outline red")
            shot(page, "l2_005_outline_red")

@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2StickerReflection:
    @allure.title("L2-006: 反射 4 参数生效")
    @allure.severity(allure.severity_level.NORMAL)
    @case_meta("L2-006", "L2", "P1")
    def test_l2_006_reflection(self, canvas_page: Page):
        """覆盖层级: L2 交互行为
        前置条件: 画布中只有一个已选中贴纸
        测试步骤:
          1. 确认反射关闭
          2. 开启并设置 50/50/0/180
          3. 改为 80/80/60/120 并断言变化
        预期结果: 两次反射状态均有非零画布差异
        """
        page = canvas_page
        cfg = DATA["right_panel"]["reflection"]
        with allure.step("准备贴纸并确认反射关闭"):
            ensure_single_sticker(page)
            set_switch(page, "反射", False)
        with allure.step("开启反射并设置默认值"):
            set_switch(page, "反射", True)
            for i, value in enumerate(cfg["defaults"]):
                set_section_range(page, "反射", i, value, require_switch=True)
            page.wait_for_timeout(800)
            canvas_crop(page, "l2_006_reflection_default_before")
            shot(page, "l2_006_reflection_default")
        with allure.step("修改 4 个反射参数并断言变化"):
            for i, value in enumerate(cfg["changed"]):
                set_section_range(page, "反射", i, value, require_switch=True)
            page.wait_for_timeout(900)
            assert_mean_changed(page, "l2_006_reflection_changed", "reflection changed", before_tag="l2_006_reflection_default")
            shot(page, "l2_006_reflection_changed")


@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.p0
@pytest.mark.login_required
class TestL2StickerFilter:
    @allure.title("L2-007: 滤镜分类、PR02 缩略图与强度生效")
    @allure.severity(allure.severity_level.CRITICAL)
    @case_meta("L2-007", "L2", "P0")
    def test_l2_007_filter(self, canvas_page: Page):
        """覆盖层级: L2 交互行为
        前置条件: 画布中只有一个已选中贴纸
        测试步骤:
          1. 确认滤镜关闭
          2. 开启滤镜并断言分类/缩略图
          3. 真实鼠标选择 PR02 并断言变化
          4. 设置强度 0/50/100 并逐段断言变化
        预期结果: PR02 和强度均改变画布，range 边界为 0/100
        """
        page = canvas_page
        cfg = DATA["right_panel"]["filter"]
        with allure.step("准备贴纸并确认滤镜关闭"):
            ensure_single_sticker(page)
            set_switch(page, "滤镜", False)
        with allure.step("开启滤镜并断言分类与缩略图"):
            set_switch(page, "滤镜", True)
            text = panel_text(page)
            assert "复古" in text and "PR02" in text
            assert page.locator('img[src*="/source/filter/thumb/"]').count() >= 20
            shot(page, "l2_007_filter_default")
        with allure.step("真实鼠标选择 PR02 并断言变化"):
            canvas_crop(page, "l2_007_filter_PR02_before")
            click_named_card(page, "滤镜", cfg["thumbnail_name"])
            assert_mean_changed(page, "l2_007_filter_PR02", f"filter={cfg['thumbnail_name']}")
            shot(page, "l2_007_filter_PR02")
        with allure.step("设置强度 0/50/100 并断言变化"):
            ranges = range_items(page, "滤镜", require_switch=True)
            assert ranges and ranges[0]["min"] == "0" and ranges[0]["max"] == "100"
            values = cfg["strengths"]
            canvas_crop(page, "l2_007_filter_strength0_before")
            assert set_section_range(page, "滤镜", 0, values[0], require_switch=True) == "0"
            page.wait_for_timeout(700)
            shot(page, "l2_007_filter_strength0")
            canvas_crop(page, "l2_007_filter_strength50_before")
            assert set_section_range(page, "滤镜", 0, values[1], require_switch=True) == "50"
            page.wait_for_timeout(700)
            assert_mean_changed(page, "l2_007_filter_strength50", "filter strength 50")
            shot(page, "l2_007_filter_strength50")
            canvas_crop(page, "l2_007_filter_strength100_before")
            assert set_section_range(page, "滤镜", 0, values[2], require_switch=True) == "100"
            page.wait_for_timeout(700)
            assert_mean_changed(page, "l2_007_filter_strength100", "filter strength 100")
            shot(page, "l2_007_filter_strength100")


@allure.epic("旧画布贴纸调参面板")
@allure.feature("L2-交互行为")
@allure.story("L2-交互行为")
@pytest.mark.login_required
class TestL2StickerBlend:
    @allure.title("L2-008: 混合模式与强度生效")
    @allure.severity(allure.severity_level.NORMAL)
    @case_meta("L2-008", "L2", "P1")
    def test_l2_008_blend(self, canvas_page: Page):
        """覆盖层级: L2 交互行为
        前置条件: 画布中只有一个已选中贴纸
        测试步骤:
          1. 开启混合并断言默认清除
          2. 选择正片叠底并断言变化
          3. 将强度改为 80 并断言变化
        预期结果: 默认态无变化，正片叠底及强度均产生非零画布差异
        """
        page = canvas_page
        cfg = DATA["right_panel"]["blend"]
        with allure.step("准备贴纸并开启混合默认态"):
            ensure_single_sticker(page)
            set_switch(page, "混合", False)
            canvas_crop(page, "l2_008_blend_default_before")
            set_switch(page, "混合", True)
            assert cfg["default_mode"] in panel_text(page)
            assert_mean_unchanged(page, "l2_008_blend_default", "blend clear default", before_tag="l2_008_blend_default")
            shot(page, "l2_008_blend_default")
        with allure.step("选择正片叠底并断言变化"):
            canvas_crop(page, "l2_008_blend_multiply_before")
            click_named_card(page, "混合", cfg["mode"])
            assert_mean_changed(page, "l2_008_blend_multiply", f"blend={cfg['mode']}")
            shot(page, "l2_008_blend_multiply")
        with allure.step("设置强度 80 并断言变化"):
            ranges = range_items(page, "混合", require_switch=True)
            assert ranges and ranges[0]["min"] == "0" and ranges[0]["max"] == "100"
            canvas_crop(page, "l2_008_blend_strength80_before")
            assert set_section_range(page, "混合", 0, cfg["strength"], require_switch=True) == "80"
            page.wait_for_timeout(800)
            assert_mean_changed(page, "l2_008_blend_strength80", "blend strength=80")
            shot(page, "l2_008_blend_strength80")
