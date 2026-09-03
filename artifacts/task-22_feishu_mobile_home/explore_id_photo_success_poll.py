# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time
TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
HOME = "http://10.17.1.66:3001/"
IMG = r"D:\Test\web-test\test_images\有人脸.JPG"
R = {"poll": []}
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US", user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(20000)
    page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)
    card = page.get_by_role("button", name="ID Photo Maker").first
    card.scroll_into_view_if_needed(); page.wait_for_timeout(400)
    with page.expect_file_chooser(timeout=8000) as fc:
        card.click()
    ch = fc.value
    ch.set_files([IMG])
    t0 = time.time()
    last_url = page.url
    for i in range(20):
        time.sleep(5)
        url = page.url
        toasts = page.eval_on_selector_all("[class*='toast'], [class*='error'], [class*='message'], [role=alert]", "els => els.slice(0,8).map(e=>({cls:(e.className||'').slice(0,100), text:(e.innerText||'').trim().slice(0,160)}))")
        body_tail = page.inner_text("body")[-300:]
        R["poll"].append({"t": round(time.time()-t0,1), "url": url, "toasts": toasts, "body_tail": body_tail})
        if url != last_url and url != HOME.rstrip("/"):
            page.screenshot(path=os.path.join(SHOTS, "19_id_photo_success_late.png"))
            break
        if i in (2, 6, 12):
            page.screenshot(path=os.path.join(SHOTS, f"19_id_photo_poll_{i}.png"))
    R["final_url"] = page.url
    with open(os.path.join(TASK,"explore_id_photo_success_poll.json"),"w",encoding="utf-8") as f:
        json.dump(R,f,ensure_ascii=False,indent=2)
    print("FINAL_URL", page.url)
    print(json.dumps(R["poll"], ensure_ascii=False, indent=2))
    browser.close()
