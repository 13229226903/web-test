"""Test specific button clicks after upload on failing pages."""
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

        tests = [
            {"name": "image-to-image-ai", "path": "/image-to-image-ai", "btn": "Create Similar", "need_upload": True},
            {"name": "add-a-person", "path": "/tools/add-a-person-to-a-photo", "btn": "Create Similar", "need_upload": True},
            {"name": "collage-maker", "path": "/collage-maker", "btn": "Create Collage Now", "need_upload": False},
        ]

        for t in tests:
            print(f"\n=== [{t['name']}] ===")
            pg2 = ctx.new_page()
            pg2.goto(f"http://10.17.1.66:3002{t['path']}", timeout=60000)
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

            if t["need_upload"]:
                pg2.locator("input[type=file]").first.set_input_files(test_img)
                pg2.wait_for_timeout(10000)
                pg2.evaluate("""() => {
                    document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                        var bg = window.getComputedStyle(o).backgroundColor;
                        if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
                    });
                }""")
                pg2.wait_for_timeout(1000)
                print(f"  after upload: {pg2.url}")

            # Find and click the target button using mouse.click (not dispatchEvent)
            btn_info = pg2.evaluate("""(text) => {
                var btns = document.querySelectorAll("button");
                for (var i = 0; i < btns.length; i++) {
                    if (btns[i].textContent.includes(text) && btns[i].offsetWidth > 50) {
                        var r = btns[i].getBoundingClientRect();
                        return {index: i, x: r.x + r.width/2, y: r.y + r.height/2,
                                text: btns[i].textContent.trim().substring(0, 60)};
                    }
                }
                return null;
            }""", t["btn"])

            if btn_info:
                print(f"  clicking '{btn_info['text']}' at ({btn_info['x']:.0f}, {btn_info['y']:.0f})")
                pg2.mouse.click(btn_info["x"], btn_info["y"])
                pg2.wait_for_timeout(10000)
                pg2.evaluate("""() => {
                    document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                        var bg = window.getComputedStyle(o).backgroundColor;
                        if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
                    });
                }""")
                pg2.wait_for_timeout(1000)
                print(f"  after click: {pg2.url}")
                body = pg2.locator("body").inner_text()[:300]
                print(f"  body[:300]: {body}")
            else:
                print(f"  button '{t['btn']}' NOT FOUND on page")

            pg2.screenshot(path=f"data/debug/{t['name']}_after_click.png", full_page=True)
            pg2.close()

        b.close()
        print("\nDone")

if __name__ == "__main__":
    main()
