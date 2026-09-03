import json, glob
files = glob.glob('reports/allure-results-matrix/*-result.json')
print('result files', len(files))
for f in files:
    d=json.load(open(f,encoding='utf-8'))
    if 'test_infinite_canvas_text_layer_v2' in d.get('fullName',''):
        labels={l['name']:l['value'] for l in d.get('labels',[])}
        print(d.get('name')[:60], '|', labels.get('epic'), '|', labels.get('feature'))
        break
