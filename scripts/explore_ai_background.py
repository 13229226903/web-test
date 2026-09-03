"""Explore AI Background panel content after reaching /agent."""
import os, sys, glob
from playwright.sync_api import sync_playwright

def main():
    td = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
    test_img = os.path.abspath(imgs[0])

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
        pg2.goto("http://10.17.1.66:3002/ai-background", timeout=60000)
        try:
            pg2.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg2.wait_for_timeout(5000)
        pg2.evaluate("""() => {
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                var bg = window.getComputedStyle(o).backgroundColor;
                if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
            });
        }""")
        pg2.wait_for_timeout(1000)

        # Upload
        pg2.locator("input[type=file]").first.set_input_files(test_img)
        pg2.wait_for_timeout(5000)

        # Wait for generation
        try:
            pg2.wait_for_function(
                "() => document.body.innerText.includes('Generating')",
                timeout=30000
            )
            print("Detected 'Generating', waiting for completion...")
            pg2.wait_for_function(
                "() => !document.body.innerText.includes('Generating')",
                timeout=600000
            )
        except Exception as e:
            print(f"Generation wait: {e}")

        pg2.wait_for_timeout(5000)
        pg2.evaluate("""() => {
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                var bg = window.getComputedStyle(o).backgroundColor;
                if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
            });
        }""")
        pg2.wait_for_timeout(1000)
        print(f"URL after generation: {pg2.url}")

        # Click canvas
        try:
            pg2.locator("canvas").first.click(timeout=10000)
            pg2.wait_for_timeout(2000)
            print("Canvas clicked")
        except Exception as e:
            print(f"Canvas click failed: {e}")

        # Find AI Background button
        ai_btn_count = pg2.locator("button:has-text('AI Background')").count()
        print(f"AI Background buttons: {ai_btn_count}")

        if ai_btn_count > 0:
            pg2.locator("button:has-text('AI Background')").first.click()
            pg2.wait_for_timeout(3000)
            print("Clicked AI Background button")
        else:
            # Try text match
            try:
                pg2.get_by_text("AI Background").first.click(timeout=5000)
                pg2.wait_for_timeout(3000)
                print("Clicked via get_by_text")
            except Exception:
                print("Could not find AI Background button")

        pg2.screenshot(path="data/debug/ai_background_after_panel.png", full_page=True)

        # Print body text
        body = pg2.locator("body").inner_text()[:1500]
        print(f"\nBody[:1500]:\n{body}")

        # Find all visible text in sidebar/panel area (right side, x > 800)
        sidebar_text = pg2.evaluate("""() => {
            var elems = document.querySelectorAll('*');
            var results = [];
            for (var i = 0; i < elems.length; i++) {
                var r = elems[i].getBoundingClientRect();
                if (r.x > 250 && r.width > 100 && r.height > 20 && r.height < 100 &&
                    elems[i].children.length === 0 && elems[i].textContent.trim().length > 2 &&
                    elems[i].textContent.trim().length < 50) {
                    results.push({
                        tag: elems[i].tagName,
                        text: elems[i].textContent.trim(),
                        y: Math.round(r.y), x: Math.round(r.x)
                    });
                }
            }
            return results.slice(0, 40);
        }""")
        print("\nSidebar elements (x>250, standalone text):")
        for el in sidebar_text[:30]:
            print(f"  {el['tag']} ({el['x']},{el['y']}) \"{el['text']}\"")

        b.close()

if __name__ == "__main__":
    main()
