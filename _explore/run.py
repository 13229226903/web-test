# -*- coding: utf-8 -*-
"""深度探索生成器：对指定工具执行 配置面板→提交→轮询等待→截图。
每次进程只跑一个工具（可传 mode 限定）。用法:
  python run.py removebg [General|Head&Face|Text]
  python run.py aibg
  python run.py expand [Square|Customize]
  python run.py erase [Manual|Smart]
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from lib import login, dismiss, log, SHOTS
from playwright.sync_api import sync_playwright

IMG = os.path.join(r"D:\Test\web-test", "test_images", "多人脸.jpg")
GEN_TIMEOUT = 480   # 单次生成上限 8 分钟


def open_tool(page, tool_text):
    dismiss(page)
    card = page.locator(f"div.cursor-pointer:has(p:text-is('{tool_text}'))").first
    card.scroll_into_view_if_needed()
    box = card.bounding_box()
    with page.expect_file_chooser(timeout=20000) as fc:
        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
    fc.value.set_files(IMG)
    page.wait_for_timeout(9000)
    dismiss(page)
    log("landed", page.url)


def credits(page):
    try:
        import re
        m = re.search(r"Credits:\s*(\d+)", page.locator("body").inner_text())
        return int(m.group(1)) if m else None
    except Exception:
        return None


def is_generating(page):
    try:
        overlay = page.evaluate("""() => {
            const els=[...document.querySelectorAll('.loading-overlay')];
            return els.some(e=>{const r=e.getBoundingClientRect();const s=getComputedStyle(e);
                return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden';});
        }""")
        bt = page.locator("body").inner_text()
        return overlay or ("Thinking" in bt) or ("Generating" in bt)
    except Exception:
        return False


def click_btn(page, name, exact=True, prefer="button_wide"):
    """找 innerText 匹配的可见元素 → 选最佳候选 → 坐标点击 + dispatchEvent。
    prefer=button_wide: 优先 <button> 且宽度最大（CTA 提交按钮特征）。"""
    cands = page.evaluate("""({name, exact}) => {
        const vis = el => { const r=el.getBoundingClientRect(); const s=getComputedStyle(el);
            return r.width>0&&r.height>0&&s.display!=='none'&&s.visibility!=='hidden'&&r.y>60; };
        const out=[];
        for (const el of document.querySelectorAll('button,[role=button],div,span')){
            if(!vis(el)) continue;
            const t=(el.innerText||'').trim();
            if(exact ? t===name : t.includes(name)){
                const r=el.getBoundingClientRect();
                out.push({tag:el.tagName,x:r.x,y:r.y,w:r.width,h:r.height});
            }
        }
        return out;
    }""", {"name": name, "exact": exact})
    if not cands:
        log(f"click FAIL '{name}': not found")
        return False
    log(f"  candidates for '{name}':", [f"{c['tag']}@{int(c['x'])},{int(c['y'])} {int(c['w'])}x{int(c['h'])}" for c in cands])
    btns = [c for c in cands if c["tag"] == "BUTTON"]
    pool = btns if btns else cands
    best = max(pool, key=lambda c: c["w"] * c["h"])   # 面积最大者 = 真正的 CTA
    cx, cy = best["x"]+best["w"]/2, best["y"]+best["h"]/2
    page.mouse.click(cx, cy)
    log(f"clicked '{name}' [{best['tag']}] @({int(cx)},{int(cy)}) {int(best['w'])}x{int(best['h'])}")
    return True


def wait_started(page, timeout=25):
    t0=time.time()
    while time.time()-t0 < timeout:
        if is_generating(page):
            log(f"generation STARTED (t+{int(time.time()-t0)}s)")
            return True
        page.wait_for_timeout(2000)
    log("WARN: no generating marker within", timeout, "s (maybe instant)")
    return False


def wait_done(page, tag, timeout=GEN_TIMEOUT):
    t0=time.time(); stable=0
    while time.time()-t0 < timeout:
        page.wait_for_timeout(12000); dismiss(page)
        gen = is_generating(page)
        el = int(time.time()-t0)
        log(f"  poll t+{el}s generating={gen} credits={credits(page)}")
        if not gen:
            stable += 1
            if stable >= 2 and el > 15:   # 连续 2 次非生成态且过了最小时间
                log(f"generation DONE at t+{el}s")
                return True
        else:
            stable = 0
    log(f"generation TIMEOUT after {timeout}s")
    return False


def shot(page, name):
    p=os.path.join(SHOTS, name+".png")
    dismiss(page)
    page.screenshot(path=p)
    log("SHOT ->", p)
    return p


def progress(event):
    import subprocess
    line=f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] page-map-sync {event}"
    with open(r"D:\Test\web-test\artifacts\2026-07-13_pokecut_create_ai_tools\progress.log","a",encoding="utf-8") as f:
        f.write(line+"\n")


# ─────────────── 各工具流程 ───────────────

def run_removebg(ctx, mode):
    modes = [mode] if mode else ["General", "Head&Face", "Text"]
    for m in modes:
        page = ctx.new_page()
        page.goto("http://10.17.1.66:3001/create"); page.wait_for_timeout(4000); dismiss(page)
        open_tool(page, "Remove Background")
        c0=credits(page); log(f"[{m}] credits before", c0)
        click_btn(page, m, exact=True); page.wait_for_timeout(1500)
        progress(f"step:submitted Remove Background/{m}")
        click_btn(page, "Remove Background", exact=True)
        wait_started(page)
        ok = wait_done(page, f"RemoveBackground_{m}")
        shot(page, f"RemoveBackground_{m}")
        log(f"[{m}] credits after", credits(page), "(before", c0, ")")
        progress(f"step:{'generated' if ok else 'timeout'} Remove Background/{m}")
        page.close()
    return True


def run_aibg(ctx, mode):
    page = ctx.new_page()
    page.goto("http://10.17.1.66:3001/create"); page.wait_for_timeout(4000); dismiss(page)
    open_tool(page, "AI Background")
    c0=credits(page); log("credits before", c0)
    # AI Background 进入即自动生成默认背景 → 先等默认完成并截图
    wait_started(page, timeout=15)
    wait_done(page, "AIBackground_default")
    shot(page, "AIBackground_default")
    progress("step:generated AI Background/default")
    # 选一个预设 (第一个场景缩略图 93x93 @ ~1268,547) 触发再生成
    try:
        page.mouse.click(1268+46, 547+46)
        log("clicked preset thumbnail @(1268,547)")
        progress("step:submitted AI Background/preset")
        wait_started(page, timeout=15)
        ok = wait_done(page, "AIBackground_preset")
        shot(page, "AIBackground_preset")
        progress(f"step:{'generated' if ok else 'timeout'} AI Background/preset")
    except Exception as e:
        log("preset click FAIL", e); ok=False
    log("credits after", credits(page), "(before", c0, ")")
    page.close(); return True


def run_expand(ctx, mode):
    page = ctx.new_page()
    page.goto("http://10.17.1.66:3001/create"); page.wait_for_timeout(4000); dismiss(page)
    open_tool(page, "AI Expand")
    c0=credits(page); log("credits before", c0)
    # 选预设比例 (点击 body 文本 Square)
    if mode in (None, "Square"):
        try:
            page.get_by_text("Square", exact=True).first.click(timeout=5000)
            log("selected preset Square")
        except Exception as e:
            log("Square select FAIL", e)
        progress("step:submitted AI Expand/Square")
        click_btn(page, "AI Extend", exact=True)
        wait_started(page)
        ok = wait_done(page, "AIExpand_Square")
        shot(page, "AIExpand_Square")
        progress(f"step:{'generated' if ok else 'timeout'} AI Expand/Square")
    log("credits after", credits(page), "(before", c0, ")")
    page.close(); return True


def run_erase(ctx, mode):
    page = ctx.new_page()
    page.goto("http://10.17.1.66:3001/create"); page.wait_for_timeout(4000); dismiss(page)
    open_tool(page, "AI Erase")
    c0=credits(page); log("credits before", c0)
    if mode in (None, "Manual"):
        click_btn(page, "Manual Mode", exact=True); page.wait_for_timeout(1000)
        # 在画布 (687,307 546x546) 上按住拖动画一条遮罩
        cx, cy = 687, 307
        page.mouse.move(cx+180, cy+250)
        page.mouse.down()
        for dx in range(0, 200, 20):
            page.mouse.move(cx+180+dx, cy+250+ (dx%40), steps=2)
        page.mouse.up()
        log("brushed mask on canvas")
        progress("step:submitted AI Erase/Manual")
        click_btn(page, "Remove", exact=True)
        wait_started(page)
        ok = wait_done(page, "AIErase_Manual")
        shot(page, "AIErase_Manual")
        progress(f"step:{'generated' if ok else 'timeout'} AI Erase/Manual")
    if mode in (None, "Smart"):
        click_btn(page, "Smart Auto Mode", exact=True); page.wait_for_timeout(1500)
        shot(page, "AIErase_Smart_panel")
        progress("step:submitted AI Erase/Smart")
        click_btn(page, "Remove", exact=True)
        wait_started(page)
        ok = wait_done(page, "AIErase_Smart")
        shot(page, "AIErase_Smart")
        progress(f"step:{'generated' if ok else 'timeout'} AI Erase/Smart")
    log("credits after", credits(page), "(before", c0, ")")
    page.close(); return True


DISPATCH = {"removebg": run_removebg, "aibg": run_aibg, "expand": run_expand, "erase": run_erase}


def run_all(ctx, mode):
    """单次登录跑完剩余生成：RemoveBG(Head&Face,Text) + AIBg + Expand + Erase。"""
    for m in ["Head&Face", "Text"]:
        try: run_removebg(ctx, m)
        except Exception as e: log("removebg", m, "ERR", repr(e))
    for fn, nm in [(run_aibg, "aibg"), (run_expand, "expand"), (run_erase, "erase")]:
        try: fn(ctx, None)
        except Exception as e: log(nm, "ERR", repr(e))
    return True


DISPATCH["all"] = run_all

if __name__ == "__main__":
    tool = sys.argv[1]
    mode = sys.argv[2] if len(sys.argv) > 2 else None
    with sync_playwright() as pw:
        browser, ctx, page = login(pw)
        progress(f"step:exploring {tool} mode={mode}")
        DISPATCH[tool](ctx, mode)
        browser.close()
        log("ALL DONE", tool, mode)
