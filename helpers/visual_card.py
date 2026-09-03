"""Allure 内嵌 HTML 可视卡片生成器

生成自包含的 HTML 卡片，附加到 Allure 报告中，提供可视化摘要。

用法：
    from helpers.visual_card import build_card_html
    html = build_card_html(page_name, url, screenshot_path, layer_results, page_meta)
    allure.attach(html, name="可视摘要", attachment_type=allure.attachment_type.HTML)
"""

import base64
import os
import json
from pathlib import Path
from typing import Optional


def _img_to_base64(path: str, max_width: int = 400) -> Optional[str]:
    """将图片转为 base64 data URI，并限制显示宽度。"""
    if not path or not os.path.exists(path):
        return None
    try:
        with open(path, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        return f"data:image/png;base64,{data}"
    except Exception:
        return None


def _badge(status: str, text: str) -> str:
    """生成状态徽章 HTML。"""
    if status == "pass":
        color, icon = "#22c55e", "&#10003;"
    elif status == "warning":
        color, icon = "#f59e0b", "&#9888;"
    elif status == "error":
        color, icon = "#ef4444", "&#10007;"
    else:
        color, icon = "#94a3b8", "&#8212;"
    return (
        f'<span style="display:inline-block;background:{color};color:#fff;'
        f'padding:2px 8px;border-radius:4px;font-size:12px;margin:2px;'
        f'white-space:nowrap">{icon} {text}</span>'
    )


def build_card_html(
    page_name: str,
    url: str,
    screenshot_path: Optional[str],
    l1_result: dict,
    l2_result: dict,
    l3_result: dict,
    page_meta: dict,
) -> str:
    """构建单页面可视化摘要 HTML 卡片。

    Args:
        page_name: 页面简称
        url: 完整 URL
        screenshot_path: 首屏截图路径
        l1_result: Layer 1 不变量检查结果 {"checks": {...}, ...}
        l2_result: Layer 2 自一致性结果 {"checks": {...}, ...}
        l3_result: Layer 3 AI 审查结果 {"passed": bool, "issues": [...], "summary": "..."}
        page_meta: {"title": str, "h1s": [str], "h2s": [str]}

    Returns:
        自包含的 HTML 字符串
    """
    screenshot_b64 = _img_to_base64(screenshot_path) if screenshot_path else None

    # ── Layer 1 数据 ──
    l1_checks = l1_result.get("checks", {})
    # accessible
    acc = l1_checks.get("accessible", {})
    acc_passed = acc.get("passed", True)
    # resources
    res = l1_checks.get("resources", {})
    res_passed = res.get("passed", True)
    # buttons (有 sub_results 就提取)
    btn_checks = l1_checks.get("buttons", {})
    btn_passed = btn_checks.get("passed", True)
    # console
    con = l1_checks.get("console", {})
    con_passed = con.get("passed", True)

    # ── Layer 2 数据 ──
    l2_checks = l2_result.get("checks", {})
    l2_items = []
    for key, label in [
        ("lang_match", "语言一致"), ("title_h1", "Title-H1"),
        ("meta", "Meta标签"), ("structure", "区块完整"),
        ("img_alt", "图片Alt"), ("link_lang", "链接语言"),
    ]:
        c = l2_checks.get(key, {})
        l2_items.append((label, c.get("passed", True), c.get("detail", "?")))

    l2_passed = sum(1 for _, p, _ in l2_items if p)
    l2_total = len(l2_items)

    # ── Layer 3 数据 ──
    l3_passed = l3_result.get("passed", True)
    l3_summary = l3_result.get("summary", l3_result.get("detail", ""))[:200]
    l3_issues = l3_result.get("issues", [])
    l3_dims = {"layout": "布局", "image": "图片", "text": "文案", "cta": "CTA", "content": "内容"}
    l3_dim_results = {}
    for dim_key, dim_label in l3_dims.items():
        dim_issues = [i for i in l3_issues if i.get("dimension") == dim_key]
        l3_dim_results[dim_label] = len(dim_issues) == 0

    # ── 收集所有 issues ──
    l1_issues_raw = l1_result.get("errors", []) + l1_result.get("warnings", [])
    l2_issues_raw = l2_result.get("warnings", []) + l2_result.get("errors", [])
    l3_issues_raw = l3_result.get("issues", [])
    all_card_issues = l1_issues_raw + l2_issues_raw + l3_issues_raw

    # L2 未通过项详情
    l2_fail_detail = ""
    for label, passed, detail in l2_items:
        if not passed:
            l2_fail_detail += f'<div style="font-size:11px;color:#f59e0b;margin:2px 0">{label}: {detail[:80]}</div>'

    # ── 按钮交互详情 ──
    btn_details_html = ""
    btn_results = btn_checks.get("results", [])
    if btn_results:
        btn_details_html = '<div style="margin-top:6px;font-size:11px;">'
        btn_details_html += '<table style="width:100%;border-collapse:collapse;font-size:11px;">'
        btn_details_html += '<tr style="background:#f1f5f9;"><th style="padding:2px 4px;text-align:left;">#</th><th style="padding:2px 4px;text-align:left;">类型</th><th style="padding:2px 4px;text-align:left;">元素</th><th style="padding:2px 4px;text-align:left;">效果</th></tr>'
        for i, br in enumerate(btn_results[:8]):
            text = br.get("text", "?")[:25]
            etype = br.get("type", "button")
            effect = br.get("effect", "?")
            if any(keyword in effect for keyword in [
                "跳转", "UI 变化", "弹层", "展开", "编辑器", "正文内容变化", "滚动到新位置", "打开"
            ]):
                dot = '<span style="color:#22c55e;">&#9679;</span>'
            elif any(keyword in effect for keyword in ["无变化", "未检测到变化", "不明显"]):
                dot = '<span style="color:#f59e0b;">&#9679;</span>'
            else:
                dot = '<span style="color:#ef4444;">&#9679;</span>'
            bg = "#f8fafc" if i % 2 == 0 else "#fff"
            btn_details_html += (
                f'<tr style="background:{bg};"><td style="padding:2px 4px;">{i+1}</td>'
                f'<td style="padding:2px 4px;font-size:10px">{"img" if etype == "image" else "btn"}</td>'
                f'<td style="padding:2px 4px;">{text}</td>'
                f'<td style="padding:2px 4px;">{dot} {effect[:40]}</td></tr>'
            )
        btn_details_html += '</table></div>'

    # ── AI 审查维度条 ──
    ai_dims_html = ""
    for dim_label, dim_ok in l3_dim_results.items():
        ai_dims_html += _badge("pass" if dim_ok else "warning", dim_label)

    # ═══════════════════════════════════════════════════
    # Precompute HTML fragments (must be done BEFORE the f-string)
    # ═══════════════════════════════════════════════════
    title = (page_meta.get("title") or url)[:80]
    h1_text = (page_meta.get("h1s", [""]) or [""])[0][:60] if page_meta.get("h1s") else ""

    # Issues panel
    issues_html = ""
    if all_card_issues:
        issue_lines = []
        for issue_item in all_card_issues[:6]:
            itype = issue_item.get("type", "?")
            idetail = issue_item.get("detail", "")[:100]
            issue_lines.append(f"[{itype}] {idetail}")
        issue_bullets = "<br>".join(issue_lines)
        issues_html = (
            f'<div style="padding:8px 18px;background:#fef2f2;'
            f'border-bottom:1px solid #fecaca;font-size:12px">'
            f'<b style="color:#dc2626">Issues Found ({len(all_card_issues)}):</b><br>{issue_bullets}</div>'
        )

    # L2 fail details
    l2_fail_html = ""
    if l2_fail_detail:
        l2_fail_html = (
            f'<div style="padding:8px 18px;background:#fefce8;'
            f'border-bottom:1px solid #fde68a;font-size:12px">{l2_fail_detail}</div>'
        )

    # ═══════════════════════════════════════════════════
    # 组装 HTML
    # ═══════════════════════════════════════════════════
    html = f"""<!DOCTYPE html>
<html lang="zh">
<head><meta charset="UTF-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background:#f8fafc; padding:16px; }}
.card {{ max-width:720px; margin:0 auto; background:#fff; border-radius:12px; box-shadow:0 1px 3px rgba(0,0,0,0.1); overflow:hidden; }}
.header {{ background:linear-gradient(135deg,#1e293b,#334155); color:#fff; padding:14px 18px; }}
.header h2 {{ font-size:16px; font-weight:600; margin-bottom:4px; }}
.header .url {{ font-size:11px; color:#94a3b8; word-break:break-all; }}
.header .meta {{ font-size:11px; color:#cbd5e1; margin-top:4px; }}
.screenshot {{ width:100%; max-height:350px; object-fit:cover; border-bottom:1px solid #e2e8f0; }}
.section {{ padding:12px 18px; border-bottom:1px solid #f1f5f9; }}
.section:last-child {{ border-bottom:none; }}
.section-title {{ font-size:13px; font-weight:700; color:#334155; margin-bottom:8px; display:flex; align-items:center; gap:8px; }}
.section-title .layer-badge {{ font-size:10px; padding:1px 6px; border-radius:3px; color:#fff; }}
.l1 {{ background:#3b82f6; }}
.l2 {{ background:#8b5cf6; }}
.l3 {{ background:#06b6d4; }}
.metrics {{ display:flex; gap:8px; flex-wrap:wrap; }}
.metric {{ flex:1; min-width:80px; background:#f8fafc; border-radius:8px; padding:8px 10px; text-align:center; }}
.metric .value {{ font-size:20px; font-weight:700; }}
.metric .label {{ font-size:10px; color:#64748b; margin-top:2px; }}
.pass {{ color:#22c55e; }}
.warning {{ color:#f59e0b; }}
.error {{ color:#ef4444; }}
.neutral {{ color:#94a3b8; }}
.l2-grid {{ display:grid; grid-template-columns: repeat(3, 1fr); gap:4px; font-size:12px; }}
.l2-item {{ padding:4px 6px; border-radius:4px; background:#f8fafc; display:flex; align-items:center; gap:4px; }}
.l2-item .dot {{ width:8px; height:8px; border-radius:50%; flex-shrink:0; }}
.dot-pass {{ background:#22c55e; }}
.dot-warn {{ background:#f59e0b; }}
.dot-err {{ background:#ef4444; }}
.ai-verdict {{ padding:8px 12px; border-radius:8px; font-size:12px; margin-top:6px; }}
.ai-pass {{ background:#f0fdf4; border:1px solid #bbf7d0; }}
.ai-fail {{ background:#fef2f2; border:1px solid #fecaca; }}
</style></head>
<body>
<div class="card">
  <div class="header">
    <h2>{title}</h2>
    <div class="url">{url}</div>
    <div class="meta">H1: {h1_text or '(空)'}</div>
  </div>
  {f'<img class="screenshot" src="{screenshot_b64}" alt="首屏截图" />' if screenshot_b64 else ''}
  {issues_html}
  {l2_fail_html}
  """

    # ── Layer 1 区块 ──
    l1_total = 4
    l1_ok = sum([1 for x in [acc_passed, res_passed, btn_passed, con_passed] if x])
    html += f"""
  <div class="section">
    <div class="section-title"><span class="layer-badge l1">L1</span> 不变量检查 <span class="{'pass' if l1_ok==l1_total else 'warning'}">{l1_ok}/{l1_total} 通过</span></div>
    <div class="metrics">
      <div class="metric"><div class="value {'pass' if acc_passed else 'error'}">{acc.get('detail','?').split()[0] if acc_passed else 'FAIL'}</div><div class="label">可访问性</div></div>
      <div class="metric"><div class="value {'pass' if res_passed else 'error'}">{'OK' if res_passed else 'FAIL'}</div><div class="label">资源加载</div></div>
      <div class="metric"><div class="value {'pass' if btn_passed else 'warning'}">{btn_checks.get('detail','?')[:20]}</div><div class="label">按钮交互</div></div>
      <div class="metric"><div class="value {'pass' if con_passed else 'warning'}">{'OK' if con_passed else 'ERR'}</div><div class="label">Console</div></div>
    </div>
    {btn_details_html}
  </div>"""

    # ── Layer 2 区块 ──
    html += f"""
  <div class="section">
    <div class="section-title"><span class="layer-badge l2">L2</span> 自一致性检查 <span class="{'pass' if l2_passed==l2_total else 'warning'}">{l2_passed}/{l2_total} 通过</span></div>
    <div class="l2-grid">"""
    for label, passed, detail in l2_items:
        cls = "dot-pass" if passed else "dot-warn"
        html += f'<div class="l2-item"><span class="dot {cls}"></span> {label}</div>'
    html += '</div></div>'

    # ── Layer 3 区块 ──
    l3_ok_count = sum(1 for v in l3_dim_results.values() if v)
    l3_total_count = len(l3_dim_results)
    l3_cls = "ai-pass" if l3_passed else "ai-fail"
    html += f"""
  <div class="section">
    <div class="section-title"><span class="layer-badge l3">L3</span> AI 内容审查 <span class="{'pass' if l3_passed else 'warning'}">{'PASS' if l3_passed else 'ISSUES'}</span></div>
    <div style="display:flex;gap:4px;flex-wrap:wrap;margin-bottom:6px;">{ai_dims_html}</div>
    <div class="ai-verdict {l3_cls}">{l3_summary or '(审查完成)'}</div>
  </div>"""

    html += """
</div>
</body></html>"""
    return html
