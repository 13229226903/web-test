"""移动端鉴黄探针 v2：每个功能都用全新未审核图独立测，统计 vB3Fse37k861v51a 调用。
- 输入鉴黄：提交后短时间内出现 nsfw 调用
- 结果鉴黄：出结果后再次出现 nsfw 调用
- 跳过鉴黄：同一图第二次用别的输入鉴黄功能，nsfw 调用=0，并抓统计
口径：测试服 3001，iPhone 390x844/dpr3/hasTouch，PRO 账号 450832596@qq.com
"""
import os, json, time
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
NSFW = "vB3Fse37k861v51a"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IMG_CLEAN = os.path.join(ROOT, "test_images", "有人脸.JPG")
OUT = os.path.join(ROOT, "artifacts", "2026-10-30_v34_nsfw_mobile_test", "evidence", "nsfw_probe")
os.makedirs(os.path.join(OUT, "shots"), exist_ok=True)

TOOLS = ["画质增强","AI消除笔","AI扩图","AI改图","AI人脸编辑器","AI身体编辑器","发型试穿","AI滤镜","AI姿势","AI换衣服工具","水印去除","老照片修复"]

def login(pg):
    pg.goto(f"{BASE}/zh", wait_until="domcontentloaded"); pg.wait_for_timeout(3000)
    pg.get_by_label("积分").click(); pg.wait_for_timeout(1200)
    pg.get_by_text("注册领取更多", exact=True).first.click(); pg.wait_for_timeout(1800)
    pg.get_by_text("登录", exact=True).last.click(); pg.wait_for_timeout(1500)
    pg.get_by_placeholder("电子邮件").fill("450832596@qq.com")
    pg.get_by_placeholder("验证码").fill("123456")
    pg.get_by_role("button", name="登录", exact=True).last.click(); pg.wait_for_timeout(5000)

def fresh_upload(pg):
    pg.goto(f"{BASE}/zh", wait_until="domcontentloaded"); pg.wait_for_timeout(2500)
    with pg.expect_file_chooser() as fc:
        pg.get_by_text("开始免费创作", exact=True).first.click()
    fc.value.set_files(IMG_CLEAN); pg.wait_for_timeout(7000)
    return pg.url

def close_panel(pg):
    pg.evaluate("()=>{const i=document.querySelector('img[src*=\"nav_btn_pop_close2\"]');if(i)(i.closest('div,button')||i).click();}")
    pg.wait_for_timeout(1200)

def main():
    res = {"tools": {}, "skip": {}, "prompt": {}}
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        ctx = b.new_context(viewport={"width":390,"height":844},
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            device_scale_factor=3, has_touch=True, is_mobile=True, locale="zh-CN")
        pg = ctx.new_page()
        calls = []
        pg.on("request", lambda r: calls.append(time.time()) if NSFW in r.url() else None)
        cons = []
        pg.on("console", lambda m: cons.append(m.text))
        login(pg)
        for name in TOOLS:
            rec = {}
            try:
                fresh_upload(pg)
                calls.clear()
                pg.get_by_text(name, exact=True).first.click(timeout=8000)
                pg.wait_for_timeout(2200)
                gen = pg.locator("button.mobile-ai-generate-button")
                if gen.count() == 0:
                    rec["status"] = "no_submit"
                    pg.screenshot(path=os.path.join(OUT,"shots",f"{name}_nosubmit.png"))
                    close_panel(pg); res["tools"][name]=rec; continue
                rec["submit"] = gen.first.inner_text().replace("\n"," ")
                t0 = time.time(); gen.first.click()
                for _ in range(12): pg.wait_for_timeout(2000)
                rec["nsfw_calls"] = len(calls)
                rec["offsets_s"] = [round(c-t0,1) for c in calls]
                body = pg.evaluate("()=>document.body.innerText")
                rec["has_moderation_ui"] = ("敏感" in body) or ("违规" in body)
                rec["status"] = "ok"
                pg.screenshot(path=os.path.join(OUT,"shots",f"{name}.png"))
                close_panel(pg)
            except Exception as e:
                rec["status"] = "error"; rec["error"] = str(e)[:180]
            res["tools"][name] = rec

        # 跳过鉴黄：同一图 画质增强 -> 背景移除（不重新上传）
        try:
            fresh_upload(pg)
            calls.clear()
            pg.get_by_text("画质增强", exact=True).first.click(); pg.wait_for_timeout(2000)
            pg.locator("button.mobile-ai-generate-button").first.click(); pg.wait_for_timeout(12000)
            calls_after_first = len(calls)
            # 应用结果
            pg.get_by_text("确认", exact=True).first.click(); pg.wait_for_timeout(4000)
            cons.clear()
            calls.clear()
            pg.locator("li.mobile-primary-panel__tab", has_text="背景").first.click(); pg.wait_for_timeout(1500)
            pg.get_by_text("背景移除", exact=True).first.click(); pg.wait_for_timeout(1800)
            gen = pg.locator("button.mobile-ai-generate-button")
            if gen.count()>0:
                gen.first.click(); pg.wait_for_timeout(12000)
            res["skip"] = {"first_tool_calls": calls_after_first, "second_tool_calls": len(calls),
                           "console_skip": [c for c in cons if "content-review" in c or "skip" in c.lower()][:10]}
        except Exception as e:
            res["skip"] = {"error": str(e)[:180]}

        # prompt 违规
        try:
            pg.locator("li.mobile-primary-panel__tab", has_text="AI生图").first.click(); pg.wait_for_timeout(2000)
            ta = pg.locator("textarea").first; ta.click(); ta.fill("裸体")
            pg.locator("button").filter(has_text="生成").last.click(); pg.wait_for_timeout(10000)
            body = pg.evaluate("()=>document.body.innerText")
            res["prompt"] = {"has_ui": "敏感" in body, "line": next((l for l in body.splitlines() if "敏感" in l), None)}
            pg.screenshot(path=os.path.join(OUT,"shots","prompt_bad.png"))
        except Exception as e:
            res["prompt"] = {"error": str(e)[:180]}

        res["console_skip_all"] = [c for c in cons if "content-review" in c or "鉴黄" in c][:20]
        ctx.close(); b.close()
    with open(os.path.join(OUT,"probe_results.json"),"w",encoding="utf-8") as f:
        json.dump(res,f,ensure_ascii=False,indent=2)
    print(json.dumps(res,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    main()
