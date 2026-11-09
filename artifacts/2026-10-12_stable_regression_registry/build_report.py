"""由 regression/summary.json + Allure 原始结果生成 report.md（稳定回归报告）。

失败清单以 Allure 原始结果为权威来源（首轮超时的 canvas_stats 也被覆盖）。
"""
import json
import re
import time
from pathlib import Path

TASK_DIR = Path(__file__).resolve().parent
ROOT = TASK_DIR.parents[1]
TASK = TASK_DIR.name
summary = json.loads((TASK_DIR / "regression" / "summary.json").read_text(encoding="utf-8"))
rows = summary["rows"]
agg = summary["aggregate_counts"]

# 模块脚本名 -> [(用例名, 原因)]
by_module = {}
res_dir = ROOT / "reports" / "allure-results-regression"
for f in res_dir.glob("*-result.json"):
    try:
        j = json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        continue
    if j.get("status") not in ("failed", "broken"):
        continue
    full = j.get("fullName") or ""
    if "#" not in full:
        continue
    module_path = full.split("#", 1)[0]
    seg = next((p for p in module_path.split(".") if p.startswith("test_")), module_path.split(".")[-1])
    msg = (j.get("statusDetails") or {}).get("message") or ""
    first = next((l.strip() for l in msg.splitlines() if l.strip()), "")
    first = re.sub(r"^(AssertionError|playwright\._impl\._errors\.\w+|TimeoutError):\s*", "", first)
    first = first.replace("assert ", "").strip()
    name = (j.get("name") or "").strip() or full.split("#")[-1]
    by_module.setdefault(seg, []).append((name[:80], first[:140] or "见 Allure 报告"))


def fmt(s):
    s = int(s)
    return f"{s // 60}m{s % 60:02d}s" if s >= 60 else f"{s}s"


passed = agg.get("passed", 0)
failed = agg.get("failed", 0) + agg.get("errors", 0)
skipped = agg.get("skipped", 0)
xfailed = agg.get("xfailed", 0)
total = passed + failed + skipped + xfailed

lines = ["# 稳定回归报告", ""]
lines += [
    f"- 任务: `{TASK}`",
    f"- 目标环境: `{summary['base_url']}/`",
    "- 执行对象: `artifacts/regression_registry.md` 中 URL 登记为本环境的 `stable_regression` 条目 `Tests` 列当前脚本（12 个 suite）",
    f"- 规模: {summary['suite_count']} 个 suite / {total} 条用例",
    f"- 日志目录: `artifacts/{TASK}/regression/`",
    f"- 汇总: `artifacts/{TASK}/regression/summary.json`",
    "- Allure 原始结果: `reports/allure-results-regression/`",
    "- Allure 报告: `reports/allure-report-regression/` → `http://localhost:8123/index.html`",
    "- 执行口径: 串行、单 suite 独立进程；未修改任何脚本 / 断言 / 测试数据",
    "",
    "## 简易回归报告",
    "",
    "```text",
    f"【回归测试报告】{time.strftime('%Y-%m-%d %H:%M')}",
    "",
]
for r in rows:
    c = r["counts"]
    ok = c.get("passed", 0) + c.get("xfailed", 0) + c.get("xpassed", 0)
    tot = sum(c.get(k, 0) for k in ("passed", "failed", "errors", "skipped", "xfailed", "xpassed"))
    extra = ""
    if c.get("skipped"):
        extra += f"  ({c['skipped']} skipped)"
    if c.get("xfailed"):
        extra += f"  ({c['xfailed']} xfailed)"
    stem = Path(r["tests"]).stem
    fails = by_module.get(stem, [])
    if r["result"] in ("failed", "timeout") or fails:
        head = f"❌ {r['feature']}  {ok}/{tot} · {fmt(r['seconds'])}{extra}"
    elif extra:
        head = f"⚠️ {r['feature']}  {ok}/{tot} · {fmt(r['seconds'])}{extra}"
    else:
        head = f"✅ {r['feature']}  {ok}/{tot} · {fmt(r['seconds'])}"
    if r["result"] == "timeout":
        head += "  ← 首轮 90min 上限截断（35/40），余下 5 条已单独复跑补全"
    lines.append(head)
    for name, reason in sorted(fails):
        lines.append(f"   └ {name} — {reason}")
lines += [
    "",
    f"合计: {passed} 通过 / {failed} 失败 / {skipped} 跳过" + (f" / {xfailed} xfailed" if xfailed else "") + f" · 总耗时 {fmt(summary['total_seconds'])}（含 canvas_stats 首轮超时 + 补跑）",
    f"状态: {'✅ 全部通过' if failed == 0 else '❌ 有失败'}",
    "",
    "Allure 报告: http://localhost:8123/index.html",
    "```",
    "",
    "## 逐 suite 结果",
    "",
    "| # | Feature | Script | Result | Counts | Time |",
    "|---|---|---|---|---|---|",
]
for i, r in enumerate(rows, 1):
    lines.append(
        f"| {i} | {r['feature']} | `{r['tests']}` | {r['result']} | {json.dumps(r['counts'], ensure_ascii=False)} | {fmt(r['seconds'])} |"
    )
lines += [
    "",
    "## 失败归因（候选分类，需局部复探确认）",
    "",
    "> 本轮按稳定回归红线未修改脚本 / 断言 / 测试数据；以下为归因假设，未做修复。",
    "",
    "1. **文字画质增强页 credits 计费（9 条）**：主按钮点数期望 `2/4/6`，实测文案 `Enhance 5` / `Enhance 10`（`cost_state=paid`）。",
    "2. **画布页文字功能（6 条，整 suite 全挂）**：进入画布后左侧工具栏文字入口 `Locator.click` 30s 超时，疑似入口 / 工具栏 selector 漂移。",
    "3. **移动端购买弹窗未出现（canvas_stats 11 条 + 移动端 SEO 相关）**：现场复核 0-credit 账号 `autotest202609171333@qq.com` credits 仍为 `0`，故更可能是移动端购买弹窗触发 / 弹窗结构变更，而非账号态问题。",
    "4. **埋点漏报（canvas_stats 5 条）**：`sendGaEvent` 期望 1 次实际 0 次（M-CORE-02/06/07、P-NEW-03、P-NEW-16）。",
    "5. **PC 无限画布 UI 缺失（P-INF-02/03）**：Enhance 面板未出现 `Ultra HD Mode` 与主 `Enhance` 提交按钮。",
    "6. **环境态偶发（SEO 上传 PC/移动端 L2-011）**：页面实测 `Processing failed, please try again` 及「30 分钟内重试」限流提示。",
    "7. **移动端首页 L3-004**：证件照成功链路点击 15s 超时（单条）。",
    "8. **移动端 SEO L2-005/L2-006**：`L2-005` 上传后未进入 `/tools/id-photo-edit?pid=`；`L2-006` 上传后未自动展开 `.mobile-feature-workspace` 工具面板。",
    "",
    "## 备注",
    "",
    "- `canvas_stats` 首轮在 5400s 上限处被截断（35/40），剩余 5 条 `M-NEW-10..14` 已单独复跑补全，40 条结果完整。",
    "- xfail 用例（移动端 SEO `L2-018` 已知缺陷 BUG-2026-0916-01）在 Allure 中计入 skipped，属预期。",
    "- 排除项：dev 域条目（detection_ui_seo_l6 / pc_home_v6 / pc_batch_v1）与 `pending_fix` 条目（infinite_canvas_enhance_v4）本轮未执行。",
    "",
]
(TASK_DIR / "report.md").write_text("\n".join(lines), encoding="utf-8")
counts = {k: len(v) for k, v in by_module.items()}
print("report.md written; failures per module:", json.dumps(counts, ensure_ascii=False))
