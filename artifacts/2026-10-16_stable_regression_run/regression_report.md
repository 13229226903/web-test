【回归测试报告】2026-10-19 14:33
环境: http://10.17.1.66:3102/

✅ 人像检测三入口页                       14/14 · 6m04s
⚠️ AI Image Text Enhancer                 15/18 · 13m05s  (3 skipped)
✅ 画布页文字功能                         6/6 · 4m56s
✅ 移动端首页（Mobile Home v3）           38/38 · 7m42s
✅ 帮助中心                               11/11 · 3m08s
✅ 检测类 UI（L6）                        2/2 · 1m53s
✅ PC 首页（Home v6）                     17/17 · 5m51s
✅ PC 批量编辑页（Batch v1）              16/16 · 4m57s
✅ 旧画布 Insert 面板                     24/24 · 10m08s
✅ 旧画布文字功能                         13/13 · 6m33s
✅ 旧画布贴纸面板                         9/9 · 3m23s
❌ PC 无限画布 Enhance 2K/4K/8K           0/6 · 3m21s
   └ 全部 6 条 — /create 入口卡漂移：Start from a Photo → Start with Photos；HD Photo Converter → Photo Enhancer
❌ SEO 主上传交互（桌面 24 页）           19/24 · 25m12s
   └ L2-002 — 上传后画布蓝色占比 ratio=0.000，期望 >=35%
   └ L2-005 — 跳转 /tools/cv-photo-editor，期望 /tools/id-photo-edit?pid=
   └ L2-014 — 跳转 /tools/phone-wallpaper-maker，期望 /create/edit?pid=
   └ L2-016 — 画布缺少文本 Brightness
   └ L2-019 — 画布缺少文本 AI Background
✅ SEO 主上传交互（移动端 24 页）         23/24 · 4m20s  (1 xfailed)
❌ Create / Chat to Edit / Auto           9/11 · 14m31s
   └ L6-004 — photoenhance_oldphoto 输出画布 2400x3200 未出现
   └ L6-006 — aireplace_bikini_1 输出画布 1200x1600 未出现
⚠️ 画布统计埋点（PC+移动 40 条）         33/40 · 1h01m33s  (2 skipped, 4 xfailed)
   └ M-CORE-05 — 移动端「画布页-AI图片增强」sendGaEvent 期望 1，实际 0（漏报）
✅ 旧画布 AI Tools（19 工具 6 用例）      6/6 · 35m23s  [修复后复跑]
   └ 原 6 error 根因：脚本从 YAML 读取 base_url（http://10.17.1.66:3001），忽略 --base-url。
     已修为 fixture 优先使用 --base-url、YAML 仅作默认值，tests/ 与 archive/ 副本同步更新。

合计: 249 通过 / 14 失败 / 5 跳过 / 5 xfailed / 6 error · 总耗时约 3h03m
状态: ❌ 有失败（14 failed + 6 error）

Allure 报告: http://localhost:8123/index.html
