"""Explore AI Filter panel: Hair Editor and preset selection."""
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

        # Click AI Filter
        pg.locator("text=AI Filter").first.click()
        pg.wait_for_timeout(3000)

        # Find all tabs/categories inside AI Filter panel
        # The panel might have sub-tabs like Face Editor, Hair Editor etc
        all_texts = pg.evaluate("""() => {
            var all = document.querySelectorAll("*");
            var results = [];
            for (var i = 0; i < all.length; i++) {
                var t = all[i].textContent.trim();
                var r = all[i].getBoundingClientRect();
                // Look for single-word or short text labels that could be tab names
                if (all[i].offsetWidth > 30 && all[i].offsetHeight > 15 &&
                    all[i].children.length <= 1 && t.length > 3 && t.length < 30 &&
                    r.x > 20 && r.x < 400 && r.y > 200 && r.y < 600) {
                    results.push({
                        text: t,
                        tag: all[i].tagName,
                        x: Math.round(r.x), y: Math.round(r.y),
                        w: all[i].offsetWidth, h: all[i].offsetHeight,
                        cls: (all[i].className || "").substring(0, 60)
                    });
                }
            }
            return results;
        }""")
        print("=== AI Filter panel elements (left sidebar area) ===")
        seen = set()
        for e in all_texts:
            if e["text"] not in seen:
                seen.add(e["text"])
                print(f"  [{e['tag']}] ({e['x']},{e['y']}) {e['w']}x{e['h']} \"{e['text']}\" cls={e['cls'][:60]}")

        # Try to find Hair Editor specifically
        hair = pg.locator("text=Hair Editor")
        hair_count = hair.count()
        print(f"\nHair Editor elements: {hair_count}")

        # Find "Face Editor" text
        face_count = pg.locator("text=Face Editor").count()
        print(f"Face Editor elements: {face_count}")

        # Try clicking various sub-tabs and see what changes
        body_before = pg.locator("body").inner_text()
        sub_tabs = ["Hair Editor", "Face Editor", "Hair", "Face", "Filter"]
        for tab in sub_tabs:
            el = pg.locator(f"text={tab}").first
            if el.count() > 0:
                el.click()
                pg.wait_for_timeout(1500)
                body = pg.locator("body").inner_text()
                # Check for new preset names
                new_lines = set(body.split("\n")) - set(body_before.split("\n"))
                new_items = sorted([l.strip() for l in new_lines if 2 < len(l.strip()) < 80])
                if new_items:
                    print(f"\nClicking '{tab}' reveals:")
                    for item in new_items[:10]:
                        print(f"  - \"{item}\"")

        # Find individual presets that are clickable
        presets = pg.evaluate("""() => {
            var all = document.querySelectorAll("*");
            return Array.from(all).filter(function(e) {
                var t = e.textContent.trim();
                return (t === "Pouty Lips" || t === "Cute Idol" || t === "Face Slimming" || t === "Young" ||
                    t.indexOf("Hair") > -1 || t.indexOf("hair") > -1) &&
                    e.offsetWidth > 0 && e.children.length <= 1;
            }).map(function(e) {
                var r = e.getBoundingClientRect();
                return {text: e.textContent.trim().substring(0, 40), y: Math.round(r.y), x: Math.round(r.x)};
            });
        }""")
        print(f"\n=== Preset elements ===")
        for p in presets[:10]:
            print(f"  ({p['x']},{p['y']}) \"{p['text']}\"")

        pg.screenshot(path="data/debug/ai_filter_panel.png", full_page=False)
        b.close()

if __name__ == "__main__":
    main()
