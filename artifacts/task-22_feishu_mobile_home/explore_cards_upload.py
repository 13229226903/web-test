# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time
TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
HOME = "http://10.17.1.66:3001/"
IMG = r"D:\Test\web-test\test_images\有人脸.JPG"
R = {}
def home(wait=6000):
    page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(wait)
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US", user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(15000)
    for nm in ["Clothes Changer","HD Photo Coverter","Body Editor","AI Replace"]:
        home()
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                page.get_by_role("button", name=nm).first.click()
            ch = fc.value
            ch.set_files([IMG])
            page.wait_for_timeout(6000)
            body = page.inner_text("body")[:500]
            R[nm] = {"url": page.url, "body_head": body}
        except Exception as e:
            R[nm] = {"error": str(e)[:200]}
    with open(os.path.join(TASK,"explore_cards_upload.json"),"w",encoding="utf-8") as f:
        json.dump(R,f,ensure_ascii=False,indent=2)
    print(json.dumps(R, ensure_ascii=False, indent=2))
    browser.close()
