import asyncio, os, time
from playwright.async_api import async_playwright
BASE = "https://pokecut-dev.guangzhuiyuan.com"
IMG = os.path.abspath("test_images/有人脸.JPG")
OUT = os.path.abspath("artifacts/new_feature_detection_ui_20260901_124711/shots")
EMAIL = "450832596@qq.com"; CODE = "123456"
def now(): return time.strftime("%H:%M:%S")

async def login(pg):
    await pg.get_by_role("button", name="Log in").first.click(); await pg.wait_for_timeout(2000)
    await pg.get_by_placeholder("Email").fill(EMAIL)
    await pg.get_by_placeholder("Verification Code").fill(CODE)
    await pg.get_by_test_id("auth-submit").click(); await pg.wait_for_timeout(5000)

async def upload(pg):
    async with pg.expect_file_chooser(timeout=10000) as fc_info:
        await pg.locator("#img2imgFirstScreenUploadInput").click(force=True)
    await (await fc_info.value).set_files(IMG)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width":1920,"height":1080}, locale="en-US", accept_downloads=True)
        pg = await ctx.new_page()
        await pg.goto(f"{BASE}/tools/ai-face-reader", wait_until="domcontentloaded"); await pg.wait_for_timeout(5000)
        await login(pg); await upload(pg)
        print(now(), "facereader uploaded, waiting full completion...")
        for i in range(20):
            await pg.wait_for_timeout(5000)
            top = (await pg.inner_text("body"))[:1800]
            g_analysis = "Generating analysis..." in top
            g_optim = "Generating optimized result..." in top
            w_analysis = "Waiting for analysis..." in top
            if (not g_analysis) and (not g_optim) and (not w_analysis):
                print(now(), "facereader FULLY complete at i=", i)
                await pg.screenshot(path=os.path.join(OUT, "facereader_full_result.png"))
                print("=== FULL RESULT TOP ===")
                print(top)
                break
            else:
                print(now(), f"i={i} analysis_gen={g_analysis} optim_gen={g_optim} wait_analysis={w_analysis}")
        await b.close()

asyncio.run(main())
