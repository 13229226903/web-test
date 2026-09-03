# -*- coding: utf-8 -*-
"""Adjust 面板控件点击前后变化（clean v2）。"""
from playwright.sync_api import sync_playwright
from pathlib import Path
import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = Path(r"D:\Test\web-test")
TASK = ROOT / "artifacts" / "2026-08-30_pokecut_canvas_text_layer"
SHOTS = TASK / "shots"; SHOTS.mkdir(exist_ok=True)
OUT = {"steps": []}

def rec(name, before=None, after=None, **kw):
    item = {"name": name}
    if before is not None: item["before"] = before
    if after is not None: item["after"] = after
    item.update(kw)
    OUT["steps"].append(item)
    print(json.dumps(item, ensure_ascii=False)[:1400])

def snap(page, name):
    p = SHOTS / f"{name}.png"; page.screenshot(path=str(p)); return str(p)

def js(page, expr, arg=None):
    return page.evaluate(expr, arg)

def section_info(page, section):
    return js(page, """(section) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0 && r.x>=1080){
          const row=sp.parentElement;
          const content=row.nextElementSibling;
          const btns=[...row.querySelectorAll('button')];
          const small=btns.filter(b=>{const br=b.getBoundingClientRect(); return br.width>0&&br.height>0&&br.width<=16&&br.height<=16;});
          const toggle=btns.filter(b=>{const br=b.getBoundingClientRect(); return br.width>0&&br.height>0&&br.width>=30&&br.width<=50&&br.height<=24;});
          const rr=row.getBoundingClientRect();
          return {
            row: {x:rr.x,y:rr.y,w:rr.width,h:rr.height},
            row_tag: row.tagName,
            content_display: content ? getComputedStyle(content).display : null,
            small: small.length ? (()=>{const b=small[0].getBoundingClientRect(); return {x:b.x,y:b.y,w:b.width,h:b.height};})() : null,
            toggle: toggle.length ? (()=>{const b=toggle[0].getBoundingClientRect(); return {x:b.x,y:b.y,w:b.width,h:b.height,cls:toggle[0].className};})() : null
          };
        }
      }
      return null;
    }""", section)

def click_rect(page, rect):
    if rect: page.mouse.click(rect["x"] + rect["w"]/2, rect["y"] + rect["h"]/2)

def click_row(page, section):
    info = section_info(page, section)
    if info: click_rect(page, info["row"])
    return info

def click_small(page, section):
    info = section_info(page, section)
    if info and info.get("small"): click_rect(page, info["small"])
    return info

def click_toggle(page, section):
    info = section_info(page, section)
    if info and info.get("toggle"): click_rect(page, info["toggle"])
    return info

def active_tab(page):
    return js(page, """() => {
      const out={};
      for(const t of ['Basic','Adjust']){
        const bs=[...document.querySelectorAll('button')].filter(b=>(b.textContent||'').trim()===t);
        for(const b of bs){const r=b.getBoundingClientRect(); if(r.width>100&&r.height>30&&r.y>400&&r.y<500){ out[t]=b.className; break; }}
      }
      return out;
    }""")

def click_tab(page, tab):
    # find visible tab button by text and y
    boxes=[]
    for loc in page.locator("button", has_text=tab).all():
        try:
            r=loc.bounding_box()
            if r and r["y"]>430 and r["y"]<500 and r["x"]>1080:
                boxes.append((r, loc))
        except: pass
    if boxes:
        r,_=boxes[0]; page.mouse.click(r["x"]+r["width"]/2, r["y"]+r["height"]/2); return r
    return None

def set_content_ranges(page, section, values):
    return js(page, """(opts) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===opts.section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0 && r.x>=1080){
          const row=sp.parentElement;
          const content=row.nextElementSibling;
          if(content){
            const sliders=[...content.querySelectorAll('input[type=range]')];
            const set=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set;
            sliders.forEach((s,i)=>{ if(i<opts.values.length){ set.call(s, String(opts.values[i])); s.dispatchEvent(new Event('input',{bubbles:true})); s.dispatchEvent(new Event('change',{bubbles:true})); } });
            return sliders.map(s=>s.value);
          }
        }
      }
      return null;
    }""", {"section":section,"values":values})

def get_content_ranges(page, section):
    return js(page, """(section) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0 && r.x>=1080){
          const row=sp.parentElement;
          const content=row.nextElementSibling;
          if(content){ const sliders=[...content.querySelectorAll('input[type=range]')]; return sliders.map(s=>({value:s.value, min:s.min, max:s.max, disabled:s.disabled})); }
        }
      }
      return null;
    }""", section)

def get_content_buttons(page, section):
    return js(page, """(section) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0 && r.x>=1080){
          const row=sp.parentElement;
          const content=row.nextElementSibling;
          if(content){ const btns=[...content.querySelectorAll('button')]; return btns.map(b=>({cls:b.className, bg:b.style.backgroundColor||null, alt:(b.querySelector('img')||{}).alt||null})); }
        }
      }
      return null;
    }""", section)

def click_content_button_by_bg(page, section, bg):
    return js(page, """(opts) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===opts.section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0 && r.x>=1080){
          const row=sp.parentElement;
          const content=row.nextElementSibling;
          if(content){
            const btns=[...content.querySelectorAll('button')];
            for(const b of btns){
              if(b.style.backgroundColor===opts.bg){
                b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true}));
                const br=b.getBoundingClientRect();
                return {x:Math.round(br.x), y:Math.round(br.y), bg:opts.bg};
              }
            }
          }
        }
      }
      return null;
    }""", {"section":section,"bg":bg})

def click_content_button_index(page, section, index):
    return js(page, """(opts) => {
      const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()===opts.section);
      for(const sp of spans){
        const r=sp.getBoundingClientRect();
        if(r.width>0 && r.x>=1080){
          const row=sp.parentElement;
          const content=row.nextElementSibling;
          if(content){
            const btns=[...content.querySelectorAll('button')];
            if(btns[opts.index]){ const b=btns[opts.index]; b.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); const br=b.getBoundingClientRect(); return {x:Math.round(br.x), y:Math.round(br.y)}; }
          }
        }
      }
      return null;
    }""", {"section":section,"index":index})

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
    page = ctx.new_page()
    page.goto("http://10.17.1.66:3001/create", timeout=120000, wait_until="domcontentloaded")
    page.wait_for_timeout(8000)
    page.evaluate("""() => { document.querySelectorAll('div[class*="fixed"]').forEach(el=>{ const r=el.getBoundingClientRect(); if(r.width>=document.documentElement.clientWidth*0.9 && r.height>=document.documentElement.clientHeight*0.9){ el.remove(); } }); }""")
    page.wait_for_timeout(1000)
    card = page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
    with page.expect_file_chooser(timeout=30000) as fc:
        card.click()
    fc.value.set_files(str(ROOT / "test_images" / "低分辨率.JPG"))
    page.wait_for_timeout(12000)
    page.locator("button[data-tool-id='text']").first.click()
    page.wait_for_timeout(3000)

    snap(page, "70_adjust_panel_before")
    initial_sections = {s:section_info(page,s) for s in ["Space","Reflection","Background","Outline"]}
    rec("initial", active_tab=active_tab(page), sections=initial_sections)

    # Tabs
    before = active_tab(page); click_tab(page, "Basic"); page.wait_for_timeout(1000)
    snap(page, "71_basic_tab_clicked"); rec("click_basic_tab", before=before, after=active_tab(page))
    click_tab(page, "Adjust"); page.wait_for_timeout(1000)
    rec("click_adjust_tab", before=active_tab(page), after=active_tab(page))

    # Space
    before = section_info(page, "Space")
    click_row(page, "Space"); page.wait_for_timeout(1000)
    after = section_info(page, "Space"); snap(page, "72_space_expanded")
    rec("click_space_header", before=before, after=after)
    before_vals = get_content_ranges(page, "Space")
    after_vals = set_content_ranges(page, "Space", [40]); page.wait_for_timeout(1000)
    snap(page, "73_space_width_40")
    rec("set_space_width_40", before=before_vals, after=after_vals)

    # Reflection
    before = section_info(page, "Reflection")
    click_small(page, "Reflection"); page.wait_for_timeout(1000)
    after = section_info(page, "Reflection"); snap(page, "74_reflection_expanded")
    rec("click_reflection_dropdown", before=before, after=after)
    before = section_info(page, "Reflection")
    click_toggle(page, "Reflection"); page.wait_for_timeout(1000)
    after = section_info(page, "Reflection"); snap(page, "75_reflection_toggle_on")
    rec("click_reflection_toggle", before=before, after=after)
    before_vals = get_content_ranges(page, "Reflection")
    after_vals = set_content_ranges(page, "Reflection", [60,30,20,90]); page.wait_for_timeout(1000)
    snap(page, "76_reflection_sliders")
    rec("set_reflection_sliders", before=before_vals, after=after_vals)

    # Background
    before = section_info(page, "Background")
    click_row(page, "Background"); page.wait_for_timeout(1000)
    after = section_info(page, "Background"); snap(page, "77_background_expanded")
    rec("click_background_header", before=before, after=after)
    before_btns = get_content_buttons(page, "Background")
    clicked_no_fill = click_content_button_index(page, "Background", 0); page.wait_for_timeout(1000)
    after_btns = get_content_buttons(page, "Background"); snap(page, "78_background_no_fill")
    rec("click_background_no_fill", before=before_btns[:3] if before_btns else None, after=after_btns[:3] if after_btns else None, clicked=clicked_no_fill)
    clicked_red = click_content_button_by_bg(page, "Background", "rgb(174, 41, 42)"); page.wait_for_timeout(1000)
    after_btns = get_content_buttons(page, "Background"); snap(page, "79_background_red")
    rec("click_background_red", clicked=clicked_red, after=after_btns[:3] if after_btns else None)

    # Outline
    before = section_info(page, "Outline")
    click_small(page, "Outline"); page.wait_for_timeout(1000)
    after = section_info(page, "Outline"); snap(page, "80_outline_expanded")
    rec("click_outline_dropdown", before=before, after=after)
    before = section_info(page, "Outline")
    click_toggle(page, "Outline"); page.wait_for_timeout(1000)
    after = section_info(page, "Outline"); snap(page, "81_outline_toggle_on")
    rec("click_outline_toggle", before=before, after=after)
    # Outline Types (buttons with img) - click type 1
    before_types = get_content_buttons(page, "Outline")
    clicked_type = click_content_button_index(page, "Outline", 1); page.wait_for_timeout(1000)
    after_types = get_content_buttons(page, "Outline"); snap(page, "82_outline_type1")
    rec("click_outline_type1", before=before_types[:5] if before_types else None, after=after_types[:5] if after_types else None, clicked=clicked_type)
    # Outline Color red (button with bg rgb(174,41,42)) - find within content
    clicked_color = click_content_button_by_bg(page, "Outline", "rgb(174, 41, 42)"); page.wait_for_timeout(1000)
    after_colors = get_content_buttons(page, "Outline"); snap(page, "83_outline_color_red")
    rec("click_outline_color_red", clicked=clicked_color, after=after_colors[:5] if after_colors else None)
    # Outline sliders
    before_vals = get_content_ranges(page, "Outline")
    after_vals = set_content_ranges(page, "Outline", [70,20,10,30]); page.wait_for_timeout(1000)
    snap(page, "84_outline_sliders")
    rec("set_outline_sliders", before=before_vals, after=after_vals)

    browser.close()

(TASK / "adjust_panel_interactions.json").write_text(json.dumps(OUT, ensure_ascii=False, indent=2), encoding="utf-8")
print("WROTE", TASK / "adjust_panel_interactions.json")
