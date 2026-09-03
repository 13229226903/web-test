"""Explore full ID Photo Maker flow: click entry -> upload -> process."""
import os, sys, glob
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
XPATH = "//*[@id='__nuxt']/div[1]/div[3]/div[2]/div[2]/div[2]/div[6]"

def main():
    td = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
    ti = os.path.abspath(imgs[0]) if imgs else None

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # Login
        pg.goto(BASE)
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

        # Navigate to /create
        pg.goto(f"{BASE}/create", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)
        pg.evaluate("""() => {
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                var bg = window.getComputedStyle(o).backgroundColor;
                if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
            });
        }""")
        pg.wait_for_timeout(2000)

        # Step 1: Click ID Photo Maker
        el = pg.locator(f"xpath={XPATH}")
        if el.count() == 0:
            print("ID Photo Maker not found!")
            b.close()
            return

        el.first.click()
        pg.wait_for_timeout(3000)
        print(f"Step 1: Clicked ID Photo Maker, URL: {pg.url}")

        # Check if any modal/appeared
        body_short = pg.locator("body").inner_text()[:300]
        print(f"Body: {body_short}")

        # Step 2: Try "Start from a Photo" button
        start_btn = pg.locator("text=Start from a Photo")
        print(f"\n'Start from a Photo' found: {start_btn.count()}")
        if start_btn.count() > 0:
            # Click it and try file chooser
            try:
                with pg.expect_file_chooser(timeout=10000) as fc:
                    start_btn.first.click()
                fc.value.set_files(ti)
                print("File uploaded via 'Start from a Photo'")
            except Exception as e:
                print(f"File chooser failed: {e}")
                # Try set_input_files fallback
                pg.locator("input[type=file]").first.set_input_files(ti)
                print("File uploaded via set_input_files")

            pg.wait_for_timeout(15000)
            print(f"\nAfter upload URL: {pg.url}")
            body = pg.locator("body").inner_text()[:800]
            print(f"Body[:800]: {body}")

            # Check for ID Photo related UI
            has_id_photo = "ID Photo" in body or "passport" in body.lower() or "证件" in body
            has_generating = "Generating" in body or "processing" in body.lower()
            print(f"Has ID Photo UI: {has_id_photo}")
            print(f"Has Generating: {has_generating}")

            # Check for tool panels
            tools_visible = pg.evaluate("""() => {
                var tools = document.querySelectorAll("[data-tool-id], [class*='tool-panel'], [class*='sidebar']");
                return Array.from(tools).filter(function(t) {
                    return t.offsetWidth > 50 && t.offsetHeight > 50;
                }).map(function(t) {
                    return (t.getAttribute("data-tool-id") || t.className || "").substring(0, 60);
                }).slice(0, 10);
            }""")
            print(f"Visible tools: {tools_visible}")

        pg.screenshot(path="data/debug/id_photo_flow.png", full_page=False)
        print("\nScreenshot saved")
        b.close()

if __name__ == "__main__":
    main()
