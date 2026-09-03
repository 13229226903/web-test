"""Correct flow: click ID Photo Maker -> file chooser -> /tools/id-photo-edit."""
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

        # Go to /create
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

        print(f"At /create: {pg.url}")

        # Step 1: Click ID Photo Maker -> expect file chooser
        el = pg.locator(f"xpath={XPATH}")
        print(f"ID Photo Maker found: {el.count()}")

        # Use mouse.click (Vue component, dispatchEvent best)
        try:
            with pg.expect_file_chooser(timeout=10000) as fc:
                el.first.click()
            fc.value.set_files(ti)
            print("File chooser triggered! Image uploaded.")
        except Exception as e:
            print(f"File chooser NOT triggered: {e}")
            # Fallback: try mouse.click
            box = el.first.bounding_box()
            try:
                with pg.expect_file_chooser(timeout=10000) as fc:
                    pg.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                fc.value.set_files(ti)
                print("File chooser via mouse.click!")
            except Exception as e2:
                print(f"mouse.click also failed: {e2}")

        pg.wait_for_timeout(15000)
        print(f"\nAfter upload URL: {pg.url}")
        print(f"Expected: /tools/id-photo-edit?pid=...")

        body = pg.locator("body").inner_text()[:1000]
        print(f"\nBody[:1000]:\n{body}")

        # Check for key UI elements
        has_country = "Country" in body or "Region" in body
        has_size = "Photo Size" in body or "mm" in body
        has_download = "Download" in body
        has_ai_filter = "AI Filter" in body
        print(f"\nKey elements: Country/Region={has_country}, Size={has_size}, Download={has_download}, AI Filter={has_ai_filter}")

        pg.screenshot(path="data/debug/id_photo_edit.png", full_page=False)
        print("\nScreenshot: data/debug/id_photo_edit.png")
        b.close()

if __name__ == "__main__":
    main()
