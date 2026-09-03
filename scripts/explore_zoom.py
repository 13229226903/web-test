"""Explore zoom-in-photos actual behavior."""
import os, sys, glob
from playwright.sync_api import sync_playwright

def main():
    td = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
    ti = os.path.abspath(imgs[0])

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # Login
        pg.goto("http://10.17.1.66:3002")
        pg.wait_for_timeout(5000)
        pg.get_by_text("Log in", exact=True).first.click()
        pg.wait_for_timeout(3000)
        pg.locator('input[type="email"]').fill("450832596@qq.com")
        pg.locator('input[placeholder="Verification Code"]').fill("123456")
        pg.evaluate("""() => {
            var bs = document.querySelectorAll("button");
            for (var i = 0; i < bs.length; i++) {
                if (bs[i].textContent.trim() === "Log in" && bs[i].offsetWidth > 200) {
                    bs[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")
        pg.wait_for_timeout(10000)
        pg.evaluate("""() => {
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                var bg = window.getComputedStyle(o).backgroundColor;
                if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
            });
        }""")
        pg.wait_for_timeout(2000)
        print("Login OK")

        pg2 = ctx.new_page()
        pg2.goto("http://10.17.1.66:3002/tools/zoom-in-photos", timeout=60000)
        try:
            pg2.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg2.wait_for_timeout(3000)
        pg2.evaluate("""() => {
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                var bg = window.getComputedStyle(o).backgroundColor;
                if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
            });
        }""")
        pg2.wait_for_timeout(1000)

        print(f"Before upload: {pg2.url}")

        # Try set_input_files
        pg2.locator("input[type=file]").first.set_input_files(ti)
        pg2.wait_for_timeout(20000)
        print(f"After upload (20s): {pg2.url}")

        body = pg2.locator("body").inner_text()[:500]
        print(f"Body[:500]: {body}")

        sliders = pg2.locator("input[type='range']").count()
        print(f"Range sliders: {sliders}")

        has_gen = "Generating" in body
        print(f"Has Generating: {has_gen}")

        # Check for any new elements after upload
        pg2.screenshot(path="data/debug/zoom_in_debug.png", full_page=False)
        print("Screenshot saved")
        b.close()

if __name__ == "__main__":
    main()
