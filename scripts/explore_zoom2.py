"""Check zoom-in-photos upload button and actual upload flow."""
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

        # Find ALL clickable elements with upload-related text or behavior
        print("\n=== Before upload ===")
        print(f"URL: {pg2.url}")

        # Check file inputs
        fi_count = pg2.locator("input[type=file]").count()
        print(f"File inputs: {fi_count}")

        # Check for all buttons and their text
        btns = pg2.evaluate("""() => {
            return Array.from(document.querySelectorAll("button, [role='button'], label")).filter(function(el) {
                return el.offsetWidth > 30;
            }).map(function(el) {
                var r = el.getBoundingClientRect();
                return {
                    tag: el.tagName,
                    text: (el.textContent || "").trim().substring(0, 60),
                    y: Math.round(r.y), w: el.offsetWidth, h: el.offsetHeight,
                    cls: (el.className || "").substring(0, 60)
                };
            });
        }""")
        print(f"Visible buttons/labels: {len(btns)}")
        for b in btns:
            print(f"  [{b['tag']}] y={b['y']} {b['w']}x{b['h']} text=\"{b['text']}\" cls=\"{b['cls']}\"")

        # Check page content before upload
        body_before = pg2.locator("body").inner_text()
        has_optimizing_before = "Optimizing" in body_before
        has_zoom_before = "Zoom in" in body_before
        slider_before = pg2.locator("input[type='range']").count()
        print(f"\nBefore: Optimizing={has_optimizing_before}, Zoom in={has_zoom_before}, sliders={slider_before}")

        # Now try uploading via set_input_files
        pg2.locator("input[type=file]").first.set_input_files(ti)
        pg2.wait_for_timeout(5000)

        body_after5 = pg2.locator("body").inner_text()
        has_optimizing = "Optimizing" in body_after5
        print(f"\nAfter 5s: Optimizing={has_optimizing}")
        if has_optimizing:
            print("  Task IS running!")
            # Wait for completion
            try:
                pg2.wait_for_function("() => !document.body.innerText.includes('Optimizing')", timeout=300000)
                print("  Task completed!")
            except Exception:
                print("  Task still running after 5min")

        print(f"\n=== After upload ===")
        print(f"URL: {pg2.url}")
        body_after = pg2.locator("body").inner_text()[:500]
        print(f"Body[:500]: {body_after}")

        slider_after = pg2.locator("input[type='range']").count()
        print(f"Sliders: {slider_after}")

        # Check if Zoom value changed
        zoom_val = pg2.evaluate("""() => {
            var s = document.querySelector("input[type='range']");
            return s ? s.value : null;
        }""")
        print(f"Zoom slider value: {zoom_val}")

        pg2.screenshot(path="data/debug/zoom_in_after.png", full_page=False)
        print("Screenshot: data/debug/zoom_in_after.png")
        b.close()

if __name__ == "__main__":
    main()
