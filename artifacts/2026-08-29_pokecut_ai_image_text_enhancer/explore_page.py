# -*- coding: utf-8 -*-
"""page-map-sync focused re-exploration for ai-image-text-enhancer (no generation)."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Test\web-test")
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
TASK = ROOT / "artifacts" / "2026-08-29_pokecut_ai_image_text_enhancer"
SHOTS = TASK / "shots"
SHOTS.mkdir(parents=True, exist_ok=True)
EFFECTS = ["enhance_text", "remove_glare", "remove_moire", "document_scanner"]
out = {"steps": []}

def snap(page, name):
    p = SHOTS / f"{name}.png"
    page.screenshot(path=str(p), full_page=False)
    return str(p)

def rec(page, name, extra=None):
    out["steps"].append({"name": name, "url": page.url, "extra": extra or {}})

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US")
    page = ctx.new_page()
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    h1 = page.locator('h1:has-text("Enhance Text in Image to 8K Online Free")')
    h1.wait_for(state="visible", timeout=30000)
    rec(page, "00_initial", {"h1": h1.inner_text(), "single_upload_count": page.locator("#singleUploadInput").count()})
    snap(page, "00_initial")

    page.set_input_files("#singleUploadInput", str(ROOT / "test_images" / "1K.jpg"), timeout=25000)
    page.wait_for_timeout(15000)
    page.locator('[data-effect="enhance_text"]').first.wait_for(state="visible", timeout=20000)
    body = page.locator("body").inner_text()
    rec(page, "01_after_upload_1k", {
        "choose_effect": "Choose the Effect" in body,
        "supports_multi": "*Supports multiple selections" in body,
        "upscale": "Upscale to" in body,
    })
    snap(page, "01_after_upload_1k")

    defaults = {e: page.locator(f'[data-effect="{e}"]').first.get_attribute("aria-pressed") for e in EFFECTS}
    cost = page.locator('[data-text-enhance-total-cost]').first.inner_text().strip() if page.locator('[data-text-enhance-total-cost]').count() else None
    rec(page, "02_defaults", {"defaults": defaults, "cost": cost, "primary_text": page.locator('[data-enhance-action="desktop-primary"]').first.inner_text().strip()})
    snap(page, "02_defaults")

    # tooltips
    tips = {}
    for e in EFFECTS:
        icon = page.locator(f'[data-effect="{e}"] [data-effect-help-icon]').first
        icon.scroll_into_view_if_needed()
        icon.hover()
        page.wait_for_timeout(1000)
        tip_texts = page.eval_on_selector_all('body *', "els => els.filter(el => { const r=el.getBoundingClientRect(); return r.width>0 && r.height>0; }).map(el => el.textContent.trim()).filter(t => t && t.length<120)")
        # pick first matching known phrase
        tips[e] = next((t for t in tip_texts if t.startswith(("Enhance blurry", "Remove glare", "Reduce moire", "Turn a photographed"))), None)
        snap(page, f"03_tooltip_{e}")
    rec(page, "03_tooltips", {"tips": tips})

    # uncheck enhance_text -> resolution hidden
    page.locator('[data-effect="enhance_text"]').first.click(timeout=10000)
    page.wait_for_timeout(1200)
    body = page.locator("body").inner_text()
    rec(page, "04_non_enhance_only", {"upscale_visible": "Upscale to" in body, "enhance_pressed": page.locator('[data-effect="enhance_text"]').first.get_attribute("aria-pressed")})
    snap(page, "04_non_enhance_only")

    # uncheck all -> primary disabled
    for e in EFFECTS:
        if page.locator(f'[data-effect="{e}"]').first.get_attribute("aria-pressed") == "true":
            page.locator(f'[data-effect="{e}"]').first.click(timeout=10000)
            page.wait_for_timeout(800)
    body = page.locator("body").inner_text()
    rec(page, "05_no_effect", {"upscale_visible": "Upscale to" in body, "primary_class": page.locator('[data-enhance-action="desktop-primary"]').first.get_attribute("class")})
    snap(page, "05_no_effect")

    ctx.close()
    b.close()

(TASK / "explore_page_v3.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print("DONE", TASK / "explore_page_v3.json")
