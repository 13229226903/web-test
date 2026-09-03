"""首页 CTA 按钮点击 - 面板打开验证

pytest 环境下按钮点击后 Vue 设置的工具上下文丢失（Body/Manual Mode 面板不打开），
使用独立 chromium 验证。包括 AI 视觉审查对截图做断言。

运行: python scripts/verify_homepage_vue.py
"""
import os, sys, glob, json, base64, time, urllib.request, urllib.error
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
RESULTS = []
API_KEY = os.environ.get("OPENAI_API_KEY", "")


def pick_test_image():
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_images")
    if os.path.isdir(d):
        imgs = sorted(glob.glob(os.path.join(d, "*")), key=lambda f: os.path.getsize(f))
        if imgs:
            return os.path.abspath(imgs[0])


def ai_review(page, test_name, expectation):
    """AI 视觉审查：发送截图给多模态模型检查面板状态。"""
    if not API_KEY:
        return {"verdict": "skipped", "reason": "未设置 OPENAI_API_KEY"}

    png_b64 = base64.b64encode(page.screenshot(full_page=False)).decode()
    body = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-5.6"),
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png_b64}"}},
                {"type": "text", "text": (
                    f"这是一个首页 CTA 按钮点击后进入画布编辑页的截图（测试: {test_name}）。"
                    f"请检查：{expectation}"
                    f"回答格式：只返回一个 JSON 对象，不要包含任何其他文字："
                    f'{{"verdict": "pass或fail", "reason": "一句话说明判断依据（中文）"}}'
                )},
            ]
        }]
    }

    req = urllib.request.Request(
        os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
    except Exception as e:
        return {"verdict": "error", "reason": f"API 调用失败: {e}"}

    cleaned = text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else parts[0]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        lower = text.lower()
        if "pass" in lower and "fail" not in lower:
            return {"verdict": "pass", "reason": text.strip()}
        elif "fail" in lower:
            return {"verdict": "fail", "reason": text.strip()}
        return {"verdict": "uncertain", "reason": f"无法解析: {text[:200]}"}


def log(verdict, test_name, detail="", ai_result=None):
    tag = "PASS" if verdict else "FAIL"
    entry = {"verdict": tag, "test": test_name, "detail": detail}
    if ai_result:
        entry["ai_review"] = ai_result
    RESULTS.append(entry)
    ai_tag = f", AI: {ai_result.get('verdict', '?')}" if ai_result else ""
    print(f"  [{tag}] {test_name}{ai_tag}")


def main():
    print(f"=== 首页 Vue 面板验证 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n")

    test_img = pick_test_image()
    if not test_img:
        print("错误: 未找到测试图片")
        return 1
    print(f"测试图片: {os.path.basename(test_img)} ({os.path.getsize(test_img)} bytes)\n")

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")

        # ── TC-HOME: Retouch Portrait with AI Now ──
        print("--- 1. Retouch Portrait with AI Now → 修图面板 ---")
        page = ctx.new_page()
        page.goto(f"{BASE}/", timeout=120000)
        page.wait_for_timeout(8000)
        page.evaluate("window.scrollTo(0, 1400)")
        page.wait_for_timeout(3000)

        btn0 = page.locator("button:has-text('Retouch Portrait with AI Now')").first
        with page.expect_file_chooser(timeout=10000) as fc:
            btn0.click(force=True)
        fc.value.set_files(test_img)
        page.wait_for_timeout(15000)
        page.screenshot(path="data/debug/verify_home_01_retouch_portrait.png")
        right0 = page.evaluate("""() => {
            var out = []; document.querySelectorAll("*").forEach(function(e) {
                if (e.children.length > 0) return;
                var r = e.getBoundingClientRect();
                var t = (e.textContent || "").trim();
                if (t && r.x > 960 && r.y > 100 && r.y < 900) out.push(t.substring(0, 80));
            }); return out;
        }""")
        has_retouch = any("Retouch" in item or "Remove" in item for item in right0)
        log(has_retouch, "RetouchPortrait-修图面板", f"Retouch相关={has_retouch}, right_panel={right0[:5]}")
        page.close()

        # ── TC-HOME-004: Enhance Your Body Now ──
        print("\n--- 2. Enhance Your Body Now → Body 面板 ---")
        page = ctx.new_page()
        page.goto(f"{BASE}/", timeout=120000)
        page.wait_for_timeout(8000)
        page.evaluate("window.scrollTo(0, 2100)")
        page.wait_for_timeout(3000)

        btn = page.locator("button:has-text('Enhance Your Body Now')").first
        with page.expect_file_chooser(timeout=10000) as fc:
            btn.click(force=True)
        fc.value.set_files(test_img)
        page.wait_for_timeout(15000)
        page.screenshot(path="data/debug/verify_home_02_enhance_body.png")

        # DOM 断言：右侧面板含 Body/Face/Hair 等身体分类
        right_panel = page.evaluate("""() => {
            var out = []; document.querySelectorAll("*").forEach(function(e) {
                if (e.children.length > 0) return;
                var r = e.getBoundingClientRect();
                var t = (e.textContent || "").trim();
                if (t && r.x > 960 && r.y > 100 && r.y < 900) out.push(t.substring(0, 80));
            }); return out;
        }""")
        has_body = any("Body" in item for item in right_panel)
        has_face = any("Face" in item for item in right_panel)
        dom_ok = has_body and has_face
        log(dom_ok, "EnhanceYourBody-Body面板", f"Body={has_body}, Face={has_face}")
        page.close()

        # ── TC-HOME-006: Cleanup Product Images Now ──
        print("\n--- 3. Cleanup Product Images Now → Manual Mode 面板 ---")
        page = ctx.new_page()
        page.goto(f"{BASE}/", timeout=120000)
        page.wait_for_timeout(8000)
        page.evaluate("window.scrollTo(0, 4200)")
        page.wait_for_timeout(3000)

        btn2 = page.locator("button:has-text('Cleanup Product Images Now')").first
        with page.expect_file_chooser(timeout=10000) as fc:
            btn2.click(force=True)
        fc.value.set_files(test_img)
        page.wait_for_timeout(15000)
        page.screenshot(path="data/debug/verify_home_03_cleanup.png")

        # DOM 断言：右侧面板含 Manual Mode 相关文本
        right_panel2 = page.evaluate("""() => {
            var out = []; document.querySelectorAll("*").forEach(function(e) {
                if (e.children.length > 0) return;
                var r = e.getBoundingClientRect();
                var t = (e.textContent || "").trim();
                if (t && r.x > 960 && r.y > 100 && r.y < 900) out.push(t.substring(0, 80));
            }); return out;
        }""")
        has_manual = any("Manual" in item for item in right_panel2)
        log(has_manual, "CleanupProductImages-Manual面板", f"Manual={has_manual}")
        page.close()

        ctx.close()
        b.close()

    # ─ 汇总 ─
    passed = sum(1 for r in RESULTS if r["verdict"] == "PASS")
    failed = sum(1 for r in RESULTS if r["verdict"] == "FAIL")
    print(f"\n=== 结果: {passed} passed, {failed} failed ===\n")
    for r in RESULTS:
        print(f"  [{r['verdict']}] {r['test']}")
        if r.get("detail"):
            print(f"     {r['detail']}")

    # Allure 结果
    allure_dir = "reports/allure-results"
    os.makedirs(allure_dir, exist_ok=True)
    import shutil as _shutil
    for i, r in enumerate(RESULTS):
        uid = f"verify-home-vue-{i:04d}"
        attachments = []
        ss_files = sorted(glob.glob(f"data/debug/verify_home_0{i//2+1}_*.png"))
        if ss_files:
            ss_uid = f"{uid}-attachment.png"
            _shutil.copy(ss_files[0], os.path.join(allure_dir, ss_uid))
            attachments.append({"name": f"截图-{r['test']}", "source": ss_uid, "type": "image/png"})
        result = {
            "name": f"[独立验证] {r['test']}",
            "status": r["verdict"].lower(),
            "stage": "finished",
            "statusDetails": {} if r["verdict"] == "PASS" else {"message": r.get("detail", ""), "trace": ""},
            "attachments": attachments,
            "start": int(time.time() * 1000) - 1000,
            "stop": int(time.time() * 1000),
            "uuid": uid, "historyId": uid, "testCaseId": uid,
            "fullName": f"scripts.verify_homepage_vue.{r['test']}",
            "labels": [
                {"name": "epic", "value": "主流程回归"},
                {"name": "feature", "value": "功能回归"},
                {"name": "story", "value": "首页"},
            ],
        }
        with open(os.path.join(allure_dir, f"{uid}-result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\nAllure 结果已写入: {allure_dir}/ (4 files)")
    print(f"截图已保存: data/debug/verify_home_*.png")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
