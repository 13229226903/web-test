import json,pathlib,re
d=json.loads(pathlib.Path('artifacts/2026-08-26_pokecut_text_enhancer/explore_desktop_interactions.json').read_text(encoding='utf-8'))
for r in d['records']:
 if r['scales']:
  print(r['step'])
  for s in r['scales']:
   m=re.search(r'<div class="w-full h-full rounded[^>]*>',s['itemOuter'])
   print(s['scale'],m.group(0)[-160:] if m else 'NA')
