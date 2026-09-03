from bs4 import BeautifulSoup
from pathlib import Path
soup=BeautifulSoup((Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer\panel_outline_expanded2.html")).read_text(encoding='utf-8'),'html.parser')
for tag in ['p','span','label']:
    for el in soup.find_all(tag):
        t=' '.join(el.get_text(' ',strip=True).split())
        if t in ('Types','Color','Size','Distance','Blur','Smooth'):
            print(tag, repr(t), 'found')
# search text
import re
text=soup.get_text(' ', strip=True)
print('contains Types', 'Types' in text)
print(text[:1500])
