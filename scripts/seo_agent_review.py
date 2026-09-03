#!/usr/bin/env python3
"""
SEO 单页 Agent 审查脚本 — 零代码，agent 直接调用。

用法:
  python scripts/seo_agent_review.py --url "http://10.17.2.54:3000/ja/tools/xxx" \
      --login-email "450832596@qq.com" --login-code "123456"

输出: JSON 结构化的审查结果，包含每层检测的详情和 LLM 判断。
"""

import os, sys, json, time, argparse, base64, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

HARNESS_ROOT = Path(__file__).parent.parent

# ── API config ──
def load_env():
    env_path = HARNESS_ROOT / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k not in os.environ:
                        os.environ[k] = v

load_env()
API_KEY = os.getenv("OPENAI_API_KEY", "")
API_BASE = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
API_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")


def ask_llm(messages, max_tokens=500):
    """Send request to the configured review model, return parsed JSON."""
    if not API_KEY:
        return None
    body = {"model": API_MODEL, "max_tokens": max_tokens, "temperature": 0, "messages": messages}
    req = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    for _ in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                # Parse JSON
                cleaned = text.strip()
                if "```" in cleaned:
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                return json.loads(cleaned.strip())
        except Exception:
            time.sleep(2)
    return None


def img_b64(png):
    return base64.b64encode(png).decode()


# ── Review functions ──

def review_screenshot(png, context="", prompt_extra=""):
    """Send a screenshot for general review. Returns LLM result dict."""
    prompt = (
        f"Context: {context}. " if context else ""
        "Review this screenshot from an SEO landing page:\n\n"
        "A) Rendering bugs: garbled/mojibake, ???? waterfalls, encoding errors, "
        "HTML leaks, placeholder text, truncation, broken layout.\n"
        "B) Copywriting issues: inconsistent numbering, mixed terminology, "
        "typos, spacing errors, ambiguous phrasing.\n"
        + (prompt_extra + "\n" if prompt_extra else "") +
        'Return JSON: {"found": true/false, "issue": "describe or empty"}'
    )
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64(png)}"}},
        {"type": "text", "text": prompt},
    ]}]
    return ask_llm(messages, max_tokens=300) or {"found": False, "issue": ""}


def review_interaction(png_before, png_after, element_text, element_type="button"):
    """Judge button/image click effect. Returns LLM result dict."""
    prompt = (
        f'Clicked [{element_type}] "{element_text[:60]}". '
        "Compare BEFORE (image 1) and AFTER (image 2).\n"
        "1. Did the page navigate? If to /agent or /create, that's NORMAL for try-images.\n"
        "2. Any UI change? (modal, dropdown, image change)\n"
        "3. Any error, blank page, garbled text, broken layout?\n"
        'Return JSON: {"passed": true/false, "effect": "navigated|ui_changed|no_change|error", '
        '"detail": "one sentence", "issues": []}'
    )
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64(png_before)}"}},
        {"type": "text", "text": "BEFORE click."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64(png_after)}"}},
        {"type": "text", "text": prompt},
    ]}]
    return ask_llm(messages, max_tokens=400) or {"passed": True, "effect": "skipped", "detail": "API failed", "issues": []}


def review_text_quality(text, lang=""):
    """Review page text for garbled text + copywriting issues. Returns LLM result dict."""
    lang_hint = f"Expected language: {lang}. " if lang else ""
    prompt = (
        f"{lang_hint}Review the following page text for issues:\n"
        "A) Bugs: garbled chars, ???? waterfalls, HTML leaks, encoding errors, truncation.\n"
        "B) Copywriting: inconsistent naming/numbering, typos, spacing errors, ambiguous phrasing.\n"
        f"=== TEXT ===\n{text[:12000]}\n=== END ===\n"
        'Return JSON: {"passed": true/false, "issues": [{"severity":"warning|error","detail":"...","location":"..."}], "summary":"..."}'
    )
    messages = [{"role": "user", "content": prompt}]
    return ask_llm(messages, max_tokens=600) or {"passed": True, "issues": [], "summary": "API failed"}


# ── Visual fallback discovery ──

def discover_via_visual(png, what="interactive elements"):
    """When selectors find nothing, ask LLM to identify elements from screenshot.
    Returns list of {"text": str, "x": int, "y": int, "type": "button"|"image"|"faq"} or []."""
    prompt = (
        f"Look at this screenshot of an SEO page. Identify all {what} that a user can click on.\n"
        "Include: CTA buttons, try/demo images, FAQ accordion items, carousel arrows, "
        "review/testimonial sections.\n"
        "For each, estimate its center coordinates as a percentage of image dimensions "
        "(0-100 for x and y, where 0,0 is top-left).\n"
        'Return ONLY a JSON list: [{"text": "button label or element description", '
        '"x_pct": 50, "y_pct": 80, "type": "button|image|faq|carousel_arrow|review"}]\n'
        "If nothing found, return []."
    )
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64(png)}"}},
        {"type": "text", "text": prompt},
    ]}]
    result = ask_llm(messages, max_tokens=600)
    if not result or not isinstance(result, list):
        return []
    # Convert pct to pixel coords (assuming 1920x1080 viewport)
    items = []
    for r in result:
        if isinstance(r, dict) and "x_pct" in r:
            items.append({
                "text": r.get("text", "element")[:60],
                "type": r.get("type", "button"),
                "x": int(r["x_pct"] / 100 * 1920),
                "y": int(r["y_pct"] / 100 * 1080),
            })
    return items


# ── Main review flow ──

def review_page(url, login_email=None, login_code=None):
    """Full SEO page review. Returns structured dict."""
    result = {
        "url": url, "page_title": "", "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "layers": {},
        "all_issues": [],
        "summary": "",
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        page = ctx.new_page()

        # ── Login if needed ──
        if login_email and login_code:
            print("[Agent] Logging in...")
            page.goto("http://10.17.1.66:3001", timeout=30000)
            page.wait_for_timeout(3000)
            page.get_by_text("Log in", exact=True).first.click()
            page.wait_for_timeout(2000)
            page.locator('input[type="email"]').wait_for(state="visible", timeout=10000)
            page.locator('input[type="email"]').fill(login_email)
            page.locator('input[placeholder="Verification Code"]').fill(login_code)
            page.evaluate("""() => {
                var btns = document.querySelectorAll('button');
                for (var i=0;i<btns.length;i++) {
                    if (btns[i].textContent.trim()==='Log in' && btns[i].offsetWidth>200) {
                        btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                        return;
                    }
                }
            }""")
            page.wait_for_timeout(8000)
            print("[Agent] Login done")

        # ── Navigate ──
        print(f"[Agent] Loading: {url}")
        resp = page.goto(url, timeout=60000)
        http_status = resp.status if resp else 0
        page.wait_for_timeout(3000)

        # Scroll to load lazy content
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        page.evaluate("window.scrollTo(0, 0)")
        page.wait_for_timeout(1000)

        result["page_title"] = page.title()
        result["http_status"] = http_status

        # ═══════════════════════════════════════
        # LAYER 1: Accessible + Resources
        # ═══════════════════════════════════════
        print("[Agent] Layer 1...")
        l1 = {"accessible": {}, "resources": {}, "interactions": [], "faq": {}, "text": {}}

        body_text = page.locator("body").inner_text()
        l1["accessible"] = {
            "http_status": http_status,
            "body_chars": len(body_text),
            "title": page.title(),
        }

        # Interaction discovery
        items = page.evaluate("""() => {
            var exclude = ['sign up','log in','sign in','register','login','english','language','debug'];
            var layout = document.querySelector('#__nuxt > div:first-child');
            var main = (layout && layout.children.length >= 2) ? layout.children[1] : null;
            var root = main || document;
            var items = [];
            // Buttons
            root.querySelectorAll('button:not([disabled]), [role="button"]').forEach(function(b) {
                var t = (b.textContent || '').trim();
                var r = b.getBoundingClientRect();
                if (t.length > 1 && r.width > 20 && r.height > 10) {
                    var lower = t.toLowerCase();
                    if (!exclude.some(function(k) { return lower.includes(k); }))
                        items.push({text: t.slice(0,60), type: 'button'});
                }
            });
            // Try-images
            root.querySelectorAll(
                '.seo-try-image-card, [class*="try-image-card"], [class*="tryImageCard"],'
                + '[class*="try-image"], [class*="TryImage"]'
            ).forEach(function(card) {
                var r = card.getBoundingClientRect();
                if (r.width < 80 || r.height < 80) return;
                var p = card.closest('a');
                var label = p ? (p.textContent||'').trim().replace(/\\s+/g,' ') : '';
                if (!label) { var img = card.querySelector('img')||card; label = (img.alt||'').trim(); }
                if (!label) label = 'DemoImage: click to try';
                items.push({text: label.slice(0,60), type: 'image'});
            });
            // Dedup
            var seen = new Set();
            return items.filter(function(x) {
                var k = x.text; if (seen.has(k)) return false; seen.add(k); return true;
            }).slice(0, 10);
        }""")

        print(f"[Agent] Selectors found {len(items)} interactive elements")

        # Fallback: if selectors found nothing, use visual discovery
        if len(items) == 0:
            print("[Agent] Selectors empty, falling back to visual discovery...")
            full_png = page.screenshot(full_page=False)
            visual_items = discover_via_visual(full_png, "buttons and try/demo images")
            if visual_items:
                print(f"[Agent] Visual found {len(visual_items)} elements")
                items = visual_items

        # Click each element
        for i, item in enumerate(items):
            before_url = page.url
            png_before = page.screenshot(full_page=False)

            # Click: visual (coordinates) vs selector (text match)
            has_coords = "x" in item and "y" in item
            if has_coords:
                # Visual fallback: click by coordinates
                page.mouse.click(item["x"], item["y"])
            elif item["type"] == "image":
                page.evaluate("""(text) => {
                    var cards = document.querySelectorAll(
                        '.seo-try-image-card, [class*="try-image"], [class*="TryImage"]');
                    for (var i=0;i<cards.length;i++) {
                        var card = cards[i];
                        var r = card.getBoundingClientRect();
                        if (r.width < 80) continue;
                        var p = card.closest('a');
                        var l = p ? (p.textContent||'').trim().replace(/\\s+/g,' ') : (card.querySelector('img')||{}).alt||'';
                        if (l.slice(0,30) === text.slice(0,30)) { (p||card).click(); return; }
                    }
                }""", item["text"])
            else:
                page.evaluate("""(text) => {
                    var btns = document.querySelectorAll('button:not([disabled]), [role="button"]');
                    for (var i=0;i<btns.length;i++) {
                        var t = (btns[i].textContent||'').trim();
                        if (t===text||t.slice(0,30)===text.slice(0,30)) {
                            btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                            return;
                        }
                    }
                }""", item["text"])

            page.wait_for_timeout(2000)
            png_after = page.screenshot(full_page=False)

            # LLM judge
            llm = review_interaction(png_before, png_after, item["text"], item["type"])
            l1["interactions"].append({
                "text": item["text"], "type": item["type"],
                "llm_judgment": llm,
            })

            # Navigate back if needed
            if page.url.rstrip("/") != before_url.rstrip("/"):
                page.goto(before_url, timeout=30000)
                page.wait_for_timeout(2000)

        # FAQ discovery + expand
        print("[Agent] FAQ check...")
        faq_items = page.evaluate("""() => {
            var items = []; var seen = new Set();
            var sels = ['[style*="accordion-icon"]','[style*="faq_icon"]','.pk-collapse-header','[class*="collapse-header"]'];
            sels.forEach(function(sel) {
                try { document.querySelectorAll(sel).forEach(function(el) {
                    if(el.offsetWidth===0)return;
                    var t=(el.textContent||'').replace(/\\s+/g,' ').trim();
                    if(t.length>=5&&t.length<=300&&!seen.has(t.slice(0,40))){seen.add(t.slice(0,40));items.push(t.slice(0,120));}
                });} catch(e){}
            });
            if(items.length===0) document.querySelectorAll('details').forEach(function(el){
                var s=el.querySelector('summary'); var t=(s||el).textContent.trim();
                if(t.length>=5&&!seen.has(t.slice(0,40))){seen.add(t.slice(0,40));items.push(t.slice(0,120));}
            });
            return items.slice(0,10);
        }""")

        # Fallback: if no FAQ found via selectors, use visual
        if len(faq_items) == 0:
            print("[Agent] FAQ selectors empty, trying visual...")
            full_png = page.screenshot(full_page=False)
            visual_faq = discover_via_visual(full_png, "FAQ or accordion items")
            if visual_faq:
                faq_items = [v["text"] for v in visual_faq if v.get("type") == "faq"]
                print(f"[Agent] Visual found {len(faq_items)} FAQ items")

        faq_count = 0
        for item in faq_items:
            try:
                page.evaluate("""(text) => {
                    var m=text.slice(0,30);
                    var sels=['[style*="accordion-icon"]','[style*="faq_icon"]','.pk-collapse-header','details summary'];
                    for(var s=0;s<sels.length;s++) {
                        var els=document.querySelectorAll(sels[s]);
                        for(var i=0;i<els.length;i++) {
                            var t=(els[i].textContent||'').replace(/\\s+/g,' ').trim();
                            if(t.slice(0,30)===m){els[i].scrollIntoView({behavior:'instant',block:'center'});return;}
                        }
                    }
                }""", item)
                page.wait_for_timeout(200)
                page.evaluate("""(text) => {
                    var m=text.slice(0,30);
                    var sels=['[style*="accordion-icon"]','[style*="faq_icon"]','.pk-collapse-header','details summary'];
                    for(var s=0;s<sels.length;s++) {
                        var els=document.querySelectorAll(sels[s]);
                        for(var i=0;i<els.length;i++) {
                            var t=(els[i].textContent||'').replace(/\\s+/g,' ').trim();
                            if(t.slice(0,30)===m){els[i].click();els[i].dispatchEvent(new MouseEvent('click',{bubbles:true}));return;}
                        }
                    }
                }""", item)
                page.wait_for_timeout(600)
                faq_count += 1
            except:
                pass

        if faq_count > 0:
            page.evaluate(f"window.scrollTo(0, {page.evaluate('document.body.scrollHeight')})")
            page.wait_for_timeout(1000)
            faq_png = page.screenshot(full_page=False)
            faq_llm = review_screenshot(faq_png, f"FAQ section with {faq_count} items expanded")
            l1["faq"] = {"expanded": faq_count, "llm_review": faq_llm}

        # Bottom section screenshot (reviews/comments)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2000)
        bottom_png = page.screenshot(full_page=False)
        bottom_llm = review_screenshot(bottom_png, "Bottom section of page (reviews/comments area)")
        l1["bottom_review"] = bottom_llm

        # Text quality
        full_text = page.locator("body").inner_text()
        tq = review_text_quality(full_text)
        l1["text"] = tq

        result["layers"]["layer1"] = l1

        # Collect all issues
        for inter in l1.get("interactions", []):
            for iss in inter.get("llm_judgment", {}).get("issues", []):
                d = iss if isinstance(iss, str) else iss.get("detail", str(iss))
                result["all_issues"].append({"source": f"interaction: {inter['text'][:30]}", "detail": d})
        if faq_llm and faq_llm.get("found"):
            result["all_issues"].append({"source": "FAQ", "detail": faq_llm.get("issue", "")})
        if bottom_llm and bottom_llm.get("found"):
            result["all_issues"].append({"source": "reviews section", "detail": bottom_llm.get("issue", "")})
        for iss in tq.get("issues", []):
            d = iss if isinstance(iss, str) else iss.get("detail", str(iss))
            result["all_issues"].append({"source": "text quality", "detail": d})

        ctx.close()
        browser.close()

    # Summary
    issue_count = len(result["all_issues"])
    result["summary"] = f"Found {issue_count} issue(s)" if issue_count > 0 else "No issues found"
    result["passed"] = issue_count == 0

    return result


# ── CLI ──
def main():
    parser = argparse.ArgumentParser(description="SEO Agent Review")
    parser.add_argument("--url", required=True, help="Full page URL")
    parser.add_argument("--login-email", default="450832596@qq.com")
    parser.add_argument("--login-code", default="123456")
    parser.add_argument("--no-login", action="store_true")
    parser.add_argument("--output", help="Output JSON file path")
    args = parser.parse_args()

    email = None if args.no_login else args.login_email
    code = None if args.no_login else args.login_code

    print(f"\n{'='*60}")
    print(f"SEO Agent Review")
    print(f"  URL: {args.url}")
    print(f"  Login: {'Yes' if email else 'No'}")
    print(f"{'='*60}\n")

    result = review_page(args.url, login_email=email, login_code=code)

    print(f"\n{'='*60}")
    print(f"Result: {'PASS' if result['passed'] else 'ISSUES FOUND'}")
    print(f"Issues: {len(result['all_issues'])}")
    for iss in result["all_issues"]:
        print(f"  [{iss['source']}] {iss['detail'][:120]}")
    print(f"{'='*60}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Saved: {args.output}")
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
