import io
p = r"artifacts\task-22_feishu_mobile_home\sync.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("status: pending_review", "status: confirmed", 1)
old = "## 四、bug_candidates\n- 本轮未确认阻塞性 bug_candidate。上一轮人像 tab 切换、画质增强按钮无响应为视口外元素未滚动到位导致的假失败，复测后均已覆盖并纠正。"
new = "## 四、bug_candidates\n- 本轮未确认阻塞首页探索的 bug_candidate（人像/画质增强假失败已纠正）。\n- 另记录：首页 Sign up 弹层切换 Log in 后，填入邮箱+验证码并点击 Log in，弹层不关闭、无跳转、无错误提示（登录未完成，file_bug，不阻塞首页探索/用例）。"
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("sync.md confirmed + login bug noted")
