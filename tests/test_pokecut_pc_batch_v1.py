"""Pokecut PC 批量编辑页自动化测试（2026-11-03 改版重基线）。

PRD引用：用户确认的改版口径 + confirmed sync.md（2026-11-03_pc_batch_v1_reexploration）
覆盖层级：L1 / L2
前置条件：落地页匿名可访问；上传进入画布需 VIP 账号（session_page）
改版口径：/batch 上传 >=2 张图片后进入 /agent?pid=* 并自动展开 Batch Edit 弹窗；
         旧 /batch-edit/edit 已废弃并重定向到 /agent。
"""

import re
from pathlib import Path

import allure
import pytest
import yaml
from playwright.sync_api import expect

from helpers.waiting import wait_visible, settle


def _repo_root() -> Path:
    """逐级上溯到含 data/pokecut_pc_batch_v1.yaml 的仓库根。

    兼容 tests/ 与 archive/<模块>/ 两种存放位置（见 AGENTS.md / rule.md 的归档副本规则）。
    """
    for c in Path(__file__).resolve().parents:
        if (c / "data" / "pokecut_pc_batch_v1.yaml").is_file():
            return c
    return Path(__file__).resolve().parents[1]


ROOT = _repo_root()
with open(ROOT / "data" / "pokecut_pc_batch_v1.yaml", "r", encoding="utf-8") as f:
    DATA = yaml.safe_load(f)

FEATURE = "PC批量编辑页"


# ────────────────────────────── 公共 helper ──────────────────────────────

def wait_render(page, timeout=2000):
    """等待页面渲染完成后再截图或断言。"""
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        pass
    settle(page, 500)


def attach(page, name):
    """等待渲染完成并附加当前视口截图（文件附件，便于 Allure 展开）。"""
    import tempfile
    wait_render(page)
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        path = f.name
    page.screenshot(path=path, full_page=False)
    allure.attach.file(path, name=name, attachment_type=allure.attachment_type.PNG)


def api_bypass_handler(route):
    """拦截 pokecut gateway API，绕过内网 origin 的 CORS 限制。"""
    req = route.request
    if req.method == "OPTIONS":
        route.fulfill(
            status=204,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            },
        )
        return
    try:
        resp = route.fetch()
        headers = dict(resp.headers)
        headers["Access-Control-Allow-Origin"] = "*"
        headers["Access-Control-Allow-Headers"] = "*"
        headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        route.fulfill(response=resp, headers=headers)
    except Exception:
        route.abort()


def goto_batch(page, base_url):
    with allure.step("导航到批量编辑页 /batch"):
        page.route("**/gateway/pokecut/api/**", api_bypass_handler)
        page.goto(f"{base_url}/batch", timeout=60000)
        wait_render(page)


def upload_via_button(page, files):
    """通过主 Upload Images 按钮上传指定文件。"""
    with page.expect_file_chooser(timeout=15000) as fc:
        page.get_by_role("button", name=DATA["landing"]["upload_button"]).click()
    fc.value.set_files(files)


def upload_via_card(page, card_text, files):
    """通过 Try Now 卡片上传指定文件。"""
    with page.expect_file_chooser(timeout=15000) as fc:
        page.get_by_text(card_text, exact=True).first.click()
    fc.value.set_files(files)


def wait_for_agent(page):
    """等待进入 /agent 且 Batch Edit 弹窗可见。"""
    expect(page).to_have_url(re.compile(r"/agent\?pid="), timeout=60000)
    dialog = page.locator("[role=dialog]").filter(
        has=page.get_by_role("heading", name=DATA["agent"]["batch_edit_title"], exact=True)
    ).first
    expect(dialog).to_be_visible(timeout=30000)
    return dialog


def selected_tab_text(page):
    """读取当前 Batch Edit 选中的 tab 文案。"""
    sel = page.locator("[role=tab][aria-selected=true]").first
    expect(sel).to_be_visible(timeout=15000)
    return (sel.inner_text() or "").strip()


# ────────────────────────────── 登录 fixture（覆盖 conftest 的 session_page） ──────────────────────────────

@pytest.fixture(scope="session")
def batch_session_context(browser, base_url):
    """创建批量编辑页专用登录上下文；登录请求经 API bypass 处理 CORS。"""
    context = browser.new_context(
        viewport={"width": 1920, "height": 1080},
        locale="en-US",
    )
    page = context.new_page()
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    page.goto(base_url, timeout=60000)
    wait_render(page)
    page.get_by_text("Log in", exact=True).first.click()
    # 可观察就绪条件：登录弹窗的邮箱输入框出现
    wait_visible(page, page.locator('input[type="email"]'), timeout=10000)
    page.locator('input[type="email"]').fill(DATA["account"]["email"])
    page.locator('input[placeholder="Verification Code"]').fill(DATA["account"]["code"])
    page.evaluate(
        """() => {
            const bs = Array.from(document.querySelectorAll('button'))
                .filter(b => b.offsetWidth > 200 && b.getBoundingClientRect().y > 700 &&
                b.textContent.trim() === 'Log in');
            if (bs.length) bs[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }"""
    )
    # 可观察就绪条件：登录完成由下方 expect 等待，无需前置固定 15s
    expect(page.get_by_text("User8JY", exact=True).first).to_be_visible(timeout=30000)
    page.close()
    yield context
    context.close()


@pytest.fixture
def session_page(batch_session_context):
    """为每个用例创建已登录页面，并继续拦截 gateway API 的 CORS。"""
    page = batch_session_context.new_page()
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    yield page
    page.close()


# ────────────────────────────── L1 结构 ──────────────────────────────

@pytest.mark.regression
@allure.feature(FEATURE)
@allure.story("L1-页面结构元素")
class TestL1BatchStructure:
    """Layer 1: PC 批量编辑页页面结构（改版后）"""

    @pytest.mark.no_login
    @allure.title("L1-001: 落地页主上传入口与 7 个 Try Now 卡片可见")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l1_001_landing_structure(self, page, base_url):
        """PRD引用：AC-001/002；覆盖层级：L1；前置条件：匿名访问。

        测试步骤：
        1. 访问 /batch
        2. 检查主按钮与 7 个卡片文案

        预期结果：Upload Images 可见；7 个 Try Now 卡片文案逐一可见。
        """
        goto_batch(page, base_url)
        with allure.step("断言主上传按钮与 7 个 Try Now 卡片可见"):
            expect(page.get_by_role("button", name=DATA["landing"]["upload_button"])).to_be_visible()
            for card in DATA["landing"]["cards"].values():
                expect(page.get_by_text(card, exact=True).first).to_be_visible()
            attach(page, "落地页_主按钮与7个卡片")


# ────────────────────────────── L2 交互 ──────────────────────────────

@pytest.mark.full
@allure.feature(FEATURE)
@allure.story("L2-交互行为与状态迁移")
class TestL2BatchInteractions:
    """Layer 2: PC 批量编辑页交互（改版后）"""

    @pytest.mark.login_required
    @allure.title("L2-001: 主按钮上传 2 图进入 agent 并默认展开 Batch Edit（Remove BG）")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_001_main_upload_enters_agent_remove_bg(self, session_page, base_url):
        """PRD引用：AC-001；覆盖层级：L2；前置条件：VIP 登录。

        测试步骤：
        1. 访问 /batch 并点击 Upload Images
        2. 选择 test_images/1K.jpg 与 test_images/4K.jpg
        3. 检查进入 /agent 并展开 Batch Edit 弹窗
        4. 检查默认选中 tab

        预期结果：URL 匹配 /agent?pid=；Batch Edit 弹窗可见；选中 tab = Remove BG。
        """
        goto_batch(session_page, base_url)
        with allure.step("点击 Upload Images 并选择 2 张测试图片"):
            upload_via_button(session_page, DATA["images"]["agent_upload"])
        dialog = wait_for_agent(session_page)
        with allure.step("断言 Batch Edit 弹窗与默认选中 tab"):
            expect(dialog).to_be_visible()
            actual = selected_tab_text(session_page)
            assert actual == DATA["agent"]["default_tab_for_upload_button"], \
                f"默认 tab 应为 {DATA['agent']['default_tab_for_upload_button']}，实际 {actual}"
            attach(session_page, "主按钮上传_agent默认RemoveBG")

    @pytest.mark.login_required
    @pytest.mark.parametrize(
        "case_id,card_key,expected_tab",
        [
            ("P-BATCH-L2-003-01", "remove_bg", "Remove BG"),
            ("P-BATCH-L2-003-02", "resizer", "Crop"),
            ("P-BATCH-L2-003-03", "change_bg", "Change BG"),
            ("P-BATCH-L2-003-04", "enhancer", "Enhance"),
            ("P-BATCH-L2-003-05", "erase", "Erase"),
            ("P-BATCH-L2-003-06", "change_clothes", "Clothes Changer"),
            ("P-BATCH-L2-003-07", "watermark", "Watermark"),
        ],
        ids=lambda v: v,
    )
    @allure.title("L2-003: 功能卡片进入 agent 后展开对应 Batch Edit tab [{expected_tab}]")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_l2_003_card_enters_agent_tab(self, session_page, base_url, case_id, card_key, expected_tab):
        """PRD引用：AC-002；覆盖层级：L2；前置条件：VIP 登录。

        测试步骤：
        1. 访问 /batch 并点击指定 Try Now 卡片
        2. 选择 2 张测试图片
        3. 检查进入 /agent 并展开 Batch Edit 弹窗
        4. 断言选中 tab 与卡片功能一致

        预期结果：不同卡片进入 agent 后分别展开对应功能 tab。
        """
        card_text = DATA["landing"]["cards"][card_key]
        goto_batch(session_page, base_url)
        with allure.step(f"点击 {card_text} 卡片并选择 2 张测试图片"):
            upload_via_card(session_page, card_text, DATA["images"]["agent_upload"])
        dialog = wait_for_agent(session_page)
        with allure.step(f"断言 Batch Edit 选中 tab = {expected_tab}"):
            expect(dialog).to_be_visible()
            actual = selected_tab_text(session_page)
            mapped = DATA["agent"]["card_tab_map"].get(card_text)
            assert mapped == expected_tab, f"数据映射不一致：{card_text} -> {mapped} / {expected_tab}"
            assert actual == expected_tab, f"{card_text} 应选中 {expected_tab}，实际 {actual}"
            attach(session_page, f"卡片_{card_key}_agent_{expected_tab.replace(' ', '_')}")

    @pytest.mark.login_required
    @allure.title("L2-013: 单张上传停留 /batch（<2 张不进入 agent）")
    @allure.severity(allure.severity_level.NORMAL)
    def test_l2_013_single_upload_stays_on_batch(self, session_page, base_url):
        """PRD引用：AC-001；覆盖层级：L2；前置条件：VIP 登录。

        测试步骤：
        1. 访问 /batch 并点击 Upload Images
        2. 仅选择 1 张图片
        3. 有界等待后确认未发生跳转（预期"不跳转"，无可观察正向信号）

        预期结果：URL 仍为 /batch，未跳转 /agent。
        """
        goto_batch(session_page, base_url)
        with allure.step("点击 Upload Images 并仅选择 1 张图片"):
            upload_via_button(session_page, DATA["images"]["single"])
            # 无可观察正向信号（预期就是"不跳转"）：有界 settle 后断言 URL
            settle(session_page, 3000)
        with allure.step("断言仍停留在 /batch"):
            assert "/batch" in session_page.url and "/agent" not in session_page.url, \
                f"单张上传应停留 /batch，实际 {session_page.url}"
            attach(session_page, "单张上传_停留batch")
