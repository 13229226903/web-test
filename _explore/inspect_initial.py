import json, pathlib
d=json.loads(pathlib.Path('artifacts/2026-08-26_pokecut_text_enhancer/explore_desktop_initial.json').read_text(encoding='utf-8'))
print(d['bodyText'][:1500])
print('\nFILE INPUTS', json.dumps(d['fileInputs'], ensure_ascii=False))
print('\nINTERACTIVE TOP')
for x in d['interactive'][:100]:
    text=x['text'][:120].replace('\n',' / ')
    print(f"{x['tag']} | {text} | {x['attrs']} | {x['rect']}")
