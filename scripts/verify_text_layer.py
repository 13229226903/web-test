"""画布文字图层独立验证：间距/轮廓/翻转旋转。

pytest chromium 下 Canvas 交互精度 + Vue slider 回滚不可靠，
用独立 chromium.launch() 验证。
"""
import os, sys, glob, json, time, base64, urllib.request, urllib.error
from datetime import datetime
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"

# 加载 .env 文件里的 OPENAI_API_KEY
_env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_env_path):
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                if _k not in os.environ:
                    os.environ[_k] = _v.strip('"').strip("'")

API_KEY = os.environ.get("OPENAI_API_KEY", "")
RESULTS = []


def pick_test_image():
    d = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "test_images")
    imgs = sorted(glob.glob(os.path.join(d, "*")), key=os.path.getsize)
    return os.path.abspath(imgs[0]) if imgs else None


def log(verdict, name, detail=""):
    RESULTS.append({"verdict": "PASS" if verdict else "FAIL", "test": name, "detail": detail})
    print(f"  [{'PASS' if verdict else 'FAIL'}] {name}")


def ai_review(page, name, expectation):
    if not API_KEY:
        return {"verdict": "skipped", "reason": "未设置 OPENAI_API_KEY"}
    png = base64.b64encode(page.screenshot(full_page=False)).decode()
    body = {
        "model": os.environ.get("OPENAI_MODEL", "gpt-5.6"), "max_tokens": 300,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png}"}},
            {"type": "text", "text": f"画布文字图层操作截图（{name}）。{expectation}回答格式：{{\"verdict\":\"pass或fail\",\"reason\":\"一句话中文判断\"}}"}
        ]}]
    }
    req = urllib.request.Request(
        os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
        data=json.dumps(body).encode(), headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            text = json.loads(r.read())["choices"][0]["message"]["content"]
    except Exception as e:
        return {"verdict": "error", "reason": str(e)}
    cleaned = text.strip()
    if "```" in cleaned:
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"): cleaned = cleaned[4:]
    try: return json.loads(cleaned.strip())
    except: return {"verdict": "pass" if "pass" in text.lower() and "fail" not in text.lower() else "fail", "reason": text.strip()}


def main():
    print(f"=== 画布文字图层独立验证 ({datetime.now():%Y-%m-%d %H:%M}) ===\n")
    test_img = pick_test_image()
    if not test_img: return 1

    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        page = ctx.new_page()

        # ── 登录 ──
        page.goto(BASE, timeout=120000)
        page.wait_for_timeout(5000)
        page.get_by_text("Log in", exact=True).first.click()
        page.wait_for_timeout(3000)
        page.locator("input[type=email]").fill("450832596@qq.com")
        page.locator("input[placeholder*=Verification]").fill("123456")
        page.evaluate("""() => {var btns=document.querySelectorAll("button");for(var i=0;i<btns.length;i++){if(btns[i].textContent.trim()==="Log in"&&btns[i].offsetWidth>200){btns[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
        page.wait_for_timeout(10000)
        page.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(o=>{var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba"))o.remove()})}""")
        page.wait_for_timeout(2000)

        def setup_canvas():
            """进画布→删图片→加文字→选中。返回容器坐标。"""
            page.goto(f"{BASE}/zh/create", timeout=120000)
            page.wait_for_timeout(8000)
            with page.expect_file_chooser(timeout=10000) as fc:
                page.evaluate("""() => {var cards=document.querySelectorAll('[class*="cursor-pointer"]');for(var i=0;i<cards.length;i++){if(cards[i].textContent.includes("Start from a Photo")||cards[i].textContent.includes("从照片")){cards[i].dispatchEvent(new MouseEvent("click",{bubbles:true,cancelable:true}));return;}}}""")
            fc.value.set_files(test_img)
            page.wait_for_timeout(15000)
            page.evaluate("""() => {document.querySelectorAll('div[class*="fixed"]').forEach(o=>{var bg=window.getComputedStyle(o).backgroundColor;if(bg&&bg.includes("rgba"))o.remove()})}""")
            page.wait_for_timeout(3000)
            ci = json.loads(page.evaluate("""() => {
                var divs=document.querySelectorAll('div.absolute');
                for(var i=0;i<divs.length;i++){var r=divs[i].getBoundingClientRect();if(r.width>200&&r.width<600&&r.height>300&&r.height<800&&r.x>300&&r.x<1200){var rc=divs[i].querySelector('div.relative');if(rc)return JSON.stringify({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});}}
                return JSON.stringify({x:778,y:307,w:364,h:546});
            }"""))
            cx, cy = ci['x'] + ci['w'] // 2, ci['y'] + ci['h'] // 2
            page.mouse.click(cx, cy); page.wait_for_timeout(2000)
            page.keyboard.press("Delete"); page.wait_for_timeout(3000)
            page.mouse.click(53, 480); page.wait_for_timeout(2000)
            page.mouse.click(cx, cy); page.wait_for_timeout(1500)
            page.keyboard.type("Test", delay=100); page.keyboard.press("Enter"); page.keyboard.press("Escape")
            page.wait_for_timeout(2000)
            page.wait_for_timeout(1000)
            # 切工具 → 切回 → 单击选中（单击=选中，双击=编辑）
            page.mouse.click(53, 430); page.wait_for_timeout(800)
            page.mouse.click(53, 480); page.wait_for_timeout(1500)
            page.mouse.click(cx, cy)
            page.wait_for_timeout(3000)
            return ci

        # ═══ 1. 间距 ═══
        print("--- 1. 间距 ---")
        ci = setup_canvas()
        page.mouse.click(650, 438); page.wait_for_timeout(2000)  # 调整
        # 用 JS 在 .panel-scroll-y 里找"间距"button 点击展开
        expanded = page.evaluate("""() => {
            var btns = document.querySelectorAll('.panel-scroll-y button');
            for(var i=0;i<btns.length;i++) {
                if(btns[i].textContent.trim().indexOf('间距')===0 && btns[i].offsetWidth>200) {
                    btns[i].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                    return 'clicked';
                }
            }
            return 'not-found';
        }""")
        page.wait_for_timeout(2000)
        page.screenshot(path="data/debug/verify_text_spacing.png")
        # 验证展开后 slider 出现
        sliders_after = page.evaluate("""() => {
            var panel=document.querySelector('.panel-scroll-y');if(!panel)return 0;
            return panel.querySelectorAll('input[type=range]').length;
        }""")
        log(sliders_after >= 2, "间距展开", f"展开后面板slider数={sliders_after}")
        # 间距宽度 slider 在 y≈588，直接用坐标拖拽（360px 宽，从左侧 1180 拖到中间 1360）
        page.mouse.move(1180, 591)
        page.wait_for_timeout(100)
        page.mouse.down()
        page.wait_for_timeout(100)
        page.mouse.move(1360, 591, steps=20)
        page.wait_for_timeout(100)
        page.mouse.up()
        page.wait_for_timeout(500)
        print("  间距滑块物理拖拽 1180→1360")
        ai = ai_review(page, "间距调整", "画布上文字图层的间距是否已调整，文字大小/位置与默认状态有变化。")
        log(ai.get("verdict") == "pass", "间距-AI审查", json.dumps(ai, ensure_ascii=False))

        # ═══ 2. 轮廓 (dropdown→toggle→sliders→截图) ═══
        print("\n--- 2. 轮廓 ---")
        setup_canvas()
        page.mouse.click(650, 438); page.wait_for_timeout(2000)
        page.evaluate("""() => {
            var el=null;document.querySelectorAll('span').forEach(function(s){if(s.textContent.trim()==='轮廓'&&s.offsetWidth>20)el=s;});
            if(!el)return;el.scrollIntoView({block:'center'});
            var row=el.closest('div');row.querySelectorAll('button').forEach(function(b){if(b.offsetWidth<=16)b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));});
        }""")
        page.wait_for_timeout(2000)
        # 逐个 slider 用原生 setter，间隔 500ms 让 Vue 逐个处理
        total = page.evaluate("""() => {
            var panel=document.querySelector('.panel-scroll-y');if(!panel)return 0;
            return panel.querySelectorAll('input[type=range]').length;
        }""")
        for idx in range(total):
            page.evaluate("""(idx) => {
                var panel=document.querySelector('.panel-scroll-y');
                var s=panel.querySelectorAll('input[type=range]');
                if(idx<s.length){
                    var ns=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
                    s[idx].focus();ns.call(s[idx],50);
                    s[idx].dispatchEvent(new Event('input',{bubbles:true}));
                    s[idx].dispatchEvent(new Event('change',{bubbles:true}));
                }
            }""", idx)
            page.wait_for_timeout(500)
        print(f"  逐个设置了 {total} 个 slider")
        page.screenshot(path="data/debug/verify_text_outline.png")
        log(total >= 4, "轮廓slider调整", f"slider数={total}")
        ai2 = ai_review(page, "轮廓调整", "画布上的文字是否有描边/轮廓效果（与默认文字相比有明显边框）。")
        log(ai2.get("verdict") == "pass", "轮廓-AI审查", json.dumps(ai2, ensure_ascii=False))

        # ═══ 3. 翻转旋转 ═══
        print("\n--- 3. 翻转旋转 ---")
        setup_canvas()
        page.mouse.click(1021, 438); page.wait_for_timeout(500)  # H翻转
        page.mouse.click(1118, 438); page.wait_for_timeout(500)  # V翻转
        page.mouse.click(1270, 438); page.wait_for_timeout(500)  # 旋转
        page.keyboard.press("Escape"); page.wait_for_timeout(1000)
        page.screenshot(path="data/debug/verify_text_flip.png")
        bar = page.evaluate("""() => {var c=0;document.querySelectorAll('button').forEach(function(b){var r=b.getBoundingClientRect();if(r.y>400&&r.y<500&&r.width>30)c++;});return c;}""")
        log(bar >= 3, "翻转旋转", f"顶栏按钮数={bar}")
        ai3 = ai_review(page, "翻转旋转", "画布上的文字方向是否与默认水平方向不同（被翻转或旋转了）。")
        log(ai3.get("verdict") == "pass", "翻转旋转-AI审查", json.dumps(ai3, ensure_ascii=False))

        ctx.close()
        b.close()

    # ── Allure ──
    import shutil
    allure_dir = "reports/allure-results"
    os.makedirs(allure_dir, exist_ok=True)
    ss_map = {0: "verify_text_spacing.png", 1: "verify_text_spacing.png", 2: "verify_text_outline.png", 3: "verify_text_outline.png", 4: "verify_text_flip.png", 5: "verify_text_flip.png"}
    for i, r in enumerate(RESULTS):
        uid = f"vtl-{i:04d}"
        atts = []
        ss = ss_map.get(i, "")
        if ss:
            sp = os.path.join("data", "debug", ss)
            if os.path.exists(sp):
                ss_uid = f"{uid}-attachment.png"
                shutil.copy(sp, os.path.join(allure_dir, ss_uid))
                atts.append({"name": f"截图-{r['test']}", "source": ss_uid, "type": "image/png"})
        result = {
            "name": f"[独立验证] {r['test']}",
            "status": r["verdict"].lower(), "stage": "finished",
            "statusDetails": {} if r["verdict"] == "PASS" else {"message": r.get("detail", ""), "trace": ""},
            "attachments": atts,
            "start": int(time.time() * 1000) - 1000, "stop": int(time.time() * 1000),
            "uuid": uid, "historyId": uid, "testCaseId": uid,
            "fullName": f"scripts.verify_text_layer.{r['test']}",
            "labels": [{"name": "epic", "value": "主流程回归"}, {"name": "feature", "value": "功能回归"}, {"name": "story", "value": "画布文字图层"}],
        }
        with open(os.path.join(allure_dir, f"{uid}-result.json"), "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

    passed = sum(1 for r in RESULTS if r["verdict"] == "PASS")
    print(f"\n=== {passed}/{len(RESULTS)} passed ===")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
