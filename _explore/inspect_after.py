import json,pathlib
p=pathlib.Path('artifacts/2026-08-26_pokecut_text_enhancer/explore_desktop_after_upload.json')
d=json.loads(p.read_text(encoding='utf-8'))
for x in d['interactive']:
 if x['rect']['y'] < 800:
  print(f"{x['tag']} | {x['text'].replace(chr(10),' / ')[:250]} | {x['attrs']} | {x['rect']}")
