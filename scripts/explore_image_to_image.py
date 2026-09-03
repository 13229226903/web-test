"""Explore image-to-image-ai post-upload button state."""
import os, sys, glob
from playwright.sync_api import sync_playwright

def main():
    td = os.path.join(os.path.dirname(__file__), "..", "test_images")
    imgs = sorted(glob.glob(os.path.join(td, "*")), key=lambda f: os.path.getsize(f))
    test_img = os.path.abspath(imgs[0])
    print(f"Test image: {os.path.basename(test_img)}")

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        pg = ctx.new_page()

        # Login
        pg.goto("http://10.17.1.66:3002"); pg.wait_for_timeout(5000)
        pg.get_by_text("Log in", exact=True).first.click(); pg.wait_for_timeout(3000)
        pg.locator('input[type="email"]').fill("450832596@qq.com")
        pg.locator('input[placeholder="Verification Code"]').fill("123456")
        pg.evaluate("""() => {var bs=document.querySelectorAll("button");for(var i=0;i<bs.length;i++){if(bs[i].textContent.trim()==="Log in"&&bs[i].offsetWidth>200){bs[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
        pg.wait_for_timeout(10000)
        pg.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove()})}""")
        pg.wait_for_timeout(2000)
        print("Login OK")

        pg2 = ctx.new_page()
        pg2.goto("http://10.17.1.66:3002/image-to-image-ai", timeout=60000)
        try: pg2.wait_for_load_state("networkidle", timeout=30000)
        except: pass
        pg2.wait_for_timeout(5000)
        pg2.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove()})}""")
        pg2.wait_for_timeout(1000)

        # Find upload button
        upload_btn = pg2.locator("button img[src*='create_generate_icon_upload_image']")
        print(f"Upload buttons found: {upload_btn.count()}")

        # Also find all buttons with imgs
        all_btn_imgs = pg2.evaluate("""() => {
            var btns = document.querySelectorAll("button img");
            return Array.from(btns).map(function(img) {
                var src = (img.src || "").substring(0, 120);
                var parent = img.parentElement;
                var r = parent.getBoundingClientRect();
                return {src: src, y: Math.round(r.y), x: Math.round(r.x), w: parent.offsetWidth, h: parent.offsetHeight};
            });
        }""")
        print("All button images:")
        for bi in all_btn_imgs:
            print(f"  y={bi['y']} {bi['w']}x{bi['h']} src={bi['src'][-80:]}")

        if upload_btn.count() > 0:
            # Click upload button
            with pg2.expect_file_chooser(timeout=10000) as fc:
                upload_btn.first.click()
            fc.value.set_files(test_img)
            print("File uploaded via upload button")
        else:
            print("No upload button found, using set_input_files")
            pg2.locator("input[type=file]").first.set_input_files(test_img)

        pg2.wait_for_timeout(15000)
        pg2.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(function(o){var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba")&&(bg.includes("0.3")||bg.includes("0.5")))o.remove()})}""")
        pg2.wait_for_timeout(1000)

        print(f"\nAfter upload URL: {pg2.url}")

        # Check for generate button
        gen_btns = pg2.evaluate("""() => {
            var btns = document.querySelectorAll("button");
            return Array.from(btns).filter(function(b) {
                return b.offsetWidth > 30 && b.offsetHeight > 30;
            }).map(function(b) {
                var r = b.getBoundingClientRect();
                var cls = (b.className || "").substring(0, 80);
                var imgs = b.querySelectorAll("img");
                var imgSrcs = Array.from(imgs).map(function(i) { return (i.src || "").substring(0, 80); });
                return {text: b.textContent.trim().substring(0, 40), y: Math.round(r.y), x: Math.round(r.x),
                        w: b.offsetWidth, h: b.offsetHeight, cls: cls, imgs: imgSrcs};
            });
        }""")
        print(f"\nVisible buttons after upload ({len(gen_btns)}):")
        for btn in gen_btns:
            img_info = ", ".join(btn["imgs"]) if btn["imgs"] else "no img"
            print(f"  y={btn['y']} {btn['w']}x{btn['h']} text=\"{btn['text']}\" cls=\"{btn['cls'][:60]}\" imgs=[{img_info}]")

        pg2.screenshot(path="data/debug/image_to_image_post_upload.png", full_page=True)
        pg2.close()
        b.close()

if __name__ == "__main__":
    main()
