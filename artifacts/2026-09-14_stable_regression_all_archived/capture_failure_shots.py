"""复现失败现场并截图（mobile home 三处 + PC home 摘要）。"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path("artifacts/2026-09-14_stable_regression_all_archived/shots/failure_capture")
OUT.mkdir(parents=True, exist_ok=True)
report = {}


def dump(pg, name, notes=None):
    path = OUT / f"{name}.png"
    pg.screenshot(path=str(path), full_page=False)
    print(f"[shot] {name} -> {path}", flush=True)


with sync_playwright() as p:
    browser = p.chromium.launch()
    ctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True,
        user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"),
        locale="en-US",
    )
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="networkidle", timeout=120000)
    pg.wait_for_timeout(3000)
    dump(pg, "mobile_home_top")

    hero = pg.locator("section.mobile-home-agent-hero")
    if hero.count():
        hero.first.scroll_into_view_if_needed()
        pg.wait_for_timeout(800)
        dump(pg, "mobile_home_hero_section")
        try:
            texts = hero.first.locator("button").all_inner_texts()
        except Exception as exc:
            texts = [f"<err {exc}>"]
        report["hero_buttons"] = [t.strip() for t in texts]
        print("hero buttons:", report["hero_buttons"], flush=True)
    else:
        print("hero section not found", flush=True)

    # 全页按钮文案，用于定位新增模型入口
    try:
        all_btns = pg.locator("button").all_inner_texts()
    except Exception as exc:
        all_btns = [f"<err {exc}>"]
    report["all_buttons"] = sorted({t.strip() for t in all_btns if t.strip()})
    print("all buttons:", json.dumps(report["all_buttons"], ensure_ascii=False)[:1500], flush=True)

    # 尝试点开 hero 区模型入口（新增模型后默认模型变化）
    try:
        trigger = pg.locator("section.mobile-home-agent-hero button").first
        trigger.click(timeout=8000)
        pg.wait_for_timeout(1500)
        dump(pg, "mobile_home_model_entry_clicked")
    except Exception as exc:
        print("hero click failed:", exc, flush=True)

    # 文案/结构证据
    try:
        report["hero_text"] = pg.locator("section.mobile-home-agent-hero").first.inner_text()[:800]
    except Exception as exc:
        report["hero_text"] = f"<err {exc}>"

    # effect template 相关入口（脚本按 name=\"Butt\" 定位）
    try:
        report["butt_like"] = pg.get_by_role("button", name="Butt").count()
    except Exception as exc:
        report["butt_like"] = f"<err {exc}>"
    print("butt-like count:", report["butt_like"], flush=True)
    try:
        pg.mouse.wheel(0, 1400)
        pg.wait_for_timeout(1200)
        dump(pg, "mobile_home_scrolled_tools")
    except Exception as exc:
        print("scroll failed:", exc, flush=True)

    (OUT / "mobile_home_capture.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    ctx.close()
    browser.close()
print("done", flush=True)