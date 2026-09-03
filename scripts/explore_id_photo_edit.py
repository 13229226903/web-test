"""Explore /tools/id-photo-edit page features after upload."""
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

        # Go to /create and trigger ID Photo Maker
        pg.goto(f"{BASE}/create", timeout=60000)
        try: pg.wait_for_load_state("networkidle", timeout=30000)
        except: pass
        pg.wait_for_timeout(5000)
        pg.evaluate("""() => {
            document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
                var bg = window.getComputedStyle(o).backgroundColor;
                if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
            });
        }""")
        pg.wait_for_timeout(2000)

        # Click ID Photo Maker -> file chooser -> upload
        with pg.expect_file_chooser(timeout=10000) as fc:
            pg.locator(f"xpath={XPATH}").first.click()
        fc.value.set_files(ti)
        pg.wait_for_timeout(15000)

        print(f"URL: {pg.url}")
        print(f"Expected: /tools/id-photo-edit?pid=...")
        print()

        # === Explore edit page features ===

        # 1. All buttons and their states
        btns = pg.evaluate("""() => {
            return Array.from(document.querySelectorAll("button")).filter(function(b) {
                return b.offsetWidth > 30 && b.offsetHeight > 15;
            }).map(function(b) {
                var r = b.getBoundingClientRect();
                return {
                    text: (b.textContent || "").trim().substring(0, 50),
                    y: Math.round(r.y), x: Math.round(r.x),
                    w: b.offsetWidth, h: b.offsetHeight,
                    disabled: b.disabled,
                    cls: (b.className || "").substring(0, 60)
                };
            });
        }""")
        print(f"=== Buttons ({len(btns)}) ===")
        for b in btns:
            d = " [DISABLED]" if b["disabled"] else ""
            if b["text"]:
                print(f"  ({b['x']},{b['y']}) {b['w']}x{b['h']} \"{b['text']}\"{d}")

        # 2. Tabs / tool sections
        tabs = pg.evaluate("""() => {
            var results = [];
            // AI Filter, Formal Wear, Refine, Change BG tabs
            var tabTexts = ["AI Filter", "Formal Wear", "Refine", "Change BG", "Photo Size"];
            tabTexts.forEach(function(t) {
                var els = document.querySelectorAll("*");
                for (var i = 0; i < els.length; i++) {
                    if (els[i].textContent.trim() === t && els[i].offsetWidth > 0 && els[i].children.length <= 1) {
                        var r = els[i].getBoundingClientRect();
                        results.push({text: t, tag: els[i].tagName, y: Math.round(r.y), x: Math.round(r.x),
                            w: els[i].offsetWidth, h: els[i].offsetHeight,
                            cls: (els[i].className || "").substring(0, 60)});
                        break;
                    }
                }
            });
            return results;
        }""")
        print(f"\n=== Tabs ===")
        for t in tabs:
            print(f"  [{t['tag']}] ({t['x']},{t['y']}) {t['w']}x{t['h']} \"{t['text']}\" cls={t['cls']}")

        # 3. Country/Region dropdown
        country_elems = pg.evaluate("""() => {
            var results = [];
            var all = document.querySelectorAll("*");
            for (var i = 0; i < all.length; i++) {
                var t = all[i].textContent.trim();
                if (t === "Country/Region" || t.startsWith("United Kingdom") || t === "Common" || t === "Visa" || t === "Passport" || t === "Others") {
                    var r = all[i].getBoundingClientRect();
                    if (all[i].offsetWidth > 0) {
                        results.push({text: t.substring(0, 40), tag: all[i].tagName,
                            y: Math.round(r.y), x: Math.round(r.x), w: all[i].offsetWidth});
                    }
                }
            }
            return results;
        }""")
        print(f"\n=== Country/Region ({len(country_elems)}) ===")
        for c in country_elems[:12]:
            print(f"  [{c['tag']}] ({c['x']},{c['y']}) \"{c['text']}\"")

        # 4. Size presets list
        size_presets = pg.evaluate("""() => {
            var results = [];
            var all = document.querySelectorAll("*");
            for (var i = 0; i < all.length; i++) {
                var t = all[i].textContent.trim();
                if (/\\d+\\s*\\*\\s*\\d+/.test(t) || /\\d+mm/.test(t) || /\\d+pixel/.test(t)) {
                    if (all[i].offsetWidth > 50 && all[i].children.length <= 2) {
                        results.push({text: t.substring(0, 60), tag: all[i].tagName,
                            y: Math.round(all[i].getBoundingClientRect().y)});
                    }
                }
            }
            return results.slice(0, 15);
        }""")
        print(f"\n=== Size Presets ({len(size_presets)}) ===")
        for s in size_presets:
            print(f"  [{s['tag']}] y={s['y']} \"{s['text']}\"")

        # 5. Body text overview
        body = pg.locator("body").inner_text()
        print(f"\n=== Key Features ===")
        for kw in ["Download", "Credits Purchase", "Photo Size", "AI Filter", "Formal Wear", "Refine", "Change BG", "Country/Region", "Tips"]:
            print(f"  {kw}: {'YES' if kw in body else 'NO'}")

        # 6. Try clicking AI Filter toggle and see what happens
        ai_filter_btn = pg.locator("text=AI Filter")
        if ai_filter_btn.count() > 0:
            print(f"\n=== AI Filter Click ===")
            ai_filter_btn.first.click()
            pg.wait_for_timeout(5000)
            has_generating = "Generating" in pg.locator("body").inner_text()
            print(f"After AI Filter click - Generating: {has_generating}")

        pg.screenshot(path="data/debug/id_photo_edit_full.png", full_page=True)
        print("\nScreenshot: data/debug/id_photo_edit_full.png")
        b.close()

if __name__ == "__main__":
    main()
