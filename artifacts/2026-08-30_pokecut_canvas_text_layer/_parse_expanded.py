from bs4 import BeautifulSoup
from pathlib import Path
TASK=Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer")
for sec in ['background','outline','reflection','space']:
    p=TASK/f'panel_{sec}_expanded2.html'
    if not p.exists(): p=TASK/f'panel_{sec}_expanded.html'
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    print('=====',sec,'size',p.stat().st_size,'=====')
    # find section label and its border-b parent
    label={'background':'Background','outline':'Outline','reflection':'Reflection','space':'Space'}[sec]
    sp=soup.find('span', string=lambda x:x and x.strip()==label)
    if not sp:
        print('no span'); continue
    el=sp
    parent=None
    for _ in range(4):
        if el is None: break
        if el.name=='div' and el.get('class') and 'border-b' in ' '.join(el.get('class')):
            parent=el; break
        el=el.parent
    if parent is None:
        print('no parent'); continue
    # print text of visible content
    texts=[]
    for t in parent.find_all(['span','label','p','button']):
        txt=' '.join(t.get_text(' ',strip=True).split())
        if txt: texts.append(txt)
    # unique
    seen=[]
    for t in texts:
        if t not in seen: seen.append(t)
    print('texts:', seen[:40])
    # inputs
    for inp in parent.find_all('input'):
        print(' input', inp.get('type'), inp.get('class'), 'value', inp.get('value'), 'min', inp.get('min'), 'max', inp.get('max'), 'disabled', inp.get('disabled'))
    # toggle/color button count
    btns=parent.find_all('button')
    color_btns=[b for b in btns if b.get('style') and 'background-color' in b.get('style','')]
    print('buttons',len(btns),'color_buttons',len(color_btns))
    if color_btns:
        print('colors', [b.get('style') for b in color_btns[:12]])
