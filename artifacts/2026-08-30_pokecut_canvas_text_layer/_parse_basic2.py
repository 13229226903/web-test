from bs4 import BeautifulSoup
from pathlib import Path
soup=BeautifulSoup((Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer\panel_basic_initial.html")).read_text(encoding='utf-8'),'html.parser')
for p in soup.find_all('p'):
    t=' '.join(p.get_text(' ',strip=True).split())
    if t in ('Alignment','Font','Fill'):
        parent=p.parent
        print('=====',t,'=====')
        print(str(parent)[:1500])
        print()
