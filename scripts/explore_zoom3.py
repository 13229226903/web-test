"""Find reliable task completion indicator for zoom-in-photos."""
import os, sys, glob, time
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

        # Check before upload
        body_before = pg2.locator("body").inner_text()
        has_download = "Download HD" in body_before
        has_edit = "Edit More" in body_before
        print(f"BEFORE: Download HD={has_download}, Edit More={has_edit}")

        # Upload
        pg2.locator("input[type=file]").first.set_input_files(ti)

        # Poll for task to complete - check for % sign disappearance
        print("Waiting for task completion...")
        start = time.time()
        for i in range(60):  # max 10 min
            pg2.wait_for_timeout(10000)
            body = pg2.locator("body").inner_text()
            # Check if there's a percentage + time estimate (e.g. "21%" or "40s")
            has_pct = any(c + "%" in body for c in "0123456789")
            has_wait = "wait" in body.lower()
            if not has_pct and not has_wait:
                elapsed = time.time() - start
                print(f"Task completed after {elapsed:.0f}s!")
                break
            if i % 6 == 0:
                # Print progress every minute
                pct_line = [l for l in body.split("\n") if "%" in l and "wait" in l.lower()]
                if pct_line:
                    print(f"  {pct_line[0].strip()}")
        else:
            print("Timeout waiting for task")

        body_after = pg2.locator("body").inner_text()
        print(f"\nAFTER task:")
        # Show just the top section (first 400 chars after "Zoom in")
        idx = body_after.find("Zoom in")
        if idx > 0:
            print(body_after[idx:idx+300])

        # Check slider value
        val = pg2.evaluate("""() => {
            var s = document.querySelector("input[type='range']");
            return s ? s.value : null;
        }""")
        print(f"Slider value: {val}")

        pg2.screenshot(path="data/debug/zoom_in_completed.png", full_page=False)
        print("Screenshot: data/debug/zoom_in_completed.png")
        b.close()

if __name__ == "__main__":
    main()
