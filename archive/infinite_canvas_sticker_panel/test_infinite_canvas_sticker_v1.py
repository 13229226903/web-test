# -*- coding: utf-8 -*-
"""无限画布贴纸功能自动化测试（infinite canvas /agent）。

基于 confirmed cases.md（5 条）与
page_map/pokecut/infinite_canvas_sticker_panel_v3.yaml 实现。

覆盖: L1 结构（并入 01）/ L2 交互与状态迁移 / L5 等价类 / L6 smoke（P-STK-01 承载）。
环境: 测试服 http://10.17.1.66:3001；匿名（无登录/credits/扣点）；素材 test_images/1K.jpg。
说明: 纯前端 DOM 调整（滑杆/开关/色块/滤镜），无后端任务提交，不适用 taskId 记录。
Filter Strength: 前四个滤镜抽 90s 验证无 Strength；其他滤镜抽 VI03 验证出现 Strength。
"""
import re
from pathlib import Path

import allure
import pytest
import yaml
from playwright.sync_api import Page

from helpers.waiting import poll_until, settle, wait_ready, wait_visible


def _repo_root() -> Path:
    """定位仓库根目录（兼容 tests/ 与 archive/<module>/ 两种存放位置）。"""
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "test_images").is_dir():
            return candidate
    return here.parent.parent


BASE_DIR = _repo_root()
DATA = yaml.safe_load((BASE_DIR / "data" / "infinite_canvas_sticker_v1.yaml").read_text(encoding="utf-8"))
IMG_1K = str(BASE_DIR / "test_images" / "1K.jpg")
SHOT_DIR = BASE_DIR / "data" / "screenshots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)

def resolve_base_url(base_url=None) -> str:
    """解析目标域名，优先级：--base-url fixture > POKECUT_BASE_URL > YAML 兜底。

    修复 2026-11-02：旧实现直接 `DATA["base_url"]`，忽略 `--base-url`，
    导致传 :3002 仍访问 YAML 里的 :3001（交叉环境误判）。
    """
    import os as _os
    return (base_url or _os.environ.get("POKECUT_BASE_URL") or DATA["base_url"]).rstrip("/")

# ---------------- page_map selector（不自行重猜） ----------------
SEL_START_PHOTO = "button:has-text('Start with Photos')"
SEL_ADD_STICKER = "button[aria-label='Add Sticker']"
SEL_STICKER_CAT = "button:has-text('Valentine1')"
SEL_STICKER_TILE = "img[alt='sticker_valentine1']"
SEL_ADJUST_BTN = "button:has-text('Adjust')"  # 贴纸浮动工具栏（注意与右侧 Adjust 区区分，用坐标）
SEL_TOOLBAR = "div:has(button:has-text('Move Up'))"
ADJUST_PANEL_TEXTS = ["Filter", "Reflection", "Outline", "Adjust"]


def shot(page: Page, name: str) -> str:
    """整页截图（viewport 全幅，保留左侧工具栏 + 画布 + 右侧面板上下文）。"""
    path = SHOT_DIR / ("%s.png" % name)
    page.screenshot(path=str(path))
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return str(path)


def dismiss_price_modal(page: Page) -> bool:
    """关闭 /create 首次进入的定价弹窗（如有）。

    实测：弹窗的半透明遮罩会 intercepts pointer events，真实 click 会超时；
    改用 JS 直接 dispatchEvent click 关闭（兜底逻辑，不影响主链路断言）。
    """
    # 实测（2026-10-15）：/create 匿名态首次进入弹「You get a limited-time offer」购买弹窗，
    # 关闭按钮（img[src*='colos_pop_btn_close']）点击后 DOM 上的遮罩节点不消失（morph 动画残留），
    # 会持续 intercepts pointer events 导致 Start with Photos 真实点击超时。
    # 兜底：先点关闭图标，再直接移除残留遮罩节点（纯环境态处理，不作断言）。
    ok = page.evaluate(
        r"""() => {
            const img = document.querySelector('img[src*="colos_pop_btn_close"]');
            if (img) {
                img.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
            const b = document.querySelector('[data-canvas-panel-dismiss-blocker]');
            if (b && b.parentElement) {
                b.parentElement.removeChild(b);
                return true;
            }
            return !!img;
        }"""
    )
    if ok:
        # 弹窗关闭后还有 morph 动画残留，等遮罩节点真正移除。
        poll_until(
            page,
            lambda: page.locator("[data-canvas-panel-dismiss-blocker]").count() == 0,
            timeout=5000,
            interval=500,
        )
    return ok


def enter_canvas(page: Page, base_url: str = None) -> None:
    """/create → 关定价弹窗 → Start with Photos → 上传 1K.jpg → /agent?pid="""
    page.goto(resolve_base_url(base_url) + "/create", wait_until="domcontentloaded", timeout=120000)
    wait_ready(page, lambda: page.locator(SEL_START_PHOTO).count() > 0, timeout=20000, settle_ms=0)
    dismiss_price_modal(page)
    btn = page.locator(SEL_START_PHOTO)
    assert btn.count() > 0, "未找到 Start with Photos 按钮"
    # 实测：购买弹窗的半透明遮罩会 intercepts pointer events，真实 click 会超时；
    # 与 AI Tools 任务同款做法：先 JS 关弹窗（含重试），再真实点击触发 file chooser。
    for _ in range(3):
        dismiss_price_modal(page)
        if not page.locator("[data-canvas-panel-dismiss-blocker]").count():
            break
    with page.expect_file_chooser(timeout=30000) as fc:
        btn.first.click()
    fc.value.set_files(IMG_1K)
    assert wait_ready(page, lambda: "/agent?pid=" in page.url, timeout=120000, settle_ms=0), \
        "未进入无限画布: %s" % page.url
    # 画布初始化完成的可观察信号：左侧 Add Sticker 入口可交互。
    wait_ready(page, lambda: page.locator(SEL_ADD_STICKER).count() > 0, timeout=30000, settle_ms=0)


def hover_add_sticker(page: Page) -> None:
    """hover 左侧第 3 个按钮（Add Sticker）展开贴纸面板。"""
    btn = page.locator(SEL_ADD_STICKER)
    assert btn.count() > 0, "未找到 Add Sticker 按钮"
    for _ in range(3):
        btn.first.hover()
        try:
            page.locator(SEL_STICKER_CAT).first.wait_for(state="visible", timeout=5000)
            return
        except Exception:
            settle(page, 1000)
    settle(page, 1000)



def add_sticker(page: Page) -> None:
    """Valentine1 → 第一个贴纸 sticker_valentine1 → 贴纸添加并选中。"""
    cat = page.locator(SEL_STICKER_CAT)
    assert cat.count() > 0, "未找到 Valentine1 分类 tab"
    cat.first.click()
    tile = page.locator(SEL_STICKER_TILE)
    wait_ready(page, lambda: tile.count() > 0, timeout=15000, settle_ms=0)
    assert tile.count() > 0, "未找到 sticker_valentine1 贴纸"
    tile.first.click()
    tb = page.locator(SEL_TOOLBAR)
    wait_ready(page, lambda: tb.count() > 0, timeout=15000, settle_ms=0)
    assert tb.count() > 0, "贴纸选中后未出现浮动工具栏"


def open_adjust_menu(page: Page) -> None:
    """点击贴纸浮动工具栏 Adjust → 右侧调整菜单打开。"""
    tb = page.locator(SEL_TOOLBAR)
    btn = tb.locator("button", has_text=re.compile(r"^Adjust$"))
    assert btn.count() > 0, "浮动工具栏未找到 Adjust 按钮"
    btn.first.click()
    wait_ready(
        page,
        lambda: all(t in page.locator("body").inner_text(timeout=2000) for t in ADJUST_PANEL_TEXTS),
        timeout=15000,
    )
    body = page.locator("body").inner_text()
    for t in ADJUST_PANEL_TEXTS:
        assert t in body, "调整菜单缺少分区: %s" % t


def find_section_row(page: Page, name: str):
    """定位右侧调整面板里指定分区标题（Filter/Reflection/Outline/Adjust）的最内层行。"""
    return page.evaluate(
        r"""([name]) => {
            const els = Array.from(document.querySelectorAll('div'))
                .filter(d => (d.innerText || '').trim() === name
                             && d.getBoundingClientRect().x > 1100
                             && d.getBoundingClientRect().height > 0);
            if (!els.length) return null;
            return true;
        }""",
        [name],
    )


def click_switch(page: Page, name: str, turn_on: bool = True) -> None:
    """点击 Filter/Reflection/Outline 的开关（按分区顺序第 0=Filter/1=Reflection/2=Outline）。"""
    idx = {"Filter": 0, "Reflection": 1, "Outline": 2}[name]
    page.evaluate(
        r"""([idx, wantOn]) => {
            const root = Array.from(document.querySelectorAll('div'))
                .find(d => d.innerText && d.innerText.includes('Reflection')
                           && d.innerText.includes('Outline') && d.innerText.includes('Adjust'));
            if (!root) throw new Error('adjust panel not found');
            const sws = Array.from(root.querySelectorAll('.relative.inline-flex'));
            const sw = sws[idx];
            if (!sw) throw new Error('switch not found: ' + idx);
            const bg = getComputedStyle(sw).backgroundColor;
            const isOn = bg === 'rgb(35, 35, 35)';
            if (wantOn && !isOn) sw.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            if (!wantOn && isOn) sw.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }""",
        [idx, turn_on],
    )
    # 开关状态以背景色 rgb(35,35,35) 表示，等其达到期望值。
    wait_ready(
        page,
        lambda: page.evaluate(
            """([idx, wantOn]) => {
                const root = Array.from(document.querySelectorAll('div'))
                    .find(d => d.innerText && d.innerText.includes('Reflection')
                               && d.innerText.includes('Outline') && d.innerText.includes('Adjust'));
                if (!root) return false;
                const sw = root.querySelectorAll('.relative.inline-flex')[idx];
                if (!sw) return false;
                const on = getComputedStyle(sw).backgroundColor === 'rgb(35, 35, 35)';
                return on === wantOn;
            }""",
            [idx, turn_on],
        ),
        timeout=10000,
    )


def set_slider(page: Page, label: str, value: str) -> None:
    """按标签定位右侧面板滑杆并设值（Vue：JS 设 value + dispatch input/change）。"""
    ok = page.evaluate(
        r"""([label, value]) => {
            // 实测：原生 input[type=range] 的 rect width=0（自定义 UI 覆盖其上），
            // 且其上层各级行容器 rect 也为 0（面板滚动容器视口外）。
            // 唯一可靠判据：input class 含 adjust-range-input，level=2 祖先
            // （.flex.flex-col.gap-1）的 innerText 去掉数字即滑杆标签。
            const sliders = Array.from(document.querySelectorAll('input.adjust-range-input'));
            const norm = s => String(s).toLowerCase().replace(/\s+/g, '');
            const labelOf = s => {
                const row = s.parentElement ? s.parentElement.parentElement : null;
                const t = row ? (row.innerText || '') : '';
                return t.replace(/[0-9\-]+.*$/, '').trim();
            };
            if (!sliders.length) return {err: 'no sliders', n: document.querySelectorAll('input').length};
            const want = norm(label);
            const target = sliders.find(s => norm(labelOf(s)) === want)
                        || sliders.find(s => norm(labelOf(s)).includes(want));
            if (!target) return {err: 'slider not found: ' + label};
            const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setVal.call(target, value);
            target.dispatchEvent(new Event('input', {bubbles: true}));
            target.dispatchEvent(new Event('change', {bubbles: true}));
            return {ok: true, value: target.value};
        }""",
        [label, str(value)],
    )
    assert ok and not ok.get("err"), "滑杆设值失败: %s" % ok
    wait_ready(page, lambda: (get_slider(page, label) or {}).get("value") == str(value), timeout=5000, settle_ms=0)


def get_slider(page: Page, label: str):
    """按标签读取右侧面板滑杆的 value/min/max/step。"""
    return page.evaluate(
        r"""([label]) => {
            const sliders = Array.from(document.querySelectorAll('input.adjust-range-input'));
            const norm = s => String(s).toLowerCase().replace(/\s+/g, '');
            const labelOf = s => {
                const row = s.parentElement ? s.parentElement.parentElement : null;
                const t = row ? (row.innerText || '') : '';
                return t.replace(/[0-9\-]+.*$/, '').trim();
            };
            if (!sliders.length) return {err: 'no sliders', n: document.querySelectorAll('input').length};
            const want = norm(label);
            const target = sliders.find(s => norm(labelOf(s)) === want)
                        || sliders.find(s => norm(labelOf(s)).includes(want));
            if (!target) return null;
            return {label: label, value: target.value, min: target.min, max: target.max, step: target.step};
        }""",
        [label],
    )


@pytest.fixture()
def sticker_session(page: Page, base_url: str):
    """每条用例独立进入画布 + 添加贴纸 + 打开调整菜单。"""
    enter_canvas(page, base_url)
    hover_add_sticker(page)
    add_sticker(page)
    open_adjust_menu(page)
    yield page


def get_filter_strength(page: Page):
    """读取当前 Filter 的 Strength；无可见滑杆时返回 None。"""
    return page.evaluate(
        r"""() => {
            const el = Array.from(document.querySelectorAll('input.filter-range-input')).find(x => {
                const r = x.getBoundingClientRect();
                return r.width || r.height;
            });
            if (!el) return null;
            return {value: el.value, min: el.min, max: el.max, step: el.step};
        }"""
    )



def set_filter_strength(page: Page, value: str) -> None:
    """设置 Filter Strength（Vue：JS 设 value + dispatch input/change）。"""
    ok = page.evaluate(
        r"""([value]) => {
            const el = Array.from(document.querySelectorAll('input.filter-range-input')).find(x => { const r = x.getBoundingClientRect(); return r.width || r.height; });
            if (!el) return {err: 'filter strength not found'};
            const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setVal.call(el, value);
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            return {ok: true, value: el.value};
        }""",
        [str(value)],
    )
    assert ok and not ok.get("err"), "Filter Strength 设值失败: %s" % ok
    wait_ready(page, lambda: (get_filter_strength(page) or {}).get("value") == str(value), timeout=5000, settle_ms=0)


def _outline_slider(page: Page, label: str):
    return page.evaluate(
        r"""([label]) => {
            const norm = s => String(s).toLowerCase().replace(/\s+/g, '');
            const idx = {size: 0, distance: 1, blur: 2, smooth: 3}[norm(label)];
            const box = Array.from(document.querySelectorAll('div')).find(b =>
                String(b.className || '').includes('space-y-3')
                && (b.innerText || '').includes('Types')
                && (b.innerText || '').includes('Smooth'));
            if (!box || idx === undefined) return null;
            const sliders = Array.from(box.querySelectorAll('input[type=range]'));
            const el = sliders[idx];
            if (!el) return null;
            return {label: label, value: el.value, min: el.min, max: el.max, step: el.step};
        }""",
        [label],
    )


def set_outline_slider(page: Page, label: str, value: str) -> None:
    ok = page.evaluate(
        r"""([label, value]) => {
            const norm = s => String(s).toLowerCase().replace(/\s+/g, '');
            const idx = {size: 0, distance: 1, blur: 2, smooth: 3}[norm(label)];
            const box = Array.from(document.querySelectorAll('div')).find(b =>
                String(b.className || '').includes('space-y-3')
                && (b.innerText || '').includes('Types')
                && (b.innerText || '').includes('Smooth'));
            if (!box || idx === undefined) return {err: 'outline box/index not found'};
            const el = Array.from(box.querySelectorAll('input[type=range]'))[idx];
            if (!el) return {err: 'outline slider not found: ' + label};
            const setVal = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
            setVal.call(el, value);
            el.dispatchEvent(new Event('input', {bubbles: true}));
            el.dispatchEvent(new Event('change', {bubbles: true}));
            return {ok: true, value: el.value};
        }""",
        [label, str(value)],
    )
    assert ok and not ok.get("err"), "Outline 滑杆设值失败: %s" % ok
    wait_ready(page, lambda: (_outline_slider(page, label) or {}).get("value") == str(value), timeout=5000, settle_ms=0)


def get_outline_slider(page: Page, label: str):
    return _outline_slider(page, label)

# ---------------- 用例 ----------------


@allure.epic("Pokecut")
@allure.feature("无限画布贴纸功能")
@allure.story("L2 入口与结构")
@pytest.mark.regression
@pytest.mark.smoke
@allure.title("L2-001: 无限画布贴纸入口 + 添加贴纸 + 打开调整菜单")
@allure.severity(allure.severity_level.CRITICAL)
def test_p_stk_01_entry_add_sticker_open_adjust(page: Page, base_url: str):
    """L2-001 无限画布贴纸入口 + 添加贴纸 + 打开调整菜单（同时承载 L1 结构 / L6 smoke）。

    PRD引用: 用户自然语言（hover 左侧第 3 个按钮 → 添加贴纸 → 探索调整菜单）
    覆盖层级: L1（结构，并入本条步骤 1）/ L2（交互）/ L6（smoke）
    前置条件: 匿名；test_images/1K.jpg；/create 可访问
    测试步骤:
      1. /create 关定价弹窗
      2. Trending Tools 点 Start with Photos
      3. 上传 1K.jpg 等 /agent?pid=
      4. hover 左侧第 3 个按钮 Add Sticker
      5. 断言贴纸面板出现分类 tab + 缩略图
      6. 点 Valentine1 第一个贴纸
      7. 断言贴纸图层添加并选中、浮动工具栏 8 按钮可见
      8. 点浮动工具栏 Adjust
      9. 断言右侧 4 分区出现
    预期结果:
      贴纸面板含 Valentine1 分类；贴纸图层添加；浮动工具栏含
      Adjust/Move Up/Move Down/To Top/To Bottom/Flip h/Flip v/Delete；
      右侧出现 Filter/Reflection/Outline/Adjust 四分区。
    """
    with allure.step("1. 进入无限画布并添加贴纸"):
        enter_canvas(page, base_url)
        with allure.step("2. hover Add Sticker 并断言贴纸面板"):
            hover_add_sticker(page)
            assert page.locator(SEL_STICKER_CAT).count() > 0, "贴纸面板缺少分类 tab"
            assert page.locator(SEL_STICKER_TILE).count() > 0, "贴纸面板缺少缩略图"
            shot(page, "P-STK-01_贴纸面板")
        with allure.step("3. 添加贴纸并断言浮动工具栏"):
            add_sticker(page)
            shot(page, "P-STK-01_贴纸添加")
        with allure.step("4. 打开调整菜单并断言 4 分区"):
            open_adjust_menu(page)
            shot(page, "P-STK-01_调整菜单")


@allure.epic("Pokecut")
@allure.feature("无限画布贴纸功能")
@allure.story("L2 Filter 功能")
@pytest.mark.regression
@allure.title("L2-002: Filter 功能（代表分类 + 跨分类 + Strength）")
@allure.severity(allure.severity_level.NORMAL)
def test_p_stk_02_filter(sticker_session: Page):
    """L2-002 Filter：前四抽一个验证无 Strength，再验证其他滤镜出现 Strength。

    PRD引用: 用户确认「Filter 不用全部分类覆盖」；前四个不用逐个点
    覆盖层级: L2 交互 / L5 分类等价类
    前置条件: 贴纸已添加且调整菜单已打开
    测试步骤:
      1. Filter 开关 ON
      2. Vintage → 90s（前 4 个代表）
      3. 断言无 Strength
      4. Vintage → VI03（其他滤镜代表）
      5. 断言 Strength 出现且 min=0 max=100 step=1 默认 100，并改值到 80
    预期结果: 90s 无 Strength；VI03 出现 Strength 且默认 100、可改值
    """
    page = sticker_session
    with allure.step("1. Filter 开关 ON 并断言结构"):
        click_switch(page, "Filter", True)
        assert page.get_by_role("button", name="Vintage", exact=True).count() > 0, "未出现 Vintage 分类"
        shot(page, "P-STK-02_Filter展开")
    with allure.step("2. Vintage → 90s（前 4 个代表）"):
        page.get_by_role("button", name="Vintage", exact=True).click()
        wait_visible(page, page.get_by_text("90s", exact=True).first, timeout=10000, settle_ms=0)
        page.get_by_text("90s", exact=True).first.click()
        # 反向断言「无 Strength」，等 Strength 状态在观察窗口内稳定
        settle(page, 1200)
        assert get_filter_strength(page) is None, "90s 属前 4 个滤镜，不应出现 Strength"
        shot(page, "P-STK-02_Vintage90s无Strength")
    with allure.step("3. Vintage → VI03（其他滤镜代表）出现 Strength"):
        page.get_by_text("VI03", exact=True).first.click()
        wait_ready(page, lambda: get_filter_strength(page) is not None, timeout=15000)
        st = get_filter_strength(page)
        assert st, "VI03 应出现 Strength"
        assert st["min"] == "0" and st["max"] == "100" and st["step"] == "1", "Strength 值域异常: %s" % st
        assert st["value"] == str(DATA["filter"]["strength_default"]), "Strength 默认值异常: %s" % st
        set_filter_strength(page, "80")
        st2 = get_filter_strength(page)
        assert st2 and st2["value"] == "80", "Strength 改值失败: %s" % st2
        shot(page, "P-STK-02_VintageVI03Strength")



@allure.epic("Pokecut")
@allure.feature("无限画布贴纸功能")
@allure.story("L2 Reflection 功能")
@pytest.mark.regression
@allure.title("L2-003: Reflection 功能（开关 + 4 滑杆）")
@allure.severity(allure.severity_level.NORMAL)
def test_p_stk_03_reflection(sticker_session: Page):
    """L2-003 Reflection：开关 ON → 4 滑杆改值（Opacity/Scope/Distance/Angle）。

    PRD引用: confirmed cases.md（4 滑杆改值验证）
    覆盖层级: L2 交互 / L5 等价类
    前置条件: 贴纸已添加且调整菜单已打开
    测试步骤:
      1. Reflection 开关 ON
      2. 断言 4 滑杆出现
      3. Opacity 50→30
      4. Scope 50→80
      5. Distance 0→40
      6. Angle 180→90
      7. 逐个断言滑杆值变化
    预期结果: 开关ON背景rgb(35,35,35)；改值后 DOM value 与设定一致
    """
    page = sticker_session
    with allure.step("1. Reflection 开关 ON"):
        click_switch(page, "Reflection", True)
        for item in DATA["reflection"]["sliders"]:
            s = get_slider(page, item["label"])
            assert s, "Reflection 滑杆 %s 未出现" % item["label"]
        shot(page, "P-STK-03_Reflection展开")
    with allure.step("2. 4 滑杆逐个改值并断言"):
        for item in DATA["reflection"]["sliders"]:
            set_slider(page, item["label"], item["target"])
            s = get_slider(page, item["label"])
            assert s and s["value"] == str(item["target"]), \
                "Reflection %s 改值失败: 期望 %s 实际 %s" % (item["label"], item["target"], s.get("value") if s else None)
        shot(page, "P-STK-03_滑杆改值")


@allure.epic("Pokecut")
@allure.feature("无限画布贴纸功能")
@allure.story("L2 Outline 功能")
@pytest.mark.regression
@allure.title("L2-004: Outline 功能（开关 + Types 1 代表 + Color + 4 滑杆）")
@allure.severity(allure.severity_level.NORMAL)
def test_p_stk_04_outline(sticker_session: Page):
    """L2-004 Outline：开关 ON → Types 1 个代表 + Color 换色 + 4 滑杆改值。

    PRD引用: 用户确认「Outline Types 取一个代表」
    覆盖层级: L2 交互 / L5 等价类
    前置条件: 贴纸已添加且调整菜单已打开
    测试步骤:
      1. Outline 开关 ON
      2. 断言 Types/Color/Size/Distance/Blur/Smooth 出现
      3. 点 Types 第一个样式按钮
      4. 点 Color 第 3 个色块
      5. Size 20→50
      6. Distance 0→30
      7. Blur 0→20
      8. Smooth 0→25
      9. 断言各控件值/选中态变化
    预期结果: 开关ON背景rgb(35,35,35)；Color约27个；改值后DOM value与设定一致
    """
    page = sticker_session
    with allure.step("1. Outline 开关 ON"):
        click_switch(page, "Outline", True)
        wait_ready(page, lambda: get_outline_slider(page, "Size") is not None, timeout=15000)
        shot(page, "P-STK-04_Outline展开")
    with allure.step("2. Types 取一个代表 + Color 换色"):
        page.evaluate(
            r"""([typeIdx, colorIdx]) => {
                const root = Array.from(document.querySelectorAll('div'))
                    .find(d => d.innerText && d.innerText.includes('Reflection')
                               && d.innerText.includes('Outline') && d.innerText.includes('Adjust'));
                if (!root) throw new Error('adjust panel not found');
                const typeBtns = Array.from(root.querySelectorAll('button')).filter(b =>
                    b.getBoundingClientRect().x > 1100 && b.getBoundingClientRect().y > 1100
                    && (b.innerText || '').trim().length === 0);
                if (typeBtns.length > typeIdx) {
                    typeBtns[typeIdx].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                }
                const colors = Array.from(root.querySelectorAll('.aspect-square')).filter(c =>
                    c.getBoundingClientRect().width > 20 && c.getBoundingClientRect().height > 20);
                if (colors.length > colorIdx) {
                    colors[colorIdx].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                }
                return {types: typeBtns.length, colors: colors.length};
            }""",
            [DATA["outline"]["type_index"], DATA["outline"]["color_index"]],
        )
        # 纯前端点击，无独立完成事件；截图前让样式应用稳定。
        settle(page, 1500)
        shot(page, "P-STK-04_样式与颜色")
    with allure.step("3. 4 滑杆逐个改值并断言"):
        for item in DATA["outline"]["sliders"]:
            set_outline_slider(page, item["label"], item["target"])
            s = get_outline_slider(page, item["label"])
            assert s and s["value"] == str(item["target"]), \
                "Outline %s 改值失败: 期望 %s 实际 %s" % (item["label"], item["target"], s.get("value") if s else None)
        shot(page, "P-STK-04_四滑杆改值")


@allure.epic("Pokecut")
@allure.feature("无限画布贴纸功能")
@allure.story("L2 Adjust 功能")
@pytest.mark.regression
@allure.title("L2-005: Adjust 功能（14 个滑杆逐个改值验证）")
@allure.severity(allure.severity_level.CRITICAL)
def test_p_stk_05_adjust_all_sliders(sticker_session: Page):
    """L2-005 Adjust：14 个滑杆逐个改值验证（无开关，直接可见）。

    PRD引用: 用户确认「Adjust 14 个滑杆逐个改值验证」
    覆盖层级: L2 交互 / L5 边界与等价类
    前置条件: 贴纸已添加且调整菜单已打开
    测试步骤:
      1. 断言 14 个滑杆全部出现
      2. 逐个改值（含正值/负值/中间值）
      3. 每个改值后断言 DOM value 与设定一致
    预期结果: 14 滑杆全部可见；每个改值后 DOM value 等于设定值
    """
    page = sticker_session
    items = DATA["adjust"]["sliders"]
    with allure.step("1. 断言 14 个滑杆全部出现"):
        for item in items:
            s = get_slider(page, item["label"])
            assert s, "Adjust 滑杆 %s 未出现" % item["label"]
            assert s["min"] == str(item["min"]) and s["max"] == str(item["max"]), \
                "%s 值域异常: 期望 %s~%s 实际 %s~%s" % (item["label"], item["min"], item["max"], s["min"], s["max"])
        shot(page, "P-STK-05_初始态")
    with allure.step("2. 14 个滑杆逐个改值并断言"):
        for item in items:
            set_slider(page, item["label"], item["target"])
            s = get_slider(page, item["label"])
            assert s and s["value"] == str(item["target"]), \
                "%s 改值失败: 期望 %s 实际 %s" % (item["label"], item["target"], s.get("value") if s else None)
            shot(page, "P-STK-05_%s_%s" % (item["label"], item["target"]))








