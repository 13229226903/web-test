from pathlib import Path
p=Path(r'D:\Test\web-test\tests\test_infinite_canvas_inspiration_debug.py')
s=p.read_text(encoding='utf-8')
# add login helper after _dismiss_purchase_overlay
marker='''def _open_agent(page: Page) -> None:
'''
insert='''def _login_member(page: Page) -> None:
    """手动登录会员账号，避免依赖 session_context 的全局登录步骤。"""
    with allure.step("登录会员账号"):
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=120000)
        page.wait_for_timeout(4500)
        _dismiss_purchase_overlay(page)
        if page.get_by_text("User8JY", exact=True).count() > 0:
            return
        login_btn = page.get_by_text("Log in", exact=True)
        expect(login_btn.first).to_be_visible(timeout=20000)
        login_btn.first.click(timeout=10000)
        page.wait_for_timeout(1200)
        try:
            page.locator("button:has-text('Log in'):visible").last.click(timeout=3000)
            page.wait_for_timeout(600)
        except Exception:
            pass
        page.locator('input[type="email"]').first.fill(MEMBER_EMAIL, timeout=10000)
        page.locator('input[placeholder="Verification Code"], input[data-testid="auth-code-input"], input[type="text"]').first.fill(VERIFY_CODE, timeout=10000)
        page.locator("button:has-text('Log in'):visible, button[data-testid='auth-submit']").last.click(timeout=10000)
        page.wait_for_timeout(7000)
        expect(page.get_by_text("User8JY", exact=True).first).to_be_visible(timeout=30000)


'''
if marker in s and '_login_member' not in s:
    s=s.replace(marker, insert+marker)
# replace test signatures session_page to page+base_url
repls=[
('def test_dbg_submit_fail_then_recover(session_page: Page):','def test_dbg_submit_fail_then_recover(page: Page, base_url: str):'),
('    page = session_page\n    _open_agent(page)','    _login_member(page)\n    _open_agent(page)'),
('def test_dbg_query_fail_then_recover(session_page: Page):','def test_dbg_query_fail_then_recover(page: Page, base_url: str):'),
('    page = session_page\n    _open_agent(page)','    _login_member(page)\n    _open_agent(page)'),
('def test_dbg_query_fail_modes(session_page: Page, switch_label: str, expected_text: str, shot_prefix: str):','def test_dbg_query_fail_modes(page: Page, base_url: str, switch_label: str, expected_text: str, shot_prefix: str):'),
('    page = session_page\n    _open_agent(page)','    _login_member(page)\n    _open_agent(page)'),
('def test_reference_upload_limit_and_delete(session_page: Page, model_text: str, max_count: int, files: list[Path], expected_tip: str, expected_counter: str):','def test_reference_upload_limit_and_delete(page: Page, base_url: str, model_text: str, max_count: int, files: list[Path], expected_tip: str, expected_counter: str):'),
('    page = session_page\n    _open_agent(page)','    _login_member(page)\n    _open_agent(page)'),
('def test_reference_switch_retains_first_n(session_page: Page):','def test_reference_switch_retains_first_n(page: Page, base_url: str):'),
('    page = session_page\n    _open_agent(page)','    _login_member(page)\n    _open_agent(page)'),
('def test_reference_multi_select_overflow_shows_tip(session_page: Page, model_text: str, files: list[Path], expected_tip: str, expected_counter: str):','def test_reference_multi_select_overflow_shows_tip(page: Page, base_url: str, model_text: str, files: list[Path], expected_tip: str, expected_counter: str):'),
('    page = session_page\n    _open_agent(page)','    _login_member(page)\n    _open_agent(page)'),
('def test_reference_upload_smoke_with_submit(session_page: Page):','def test_reference_upload_smoke_with_submit(page: Page, base_url: str):'),
('    page = session_page\n    _open_agent(page)','    _login_member(page)\n    _open_agent(page)'),
]
for old,new in repls:
    if old in s:
        s=s.replace(old,new)
# add base_url import usage maybe not needed; ensure anonymous tests not present.
p.write_text(s,encoding='utf-8')
