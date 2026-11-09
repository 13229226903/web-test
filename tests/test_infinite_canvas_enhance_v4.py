# -*- coding: utf-8 -*-
"""PC 无限画布 Enhance 2K/4K/8K 分辨率选择与画质增强工作流测试。

基于 confirmed cases.md（6 条）与 page_map/pokecut/infinite_canvas_enhance_v6.yaml。
环境：测试服 /en，PC 1920x1080，en-US，会员 450832596@qq.com；素材仅 test_images/。
"""
from __future__ import annotations

import functools
import os
import re
import time
from pathlib import Path

import allure
import pytest
import yaml
from helpers_create_entry import dismiss_create_promo

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError, expect

from helpers.waiting import poll_until

ROOT = Path(__file__).resolve().parents[1]
DATA = yaml.safe_load((ROOT / "data" / "pokecut_infinite_canvas_enhance_v4.yaml").read_text(encoding="utf-8"))
TASK_ID = "2026-09-09_task-33_canvas_enhance_optimization"
TASK_DIR = ROOT / "artifacts" / TASK_ID
SHOT_DIR = TASK_DIR / "shots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
PAGE_MAP = ROOT / "page_map" / "pokecut" / "infinite_canvas_enhance_v6.yaml"


def case_meta(case_id: str, layer: str, priority: str):
    """写入 case_id / layer / priority label。"""
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            allure.dynamic.label("case_id", case_id)
            allure.dynamic.label("layer", layer)
            allure.dynamic.label("priority", priority)
            return fn(*args, **kwargs)
        return wrapper
    return deco


def asset(name: str) -> str:
    return str(ROOT / "test_images" / name)


def norm_base(base_url: str) -> str:
    return base_url.rstrip("/")


def dismiss_overlays(page: Page) -> None:
    page.evaluate("""() => {
      for (const el of document.querySelectorAll('div[class*="fixed"],div[class*="absolute"]')) {
        const r = el.getBoundingClientRect();
        const st = getComputedStyle(el);
        const bg = st.backgroundColor || '';
        const z = parseInt(st.zIndex || '0', 10);
        if ((bg.includes('rgba(0, 0, 0,') || bg.includes('rgba(0,0,0,')) && r.width > 600 && r.height > 400 && z > 30) el.remove();
      }
    }""")
    # 遮罩移除生效信号：不再存在满足条件的暗色大遮罩
    poll_until(page, lambda: page.evaluate("""() => ![...document.querySelectorAll('div[class*="fixed"],div[class*="absolute"]')].some(el => {
      const r = el.getBoundingClientRect(); const st = getComputedStyle(el);
      const bg = st.backgroundColor || ''; const z = parseInt(st.zIndex || '0', 10);
      return (bg.includes('rgba(0, 0, 0,') || bg.includes('rgba(0,0,0,')) && r.width > 600 && r.height > 400 && z > 30;
    })"""), timeout=4000, interval=200)


def shot(page: Page, name: str) -> Path:
    path = SHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return path


def goto_create(page: Page, base_url: str) -> None:
    page.goto(norm_base(base_url) + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
    # 入口就绪信号：create 工具卡出现（替代固定 7s）
    poll_until(page, lambda: page.locator("button.create-tool-pill").count() > 0, timeout=30000, interval=300)
    dismiss_overlays(page)


def wait_canvas(page: Page) -> None:
    # URL 就绪 + 画布已有真实图片（原为 upload_settle_ms 固定 15s，改为条件等待）
    page.wait_for_function(
        "() => location.href.includes('/agent?pid=') && [...document.querySelectorAll('img')].some(i => i.naturalWidth > 0 && i.naturalHeight > 0)",
        timeout=DATA["waits"]["canvas_ready_timeout_ms"],
    )
    page.locator("button.enhance-shortcut-trigger").first.wait_for(
        state="visible", timeout=DATA["waits"]["canvas_ready_timeout_ms"]
    )
    # Enhance 工具入口可见即结束；不再盲等 1.2s


# 2026-10-19 漂移修复：/create 入口卡由 div.cursor-pointer+p 重构为
# button.create-tool-pill；文案 Start from a Photo→Start with Photos，HD Photo Converter→Photo Enhancer。
# 优先用稳定属性 data-tool-id 定位（文案可能再变）。
ENTRY_TOOL_ID = {
    "Start from a Photo": "start-photo",
    "Start with Photos": "start-photo",
    "HD Photo Converter": "photo-enhancer",
    "Photo Enhancer": "photo-enhancer",
}


def upload_via_create(page: Page, base_url: str, image_name: str, entry: str = "Start with Photos") -> None:
    goto_create(page, base_url)
    tool_id = ENTRY_TOOL_ID.get(entry, "start-photo")
    card = page.locator(f"button.create-tool-pill[data-tool-id='{tool_id}']").first
    dismiss_create_promo(page)  # 全新会话进入 /create 的 VIP 促销/定价弹窗会拦截入口点击
    card.wait_for(state="visible", timeout=30000)
    with page.expect_file_chooser(timeout=30000) as chooser_info:
        card.click(timeout=20000)
    chooser_info.value.set_files(asset(image_name))
    wait_canvas(page)


def panel_rows(page: Page) -> list[dict]:
    return page.evaluate("""() => [...document.querySelectorAll('[data-enhance-row]')].map(r => ({
      text: (r.innerText || '').trim(),
      selected: /ring-c-theme/.test(r.className || ''),
      cls: String(r.className || '')
    }))""")


def open_enhance_panel(page: Page, mode: str = "Ultra HD Mode") -> None:
    """打开 Enhance 面板。

    2026-10-19 漂移：工具栏 Enhance 不再直接开面板，而是弹出模式下拉菜单
    （button.enhance-shortcut-trigger -> .enhance-shortcut-region 的 role=menuitem），
    需先点 trigger 再选一个模式，面板才出现并选中该模式。
    """
    if page.locator("[data-enhance-row]").count() == 0:
        # 下拉偶发未渲染/被遮罩拦截时重试一次（不改断言，仅等待健壮性）
        last_err = None
        for _ in range(2):
            try:
                page.locator("button.enhance-shortcut-trigger").first.click(timeout=15000)
                menu = page.get_by_role("menuitem", name=mode).first
                menu.wait_for(state="visible", timeout=15000)
                menu.click(timeout=15000)
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                # 重试间隔：下拉偶发未渲染，等一次重开；无独立可观察信号
                page.wait_for_timeout(1500)
        else:
            raise AssertionError(f"打开 Enhance 模式下拉失败: {last_err}")
    # 面板就绪信号：增强行 attached 且选中行 ring-c-theme 出现
    page.locator("[data-enhance-row]").first.wait_for(state="attached", timeout=DATA["waits"]["panel_ready_timeout_ms"])
    poll_until(page, lambda: page.evaluate("() => [...document.querySelectorAll('[data-enhance-row]')].some(r => /ring-c-theme/.test(r.className || ''))"),
               timeout=DATA["waits"]["panel_ready_timeout_ms"], interval=300)


def read_selected_state(page: Page) -> dict:
    return page.evaluate("""() => {
      const rows = [...document.querySelectorAll('[data-enhance-row]')];
      const selected = rows.find(r => /ring-c-theme/.test(r.className || ''));
      const ctrls = selected ? [...selected.querySelectorAll('button')].filter(b => /^(2k|4k|8k)$/i.test((b.textContent || '').trim())).map(b => ({
        text: (b.textContent || '').trim().toLowerCase(),
        aria_disabled: b.getAttribute('aria-disabled'),
        cls: String(b.className || '')
      })) : [];
      return {row_text: selected ? (selected.innerText || '').trim() : '', controls: ctrls};
    }""")


def control_enabled(state: dict, res: str) -> bool:
    for c in state.get("controls", []):
        if c["text"] == res:
            return str(c.get("aria_disabled")).lower() != "true"
    raise AssertionError(f"未找到分辨率控件 {res}: {state}")


def select_mode(page: Page, mode: str) -> None:
    row = page.locator("[data-enhance-row]").filter(has_text=mode).first
    row.click(timeout=15000)
    # 切换生效信号：选中行（ring-c-theme）文本以目标模式开头
    poll_until(page, lambda: read_selected_state(page).get("row_text", "").startswith(mode),
               timeout=8000, interval=250)
    state = read_selected_state(page)
    assert state["row_text"].startswith(mode), f"模式未切换成功: {mode}, actual={state['row_text']}"


def select_res(page: Page, res: str) -> None:
    clicked = page.evaluate("""(name) => {
      const row = [...document.querySelectorAll('[data-enhance-row]')].find(r => /ring-c-theme/.test(r.className || ''));
      if (!row) return false;
      const b = [...row.querySelectorAll('button')].find(x => (x.textContent || '').trim().toLowerCase() === name);
      if (!b) return false;
      b.click();
      return true;
    }""", res)
    assert clicked, f"当前模式未找到分辨率 {res}"
    # 切换生效信号：选中行中出现该分辨率按钮被激活（bg-[linear-gradient）
    poll_until(page, lambda: any(
        c.get("text") == res and "bg-[linear-gradient" in c.get("cls", "")
        for c in read_selected_state(page).get("controls", [])
    ), timeout=8000, interval=250)
    state = read_selected_state(page)
    assert state["row_text"], "选择分辨率后未读取到选中行"


def assert_panel_state(page: Page, expected: dict, label: str) -> None:
    state = read_selected_state(page)
    assert state["row_text"].startswith("Ultra HD Mode"), f"{label}: 默认模式应为 Ultra HD Mode, actual={state['row_text'][:80]}"
    assert f"{expected['target'][0]}px" in state["row_text"] and f"{expected['target'][1]}px" in state["row_text"], \
        f"{label}: 目标尺寸不匹配: {state['row_text']}"
    for res, disabled in expected["controls"].items():
        assert control_enabled(state, res) is (not disabled), f"{label}: {res} 可用态不符: {state}"
    default_state = read_selected_state(page)
    active = [c["text"] for c in default_state["controls"] if "bg-[linear-gradient" in c["cls"]]
    assert expected["default_res"] in active, f"{label}: 默认选中应为 {expected['default_res']}, actual={active}"


def click_primary_enhance(page: Page) -> None:
    # 2026-10-19 漂移：主按钮文案由 'Enhance' 变为 'Enhance <credits>'（如 'Enhance 10'），
    # 允许可选的尾部消耗点数。
    clicked = page.evaluate("""() => {
      const b = [...document.querySelectorAll('button')].find(x => /^Enhance(\\s+\\d+)?$/.test((x.innerText || '').trim())
        && /btn-bg-gradient1/.test(String(x.className || '')) && x.offsetWidth > 0 && x.offsetHeight > 0);
      if (!b) return false; b.click(); return true;
    }""")
    assert clicked, "未找到面板主 Enhance 按钮"
    # 提交受理生效信号：出现 Enhanced 占位/结果图层，或任务 loading 文案
    poll_until(page, lambda: page.evaluate("""() => [...document.querySelectorAll('img')].some(i => ((i.alt || '').toLowerCase().includes('enhanced')))
        || /generating|processing|enhancing/i.test(document.body.innerText || '')"""),
               timeout=30000, interval=500)


def get_credits(page: Page) -> int:
    """读取当前可用 Credits。

    2026-10-19 漂移：Credits 由旧文案「Credits 10590 left」改为纯数字
    （span.credits-entry__value）。优先用稳定 class 读取，缺失时回退旧文案。
    """
    val = page.evaluate("""() => {
      const el = document.querySelector('.credits-entry__value');
      return el ? (el.innerText || '').trim() : null;
    }""")
    if val:
        digits = re.sub(r"[^\d]", "", val)
        if digits:
            return int(digits)
    text = page.locator("body").inner_text(timeout=10000)
    m = re.search(r"Credits\s*:?\s*([\d,]+)", text)
    assert m, f"未读取到 Credits: {text[:300]}"
    return int(m.group(1).replace(",", ""))


def image_snapshot(page: Page) -> list[dict]:
    return page.evaluate("""() => [...document.querySelectorAll('img')].filter(im => (im.src || '').startsWith('blob:')).map(im => {
      const b = im.getBoundingClientRect();
      return {alt: im.alt || '', w: im.naturalWidth, h: im.naturalHeight, src: im.src,
              x: b.x, y: b.y, width: b.width, height: b.height};
    })""")


def wait_result(page: Page, source_w: int, source_h: int, expected_long_edge: int, timeout_ms: int | None = None, logs: list[str] | None = None) -> dict:
    deadline = time.time() + (timeout_ms or DATA["waits"]["result_timeout_ms"]) / 1000
    last = []
    while time.time() < deadline:
        # 结果轮询间隔（本函数已自带有界 deadline，属显式轮询而非盲等）
        page.wait_for_timeout(DATA["waits"]["poll_interval_ms"])
        last = image_snapshot(page)
        candidates = [x for x in last if "enhanced" in (x.get("alt") or "").lower() and x.get("w") and x.get("h")]
        for item in sorted(candidates, key=lambda x: x["w"] * x["h"], reverse=True):
            ratio_ok = abs((item["w"] / item["h"]) - (source_w / source_h)) < 0.01
            if max(item["w"], item["h"]) == expected_long_edge and ratio_ok:
                return item
        joined_logs = "\n".join(logs or [])
        if any(marker in joined_logs for marker in ["task fail", "Canvas Enhance TaskFlow failed", "Error: -1002"]):
            shot(page, f"enhance_task_failure_long_{expected_long_edge}")
            allure.attach(joined_logs[-6000:], name="enhance_task_failure_console", attachment_type=allure.attachment_type.TEXT)
            pytest.fail(f"Enhance 任务失败，前端 console 出现错误: {joined_logs[-1200:]}")
        body = page.locator("body").inner_text(timeout=8000)
        if re.search(r"failed|error|失败", body, re.I):
            pytest.fail(f"Enhance 任务失败: {body[-1200:]}")
    raise AssertionError(f"未在超时内得到长边 {expected_long_edge} 的结果图；最后图片: {last}")


def console_evidence(logs: list[str]) -> dict:
    text = "\n".join(logs)
    def find(pattern: str):
        m = re.search(pattern, text)
        return m.group(1) if m else None
    return {
        "task_id": find(r"(gzy_[A-Za-z0-9_]+)") or find(r"轮询结果\s+(\S+)"),
        "flow_job_id": find(r"flowJobId:\s*([0-9a-f-]+)"),
        "style_id": find(r"styleId:\s*([A-Za-z0-9_]+)"),
        "resource_code": find(r"resourceCode:\s*([A-Za-z0-9_]+)"),
        "ef_mode": find(r"efMode:\s*(\d+)"),
        "raw": text,
    }


def assert_route(logs: list[str], *, resource_code: str, style_id: str | None = None, ef_mode: str | None = None) -> dict:
    ev = console_evidence(logs)
    assert ev["task_id"], f"未捕获 taskId: {ev['raw'][-2000:]}"
    assert ev["resource_code"] == resource_code, f"resourceCode 不符: expected={resource_code}, actual={ev['resource_code']}"
    if style_id is not None:
        assert ev["style_id"] == style_id, f"styleId 不符: expected={style_id}, actual={ev['style_id']}"
    if ef_mode:
        if ev["ef_mode"] is None:
            allure.attach("前端 console 未暴露 efMode，按 sync gap 记录", name="efMode_gap", attachment_type=allure.attachment_type.TEXT)
        else:
            assert ev["ef_mode"] == ef_mode, f"efMode 不符: expected={ef_mode}, actual={ev['ef_mode']}"
    allure.attach(str(ev), name="submit_evidence", attachment_type=allure.attachment_type.TEXT)
    return ev


def click_result_center(page: Page, result: dict) -> None:
    box = page.evaluate("""() => {
      const im = [...document.querySelectorAll('img')].filter(x => (x.alt || '').toLowerCase().includes('enhanced'))
        .sort((a,b) => (b.naturalWidth*b.naturalHeight) - (a.naturalWidth*a.naturalHeight))[0];
      if (!im) return null; const b = im.getBoundingClientRect();
      return {x:b.x + b.width/2, y:b.y + b.height/2};
    }""")
    assert box, "未找到结果图用于点击 Compare"
    page.mouse.click(box["x"], box["y"])
    # 进入 Compare 生效信号：Before/After 文案或对比 handle 出现
    poll_until(page, lambda: page.evaluate("() => { const t = document.body.innerText || ''; return (t.includes('Before') && t.includes('After')) || document.querySelectorAll(\"img[src*='infinite_canvas_enhance_compare_handle.svg']\").length > 0; }"),
               timeout=12000, interval=300)


def assert_compare_state(page: Page) -> None:
    body = page.locator("body").inner_text(timeout=8000)
    assert "Before" in body and "After" in body, f"Compare 文案缺失: {body[-1200:]}"
    assert "text.canvasEnhanceUINow" not in body, "Compare 仍出现 i18n key 泄漏"
    assert page.locator("img[src*='infinite_canvas_enhance_compare_handle.svg']").count() > 0, "Compare handle 未出现"
    badge_count = page.locator("img[src*='infinite_canvas_enhance_result_']").count()
    assert badge_count > 0, "Compare result badge 未出现"


def drag_compare_handle(page: Page) -> None:
    handle = page.locator("img[src*='infinite_canvas_enhance_compare_handle.svg']").first
    box = handle.bounding_box()
    assert box, "Compare handle 无 bounding box"
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x - 80, y, steps=10)
    page.mouse.up()
    # 拖动后画布重绘稳定即继续（handle 位置变化无独立断言，后续 Compare 状态校验）
    poll_until(page, lambda: page.locator("img[src*='infinite_canvas_enhance_compare_handle.svg']").first.bounding_box() is not None,
               timeout=4000, interval=200)


def exit_compare(page: Page) -> None:
    page.keyboard.press("Escape")
    # 退出生效信号：Compare 文案/对比 handle 消失
    poll_until(page, lambda: page.evaluate("() => { const t = document.body.innerText || ''; return !t.includes('Before :') && document.querySelectorAll(\"img[src*='infinite_canvas_enhance_compare_handle.svg']\").length === 0; }"),
               timeout=8000, interval=250)
    body = page.locator("body").inner_text(timeout=8000)
    assert "Before :" not in body, f"Escape 未退出 Compare: {body[-1000:]}"


def enter_compare_again(page: Page, result: dict) -> None:
    # 结果图选中后如有 Compare 按钮则点击；否则点击结果中心。
    compare_btn = page.locator("button:has-text('Compare')").last
    if compare_btn.count() and compare_btn.is_visible():
        compare_btn.click(timeout=10000)
    else:
        click_result_center(page, result)
    # 重进 Compare 生效信号：Before/After 文案与 handle 出现
    poll_until(page, lambda: page.evaluate("() => { const t = document.body.innerText || ''; return t.includes('Before') && t.includes('After') && document.querySelectorAll(\"img[src*='infinite_canvas_enhance_compare_handle.svg']\").length > 0; }"),
               timeout=12000, interval=300)
    assert_compare_state(page)


def blob_layer_count(page: Page) -> int:
    return page.evaluate("""() => [...document.querySelectorAll('img')].filter(im => (im.src || '').startsWith('blob:') && im.naturalWidth > 0 && im.naturalHeight > 0 && im.getBoundingClientRect().width > 0).length""")


def submit_and_wait(page: Page, logs: list[str], image_name: str, source_w: int, source_h: int, expected_long_edge: int) -> dict:
    with allure.step(f"选择素材 {image_name}，提交增强并等待结果"):
        click_primary_enhance(page)
        result = wait_result(page, source_w, source_h, expected_long_edge)
        allure.attach(str(result), name="result_image", attachment_type=allure.attachment_type.TEXT)
        return result


@pytest.fixture(scope="session")
def pro_context(playwright, base_url):
    """会话级登录一次，后续每用例新开 page。"""
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    page.goto(norm_base(base_url) + "/en", wait_until="domcontentloaded", timeout=120000)
    # 首页就绪信号：Log in 入口可见（替代固定 6s）
    page.get_by_text("Log in", exact=True).first.wait_for(state="visible", timeout=30000)
    page.get_by_text("Log in", exact=True).first.click(timeout=15000)
    # 登录弹窗就绪信号：email 输入框可见（替代固定 2s）
    page.locator('input[type="email"]').first.wait_for(state="visible", timeout=15000)
    page.locator('input[type="email"]').fill(DATA["accounts"]["pro"]["email"])
    page.locator('input[placeholder="Verification Code"]').fill(str(DATA["accounts"]["pro"]["code"]))
    page.evaluate("""() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Log in' && x.offsetWidth > 200);
      if (!b) return false; b.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true})); return true;
    }""")
    # 登录成功信号（2026-11-08 修复）：原判据 `/Credits|User/` 会**假阳性**——
    # 未登录首页的营销文案里也含 "Credits"，实测 poll 在 0.9s 就返回 True，
    # 而此刻仍是未登录态（页面仍有 "Sign up | Log in"），导致后续用例拿到非 VIP 的
    # 默认模式（Standard Mode），批量跑时表现为 "默认应为 Ultra HD Mode, actual=Standard Mode"。
    # 改为可靠信号：登录入口消失 且 出现账号标识（User8JY / 余额数字）。
    poll_until(
        page,
        lambda: page.evaluate(r"""() => {
            const t = document.body.innerText || '';
            const stillLoggedOut = /(^|\n)\s*Log in\s*(\n|$)/.test(t) || /(^|\n)\s*Sign up\s*(\n|$)/.test(t);
            const hasAccount = /User8JY|Credits\s*\d|\b\d{4,6}\b/.test(t);
            return !stillLoggedOut && hasAccount;
        }"""),
        timeout=40000, interval=500,
    )
    body = page.locator("body").inner_text(timeout=10000)
    assert ("Log in" not in body) or ("User8JY" in body), f"Pro 登录失败（仍处于未登录态）: {body[:1000]}"
    assert "User8JY" in body, f"Pro 登录失败（未出现账号标识 User8JY）: {body[:1000]}"
    page.close()
    yield context
    context.close()
    browser.close()


def new_page(context) -> Page:
    page = context.new_page()
    page.set_default_timeout(15000)
    return page


@allure.epic("PC 无限画布 Enhance 2K/4K/8K")
@allure.feature("L1-页面结构与入口")
class TestL1EnhanceStructure:
    @pytest.mark.p0
    @pytest.mark.smoke
    @allure.title("L1-001: Enhance 面板结构、默认 Ultra HD 2k 与模式切换基础态")
    @allure.severity(allure.severity_level.BLOCKER)
    @case_meta("L1-001", "L1", "P0")
    def test_l1_001_panel_structure_and_default_state(self, pro_context, base_url):
        """覆盖层级: L1
        测试步骤:
          1. /en/create 上传 1K.jpg
          2. 打开 Enhance 面板并断言结构
          3. 断言默认 Ultra HD 2k / 目标尺寸
          4. 切换五个模式并断言旧照片无分辨率
        预期结果: 面板结构、默认态、模式切换均符合 page_map v4
        """
        page = new_page(pro_context)
        try:
            upload_via_create(page, base_url, DATA["assets"]["one_k"])
            open_enhance_panel(page)
            with allure.step("断言 Enhance 面板结构"):
                # 2026-11-08 产品漂移：Enhance 模式新增 Low-Res Mode，面板行由 5 变 6。
                # 实测下拉菜单 = [Standard, Old Photo, Low-Res, Portrait, Text, Ultra HD]（6 项），
                # VIP 默认选中 Ultra HD。此处按现状修正行数（原断言为 5）。
                assert page.locator("[data-enhance-row]").count() == 6
                assert page.locator("img[src*='enhance_help']").count() >= 4
                assert page.locator("button.btn-bg-gradient1:has-text('Enhance')").count() == 1
                assert_panel_state(page, DATA["expected"]["one_k"], "1K 默认态")
            with allure.step("切换模式并断言分辨率显隐"):
                # 2026-11-08：补入产品新增的 Low-Res Mode，覆盖全部 6 个模式。
                for mode in ["Old Photo Mode", "Low-Res Mode", "Standard Mode", "Portrait Mode", "Text Mode", "Ultra HD Mode"]:
                    select_mode(page, mode)
                    state = read_selected_state(page)
                    # 实测（2026-11-08 探针）：Old Photo Mode 与 Low-Res Mode 均不展示
                    # 2k/4k/8k 分辨率控件；Standard / Portrait / Text / Ultra HD 展示全部三档。
                    if mode in ("Old Photo Mode", "Low-Res Mode"):
                        assert not state["controls"], f"{mode} 不应展示 2k/4k/8k"
                    else:
                        assert {c["text"] for c in state["controls"]} == {"2k", "4k", "8k"}, \
                            f"{mode} 应展示 2k/4k/8k，实际 {state['controls']}"
            shot(page, "L1-001_panel_structure")
        finally:
            page.close()

    @pytest.mark.p0
    @pytest.mark.smoke
    @allure.title("L1-002: Photo Enhancer 入口自动选中并自动打开 Enhance 面板")
    @allure.severity(allure.severity_level.CRITICAL)
    @case_meta("L1-002", "L1", "P0")
    def test_l1_002_hd_photo_converter_auto_open(self, pro_context, base_url):
        """覆盖层级: L1
        测试步骤:
          1. /en/create 点击 Photo Enhancer 上传 1K.jpg
          2. 等待进入 /agent?pid=<uuid>
          3. 不点击顶部 Enhance，断言面板自动打开
          4. 断言默认 Ultra HD 2k
        预期结果: 自动选中并自动打开 Enhance
        """
        page = new_page(pro_context)
        try:
            upload_via_create(page, base_url, DATA["assets"]["one_k"], entry="Photo Enhancer")
            page.locator("[data-enhance-row]").first.wait_for(state="attached", timeout=15000)
            assert_panel_state(page, DATA["expected"]["one_k"], "Photo Enhancer 默认态")
            shot(page, "L1-002_hd_converter_auto_panel")
        finally:
            page.close()


@allure.epic("PC 无限画布 Enhance 2K/4K/8K")
@allure.feature("L5-分辨率边界与数据等价类")
class TestL5ResolutionBoundaries:
    @pytest.mark.p0
    @pytest.mark.regression
    @allure.title("L5-001: 长边默认档位矩阵与 8K 上传不压缩")
    @allure.severity(allure.severity_level.BLOCKER)
    @case_meta("L5-001", "L5", "P0")
    def test_l5_001_resolution_default_matrix_and_8k_uncompressed(self, pro_context, base_url):
        """覆盖层级: L5
        测试步骤:
          1. 循环上传低清、4K.jpg、4K.png、8K.jpg
          2. 打开 Enhance 并断言默认档位/禁用态/目标尺寸
          3. 点击禁用档断言 over toast
          4. 8K 文件断言画布不被压缩到 4096
        预期结果: 各长边分档和 8K 上传行为符合 PRD
        """
        # 2026-11-08 产品调整（用户确认）：所有原图尺寸下 2k/4k/8k 均可选，不再有
        # 「禁用档 + 点击弹 over N K toast」的行为；实测 1K/4K.jpg/4K.png/8K 全为可用。
        # 故 disabled_res 一律 None（原为 4K/8K 图上的 ["2k","4k"]）。
        cases = [
            ("low", DATA["assets"]["low"], DATA["expected"]["low"], None),
            ("4Kjpg", DATA["assets"]["four_k_jpg"], DATA["expected"]["four_k_jpg"], None),
            ("4Kpng", DATA["assets"]["four_k_png"], DATA["expected"]["four_k_png"], None),
            ("8Kjpg", DATA["assets"]["eight_k"], DATA["expected"]["eight_k"], None),
        ]
        for label, image_name, expected, disabled_res in cases:
            page = new_page(pro_context)
            try:
                with allure.step(f"上传 {label} 并检查默认档位"):
                    upload_via_create(page, base_url, image_name)
                    if label == "8Kjpg":
                        body = page.locator("body").inner_text(timeout=8000)
                        assert "8000 x 6000" in body or "8000x6000" in body, f"8K 画布尺寸被压缩: {body[:800]}"
                    open_enhance_panel(page)
                    assert_panel_state(page, expected, label)
                    for res in disabled_res or []:
                        clicked = page.evaluate("""(name) => {
                          const row = [...document.querySelectorAll('[data-enhance-row]')].find(r => /ring-c-theme/.test(r.className || ''));
                          const b = row ? [...row.querySelectorAll('button')].find(x => (x.textContent || '').trim().toLowerCase() === name) : null;
                          if (!b) return false; b.click(); return true;
                        }""", res)
                        assert clicked, f"{label}: 未找到 {res}"
                        expected_toast = "over 2K" if res == "2k" else "over 4K"
                        # toast 生效信号：正文出现 over N K 提示（替代固定 600ms）
                        poll_until(page, lambda: expected_toast in page.evaluate("() => document.body.innerText || ''"),
                                   timeout=5000, interval=200)
                        body = page.locator("body").inner_text(timeout=5000)
                        assert expected_toast in body, f"{label}: 点击 {res} 未出现 {expected_toast}"
                    shot(page, f"L5-001_{label}_panel")
            finally:
                page.close()


@allure.epic("PC 无限画布 Enhance 2K/4K/8K")
@allure.feature("L6-工作流路由与结果 E2E")
class TestL6EnhanceWorkflow:
    @pytest.mark.p0
    @pytest.mark.smoke
    @allure.title("L6-001: Ultra 2k/4k 全链路、结果 resize、Compare、无副作用与扣点")
    @allure.severity(allure.severity_level.BLOCKER)
    @case_meta("L6-001", "L6", "P0")
    def test_l6_001_ultra_2k_4k_e2e(self, pro_context, base_url):
        """覆盖层级: L6
        测试步骤:
          1. 会员登录上传 1K.jpg，提交 Ultra 2k/4k
          2. 断言 route、结果尺寸、Compare、滑杆和扣点
          3. Compare 退出/重进不产生任务或扣点副作用
        预期结果: Ultra 2k/4k 全链路按 PRD 工作
        """
        page = new_page(pro_context)
        logs: list[str] = []
        page.on("console", lambda msg: logs.append(msg.text))
        try:
            before_credits = None
            with allure.step("Ultra 2k 提交与结果断言"):
                upload_via_create(page, base_url, DATA["assets"]["one_k"])
                before_credits = get_credits(page)
                open_enhance_panel(page)
                select_mode(page, DATA["ultra"]["ultra_2k"]["mode"])
                select_res(page, DATA["ultra"]["ultra_2k"]["res"])
                click_primary_enhance(page)
                result = wait_result(page, DATA["expected"]["one_k"]["width"], DATA["expected"]["one_k"]["height"], DATA["ultra"]["ultra_2k"]["long_edge"], logs=logs)
                assert_route(logs, resource_code=DATA["ultra"]["ultra_2k"]["resource_code"], style_id=DATA["ultra"]["ultra_2k"]["style_id"])
                after_credits = get_credits(page)
                assert before_credits - after_credits == DATA["ultra"]["ultra_2k"]["credits"], f"Ultra 2k 扣点不符: {before_credits}->{after_credits}"
                shot(page, "L6-001_ultra2k_result")
            with allure.step("Compare 进入、拖动、退出与重进"):
                layers_before = blob_layer_count(page)
                click_result_center(page, result)
                assert_compare_state(page)
                shot(page, "L6-001_ultra2k_compare")
                drag_compare_handle(page)
                layers_after_drag = blob_layer_count(page)
                assert layers_after_drag == layers_before, "Compare 拖拽改变了图层数"
                exit_compare(page)
                enter_compare_again(page, result)
                assert blob_layer_count(page) == layers_before, "Compare 重进改变了图层数"
                assert get_credits(page) == after_credits, "Compare 操作发生扣点"
                shot(page, "L6-001_compare_reenter")
            with allure.step("Ultra 4k 提交与结果断言"):
                page2 = new_page(pro_context)
                logs2: list[str] = []
                page2.on("console", lambda msg: logs2.append(msg.text))
                try:
                    upload_via_create(page2, base_url, DATA["assets"]["one_k"])
                    c1 = get_credits(page2)
                    open_enhance_panel(page2)
                    select_mode(page2, DATA["ultra"]["ultra_4k"]["mode"])
                    select_res(page2, DATA["ultra"]["ultra_4k"]["res"])
                    click_primary_enhance(page2)
                    wait_result(page2, DATA["expected"]["one_k"]["width"], DATA["expected"]["one_k"]["height"], DATA["ultra"]["ultra_4k"]["long_edge"], logs=logs2)
                    assert_route(logs2, resource_code=DATA["ultra"]["ultra_4k"]["resource_code"], style_id=DATA["ultra"]["ultra_4k"]["style_id"])
                    c2 = get_credits(page2)
                    assert c1 - c2 == DATA["ultra"]["ultra_4k"]["credits"], f"Ultra 4k 扣点不符: {c1}->{c2}"
                    shot(page2, "L6-001_ultra4k_result")
                finally:
                    page2.close()
        finally:
            page.close()

    @pytest.mark.regression
    @allure.title("L6-002: Standard/Portrait/Text x 2k/4k 路由与结果长边")
    @allure.severity(allure.severity_level.CRITICAL)
    @case_meta("L6-002", "L6", "P1")
    def test_l6_002_standard_portrait_text_matrix(self, pro_context, base_url):
        """覆盖层级: L6
        测试步骤:
          1. 循环 Standard/Portrait/Text x 2k/4k
          2. 提交并断言 resourceCode/dimensions
          3. 记录 taskId/styleId/efMode
        预期结果: 所有前端可见路由字段和结果长边符合需求
        """
        for key in ["standard_2k", "standard_4k", "portrait_2k", "portrait_4k", "text_2k", "text_4k"]:
            cfg = DATA["routes"][key]
            page = new_page(pro_context)
            logs: list[str] = []
            page.on("console", lambda msg: logs.append(msg.text))
            try:
                with allure.step(f"{key} 提交与结果断言"):
                    upload_via_create(page, base_url, DATA["assets"][cfg["asset"]])
                    open_enhance_panel(page)
                    select_mode(page, cfg["mode"])
                    select_res(page, cfg["res"])
                    click_primary_enhance(page)
                    expected_src = DATA["expected"][cfg["asset"]]
                    wait_result(page, expected_src["width"], expected_src["height"], cfg["long_edge"], logs=logs)
                    assert_route(logs, resource_code=cfg["resource_code"], style_id=cfg["style_id"], ef_mode=cfg.get("ef_mode"))
                    shot(page, f"L6-002_{key}_result")
            finally:
                page.close()

    @pytest.mark.p0
    @pytest.mark.smoke
    @allure.title("L6-003: 8K 链式与 direct realesrgan 路由矩阵")
    @allure.severity(allure.severity_level.BLOCKER)
    @case_meta("L6-003", "L6", "P0")
    def test_l6_003_8k_routes(self, pro_context, base_url):
        """覆盖层级: L6
        测试步骤:
          1. Standard/Portrait/Text/Ultra + 1K.jpg + 8k 链式提交
          2. 4K.jpg + Ultra 8k 直走 realesrgan
          3. 断言路由、结果长边、Pro 扣点
        预期结果: 8K 路由与扣点符合需求
        """
        for key in ["standard_8k", "portrait_8k", "text_8k", "ultra_8k", "ultra_8k_from_4k"]:
            cfg = DATA["eight_k_routes"][key]
            page = new_page(pro_context)
            logs: list[str] = []
            page.on("console", lambda msg: logs.append(msg.text))
            try:
                with allure.step(f"{key} 提交与结果断言"):
                    upload_via_create(page, base_url, DATA["assets"][cfg["asset"]])
                    c1 = get_credits(page)
                    open_enhance_panel(page)
                    select_mode(page, cfg["mode"])
                    select_res(page, cfg["res"])
                    click_primary_enhance(page)
                    src = DATA["expected"][cfg["asset"]]
                    wait_result(page, src["width"], src["height"], cfg["long_edge"], logs=logs)
                    assert_route(logs, resource_code=cfg["resource_code"], style_id=cfg["style_id"])
                    c2 = get_credits(page)
                    assert c1 - c2 == cfg["credits"], f"{key} 扣点不符: {c1}->{c2}"
                    shot(page, f"L6-003_{key}_result")
            finally:
                page.close()

