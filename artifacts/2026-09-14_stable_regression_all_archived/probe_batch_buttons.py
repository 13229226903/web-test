"""探测 batch 编辑页顶部按钮的可访问名 / aria-label（删除按钮文案核对）。"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
PID = "4c951fbf-9797-4472-a63d-79f4f0fe8db3"
OUT = Path("artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture")


def api_bypass_handler(route):
    req = route.request
    if req.method == "OPTIONS":
        route.fulfill(status=204, headers={"Access-Control-Allow-Origin": "*",
                                           "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                                           "Access-Control-Allow-Headers": "*"})
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


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = ctx.new_page()
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    page.goto(BASE, timeout=90000)
    page.wait_for_timeout(2000)
    page.get_by_text("Log in", exact=True).first.click()
    page.wait_for_timeout(1500)
    page.locator('input[type="email"]').fill("450832596@qq.com")
    page.locator('input[placeholder="Verification Code"]').fill("123456")
    page.evaluate("""() => {
        const bs = Array.from(document.querySelectorAll('button'))
            .filter(b => b.offsetWidth > 200 && b.getBoundingClientRect().y > 700 && b.textContent.trim() === 'Log in');
        if (bs.length) bs[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
    }""")
    page.wait_for_timeout(12000)

    page.goto(f"{BASE}/batch-edit/edit?pid={PID}#", timeout=90000)
    page.wait_for_timeout(8000)
    page.screenshot(path=str(OUT / "batch_reopen_pid.png"), full_page=False)

    info = page.evaluate("""() => {
        return Array.from(document.querySelectorAll('button')).map(b => ({
            text: (b.innerText || '').trim(),
            aria: b.getAttribute('aria-label'),
            title: b.getAttribute('title'),
            cls: b.className,
            y: Math.round(b.getBoundingClientRect().y),
            x: Math.round(b.getBoundingClientRect().x),
            html: b.innerHTML.slice(0, 120),
        }));
    }""")
    interesting = [i for i in info if i["y"] < 80]
    print(json.dumps(interesting, ensure_ascii=False, indent=2)[:4000], flush=True)
    print("---- any Delect/Delete anywhere ----", flush=True)
    print(json.dumps([i for i in info if "lect" in (i["text"] + str(i["aria"]) + str(i["title"]))], ensure_ascii=False), flush=True)
    (OUT / "batch_top_buttons.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    ctx.close()
    browser.close()