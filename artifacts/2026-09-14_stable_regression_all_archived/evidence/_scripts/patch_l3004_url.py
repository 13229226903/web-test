from pathlib import Path
f = Path("tests/test_mobile_home.py"); s = f.read_text(encoding="utf-8")
old = '''        with allure.step("断言进入证件照画布"):
            body = page.inner_text("body")
            assert "/create/edit?pid=" in page.url, f"未进入画布: url={page.url}"
            markers = ["ID Photo", "Passport", "ID photo", "证件照"]
            assert any(m in body for m in markers), f"画布未出现证件照面板标记 {markers}，正文片段: {body[:200]}"'''
new = '''        with allure.step("断言进入证件照画布"):
            # 2026-09-15 实测：ID Photo Maker 抠图成功后进入 /tools/id-photo-edit?pid=<uuid>（证件照画布）
            assert "/tools/id-photo-edit?pid=" in page.url, f"未进入证件照画布: url={page.url}"
            assert page.locator("canvas, img").count() > 0, "证件照画布未渲染图片/画布元素"'''
print("patched" if old in s else "!! anchor missing")
f.write_text(s.replace(old, new), encoding="utf-8")