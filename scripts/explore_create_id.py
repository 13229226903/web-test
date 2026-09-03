"""Explore /create page ID Photo Maker flow."""
import os, sys, glob
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"

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
        print(f"After login: {pg.url}")

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
        print(f"At /create: {pg.url}")

        # Find upload button and AI Portraits related tools
        tools = pg.evaluate("""() => {
            var all = document.querySelectorAll("[data-tool-id], button, a, [class*='tool'], [class*='card'], [class*='portrait']");
            return Array.from(all).filter(function(e) {
                return e.offsetWidth > 30 && e.offsetHeight > 20;
            }).map(function(e) {
                var r = e.getBoundingClientRect();
                var tid = e.getAttribute("data-tool-id") || e.getAttribute("id") || "";
                return {
                    tag: e.tagName,
                    text: (e.textContent || "").trim().substring(0, 50),
                    tid: tid,
                    y: Math.round(r.y), x: Math.round(r.x),
                    w: e.offsetWidth, h: e.offsetHeight,
                    cls: (e.className || "").substring(0, 60)
                };
            });
        }""")

        print(f"\n=== /create page tools ({len(tools)}) ===")
        for t in tools[:30]:
            if t['text']:
                print(f"  [{t['tag']}] ({t['x']},{t['y']}) {t['w']}x{t['h']} tid=\"{t['tid']}\" \"{t['text']}\"")

        # Find ID Photo / Passport related entries specifically
        id_entries = pg.evaluate("""() => {
            var all = document.querySelectorAll("*");
            return Array.from(all).filter(function(e) {
                var t = (e.textContent || "").toLowerCase();
                var r = e.getBoundingClientRect();
                return (t.includes("id photo") || t.includes("passport") || t.includes("portrait")) &&
                    r.width > 50 && r.height > 20 && e.children.length <= 1;
            }).map(function(e) {
                var r = e.getBoundingClientRect();
                return {
                    tag: e.tagName,
                    text: (e.textContent || "").trim().substring(0, 50),
                    y: Math.round(r.y), x: Math.round(r.x),
                    w: e.offsetWidth, h: e.offsetHeight,
                    clickable: e.tagName === 'BUTTON' || e.tagName === 'A' || e.onclick !== null
                };
            });
        }""")

        print(f"\n=== ID Photo / Passport entries ({len(id_entries)}) ===")
        for e in id_entries[:15]:
            print(f"  [{e['tag']}] ({e['x']},{e['y']}) {e['w']}x{e['h']} clickable={e['clickable']} \"{e['text']}\"")

        pg.screenshot(path="data/debug/create_canvas.png", full_page=False)
        print("\nScreenshot saved")
        b.close()

if __name__ == "__main__":
    main()
