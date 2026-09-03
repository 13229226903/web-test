# -*- coding: utf-8 -*-
"""Panel (Basic/Adjust) exploration."""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT=Path(r"D:\Test\web-test")
TASK=ROOT/"artifacts"/"2026-08-30_pokecut_canvas_text_layer"
SHOTS=TASK/"shots"; SHOTS.mkdir(exist_ok=True)
OUT={"steps":[]}
def rec(name,**kw):
    item={"name":name,**kw}; OUT["steps"].append(item); print(json.dumps(item,ensure_ascii=False)[:900])
def snap(page,name):
    path=SHOTS/f"{name}.png"; page.screenshot(path=str(path)); return path

def visible_texts(page):
    return page.evaluate("""() => {
      const out=[];
      document.querySelectorAll('button,span,p,label,input,textarea').forEach(el=>{
        const r=el.getBoundingClientRect();
        const s=getComputedStyle(el);
        if(r.width>0&&r.height>0&&r.x>=1090&&r.x<=1560&&r.y>=430&&r.y<=820&&s.display!=='none'&&s.visibility!=='hidden'){
          let t=(el.tagName==='INPUT' ? el.value : (el.textContent||'')).trim().replace(/\\s+/g,' ');
          if(t && t.length<100) out.push({tag:el.tagName,text:t,x:Math.round(r.x),y:Math.round(r.y)});
        }
      });
      // unique by text+pos
      const seen=new Set(); const res=[];
      for(const o of out){const k=o.tag+'|'+o.text+'|'+o.x+'|'+o.y; if(!seen.has(k)){seen.add(k);res.push(o);} }
      return res;
    }""")

def js_click_button(page, text, ymin=430,ymax=820, xmin=1090,xmax=1560, tag='button'):
    return page.evaluate("""(opts)=>{
      const els=[...document.querySelectorAll(opts.tag)];
      for(const el of els){
        const r=el.getBoundingClientRect();
        const s=getComputedStyle(el);
        const t=(el.textContent||'').trim().replace(/\\s+/g,' ');
        if(r.width>0&&r.height>0&&r.x>=opts.xmin&&r.x<=opts.xmax&&r.y>=opts.ymin&&r.y<=opts.ymax&&s.display!=='none'&&s.visibility!=='hidden'&&t===opts.text){
          el.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
          return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)};
        }
      }
      return null;
    }""", {"text":text,"ymin":ymin,"ymax":ymax,"xmin":xmin,"xmax":xmax,"tag":tag})

def js_click_dropdown(page, section):
    return page.evaluate("""(section)=>{
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0&&r.x>=1090&&r.x<=1560&&r.y>=430&&r.y<=820){
          let header=sp.parentElement;
          for(let i=0;i<4;i++){ if(!header) break; header=header.parentElement; }
          if(header){
            const btns=[...header.querySelectorAll('button')];
            // dropdown arrow is small button (size ~12), toggle is wider (~42)
            const small=btns.filter(b=>{const br=b.getBoundingClientRect(); return br.width>0&&br.height>0&&br.width<=16&&br.height<=16;});
            const target=small.length?small[small.length-1]:null;
            if(target){target.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return {x:Math.round(target.getBoundingClientRect().x),y:Math.round(target.getBoundingClientRect().y)};}
            if(btns.length){btns[btns.length-1].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return 'last';}
          }
        }
      }
      return null;
    }""", section)

def js_click_toggle(page, section):
    return page.evaluate("""(section)=>{
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0&&r.x>=1090&&r.x<=1560&&r.y>=430&&r.y<=820){
          let header=sp.parentElement;
          for(let i=0;i<4;i++){ if(!header) break; header=header.parentElement; }
          if(header){
            const btns=[...header.querySelectorAll('button')];
            const toggles=btns.filter(b=>{const br=b.getBoundingClientRect(); return br.width>0&&br.height>0&&br.width>=30&&br.width<=50&&br.height<=24;});
            if(toggles.length){const t=toggles[0]; t.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return {x:Math.round(t.getBoundingClientRect().x),y:Math.round(t.getBoundingClientRect().y)};}
          }
        }
      }
      return null;
    }""", section)

def panel_html(page):
    return page.evaluate("""() => { const bs=[...document.querySelectorAll('button')].filter(b=>b.textContent.trim()==='Basic'); for(const b of bs){let el=b; for(let i=0;i<6;i++){ if(!el.parentElement)break; el=el.parentElement; if(el.textContent&&el.textContent.includes('Space'))return el.outerHTML;} } return ''; }""")

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    ctx=browser.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page=ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1000)
    card=page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc:
        card.click()
    fc.value.set_files(str(ROOT/"test_images"/"低分辨率.JPG"))
    page.wait_for_timeout(12000)
    page.locator("button[data-tool-id='text']").first.click()
    page.wait_for_timeout(3000)
    snap(page,"50_panel_adjust_default")
    rec("adjust_default", visible=visible_texts(page))
    # Basic tab
    rec("click_basic_tab", result=js_click_button(page,'Basic',ymin=430,ymax=500))
    page.wait_for_timeout(1500)
    snap(page,"51_panel_basic")
    rec("basic_default", visible=visible_texts(page))
    (TASK/'panel_basic_visible.html').write_text(panel_html(page),encoding='utf-8')
    # Font dropdown
    rec("click_font", result=js_click_button(page,'Font'))
    page.wait_for_timeout(1500)
    snap(page,"52_basic_font_open")
    rec("font_open", visible=visible_texts(page))
    (TASK/'panel_font_open.html').write_text(panel_html(page),encoding='utf-8')
    # close font by clicking elsewhere (blank canvas)
    page.mouse.click(900,300); page.wait_for_timeout(1000)
    # Need reselect text layer and panel after blank (deselect). Instead click text layer? We'll re-add text.
    page.locator("button[data-tool-id='text']").first.click(); page.wait_for_timeout(1500)
    js_click_button(page,'Basic',ymin=430,ymax=500); page.wait_for_timeout(800)
    # Fill color
    rec("click_fill", result=js_click_button(page,'Fill'))
    page.wait_for_timeout(1500)
    snap(page,"53_basic_fill_open")
    rec("fill_open", visible=visible_texts(page))
    (TASK/'panel_fill_open.html').write_text(panel_html(page),encoding='utf-8')
    # Switch back to Adjust tab
    js_click_button(page,'Adjust',ymin=430,ymax=500); page.wait_for_timeout(1500)
    # Explore sections
    sections=['Space','Reflection','Background','Outline']
    for sec in sections:
        if sec in ('Space','Background'):
            r=js_click_button(page,sec,ymin=480,ymax=820)
        else:
            r=js_click_dropdown(page,sec)
        page.wait_for_timeout(1500)
        snap(page,f"54_{sec.lower()}_expand")
        rec(f"expand_{sec.lower()}", result=r, visible=visible_texts(page))
        (TASK/f'panel_{sec.lower()}_expanded.html').write_text(panel_html(page),encoding='utf-8')
        if sec=='Space':
            # adjust Width slider via native setter to 40
            val=page.evaluate("""() => { const p=document.querySelector('.panel-scroll-y'); const s=p?p.querySelector('input.space-slider'):null; if(!s)return null; const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set; set.call(s,40); s.dispatchEvent(new Event('input',{bubbles:true})); s.dispatchEvent(new Event('change',{bubbles:true})); return s.value; }""")
            page.wait_for_timeout(1000)
            snap(page,"55_space_width_adjusted")
            rec("space_width_adjusted", value=val, visible=visible_texts(page))
        if sec in ('Reflection','Outline'):
            # click toggle
            rt=js_click_toggle(page,sec); page.wait_for_timeout(1500)
            snap(page,f"55_{sec.lower()}_toggle")
            rec(f"toggle_{sec.lower()}", result=rt, visible=visible_texts(page))
    # final panel state
    page.evaluate("""() => { const p=document.querySelector('.panel-scroll-y'); if(p) p.scrollTop=p.scrollHeight; }""")
    page.wait_for_timeout(1000)
    snap(page,"56_panel_final_adjust")
    rec("final_adjust", visible=visible_texts(page))
    browser.close()
(TASK/"explore_panel.json").write_text(json.dumps(OUT,ensure_ascii=False,indent=2),encoding="utf-8")
print("WROTE", TASK/"explore_panel.json")
