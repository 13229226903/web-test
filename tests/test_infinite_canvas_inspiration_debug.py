"""Pokecut 无限画布 Inspiration / Debug / 图生图边界回归。

覆盖 cases.md 的 27 条矩阵中由独立浏览器执行的 6 条：
- L3-002~005：Debug 面板任务流模拟
- L5-008 / L5-010：模型参考图切换与一次多选超限边界
"""

from __future__ import annotations

from pathlib import Path
from functools import lru_cache

import allure
import pytest
import yaml
from playwright.sync_api import Page, expect


ROOT = Path(__file__).resolve().parents[1]
CFG = yaml.safe_load((ROOT / "data" / "pokecut_infinite_canvas_inspiration.yaml").read_text(encoding="utf-8"))

BASE_URL: str = CFG["base_url"]
AGENT_PID: str = CFG["agent_pid"]
MEMBER_EMAIL: str = CFG["login"]["member_email"]
VERIFY_CODE: str = CFG["login"]["code"]
IMG = {k: (ROOT / v).resolve() for k, v in CFG["images"].items()}
DEBUG = CFG["debug_taskflow"]
MODELS = CFG["models"]
SELECTORS = CFG["selectors"]
LIMITS = CFG["limits"]
EXPECTED = CFG["expected_messages"]
TASK_ARTIFACT_DIR = ROOT / "artifacts" / "2026-08-27_pokecut_infinite_canvas_start_from_photo"
SHOT_DIR = TASK_ARTIFACT_DIR / "shots"


# ═══════════════════════════════════════════════════════════════
# 通用 helper
# ═══════════════════════════════════════════════════════════════


@pytest.fixture
def page(standalone_page):
    """Use the standalone browser fixture for more stable canvas interactions."""
    return standalone_page


def _shot(page: Page, name: str) -> None:
    """截图但不改 viewport，避免触发布局重排导致上传缩略图/按钮状态漂移。"""
    with allure.step(f"截图：{name}"):
        SHOT_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = ''.join(ch if ch.isalnum() or ch in ('-', '_') else '_' for ch in name)
        png = page.screenshot(full_page=False)
        (SHOT_DIR / f"{safe_name}.png").write_bytes(png)
        allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)


LAYER_SUITE = {
    "L1": "L1 页面元素存在性",
    "L2": "L2 交互行为",
    "L3": "L3 异常 / 权限 / 兼容流程",
    "L4": "L4 PRD 验收标准",
    "L5": "L5 数据边界值",
    "L6": "L6 核心 Happy Path / E2E",
}


# cases.md 是本矩阵唯一来源；此映射只承载报告元数据，不得扩展用例。
CASE_META = {
    "L1-001": ("P0", "默认页结构存在"),
    "L1-002": ("P0", "Inspiration 面板与 9 个分类 tab"),
    "L1-003": ("P1", "三类代表模板卡片存在"),
    "L1-004": ("P0", "SEO Select 弹窗结构存在"),
    "L2-001": ("P0", "Inspiration 面板可打开且可收起"),
    "L2-002": ("P0", "文生图模板预填且不自动提交"),
    "L2-003": ("P0", "图生图模板预填并展示参考图引导"),
    "L2-004": ("P1", "图生图上传参考图后进入激活态"),
    "L2-005": ("P1", "Setting 弹窗参数选项完整"),
    "L2-006": ("P0", "文生图手动提交生成并扣 15 credits"),
    "L2-008": ("P0", "Select 上传可取消后继续上传"),
    "L2-009": ("P1", "Select 弹窗可关闭"),
    "L2-010": ("P0", "左侧工具栏上传图片进入 Canvas"),
    "L3-001": ("P0", "匿名 Select 选择上传图出现登录拦截"),
    "L3-002": ("P0", "提交失败开关立即失败并可恢复"),
    "L3-003": ("P0", "查询失败开关结果失败并可恢复"),
    "L3-004": ("P0", "查询失败 -123 出现 policy violation"),
    "L3-005": ("P0", "查询失败 -124 出现 server busy"),
    "L3-006": ("P2", "损坏图片上传不产生有效缩略图"),
    "L5-002": ("P1", "模板预填 textarea 可编辑且状态不丢失"),
    "L5-004": ("P2", "连续左侧上传两张画布图后 Select 单选"),
    "L5-005": ("P2", "Select 上传图刷新后保留且不重复"),
    "L5-006": ("P0", "各模型参考图上传上限正确"),
    "L5-007": ("P0", "上限态 hover 删除参考图并恢复上传"),
    "L5-008": ("P0", "模型切换按目标上限保留前 N 张"),
    "L5-009": ("P1", "一次多选未超上限时数量与状态正确"),
    "L5-010": ("P0", "一次多选超上限提示并截断到上限"),
}


def _matrix_case(case_id: str, summary: str | None = None) -> None:
    """按 cases.md 的 case_id / priority / title 输出矩阵 Allure 元数据。"""
    if case_id not in CASE_META:
        raise AssertionError(f"case_id 不存在于 cases.md 矩阵：{case_id}")
    priority, matrix_title = CASE_META[case_id]
    layer, serial = case_id.split('-', 1)
    feature = LAYER_SUITE[layer]
    allure.dynamic.epic("Pokecut 无限画布 Start from Photo / Inspiration")
    allure.dynamic.feature(feature)
    allure.dynamic.title(f"{case_id} | {matrix_title}")
    allure.dynamic.label("case_id", case_id)
    allure.dynamic.label("layer", layer)
    allure.dynamic.label("layer_suite", feature)
    allure.dynamic.label("priority", priority)
    allure.dynamic.label("matrix_order", serial)
    allure.severity({"P0": allure.severity_level.BLOCKER, "P1": allure.severity_level.CRITICAL, "P2": allure.severity_level.NORMAL}[priority])


def _dismiss_purchase_overlay(page: Page) -> None:
    page.evaluate(
        """() => {
            document.querySelectorAll('.purchase-gift-modal').forEach((e) => e.remove());
        }"""
    )


def _login_member(page: Page) -> None:
    """手动登录会员账号，避免依赖 session_context 的全局登录步骤。"""
    with allure.step("登录会员账号"):
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4500)
        _dismiss_purchase_overlay(page)
        if page.get_by_text("User8JY", exact=True).count() > 0:
            return
        login_btn = page.get_by_text("Log in", exact=True)
        expect(login_btn.first).to_be_visible(timeout=20000)
        login_btn.first.click(timeout=10000)
        page.wait_for_timeout(1200)
        page.locator('input[type="email"]').first.fill(MEMBER_EMAIL, timeout=10000)
        code_input = page.locator('input[data-testid="auth-code-input"]')
        if code_input.count() == 0:
            code_input = page.locator('input[placeholder="Verification Code"]')
        expect(code_input.first).to_be_visible(timeout=10000)
        code_input.first.fill(VERIFY_CODE, timeout=10000)
        page.evaluate("""() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                const text = (b.textContent || '').trim();
                if (text === 'Log in' && b.offsetWidth > 200) {
                    b.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    return true;
                }
            }
            return false;
        }""")
        page.wait_for_timeout(7000)
        if page.get_by_text("User8JY", exact=True).count() > 0:
            return
        # 首页偶发不渲染用户昵称时，用 /agent 顶栏做二次确认；不能仅用 Credits，游客也会显示 Credits。
        page.goto(f"{BASE_URL}{SELECTORS['agent_url']}", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(5500)
        _dismiss_purchase_overlay(page)
        expect(page.get_by_text("User8JY", exact=True).first).to_be_visible(timeout=30000)




def _require_member_login(page: Page) -> None:
    try:
        _login_member(page)
    except Exception as exc:
        pytest.skip(f"会员登录前置条件不可用，跳过需提交任务流的 Debug 用例：{exc}")


def _open_agent(page: Page) -> None:
    with allure.step("进入 /agent 画布"):
        page.goto(f"{BASE_URL}{SELECTORS['agent_url']}", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(5500)
        _dismiss_purchase_overlay(page)
        expect(page.locator(SELECTORS["inspiration_button"]).first).to_be_visible(timeout=20000)


def _open_inspiration(page: Page) -> None:
    with allure.step("打开 Inspiration 模板面板"):
        page.locator(SELECTORS["inspiration_button"]).first.click(timeout=10000)
        page.wait_for_timeout(1200)
        expect(page.get_by_role("button", name="Trending", exact=True)).to_be_visible(timeout=20000)


def _select_template(page: Page, style_id: str) -> None:
    with allure.step(f"点击模板卡片 {style_id}"):
        clicked = page.evaluate(
            """(styleId) => {
                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
                };
                const el = document.querySelector(`[data-explore-style-id='${styleId}']`);
                if (!el || !visible(el)) return false;
                el.click();
                return true;
            }""",
            style_id,
        )
        if not clicked:
            page.locator(f"[data-explore-style-id='{style_id}']").first.click(timeout=10000)
        page.wait_for_timeout(1800)
        prompt = page.locator(SELECTORS["prompt_textarea"]).first
        expect(prompt).to_be_visible(timeout=20000)
        expect(prompt).not_to_have_value("", timeout=20000)


def _open_debug_panel(page: Page) -> None:
    with allure.step("打开 Debug 面板"):
        if page.locator(".debug-panel-content:visible").count() == 0:
            page.locator(SELECTORS["debug_button"]).first.click(timeout=10000)
            page.wait_for_timeout(700)
        page.evaluate("""() => { const c = document.querySelector('.debug-panel-content'); if (c) c.scrollTop = 1680; }""")
        page.wait_for_timeout(500)
        expect(page.locator(".debug-panel-content")).to_be_visible(timeout=10000)


def _close_debug_panel(page: Page) -> None:
    with allure.step("关闭 Debug 面板"):
        if page.locator(".debug-panel").count() == 0:
            return
        launcher = page.locator(SELECTORS["debug_button"]).first
        if launcher.count() > 0:
            launcher.click(timeout=10000)
            page.wait_for_timeout(600)
            if page.locator(".debug-panel").count() == 0:
                return
        close_candidates = [
            ".debug-panel .close-btn",
            ".debug-panel button.close-btn",
            ".debug-panel button:has-text('×')",
            ".debug-panel button:has-text('✕')",
        ]
        for selector in close_candidates:
            candidate = page.locator(selector).first
            if candidate.count() > 0:
                candidate.click(timeout=10000)
                page.wait_for_timeout(500)
                return
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)


def _debug_switch_row(page: Page, label: str):
    # 不能只用 has_text："模拟查询结果失败" 会同时匹配 -123/-124 两个子开关。
    rows = page.locator(".debug-panel-content .switch-row")
    expect(rows.first).to_be_visible(timeout=10000)
    for idx in range(rows.count()):
        row = rows.nth(idx)
        row_text = row.inner_text(timeout=3000).strip().rstrip(":：").strip()
        if row_text == label:
            return row
    raise AssertionError(f"未找到 Debug 开关：{label}")


def _debug_switch(page: Page, label: str):
    return _debug_switch_row(page, label).locator("input[type='checkbox']")


def _set_debug_switch(page: Page, label: str, enabled: bool) -> None:
    with allure.step(f"设置 Debug 开关：{label} -> {enabled}"):
        row = _debug_switch_row(page, label)
        sw = row.locator("input[type='checkbox']")
        if sw.is_checked() != enabled:
            row.locator(".slider").click(force=True, timeout=10000)
            page.wait_for_timeout(500)
        assert sw.is_checked() == enabled, f"{label} 开关状态不符合预期：{enabled}"


def _cleanup_debug_switches(page: Page, *labels: str) -> None:
    with allure.step("清理 Debug 模拟开关"):
        try:
            _open_debug_panel(page)
            for label in labels:
                _set_debug_switch(page, label, False)
        finally:
            try:
                _close_debug_panel(page)
            except Exception:
                pass


def _submit_via_send(page: Page) -> None:
    with allure.step("点击底部提交按钮"):
        page.locator("img.canvas-text2img-submit-guide").first.click(timeout=10000)
        page.wait_for_timeout(1000)


def _wait_for_text(page: Page, text: str, timeout_ms: int = 150000) -> None:
    expect(page.locator("body")).to_contain_text(text, timeout=timeout_ms)


def _upload_input(page: Page):
    return page.locator(SELECTORS["upload_ref_input"]).last


def _select_model(page: Page, model_text: str) -> None:
    with allure.step(f"切换模型到 {model_text}"):
        panel = page.locator("div.canvas-textbox-expanded-state:visible").first
        expect(panel).to_be_visible(timeout=20000)
        model_trigger = panel.locator("div[title='Model']").first
        expect(model_trigger).to_be_visible(timeout=20000)
        current_model = model_trigger.locator("span").first.inner_text(timeout=5000).strip()
        if current_model == model_text:
            return
        clicked = page.evaluate(
            """() => {
                const visible = (el) => {
                    if (!el) return false;
                    const r = el.getBoundingClientRect();
                    const s = getComputedStyle(el);
                    return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
                };
                const trigger = [...document.querySelectorAll("div[title='Model']")].find(visible);
                if (!trigger) return false;
                trigger.click();
                return true;
            }"""
        )
        if not clicked:
            model_trigger.click(timeout=10000)
        page.wait_for_timeout(800)
        dropdown = page.locator("div[class*='max-h-[22rem]'][class*='overflow-y-auto']").first
        expect(dropdown).to_be_visible(timeout=20000)
        target = dropdown.get_by_text(model_text, exact=True)
        assert target.count() > 0, f"未找到模型选项：{model_text}"
        option = target.first.locator("xpath=ancestor::div[contains(@class,'cursor-pointer')][1]")
        if option.count() == 0:
            option = target.first
        option.click(timeout=10000)


def _select_model_and_upload(page: Page, model_text: str, files: list[Path]) -> None:
    with allure.step(f"切换模型到 {model_text} 并上传参考图"):
        _select_model(page, model_text)
        page.wait_for_timeout(800)
        _upload_input(page).set_input_files([str(f) for f in files])
        page.wait_for_timeout(6000)


def _visible_ref_image_srcs(page: Page) -> list[str]:
    return page.evaluate(
        """() => {
            const visible = (e) => {
                const r = e.getBoundingClientRect();
                const s = getComputedStyle(e);
                return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
            };
            const panel = [...document.querySelectorAll('div.canvas-textbox-expanded-state')].find(visible);
            if (!panel) return [];
            return [...panel.querySelectorAll('img')].filter(visible).map((img) => img.currentSrc || img.src || '').filter((src) => src.startsWith('blob:') || src.startsWith('data:image'));
        }"""
    )


@lru_cache(maxsize=None)
def _visible_ref_blob_images(page: Page) -> int:
    return page.evaluate(
        """() => {
            const visible = (e) => {
                const r = e.getBoundingClientRect();
                const s = getComputedStyle(e);
                return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
            };
            return [...document.images].filter(visible).filter((img) => {
                const src = (img.currentSrc || img.src || '');
                return src.startsWith('blob:') || src.startsWith('data:image');
            }).length;
        }"""
    )


def _ref_blob_count(page: Page) -> int:
    return page.evaluate(
        """() => {
            const visible = (e) => {
                const r = e.getBoundingClientRect();
                const s = getComputedStyle(e);
                return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
            };
            return [...document.images].filter(visible).filter((img) => {
                const src = (img.currentSrc || img.src || '');
                return src.startsWith('blob:') || src.startsWith('data:image');
            }).length;
        }"""
    )


def _first_ref_thumbnail_box(page: Page):
    return page.evaluate(
        """() => {
            const visible = (e) => {
                const r = e.getBoundingClientRect();
                const s = getComputedStyle(e);
                return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && s.opacity !== '0';
            };
            const thumb = [...document.images].find((img) => {
                const src = (img.currentSrc || img.src || '');
                const r = img.getBoundingClientRect();
                return (src.startsWith('blob:') || src.startsWith('data:image')) && r.y > 800;
            });
            if (!thumb) return null;
            const r = thumb.getBoundingClientRect();
            return { x: r.x, y: r.y, width: r.width, height: r.height };
        }"""
    )


def _hover_first_ref_thumbnail(page: Page) -> None:
    box = _first_ref_thumbnail_box(page)
    assert box, '未找到参考图缩略图'
    page.mouse.move(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)
    page.wait_for_timeout(500)


def _upload_button(page: Page):
    # 最小独立脚本已验证：上传控件恢复后只有 title 稳定存在，文本节点可能不存在。
    return page.locator("[title='Upload reference images']")


def _visible_upload_button_count(page: Page) -> int:
    return page.locator("[title='Upload reference images']:visible").count()


def _assert_upload_button_hidden_at_limit(page: Page) -> None:
    assert _visible_upload_button_count(page) == 0, "达到上限后上传按钮应隐藏"


def _assert_upload_button_restored_after_delete(page: Page) -> None:
    expect(_upload_button(page).first).to_be_visible(timeout=10000)


# ═══════════════════════════════════════════════════════════════
# L3-002 ~ L3-005
# ═══════════════════════════════════════════════════════════════


@pytest.mark.regression
@pytest.mark.p0
def test_dbg_submit_fail_then_recover(page: Page, base_url: str):
    """L3-002：提交失败开关应直接让任务提交失败，并可关闭恢复。"""
    _matrix_case("L3-002", "提交失败开关：开启后立即失败，关闭后恢复")
    _require_member_login(page)
    _open_agent(page)
    _cleanup_debug_switches(page, DEBUG["submit_fail"], DEBUG["query_fail"], DEBUG["policy_fail"], DEBUG["server_busy"])
    _open_inspiration(page)
    _select_template(page, "trend_gptimage1")
    try:
        _open_debug_panel(page)
        _set_debug_switch(page, DEBUG["submit_fail"], True)
        _shot(page, "dbg_submit_fail_on")
        _close_debug_panel(page)
        _submit_via_send(page)
        _wait_for_text(page, EXPECTED["network_error"], timeout_ms=30000)
        _shot(page, "dbg_submit_fail_failure")
    finally:
        _cleanup_debug_switches(page, DEBUG["submit_fail"])
        _shot(page, "dbg_submit_fail_off")


@pytest.mark.regression
@pytest.mark.p0
def test_dbg_query_fail_then_recover(page: Page, base_url: str):
    """L3-003：查询失败开关应允许提交，但最终查询失败。"""
    _matrix_case("L3-003", "查询失败开关：允许提交但结果失败，关闭后恢复")
    _require_member_login(page)
    _open_agent(page)
    _cleanup_debug_switches(page, DEBUG["submit_fail"], DEBUG["query_fail"], DEBUG["policy_fail"], DEBUG["server_busy"])
    _open_inspiration(page)
    _select_template(page, "trend_gptimage1")
    try:
        _open_debug_panel(page)
        _set_debug_switch(page, DEBUG["query_fail"], True)
        _shot(page, "dbg_query_fail_on")
        _close_debug_panel(page)
        _submit_via_send(page)
        _wait_for_text(page, EXPECTED["network_error"], timeout_ms=150000)
        _shot(page, "dbg_query_fail_failure")
    finally:
        _cleanup_debug_switches(page, DEBUG["query_fail"])
        _shot(page, "dbg_query_fail_off")


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.parametrize(
    "switch_label,expected_text,shot_prefix",
    [
        (DEBUG["policy_fail"], EXPECTED["policy_error"], "dbg_minus123"),
        (DEBUG["server_busy"], EXPECTED["server_busy"], "dbg_minus124"),
    ],
    ids=["L3-004", "L3-005"],
)
def test_dbg_query_fail_modes(page: Page, base_url: str, request: pytest.FixtureRequest, switch_label: str, expected_text: str, shot_prefix: str):
    """L3-004/005：-123/-124 开关应分别映射到 policy / server busy 失败文案。"""
    _matrix_case(request.node.callspec.id, f"{switch_label}：查询结果失败文案模拟")
    _require_member_login(page)
    _open_agent(page)
    _cleanup_debug_switches(page, DEBUG["submit_fail"], DEBUG["query_fail"], DEBUG["policy_fail"], DEBUG["server_busy"])
    _open_inspiration(page)
    _select_template(page, "trend_gptimage1")
    try:
        _open_debug_panel(page)
        _set_debug_switch(page, switch_label, True)
        _shot(page, f"{shot_prefix}_on")
        _close_debug_panel(page)
        _submit_via_send(page)
        _wait_for_text(page, expected_text, timeout_ms=150000)
        _shot(page, f"{shot_prefix}_failure")
    finally:
        _cleanup_debug_switches(page, switch_label)
        _shot(page, f"{shot_prefix}_off")


# ═══════════════════════════════════════════════════════════════
# L5-008 / L5-010
# ═══════════════════════════════════════════════════════════════


@pytest.mark.regression
@pytest.mark.p0
def test_reference_model_switch_truncates_to_new_limit(page: Page, base_url: str):
    """L5-008：从 9 图模型切到 Pro/Basic 时仅保留前 N 张参考图。"""
    _matrix_case("L5-008", "模型切换保留前 N 张参考图")
    _open_agent(page)
    _open_inspiration(page)
    files = [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"], IMG["img_face"]]
    _select_model_and_upload(page, MODELS["nano"], files)
    _wait_for_text(page, "4/9", timeout_ms=20000)
    srcs_4 = _visible_ref_image_srcs(page)
    assert len(srcs_4) == 4, f"9 图模型下应保留 4 张缩略图，实际 {len(srcs_4)}"
    _shot(page, "switch_retention_nano_4")

    _select_model(page, MODELS["pro"])
    page.wait_for_timeout(1500)
    _wait_for_text(page, "3/3", timeout_ms=20000)
    srcs_3 = _visible_ref_image_srcs(page)
    assert srcs_3 == srcs_4[:3], "切换到 Pokecut Pro 后应仅保留前 3 张参考图且顺序不变"
    _assert_upload_button_hidden_at_limit(page)
    _shot(page, "switch_retention_pro_3")

    _select_model(page, MODELS["basic"])
    page.wait_for_timeout(1500)
    _wait_for_text(page, "1/1", timeout_ms=20000)
    srcs_1 = _visible_ref_image_srcs(page)
    assert srcs_1 == srcs_4[:1], "切换到 Pokecut Basic 后应仅保留第 1 张参考图"
    _assert_upload_button_hidden_at_limit(page)
    _shot(page, "switch_retention_basic_1")


@pytest.mark.regression
@pytest.mark.p0
def test_reference_multi_select_overflow_shows_tip(page: Page, base_url: str):
    """L5-010：Basic/Pro/其他模型一次多选超限均提示并截断到上限。"""
    _matrix_case("L5-010")
    # 参考图上传边界是纯前端输入区交互，不消耗 credits；避免登录接口波动影响该组用例。
    overflow_cases = [
        (
            MODELS["basic"],
            [IMG["img_1k"], IMG["img_4k_jpg"]],
            "You can add up to 1 reference images",
            "1/1",
            "basic",
        ),
        (
            MODELS["pro"],
            [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"], IMG["img_face"]],
            "Pokecut Pro model supports up to 3 reference images.",
            "3/3",
            "pro",
        ),
        (
            MODELS["nano"],
            [
                IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"], IMG["img_face"],
                IMG["img_multi_face"], IMG["img_no_face"], IMG["img_low_res"],
                IMG["img_small_head_1"], IMG["img_small_head_3"], IMG["img_small_head_4"],
            ],
            "You can add up to 9 reference images",
            "9/9",
            "nano",
        ),
    ]
    try:
        for model_text, files, tip_text, expected_counter, shot_prefix in overflow_cases:
            _open_agent(page)
            _open_inspiration(page)
            _select_model(page, model_text)
            _upload_input(page).set_input_files([str(item) for item in files])
            expect(page.get_by_text(tip_text, exact=True).first).to_be_visible(timeout=5000)
            _shot(page, f"{shot_prefix}_overflow_tip")
            page.wait_for_timeout(5000)
            _wait_for_text(page, expected_counter, timeout_ms=20000)
            assert len(_visible_ref_image_srcs(page)) == int(expected_counter.split("/", 1)[0])
            _assert_upload_button_hidden_at_limit(page)
            _shot(page, f"{shot_prefix}_overflow_final")
            # 达上限后重新打开输入区，供下一等价类从干净状态开始。
            if model_text != MODELS["nano"]:
                while page.locator("button[aria-label='Delete']").count() > 0:
                    thumb = page.locator("div.flex-shrink-0.w-auto").first
                    if thumb.count() == 0:
                        break
                    thumb.hover(timeout=10000)
                    delete_btn = page.locator("button[aria-label='Delete']").first
                    expect(delete_btn).to_be_visible(timeout=10000)
                    delete_btn.click(timeout=10000)
                    page.wait_for_timeout(800)
    finally:
        # 防御性恢复：若任一等价类失败，也保证页面残留图片不会影响后续用例。
        page.goto(f"{BASE_URL}{SELECTORS['agent_url']}", wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(1000)
