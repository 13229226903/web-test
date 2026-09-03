# -*- coding: utf-8 -*-
"""Authorized real-generation exploration for result state. No purchase, no paid credits."""
import json, pathlib
from playwright.sync_api import sync_playwright
ROOT = pathlib.Path(r"D:\Test\web-test")
OUT = ROOT / "artifacts" / "2026-08-26_pokecut_text_enhancer"
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"
IMAGE = ROOT / "data" / "debug" / "test_photo.png"
with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(URL, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(6000)
    page.set_input_files("#singleUploadInput", str(IMAGE))
    page.wait_for_timeout(12000)
    before = {
        "url": page.evaluate("location.href"),
        "effects": page.evaluate("Array.prototype.map.call(document.querySelectorAll('[data-effect]'), function(el){return {effect:el.getAttribute('data-effect'),pressed:el.getAttribute('aria-pressed')}})"),
        "main": page.evaluate("(function(){var el=document.querySelector('[data-enhance-action=desktop-primary]'); return el?el.innerText:null})()"),
    }
    page.screenshot(path=str(OUT / "generation_00_before_click.png"), full_page=False)
    page.click('[data-enhance-action="desktop-primary"]')
    page.wait_for_timeout(1000)
    page.screenshot(path=str(OUT / "generation_01_after_click.png"), full_page=False)
    records = []
    result_detected = False
    last = 0
    for elapsed in [5, 10, 20, 30, 45, 60, 90, 120]:
        page.wait_for_timeout((elapsed - last) * 1000)
        last = elapsed
        body = page.evaluate("document.body.innerText")
        rec = {
            "elapsed": elapsed,
            "url": page.evaluate("location.href"),
            "body_has_continue": "Continue Enhancing" in body,
            "body_has_edit_more": "Edit More" in body,
            "body_has_download": "Download" in body,
            "body_has_before": "before" in body.lower(),
            "body_has_after": "after" in body.lower(),
            "body_snippet": body[:3000],
        }
        records.append(rec)
        page.screenshot(path=str(OUT / f"generation_{elapsed:03d}s.png"), full_page=False)
        if rec["body_has_continue"] and (rec["body_has_edit_more"] or rec["body_has_download"]):
            result_detected = True
            break
    result = {
        "before": before,
        "records": records,
        "result_detected": result_detected,
        "final_body": page.evaluate("document.body.innerText"),
        "final_url": page.evaluate("location.href"),
        "final_title": page.evaluate("document.title"),
    }
    (OUT / "explore_desktop_real_generation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "explore_desktop_real_generation.txt").write_text(result["final_body"], encoding="utf-8")
    print(json.dumps({"result_detected": result_detected, "records": records[-1] if records else None}, ensure_ascii=False, indent=2))
    browser.close()
