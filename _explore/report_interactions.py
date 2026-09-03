import json,pathlib
p=pathlib.Path('artifacts/2026-08-26_pokecut_text_enhancer/explore_desktop_interactions.json')
d=json.loads(p.read_text(encoding='utf-8'))
for r in d['records']:
 print('\n',r['step'])
 print('effects',[(x['effect'],x['pressed'],x['disabled']) for x in r['effects']])
 print('scalebox',[(x['scale'],x['boxVisible'],x['boxHeight']) for x in r['scales']])
 print('scale selected',[(x['scale'],'selected-border-display-not-none' if 'display: none' not in x['itemOuter'].split('border-[#3338EE]')[1][:300] else False) for x in r['scales']])
 print('main class',r['main'].get('className') if r['main'] else None)
 print('main state/cost/text',r['main'].get('state'),r['main'].get('cost'),repr(r['main'].get('text')) if r['main'] else None)
 print('panel',repr(r['panelText']))
for t in d['tooltips']:
 lines=[x.strip() for x in t['bodyText'].splitlines() if x.strip()]
 # collect tooltip phrases
 for phrase in ['Enhance blurry text and improve readability.','Remove glare from reflective surfaces.','Reduce moire patterns in screens or printed images.','Turn a photographed document into a clean scanned page.']:
  if phrase in lines: print(t['effect'],'=>',phrase)
