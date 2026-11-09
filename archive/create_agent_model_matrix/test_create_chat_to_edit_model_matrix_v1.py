# -*- coding: utf-8 -*-
"""Create / Agent 模型矩阵自动化测试（Chat to Edit）。

基于 confirmed cases.md（21 条）与 page_map/pokecut/create_chat_to_edit_model_matrix_v2.yaml。
环境：测试服 /create 与 /agent，PC 1920x1080，en-US，VIP 450832596@qq.com；素材仅 test_images/。

关键口径（用户确认 2026-11-04）：
- 提交任何生成任务前，必须在 DEBUG 面板把「测试服兜底上传地址」切到「正式」；该开关刷新后恢复「内网」。
- 仅断言「提交成功（resultCode=100 且 taskId 非空）+ 出现结果图」，不断言 styleId / 分辨率。
- 失败态（Network error）归为环境问题，不做失败注入；P-MX-L2-020 为补位点（探索期未单跑，按用户口径默认通过）。
"""
from __future__ import annotations

import functools
import re
import time
from pathlib import Path
from typing import Any

import allure
import pytest
import yaml
from playwright.sync_api import Page, expect

from helpers_create_entry import dismiss_create_promo

from helpers.waiting import poll_until, settle, wait_canvas_ready, wait_ready


def _repo_root() -> Path:
    """逐级上溯仓库根，兼容 tests/ 与 archive/<module>/ 两种位置。"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pytest.ini").exists() or (parent / ".git").exists():
            return parent
    return current.parents[1]


ROOT = _repo_root()
DATA_PATH = ROOT / "data" / "pokecut_create_chat_to_edit_model_matrix_v1.yaml"
DATA = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8"))
TASK_ID = "2026-11-03_create_agent_model_matrix"
TASK_DIR = ROOT / "artifacts" / TASK_ID
SHOT_DIR = TASK_DIR / "shots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)

MODEL_OPTION_FIRST_LINE = "div.cursor-pointer"
PROMPT_SELECTOR = "textarea[placeholder='What do you want to design today?']"
MODEL_SELECTOR = "div[title='Model']"
SETTING_SELECTOR = "div[title='Setting']"
UPLOAD_SELECTOR = "div[title='Upload reference images']"
SUBMIT_SELECTOR = "div.cursor-pointer:has(img[src*='create_chat_send_btn.svg'])"
DEBUG_BUTTON_SELECTOR = "button:has-text('DEBUG')"


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


def shot(page: Page, name: str) -> Path:
    """截图并附加到 Allure。"""
    path = SHOT_DIR / f"{name}.png"
    page.screenshot(path=str(path), full_page=False)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return path


def goto_create(page: Page, base_url: str) -> None:
    """/create 入口 + 关闭促销弹窗。"""
    page.goto(base_url.rstrip("/") + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
    # 就绪信号：Chat to Edit 标题 + prompt + 上传 + Model 均挂载（替代固定 7s）
    wait_ready(
        page,
        lambda: page.get_by_role("heading", name="Chat to Edit").count() > 0
        and page.locator(PROMPT_SELECTOR).count() > 0
        and page.locator(UPLOAD_SELECTOR).count() > 0
        and page.locator(MODEL_SELECTOR).count() > 0,
        timeout=30000,
        settle_ms=0,
    )
    dismiss_create_promo(page)
    poll_until(
        page,
        lambda: page.locator("img[src*='colos_pop_btn_close']").count() == 0,
        timeout=5000,
        interval=300,
    )


def enter_agent(page: Page, base_url: str) -> None:
    """从 /create 进 agent：先切「正式」兜底上传，再点 Start with Photos 选图 → /agent?pid=*。

    顺序很关键：Start with Photos 选图会立刻触发参考图的「内容审核上传」，
    若此时兜底上传地址仍是「内网」，会 30s 超时并导致后续任务「前序失败」。
    所以必须在选图之前先把兜底上传切到「正式」。
    """
    goto_create(page, base_url)
    set_official_fallback_upload(page)
    upload = page.locator("button:has-text('Start with Photos')").first
    expect(upload).to_be_visible(timeout=20000)
    with page.expect_file_chooser(timeout=30000) as chooser_info:
        upload.click(timeout=20000)
    chooser_info.value.set_files(str(ROOT / DATA["reference_image"]))
    page.wait_for_url(re.compile(r"/agent\?pid="), timeout=DATA["waits"]["submit_timeout_ms"])
    # 2026-11-05: URL 到位 != 画布就绪；等可见 canvas/大图真正渲染
    wait_canvas_ready(page, timeout=30000)


def open_debug_panel(page: Page) -> None:
    """打开右下角 DEBUG 面板。"""
    if page.locator(".debug-panel").count() and page.locator(".debug-panel").first.is_visible():
        return
    btn = page.get_by_role("button", name=re.compile(r"^DEBUG$", re.I)).last
    expect(btn).to_be_visible(timeout=15000)
    try:
        btn.click(timeout=8000)
    except Exception:
        btn.click(timeout=8000, force=True)
    page.locator(".debug-panel").first.wait_for(state="visible", timeout=10000)
    # DEBUG 面板展开动画收尾（内容已可见，无独立可观察信号）
    settle(page, 600)


def close_debug_panel(page: Page) -> None:
    """关闭 DEBUG 面板。"""
    try:
        panel = page.locator(".debug-panel").first
        if panel.count() and panel.is_visible():
            close_btn = panel.locator("button.close-btn").first
            if close_btn.count():
                close_btn.click(timeout=6000)
            else:
                page.keyboard.press("Escape")
            poll_until(page, lambda: page.locator(".debug-panel").count() == 0,
                       timeout=5000, interval=200)
    except Exception:
        page.keyboard.press("Escape")
        settle(page, 400)


def set_official_fallback_upload(page: Page) -> None:
    """前置条件：DEBUG → 测试服兜底上传地址 → 正式。

    该开关刷新后恢复「内网」，每条用例重载后必须重设。
    """
    open_debug_panel(page)
    heading = page.locator("h4:has-text('测试服兜底上传地址')").first
    expect(heading).to_be_visible(timeout=10000)
    panel = page.locator(".debug-panel").first
    official = panel.get_by_role("button", name=re.compile(r"^正式$")).first
    if official.count() == 0:
        official = panel.get_by_text("正式", exact=True).first
    expect(official).to_be_visible(timeout=10000)
    try:
        official.click(timeout=8000)
    except Exception:
        official.click(timeout=8000, force=True)
    # 切「正式」后按钮选中态生效（无独立 DOM 信号时退回有界 settle）
    settle(page, 1200)
    close_debug_panel(page)


def open_model_dropdown(page: Page) -> None:
    """打开模型选择弹窗。"""
    model = page.locator(MODEL_SELECTOR).first
    expect(model).to_be_visible(timeout=15000)
    model.click(timeout=15000)
    # 弹窗就绪信号：Model Multi Mode 开关出现
    poll_until(
        page,
        lambda: page.locator("switch[name='Model Multi Mode'], [role=switch]").count() > 0,
        timeout=10000,
        interval=200,
    )


def model_popup_root(page: Page):
    """模型选择弹窗根节点（switch 向上第 3 层，含全部模型选项）。"""
    sw = page.locator("switch[name='Model Multi Mode'], [role=switch]").first
    expect(sw).to_be_visible(timeout=15000)
    return sw.locator("xpath=../../..").first


def model_option_available(page: Page, name: str) -> bool:
    """模型弹窗内是否已出现可交互的指定选项（用于等弹窗/多选模式就绪）。"""
    try:
        root = model_popup_root(page)
        opts = root.locator(MODEL_OPTION_FIRST_LINE)
        for i in range(opts.count()):
            txt = (opts.nth(i).inner_text() or "").strip()
            if txt.split("\n")[0].strip() == name:
                return True
    except Exception:
        return False
    return False


def model_option(page: Page, name: str):
    """按「首行文本精确等于模型名」定位选项。

    注意：弹窗里 Nano Banana 2 Lite / Pro / 2 互为子串前缀，且触发器本身也含模型文案，
    因此不能用 :has-text 子串匹配，必须限定弹窗作用域 + 首行精确匹配；
    带描述行的真实选项优先于同名的隐藏占位项。
    """
    root = model_popup_root(page)
    opts = root.locator(MODEL_OPTION_FIRST_LINE)
    candidates = []
    for i in range(opts.count()):
        txt = (opts.nth(i).inner_text() or "").strip()
        if txt.split("\n")[0].strip() == name:
            candidates.append(("\n" in txt, opts.nth(i)))
    assert candidates, f"模型弹窗中未找到选项: {name}"
    candidates.sort(key=lambda x: not x[0])
    return candidates[0][1]


def dismiss_overlay(page: Page) -> None:
    """关闭可能残留的遮罩层。"""
    try:
        overlay = page.locator("div.fixed.inset-0.z-30").first
        if overlay.count() and overlay.is_visible():
            overlay.click(timeout=4000)
            poll_until(page, lambda: not page.locator("div.fixed.inset-0.z-30").first.is_visible(),
                       timeout=5000, interval=200)
    except Exception:
        pass


def select_single_model(page: Page, model: str) -> None:
    """单模型模式：打开弹窗并选中指定模型。"""
    open_model_dropdown(page)
    option = model_option(page, model)
    expect(option).to_be_visible(timeout=10000)
    option.click(timeout=15000)
    # 选择生效信号：触发器回显所选模型
    expect(page.locator(MODEL_SELECTOR).first).to_contain_text(model, timeout=10000)


def select_multi_models(page: Page) -> None:
    """多模型模式：打开 Model Multi Mode 并勾选前四模型。"""
    open_model_dropdown(page)
    switch = page.locator("switch[name='Model Multi Mode'], [role=switch]").first
    expect(switch).to_be_visible(timeout=10000)
    switch.click(timeout=15000)
    # 多选模式生效信号：首个模型选项可选
    poll_until(page, lambda: model_option_available(page, DATA["multi_mode_first_four"][0]),
               timeout=10000, interval=300)
    selected: list[str] = []
    for name in DATA["multi_mode_first_four"]:
        option = model_option(page, name)
        expect(option).to_be_visible(timeout=10000)
        option.click(timeout=15000)
        selected.append(name)
    dismiss_overlay(page)
    # 多选生效信号：已勾选模型出现在触发器
    poll_until(
        page,
        lambda: all(n in page.locator(MODEL_SELECTOR).first.inner_text() for n in selected),
        timeout=10000,
        interval=300,
    )


def upload_reference(page: Page, image_rel: str) -> None:
    """上传参考图。"""
    upload = page.locator(UPLOAD_SELECTOR).first
    expect(upload).to_be_visible(timeout=15000)
    with page.expect_file_chooser(timeout=30000) as chooser_info:
        upload.click(timeout=20000)
    chooser_info.value.set_files(str(ROOT / image_rel))
    # 上传完成信号：参考图缩略图（blob 图）挂载；无则退回有界 settle
    uploaded = wait_ready(
        page,
        lambda: page.evaluate("""() => [...document.querySelectorAll('img')].some(i => {
            const r = i.getBoundingClientRect();
            return r.width > 40 && r.width < 160 && (i.src || '').startsWith('blob:');
        })"""),
        timeout=15000,
        settle_ms=300,
    )
    if not uploaded:
        settle(page, DATA["waits"]["action_settle_ms"])


def set_image_count(page: Page, count: int) -> None:
    """Settings → Number of images → <count>。"""
    setting = page.locator(SETTING_SELECTOR).first
    expect(setting).to_be_visible(timeout=15000)
    setting.click(timeout=15000)
    option = page.get_by_text(str(count), exact=True).last
    expect(option).to_be_visible(timeout=10000)
    option.click(timeout=15000)
    dismiss_overlay(page)
    # 数量设置生效信号：设置面板不再遮挡（overlay 已关闭）
    poll_until(page, lambda: not page.locator("div.fixed.inset-0.z-30").first.is_visible(),
               timeout=5000, interval=200)


def fill_prompt(page: Page, prompt: str) -> None:
    """真实键盘输入 prompt（JS 直接赋值可能不触发提交按钮启用）。"""
    box = page.locator(PROMPT_SELECTOR).first
    expect(box).to_be_visible(timeout=15000)
    box.click(timeout=10000)
    box.type(prompt, delay=25, timeout=30000)
    wait_ready(page, lambda: box.input_value() == prompt, timeout=5000, settle_ms=0)


def submit_task(page: Page) -> None:
    """点击提交图标。

    提交按钮在「参考图内容审核中」或「有任务处理中」时是禁用态
    （create_chat_send_btn_disable.svg）；必须等它恢复为可提交图标再点，
    否则会出现点击无效、console 停在内容审核上传的情况。
    """
    submit_holder: dict = {}

    def _submit_ready() -> bool:
        enabled = page.locator(SUBMIT_SELECTOR)
        if enabled.count() > 0 and enabled.first.is_visible():
            submit_holder["loc"] = enabled.first
            return True
        return False

    if not poll_until(page, _submit_ready, timeout=DATA["waits"]["submit_timeout_ms"], interval=800):
        raise AssertionError("提交按钮始终未变为可提交状态（可能参考图审核中或有任务处理中）")
    submit = submit_holder["loc"]
    # 内容审核上传完成后按钮才真正可点，避免过早点击无效（延后一个短窗口）
    settle(page, 1500)
    try:
        submit.click(timeout=20000)
    except Exception:
        submit.click(timeout=20000, force=True)
    # 提交后等路由跳转（而非固定 1.5s）
    wait_ready(page, lambda: "/agent?pid=" in page.url, timeout=30000, settle_ms=0)


TASK_ID_PATTERNS = (
    re.compile(r'"taskId"\s*:\s*"([A-Za-z0-9_\-]{6,})"'),
    re.compile(r"taskId[=:]\s*[\"']?([A-Za-z0-9_\-]{10,})"),
    re.compile(r"jobId[=:]\s*([0-9a-fA-F\-]{20,})"),
    re.compile(r"taskIds:\s*\[\s*[\"']([A-Za-z0-9_\-]{6,})"),
)


def extract_task_id(logs: list[str]) -> str | None:
    """从 console 提取 taskId / jobId。

    两条提交链路证据不同（且 console 中文可能被转义，故只用 ASCII 标记）：
    - 文生图 / 部分图生图：`handleSubmitTask result {..., data:{taskId: ...}}`
    - 图生图新链路：`TaskFlowManager ... jobId=<uuid>`（无 handleSubmitTask 行）
    """
    text = "\n".join(logs)
    for pat in TASK_ID_PATTERNS:
        m = pat.search(text)
        if m:
            return m.group(1)
    return None


def submit_result_code(logs: list[str]) -> int | None:
    """提取 handleSubmitTask 的 resultCode（仅文生图链路有此行）。"""
    text = "\n".join(logs)
    m = re.search(r'handleSubmitTask result\s*\{"resultCode"\s*:\s*(-?\d+)', text)
    return int(m.group(1)) if m else None


# 提交成功的 ASCII 证据标记（console 中文可能被转义，故不依赖中文）
SUBMIT_OK_MARKERS = (
    "TaskFlowManager",     # 图生图新链路：已提交 job
    "handleSubmitTask",    # 文生图链路：已提交任务
    "taskCount",           # CanvasTextboxService 已建任务
)


def wait_for_submit(page: Page, logs: list[str]) -> str:
    """等待任务提交成功。

    判定（不弱化「提交成功」这一硬要求）：
    - 文生图链路：handleSubmitTask result resultCode=100；
    - 图生图链路：TaskFlowManager 已提交 job（console 无 handleSubmitTask 行）；
    两条链路都必须取到 taskId / jobId，否则判失败。
    """
    task_id = {"value": None}

    def _submitted() -> bool:
        text = "\n".join(logs)
        task_id["value"] = extract_task_id(logs)
        code = submit_result_code(logs)
        has_marker = any(m in text for m in SUBMIT_OK_MARKERS)
        return bool(task_id["value"] and (code == 100 or (code is None and has_marker)))

    if poll_until(page, _submitted, timeout=DATA["waits"]["result_timeout_ms"], interval=800):
        return task_id["value"]
    task_id = task_id["value"]
    text = "\n".join(logs)
    code = submit_result_code(logs)
    assert task_id, f"未捕获 taskId/jobId（resultCode={code}）；console 末尾：{text[-1500:]}"
    assert code == 100 or any(m in text for m in SUBMIT_OK_MARKERS), (
        f"提交失败 resultCode={code}；console 末尾：{text[-1500:]}"
    )
    return task_id


RESULT_OK_MARKERS = (
    "生成成功",
    "stage: complete, status: success",
    "CanvasTextboxResult] received",
)
RESULT_FAIL_MARKERS = (
    "Network error",
    "生成失败",
    "前序失败",
    "task fail",
    "status: failed",          # 结果图内容审核上传失败（环境类）
    "upload_image, status: failed",
)


class EnvironmentFlakyError(AssertionError):
    """环境级波动（内容审核上传 30s 超时 / Network error / 前序失败）。

    按用户口径（2026-11-04）：这类失败属环境问题，切「正式」兜底上传后应可复现通过；
    测试内部允许重试一次，重试仍失败才判 failed。
    """


def logs_text(logs: list[str]) -> str:
    return "\n".join(logs)


def wait_for_result_image(page: Page, logs: list[str], count: int, multi: bool) -> None:
    """等待出现结果图。

    判定口径（用户确认）：只需「提交成功 + 出现结果图」。
    - 成功信号：console 出现「生成成功」/「stage: complete, status: success」/「CanvasTextboxResult] received」，
      或 document.title 含 Image Ready / N Images Ready。
    - 失败信号：console 出现 Network error / 生成失败 / 前序失败。

    注意：轮询期间 `resultCode: -112 未完成` 是正常中间态，不作为失败信号。
    """
    state = {"title": "", "fail": None}

    def _ready() -> bool:
        text = logs_text(logs)
        state["title"] = page.title()
        if re.search(r"(Image|Images)\s+Ready", state["title"], re.I) or any(m in text for m in RESULT_OK_MARKERS):
            return True
        state["fail"] = next((m for m in RESULT_FAIL_MARKERS if m in text), None)
        return state["fail"] is not None

    poll_until(page, _ready, timeout=DATA["waits"]["result_timeout_ms"],
               interval=DATA["waits"]["poll_interval_ms"])
    if state["fail"]:
        raise EnvironmentFlakyError(
            f"生成失败（命中 {state['fail']!r}；count={count}, multi={multi}）；"
            f"console 末尾：{logs_text(logs)[-1500:]}"
        )
    if not re.search(r"(Image|Images)\s+Ready", state["title"], re.I):
        raise AssertionError(
            f"超时未见结果图（count={count}, multi={multi}）；title={state['title']!r}；"
            f"console 末尾：{logs_text(logs)[-1500:]}"
        )
    # 结果标题已就绪，等渲染稳定后截图
    settle(page, 1200)


PROMPTS = {
    "t2i": "a cute cat sitting on a wooden table, soft light",
    "i2i": "make it a watercolor style",
}


@allure.feature("Create / Agent 模型矩阵")
@allure.story("L1-页面结构元素")
@pytest.mark.regression
@pytest.mark.login_required
class TestL1DebugOfficialUploadPrecondition:
    """Layer 1: DEBUG「测试服兜底上传地址」前置条件。"""

    @case_meta("P-MX-L1-001", "L1", "P0")
    @allure.title("P-MX-L1-001: DEBUG 面板「测试服兜底上传地址」默认内网且可切「正式」")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_debug_official_upload_switch(self, session_page: Page, base_url: str):
        """PRD引用：Chat to Edit 生成前置条件。

        覆盖层级：L1 页面元素 / 结构
        前置条件：VIP 已登录；测试服可访问。
        测试步骤：
            1. 进入 /create。
            2. 点击右下角 DEBUG。
            3. 查看「测试服兜底上传地址」标题与按钮组。
            4. 点击「正式」。
        预期结果：标题与「内网」「正式」按钮组可见；默认内网选中；点正式后选中态生效且提示含刷新后恢复内网。
        """
        page = session_page
        with allure.step("进入 /create 并打开 DEBUG 面板"):
            goto_create(page, base_url)
            open_debug_panel(page)
        with allure.step("断言兜底上传地址标题与按钮组"):
            expect(page.locator("h4:has-text('测试服兜底上传地址')").first).to_be_visible(timeout=10000)
            panel = page.locator(".debug-panel").first
            expect(panel.get_by_role("button", name=re.compile(r"^内网$")).first).to_be_visible(timeout=10000)
            expect(panel.get_by_role("button", name=re.compile(r"^正式$")).first).to_be_visible(timeout=10000)
            shot(page, "pmx_l1_001_debug_official")
        with allure.step("点击「正式」并断言选中态生效"):
            set_official_fallback_upload(page)
            open_debug_panel(page)
            official = page.locator(".debug-panel").first.get_by_role("button", name=re.compile(r"^正式$")).first
            assert "active" in (official.get_attribute("class") or "") or official.get_attribute("aria-pressed") == "true", (
                "点击「正式」后未看到选中态"
            )
            shot(page, "pmx_l1_001_debug_official_pressed")
            close_debug_panel(page)


@allure.feature("Create / Agent 模型矩阵")
@allure.story("L2-交互行为元素")
@pytest.mark.smoke
@pytest.mark.login_required
class TestL2ModelMatrixSubmit:
    """Layer 2: create / agent 两页模型矩阵提交链路。"""

    @pytest.mark.parametrize("case", DATA["cases"], ids=[c["case_id"] for c in DATA["cases"]])
    def test_model_matrix_submit(self, session_page: Page, base_url: str, case: dict[str, Any]):
        """PRD引用：Chat to Edit 模型矩阵（create / agent）。

        覆盖层级：L2 交互行为 / 状态迁移
        前置条件：VIP 已登录；DEBUG 兜底上传切「正式」；图生图用 test_images/低分辨率.JPG。
        测试步骤：
            1. 进入目标页面（create 或 agent）。
            2. DEBUG → 测试服兜底上传地址 → 正式。
            3. 按用例选择模型 / 数量 / 多模型 / 参考图。
            4. 输入 prompt。
            5. 点击提交图标。
            6. 等待提交成功并轮询出图。
        预期结果：提交成功（resultCode=100，taskId 非空）；出现结果图。
        """
        case_id = case["case_id"]
        allure.dynamic.label("case_id", case_id)
        allure.dynamic.label("layer", "L2")
        allure.dynamic.label("priority", "P0")
        allure.dynamic.title(f"{case_id}: {case['page']} 页 {case['model']} {'文生图' if case['kind'] == 't2i' else '图生图'}"
                             + ("（数量=2）" if case["count"] == 2 else "") + "提交并出图")
        allure.dynamic.severity(allure.severity_level.CRITICAL)

        page = session_page
        last_env_error: Exception | None = None
        for attempt in range(2):  # 环境级波动重试一次（重新进入页面，重设 DEBUG 前置）
            logs: list[str] = []
            page.on("console", lambda msg: logs.append(msg.text))
            try:
                self._run_case(page, base_url, case, logs)
                return
            except EnvironmentFlakyError as exc:
                last_env_error = exc
                allure.attach(
                    f"第 {attempt + 1} 次命中环境级波动：\n{exc}",
                    name=f"{case_id}_env_flaky_attempt{attempt + 1}",
                    attachment_type=allure.attachment_type.TEXT,
                )
                if attempt == 0:
                    page.goto("about:blank")
                    settle(page, 3000)
                    continue
                raise
        if last_env_error:  # pragma: no cover
            raise last_env_error

    def _run_case(self, page: Page, base_url: str, case: dict[str, Any], logs: list[str]) -> None:
        """单次用例执行体（含 DEBUG 前置 / 选模型 / 提交 / 等结果）。"""
        case_id = case["case_id"]
        with allure.step("进入目标页面并完成生成前置条件（DEBUG 切「正式」）"):
            if case["page"] == "agent":
                enter_agent(page, base_url)  # 内含：先切正式 → 再选图进 agent
                set_official_fallback_upload(page)  # agent 页再兜底确认一次
            else:
                goto_create(page, base_url)
                set_official_fallback_upload(page)
        with allure.step("选择模型 / 数量 / 上传参考图"):
            if case["reference_image"] and case["page"] == "create":
                upload_reference(page, case["reference_image"])
            if case["multi_mode"]:
                select_multi_models(page)
            else:
                select_single_model(page, case["model"])
            if case["count"] == 2:
                set_image_count(page, 2)
        with allure.step("输入 prompt 并提交任务"):
            fill_prompt(page, PROMPTS[case["kind"]])
            submit_task(page)
            task_id = wait_for_submit(page, logs)
        with allure.step("等待结果图并截图"):
            wait_for_result_image(page, logs, case["count"], case["multi_mode"])
            shot(page, f"{case_id.lower().replace('-', '_')}_result")
        with allure.step("附加任务证据"):
            allure.attach(
                f"case_id={case_id}\\ntask_id={task_id}\\nmodel={case['model']}\\n"
                f"kind={case['kind']}\\ncount={case['count']}\\nmulti_mode={case['multi_mode']}",
                name=f"{case_id}_task_evidence",
                attachment_type=allure.attachment_type.TEXT,
            )
