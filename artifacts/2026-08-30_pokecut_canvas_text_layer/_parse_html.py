from bs4 import BeautifulSoup
from pathlib import Path
import re, json
TASK=Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer")
for f in ['panel_basic_initial.html','panel_adjust_scrolled.html','panel_space_expanded.html']:
    p=TASK/f
    if not p.exists(): continue
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    print('===',f,'===')
    # tabs
    buttons=soup.find_all('button')
    print('buttons', len(buttons))
    texts=[]
    for b in buttons:
        t=' '.join(b.get_text(' ', strip=True).split())
        if t:
            texts.append(t)
    # print unique texts (keep order)
    seen=[]
    for t in texts:
        if t not in seen: seen.append(t)
    print('button texts unique:', seen[:80])
    # inputs
    inputs=soup.find_all('input')
    print('inputs', len(inputs))
    for i in inputs[:60]:
        print('  input', i.get('type'), i.get('class'), 'value', i.get('value'), 'min', i.get('min'), 'max', i.get('max'), 'disabled', i.get('disabled'))
