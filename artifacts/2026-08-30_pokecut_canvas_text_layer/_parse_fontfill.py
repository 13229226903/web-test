from bs4 import BeautifulSoup
from pathlib import Path
TASK=Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer")
for f in ['panel_font_open.html','panel_fill_open.html','panel_basic_initial.html']:
    p=TASK/f
    soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
    print('=====',f,'size',p.stat().st_size,'=====')
    # find all text nodes around fonts
    texts=[]
    for t in soup.find_all(['span','p','button','label']):
        txt=' '.join(t.get_text(' ',strip=True).split())
        if txt and txt not in texts:
            texts.append(txt)
    print('unique texts:', texts[:60])
    # look for font-related buttons with class containing font
    font_btns=soup.find_all('button')
    # count color buttons
    color=[b for b in font_btns if b.get('style') and 'background-color' in b.get('style','')]
    print('buttons',len(font_btns),'color_buttons',len(color))
    if color: print('colors', [b.get('style') for b in color[:10]])
    # find font list items: likely text spans with font-family style
    for s in soup.find_all(['span','button','div']):
        st=s.get('style','')
        if 'font-family' in st.lower() or 'font-family' in ' '.join(s.get('class',[])).lower():
            print('FONT ITEM', ' '.join(s.get_text(' ',strip=True).split()), st[:100])
            if len([x for x in locals().get('cnt',[0]) if x])>10: pass
