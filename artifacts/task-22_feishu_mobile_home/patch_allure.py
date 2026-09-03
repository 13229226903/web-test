import io, re
p = r"tests\test_mobile_home.py"
s = io.open(p, encoding="utf-8").read()

CASE_META = {
 "TC-MH-L1-001": ("L1", "移动端首页首屏结构与各板块存在"),
 "TC-MH-L1-002": ("L1", "首屏文案与控件排列"),
 "TC-MH-L2-001": ("L2", "主按钮唤起系统上传弹窗"),
 "TC-MH-L2-002": ("L2", "主按钮上传有效图进入移动端画布"),
 "TC-MH-L2-003": ("L2", "模型入口展开模型列表"),
 "TC-MH-L2-004": ("L2", "比例入口展开比例列表"),
 "TC-MH-L2-006": ("L2", "Generate 未满足条件禁用"),
 "TC-MH-L2-022": ("L2", "Agent 输入框输入文本后 Generate 可点击并进入画布"),
 "TC-MH-L2-007": ("L2", "功能卡片上传打开对应画布面板"),
 "TC-MH-L2-008": ("L2", "ID Photo Maker 匿名态上传有效图弹注册弹层"),
 "TC-MH-L2-009": ("L2", "More Pokecut Tools 跳转 tools 页"),
 "TC-MH-L2-010": ("L2", "effect 模板卡上传进入画布"),
 "TC-MH-L2-011": ("L2", "See More Creations 跳转 create 页"),
 "TC-MH-L2-012": ("L2", "Test 4 链接跳转站内工具页"),
 "TC-MH-L2-013": ("L2", "人像 tab 切换内容切换"),
 "TC-MH-L2-014": ("L2", "画质增强 4 标签交互"),
 "TC-MH-L2-015": ("L2", "数据卡片点击选中态"),
 "TC-MH-L2-016": ("L2", "Product Hunt 新标签页跳转"),
 "TC-MH-L2-018": ("L2", "FAQ 展开收起与答案链接"),
 "TC-MH-L2-020": ("L2", "底部导航各入口"),
 "TC-MH-L3-004": ("L3", "ID Photo Maker 抠图成功进入证件照画布"),
}

# 1) insert layer label + static title after each case_id label
def repl(m):
    cid = m.group(1)
    layer, title = CASE_META[cid]
    return (f'@allure.label("case_id", "{cid}")\n'
            f'@allure.label("layer", "{layer}")\n'
            f'@allure.title("{cid} [{layer}] {title}")')

s = re.sub(r'@allure\.label\("case_id", "(TC-MH-[A-Z0-9-]+)"\)', repl, s)

# 2) add dynamic title with actual parameter value for parameterized tests
param_expr = {
 "test_function_card_upload_panel": ("card_name", "card_name"),
 "test_test_board_links": ("name", "name"),
 "test_portrait_tab_switch": ("tab", "tab"),
 "test_enhance_actions": ("name", "name"),
 "test_bottom_nav": ("item", "item"),
}
for fn, (param, expr) in param_expr.items():
    # find def line
    m = re.search(rf'(def {fn}\(.*?\):\n)', s)
    if not m:
        continue
    # find cid from the nearest preceding case_id label
    before = s[:m.start()]
    cidm = re.findall(r'@allure\.label\("case_id", "(TC-MH-[A-Z0-9-]+)"\)', before)
    if not cidm:
        continue
    cid = cidm[-1]
    layer, title = CASE_META[cid]
    insert = (f'    allure.dynamic.title(f"{cid} [{layer}] {title} — {{{expr}}}")\n')
    s = s[:m.end()] + insert + s[m.end():]

io.open(p, "w", encoding="utf-8").write(s)
print("patched allure titles/layers")
