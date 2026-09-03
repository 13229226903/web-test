# -*- coding: utf-8 -*-
import time, json, re
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Test\web-test")
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
TASK = ROOT / "artifacts" / "2026-08-29_pokecut_ai_image_text_enhancer"
EMAIL = "450832596@qq.com"; CODE = "123456"
out = []

def snap(page, name):
    p = TASK / "shots" / f"{name}.png"
    page.screenshot(path=str(p), full_page=False)
    return str(p)

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width":1440,"height":1000}, locale="en-US")
    page = ctx.new_page()
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    page.locator('h1:has-text("Enhance Text in Image to 8K Online Free")').wait_for(state="visible", timeout=30000)

    page.click(".debug-float-btn", timeout=10000)
    page.wait_for_timeout(800)
    page.locator(".environment-options .action-btn", has_text="预部署").click(timeout=10000)
    page.wait_for_timeout(7000)

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
    out.append({"step":"after_login", "has_login_btn": "Log in" in body, "has_email": EMAIL in body, "has_hi": bool(re.search(r"(Hi,|My Account|Sign out|Log out)", body))})
    # localStorage user info
    ls = page.evaluate("() => { const o={}; for (let i=0;i<localStorage.length;i++){ const k=localStorage.key(i); o[k]=localStorage.getItem(k); } return o; }")
    interesting = {k:v for k,v in ls.items() if re.search(r"user|token|auth|vip|member|subscri|account", k, re.I)}
    out.append({"step":"localStorage", "interesting_keys": interesting})
    snap(page, "member_predeploy_after_login")

    page.set_input_files("#singleUploadInput", str(ROOT/"test_images"/"文字测例.jpg"), timeout=25000)
    page.wait_for_timeout(15000)
    page.locator('[data-effect="enhance_text"]').first.wait_for(state="visible", timeout=20000)
    prim = page.locator('[data-enhance-action="desktop-primary"]').first
    cost_el = prim.locator("[data-text-enhance-total-cost]").first
    def info(label):
        return {"label":label, "primary_text": prim.inner_text().strip().replace("\n"," "), "cost": cost_el.inner_text().strip() if cost_el.count() else None, "cost_state": cost_el.get_attribute("data-text-enhance-cost-state") if cost_el.count() else None}
    out.append(info("default_2k"))
    page.locator('p:text-is("4k")').first.click(timeout=10000); page.wait_for_timeout(900)
    out.append(info("4k"))
    page.locator('p:text-is("8k")').first.click(timeout=10000); page.wait_for_timeout(900)
    out.append(info("8k"))
    # all effects at 8k
    for e in ["remove_glare","remove_moire","document_scanner"]:
        if page.locator(f'[data-effect="{e}"]').first.get_attribute("aria-pressed") != "true":
            page.locator(f'[data-effect="{e}"]').first.click(timeout=10000); page.wait_for_timeout(700)
    out.append(info("all_8k"))
    snap(page, "member_predeploy_all_8k")
    ctx.close(); b.close()

(TASK / "investigate_member_v3.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
