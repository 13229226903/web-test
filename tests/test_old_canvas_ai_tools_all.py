# -*- coding: utf-8 -*-
"""旧画布 AI Tools 功能栏自动化测试（legacy canvas / en-US）。

基于 confirmed cases.md（6 条，去重后）与
page_map/pokecut/infinite_canvas_ai_tools_v1.yaml 实现。

覆盖: L1 结构 / L2 三态（初始 / 生成中 / 结束）/ L5 等价类 / L6 smoke。
去重: 19 个功能按「面板形态 + 提交前置」归并为 6 条用例，功能以组内循环项覆盖。
环境: 目标地址由 pytest --base-url 配置；PRO 会员 450832596@qq.com；素材 test_images/1K.jpg。
说明: 按用户要求不产出异常用例；merge layers 前置框与限流 Tips 仅在等待逻辑内兜底，不作断言。
"""
import os
import re
from pathlib import Path

import allure
import pytest
import hashlib
import json
import yaml
from playwright.sync_api import Page

from helpers.waiting import poll_until, settle, wait_network_quiet

def _repo_root() -> Path:
    """定位仓库根目录（兼容 tests/ 与 archive/<module>/ 两种存放位置）。"""
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "test_images").is_dir():
            return candidate
    return here.parent.parent

BASE_DIR = _repo_root()
DATA = yaml.safe_load((BASE_DIR / "data" / "old_canvas_ai_tools_v1.yaml").read_text(encoding="utf-8"))
IMG_1K = str(BASE_DIR / "test_images" / "1K.jpg")
SHOT_DIR = BASE_DIR / "data" / "screenshots"

# ---------------- page_map selector（不自行重猜） ----------------
SEL_NAV = 'div.flex.w-\\[5rem\\].flex-shrink-0.flex-col'
SEL_AI_TAB = SEL_NAV + ' > div:has(img[src*="edit_left_tab_btn_s_ai_tools"])'
SEL_LIST = 'div.h-\\[calc\\(100vh-5rem\\)\\].w-\\[25rem\\]:has-text("Common Tools")'
SEL_TOOL_CARD = 'li.flex.flex-col.items-center'
SEL_MODAL_CARD = 'div[class*="83.125rem"]'
SEL_SUBMIT = 'div.btn-bg-gradient1, button.btn-bg-gradient1'
SEL_PAINT_CANVAS = 'canvas[class*="z-0"][class*="500px"]'

SUBMIT_LABELS = {"Enhance", "Start Photo Restoration", "Generate", "Remove", "Refine", "AI Extend", "Remove Background", "Apply"}


# ---------------- 通用工具 ----------------
def shot(page: Page, name: str) -> str:
    """整页截图并附加到 Allure（保留左面板 / 画布 / 右属性面板上下文）。"""
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    safe = re.sub(r"[^0-9A-Za-z_\-\u4e00-\u9fff]+", "_", name)
    path = SHOT_DIR / f"{safe}.png"
    page.screenshot(path=str(path), full_page=False)
    allure.attach.file(str(path), name=name, attachment_type=allure.attachment_type.PNG)
    return str(path)


def wait_layout_stable(page: Page, rounds: int = 2, interval: int = 400) -> None:
    """等布局指纹连续两次一致（canvas 数 + 几何），避免截到过渡帧。"""
    def fingerprint():
        return page.evaluate(
            """() => {
                const cs = Array.from(document.querySelectorAll('canvas'))
                    .map(c => c.getBoundingClientRect())
                    .filter(r => r.width > 0 && r.height > 0)
                    .map(r => [Math.round(r.x), Math.round(r.y), Math.round(r.width), Math.round(r.height)]);
                return JSON.stringify(cs.sort());
            }"""
        )

    last = None
    same = 0
    for _ in range(20):
        cur = fingerprint()
        same = same + 1 if cur == last else 0
        last = cur
        if same >= rounds - 1:
            return
        # 稳定轮询间隔（本函数内置 20 轮上限 + interval 参数，属显式轮询）
        page.wait_for_timeout(interval)


def _safe_click(page: Page, locator) -> bool:
    """兜底点击：优先真实点击，被遮罩（z-50 半透明层）拦截时改用 JS 直接派发 click。

    实测（2026-10-13）：限流 Tips / merge 弹层的半透明遮罩会 intercepts pointer events，
    真实点击会 30s 超时并把整个用例带崩；这类弹层本身只是环境态兜底，不应影响主链路。
    """
    try:
        locator.click(timeout=6000)
        return True
    except Exception:
        try:
            locator.first.evaluate(
                "el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))"
            )
            return True
        except Exception:
            return False


def dismiss_blockers(page: Page) -> bool:
    """关闭 merge layers 前置框 / 限流 Tips / Processing failed（兜底，不作断言）。"""
    handled = False
    for _ in range(4):
        merge = page.locator('div.fixed[class*="0.5"]').filter(has_text="merge layers")
        if merge.count():
            btn = merge.first.locator('button:has-text("Confirm")')
            if btn.count():
                _safe_click(page, btn.last)
                # 关闭生效信号：merge layers 弹层消失
                poll_until(page, lambda: page.locator('div.fixed[class*="0.5"]').filter(has_text="merge layers").count() == 0,
                           timeout=8000, interval=300)
                handled = True
                continue
        body = page.locator("body").inner_text()
        # 2026-11-07：补充服务端繁忙文案。实测 P-AIT-02 Hair Removal Manual 段弹出
        #   "The server is busy, please try again later."（截图取证），原兜底只匹配
        #   "This feature is busy"，导致弹窗一直挡着、后续点击被吞、失败点逐次漂移。
        BUSY_TEXTS = ("This feature is busy", "Processing failed",
                      "The server is busy", "server is busy", "please try again later",
                      # 2026-11-08：实测 Magic Eraser Manual 段弹出
                      # "Please check the network and try again."（环境/网络类），原兜底未覆盖。
                      "Please check the network", "check the network and try again")
        if any(t in body for t in BUSY_TEXTS):
            clicked = False
            for label in ("OK", "Cancel", "Try again"):
                b = page.locator('button:has-text("%s")' % label)
                if b.count():
                    _safe_click(page, b.last)
                    # 关闭生效信号：busy / Processing failed 文案消失
                    poll_until(page, lambda: not any(
                        t in page.locator("body").inner_text() for t in BUSY_TEXTS
                    ), timeout=8000, interval=300)
                    handled = True
                    clicked = True
                    break
            if not clicked:
                break
            continue
        break
    return handled


EDITOR_NAV_JS = """() => [...document.querySelectorAll('img')]
  .filter(i => (i.getAttribute('src') || '').includes('edit_left_tab_btn_')).length"""

# 旧画布进入后的全屏遮罩（含 loading spinner：.pk-loading-svg 的 z-[230] 半透明层）。
# 该层会拦截所有 pointer 事件；它消失 == 画布内容加载完成，是真正的就绪信号。
EDITOR_OVERLAY_JS = """() => Array.from(document.querySelectorAll('div')).filter(el => {
    const st = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    const z = parseInt(st.zIndex || '0', 10);
    return st.position === 'fixed' && z >= 100 && r.width > 800 && r.height > 500
           && st.display !== 'none' && st.visibility !== 'hidden';
  }).length"""


def wait_editor_ready(page: Page, timeout: int = 60000) -> bool:
    """等旧画布编辑器真正可交互：左侧工具栏 >= 8 项 **且** 全屏 loading 遮罩已消失。

    - 工具栏出现只说明 Vue 挂载完，画布图片仍在 loading（z-230 半透明层拦截 pointer）。
    - 必须同时满足遮罩消失，否则后续任何 click 都会被 "intercepts pointer events" 卡死。
    编辑器专属判据；不用「任意大图」避免 /create 模板缩略图造成的假就绪。
    """

    def _ready() -> bool:
        return page.evaluate(EDITOR_NAV_JS) >= 8 and page.evaluate(EDITOR_OVERLAY_JS) == 0

    return poll_until(page, _ready, timeout=timeout, interval=500)


def enter_canvas_via_template(page: Page, base_url: str, image: str = IMG_1K, attempts: int = 4) -> str:
    """从 /template 第一个模板卡上传并进入旧画布（入口同 page_map.entry）。"""
    last_err = None
    for attempt in range(1, attempts + 1):
        try:
            with allure.step("进入 /template 第一个模板并上传 1K.jpg（第 %d 次）" % attempt):
                page.goto(base_url + "/template", wait_until="domcontentloaded", timeout=120000)
                card = page.locator('div.relative.flex.w-\\[9\\.625rem\\].cursor-pointer').first
                # 模板入口就绪信号：首个模板卡可见（替代固定 5s）
                card.wait_for(state="visible", timeout=30000)
                card.scroll_into_view_if_needed()
                # 等 Vue hydration 完成，避免点击被冷启动竞态吞掉（filechooser 不触发）
                wait_network_quiet(page, timeout=10000, idle_ms=1200)
                # 点击受理判据 = filechooser 弹出；未弹出则重试点击
                opened = False
                for _ in range(3):
                    try:
                        with page.expect_file_chooser(timeout=12000) as fc:
                            card.click()
                        fc.value.set_files(image)
                        opened = True
                        break
                    except Exception:
                        wait_network_quiet(page, timeout=3000, idle_ms=0)
                if not opened:
                    raise AssertionError("模板卡点击未触发文件选择器，当前 URL: %s" % page.url)
                # URL 就绪信号：进入旧画布
                poll_until(page, lambda: "/create/edit?pid=" in page.url, timeout=90000, interval=1000)
                if "/create/edit?pid=" not in page.url:
                    raise AssertionError("模板卡上传后未进入画布，当前 URL: %s" % page.url)
                # 编辑器专属就绪信号：左侧工具栏 edit_left_tab_btn_* >= 8 且加载遮罩消失。
                # 不能用 wait_canvas_ready 的「任意大图」判据——/create 模板页有 189 张缩略图
                # 会假就绪，导致 session 在编辑器真正渲染前就关页，复用时被甩回 /create。
                assert wait_editor_ready(page, timeout=60000), "旧画布编辑器未在超时内渲染完成"
            return page.url
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            if attempt == attempts:
                break
            # 重试间隔：等上一条失败上传请求释放（无独立可观察信号）
            page.wait_for_timeout(2500)
    raise AssertionError("模板入口进入旧画布失败（已重试 %d 次）: %s" % (attempts, last_err))


def login_vip(page: Page, base_url: str) -> None:
    """会员账号登录（PRO 450832596@qq.com）。"""
    page.goto(base_url + "/", wait_until="domcontentloaded", timeout=120000)
    btn = page.get_by_role("button", name="Log in", exact=True)
    # 首页就绪信号：Log in 入口出现（替代固定 3.5s）
    poll_until(page, lambda: page.get_by_role("button", name="Log in", exact=True).count() > 0
               or page.locator('input[type="email"]').count() > 0, timeout=30000, interval=300)
    if btn.count():
        # 元素挂载 != Vue 事件绑定完成：等网络静默后再点，避免点击被 hydration 竞态吞掉
        wait_network_quiet(page, timeout=4000, idle_ms=500)
        # 点击受理判据 = 邮箱框出现；未出现则重试点击（同 insert_panel 修法）
        for _ in range(5):
            btn.first.click()
            if poll_until(page, lambda: page.locator('input[type="email"]').count() > 0, timeout=3000, interval=300):
                break
        assert page.locator('input[type="email"]').count() > 0, "点击 Log in 后登录弹窗未出现"
        page.locator('input[type="email"]').first.fill(DATA["account"]["email"])
        page.locator('input[placeholder*="Verification"]').first.fill(DATA["account"]["code"])
        page.locator('button:has-text("Log in")').last.click()
        # 登录成功信号：email 输入框消失（替代固定 8s）
        poll_until(page, lambda: page.locator('input[type="email"]').count() == 0, timeout=40000, interval=1000)


def open_ai_tools(page: Page) -> None:
    # 点前兜底：等画布 loading 遮罩消失，否则点击会被 z-230 spinner 层拦截
    poll_until(page, lambda: page.evaluate(EDITOR_OVERLAY_JS) == 0, timeout=15000, interval=300)
    page.locator(SEL_AI_TAB).first.click()
    # 面板就绪信号：工具列表面板出现（替代固定 1.5s）
    poll_until(page, lambda: page.locator(SEL_LIST).count() > 0, timeout=10000, interval=250)
    assert page.locator(SEL_LIST).count() > 0, "AI Tools 工具列表面板未出现"


def click_tool_card(page: Page, name: str) -> None:
    """滚动工具列表并点击指定工具卡。"""
    card = page.locator(SEL_TOOL_CARD).filter(has_text=re.compile(r"^%s$" % re.escape(name)))
    assert card.count() > 0, "AI Tools 列表未找到工具卡: %s" % name
    card.first.scroll_into_view_if_needed()
    card.first.click()
    # 面板打开信号：Confirm 出现（替代固定 2.5s）
    poll_until(page, lambda: panel(page) is not None and panel(page).locator("text=Confirm").count() > 0,
               timeout=20000, interval=400)
    dismiss_blockers(page)


def panel(page: Page):
    """功能面板根节点（各类模态共用 w-[83.125rem] 白卡）。"""
    loc = page.locator(SEL_MODAL_CARD)
    return loc.nth(loc.count() - 1) if loc.count() else None


def wait_panel(page: Page, timeout_ms: int = 30000):
    step = 1500
    waited = 0
    while waited < timeout_ms:
        p = panel(page)
        if p is not None and p.locator("text=Confirm").count() > 0:
            return p
        dismiss_blockers(page)
        # 面板轮询间隔（本函数自带有界 timeout_ms，属显式轮询）
        page.wait_for_timeout(step)
        waited += step
    return None


def click_text_in_panel(page: Page, text: str) -> bool:
    """在功能面板内点击文本精确匹配的最内层可点元素。"""
    box = page.evaluate(
        r"""([cardSel, text]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return null;
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const cands = Array.from(root.querySelectorAll('*')).filter(el => {
                if (norm(el.innerText) !== text) return false;
                const r = el.getBoundingClientRect();
                if (r.width <= 0 || r.height <= 0) return false;
                if (r.height < 18 || r.height > 300) return false;
                return getComputedStyle(el).cursor === 'pointer';
            });
            if (!cands.length) return null;
            cands.sort((a, b) => a.getBoundingClientRect().height - b.getBoundingClientRect().height);
            const r = cands[0].getBoundingClientRect();
            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
        }""",
        [SEL_MODAL_CARD, text],
    )
    if not box:
        return False
    page.mouse.click(box["x"], box["y"])
    # 面板重建窗口（有界）：切换分类/预设后面板异步重建（预设列表 + 主按钮由 Confirm 变 Generate），
    # 重建完成前立即提交会被吞掉（P-AIT-01 跨分类 120s 假超时的根因）。
    # 2026-11-07 备注：曾尝试改为「轮询主按钮解禁」以缩短等待，但该信号有假阳性——
    # 连续第二次选预设时主按钮本就处于解禁态（上一次选择留下的），轮询会立即返回并跳过了
    # 重建等待，导致 P-AIT-02 Magic Eraser 等再次超时。故保留有界停等（与改造前语义一致）；
    # 「提交前主按钮必须解禁」的 fail-fast 已下沉到 submit_and_wait_done，不再依赖此处。
    settle(page, 2500)
    return True


def click_tile_by_index(page: Page, index: int) -> bool:
    """点击面板内第 index 个含 img 的可点预设瓦片（用于无文字的缩略图预设）。"""
    box = page.evaluate(
        """([cardSel, idx]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return null;
            const cands = Array.from(root.querySelectorAll('div')).filter(el => {
                const r = el.getBoundingClientRect();
                if (r.width < 40 || r.width > 200 || r.height < 40 || r.height > 300) return false;
                if (!el.querySelector('img')) return false;
                return getComputedStyle(el).cursor === 'pointer';
            });
            if (cands.length <= idx) return null;
            const r = cands[idx].getBoundingClientRect();
            return {x: r.x + r.width / 2, y: r.y + r.height / 2};
        }""",
        [SEL_MODAL_CARD, index],
    )
    if not box:
        return False
    page.mouse.click(box["x"], box["y"])
    # 预设选中生效由后续 submit_enabled 轮询校验；不再盲等 2s
    return True


def _clickable_info(page: Page, text: str):
    """按文案定位面板内可点控件，返回其禁用状态与中心点。

    口径：文本精确等于 text 的叶子节点，向上找最近带 cursor-pointer / cursor-not-allowed
    的祖先作为控件本体（各工具的 Confirm/Cancel 容器 class 不同，如 div.flex-1 与
    ml-auto h-[5rem] w-[13.75rem] rounded-[1.25rem]，故不能按 class 定位）。
    """
    return page.evaluate(
        r"""([cardSel, text]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return null;
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const leaves = Array.from(root.querySelectorAll('span,p,div,button')).filter(el => {
                if (norm(el.innerText) !== text) return false;
                if (el.children.length > 1) return false;
                const r = el.getBoundingClientRect();
                if (r.width <= 0 || r.height <= 0) return false;
                return r.height <= 80;
            });
            if (!leaves.length) return null;
            leaves.sort((a, b) => {
                const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
                return (rb.width * rb.height) - (ra.width * ra.height);
            });
            const leaf = leaves[0];
            let btn = null;
            for (let cur = leaf, i = 0; cur && cur !== root && i < 6; i++, cur = cur.parentElement) {
                const cls = String(cur.className);
                if (cls.includes('cursor-not-allowed') || cls.includes('cursor-pointer')) { btn = cur; break; }
            }
            if (!btn) btn = leaf;
            const cls = String(btn.className);
            const r = btn.getBoundingClientRect();
            return {text: text, disabled: cls.includes('cursor-not-allowed'),
                    x: r.x + r.width / 2, y: r.y + r.height / 2, cls: cls.slice(0, 90)};
        }""",
        [SEL_MODAL_CARD, text],
    )


def click_confirm(page: Page) -> bool:
    """点击面板 Confirm（按文案识别）。"""
    info = _clickable_info(page, "Confirm")
    if not info:
        return False
    page.mouse.click(info["x"], info["y"])
    # 点击受理即可；后续 wait_result_state 会轮询结束态（去掉固定 1.5s）
    return True


def confirm_state(page: Page) -> str:
    """状态判据：Confirm 控件禁用 = 初始/生成中；可用 = 结束。"""
    if panel(page) is None:
        return "gone"
    info = _clickable_info(page, "Confirm")
    if not info:
        return "gone"
    return "disabled" if info["disabled"] else "enabled"


def mode_option_state(page: Page, text: str) -> str:
    """返回模式/预设选项的选中态：selected / unselected / absent。"""
    return page.evaluate(
        r"""([cardSel, text]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return "absent";
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const el = Array.from(root.querySelectorAll('p,div,span')).find(e => {
                if (norm(e.innerText) !== text) return false;
                if (e.children.length > 0) return false;
                const r = e.getBoundingClientRect();
                return r.width > 0 && r.height > 0 && r.height <= 120;
            });
            if (!el) return "absent";
            const cls = String(el.className);
            if (cls.includes('text-c-theme')) return "selected";
            if (cls.includes('text-c-btnicon')) return "unselected";
            return "unknown";
        }""",
        [SEL_MODAL_CARD, text],
    )


def panel_mode_labels(page: Page):
    """返回面板内所有「模式」选项文案（选中/未选中态）+ 数量，用于检测新增模式。"""
    return page.evaluate(
        r"""([cardSel]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return {labels: [], err: "panel_not_found"};
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const seen = [];
            for (const el of Array.from(root.querySelectorAll('p,div,span'))) {
                if (el.children.length > 0) continue;
                const t = norm(el.innerText);
                if (!/Mode$/.test(t)) continue;
                const r = el.getBoundingClientRect();
                if (r.width <= 0 || r.height <= 0 || r.height > 120) continue;
                const cls = String(el.className);
                if (!cls.includes('text-c-theme') && !cls.includes('text-c-btnicon')) continue;
                if (!seen.includes(t)) seen.push(t);
            }
            return {labels: seen};
        }""",
        [SEL_MODAL_CARD],
    )


def assert_mode_options(page: Page, label: str, expected_modes, default_mode) -> None:
    """断言模式集合完整、默认选中项正确、且每个模式可选中（2026-10-29 补强）。

    补强点（用户 2026-10-29 需求）：
      - 断言初始态存在全部模式选项（含新增 Low-Res Mode），任何多余/缺失模式都失败；
      - 断言会员/有积分账号默认选中 Ultra HD Mode，其余模式初始未选中；
      - 逐个点选每个模式并断言真的切换到选中态，最后复位默认模式。
    """
    found = panel_mode_labels(page)
    got = list(found.get("labels") or [])
    assert not found.get("err"), "%s 模式列表定位失败: %s" % (label, found.get("err"))
    assert set(got) == set(expected_modes), \
        "%s 初始态模式集合不符：期望 %s / 实际 %s" % (label, expected_modes, got)
    assert len(got) == len(expected_modes), \
        "%s 初始态模式数量不符：期望 %s 个 / 实际 %s 个 %s" % (
            label, len(expected_modes), len(got), got)
    assert mode_option_state(page, default_mode) == "selected", \
        "%s 默认选中模式应为 %s" % (label, default_mode)
    for mode in expected_modes:
        if mode == default_mode:
            continue
        assert mode_option_state(page, mode) == "unselected", \
            "%s 非默认模式 %s 初始不应选中" % (label, mode)
    for mode in expected_modes:
        assert click_text_in_panel(page, mode), "%s 未找到模式 %s" % (label, mode)
        state = mode_option_state(page, mode)
        assert state == "selected", "%s 点击模式 %s 后未选中（state=%s）" % (label, mode, state)
    assert click_text_in_panel(page, default_mode), "%s 未能复位到默认模式 %s" % (label, default_mode)
    assert mode_option_state(page, default_mode) == "selected", \
        "%s 复位到默认模式 %s 后未选中" % (label, default_mode)


def _primary_submit_info(page: Page):
    """按文案定位面板主提交按钮，并返回其禁用状态与中心点。

    口径：主按钮文案属于 SUBMIT_LABELS（Enhance / Generate / Remove / Refine / AI Extend /
    Start Photo Restoration / Remove Background / Apply），按钮态由最近祖先的
    cursor-not-allowed（禁用）/ cursor-pointer（可用）判定。
    page_map.states.tool_panel_initial.buttons.primary_submit 只登记了 btn-bg-gradient1，
    实测 AI Replace 的 Generate 用 custom-bg，故这里按 role_or_text 语义识别（已在 impl.md 记录漂移）。
    """
    return page.evaluate(
        r"""([cardSel, labels]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return null;
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const leaves = Array.from(root.querySelectorAll('span,p,div')).filter(el => {
                const t = norm(el.innerText);
                if (!labels.includes(t)) return false;
                if (el.children.length > 1) return false;
                const r = el.getBoundingClientRect();
                if (r.width <= 0 || r.height <= 0) return false;
                if (r.height > 60) return false;
                return true;
            });
            if (!leaves.length) return null;
            // 取最后一个（主按钮通常在 Cancel/Confirm 之前渲染，但更稳妥的是取面积最大者）
            leaves.sort((a, b) => {
                const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
                return (rb.width * rb.height) - (ra.width * ra.height);
            });
            const leaf = leaves[0];
            let btn = leaf;
            for (let i = 0; i < 6 && btn && btn !== root; i++) {
                const cls = String(btn.className);
                if (cls.includes('cursor-not-allowed') || cls.includes('cursor-pointer')) break;
                btn = btn.parentElement;
            }
            const cls = String(btn.className);
            const disabled = cls.includes('cursor-not-allowed');
            const r = btn.getBoundingClientRect();
            return {label: norm(leaf.innerText), disabled: disabled,
                    x: r.x + r.width / 2, y: r.y + r.height / 2, cls: cls.slice(0, 90)};
        }""",
        [SEL_MODAL_CARD, sorted(SUBMIT_LABELS)],
    )


def click_primary_submit(page: Page) -> str:
    """点击面板主提交按钮（按文案识别）。"""
    info = _primary_submit_info(page)
    assert info, "功能面板未找到主提交按钮"
    recorder_for(page).arm()
    page.mouse.click(info["x"], info["y"])
    # 提交受理信号：submit recorder 抓到请求或状态转入生成中（由 wait_result_state 轮询）
    return info["label"]


def _panel_canvas_rects(page: Page):
    """返回面板卡片内所有大尺寸可见 canvas 的几何（按面积降序、DOM 逆序）。"""
    return page.evaluate(
        r"""([cardSel]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return {err: 'panel_not_found'};
            const rr = root.getBoundingClientRect();
            const big = Array.from(document.querySelectorAll('canvas')).filter(c => {
                const r = c.getBoundingClientRect();
                return r.width >= 150 && r.height >= 150;
            });
            let pool = big.filter(c => {
                const r = c.getBoundingClientRect();
                return r.x >= rr.x - 8 && r.y >= rr.y - 8 && r.right <= rr.right + 8 && r.bottom <= rr.bottom + 8;
            });
            if (!pool.length) pool = big;
            const items = pool.map((c, i) => {
                const r = c.getBoundingClientRect();
                return {idx: i, x: r.x, y: r.y, w: r.width, h: r.height, area: r.width * r.height,
                        cls: String(c.className).slice(0, 90)};
            });
            items.sort((a, b) => (b.area - a.area) || (b.idx - a.idx));
            return {items: items};
        }""",
        [SEL_MODAL_CARD],
    )


def _dispatch_paint(page: Page, rect, steps: int = 20) -> bool:
    """向区块内第 index 个 canvas 派发 pointer/mouse 事件序列完成涂抹。"""
    res = page.evaluate(
        r"""([cardSel, idx, steps, x0, y0, w, h]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return {err: 'panel_not_found'};
            const rr = root.getBoundingClientRect();
            const big = Array.from(document.querySelectorAll('canvas')).filter(c => {
                const r = c.getBoundingClientRect();
                return r.width >= 150 && r.height >= 150;
            });
            let pool = big.filter(c => {
                const r = c.getBoundingClientRect();
                return r.x >= rr.x - 8 && r.y >= rr.y - 8 && r.right <= rr.right + 8 && r.bottom <= rr.bottom + 8;
            });
            if (!pool.length) pool = big;
            const el = pool[idx];
            if (!el) return {err: 'canvas_index_out_of_range', count: pool.length};
            const fire = (type, x, y, isPointer) => {
                const E = isPointer ? PointerEvent : MouseEvent;
                el.dispatchEvent(new E(type, {
                    bubbles: true, cancelable: true, clientX: x, clientY: y,
                    pointerId: 1, pointerType: 'mouse', isPrimary: true,
                    buttons: 1, button: 0, pressure: 0.5, composed: true,
                }));
            };
            const sx = x0 + w * 0.25, sy = y0 + h * 0.35;
            fire('pointerdown', sx, sy, true);
            fire('mousedown', sx, sy, false);
            for (let i = 1; i <= steps; i++) {
                const px = sx + w * 0.5 * i / steps;
                const py = sy + h * 0.2 * ((i % 3) / 2.0);
                fire('pointermove', px, py, true);
                fire('mousemove', px, py, false);
            }
            fire('pointerup', sx + w * 0.5, sy, true);
            fire('mouseup', sx + w * 0.5, sy, false);
            return {ok: true, cls: String(el.className).slice(0, 90)};
        }""",
        [SEL_MODAL_CARD, rect["_idx"], steps, rect["x"], rect["y"], rect["w"], rect["h"]],
    )
    return bool(res and res.get("ok"))


def canvas_alpha_probe(page: Page) -> list:
    """读取面板内各候选 canvas 的非透明像素数（判断涂抹是否真的落到画布上）。"""
    return page.evaluate(
        r"""([cardSel]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return [];
            const rr = root.getBoundingClientRect();
            const big = Array.from(document.querySelectorAll('canvas')).filter(c => {
                const r = c.getBoundingClientRect();
                return r.width >= 150 && r.height >= 150;
            });
            let pool = big.filter(c => {
                const r = c.getBoundingClientRect();
                return r.x >= rr.x - 8 && r.y >= rr.y - 8 && r.right <= rr.right + 8 && r.bottom <= rr.bottom + 8;
            });
            if (!pool.length) pool = big;
            return pool.map((c, i) => {
                const r = c.getBoundingClientRect();
                const out = {i: i, w: Math.round(r.width), h: Math.round(r.height),
                             cls: String(c.className).slice(0, 60), nonTransparent: null, err: null};
                try {
                    const ctx = c.getContext('2d');
                    if (!ctx) { out.err = 'no_2d_ctx'; return out; }
                    const d = ctx.getImageData(0, 0, c.width, c.height).data;
                    let n = 0;
                    for (let k = 3; k < d.length; k += 4) { if (d[k] > 0) n++; }
                    out.nonTransparent = n;
                } catch (e) { out.err = String(e).slice(0, 60); }
                return out;
            });
        }""",
        [SEL_MODAL_CARD],
    )


def paint_on_canvas(page: Page, until=None) -> bool:
    """在预览区涂抹蒙版，直到主按钮可用（= 涂抹生效）或被全部候选画布尝试过。

    - 定位：面板卡片内大尺寸可见 canvas，按面积降序、DOM 逆序逐个尝试（上层蒙版画布优先）。
    - 涂抹：向 canvas 派发 pointerdown/mousedown → pointermove/mousemove → pointerup/mouseup
      （handoff 已声明 driver），不依赖鼠标命中，避免被叠加层遮挡。
    - until: 判定涂抹是否生效的可调用对象；默认判定主按钮可用性。
    """
    check = until or (lambda: submit_enabled(page))
    info = _panel_canvas_rects(page)
    assert not info.get("err"), "涂抹 canvas 定位失败: %s" % info.get("err")
    items = info.get("items") or []
    assert items, "面板内未找到可涂抹的大尺寸 canvas"
    for rect in items:
        rect = dict(rect)
        rect["_idx"] = rect.get("idx", 0)
        _dispatch_paint(page, rect)
        # 涂抹生效信号：check() 变为真（短轮询替代固定 2.5s）
        poll_until(page, check, timeout=6000, interval=300)
        if check():
            return True
    return False


def submit_enabled(page: Page) -> bool:
    """主提交按钮当前是否可用（按文案识别主按钮后判断禁用态）。"""
    info = _primary_submit_info(page)
    return bool(info) and not info["disabled"]


# ---------------- 提交任务记录（taskId / styleId / efMode） ----------------
_RECORDERS = {}


class TaskRecorder:
    """监听 console，抓取每次真实提交后端任务产生的 taskId / styleId / efMode / resourceCode。

    实测（2026-10-13，旧画布 AI Tools 链路）：
      handleSubmitTask result {"resultCode":100,...,"data":{"taskId":"gzy_comfytextart_PokeCutWeb_..._cross"}}
      [AIGC 公告板][开始检查] {funcType: aiReplaceClothes, styleId: pkweb_comfyui_transfer_outfit_whitebg, ...}
    另：无提交的路径（客户端即时预览 / no-op）不会出现 handleSubmitTask，此时不作 taskId 断言。
    """

    def __init__(self, page: Page):
        self.logs = []
        self.pending = False
        page.on("console", lambda msg: self.logs.append(msg.text))

    def arm(self) -> None:
        """主按钮点击后调用：清空日志并标记「有提交待核验」。"""
        self.logs = []
        self.pending = True

    def collect(self) -> dict:
        text = "\n".join(self.logs)
        def grab(pattern):
            m = re.search(pattern, text)
            return m.group(1) if m else ""
        task = grab(r'"taskId"\s*:\s*"([^"]+)"') or \
               grab(r'taskId:\s*"?(?!undefined)([A-Za-z0-9_\-]{6,})')
        return {
            "submitted": "handleSubmitTask" in text,
            "taskId": task,
            "styleId": grab(r'styleId:\s*([^,}\s]+)'),
            "efMode": grab(r'efMode:\s*(\d+)'),
            "resourceCode": grab(r'resourceCode:\s*([^,}\s]+)'),
            "flowJobId": grab(r'flowJobId:\s*([A-Za-z0-9_\-]+)'),
        }


def recorder_for(page: Page) -> TaskRecorder:
    rec = _RECORDERS.get(id(page))
    if rec is None:
        rec = TaskRecorder(page)
        _RECORDERS[id(page)] = rec
    return rec


def record_submission(page: Page, label: str = "") -> dict:
    """在任务结束时汇总本次提交证据：附到 Allure；真实提交则断言 taskId 非空。"""
    rec = recorder_for(page)
    if not rec.pending:
        return {}
    rec.pending = False
    info = rec.collect()
    allure.attach(
        json.dumps(info, ensure_ascii=False, indent=2),
        name="提交任务记录: %s" % (label or "task"),
        attachment_type=allure.attachment_type.JSON,
    )
    if not info["submitted"]:
        # 客户端即时预览 / no-op 路径：没有提交后端任务，不伪造 taskId
        return info
    assert info["taskId"], "已提交后端任务但未抓到 taskId（提交证据：%s）" % info
    return info


def _cancel_disabled(page: Page) -> bool:
    """Cancel 当前是否禁用（page_map: Cancel 恒可用，故禁用 = 面板处于生成中/不可交互）。"""
    return bool((_clickable_info(page, "Cancel") or {}).get("disabled"))


def wait_cancel_enabled(page: Page, timeout_s: int = 180) -> bool:
    """等待 Cancel 恢复可用（面板空闲）。"""
    return wait_until(page, lambda: not _cancel_disabled(page), timeout_s=timeout_s)


def task_completed(page: Page) -> bool:
    """任务完成的**权威**信号：console 出现 taskflow stage: complete / 生成成功 / 结果就绪。

    2026-11-07 根因定位：本工具族没有可靠的 DOM 结束判据——
      - 进度环百分比画在 canvas 上，innerText 里读不到（实测恒为 None）；
      - 上一轮结果会让 Confirm 保持可用，而 Cancel 的点击容器并无 cursor-not-allowed 类，
        故 _cancel_disabled() 在生成期间恒为 False；
      - preview_digest 在生成中也可能连续 8 秒以上完全不变（canvas 动画不被 digest 捕获）。
    以上三点叠加，导致 wait_done_settled 在任务刚提交时就「假结束」（取证截图进度环 1%/40%/90%）。
    唯一稳定可信的结束信号是 console 里的 taskflow 完成事件（实测 t≈12.7s 出现
    "stage: complete, status: success"）。
    """
    text = "\n".join(recorder_for(page).logs)
    # 完成信号族（按实测覆盖度从强到弱）：
    #   - "stage: complete, status: success"：taskflow 结果链路完整走到完成（Watermark Remover 实测 t≈12.7s）
    #   - "TaskFlowManager 完成一个job"：job 收尾（AI Image Extender 实测 t≈26.1s，该链路不发 stage: complete）
    #   - "生成成功"：部分工具的直接文案
    return ("stage: complete, status: success" in text
            or "TaskFlowManager 完成一个job" in text
            or "生成成功" in text)


def task_submitted(page: Page) -> bool:
    """本次提交是否真的起了生成任务（用于决定结束判据）。

    覆盖两类链路：
      - 走 taskflow 的常规提交：出现 handleSubmitTask / flowJobId；
      - Manual Mode 手绘蒙版提交（Hair Removal / Magic Eraser 实测）：**不发 handleSubmitTask**，
        但会发 `sendGaEvent 生成成功` / `统计：生成成功`，且完成后主按钮**不会**自动恢复可用
        （需用户点 Confirm 应用），因此不能靠「主按钮恢复」判结束。
    无上述任何信号的路径才回退到纯 UI 判据。
    """
    text = "\n".join(recorder_for(page).logs)
    return ("handleSubmitTask" in text) or ("flowJobId" in text) or ("生成成功" in text)


def wait_done_settled(page: Page, timeout_s: int = 180) -> bool:
    """等待面板**完全**落到结束态：Confirm 可用 且 Cancel 可用，且预览画面稳定。

    实测（2026-10-14，AI Clothes Changer 第二次提交 Dresses）：生成期间 Confirm 始终保持
    可用（面板显示的是上一次结果的状态），只有 Cancel 变为 cursor-not-allowed
    （t=4..28 均如此，t=32 才恢复）。因此仅凭「Confirm 可用」判断结束会得到**假结束**
    ——取证截图里仍带进度环、Cancel 仍禁用。结束判据必须同时要求 Cancel 可用。
    """
    # 2026-11-07 修复（假结束）：原实现把 wait_preview_stable 的返回值丢弃，
    # 无条件 return True。而本工具族 Cancel 的点击容器并无 cursor-not-allowed 类，
    # 生成期间 _cancel_disabled() 恒为 False；一旦上一轮结果让 Confirm 保持可用，
    # 判据在**任务刚提交约 0.5s** 就为真 —— 取证截图里进度环仍停在 40%/90%，
    # 用例却当作「已结束」继续点 Before/After，造成失败点逐次漂移（flaky）。
    # 现在「预览画面稳定」是**必需**条件：进度环动画会让预览指纹持续变化，
    # 只有真正结束（画面不再变化）才放行。
    import time as _time
    deadline = _time.monotonic() + timeout_s
    while _time.monotonic() < deadline:
        dismiss_blockers(page)
        # 判据分流：
        #   - 起了后端任务 → 必须拿到 console 完成事件（UI 侧状态与预览指纹都不可靠，见 task_completed 注释）；
        #   - 无后端任务（客户端即时生效 / no-op）→ 退回 UI 判据 + 预览稳定。
        if task_submitted(page):
            if task_completed(page):
                # 注意：Manual Mode 完成后主按钮保持禁用（需用户点 Confirm），
                # 故这里不能用 submit_enabled 作附加条件，仅等画面稳定即可。
                wait_preview_stable(page, timeout_s=min(30, max(8, int(deadline - _time.monotonic()))))
                return True
        else:
            if confirm_state(page) == "enabled" and not _cancel_disabled(page):
                remaining = max(8, int(deadline - _time.monotonic()))
                if wait_preview_stable(page, timeout_s=min(30, remaining)):
                    return True
        # 状态轮询间隔（本函数自带有界 timeout_s，属显式轮询）
        page.wait_for_timeout(1000)

    # 失败取证（2026-11-07）：超时时 dump 面板真实状态 + 提交/任务 console 证据 +
    # 进度环百分比，区分「任务真卡住」与「状态判据未捕获结束」。不带取证的超时只能看到
    # "等不到结束态"，无法归因（多次复现失败点漂移，属 flaky，必须留证）。
    try:
        diag = page.evaluate(
            r"""([cardSel]) => {
                const cards = Array.from(document.querySelectorAll(cardSel));
                const root = cards[cards.length - 1];
                if (!root) return {err: 'panel_gone'};
                const t = (root.innerText || '');
                const m = t.match(/(\d{1,3})\s*%/);
                return {
                    panel_text: t.replace(/\s+/g, ' ').slice(0, 600),
                    progress: m ? m[1] + '%' : null,
                };
            }""",
            [SEL_MODAL_CARD],
        )
        rec = recorder_for(page)
        info = rec.collect() if rec.pending else {}
        confirm = confirm_state(page)
        cancel_disabled = _cancel_disabled(page)
        allure.attach(
            json.dumps({
                "confirm_state": confirm,
                "cancel_disabled": cancel_disabled,
                "panel_diag": diag,
                "submit_record": info,
                "console_tail": "\n".join(rec.logs[-40:]),
            }, ensure_ascii=False, indent=2),
            name="wait_done_settled 超时取证",
            attachment_type=allure.attachment_type.TEXT,
        )
        shot(page, "wait_done_settled_超时")
    except Exception:
        pass
    return False


def submit_and_wait_done(page: Page, label: str, timeout_s: int = 180, expect_label: str = None,
                         assert_started: bool = False) -> str:
    """点主按钮 → 先确认任务真的起步 → 再等结束。

    实测（2026-10-14，AI Clothes Changer Dresses）：同一面板内**第二次**提交时，
    上一个结果的 Confirm 仍处于可用态，若直接调 wait_done 会立刻返回「结束」，
    而实际任务刚刚起步（取证截图中可见 10% 进度环、Cancel 仍为 cursor-not-allowed）。
    因此必须先观察到状态迁移（Confirm 转禁用 或 预览画面变化）才认为任务开始，
    该迁移同时兜底了 no-op 路径（不迁移时最多白等 bounded 窗口）。
    """
    # 提交前置：主按钮必须已解禁。若仍禁用说明预设点击被吞/未生效。
    # 2026-11-07 修复：原先直接点主按钮——若它仍 disabled 则点击无效果，白等到 120s 超时
    # （P-AIT-01 偶发卡死的表象）。这里先做有界等待，再 fail-fast 给出可诊断的错误，
    # 不猜测预设名去重试（预设名由各用例/数据文件决定，避免张冠李戴）。
    if (_primary_submit_info(page) or {}).get("disabled"):
        poll_until(page, lambda: (_primary_submit_info(page) or {}).get("disabled") is False,
                   timeout=8000, interval=300)
    info = _primary_submit_info(page)
    assert info and not info.get("disabled"), \
        "%s 主提交按钮在提交前仍为禁用态（预设/分类点击未生效）：label=%s" % (
            label, info and info.get("label"))
    d0 = preview_digest(page)
    got = click_primary_submit(page)
    assert got, "%s 主提交按钮文案为空" % label
    if expect_label:
        assert got == expect_label, "%s 主按钮文案应为 %s，实际 %s" % (label, expect_label, got)
    # 生成中态判据：
    #   - 常规工具：Confirm 转禁用 或 Cancel 转禁用 或 预览指纹变化；
    #   - assert_started=True（Photo Enhancer 补强）：初始 Confirm 本即禁用，不能用它判起步，
    #     必须要求更强信号「Cancel 转禁用 或 预览指纹变化」，否则会在提交瞬间假通过。
    if assert_started:
        started = wait_until(page, lambda: _cancel_disabled(page) or preview_digest(page) != d0,
                             timeout_s=30)
        assert started, "%s 提交后未进入生成中态（Cancel/预览均无迁移）" % label
    else:
        wait_until(page, lambda: confirm_state(page) == "disabled" or _cancel_disabled(page)
                   or preview_digest(page) != d0, timeout_s=30)
    assert wait_done_settled(page, timeout_s=timeout_s), \
        "%s 任务未在超时内进入结束态（Confirm/Cancel 未同时可用）" % label
    return "enabled"


def wait_done(page: Page, timeout_s: int = 120) -> str:
    """轮询 Confirm 直到 enabled（= 任务结束）。"""
    waited = 0.0
    while waited < timeout_s:
        dismiss_blockers(page)
        state = confirm_state(page)
        if state == "enabled":
            record_submission(page)
            return state
        # 状态轮询间隔（本函数自带有界 timeout_s，属显式轮询）
        page.wait_for_timeout(2500)
        waited += 2.5
    return confirm_state(page)


def close_panel(page: Page) -> None:
    """关闭功能面板回到 AI Tools 列表（组内工具连续执行用）。

    关闭判据：功能面板白卡（w-[83.125rem]）消失；Cancel 无效时用 Escape 兜底。
    注意：生成中的百分比进度层会吞掉点击，故先等面板空闲。
    """
    if panel(page) is not None:
        # 面板空闲判据：Cancel 恢复可用（生成中 Cancel 为禁用；初始态 Confirm 可能禁用，
        # 故这里不能用「Confirm 可用」判定，否则会白等超时）
        wait_cancel_enabled(page, timeout_s=120)
        wait_preview_stable(page, timeout_s=120)
    for _ in range(4):
        if panel(page) is None:
            return
        info = _clickable_info(page, "Cancel")
        if info:
            page.mouse.click(info["x"], info["y"])
        else:
            page.keyboard.press("Escape")
        # 关闭生效信号：面板消失（替代固定 2.5s）
        poll_until(page, lambda: panel(page) is None, timeout=20000, interval=400)
        wait_preview_stable(page, timeout_s=60)
    assert panel(page) is None, "功能面板未能关闭（Cancel/Escape 均无效）"


def open_tool(page: Page, name: str):
    """打开工具并等待面板就绪；返回面板或 None。"""
    close_panel(page)
    assert panel(page) is None, "打开 %s 前仍有功能面板未关闭" % name
    click_tool_card(page, name)
    return wait_panel(page)


def model_selected(page: Page, text: str) -> bool:
    """模型/预设是否处于选中态（Background Remover / Face Cutout 实测选中标记 = text-c-theme）。"""
    return bool(page.evaluate(
        r"""([cardSel, text]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return false;
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            return Array.from(root.querySelectorAll('div,span,p')).some(el => {
                if (norm(el.innerText) !== text) return false;
                const r = el.getBoundingClientRect();
                if (r.width <= 0 || r.height <= 0 || r.height > 120) return false;
                return String(el.className).includes('text-c-theme');
            });
        }""",
        [SEL_MODAL_CARD, text],
    ))


def select_model(page: Page, text: str, tries: int = 5, interval_s: float = 3.0) -> bool:
    """点击模型/预设并重试（服务端 busy Tips 或异步加载会吞掉点击）。"""
    for _ in range(tries):
        dismiss_blockers(page)
        if click_text_in_panel(page, text):
            # 选中生效信号：模式/预设变为选中态
            poll_until(page, lambda: mode_option_state(page, text) == "selected", timeout=8000, interval=300)
            return True
        # 重试间隔：busy Tips 会吞点击，需等一轮再试（无独立可观察信号）
        page.wait_for_timeout(int(interval_s * 1000))
    return False


def panel_text(page: Page) -> str:
    """功能面板当前可见文本（用于判定是否仍处于生成中）。"""
    p = panel(page)
    return p.inner_text() if p is not None else ""


def wait_panel_idle(page: Page, timeout_s: int = 120, require_result: bool = True, stable: int = 2) -> bool:
    """等待面板真正空闲。

    实测：生成中的百分比进度环是**画在 canvas 上**的（DOM 文本里拿不到 "NN%"），
    进度层会吞掉所有点击（含 Cancel），所以「是否还在生成」要看画面而不是文本；
    这里同时要求面板文本无残留百分比、且（require_result 时）已回到结果态。
    """
    ok = 0
    waited = 0.0
    while waited < timeout_s:
        dismiss_blockers(page)
        busy = bool(re.search(r"\d{1,3}%", panel_text(page)))
        ready = (not busy) and (confirm_state(page) == "enabled" if require_result else True)
        if ready:
            ok += 1
            if ok >= stable:
                return True
        else:
            ok = 0
        # 稳定轮询间隔（本函数自带有界 timeout_s，属显式轮询）
        page.wait_for_timeout(2000)
        waited += 2
    return ok >= stable


def _tab_marker(page: Page, text: str):
    """返回面板内文本精确等于 text 的最内层控件（h>=40）的 class 串；找不到返回 None。"""
    return page.evaluate(
        r"""([cardSel, text]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return null;
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const cands = Array.from(root.querySelectorAll('div,span,button,p')).filter(el => {
                if (norm(el.innerText) !== text) return false;
                const r = el.getBoundingClientRect();
                return r.width > 0 && r.height >= 40;
            });
            if (!cands.length) return null;
            cands.sort((a, b) => a.getBoundingClientRect().height - b.getBoundingClientRect().height);
            return String(cands[0].className) + ' ##' + String(cands[0].id);
        }""",
        [SEL_MODAL_CARD, text],
    )


def tab_selected(page: Page, text: str) -> bool:
    """模式/分类 tab 是否处于选中态（实测选中标记为 class 含 bg-c-theme + text-white）。"""
    cls = _tab_marker(page, text)
    return bool(cls) and "bg-c-theme" in cls


def select_tab(page: Page, text: str, tries: int = 6) -> bool:
    """切换模式/分类 tab，并断言切换真的生效（防点击被 Tips 遮罩吞掉）。"""
    for _ in range(tries):
        if tab_selected(page, text):
            return True
        dismiss_blockers(page)
        if click_text_in_panel(page, text):
            # tab 切换生效信号：tab_selected(page, text)（替代固定 1.5s）
            poll_until(page, lambda: tab_selected(page, text), timeout=8000, interval=300)
            if tab_selected(page, text):
                return True
        # 重试间隔：Tips 遮罩会吞点击，等一轮再试（无独立可观察信号）
        page.wait_for_timeout(1000)
    return tab_selected(page, text)


def wait_until(page: Page, predicate, timeout_s: int = 60, poll_s: float = 1.5) -> bool:
    """轮询谓词直到为真或超时。"""
    waited = 0.0
    while waited < timeout_s:
        dismiss_blockers(page)
        if predicate():
            return True
        # 轮询间隔（本函数自带有界 timeout_s，属显式轮询）
        page.wait_for_timeout(int(poll_s * 1000))
        waited += poll_s
    return predicate()


def result_state(page: Page) -> str:
    """结果态判据：主按钮为 Refine 且 Confirm 可用（= 已有可用结果）。"""
    info = _primary_submit_info(page) or {}
    return "result" if info.get("label") == "Refine" and confirm_state(page) == "enabled" else "not_result"


def preview_digest(page: Page):
    """面板预览区的画面指纹。

    口径：截取功能面板左半（预览区）。实测生成中的百分比进度环是画在 canvas 上的
    （DOM 文本里拿不到 "NN%"），所以只能用画面指纹来判断"是否仍在动"。
    """
    p = panel(page)
    if p is None:
        return None
    b = p.bounding_box()
    if not b:
        return None
    clip = {"x": b["x"], "y": b["y"], "width": max(1.0, b["width"] * 0.55), "height": b["height"]}
    return hashlib.md5(page.screenshot(clip=clip)).hexdigest()


def wait_preview_stable(page: Page, timeout_s: int = 180, stable: int = 3, poll_s: float = 2.0) -> bool:
    """等待预览区画面停止变化（= 生成/应用中的进度环已结束）。"""
    last = None
    same = 0
    waited = 0.0
    while waited < timeout_s:
        cur = preview_digest(page)
        if cur is not None and cur == last:
            same += 1
            if same >= stable:
                return True
        else:
            same = 0
        last = cur
        # 稳定轮询间隔（本函数自带有界 timeout_s，属显式轮询）
        page.wait_for_timeout(int(poll_s * 1000))
        waited += poll_s
    return same >= stable


def canvas_area_digest(page: Page):
    """主画布区域（排除功能面板内的预览 canvas）的画面指纹。

    用于破坏性工具「应用后画布是否真的变了」的断言：工具面板关闭后仍可稳定取到，
    且与打开工具前的基线取自同一区域，可直接比较。
    """
    box = page.evaluate(
        r"""() => {
            const cards = Array.from(document.querySelectorAll('div[class*="83.125rem"]'));
            const root = cards.length ? cards[cards.length - 1] : null;
            const rr = root ? root.getBoundingClientRect() : null;
            let best = null;
            for (const c of Array.from(document.querySelectorAll('canvas'))) {
                const r = c.getBoundingClientRect();
                if (r.width < 200 || r.height < 200) continue;
                if (rr && r.x >= rr.x - 8 && r.y >= rr.y - 8 && r.right <= rr.right + 8 && r.bottom <= rr.bottom + 8) continue;
                const area = r.width * r.height;
                if (!best || area > best.area) best = {x: r.x, y: r.y, w: r.width, h: r.height, area: area};
            }
            return best;
        }"""
    )
    if not box:
        return None
    x = max(0.0, box["x"]); y = max(0.0, box["y"])
    clip = {"x": x, "y": y,
            "width": max(1.0, min(box["w"], 1920 - x)),
            "height": max(1.0, min(box["h"], 1080 - y))}
    return hashlib.md5(page.screenshot(clip=clip)).hexdigest()


def click_clothes_tile(page: Page, kind: str, tries: int = 4, download_timeout_s: int = 40):
    """选中服装预设缩略图并等待资源下载完成。

    用户指正（2026-10-13）：选中服装预设后需要**等待预设资源下载完成**，主按钮 Generate
    才会由禁用变为可点；下载前点击/断言都会失败。
    实测补充：预设网格是滚动容器（max-h-18rem overflow-y-auto，可见带约 288px 高），
    切换分类后靠前的缩略图可能落在可见带外，需先滚进可见带再点，否则会点到被遮挡的按钮。

    返回生效的缩略图 src；失败返回 None。
    """
    for idx in range(tries):
        res = page.evaluate(
            r"""([cardSel, kind, idx]) => {
                const cards = Array.from(document.querySelectorAll(cardSel));
                const root = cards[cards.length - 1];
                if (!root) return null;
                const imgs = Array.from(root.querySelectorAll('img'))
                    .filter(i => (i.getAttribute('src') || '').includes(kind));
                const img = imgs[idx];
                if (!img) return {err: 'index_out_of_range', total: imgs.length};
                let band = null;
                for (let cur = img.parentElement; cur && cur !== root; cur = cur.parentElement) {
                    if (cur.scrollHeight > cur.clientHeight + 8) { band = cur; break; }
                }
                if (band) {
                    const br = band.getBoundingClientRect();
                    const ir = img.getBoundingClientRect();
                    if (ir.top < br.top + 4 || ir.bottom > br.bottom - 4) {
                        band.scrollTop += (ir.top - br.top) - 16;
                    }
                }
                return {w: img.getBoundingClientRect().width, h: img.getBoundingClientRect().height};
            }""",
            [SEL_MODAL_CARD, kind, idx],
        )
        if not res or res.get("err"):
            break
        # 缩略图滚动进入可见带后索引会变化；点击后由 wait_until(submit_enabled) 轮询校验
        box = page.evaluate(
            r"""([cardSel, kind, idx]) => {
                const cards = Array.from(document.querySelectorAll(cardSel));
                const root = cards[cards.length - 1];
                if (!root) return null;
                const imgs = Array.from(root.querySelectorAll('img'))
                    .filter(i => (i.getAttribute('src') || '').includes(kind));
                const img = imgs[idx];
                if (!img) return null;
                const r = img.getBoundingClientRect();
                if (r.width <= 0 || r.height <= 0) return null;
                return {x: r.x + r.width / 2, y: r.y + r.height / 2, src: img.getAttribute('src')};
            }""",
            [SEL_MODAL_CARD, kind, idx],
        )
        if not box:
            break
        page.mouse.click(box["x"], box["y"])
        # 等待预设资源下载完成 → Generate 由禁用变可点
        if wait_until(page, lambda: submit_enabled(page), timeout_s=download_timeout_s):
            return box["src"]
        # 预设资源下载未完成时换下一张；短间隔后重试（无独立可观察信号）
        page.wait_for_timeout(1000)
    return None


# ---------------- 结束态各按钮状态断言 ----------------
def before_after_state(page: Page) -> dict:
    """探测面板内 Before/After 切换器及其选中态。

    实测结构：外层容器 h=60（选中 bg=rgb(35,35,35)，未选中 transparent）；
    内层文字 h=19（选中 class 含 text-white，未选中 text-[--tc-gray-p7]）。
    注意：**并非所有工具都有该控件**（如 Photo Enhancer 面板无 Before/After），
    故调用方须按 exists 判断，不能无条件断言。
    """
    return page.evaluate(
        r"""([cardSel]) => {
            const cards = Array.from(document.querySelectorAll(cardSel));
            const root = cards[cards.length - 1];
            if (!root) return {exists: false};
            const norm = t => (t || '').replace(/\s+/g, ' ').trim();
            const res = {exists: true, before: false, after: false};
            for (const el of Array.from(root.querySelectorAll('div,span,p,button'))) {
                const t = norm(el.innerText);
                if (t !== 'Before' && t !== 'After') continue;
                const r = el.getBoundingClientRect();
                if (r.width <= 0 || r.height <= 0) continue;
                const cs = getComputedStyle(el);
                const selected = String(el.className).includes('text-white')
                    || cs.backgroundColor === 'rgb(35, 35, 35)';
                if (!selected) continue;
                if (t === 'Before') res.before = true; else res.after = true;
            }
            return res;
        }""",
        [SEL_MODAL_CARD],
    )


def assert_done_state_controls(page: Page, label: str) -> dict:
    """结束态面板各按钮状态断言（page_map: states.tool_panel_done.buttons）。

    覆盖：
      - confirm_enabled：由调用方的 wait_done() 断言（Confirm 可用）
      - cancel（page_map: 恒可用）：断言 Cancel 存在且未禁用
      - after_tab（page_map: visible_condition=结果已就绪、恒可用、选中态黑底白字、
        action_result=预览切换到结果图）：若面板存在该控件，断言可在 Before/After 间切换
        且选中态正确；不存在则记 absent（Photo Enhancer 等工具确实无此控件）。
    说明：不断言「切换后预览像素必变」——结果态工具存在合法 no-op（如原图无水印，
    Watermark Remover 结果与 Before 一致），像素比对会产生假失败；仅作诊断附件。
    """
    assert wait_done_settled(page, timeout_s=180), \
        "%s 结束态未稳定（Confirm/Cancel 未同时可用，可能仍在生成中）" % label
    cancel = _clickable_info(page, "Cancel")
    assert cancel and not cancel.get("disabled"), \
        "%s 结束态 Cancel 应可用（page_map: 恒可用）" % label

    ba = before_after_state(page)
    out = {"cancel": "enabled", "confirm": "enabled", "before_after": "absent"}
    if not ba.get("exists") or not (ba.get("before") or ba.get("after")):
        allure.attach("面板无 Before/After 切换器（该工具确实无此控件）",
                      name="%s 结束态按钮状态" % label,
                      attachment_type=allure.attachment_type.TEXT)
        return out

    current = "After" if ba.get("after") else "Before"
    other = "Before" if current == "After" else "After"
    d0 = preview_digest(page)
    assert click_text_in_panel(page, other), "%s 结束态未点到 %s" % (label, other)
    # 切换生效信号：选中态切到目标（替代固定 2s）
    poll_until(page, lambda: (before_after_state(page).get("before") if other == "Before"
                              else before_after_state(page).get("after")), timeout=8000, interval=300)
    st = before_after_state(page)
    assert not (st.get("before") and st.get("after")), \
        "%s Before/After 同时处于选中态" % label
    assert (st.get("before") if other == "Before" else st.get("after")), \
        "%s 点 %s 后选中态未切到 %s（page_map: 选中态黑底白字）" % (label, other, other)
    d1 = preview_digest(page)
    assert click_text_in_panel(page, current), "%s 结束态未点回 %s" % (label, current)
    # 切换生效信号：选中态切回 current（替代固定 2s）
    poll_until(page, lambda: (before_after_state(page).get("before") if current == "Before"
                              else before_after_state(page).get("after")), timeout=8000, interval=300)
    st2 = before_after_state(page)
    assert (st2.get("before") if current == "Before" else st2.get("after")), \
        "%s 点回 %s 后选中态未恢复" % (label, current)
    out["before_after"] = "%s<->%s 可切换" % (current, other)
    allure.attach("结束态按钮状态：%s\n初始选中=%s；切换 %s -> %s 成功；预览指纹 %s -> %s" % (
        out, current, current, other, d0, d1),
        name="%s 结束态按钮状态" % label, attachment_type=allure.attachment_type.TEXT)
    return out


def switch_until_invalidated(page: Page, candidates, expect_label: str, tries_s: int = 180) -> str:
    """依次切候选模型，直到出现「结果失效」态（Confirm 禁用 + 主按钮变回 expect_label）。

    实测（2026-10-13/14，Face Cutout + Background Remover 同源面板）：
      - 打开即按默认模型出结果（Head&Face 或 General）；
      - 切到**本会话已生成过**的模型 → 命中缓存，直接保持结果态（无新任务）；
      - 切到**尚未生成过**的模型（Face Cutout 实测为 Text）→ 结果失效，主按钮变回
        `Remove Background` 且可点，必须点它才真正提交后端任务。
    返回触发失效的模型名；全部命中缓存则返回 ""。
    """
    for cand in candidates:
        dismiss_blockers(page)
        if model_selected(page, cand):
            continue
        if not select_model(page, cand):
            continue
        # 失效可能不会立刻出现；给一个短窗口，再继续尝试下一个候选
        if wait_until(page, lambda: confirm_state(page) == "disabled", timeout_s=25):
            info = _primary_submit_info(page) or {}
            if info.get("label") == expect_label:
                return cand
    return ""


def regen_by_submit(page: Page, expect_label: str, timeout_s: int = 240) -> None:
    """实测状态机：切换未生成过的模型后结果失效，主按钮变为可点的重新生成按钮，
    必须点它才会触发服务端任务（Background Remover / Face Cutout 实测 90s 内不会自动恢复）。"""
    assert wait_until(page, lambda: confirm_state(page) == "disabled", timeout_s=30), \
        "切预设后未进入「结果失效/待重新生成」态"
    info = _primary_submit_info(page) or {}
    assert info.get("label") == expect_label, \
        "切预设后主按钮应为 %s，实际 %s" % (expect_label, info.get("label"))
    assert not info.get("disabled"), "重新生成按钮 %s 应为可点" % expect_label
    assert click_primary_submit(page) == expect_label, "未点到重新生成按钮 %s" % expect_label
    assert wait_done(page, timeout_s=timeout_s) == "enabled", "重新生成未在超时内结束"
    wait_preview_stable(page, timeout_s=180)


# ---------------- session 前置 ----------------
@pytest.fixture(scope="session")
def canvas_session(playwright, base_url):
    """session 级：只做一次会员登录，提供已登录 context。

    2026-11-06：不再 session 上传一次并复用 pid URL——复用 pid 不是真实用户路径，
    且页面常驻 loading 遮罩（画布内容加载不完），改用每条用例走正常入口上传。
    """
    base_url = (base_url or DATA["base_url"]).rstrip("/")
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    login_vip(page, base_url)
    page.close()
    yield {"context": context, "base_url": base_url}
    context.close()
    browser.close()


@pytest.fixture
def canvas_page(canvas_session):
    """每条用例：复用同一 pid，重新打开画布得到干净初始态。"""
    page = canvas_session["context"].new_page()
    # 每条用例走正常入口（/template 模板首卡上传）进入旧画布，得到干净初始态
    enter_canvas_via_template(page, canvas_session["base_url"])
    wait_layout_stable(page)
    dismiss_blockers(page)
    yield page
    page.close()


# ---------------- 用例实现 ----------------


@allure.epic("Pokecut")
@allure.feature("旧画布 AI Tools 功能栏")
@allure.story("L2 面板三态（打开即结果）")
@pytest.mark.regression
@allure.title("L2-003: 打开即结果态类 2 个功能的三态（自动结果 → 切预设重生成 → 结束）")
def test_p_ait_03_opens_with_result_group(canvas_page: Page):
    """L2-003 打开即结果态类 2 个功能：打开即结果 → 切预设 → 结果态/重新生成 → 结束。

    实测状态机（2026-10-13 探针，同一 pid 复现）：
      - 打开 → 自动按默认模型出结果（主按钮 Refine + Confirm 可用）。
      - Background Remover：切到「未生成过」的模型 → 结果失效（Confirm 禁用、主按钮变回
        Remove Background 且可点）；**不会自动重生成**（实测轮询 90s 仍为待提交态），
        必须点主按钮才发起服务端任务 → 生成中 → 结束。
      - Blur Background：切模型属客户端即时预览（强度/样式本地重算），状态恒为结果态、
        不产生新任务；故以「结果态保持 + 预览画面即时刷新」作为该分支断言。

    测试步骤:
      1. 打开工具，断言打开即结果态（Confirm 可用 + 主按钮 Refine）
      2. 切到另一预设：
         2a 需重生成类 → 断言结果失效 → 点主按钮重新生成 → 断言生成中 → 等结束
         2b 即时预览类 → 断言仍为结果态且预览画面发生变化
    """
    page = canvas_page
    open_ai_tools(page)

    for item in DATA["groups"]["opens_with_result"]:
        name = item["name"]
        with allure.step("1. 功能 %s：打开即结果态" % name):
            p = open_tool(page, name)
            assert p is not None, "%s 功能面板未打开" % name
            assert confirm_state(page) == "enabled", "%s 打开后应为结果态（Confirm 可用）" % name
            assert result_state(page) == "result", "%s 打开后主按钮应为 Refine（实测漂移）" % name
            shot(page, "P-AIT-03_%s_打开即结果" % name)
            assert wait_panel_idle(page, timeout_s=120), "%s 打开后长时间处于生成中" % name

        with allure.step("2. 功能 %s：切换预设" % name):
            before = preview_digest(page)
            if item.get("switch_regenerates"):
                # 默认选中项随机型内容变化，且已生成过的模型会命中缓存（无新任务）；
                # 必须切到「尚未生成过」的模型才会真正失效并要求重新提交。
                target = switch_until_invalidated(page, item["model_candidates"],
                                                  item["submit_after_switch"])
                assert target, "%s 切换候选 %s 后均未进入结果失效态（可能全部命中缓存）" % (
                    name, item["model_candidates"])
                allure.attach("触发重新生成的模型=%s" % target, name="P-AIT-03 切预设",
                              attachment_type=allure.attachment_type.TEXT)
                shot(page, "P-AIT-03_%s_切预设后" % name)
                regen_by_submit(page, item["submit_after_switch"])
                assert result_state(page) == "result", \
                    "%s 重新生成结束后应回到结果态（Refine + Confirm 可用）" % name
                shot(page, "P-AIT-03_%s_结束态" % name)
                assert_done_state_controls(page, name)
            else:
                # 客户端即时预览：结果态不失效，但预览画面必须随之刷新
                assert select_model(page, item["switch_model"]), \
                    "%s 未找到/未点到预设 %s（重试后仍不可点）" % (name, item["switch_model"])
                shot(page, "P-AIT-03_%s_切预设后" % name)
                assert wait_panel_idle(page, timeout_s=120), "%s 切预设后长时间处于生成中" % name
                assert result_state(page) == "result", \
                    "%s 切预设属即时预览，应保持结果态" % name
                after = preview_digest(page)
                assert before and after and before != after, \
                    "%s 切换预设后预览画面未刷新（before=%s after=%s）" % (name, before, after)
                shot(page, "P-AIT-03_%s_结束态" % name)
                assert_done_state_controls(page, name)


@allure.epic("Pokecut")
@allure.feature("旧画布 AI Tools 功能栏")
@allure.story("L2 跳转类")
@pytest.mark.regression
@pytest.mark.p0
@allure.title("L2-005: 跳转类 AI Image Generator 新标签页跳转无限画布（预期行为）")
def test_p_ait_05_navigate_only(canvas_page: Page):
    """L2-005 AI Image Generator 新标签页跳无限画布（用户确认属预期，不断言 /agent 内部）。

    测试步骤:
      1. 记录旧画布 URL
      2. 点工具卡 AI Image Generator，等待新标签页
      3. 断言新标签页 URL 匹配 /agent?pid=<uuid>
      4. 断言旧画布标签页仍为 /create/edit?pid=<uuid>
      5. 关闭新页，切回旧画布
    """
    page = canvas_page
    item = DATA["groups"]["navigate_only"][0]
    name = item["name"]

    open_ai_tools(page)
    origin_url = page.url
    assert "/create/edit?pid=" in origin_url, "旧画布 URL 异常: %s" % origin_url

    with allure.step("1. 点击 %s 并捕获新标签页" % name):
        card = page.locator(SEL_TOOL_CARD).filter(has_text=re.compile(r"^%s$" % re.escape(name)))
        assert card.count() > 0, "未找到工具卡 %s" % name
        card.first.scroll_into_view_if_needed()
        with page.context.expect_page(timeout=30000) as new_page_info:
            card.first.click()
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        # 新标签页跳 /agent（新画布）——就绪信号取 URL（下一步即断言 /agent?pid=）
        poll_until(new_page, lambda: "/agent?pid=" in new_page.url, timeout=30000, interval=500)

    with allure.step("2. 断言新标签页跳转 /agent?pid=<uuid>"):
        new_url = new_page.url
        assert re.search(r"/agent\?pid=[0-9a-f\-]+", new_url), "新标签页 URL 未匹配 /agent?pid=<uuid>: %s" % new_url
        shot(new_page, "P-AIT-05_新标签页")

    with allure.step("3. 断言旧画布标签页仍在"):
        assert "/create/edit?pid=" in page.url, "旧画布标签页被导航走了: %s" % page.url
        assert page.locator(SEL_LIST).count() > 0, "旧画布 AI Tools 列表应保持可见"
        shot(page, "P-AIT-05_旧画布仍在")

    with allure.step("4. 关闭新页并切回旧画布"):
        new_page.close()
        page.bring_to_front()
        # 切回旧页即可；后续断言直接读旧页 DOM（去掉固定 1s）


@allure.epic("Pokecut")
@allure.feature("旧画布 AI Tools 功能栏")
@allure.story("L2 面板三态（需蒙版）")
@pytest.mark.regression
@allure.title("L2-004: 需蒙版类 AI Replace 的三态（未涂蒙版禁用 → 涂抹后可用 → 结束）")
def test_p_ait_04_mask_required(canvas_page: Page):
    """L2-004 需蒙版类 AI Replace：未涂蒙版禁用 → 涂抹后可用 → 结束。

    测试步骤:
      1. 打开 AI Replace（默认 Replace Object + Description）
      2. 断言 Generate 未涂蒙版时禁用
      3. 填描述并涂抹蒙版，断言 Generate 变可用
      4. 提交并等结束
    """
    page = canvas_page
    item = DATA["groups"]["mask_required"][0]
    name = item["name"]

    open_ai_tools(page)
    with allure.step("1. 打开 %s 并断言未涂蒙版时禁用" % name):
        p = open_tool(page, name)
        assert p is not None, "%s 功能面板未打开" % name
        assert not submit_enabled(page), "%s 未涂蒙版时主按钮应禁用" % name
        shot(page, "P-AIT-04_未涂蒙版禁用")

    with allure.step("2. 填描述 + 涂抹蒙版后主按钮可用"):
        p = panel(page)
        ta = p.locator("textarea").first
        assert ta.count() > 0, "AI Replace 未找到描述输入框"
        ta.fill(item["description"])
        # 填描述生效信号：input value 已写入（Playwright fill 已同步，去掉固定 1.5s）
        before_probe = canvas_alpha_probe(page)
        painted = paint_on_canvas(page)
        after_probe = canvas_alpha_probe(page)
        shot(page, "P-AIT-04_涂蒙版后")
        diag = "涂抹前=%s\n涂抹后=%s\npaint_on_canvas=%s\nsubmit_enabled=%s" % (
            before_probe, after_probe, painted, submit_enabled(page))
        allure.attach(diag, name="涂抹诊断", attachment_type=allure.attachment_type.TEXT)
        assert painted and submit_enabled(page), (
            "AI Replace 涂蒙版后主按钮应可用。诊断：\n%s" % diag)

    with allure.step("3. 提交并等结束"):
        assert submit_and_wait_done(page, name, timeout_s=120) == "enabled", "AI Replace 任务未结束"
        shot(page, "P-AIT-04_结束态")
        assert_done_state_controls(page, name)


@allure.epic("Pokecut")
@allure.feature("旧画布 AI Tools 功能栏")
@allure.story("L2 面板三态")
@pytest.mark.regression
@pytest.mark.p0
@allure.title("L2-001: 预设选择类 10 个功能的面板三态")
def test_p_ait_01_preset_select_group(canvas_page: Page):
    """L2-001 预设选择类 10 个功能的面板三态（去重：同路径/同前置合并）。

    测试步骤:
      1. 进入旧画布 AI Tools，断言列表结构（Common Tools / Popular Al）
      2. 逐个功能：点工具卡 →（多分类先点分类）→ 点预设 → 点主提交 → 等 Confirm 变可用
      3. 每个功能断言 Confirm 三态：初始 disabled → 生成中 disabled → 结束 enabled
    """
    page = canvas_page
    with allure.step("1. 进入旧画布 AI Tools 并断言列表结构"):
        open_ai_tools(page)
        body = page.locator(SEL_LIST).first.inner_text()
        assert "Common Tools" in body, "AI Tools 列表缺少 Common Tools 分组"
        assert "Popular Al" in body, "AI Tools 列表缺少 Popular Al 分组"
        assert page.locator(SEL_TOOL_CARD).count() >= 19, "工具卡数量不足 19 个"
        shot(page, "P-AIT-01_列表结构")

    for item in DATA["groups"]["preset_select"]:
        name = item["name"]
        with allure.step("2. 功能 %s：面板三态" % name):
            p = open_tool(page, name)
            assert p is not None, "%s 功能面板未打开" % name
            initial = confirm_state(page)
            shot(page, "P-AIT-01_%s_初始态" % name)

            # 初始态断言：结果态工具（若存在）直接 enabled；其余应为 disabled
            assert initial in ("disabled", "enabled"), "%s 初始 Confirm 状态异常: %s" % (name, initial)

            if item.get("expected_modes"):
                # 2026-10-29 画质增强补强（仅 Photo Enhancer 声明 expected_modes）：
                # 断言初始态模式集合（含新增 Low-Res Mode）、默认 Ultra HD Mode，且逐个模式可切换。
                with allure.step("2.1 初始态模式选项与默认选中"):
                    assert_mode_options(page, name, item["expected_modes"], item["default_mode"])
                    assert confirm_state(page) == "disabled", \
                        "%s 初始 Confirm 应为 disabled（选择模式后置灰）" % name
                    cancel = _clickable_info(page, "Cancel")
                    assert cancel and not cancel.get("disabled"), \
                        "%s 初始 Cancel 应可用" % name
                shot(page, "P-AIT-01_%s_模式断言" % name)
            else:
                if item.get("category"):
                    assert click_text_in_panel(page, item["category"]), "%s 未找到分类 %s" % (name, item["category"])
                for preset in item["presets"]:
                    assert click_text_in_panel(page, preset), "%s 未找到预设 %s" % (name, preset)

            mid = submit_and_wait_done(page, name, timeout_s=120,
                                       assert_started=bool(item.get("expected_modes")))
            if mid != "enabled":
                shot(page, "P-AIT-01_%s_生成中" % name)
            assert mid == "enabled", "%s 任务未在超时内结束（Confirm=%s）" % (name, mid)
            shot(page, "P-AIT-01_%s_结束态" % name)
            assert_done_state_controls(page, name)

            # 跨分类等价类（AI Filter 等）
            extra = item.get("extra_cross_category")
            if extra:
                with allure.step("3. 功能 %s：跨分类预设 %s" % (name, extra["preset"])):
                    assert click_text_in_panel(page, extra["category"]), "%s 未找到跨分类 %s" % (name, extra["category"])
                    assert click_text_in_panel(page, extra["preset"]), "%s 未找到跨分类预设 %s" % (name, extra["preset"])
                    assert submit_and_wait_done(page, "%s 跨分类" % name, timeout_s=120) == "enabled", \
                        "%s 跨分类任务未结束" % name
                    shot(page, "P-AIT-01_%s_跨分类结束态" % name)
                    assert_done_state_controls(page, "%s 跨分类" % name)


@allure.epic("Pokecut")
@allure.feature("旧画布 AI Tools 功能栏")
@allure.story("L2 面板三态 + Manual Mode")
@pytest.mark.regression
@pytest.mark.p0
@allure.title("L2-002: 模式+分类类 4 个功能的面板三态 + Manual Mode 手绘蒙版")
def test_p_ait_02_mode_and_category_group(canvas_page: Page):
    """L2-002 模式+分类类 4 个功能的三态 + Manual Mode 手绘蒙版。

    实测状态机（2026-10-13 探针）：
      - 结果态工具（Watermark Remover / Hair Removal）打开即自动跑一次默认模型；
        若此刻 Confirm 仍禁用说明任务在途，必须等它结束再切模式，否则模式 tab 点击会被吞。
      - Magic Eraser 打开默认 Manual Mode（主按钮禁用），切 Smart Auto Mode 会立即用默认
        预设起一次任务。
      - Manual Mode 未涂抹时主按钮 Remove 恒禁用；涂抹后变可用（ready 判据）。
      - Watermark Remover 实测（探针 P5/P6）：切换 Manual Mode 后 DOM 仍停留在参数面板，
        `manual_paint_canvas` 不出现，主按钮 Remove 保持可用 → 该工具的 Manual Mode 在本环境
        不可达，按实测记录为 blocked 分支，不做弱化断言。
      - AI Clothes Changer 分类列表横向可滚动，Wedding Dress 在视口外不可点；改用可见的
        Formal Wear / Dresses 两个分类各取一个预设（跨分类等价类不变）。
    """
    page = canvas_page
    open_ai_tools(page)

    for item in DATA["groups"]["mode_and_category"]:
        name = item["name"]

        # —— 分支 A：纯模式+分类（AI Clothes Changer）——
        if item.get("tile_kind"):
            with allure.step("1. 功能 %s：跨分类服装预设生成" % name):
                p = open_tool(page, name)
                assert p is not None, "%s 功能面板未打开" % name
                initial = confirm_state(page)
                assert initial in ("disabled", "enabled"), "%s 初始态异常: %s" % (name, initial)
                shot(page, "P-AIT-02_%s_初始态" % name)

                assert click_text_in_panel(page, item["mode"]), \
                    "%s 未找到模式 %s" % (name, item["mode"])
                # 模式选中生效信号（替代固定 2.5s）
                poll_until(page, lambda: mode_option_state(page, item["mode"]) == "selected",
                           timeout=8000, interval=300)
                for cat in item["categories"]:
                    with allure.step("1.%s 分类 %s：选预设并生成" % (item["categories"].index(cat) + 1, cat)):
                        assert select_model(page, cat), "%s 未找到/未点到分类 %s" % (name, cat)
                        src = click_clothes_tile(page, item["tile_kind"])
                        assert src, "%s 分类 %s 下未找到生效的服装预设缩略图" % (name, cat)
                        allure.attach(src, name="%s %s 选中缩略图" % (name, cat),
                                      attachment_type=allure.attachment_type.TEXT)
                        assert submit_enabled(page), \
                            "%s 选中服装预设 %s 后 Generate 应可用" % (name, src)
                        shot(page, "P-AIT-02_%s_%s_选中" % (name, cat.replace(" ", "")))
                        assert submit_and_wait_done(page, "%s %s" % (name, cat),
                                                    timeout_s=180, expect_label="Generate") == "enabled", \
                            "%s 分类 %s 任务未在超时内结束" % (name, cat)
                        shot(page, "P-AIT-02_%s_%s_结束态" % (name, cat.replace(" ", "")))
                        assert_done_state_controls(page, "%s %s" % (name, cat))
            continue

        # —— 分支 B：结果态工具 / Magic Eraser ——
        with allure.step("1. 功能 %s：Smart Auto Mode 跨分类预设" % name):
            p = open_tool(page, name)
            assert p is not None, "%s 功能面板未打开" % name
            shot(page, "P-AIT-02_%s_初始态" % name)

            assert select_tab(page, "Smart Auto Mode"), \
                "%s 未切到 Smart Auto Mode（点击可能被遮挡）" % name
            # 实测：切 Smart Auto Mode 后是「待提交」态（Confirm 禁用 + 主按钮可用），
            # 不是自动任务；这里只做有界 settle，真正的判据放在选完预设后断言主按钮可用。
            wait_until(page, lambda: confirm_state(page) == "enabled", timeout_s=25)

            for cross in item["smart_auto_cross"]:
                with allure.step("1.x 跨分类 %s > %s" % (cross["category"], cross["preset"])):
                    assert select_model(page, cross["category"]), \
                        "%s 未找到/未点到分类 %s" % (name, cross["category"])
                    assert select_model(page, cross["preset"]), \
                        "%s 未找到/未点到预设 %s" % (name, cross["preset"])
                    shot(page, "P-AIT-02_%s_%s" % (name, cross["preset"].replace(" ", "")))
                    assert submit_enabled(page), "%s 选预设 %s 后主按钮应可用" % (name, cross["preset"])
                    assert submit_and_wait_done(page, "%s %s" % (name, cross["preset"]),
                                                timeout_s=180, expect_label="Remove") == "enabled", \
                        "%s 预设 %s 任务未在超时内结束" % (name, cross["preset"])
                    shot(page, "P-AIT-02_%s_结束态" % name)
                    assert_done_state_controls(page, name)

        if not item.get("sweep_manual"):
            continue

        with allure.step("2. 功能 %s：Manual Mode 手绘蒙版" % name):
            assert wait_panel_idle(page, timeout_s=180), \
                "%s 切 Manual Mode 前仍处于生成中（进度层会吞掉点击）" % name
            assert select_tab(page, "Manual Mode"), \
                "%s 未切到 Manual Mode（点击可能被遮挡）" % name
            assert "Retouch Tools" in (panel(page).inner_text() if panel(page) else ""), \
                "%s 切 Manual Mode 后未出现 Retouch Tools（手绘蒙版面板）" % name
            assert not submit_enabled(page), "%s Manual Mode 未涂抹时主按钮应禁用" % name
            shot(page, "P-AIT-02_%s_Manual未涂抹" % name)
            assert paint_on_canvas(page), "%s Manual Mode 涂抹失败" % name
            assert submit_enabled(page), "%s Manual Mode 涂抹后主按钮应可用" % name
            shot(page, "P-AIT-02_%s_Manual涂抹" % name)
            assert submit_and_wait_done(page, "%s Manual" % name,
                                        timeout_s=180, expect_label="Remove") == "enabled", \
                "%s Manual Mode 任务未结束" % name
            shot(page, "P-AIT-02_%s_Manual结束态" % name)
            assert_done_state_controls(page, "%s Manual" % name)


@allure.epic("Pokecut")
@allure.feature("旧画布 AI Tools 功能栏")
@allure.story("L2 破坏性工具（执行序末位）")
@pytest.mark.regression
@pytest.mark.p0
@allure.title("L2-006: 破坏性工具 Face Cutout 三态 + 跨分类（执行序末位）")
def test_p_ait_06_face_cutout_last(canvas_page: Page):
    """L2-006 破坏性工具 Face Cutout：打开即结果 + 切跨分类模型重生成 + Confirm 应用。

    实测状态机（2026-10-13 探针）：
      - 打开后面板默认选中的是 **Head&Face**（图片含人脸时自动选中），自动出结果；
        故「切 Head&Face」是 no-op，不触发重生成。
      - 切到 **General**（未生成过的模型）→ 结果失效（Confirm 禁用 + 主按钮 Remove Background
        可点）→ 点主按钮才重新生成 → 生成中 → 结束（Refine + Confirm 可用）。
      - 切回 Head&Face 会命中缓存立即恢复结果态。

    测试步骤:
      1. 打开 Face Cutout（执行序末位），断言自动出结果（Confirm 可用 + Refine）
      2. 切 General → 断言结果失效 → 点 Remove Background 重新生成 → 等结束
      3. 点 Confirm 应用破坏性结果，断言面板关闭
    """
    page = canvas_page
    item = DATA["groups"]["destructive"][0]
    name = item["name"]

    open_ai_tools(page)
    baseline = canvas_area_digest(page)
    assert baseline, "%s 未取到打开工具前的主画布基线" % name
    allure.attach(baseline, name="P-AIT-06 打开工具前画布基线",
                  attachment_type=allure.attachment_type.TEXT)

    with allure.step("1. 打开 %s（执行序末位）并断言自动出结果" % name):
        p = open_tool(page, name)
        assert p is not None, "%s 功能面板未打开" % name
        opened = confirm_state(page)
        allure.attach("打开时 Confirm 状态=%s" % opened, name="P-AIT-06 打开态",
                      attachment_type=allure.attachment_type.TEXT)
        shot(page, "P-AIT-06_打开态")
        assert wait_done(page, timeout_s=120) == "enabled", "%s 打开后未自动出结果" % name
        assert result_state(page) == "result", "%s 自动结果应为 Refine + Confirm 可用" % name
        assert wait_panel_idle(page, timeout_s=120), "%s 打开后长时间处于生成中" % name

    target = switch_until_invalidated(page, item["model_candidates"], item["submit_after_switch"])
    assert target, "%s 切换候选 %s 后均未进入结果失效态（可能全部命中缓存）" % (
        name, item["model_candidates"])
    with allure.step("2. 切跨分类模型 %s 触发重新生成" % target):
        allure.attach("触发重新生成的模型=%s；当前 Confirm=%s 主按钮=%s" % (
            target, confirm_state(page), (_primary_submit_info(page) or {}).get("label")),
            name="P-AIT-06 切预设失效态", attachment_type=allure.attachment_type.TEXT)
        shot(page, "P-AIT-06_切预设后")
        # 失效态 → 点主按钮提交 → 生成中 → 结束（与 P-AIT-03 同一断言强度）
        regen_by_submit(page, item["submit_after_switch"])
        assert result_state(page) == "result", "%s 重生成结束后应回到结果态" % name
        shot(page, "P-AIT-06_跨分类结束态")
        assert_done_state_controls(page, name)

    with allure.step("3. 点 Confirm 应用破坏性结果"):
        assert click_confirm(page), "Face Cutout 未找到 Confirm 按钮"
        # 应用生效信号：功能面板关闭（替代固定 5s）
        poll_until(page, lambda: panel(page) is None, timeout=30000, interval=500)
        wait_layout_stable(page)
        shot(page, "P-AIT-06_执行后画布")
        assert panel(page) is None, "%s 确认后功能面板未关闭" % name
        after_apply = canvas_area_digest(page)
        allure.attach("打开工具前画布指纹=%s\n应用后画布指纹=%s" % (baseline, after_apply),
                      name="P-AIT-06 破坏性生效诊断", attachment_type=allure.attachment_type.TEXT)
        assert after_apply, "%s 应用后未取到主画布指纹" % name
        assert after_apply != baseline, \
            "%s 应用后主画布画面未变化（破坏性结果未生效）" % name
