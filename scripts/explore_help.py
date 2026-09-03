"""Explore the Pokecut /help page using Playwright."""

import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://10.17.1.66:3102"
HELP_URL = f"{BASE_URL}/help"
OUTPUT_DIR = Path(r"D:\Test\web-test\data\debug")

def explore_help_page():
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = context.new_page()

        # --- Step 1: Navigate to /help ---
        print("[STEP] Navigating to /help ...")
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        # Extra wait for Vue SPA rendering
        page.wait_for_timeout(3000)

        current_url = page.url
        page_title = page.title()
        print(f"[INFO] URL: {current_url}")
        print(f"[INFO] Title: {page_title}")

        results["url"] = current_url
        results["title"] = page_title

        # --- Step 2: Collect headings ---
        headings = {}
        for level in ["h1", "h2", "h3"]:
            texts = page.evaluate(f"""
                Array.from(document.querySelectorAll('{level}'))
                    .map(el => el.textContent.trim())
                    .filter(t => t.length > 0)
            """)
            headings[level] = texts
            print(f"[HEADINGS] {level}: {texts}")

        results["headings"] = headings

        # --- Step 3: Collect all buttons with text ---
        buttons = page.evaluate("""
            Array.from(document.querySelectorAll(
                'button, a[class*="btn"], a[class*="button"], [role="button"]'
            ))
            .filter(el => {
                const text = el.textContent.trim();
                const rect = el.getBoundingClientRect();
                return text.length > 0 && rect.width > 0 && rect.height > 0;
            })
            .map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().replace(/\\s+/g, ' '),
                    href: el.getAttribute('href') || null,
                    target: el.getAttribute('target') || null,
                    rel: el.getAttribute('rel') || null,
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    width: Math.round(rect.width),
                    height: Math.round(rect.height),
                    id: el.id || null,
                    className: el.className || null
                };
            })
        """)
        print(f"[BUTTONS] Found {len(buttons)} buttons/links")
        for b in buttons:
            print(f"  [{b['tag']}] text='{b['text'][:80]}' href={b['href']} target={b['target']} pos=({b['x']},{b['y']})")
        results["buttons"] = buttons

        # --- Step 4: Collect all links (href) ---
        links = page.evaluate("""
            Array.from(document.querySelectorAll('a[href]'))
            .filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            })
            .map(el => {
                const rect = el.getBoundingClientRect();
                return {
                    text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 200),
                    href: el.getAttribute('href'),
                    target: el.getAttribute('target') || null,
                    rel: el.getAttribute('rel') || null,
                    x: Math.round(rect.x),
                    y: Math.round(rect.y),
                    isExternal: el.getAttribute('href') && (el.getAttribute('href').startsWith('http://') || el.getAttribute('href').startsWith('https://')),
                    opensNewWindow: el.getAttribute('target') === '_blank'
                };
            })
        """)
        print(f"[LINKS] Found {len(links)} links")
        for l in links:
            print(f"  text='{l['text'][:80]}' href={l['href']} external={l['isExternal']} newWindow={l['opensNewWindow']}")
        results["links"] = links

        # --- Step 5: Collect FAQ / collapsible panels ---
        # Look for details/summary, accordion, or common collapsible patterns
        faq_items = page.evaluate("""() => {
                // HTML5 details/summary
                let details = Array.from(document.querySelectorAll('details summary'))
                    .map(el => ({
                        type: 'details',
                        question: el.textContent.trim().replace(/\\s+/g, ' '),
                        answer: el.parentElement.textContent.trim().replace(/\\s+/g, ' ')
                    }));

                // Vue collapse / accordion patterns
                let collapsibles = Array.from(document.querySelectorAll(
                    '[class*="collapse"], [class*="accordion"], [class*="faq"], [class*="question"], [class*="panel"]'
                ))
                .filter(el => {
                    const rect = el.getBoundingClientRect();
                    return rect.width > 0 && rect.height > 0;
                })
                .map(el => ({
                    type: 'collapse',
                    tag: el.tagName.toLowerCase(),
                    text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 300),
                    className: el.className || null
                }));

                return {details, collapsibles};
            }
        """)
        print(f"[FAQ] Details elements: {len(faq_items['details'])}")
        print(f"[FAQ] Collapsible elements: {len(faq_items['collapsibles'])}")
        for d in faq_items['details']:
            print(f"  Q: {d['question'][:120]}")
        for c in faq_items['collapsibles']:
            print(f"  [{c['tag']}] {c['text'][:120]}")
        results["faq"] = faq_items

        # --- Step 6: Search functionality ---
        search_inputs = page.evaluate("""
            Array.from(document.querySelectorAll('input[type="search"], input[placeholder*="search" i], input[placeholder*="Search" i]'))
            .map(el => ({
                type: el.getAttribute('type') || 'text',
                placeholder: el.getAttribute('placeholder') || null,
                id: el.id || null,
                name: el.getAttribute('name') || null,
                ariaLabel: el.getAttribute('aria-label') || null
            }))
        """)
        print(f"[SEARCH] Found {len(search_inputs)} search inputs: {search_inputs}")
        results["search"] = search_inputs

        # --- Step 7: Contact / support entries ---
        contact_entries = page.evaluate("""
            Array.from(document.querySelectorAll('a, button, span, div'))
            .filter(el => {
                const text = el.textContent.toLowerCase();
                return text.includes('contact') || text.includes('support') || text.includes('help center') || text.includes('客服') || text.includes('联系');
            })
            .map(el => ({
                tag: el.tagName.toLowerCase(),
                text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 200),
                href: el.getAttribute('href') || null
            }))
        """)
        print(f"[CONTACT] Found {len(contact_entries)} contact/support elements: {contact_entries}")
        results["contact"] = contact_entries

        # --- Step 8: Page structure - full body text ---
        body_text = page.evaluate("document.body.innerText")
        # Print first 3000 chars
        print(f"\n[BODY TEXT] (first 3000 chars):\n{body_text[:3000]}".encode('ascii', errors='replace').decode())

        # --- Step 9: Screenshot ---
        screenshot_path = OUTPUT_DIR / "help_full.png"
        page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"\n[SCREENSHOT] Saved to {screenshot_path}")
        results["screenshot"] = str(screenshot_path)

        # --- Step 10: Check /zh/help ---
        print("\n=== Checking /zh/help ===")
        zh_url = f"{BASE_URL}/zh/help"
        resp = page.goto(zh_url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        zh_status = resp.status if resp else "unknown"
        zh_url_actual = page.url
        zh_title = page.title()
        print(f"[ZH] Status: {zh_status}, URL: {zh_url_actual}, Title: {zh_title}")

        # Collect zh headings
        zh_headings = {}
        for level in ["h1", "h2", "h3"]:
            texts = page.evaluate(f"""
                Array.from(document.querySelectorAll('{level}'))
                    .map(el => el.textContent.trim())
                    .filter(t => t.length > 0)
            """)
            zh_headings[level] = texts

        results["zh_help"] = {
            "status": zh_status,
            "url": zh_url_actual,
            "title": zh_title,
            "headings": zh_headings
        }

        # --- Step 11: Check other language variants ---
        print("\n=== Checking other language /help pages ===")
        lang_results = {}
        for lang in ["es", "fr", "de", "ja", "ko", "pt", "ru", "ar", "th", "vi", "id", "tr"]:
            lang_url = f"{BASE_URL}/{lang}/help"
            try:
                resp = page.goto(lang_url, wait_until="domcontentloaded", timeout=10000)
                page.wait_for_load_state("networkidle", timeout=5000)
                page.wait_for_timeout(1000)
                lang_results[lang] = {
                    "status": resp.status if resp else "unknown",
                    "url": page.url,
                    "title": page.title()
                }
                print(f"  [{lang}] {resp.status if resp else 'unknown'} -> {page.url} -> {page.title()}")
            except Exception as e:
                lang_results[lang] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"  [{lang}] ERROR: {e}")

        results["language_variants"] = lang_results

        # --- Step 12: Check if there's a help-specific navigation or sidebar ---
        nav_elements = page.evaluate("""
            // Go back to English help
            Array.from(document.querySelectorAll('nav, [class*="sidebar"], [class*="side-nav"], aside'))
            .filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            })
            .map(el => ({
                tag: el.tagName.toLowerCase(),
                text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 500),
                className: el.className || null
            }))
        """)
        print(f"\n[NAV/SIDEBAR] Found {len(nav_elements)} navigation elements")
        for n in nav_elements:
            print(f"  [{n['tag']}] {n['text'][:200]}")

        # Go back to /help for nav check
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        nav_elements_en = page.evaluate("""
            Array.from(document.querySelectorAll('nav, [class*="sidebar"], [class*="side-nav"], aside'))
            .filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0;
            })
            .map(el => ({
                tag: el.tagName.toLowerCase(),
                text: el.textContent.trim().replace(/\\s+/g, ' ').substring(0, 500),
                className: el.className || null
            }))
        """)
        results["nav_elements"] = nav_elements_en

        # --- Step 13: Check for help categories/topics sections ---
        page.goto(HELP_URL, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Get all major sections (div with headings)
        sections = page.evaluate("""() => {
                const sections = [];
                const headings = document.querySelectorAll('h1, h2, h3, h4');
                headings.forEach(h => {
                    const rect = h.getBoundingClientRect();
                    if (rect.width > 0 && rect.height > 0) {
                        // Get following siblings text until next heading
                        let content = '';
                        let next = h.nextElementSibling;
                        while (next && !['H1','H2','H3','H4'].includes(next.tagName)) {
                            const t = next.textContent.trim();
                            if (t) content += t + ' ';
                            next = next.nextElementSibling;
                        }
                        sections.push({
                            level: h.tagName,
                            title: h.textContent.trim().replace(/\\s+/g, ' '),
                            contentPreview: content.trim().substring(0, 500)
                        });
                    }
                });
                return sections;
            }
        """)
        print(f"\n[SECTIONS] Found {len(sections)} sections")
        for s in sections:
            print(f"  [{s['level']}] {s['title'][:120]}")
            if s['contentPreview']:
                print(f"    Content: {s['contentPreview'][:200]}...")

        results["sections"] = sections

        # --- Step 14: Screenshot of Chinese version ---
        page.goto(zh_url, wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)
        zh_screenshot_path = OUTPUT_DIR / "help_zh_full.png"
        page.screenshot(path=str(zh_screenshot_path), full_page=True)
        print(f"\n[SCREENSHOT ZH] Saved to {zh_screenshot_path}")
        results["screenshot_zh"] = str(zh_screenshot_path)

        browser.close()

    return results


if __name__ == "__main__":
    try:
        results = explore_help_page()
        # Save results as JSON for later processing
        output_json = Path(r"D:\Test\web-test\data\debug\help_exploration.json")
        # Custom JSON serialization for non-serializable objects
        output_json.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"\n[DONE] Results saved to {output_json}")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
