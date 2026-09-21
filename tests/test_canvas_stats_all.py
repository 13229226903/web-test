# -*- coding: utf-8 -*-
"""画布统计正常路径用例（Allure 顶层仅 PC端 / 移动端 两大类）。

数据源：data/pokecut_canvas_stats_v1.yaml
用例源：artifacts/2026-09-17_mobile_canvas_stats_first10/cases.md

统计断言口径：单次目标动作内，目标事件的 sendGaEvent 与 debug 统计都恰好 1 次。
已知 bug 用例保留需求期望断言，并用 xfail(strict=True) 标记。
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import datetime
from pathlib import Path

import allure
import pytest
import yaml

def _repo_root() -> Path:
    """解析仓库根：live(tests/) 与 archive(<module>/) 副本都能定位到仓库根。

    归档副本位于 archive/<module>/ 下，parents[1] 会落在 archive/，
    因此改为逐级上溯，寻找同时含 data/ 与 test_images/ 的目录。
    """
    here = Path(__file__).resolve()
    for candidate in (here.parent, *here.parents):
        if (candidate / "data").is_dir() and (candidate / "test_images").is_dir():
            return candidate
    return here.parents[1]


ROOT = _repo_root()
DATA_FILE = ROOT / "data" / "pokecut_canvas_stats_v1.yaml"
IMAGE = ROOT / "test_images" / "1K.jpg"
CFG = yaml.safe_load(DATA_FILE.read_text(encoding="utf-8"))
CASES = CFG["cases"]
CODE = str(CFG["code"])
ZERO_CREDIT_EMAIL = os.environ.get("POKECUT_ZERO_CREDIT_EMAIL", "autotest202609171333@qq.com")

_SEND_RE = re.compile(r"sendGaEvent\s+(\S+)")
_DEBUG_RE = re.compile(r"统计[：:]\s*(\S+)")


# ─────────────────────────── 统计录制与断言 ───────────────────────────

class StatsRecorder:
    def __init__(self, page):
        self.send: list[str] = []
        self.debug: list[str] = []
        page.on("console", self._on_console)

    def _on_console(self, msg):
        text = msg.text or ""
        m = _SEND_RE.search(text)
        if m:
            self.send.append(m.group(1))
        m = _DEBUG_RE.search(text)
        if m:
            self.debug.append(m.group(1))

    def send_count(self, event: str) -> int:
        return sum(1 for item in self.send if item == event)

    def debug_count(self, event: str) -> int:
        return sum(1 for item in self.debug if item == event)


def wait_for_event(rec: StatsRecorder, event: str, timeout: float = 25.0, interval: float = 0.5) -> bool:
    """等待目标事件成对出现（异步上报，避免误判漏报）。"""
    import time

    deadline = time.time() + timeout
    while time.time() < deadline:
        if rec.send_count(event) >= 1 and rec.debug_count(event) >= 1:
            return True
        time.sleep(interval)
    return False


def assert_event_pair(rec: StatsRecorder, event: str, timeout: float = 25.0) -> None:
    wait_for_event(rec, event, timeout=timeout)
    send = rec.send_count(event)
    debug = rec.debug_count(event)
    with allure.step(f"断言统计事件「{event}」sendGaEvent=1 / debug 统计=1（实际 {send}/{debug}）"):
        allure.attach(
            "\n".join(f"sendGaEvent {e}" for e in rec.send) or "(无 sendGaEvent)",
            name=f"Console sendGaEvent 记录 - {event}",
            attachment_type=allure.attachment_type.TEXT,
        )
        recent = " | ".join(rec.send[-12:]) or "(无)"
        assert send == 1, (
            f"「{event}」sendGaEvent 次数应为 1，实际 {send}（0=漏报，>=2=多报）；"
            f"最近 sendGaEvent: {recent}"
        )
        assert debug == 1, (
            f"「{event}」debug 统计次数应为 1，实际 {debug}（0=漏报，>=2=多报）；"
            f"最近 sendGaEvent: {recent}"
        )


def attach_shot(page, name: str) -> Path:
    shot_dir = ROOT / "data" / "screenshots"
    shot_dir.mkdir(parents=True, exist_ok=True)
    path = shot_dir / name
    try:
        page.screenshot(path=str(path), full_page=False)
        allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    except Exception:
        pass
    return path


# ─────────────────────────── 通用交互 helper ───────────────────────────

def fresh_email() -> str:
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"autotest{stamp}{uuid.uuid4().hex[:4]}@qq.com"


def safe_goto(page, url: str, timeout: int = 90000) -> None:
    try:
        page.goto(url, timeout=timeout, wait_until="domcontentloaded")
    except Exception:
        pass
    page.wait_for_timeout(2500)


def click_text(page, text: str, timeout: int = 15000, last: bool = False) -> bool:
    pattern = re.compile(rf"^{re.escape(text)}$", re.I)
    for loc in (
        page.get_by_role("button", name=pattern),
        page.get_by_role("listitem", name=pattern),
        page.get_by_text(text, exact=True),
    ):
        try:
            target = loc.last if last else loc.first
            target.wait_for(state="visible", timeout=timeout)
            target.click(timeout=timeout)
            return True
        except Exception:
            continue
    try:
        handle = page.locator("button, [role=button], li, span, p").filter(
            has_text=re.compile(re.escape(text), re.I)
        )
        target = handle.last if last else handle.first
        target.wait_for(state="visible", timeout=timeout)
        box = target.bounding_box()
        if box:
            page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
            return True
    except Exception:
        pass
    try:
        page.evaluate(
            """(text) => {
                const norm = (v) => (v || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                const target = norm(text);
                for (const el of document.querySelectorAll('button, [role=button], li, span, p, a')) {
                    if (norm(el.textContent) === target && el.offsetWidth > 0 && el.offsetHeight > 0) {
                        el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        return true;
                    }
                }
                return false;
            }""",
            text,
        )
        return True
    except Exception:
        return False


def upload_on_page(page, timeout: int = 15000) -> bool:
    # SEO 首屏上传必须走真实按钮，保留 picenhance/aiReplace/aiextend 工具上下文。
    try:
        seo_btn = page.locator("button.seo-first-screen-upload-button").first
        if seo_btn.count() and seo_btn.is_visible():
            with page.expect_file_chooser(timeout=timeout) as fc:
                seo_btn.click(timeout=timeout)
            fc.value.set_files(str(IMAGE))
            page.wait_for_timeout(3000)
            return True
    except Exception:
        pass
    patterns = [
        re.compile(r"Enhance Photo Quality Now$", re.I),
        re.compile(r"Upload Image$", re.I),
        re.compile(r"Upload Photo", re.I),
        re.compile(r"Start from a Photo", re.I),
        re.compile(r"Choose File", re.I),
        re.compile(r"^Upload$", re.I),
        re.compile(r"Upload reference image", re.I),
    ]
    for pattern in patterns:
        try:
            btn = page.get_by_role("button", name=pattern).first
            btn.wait_for(state="visible", timeout=timeout)
            with page.expect_file_chooser(timeout=timeout) as fc:
                btn.click(timeout=timeout)
            fc.value.set_files(str(IMAGE))
            page.wait_for_timeout(2500)
            return True
        except Exception:
            continue
    # PC /create 的 "Start from a Photo" 是可点击 div，不是 button。
    try:
        target = page.get_by_text("Start from a Photo", exact=True).first
        target.wait_for(state="visible", timeout=timeout)
        with page.expect_file_chooser(timeout=timeout) as fc:
            target.click(timeout=timeout)
        fc.value.set_files(str(IMAGE))
        page.wait_for_timeout(2500)
        return True
    except Exception:
        pass
    try:
        page.locator("input[type=file]").first.set_input_files(str(IMAGE), timeout=timeout)
        page.wait_for_timeout(2500)
        return True
    except Exception:
        return False


def wait_canvas(page, platform: str, timeout: int = 120000) -> None:
    needle = "/agent?" if platform == "pc" else "/create/edit?"
    try:
        page.wait_for_url(re.compile(re.escape(needle)), timeout=timeout)
    except Exception:
        pass
    try:
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
    except Exception:
        pass
    page.wait_for_timeout(4000)


def register_or_login(page, mobile: bool = False, pro: bool = False, email: str | None = None) -> str:
    if email is None:
        if pro:
            email = os.environ.get("POKECUT_TEST_EMAIL", "450832596@qq.com")
        else:
            email = fresh_email()
    code = os.environ.get("POKECUT_TEST_CODE", CODE) if pro else CODE
    if mobile:
        try:
            email_box = page.get_by_role("textbox", name="Email").first
            if email_box.count() == 0 or not email_box.is_visible():
                page.get_by_role("button", name="Sign up").first.click(timeout=15000)
                page.wait_for_timeout(1500)
            page.get_by_role("textbox", name="Email").fill(email)
            page.get_by_role("textbox", name="Verification Code").fill(code)
            page.wait_for_timeout(900)
            submit = page.locator("[data-testid='auth-submit']").last
            if submit.count():
                submit.click(timeout=15000)
            else:
                page.get_by_role("button", name=re.compile(r"^Sign up$", re.I)).last.click(timeout=15000)
            page.wait_for_timeout(8000)
        except Exception:
            pass
        return email
    try:
        entry = page.get_by_text("Log in", exact=True)
        if entry.count() == 0:
            entry = page.get_by_role("button", name=re.compile(r"Sign up|Log in", re.I))
        entry.first.click(timeout=15000)
        page.wait_for_timeout(1800)
        login_text = page.get_by_text("Log in", exact=True)
        if login_text.count() and (pro or page.get_by_text("Already have an account?").count()):
            try:
                login_text.last.click(timeout=5000)
                page.wait_for_timeout(800)
            except Exception:
                pass
        page.locator('input[type="email"]').first.fill(email)
        page.locator('input[placeholder="Verification Code"]').first.fill(code)
        page.get_by_role("button", name=re.compile(r"Log in|Sign up", re.I)).last.click(timeout=15000)
        page.wait_for_timeout(8000)
    except Exception:
        pass
    return email


def canvas_entry_from_home(page, base: str) -> None:
    safe_goto(page, base + "/en")
    upload_on_page(page)


def _visible_promo_modal(page):
    """返回当前可见的“促销弹窗”（不依赖语言）。

    促销弹窗与内购弹窗共用 .purchase-gift-modal 容器，区别是：
    - 促销弹窗：无套餐卡片 li.purchase-pro-plan__card，含倒计时/VIP 对比
    - 内购弹窗：含套餐卡片 li.purchase-pro-plan__card
    依据 2026-09-21 用户说明：新用户 24h 内促销弹窗会比内购弹窗先弹。
    """
    try:
        modals = page.locator('.purchase-gift-modal:visible')
        for i in range(modals.count()):
            m = modals.nth(i)
            try:
                if m.locator("li.purchase-pro-plan__card").count() == 0:
                    return m
            except Exception:
                continue
    except Exception:
        pass
    return None


def close_promo_modal(page) -> bool:
    """关闭新用户 24h 促销弹窗（语言无关），随后才出现真正的内购弹窗。"""
    modal = _visible_promo_modal(page)
    if modal is None:
        return False
    try:
        close_btn = modal.locator(
            "img[src*='colos_pop_btn_close.svg'], img[src*='nav_btn_pop_close.svg']"
        ).last
        if close_btn.count() == 0:
            return False
        try:
            close_btn.click(timeout=8000)
        except Exception:
            close_btn.click(timeout=8000, force=True)
        # 等促销弹窗消失
        page.wait_for_function(
            """() => !Array.from(document.querySelectorAll('.purchase-gift-modal'))
                .some((m) => m.getBoundingClientRect().height > 0
                            && !m.querySelector('li.purchase-pro-plan__card'))""",
            timeout=15000,
        )
        page.wait_for_timeout(900)
        return True
    except Exception:
        return False


def wait_purchase_modal(page, timeout: int = 45000) -> bool:
    markers = [
        "Get Started for $1 USD",
        "Debug: 跳过真实购买",
        "Premium Plan",
        "购买界面",
    ]
    try:
        page.wait_for_function(
            """(markers) => {
                // 内购弹窗的结构化判定，兼容 pt/it 等本地化文案；
                // 必须排除只有促销内容的弹窗（无套餐卡片）。
                const modals = Array.from(document.querySelectorAll('.purchase-gift-modal'))
                    .filter((m) => m.getBoundingClientRect().height > 0);
                const real = modals.find((m) => m.querySelector('li.purchase-pro-plan__card'));
                if (real) return true;
                const text = document.body.innerText || '';
                return modals.length > 0 && markers.some((m) => text.includes(m));
            }""",
            arg=markers,
            timeout=timeout,
        )
        return True
    except Exception:
        return False


JS_CLICK_EXACT = r"""(text) => {
    const norm = (v) => (v || '').replace(/\s+/g, ' ').trim();
    const target = norm(text).toLowerCase();
    const all = Array.from(document.querySelectorAll('button, [role=button], label, div, span'));
    for (let i = all.length - 1; i >= 0; i--) {
        const el = all[i];
        if (norm(el.textContent).toLowerCase() !== target) continue;
        const style = window.getComputedStyle(el);
        if (style.display === 'none' || style.visibility === 'hidden' || parseFloat(style.opacity || '1') === 0) continue;
        const rect = el.getBoundingClientRect();
        if (rect.width <= 0 || rect.height <= 0) continue;
        el.scrollIntoView({block: 'center', inline: 'center'});
        el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        return true;
    }
    return false;
}"""


def js_click_exact(page, text: str) -> bool:
    try:
        return bool(page.evaluate(JS_CLICK_EXACT, text))
    except Exception:
        return False


def dismiss_auto_purchase_overlay(page) -> None:
    """关闭并移除进入 /create 时自动出现的购买遮罩，避免误走 create 页购买链路。"""
    # 稳定关闭入口来自 page_map：购买弹窗关闭图标
    for sel in (
        ".purchase-gift-modal img[src*='colos_pop_btn_close.svg']",
        ".purchase-gift-modal img[src*='nav_btn_pop_close.svg']",
    ):
        try:
            target = page.locator(sel).last
            if target.count():
                target.click(timeout=5000, force=True)
                page.wait_for_timeout(1200)
        except Exception:
            pass
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(600)
    except Exception:
        pass
    # 只移除购买弹窗节点，不能删除任意大容器，否则会破坏 /create 页面主体。
    try:
        page.evaluate("""() => {
            document.querySelectorAll('.purchase-gift-modal').forEach((el) => el.remove());
        }""")
        page.wait_for_timeout(600)
    except Exception:
        pass


def debug_toggle_state(page) -> bool | None:
    """读取“跳过真实购买”开关状态。"""
    try:
        row = page.locator('div.switch-row:has-text("跳过真实购买")').first
        if row.count() == 0:
            return None
        return bool(row.locator('input[type=checkbox]').first.is_checked())
    except Exception:
        return None


def _debug_panel_visible(page) -> bool:
    try:
        return page.locator('.debug-panel').first.is_visible()
    except Exception:
        return False


def _open_debug_panel(page) -> bool:
    if _debug_panel_visible(page):
        return True
    try:
        btn = page.get_by_role("button", name=re.compile(r"^DEBUG$", re.I)).last
        if btn.count() == 0:
            return False
        try:
            btn.click(timeout=8000)
        except Exception:
            btn.click(timeout=8000, force=True)
        page.locator('.debug-panel').first.wait_for(state='visible', timeout=8000)
        page.wait_for_timeout(600)
        return True
    except Exception:
        return False


def _close_debug_panel(page) -> None:
    """关闭 Debug 面板：优先点面板内稳定的 .close-btn（移动端/PC 通用）。"""
    for _ in range(3):
        try:
            panel = page.locator('.debug-panel').first
            if panel.count() == 0 or not panel.is_visible():
                return
            close_btn = panel.locator("button.close-btn").first
            if close_btn.count() == 0:
                close_btn = panel.get_by_role("button", name=re.compile(r"^[×x]$", re.I)).first
            if close_btn.count():
                try:
                    close_btn.click(timeout=6000)
                except Exception:
                    close_btn.click(timeout=6000, force=True)
                page.wait_for_timeout(900)
        except Exception:
            page.wait_for_timeout(600)
    # 兜底：DEBUG 浮层再点一次
    try:
        page.evaluate("""() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const btn = btns.find((b) => (b.textContent || '').trim() === 'DEBUG');
            if (btn) btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
        }""")
        page.wait_for_timeout(700)
    except Exception:
        pass


def set_debug_skip_toggle(page, enabled: bool = True) -> bool:
    """开启/关闭 Debug“跳过真实购买”，使用真实 switch 点击并回读状态。"""
    if not _open_debug_panel(page):
        return False
    try:
        row = page.locator('div.switch-row:has-text("跳过真实购买")').first
        row.wait_for(state='attached', timeout=10000)
        row.scroll_into_view_if_needed(timeout=5000)
        checkbox = row.locator('input[type=checkbox]').first
        current = bool(checkbox.is_checked())
        if current != enabled:
            switch = row.locator('label.switch').first
            try:
                switch.click(timeout=8000)
            except Exception:
                switch.click(timeout=8000, force=True)
            page.wait_for_timeout(1000)
        current = bool(checkbox.is_checked())
        return current == enabled
    except Exception:
        return False
    finally:
        _close_debug_panel(page)


def enable_debug_skip(page) -> bool:
    """开启 Debug 面板中的“跳过真实购买（查看统计项用）”。"""
    return set_debug_skip_toggle(page, True)


def click_debug_skip_purchase(page) -> bool:
    """点击 checkout 内的 Debug 跳过真实购买。绝不点击真实付款按钮。"""
    names = re.compile(r"Debug[:：]\s*跳过真实购买")
    try:
        btn = page.get_by_role("button", name=names).first
        btn.wait_for(state="visible", timeout=25000)
        try:
            btn.scroll_into_view_if_needed(timeout=5000)
        except Exception:
            pass
        # 优先真实点击：force=True 可能因遮罩导致坐标落到真实支付按钮上。
        btn.click(timeout=8000)
        page.wait_for_timeout(6000)
        return True
    except Exception:
        pass
    # 真实点击失败时，直接向目标按钮派发 DOM click，避免坐标命中外层支付按钮。
    if js_click_exact(page, "Debug: 跳过真实购买"):
        page.wait_for_timeout(6000)
        return True
    try:
        btn = page.get_by_role("button", name=names).first
        btn.click(timeout=8000, force=True)
        page.wait_for_timeout(6000)
        return True
    except Exception:
        return False


def _checkout_markers(page) -> str:
    try:
        body = page.locator("body").inner_text()
    except Exception:
        return ""
    markers = [
        m for m in ("Yearly Plan", "Monthly Plan", "PayPal", "stripe", "Debug: 跳过真实购买")
        if m.lower() in body.lower()
    ]
    return ", ".join(markers) or "(无 checkout 标记)"


def select_purchase_plan(page, plan_name: str | None = None, monthly: bool = False) -> bool:
    """在 Premium Plan 弹窗内选择计费周期和套餐，供明确的统计抽测项使用。"""
    try:
        modal = page.locator('.purchase-gift-modal').first
        if modal.count() == 0:
            return False
        if monthly:
            toggle = modal.locator("img[src*='pro_plan_left.svg']").first
            if toggle.count() and toggle.is_visible():
                toggle.click(timeout=8000)
                page.wait_for_timeout(1200)
        if plan_name:
            card = modal.locator(f"li.purchase-pro-plan__card:has-text('{plan_name}')").first
            if card.count() == 0:
                return False
            card.click(timeout=8000)
            page.wait_for_timeout(1000)
            selected = card.locator("img[src*='purchase_selected_point.svg']").count() > 0
            return selected
        return True
    except Exception:
        return False


def _click_purchase_get_started(page) -> bool:
    # 优先结构化按钮，兼容 pt/it 本地化后的 Get Started 文案。
    for sel in ("button.purchase-pro-plan__button", "[class*='purchase-pro-plan__button']"):
        try:
            btn = page.locator(sel).first
            if btn.count() and btn.is_visible():
                btn.click(timeout=10000)
                page.wait_for_timeout(4500)
                return True
        except Exception:
            continue
    pattern = re.compile(r"Get Started(?: for \$1 USD)?", re.I)
    try:
        btn = page.get_by_role("button", name=pattern).last
        if btn.count() and btn.is_visible():
            btn.click(timeout=10000)
            page.wait_for_timeout(4500)
            return True
    except Exception:
        pass
    for text in ("Get Started", "Get Started for $1 USD", "Get started"):
        if js_click_exact(page, text):
            page.wait_for_timeout(4500)
            return True
    return False


def debug_skip_flow(page, plan_name: str | None = None, monthly: bool = False) -> bool:
    """开启 Debug 跳过开关 → Get Started → 点击 checkout 的 Debug 跳过真实购买。"""
    trace: list[str] = []
    toggled = enable_debug_skip(page)
    trace.append(f"开关开启/回读={toggled}")
    if not toggled:
        allure.attach("\n".join(trace), name="Debug 跳过真实购买执行轨迹", attachment_type=allure.attachment_type.TEXT)
        return False

    # 按用例要求选择抽测套餐（PC 默认 Yearly Ultra；移动 SEO 新画布抽测 Monthly SE）。
    plan_selected = select_purchase_plan(page, plan_name=plan_name, monthly=monthly)
    trace.append(f"套餐选择 plan={plan_name or '默认'}, monthly={monthly}, selected={plan_selected}")

    # 关闭 Debug 面板后必须确认不再遮挡购买弹窗。
    _close_debug_panel(page)
    page.wait_for_timeout(800)
    panel_visible = _debug_panel_visible(page)
    trace.append(f"Debug 面板关闭后仍可见={panel_visible}")

    def debug_button_visible() -> bool:
        try:
            return page.get_by_role("button", name=re.compile(r"Debug[:：]\s*跳过真实购买")).first.is_visible()
        except Exception:
            return False

    # 仅以 checkout 内的 Debug 跳过按钮判断 checkout 是否已打开；
    # PayPal/stripe 图标在内购弹窗内也会出现，不能作为 checkout 判定。
    checkout_already_open = debug_button_visible()
    if checkout_already_open:
        opened = True
        trace.append("checkout 已打开，跳过 Get Started")
    else:
        opened = _click_purchase_get_started(page)
        trace.append(f"Get Started 点击={opened}")
    if not opened:
        trace.append(f"页面状态={_checkout_markers(page)}")
        allure.attach("\n".join(trace), name="Debug 跳过真实购买执行轨迹", attachment_type=allure.attachment_type.TEXT)
        return False

    trace.append(f"checkout 标记={_checkout_markers(page)}")
    if not debug_button_visible():
        page.wait_for_timeout(6000)
        trace.append(f"等待后 checkout Debug 按钮={debug_button_visible()}; 页面状态={_checkout_markers(page)}")

    if not debug_button_visible():
        toggled = set_debug_skip_toggle(page, True)
        trace.append(f"checkout 内重开开关={toggled}")
        if toggled:
            page.wait_for_timeout(3500)
            trace.append(f"重开后 checkout Debug 按钮={debug_button_visible()}")

    ok = click_debug_skip_purchase(page)
    trace.append(f"checkout Debug 跳过购买点击={ok}")
    allure.attach(
        "\n".join(trace),
        name="Debug 跳过真实购买执行轨迹",
        attachment_type=allure.attachment_type.TEXT,
    )
    return ok


def drag_canvas(page) -> None:
    try:
        box = page.locator("canvas").first.bounding_box()
        if not box:
            return
        page.mouse.move(box["x"] + box["width"] * 0.35, box["y"] + box["height"] * 0.35)
        page.mouse.down()
        page.mouse.move(box["x"] + box["width"] * 0.65, box["y"] + box["height"] * 0.65, steps=10)
        page.mouse.up()
        page.wait_for_timeout(1500)
    except Exception:
        pass


def paint_mask_cdp(page, strokes: int = 3) -> bool:
    """移动端 AI Delete 蒙版涂抹：在图片区域用 CDP 触摸事件绘制，激活 Remove 提交。

    依据 page_map/pokecut/mobile_canvas_v10.yaml
    states.mobile_canvas_ai_delete_paint_mask_remove（2026-09-21 MCP 复核）。
    仅用鼠标/合成 PointerEvent 无法写入蒙版，必须走 Input.dispatchTouchEvent。
    """
    try:
        client = page.context.new_cdp_session(page)
        box = page.locator("canvas").first.bounding_box()
        if not box:
            return False
        for k in range(strokes):
            y = box["y"] + box["height"] * (0.30 + 0.12 * k)
            x0 = box["x"] + box["width"] * 0.38
            client.send("Input.dispatchTouchEvent", {
                "type": "touchStart",
                "touchPoints": [{"x": x0, "y": y, "id": 1}],
            })
            for i in range(1, 21):
                client.send("Input.dispatchTouchEvent", {
                    "type": "touchMove",
                    "touchPoints": [{"x": x0 + i * 2.6, "y": y + i * 1.2, "id": 1}],
                })
                page.wait_for_timeout(30)
            client.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
            page.wait_for_timeout(800)
        page.wait_for_timeout(2500)
        return True
    except Exception:
        return False


def submit_remove_after_mask(page) -> bool:
    """涂抹蒙版后点击 .mobile-ai-generate-button 提交 Remove。"""
    try:
        btn = page.locator(".mobile-ai-generate-button").first
        btn.wait_for(state="visible", timeout=15000)
        for _ in range(10):
            src = btn.locator("img").first.get_attribute("src") if btn.locator("img").count() else ""
            if src and "cannot_remove" not in src:
                break
            page.wait_for_timeout(1500)
        btn.click(timeout=10000)
        page.wait_for_timeout(4000)
        return True
    except Exception:
        return False


def run_actions(page, actions: list[dict] | None) -> None:
    for action in actions or []:
        if "click" in action:
            click_text(page, action["click"])
            page.wait_for_timeout(2000)
        elif action.get("drag_canvas"):
            drag_canvas(page)
        elif action.get("fill_last_textarea"):
            try:
                page.locator("textarea").last.fill(action["fill_last_textarea"])
            except Exception:
                pass
            page.wait_for_timeout(800)
        elif action.get("fill_first_textarea"):
            try:
                page.locator("textarea").first.fill(action["fill_first_textarea"])
            except Exception:
                pass
            page.wait_for_timeout(800)
        elif action.get("click_vip_sticker"):
            try:
                # 点击贴纸列表中的第一张 VIP 贴纸按钮，避免点到角标文本。
                page.locator("button:has-text('VIP')").first.click(timeout=8000)
            except Exception:
                pass
            page.wait_for_timeout(1800)
        elif action.get("select_all_layers"):
            try:
                layer_btn = page.get_by_role("button", name="Layer").first
                if layer_btn.count():
                    layer_btn.click(timeout=8000)
                    page.wait_for_timeout(1200)
                page.keyboard.press("Control+A")
                page.wait_for_timeout(1500)
            except Exception:
                pass
        elif action.get("paint_mask_cdp"):
            paint_mask_cdp(page)
        elif action.get("click_remove_submit"):
            submit_remove_after_mask(page)
        elif action.get("drag_canvas_select_all"):
            try:
                box = page.locator("canvas").first.bounding_box()
                if box:
                    page.mouse.move(box["x"] + 10, box["y"] + 10)
                    page.mouse.down()
                    page.mouse.move(box["x"] + box["width"] - 10, box["y"] + box["height"] - 10, steps=12)
                    page.mouse.up()
                    page.wait_for_timeout(1200)
            except Exception:
                pass


def close_auth_modal(page) -> bool:
    """关闭移动端注册弹窗：右上角关闭/遮罩顶部点击（依据 2026-09-21 MCP 复核）。"""
    try:
        if page.locator("input[type=email]").count() == 0:
            return False
        # 右上角关闭按钮（部分渲染下无 aria-label，按右上角坐标点击）
        dialog = page.locator("[data-testid='auth-dialog']").first
        box = dialog.bounding_box() if dialog.count() else None
        if box:
            page.mouse.click(box["x"] + box["width"] - 22, box["y"] + 22)
            page.wait_for_timeout(1800)
        if page.locator("input[type=email]").count() == 0:
            return True
        # 兜底：点遮罩顶部空白区域
        page.mouse.click(page.viewport_size["width"] / 2, 8)
        page.wait_for_timeout(1800)
        return page.locator("input[type=email]").count() == 0
    except Exception:
        return False


def close_purchase_modal(page) -> None:
    try:
        close_icon = page.locator(".purchase-gift-modal img[src*='nav_btn_pop_close.svg']").last
        if close_icon.count():
            close_icon.click(timeout=5000, force=True)
            page.wait_for_timeout(1500)
            return
    except Exception:
        pass
    for name in ("Close", "×"):
        try:
            page.get_by_role("button", name=name).last.click(timeout=5000, force=True)
            page.wait_for_timeout(1500)
            return
        except Exception:
            continue


# ─────────────────────────── 业务 flows ───────────────────────────

def flow_skipped_dependency(page, base, case, rec):
    pytest.skip(case.get("skip_reason", "依赖未提供"))


def flow_pc_infinite_register(page, base, case, rec):
    safe_goto(page, base + "/create")
    dismiss_auto_purchase_overlay(page)
    upload_on_page(page)
    wait_canvas(page, "pc")
    click_text(page, "Enhance")
    click_text(page, "Ultra HD Mode")
    click_text(page, "Enhance")
    page.wait_for_timeout(3000)
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][0])
    register_or_login(page, email=ZERO_CREDIT_EMAIL)
    page.wait_for_timeout(6000)
    assert_event_pair(rec, case["expected"][1])


def complete_pc_signup_if_present(page) -> bool:
    """完成画布内邮箱注册弹窗（随机唯一邮箱 + 固定验证码）。"""
    try:
        email_input = page.locator('input[type="email"]').first
        if not email_input.is_visible():
            return False
        email_input.fill(fresh_email())
        page.locator('input[placeholder="Verification Code"]').first.fill(CODE)
        page.get_by_role("button", name=re.compile(r"^Sign up$", re.I)).last.click(timeout=10000)
        page.wait_for_timeout(8000)
        return True
    except Exception:
        return False


def flow_pc_infinite_purchase(page, base, case, rec):
    # 免费 0-credit 账号：/create 上传 -> Enhance/Ultra 提交 -> 功能级购买 -> Debug 跳过成功。
    safe_goto(page, base + "/en")
    register_or_login(page, email=ZERO_CREDIT_EMAIL)
    safe_goto(page, base + "/create")
    page.wait_for_timeout(2500)
    dismiss_auto_purchase_overlay(page)
    assert upload_on_page(page), "PC /create 未找到可用的上传入口"
    wait_canvas(page, "pc")

    ultra = page.get_by_role("button", name=re.compile(r"Ultra HD Mode", re.I)).first
    if ultra.count() == 0 or not ultra.is_visible():
        click_text(page, "Enhance")
        page.wait_for_timeout(2200)
    assert ultra.count() > 0 and ultra.is_visible(), "PC Enhance 面板未显示 Ultra HD Mode"
    ultra.click(timeout=10000)
    page.wait_for_timeout(1200)

    submit = page.locator("button.btn-bg-gradient1:has-text('Enhance')").first
    assert submit.count() > 0 and submit.is_visible(), "PC Enhance 面板未显示主提交按钮"
    submit.click(timeout=10000)
    page.wait_for_timeout(3500)
    assert wait_purchase_modal(page), "未出现无限画布功能级购买弹窗"
    attach_shot(page, case["screenshot"])
    assert debug_skip_flow(page), "未能通过 Debug 跳过真实购买"
    assert_event_pair(rec, case["expected"][0])


def flow_pc_infinite_download(page, base, case, rec):
    # 结果图下载：/create 上传 -> Enhance -> Standard Mode 生成 -> 选中 Enhanced 结果层 -> 下载。
    safe_goto(page, base + "/en")
    register_or_login(page, pro=True)
    safe_goto(page, base + "/create")
    dismiss_auto_purchase_overlay(page)
    assert upload_on_page(page), "PC /create 未找到上传入口"
    wait_canvas(page, "pc")

    # 打开 AI Enhancer 面板并点击面板主提交按钮；先前漏点导致没有生成结果。
    click_text(page, "Enhance")
    page.wait_for_timeout(2200)
    submit = page.locator("button.btn-bg-gradient1:has-text('Enhance')").first
    assert submit.count() > 0 and submit.is_visible(), "AI Enhancer 面板未显示主 Enhance 提交按钮"
    submit.click(timeout=10000)

    # 等待结果图层产生；只有结果图层存在时才进入下载步骤。
    try:
        page.wait_for_function(
            """() => !!document.querySelector("img[alt*='Enhanced']")
                 || (document.body.innerText || '').includes('Enhanced')""",
            timeout=360000,
        )
    except Exception:
        page.wait_for_timeout(30000)

    layer_btn = page.locator("button[aria-label='Layer']").first
    if layer_btn.count() == 0 or not layer_btn.is_visible():
        click_text(page, "Layer")
    else:
        layer_btn.click(timeout=8000)
    page.wait_for_timeout(1500)

    # 选中生成后的 Enhanced 结果图层；不得对原图执行下载。
    result_item = page.locator("img[alt*='Enhanced']").first
    if result_item.count() == 0:
        result_item = page.get_by_text("Enhanced", exact=False).last
    assert result_item.count() > 0, "未找到 Enhanced 结果图层"
    # 结果图 img 自身 pointer-events:none，点击其可交互父容器完成图层选中。
    result_click = result_item.locator("xpath=..").first
    result_click.click(timeout=10000)
    page.wait_for_timeout(1200)

    download_btn = page.locator("button[class*='download-left']").first
    assert download_btn.count() > 0 and download_btn.is_visible(), "未找到结果图下载按钮"
    download_btn.click(timeout=10000)
    page.wait_for_timeout(5000)
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][0])


def click_tool_primary_submit(page) -> bool:
    """点击功能面板的主提交按钮，跳过购买弹窗中的支付类按钮。"""
    forbidden = {"Get Started", "Get Started for $1 USD", "Try Free Trial", "Continue"}
    selectors = (
        # 移动端画布功能面板主提交按钮（Photo Enhancer / Magic Eraser 等）
        "button.mobile-ai-generate-button:visible",
        # 移动端 AI Image Extender 面板主提交按钮
        "button.mobile-ai-expand-generate-button:visible",
        # PC 端画布功能面板主提交按钮
        "button.btn-bg-gradient1:visible",
        "button[class*='submit-gradient']:visible",
        "button[class*='ai-replace'][class*='gradient']:visible",
        "button[class*='gradient']:visible",
    )
    for sel in selectors:
        try:
            btns = page.locator(sel)
            for i in range(btns.count()):
                btn = btns.nth(i)
                label = (btn.inner_text() or "").strip()
                if label in forbidden or not label:
                    continue
                if not btn.is_visible():
                    continue
                btn.click(timeout=10000)
                page.wait_for_timeout(3500)
                return True
        except Exception:
            continue
    return False


def upload_via_create_upload_button(page, timeout: int = 15000) -> bool:
    """点击 SEO 首屏无文案的上传图标按钮，保留 image-to-image 工具上下文。"""
    try:
        btn = page.locator("button:has(img[src*='create_generate_icon_upload_image.svg'])").first
        btn.wait_for(state="visible", timeout=timeout)
        with page.expect_file_chooser(timeout=timeout) as fc:
            btn.click(timeout=timeout)
        fc.value.set_files(str(IMAGE))
        page.wait_for_timeout(3000)
        return True
    except Exception:
        return False


def click_create_go(page, timeout: int = 15000) -> bool:
    """点击 SEO 首屏无文案的 Generate/Go 图标按钮。"""
    try:
        btn = page.locator("button:has(img[src*='create_generate_icon_go.svg'])").first
        btn.wait_for(state="visible", timeout=timeout)
        btn.click(timeout=timeout)
        page.wait_for_timeout(3000)
        return True
    except Exception:
        return False


def flow_seo_new_canvas(page, base, case, rec):
    entry_action = case.get("entry_action", "upload_only")
    safe_goto(page, base + "/en")
    if case["platform"] == "mobile":
        # 移动端新画布购买成功抽测“月SE试用”，必须是未消耗试用资格的新账号。
        register_or_login(page, mobile=True)
    else:
        register_or_login(page, email=ZERO_CREDIT_EMAIL)
    safe_goto(page, base + case["entry"])
    if entry_action == "generate_only":
        assert click_create_go(page), "AI 文生图首屏未找到 Generate 图标按钮"
    elif entry_action == "upload_then_generate":
        assert upload_via_create_upload_button(page), "图生图首屏未找到上传图标按钮"
        page.wait_for_timeout(2500)
        assert click_create_go(page), "图生图首屏未找到 Generate 图标按钮"
    else:
        upload_on_page(page)
    wait_canvas(page, case["platform"])
    run_actions(page, case.get("actions"))
    page.wait_for_timeout(3000)

    # SEO 新画布进入画布后功能面板已自动打开；若尚未弹购买，则点击面板主提交按钮。
    # PC 与移动端的按钮 class 不同（PC: btn-bg-gradient1 / 移动端: mobile-ai-*-generate-button），
    # click_tool_primary_submit 已覆盖两者；依据 page_map v10 与第 4 批失败复核。
    if page.locator(".purchase-gift-modal:visible").count() == 0:
        click_tool_primary_submit(page)
        page.wait_for_timeout(2500)
    # 部分面板需要重试才能稳定提交（移动端面板动画/遮罩未就绪）。
    if page.locator(".purchase-gift-modal:visible").count() == 0:
        page.wait_for_timeout(2000)
        click_tool_primary_submit(page)
        page.wait_for_timeout(2500)

    # SEO 新画布链路可能先弹促销弹窗；先关闭促销弹窗，再等待真正的内购弹窗。
    close_promo_modal(page)
    page.wait_for_timeout(1200)
    assert wait_purchase_modal(page), "未出现购买弹窗，无法断言购买出现统计"
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][0])
    if case["platform"] == "mobile":
        debug_skip_flow(page, plan_name="SE", monthly=True)
    else:
        # PC 新画布统一抽测 Yearly Ultra；避免默认落到 SE / 3-Day Free。
        assert debug_skip_flow(page, plan_name="Ultra"), "PC 新画布未完成 Yearly Ultra Debug 跳过购买"
    attach_shot(page, case["screenshot"].replace(".png", "_after_debug.png"))
    assert_event_pair(rec, case["expected"][1])


def flow_mobile_register_pair(page, base, case, rec):
    canvas_entry_from_home(page, base)
    wait_canvas(page, "mobile")
    click_text(page, "Photo Enhancer")
    click_text(page, "Enhance")
    page.wait_for_timeout(2500)
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][0])
    register_or_login(page, mobile=True)  # 随机新邮箱，触发注册成功统计
    page.wait_for_timeout(6000)
    assert_event_pair(rec, case["expected"][1])


def mobile_feature_register_session(page, base: str, feature: str, rec: StatsRecorder) -> None:
    """单个匿名会话：进入移动画布 -> 某功能 0 credits -> 注册弹窗 -> 随机新账号注册成功。

    注册弹窗由哪个功能打开，就只会产出该功能自己的功能级注册/注册成功事件。
    依据证据 console_credits_register_success.log（画质增强）与
    console_credits_register_extra_features.log（AI扩图）。
    """
    canvas_entry_from_home(page, base)
    wait_canvas(page, "mobile")

    if feature == "enhance":
        click_text(page, "Photo Enhancer")
        page.wait_for_timeout(1500)
        assert click_tool_primary_submit(page), "Photo Enhancer 面板未显示主提交按钮"
    elif feature == "extend":
        extender = page.locator("button.tool-card:has-text('AI Image Extender')").first
        assert extender.count() > 0, "Trending Tools 未找到 AI Image Extender 工具卡"
        extender.click(timeout=10000, force=True)
        page.wait_for_timeout(2500)
        submit = page.locator("button.mobile-ai-expand-generate-button").first
        assert submit.count() > 0, "AI Image Extender 面板未显示主提交按钮"
        submit.click(timeout=10000, force=True)
    else:
        raise ValueError(f"未知功能: {feature}")

    page.wait_for_timeout(3500)
    assert page.locator("input[type=email]").count() > 0, f"{feature} 未出现注册弹窗"


def flow_mobile_purchase_appearance(page, base, case, rec):
    canvas_entry_from_home(page, base)
    register_or_login(page, mobile=True, email=ZERO_CREDIT_EMAIL)
    page.wait_for_timeout(1500)
    click_text(page, "Photo Enhancer")
    click_text(page, "Enhance")
    page.wait_for_timeout(2000)
    assert wait_purchase_modal(page), "未出现购买弹窗"
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][0])

    close_purchase_modal(page)
    page.wait_for_timeout(1800)
    # 关闭功能面板，回到一级工具列表；英文移动画布按钮为 AI Image Extender + AI Extend。
    try:
        page.get_by_role("button", name="Close").last.click(timeout=5000, force=True)
    except Exception:
        pass
    page.wait_for_timeout(1200)
    tab = page.locator("li.mobile-primary-panel__tab:has-text('Trending Tools')").first
    if tab.count():
        tab.click(timeout=8000, force=True)
    page.wait_for_timeout(1800)

    extender = page.locator("button.tool-card:has-text('AI Image Extender')").first
    assert extender.count() > 0, "未回到 Trending Tools 的 AI Image Extender 工具卡"
    ai_extend = page.get_by_role("button", name=re.compile(r"^AI Extend$", re.I)).first
    if ai_extend.count() == 0:
        ai_extend = page.locator("button:has-text('AI Extend')").first
    for _ in range(3):
        if ai_extend.count() > 0:
            break
        extender.click(timeout=10000, force=True)
        # 等待二级面板真正打开，避免点击落在过渡层上。
        try:
            page.wait_for_function(
                """() => Array.from(document.querySelectorAll('button'))
                    .some((el) => (el.textContent || '').trim() === 'AI Extend'
                                 && el.getBoundingClientRect().height > 0)""",
                timeout=12000,
            )
        except Exception:
            pass
        page.wait_for_timeout(1200)
        ai_extend = page.get_by_role("button", name=re.compile(r"^AI Extend$", re.I)).first
        if ai_extend.count() == 0:
            ai_extend = page.locator("button:has-text('AI Extend')").first
    if ai_extend.count() == 0:
        raise AssertionError("AI Image Extender 面板未显示 AI Extend 按钮")
    try:
        ai_extend.scroll_into_view_if_needed(timeout=5000)
    except Exception:
        pass
    ai_extend.click(timeout=10000, force=True)
    page.wait_for_timeout(2500)
    assert wait_purchase_modal(page), "AI 扩图未出现购买弹窗"
    assert_event_pair(rec, case["expected"][1])


def flow_mobile_purchase_success(page, base, case, rec):
    canvas_entry_from_home(page, base)
    register_or_login(page, mobile=True, email=ZERO_CREDIT_EMAIL)
    page.wait_for_timeout(1500)
    click_text(page, "AI Image Extender")
    click_text(page, "AI Extend")
    page.wait_for_timeout(2000)
    assert wait_purchase_modal(page), "未出现购买弹窗"
    debug_skip_flow(page)
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][0])
    assert_event_pair(rec, case["expected"][1])


def flow_mobile_modal_appear(page, base, case, rec):
    canvas_entry_from_home(page, base)
    wait_canvas(page, "mobile")
    click_text(page, "Photo Enhancer")
    page.wait_for_timeout(1500)
    assert_event_pair(rec, case["expected"][0])
    close_purchase_modal(page)
    click_text(page, "Magic Eraser")
    page.wait_for_timeout(2000)
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][1])


def flow_mobile_modal_confirm(page, base, case, rec):
    canvas_entry_from_home(page, base)
    register_or_login(page, mobile=True, pro=True)
    page.wait_for_timeout(1500)
    click_text(page, "Adjust")
    click_text(page, "Filter")
    click_text(page, "Confirm")
    page.wait_for_timeout(2000)
    assert_event_pair(rec, case["expected"][0])
    click_text(page, "Background")
    click_text(page, "Background Remover")
    click_text(page, "Remove Background")
    page.wait_for_timeout(15000)
    click_text(page, "Confirm")
    page.wait_for_timeout(2500)
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][1])


def move_debug_button_away(page) -> bool:
    """把右下角 DEBUG 浮层移开，避免遮挡结果弹窗底部下载按钮。

    依据 2026-09-21 用户反馈 + page_map v10：DEBUG 浮层位于右下角
    (.debug-float-btn，约 330,604)，与结果弹窗底部下载按钮位置重叠。
    """
    try:
        return bool(page.evaluate("""() => {
            // DEBUG 浮层为 position:static，改 left/top 无效，必须改成 fixed 才能移动。
            const btn = document.querySelector('.debug-float-btn');
            if (!btn) return false;
            btn.style.setProperty('position', 'fixed', 'important');
            btn.style.setProperty('left', '4px', 'important');
            btn.style.setProperty('top', '4px', 'important');
            btn.style.setProperty('right', 'auto', 'important');
            btn.style.setProperty('bottom', 'auto', 'important');
            return true;
        }"""))
    except Exception:
        return False


def flow_mobile_popup_download(page, base, case, rec):
    """M-CORE-07 移动端画布页_xx弹窗下载。

    依据 page_map v10 / evidence mobile_stat11_enhance_popup_download_*：
    登录态账号 -> 首页上传进入画布 -> Photo Enhancer 面板 -> 面板主提交按钮生成结果
    -> 结果弹窗底部下载按钮 (pmd_remodver_bg_btn_icon_download.svg) -> 目标统计。
    注意：必须点面板主提交按钮，点画布工具栏 Enhance 不会生成结果。
    """
    canvas_entry_from_home(page, base)
    wait_canvas(page, "mobile")
    register_or_login(page, mobile=True, pro=True)

    # 等登录弹窗关闭，避免登录未完成就操作面板
    for _ in range(20):
        if page.locator("input[type=email]").count() == 0:
            break
        page.wait_for_timeout(1000)
    page.wait_for_timeout(3000)

    # 打开 Photo Enhancer 面板：可能已自动打开，未打开/未稳定时重试点工具卡。
    for _ in range(4):
        if page.locator("button.mobile-ai-generate-button:visible").count():
            break
        card = page.locator("button.tool-card:has-text('Photo Enhancer')").first
        if card.count() == 0:
            break
        try:
            card.click(timeout=8000)
        except Exception:
            card.click(timeout=8000, force=True)
        page.wait_for_timeout(3000)
    assert page.locator("button.mobile-ai-generate-button:visible").count() > 0, \
        "Photo Enhancer 面板未打开（未找到主 Enhance 提交按钮）"
    assert click_tool_primary_submit(page), "Photo Enhancer 面板未显示主 Enhance 提交按钮"

    # 结果弹窗底部下载按钮只在结果图生成后出现；用位置区分画布顶部工具栏同图标下载。
    # 判据：可见的 pmd_remodver_bg_btn_icon_download 且位于视口下半部。
    bottom_download_js = """() => Array.from(
        document.querySelectorAll("img[src*='pmd_remodver_bg_btn_icon_download']")
    ).some((el) => {
        const r = el.getBoundingClientRect();
        return r.width > 0 && r.height > 0 && r.top > window.innerHeight * 0.6;
    })"""
    try:
        page.wait_for_function(bottom_download_js, timeout=360000)
    except Exception:
        pass

    # 底部下载按钮位于右下角，会被 DEBUG 浮层遮挡；先移开 DEBUG。
    move_debug_button_away(page)
    page.wait_for_timeout(1000)

    clicked = False
    for sel in (
        "button:has(img[src*='pmd_remodver_bg_btn_icon_download'])",
        "img[src*='pmd_remodver_bg_btn_icon_download']",
    ):
        try:
            cands = page.locator(sel)
            best, best_y = None, -1.0
            for i in range(cands.count()):
                cand = cands.nth(i)
                try:
                    if not cand.is_visible():
                        continue
                    box = cand.bounding_box()
                    if box and box["y"] > best_y:
                        best, best_y = cand, box["y"]
                except Exception:
                    continue
            if best is None:
                continue
            try:
                best.click(timeout=15000)
            except Exception:
                best.click(timeout=15000, force=True)
            clicked = True
            break
        except Exception:
            continue
    assert clicked, "未找到结果弹窗底部下载按钮"
    page.wait_for_timeout(5000)
    attach_shot(page, case["screenshot"])
    assert_event_pair(rec, case["expected"][0])


FLOWS = {
    "skipped_dependency": flow_skipped_dependency,
    "pc_infinite_register": flow_pc_infinite_register,
    "pc_infinite_purchase": flow_pc_infinite_purchase,
    "pc_infinite_download": flow_pc_infinite_download,
    "seo_new_canvas": flow_seo_new_canvas,
    "mobile_register_pair": flow_mobile_register_pair,
    "mobile_purchase_appearance": flow_mobile_purchase_appearance,
    "mobile_purchase_success": flow_mobile_purchase_success,
    "mobile_modal_appear": flow_mobile_modal_appear,
    "mobile_modal_confirm": flow_mobile_modal_confirm,
    "mobile_popup_download": flow_mobile_popup_download,
}


# ─────────────────────────── pytest 入口 ───────────────────────────

def _run_case(browser, playwright, base_url, case):
    base = base_url.rstrip("/")
    if case["flow"] == "mobile_feature_register":
        # 功能级注册成功事件由打开注册弹窗的功能决定；
        # 注册后即变登录态，无法在同一会话再走一次注册弹窗，因此用两个独立匿名会话。
        for feature, expected_appear, expected_success in (
            ("enhance",
             "移动端画布画质增强ultra功能点数用完触发注册",
             "移动端画布画质增强ultra功能点数用完触发注册成功"),
            ("extend",
             "移动端画布AI扩图功能点数用完触发注册",
             "移动端画布AI扩图功能点数用完触发注册成功"),
        ):
            context = browser.new_context(**playwright.devices["iPhone 13"])
            page = context.new_page()
            try:
                rec = StatsRecorder(page)
                with allure.step(f"匿名会话：{feature} 触发注册并注册成功"):
                    mobile_feature_register_session(page, base, feature, rec)
                    assert_event_pair(rec, expected_appear)
                    attach_shot(page, f"mobile_login_02_{feature}_register.png")
                    register_or_login(page, mobile=True)
                    page.wait_for_timeout(7000)
                    assert_event_pair(rec, expected_success)
            finally:
                context.close()
        return

    if case["platform"] == "mobile":
        context = browser.new_context(**playwright.devices["iPhone 13"])
    else:
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    try:
        rec = StatsRecorder(page)
        FLOWS[case["flow"]](page, base, case, rec)
    finally:
        context.close()


def _build_test(case):
    description = (
        f"维度：{case['epic']} / {case['feature']}\n"
        "统计口径：目标事件 sendGaEvent=1 且 debug 统计=1；0=漏报，>=2=多报。"
    )

    def _test(browser, playwright, base_url):
        with allure.step(f"执行正常路径统计用例 {case['id']}"):
            _run_case(browser, playwright, base_url, case)

    _test.__name__ = "test_" + case["id"].lower().replace("-", "_")
    _test.__doc__ = description

    _test = allure.epic(case["epic"])(_test)
    _test = allure.feature(case["feature"])(_test)
    _test = allure.story(case["id"])(_test)
    _test = allure.title(f"{case['id']}: {case['title']}")(_test)
    _test = allure.description(description)(_test)
    _test = allure.severity(
        allure.severity_level.CRITICAL if case["priority"] == "P0" else allure.severity_level.NORMAL
    )(_test)
    _test = pytest.mark.regression(_test)
    if case["priority"] == "P0":
        _test = pytest.mark.p0(_test)
    if case.get("known_bug"):
        _test = pytest.mark.xfail(
            strict=True, reason="已知统计埋点缺陷，保留需求期望断言"
        )(_test)
    return _test


for _case in CASES:
    globals()[_build_test(_case).__name__] = _build_test(_case)
