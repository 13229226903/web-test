# -*- coding: utf-8 -*-
import time, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Test\web-test")
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
TASK = ROOT / "artifacts" / "2026-08-29_pokecut_ai_image_text_enhancer"
EMAIL = "450832596@qq.com"; CODE = "123456"
out = []

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width":1440,"height":1000}, locale="en-US")
    page = ctx.new_page()
    page.on("console", lambda m: out.append({"console": m.type+": "+m.text[:160]}) if m.type in ("error","warning") and any(k in m.text for k in ["authToken","404","failed","error","purchase","credit"]) else None)
    page.goto(URL, timeout=120000, wait_until="domcontentloaded"); page.wait_for_timeout(7000)
    page.locator('h1:has-text("Enhance Text in Image to 8K Online Free")').wait_for(state="visible", timeout=30000)
    page.click(".debug-float-btn", timeout=10000); page.wait_for_timeout(800)
    page.locator(".environment-options .action-btn", has_text="预部署").click(timeout=10000); page.wait_for_timeout(7000)
    if page.locator('input[type="email"]').count() == 0:
        try: page.locator('button:has-text("Log in")').first.click(timeout=10000)
        except Exception: page.get_by_text("Log in", exact=True).first.click(timeout=10000)
        page.wait_for_timeout(1500)
    page.locator('input[type="email"]').first.fill(EMAIL, timeout=10000)
    page.locator('input[placeholder="Verification Code"]').first.fill(CODE, timeout=10000)
    page.evaluate("""() => { for (const el of document.querySelectorAll('button')) { const t=(el.innerText||'').trim(); const r=el.getBoundingClientRect(); if ((t==='Log in'||t==='Sign up') && r.width>100 && r.height>20){ el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true; } } return false; }""")
    page.wait_for_timeout(9000)
    if "/create" in page.url:
        page.goto(URL, timeout=120000, wait_until="domcontentloaded"); page.wait_for_timeout(7000)
    page.keyboard.press("Escape"); page.wait_for_timeout(500)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(o => { const bg=window.getComputedStyle(o).backgroundColor; if (bg && (bg.includes('0.3')||bg.includes('0.5'))) o.remove(); }); }""")
    page.wait_for_timeout(500)

    page.set_input_files("#singleUploadInput", str(ROOT/"test_images"/"文字测例.jpg"), timeout=25000); page.wait_for_timeout(15000)
    page.locator('[data-effect="enhance_text"]').first.wait_for(state="visible", timeout=20000)
    if page.locator('[data-effect="enhance_text"]').first.get_attribute("aria-pressed") == "true":
        page.locator('[data-effect="enhance_text"]').first.click(timeout=10000); page.wait_for_timeout(800)
    if page.locator('[data-effect="remove_glare"]').first.get_attribute("aria-pressed") != "true":
        page.locator('[data-effect="remove_glare"]').first.click(timeout=10000); page.wait_for_timeout(800)
    out.append({"step":"before_generate", "primary": page.locator('[data-enhance-action="desktop-primary"]').first.inner_text().strip().replace("\n"," ")})
    box = page.locator('[data-enhance-action="desktop-primary"]').first.bounding_box()
    page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
    for i in range(20):
        page.wait_for_timeout(6000)
        body = page.locator("body").inner_text()
        html = page.locator("body").evaluate("el => el.innerHTML")
        out.append({"t":(i+1)*6, "has_result": all(t in body for t in ["Continue Enhancing","Edit More"]), "has_purchase": "purchase-gift-modal" in html, "has_before": "Before" in body, "has_now": "Now" in body, "tail": body[-200:]})
        if all(t in body for t in ["Continue Enhancing","Edit More"]) or "purchase-gift-modal" in html:
            page.screenshot(path=str(TASK/"shots"/"L2_002_non_enhance_result.png"), full_page=False)
            break
    ctx.close(); b.close()

(TASK / "investigate_l2_002b_v3.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
