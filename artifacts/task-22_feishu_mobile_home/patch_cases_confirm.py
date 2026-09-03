import io
p = r"artifacts\task-22_feishu_mobile_home\cases.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace("status: pending_review", "status: confirmed", 1)
io.open(p, "w", encoding="utf-8").write(s)
print("cases.md confirmed")
