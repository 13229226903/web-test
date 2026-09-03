# -*- coding: utf-8 -*-
"""Probe2: 打开工具，等待/轮询，转储【全宽】可见交互元素 + body 文本片段。"""
import sys, os, time
sys.path.insert(0, os.path.dirname(__file__))
from lib import login, dismiss, log, DEBUG
from playwright.sync_api import sync_playwright

TOOL = sys.argv[1] if len(sys.argv) > 1 else "AI Background"
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 20000
IMG = os.path.join(r"D:\Test\web-test", "test_images", "多人脸.jpg")


def open_tool(page, tool_text):
    dismiss(page)
    card = page.locator(f"div.cursor-pointer:has(p:text-is('{tool_text}'))").first
    card.scroll_into_view_if_needed()
    box = card.bounding_box()
    with page.expect_file_chooser(timeout=20000) as fc:
        page.mouse.click(box["x"]+box["width"]/2, box["y"]+box["height"]/2)
    fc.value.set_files(IMG)


def snap(page):
    return page.evaluate("""() => {
        const vis = el => { const r=el.getBoundingClientRect(); const s=getComputedStyle(el);
            return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'&&r.y>60&&r.y<1060; };
        const rows=[];
        document.querySelectorAll('button,[role=button],img,input,textarea,label').forEach(el=>{
            if(!vis(el)) return; const r=el.getBoundingClientRect();
            const t=(el.innerText||el.value||el.placeholder||'').trim().slice(0,40);
            const bgi=getComputedStyle(el).backgroundImage;
            const hasImg=el.tagName==='IMG'||(bgi&&bgi!=='none');
            rows.push({tag:el.tagName,t,x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),img:hasImg?1:0});
        });
        return {rows, body: document.body.innerText.slice(0,1200)};
    }""")


with sync_playwright() as pw:
    browser, ctx, page = login(pw)
    page.goto("http://10.17.1.66:3001/create"); page.wait_for_timeout(4000); dismiss(page)
    open_tool(page, TOOL)
    # 轮询等待 "Thinking"/"Generating" 消失，最多 WAIT
    t0=time.time(); last=""
    while (time.time()-t0)*1000 < WAIT:
        page.wait_for_timeout(5000); dismiss(page)
        try: bt=page.locator("body").inner_text()
        except: bt=""
        thinking = ("Thinking" in bt) or ("Generating" in bt) or ("%" in bt and "Credits" in bt.split("%")[0][-20:])
        log(f"t+{int(time.time()-t0)}s thinking={'Thinking' in bt or 'Generating' in bt}")
        if "Thinking" not in bt and "Generating" not in bt and (time.time()-t0)>8:
            break
    data = snap(page)
    tag=TOOL.replace(" ","_")
    p=os.path.join(DEBUG, f"probe2_{tag}.txt")
    with open(p,"w",encoding="utf-8") as f:
        f.write("URL: "+page.url+"\n\n== BODY TEXT ==\n"+data["body"]+"\n\n== INTERACTIVE (full width) ==\n")
        for r in sorted(data["rows"], key=lambda x:(x['x'],x['y'])):
            f.write(f"  <{r['tag']}> [{r['x']},{r['y']} {r['w']}x{r['h']}] img={r['img']} t={r['t']!r}\n")
    log("wrote",p,"rows=",len(data["rows"]))
    # 截图存 shots
    page.screenshot(path=os.path.join(r"D:\Test\web-test\artifacts\2026-07-13_pokecut_create_ai_tools\shots", f"probe2_{tag}.png"))
    browser.close()
