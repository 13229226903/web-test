"""Check what username appears after login on new server."""
from playwright.sync_api import sync_playwright

BASE = "http://10.17.2.54:3000"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    pg = ctx.new_page()

    pg.goto(BASE)
    pg.wait_for_timeout(5000)
    pg.get_by_text("Log in", exact=True).first.click()
    pg.wait_for_timeout(3000)
    pg.locator('input[type="email"]').fill("450832596@qq.com")
    pg.locator('input[placeholder="Verification Code"]').fill("123456")
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

    print(f"URL after login: {pg.url}")
    body = pg.locator("body").inner_text()[:500]
    print(f"Body[:500]:\n{body}")

    # Check for username patterns
    import re
    # Look for text that looks like a username (not navigation items)
    lines = body.split("\n")
    for line in lines[:20]:
        line = line.strip()
        if line and line not in ["All Free Tools", "Resource", "Help", "Pricing", "60% OFF",
                                   "Start to Create", "Create", "Tools", "Batch", "Templates",
                                   "Project", "FAQ", "Contact us", "Notification", "Sign Out",
                                   "Upgrade", "View Profile", "My Project", "My Order",
                                   "Chat to Edit", "0/3000", "Nano Banana", "DEBUG",
                                   "Home", "Trending Tools", "Remove Background", "AI Background",
                                   "AI Expand", "AI Erase", "ID Photo M", "Blur Background",
                                   "Try More New Models"]:
            if len(line) > 2 and "http" not in line and "©" not in line:
                print(f"  Candidate username: \"{line}\"")

    pg.screenshot(path="data/debug/new_server_login.png", full_page=False)
    b.close()
