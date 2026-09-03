"""Click language switcher button to reveal available locales."""
import os, sys, json
from playwright.sync_api import sync_playwright

BASE_URL = "http://10.17.1.66:3001"
DEBUG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "debug")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "debug", "zh_tw_lang_options.json")

def dismiss_overlay(page):
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
            var bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes('rgba')) o.remove();
        });
    }""")

def main():
    os.makedirs(DEBUG_DIR, exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-TW"
        )
        pg = ctx.new_page()

        pg.goto(f"{BASE_URL}/zh-tw", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Scroll to footer
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(3000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Find and click the language button
        # The button text is "語言：繁體中文" but garbled in console
        # Use the class and position to locate it
        lang_btn_selector = "button.btn-bg-purple"
        try:
            lang_btn = pg.locator(lang_btn_selector).first
            lang_btn.wait_for(state="visible", timeout=5000)
            print(f"Language button found: {lang_btn.inner_text()}")

            # Try clicking with dispatchEvent (Vue component)
            pg.evaluate("""() => {
                var btn = document.querySelector("button.btn-bg-purple");
                if (btn) {
                    btn.dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                }
            }""")
            pg.wait_for_timeout(3000)

            # Take screenshot after clicking
            pg.screenshot(path=os.path.join(DEBUG_DIR, "zh_tw_lang_dropdown.png"), full_page=False)

            # Now look for dropdown/popup with language options
            # Check for newly appeared elements
            dropdown_content = pg.evaluate("""() => {
                var results = [];
                // Look for newly visible elements that look like language options
                // Check for elements containing locale codes or language names
                var all = document.querySelectorAll("[class*='dropdown'], [class*='popup'], [class*='menu'], [class*='select'], [class*='locale'], [class*='lang'], [class*='option'], [role='menu'], [role='listbox'], [role='option']");
                all.forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.width > 20 && r.height > 10 && r.y > 6000) {
                        var text = (el.textContent || "").trim();
                        if (text.length > 0 && text.length < 200) {
                            results.push({
                                tag: el.tagName,
                                text: text.substring(0, 120),
                                y: Math.round(r.y),
                                x: Math.round(r.x),
                                w: el.offsetWidth,
                                h: el.offsetHeight,
                                class: (el.className || "").toString().substring(0, 100),
                                role: el.getAttribute("role") || "",
                                visible: r.width > 0 && r.height > 0
                            });
                        }
                    }
                });

                // Also check ALL elements near the language button (y=8006)
                var nearButton = [];
                document.querySelectorAll("*").forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.y > 7500 && r.y < 8500 && r.width > 30 && r.height > 10) {
                        var text = (el.textContent || "").trim();
                        if (text.length > 0 && text.length < 150 && text !== 'POKECUT' +
                            '語言：繁體中文免費AI工具所有工具圖片拼貼製作器批量照片編輯AI圖生圖AI換圖AI 背景AI圖像生成器在線去背背景更換魔術橡皮擦畫質增強AI證件照AI擴圖資源FAQ聯繫我們隱私政策服務條款支付條款公司關於我們Download on theApp StoreGET IT ONGoogle Play' +
                            'POKECUTLanguage: EnglishFree AI ToolsAll ToolsCollage MakerBatch EditImage to ImageAI ReplaceAI BackgroundAI Image GeneratorRemove BackgroundChange BackgroundMagic EraserPhoto EnhancerID Photo MakerAI ExpandResourcesFAQContact UsPrivacy PolicyTerms of ServicePayment TermsCompanyAbout UsDownload on theApp StoreGET IT ONGoogle PlayInstagramThreadsYoutubeTiktokXDiscord' &&
                            !text.includes('POKECUT')) {
                            nearButton.push({
                                tag: el.tagName,
                                text: text,
                                y: Math.round(r.y),
                                w: el.offsetWidth,
                                h: el.offsetHeight,
                                class: (el.className || "").toString().substring(0, 80),
                                href: el.getAttribute("href") || ""
                            });
                        }
                    }
                });

                return {dropdown_elements: results, near_button: nearButton};
            }""")
            print(f"\nDropdown elements: {len(dropdown_content['dropdown_elements'])}")
            for d in dropdown_content['dropdown_elements']:
                print(f"  {d['tag']} y={d['y']} {d['w']}x{d['h']}: \"{d['text'][:80]}\" class=\"{d['class'][:60]}\" role=\"{d['role']}\"")

            print(f"\nNear-button elements: {len(dropdown_content['near_button'])}")
            for n in dropdown_content['near_button']:
                print(f"  {n['tag']} y={n['y']} {n['w']}x{n['h']}: \"{n['text']}\" href=\"{n['href']}\"")

        except Exception as e:
            print(f"Error interacting with language button: {e}")

        # Also try using mouse click at the button's location
        print("\n=== Attempt 2: Mouse click ===")
        pg.goto(f"{BASE_URL}/zh-tw", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)
        dismiss_overlay(pg)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(3000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Get button position and click
        btn_info = pg.evaluate("""() => {
            var btn = document.querySelector("button.btn-bg-purple");
            if (!btn) return null;
            var r = btn.getBoundingClientRect();
            return {x: r.x + r.width/2, y: r.y + r.height/2, text: btn.textContent.trim()};
        }""")
        print(f"Button info: {btn_info}")

        if btn_info:
            pg.mouse.click(btn_info['x'], btn_info['y'])
            pg.wait_for_timeout(3000)

            pg.screenshot(path=os.path.join(DEBUG_DIR, "zh_tw_lang_dropdown_mouse.png"), full_page=False)

            # Find new elements
            new_elements = pg.evaluate("""() => {
                var results = [];
                document.querySelectorAll("*").forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.y > 7000 && r.y < 8500 && r.width > 50 && r.height > 10) {
                        var text = (el.textContent || "").trim();
                        if (text.length > 1 && text.length < 100) {
                            results.push({
                                tag: el.tagName,
                                text: text,
                                y: Math.round(r.y),
                                x: Math.round(r.x),
                                w: el.offsetWidth,
                                h: el.offsetHeight,
                                class: (el.className || "").toString().substring(0, 100),
                                href: el.getAttribute("href") || ""
                            });
                        }
                    }
                });
                return results;
            }""")
            print(f"\nAll elements near button area after click ({len(new_elements)}):")
            for e in new_elements:
                if e['text'] != 'POKECUT':
                    print(f"  {e['tag']} y={e['y']} {e['w']}x{e['h']}: \"{e['text']}\" class=\"{e['class'][:60]}\" href=\"{e['href']}\"")

        # Try a third approach: use Playwright's built-in click with force
        print("\n=== Attempt 3: Force click + evaluate page state ===")
        pg.goto(f"{BASE_URL}/zh-tw", timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)
        dismiss_overlay(pg)
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(3000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Try force click
        lang_btn = pg.locator("button.btn-bg-purple").first
        try:
            lang_btn.click(force=True, timeout=5000)
            pg.wait_for_timeout(3000)

            # Get all visible elements in the lower area
            visible_texts = pg.evaluate("""() => {
                var results = [];
                document.querySelectorAll("div, span, button, a, li, p").forEach(function(el) {
                    var r = el.getBoundingClientRect();
                    if (r.y > 7000 && r.y < 8600 && r.width > 40 && r.height > 15) {
                        var text = (el.textContent || "").trim();
                        if (text.length > 0 && text.length < 100) {
                            results.push({
                                tag: el.tagName,
                                text: text,
                                y: Math.round(r.y),
                                x: Math.round(r.x),
                                w: el.offsetWidth,
                                h: el.offsetHeight
                            });
                        }
                    }
                });
                return results;
            }""")
            print(f"Visible elements after force click ({len(visible_texts)}):")
            # Deduplicate
            seen = set()
            for e in visible_texts:
                key = f"{e['tag']}|{e['text']}|{e['y']}"
                if key not in seen:
                    seen.add(key)
                    print(f"  {e['tag']} y={e['y']} {e['w']}x{e['h']}: \"{e['text']}\"")
        except Exception as e:
            print(f"Force click error: {e}")

        # Approach 4: Check the Nuxt i18n pattern - try navigating to other locale paths
        print("\n=== Approach 4: Probe locale paths ===")
        locales_to_probe = [
            "en", "ja", "ko", "de", "fr", "pt", "es", "ar", "ru", "th",
            "vi", "id", "it", "nl", "pl", "tr", "hi", "ms", "fil", "zh"
        ]
        working_locales = []

        for loc in locales_to_probe:
            pg2 = ctx.new_page()
            try:
                resp = pg2.goto(f"{BASE_URL}/{loc}", timeout=30000)
                pg2.wait_for_timeout(3000)
                actual_url = pg2.url
                title = pg2.title()[:80] if pg2.title() else ""

                # Check if we got a valid page (not 404)
                status = resp.status if resp else "unknown"
                if status < 400:
                    working_locales.append({
                        "locale": loc,
                        "url": actual_url,
                        "status": status,
                        "title": title
                    })
                    print(f"  {loc}: OK ({status}) -> {actual_url}")
                else:
                    print(f"  {loc}: FAIL ({status})")
            except Exception as e:
                print(f"  {loc}: ERROR {str(e)[:60]}")
            finally:
                pg2.close()

        print(f"\nWorking locales: {[w['locale'] for w in working_locales]}")

        # Save results
        output = {
            "btn_info": btn_info,
            "dropdown_content": dropdown_content if 'dropdown_content' in dir() else None,
            "new_elements_after_mouse_click": new_elements if 'new_elements' in dir() else None,
            "visible_texts_after_force_click": visible_texts if 'visible_texts' in dir() else None,
            "working_locales": working_locales
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\nResults saved to: {OUTPUT_FILE}")
        b.close()

if __name__ == "__main__":
    main()
