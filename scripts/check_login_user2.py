"""Debug login on new server - dismiss VIP popup first."""
from playwright.sync_api import sync_playwright

BASE = "http://10.17.2.54:3000"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    pg = ctx.new_page()

    pg.goto(BASE)
    pg.wait_for_timeout(5000)

    # Dismiss any popups before login
    pg.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
            var bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
        });
        // Also try removing modals/dialogs
        document.querySelectorAll('[class*="modal"], [class*="dialog"], [class*="popup"], [class*="overlay"]').forEach(function(o) {
            if (o.offsetHeight > 100) o.remove();
        });
    }""")
    pg.wait_for_timeout(2000)

    pg.get_by_text("Log in", exact=True).first.click()
    pg.wait_for_timeout(3000)
    pg.screenshot(path="data/debug/login_modal.png")

    pg.locator('input[type="email"]').fill("450832596@qq.com")
    pg.locator('input[placeholder="Verification Code"]').fill("123456")

    # Find and click the submit button in the login modal
    btns = pg.evaluate("""() => {
        return Array.from(document.querySelectorAll("button")).filter(function(b) {
            return b.offsetWidth > 100 && b.textContent.trim() === "Log in";
        }).map(function(b) {
            var r = b.getBoundingClientRect();
            return {text: b.textContent.trim(), x: Math.round(r.x), y: Math.round(r.y),
                w: b.offsetWidth, h: b.offsetHeight, disabled: b.disabled};
        });
    }""")
    print(f"Login buttons found: {len(btns)}")
    for b in btns:
        print(f"  ({b['x']},{b['y']}) {b['w']}x{b['h']} text=\"{b['text']}\" disabled={b['disabled']}")

    # Click the largest visible login button
    if btns:
        largest = max(btns, key=lambda x: x['w'])
        pg.mouse.click(largest['x'] + largest['w']/2, largest['y'] + largest['h']/2)
        print(f"Clicked button at ({largest['x']},{largest['y']})")
    else:
        # Fallback: dispatchEvent
        pg.evaluate("""() => {
            var bs = document.querySelectorAll("button");
            for (var i = 0; i < bs.length; i++) {
                if (bs[i].textContent.trim() === "Log in" && bs[i].offsetWidth > 200) {
                    bs[i].dispatchEvent(new MouseEvent("click", {bubbles: true, cancelable: true}));
                    return;
                }
            }
        }""")

    pg.wait_for_timeout(10000)
    pg.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(function(o) {
            var bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes("rgba") && (bg.includes("0.3") || bg.includes("0.5"))) o.remove();
        });
    }""")
    pg.wait_for_timeout(2000)

    print(f"\nURL after login: {pg.url}")
    body = pg.locator("body").inner_text()[:800]
    print(f"Body[:800]:\n{body}")

    # Check for any username
    for line in body.split("\n"):
        line = line.strip()
        if line and len(line) > 2 and len(line) < 20 and line not in [
            "All Free Tools", "Resource", "Help", "Pricing", "60% OFF", "Start to Create",
            "Create", "Tools", "Batch", "Templates", "Project", "FAQ", "Contact us",
            "Sign up", "Log in", "Notification", "Sign Out", "Upgrade", "View Profile",
            "My Project", "My Order", "Chat to Edit", "0/3000", "Nano Banana", "DEBUG",
            "Home", "Trending Tools", "Try More New Models", "Explore More", "Blog",
            "Remove Background", "AI Background", "AI Expand", "AI Erase", "ID Photo M",
            "Blur Background", "HD Photo Converter", "Add Person to Photo",
            "Free AI Photo Editor & Generator", "AI Photo Editor", "AI Image Generator",
            "Upload Image", "Batch Edit"
        ]:
            if "http" not in line and "©" not in line and "offer" not in line.lower():
                print(f"  Possible username: \"{line}\"")

    pg.screenshot(path="data/debug/login_result.png", full_page=False)
    b.close()
