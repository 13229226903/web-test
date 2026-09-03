"""Test ID Photo Maker xpath and click interaction."""
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

        # Find ID Photo Maker by xpath
        el = pg.locator(f"xpath={XPATH}")
        count = el.count()
        print(f"ID Photo Maker xpath found: {count}")

        if count > 0:
            text = el.first.inner_text()
            tag = el.first.evaluate("el => el.tagName")
            box = el.first.bounding_box()
            print(f"Tag: {tag}, Text: \"{text}\"")
            print(f"Box: {box}")

            # Click the entry
            el.first.click()
            pg.wait_for_timeout(5000)
            print(f"After click URL: {pg.url}")
            body = pg.locator("body").inner_text()[:500]
            print(f"Body[:500]: {body}")

            # Check for file input or upload prompt
            has_upload = pg.locator("input[type=file]").count()
            has_text = "upload" in body.lower() or "photo" in body.lower()
            print(f"File inputs: {has_upload}, Upload/Photo text: {has_text}")

            pg.screenshot(path="data/debug/id_photo_after_click.png", full_page=False)
            print("Screenshot saved")
        else:
            print("ID Photo Maker NOT FOUND by xpath")
            # Try fallback: search all elements for "ID Photo" text
            all_text = pg.evaluate("""() => {
                return document.body.innerText.substring(0, 2000);
            }""")
            print(f"Page body (first 500 chars): {all_text[:500]}")

        b.close()

if __name__ == "__main__":
    main()
