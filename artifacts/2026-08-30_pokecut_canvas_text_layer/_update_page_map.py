from pathlib import Path
p = Path('page_map/pokecut/infinite_canvas_text_layer_v2.yaml')
s = p.read_text(encoding='utf-8')
add = """
  # ── 补充：两行编辑与色盘/取色控件（sync.md 第 8 节）────────
  text_edit_hidden_textarea:
    selector: "textarea.fixed.h-px.w-px"
    description: 双击文字图层后出现的隐藏文本编辑框，用于输入多行文字
  background_color_palette_btn:
    selector: "button:has(img[alt='picker'][src*='edit_icon_color_picker.png'])"
    description: Background 展开区第一个特殊按钮（色盘），点击弹出调色弹窗
  background_picker_btn:
    selector: "div[class*='border-b']:has(span:text('Background')) button:has(svg.size-[1.25rem])"
    description: Background 展开区取色按钮（位于色盘按钮之后）
  color_modal_hex:
    selector: "input.hexInput"
    description: 调色弹窗内的十六进制色值输入框
  outline_color_palette_btn:
    selector: "button:has(img[alt='picker'][src*='edit_icon_color_picker.png'])"
    description: Outline Color 区第一个特殊按钮（色盘）
  outline_picker_btn:
    selector: "div[class*='border-b']:has(span:text('Outline')) button:has(svg.size-[1.25rem])"
    description: Outline Color 区取色按钮
"""
s = s.replace('\ntabs:\n', '\n' + add + '\ntabs:\n')
p.write_text(s, encoding='utf-8')
print('page_map updated')
