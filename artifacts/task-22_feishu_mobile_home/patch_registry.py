import io
p = r"artifacts\regression_registry.md"
s = io.open(p, encoding="utf-8").read()
row = "| Pokecut 移动端首页优化（Mobile Home v3） | http://10.17.1.66:3001/ （移动端 390x844） | stable_regression | task-22_feishu_mobile_home | tests/test_mobile_home.py | archive/mobile_home/test_mobile_home.py | page_map/pokecut/mobile_home_v1.yaml | artifacts/task-22_feishu_mobile_home/sync.md | artifacts/task-22_feishu_mobile_home/cases.md | impl.md completed / review.md pass / visual-review 不需要 | 2026-08-31 37 passed, 1 skipped in 402s；`python -m pytest tests/test_mobile_home.py -q` | 测试服 http://10.17.1.66:3001；移动端 390x844 en-US；匿名浏览无需登录；素材 test_images/有人脸.JPG | 登录弹层提交无反应 bug（TC-MH-L3-004 skip）；21 用例 37 passed/1 skipped；Allure feature/story/class/title/severity/markers |\n"
if not s.endswith("\n"):
    s += "\n"
s += row
io.open(p, "w", encoding="utf-8").write(s)
print("registry appended")
