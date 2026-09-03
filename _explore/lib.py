# -*- coding: utf-8 -*-
"""page-map-sync 深度探索共享库：登录、打开工具卡、去遮罩、DOM 转储、轮询等待。
非测试代码，仅用于地图探索。"""
import os, sys, time, io

# 保证 stdout 用 utf-8（Windows 控制台默认 gbk 会崩）
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

REPO = r"D:\Test\web-test"
SHOTS = os.path.join(REPO, "artifacts", "2026-07-13_pokecut_create_ai_tools", "shots")
DEBUG = os.path.join(REPO, "data", "debug")
IMG = os.path.join(REPO, "test_images", "多人脸.jpg")   # 114KB 小图，含人物主体
os.makedirs(SHOTS, exist_ok=True)
os.makedirs(DEBUG, exist_ok=True)

BASE = "http://10.17.1.66:3001"
EMAIL = os.environ.get("POKECUT_TEST_EMAIL", "450832596@qq.com")
CODE = os.environ.get("POKECUT_TEST_CODE", "123456")


def log(*a):
    print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)


def dismiss(page):
    """JS 移除定价/VIP 半透明遮罩（只删背景遮罩，不碰弹窗内容/登录表单）。"""
    try:
        page.evaluate("""() => {
            document.querySelectorAll('div[class*="fixed"]').forEach(o => {
                const bg = window.getComputedStyle(o).backgroundColor;
                if (bg && bg.includes('rgba') && (bg.includes('0.3') || bg.includes('0.5') || bg.includes('0.6'))) {
                    o.remove();
                }
            });
        }""")
    except Exception:
        pass


def close_vip_modal(page):
    """关闭首页 VIP 定价弹窗：找关闭按钮/Escape，不误删登录表单。"""
    try:
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
    except Exception:
        pass


def _do_login(page):
    log("goto", BASE)
    page.goto(BASE)
    page.wait_for_timeout(6000)
    dismiss(page)               # 关掉首页 VIP 定价弹窗背景遮罩
    page.wait_for_timeout(1000)
    # 反复尝试打开登录表单：点 "Log in" → 轮询 email 输入框；期间关 VIP 弹窗
    email_box = page.locator('input[type="email"]')
    opened = False
    for i in range(4):
        # 点顶部导航 "Log in"（Vue 组件：坐标点击 + dispatchEvent，locator.click 不生效）
        try:
            box = page.evaluate("""() => {
                for (const b of document.querySelectorAll('button')) {
                    const r=b.getBoundingClientRect();
                    if ((b.innerText||'').trim()==='Log in' && r.y<100 && r.width>0) {
                        b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                        return {x:r.x,y:r.y,w:r.width,h:r.height};
                    }
                }
                return null;
            }""")
            if box:
                page.mouse.click(box["x"]+box["w"]/2, box["y"]+box["h"]/2)
        except Exception as e:
            log(f"  nav Log in click try{i} err:", str(e)[:60])
        # 轮询 email 输入框最多 ~6s
        for _ in range(6):
            page.wait_for_timeout(1000)
            try:
                if email_box.first.is_visible():
                    opened = True
                    break
            except Exception:
                pass
        if opened:
            log(f"  login form opened (try{i})")
            break
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        dismiss(page)
        page.wait_for_timeout(1000)
    if not opened:
        log("  login form NOT opened")
        page.screenshot(path=os.path.join(DEBUG, "login_form_fail.png"))
        return False
    try:
        page.locator('input[type="email"]').fill(EMAIL)
        page.locator('input[placeholder="Verification Code"]').fill(CODE)
    except Exception as e:
        log("fill failed:", str(e)[:60])
        page.screenshot(path=os.path.join(DEBUG, "login_fill_fail.png"))
        return False
    page.evaluate("""() => {
        for (const b of document.querySelectorAll('button')) {
            if (b.textContent.trim() === 'Log in' && b.offsetWidth > 200) {
                b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                return;
            }
        }
    }""")
    page.wait_for_timeout(10000)
    dismiss(page)
    page.wait_for_timeout(2000)
    bt = ""
    try:
        bt = page.locator("body").inner_text()
    except Exception:
        pass
    ok = ("User8JY" in bt) or ("Credits:" in bt)
    log("post-login check url=", page.url, "ok=", ok, "| body:", bt.replace("\n", " ")[:120])
    if not ok:
        page.screenshot(path=os.path.join(DEBUG, "login_check_fail.png"))
    return ok


def login(pw):
    browser = pw.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    page = ctx.new_page()
    ok = False
    for attempt in range(3):
        log(f"login attempt {attempt+1}")
        if _do_login(page):
            ok = True
            break
        log("login attempt failed, retrying...")
        page.wait_for_timeout(3000)
    if not ok:
        page.screenshot(path=os.path.join(DEBUG, "login_fail.png"))
        raise RuntimeError("LOGIN FAILED after 3 attempts")
    # 落地 /create 并确认 credits
    page.goto(BASE + "/create")
    page.wait_for_timeout(4000)
    dismiss(page)
    import re
    m = re.search(r"Credits:\s*(\d+)", page.locator("body").inner_text())
    cr = int(m.group(1)) if m else -1
    log("login OK url=", page.url, "credits=", cr)
    if cr <= 0:
        log("WARN credits<=0! =", cr)
    return browser, ctx, page


def open_tool(page, tool_text, image=IMG):
    """点击 Trending Tools 卡片 → 文件选择器 → 上传 → 返回落地 URL。"""
    dismiss(page)
    sel = f"div.cursor-pointer:has(p:text-is('{tool_text}'))"
    card = page.locator(sel).first
    card.scroll_into_view_if_needed()
    box = card.bounding_box()
    log(f"card '{tool_text}' box=", box)
    with page.expect_file_chooser(timeout=20000) as fc_info:
        # Vue 组件优先坐标点击
        page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    fc = fc_info.value
    fc.set_files(image)
    log("file set:", os.path.basename(image))
    page.wait_for_timeout(8000)
    dismiss(page)
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    dismiss(page)
    log("landed url=", page.url)
    return page.url


def dump_ui(page, tag):
    """转储当前可见 button 文案 + 关键控件，写入 debug 文件并打印。"""
    dismiss(page)
    info = page.evaluate("""() => {
        const vis = el => { const r = el.getBoundingClientRect();
            const s = getComputedStyle(el);
            return r.width>0 && r.height>0 && s.visibility!=='hidden' && s.display!=='none'; };
        const out = {buttons:[], inputs:[], ranges:[], canvases:[], textsnips:[], toggles:[]};
        document.querySelectorAll('button').forEach(b=>{ if(vis(b)){
            const r=b.getBoundingClientRect();
            out.buttons.push({t:(b.innerText||'').trim().slice(0,40), x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
        }});
        document.querySelectorAll('input').forEach(i=>{ if(vis(i)){
            const r=i.getBoundingClientRect();
            out.inputs.push({type:i.type,ph:i.placeholder||'',x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});
            if(i.type==='range') out.ranges.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width)});
        }});
        document.querySelectorAll('canvas').forEach(c=>{ if(vis(c)){
            const r=c.getBoundingClientRect();
            out.canvases.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
        }});
        // toggles: rounded-full 小按钮
        document.querySelectorAll('[class*="rounded-full"]').forEach(e=>{ if(vis(e)){
            const r=e.getBoundingClientRect();
            if(r.width<60 && r.height<40 && r.width>20) out.toggles.push({x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)});
        }});
        return out;
    }""")
    p = os.path.join(DEBUG, f"dump_{tag}.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("URL: " + page.url + "\n\n")
        f.write("== BUTTONS ==\n")
        for b in info["buttons"]:
            f.write(f"  [{b['x']},{b['y']} {b['w']}x{b['h']}] {b['t']!r}\n")
        f.write("\n== INPUTS ==\n")
        for i in info["inputs"]:
            f.write(f"  [{i['x']},{i['y']}] type={i['type']} ph={i['ph']!r}\n")
        f.write("\n== RANGES ==\n" + str(info["ranges"]) + "\n")
        f.write("\n== CANVASES ==\n" + str(info["canvases"]) + "\n")
        f.write("\n== TOGGLES(rounded-full small) ==\n" + str(info["toggles"]) + "\n")
    log(f"dumped -> {p}  ({len(info['buttons'])} buttons, {len(info['canvases'])} canvas)")
    return info


def shot(page, name):
    p = os.path.join(SHOTS, name + ".png")
    try:
        page.screenshot(path=p)
        log("shot ->", p)
    except Exception as e:
        log("shot FAIL", name, e)
    return p
