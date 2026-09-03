from bs4 import BeautifulSoup
from pathlib import Path
import re, json
TASK=Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer")
soup=BeautifulSoup((TASK/'panel_basic_initial.html').read_text(encoding='utf-8'),'html.parser')
# find text spans / labels
print('spans:')
for s in soup.find_all('span')[:100]:
    t=' '.join(s.get_text(' ',strip=True).split())
    if t: print(' ', repr(t))
print('labels:')
for s in soup.find_all('label')[:30]:
    t=' '.join(s.get_text(' ',strip=True).split())
    if t: print(' ', repr(t))
print('paragraphs:')
for s in soup.find_all('p')[:50]:
    t=' '.join(s.get_text(' ',strip=True).split())
    if t: print(' ', repr(t))
