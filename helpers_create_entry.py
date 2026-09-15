# -*- coding: utf-8 -*-
"""进入 /create 页的公共处理：关闭全新会话弹出的 VIP 促销/定价弹窗。

2026-09-14 Playwright MCP 复探结论（见 page_map/pokecut/create_ai_tools_v2.yaml）：
全新匿名会话进入 /create 会先弹出 `.purchase-gift-modal`（$1 USD 限时优惠），
点掉第一层后还会出现第二层「Premium Plan / Credits Purchase」定价弹窗，
必须连点两次关闭控件后，Trending Tools 入口卡片才恢复可点击。
"""
from playwright.sync_api import Page

PROMO_MODAL = ".purchase-gift-modal"
PROMO_CLOSE = ".purchase-gift-modal img[src*='colos_pop_btn_close']"


def dismiss_create_promo(page: Page, max_clicks: int = 3, wait_ms: int = 1200) -> int:
    """关闭 /create 促销/定价弹窗，返回实际点击关闭控件的次数（0 表示未弹窗）。"""
    clicked = 0
    for _ in range(max_clicks):
        close = page.locator(PROMO_CLOSE).first
        if close.count() == 0:
            break
        try:
            if not page.locator(PROMO_MODAL).first.is_visible():
                break
            close.click(force=True, timeout=5000)
            clicked += 1
            page.wait_for_timeout(wait_ms)
        except Exception:
            break
    return clicked