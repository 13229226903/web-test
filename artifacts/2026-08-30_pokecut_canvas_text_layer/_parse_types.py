from bs4 import BeautifulSoup
from pathlib import Path
soup=BeautifulSoup((Path(r"D:\Test\web-test\artifacts\2026-08-30_pokecut_canvas_text_layer\panel_outline_expanded2.html")).read_text(encoding='utf-8'),'html.parser')
# find span Types
sp=soup.find('span', string=lambda x:x and x.strip()=='Types')
print('Types span found', sp is not None)
if sp:
    parent=sp.parent
    for _ in range(5):
        if parent is None: break
        print('LEVEL', parent.name, 'class', ' '.join(parent.get('class',[]))[:100])
        print(str(parent)[:2000])
        print('---')
        parent=parent.parent
