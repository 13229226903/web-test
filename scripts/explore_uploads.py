"""Explore actual upload behavior for failing tool pages."""
import os, sys, glob
from playwright.sync_api import sync_playwright

PAGES = [
    ("id-photo-maker", "/tools/id-photo-maker", "expect navigation"),
    ("batch-edit", "/batch-edit", "expect navigation to /batch-edit/edit"),
    ("ai-image-generator", "/ai-image-generator", "expect navigation to /agent"),
    ("image-to-image-ai", "/image-to-image-ai", "two-stage: 1st stay, 2nd navigate"),
    ("add-a-person", "/tools/add-a-person-to-a-photo", "two-stage: 1st stay, 2nd navigate"),
]

def dismiss_overlay(page):
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(o => {
            var bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes('rgba') && (bg.includes('0.3') || bg.includes('0.5'))) {
                o.remove();
            }
        });
    }""")

def click_upload_btn(page):
    """Click the first visible upload button via dispatchEvent."""
    page.evaluate("""() => {
        var btns = document.querySelectorAll("button");
        for (var i = 0; i < btns.length; i++) {
            var r = btns[i].getBoundingClientRect();
            if (btns[i].textContent.trim() && r.y > 200 && r.y < 1500 && r.width > 100) {
                btns[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                return;
            }
        }
    }""")

def try_upload(page, test_img):
    """Try to upload an image, return whether file chooser was used."""
    try:
        with page.expect_file_chooser(timeout=10000) as fc:
            click_upload_btn(page)
        fc.value.set_files(test_img)
        return True
    except Exception:
        page.locator("input[type=file]").first.set_input_files(test_img)
        return False

def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # Login
        print("=== Logging in ===")
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

        # Get test image
        td = os.path.join(os.path.dirname(__file__), "..", "test_images")
        imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
        test_img = os.path.abspath(imgs[0]) if imgs else None
        print(f"Test image: {os.path.basename(test_img)} ({os.path.getsize(test_img)} bytes)")

        BASE = "http://10.17.1.66:3002"

        for name, path, desc in PAGES:
            print(f"\n=== [{name}] {desc} ===")
            pg2 = ctx.new_page()
            pg2.goto(f"{BASE}{path}", timeout=60000)
            try:
                pg2.wait_for_load_state("networkidle", timeout=30000)
            except Exception:
                pass
            pg2.wait_for_timeout(5000)
            dismiss_overlay(pg2)
            pg2.wait_for_timeout(1000)

            print(f"  before: {pg2.url}")

            # Find visible buttons on page
            btns = pg2.evaluate("""() => {
                var all = document.querySelectorAll("button");
                return Array.from(all).filter(function(b) {
                    return b.offsetWidth > 50 && b.offsetHeight > 20 && b.textContent.trim().length > 0;
                }).map(function(b) {
                    var r = b.getBoundingClientRect();
                    return {text: b.textContent.trim().substring(0, 60), y: Math.round(r.y), w: b.offsetWidth, h: b.offsetHeight};
                });
            }""")
            for btn in btns:
                if btn["y"] < 1500:
                    print(f"  BTN: y={btn['y']} {btn['w']}x{btn['h']} \"{btn['text']}\"")

            # Try upload
            used_fc = try_upload(pg2, test_img)
            print(f"  file_chooser used: {used_fc}")
            pg2.wait_for_timeout(15000)
            dismiss_overlay(pg2)
            pg2.wait_for_timeout(1000)
            print(f"  after 1st upload: {pg2.url}")
            body = pg2.locator("body").inner_text()[:300]
            print(f"  body[:300]: {body}")

            # For two-stage pages, try second upload
            if "two-stage" in desc:
                print("  --- 2nd upload ---")
                used_fc2 = try_upload(pg2, test_img)
                print(f"  file_chooser used: {used_fc2}")
                pg2.wait_for_timeout(15000)
                dismiss_overlay(pg2)
                pg2.wait_for_timeout(1000)
                print(f"  after 2nd upload: {pg2.url}")

            pg2.screenshot(path=f"data/debug/{name}_after_upload.png", full_page=True)
            pg2.close()

        b.close()
        print("\n=== Done ===")

if __name__ == "__main__":
    main()
