import asyncio, json, os, time
from playwright.async_api import async_playwright

BASE = "https://pokecut-dev.guangzhuiyuan.com"
IMG = os.path.abspath("test_images/有人脸.JPG")
OUT = os.path.abspath("artifacts/new_feature_detection_ui_20260901_124711")
SHOTS = os.path.join(OUT, "shots")
os.makedirs(SHOTS, exist_ok=True)
EMAIL = "450832596@qq.com"
CODE = "123456"

KEYWORDS = ["Generating analysis", "Waiting for analysis", "Generating optimized result",
            "Original Image", "Analysis Result", "Optimized Result", "Get It Now",
            "Continue in Portrait Editor", "Portrait Editor", "Download", "Upload Image",
            "Change Image", "Try again", "Network error", "Server busy", "Policy violation",
            "Optimization failed", "No credits", "credits", "Get Free Credits", "Sign Up"]

def now(): return time.strftime("%H:%M:%S")

async def login(page):
    await page.get_by_role("button", name="Log in").first.click()
    await page.wait_for_timeout(2000)
    await page.get_by_placeholder("Email").fill(EMAIL)
    await page.get_by_placeholder("Verification Code").fill(CODE)
    await page.get_by_test_id("auth-submit").click()
    await page.wait_for_timeout(5000)
    body = await page.inner_text("body")
    print(f"{now()} login done, nav has 'Log in':", "Log in" in body[:600])
    await page.screenshot(path=os.path.join(SHOTS, "after_login.png"))

async def upload(page, tag):
    ok = False
    try:
        el = page.get_by_text("Choose File", exact=True).first
        box = await el.bounding_box()
        async with page.expect_file_chooser(timeout=8000) as fc_info:
            await page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
        fc = await fc_info.value
        await fc.set_files(IMG)
        ok = True
        print(f"{now()} {tag}: coordinate-click file chooser OK")
    except Exception as e:
        print(f"{now()} {tag}: coordinate-click file chooser FAILED: {str(e)[:180]}")
    if not ok:
        try:
            await page.locator("#img2imgFirstScreenUploadInput").set_input_files(IMG)
            await page.locator("#img2imgFirstScreenUploadInput").dispatch_event("change")
            print(f"{now()} {tag}: set_input_files+change fallback")
            ok = True
        except Exception as e2:
            print(f"{now()} {tag}: set_input_files fallback FAILED: {str(e2)[:180]}")

async def observe(page, tag, base_label):
    events = []
    for i in range(24):
        await page.wait_for_timeout(5000)
        body = await page.inner_text("body")
        for kw in KEYWORDS:
            if kw in body:
                events.append({"i": i, "t": now(), "kw": kw})
        # capture every 3rd
        if i % 3 == 0:
            await page.screenshot(path=os.path.join(SHOTS, f"{base_label}_state_{i}.png"), full_page=True)
        # terminal?
        if any(k in body for k in ["Original Image", "Get It Now", "Optimization failed", "Network error", "Server busy", "Policy violation"]):
            print(f"{now()} {tag}: terminal-ish at i={i}")
            break
    body = await page.inner_text("body")
    return body

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width":1920,"height":1080}, locale="en-US", accept_downloads=True)
        pg = await ctx.new_page()
        result = {}

        await pg.goto(f"{BASE}/tools/nose-shape-detector", wait_until="domcontentloaded")
        await pg.wait_for_timeout(5000)
        await login(pg)
        await upload(pg, "nose")
        body = await observe(pg, "nose", "nose")
        result["nose_tail"] = body[-2500:]

        await pg.goto(f"{BASE}/tools/ai-face-reader", wait_until="domcontentloaded")
        await pg.wait_for_timeout(5000)
        await upload(pg, "facereader")
        body = await observe(pg, "facereader", "facereader")
        result["facereader_tail"] = body[-2500:]

        with open(os.path.join(OUT, "observe_result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print("OBSERVE DONE")
        await b.close()

asyncio.run(main())
