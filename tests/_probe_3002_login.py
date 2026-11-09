from playwright.sync_api import sync_playwright
BASE = "http://10.17.1.66:3002"
EMAIL = "450832596@qq.com"
CODE = "123456"
DIALOG = "[data-testid=\"auth-dialog\"]"

def test_probe_login_3002():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
        pg = ctx.new_page()
        pg.goto(BASE + "/tools/ethnicity-guesser-ai", timeout=120000)
        pg.wait_for_timeout(6000)
        print("URL0", pg.url)
        lb = pg.get_by_role("button", name="Log in", exact=True).first
        if lb.count() == 0:
            lb = pg.get_by_text("Log in", exact=True).first
        print("login_count", lb.count())
        lb.click()
        pg.wait_for_timeout(2500)
        print("dialog", pg.locator(DIALOG).count())
        ei = pg.locator("[data-testid=\"auth-email-input\"]").first
        ci = pg.locator("[data-testid=\"auth-code-input\"]").first
        print("email", ei.count(), "code", ci.count())
        ei.click(); pg.keyboard.type(EMAIL)
        ci.click(); pg.keyboard.type(CODE)
        pg.locator("[data-testid=\"auth-submit\"]").first.click()
        for i in range(25):
            pg.wait_for_timeout(1000)
            if pg.locator(DIALOG).count() == 0:
                print("closed_at", i); break
        else:
            print("still_open")
        pg.reload()
        pg.wait_for_timeout(4000)
        body = pg.locator("body").inner_text()
        print("URL2", pg.url)
        print("HAS_USER", "Log in" not in body[:200])
        print("BODY_HEAD", body[:200].replace(chr(10), " / "))
        pg.screenshot(path="data/debug/probe_3002_direct_login.png")
        b.close()

