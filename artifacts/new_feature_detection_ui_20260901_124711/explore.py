import asyncio, json, os, sys, time
from playwright.async_api import async_playwright

BASE = "https://pokecut-dev.guangzhuiyuan.com"
IMG = os.path.abspath("test_images/有人脸.JPG")
OUT = os.path.abspath("artifacts/new_feature_detection_ui_20260901_124711")
SHOTS = os.path.join(OUT, "shots")
os.makedirs(SHOTS, exist_ok=True)

def now():
    return time.strftime("%H:%M:%S")

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        page = await ctx.new_page()
        log = []

        async def record(label):
            try:
                body = await page.inner_text("body", timeout=5000)
            except Exception as e:
                body = f"<inner_text error: {e}>"
            log.append({"t": now(), "label": label, "url": page.url, "body": body[:6000]})
            print(f"--- {label} @ {now()} url={page.url} ---")

        # 1) nose-shape-detector
        await page.goto(f"{BASE}/tools/nose-shape-detector", wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)
        await record("nose_pre_upload")
        await page.screenshot(path=os.path.join(SHOTS, "nose_pre_upload.png"), full_page=True)

        # upload via real button + file chooser
        try:
            async with page.expect_file_chooser(timeout=10000) as fc_info:
                await page.get_by_role("button", name="Choose File").click()
            fc = await fc_info.value
            await fc.set_files(IMG)
            print(f"{now()} nose: file chooser set {IMG}")
        except Exception as e:
            print(f"{now()} nose: file chooser FAILED {e}")
            # fallback: set input[type=file]
            try:
                inp = page.locator("input[type=file]").first
                await inp.set_input_files(IMG)
                print(f"{now()} nose: fallback set_input_files used")
            except Exception as e2:
                print(f"{now()} nose: fallback FAILED {e2}")

        # poll loading/result states
        await page.wait_for_timeout(1500)
        await record("nose_after_upload_1.5s")
        await page.screenshot(path=os.path.join(SHOTS, "nose_after_upload_1.5s.png"), full_page=True)
        await page.wait_for_timeout(4000)
        await record("nose_after_upload_5.5s")
        await page.wait_for_timeout(10000)
        await record("nose_after_upload_15s")
        await page.wait_for_timeout(20000)
        await record("nose_after_upload_35s")
        await page.screenshot(path=os.path.join(SHOTS, "nose_after_upload_35s.png"), full_page=True)

        # 2) ai-face-reader
        await page.goto(f"{BASE}/tools/ai-face-reader", wait_until="domcontentloaded")
        await page.wait_for_timeout(6000)
        await record("facereader_pre_upload")
        await page.screenshot(path=os.path.join(SHOTS, "facereader_pre_upload.png"), full_page=True)

        try:
            async with page.expect_file_chooser(timeout=10000) as fc_info:
                await page.get_by_role("button", name="Choose File").click()
            fc = await fc_info.value
            await fc.set_files(IMG)
            print(f"{now()} facereader: file chooser set")
        except Exception as e:
            print(f"{now()} facereader: file chooser FAILED {e}")
            try:
                await page.locator("input[type=file]").first.set_input_files(IMG)
                print(f"{now()} facereader: fallback set_input_files used")
            except Exception as e2:
                print(f"{now()} facereader: fallback FAILED {e2}")

        await page.wait_for_timeout(1500)
        await record("facereader_after_upload_1.5s")
        await page.screenshot(path=os.path.join(SHOTS, "facereader_after_upload_1.5s.png"), full_page=True)
        await page.wait_for_timeout(4000)
        await record("facereader_after_upload_5.5s")
        await page.wait_for_timeout(10000)
        await record("facereader_after_upload_15s")
        await page.wait_for_timeout(20000)
        await record("facereader_after_upload_35s")
        await page.screenshot(path=os.path.join(SHOTS, "facereader_after_upload_35s.png"), full_page=True)

        # save transcript
        with open(os.path.join(OUT, "explore_transcript.json"), "w", encoding="utf-8") as f:
            json.dump(log, f, ensure_ascii=False, indent=2)
        print("DONE transcript saved")
        await browser.close()

asyncio.run(main())
