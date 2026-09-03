"""Comprehensive exploration of the Pokecut /help page for page-map-sync agent.

Covers 8 sections:
1. Hero search area
2. Popular search terms (tags)
3. Category cards
4. FAQ area
5. Search functionality
6. Contact support CTA
7. Multi-language
8. Mobile layout
"""

import json
import sys
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

# Force UTF-8 stdout for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

BASE_URL = "http://10.17.1.66:3102"
HELP_URL = f"{BASE_URL}/help"
OUTPUT_DIR = Path(r"D:\Test\web-test\data\debug")


def explore():
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = context.new_page()

        # =========================================================
        # SECTION 0: Navigate and full body text
        # =========================================================
        print("=" * 60)
        print("[SECTION 0] Navigate to /help")
        print("=" * 60)
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        results["url"] = page.url
        results["title"] = page.title()
        print(f"URL: {page.url}")
        print(f"Title: {page.title()}")

        full_body = page.evaluate("document.body.innerText")
        results["body_text"] = full_body[:5000]
        print(f"\nBody text length: {len(full_body)}")
        # Print safely encoding as ASCII, replacing unicode chars
        safe_text = full_body[:5000].encode('ascii', errors='replace').decode('ascii')
        print(f"Body text (first 5000 chars):\n{safe_text}")

        # =========================================================
        # SECTION 1: Hero Search Area
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 1] Hero Search Area")
        print("=" * 60)

        hero = page.evaluate("""() => {
            const heroSection = document.querySelector('section[class*="hero"], div[class*="hero"], section[class*="help-v2-hero"], div[class*="help-v2-hero"]');
            const fallback = { tag: 'not_found' };

            // Look for elements in the top portion of the page (y < 700)
            const elements = [];

            // H1 / H2 in hero area
            const headings = document.querySelectorAll('h1, h2, h3, h4');
            headings.forEach(h => {
                const rect = h.getBoundingClientRect();
                if (rect.width > 0) {
                    elements.push({
                        tag: h.tagName,
                        text: h.textContent.trim().replace(/\\s+/g, ' '),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            });

            // Paragraphs / descriptions in hero area
            const paragraphs = document.querySelectorAll('p, span[class*="desc"], span[class*="subtitle"]');
            paragraphs.forEach(p => {
                const rect = p.getBoundingClientRect();
                if (rect.width > 100 && rect.y < 700 && p.textContent.trim().length > 10) {
                    elements.push({
                        tag: p.tagName,
                        text: p.textContent.trim().replace(/\\s+/g, ' ').substring(0, 300),
                        className: p.className || null,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y)
                    });
                }
            });

            // Search input
            const inputs = document.querySelectorAll('input');
            inputs.forEach(inp => {
                const rect = inp.getBoundingClientRect();
                if (rect.width > 0 && rect.y < 800) {
                    elements.push({
                        tag: 'input',
                        type: inp.getAttribute('type'),
                        placeholder: inp.getAttribute('placeholder'),
                        className: inp.className || null,
                        id: inp.id || null,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            });

            // Search button
            const buttons = document.querySelectorAll('button, a');
            buttons.forEach(b => {
                const rect = b.getBoundingClientRect();
                const text = b.textContent.trim().toLowerCase();
                if (rect.width > 0 && rect.y < 800 && (text.includes('search') || text.includes('find'))) {
                    elements.push({
                        tag: b.tagName,
                        text: b.textContent.trim().replace(/\\s+/g, ' '),
                        className: b.className || null,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            });

            return { heroSectionFounded: !!heroSection, elements };
        }""")
        results["section1_hero"] = hero
        print(json.dumps(hero, indent=2, ensure_ascii=False))

        # =========================================================
        # SECTION 2: Popular Search Terms (tags)
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 2] Popular Search Terms")
        print("=" * 60)

        tags = page.evaluate("""() => {
            // Look for tag/chip elements in the hero area
            const tagElements = document.querySelectorAll('[class*="tag"], [class*="chip"], [class*="pill"], [class*="quick"], [class*="popular"]');
            const results = [];
            tagElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 && rect.y < 800) {
                    results.push({
                        tag: el.tagName,
                        text: el.textContent.trim().replace(/\\s+/g, ' '),
                        className: el.className || null,
                        isButton: el.tagName === 'BUTTON',
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            });

            // Also look for small buttons near the search area (popular terms)
            if (results.length === 0) {
                const allButtons = document.querySelectorAll('button');
                allButtons.forEach(b => {
                    const rect = b.getBoundingClientRect();
                    const text = b.textContent.trim();
                    if (rect.width > 0 && rect.width < 250 && rect.y > 300 && rect.y < 700 && text.length <= 30) {
                        results.push({
                            tag: 'BUTTON',
                            text: text,
                            className: b.className || null,
                            x: Math.round(rect.x),
                            y: Math.round(rect.y),
                            width: Math.round(rect.width),
                            height: Math.round(rect.height)
                        });
                    }
                });
            }
            return results;
        }""")
        results["section2_tags"] = tags
        print(f"Found {len(tags)} popular search tags:")
        for t in tags:
            cn = (t.get('className') or '')[:80]
            print(f"  [{t['tag']}] text='{t['text']}' pos=({t['x']},{t['y']}) class={cn}")

        # =========================================================
        # SECTION 3: Category Cards
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 3] Category Cards")
        print("=" * 60)

        cards = page.evaluate("""() => {
            const allElements = document.querySelectorAll('[class*="card"], [class*="category"], article, a');
            const results = [];
            allElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                const text = el.textContent.trim().replace(/\\s+/g, ' ');
                if (rect.width > 200 && rect.height > 80 && rect.y > 500 && rect.y < 2000 && text.length > 20) {
                    // Check if it contains a heading-like structure
                    const hasHeading = el.querySelector('h1, h2, h3, h4, strong, [class*="title"], [class*="heading"]');
                    const headingText = hasHeading ? hasHeading.textContent.trim() : '';
                    results.push({
                        tag: el.tagName,
                        text: text.substring(0, 200),
                        heading: headingText || text.split(/\\n|·|-/).filter(s => s.trim().length > 0)[0] || '',
                        className: el.className || null,
                        href: el.getAttribute('href') || null,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            });
            // Deduplicate by bounding box overlap
            const unique = [];
            const seen = new Set();
            results.forEach(r => {
                const key = `${r.x},${r.y},${r.width}`;
                if (!seen.has(key)) {
                    seen.add(key);
                    unique.push(r);
                }
            });
            return unique;
        }""")
        results["section3_cards"] = cards
        print(f"Found {len(cards)} category card elements:")
        for c in cards:
            print(f"  [{c['tag']}] heading='{c['heading'][:80]}' text='{c['text'][:120]}' pos=({c['x']},{c['y']}) href={c['href']}")

        # =========================================================
        # SECTION 4: FAQ Area
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 4] FAQ Area")
        print("=" * 60)

        # Get all FAQ questions and group structure
        faq_structure = page.evaluate("""() => {
            // Find FAQ sections by looking for headings followed by collapsible items
            const allElements = document.querySelectorAll('h1, h2, h3, h4, p, span, button, a');
            const groupHeadings = [];

            // First, find all group headings (likely h2/h3 with category names)
            allElements.forEach(el => {
                const rect = el.getBoundingClientRect();
                const text = el.textContent.trim().replace(/\\s+/g, ' ');
                if (['H1','H2','H3','H4'].includes(el.tagName) && rect.width > 0 && rect.y > 800) {
                    groupHeadings.push({
                        tag: el.tagName,
                        text: text,
                        y: Math.round(rect.y),
                        className: el.className || null
                    });
                }
            });

            // Find all accordion/question buttons (elements that look like FAQ items)
            const faqItems = [];
            document.querySelectorAll('button, [class*="question"], [class*="faq-item"], [class*="accordion-item"], div[class*="question"]').forEach(el => {
                const rect = el.getBoundingClientRect();
                const text = el.textContent.trim().replace(/\\s+/g, ' ');
                if (rect.width > 200 && rect.y > 800 && text.length > 5 && text.length < 300) {
                    faqItems.push({
                        tag: el.tagName,
                        text: text.substring(0, 250),
                        className: el.className || null,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        hasPlusMinus: text.includes('+') || text.includes('-') || el.innerHTML.includes('+') || el.innerHTML.includes('-')
                    });
                }
            });

            // Deduplicate FAQ items (often clickable wrapper + inner button point to same thing)
            const deduped = [];
            const seenY = new Set();
            faqItems.forEach(f => {
                const yKey = Math.round(f.y / 10) * 10;
                if (!seenY.has(yKey)) {
                    seenY.add(yKey);
                    deduped.push(f);
                }
            });

            return { groupHeadings, faqItems: deduped, totalFaqItems: deduped.length };
        }""")
        results["section4_faq"] = faq_structure
        print(f"Group headings: {len(faq_structure['groupHeadings'])}")
        for g in faq_structure['groupHeadings']:
            print(f"  [{g['tag']}] text='{g['text']}' y={g['y']}")
        print(f"\nFAQ items: {len(faq_structure['faqItems'])}")
        for f in faq_structure['faqItems']:
            cn = (f.get('className') or '')[:80]
            print(f"  [{f['tag']}] text='{f['text'][:120]}' y={f['y']} class={cn}")

        # =========================================================
        # SECTION 5: Search Functionality
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 5] Search Functionality")
        print("=" * 60)

        # Test search with keyword "credits"
        search_input_sel = "input[placeholder*='Search']"
        search_input = page.locator(search_input_sel)
        if search_input.count() > 0:
            search_input.fill("credits")
            page.wait_for_timeout(500)
            # Try clicking Search button
            search_btn = page.locator("button:has-text('Search')")
            if search_btn.count() > 0:
                box = search_btn.first.bounding_box()
                if box:
                    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    page.wait_for_timeout(3000)

            search_results_data = page.evaluate("""() => {
                const url = window.location.href;
                // Gather visible questions after search
                const visibleQuestions = [];
                document.querySelectorAll('button, [class*="question"], [class*="faq-item"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 200 && rect.y > 400) {
                        visibleQuestions.push({
                            text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 200),
                            y: Math.round(rect.y),
                            visible: rect.height > 0
                        });
                    }
                });

                // Check for "no results" message
                const noResults = document.querySelector('[class*="no-result"], [class*="empty"], [class*="not-found"]');
                const noResultsText = noResults ? noResults.textContent.trim() : null;

                return { url, visibleQuestions, noResultsText, totalVisible: visibleQuestions.length };
            }""")
            results["section5_search_credits"] = search_results_data
            print(f"Search URL: {search_results_data['url']}")
            print(f"Total visible questions: {search_results_data['totalVisible']}")
            print(f"No results text: {search_results_data['noResultsText']}")
        else:
            results["section5_search_credits"] = "search_input_not_found"

        # Test search with nonsense keyword to trigger no-results
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        search_input2 = page.locator(search_input_sel)
        if search_input2.count() > 0:
            search_input2.fill("xyznonexistent123")
            page.wait_for_timeout(500)
            search_btn2 = page.locator("button:has-text('Search')")
            if search_btn2.count() > 0:
                box = search_btn2.first.bounding_box()
                if box:
                    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    page.wait_for_timeout(3000)

            no_results_data = page.evaluate("""() => {
                const url = window.location.href;
                const visibleQuestions = [];
                document.querySelectorAll('button, [class*="question"], [class*="faq-item"]').forEach(el => {
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 200 && rect.y > 400 && rect.height > 0) {
                        visibleQuestions.push(el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 100));
                    }
                });

                // Check entire body text for no-results indicators
                const bodyText = document.body.innerText;
                const hasNoResults = bodyText.toLowerCase().includes('no result') || bodyText.toLowerCase().includes('no questions') || bodyText.toLowerCase().includes('no faq') || bodyText.includes('0 result');

                return { url, visibleQuestions, totalVisible: visibleQuestions.length, hasNoResults };
            }""")
            results["section5_search_noresults"] = no_results_data
            print(f"No-results URL: {no_results_data['url']}")
            print(f"Visible questions after nonsense search: {no_results_data['totalVisible']}")
            print(f"Has no-results indicator: {no_results_data['hasNoResults']}")

        # =========================================================
        # SECTION 6: Contact Support CTA
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 6] Contact Support CTA")
        print("=" * 60)

        # Go back to clean help page
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        contact_section = page.evaluate("""() => {
            // Find "Still have questions?" and "Contact us" elements near bottom
            const elements = [];
            document.querySelectorAll('h1, h2, h3, h4, p, span, button, a, div').forEach(el => {
                const text = el.textContent;
                const lower = text.toLowerCase();
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0 &&
                    (lower.includes('still have questions') ||
                     lower.includes('contact us') ||
                     lower.includes('submit a ticket') ||
                     lower.includes('get in touch') ||
                     lower.includes('contact support') ||
                     lower.includes('support ticket'))) {
                    elements.push({
                        tag: el.tagName,
                        text: text.trim().replace(/\\s+/g, ' ').substring(0, 300),
                        className: el.className || null,
                        href: el.getAttribute('href') || null,
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                }
            });
            return elements;
        }""")
        results["section6_contact"] = contact_section
        print(f"Found {len(contact_section)} contact-related elements:")
        for c in contact_section:
            cn = (c.get('className') or '')[:80]
            print(f"  [{c['tag']}] text='{c['text'][:120]}' y={c['y']} href={c['href']} class={cn}")

        # Click Contact us button and check what happens
        contact_btn = page.locator("button:has-text('Contact us')")
        if contact_btn.count() == 0:
            contact_btn = page.locator("a:has-text('Contact us')")
        if contact_btn.count() == 0:
            contact_btn = page.locator("[class*='contact-us'], [class*='contact-us'] button, [class*='contact-us'] a")

        contact_click_result = "not_found"
        if contact_btn.count() > 0:
            box = contact_btn.first.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                page.wait_for_timeout(3000)

                # Check what appeared: modal? redirect? new page?
                contact_click_result = page.evaluate("""() => {
                    const url = window.location.href;
                    // Check for modal/ticket form
                    const modal = document.querySelector('[class*="modal"], [class*="dialog"], [class*="popup"], [class*="ticket"], [class*="form"]');
                    const modalText = modal ? modal.textContent.trim().replace(/\\s+/g, ' ').substring(0, 500) : null;
                    // Check for any new visible content in center
                    const centerEls = [];
                    document.querySelectorAll('div, form, section').forEach(el => {
                        const rect = el.getBoundingClientRect();
                        if (rect.width > 300 && rect.height > 100 &&
                            Math.abs(rect.x + rect.width/2 - window.innerWidth/2) < 300 &&
                            Math.abs(rect.y + rect.height/2 - window.innerHeight/2) < 300) {
                            centerEls.push({
                                text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 300),
                                className: el.className || null
                            });
                        }
                    });
                    return { url, hasModal: !!modal, modalText, centerElements: centerEls };
                }""")
        results["section6_contact_click"] = contact_click_result
        print(f"Contact us click result: {json.dumps(contact_click_result, indent=2, ensure_ascii=False)}")

        # =========================================================
        # SECTION 7: Multi-Language
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 7] Multi-Language")
        print("=" * 60)

        lang_results = {}

        # Chinese
        print("\n--- /zh/help ---")
        page.goto(f"{BASE_URL}/zh/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        zh_data = page.evaluate("""() => ({
            url: window.location.href,
            title: document.title,
            bodyText: document.body.innerText.substring(0, 2000),
            headings: {
                h1: Array.from(document.querySelectorAll('h1')).map(e => e.textContent.trim()),
                h2: Array.from(document.querySelectorAll('h2')).map(e => e.textContent.trim()),
                h3: Array.from(document.querySelectorAll('h3')).map(e => e.textContent.trim())
            }
        })""")
        lang_results["zh"] = zh_data
        print(f"URL: {zh_data['url']}, Title: {zh_data['title']}")
        zh_screenshot = OUTPUT_DIR / "help_zh_full.png"
        page.screenshot(path=str(zh_screenshot), full_page=True)
        print(f"Screenshot: {zh_screenshot}")
        results["screenshot_zh"] = str(zh_screenshot)

        # Check a few other languages
        for lang in ["es", "fr", "de", "ja", "ko"]:
            print(f"\n--- /{lang}/help ---")
            try:
                resp = page.goto(f"{BASE_URL}/{lang}/help", wait_until="domcontentloaded", timeout=10000)
                page.wait_for_load_state("networkidle", timeout=5000)
                page.wait_for_timeout(1000)
                lang_data = page.evaluate("""() => ({
                    url: window.location.href,
                    title: document.title,
                    bodyText: document.body.innerText.substring(0, 500),
                    headings: {
                        h1: Array.from(document.querySelectorAll('h1')).map(e => e.textContent.trim()),
                        h2: Array.from(document.querySelectorAll('h2')).map(e => e.textContent.trim()),
                        h3: Array.from(document.querySelectorAll('h3')).map(e => e.textContent.trim())
                    }
                })""")
                lang_results[lang] = lang_data
                print(f"  Status: {resp.status if resp else 'unknown'}, URL: {lang_data['url']}, Title: {lang_data['title']}")
            except Exception as e:
                lang_results[lang] = {"error": str(e)}
                print(f"  ERROR: {e}")

        results["section7_languages"] = lang_results

        # =========================================================
        # SECTION 8: Mobile Layout (375px)
        # =========================================================
        print("\n" + "=" * 60)
        print("[SECTION 8] Mobile Layout (375px)")
        print("=" * 60)

        # Set viewport to mobile
        page.set_viewport_size({"width": 375, "height": 812})
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        mobile_data = page.evaluate("""() => ({
            url: window.location.href,
            title: document.title,
            viewport: { width: window.innerWidth, height: window.innerHeight },

            // Hero area elements
            heroElements: Array.from(document.querySelectorAll('h1, h2, h3, h4, input, button, p'))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0 && rect.y < 500;
                })
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 150),
                    x: Math.round(el.getBoundingClientRect().x),
                    y: Math.round(el.getBoundingClientRect().y),
                    width: Math.round(el.getBoundingClientRect().width),
                    height: Math.round(el.getBoundingClientRect().height)
                })),

            // Category cards
            cardElements: Array.from(document.querySelectorAll('[class*="card"], [class*="category"], article'))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 100 && rect.height > 50 && rect.y > 300;
                })
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 150),
                    x: Math.round(el.getBoundingClientRect().x),
                    y: Math.round(el.getBoundingClientRect().y),
                    width: Math.round(el.getBoundingClientRect().width),
                    height: Math.round(el.getBoundingClientRect().height)
                })),

            // FAQ items
            faqItems: Array.from(document.querySelectorAll('button, [class*="question"]'))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 100 && rect.y > 500;
                })
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 150),
                    y: Math.round(el.getBoundingClientRect().y),
                    width: Math.round(el.getBoundingClientRect().width)
                })),

            // Contact section
            contactElements: Array.from(document.querySelectorAll('h1, h2, h3, h4, button, a, p'))
                .filter(el => {
                    const text = el.textContent.toLowerCase();
                    return text.includes('still have') || text.includes('contact us') || text.includes('get in touch');
                })
                .map(el => ({
                    tag: el.tagName,
                    text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 150),
                    y: Math.round(el.getBoundingClientRect().y)
                })),

            // Body overflow check
            bodyWidth: document.body.scrollWidth,
            hasHorizontalOverflow: document.body.scrollWidth > 375
        })""")
        results["section8_mobile"] = mobile_data
        print(f"Mobile URL: {mobile_data['url']}")
        print(f"Hero elements: {len(mobile_data['heroElements'])}")
        for e in mobile_data['heroElements']:
            print(f"  [{e['tag']}] text='{e['text'][:80]}' pos=({e['x']},{e['y']}) size=({e['width']},{e['height']})")
        print(f"Card elements: {len(mobile_data['cardElements'])}")
        for e in mobile_data['cardElements']:
            print(f"  [{e['tag']}] text='{e['text'][:80]}' pos=({e['x']},{e['y']})")
        print(f"FAQ items: {len(mobile_data['faqItems'])}")
        print(f"Contact elements: {len(mobile_data['contactElements'])}")
        print(f"Has horizontal overflow: {mobile_data['hasHorizontalOverflow']}")

        mobile_screenshot = OUTPUT_DIR / "help_mobile.png"
        page.screenshot(path=str(mobile_screenshot), full_page=True)
        print(f"Mobile screenshot: {mobile_screenshot}")
        results["screenshot_mobile"] = str(mobile_screenshot)

        # =========================================================
        # CORE SCREENSHOTS (desktop)
        # =========================================================
        page.set_viewport_size({"width": 1920, "height": 1080})
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        screenshot_full = OUTPUT_DIR / "help_full_v2.png"
        page.screenshot(path=str(screenshot_full), full_page=True)
        results["screenshot_full"] = str(screenshot_full)
        print(f"\nFull screenshot: {screenshot_full}")

        # =========================================================
        # INTERACTION: Click a tag and verify search triggers
        # =========================================================
        print("\n" + "=" * 60)
        print("[INTERACTION] Clicking 'Credits' tag")
        print("=" * 60)

        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Find Credits tag button in hero area
        credits_tag = page.locator("button:has-text('Credits')")
        tag_click_result = None
        if credits_tag.count() > 0:
            # Find the one in hero area (y < 700)
            for i in range(min(credits_tag.count(), 10)):
                box = credits_tag.nth(i).bounding_box()
                if box and box['y'] < 700 and box['width'] < 200:
                    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    page.wait_for_timeout(2000)
                    tag_click_result = page.evaluate("""() => {
                        const url = window.location.href;
                        const searchInput = document.querySelector('input[placeholder*="Search"]');
                        const searchValue = searchInput ? searchInput.value : null;
                        // Count visible FAQ
                        const visibleBtns = Array.from(document.querySelectorAll('button'))
                            .filter(b => b.getBoundingClientRect().width > 0 && b.getBoundingClientRect().y > 400)
                            .map(b => b.textContent.trim().replace(/\\s+/g, ' ').substring(0, 100));
                        return { url, searchValue, visibleButtonCount: visibleBtns.length, visibleButtons: visibleBtns.slice(0, 10) };
                    }""")
                    print(f"Tag click result: {json.dumps(tag_click_result, indent=2, ensure_ascii=False)}")
                    break
        results["interaction_tag_click"] = tag_click_result

        # =========================================================
        # INTERACTION: Click a category card and verify scroll
        # =========================================================
        print("\n" + "=" * 60)
        print("[INTERACTION] Clicking 'Getting Started' category card")
        print("=" * 60)

        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Click the Getting Started card
        gs_card = page.locator("button:has-text('Getting Started')")
        category_click_result = None
        if gs_card.count() > 0:
            for i in range(min(gs_card.count(), 10)):
                box = gs_card.nth(i).bounding_box()
                if box and box['width'] > 200:
                    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    page.wait_for_timeout(2000)
                    category_click_result = page.evaluate("""() => {
                        const url = window.location.href;
                        const scrollY = window.scrollY;
                        // Check FAQ section headings visible
                        const faqHeadings = Array.from(document.querySelectorAll('h1, h2, h3, h4'))
                            .filter(h => h.getBoundingClientRect().y > 0 && h.getBoundingClientRect().y < window.innerHeight)
                            .map(h => ({ tag: h.tagName, text: h.textContent.trim().replace(/\\s+/g, ' '), y: Math.round(h.getBoundingClientRect().y) }));
                        // Expanded articles
                        const articles = Array.from(document.querySelectorAll('article'))
                            .filter(a => a.getBoundingClientRect().height > 30)
                            .map(a => a.textContent.trim().replace(/\\s+/g, ' ').substring(0, 200));
                        return { url, scrollY, faqHeadings, expandedArticles: articles };
                    }""")
                    print(f"Category click result: {json.dumps(category_click_result, indent=2, ensure_ascii=False)}")
                    break
        results["interaction_category_click"] = category_click_result

        # =========================================================
        # INTERACTION: Expand an FAQ question
        # =========================================================
        print("\n" + "=" * 60)
        print("[INTERACTION] Expanding first FAQ question")
        print("=" * 60)

        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Click the "Getting Started" card first to filter
        gs_card2 = page.locator("button:has-text('Getting Started')")
        if gs_card2.count() > 0:
            for i in range(min(gs_card2.count(), 5)):
                box = gs_card2.nth(i).bounding_box()
                if box and box['width'] > 200:
                    page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                    page.wait_for_timeout(1500)
                    break

        # Find the first expanded/collapsible question
        faq_expand_result = page.evaluate("""() => {
            const faqButtons = Array.from(document.querySelectorAll('button'))
                .filter(b => {
                    const rect = b.getBoundingClientRect();
                    return rect.width > 200 && rect.y > 600 && rect.y < 2000 && b.textContent.trim().length > 10;
                })
                .slice(0, 5)
                .map(b => ({
                    text: b.textContent.trim().replace(/\\s+/g, ' ').substring(0, 150),
                    y: Math.round(b.getBoundingClientRect().y),
                    x: Math.round(b.getBoundingClientRect().x),
                    className: b.className || null
                }));
            return { faqButtons, count: faqButtons.length };
        }""")
        results["interaction_faq_expand"] = faq_expand_result
        print(f"FAQ buttons found: {faq_expand_result['count']}")
        for fb in faq_expand_result['faqButtons']:
            cn = (fb.get('className') or '')[:100]
            print(f"  text='{fb['text'][:100]}' y={fb['y']} class={cn}")

        # Click the first FAQ button
        if faq_expand_result['count'] > 0:
            first_faq = faq_expand_result['faqButtons'][0]
            page.mouse.click(first_faq['x'] + 100, first_faq['y'] + 10)
            page.wait_for_timeout(2000)

            after_expand = page.evaluate("""() => {
                // Get all visible articles (expanded content)
                const articles = Array.from(document.querySelectorAll('article'))
                    .filter(a => a.getBoundingClientRect().height > 30)
                    .map((a, i) => ({
                        index: i,
                        text: a.textContent.trim().replace(/\\s+/g, ' ').substring(0, 300),
                        y: Math.round(a.getBoundingClientRect().y),
                        height: Math.round(a.getBoundingClientRect().height)
                    }));
                return articles;
            }""")
            results["interaction_after_expand"] = after_expand
            print(f"Articles after expanding first FAQ: {len(after_expand)}")
            for a in after_expand:
                print(f"  [{a['index']}] text='{a['text'][:120]}...' y={a['y']} h={a['height']}")

        # Screenshot after expansion
        expanded_screenshot = OUTPUT_DIR / "help_expanded_v2.png"
        page.screenshot(path=str(expanded_screenshot), full_page=True)
        results["screenshot_expanded"] = str(expanded_screenshot)

        browser.close()

    return results


if __name__ == "__main__":
    try:
        results = explore()
        output_json = OUTPUT_DIR / "help_exploration_v2.json"
        output_json.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"\n[DONE] Results saved to {output_json}")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
