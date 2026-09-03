# -*- coding: utf-8 -*-
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Test\web-test")
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
TASK = ROOT / "artifacts" / "2026-08-29_pokecut_ai_image_text_enhancer"
EFFECTS = ["enhance_text", "remove_glare", "remove_moire", "document_scanner"]
out = {"steps": []}

def rec(page, name, extra=None):
    out["steps"].append({"name": name, "url": page.url, "extra": extra or {}})

def pressed(page, e):
    return page.locator(f'[data-effect="{e}"]').first.get_attribute("aria-pressed") == "true"

def set_effects(page, desired):
    for e in EFFECTS:
        want = e in desired
        for _ in range(5):
            if pressed(page, e) == want:
                break
            page.locator(f'[data-effect="{e}"]').first.click(timeout=10000)
            page.wait_for_timeout(700)
    for e in EFFECTS:
        assert pressed(page, e) == (e in desired), f"{e} state wrong"

def costinfo(page):
    primary = page.locator('[data-enhance-action="desktop-primary"]').first
    cost_el = primary.locator("[data-text-enhance-total-cost]").first
    return {
        "primary_text": primary.inner_text().strip().replace("\n", " "),
        "cost": cost_el.inner_text().strip() if cost_el.count() else None,
        "cost_state": cost_el.get_attribute("data-text-enhance-cost-state") if cost_el.count() else None,
    }

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1440, "height": 1000}, locale="en-US")
    page = ctx.new_page()
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    page.locator('h1:has-text("Enhance Text in Image to 8K Online Free")').wait_for(state="visible", timeout=30000)
    page.set_input_files("#singleUploadInput", str(ROOT/"test_images"/"1K.jpg"), timeout=25000)
    page.wait_for_timeout(15000)
    page.locator('[data-effect="enhance_text"]').first.wait_for(state="visible", timeout=20000)

    rec(page, "default_enhance_2k", costinfo(page))
    set_effects(page, {"remove_glare"})
    rec(page, "remove_glare_only", costinfo(page))
    set_effects(page, {"remove_glare", "remove_moire"})
    rec(page, "glare_moire", costinfo(page))
    set_effects(page, {"remove_glare", "remove_moire", "document_scanner"})
    rec(page, "three_non_enhance", costinfo(page))
    set_effects(page, {"enhance_text"})
    # try 4k/8k
    page.locator('p:text-is("4k")').first.click(timeout=10000); page.wait_for_timeout(900)
    rec(page, "enhance_4k", costinfo(page))
    page.locator('p:text-is("8k")').first.click(timeout=10000); page.wait_for_timeout(900)
    rec(page, "enhance_8k", costinfo(page))
    set_effects(page, {"enhance_text","remove_glare","remove_moire","document_scanner"})
    rec(page, "all_8k", costinfo(page))

    ctx.close(); b.close()

(TASK / "explore_cost_v3.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(out, ensure_ascii=False, indent=2))
