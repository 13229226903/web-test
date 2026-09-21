# -*- coding: utf-8 -*-
"""Create 页 Chat to Edit / Auto 意图识别自动化测试。

基于 confirmed cases.md（11 条）与 page_map/pokecut/create_chat_to_edit_auto_v1.yaml。
环境：测试服 /create，PC 1920x1080，en-US，会员 450832596@qq.com；素材仅 test_images/。
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
from helpers_create_entry import dismiss_create_promo
from playwright.sync_api import Page, expect

def _repo_root() -> Path:
    """逐级上溯仓库根，兼容 tests/ 与 archive/<module>/ 两种位置。"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pytest.ini").exists() or (parent / ".git").exists():
            return parent
    return current.parents[1]


ROOT = _repo_root()
DATA_PATH = ROOT / "data" / "pokecut_create_chat_to_edit_auto_v1.yaml"
DATA = yaml.safe_load(DATA_PATH.read_text(encoding="utf-8"))
TASK_ID = "2026-09-17_create_auto_intent_recognition"
TASK_DIR = ROOT / "artifacts" / TASK_ID
SHOT_DIR = TASK_DIR / "shots"
SHOT_DIR.mkdir(parents=True, exist_ok=True)


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
    """进入 /create 并处理促销弹窗。"""
    page.goto(base_url.rstrip("/") + DATA["entry_path"], wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(DATA["waits"]["page_load_ms"])
    dismiss_create_promo(page)
    page.wait_for_timeout(500)


def select_auto_model(page: Page) -> None:
    """选择 Auto 模型。"""
    page.locator("div[title='Model']").click(timeout=20000)
    page.wait_for_timeout(800)
    auto = page.locator("div.cursor-pointer:has(img[src*='model_icon_auto.svg'])").first
    expect(auto).to_be_visible(timeout=10000)
    auto.click(timeout=20000)
    page.wait_for_timeout(800)
    expect(page.locator("div[title='Model']")).to_contain_text("Auto", timeout=10000)


def upload_reference(page: Page) -> None:
    """上传指定参考图。"""
    upload = page.locator("div[title='Upload reference images']").first
    expect(upload).to_be_visible(timeout=10000)
    with page.expect_file_chooser(timeout=30000) as chooser_info:
        upload.click(timeout=20000)
    image_path = ROOT / DATA["reference_image"]
    chooser_info.value.set_files(str(image_path))
    page.wait_for_timeout(DATA["waits"]["action_settle_ms"])


def fill_prompt(page: Page, prompt: str) -> None:
    """填写 Chat to Edit prompt。"""
    prompt_box = page.locator("textarea[placeholder='What do you want to design today?']").first
    expect(prompt_box).to_be_visible(timeout=10000)
    prompt_box.fill(prompt)
    page.wait_for_timeout(500)


def submit_task(page: Page) -> None:
    """提交任务并等待跳转画布。"""
    submit = page.locator("div.cursor-pointer:has(img[src*='create_chat_send_btn.svg'])").first
    expect(submit).to_be_visible(timeout=10000)
    submit.click(timeout=20000)
    page.wait_for_url(re.compile(r"/agent\?pid="), timeout=DATA["waits"]["submit_timeout_ms"])
    page.wait_for_timeout(1500)


def extract_evidence(logs: list[str]) -> dict[str, Any]:
    """从 console 日志提取 taskId / styleId。"""
    text = "\n".join(logs)
    task_match = re.search(r"taskId:\s*[\"']?([A-Za-z0-9_\-]+)", text)
    if not task_match:
        task_match = re.search(r"轮询结果\s+([A-Za-z0-9_\-]+)", text)
    route_match = re.search(r"responseCapabilityId:\s*([A-Za-z0-9_\-]+)", text)
    style_match = re.search(r"styleId:\s*[\"']?([A-Za-z0-9_\-]+)", text)
    return {
        "task_id": task_match.group(1) if task_match else None,
        "style_id": route_match.group(1) if route_match else (style_match.group(1) if style_match else None),
        "raw": text,
    }


def wait_for_task_evidence(page: Page, logs: list[str], expected_style_id: str | None) -> dict[str, Any]:
    """等待 taskId / styleId 证据出现。"""
    deadline = time.time() + DATA["waits"]["result_timeout_ms"] / 1000
    last: dict[str, Any] = {}
    while time.time() < deadline:
        last = extract_evidence(logs)
        if last["task_id"] and (expected_style_id is None or last["style_id"] == expected_style_id):
            return last
        if any(marker in last["raw"] for marker in ["task fail", "AutoCanvasSuccess hasError: true", "gpuErrorCode:"]):
            break
        page.wait_for_timeout(DATA["waits"]["poll_interval_ms"])
    assert last.get("task_id"), f"未捕获 taskId: {last.get('raw', '')[-2000:]}"
    if expected_style_id:
        assert last.get("style_id") == expected_style_id, (
            f"styleId 不符: expected={expected_style_id}, actual={last.get('style_id')}"
        )
    return last


def wait_for_resolution(page: Page, width: int, height: int) -> None:
    """等待画布结果分辨率文本出现。"""
    expected = f"{width} x {height}"
    deadline = time.time() + DATA["waits"]["result_timeout_ms"] / 1000
    last_text = ""
    while time.time() < deadline:
        last_text = page.locator("body").inner_text(timeout=10000)
        if expected in last_text:
            return
        page.wait_for_timeout(DATA["waits"]["poll_interval_ms"])
    raise AssertionError(f"未在超时内看到结果分辨率 {expected}; body={last_text[-1200:]}")


@allure.feature("Create Chat to Edit Auto")
@allure.story("L1-页面结构元素")
@pytest.mark.regression
@pytest.mark.login_required
class TestL1CreateChatToEditAutoStructure:
    """Layer 1: Create / Chat to Edit 页面结构与默认态。"""

    @case_meta("L1-001", "L1", "P0")
    @allure.title("L1-001: Create 页 Chat to Edit 结构与默认态")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_chat_to_edit_structure(self, session_page: Page, base_url: str):
        """PRD引用：Create / Chat to Edit / Auto 意图识别。

        覆盖层级：L1 页面元素 / 结构
        前置条件：会员账号已登录；测试服可访问。
        测试步骤：
            1. 进入 /create。
            2. 等待 Chat to Edit 标题可见。
            3. 断言 prompt 输入框、上传按钮、Model、Setting 可见；提交图标为状态依赖元素，由 L6 覆盖。
            4. 断言默认模型为 Nano Banana 2 Lite，字数为 0/3000。
        预期结果：默认态核心元素完整可见；默认模型与字数正确；提交图标按 page_map 仅在 prompt+图片后出现。
        """
        page = session_page
        with allure.step("进入 /create 并关闭促销弹窗"):
            goto_create(page, base_url)
        with allure.step("断言 Chat to Edit 核心结构"):
            expect(page.get_by_role("heading", name="Chat to Edit")).to_be_visible(timeout=15000)
            expect(page.locator("textarea[placeholder='What do you want to design today?']")).to_be_visible(timeout=10000)
            expect(page.locator("div[title='Upload reference images']")).to_be_visible(timeout=10000)
            expect(page.locator("div[title='Model']")).to_be_visible(timeout=10000)
            expect(page.locator("div[title='Setting']")).to_be_visible(timeout=10000)
            expect(page.locator("div[title='Model']")).to_contain_text("Nano Banana 2 Lite", timeout=10000)
            expect(page.get_by_text("0/3000", exact=True)).to_be_visible(timeout=10000)
        with allure.step("截图记录页面结构"):
            shot(page, "L1-001_create_structure")


@allure.feature("Create Chat to Edit Auto")
@allure.story("L6-核心Happy Path")
@pytest.mark.smoke
@pytest.mark.login_required
class TestL6CreateChatToEditAutoHappyPath:
    """Layer 6: Create / Chat to Edit / Auto 十条核心生成链路。"""

    @pytest.mark.parametrize(
        "case",
        DATA["cases"],
        ids=[item["case_id"] for item in DATA["cases"]],
    )
    def test_auto_intent_prompt(self, session_page: Page, base_url: str, case: dict[str, Any]):
        """PRD引用：Create / Chat to Edit / Auto 意图识别。

        覆盖层级：L6 核心 Happy Path / E2E
        前置条件：会员账号已登录；使用 test_images/1K.jpg；测试服可访问。
        测试步骤：
            1. 进入 /create。
            2. 上传 1K.jpg。
            3. 选择 Auto 模型。
            4. 输入指定 prompt。
            5. 提交任务并等待跳转 /agent?pid=...。
            6. 等待 taskId / styleId / 结果分辨率。
            7. 截图记录结果。
        预期结果：taskId 非空；styleId 与预期一致；除“背景换成沙滩”外，结果分辨率与预期一致。
        """
        case_id = case["case_id"]
        prompt = case["prompt"]
        expected_style_id = case.get("expected_style_id") or None
        expected_resolution = case.get("expected_resolution") or None
        allure.dynamic.label("case_id", case_id)
        allure.dynamic.label("layer", "L6")
        allure.dynamic.label("priority", "P0")
        allure.dynamic.title(f"{case_id}: {prompt} Auto 意图识别")
        allure.dynamic.severity(allure.severity_level.CRITICAL)

        page = session_page
        logs: list[str] = []
        page.on("console", lambda msg: logs.append(msg.text))

        with allure.step("进入 /create 并准备 Chat to Edit"):
            goto_create(page, base_url)
        with allure.step("上传参考图并选择 Auto 模型"):
            upload_reference(page)
            select_auto_model(page)
        with allure.step(f"输入 prompt：{prompt}"):
            fill_prompt(page, prompt)
        with allure.step("提交任务并等待跳转画布"):
            submit_task(page)
        with allure.step("等待 taskId / styleId / 结果"):
            evidence = wait_for_task_evidence(page, logs, expected_style_id)
            if expected_resolution:
                wait_for_resolution(page, expected_resolution["width"], expected_resolution["height"])
        with allure.step("截图记录结果"):
            shot(page, f"{case_id}_{prompt}_result")
        with allure.step("附加任务证据"):
            allure.attach(
                str(evidence),
                name=f"{case_id}_task_evidence",
                attachment_type=allure.attachment_type.TEXT,
            )
