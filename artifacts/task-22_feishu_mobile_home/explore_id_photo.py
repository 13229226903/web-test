# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time
TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
HOME = "http://10.17.1.66:3001/"
IMG = r"D:\Test\web-test\test_images\有人脸.JPG"
DAMAGED = r"D:\Test\web-test\test_images\损坏的图.png"
R = {}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US", user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(20000)
    def home(wait=6000):
        page.goto(HOME, wait_until="domcontentloaded", timeout=60000); page.wait_for_timeout(wait)
    # success flow
    home()
    card = page.get_by_role("button", name="ID Photo Maker").first
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    try:
        with page.expect_file_chooser(timeout=8000) as fc:
            card.click()
        ch = fc.value
        R["success_file_chooser"] = True
        ch.set_files([IMG])
        # matting may take time
        page.wait_for_timeout(12000)
        R["success_url"] = page.url
        R["success_body_head"] = page.inner_text("body")[:600]
        page.screenshot(path=os.path.join(SHOTS, "17_id_photo_success.png"))
    except Exception as e:
        R["success_error"] = str(e)[:300]
    # failure flow with damaged image
    home()
    card = page.get_by_role("button", name="ID Photo Maker").first
    card.scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    try:
        with page.expect_file_chooser(timeout=8000) as fc:
            card.click()
        ch = fc.value
        ch.set_files([DAMAGED])
        page.wait_for_timeout(10000)
        R["failure_url"] = page.url
        R["failure_stayed_home"] = page.url.rstrip("/") == HOME.rstrip("/")
        # capture error/toast text
        R["failure_toasts"] = page.eval_on_selector_all("[class*='toast'], [class*='error'], [class*='message'], [role=alert]", "els => els.slice(0,10).map(e=>({cls:(e.className||'').slice(0,120), text:(e.innerText||'').trim().slice(0,200)}))")
        R["failure_body_head"] = page.inner_text("body")[:600]
        page.screenshot(path=os.path.join(SHOTS, "18_id_photo_failure.png"))
    except Exception as e:
        R["failure_error"] = str(e)[:300]
    with open(os.path.join(TASK,"explore_id_photo.json"),"w",encoding="utf-8") as f:
        json.dump(R,f,ensure_ascii=False,indent=2)
    print(json.dumps(R, ensure_ascii=False, indent=2))
    browser.close()
