"""Explore batch-edit SEO pages for test design."""
import os, sys, glob
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
PAGES = [
    ("/batch-edit/bulk-background-remover", "背景移除tab"),
    ("/batch-edit/bulk-background-changer", "背景更改tab"),
    ("/batch-edit/bulk-image-enhancer", "画质增强tab"),
    ("/batch-edit/bulk-image-resizer", "resizer tab"),
]

def main():
    td = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
    ti = os.path.abspath(imgs[0]) if imgs else None

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # Login
        pg.goto(BASE); pg.wait_for_timeout(5000)
        pg.get_by_text("Log in", exact=True).first.click(); pg.wait_for_timeout(3000)
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
        print("Login OK\n")

        for path, tab_name in PAGES:
            pg2 = ctx.new_page()
            pg2.goto(f"{BASE}{path}", timeout=60000)
            try: pg2.wait_for_load_state("networkidle", timeout=30000)
            except: pass
            pg2.wait_for_timeout(3000)
            pg2.evaluate("""() => {
                document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                    var bg = window.getComputedStyle(o).backgroundColor;
                    if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
                });
            }""")
            pg2.wait_for_timeout(1000)

            name = path.split("/")[-1]
            title = pg2.title()[:80]
            h1s = [h.inner_text()[:60] for h in pg2.locator("h1").all()[:2]]

            # Check for try/demo image area (should NOT exist)
            body = pg2.locator("body").inner_text()
            has_try = "Try " in body or " Demo " in body

            # Find upload trigger
            fi = pg2.locator("input[type=file]").count()
            upload_btns = pg2.evaluate("""() => {
                return Array.from(document.querySelectorAll("button, [class*='upload'], img[src*='upload']")).filter(function(e) {
                    var r = e.getBoundingClientRect();
                    return r.y > 200 && r.y < 2000 && r.width > 50 && e.offsetHeight > 20;
                }).map(function(e) {
                    var r = e.getBoundingClientRect();
                    return {tag: e.tagName, text: (e.textContent || e.alt || "").trim().substring(0, 40),
                        y: Math.round(r.y), w: e.offsetWidth, h: e.offsetHeight};
                });
            }""")

            print(f"=== {name} ({tab_name}) ===")
            print(f"  Title: {title}")
            print(f"  H1: {h1s}")
            print(f"  Has try/demo area: {has_try} | file_inputs: {fi}")
            for b in upload_btns[:5]:
                print(f"  [{b['tag']}] y={b['y']} {b['w']}x{b['h']} \"{b['text']}\"")

            # Try upload and see what happens
            if fi > 0:
                pg2.locator("input[type=file]").first.set_input_files(ti)
                pg2.wait_for_timeout(15000)
                pg2.evaluate("""() => {
                    document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                        var bg = window.getComputedStyle(o).backgroundColor;
                        if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
                    });
                }""")
                pg2.wait_for_timeout(2000)
                print(f"  After upload URL: {pg2.url}")
                pg2.screenshot(path=f"data/debug/batch_{name}.png", full_page=False)

            pg2.close()
            print()

        b.close()

if __name__ == "__main__":
    main()
