"""Explore /create page on new test server for ID Photo Maker entry."""
import os, sys, glob
from playwright.sync_api import sync_playwright

BASE_NEW = "http://10.17.1.66:3102"

def main():
    td = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
    ti = os.path.abspath(imgs[0]) if imgs else None

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # Login on new server
        pg.goto(f"{BASE_NEW}")
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
        print(f"URL after login: {pg.url}")

        # Find ID Photo Maker related elements
        btns = pg.evaluate("""() => {
            var all = document.querySelectorAll("button, a, [class*='tool'], [class*='Tool'], [class*='photo'], [class*='ID'], [class*='card']");
            return Array.from(all).filter(function(e) {
                var t = (e.textContent || "").toLowerCase();
                var r = e.getBoundingClientRect();
                return (t.includes("id") || t.includes("photo") || t.includes("passport") || t.includes("证件")) && r.width > 30;
            }).map(function(e) {
                var r = e.getBoundingClientRect();
                return {tag: e.tagName, text: (e.textContent || "").trim().substring(0, 60),
                    y: Math.round(r.y), x: Math.round(r.x), w: e.offsetWidth, h: e.offsetHeight,
                    cls: (e.className || "").substring(0, 80)};
            });
        }""")
        print(f"\nID Photo related elements: {len(btns)}")
        for b in btns[:15]:
            print(f"  [{b['tag']}] ({b['x']},{b['y']}) {b['w']}x{b['h']} \"{b['text']}\"")
            print(f"    cls: {b['cls'][:80]}")

        # Also list all visible tool buttons
        tools = pg.evaluate("""() => {
            var all = document.querySelectorAll("button, [data-tool-id], [class*='tool-btn'], [class*='ToolBtn']");
            return Array.from(all).filter(function(e) {
                return e.offsetWidth > 30 && e.offsetHeight > 20;
            }).map(function(e) {
                var r = e.getBoundingClientRect();
                var tid = e.getAttribute("data-tool-id") || "";
                return {tag: e.tagName, text: (e.textContent || "").trim().substring(0, 40),
                    tid: tid, y: Math.round(r.y), x: Math.round(r.x), w: e.offsetWidth};
            });
        }""")
        print(f"\nTool buttons ({len(tools)}):")
        for t in tools[:20]:
            print(f"  [{t['tag']}] ({t['x']},{t['y']}) data-tool-id=\"{t['tid']}\" \"{t['text']}\"")

        pg.screenshot(path="data/debug/create_id_photo.png", full_page=False)
        print("\nScreenshot: data/debug/create_id_photo.png")
        b.close()

if __name__ == "__main__":
    main()
