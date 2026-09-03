from pathlib import Path
p = Path('artifacts/runtime/orchestrator.md')
s = p.read_text(encoding='utf-8')
old = '以本地服务器打开报告供用户查看'
new = '启动本地 HTTP 服务器（如 `python -m http.server 8123 --directory reports/allure-report-matrix`），并在浏览器打开 `http://localhost:8123/index.html` 供用户查看（不得直接打开静态 HTML 文件）'
s = s.replace(old, new)
p.write_text(s, encoding='utf-8')
print('orchestrator.md updated')
