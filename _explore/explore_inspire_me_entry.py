from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT = Path(r"D:\Test\web-test")
TASK = ROOT / "artifacts" / "2026-08-27_pokecut_infinite_canvas_inspire_me"
SHOTS = TASK / "shots"
SHOTS.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = context.new_page()
    console_errors = []
    page.on("console", lambda m: console_errors.append({"type": m.type, "text": m.text}) if m.type == "error" else None)
    page.goto("http://10.17.1.66:3001/create", wait_until="domcontentloaded")
    page.wait_for_timeout(7000)
    page.screenshot(path=str(SHOTS / "01_create_default.png"), full_page=True)
    # Remove the recurring purchase/gift modal that intercepts entry clicks.
    removed = page.evaluate("""() => {
      const nodes = [...document.querySelectorAll('.purchase-gift-modal')];
      nodes.forEach(n => n.remove());
      return nodes.length;
    }""")
    print("removed purchase modals:", removed)
    page.wait_for_timeout(500)

    with page.expect_file_chooser() as fc_info:
        page.locator("text=Start from a Photo").first.click(timeout=15000)
    fc = fc_info.value
    fc.set_files(str(ROOT / "test_images" / "无人脸.jpg"))
    page.wait_for_url("**/agent**", timeout=30000)
    page.wait_for_timeout(10000)
    page.screenshot(path=str(SHOTS / "02_canvas_loaded.png"), full_page=True)

    inventory = page.evaluate("""() => {
      const visible = el => {
        const r = el.getBoundingClientRect();
        const s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none';
      };
      const controls = [];
      for (const el of document.querySelectorAll('button, [role="button"], input, textarea, [contenteditable="true"], a')) {
        if (!visible(el)) continue;
        const r = el.getBoundingClientRect();
        controls.push({
          tag: el.tagName.toLowerCase(),
          text: (el.innerText || el.value || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\\s+/g, ' ').slice(0, 160),
          role: el.getAttribute('role'),
          placeholder: el.getAttribute('placeholder'),
          aria: el.getAttribute('aria-label'),
          id: el.id || null,
          dataToolId: el.getAttribute('data-tool-id'),
          cls: (el.className || '').toString().slice(0, 180),
          rect: {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)},
        });
      }
      const texts = [];
      for (const el of document.body.querySelectorAll('*')) {
        if (!visible(el)) continue;
        const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent.trim()).filter(Boolean).join(' ');
        if (own) texts.push(own.replace(/\\s+/g, ' ').slice(0, 160));
      }
      return {url: location.href, title: document.title, controls, texts: [...new Set(texts)].slice(0, 500)};
    }""")
    (SHOTS / "canvas_inventory.json").write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print("URL:", inventory["url"])
    print("TITLE:", inventory["title"])
    print("CONTROL_COUNT:", len(inventory["controls"]))
    for item in inventory["controls"]:
        print(json.dumps(item, ensure_ascii=False))
    print("CONSOLE_ERRORS:", json.dumps(console_errors, ensure_ascii=False, indent=2))
    browser.close()
