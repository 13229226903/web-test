import io
p = r"artifacts\task-22_feishu_mobile_home\impl.md"
s = io.open(p, encoding="utf-8").read()
old = """## 自修日志
- round 1：`test_mobile_home_structure` 底部导航 Upload 项断言用 `filter(has=...)` 误判（icon-only 按钮无文本子节点）。改为 `nav.locator("button[aria-label='...']").count()==1` 后通过。
- 其余用例首次即通过。"""
new = """## 自修日志
- round 1：`test_mobile_home_structure` 底部导航 Upload 项断言用 `filter(has=...)` 误判（icon-only 按钮无文本子节点）。改为 `nav.locator("button[aria-label='...']").count()==1` 后通过。
- round 2：用户指出 Allure 缺 L1~L6 分层——补充 `@allure.label("layer")`、`@allure.title("<case_id> [<Layer>] <标题>")`，参数化用例用 `allure.dynamic.title` 带实际值；重跑 matrix 并重新生成报告。"""
assert old in s
s = s.replace(old, new, 1)
s = s.replace("self_run: 37 passed, 1 skipped (TC-MH-L3-004 blocked_by_bug)", "self_run: 37 passed, 1 skipped (TC-MH-L3-004 blocked_by_bug)（matrix run，含 Layer/标题修正后）")
io.open(p, "w", encoding="utf-8").write(s)
print("impl.md updated")
