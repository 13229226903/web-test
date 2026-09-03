from bs4 import BeautifulSoup
from pathlib import Path
soup=BeautifulSoup((Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer\panel_fill_open.html")).read_text(encoding='utf-8'),'html.parser')
import re
# count elements with style background-color
els=[e for e in soup.find_all(True) if e.get('style') and 'background-color' in e.get('style','')]
print('elements with bg-color style', len(els))
for e in els[:20]: print(e.name, e.get('style'))
# font list items maybe have style font-family
ff=[e for e in soup.find_all(True) if e.get('style') and 'font-family' in e.get('style','')]
print('font-family els', len(ff))
for e in ff[:30]: print(e.name, ' '.join(e.get_text(' ',strip=True).split()), e.get('style')[:120])
