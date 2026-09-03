import asyncio, os, time
from playwright.async_api import async_playwright
BASE = "https://pokecut-dev.guangzhuiyuan.com"
IMG = os.path.abspath("test_images/有人脸.JPG")
OUT = os.path.abspath("artifacts/new_feature_detection_ui_20260901_124711/shots")
EMAIL = "450832596@qq.com"; CODE = "123456"
def now(): return time.strftime("%H:%M:%S")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width":1920,"height":1080}, locale="en-US", accept_downloads=True)
        pg = await ctx.new_page()
        await pg.goto(f"{BASE}/tools/nose-shape-detector", wait_until="domcontentloaded")
        await pg.wait_for_timeout(5000)
        # login
        await pg.get_by_role("button", name="Log in").first.click()
        await pg.wait_for_timeout(2000)
        await pg.get_by_placeholder("Email").fill(EMAIL)
        await pg.get_by_placeholder("Verification Code").fill(CODE)
        await pg.get_by_test_id("auth-submit").click()
        await pg.wait_for_timeout(5000)
        print(now(), "logged in, nav Log in present:", "Log in" in (await pg.inner_text("body"))[:600])

        # inspect upload DOM
        inp = pg.locator("#img2imgFirstScreenUploadInput")
        info = await inp.evaluate("el => { let a=[]; let n=el; for(let i=0;i<4 && n;i++){a.push(n.tagName+'.'+n.className); n=n.parentElement;} return {parentChain:a, id:el.id, type:el.type}; }")
        print("DOM parent chain:", info)

        # try clicking the label via role button name Choose File -> force
        try:
            async with pg.expect_file_chooser(timeout=8000) as fc_info:
                await pg.locator("#img2imgFirstScreenUploadInput").click(force=True)
            fc = await fc_info.value
            await fc.set_files(IMG)
            print(now(), "label-force-click file chooser OK")
        except Exception as e:
            print(now(), "label-force-click FAILED:", str(e)[:200])

        await pg.wait_for_timeout(8000)
        # capture top viewport
        await pg.screenshot(path=os.path.join(OUT, "nose_top_after_upload.png"))
        body = await pg.inner_text("body")
        print("=== TOP BODY (first 1800) ===")
        print(body[:1800])
        await b.close()

asyncio.run(main())
