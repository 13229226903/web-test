#!/usr/bin/env python3
"""生成 SEO 检测总览仪表盘 — 展示每页检测结果和问题详情"""
import os, sys, re, json, base64, glob as _glob, argparse
from pathlib import Path
from datetime import datetime

HARNESS_ROOT = Path(__file__).parent.parent

def find_test_results(allure_dir):
    return [json.load(open(p, encoding="utf-8")) for p in sorted(_glob.glob(f"{allure_dir}/*-result.json"))]

def read_attachment(allure_dir, source):
    p = os.path.join(allure_dir, source)
    return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""

def _collect_texts(step, allure_dir):
    texts = {}
    for a in step.get("attachments", []):
        if a.get("type") in ("text/plain", "application/yaml"):
            c = read_attachment(allure_dir, a.get("source", ""))
            if c: texts[a.get("name", "")] = c
    for s in step.get("steps", []): texts.update(_collect_texts(s, allure_dir))
    return texts

def _parse_btn_detail(texts):
    """从按钮子步骤文本附件中提取每个按钮的效果。"""
    btns = []
    for name, content in texts.items():
        if name.startswith("btn-") and "结果" in name:
            m = re.search(r"按钮文案:\s*(.+?)\n效果:\s*(.+)$", content, re.MULTILINE)
            if m:
                btns.append({"text": m.group(1)[:50], "effect": m.group(2)[:80]})
    # Also try a generic pattern
    if not btns:
        for name, content in texts.items():
            if name.startswith("btn-") and "结果" in name:
                btns.append({"text": name, "effect": content.strip()[:100]})
    return btns

def parse_page_data(item, allure_dir):
    info = {
        "name": item.get("name", "?"), "status": item.get("status", "unknown"),
        "url": "", "lang": "",
        "l1_issues": [],
        "l2_issues": [],
        "l3_issues": [],
        "l1": {"body_chars": 0, "resource_total": 0, "resource_failed": 0,
               "broken_imgs": 0, "btn_count": 0, "img_count": 0,
               "btn_tested": 0, "btn_ok": 0, "console_errors": 0},
        "l2": {"passed": 0, "total": 6, "details": {}},
        "l3": {"passed": True, "summary": "", "dims": {}},
        "btn_details": [],
        "btn_screenshots": {},  # btn_idx -> {before: source, after: source}
        "screenshot_source": None,
    }
    for p in item.get("parameters", []):
        if p.get("name") == "url":
            raw = p.get("value", "")
            info["url"] = raw.strip("'\"")  # strip quotes added by Allure
    for a in item.get("attachments", []):
        if a.get("type") == "image/png":
            info["screenshot_source"] = a.get("source"); break

    for step in item.get("steps", []):
        texts = _collect_texts(step, allure_dir)
        sname = step.get("name", "")

        if "Layer 1" in sname:
            # Parse L1 text attachments
            for name, content in texts.items():
                if "可访问" in name:
                    m = re.search(r"Body.*?(\d+)\s*chars", content)
                    if m: info["l1"]["body_chars"] = int(m.group(1))
                    if "过少" in content:
                        info["l1_issues"].append({"layer": "L1", "check": "可访问性", "detail": content.split("\n")[0][:120], "severity": "error"})
                elif "资源" in name:
                    m = re.search(r"资源总数:\s*(\d+)", content);
                    if m: info["l1"]["resource_total"] = int(m.group(1))
                    m = re.search(r"关键\s*(\d+)\s*个", content)
                    if m: info["l1"]["resource_failed"] = int(m.group(1))
                    m = re.search(r"图片加载失败.*?:\s*(\d+)", content)
                    if m: info["l1"]["broken_imgs"] = int(m.group(1))
                    if info["l1"]["resource_failed"] > 3 or info["l1"]["broken_imgs"] > 2:
                        info["l1_issues"].append({"layer": "L1", "check": "资源加载", "detail": f"关键失败 {info['l1']['resource_failed']} 个, 裂图 {info['l1']['broken_imgs']} 张", "severity": "error"})
                    elif info["l1"]["resource_failed"] > 0 or info["l1"]["broken_imgs"] > 0:
                        info["l1_issues"].append({"layer": "L1", "check": "资源加载", "detail": f"关键失败 {info['l1']['resource_failed']} 个, 裂图 {info['l1']['broken_imgs']} 张", "severity": "warning"})
                elif "按钮" in name and "清单" in name:
                    m = re.search(r"(\d+) 个交互元素.*?(\d+) 按钮.*?(\d+) 试用图", content)
                    if m: info["l1"]["btn_count"] = int(m.group(2)); info["l1"]["img_count"] = int(m.group(3))
                elif "按钮" in name and "交互" in name:
                    m = re.search(r"采样按钮:\s*(\d+)", content);
                    if m: info["l1"]["btn_tested"] = int(m.group(1))
                    m = re.search(r"有响应:\s*(\d+)", content);
                    if m: info["l1"]["btn_ok"] = int(m.group(1))
                elif "Console" in name:
                    m = re.search(r"过滤后\s*(\d+)", content)
                    if m:
                        info["l1"]["console_errors"] = int(m.group(1))
                        if info["l1"]["console_errors"] > 0:
                            info["l1_issues"].append({"layer": "L1", "check": "Console", "detail": f"{info['l1']['console_errors']} 个 console error", "severity": "warning"})
            # Parse button detail sub-steps + screenshots
            info["btn_details"] = []
            info["btn_screenshots"] = {}
            btn_idx = 0
            for sub in step.get("steps", []):
                if "按钮" in sub.get("name", "") or "试用图" in sub.get("name", ""):
                    for bsub in sub.get("steps", []):
                        sub_texts = _collect_texts(bsub, allure_dir)
                        btn_info = _parse_btn_detail(sub_texts)
                        # Collect PNG screenshots
                        pngs = {}
                        for a in bsub.get("attachments", []):
                            if a.get("type") == "image/png":
                                aname = a.get("name", "")
                                src = a.get("source", "")
                                if "before" in aname:
                                    pngs["before"] = src
                                elif "after" in aname:
                                    pngs["after"] = src
                        if pngs:
                            info["btn_screenshots"][btn_idx] = pngs
                        if btn_info:
                            info["btn_details"].extend(btn_info)
                        btn_idx += 1

        elif "Layer 2" in sname:
            labels = {"语言一致性": "lang_match", "Title-H1": "title_h1",
                      "Meta标签": "meta", "区块完整性": "structure",
                      "图片Alt": "img_alt", "链接语言": "link_lang"}
            for name, content in texts.items():
                for lbl, key in labels.items():
                    if lbl in name:
                        p = "失败" not in content and "ERROR" not in content.upper() and "error" not in content.lower()
                        info["l2"]["details"][lbl] = {"passed": p, "detail": content.strip()[:200]}
                        if p: info["l2"]["passed"] += 1
                        else: info["l2_issues"].append({"layer": "L2", "check": lbl, "detail": content.strip()[:150], "severity": "warning"})

        elif "Layer 3" in sname:
            for name, content in texts.items():
                if "总览" in name:
                    info["l3"]["summary"] = content[:300]
                    info["l3"]["passed"] = "PASS" in content or "pass" in content
                elif "AI审查-" in name:
                    dn = name.replace("AI审查-", "")
                    has_issue = any(kw in content.lower() for kw in ["error", "warning", "问题", "异常", "乱码", "截断", "空白", "重叠"])
                    info["l3"]["dims"][dn] = not has_issue
                    if has_issue:
                        info["l3_issues"].append({"layer": "L3", "check": dn, "detail": content.strip()[:200], "severity": "warning"})

    return info

def load_image_b64(allure_dir, source):
    p = os.path.join(allure_dir, source)
    if not os.path.exists(p): return ""
    try:
        with open(p, "rb") as f: return "data:image/png;base64," + base64.b64encode(f.read()).decode()
    except: return ""

def build_dashboard(results, allure_dir):
    pages = []
    for item in results:
        info = parse_page_data(item, allure_dir)
        thumb = load_image_b64(allure_dir, info["screenshot_source"]) if info["screenshot_source"] else ""
        path = info["url"].split("3000")[-1] if "3000" in info["url"] else info["url"]
        pages.append({"info": info, "thumb": thumb, "path": path})

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    passed = sum(1 for p in pages if p["info"]["status"] == "passed")
    failed = len(pages) - passed

    # Build per-page card HTML
    cards = []
    card_index = 0
    for p in pages:
        info = p["info"]; l1 = info["l1"]; l2 = info["l2"]; l3 = info["l3"]
        cid = card_index
        card_index += 1
        all_issues = info["l1_issues"] + info["l2_issues"] + info["l3_issues"]
        error_count = sum(1 for i in all_issues if i["severity"] == "error")
        warn_count = sum(1 for i in all_issues if i["severity"] == "warning")

        # Status indicator
        if error_count > 0:
            status_icon, status_color = "&#10007;", "#ef4444"
        elif warn_count > 0:
            status_icon, status_color = "&#9888;", "#f59e0b"
        else:
            status_icon, status_color = "&#10003;", "#22c55e"

        # L1 stat line
        l1_parts = []
        l1_parts.append(f"Body: {l1['body_chars']} chars")
        if l1['resource_total'] > 0:
            rp = "" if l1['resource_failed'] == 0 else f' <span style="color:#ef4444;font-weight:700">({l1["resource_failed"]} failed)</span>'
            l1_parts.append(f"Res: {l1['resource_total']}{rp}")
        if l1['btn_tested'] > 0:
            bp = "" if l1['btn_tested'] == l1['btn_ok'] else f' <span style="color:#f59e0b;font-weight:700">({l1["btn_ok"]}/{l1["btn_tested"]})</span>'
            l1_parts.append(f"Btn: {l1['btn_count']}+{l1['img_count']}imgs{bp}")
        if l1['console_errors'] > 0:
            l1_parts.append(f'<span style="color:#f59e0b">Console: {l1["console_errors"]}</span>')

        # Issues preview (first 2-3)
        issue_preview = ""
        if all_issues:
            preview_items = all_issues[:3]
            issue_preview = " | ".join(
                f'<span style="color:{"#ef4444" if i["severity"]=="error" else "#f59e0b"}">[{i["check"]}] {i["detail"][:60]}</span>'
                for i in preview_items
            )

        # Button detail rows + screenshot modals
        btn_rows = ""
        btn_modals = ""
        for i, bi in enumerate(info["btn_details"]):
            effect = bi["effect"]
            ec = "#22c55e" if ("跳转" in effect or "UI 变化" in effect) else ("#f59e0b" if "无变化" in effect else "#ef4444")
            ss = info["btn_screenshots"].get(i, {})
            clickable = ""
            if ss:
                # Load screenshots as base64
                before_b64 = load_image_b64(allure_dir, ss.get("before", "")) if ss.get("before") else ""
                after_b64 = load_image_b64(allure_dir, ss.get("after", "")) if ss.get("after") else ""
                modal_id = f"modal-{hash(p['path'])}-{cid}"
                clickable = f' style="cursor:pointer;text-decoration:underline;color:{ec}" onclick="event.stopPropagation();document.getElementById(\'{modal_id}\').style.display=\'flex\'"'
                btn_modals += f"""
        <div id="{modal_id}" class="screenshot-modal" onclick="event.stopPropagation();this.style.display='none'">
            <div class="modal-content" onclick="event.stopPropagation()">
                <span class="modal-close" onclick="document.getElementById('{modal_id}').style.display='none'">&times;</span>
                <div class="modal-title">{bi['text'][:40]}</div>
                <div class="modal-pair">
                    {f'<div><div class="modal-label">Before</div><img src="{before_b64}" /></div>' if before_b64 else ''}
                    {f'<div><div class="modal-label">After</div><img src="{after_b64}" /></div>' if after_b64 else ''}
                </div>
            </div>
        </div>"""
            btn_rows += f'<tr><td style="padding:2px 4px;font-size:11px">{bi["text"][:35]}</td><td style="padding:2px 4px;font-size:11px"{clickable}>{effect[:60]}</td></tr>'

        # L2 detail rows
        l2_rows = ""
        for lbl, d in l2["details"].items():
            c = "#22c55e" if d["passed"] else "#f59e0b"
            l2_rows += f'<span style="margin:2px;padding:2px 6px;border-radius:3px;font-size:10px;background:{"#f0fdf4" if d["passed"] else "#fefce8"};color:{c}">{lbl}: {"OK" if d["passed"] else "WARN"}</span>'

        # L3 dim dots
        l3_dots = ""
        for dn, dok in l3["dims"].items():
            dc = "#22c55e" if dok else "#f59e0b"
            l3_dots += f'<span style="display:inline-block;width:8px;height:8px;border-radius:50%;margin:1px;background:{dc}" title="{dn}"></span>'

        cards.append(f"""
        <div class="card" onclick="if(!event.target.closest('a'))this.classList.toggle('expanded')">
            <div class="card-top">
                <div class="card-path"><a href="{info['url']}" target="_blank" style="color:#334155;text-decoration:none" onclick="event.stopPropagation()" title="Open in new tab">{p['path']}</a></div>
                <div class="card-status" style="background:{status_color}">{status_icon}</div>
            </div>
            {f'<img class="card-thumb" src="{p["thumb"]}" loading="lazy" onclick="event.stopPropagation();document.getElementById(\'main-modal-{cid}\').style.display=\'flex\'" title="Click to enlarge" />' if p['thumb'] else '<div class="card-no-thumb">No Screenshot</div>'}
            <div class="card-body">
                <div class="card-stats-line">{" | ".join(l1_parts)}</div>
                {f'<div class="card-issues">{issue_preview}</div>' if issue_preview else '<div class="card-issues" style="color:#22c55e">All checks passed</div>'}
                <div class="card-summary-row">
                    <span style="font-size:10px;color:#64748b">L2:</span> {l2_rows}
                </div>
                <div class="card-summary-row">
                    <span style="font-size:10px;color:#64748b">L3:</span> {l3_dots} <span style="font-size:10px;color:#64748b">{l3['summary'][:80] if l3['summary'] else ('PASS' if l3['passed'] else 'ISSUES')}</span>
                </div>
            </div>
            <div class="card-expand">
                <div class="expand-section">
                    <h4>Button & Image Interaction Results (click effect to view screenshots)</h4>
                    {f'<table style="width:100%;border-collapse:collapse"><tr style="background:#f1f5f9"><th style="padding:2px 4px;font-size:11px;text-align:left">Element</th><th style="padding:2px 4px;font-size:11px;text-align:left">Effect</th></tr>{btn_rows}</table>' if btn_rows else '<div style="font-size:11px;color:#94a3b8">No interaction data</div>'}
                </div>
                {f'''<div id="main-modal-{cid}" class="screenshot-modal" onclick="event.stopPropagation();this.style.display='none'">
            <div class="modal-content zoom-container" onclick="event.stopPropagation()" id="zoom-container-{cid}">
                <span class="modal-close" onclick="document.getElementById('main-modal-{cid}').style.display='none'">&times;</span>
                <div class="modal-title">Full Page Screenshot — {p['path']} <span style="font-weight:400;color:#94a3b8;font-size:10px">(scroll to zoom, drag to pan, double-click to reset)</span></div>
                <div style="overflow:hidden;border-radius:6px;cursor:grab" id="zoom-viewport-{cid}">
                    <img src="{p['thumb']}" id="zoom-img-{cid}" style="display:block;max-width:90vw;max-height:78vh;transform-origin:0 0;transition:none" />
                </div>
            </div>
        </div>''' if p['thumb'] else ''}
                {btn_modals}
                <div class="expand-section">
                    <h4>L2 Self-Consistency Details</h4>
                    <div style="font-size:11px">
                    {"<br>".join(f'{"OK" if d["passed"] else "WARN"}: {lbl} — {d["detail"][:120]}' for lbl,d in l2["details"].items()) if l2["details"] else "No data"}
                    </div>
                </div>
                <div class="expand-section">
                    <h4>L3 AI Review</h4>
                    <div style="font-size:11px;color:#64748b">{l3['summary'][:300] or 'N/A'}</div>
                </div>
                <div class="expand-actions">
                    <a href="{info['url']}" target="_blank" class="expand-link">Open Page</a>
                    <a href="../allure-report/index.html" target="_blank" class="expand-link" style="background:#64748b">Allure Report</a>
                </div>
            </div>
        </div>""")

    # ── Assemble full HTML ──
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>SEO Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f1f5f9;color:#1e293b;padding:24px}}
.header{{max-width:1500px;margin:0 auto 16px}}
.header h1{{font-size:22px;font-weight:700}}
.header .meta{{font-size:12px;color:#64748b}}
.stats{{display:flex;gap:8px;margin:10px 0;flex-wrap:wrap}}
.stat{{background:#fff;border-radius:8px;padding:10px 16px;box-shadow:0 1px 2px rgba(0,0,0,0.04)}}
.stat-val{{font-size:24px;font-weight:700}}
.stat-label{{font-size:10px;color:#64748b}}
.grid{{max-width:1500px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:12px}}
.card{{background:#fff;border-radius:10px;box-shadow:0 1px 3px rgba(0,0,0,0.06);overflow:hidden;cursor:pointer;transition:box-shadow .2s}}
.card:hover{{box-shadow:0 4px 12px rgba(0,0,0,0.10)}}
.card-top{{display:flex;justify-content:space-between;align-items:center;padding:6px 10px;background:#f8fafc}}
.card-path{{font-size:12px;font-weight:600;color:#334155;word-break:break-all;flex:1;margin-right:6px}}
.card-status{{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;font-weight:700;flex-shrink:0}}
.card-thumb{{width:100%;height:160px;object-fit:cover;object-position:top;cursor:pointer}}
.card-no-thumb{{width:100%;height:50px;display:flex;align-items:center;justify-content:center;color:#94a3b8;font-size:12px;background:#f8fafc}}
.card-body{{padding:6px 10px}}
.card-stats-line{{font-size:10px;color:#475569;line-height:1.6;margin-bottom:4px}}
.card-issues{{font-size:10px;line-height:1.4;margin-bottom:4px;padding:4px 6px;border-radius:4px;background:#fefce8}}
.card-summary-row{{margin-top:3px;line-height:1.8}}
.card-expand{{display:none;padding:0 10px 10px}}
.card.expanded .card-expand{{display:block}}
.expand-section{{margin-top:8px;padding-top:8px;border-top:1px solid #f1f5f9}}
.expand-section h4{{font-size:11px;color:#475569;margin-bottom:4px}}
.expand-actions{{display:flex;gap:6px;margin-top:10px}}
.expand-link{{padding:5px 12px;border-radius:5px;font-size:11px;color:#fff;text-decoration:none;background:#3b82f6;display:inline-block}}
.screenshot-modal{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:9999;align-items:center;justify-content:center}}
.modal-content{{background:#fff;border-radius:10px;padding:16px;max-width:95vw;max-height:90vh;overflow:auto;position:relative}}
.modal-close{{position:absolute;top:8px;right:14px;font-size:24px;cursor:pointer;color:#64748b}}
.modal-title{{font-size:14px;font-weight:600;margin-bottom:10px;color:#1e293b}}
.modal-pair{{display:flex;gap:12px;flex-wrap:wrap;justify-content:center}}
.modal-pair img{{max-height:70vh;max-width:45vw;border-radius:6px;box-shadow:0 2px 8px rgba(0,0,0,0.15)}}
.modal-label{{font-size:11px;color:#64748b;margin-bottom:4px;text-align:center}}
</style></head>
<body>
<div class="header">
    <h1>SEO New Page Dashboard</h1>
    <div class="meta">Generated: {now} | {len(pages)} pages | {passed} passed, {failed} failed</div>
    <div class="stats">
        <div class="stat"><div class="stat-val">{len(pages)}</div><div class="stat-label">Pages</div></div>
        <div class="stat"><div class="stat-val" style="color:#22c55e">{passed}</div><div class="stat-label">Passed</div></div>
        <div class="stat"><div class="stat-val" style="color:#ef4444">{failed}</div><div class="stat-label">Failed</div></div>
    </div>
</div>
<div class="grid">""" + "".join(cards) + """</div>
<script>
(function() {
    var states = {};
    document.querySelectorAll('[id^="zoom-viewport-"]').forEach(function(vp) {
        var idx = vp.id.replace('zoom-viewport-', '');
        var img = document.getElementById('zoom-img-' + idx);
        if (!img) return;
        states[idx] = { scale: 1, tx: 0, ty: 0, dragging: false, mx: 0, my: 0 };
        function apply() {
            var s = states[idx];
            img.style.transform = 'translate(' + s.tx + 'px,' + s.ty + 'px) scale(' + s.scale + ')';
        }
        vp.addEventListener('wheel', function(e) {
            e.preventDefault();
            var s = states[idx];
            var rect = img.getBoundingClientRect();
            var cx = e.clientX - rect.left, cy = e.clientY - rect.top;
            var old = s.scale;
            s.scale = Math.max(0.3, Math.min(5, s.scale * (e.deltaY > 0 ? 0.9 : 1.1)));
            s.tx = cx - (cx - s.tx) * (s.scale / old);
            s.ty = cy - (cy - s.ty) * (s.scale / old);
            apply();
        }, { passive: false });
        vp.addEventListener('mousedown', function(e) {
            states[idx].dragging = true; states[idx].mx = e.clientX; states[idx].my = e.clientY;
            vp.style.cursor = 'grabbing'; e.preventDefault();
        });
        window.addEventListener('mousemove', function(e) {
            var s = states[idx]; if (!s.dragging) return;
            s.tx += e.clientX - s.mx; s.ty += e.clientY - s.my;
            s.mx = e.clientX; s.my = e.clientY; apply();
        });
        window.addEventListener('mouseup', function() {
            states[idx].dragging = false; vp.style.cursor = 'grab';
        });
        vp.addEventListener('dblclick', function() {
            var s = states[idx]; s.scale = 1; s.tx = 0; s.ty = 0; apply();
        });
    });
})();
</script>
</body></html>"""
    return html

def main():
    p = argparse.ArgumentParser(description="Generate SEO Dashboard")
    p.add_argument("--input", default=str(HARNESS_ROOT / "reports" / "allure-results"))
    p.add_argument("--output", default=str(HARNESS_ROOT / "reports" / "seo-dashboard.html"))
    args = p.parse_args()
    if not os.path.isdir(args.input):
        print(f"Error: {args.input} not found."); sys.exit(1)
    print(f"[Dashboard] Reading: {args.input}")
    results = find_test_results(args.input)
    print(f"[Dashboard] {len(results)} results")
    html = build_dashboard(results, args.input)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f: f.write(html)
    print(f"[Dashboard] Saved: {args.output} ({os.path.getsize(args.output)//1024} KB)")

if __name__ == "__main__": main()
