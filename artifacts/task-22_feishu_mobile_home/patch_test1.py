import io
p = r"tests\test_mobile_home.py"
s = io.open(p, encoding="utf-8").read()
old = """    for item in ["Home", "All Tools", "Upload", "Generate", "Pricing"]:
        assert nav_items.filter(has=page.locator(f"[aria-label='{item}']")).count() == 1 or \\
               nav_items.filter(has_text=item).count() >= 1"""
new = """    nav = page.locator("nav.home-mobile-bottom-nav")
    for item in ["Home", "All Tools", "Upload", "Generate", "Pricing"]:
        assert nav.locator(f"button[aria-label='{item}']").count() == 1, f"缺少底部导航入口: {item}\""""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("patched structure nav assertion")
