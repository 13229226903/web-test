from PIL import Image
from pathlib import Path
p=Path('artifacts/2026-08-30_pokecut_canvas_text_layer/_dbg_pal.png')
if not p.exists(): print('no file')
else:
    img=Image.open(p).convert('RGB')
    found=[]
    for y in range(307, 853, 5):
        for x in range(778, 1142, 5):
            r,g,b=img.getpixel((x,y))
            if not (max(r,g,b)>245 or max(r,g,b)<20):
                if abs(r-g)>30 or abs(g-b)>30 or abs(r-b)>30:
                    found.append((x,y,(r,g,b)))
    print('colored pixels', len(found), found[:10])
