# -*- coding: utf-8 -*-
"""精确类名复探：底部 CTA 容器 + 移动端分类卡片。"""
import json
from playwright.sync_api import sync_playwright
BASE="http://10.17.1.66:3001"
def main():
    R={}
    with sync_playwright() as p:
        b=p.chromium.launch(headless=True)
        c=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
        c.add_init_script("window.__norm=(s)=>(s||'').replace(/\\s+/g,' ').trim();")
        pg=c.new_page()
        pg.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        pg.wait_for_timeout(8000)
        R["support_cta"]=pg.evaluate("""() => {
            const els=Array.from(document.querySelectorAll('[class*="support-cta"], [class*="support"]'));
            return els.map(el=>({tag:el.tagName.toLowerCase(), cls:el.className, text:window.__norm(el.textContent).slice(0,120)})).slice(0,8);
        }""")
        print("[SUPPORT CTA]", json.dumps(R["support_cta"], ensure_ascii=False, indent=2))
        b.close()

        m=p.chromium.launch(headless=True)
        mc=m.new_context(viewport={"width":375,"height":812}, locale="en-US")
        mc.add_init_script("window.__norm=(s)=>(s||'').replace(/\\s+/g,' ').trim();")
        mp=mc.new_page()
        mp.goto(f"{BASE}/help", wait_until="domcontentloaded", timeout=120000)
        mp.wait_for_timeout(8000)
        R["mobile_cards"]=mp.evaluate("""() => {
            const els=Array.from(document.querySelectorAll('button')).filter(b=>/Getting Started|Account & Access|Plans, Credits & Billing/.test(window.__norm(b.textContent)) && b.textContent.length < 200);
            return els.map(el=>({tag:el.tagName.toLowerCase(), cls:el.className, text:window.__norm(el.textContent).slice(0,80)})).slice(0,8);
        }""")
        print("[MOBILE CARDS]", json.dumps(R["mobile_cards"], ensure_ascii=False, indent=2))
        m.close()
    json.dump(R, open(r"D:\Test\web-test\artifacts\2026-08-31_pokecut_help_center\explore_classnames.json","w",encoding="utf-8"), ensure_ascii=False, indent=2)
if __name__=="__main__":
    main()
