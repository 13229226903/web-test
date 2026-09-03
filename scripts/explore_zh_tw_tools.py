"""Explore zh-tw homepage 'Free Tools' (免費工具) section."""
import os, sys, json, glob
from playwright.sync_api import sync_playwright

BASE_URL = "http://10.17.1.66:3001"
ZH_TW_HOME = f"{BASE_URL}/zh-tw"
DEBUG_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "debug")
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "debug", "zh_tw_explore.json")

def dismiss_overlay(page):
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
            var bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes('rgba')) o.remove();
        });
    }""")

def scroll_down(page, steps=4):
    """Scroll down in steps to trigger lazy loading."""
    for i in range(steps):
        page.evaluate(f"window.scrollBy(0, {1500})")
        page.wait_for_timeout(800)

def scroll_to_bottom(page):
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(1500)

def main():
    os.makedirs(DEBUG_DIR, exist_ok=True)

    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-TW"
        )
        pg = ctx.new_page()

        # ========== STEP 1: Explore zh-tw homepage ==========
        print("=" * 60)
        print("STEP 1: Exploring zh-tw homepage")
        print("=" * 60)

        pg.goto(ZH_TW_HOME, timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)

        # Scroll to trigger lazy loading
        scroll_down(pg, steps=6)
        pg.wait_for_timeout(2000)
        scroll_to_bottom(pg)
        pg.wait_for_timeout(2000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Save full page screenshot
        pg.screenshot(path=os.path.join(DEBUG_DIR, "zh_tw_homepage.png"), full_page=True)
        print("Saved screenshot: zh_tw_homepage.png")

        # Extract page title
        title = pg.title()
        print(f"Page title: {title}")

        # Get all body text for keyword analysis
        body_text = pg.locator("body").inner_text()
        # Find sections that might be "free tools"
        # Search for relevant keywords in zh-TW
        keywords = ["免費", "免费", "Free", "免費工具", "工具", "Tools", "Free Tools"]
        lines = body_text.splitlines()
        candidate_lines = []
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            for kw in keywords:
                if kw.lower() in line_stripped.lower():
                    candidate_lines.append((i, line_stripped))
                    break

        print("\nCandidate lines with free/tools keywords:")
        for idx, line in candidate_lines:
            print(f"  [{idx}] {line[:120]}")

        # Get all links in the page
        links_data = pg.evaluate("""() => {
            var links = document.querySelectorAll("a[href]");
            var results = [];
            links.forEach(function(a) {
                var href = a.getAttribute("href");
                var text = (a.textContent || "").trim().substring(0, 80);
                var r = a.getBoundingClientRect();
                if (href && !href.startsWith("#") && !href.startsWith("javascript:")) {
                    results.push({
                        href: href,
                        text: text,
                        y: Math.round(r.y),
                        visible: r.width > 0
                    });
                }
            });
            return results;
        }""")

        # Filter to /tools/ paths
        tool_links = [l for l in links_data if "/tools/" in l["href"]]
        print(f"\nAll /tools/ links on page ({len(tool_links)}):")
        for l in tool_links:
            print(f"  {l['href']} | y={l['y']} | visible={l['visible']} | text=\"{l['text'][:60]}\"")

        # ========== STEP 2: Find the "Free Tools" section and its tool cards ==========
        print("\n" + "=" * 60)
        print("STEP 2: Finding 'Free Tools' (免費工具) section")
        print("=" * 60)

        # Look for the section with free tools - check for section headings
        sections = pg.evaluate("""() => {
            var headings = document.querySelectorAll("h1, h2, h3, h4, h5, h6, p, span, div");
            var results = [];
            headings.forEach(function(el) {
                var text = (el.textContent || "").trim().substring(0, 100);
                var r = el.getBoundingClientRect();
                if ((text.includes('免費') || text.includes('Free') || text.includes('工具') || text.includes('Tools')) &&
                    r.width > 30 && r.y > 200) {
                    results.push({
                        tag: el.tagName,
                        text: text,
                        y: Math.round(r.y),
                        x: Math.round(r.x),
                        class: (el.className || "").toString().substring(0, 80)
                    });
                }
            });
            return results;
        }""")

        print("\nElements matching 'free/tools' heading keywords:")
        for s in sections:
            print(f"  {s['tag']} y={s['y']}: \"{s['text'][:80]}\" class=\"{s['class'][:60]}\"")

        # Now collect cards within the free tools section area
        # Strategy: find all anchor elements that look like tool cards near the free tools section
        # We need to find the free tools section y-range first
        free_tools_y = None
        for s in sections:
            if any(kw in s['text'] for kw in ['免費工具', 'Free Tools', '免费工具']):
                free_tools_y = s['y']
                print(f"\nFound Free Tools section at y={free_tools_y}: \"{s['text']}\"")
                break

        if free_tools_y is None:
            # Fallback: use any line with "免費" and "工具"
            for s in sections:
                if '免費' in s['text']:
                    free_tools_y = s['y']
                    print(f"\nFallback Free Tools section at y={free_tools_y}: \"{s['text']}\"")
                    break

        # Now find all tool cards within this section area
        # Collect cards: look for clickable card-like elements with image + text
        tool_cards = pg.evaluate(f"""(free_tools_y) => {{
            var free_tools_y = {free_tools_y if free_tools_y else 0};
            var cards = [];

            // Strategy 1: Find all anchors (a[href]) within a reasonable y-range below the heading
            var allLinks = document.querySelectorAll("a[href]");
            allLinks.forEach(function(a) {{
                var r = a.getBoundingClientRect();
                var text = (a.textContent || "").trim();
                var href = a.getAttribute("href");

                // If we have free_tools_y, filter by y range
                if (free_tools_y > 0) {{
                    if (r.y < free_tools_y || r.y > free_tools_y + 3000) return;
                }}

                // Only collect links that look like cards (have image or icon children, or are in a card container)
                var hasImg = a.querySelector("img, svg");
                var isToolCard = href.includes("/tools/") || href.includes("/zh-tw/tools/");

                if (isToolCard || hasImg) {{
                    cards.push({{
                        href: href,
                        text: text.substring(0, 80),
                        y: Math.round(r.y),
                        x: Math.round(r.x),
                        w: a.offsetWidth,
                        h: a.offsetHeight,
                        hasImg: !!hasImg,
                        isToolCard: isToolCard
                    }});
                }}
            }});

            // Strategy 2: Find card containers (divs) that look like tool cards
            // Many Vue SPA tool cards are divs, not anchors
            var divs = document.querySelectorAll("div");
            divs.forEach(function(div) {{
                var r = div.getBoundingClientRect();
                if (r.width < 100 || r.height < 80) return;
                if (free_tools_y > 0) {{
                    if (r.y < free_tools_y || r.y > free_tools_y + 3000) return;
                }}

                var text = (div.textContent || "").trim();
                // Check if this div looks like a standalone card (has image + single line text)
                var imgs = div.querySelectorAll("img, svg");
                var links = div.querySelectorAll("a[href]");

                if (links.length > 0 && imgs.length > 0 && text.length < 100) {{
                    cards.push({{
                        href: links[0].getAttribute("href"),
                        text: text.substring(0, 80),
                        y: Math.round(r.y),
                        x: Math.round(r.x),
                        w: div.offsetWidth,
                        h: div.offsetHeight,
                        hasImg: true,
                        isToolCard: false
                    }});
                }}
            }});

            // Deduplicate by href+text
            var seen = new Set();
            var deduped = [];
            cards.forEach(function(c) {{
                var key = c.href + "|" + c.text;
                if (!seen.has(key)) {{
                    seen.add(key);
                    deduped.push(c);
                }}
            }});
            return deduped;
        }}
        """, free_tools_y)

        print(f"\nTool cards found in Free Tools area ({len(tool_cards)}):")
        for c in sorted(tool_cards, key=lambda x: (x['y'] or 0)):
            print(f"  y={c['y']} {c['w']}x{c['h']} | {c['href']} | \"{c['text'][:60]}\" | hasImg={c['hasImg']}")

        # Also collect more broadly - ALL /tools/ links anywhere on page with their CTA
        all_potential_cards = pg.evaluate("""() => {
            var results = [];

            // Find all div elements that could be cards
            document.querySelectorAll("div").forEach(function(div) {
                var r = div.getBoundingClientRect();
                if (r.width < 80 || r.height < 60 || r.y < 100 || r.y > 20000) return;

                var links = div.querySelectorAll("a[href]");
                if (links.length === 0) return;

                var firstLink = links[0].getAttribute("href");
                if (!firstLink || (!firstLink.includes("/tools/") && !firstLink.includes("/zh-tw/tools/"))) return;

                var text = (div.textContent || "").trim();
                // Find button text within this card
                var buttons = div.querySelectorAll("button");
                var btnTexts = [];
                buttons.forEach(function(b) {
                    var bt = (b.textContent || "").trim();
                    if (bt) btnTexts.push(bt);
                });

                // Get the main text (excluding button text)
                var mainText = text;
                btnTexts.forEach(function(bt) { mainText = mainText.replace(bt, "").trim(); });

                results.push({
                    href: firstLink,
                    text: mainText.substring(0, 80),
                    btnText: btnTexts.length > 0 ? btnTexts[0] : "",
                    y: Math.round(r.y),
                    x: Math.round(r.x),
                    w: div.offsetWidth,
                    h: div.offsetHeight
                });
            });

            // Also check standalone a[href] links
            document.querySelectorAll("a[href]").forEach(function(a) {
                var href = a.getAttribute("href");
                if (!href || (!href.includes("/tools/") && !href.includes("/zh-tw/tools/"))) return;
                var r = a.getBoundingClientRect();
                if (r.width < 40 || r.height < 20 || r.y < 100 || r.y > 20000) return;
                var text = (a.textContent || "").trim();
                var buttons = a.querySelectorAll("button");
                var btnTexts = [];
                buttons.forEach(function(b) {
                    var bt = (b.textContent || "").trim();
                    if (bt) btnTexts.push(bt);
                });

                results.push({
                    href: href,
                    text: text.substring(0, 80),
                    btnText: btnTexts.length > 0 ? btnTexts[0] : "",
                    y: Math.round(r.y),
                    x: Math.round(r.x),
                    w: a.offsetWidth,
                    h: a.offsetHeight
                });
            });

            // Deduplicate
            var seen = new Set();
            var deduped = [];
            results.forEach(function(r) {
                var key = r.href + "|" + r.text.substring(0, 30) + "|" + r.y;
                if (!seen.has(key)) {
                    seen.add(key);
                    deduped.push(r);
                }
            });
            return deduped;
        }""")

        print(f"\nAll /tools/ card elements on page ({len(all_potential_cards)}):")
        for c in sorted(all_potential_cards, key=lambda x: (x['y'] or 0)):
            print(f"  y={c['y']} {c['w']}x{c['h']} | {c['href']} | text=\"{c['text'][:60]}\" | btn=\"{c['btnText']}\"")

        # ========== STEP 3: Iterate each tool page ==========
        # Collect unique tool paths from the discovered cards
        unique_paths = set()
        for c in all_potential_cards:
            href = c['href']
            # Normalize: remove /zh-tw prefix if present to get the canonical path
            if href.startswith("/zh-tw/"):
                href = href[6:]  # Remove "/zh-tw" prefix
            if href.startswith("/tools/") and href != "/tools/" and href != "/tools":
                unique_paths.add(href)

        print(f"\n" + "=" * 60)
        print(f"STEP 3: Exploring {len(unique_paths)} unique tool pages")
        print("=" * 60)
        print(f"Paths: {sorted(unique_paths)}")

        tool_page_details = []

        for tool_path in sorted(unique_paths):
            zh_path = f"/zh-tw{tool_path}"
            url = f"{BASE_URL}{zh_path}"
            print(f"\n--- Exploring: {url} ---")

            pg2 = ctx.new_page()
            try:
                pg2.goto(url, timeout=60000)
                try:
                    pg2.wait_for_load_state("networkidle", timeout=30000)
                except Exception:
                    pass
                pg2.wait_for_timeout(5000)
                dismiss_overlay(pg2)
                pg2.wait_for_timeout(1000)

                # Take screenshot
                safe_name = tool_path.replace("/", "_").replace("-", "_")
                pg2.screenshot(path=os.path.join(DEBUG_DIR, f"tool_{safe_name}.png"), full_page=True)

                detail = {
                    "path": tool_path,
                    "zh_tw_url": url,
                    "actual_url": pg2.url,
                    "title": pg2.title(),
                }

                # Collect h1
                h1s = pg.locator("h1").all()
                detail["h1s"] = []
                for h1 in h1s[:5]:
                    try:
                        detail["h1s"].append(h1.inner_text().strip()[:100])
                    except Exception:
                        pass

                # Collect visible buttons as CTAs
                btns = pg2.evaluate("""() => {
                    var all = document.querySelectorAll("button, a[role='button']");
                    return Array.from(all).filter(function(b) {
                        return b.offsetWidth > 50 && b.offsetHeight > 20;
                    }).map(function(b) {
                        var r = b.getBoundingClientRect();
                        return {
                            text: (b.textContent || "").trim().substring(0, 60),
                            y: Math.round(r.y),
                            x: Math.round(r.x),
                            w: b.offsetWidth,
                            h: b.offsetHeight,
                            tag: b.tagName
                        };
                    });
                }""")
                detail["cta_buttons"] = [b for b in btns if b["y"] < 3000]

                # Check for file input
                file_inputs = pg2.locator("input[type=file]").count()
                detail["file_input_count"] = file_inputs

                # Count visible images (excluding icons)
                img_count = pg2.evaluate("""() => {
                    var imgs = document.querySelectorAll("img:not([width='1']):not([height='1'])");
                    var count = 0;
                    imgs.forEach(function(img) {
                        if (img.offsetWidth > 30 && img.offsetHeight > 30) count++;
                    });
                    return count;
                }""")
                detail["visible_images"] = img_count

                # Detect interaction mode
                detail["interaction_mode"] = "unknown"
                page_text = pg2.locator("body").inner_text()[:500]

                if file_inputs > 0:
                    # Check if there's an upload flow
                    detail["interaction_mode"] = "upload_to_process"
                elif any("上傳" in b["text"] or "Upload" in b["text"] for b in detail["cta_buttons"]):
                    detail["interaction_mode"] = "upload_to_process"
                else:
                    # Might be content page, info page, or redirect
                    detail["interaction_mode"] = "info_or_content"

                # Collect some body text for context
                detail["body_text_preview"] = page_text[:200]

                print(f"  Title: {detail['title'][:80]}")
                print(f"  H1s: {detail['h1s']}")
                print(f"  File inputs: {file_inputs}")
                print(f"  Visible images: {img_count}")
                print(f"  Interaction mode: {detail['interaction_mode']}")
                print(f"  CTAs: {[(b['text'][:40], b['y']) for b in detail['cta_buttons']]}")

                tool_page_details.append(detail)
            except Exception as e:
                print(f"  ERROR: {e}")
                tool_page_details.append({
                    "path": tool_path,
                    "zh_tw_url": url,
                    "error": str(e)
                })
            finally:
                pg2.close()

        # ========== STEP 4: Explore language switcher ==========
        print("\n" + "=" * 60)
        print("STEP 4: Exploring language switcher")
        print("=" * 60)

        pg.goto(ZH_TW_HOME, timeout=60000)
        try:
            pg.wait_for_load_state("networkidle", timeout=30000)
        except Exception:
            pass
        pg.wait_for_timeout(5000)
        scroll_to_bottom(pg)
        pg.wait_for_timeout(2000)
        dismiss_overlay(pg)
        pg.wait_for_timeout(1000)

        # Save footer screenshot
        pg.screenshot(path=os.path.join(DEBUG_DIR, "zh_tw_footer.png"), full_page=True)

        # Find language switcher in footer
        lang_data = pg.evaluate("""() => {
            var results = {languages: [], switcher_found: false};

            // Look for language dropdown or locale selector
            // Nuxt i18n often uses locale selectors
            var langLinks = document.querySelectorAll(
                "a[href*='/zh-tw/'], a[href*='/ja/'], a[href*='/ko/'], a[href*='/de/'], " +
                "a[href*='/fr/'], a[href*='/pt/'], a[href*='/es/'], a[href*='/ar/'], " +
                "a[href*='/ru/'], a[href*='/th/'], a[href*='/vi/'], a[href*='/id/'], " +
                "a[href*='/it/'], a[href*='/nl/'], a[href*='/pl/'], a[href*='/tr/'], " +
                "a[href*='/hi/'], a[href*='/ms/'], a[href*='/fil/']"
            );

            var langs = new Set();
            langLinks.forEach(function(a) {
                var href = a.getAttribute("href");
                var match = href.match(/^\/([a-z]{2}(-[a-z]{2})?)\//);
                if (match) {
                    langs.add(match[1]);
                }
            });

            results.languages = Array.from(langs).sort();
            results.switcher_found = langs.size > 0;

            // Also check for select/button with language names
            var localeSelect = document.querySelector("select, [class*='locale'], [class*='lang'], [class*='language']");
            if (localeSelect) {
                results.selector_html = localeSelect.outerHTML.substring(0, 300);
            }

            // Get all unique locale-prefixed paths from the footer
            var allLinks = document.querySelectorAll("a[href]");
            var localeMap = {};
            allLinks.forEach(function(a) {
                var href = a.getAttribute("href");
                var match = href.match(/^\/([a-z]{2}(-[a-z]{2})?)\//);
                if (match && !localeMap[match[1]]) {
                    localeMap[match[1]] = href;
                }
            });
            results.locale_links = localeMap;

            return results;
        }""")

        print(f"Language switcher found: {lang_data['switcher_found']}")
        print(f"Languages: {lang_data['languages']}")
        print(f"Locale links: {json.dumps(lang_data.get('locale_links', {}), indent=2)}")

        # Also check for a language dropdown directly
        # Look for elements containing language code indicators
        lang_dropdown = pg.evaluate("""() => {
            var results = [];
            var all = document.querySelectorAll("[class*='lang'], [class*='locale'], [class*='i18n'], " +
                "select, [class*='switch'], button, a");
            all.forEach(function(el) {
                var text = (el.textContent || "").trim();
                var r = el.getBoundingClientRect();
                // Only consider elements near the footer
                if (r.y > document.body.scrollHeight - 1000 && r.width > 20) {
                    if (text.length < 30 && text.length > 1) {
                        results.push({
                            tag: el.tagName,
                            text: text,
                            y: Math.round(r.y),
                            href: el.getAttribute("href") || "",
                            class: (el.className || "").toString().substring(0, 60)
                        });
                    }
                }
            });
            return results;
        }""")

        # Collect unique languages from footer links
        footer_links = pg.evaluate("""() => {
            var results = [];
            var all = document.querySelectorAll("footer a[href], footer a[href] *, div a[href]");
            all.forEach(function(el) {
                var href = el.getAttribute("href") || el.closest("a")?.getAttribute("href");
                if (!href) return;
                var match = href.match(/^\/([a-z]{2}(-[a-z]{2})?)\//);
                if (match) {
                    results.push({locale: match[1], href: href});
                }
            });
            return results;
        }""")
        print(f"\nFooter locale links: {len(footer_links)}")
        locale_set = set()
        for fl in footer_links:
            if fl['locale'] not in locale_set:
                locale_set.add(fl['locale'])
                print(f"  {fl['locale']} -> {fl['href']}")

        # Also explicitly check for the language switcher UI component
        # Many Nuxt sites have a language dropdown
        all_locale_links = pg.evaluate("""() => {
            var all = document.querySelectorAll("a[href*='/zh-tw'], a[href*='/ja/'], a[href*='/ko/'], a[href*='/de/'], " +
                "a[href*='/fr/'], a[href*='/pt/'], a[href*='/es/'], a[href*='/ar/'], a[href*='/ru/'], a[href*='/th/'], " +
                "a[href*='/vi/'], a[href*='/id/'], a[href*='/it/'], a[href*='/nl/'], a[href*='/pl/'], a[href*='/tr/'], " +
                "a[href*='/hi/'], a[href*='/ms/'], a[href*='/fil/']");
            var locales = new Set();
            all.forEach(function(a) {
                var href = a.getAttribute("href");
                var r = a.getBoundingClientRect();
                var match = href.match(/^\/([a-z]{2}(-[a-z]{2})?)\\//);
                if (match && r.y > document.body.scrollHeight - 800) {
                    locales.add(match[1]);
                }
            });
            return Array.from(locales).sort();
        }""")
        print(f"\nAll locale codes in footer: {all_locale_links}")

        # Save all results
        output = {
            "page_title": title,
            "tool_cards_in_free_tools_area": sorted(tool_cards, key=lambda x: (x['y'] or 0)),
            "all_tool_card_elements": sorted(all_potential_cards, key=lambda x: (x['y'] or 0)),
            "unique_tool_paths": sorted(unique_paths),
            "tool_page_details": tool_page_details,
            "language_switcher": lang_data,
            "footer_locale_links": footer_links,
            "all_footer_locales": all_locale_links
        }

        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)

        print(f"\n\nResults saved to: {OUTPUT_FILE}")
        print(f"Total tool pages explored: {len(tool_page_details)}")
        print(f"Languages in footer: {all_locale_links}")

        b.close()

if __name__ == "__main__":
    main()
