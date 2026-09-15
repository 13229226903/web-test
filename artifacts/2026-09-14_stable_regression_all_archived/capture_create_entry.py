"""抓取 /create 入口页现状（L5-001 失败的 Start from a Photo 卡片）。"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path("artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture")
OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = ctx.new_page()
    page.goto(f"{BASE}/create", wait_until="networkidle", timeout=120000)
    page.wait_for_timeout(4000)
    page.screenshot(path=str(OUT / "create_entry_page.png"), full_page=False)
    body = page.locator("body").inner_text()
    print("has 'Start from a Photo':", "Start from a Photo" in body, flush=True)
    print("has 'Start from Photo':", "Start from Photo" in body, flush=True)
    print("has 'Trending Tools':", "Trending Tools" in body, flush=True)
    cards = page.locator("div.cursor-pointer").count()
    print("div.cursor-pointer count:", cards, flush=True)
    texts = [t.strip() for t in page.locator("div.cursor-pointer").all_inner_texts()]
    print("cursor-pointer texts:", json.dumps(texts[:25], ensure_ascii=False)[:1500], flush=True)
    (OUT / "create_entry_body.txt").write_text(body[:4000], encoding="utf-8")
    ctx.close()
    browser.close()