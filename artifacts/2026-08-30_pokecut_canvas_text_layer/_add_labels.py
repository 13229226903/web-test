from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
lines = s.splitlines()
out = []
for line in lines:
    out.append(line)
    if 'allure.dynamic.title(' in line:
        indent = line[:len(line)-len(line.lstrip())]
        out.append(f'{indent}allure.dynamic.epic("画布页文字功能")')
        out.append(f'{indent}allure.dynamic.feature("画布页文字功能")')
p.write_text('\n'.join(out), encoding='utf-8')
print('labels inserted')
