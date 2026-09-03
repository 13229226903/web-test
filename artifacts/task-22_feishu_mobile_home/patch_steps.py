import io
p = r"tests\test_mobile_home.py"
s = io.open(p, encoding="utf-8").read()

# 1) import allure_screenshot
s = s.replace(
"from playwright.sync_api import Page, expect\n",
"from playwright.sync_api import Page, expect\nfrom conftest import allure_screenshot\n",
1
)

# 2) helpers wrap in allure.step and shot helper
s = s.replace(
'''def goto_home(page: Page, base_url: str):
    page.goto(f"{base_url}{BASE_PATH}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)


def scroll_to(locator):
    locator.scroll_into_view_if_needed()
    page = locator.page
    page.wait_for_timeout(300)


def upload_via(page: Page, trigger, file_path: str):
    with page.expect_file_chooser(timeout=8000) as fc:
        trigger.click()
    fc.value.set_files(file_path)''',
'''def goto_home(page: Page, base_url: str):
    with allure.step("打开移动端首页"):
        page.goto(f"{base_url}{BASE_PATH}", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)
        allure_screenshot(page, "首页加载")


def scroll_to(locator):
    with allure.step("滚动到目标元素"):
        locator.scroll_into_view_if_needed()
        page = locator.page
        page.wait_for_timeout(300)


def upload_via(page: Page, trigger, file_path: str):
    with allure.step("点击上传并选择素材"):
        with page.expect_file_chooser(timeout=8000) as fc:
            trigger.click()
        fc.value.set_files(file_path)
        page.wait_for_timeout(300)


def shot(page: Page, name: str):
    with allure.step(name):
        allure_screenshot(page, name)''',
1
)

# 3) add autouse fixture for end screenshot (after mobile_page fixture)
s = s.replace(
'''@pytest.fixture
def mobile_page(browser):
    """移动端专用 context/page。"""
    ctx = browser.new_context(**MOBILE_CONTEXT)
    page = ctx.new_page()
    page.set_default_timeout(15000)
    yield page
    ctx.close()''',
'''@pytest.fixture
def mobile_page(browser):
    """移动端专用 context/page。"""
    ctx = browser.new_context(**MOBILE_CONTEXT)
    page = ctx.new_page()
    page.set_default_timeout(15000)
    yield page
    ctx.close()


@pytest.fixture(autouse=True)
def _mobile_end_screenshot(mobile_page):
    """每个用例结束态自动附截图到 Allure。"""
    yield
    with allure.step("用例结束态"):
        allure_screenshot(mobile_page, "用例结束态")''',
1
)

io.open(p, "w", encoding="utf-8").write(s)
print("patched test file with steps/screenshots")
