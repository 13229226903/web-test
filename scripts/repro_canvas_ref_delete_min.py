from pathlib import Path

from playwright.sync_api import sync_playwright

BASE_URL = "http://10.17.1.66:3001"
EMAIL = "450832596@qq.com"
CODE = "123456"
AGENT_URL = f"{BASE_URL}/agent?pid=bb26ac41-558a-43d8-97fe-5ed0ee2b4f55"
IMG = Path("test_images/1K.jpg").resolve()


def log(msg: str) -> None:
    print(f"[repro] {msg}")


def login(page):
    page.goto(BASE_URL, wait_until="domcontentloaded", timeout=120000)
    page.wait_for_timeout(5000)
    if page.get_by_text("User8JY", exact=True).count() > 0:
        log("already logged in")
        return
    log("open login modal")
    page.get_by_text("Log in", exact=True).first.click(timeout=10000)
    page.wait_for_timeout(3000)
    try:
        page.locator("button:has-text('Log in'):visible").last.click(timeout=3000)
        page.wait_for_timeout(600)
    except Exception:
        pass
    email_input = page.locator('input[type="email"]')
    email_input.first.fill(EMAIL)
    code_input = page.locator('input[data-testid="auth-code-input"]')
    if code_input.count() == 0:
        code_input = page.locator('input[placeholder="Verification Code"]')
    code_input.first.fill(CODE)
    page.evaluate(
        """() => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                const text = (b.textContent || '').trim();
                if (text === 'Log in' && b.offsetWidth > 200) {
                    b.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
                    return true;
                }
            }
            return false;
        }"""
    )
    page.wait_for_timeout(10000)
    if page.get_by_text("User8JY", exact=True).count() == 0:
        raise RuntimeError("login failed")
    log("login success")


def select_basic(page):
    page.locator("button:has-text('Inspiration')").first.click(timeout=10000)
    page.wait_for_timeout(1200)
    panel = page.locator("div.canvas-textbox-expanded-state:visible").first
    trigger = panel.locator("div[title='Model']").first
    trigger.click(timeout=10000)
    page.wait_for_timeout(800)
    page.get_by_text("Pokecut Basic", exact=True).last.locator("xpath=ancestor::div[contains(@class,'cursor-pointer')][1]").click(timeout=10000)
    page.wait_for_timeout(800)
    log("selected Pokecut Basic")


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        login(page)
        page.goto(AGENT_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(5500)
        select_basic(page)
        file_input = page.locator("input[type='file'][accept='image/png,image/jpeg,image/webp,image/bmp']").last
        file_input.set_input_files([str(IMG)])
        page.wait_for_timeout(6000)
        body = page.locator("body").inner_text(timeout=5000)
        log("after upload body tail: " + body[-220:].replace("\n", " | "))
        if page.get_by_text("1/1", exact=True).count() == 0:
            raise RuntimeError("1/1 not visible after upload")
        thumb = page.locator("div.flex-shrink-0.w-auto").first
        if thumb.count() == 0:
            raise RuntimeError("thumbnail container not found")
        thumb.hover(timeout=10000)
        page.wait_for_timeout(1000)
        delete_btn = page.locator("button[aria-label='Delete']").first
        if delete_btn.count() == 0:
            raise RuntimeError("delete button not visible")
        delete_btn.click(timeout=10000)
        page.wait_for_timeout(1200)
        body = page.locator("body").inner_text(timeout=5000)
        log("after delete body tail: " + body[-220:].replace("\n", " | "))
        upload_title_count = page.locator("[title='Upload reference images']").count()
        upload_text_count = page.get_by_text("Upload reference images", exact=True).count()
        log(f"upload button title count={upload_title_count}, text count={upload_text_count}")
        if upload_title_count == 0:
            raise RuntimeError("upload button did not return")
        log("success")
        browser.close()


if __name__ == "__main__":
    main()
