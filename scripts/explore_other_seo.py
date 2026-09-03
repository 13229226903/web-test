"""Explore upload interaction for other SEO pages."""
import os, sys, glob
from playwright.sync_api import sync_playwright

PAGES = [
    "zoom-in-photos", "photo-restoration", "monogram-maker",
    "phone-wallpaper-maker", "photo-border", "digicam-effect",
    "add-hearts-to-photo", "youtube-banner-maker", "outline-image",
    "add-name-and-date-on-photo", "big-head-cutout-face-cutout",
]

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
        print("Login OK\n")

        BASE = "http://10.17.1.66:3002"
        results = {}

        for name in PAGES:
            if name == "big-head-cutout-face-cutout":
                path = "/de/tools/big-head-cutout-face-cutout"
            else:
                path = f"/tools/{name}"

            pg2 = ctx.new_page()
            pg2.goto(f"{BASE}{path}", timeout=60000)
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

            before_url = pg2.url
            before_title = pg2.title()

            # Try to find upload trigger: any element with "upload" in text, sr-only label, etc.
            upload_triggers = pg2.evaluate("""() => {
                var results = [];
                // Check for any label pointing to a file input
                var fileInputs = document.querySelectorAll("input[type='file']");
                fileInputs.forEach(function(fi) {
                    var id = fi.id;
                    if (id) {
                        var labels = document.querySelectorAll("label[for='" + id + "']");
                        labels.forEach(function(l) {
                            var r = l.getBoundingClientRect();
                            results.push({type: "label[for]", text: l.textContent.trim().substring(0, 40),
                                y: Math.round(r.y), w: l.offsetWidth, h: l.offsetHeight, visible: r.width > 0});
                        });
                    }
                });
                // Check for elements with upload-related text or classes
                var candidates = document.querySelectorAll(
                    "[class*='upload'], [class*='Upload'], button, [role='button'], label, " +
                    "[class*='cta'], [class*='CTA'], [class*='hero'] button, [class*='hero'] div[class*='btn']"
                );
                candidates.forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.y > 100 && r.y < 2000 && r.width > 30 && r.height > 20) {
                        var txt = (el.textContent || "").trim().substring(0, 50);
                        var tag = el.tagName;
                        var cls = (el.className || "").substring(0, 80);
                        results.push({type: tag + "[visible]", text: txt, y: Math.round(r.y),
                            w: el.offsetWidth, h: el.offsetHeight, cls: cls});
                    }
                });
                return results;
            }""")

            print(f"[{name}]")
            print(f"  Title: {before_title[:80]}")
            print(f"  Upload triggers found: {len(upload_triggers)}")
            for t in upload_triggers[:8]:
                print(f"    {t['type']}: y={t['y']} {t['w']}x{t['h']} text=\"{t['text']}\"")

            # Try set_input_files and see if URL changes
            file_count = pg2.locator("input[type=file]").count()
            if file_count > 0:
                pg2.locator("input[type=file]").first.set_input_files(test_img)
                pg2.wait_for_timeout(15000)
                after_url = pg2.url
                navigated = after_url != before_url
                print(f"  set_input_files: {'NAVIGATED' if navigated else 'STAYED'} -> {after_url}")
                results[name] = {"navigated": navigated, "after_url": after_url}
            else:
                print(f"  NO file input found!")
                results[name] = {"navigated": False, "after_url": before_url}

            pg2.close()
            print()

        # Summary
        print("\n=== SUMMARY ===")
        for name, r in results.items():
            print(f"  {name}: {'NAVIGATED' if r['navigated'] else 'STAYED'}")

        b.close()

if __name__ == "__main__":
    main()
