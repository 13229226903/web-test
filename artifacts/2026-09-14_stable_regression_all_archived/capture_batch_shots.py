"""复现 batch 页删除按钮文案现场并截图。"""
import json
import re
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path("artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture")
OUT.mkdir(parents=True, exist_ok=True)
EMAIL = "450832596@qq.com"
CODE = "123456"


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


info = {}
with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = ctx.new_page()
    page.route("**/gateway/pokecut/api/**", api_bypass_handler)
    page.goto(BASE, timeout=90000)
    page.wait_for_timeout(2500)
    page.get_by_text("Log in", exact=True).first.click()
    page.wait_for_timeout(2000)
    page.locator('input[type="email"]').fill(EMAIL)
    page.locator('input[placeholder="Verification Code"]').fill(CODE)
    page.evaluate("""() => {
        const bs = Array.from(document.querySelectorAll('button'))
            .filter(b => b.offsetWidth > 200 && b.getBoundingClientRect().y > 700 && b.textContent.trim() === 'Log in');
        if (bs.length) bs[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
    }""")
    page.wait_for_timeout(15000)
    print("logged in, url =", page.url, flush=True)

    page.goto(f"{BASE}/batch", timeout=90000)
    page.wait_for_timeout(2500)
    page.screenshot(path=str(OUT / "batch_landing.png"), full_page=False)
    try:
        with page.expect_file_chooser(timeout=20000) as fc:
            page.get_by_role("button", name="Upload Images").click()
        fc.value.set_files(["test_images/1K.jpg", "test_images/无人脸.jpg"])
        expect(page).to_have_url(re.compile(r"/batch-edit/edit\?pid="), timeout=60000)
        page.wait_for_timeout(6000)
        print("entered", page.url, flush=True)
    except Exception as exc:
        print("upload flow failed:", exc, flush=True)

    page.screenshot(path=str(OUT / "batch_edit_with_images.png"), full_page=False)

    texts = page.get_by_role("button").all_inner_texts()
    info["buttons"] = sorted({t.strip() for t in texts if t.strip()})
    body = page.locator("body").inner_text()[:6000]
    info["body_has_Delect"] = "Delect" in body
    info["body_has_Delete"] = "Delete" in body
    for m in re.finditer(r"[A-Za-z]{3,10}", body):
        pass
    print("body_has_Delect:", info["body_has_Delect"], "| body_has_Delete:", info["body_has_Delete"], flush=True)
    print("buttons:", json.dumps(info["buttons"], ensure_ascii=False)[:2000], flush=True)

    # 尝试选中一张图，让删除按钮出现在右侧工具栏
    try:
        page.mouse.click(960, 540)
        page.wait_for_timeout(2500)
        page.screenshot(path=str(OUT / "batch_selected_image.png"), full_page=False)
        sel_texts = sorted({t.strip() for t in page.get_by_role("button").all_inner_texts() if t.strip()})
        info["buttons_after_select"] = sel_texts
        print("buttons after select:", json.dumps(sel_texts, ensure_ascii=False)[:2000], flush=True)
    except Exception as exc:
        print("select failed:", exc, flush=True)

    (OUT / "batch_capture.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    ctx.close()
    browser.close()
print("done", flush=True)