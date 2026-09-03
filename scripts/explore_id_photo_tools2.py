"""Explore Formal Wear, Refine, Change BG, Country tabs."""
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

        # Login + nav + upload
        pg.goto(BASE); pg.wait_for_timeout(5000)
        pg.get_by_text("Log in", exact=True).first.click(); pg.wait_for_timeout(3000)
        pg.locator('input[type="email"]').fill("450832596@qq.com")
        pg.locator('input[placeholder="Verification Code"]').fill("123456")
        pg.evaluate("""() => {var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
        pg.wait_for_timeout(10000)
        pg.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove()})}""")
        pg.wait_for_timeout(2000)
        pg.goto(f"{BASE}/create", timeout=60000)
        try: pg.wait_for_load_state("networkidle", timeout=30000)
        except: pass
        pg.wait_for_timeout(5000)
        pg.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove()})}""")
        pg.wait_for_timeout(2000)
        with pg.expect_file_chooser(timeout=10000) as fc:
            pg.locator(f"xpath={XPATH}").first.click()
        fc.value.set_files(ti)
        pg.wait_for_timeout(15000)
        print(f"URL: {pg.url}\n")

        # Get baseline body
        body_before = pg.locator("body").inner_text()

        # Explore Formal Wear
        tools = ["Formal Wear", "Refine", "Change BG"]
        for tool_name in tools:
            print(f"{'='*60}")
            print(f"=== {tool_name} ===")
            el = pg.locator(f"text={tool_name}").first
            if el.count() == 0: continue
            el.click(); pg.wait_for_timeout(3000)
            body = pg.locator("body").inner_text()
            # Find new text lines
            new_lines = set(body.split("\n")) - set(body_before.split("\n"))
            new_items = sorted([l.strip() for l in new_lines if 2 < len(l.strip()) < 100])
            print(f"  New elements ({len(new_items)}):")
            for item in new_items[:20]:
                print(f"    - \"{item}\"")
            has_gen = "Generating" in body
            print(f"  Generating: {has_gen}")
            # Look for "Generate" or "Apply" button
            gen_btn = pg.locator("button:has-text('Generate')").count() + pg.locator("button:has-text('Apply')").count()
            print(f"  Generate/Apply buttons: {gen_btn}")
            pg.screenshot(path=f"data/debug/id_tool_{tool_name.replace(' ','_').lower()}.png", full_page=False)
            # Reset by clicking the tool again (toggle)
            el.click(); pg.wait_for_timeout(1000)
            print()

        # Explore Country/Region switching
        print(f"{'='*60}")
        print("=== Country Categories ===")
        for cat in ["Common", "Visa", "Passport", "Others"]:
            el = pg.locator(f"text={cat}").first
            if el.count() > 0:
                el.click(); pg.wait_for_timeout(1500)
                # Count presets
                preset_count = pg.evaluate("""() => {
                    var all = document.querySelectorAll("*");
                    var count = 0;
                    for (var i = 0; i < all.length; i++) {
                        var t = all[i].textContent.trim();
                        if (/^\d+\s*\*\s*\d+$/.test(t) && all[i].offsetWidth > 50) count++;
                    }
                    return count;
                }""")
                print(f"  {cat}: {preset_count} size presets visible")
                pg.screenshot(path=f"data/debug/id_country_{cat.lower()}.png", full_page=False)

        # Final: click a preset and see what happens
        print(f"\n{'='*60}")
        print("=== Click first size preset ===")
        # Find and click the first visible dimension text
        clicked = pg.evaluate("""() => {
            var all = document.querySelectorAll("*");
            for (var i = 0; i < all.length; i++) {
                var t = all[i].textContent.trim();
                if (/^\d+\s*\*\s*\d+$/.test(t) && all[i].offsetWidth > 50 && all[i].getBoundingClientRect().y > 250) {
                    all[i].click();
                    return t;
                }
            }
            return "NOT FOUND";
        }""")
        print(f"Clicked: {clicked}")
        pg.wait_for_timeout(2000)
        # Check if Photo Size changed
        body_after = pg.locator("body").inner_text()[:500]
        print(f"Body after click: {body_after[:300]}")

        b.close()

if __name__ == "__main__":
    main()
