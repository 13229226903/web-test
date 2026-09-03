from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
old = '    target_info, target_dist = most_distinct_pixel(str(outline_palette_path), (255, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))'
new_bg = '    target_info, target_dist = most_distinct_pixel(str(palette_path), (0, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))'
# Replace only first occurrence
s = s.replace(old, new_bg, 1)
p.write_text(s, encoding='utf-8')
print('first occurrence fixed to palette_path/blue')
