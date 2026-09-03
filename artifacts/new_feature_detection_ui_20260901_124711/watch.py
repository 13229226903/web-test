import asyncio, json, os, time
from playwright.async_api import async_playwright
BASE = "https://pokecut-dev.guangzhuiyuan.com"
IMG = os.path.abspath("test_images/有人脸.JPG")
OUT = os.path.abspath("artifacts/new_feature_detection_ui_20260901_124711/shots")
EMAIL = "450832596@qq.com"; CODE = "123456"
def now(): return time.strftime("%H:%M:%S")

async def login(pg):
    await pg.get_by_role("button", name="Log in").first.click()
    await pg.wait_for_timeout(2000)
    await pg.get_by_placeholder("Email").fill(EMAIL)
    await pg.get_by_placeholder("Verification Code").fill(CODE)
    await pg.get_by_test_id("auth-submit").click()
    await pg.wait_for_timeout(5000)

async def upload(pg, tag):
    async with pg.expect_file_chooser(timeout=10000) as fc_info:
        await pg.locator("#img2imgFirstScreenUploadInput").click(force=True)
    fc = await fc_info.value
    await fc.set_files(IMG)
    print(now(), tag, "uploaded via force-click chooser")

async def watch(pg, tag):
    seen = []
    for i in range(40):
        await pg.wait_for_timeout(4000)
        body = await pg.inner_text("body")
        top = body[:2200]
        for kw in ["Generating analysis...", "Waiting for analysis...", "Generating optimized result...",
                   "Analysis Result", "Optimized Result", "Original Image", "Get It Now",
                   "Continue in Portrait Editor", "Upload Image", "Download", "Optimization failed",
                   "Network error", "Server busy", "Policy violation"]:
            if kw in top and kw not in [s[0] for s in seen]:
                seen.append((kw, now()))
                print(now(), tag, "STATE:", kw)
                await pg.screenshot(path=os.path.join(OUT, f"{tag}_{len(seen)}_{kw.replace('...','').replace(':','').replace(' ','_')[:30]}.png"))
        # terminal: analysis done (no longer 'Generating analysis'/'Waiting') and optimized done or placeholder
        if ("Generating analysis..." not in top and "Waiting for analysis..." not in top
                and ("Continue in Portrait Editor" in top or "Get It Now" in top or "Optimization failed" in top or "Network error" in top or "Server busy" in top or "Policy violation" in top)):
            print(now(), tag, "terminal reached at i=", i)
            await pg.screenshot(path=os.path.join(OUT, f"{tag}_final.png"))
            break
    return await pg.inner_text("body")

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width":1920,"height":1080}, locale="en-US", accept_downloads=True)
        pg = await ctx.new_page()
        out = {}

        await pg.goto(f"{BASE}/tools/nose-shape-detector", wait_until="domcontentloaded")
        await pg.wait_for_timeout(5000)
        await login(pg)
        await upload(pg, "nose")
        body = await watch(pg, "nose")
        out["nose_top"] = body[:2200]

        await pg.goto(f"{BASE}/tools/ai-face-reader", wait_until="domcontentloaded")
        await pg.wait_for_timeout(5000)
        await upload(pg, "facereader")
        body = await watch(pg, "facereader")
        out["facereader_top"] = body[:2200]

        with open(os.path.join(os.path.dirname(OUT), "watch_result.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
        print("WATCH DONE")
        await b.close()

asyncio.run(main())
