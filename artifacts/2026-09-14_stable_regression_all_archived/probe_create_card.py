"""定位 /create 页 Start from a Photo 卡片的实际 DOM（L5-001 失败定位）。"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path("artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture")

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = ctx.new_page()
    page.goto(f"{BASE}/create", wait_until="networkidle", timeout=120000)
    page.wait_for_timeout(4000)
    loc = page.locator("div.cursor-pointer:has(p:text-is('Start from a Photo'))")
    print("strict-card locator count:", loc.count(), flush=True)
    info = page.evaluate("""() => {
        const out = [];
        const walk = (el, depth) => {
            if (depth > 8) return;
            for (const c of el.children) {
                const t = (c.innerText || '').trim();
                if (t === 'Start from a Photo') {
                    out.push({tag: c.tagName, cls: c.className, parentCls: c.parentElement.className,
                              parentTag: c.parentElement.tagName, depth});
                }
                walk(c, depth + 1);
            }
        };
        walk(document.body, 0);
        return out;
    }""")
    print("exact-text nodes:", json.dumps(info, ensure_ascii=False, indent=2)[:2000], flush=True)
    node = page.get_by_text("Start from a Photo", exact=True)
    print("get_by_text count:", node.count(), flush=True)
    try:
        node.first.scroll_into_view_if_needed(timeout=8000)
        page.wait_for_timeout(1200)
        page.screenshot(path=str(OUT / "create_start_from_photo_card.png"), full_page=False)
        print("scrolled + shot", flush=True)
    except Exception as exc:
        print("scroll failed:", exc, flush=True)
    ctx.close()
    browser.close()