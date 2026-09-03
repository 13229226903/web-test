import io
# page_map update
p = r"page_map\pokecut\mobile_home_v1.yaml"
s = io.open(p, encoding="utf-8").read()
old = """        enabled_condition: 输入框为空时不满足提交条件，默认 disabled
        action_result: 禁用态点击不跳转、不发起生成"""
new = """        enabled_condition: 输入框为空时 disabled；输入文本后 enabled
        action_result: 空态点击不跳转/不生成；输入文本后点击进入 /create/edit?pid=* 画布（匿名态随后弹出注册/获取点数弹层）"""
assert old in s
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)

# cases.md add new case row and update frontmatter counts
p2 = r"artifacts\task-22_feishu_mobile_home\cases.md"
c = io.open(p2, encoding="utf-8").read()
newrow = "| TC-MH-L2-022 | L2 | default_full | Agent 输入框输入文本后 Generate 可点击并进入画布 | 在首屏 textarea 输入 \"a studio portrait with soft light\" 后点击 Generate | 1.5s/8s | 输入前 Generate disabled；输入后 enabled；点击后 URL 进入 /create/edit?pid=* 画布（匿名态随后出现注册/获取点数弹层） | 画布+弹层 | states.mobile_default.buttons.agent_generate |\n"
anchor = "| TC-MH-L2-006 |"
idx = c.find(anchor)
# find end of that line
end = c.find("\n", idx)
c = c[:end+1] + newrow + c[end+1:]
c = c.replace("case_count: 28", "case_count: 21")
c = c.replace("priority_breakdown: {P0: 2, P1: 16, P2: 10}", "priority_breakdown: {P0: 1, P1: 16, P2: 4}")
io.open(p2, "w", encoding="utf-8").write(c)
print("patched page_map + cases.md")
