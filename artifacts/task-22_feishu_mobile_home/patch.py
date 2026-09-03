import io
p = r"artifacts\task-22_feishu_mobile_home\explore_fix2.py"
s = io.open(p, encoding="utf-8").read()
old = 'panel.eval_on_selector_all("a", "els => els.map(e=>({t:(e.innerText||\'\').trim(), href:e.href, submit:e.getAttribute(\'data-submit-ticket\')}))")'
new = 'panel.locator("a").evaluate_all("els => els.map(e=>({t:(e.innerText||\'\').trim(), href:e.href, submit:e.getAttribute(\'data-submit-ticket\')}))")'
assert old in s, "old not found"
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("ok")
