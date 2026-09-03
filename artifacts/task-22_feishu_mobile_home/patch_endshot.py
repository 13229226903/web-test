import io, re
p = r"tests\test_mobile_home.py"
s = io.open(p, encoding="utf-8").read()

# 1) remove 首页加载 screenshot from goto_home
s = s.replace("        page.wait_for_timeout(6000)\n        allure_screenshot(page, \"首页加载\")",
              "        page.wait_for_timeout(6000)")

# 2) remove autouse end-screenshot fixture block
old_fix = '''

@pytest.fixture(autouse=True)
def _mobile_end_screenshot(mobile_page):
    """每个用例结束态自动附截图到 Allure。"""
    yield
    with allure.step("用例结束态"):
        allure_screenshot(mobile_page, "用例结束态")
'''
s = s.replace(old_fix, "")

# 3) insert end-state screenshot at end of every test function that uses page
def insert_end_shots(src):
    lines = src.split("\n")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = re.match(r"def (test_[a-zA-Z0-9_]+)\((mobile_page.*)?\):", line)
        if m and "test_id_photo_success_logged_in" not in line:
            # find block: subsequent lines until a non-indented line
            j = i + 1
            last_indented = i
            while j < len(lines):
                nxt = lines[j]
                if nxt.strip() == "":
                    # blank line may separate block end; skip blanks but don't insert inside
                    j += 1
                    continue
                if nxt[0] in (" ", "\t"):
                    last_indented = j
                    j += 1
                else:
                    break
            # insert end shot after last_indented
            insert_at = last_indented + 1
            # skip if already has shot(page, "用例结束态")
            block = "\n".join(lines[i+1:j])
            if "用例结束态" not in block:
                out.append("    shot(page, \"用例结束态\")")
            i = j - 1
        i += 1
    return "\n".join(out)

s = insert_end_shots(s)

io.open(p, "w", encoding="utf-8").write(s)
print("patched: removed 首页加载/autouse, added per-test end shot")
