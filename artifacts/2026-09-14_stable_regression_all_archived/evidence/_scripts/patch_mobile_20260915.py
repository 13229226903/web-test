# -*- coding: utf-8 -*-
"""2026-09-15: 修复移动端首页 L2-020(Generate 默认模型断言) 与 L3-004(登录态上线后落地真实用例)。"""
from pathlib import Path

f = Path("tests/test_mobile_home.py")
s = f.read_text(encoding="utf-8")
log = []

helper = '''ACCOUNT_EMAIL = "450832596@qq.com"
ACCOUNT_CODE = "123456"
MODEL_NAMES = ["Auto", "Nano Banana 2 Lite", "Nano Banana 2", "Nano Banana Pro", "Seedream 5.0 Pro",
               "Seedream 5.0 Lite", "Seedream4.0", "Pokecut Pro", "Pokecut Basic", "ChatGPT Image 2.0"]


def login_vip(page: Page, base_url: str) -> None:
    """首页 Sign up/Log in 弹层登录 VIP 账号。

    2026-09-15 复探：弹层需先点 Send（获取/校验验证码）再点 Log in 提交；
    登录成功后 header 的 Sign up / Log in 按钮消失。
    """
    goto_home(page, base_url)
    page.get_by_role("button", name="Sign up").first.click()
    page.wait_for_timeout(2500)
    page.get_by_text("Log in", exact=True).last.click()
    page.wait_for_timeout(1500)
    page.locator("input[type='email']").first.fill(ACCOUNT_EMAIL)
    page.locator("input[placeholder='Verification Code']").first.fill(ACCOUNT_CODE)
    page.wait_for_timeout(500)
    page.get_by_role("button", name="Send").first.click()
    page.wait_for_timeout(2500)
    page.get_by_role("button", name="Log in").last.click()
    page.wait_for_timeout(12000)


'''
anchor_upload = "def upload_via(page: Page, trigger, file_path: str):"
if "def login_vip(" in s:
    log.append("login_vip already present")
elif anchor_upload in s:
    s = s.replace(anchor_upload, helper + anchor_upload)
    log.append("inserted login_vip + constants")
else:
    log.append("!! upload anchor missing")

old_else = '                else:\n                    assert "/create/edit?pid=" in page.url'
new_else = '''                else:
                    assert "/create/edit?pid=" in page.url
                    if item == "Generate":
                        # 2026-09-15 复探：生图面板应默认选中 Auto（实测当前为 Nano Banana 2 Lite）
                        actual_model = None
                        for idx in range(page.locator("button").count()):
                            text = (page.locator("button").nth(idx).inner_text() or "").strip()
                            if text in MODEL_NAMES:
                                actual_model = text
                                break
                        assert actual_model == "Auto", f"生图面板默认模型应为 Auto，实际为 {actual_model}"'''
if old_else in s:
    s = s.replace(old_else, new_else)
    log.append("patched L2-020 Generate assertion")
else:
    log.append("!! L2-020 anchor missing")

old_stub = '''    @pytest.mark.skip(reason="blocked_by_bug: 首页 Sign up 登录弹层提交无反应，无法建立登录态")
    def test_l3_004_id_photo_success(self):
        """覆盖层级: Layer 3 — 异常/权限；前置条件: 登录具备 ID credits 的账号；预期: 抠图成功进入证件照画布"""
        pass'''
new_impl = '''    def test_l3_004_id_photo_success(self, mobile_page: Page, base_url: str):
        """覆盖层级: Layer 3 — 登录态 + 证件照流程。

        2026-09-15 复探：首页 Sign up/Log in 弹层现已可正常建立登录态（需先 Send 再提交），
        故选例取消 skip，落地真实断言。
        前置条件: 登录具备 ID credits 的 VIP 账号；预期: 抠图成功进入证件照画布。
        """
        page = mobile_page
        login_vip(page, base_url)
        with allure.step("ID Photo Maker 上传有人脸图片"):
            upload_via(page, page.get_by_role("button", name="ID Photo Maker").first, IMG_VALID)
            page.wait_for_timeout(30000)
        with allure.step("断言进入证件照画布"):
            body = page.inner_text("body")
            assert "/create/edit?pid=" in page.url, f"未进入画布: url={page.url}"
            markers = ["ID Photo", "Passport", "ID photo", "证件照"]
            assert any(m in body for m in markers), f"画布未出现证件照面板标记 {markers}，正文片段: {body[:200]}"
        shot(page, "L3-004_证件照画布")'''
if old_stub in s:
    s = s.replace(old_stub, new_impl)
    log.append("unskipped + implemented L3-004")
else:
    log.append("!! L3-004 stub anchor missing")

f.write_text(s, encoding="utf-8")
print("\n".join(log))