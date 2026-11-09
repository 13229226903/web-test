import asyncio, sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(**p.devices["iPhone 13"], locale="en-US")
    page = ctx.new_page()
    page.goto("http://10.17.1.66:3001/", wait_until="domcontentloaded")
    page.wait_for_timeout(3000)
    page.get_by_role("button", name="ID Photo Maker").first.click()
    page.wait_for_timeout(1500)
    for fi in page.locator("input[type=file]").all():
        fi.set_input_files("test_images/有人脸.JPG")
    page.wait_for_timeout(8000)
    print("URL:", page.url)
    body = page.inner_text("body")
    print("BODY_LEN", len(body))
    print("---BODY---")
    print(body[:3000])
    print("---dialog count:", page.locator("[role=dialog]").count())
    for t in ["Get Free Credits","Get Up to","Sign up","Free","Upgrade","Continue","Email","Verification Code"]:
        print(repr(t), "=>", t in body)
    page.screenshot(path="artifacts/2026-11-09_stable_regression_3001/shots/probe_l2_008.png")
    b.close()
