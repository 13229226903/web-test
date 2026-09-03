import io
p = r"artifacts\task-22_feishu_mobile_home\sync.md"
s = io.open(p, encoding="utf-8").read()
old = "- ✅ Generate 未满足条件禁用 — covered"
new = "- ✅ Generate 未满足条件禁用 — covered（输入框为空时 disabled）\n- ✅ Agent 输入框输入文本后 Generate 可点击并进入画布 — covered（输入后 enabled，点击进入 /create/edit?pid=*，匿名态随后弹注册/获取点数弹层）"
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("sync.md updated")
