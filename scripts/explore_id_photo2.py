"""Find ID Photo Maker in Trending Tools on /create page."""
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

        # Login on new server
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

        # Navigate to /create
        pg.goto(f"{BASE}/create", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)

        # Check if logged in
        body = pg.locator("body").inner_text()[:500]
        logged_in = "User" in body or "Credits" in body
        print(f"Logged in on /create: {logged_in}")
        print(f"URL: {pg.url}")

        # Find Trending Tools section and ID Photo Maker
        # Look for elements with "Trending" text
        trending_elems = pg.evaluate("""() => {
            var all = document.querySelectorAll("*");
            return Array.from(all).filter(function(e) {
                var t = e.textContent.trim();
                return (t === "Trending Tools" || t === "Trending") && e.offsetWidth > 0;
            }).map(function(e) {
                var r = e.getBoundingClientRect();
                return {tag: e.tagName, text: t, y: Math.round(r.y), x: Math.round(r.x)};
            });
        }""")
        print(f"\nTrending elements: {len(trending_elems)}")
        for e in trending_elems[:5]:
            print(f"  [{e['tag']}] ({e['x']},{e['y']}) \"{e['text']}\"")

        # Try the specific xpath
        xpath = "//*[@id='__nuxt']/div[1]/div[3]/div[2]/div[2]/div[2]/div[6]"
        el = pg.locator(f"xpath={xpath}")
        count = el.count()
        print(f"\nID Photo Maker xpath found: {count}")
        if count > 0:
            for i in range(count):
                e = el.nth(i)
                text = e.inner_text()
                box = e.bounding_box()
                print(f"  [{i}] text=\"{text}\" box={box}")

        # Also search for "ID Photo" text broadly
        id_elements = pg.evaluate("""() => {
            var all = document.querySelectorAll("*");
            return Array.from(all).filter(function(e) {
                var t = (e.textContent || "").trim();
                return t.includes("ID Photo") && t.length < 50 && e.offsetWidth > 0 && e.children.length <= 2;
            }).map(function(e) {
                var r = e.getBoundingClientRect();
                return {tag: e.tagName, text: t, y: Math.round(r.y), x: Math.round(r.x),
                    w: e.offsetWidth, h: e.offsetHeight};
            });
        }""")
        print(f"\n'ID Photo' elements: {len(id_elements)}")
        for e in id_elements[:10]:
            print(f"  [{e['tag']}] ({e['x']},{e['y']}) {e['w']}x{e['h']} \"{e['text']}\"")

        pg.screenshot(path="data/debug/create_trending.png", full_page=False)
        print("\nScreenshot: data/debug/create_trending.png")
        b.close()

if __name__ == "__main__":
    main()
