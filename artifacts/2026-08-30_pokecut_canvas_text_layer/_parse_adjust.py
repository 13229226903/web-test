from bs4 import BeautifulSoup
from pathlib import Path
soup=BeautifulSoup((Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer\panel_adjust_scrolled.html")).read_text(encoding='utf-8'),'html.parser')
# find span texts for sections
for sec in ['Space','Reflection','Background','Outline']:
    s=soup.find('span', string=lambda x: x and x.strip()==sec)
    print('=====',sec,'=====')
    if s:
        # climb to section/header parent
        el=s.parent
        for _ in range(4):
            if el is None: break
            if el.name=='div' and el.get('class') and 'border-b' in ' '.join(el.get('class')):
                print(str(el)[:1200]); break
            el=el.parent
    else:
        print('span not found')
    print()
