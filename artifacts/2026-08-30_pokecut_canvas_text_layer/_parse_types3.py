from bs4 import BeautifulSoup
from pathlib import Path
soup=BeautifulSoup((Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer\panel_outline_expanded2.html")).read_text(encoding='utf-8'),'html.parser')
p=soup.find('p', string=lambda x:x and x.strip()=='Types')
print(str(p.parent)[:2500])
