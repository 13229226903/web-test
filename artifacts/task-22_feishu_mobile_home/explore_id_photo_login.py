# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time
TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
HOME = "http://10.17.1.66:3001/"
EMAIL = "450832596@qq.com"
CODE = "123456"
IMG = r"D:\Test\web-test\test_images\有人脸.JPG"
R = {}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US", user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(20000)
    page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    page.get_by_role("button", name="Sign up").click()
    page.wait_for_timeout(1500)
    # switch to log in if available
    try:
        page.get_by_role("button", name="Log in", exact=True).click()
        page.wait_for_timeout(1200)
    except Exception as e:
        R["switch_login_error"] = str(e)[:200]
    # fill email and code
    try:
        page.locator("input[placeholder='Email']").fill(EMAIL)
        page.locator("input[placeholder='Verification Code']").fill(CODE)
        page.wait_for_timeout(500)
        R["filled"] = True
    except Exception as e:
        R["fill_error"] = str(e)[:200]
    # submit via button Log in
    try:
        page.get_by_role("button", name="Log in", exact=True).click()
        page.wait_for_timeout(6000)
    except Exception as e:
        R["submit_error"] = str(e)[:200]
    R["after_login_url"] = page.url
    R["after_login_header"] = page.evaluate("""() => { const b=[...document.querySelectorAll('button')].filter(e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;}).map(e=>(e.innerText||'').trim()).filter(Boolean).slice(0,12); return b; }""")
    page.screenshot(path=os.path.join(SHOTS, "20_after_login.png"))
    # Now ID Photo Maker success
    card = page.get_by_role("button", name="ID Photo Maker").first
    card.scroll_into_view_if_needed(); page.wait_for_timeout(400)
    try:
        with page.expect_file_chooser(timeout=8000) as fc:
            card.click()
        ch = fc.value
        ch.set_files([IMG])
        page.wait_for_timeout(15000)
        R["id_success_url"] = page.url
        R["id_success_body_tail"] = page.inner_text("body")[-500:]
        page.screenshot(path=os.path.join(SHOTS, "21_id_photo_logged_success.png"))
    except Exception as e:
        R["id_success_error"] = str(e)[:300]
    with open(os.path.join(TASK,"explore_id_photo_login.json"),"w",encoding="utf-8") as f:
        json.dump(R,f,ensure_ascii=False,indent=2)
    print("saved")
    browser.close()
