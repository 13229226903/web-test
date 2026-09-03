# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json
URL="http://10.17.1.66:3001/create"
with sync_playwright() as p:
    b=p.chromium.launch(headless=True)
    ctx=b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto(URL, timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    # remove pricing overlay
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ if(el.offsetHeight>0 && el.offsetHeight<document.body.scrollHeight){ const s=getComputedStyle(el); if((s.position==='fixed'||s.position==='absolute') && (s.backgroundColor!=='rgba(0, 0, 0, 0)' && s.backgroundColor!=='transparent')){ /* only remove full-screen translucent overlays */ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } } } }); }""")
    page.wait_for_timeout(2000)
    print("URL", page.url)
    print("TITLE", page.title())
    body=page.locator("body").inner_text()
    print("has Trending Tools", "Trending Tools" in body)
    # locate first button
    loc=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    print("start loc count", loc.count())
    if loc.count():
        print("start visible", loc.is_visible(), loc.inner_text())
        box=loc.bounding_box(); print("box", box)
    # print first 15 card texts containing p
    cards=page.locator("div.cursor-pointer")
    print("cards", cards.count())
    for i in range(min(cards.count(),20)):
        c=cards.nth(i)
        try:
            txt=c.inner_text().strip().replace("\n"," | ")
            print(i, txt[:80], c.is_visible())
        except Exception as e:
            print(i, "ERR", e)
    b.close()
