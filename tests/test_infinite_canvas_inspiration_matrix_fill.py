
from __future__ import annotations

from pathlib import Path
import re

import allure
import pytest
from playwright.sync_api import Page, expect

from tests.test_infinite_canvas_inspiration_debug import (
    BASE_URL,
    DEBUG,
    EXPECTED,
    IMG,
    LIMITS,
    MODELS,
    SELECTORS,
    _assert_upload_button_hidden_at_limit,
    _assert_upload_button_restored_after_delete,
    _cleanup_debug_switches,
    _close_debug_panel,
    _hover_first_ref_thumbnail,
    _login_member,
    _matrix_case,
    _open_agent,
    _open_debug_panel,
    _open_inspiration,
    _ref_blob_count,
    _require_member_login,
    _select_model,
    _select_model_and_upload,
    _select_template,
    _set_debug_switch,
    _shot,
    _submit_via_send,
    _upload_button,
    _upload_input,
    _visible_ref_image_srcs,
    _wait_for_text,
)


@pytest.fixture
def page(standalone_page):
    return standalone_page


LAYER_SUITE = {
    "L1": "L1 页面元素存在性",
    "L2": "L2 交互行为",
    "L3": "L3 异常 / 权限 / 兼容流程",
    "L4": "L4 PRD 验收标准",
    "L5": "L5 数据边界值",
    "L6": "L6 核心 Happy Path / E2E",
}


def _title(case_id: str, summary: str) -> None:
    # 元数据统一来自 debug 模块的 cases.md 映射，避免两个脚本各自漂移。
    _matrix_case(case_id)


def _open_hair_select_modal(page: Page) -> None:
    _open_agent(page)
    _open_inspiration(page)
    page.get_by_role("button", name="Hair", exact=True).click(timeout=10000)
    page.wait_for_timeout(1800)
    page.locator("[data-explore-style-id='pkweb_comfyui_hairthiken']").first.click(force=True, timeout=10000)
    expect(page.locator("div[data-canvas-seo-select-dialog]")).to_be_visible(timeout=20000)
    page.wait_for_timeout(2500)


def _select_upload_card(page: Page, path: Path) -> None:
    with page.expect_file_chooser() as fc:
        page.locator("div[data-canvas-seo-select-dialog] button:has-text('Upload')").first.click(timeout=10000)
    fc.value.set_files([str(path)])
    page.wait_for_timeout(1200)


def _canvas_upload_button(page: Page):
    return page.locator("button[aria-label='Upload Image']").first


def _click_left_upload_and_set(page: Page, path: Path) -> None:
    with page.expect_file_chooser() as fc:
        _canvas_upload_button(page).click(timeout=10000)
    fc.value.set_files([str(path)])
    page.wait_for_timeout(1200)


def _parse_credits(page: Page) -> int:
    body = page.locator("body").inner_text(timeout=5000)
    m = re.search(r"Credits:(\d+)", body)
    assert m, f"未找到 credits 文本：{body[-300:]}"
    return int(m.group(1))


def _wait_generation_progress(page: Page) -> None:
    page.wait_for_function(
        """() => {
            const text = document.body.innerText;
            return text.includes('Less than 1 min') || text.includes('Premium boost applied. Processing will finish in under 30s.') || /\\b\\d{1,3}%\\b/.test(text);
        }""",
        timeout=60000,
    )


def _open_settings(page: Page) -> None:
    page.wait_for_timeout(2500)
    clicked = page.evaluate("""() => {
        const visible = (el) => {
            const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
        };
        const target = [...document.querySelectorAll('button,div,span')].find((el) => visible(el) && (el.textContent || "").trim() === 'Setting');
        if (!target) return false;
        target.click();
        return true;
    }""")
    if not clicked:
        page.locator("text=Setting").first.click(force=True, timeout=10000)
    page.wait_for_timeout(1500)
    expect(page.get_by_text("Output Ratio:", exact=True)).to_be_visible(timeout=10000)


def _open_inspiration_and_assert(page: Page) -> None:
    _open_agent(page)
    _open_inspiration(page)


# ═══════════════════════════════════════════════════════════════
# L1
# ═══════════════════════════════════════════════════════════════


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.parametrize(
    "case_id,action",
    [
        ("L1-001", "default"),
        ("L1-002", "tabs"),
        ("L1-003", "cards"),
        ("L1-004", "select_modal"),
    ],
    ids=["L1-001", "L1-002", "L1-003", "L1-004"],
)
def test_matrix_l1_structure(page: Page, case_id: str, action: str):
    _title(case_id, {
        "L1-001": "默认页结构存在",
        "L1-002": "Inspiration 面板与 9 个 tab",
        "L1-003": "代表模板卡片存在",
        "L1-004": "SEO Select 弹窗结构存在",
    }[case_id])
    if action == "default":
        _open_agent(page)
        expect(page.locator(SELECTORS["prompt_textarea"])).to_be_visible(timeout=20000)
        for text in ["Inspiration", "Remove BG", "Enhance", "Erase", "AI Replace", "Portrait Editor", "Clothes Changer"]:
            expect(page.get_by_text(text, exact=True)).to_be_visible(timeout=10000)
    elif action == "tabs":
        _open_inspiration_and_assert(page)
        for tab in ["Trending", "Festival", "Face", "Body", "Hair", "Creative Effects", "Ecommerce", "Anime gaming", "Digital_art"]:
            expect(page.get_by_role("button", name=tab, exact=True)).to_be_visible(timeout=10000)
        assert page.locator("[data-explore-style-id]").count() > 0
        expect(page.get_by_text("Create Similar", exact=True).first).to_be_visible(timeout=10000)
    elif action == "cards":
        _open_inspiration_and_assert(page)
        for sid in ["trend_gptimage1", "trend_flux1", "pkweb_comfyui_hairthiken"]:
            expect(page.locator(f"[data-explore-style-id='{sid}']").first).to_be_visible(timeout=10000)
    elif action == "select_modal":
        _open_hair_select_modal(page)
        for text in ["Select", "Upload", "Canvas"]:
            expect(page.get_by_text(text, exact=True)).to_be_visible(timeout=10000)
        expect(page.locator("div[data-canvas-seo-select-dialog] button[aria-label='Close']").first).to_be_visible(timeout=10000)
    _shot(page, f"{case_id}_{action}_final")

# ═══════════════════════════════════════════════════════════════
# L2
# ═══════════════════════════════════════════════════════════════


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.parametrize(
    "case_id,action",
    [
        ("L2-001", "collapse"),
        ("L2-002", "gpt_prefill"),
        ("L2-003", "flux_prefill"),
        ("L2-004", "flux_upload"),
        ("L2-005", "settings"),
        ("L2-006", "submit_generate"),
        ("L2-008", "select_upload_cancel_then_upload"),
        ("L2-009", "select_close"),
        ("L2-010", "left_toolbar_upload"),
    ],
    ids=["L2-001", "L2-002", "L2-003", "L2-004", "L2-005", "L2-006", "L2-008", "L2-009", "L2-010"],
)
def test_matrix_l2_interactions(page: Page, case_id: str, action: str):
    _title(case_id, {
        "L2-001": "Inspiration 面板可打开/收起",
        "L2-002": "文生图模板点击后预填且可编辑",
        "L2-003": "图生图模板点击后预填并展示参考图提示",
        "L2-004": "图生图上传参考图后进入激活态",
        "L2-005": "Setting 弹窗结构与选项",
        "L2-006": "文生图手动提交生成并扣 15 credits",
        "L2-008": "Select 上传可取消后继续上传",
        "L2-009": "Select 弹窗可关闭",
        "L2-010": "左侧工具栏上传图片进入 Canvas",
    }[case_id])
    if action == "collapse":
        _open_inspiration_and_assert(page)
        clicked = page.evaluate("""() => {
            const visible = (el) => {
                const r = el.getBoundingClientRect();
                const s = getComputedStyle(el);
                return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden' && s.opacity !== '0';
            };
            const target = [...document.querySelectorAll('button,div,span')].find((el) => visible(el) && (el.textContent || "").trim() === 'Collapse');
            if (!target) return false;
            target.click();
            return true;
        }""")
        if not clicked:
            page.locator(SELECTORS["inspiration_button"]).first.click(timeout=10000)
        page.wait_for_timeout(1000)
        expect(page.get_by_role("button", name="Trending", exact=True)).to_have_count(0)
        expect(page.locator(SELECTORS["prompt_textarea"])).to_be_visible(timeout=10000)
    elif action == "gpt_prefill":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        _select_template(page, "trend_gptimage1")
        prompt = page.locator(SELECTORS["prompt_textarea"]).first
        expect(page.get_by_text("ChatGPT Image 2.0", exact=True)).to_be_visible(timeout=10000)
        expect(page.get_by_text("15", exact=True)).to_be_visible(timeout=10000)
        expect(page.locator("img.canvas-text2img-submit-guide").first).to_be_visible(timeout=10000)
        expect(prompt).not_to_have_value("", timeout=10000)
    elif action == "flux_prefill":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        _select_template(page, "trend_flux1")
        prompt = page.locator(SELECTORS["prompt_textarea"]).first
        expect(prompt).not_to_have_value("", timeout=10000)
        expect(page.get_by_text("Upload or click 'Chat to Edit' on the canvas image.", exact=True)).to_be_visible(timeout=10000)
    elif action == "flux_upload":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        _select_template(page, "trend_flux1")
        _upload_input(page).set_input_files([str(IMG["img_1k"])])
        page.wait_for_timeout(2000)
        assert _ref_blob_count(page) >= 1
        expect(page.locator(SELECTORS["prompt_textarea"])).to_be_visible(timeout=10000)
    elif action == "settings":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        _select_template(page, "trend_gptimage1")
        _open_settings(page)
        for ratio in ["1:1", "3:4", "4:3", "9:16", "16:9", "2:3", "3:2", "4:5", "9:21"]:
            expect(page.get_by_text(ratio, exact=True)).to_be_visible(timeout=10000)
        for token in ["1K", "2K", "4K", "1", "2", "3", "4"]:
            expect(page.get_by_text(token, exact=True)).to_be_visible(timeout=10000)
    elif action == "submit_generate":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        _select_template(page, "trend_gptimage1")
        before = _parse_credits(page)
        _submit_via_send(page)
        _wait_generation_progress(page)
        page.wait_for_timeout(3000)
        after = _parse_credits(page)
        assert before - after == 15, f"生成后 credits 应减少 15，实际 {before}->{after}"
    elif action == "select_upload_cancel_then_upload":
        _open_hair_select_modal(page)
        with page.expect_file_chooser() as fc:
            page.locator("div[data-canvas-seo-select-dialog] button:has-text('Upload')").first.click(timeout=10000)
        fc.value.set_files([])
        expect(page.locator("div[data-canvas-seo-select-dialog]")).to_be_visible(timeout=10000)
        _select_upload_card(page, IMG["img_1k"])
        expect(page.locator("div[data-canvas-seo-select-dialog] img[src^='blob:'], div[data-canvas-seo-select-dialog] img[src^='data:image/webp']").first).to_be_visible(timeout=10000)
    elif action == "select_close":
        _open_hair_select_modal(page)
        page.locator("div[data-canvas-seo-select-dialog] button[aria-label='Close']").first.click(timeout=10000)
        page.wait_for_timeout(1000)
        expect(page.locator("div[data-canvas-seo-select-dialog]")).to_have_count(0)
        expect(page.locator(SELECTORS["prompt_textarea"])).to_be_visible(timeout=10000)
    elif action == "left_toolbar_upload":
        _open_agent(page)
        _click_left_upload_and_set(page, IMG["img_1k"])
        assert "1/9" in page.locator("body").inner_text(timeout=5000)
        _open_hair_select_modal(page)
        assert page.locator("div[data-canvas-seo-select-dialog] img[src^='data:image/webp']").count() > 0
    _shot(page, f"{case_id}_{action}_final")

# ═══════════════════════════════════════════════════════════════
# L3
# ═══════════════════════════════════════════════════════════════


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.parametrize(
    "case_id,action",
    [
        ("L3-001", "auth_block"),
        ("L3-006", "corrupt_upload"),
    ],
    ids=["L3-001", "L3-006"],
)
def test_matrix_l3_failures(page: Page, case_id: str, action: str):
    _title(case_id, {
        "L3-001": "匿名态 Select 选择图出现登录拦截",
        "L3-006": "损坏图片上传异常",
    }[case_id])
    if action == "auth_block":
        _open_hair_select_modal(page)
        _select_upload_card(page, IMG["img_1k"])
        page.locator("div[data-canvas-seo-select-dialog] img[src^='blob:'], div[data-canvas-seo-select-dialog] img[src^='data:image/webp']").first.click(force=True, timeout=10000)
        expect(page.locator("[data-testid='auth-dialog']").first).to_be_visible(timeout=10000)
        expect(page.locator("[data-testid='auth-submit']").first).to_be_visible(timeout=10000)
        _shot(page, f"{case_id}_{action}_final")
    elif action == "corrupt_upload":
        _open_hair_select_modal(page)
        with page.expect_file_chooser() as fc:
            page.locator("div[data-canvas-seo-select-dialog] button:has-text('Upload')").first.click(timeout=10000)
        fc.value.set_files([str(IMG["img_corrupt"])]) if "img_corrupt" in IMG else fc.value.set_files([str((Path('test_images') / '损坏的图.png').resolve())])
        page.wait_for_timeout(3000)
        assert page.locator("div[data-canvas-seo-select-dialog]").count() > 0
        assert page.locator("div[data-canvas-seo-select-dialog] img[src^='blob:'], div[data-canvas-seo-select-dialog] img[src^='data:image/webp']").count() == 0
    _shot(page, f"{case_id}_{action}_final")

# ═══════════════════════════════════════════════════════════════
# L5
# ═══════════════════════════════════════════════════════════════


@pytest.mark.regression
@pytest.mark.p0
@pytest.mark.parametrize(
    "case_id,action",
    [
        ("L5-002", "textarea_edit"),
        ("L5-004", "canvas_multi_upload_select"),
        ("L5-005", "select_refresh_repeat"),
        ("L5-006", "all_models_to_limit"),
        ("L5-007", "hover_delete_x"),
        ("L5-009", "multi_select_not_over_limit"),
    ],
    ids=["L5-002", "L5-004", "L5-005", "L5-006", "L5-007", "L5-009"],
)
def test_matrix_l5_bounds(page: Page, case_id: str, action: str):
    _title(case_id, {
        "L5-002": "模板预填 textarea 可编辑且状态不丢失",
        "L5-004": "连续左侧上传两张画布图后 Select 单选",
        "L5-005": "Select 上传图刷新后保留且不重复",
        "L5-006": "各模型参考图上传上限正确",
        "L5-007": "上限态 hover 删除参考图并恢复上传",
        "L5-009": "一次多选未超上限时数量与状态正确",
    }[case_id])
    if action == "textarea_edit":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        _select_template(page, "trend_gptimage1")
        prompt = page.locator(SELECTORS["prompt_textarea"]).first
        value = prompt.input_value()
        prompt.fill(value + " -- codex edit check")
        page.wait_for_timeout(2500)
        assert "-- codex edit check" in prompt.input_value()
        expect(page.get_by_text("ChatGPT Image 2.0", exact=True)).to_be_visible(timeout=10000)
    elif action == "canvas_multi_upload_select":
        _open_agent(page)
        _click_left_upload_and_set(page, IMG["img_1k"])
        _click_left_upload_and_set(page, IMG["img_face"])
        _open_hair_select_modal(page)
        assert page.locator("div[data-canvas-seo-select-dialog] img[src^='data:image/webp']").count() >= 1
    elif action == "select_refresh_repeat":
        _open_hair_select_modal(page)
        _select_upload_card(page, IMG["img_1k"])
        for _ in range(2):
            page.reload(wait_until="domcontentloaded")
            page.wait_for_timeout(5000)
            _open_hair_select_modal(page)
            assert page.locator("div[data-canvas-seo-select-dialog] img[src^='blob:'], div[data-canvas-seo-select-dialog] img[src^='data:image/webp']").count() > 0
    elif action == "all_models_to_limit":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        model_cases = [
            (MODELS["basic"], [IMG["img_1k"]], "1/1"),
            (MODELS["pro"], [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"]], "3/3"),
            (MODELS["nano"], [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"], IMG["img_face"], IMG["img_multi_face"], IMG["img_no_face"], IMG["img_low_res"], IMG["img_small_head_1"], IMG["img_small_head_3"]], "9/9"),
            (MODELS["chatgpt"], [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"], IMG["img_face"], IMG["img_multi_face"], IMG["img_no_face"], IMG["img_low_res"], IMG["img_small_head_1"], IMG["img_small_head_3"]], "9/9"),
            (MODELS["seedream"], [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"], IMG["img_face"], IMG["img_multi_face"], IMG["img_no_face"], IMG["img_low_res"], IMG["img_small_head_1"], IMG["img_small_head_3"]], "9/9"),
        ]
        for model_text, files, counter in model_cases:
            _select_model_and_upload(page, model_text, files)
            _wait_for_text(page, counter, timeout_ms=20000)
            _assert_upload_button_hidden_at_limit(page)
    elif action == "hover_delete_x":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        _select_model_and_upload(page, MODELS["pro"], [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"]])
        thumb = page.locator("div.flex-shrink-0.w-auto").first
        thumb.hover(timeout=10000)
        page.wait_for_timeout(800)
        delete_btn = page.locator("button[aria-label='Delete']").first
        expect(delete_btn).to_be_visible(timeout=10000)
        delete_btn.click(timeout=10000)
        page.wait_for_timeout(1200)
        _assert_upload_button_restored_after_delete(page)
    elif action == "multi_select_not_over_limit":
        _require_member_login(page)
        _open_inspiration_and_assert(page)
        model_cases = [
            (MODELS["basic"], [IMG["img_1k"]], 1, True),
            (MODELS["pro"], [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"]], 3, True),
            (MODELS["nano"], [IMG["img_1k"], IMG["img_4k_jpg"], IMG["img_4k_png"]], 3, False),
        ]
        for model_text, files, expected_count, should_hide in model_cases:
            _select_model(page, model_text)
            _upload_input(page).set_input_files([str(item) for item in files])
            page.wait_for_timeout(3000)
            actual_count = len(_visible_ref_image_srcs(page))
            assert actual_count == expected_count, f"{model_text} 多选后应有 {expected_count} 张，实际 {actual_count}"
            visible_upload_count = page.locator("[title='Upload reference images']:visible").count()
            assert visible_upload_count == (0 if should_hide else 1), f"{model_text} 上传按钮可见性错误"
    _shot(page, f"{case_id}_{action}_final")
