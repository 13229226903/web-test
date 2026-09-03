"""Additional exploration: FAQ question expansion and Contact us flow."""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "http://10.17.1.66:3102"
OUTPUT_DIR = Path(r"D:\Test\web-test\data\debug")

def explore_details():
    results = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = context.new_page()

        # --- Step 1: Click a Popular question to expand it ---
        print("[STEP] Clicking 'What is Pokecut and what can I use it for?' to expand...")
        page.goto(BASE_URL + "/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(3000)

        # Click the first Popular question
        q1 = page.locator("button:has-text('What is Pokecut and what can I use it for?')")
        if q1.count() > 0:
            # Use coordinate click for Vue component compatibility
            box = q1.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                page.wait_for_timeout(1500)

                # Check what content appeared after clicking
                expanded_content = page.evaluate("""() => {
                    const articles = document.querySelectorAll('article');
                    let results = [];
                    articles.forEach(a => {
                        const rect = a.getBoundingClientRect();
                        if (rect.width > 0 && rect.height > 0) {
                            results.push({
                                text: a.textContent.trim().replace(/\\s+/g, ' ').substring(0, 500),
                                height: Math.round(rect.height)
                            });
                        }
                    });
                    return results;
                }""")
                print(f"[EXPANDED] Article content after click: {expanded_content}")
                results["expanded_question"] = expanded_content
            else:
                print("[EXPANDED] Could not get bounding box for question button")
                results["expanded_question"] = "bounding_box_failed"
        else:
            print("[EXPANDED] Question button not found")
            results["expanded_question"] = "not_found"

        # --- Step 2: Click second question to check multi-expand behavior ---
        print("\n[STEP] Clicking 'Is Pokecut free?' to check multi-expand...")
        page.goto(BASE_URL + "/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        q2 = page.locator("button:has-text('Is Pokecut free?')")
        if q2.count() > 0:
            box = q2.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                page.wait_for_timeout(1500)

                # Check URL change
                print(f"[Q2] URL after click: {page.url}")

                # Get all visible article content
                articles_after = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('article'))
                        .filter(a => a.getBoundingClientRect().width > 0 && a.getBoundingClientRect().height > 0)
                        .map(a => a.textContent.trim().replace(/\\s+/g, ' ').substring(0, 300));
                }""")
                print(f"[Q2] Visible articles: {articles_after}")
                results["q2_expanded"] = {
                    "url": page.url,
                    "articles": articles_after
                }
            else:
                results["q2_expanded"] = "bounding_box_failed"
        else:
            results["q2_expanded"] = "not_found"

        # --- Step 3: Check search functionality ---
        print("\n[STEP] Testing search with 'credits'...")
        page.goto(BASE_URL + "/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        search_input = page.locator("input[placeholder*='Search by keyword']")
        if search_input.count() > 0:
            search_input.fill("credits")
            search_button = page.locator("button:has-text('Search')")
            if search_button.count() > 0:
                search_button.click()
                page.wait_for_timeout(3000)
                print(f"[SEARCH] URL after search: {page.url}")

                # Check what results appeared
                search_results = page.evaluate("""() => {
                    const articles = document.querySelectorAll('article');
                    return Array.from(articles)
                        .filter(a => a.getBoundingClientRect().width > 0)
                        .map(a => ({
                            text: a.textContent.trim().replace(/\\s+/g, ' ').substring(0, 300),
                            visible: a.getBoundingClientRect().height > 0
                        }));
                }""")
                print(f"[SEARCH] Results: {search_results}")
                results["search_test"] = {
                    "url": page.url,
                    "results": search_results
                }
            else:
                # Try pressing Enter
                search_input.press("Enter")
                page.wait_for_timeout(3000)
                print(f"[SEARCH] URL after Enter: {page.url}")
                results["search_test"] = {"url": page.url, "method": "enter"}
        else:
            print("[SEARCH] Search input not found")
            results["search_test"] = "search_input_not_found"

        # --- Step 4: Click Contact us ---
        print("\n[STEP] Clicking 'Contact us'...")
        page.goto(BASE_URL + "/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Click the bottom "Contact us" button (in "Still have questions?" section)
        contact_btn = page.locator("button.help-v2-support-cta-section__button")
        if contact_btn.count() > 0:
            box = contact_btn.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                page.wait_for_timeout(2000)
                print(f"[CONTACT] URL after click: {page.url}")
                results["contact_click"] = {"url": page.url}
            else:
                results["contact_click"] = "bounding_box_failed"
        else:
            print("[CONTACT] Bottom contact button not found, trying link...")
            contact_link = page.locator("a[href*='contact-us']")
            if contact_link.count() > 0:
                print(f"[CONTACT] Found link: {contact_link.first.get_attribute('href')}")
                results["contact_click"] = {"href": contact_link.first.get_attribute('href')}
            else:
                results["contact_click"] = "not_found"

        # --- Step 5: Check category button clicks ---
        print("\n[STEP] Clicking category 'Credits' quick-link button...")
        page.goto(BASE_URL + "/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        credits_btn = page.locator("button:has-text('Credits')")
        if credits_btn.count() > 0:
            # There might be multiple, get the one in the help hero area (y < 700)
            count = credits_btn.count()
            for i in range(count):
                try:
                    box = credits_btn.nth(i).bounding_box()
                    if box and box['y'] < 700:
                        page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                        page.wait_for_timeout(2000)
                        print(f"[CREDITS BTN] URL after click: {page.url}")
                        results["credits_quick_btn"] = {"url": page.url}

                        # Check search field
                        search_val = page.evaluate("""() => {
                            const input = document.querySelector('input[placeholder*="Search"]');
                            return input ? input.value : null;
                        }""")
                        print(f"[CREDITS BTN] Search input value: {search_val}")
                        results["credits_quick_btn"]["search_value"] = search_val
                        break
                except Exception as e:
                    print(f"  Skipping credits button {i}: {e}")
        else:
            results["credits_quick_btn"] = "not_found"

        # --- Step 6: Check category card clicks ---
        print("\n[STEP] Clicking category card 'Getting Started'...")
        page.goto(BASE_URL + "/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        getting_started_card = page.locator("button:has-text('Getting Started'):has-text('Learn what Pokecut is')")
        if getting_started_card.count() > 0:
            box = getting_started_card.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                page.wait_for_timeout(2000)
                print(f"[CATEGORY CARD] URL after click: {page.url}")

                # Get all visible question buttons
                questions = page.evaluate("""() => {
                    return Array.from(document.querySelectorAll('button'))
                        .filter(b => b.getBoundingClientRect().width > 0 && b.getBoundingClientRect().height > 0)
                        .map(b => b.textContent.trim().replace(/\\s+/g, ' '))
                        .filter(t => t.length > 10 && t.length < 200);
                }""")
                print(f"[CATEGORY CARD] Visible questions after click: {questions}")
                results["category_card_click"] = {
                    "url": page.url,
                    "visible_questions": questions
                }
            else:
                results["category_card_click"] = "bounding_box_failed"
        else:
            results["category_card_click"] = "not_found"

        # --- Step 7: Take screenshot of expanded question ---
        page.goto(BASE_URL + "/help", wait_until="domcontentloaded")
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(2000)

        # Click a question to expand it
        q_btn = page.locator("button:has-text('What is Pokecut and what can I use it for?')")
        if q_btn.count() > 0:
            box = q_btn.bounding_box()
            if box:
                page.mouse.click(box['x'] + box['width']/2, box['y'] + box['height']/2)
                page.wait_for_timeout(1500)

        expanded_screenshot = OUTPUT_DIR / "help_expanded_question.png"
        page.screenshot(path=str(expanded_screenshot), full_page=True)
        print(f"[SCREENSHOT] Expanded question saved to {expanded_screenshot}")
        results["screenshot_expanded"] = str(expanded_screenshot)

        browser.close()

    return results


if __name__ == "__main__":
    try:
        results = explore_details()
        output_json = Path(r"D:\Test\web-test\data\debug\help_details.json")
        output_json.write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
        print(f"\n[DONE] Details saved to {output_json}")
    except Exception as e:
        print(f"[ERROR] {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
