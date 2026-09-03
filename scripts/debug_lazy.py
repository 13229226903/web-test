"""Debug: check how many lazy images load on a tool page."""
import sys
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    pg = ctx.new_page()
    pg.goto("http://10.17.1.66:3002/tools/background-remover", timeout=120000)
    try: pg.wait_for_load_state("networkidle", timeout=30000)
    except: pass
    pg.wait_for_timeout(3000)

    def check_imgs(label):
        info = pg.evaluate("""() => {
            var imgs = document.querySelectorAll("img");
            var total = imgs.length;
            var visible = 0, hidden = 0, loading_lazy = 0, loaded = 0, failed = 0, tiny = 0;
            for (var i = 0; i < imgs.length; i++) {
                var img = imgs[i];
                if (img.offsetWidth > 50 && img.offsetHeight > 50) visible++;
                else if (img.offsetWidth > 0) tiny++;
                else hidden++;
                if (img.loading === "lazy") loading_lazy++;
                if (img.complete && img.naturalWidth > 0) loaded++;
                else if (img.complete && img.naturalWidth === 0) failed++;
            }
            return {total, visible, hidden, tiny, loading_lazy, loaded, failed};
        }""")
        print(f"[{label}] total={info['total']} visible={info['visible']} hidden={info['hidden']} "
              f"tiny={info['tiny']} lazy={info['loading_lazy']} loaded={info['loaded']} failed={info['failed']}")

    check_imgs("after page load")

    # Try current lazy_scroll approach
    pg.evaluate("""() => {
        var h = document.body.scrollHeight;
        var step = window.innerHeight;
        for (var y = step; y < h; y += step) {
            window.scrollTo(0, y);
        }
        window.scrollTo(0, 0);
    }""")
    pg.wait_for_timeout(2000)
    check_imgs("after fast scrollTo")

    # Try mouse.wheel approach
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    pg.wait_for_timeout(1000)
    for _ in range(12):
        pg.mouse.wheel(0, -400)
        pg.wait_for_timeout(300)
    pg.wait_for_timeout(2000)
    check_imgs("after mouse.wheel scroll")

    # Try force-eager approach
    pg.evaluate("""() => {
        document.querySelectorAll('img[loading="lazy"]').forEach(function(img) {
            img.loading = 'eager';
            var src = img.getAttribute('src');
            if (src) { img.removeAttribute('src'); img.setAttribute('src', src); }
        });
    }""")
    pg.wait_for_timeout(3000)
    check_imgs("after force eager")

    # Also try scrollIntoView on hidden images
    pg.evaluate("""() => {
        document.querySelectorAll('img').forEach(function(img) {
            if (img.offsetWidth === 0 && img.offsetHeight === 0 && img.loading === 'lazy') {
                img.scrollIntoView({block: 'center'});
            }
        });
    }""")
    pg.wait_for_timeout(3000)
    check_imgs("after scrollIntoView")

    pg.screenshot(path="data/debug/lazy_load_test.png", full_page=True)
    print("Screenshot saved to data/debug/lazy_load_test.png")
    b.close()
