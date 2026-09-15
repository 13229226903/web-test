from pathlib import Path
f = Path("tests/test_mobile_home.py"); s = f.read_text(encoding="utf-8")
old = '''    page.wait_for_timeout(500)
    page.get_by_role("button", name="Send").first.click()
    page.wait_for_timeout(2500)'''
new = '''    page.wait_for_timeout(500)
    # Log in 页签下无 Send 按钮（仅注册页签需要先 Send），存在才点
    send = page.get_by_role("button", name="Send")
    if send.count():
        send.first.click()
        page.wait_for_timeout(2500)'''
print("patched" if old in s else "!! anchor missing")
f.write_text(s.replace(old, new), encoding="utf-8")