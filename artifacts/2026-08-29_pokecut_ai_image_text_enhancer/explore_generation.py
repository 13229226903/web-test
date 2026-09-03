# -*- coding: utf-8 -*-
import time, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Test\web-test")
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
TASK = ROOT / "artifacts" / "2026-08-29_pokecut_ai_image_text_enhancer"
SHOTS = TASK / "shots"
EMAIL = "450832596@qq.com"
CODE = "123456"
out = []

def shot(page, name):
    p = SHOTS / f"{name}.png"
    page.screenshot(path=str(p), full_page=False)
    return str(p)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US")
    page = ctx.new_page()
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    page.locator('h1:has-text("Enhance Text in Image to 8K Online Free")').wait_for(state="visible", timeout=30000)

    # login
    if page.locator('input[type="email"]').count() == 0:
        try:
            page.locator('button:has-text("Log in")').first.click(timeout=10000)
        except Exception:
            page.get_by_text("Log in", exact=True).first.click(timeout=10000)
        page.wait_for_timeout(1500)
    page.locator('input[type="email"]').first.fill(EMAIL, timeout=10000)
    page.locator('input[placeholder="Verification Code"]').first.fill(CODE, timeout=10000)
    page.evaluate("""() => { for (const el of document.querySelectorAll('button')) { const t=(el.innerText||'').trim(); const r=el.getBoundingClientRect(); if ((t==='Log in'||t==='Sign up') && r.width>100 && r.height>20){ el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true; } } return false; }""")
    page.wait_for_timeout(9000)
    if "/create" in page.url:
        page.goto(URL, timeout=120000, wait_until="domcontentloaded")
        page.wait_for_timeout(7000)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(o => { const bg=window.getComputedStyle(o).backgroundColor; if (bg && (bg.includes('0.3')||bg.includes('0.5'))) o.remove(); }); }""")
    page.wait_for_timeout(500)
    out.append({"step":"after_login", "url": page.url})
    shot(page, "gen_00_after_login")

    page.set_input_files("#singleUploadInput", str(ROOT/"test_images"/"1K.jpg"), timeout=25000)
    page.wait_for_timeout(15000)
    page.locator('[data-effect="enhance_text"]').first.wait_for(state="visible", timeout=20000)
    out.append({"step":"after_upload", "cost_state": page.locator('[data-text-enhance-total-cost]').first.get_attribute("data-text-enhance-cost-state") if page.locator('[data-text-enhance-total-cost]').count() else None})
    shot(page, "gen_01_after_upload")

    page.locator('[data-enhance-action="desktop-primary"]').first.click(timeout=10000)
    out.append({"step":"after_click_generate"})
    for i in range(18):
        page.wait_for_timeout(5000)
        body = page.locator("body").inner_text()
        has_pct = bool(re.search(r"\b\d{1,3}%\b", body))
        has_result = all(t in body for t in ["Continue Enhancing", "Edit More", "Download"])
        html = page.locator("body").evaluate("el => el.innerHTML")
        has_purchase = "purchase-gift-modal" in html
        out.append({"t": (i+1)*5, "url": page.url, "has_pct": has_pct, "has_result": has_result, "has_purchase": has_purchase, "body_tail": body[-300:]})
        if has_result or has_purchase:
            shot(page, f"gen_02_state_{i}")
            break
        if i in (3, 8, 14):
            shot(page, f"gen_02_state_{i}")
    shot(page, "gen_03_final")
    ctx.close(); b.close()

(TASK / "explore_generation_v3.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))

