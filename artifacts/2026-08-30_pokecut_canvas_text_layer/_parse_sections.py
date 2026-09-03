from bs4 import BeautifulSoup
from pathlib import Path
TASK=Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer")
for sec in ['background','outline','reflection','space']:
    p=TASK/f'panel_{sec}_expanded.html'
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    # find section header
    for label in ['Background','Outline','Reflection','Space']:
        sp=soup.find('span', string=lambda x:x and x.strip()==label)
        if not sp: continue
        el=sp
        for _ in range(3):
            if el is None: break
            if el.name=='div' and el.get('class') and 'border-b' in ' '.join(el.get('class')):
                # find content div(s)
                content_divs=[d for d in el.find_all('div', recursive=False) if 'style' in (d.attrs or {}) and d.get('style','').startswith('display: none')]
                content_visible=[d for d in el.find_all('div', recursive=False) if d.get('style') and 'display: none' not in d.get('style')]
                print(sec, label, 'header found; direct child divs:')
                for d in el.find_all('div', recursive=False):
                    style=d.get('style','')
                    cls=' '.join(d.get('class',[]))
                    print('   ', cls[:60], 'style=', style[:30])
                break
            el=el.parent
        break
