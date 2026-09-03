"""Deep explore each left-side tool in /tools/id-photo-edit."""
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

        # Login + navigate + upload
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
        with pg.expect_file_chooser(timeout=10000) as fc:
            pg.locator(f"xpath={XPATH}").first.click()
        fc.value.set_files(ti)
        pg.wait_for_timeout(15000)
        print(f"URL: {pg.url}\n")

        # Get baseline body before any interaction
        body_before = pg.locator("body").inner_text()

        # === Explore each tool ===
        tools = ["Photo Size", "AI Filter", "Formal Wear", "Refine", "Change BG"]
        for tool_name in tools:
            print(f"{'='*60}")
            print(f"=== {tool_name} ===")

            # Click the tool
            el = pg.locator(f"text={tool_name}").first
            if el.count() == 0:
                print(f"  NOT FOUND")
                continue

            el.click()
            pg.wait_for_timeout(3000)

            # Check what changed
            body = pg.locator("body").inner_text()

            # Check for new panels, modals, dropdowns
            # Look for text that appeared after click
            before_lines = set(body_before.split("\n"))
            after_lines = set(body.split("\n"))
            new_content = after_lines - before_lines
            new_items = [l.strip() for l in new_content if len(l.strip()) > 2 and len(l.strip()) < 100]

            print(f"  New UI elements after click:")
            for item in new_items[:15]:
                if item not in ["Collage", "Photo", "User8JY"]:
                    print(f"    - \"{item}\"")

            # Check for modals, dropdowns, panels
            has_generating = "Generating" in body
            has_loading = "loading" in body.lower() or "processing" in body.lower()
            print(f"  Generating: {has_generating}, Loading: {has_loading}")

            # Check for any visible new buttons in the expanded area
            new_btns = pg.evaluate("""(before) => {
                var bs = document.querySelectorAll("button");
                return Array.from(bs).filter(function(b) {
                    var t = (b.textContent || "").trim();
                    return b.offsetWidth > 30 && b.offsetHeight > 15 && t && before.indexOf(t) === -1;
                }).map(function(b) {
                    var r = b.getBoundingClientRect();
                    return {text: t.substring(0, 50), y: Math.round(r.y), x: Math.round(r.x)};
                });
            }""", body_before)
            if new_btns:
                print(f"  New buttons: {len(new_btns)}")
                for nb in new_btns[:8]:
                    print(f"    [{nb['x']},{nb['y']}] \"{nb['text']}\"")

            pg.screenshot(path=f"data/debug/id_photo_tool_{tool_name.replace(' ','_').lower()}.png", full_page=False)
            print()

        # === Also explore Country/Region category switching ===
        print(f"{'='*60}")
        print("=== Country Category Tabs ===")
        for cat in ["Common", "Visa", "Passport", "Others"]:
            el = pg.locator(f"text={cat}").first
            if el.count() > 0:
                el.click()
                pg.wait_for_timeout(1000)
                # Check if presets changed
                presets_text = pg.evaluate("""() => {
                    var ps = document.querySelectorAll("*");
                    var texts = [];
                    for (var i = 0; i < ps.length; i++) {
                        var t = ps[i].textContent.trim();
                        if (/\\d+\\s*\\*\\s*\\d+/.test(t) && t.length < 30) {
                            texts.push(t);
                        }
                    }
                    return texts.slice(0, 8);
                }""")
                print(f"  {cat}: {len(presets_text)} presets - {presets_text[:4]}")

        b.close()

if __name__ == "__main__":
    main()
