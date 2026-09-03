import io
p = r"artifacts\task-22_feishu_mobile_home\sync.md"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
"- ⏭ ID Photo Maker 抠图成功/失败/点数不足 — skipped（完整上传会触发抠图，可能消耗 credits；文件选择器触发已覆盖）",
"- ✅ ID Photo Maker 点击唤起上传弹窗 — covered（文件选择器触发）\n- ⚠️ ID Photo Maker 匿名态上传有效图 — 实际：停留在首页并打开注册/获取点数弹层（需登录 + credits 才进入抠图）\n- ✅ ID Photo Maker 匿名态上传损坏图 — covered：不跳转、不进入画布（首页拦截；未捕获明确错误提示）\n- ⏭ ID Photo Maker 抠图成功/点数不足 — skipped（需登录且具备对应 credits 的账号状态）\n- ⏭ ID Photo Maker 抠图失败反馈 — skipped（需登录后可正常上传但抠图失败的素材/账号态，暂缺）"
)
s = s.replace(
"- ID Photo Maker 完整上传流程（抠图成功/失败/点数不足）：可能消耗 credits，探索阶段仅验证文件选择器触发。",
"- ID Photo Maker 抠图成功/抠图失败/点数不足：需登录且具备对应 credits/账号状态的账号；匿名态仅能验证到「打开注册/获取点数弹层」与「损坏图首页拦截」。"
)
io.open(p, "w", encoding="utf-8").write(s)
print("patched sync.md")
