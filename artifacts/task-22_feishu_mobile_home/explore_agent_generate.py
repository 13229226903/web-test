# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time
TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
HOME = "http://10.17.1.66:3001/"
R = {}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US", user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(20000)
    page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(7000)
    gen = page.locator("section.mobile-home-agent-hero button", has_text="Generate").first
    R["generate_disabled_before_text"] = gen.is_disabled()
    ta = page.locator("textarea[aria-label]").first
    ta.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    try:
        ta.fill("a studio portrait with soft light")
        page.wait_for_timeout(1500)
    except Exception as e:
        R["fill_error"] = str(e)[:200]
    R["generate_disabled_after_text"] = gen.is_disabled()
    R["generate_class_after_text"] = gen.get_attribute("class")[:200]
    # click Generate
    url_before = page.url
    try:
        gen.click(timeout=5000)
    except Exception as e:
        R["click_error"] = str(e)[:250]
    page.wait_for_timeout(8000)
    R["url_after_generate"] = page.url
    R["body_head_after"] = page.inner_text("body")[:500]
    page.screenshot(path=os.path.join(SHOTS, "22_agent_generate_after_text.png"))
    with open(os.path.join(TASK,"explore_agent_generate.json"),"w",encoding="utf-8") as f:
        json.dump(R,f,ensure_ascii=False,indent=2)
    print(json.dumps(R, ensure_ascii=False, indent=2))
    browser.close()
