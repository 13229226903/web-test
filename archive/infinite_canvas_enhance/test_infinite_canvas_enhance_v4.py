# -*- coding: utf-8 -*-
"""PC 无限画布 Enhance 2K/4K/8K 分辨率选择与画质增强工作流测试。

基于 confirmed cases.md（6 条）与 page_map/pokecut/infinite_canvas_enhance_v4.yaml。
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

def _repo_root() -> Path:
    """归档副本位于 archive/<dir>/，按 data/ + page_map/ + test_images/ 上溯仓库根。"""
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "data").is_dir() and (candidate / "page_map").is_dir() and (candidate / "test_images").is_dir():
            return candidate
    return here.parents[1]


ROOT = _repo_root()
DATA = yaml.safe_load((ROOT / "data" / "pokecut_infinite_canvas_enhance_v4.yaml").read_text(encoding="utf-8"))
TASK_ID = "2026-09-09_task-33_canvas_enhance_optimization"
TASK_DIR = ROOT / "artifacts" / TASK_ID
SHOT_DIR = TASK_DIR / "shots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)
PAGE_MAP = ROOT / "page_map" / "pokecut" / "infinite_canvas_enhance_v4.yaml"


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
    page.wait_for_timeout(500)


def shot(page: Page, name: str) -> Path:
    path = SHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return path


def goto_create(page: Page, base_url: str) -> None:
    page.goto(norm_base(base_url) + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(7000)
    dismiss_overlays(page)


def wait_canvas(page: Page) -> None:
    page.wait_for_timeout(DATA["waits"]["upload_settle_ms"])
    page.wait_for_function(
        "() => location.href.includes('/agent?pid=') && [...document.querySelectorAll('img')].some(i => i.naturalWidth > 0 && i.naturalHeight > 0)",
        timeout=DATA["waits"]["canvas_ready_timeout_ms"],
    )
    page.locator("button.toolbar-hover-button:has-text('Enhance')").first.wait_for(
        state="visible", timeout=DATA["waits"]["canvas_ready_timeout_ms"]
    )
    page.wait_for_timeout(1200)


def upload_via_create(page: Page, base_url: str, image_name: str, entry: str = "Start from a Photo") -> None:
    goto_create(page, base_url)
    if entry == "HD Photo Converter":
        card = page.get_by_text("HD Photo Converter", exact=True).first
    else:
        card = page.locator("div.cursor-pointer:has(p:text-is('Start from a Photo'))").first
    dismiss_create_promo(page)  # 全新会话进入 /create 的 VIP 促销/定价弹窗会拦截入口点击
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


def open_enhance_panel(page: Page) -> None:
    if page.locator("[data-enhance-row]").count() == 0:
        page.locator("button.toolbar-hover-button:has-text('Enhance')").first.click(timeout=15000)
    page.locator("[data-enhance-row]").first.wait_for(state="attached", timeout=DATA["waits"]["panel_ready_timeout_ms"])
    page.wait_for_timeout(1500)


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
    page.wait_for_timeout(DATA["waits"]["action_settle_ms"])
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
    page.wait_for_timeout(DATA["waits"]["action_settle_ms"])
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
    clicked = page.evaluate("""() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Enhance'
        && /btn-bg-gradient1/.test(String(x.className || '')) && x.offsetWidth > 0 && x.offsetHeight > 0);
      if (!b) return false; b.click(); return true;
    }""")
    assert clicked, "未找到面板主 Enhance 按钮"
    page.wait_for_timeout(5000)


def get_credits(page: Page) -> int:
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
    page.wait_for_timeout(2500)


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
    page.wait_for_timeout(800)


def exit_compare(page: Page) -> None:
    page.keyboard.press("Escape")
    page.wait_for_timeout(1500)
    body = page.locator("body").inner_text(timeout=8000)
    assert "Before :" not in body, f"Escape 未退出 Compare: {body[-1000:]}"


def enter_compare_again(page: Page, result: dict) -> None:
    # 结果图选中后如有 Compare 按钮则点击；否则点击结果中心。
    compare_btn = page.locator("button:has-text('Compare')").last
    if compare_btn.count() and compare_btn.is_visible():
        compare_btn.click(timeout=10000)
    else:
        click_result_center(page, result)
    page.wait_for_timeout(1800)
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
    page.wait_for_timeout(6000)
    page.get_by_text("Log in", exact=True).first.click(timeout=15000)
    page.wait_for_timeout(2000)
    page.locator('input[type="email"]').fill(DATA["accounts"]["pro"]["email"])
    page.locator('input[placeholder="Verification Code"]').fill(str(DATA["accounts"]["pro"]["code"]))
    page.evaluate("""() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Log in' && x.offsetWidth > 200);
      if (!b) return false; b.dispatchEvent(new MouseEvent('click', {bubbles:true, cancelable:true})); return true;
    }""")
    page.wait_for_timeout(12000)
    body = page.locator("body").inner_text(timeout=10000)
    assert "Credits" in body or "User" in body, f"Pro 登录失败: {body[:1000]}"
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
                assert page.locator("[data-enhance-row]").count() == 5
                assert page.locator("img[src*='enhance_help']").count() >= 4
                assert page.locator("button.btn-bg-gradient1:has-text('Enhance')").count() == 1
                assert_panel_state(page, DATA["expected"]["one_k"], "1K 默认态")
            with allure.step("切换模式并断言分辨率显隐"):
                for mode in ["Old Photo Mode", "Standard Mode", "Portrait Mode", "Text Mode", "Ultra HD Mode"]:
                    select_mode(page, mode)
                    state = read_selected_state(page)
                    if mode == "Old Photo Mode":
                        assert not state["controls"], "Old Photo Mode 不应展示 2k/4k/8k"
                    else:
                        assert {c["text"] for c in state["controls"]} == {"2k", "4k", "8k"}
            shot(page, "L1-001_panel_structure")
        finally:
            page.close()

    @pytest.mark.p0
    @pytest.mark.smoke
    @allure.title("L1-002: HD Photo Converter 入口自动选中并自动打开 Enhance 面板")
    @allure.severity(allure.severity_level.CRITICAL)
    @case_meta("L1-002", "L1", "P0")
    def test_l1_002_hd_photo_converter_auto_open(self, pro_context, base_url):
        """覆盖层级: L1
        测试步骤:
          1. /en/create 点击 HD Photo Converter 上传 1K.jpg
          2. 等待进入 /agent?pid=<uuid>
          3. 不点击顶部 Enhance，断言面板自动打开
          4. 断言默认 Ultra HD 2k
        预期结果: 自动选中并自动打开 Enhance
        """
        page = new_page(pro_context)
        try:
            upload_via_create(page, base_url, DATA["assets"]["one_k"], entry="HD Photo Converter")
            page.locator("[data-enhance-row]").first.wait_for(state="attached", timeout=15000)
            assert_panel_state(page, DATA["expected"]["one_k"], "HD Photo Converter 默认态")
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
        cases = [
            ("low", DATA["assets"]["low"], DATA["expected"]["low"], None),
            ("4Kjpg", DATA["assets"]["four_k_jpg"], DATA["expected"]["four_k_jpg"], ["2k", "4k"]),
            ("4Kpng", DATA["assets"]["four_k_png"], DATA["expected"]["four_k_png"], ["2k", "4k"]),
            ("8Kjpg", DATA["assets"]["eight_k"], DATA["expected"]["eight_k"], ["2k", "4k"]),
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
                        page.wait_for_timeout(600)
                        body = page.locator("body").inner_text(timeout=5000)
                        expected_toast = "over 2K" if res == "2k" else "over 4K"
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

