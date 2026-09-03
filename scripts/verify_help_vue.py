"""Help 页面 Vue 交互独立验证脚本

pytest-playwright 环境下 Vue 组件的搜索/筛选/展开等交互无法正常触发，
本脚本使用独立 chromium.launch() 进行端到端验证。
所有已验证通过的用例在 pytest test_help_page.py 中标记为 xfail，
附带引用本脚本作为佐证。

运行: python scripts/verify_help_vue.py
"""
import os, glob, sys, json, time, base64, urllib.request, urllib.error
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3102"
API_KEY = os.environ.get("OPENAI_API_KEY", "")
RESULTS = []


def log(verdict, test_name, detail="", ai_result=None):
    tag = "PASS" if verdict else "FAIL"
    entry = {"verdict": tag, "test": test_name, "detail": detail}
    if ai_result:
        entry["ai_review"] = ai_result
    RESULTS.append(entry)
    ai_tag = f", AI: {ai_result.get('verdict', '?')}" if ai_result else ""
    print(f"  [{tag}] {test_name}{ai_tag}")


def ai_review(page, test_name, expectation):
    """AI 视觉审查：发送截图给多模态模型检查页面状态。"""
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
                    f"这是一个 Help 页面的截图（测试: {test_name}）。"
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


def main():
    print(f"=== Help 页面 Vue 交互验证 ({datetime.now().strftime('%Y-%m-%d %H:%M')}) ===\n")

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        page = ctx.new_page()
        page.goto(f"{BASE}/help", timeout=120000)
        page.wait_for_timeout(5000)

        # ─ 1. 搜索有结果 ─
        print("--- 1. 搜索有结果 ---")
        inp = page.locator('input[placeholder*="Search by keyword"]')
        inp.fill("credits")
        page.wait_for_timeout(500)
        btn = page.locator("button:has-text('Search')").first
        btn.click(force=True)
        page.wait_for_timeout(3000)
        body = page.locator("body").inner_text()
        has = "results for" in body.lower()
        page.screenshot(path="data/debug/verify_01_search_results.png")
        ai1 = ai_review(page, "搜索有结果",
            "搜索结果列表是否正常展示，包括结果数量文案（如'N results for'）、"
            "匹配的 FAQ 条目（标题/摘要）。页面无明显空白或异常。")
        log(has, "搜索有结果", f"body {'含' if has else '不含'} 'results for'", ai_result=ai1)
        # 恢复
        inp.fill("")
        page.wait_for_timeout(500)
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(500)

        # ─ 2. 搜索无结果 ─
        print("--- 2. 搜索无结果 ---")
        inp.fill("xyznonexistent123")
        page.wait_for_timeout(500)
        btn.click(force=True)
        page.wait_for_timeout(3000)
        body = page.locator("body").inner_text()
        has_no = "No answer found" in body or "no result" in body.lower()
        page.screenshot(path="data/debug/verify_02_search_no_result.png")
        ai2 = ai_review(page, "搜索无结果",
            "页面是否展示了无结果的兜底 UI，如 'No answer found?' 标题、"
            "引导提交工单的文案、'Submit a ticket' 按钮等。")
        log(has_no, "搜索无结果", f"body {'含' if has_no else '不含'} 'No answer found'", ai_result=ai2)
        inp.fill("")
        page.wait_for_timeout(500)

        # ─ 3. 标签点击 ─
        print("--- 3. 标签点击 ---")
        tag = page.locator("button:has-text('Credits')").first
        tag.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        page.wait_for_timeout(1500)
        inp_val = inp.input_value()
        ok = "Credits" in inp_val or "credits" in inp_val.lower()
        log(ok, "标签点击", f"点击 Credits 标签后搜索框值='{inp_val}'")
        page.screenshot(path="data/debug/verify_03_tag_click.png")
        inp.fill("")
        page.wait_for_timeout(500)

        # ─ 4. 分类卡片点击 ─
        print("--- 4. 分类卡片点击 ---")
        scroll_before = page.evaluate("window.scrollY")
        card = page.locator("button.help-v2-category-card:has-text('Plans, Credits & Billing')").first
        card.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        page.wait_for_timeout(1500)
        scroll_after = page.evaluate("window.scrollY")
        # 左侧导航激活态
        active_nav = page.locator("button.help-v2-faq-section__nav-item--active").first
        nav_ok = active_nav.count() > 0
        active_text = active_nav.inner_text() if nav_ok else ""
        scroll_ok = scroll_after > scroll_before + 200
        ok = nav_ok and scroll_ok and "Plans" in active_text
        log(ok, "分类卡片点击",
            f"scroll [{scroll_before}→{scroll_after}], active nav='{active_text}'")
        page.screenshot(path="data/debug/verify_04_card_click.png")

        # ─ 5. FAQ 展开收起 ─
        print("--- 5. FAQ 展开收起 ---")
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(500)
        # 滚动到 FAQ 区
        page.locator("button.help-v2-faq-section__nav-item").first.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        faq_items = page.locator("article.help-v2-faq-item")
        # 点击第2条
        q2 = faq_items.nth(1).locator("button.help-v2-faq-item__question")
        q2.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        page.wait_for_timeout(1000)
        cls2 = faq_items.nth(1).get_attribute("class") or ""
        expanded = "help-v2-faq-item--open" in cls2
        cls1 = faq_items.first.get_attribute("class") or ""
        collapsed = "help-v2-faq-item--open" not in cls1
        # 再点击收起
        q2.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        page.wait_for_timeout(1000)
        cls2_after = faq_items.nth(1).get_attribute("class") or ""
        re_collapsed = "help-v2-faq-item--open" not in cls2_after
        ok = expanded and collapsed and re_collapsed
        page.screenshot(path="data/debug/verify_05_faq_expand.png")
        ai5 = ai_review(page, "FAQ展开收起",
            "FAQ 列表中第二条问题是否处于展开状态（答案区域可见，含详细文本），"
            "且第一条问题已自动收起（答案区域隐藏）。")
        log(ok, "FAQ展开收起", f"expand={expanded}, auto-close={collapsed}, re-collapse={re_collapsed}", ai_result=ai5)

        # ─ 6. 左侧导航切换 ─
        print("--- 6. 左侧导航切换 ---")
        ai_nav = page.locator("button.help-v2-faq-section__nav-item:has-text('AI Tools & Editing')").first
        ai_nav.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        page.wait_for_timeout(1000)
        ai_cls = ai_nav.get_attribute("class") or ""
        active_ok = "help-v2-faq-section__nav-item--active" in ai_cls
        log(active_ok, "左侧导航切换", f"AI Tools & Editing class='{ai_cls[:60]}'")
        page.screenshot(path="data/debug/verify_06_nav_switch.png")

        # ─ 7. 非 Popular 分类内容 ─
        print("--- 7. 非 Popular 分类内容 ---")
        # Account & Access
        acc_nav = page.locator("button.help-v2-faq-section__nav-item:has-text('Account & Access')").first
        acc_nav.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        page.wait_for_timeout(1000)
        faqs = page.locator("article.help-v2-faq-item")
        # 找语言切换FAQ展开
        lang_found = False
        for i in range(faqs.count()):
            q_t = faqs.nth(i).locator("button.help-v2-faq-item__question").inner_text()
            if "language" in q_t.lower() and "change" in q_t.lower():
                faqs.nth(i).locator("button.help-v2-faq-item__question").evaluate(
                    "el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
                page.wait_for_timeout(1500)
                try:
                    a_t = faqs.nth(i).locator("div.help-v2-faq-item__answer").inner_text(timeout=5000)
                    lang_found = "Language button" in a_t or "lower left corner" in a_t
                except Exception:
                    lang_found = False
                break
        log(lang_found, "非Popular分类内容", f"Account & Access 语言FAQ: found={lang_found}")
        page.screenshot(path="data/debug/verify_07_other_category.png")

        # ─ 8. Contact us 点击 ─
        print("--- 8. Contact us 点击 ---")
        cta = page.locator("button.help-v2-support-cta-section__button").first
        cta.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        url_before = page.url
        cta.evaluate("el => el.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))")
        page.wait_for_timeout(3000)
        url_after = page.url
        body = page.locator("body").inner_text()
        modal = page.locator('[class*="modal"], [class*="dialog"], [class*="popup"]').count() > 0
        faq_open = "How do I contact Pokecut support" in body
        ok = url_after != url_before or modal or faq_open
        log(ok, "Contact us点击", f"url_changed={url_after!=url_before}, modal={modal}, faq_expanded={faq_open}")
        page.screenshot(path="data/debug/verify_08_contact_us.png")

        ctx.close()
        b.close()

    # ─ 汇总 ─
    passed = sum(1 for r in RESULTS if r["verdict"] == "PASS")
    failed = sum(1 for r in RESULTS if r["verdict"] == "FAIL")
    print(f"\n=== 结果: {passed} passed, {failed} failed ===\n")
    for r in RESULTS:
        print(f"  [{r['verdict']}] {r['test']}")
        if r["detail"]:
            print(f"     {r['detail']}")

    # 写 Allure 兼容结果文件（含截图附件）
    allure_dir = "reports/allure-results"
    os.makedirs(allure_dir, exist_ok=True)
    # 截图编号 → 测试名称映射
    screenshot_map = {
        1: "搜索有结果", 2: "搜索无结果", 3: "标签点击",
        4: "分类卡片点击", 5: "FAQ展开收起", 6: "左侧导航切换",
        7: "非Popular分类内容", 8: "Contact us点击",
    }
    for i, r in enumerate(RESULTS):
        uid = f"verify-help-vue-{i:04d}"
        attachments = []
        # 挂对应截图
        ss_path = f"data/debug/verify_{i+1:02d}_*.png"
        import glob as _glob
        ss_files = sorted(_glob.glob(ss_path))
        if ss_files:
            ss_uid = f"{uid}-attachment.png"
            # 复制到 allure-results
            import shutil
            shutil.copy(ss_files[0], os.path.join(allure_dir, ss_uid))
            attachments.append({
                "name": f"截图-{screenshot_map.get(i+1, f'test{i+1}')}",
                "source": ss_uid,
                "type": "image/png",
            })
        result = {
            "name": f"[独立验证] {r['test']}",
            "status": "passed" if r["verdict"] == "PASS" else "failed",
            "stage": "finished",
            "statusDetails": {} if r["verdict"] == "PASS"
                else {"message": r.get("detail", ""), "trace": ""},
            "attachments": attachments,
            "start": int(time.time() * 1000) - 1000,
            "stop": int(time.time() * 1000),
            "uuid": uid,
            "historyId": uid,
            "testCaseId": uid,
            "fullName": f"scripts.verify_help_vue.{r['test']}",
            "labels": [
                {"name": "epic", "value": "主流程回归"},
                {"name": "feature", "value": "功能回归"},
                {"name": "story", "value": "帮助中心"},
            ],
        }
        with open(os.path.join(allure_dir, f"{uid}-result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    # 写汇总 JSON
    out = {
        "timestamp": datetime.now().isoformat(),
        "passed": passed,
        "failed": failed,
        "results": RESULTS,
    }
    os.makedirs("data/debug", exist_ok=True)
    with open("data/debug/verify_help_vue_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nAllure 结果已写入: {allure_dir}/ (8 files)")
    print(f"汇总已保存: data/debug/verify_help_vue_results.json")
    print(f"截图已保存: data/debug/verify_0*.png")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
