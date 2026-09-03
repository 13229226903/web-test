import io
p = r"pytest.ini"
s = io.open(p, encoding="utf-8").read()
if "login_required" not in s:
    s = s.replace(
        "markers =\n    regression: SEO/功能回归测试\n",
        "markers =\n    regression: SEO/功能回归测试\n    login_required: 需要登录\n    no_login: 无需登录\n    full: 全量用例\n"
    )
    io.open(p, "w", encoding="utf-8").write(s)
    print("pytest.ini markers added")
else:
    print("markers already present")
