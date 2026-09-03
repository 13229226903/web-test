# -*- coding: utf-8 -*-
import time, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Test\web-test")
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
TASK = ROOT / "artifacts" / "2026-08-29_pokecut_ai_image_text_enhancer"
EMAIL = "450832596@qq.com"; CODE = "123456"
out = []
reqs = []

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width":1440,"height":1000}, locale="en-US")
    page = ctx.new_page()
    page.on("console", lambda m: out.append({"console": m.type+": "+m.text[:200]}) if m.type in ("error","warning") else None)
    page.on("request", lambda r: reqs.append({"url": r.url, "method": r.method}) if any(k in r.url for k in ["pokecut/api","textenhance","enhance","comfyui","gateway"]) else None)
    page.on("response", lambda r: reqs.append({"resp": r.status, "url": r.url}) if any(k in r.url for k in ["pokecut/api","textenhance","enhance","comfyui","gateway"]) else None)

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
    page.keyboard.press("Escape"); page.wait_for_timeout(500)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(o => { const bg=window.getComputedStyle(o).backgroundColor; if (bg && (bg.includes('0.3')||bg.includes('0.5'))) o.remove(); }); }""")
    page.wait_for_timeout(500)
    body = page.locator("body").inner_text()
    out.append({"step":"after_login", "has_login_btn": "Log in" in body, "has_avatar_user": bool(re.search(r"(Hi,|My Account|Sign out|450832596)", body))})

    page.set_input_files("#singleUploadInput", str(ROOT/"test_images"/"1K.jpg"), timeout=25000)
    page.wait_for_timeout(15000)
    page.locator('[data-effect="enhance_text"]').first.wait_for(state="visible", timeout=20000)
    prim = page.locator('[data-enhance-action="desktop-primary"]').first
    out.append({"step":"after_upload", "primary_text": prim.inner_text().strip().replace("\n"," "), "primary_class": prim.get_attribute("class"), "cost_state": page.locator('[data-text-enhance-total-cost]').first.get_attribute("data-text-enhance-cost-state")})

    # coordinate click fallback
    box = prim.bounding_box()
    out.append({"step":"before_click", "box": box})
    page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
    out.append({"step":"after_click"})
    for i in range(12):
        page.wait_for_timeout(5000)
        body = page.locator("body").inner_text()
        kw = {k: (k in body) for k in ["Choose the Effect","Upscale to","Continue Enhancing","Edit More","Download","Before","Now","Uploading","Processing","Enhancing","failed","error","purchase"]}
        out.append({"t":(i+1)*5, "primary_text": prim.inner_text().strip().replace("\n"," "), "kw": kw})
        if kw["Continue Enhancing"] or kw["purchase"]:
            break

    ctx.close(); b.close()

(TASK / "explore_generation2_v3.json").write_text(json.dumps({"out": out, "reqs": reqs}, ensure_ascii=False, indent=2), encoding="utf-8")
print("written")
