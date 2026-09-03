import json, glob
files = glob.glob('reports/allure-results/*-result.json')
print('result files', len(files))
for f in files[:6]:
    d = json.load(open(f, encoding='utf-8'))
    print('---', d.get('name'), '|', d.get('fullName'))
    print('labels', [ (l.get('name'), l.get('value')) for l in d.get('labels', []) if l.get('name') in ('epic','feature','layer','case_id','parentSuite','suite')])
