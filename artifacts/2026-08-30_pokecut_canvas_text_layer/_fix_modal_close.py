from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
# Background: replace Escape close with toggle palette button close
old_bg = '''    assert page.locator("input.hexInput").input_value() == "#0000ff"
    page.keyboard.press("Escape")
    page.wait_for_timeout(1000)'''
new_bg = '''    assert page.locator("input.hexInput").input_value() == "#0000ff"
    # 再次点击色盘按钮关闭调色弹窗（Escape 在 Enter 后无法关闭）
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)'''
s = s.replace(old_bg, new_bg)
# Outline: replace Escape close
old_ol = '''    assert page.locator("input.hexInput").input_value() == "#ff00ff"
    page.keyboard.press("Escape")
    page.wait_for_timeout(800)'''
new_ol = '''    assert page.locator("input.hexInput").input_value() == "#ff00ff"
    # 再次点击色盘按钮关闭调色弹窗（Escape 在 Enter 后无法关闭）
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(800)'''
s = s.replace(old_ol, new_ol)
p.write_text(s, encoding='utf-8')
print('palette modal close fixed')
