# -*- coding: utf-8 -*-
"""Dump 首页所有 fixed/absolute 高层遮罩/弹窗，判断是什么拦截了登录。"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from lib import BASE, DEBUG, log
from playwright.sync_api import sync_playwright

with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True)
    c = b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    p = c.new_page()
    p.goto(BASE); p.wait_for_timeout(7000)
    ov = p.evaluate("""() => {
        const out=[];
        document.querySelectorAll('*').forEach(el=>{
            const s=getComputedStyle(el); const r=el.getBoundingClientRect();
            if((s.position==='fixed'||s.position==='absolute') && r.width>200 && r.height>150){
                const z=parseInt(s.zIndex||'0');
                if(z>=20 || s.position==='fixed'){
                    out.push({tag:el.tagName, z:s.zIndex, pos:s.position,
                        x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height),
                        bg:s.backgroundColor, t:(el.innerText||'').replace(/\\n/g,' ').trim().slice(0,80)});
                }
            }
        });
        return out;
    }""")
    log("OVERLAYS (fixed/absolute, big):")
    for o in ov:
        log(f"  <{o['tag']}> z={o['z']} {o['pos']} [{o['x']},{o['y']} {o['w']}x{o['h']}] bg={o['bg']} t={o['t']!r}")
    p.screenshot(path=os.path.join(DEBUG, "home_overlays.png"), full_page=False)
    log("shot home_overlays.png")
    b.close()
