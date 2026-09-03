# -*- coding: utf-8 -*-
"""Probe: 打开指定工具，转储右侧面板(x>1240)的完整文本 + 预设网格候选元素。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import login, dismiss, log, DEBUG
from playwright.sync_api import sync_playwright

TOOL = sys.argv[1] if len(sys.argv) > 1 else "AI Background"
WAIT = int(sys.argv[2]) if len(sys.argv) > 2 else 6000
IMG = os.path.join(r"D:\Test\web-test", "test_images", "多人脸.jpg")


def open_tool(page, tool_text):
    dismiss(page)
    sel = f"div.cursor-pointer:has(p:text-is('{tool_text}'))"
    card = page.locator(sel).first
    card.scroll_into_view_if_needed()
    box = card.bounding_box()
    with page.expect_file_chooser(timeout=20000) as fc:
        page.mouse.click(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
    fc.value.set_files(IMG)
    page.wait_for_timeout(WAIT)
    dismiss(page)


def probe(page):
    return page.evaluate("""() => {
        const vis = el => { const r=el.getBoundingClientRect(); const s=getComputedStyle(el);
            return r.width>0&&r.height>0&&s.visibility!=='hidden'&&s.display!=='none'; };
        // 右侧面板容器：收集 x>1240 且可见、直接含文本或图片的元素
        const rows=[];
        document.querySelectorAll('div,button,span,p,img,label').forEach(el=>{
            if(!vis(el)) return;
            const r=el.getBoundingClientRect();
            if(r.x < 1240) return;
            const own = Array.from(el.childNodes).filter(n=>n.nodeType===3).map(n=>n.textContent.trim()).join(' ').trim();
            const bgi = getComputedStyle(el).backgroundImage;
            const hasImg = el.tagName==='IMG' || (bgi && bgi!=='none');
            const cls = (el.className && el.className.toString) ? el.className.toString().slice(0,50) : '';
            if(own || hasImg){
                rows.push({tag:el.tagName, t:own.slice(0,50),
                    x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
                    img:hasImg?1:0, cls});
            }
        });
        // 整个右侧面板 innerText
        let panelText='';
        const cand=document.querySelectorAll('div');
        let best=null,bestA=0;
        cand.forEach(d=>{const r=d.getBoundingClientRect();
            if(r.x>1240 && r.x<1700 && r.width>300 && r.height>300){const a=r.width*r.height; if(a>bestA){bestA=a;best=d;}}});
        if(best) panelText=best.innerText.slice(0,1500);
        return {rows, panelText};
    }""")


with sync_playwright() as pw:
    browser, ctx, page = login(pw)
    page.goto("http://10.17.1.66:3001/create"); page.wait_for_timeout(4000); dismiss(page)
    open_tool(page, TOOL)
    page.wait_for_timeout(2000)
    data = probe(page)
    tag = TOOL.replace(" ", "_")
    p = os.path.join(DEBUG, f"probe_{tag}.txt")
    with open(p, "w", encoding="utf-8") as f:
        f.write("URL: "+page.url+"\n\n== PANEL innerText ==\n"+data["panelText"]+"\n\n== RIGHT-PANEL ELEMENTS (x>1240) ==\n")
        for r in data["rows"]:
            f.write(f"  <{r['tag']}> [{r['x']},{r['y']} {r['w']}x{r['h']}] img={r['img']} t={r['t']!r} cls={r['cls']!r}\n")
    log("wrote", p, "rows=", len(data["rows"]))
    browser.close()
