"""Explore zh-tw footer language switcher and free tools section."""
import os, sys, json
from playwright.sync_api import sync_playwright

BASE_URL = "http://10.17.1.66:3001"
ZH_TW_HOME = f"{BASE_URL}/zh-tw"
DEBUG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "debug")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "debug", "zh_tw_lang_explore.json")

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

        pg.goto(ZH_TW_HOME, timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Scroll to bottom to ensure footer is fully rendered
        pg.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg.wait_for_timeout(3000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Take footer screenshot
        pg.screenshot(path=os.path.join(DEBUG_DIR, "zh_tw_footer_full.png"), full_page=False)
        pg.screenshot(path=os.path.join(DEBUG_DIR, "zh_tw_footer_fullpage.png"), full_page=True)

        # ===== Find language switcher =====
        # Strategy: Look for locale-related elements (select, dropdown, button with language text)
        # Nuxt/i18n typically uses a select or button to switch locales

        print("=== Finding language switcher ===")

        # 1. Check for any select element
        selects = pg.evaluate("""() => {
            var all = document.querySelectorAll("select");
            return Array.from(all).map(function(s) {
                var r = s.getBoundingClientRect();
                var options = Array.from(s.querySelectorAll("option")).map(function(o) {
                    return {value: o.value, text: o.textContent.trim()};
                });
                return {
                    y: Math.round(r.y),
                    visible: r.width > 0,
                    options: options,
                    html: s.outerHTML.substring(0, 500)
                };
            });
        }""")
        print(f"Select elements: {len(selects)}")
        for s in selects:
            print(f"  y={s['y']} visible={s['visible']} options={s['options']}")

        # 2. Check footer for any clickable elements that might trigger locale change
        footer_elements = pg.evaluate("""() => {
            var results = [];
            var footer = document.querySelector("footer");
            if (!footer) {
                // Try to find a footer-like element
                var candidates = document.querySelectorAll("[class*='footer'], [class*='Footer'], footer, div:last-of-type");
                for (var i = 0; i < candidates.length && !footer; i++) {
                    if (candidates[i].getBoundingClientRect().y > 3000) footer = candidates[i];
                }
            }

            // If still no footer, look at all elements in the bottom 2000px
            var scrollH = document.body.scrollHeight;

            // Find all elements that could be language-related
            var all = document.querySelectorAll(
                "select, [class*='lang'], [class*='locale'], [class*='i18n'], [class*='switch'], " +
                "button, [role='button'], [class*='dropdown'], [class*='select']"
            );
            all.forEach(function(el) {
                var r = el.getBoundingClientRect();
                if (r.y > scrollH - 2000 && r.width > 20 && r.height > 10) {
                    var text = (el.textContent || "").trim();
                    results.push({
                        tag: el.tagName,
                        text: text.substring(0, 100),
                        y: Math.round(r.y),
                        x: Math.round(r.x),
                        w: el.offsetWidth,
                        h: el.offsetHeight,
                        class: (el.className || "").toString().substring(0, 100),
                        id: el.id || "",
                        href: el.getAttribute("href") || ""
                    });
                }
            });
            return results;
        }""")

        print(f"\nFooter interactive elements ({len(footer_elements)}):")
        for e in footer_elements:
            print(f"  {e['tag']} y={e['y']} {e['w']}x{e['h']} class=\"{e['class'][:60]}\" text=\"{e['text'][:60]}\" id=\"{e['id']}\"")

        # 3. Check for elements that contain language codes or language names
        lang_patterns = pg.evaluate("""() => {
            var results = [];
            var scrollH = document.body.scrollHeight;
            document.querySelectorAll("*").forEach(function(el) {
                var text = (el.textContent || "").trim();
                var r = el.getBoundingClientRect();
                if (r.y > scrollH - 2000 && r.width > 20 && text.length > 0 && text.length < 50) {
                    // Check for language-related keywords or locale patterns
                    if (/English|中文|日本語|한국어|Deutsch|Français|Español|Português|العربية|Русский|ไทย|Tiếng|Indonesia|Italiano|Nederlands|Polski|Türkçe|हिन्दी|Melayu|Filipino|繁體|简体/gi.test(text)) {
                        results.push({
                            tag: el.tagName,
                            text: text,
                            y: Math.round(r.y),
                            class: (el.className || "").toString().substring(0, 80)
                        });
                    }
                }
            });
            return results;
        }""")
        print(f"\nLanguage-named elements in footer: {len(lang_patterns)}")
        for lp in lang_patterns:
            print(f"  {lp['tag']} y={lp['y']}: \"{lp['text']}\"")

        # 4. Explicitly look for the locale/language switch area
        # The footer HTML snippet from step 1 showed: "POKECUT語言：繁體中文免費AI工具..."
        # So "語言：" is the label, followed by "繁體中文" which is likely a clickable element
        lang_switch_area = pg.evaluate("""() => {
            var results = [];
            var scrollH = document.body.scrollHeight;

            // Search near the bottom for elements containing "語言", "Language", "Lang"
            var allElements = document.querySelectorAll("*");
            for (var i = 0; i < allElements.length; i++) {
                var el = allElements[i];
                var text = (el.textContent || "").trim();
                if (text.length > 0 && text.length < 200 && (
                    text.includes('語言') || text.includes('语言') || text.includes('Language') ||
                    text.includes('言語') || text.includes('언어') || text.includes('Sprache')
                )) {
                    var r = el.getBoundingClientRect();
                    if (r.y > scrollH - 4000) {
                        results.push({
                            tag: el.tagName,
                            text: text,
                            y: Math.round(r.y),
                            x: Math.round(r.x),
                            w: el.offsetWidth,
                            h: el.offsetHeight,
                            class: (el.className || "").toString().substring(0, 100),
                            html: el.outerHTML.substring(0, 500)
                        });
                    }
                }
            }
            return results;
        }""")
        print(f"\n'Language' keyword elements ({len(lang_switch_area)}):")
        for a in lang_switch_area:
            print(f"  {a['tag']} y={a['y']} {a['w']}x{a['h']}: \"{a['text'][:120]}\"")
            print(f"    HTML: {a['html'][:300]}")
            print()

        # 5. Find the specific locale switcher component
        # Many Nuxt i18n sites use <NuxtLink> or custom drop-downs
        # Try clicking on elements around the "語言" label
        locale_clickable = pg.evaluate("""() => {
            var results = [];
            var scrollH = document.body.scrollHeight;

            // Find the "語言" label first, then collect sibling/child clickable elements
            var allDivs = document.querySelectorAll("div");
            for (var i = 0; i < allDivs.length; i++) {
                var div = allDivs[i];
                var text = div.textContent || "";
                if (text.includes('語言') || text.includes('POKECUT')) {
                    var r = div.getBoundingClientRect();
                    if (r.y > scrollH - 4000) {
                        // Collect all child elements that might be interactive
                        var children = div.querySelectorAll("button, a, [role='button'], [class*='click'], [class*='select'], [class*='dropdown']");
                        children.forEach(function(child) {
                            var cr = child.getBoundingClientRect();
                            results.push({
                                parentType: 'div with 語言/POKECUT',
                                parentY: Math.round(r.y),
                                tag: child.tagName,
                                text: (child.textContent || "").trim().substring(0, 60),
                                y: Math.round(cr.y),
                                x: Math.round(cr.x),
                                w: child.offsetWidth,
                                h: child.offsetHeight,
                                class: (child.className || "").toString().substring(0, 100),
                                href: child.getAttribute("href") || ""
                            });
                        });

                        // Check div itself for links/buttons
                        var selfLinks = div.querySelectorAll("a[href*='/ja/'], a[href*='/ko/'], a[href*='/de/'], a[href*='/fr/'], a[href*='/pt/'], a[href*='/es/'], a[href*='/ar/'], a[href*='/ru/'], a[href*='/th/'], a[href*='/vi/'], a[href*='/id/'], a[href*='/it/'], a[href*='/nl/'], a[href*='/pl/'], a[href*='/tr/'], a[href*='/hi/'], a[href*='/ms/'], a[href*='/fil/'], a[href*='/en/'], a[href*='/zh/']");
                        selfLinks.forEach(function(link) {
                            var lr = link.getBoundingClientRect();
                            results.push({
                                parentType: 'div with 語言 (locale link)',
                                parentY: Math.round(r.y),
                                tag: 'A',
                                text: (link.textContent || "").trim().substring(0, 60),
                                y: Math.round(lr.y),
                                x: Math.round(lr.x),
                                w: link.offsetWidth,
                                h: link.offsetHeight,
                                class: (link.className || "").toString().substring(0, 100),
                                href: link.getAttribute("href")
                            });
                        });
                    }
                }
            }
            return results;
        }""")
        print(f"\nLocale-related clickable elements near '語言' ({len(locale_clickable)}):")
        for lc in locale_clickable:
            print(f"  [{lc['parentType']}] {lc['tag']} y={lc['y']} {lc['w']}x{lc['h']}: \"{lc['text']}\" href=\"{lc['href']}\"")

        # 6. Direct attempt: look for all links in locale prefix pattern
        all_locale_links = pg.evaluate("""() => {
            var locales = new Set();
            var links = document.querySelectorAll("a[href]");
            links.forEach(function(a) {
                var href = a.getAttribute("href");
                // Match locale prefix: /xx/ or /xx-xx/
                var m = href.match(/^\\/([a-z]{2}(-[a-z]{2})?)\\//);
                if (m && m[1] !== 'zh-tw') {
                    locales.add(m[1]);
                }
            });
            return Array.from(locales).sort();
        }""")
        print(f"\nAll non-zh-tw locale codes in page: {all_locale_links}")

        # 7. If nothing found yet, check the EN page to see if the footer is different
        # First check the default page for locale switch
        pg2 = ctx.new_page()
        pg2.goto(f"{BASE_URL}/en", timeout=60000)
        try:
            pg2.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg2.wait_for_timeout(5000)
        dismiss_overlay(pg2)
        pg2.wait_for_timeout(1000)
        pg2.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        pg2.wait_for_timeout(3000)
        dismiss_overlay(pg2)
        pg2.wait_for_timeout(1000)

        # Find language switcher on EN page
        en_lang_switch = pg2.evaluate("""() => {
            var results = [];
            var scrollH = document.body.scrollHeight;

            // Search for language-related elements
            var all = document.querySelectorAll("*");
            for (var i = 0; i < all.length; i++) {
                var el = all[i];
                var text = (el.textContent || "").trim();
                var r = el.getBoundingClientRect();
                if (r.y > scrollH - 2000 && text.length > 0 && text.length < 80 && (
                    text === 'English' || text === 'Language' ||
                    text.includes('繁體') || text.includes('简体') || text.includes('中文') ||
                    /^[A-Z][a-z]+$/.test(text)
                )) {
                    // Only collect elements that look like language options
                    var parent = el.parentElement;
                    var siblings = parent ? parent.children.length : 0;
                    if (siblings >= 3 || el.tagName === 'BUTTON' || el.tagName === 'A' || el.tagName === 'SELECT' || el.tagName === 'OPTION') {
                        results.push({
                            tag: el.tagName,
                            text: text,
                            y: Math.round(r.y),
                            x: Math.round(r.x),
                            w: el.offsetWidth,
                            h: el.offsetHeight,
                            class: (el.className || "").toString().substring(0, 80),
                            href: el.getAttribute("href") || "",
                            parentTag: parent ? parent.tagName : "",
                            siblingCount: siblings
                        });
                    }
                }
            }
            return results;
        }""")
        print(f"\n=== /en page language elements ({len(en_lang_switch)}) ===")
        for e in en_lang_switch:
            print(f"  {e['tag']} y={e['y']} {e['w']}x{e['h']}: \"{e['text']}\" parent={e['parentTag']} siblings={e['siblingCount']} href=\"{e['href']}\"")

        # Also check /en footer locale links
        en_locales = pg2.evaluate("""() => {
            var locales = new Set();
            var links = document.querySelectorAll("a[href]");
            links.forEach(function(a) {
                var href = a.getAttribute("href");
                var m = href.match(/^\\/([a-z]{2}(-[a-z]{2})?)\\//);
                if (m) locales.add(m[1]);
            });
            return Array.from(locales).sort();
        }""")
        print(f"\n/en page locale codes: {en_locales}")

        pg2.screenshot(path=os.path.join(DEBUG_DIR, "en_footer.png"), full_page=False)

        # 8. Try to find the language switch by checking the HTML structure of the footer
        # Look at the raw HTML near the bottom
        footer_html = pg.evaluate("""() => {
            var scrollH = document.body.scrollHeight;
            // Get elements within the bottom 3000px
            var bottomElements = [];
            document.querySelectorAll("div, footer").forEach(function(el) {
                var r = el.getBoundingClientRect();
                if (r.y > scrollH - 3000 && r.width > 100 && el.offsetHeight > 30) {
                    var text = (el.textContent || "").trim().substring(0, 150);
                    if (text.includes('POKECUT') || text.includes('語言') || text.includes('Language')) {
                        bottomElements.push({
                            y: Math.round(r.y),
                            h: el.offsetHeight,
                            text: text,
                            children: el.children.length,
                            class: (el.className || "").toString().substring(0, 100),
                            innerHTML: el.innerHTML.substring(0, 2000)
                        });
                    }
                }
            });
            return bottomElements;
        }""")
        print(f"\n=== Footer HTML sections ===")
        for fe in footer_html:
            print(f"\n  y={fe['y']} h={fe['h']} children={fe['children']} class=\"{fe['class'][:80]}\"")
            print(f"  Text: \"{fe['text'][:150]}\"")
            print(f"  InnerHTML (first 500): {fe['innerHTML'][:500]}")

        pg2.close()

        # Save results
        output = {
            "selects": selects,
            "footer_elements": footer_elements,
            "lang_patterns": lang_patterns,
            "lang_switch_area": lang_switch_area,
            "locale_clickable": locale_clickable,
            "all_locale_links": all_locale_links,
            "en_lang_switch": en_lang_switch,
            "en_locales": en_locales,
            "footer_html_sections": footer_html
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n\nResults saved to: {OUTPUT_FILE}")
        b.close()

if __name__ == "__main__":
    main()
