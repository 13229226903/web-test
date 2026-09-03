"""Explore what happens after upload on failing pages: new buttons, preview, scroll position."""
import os, sys, glob
from playwright.sync_api import sync_playwright

PAGES = [
    ("batch-edit", "/batch-edit"),
    ("ai-image-generator", "/ai-image-generator"),
    ("image-to-image-ai", "/image-to-image-ai"),
    ("add-a-person", "/tools/add-a-person-to-a-photo"),
]

def dismiss_overlay(page):
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(o => {
            var bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes('rgba') && (bg.includes('0.3') || bg.includes('0.5'))) o.remove();
        });
    }""")

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # Login
        print("Logging in...")
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
        dismiss_overlay(pg)
        pg.wait_for_timeout(2000)
        print("Login OK")

        td = os.path.join(os.path.dirname(__file__), "..", "test_images")
        imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
        test_img = os.path.abspath(imgs[0])
        BASE = "http://10.17.1.66:3002"

        for name, path in PAGES:
            print(f"\n{'='*60}")
            print(f"[{name}] {path}")
            print(f"{'='*60}")
            pg2 = ctx.new_page()
            pg2.goto(f"{BASE}{path}", timeout=60000)
            try:
                pg2.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass
            pg2.wait_for_timeout(5000)
            dismiss_overlay(pg2)
            pg2.wait_for_timeout(1000)

            # Upload image directly
            file_inputs = pg2.locator("input[type=file]")
            print(f"File inputs count: {file_inputs.count()}")
            if file_inputs.count() > 0:
                file_inputs.first.set_input_files(test_img)
                print("Uploaded via set_input_files")
            else:
                print("No file input found!")
                pg2.screenshot(path=f"data/debug/{name}_no_input.png", full_page=True)
                pg2.close()
                continue

            pg2.wait_for_timeout(15000)
            dismiss_overlay(pg2)
            pg2.wait_for_timeout(2000)

            print(f"URL after upload: {pg2.url}")

            # Check for new UI elements
            # 1. Generate/Create/Submit buttons
            gen_btns = pg2.evaluate("""() => {
                var btns = document.querySelectorAll("button");
                return Array.from(btns)
                    .filter(function(b) { return b.offsetWidth > 50 && b.offsetHeight > 20; })
                    .map(function(b) {
                        var r = b.getBoundingClientRect();
                        return {
                            text: b.textContent.trim().substring(0, 80),
                            y: Math.round(r.y), x: Math.round(r.x),
                            w: b.offsetWidth, h: b.offsetHeight,
                            disabled: b.disabled
                        };
                    })
                    .filter(function(b) { return b.y < 2000; });
            }""")
            print("Visible buttons (y<2000):")
            for btn in gen_btns:
                d = " [DISABLED]" if btn["disabled"] else ""
                print(f"  y={btn['y']} {btn['w']}x{btn['h']} \"{btn['text']}\"{d}")

            # 2. Image preview areas
            img_container = pg2.evaluate("""() => {
                // Check for uploaded image preview
                var imgs = document.querySelectorAll("img");
                var large_imgs = Array.from(imgs).filter(function(img) {
                    return img.offsetWidth > 200 || img.offsetHeight > 200;
                }).map(function(img) {
                    var r = img.getBoundingClientRect();
                    return {
                        src: (img.src || "").substring(0, 100),
                        w: img.offsetWidth, h: img.offsetHeight,
                        y: Math.round(r.y), x: Math.round(r.x)
                    };
                });
                // Check for canvas
                var canvases = document.querySelectorAll("canvas");
                var large_c = Array.from(canvases).filter(function(c) {
                    return c.offsetWidth > 200;
                }).map(function(c) {
                    var r = c.getBoundingClientRect();
                    return {w: c.offsetWidth, h: c.offsetHeight, y: Math.round(r.y)};
                });
                return {img_count: large_imgs.length, images: large_imgs.slice(0, 3),
                        canvas_count: large_c.length, canvases: large_c};
            }""")
            print(f"Large images: {img_container['img_count']}, Large canvases: {img_container['canvas_count']}")
            if img_container['images']:
                for img in img_container['images'][:3]:
                    print(f"  img: {img['w']}x{img['h']} at y={img['y']} src={img['src'][:60]}")

            # 3. Text input / textarea
            inputs = pg2.evaluate("""() => {
                var elems = document.querySelectorAll("textarea, input[type='text'], [contenteditable='true']");
                return Array.from(elems).filter(function(e) {
                    return e.offsetWidth > 50;
                }).map(function(e) {
                    var r = e.getBoundingClientRect();
                    return {tag: e.tagName, placeholder: (e.placeholder || "").substring(0, 60),
                            y: Math.round(r.y), w: e.offsetWidth};
                });
            }""")
            if inputs:
                print(f"Text inputs: {len(inputs)}")
                for inp in inputs[:5]:
                    print(f"  {inp['tag']} placeholder=\"{inp['placeholder']}\" y={inp['y']} w={inp['w']}")

            pg2.screenshot(path=f"data/debug/{name}_after_upload.png", full_page=True)
            pg2.close()

        b.close()
        print("\nDone")

if __name__ == "__main__":
    main()
