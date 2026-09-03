import io, re
p = r"tests\test_mobile_home.py"
s = io.open(p, encoding="utf-8").read()

# priorities
PRI = {
 "TC-MH-L1-001":"P1","TC-MH-L1-002":"P1",
 "TC-MH-L2-001":"P1","TC-MH-L2-002":"P0","TC-MH-L2-003":"P1","TC-MH-L2-004":"P1",
 "TC-MH-L2-006":"P1","TC-MH-L2-022":"P1","TC-MH-L2-007":"P1","TC-MH-L2-008":"P1",
 "TC-MH-L2-009":"P2","TC-MH-L2-010":"P1","TC-MH-L2-011":"P2","TC-MH-L2-012":"P2",
 "TC-MH-L2-013":"P1","TC-MH-L2-014":"P1","TC-MH-L2-015":"P2","TC-MH-L2-016":"P2",
 "TC-MH-L2-018":"P1","TC-MH-L2-020":"P1","TC-MH-L3-004":"P1",
}
LAYER_FEATURE = {
 "L1":"L1 页面元素与结构",
 "L2":"L2 交互与状态迁移",
 "L3":"L3 异常与权限",
 "L4":"L4 PRD AC 逐条映射",
 "L5":"L5 数据边界与等价类",
 "L6":"L6 核心 Happy Path / E2E",
}

# 1) helpers: remove allure.step wrappers and replace shot with end_shot direct attach
s = s.replace('''def goto_home(page: Page, base_url: str):
    with allure.step("打开移动端首页"):
        page.goto(f"{base_url}{BASE_PATH}", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(6000)''',
'''def goto_home(page: Page, base_url: str):
    page.goto(f"{base_url}{BASE_PATH}", wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(6000)''')

s = s.replace('''def scroll_to(locator):
    with allure.step("滚动到目标元素"):
        locator.scroll_into_view_if_needed()
        page = locator.page
        page.wait_for_timeout(300)''',
'''def scroll_to(locator):
    locator.scroll_into_view_if_needed()
    page = locator.page
    page.wait_for_timeout(300)''')

s = s.replace('''def upload_via(page: Page, trigger, file_path: str):
    with allure.step("点击上传并选择素材"):
        with page.expect_file_chooser(timeout=8000) as fc:
            trigger.click()
        fc.value.set_files(file_path)
        page.wait_for_timeout(300)''',
'''def upload_via(page: Page, trigger, file_path: str):
    with page.expect_file_chooser(timeout=8000) as fc:
        trigger.click()
    fc.value.set_files(file_path)
    page.wait_for_timeout(300)''')

s = s.replace('''def shot(page: Page, name: str):
    with allure.step(name):
        allure_screenshot(page, name)''',
'''def end_shot(page: Page):
    allure.attach(page.screenshot(), name="用例截图", attachment_type=allure.attachment_type.PNG)''')

# 2) replace all shot(page, "用例结束态") calls
s = s.replace('shot(page, "用例结束态")', 'end_shot(page)')

# 3) remove unused import allure_screenshot if no longer used
s = s.replace("from conftest import allure_screenshot\n", "")

# 4) remove @allure.story lines
s = re.sub(r'@allure\.story\([^\n]*\)\n', '', s)

# 5) remove @allure.label("layer", ...) lines
s = re.sub(r'@allure\.label\("layer", "[^\n]*"\)\n', '', s)

# 6) replace epic
s = s.replace('@allure.epic("Pokecut Mobile Home")', '@allure.epic("移动端首页")')

# 7) remove old feature lines, then re-insert feature after case_id label
s = re.sub(r'@allure\.feature\("移动端首页"\)\n', '', s)

def repl_case(m):
    cid = m.group(1)
    layer = cid.split("-")[2]
    feat = LAYER_FEATURE.get(layer, "L2 交互与状态迁移")
    return f'@allure.label("case_id", "{cid}")\n@allure.feature("{feat}")'

s = re.sub(r'@allure\.label\("case_id", "(TC-MH-[A-Z0-9-]+)"\)', repl_case, s)

# 8) titles: replace [Lx] with [PRI]
def repl_title(m):
    cid = m.group(1)
    pri = PRI.get(cid, "P1")
    return f'{cid} [{pri}]'

s = re.sub(r'(TC-MH-[A-Z0-9-]+) \[L\d\]', repl_title, s)

io.open(p, "w", encoding="utf-8").write(s)
print("patched to reference-style Allure hierarchy")
