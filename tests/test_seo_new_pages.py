"""SEO 新页面自动化检测（规则 + direct LLM 覆盖）

与现有 SEO 回归测试（test_seo_*.py）独立：
  - SEO 回归：手写预期，针对已知页面，Allure → reports/seo-regression/
  - SEO 新页面：配置驱动，针对新增页面，Allure → reports/seo-new-pages/

三层覆盖：
  Layer 1: 不变量检查 — 页面可访问 / 资源加载 / 按钮交互 / console 错误 / 内链 / FAQ
  Layer 2: 自一致性检查 — 语言/title-h1/meta/区块/图片alt/链接前缀
  Layer 3: AI 内容审查 — 布局/图片/文案/CTA（多模态模型）
  Layer 4: direct LLM 语义复核 — 基于首屏截图 + 页面提示的内容审查

新页面用法：在 config/seo_new_pages.yaml 加一条 path 即可；`semantic_review` 默认开启，可显式设为 `false` 关闭。

运行方式：
  python -m pytest tests/test_seo_new_pages.py -v -m seo_new --alluredir=reports/allure-results
"""

import os
import re
import json
import traceback
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import pytest
import allure

HARNESS_ROOT = Path(__file__).parent.parent

MOBILE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
    "Mobile/15E148 Safari/604.1"
)

from conftest import allure_screenshot, SCREENSHOT_DIR, _dismiss_login_popup_if_present
from helpers.ai_page_review import create_reviewer
from helpers.link_checker import verify_seo_links
from helpers.visual_card import build_card_html
from helpers.llm_judge import judge_text_quality
from helpers.simple_yaml import load_simple_yaml
import glob as _glob


# ═══════════════════════════════════════════════════════════════
# 加载 SEO 新页面清单
# ═══════════════════════════════════════════════════════════════

def _load_seo_new_pages():
    config_path = HARNESS_ROOT / "config" / "seo_new_pages.yaml"
    if not config_path.exists():
        return "", []
    data = load_simple_yaml(config_path)
    domain = os.getenv("SEO_DOMAIN", data.get("seo_domain", ""))
    pages = data.get("seo_pages", [])
    return domain, pages


SEO_DOMAIN, SEO_PAGES = _load_seo_new_pages()


def _page_name(path: str) -> str:
    if isinstance(path, dict):
        path = path.get("path", "")
    return path.strip("/").rsplit("/", 1)[-1]


def _detect_lang_prefix(path: str) -> str:
    m = re.match(r"^/([a-z]{2}(?:-[a-z]{2})?)/", path)
    return m.group(1) if m else ""


def _entry_path(entry) -> str:
    return entry.get("path", "") if isinstance(entry, dict) else entry


def _entry_semantic_review(entry) -> bool:
    if isinstance(entry, dict):
        if "semantic_review" in entry:
            return bool(entry.get("semantic_review"))
        return True
    env_value = os.getenv("SEO_SEMANTIC_REVIEW", os.getenv("SEO_AGENT_REVIEW", "1")).lower()
    return env_value in {"1", "true", "yes"}


def _entry_review_notes(entry) -> str:
    if isinstance(entry, dict):
        return str(entry.get("review_notes", "")).strip()
    return ""


def _build_review_hints(page_path: str, page_meta: dict, entry) -> str:
    hints = {
        "path": page_path,
        "title": page_meta.get("title", ""),
        "h1s": page_meta.get("h1s", [])[:3],
        "h2s": page_meta.get("h2s", [])[:5],
        "meta_description": page_meta.get("meta_description", ""),
        "cta_buttons": page_meta.get("cta_buttons", [])[:8],
        "internal_links": [
            f"{item.get('text', '')} -> {item.get('href', '')}"
            for item in page_meta.get("internal_links", [])[:8]
        ],
        "review_notes": _entry_review_notes(entry),
    }
    return json.dumps({k: v for k, v in hints.items() if v}, ensure_ascii=False, indent=2)


def _safe_report_name(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]+", "-", text.strip())
    text = re.sub(r"\s+", "-", text)
    return text[:120].strip("-") or "seo-page"


def _write_bug_report(name: str, url: str, page_path: str, page_meta: dict,
                      all_errors: list[dict], all_warnings: list[dict],
                      screenshot_path: str | None = None) -> Path:
    report_dir = HARNESS_ROOT / "reports" / "seo-bug-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    safe_name = _safe_report_name(name)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_path = report_dir / f"{stamp}-{safe_name}.md"

    title = page_meta.get("title", "").strip() or "N/A"
    h1 = page_meta.get("h1s", [""])[0].strip() if page_meta.get("h1s") else "N/A"
    lang = _detect_lang_prefix(page_path) or "en"

    lines = [
        f"# SEO Bug Report - {name}",
        "",
        f"- SEO URL: {url}",
        f"- Path: {page_path}",
        f"- Language: {lang}",
        f"- Title: {title}",
        f"- H1: {h1}",
        f"- Error Count: {len(all_errors)}",
        f"- Warning Count: {len(all_warnings)}",
        "",
        "## Failure Summary",
        f"{len(all_errors)} error(s), {len(all_warnings)} warning(s).",
        "",
        "## Error Details",
    ]

    if all_errors:
        for idx, item in enumerate(all_errors, 1):
            lines.append(f"{idx}. [{item.get('type', '?')}] {item.get('detail', '')}")
    else:
        lines.append("None")

    if all_warnings:
        lines.extend(["", "## Warning Details"])
        for idx, item in enumerate(all_warnings, 1):
            lines.append(f"{idx}. [{item.get('type', '?')}] {item.get('detail', '')}")

    lines.extend([
        "",
        "## Evidence",
        f"- Allure report: {HARNESS_ROOT / 'reports' / 'allure-report' / 'index.html'}",
    ])
    if screenshot_path:
        lines.append(f"- First screen screenshot: {screenshot_path}")
    lines.extend([
        "",
        "## Repro",
        "1. Open the SEO URL.",
        "2. Re-run the SEO new page test.",
        "3. Check the failing layer details in Allure and the attachments above.",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _write_batch_bug_report(batch_name: str, results: list[dict]) -> Path:
    report_dir = HARNESS_ROOT / "reports" / "seo-bug-reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = _safe_report_name(batch_name)
    report_path = report_dir / f"{stamp}-{safe_name}.md"

    failed = [item for item in results if item.get("errors")]
    passed = [item for item in results if not item.get("errors")]
    lines = [
        f"# SEO Bug Report - {batch_name}",
        "",
        f"- Total Cases: {len(results)}",
        f"- Passed Cases: {len(passed)}",
        f"- Failed Cases: {len(failed)}",
        "",
        "## Failed Cases",
    ]

    if not failed:
        lines.append("None")
    else:
        for idx, item in enumerate(failed, 1):
            errors = item.get("errors", [])
            warnings = item.get("warnings", [])
            lines.extend([
                "",
                f"### {idx}. [{item.get('device', '?')}] {item.get('name', '?')}",
                f"- SEO URL: {item.get('url', '')}",
                f"- Path: {item.get('page_path', '')}",
                f"- Language: {item.get('lang', '')}",
                f"- Title: {item.get('title', '')}",
                f"- H1: {item.get('h1', '')}",
                f"- Error Count: {len(errors)}",
                f"- Warning Count: {len(warnings)}",
                "",
                "#### Error Details",
            ])
            if errors:
                for j, err in enumerate(errors, 1):
                    lines.append(f"{j}. [{err.get('type', '?')}] {err.get('detail', '')}")
            else:
                lines.append("None")
            if warnings:
                lines.extend(["", "#### Warning Details"])
                for j, warn in enumerate(warnings, 1):
                    lines.append(f"{j}. [{warn.get('type', '?')}] {warn.get('detail', '')}")
            lines.extend([
                "",
                "#### Evidence",
                f"- Allure report: {HARNESS_ROOT / 'reports' / 'allure-report-seo-new' / 'index.html'}",
            ])
            if item.get("screenshot_path"):
                lines.append(f"- Screenshot: {item.get('screenshot_path')}")

    lines.extend([
        "",
        "## Summary",
        f"Batch cases: {len(results)}, failed: {len(failed)}",
    ])

    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def _capture_screenshot(page, stem: str, full_page: bool = False) -> str:
    screenshot_dir = HARNESS_ROOT / "data" / "screenshots"
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = _safe_report_name(stem)
    path = screenshot_dir / f"{safe_stem}.png"
    png = page.screenshot(full_page=full_page)
    path.write_bytes(png)
    allure.attach(png, name=stem, attachment_type=allure.attachment_type.PNG)
    return str(path)


def _warm_up_lazy_content(page, exhaustive: bool = False) -> dict:
    """Scroll the page enough to trigger lazy/deferred visual content."""
    page.evaluate("""() => {
        document.querySelectorAll('img').forEach(function(img) {
            if (img.loading === 'lazy') img.loading = 'eager';
            if (!(img.getAttribute('src') || img.currentSrc)) {
                var fallback = img.getAttribute('data-src') ||
                    img.getAttribute('data-original') ||
                    img.getAttribute('data-lazy-src') ||
                    img.getAttribute('data-url');
                if (fallback) img.setAttribute('src', fallback);
            }
        });
        window.dispatchEvent(new Event('scroll'));
        window.dispatchEvent(new Event('resize'));
    }""")
    page.wait_for_timeout(800)

    viewport_height = page.evaluate("window.innerHeight || document.documentElement.clientHeight || 800")
    step = max(350, int(viewport_height * 0.75))
    max_steps = 80 if exhaustive else 10
    steps = 0
    last_y = -1
    for _ in range(max_steps):
        y = page.evaluate("window.scrollY || 0")
        height = page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
        if y >= max(0, height - viewport_height - 5):
            break
        page.mouse.wheel(0, step)
        page.wait_for_timeout(300 if exhaustive else 220)
        steps += 1
        new_y = page.evaluate("window.scrollY || 0")
        if new_y == last_y:
            break
        last_y = new_y

    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1200 if exhaustive else 800)
    final_height = page.evaluate("Math.max(document.body.scrollHeight, document.documentElement.scrollHeight)")
    return {"steps": steps, "height": final_height, "step": step}


def _restart_seo_backend(browser) -> bool:
    admin_url = "http://10.17.2.54:3005/"
    context = browser.new_context(viewport={"width": 1280, "height": 800}, locale="en-US")
    page = context.new_page()
    try:
        page.goto(admin_url, timeout=60000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1500)
        clicked = page.evaluate("""() => {
            const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim().toLowerCase();
            const buttons = Array.from(document.querySelectorAll('button'));
            const target = buttons.find((btn) => {
                const text = norm(btn.textContent);
                return text === '重启' || text === 'restart' || text === 'reboot';
            });
            if (!target) return false;
            target.click();
            return true;
        }""")
        allure.attach(
            f"管理后台重启按钮点击结果: {'成功' if clicked else '未找到'}",
            name="500兜底-重启",
            attachment_type=allure.attachment_type.TEXT,
        )
        page.wait_for_timeout(8000)
        return bool(clicked)
    finally:
        context.close()


def _collect_page_meta(page, include_internal_links: bool = True) -> dict:
    return page.evaluate("""(includeLinks) => {
        var title = document.title || '';
        var h1s = [];
        document.querySelectorAll('h1').forEach(function(h) {
            var t = (h.textContent || '').trim().replace(/\\s+/g, ' ');
            if (t.length > 2) h1s.push(t);
        });
        var h2s = [];
        document.querySelectorAll('h2').forEach(function(h) {
            var t = (h.textContent || '').trim().replace(/\\s+/g, ' ');
            if (t.length > 2) h2s.push(t);
        });
        var metaDesc = document.querySelector('meta[name="description"]');
        var layout = document.querySelector('#__nuxt > div:first-child');
        var mainEl = (layout && layout.children && layout.children.length >= 2) ? layout.children[1] : null;
        var root = mainEl || document;
        var ctaButtons = [];
        root.querySelectorAll('button:not([disabled]), [role="button"]').forEach(function(btn) {
            var t = (btn.textContent || '').trim().replace(/\\s+/g, ' ');
            var rect = btn.getBoundingClientRect();
            if (t.length > 1 && rect.width > 0 && rect.height > 0) {
                ctaButtons.push(t.slice(0, 60));
            }
        });
        var internalLinks = [];
        if (includeLinks) {
            root.querySelectorAll('a[href]').forEach(function(a) {
                var h = a.getAttribute('href') || '';
                var t = (a.textContent || '').trim().replace(/\\s+/g, ' ');
                if (h && h.startsWith('/') && !h.startsWith('//') && t && !t.toLowerCase().includes('home')) {
                    internalLinks.push({href: h, text: t.slice(0, 50)});
                }
            });
        }
        return {
            title: title, h1s: h1s, h2s: h2s,
            meta_description: metaDesc ? metaDesc.getAttribute('content') || '' : '',
            cta_buttons: ctaButtons.slice(0, 12),
            internal_links: internalLinks.slice(0, 12),
            body_chars: (document.body.innerText || '').replace(/\\s+/g, ' ').length,
        };
    }""", include_internal_links)


def _collect_text_for_review(page) -> str:
    return page.evaluate("""() => {
        const body = document.body || document.documentElement;
        const clone = body.cloneNode(true);
        const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim().toLowerCase();
        const looksLikeFloatingLayer = (el) => {
            if (!el || !el.getBoundingClientRect) return false;
            const style = window.getComputedStyle(el);
            if (!style) return false;
            const name = norm([
                el.className,
                el.id,
                el.getAttribute && el.getAttribute('role'),
                el.getAttribute && el.getAttribute('aria-label'),
                el.getAttribute && el.getAttribute('title'),
                el.textContent,
            ].join(' '));
            if (/(popup|modal|drawer|popover|tooltip|toast|floating|float|overlay|debug|result-panel|resultpanel|notice|banner)/i.test(name)) {
                return true;
            }
            if (style.position === 'fixed' || style.position === 'sticky') return true;
            const rect = el.getBoundingClientRect();
            if (rect.width < 40 || rect.height < 24) return false;
            if ((style.zIndex && style.zIndex !== 'auto') && (style.position === 'absolute' || style.position === 'fixed' || style.position === 'sticky')) {
                return true;
            }
            return false;
        };
        const walker = document.createTreeWalker(clone, NodeFilter.SHOW_ELEMENT);
        const remove = [];
        while (walker.nextNode()) {
            const el = walker.currentNode;
            if (looksLikeFloatingLayer(el)) {
                remove.push(el);
            }
        }
        remove.forEach((el) => el.remove());
        clone.querySelectorAll('[aria-modal="true"], dialog[open], [role="dialog"]').forEach((el) => el.remove());
        clone.querySelectorAll('script, style, noscript').forEach((el) => el.remove());
        clone.querySelectorAll('.debug-float-btn, [class*="debug-float"], [class*="debug"], [id*="debug"]').forEach((el) => el.remove());
        clone.querySelectorAll('[class*="result-panel"], [class*="resultPanel"]').forEach((el) => el.remove());
        clone.querySelectorAll('[class*="floating"], [class*="float"]').forEach((el) => el.remove());
        clone.querySelectorAll('[aria-label*="debug"], [title*="debug"]').forEach((el) => el.remove());
        const text = (clone.innerText || '').replace(/\\s+/g, ' ').trim();
        return text;
    }""")


def _latest_named_screenshot(name: str, suffix: str = "01-首屏") -> str | None:
    pattern = os.path.join(SCREENSHOT_DIR, f"*{name}*{suffix}*.png")
    files = sorted(_glob.glob(pattern), key=os.path.getmtime, reverse=True)
    return files[0] if files else None


def _interaction_snapshot(page) -> dict:
    return page.evaluate("""() => {
        const root = document.querySelector('#__nuxt > div:first-child') || document.body || document.documentElement;
        const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim();
        const isVisible = (el) => {
            if (!el) return false;
            const style = window.getComputedStyle(el);
            if (!style || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        };
        const countVisible = (selectors) => {
            let total = 0;
            for (const selector of selectors) {
                document.querySelectorAll(selector).forEach((el) => {
                    if (isVisible(el)) total += 1;
                });
            }
            return total;
        };
        const text = norm((root && root.innerText) || document.body.innerText || '');
        return {
            url: location.href,
            title: document.title || '',
            scroll_y: window.scrollY || 0,
            text_len: text.length,
            text_sig: text.slice(0, 3000),
            dialog_count: countVisible([
                '[role="dialog"]', 'dialog[open]', '[aria-modal="true"]',
                '[class*="modal"]', '[class*="drawer"]', '[class*="popup"]', '[class*="popover"]'
            ]),
            expanded_count: countVisible([
                'details[open]', '[aria-expanded="true"]',
                '[class*="help-v2-faq-item--open"]', '[class*="faq-item--open"]',
                '[class*="accordion-item--open"]', '[class*="collapse-item--open"]'
            ]),
            editor_count: countVisible([
                'canvas', '[contenteditable="true"]', '[class*="canvas"]',
                '[class*="editor"]', '[data-editor]', '[data-testid*="editor"]'
            ]),
        };
    }""")


def _classify_interaction(before: dict, after: dict, is_image: bool) -> dict:
    url_changed = before.get("url") != after.get("url")
    dialog_opened = after.get("dialog_count", 0) > before.get("dialog_count", 0)
    expanded_changed = after.get("expanded_count", 0) > before.get("expanded_count", 0)
    editor_opened = after.get("editor_count", 0) > before.get("editor_count", 0)
    text_changed = after.get("text_sig", "") != before.get("text_sig", "")
    scroll_changed = abs(after.get("scroll_y", 0) - before.get("scroll_y", 0)) > 120

    if url_changed:
        effect = "跳转到新页面"
    elif editor_opened:
        effect = "编辑器/画布状态变化"
    elif dialog_opened:
        effect = "弹层/抽屉出现"
    elif expanded_changed:
        effect = "展开/收起状态变化"
    elif text_changed:
        effect = "正文内容变化"
    elif scroll_changed:
        effect = "滚动到新位置"
    else:
        effect = "无变化"

    if is_image:
        passed = url_changed or editor_opened or dialog_opened or expanded_changed or text_changed
        if not passed:
            detail = "试用图点击后没有进入编辑器、弹层或可验证的内容变化"
            if scroll_changed:
                detail = "试用图点击后仅发生滚动，没有进入编辑器/弹层/内容变化"
            issues = [{"severity": "error", "detail": detail}]
        else:
            issues = []
    else:
        passed = effect != "无变化"
        issues = [] if passed else [{
            "severity": "error",
            "detail": "按钮点击后没有出现 URL、弹层、展开、正文或滚动变化",
        }]

    return {
        "passed": passed,
        "effect": effect,
        "issues": issues,
        "url_changed": url_changed,
        "dialog_opened": dialog_opened,
        "expanded_changed": expanded_changed,
        "editor_opened": editor_opened,
        "text_changed": text_changed,
        "scroll_changed": scroll_changed,
    }


def _looks_like_canvas_url(url: str) -> bool:
    url = (url or "").lower()
    return any(token in url for token in (
        "/agent",
        "/create",
        "/editor",
        "/canvas",
        "/edit",
        "pid=",
    ))


def _looks_like_page_error(snapshot: dict) -> bool:
    text = f"{snapshot.get('title', '')} {snapshot.get('text_sig', '')}".lower()
    return any(token in text for token in (
        "404",
        "page not found",
        "not found",
        "server error",
        "something went wrong",
        "error",
        "failed",
    ))


def _detect_404_state(page, http_status: int) -> tuple[bool, dict]:
    if http_status == 404:
        return True, {"reason": "HTTP 404"}

    try:
        snapshot = page.evaluate("""() => {
            const text = (document.body && document.body.innerText ? document.body.innerText : '')
                .replace(/\\s+/g, ' ')
                .trim();
            return {
                title: document.title || '',
                text: text.slice(0, 5000),
            };
        }""")
    except Exception:
        return False, {}

    text = f"{snapshot.get('title', '')} {snapshot.get('text', '')}".lower()
    if any(token in text for token in (
        "404",
        "page not found",
        "not found",
        "page doesn't exist",
    )):
        return True, {
            "reason": "404 marker in page content",
            "title": snapshot.get("title", ""),
            "text": snapshot.get("text", "")[:500],
        }

    return False, {}


def _classify_trial_image_interaction(before: dict, after: dict) -> dict:
    """试用图点击：只接受进入画布页 / 编辑器态。"""
    url_changed = before.get("url") != after.get("url")
    entered_canvas = _looks_like_canvas_url(after.get("url", "")) or after.get("editor_count", 0) > before.get("editor_count", 0)
    page_error = _looks_like_page_error(after)

    if entered_canvas and not page_error:
        return {
            "passed": True,
            "effect": "进入画布页",
            "issues": [],
            "url_changed": url_changed,
            "entered_canvas": True,
            "page_error": False,
        }

    detail = "试用图点击后没有进入画布页"
    if page_error:
        detail = "试用图点击后进入了异常页面或出现报错"
    elif url_changed:
        detail = f"试用图点击后跳转了，但未确认进入画布页: {after.get('url', '')}"

    return {
        "passed": False,
        "effect": "error" if page_error else ("跳转到其他页面" if url_changed else "无变化"),
        "issues": [{"severity": "error", "detail": detail}],
        "url_changed": url_changed,
        "entered_canvas": entered_canvas,
        "page_error": page_error,
    }


def _collect_trial_cards_js() -> str:
    return """() => {
        const root = document.querySelector('#__nuxt > div:first-child')?.children?.[1] || document;
        const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim();
        const isVisible = (el) => {
            if (!el) return false;
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            return rect.width >= 80 && rect.height >= 80 &&
                style && style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                style.opacity !== '0';
        };

        let cards = Array.from(root.querySelectorAll('.seo-try-image-card'));
        if (!cards.length) {
            cards = Array.from(root.querySelectorAll(
                '.try-image-card, [class*="try-image-card"], [class*="tryImageCard"], [class*="try-image"], [class*="TryImage"], [class*="demo-image"]'
            )).map((node) => node.closest('.seo-try-image-card') || node);
        }

        const seen = new Set();
        const items = [];
        for (const card of cards) {
            const cardEl = card && card.closest ? (card.closest('.seo-try-image-card') || card) : card;
            if (!cardEl || seen.has(cardEl)) continue;
            if (!isVisible(cardEl)) continue;
            seen.add(cardEl);
            const rect = cardEl.getBoundingClientRect();
            const img = cardEl.querySelector('img');
            const src = img ? (img.getAttribute('src') || '') : '';
            items.push({
                text: `DemoImage${items.length + 1}: click to try`,
                y: Math.round(rect.top + window.scrollY),
                type: 'image',
                image_order: items.length + 1,
                src: src,
            });
        }
        return items.slice(0, 4);
    }"""


def _click_trial_card_js() -> str:
    return """({order}) => {
        const root = document.querySelector('#__nuxt > div:first-child')?.children?.[1] || document;
        const cards = Array.from(root.querySelectorAll('.seo-try-image-card')).filter((card) => {
            const rect = card.getBoundingClientRect();
            const style = window.getComputedStyle(card);
            return rect.width >= 80 && rect.height >= 80 &&
                style && style.display !== 'none' &&
                style.visibility !== 'hidden' &&
                style.opacity !== '0';
        });
        const idx = Math.max(0, Math.min(cards.length - 1, (order || 1) - 1));
        const card = cards[idx];
        if (!card) return false;
        card.scrollIntoView({behavior: 'instant', block: 'center'});
        card.dispatchEvent(new MouseEvent('mouseenter', {bubbles: true, cancelable: true, view: window}));
        card.dispatchEvent(new MouseEvent('mousemove', {bubbles: true, cancelable: true, view: window}));
        if (typeof card.click === 'function') {
            card.click();
        } else {
            card.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, view: window}));
        }
        return true;
    }"""


def _restore_page_after_interaction(page, before_url: str):
    try:
        if page.url.rstrip("/") == before_url.rstrip("/"):
            page.reload(timeout=30000)
        else:
            page.goto(before_url, timeout=30000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1200)
    except Exception:
        try:
            page.goto(before_url, timeout=30000)
            page.wait_for_timeout(1200)
        except Exception:
            pass


def _discover_faq_items(page) -> list[dict]:
    return page.evaluate("""() => {
        const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim();
        const isVisible = (el) => {
            if (!el) return false;
            const style = window.getComputedStyle(el);
            if (!style || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        };

        const rootHints = [];
        document.querySelectorAll('[class*="faq"], [id*="faq"], [class*="accordion"], [id*="accordion"], [class*="collapse"], [id*="collapse"]').forEach((el) => {
            if (isVisible(el)) rootHints.push(el);
        });
        document.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach((h) => {
            const text = norm(h.textContent).toLowerCase();
            if (/faq|frequently asked|常见问题|问题/.test(text)) {
                let root = h.parentElement;
                for (let i = 0; i < 2 && root; i++) {
                    root = root.parentElement || root;
                }
                if (root && isVisible(root)) rootHints.push(root);
            }
        });

        const roots = rootHints.length ? Array.from(new Set(rootHints)) : [document.body];
        const selectors = [
            '.pk-collapse-header',
            '.pk-collapse-header h3',
            '.pk-collapse-header [class*="title"]',
            'details > summary',
            'summary',
            'button[aria-expanded]',
            '[role="button"][aria-expanded]',
            'button',
            '[role="button"]',
            '[onclick]',
            '[tabindex]',
        ];

        const items = [];
        const seen = new Set();
        for (const root of roots) {
            for (const selector of selectors) {
                root.querySelectorAll(selector).forEach((el) => {
                    if (!isVisible(el)) return;
                    if (el.closest('nav, aside')) return;
                    const text = norm(el.textContent);
                    if (text.length < 5 || text.length > 300) return;
                    const lower = text.toLowerCase();
                    if (lower.includes('upload') || lower.includes('debug')) return;
                    const container = el.closest(
                        'details, [class*="faq-item"], [class*="accordion-item"], [class*="collapse-item"], [class*="pk-collapse"], article, li, section, div'
                    ) || el.parentElement;
                    const meta = ((container && (container.className || '')) + ' ' + (container && (container.id || '')) +
                        ' ' + norm(container ? container.textContent : '').slice(0, 160)).toLowerCase();
                    const questionLike = /\\?$/.test(text) ||
                        /^(how|what|why|can|does|do|is|are|when|where|will|should)\b/i.test(lower) ||
                        /常见问题|问题|问答/.test(text);
                    const looksLikeFaq = questionLike ||
                        /faq|accordion|collapse|question|常见问题|问题/.test(meta) ||
                        /faq|accordion|collapse/.test(lower) ||
                        selector.indexOf('summary') >= 0 ||
                        selector.indexOf('aria-expanded') >= 0;
                    if (!looksLikeFaq) return;
                    if (/nav-item|section__nav|\\bnav\\b|tab|category/.test(meta)) return;
                    const key = text.slice(0, 60);
                    if (seen.has(key)) return;
                    seen.add(key);
                    items.push({ text: text.slice(0, 120), kind: selector });
                });
            }
        }
        return items.slice(0, 12);
    }""")


def _faq_probe(page, question: str, kind: str = "", click: bool = False) -> dict:
    return page.evaluate("""({ needle, kind, doClick }) => {
        const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim();
        const isVisible = (el) => {
            if (!el) return false;
            const style = window.getComputedStyle(el);
            if (!style || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
            const rect = el.getBoundingClientRect();
            return rect.width > 0 && rect.height > 0;
        };
        const target = norm(needle).toLowerCase();

        const rootHints = [];
        document.querySelectorAll('[class*="faq"], [id*="faq"], [class*="accordion"], [id*="accordion"], [class*="collapse"], [id*="collapse"]').forEach((el) => {
            if (isVisible(el)) rootHints.push(el);
        });
        document.querySelectorAll('h1,h2,h3,h4,h5,h6').forEach((h) => {
            const text = norm(h.textContent).toLowerCase();
            if (/faq|frequently asked|常见问题|问题/.test(text)) {
                let root = h.parentElement;
                for (let i = 0; i < 2 && root; i++) {
                    root = root.parentElement || root;
                }
                if (root && isVisible(root)) rootHints.push(root);
            }
        });

        const roots = rootHints.length ? Array.from(new Set(rootHints)) : [document.body];
        const selectors = kind ? [
            '.pk-collapse-header',
            '.pk-collapse-header h3',
            kind,
            'details > summary',
            'summary',
            'button[aria-expanded]',
            '[role="button"][aria-expanded]',
            'button',
            '[role="button"]',
            '[onclick]',
            '[tabindex]',
        ] : [
            'details > summary',
            'summary',
            'button[aria-expanded]',
            '[role="button"][aria-expanded]',
            '.pk-collapse-header',
            '.pk-collapse-header h3',
            'button',
            '[role="button"]',
            '[onclick]',
            '[tabindex]',
        ];

        const score = (text) => {
            if (!target) return 1;
            const lower = text.toLowerCase();
            if (lower === target) return 0;
            if (lower.startsWith(target.slice(0, 30))) return 1;
            if (target.startsWith(lower.slice(0, 30))) return 2;
            if (lower.includes(target.slice(0, 20))) return 3;
            return 99;
        };

        let best = null;
        let bestEl = null;
        let bestScore = 999;
        const seen = new Set();
        for (const root of roots) {
            for (const selector of selectors) {
                root.querySelectorAll(selector).forEach((el) => {
                    if (!isVisible(el)) return;
                    if (el.closest('nav, aside')) return;
                    const text = norm(el.textContent);
                    if (text.length < 5 || text.length > 300) return;
                    const lower = text.toLowerCase();
                    if (lower.includes('upload') || lower.includes('debug')) return;
                    const container = el.closest(
                        'details, [class*="faq-item"], [class*="accordion-item"], [class*="collapse-item"], [class*="pk-collapse"], article, li, section, div'
                    ) || el.parentElement;
                    const meta = ((container && (container.className || '')) + ' ' + (container && (container.id || '')) +
                        ' ' + norm(container ? container.textContent : '').slice(0, 160)).toLowerCase();
                    const questionLike = /\\?$/.test(text) ||
                        /^(how|what|why|can|does|do|is|are|when|where|will|should)\b/i.test(lower) ||
                        /常见问题|问题|问答/.test(text);
                    const looksLikeFaq = questionLike ||
                        /faq|accordion|collapse|question|常见问题|问题/.test(meta) ||
                        /faq|accordion|collapse/.test(lower) ||
                        selector.indexOf('summary') >= 0 ||
                        selector.indexOf('aria-expanded') >= 0;
                    if (!looksLikeFaq) return;
                    if (/nav-item|section__nav|\\bnav\\b|tab|category/.test(meta)) return;
                    const key = text.slice(0, 60);
                    if (seen.has(key)) return;
                    seen.add(key);
                    const currentScore = score(text);
                    if (currentScore >= 99) return;
                    const candidate = {
                        found: true,
                        text: text.slice(0, 120),
                        selector: selector,
                        container_class: container && container.className ? String(container.className).slice(0, 120) : '',
                        control_class: el.className ? String(el.className).slice(0, 120) : '',
                        header_class: (el.closest('.pk-collapse-header') && el.closest('.pk-collapse-header').className) ? String(el.closest('.pk-collapse-header').className).slice(0, 120) : '',
                        expanded: (el.getAttribute('aria-expanded') === 'true') ||
                                  (container && container.tagName === 'DETAILS' && container.open) ||
                                  /(?:^|\\s)(open|active|expanded)(?:\\s|$)/i.test(((container && container.className) || '') + ' ' + (el.className || '')),
                        answer_visible: !!(container && (() => {
                            const answer = container.querySelector(
                                '[class*="answer"], [role="region"], [data-state="open"], [class*="content"], [class*="panel"]'
                            );
                            if (!answer) return false;
                            const style = window.getComputedStyle(answer);
                            if (!style || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') return false;
                            const rect = answer.getBoundingClientRect();
                            return rect.width > 0 && rect.height > 0;
                        })()),
                        answer_text: container ? norm(container.textContent).slice(0, 160) : '',
                    };
                    if (!best || currentScore < bestScore || (currentScore === bestScore && candidate.text.length < best.text.length)) {
                        best = candidate;
                        bestEl = el;
                        bestScore = currentScore;
                    }
                });
            }
        }

        if (!best) return { found: false };
        if (doClick && bestEl) {
            const clickRoot = bestEl.closest('.pk-collapse-header') || bestEl;
            clickRoot.scrollIntoView({ behavior: 'instant', block: 'center' });
            const rect = clickRoot.getBoundingClientRect();
            const points = [
                { x: Math.max(rect.left + 8, rect.right - 12), y: rect.top + rect.height / 2 },
                { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 },
            ];
            for (const point of points) {
                const target = document.elementFromPoint(point.x, point.y) || clickRoot;
                const opts = {
                    bubbles: true,
                    cancelable: true,
                    view: window,
                    clientX: point.x,
                    clientY: point.y,
                    button: 0,
                    buttons: 1,
                    pointerId: 1,
                    pointerType: 'mouse',
                    isPrimary: true,
                };
                try { target.dispatchEvent(new PointerEvent('pointerdown', opts)); } catch (e) {}
                try { target.dispatchEvent(new PointerEvent('pointerup', opts)); } catch (e) {}
                target.dispatchEvent(new MouseEvent('mousedown', opts));
                target.dispatchEvent(new MouseEvent('mouseup', opts));
                target.dispatchEvent(new MouseEvent('click', opts));
            }
            best.clicked = true;
        } else {
            best.clicked = false;
        }
        return best;
    }""", {"needle": question, "kind": kind or "", "doClick": click})


# ═══════════════════════════════════════════════════════════════
# 导航辅助
# ═══════════════════════════════════════════════════════════════

def _navigate_and_wait(page, base_url: str, path: str, lazy_scroll: bool = True) -> int:
    """Navigate to SEO page, wait for render. Returns HTTP status code."""
    url = f"{base_url}{path}"
    response = page.goto(url, timeout=60000)
    http_status = response.status if response else 0
    try:
        page.wait_for_load_state("networkidle", timeout=30000)
    except Exception:
        pass
    page.wait_for_timeout(3000)

    if lazy_scroll:
        _warm_up_lazy_content(page, exhaustive=False)

    return http_status


# ═══════════════════════════════════════════════════════════════
# 测试类
# ═══════════════════════════════════════════════════════════════

@allure.epic("SEO新页面检测")
@allure.feature("规则 + direct LLM 覆盖")
class TestSEONewPages:
    """SEO 新页面自动化检测 — 规则层保底，LLM 层补语义。"""

    @allure.title("[新页面批次] SEO新页面检测（PC + Mobile）")
    @pytest.mark.seo_new
    def test_seo_new_page(self, browser, session_context, base_url):
        allure.dynamic.parameter("device_order", "PC -> Mobile")
        allure.dynamic.parameter("page_count", len(SEO_PAGES))

        batch_results = []
        desktop_context = browser.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
        mobile_context = browser.new_context(
            viewport={"width": 375, "height": 812},
            screen={"width": 375, "height": 812},
            locale="en-US",
            user_agent=MOBILE_USER_AGENT,
            device_scale_factor=3,
            is_mobile=True,
            has_touch=True,
            color_scheme="light",
        )

        def _finalize_case(device: str, name: str, page_path: str, url: str,
                           page_meta: dict, l1: dict, l2: dict, l3: dict,
                           errors: list[dict], warnings: list[dict],
                           screenshot_path: str | None) -> dict:
            with allure.step(f"{device} / {name} - 可视摘要卡片"):
                card_html = build_card_html(
                    page_name=f"{device}-{name}",
                    url=url,
                    screenshot_path=screenshot_path,
                    l1_result=l1,
                    l2_result=l2,
                    l3_result=l3,
                    page_meta=page_meta,
                )
                allure.attach(card_html, name=f"可视摘要卡片-{device}-{name}",
                              attachment_type=allure.attachment_type.HTML)

            summary_lines = [
                f"Device: {device}",
                f"URL: {url}",
                f"Path: {page_path}",
                f"Title: {page_meta.get('title', 'N/A')[:80]}",
                f"H1: {page_meta.get('h1s', ['N/A'])[0][:80] if page_meta.get('h1s') else 'N/A'}",
                "",
                f"Error: {len(errors)}, Warning: {len(warnings)}",
            ]
            if errors:
                summary_lines.append("\n=== Errors ===")
                for e in errors:
                    summary_lines.append(f"  [{e.get('type','?')}] {e.get('detail','')[:150]}")
            if warnings:
                summary_lines.append("\n=== Warnings ===")
                for w in warnings:
                    summary_lines.append(f"  [{w.get('type','?')}] {w.get('detail','')[:150]}")

            allure.attach(
                "\n".join(summary_lines),
                name=f"检测汇总-{device}-{name}",
                attachment_type=allure.attachment_type.TEXT,
            )

            return {
                "device": device,
                "name": name,
                "url": url,
                "page_path": page_path,
                "lang": _detect_lang_prefix(page_path) or "en",
                "title": page_meta.get("title", ""),
                "h1": page_meta.get("h1s", [""])[0] if page_meta.get("h1s") else "",
                "errors": list(errors),
                "warnings": list(warnings),
                "screenshot_path": screenshot_path,
                "passed": not errors,
            }

        def _run_pc_case(entry) -> dict:
            name = _page_name(entry)
            page_path = _entry_path(entry)
            url = f"{base_url}{page_path}"
            lang_prefix = _detect_lang_prefix(urlparse(url).path)
            desktop_page = desktop_context.new_page()
            login_page = session_context.new_page()
            page_meta = {}
            l1 = {"errors": [], "warnings": []}
            l2 = {"errors": [], "warnings": []}
            l3 = {"errors": [], "warnings": []}
            errors: list[dict] = []
            warnings: list[dict] = []
            screenshot_path = None
            try:
                with allure.step(f"PC / {name} - 页面准备"):
                    http_status = _navigate_and_wait(desktop_page, base_url, page_path)
                    if http_status == 500 and _restart_seo_backend(browser):
                        desktop_page.wait_for_timeout(3000)
                        http_status = _navigate_and_wait(desktop_page, base_url, page_path)
                    is_404, not_found_info = _detect_404_state(desktop_page, http_status)
                    if is_404:
                        page_meta = {
                            "title": not_found_info.get("title", ""),
                            "h1s": [],
                            "h2s": [],
                            "meta_description": "",
                            "cta_buttons": [],
                            "internal_links": [],
                            "body_chars": len(not_found_info.get("text", "")),
                        }
                        errors.append({
                            "severity": "error",
                            "type": "accessible",
                            "detail": "页面检测到 404 / Page Not Found，已直接判定失败并跳过后续检测",
                        })
                        allure.attach(
                            json.dumps({
                                "http_status": http_status,
                                "title": not_found_info.get("title", ""),
                                "body_text": not_found_info.get("text", "")[:1000],
                                "reason": not_found_info.get("reason", "404"),
                            }, ensure_ascii=False, indent=2),
                            name=f"PC / {name} - 404 早退",
                            attachment_type=allure.attachment_type.JSON,
                        )
                        return _finalize_case("PC", name, page_path, url, page_meta, l1, l2, l3, errors, warnings, screenshot_path)
                    screenshot_path = _capture_screenshot(desktop_page, f"seo-new-pc-{name}-01-首屏")
                    verify_seo_links(desktop_page, base_url, page_path)
                    _navigate_and_wait(login_page, base_url, page_path, lazy_scroll=True)
                    page_meta = _collect_page_meta(desktop_page, include_internal_links=True)

                with allure.step(f"PC / {name} - Layer 1"):
                    l1 = self._layer1_check(login_page, name, lang_prefix, http_status=http_status, device="pc")
                    errors.extend(l1["errors"])
                    warnings.extend(l1["warnings"])

                with allure.step(f"PC / {name} - Layer 2"):
                    l2 = self._layer2_check(desktop_page, url, page_meta)
                    errors.extend(l2["errors"])
                    warnings.extend(l2["warnings"])

                with allure.step(f"PC / {name} - Layer 3"):
                    l3 = self._layer3_check(
                        page_meta, url, lang_prefix, name,
                        screenshot_path=screenshot_path, focus="desktop",
                        device_label="PC", hints=_build_review_hints(page_path, page_meta, entry),
                    )
                    errors.extend(l3["errors"])
                    warnings.extend(l3["warnings"])

                with allure.step(f"PC / {name} - Layer 4"):
                    if _entry_semantic_review(entry):
                        reviewer = create_reviewer()
                        if reviewer and screenshot_path:
                            review_hints = _build_review_hints(page_path, page_meta, entry)
                            page_info = {
                                "url": url,
                                "lang": lang_prefix or "en",
                                "title": page_meta.get("title", ""),
                                "h1s": page_meta.get("h1s", []),
                            }
                            review_result = reviewer.review(screenshot_path, page_info, hints=review_hints, focus="desktop")
                            allure.attach(
                                json.dumps(review_result, ensure_ascii=False, indent=2),
                                name=f"direct-llm-语义复核结果-PC-{name}",
                                attachment_type=allure.attachment_type.JSON,
                            )
                            issues = review_result.get("issues", [])
                            if not review_result.get("passed", True):
                                if not issues:
                                    warnings.append({
                                        "severity": "warning",
                                        "type": "direct_llm",
                                        "detail": "direct LLM semantic review returned passed=false but no issues",
                                    })
                                for issue in issues:
                                    if isinstance(issue, dict):
                                        severity = issue.get("severity", "warning")
                                        detail = issue.get("detail", "")
                                    else:
                                        severity = "warning"
                                        detail = str(issue)
                                    if severity == "error":
                                        errors.append({
                                            "severity": "error",
                                            "type": "direct_llm",
                                            "detail": detail[:150] or "direct LLM semantic review failed",
                                        })
                                    else:
                                        warnings.append({
                                            "severity": "warning",
                                            "type": "direct_llm",
                                            "detail": detail[:150] or "direct LLM semantic review warning",
                                        })
                            else:
                                allure.attach(
                                    review_result.get("summary", "OK"),
                                    name=f"direct-llm-语义复核摘要-PC-{name}",
                                    attachment_type=allure.attachment_type.TEXT,
                                )
                        else:
                            allure.attach(
                                "跳过 direct LLM 语义复核：未找到首屏截图或审查器不可用。",
                                name=f"direct-llm-语义复核-跳过-PC-{name}",
                                attachment_type=allure.attachment_type.TEXT,
                            )
                    else:
                        allure.attach(
                            "当前页面显式关闭 semantic_review，仅执行规则层与静态 AI 审查。",
                            name=f"direct-llm-语义复核-未启用-PC-{name}",
                            attachment_type=allure.attachment_type.TEXT,
                        )

                return _finalize_case("PC", name, page_path, url, page_meta, l1, l2, l3, errors, warnings, screenshot_path)
            except Exception as exc:
                tb = traceback.format_exc()
                allure.attach(tb, name=f"PC-{name}-exception", attachment_type=allure.attachment_type.TEXT)
                errors.append({"severity": "error", "type": "exception", "detail": str(exc)[:200]})
                return _finalize_case("PC", name, page_path, url, page_meta, l1, l2, l3, errors, warnings, screenshot_path)
            finally:
                try:
                    login_page.close()
                except Exception:
                    pass
                try:
                    desktop_page.close()
                except Exception:
                    pass

        def _run_mobile_case(entry) -> dict:
            name = _page_name(entry)
            page_path = _entry_path(entry)
            url = f"{base_url}{page_path}"
            lang_prefix = _detect_lang_prefix(urlparse(url).path)
            page = mobile_context.new_page()
            page_meta = {}
            l1 = {"errors": [], "warnings": []}
            l2 = {"errors": [], "warnings": [], "checks": {"skipped": True}}
            l3 = {"errors": [], "warnings": []}
            errors: list[dict] = []
            warnings: list[dict] = []
            screenshot_path = None
            try:
                with allure.step(f"Mobile / {name} - 页面准备"):
                    http_status = _navigate_and_wait(page, base_url, page_path)
                    if http_status == 500 and _restart_seo_backend(browser):
                        page.wait_for_timeout(3000)
                        http_status = _navigate_and_wait(page, base_url, page_path)
                    _dismiss_login_popup_if_present(page)
                    is_404, not_found_info = _detect_404_state(page, http_status)
                    if is_404:
                        page_meta = {
                            "title": not_found_info.get("title", ""),
                            "h1s": [],
                            "h2s": [],
                            "meta_description": "",
                            "cta_buttons": [],
                            "internal_links": [],
                            "body_chars": len(not_found_info.get("text", "")),
                        }
                        errors.append({
                            "severity": "error",
                            "type": "accessible",
                            "detail": "页面检测到 404 / Page Not Found，已直接判定失败并跳过后续检测",
                        })
                        allure.attach(
                            json.dumps({
                                "http_status": http_status,
                                "title": not_found_info.get("title", ""),
                                "body_text": not_found_info.get("text", "")[:1000],
                                "reason": not_found_info.get("reason", "404"),
                            }, ensure_ascii=False, indent=2),
                            name=f"Mobile / {name} - 404 早退",
                            attachment_type=allure.attachment_type.JSON,
                        )
                        return _finalize_case("Mobile", name, page_path, url, page_meta, l1, l2, l3, errors, warnings, screenshot_path)
                    page_meta = _collect_page_meta(page, include_internal_links=False)

                with allure.step(f"Mobile / {name} - Layer 1"):
                    l1 = self._layer1_check(page, name, lang_prefix, http_status=http_status, device="mobile")
                    errors.extend(l1["errors"])
                    warnings.extend(l1["warnings"])

                with allure.step(f"Mobile / {name} - 全页 AI 审查"):
                    lazy_stats = _warm_up_lazy_content(page, exhaustive=True)
                    allure.attach(
                        json.dumps(lazy_stats, ensure_ascii=False, indent=2),
                        name=f"Mobile / {name} - 截图前懒加载预热",
                        attachment_type=allure.attachment_type.JSON,
                    )
                    screenshot_path = _capture_screenshot(page, f"seo-new-mobile-{name}-整页", full_page=True)
                    mobile_hints = _build_review_hints(page_path, page_meta, entry) + (
                        "\n\n移动端审查范围：只看整页布局、按钮/试用图可见性、点击后页面态和全页视觉完整性，不检查内链、FAQ 文本或文案润色。"
                    )
                    l3 = self._layer3_check(
                        page_meta, url, lang_prefix, name,
                        screenshot_path=screenshot_path, focus="mobile",
                        device_label="Mobile", hints=mobile_hints,
                    )
                    errors.extend(l3["errors"])
                    warnings.extend(l3["warnings"])

                return _finalize_case("Mobile", name, page_path, url, page_meta, l1, l2, l3, errors, warnings, screenshot_path)
            except Exception as exc:
                tb = traceback.format_exc()
                allure.attach(tb, name=f"Mobile-{name}-exception", attachment_type=allure.attachment_type.TEXT)
                errors.append({"severity": "error", "type": "exception", "detail": str(exc)[:200]})
                return _finalize_case("Mobile", name, page_path, url, page_meta, l1, l2, l3, errors, warnings, screenshot_path)
            finally:
                try:
                    page.close()
                except Exception:
                    pass

        try:
            for entry in SEO_PAGES:
                batch_results.append(_run_pc_case(entry))

            for entry in SEO_PAGES:
                batch_results.append(_run_mobile_case(entry))
        finally:
            try:
                desktop_context.close()
            except Exception:
                pass
            try:
                mobile_context.close()
            except Exception:
                pass

        failed_cases = [item for item in batch_results if item.get("errors")]
        passed_cases = [item for item in batch_results if not item.get("errors")]
        batch_summary_lines = [
            "Batch: PC -> Mobile",
            f"Total cases: {len(batch_results)}",
            f"Passed cases: {len(passed_cases)}",
            f"Failed cases: {len(failed_cases)}",
        ]
        if failed_cases:
            batch_summary_lines.append("")
            batch_summary_lines.append("Failed case list:")
            for item in failed_cases:
                batch_summary_lines.append(
                    f"- [{item.get('device', '?')}] {item.get('name', '?')} => {item.get('page_path', '')}"
                )
        allure.attach(
            "\n".join(batch_summary_lines),
            name="批次检测汇总",
            attachment_type=allure.attachment_type.TEXT,
        )

        if failed_cases:
            report_path = _write_batch_bug_report("SEO新页面检测批次", batch_results)
            allure.attach(
                report_path.read_text(encoding="utf-8"),
                name="批次Bug单Markdown",
                attachment_type=allure.attachment_type.TEXT,
            )
            allure.attach(
                f"批次 Bug 单已生成: {report_path}",
                name="批次Bug单路径",
                attachment_type=allure.attachment_type.TEXT,
            )
            error_lines = []
            for item in failed_cases[:10]:
                issue_bits = []
                for err in item.get("errors", [])[:3]:
                    issue_bits.append(f"[{err.get('type','?')}] {err.get('detail','')[:80]}")
                error_lines.append(
                    f"  [{item.get('device','?')}] {item.get('name','?')}: " + "; ".join(issue_bits)
                )
            error_list = "\n".join(error_lines)
            pytest.fail(
                f"SEO新页面检测批次发现 {len(failed_cases)} 个有问题的页面/设备组合:\n{error_list}"
            )

        allure.dynamic.description(
            f"规则 + AI 检测完成: 全部通过（PC {len(SEO_PAGES)} 页 + Mobile {len(SEO_PAGES)} 页）"
        )

    # ═══════════════════════════════════════════════════════════
    # Layer 1: 不变量检查（逐项展开）
    # ═══════════════════════════════════════════════════════════

    def _layer1_check(self, page, name: str, lang_prefix: str, http_status: int = 0, device: str = "pc") -> dict:
        errors = []
        warnings = []
        checks = {}
        btn_results = []
        resource_stats = {}

        # --- 1.1 页面可访问 ---
        with allure.step("1.1 页面可访问"):
            body_text = page.locator("body").inner_text()
            title_text = page.title()

            # 检查 404 标记
            is_404 = any(kw in body_text.lower() for kw in [
                "page not found", "404", "not found", "page doesn't exist",
                "seite nicht gefunden", "page introuvable", "pagina no encontrada"
            ]) or any(kw in title_text.lower() for kw in [
                "page not found", "404", "not found"
            ])

            # 检查 HTTP status
            http_ok = http_status == 200 or http_status == 304
            if http_status == 0:
                http_label = "unknown (no response object)"
            else:
                http_label = str(http_status)

            l1_1_text = (
                f"HTTP Status: {http_label}\n"
                f"页面 Title: {title_text[:100]}\n"
                f"Body 文本长度: {len(body_text)} 字符\n"
                f"404 标记检测: {'是' if is_404 else '否'}\n"
                f"当前 URL: {page.url}"
            )
            allure.attach(l1_1_text, name="可访问性详情", attachment_type=allure.attachment_type.TEXT)

            accessible_passed = len(body_text) > 50 and http_ok and not is_404
            checks["accessible"] = {
                "passed": accessible_passed,
                "detail": f"HTTP={http_label}, Body={len(body_text)} chars, Title={title_text[:40]}",
            }

            if not http_ok:
                errors.append({
                    "severity": "error", "type": "accessible",
                    "detail": f"HTTP {http_label} — 页面返回非 200 状态码",
                })
            elif is_404:
                errors.append({
                    "severity": "error", "type": "accessible",
                    "detail": "页面检测到 404/Page Not Found 标记",
                })
            elif len(body_text) <= 50:
                errors.append({
                    "severity": "error", "type": "accessible",
                    "detail": f"页面内容过少（{len(body_text)}字符），可能未正常渲染",
                })

        # --- 1.2 资源加载 ---
        with allure.step("1.2 资源加载"):
            # 安装网络响应监听
            page.evaluate("""() => {
                window.__seo_failed_resources = [];
                window.__seo_resource_count = {total: 0, img: 0, script: 0, css: 0, other: 0};
            }""")

            def _on_response(response):
                try:
                    resource_type = response.request.resource_type
                    status = response.status
                    page.evaluate("""(r) => {
                        window.__seo_resource_count.total++;
                        window.__seo_resource_count[r.type] = (window.__seo_resource_count[r.type] || 0) + 1;
                        if (r.status >= 400 && r.status < 600) {
                            window.__seo_failed_resources.push({
                                url: r.url.slice(-100),
                                status: r.status,
                                type: r.type
                            });
                        }
                    }""", {"url": response.url, "status": status, "type": resource_type})
                except Exception:
                    pass

            page.on("response", _on_response)

            # 逐屏预热，触发中间区域的懒加载/延迟渲染资源。
            lazy_stats = _warm_up_lazy_content(page, exhaustive=str(device).lower() == "mobile")

            page.remove_listener("response", _on_response)

            # 收集结果
            res_stats = page.evaluate("""() => {
                var broken = [];
                var emptySrc = [];
                function parentInfo(img) {
                    var node = img.parentElement;
                    var chosen = null;
                    for (var i = 0; i < 6 && node; i++, node = node.parentElement) {
                        var r = node.getBoundingClientRect();
                        var text = (node.textContent || '').replace(/\\s+/g, ' ').trim();
                        if (r.width > 80 && r.height > 80) {
                            chosen = {
                                text: text.slice(0, 140),
                                top: Math.round(r.top + window.scrollY),
                                width: Math.round(r.width),
                                height: Math.round(r.height),
                                className: String(node.className || '').slice(0, 120)
                            };
                            if (text.length > 12) break;
                        }
                    }
                    return chosen || {text: '', top: 0, width: 0, height: 0, className: ''};
                }
                document.querySelectorAll('img').forEach(function(img) {
                    var src = img.currentSrc || img.src || img.getAttribute('src') || '';
                    if (img.complete && img.naturalWidth === 0 && img.naturalHeight === 0) {
                        var rect = img.getBoundingClientRect();
                        var parent = parentInfo(img);
                        var hasBusinessParent = parent.width > 80 && parent.height > 80 && parent.text.length > 12;
                        if (rect.width > 10 || rect.height > 10 || hasBusinessParent) {
                            var item = {
                                src: src ? src.slice(-100) : '',
                                alt: (img.getAttribute('alt') || '').slice(0, 120),
                                parent_text: parent.text,
                                parent_top: parent.top,
                                parent_size: parent.width + 'x' + parent.height,
                                parent_class: parent.className
                            };
                            if (!src) {
                                emptySrc.push(item);
                            } else {
                                broken.push(item);
                            }
                        }
                    }
                });
                return {
                    resource_counts: window.__seo_resource_count || {},
                    failed_resources: (window.__seo_failed_resources || []).slice(0, 30),
                    broken_images: broken.slice(0, 15),
                    empty_src_images: emptySrc.slice(0, 15)
                };
            }""")

            total_req = res_stats.get("resource_counts", {}).get("total", 0)
            img_count = res_stats.get("resource_counts", {}).get("img", 0)
            script_count = res_stats.get("resource_counts", {}).get("script", 0)
            css_count = res_stats.get("resource_counts", {}).get("css", 0)
            failed = res_stats.get("failed_resources", [])
            broken_imgs = res_stats.get("broken_images", [])
            empty_src_imgs = res_stats.get("empty_src_images", [])

            # 过滤第三方无关资源
            IGNORE_DOMAINS = ["google", "facebook", "analytics", "gtm", "pixel",
                              "clarity", "hotjar", "doubleclick", "googletagmanager"]
            critical_failed = [
                f for f in failed
                if not any(d in f.get("url", "").lower() for d in IGNORE_DOMAINS)
            ]

            detail = (
                f"资源总数: {total_req} (img={img_count}, script={script_count}, css={css_count}, other={total_req - img_count - script_count - css_count})\n"
                f"失败资源(4xx/5xx): 共 {len(failed)} 个, 其中关键 {len(critical_failed)} 个（排除第三方）\n"
                f"图片加载失败(naturalWidth=0): {len(broken_imgs)} 张\n"
                f"业务区域空 src 图片: {len(empty_src_imgs)} 张\n"
                f"懒加载预热: steps={lazy_stats.get('steps')}, height={lazy_stats.get('height')}, step={lazy_stats.get('step')}\n"
            )
            if critical_failed:
                detail += "\n关键失败资源:\n"
                for r in critical_failed[:10]:
                    detail += f"  [{r['status']}] {r['type']}: {r.get('url', r.get('url','?'))}\n"
            if broken_imgs:
                detail += "\n加载失败的图片:\n"
                for img in broken_imgs[:5]:
                    detail += f"  {img.get('src') or img.get('alt') or img.get('parent_text')}\n"
            if empty_src_imgs:
                detail += "\n业务区域空 src 图片:\n"
                for img in empty_src_imgs[:8]:
                    detail += (
                        f"  top={img.get('parent_top')} size={img.get('parent_size')} "
                        f"alt={img.get('alt') or '-'} parent={img.get('parent_text') or '-'}\n"
                    )

            allure.attach(detail, name="资源加载详情", attachment_type=allure.attachment_type.TEXT)

            checks["resources"] = {
                "passed": len(critical_failed) <= 3 and len(broken_imgs) <= 2 and len(empty_src_imgs) == 0,
                "detail": (
                    f"total={total_req}, failed={len(critical_failed)}, "
                    f"broken_imgs={len(broken_imgs)}, empty_src_imgs={len(empty_src_imgs)}"
                ),
            }
            resource_stats = {
                "total": total_req, "img": img_count, "script": script_count,
                "css": css_count, "failed": len(critical_failed),
                "broken_imgs": len(broken_imgs), "empty_src_imgs": len(empty_src_imgs),
            }

            if len(critical_failed) > 3 or len(broken_imgs) > 2 or empty_src_imgs:
                errors.append({
                    "severity": "error", "type": "resources",
                    "detail": (
                        f"关键资源失败 {len(critical_failed)} 个, 图片加载失败 {len(broken_imgs)} 张, "
                        f"业务区域空 src 图片 {len(empty_src_imgs)} 张"
                    ),
                })
            elif critical_failed or broken_imgs:
                warnings.append({
                    "severity": "warning", "type": "resources",
                    "detail": f"关键资源失败 {len(critical_failed)} 个, 图片加载失败 {len(broken_imgs)} 张",
                })

        # --- 1.3 正文 CTA + 试用图交互 ---
        with allure.step("1.3 正文 CTA + 试用图交互"):
            EXCLUDE_BTN = {"sign up", "log in", "sign in", "register", "login",
                           "english", "language", "debug", "upload"}

            mobile_mode = str(device).lower() == "mobile"

            btn_info = page.evaluate("""({exclude, mobile}) => {
                var layout = document.querySelector('#__nuxt > div:first-child');
                var main = (layout && layout.children.length >= 2) ? layout.children[1] : null;
                var root = main || document;
                var items = [];

                // 1. 正文 CTA 按钮（排除左侧功能栏/导航栏）
                var BODY_X_MIN = mobile ? 0 : Math.max(260, Math.round(window.innerWidth * 0.18));
                root.querySelectorAll('button:not([disabled]), [role="button"]').forEach(function(b) {
                    var txt = (b.textContent || '').trim();
                    var rect = b.getBoundingClientRect();
                    if (txt.length > 1 && rect.width > 20 && rect.height > 10 && rect.left >= BODY_X_MIN) {
                        var lower = txt.toLowerCase();
                        if (!exclude.some(function(kw) { return lower.includes(kw); })) {
                            items.push({
                                text: txt.slice(0, 60),
                                y: Math.round(rect.top + window.scrollY),
                                type: 'button'
                            });
                        }
                    }
                });

                // 2. 试用图卡片（seo-try-image-card 等）
                var trialCards = Array.from(root.querySelectorAll('.seo-try-image-card'));
                if (!trialCards.length) {
                    trialCards = Array.from(root.querySelectorAll(
                        '.try-image-card, [class*="try-image-card"], [class*="tryImageCard"],'
                        + '[class*="try-image"], [class*="TryImage"], [class*="demo-image"]'
                    )).map(function(node) {
                        return node.closest('.seo-try-image-card') || node;
                    });
                }
                var seenCards = new Set();
                var order = 0;
                for (var ci = 0; ci < trialCards.length; ci++) {
                    var card = trialCards[ci];
                    if (!card || seenCards.has(card)) continue;
                    seenCards.add(card);
                    var rect = card.getBoundingClientRect();
                    var style = window.getComputedStyle(card);
                    if (rect.width < 80 || rect.height < 80) continue;
                    if (!style || style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') continue;
                    order++;
                    items.push({
                        text: 'DemoImage' + order + ': click to try',
                        y: Math.round(rect.top + window.scrollY),
                        type: 'image',
                        image_order: order
                    });
                }

                // 去重（同文本按钮只保留一个，试用图按卡片顺序保留）
                var seen = new Set();
                var result = [];
                for (var i = 0; i < items.length; i++) {
                    if (items[i].type === 'image' || !seen.has(items[i].text)) {
                        seen.add(items[i].text);
                        result.push(items[i]);
                    }
                }
                return result;
            }""", {"exclude": list(EXCLUDE_BTN), "mobile": mobile_mode})

            # 分开取样：按钮只抽少量，试用图尽量全点，避免被按钮挤掉
            button_items = []
            image_items = []
            seen_buttons = set()
            seen_images = set()
            for b in btn_info:
                if b.get("type") == "image":
                    if b["text"] not in seen_images:
                        seen_images.add(b["text"])
                        image_items.append(b)
                else:
                    if b["text"] not in seen_buttons:
                        seen_buttons.add(b["text"])
                        button_items.append(b)

            button_items = button_items[:4]
            image_items = image_items[:4]
            sample_btns = button_items + image_items

            btn_count = len(button_items)
            img_count = len(image_items)
            allure.attach(
                f"发现 {len(btn_info)} 个交互元素（{btn_count} 正文CTA + {img_count} 试用图），采样 {len(sample_btns)} 个\n\n" +
                "\n".join(f"  [{i+1}] [{b.get('type','btn')}] {b['text'][:60]}" for i, b in enumerate(sample_btns)),
                name="正文CTA+试用图清单",
                attachment_type=allure.attachment_type.TEXT,
            )

            btn_results = []
            failed_count = 0
            for idx, bi in enumerate(sample_btns):
                btn_text_short = bi["text"][:30].replace("/", "_")
                elem_type = "试用图" if bi.get("type") == "image" else "按钮"
                with allure.step(f"{elem_type} [{idx+1}/{len(sample_btns)}]: {btn_text_short}"):
                    before_url = page.url
                    before_state = _interaction_snapshot(page)

                    # 截图前：滚动到按钮位置
                    try:
                        page.evaluate("""(text) => {
                            var btns = document.querySelectorAll('button:not([disabled]), [role="button"]');
                            for (var i = 0; i < btns.length; i++) {
                                var t = (btns[i].textContent || '').trim();
                                if (t === text || t.slice(0, 30) === text.slice(0, 30)) {
                                    btns[i].scrollIntoView({behavior: 'instant', block: 'center'});
                                    return;
                                }
                            }
                        }""", bi["text"])
                        page.wait_for_timeout(300)
                    except Exception:
                        pass

                    # 截图：点击前
                    png_before = None
                    try:
                        png_before = page.screenshot(full_page=False)
                        allure.attach(png_before, name=f"btn-{idx+1:02d}-before",
                                      attachment_type=allure.attachment_type.PNG)
                    except Exception:
                        pass

                    # 点击（区分按钮 vs 试用图）
                    effect = ""
                    png_after = None
                    console_errors_during = []
                    is_image = (bi.get("type") == "image")
                    click_error = ""
                    try:
                        def _on_console(msg):
                            if msg.type == "error":
                                console_errors_during.append(msg.text[:120])

                        page.on("console", _on_console)

                        if is_image:
                            # 试用图：按卡片顺序命中第 N 张，且只点顶层卡片本身
                            page.evaluate(_click_trial_card_js(), {"order": bi.get("image_order", 1)})
                        else:
                            # 常规按钮：dispatchEvent
                            page.evaluate("""(text) => {
                                var btns = document.querySelectorAll('button:not([disabled]), [role="button"]');
                                for (var i = 0; i < btns.length; i++) {
                                    var t = (btns[i].textContent || '').trim();
                                    if (t === text || t.slice(0, 30) === text.slice(0, 30)) {
                                        btns[i].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                                        return;
                                    }
                                }
                            }""", bi["text"])

                        page.wait_for_timeout(1500)
                        try:
                            page.wait_for_load_state("networkidle", timeout=5000)
                        except Exception:
                            pass
                        click_ok = True

                    except Exception as e:
                        click_error = f"点击异常: {str(e)[:120]}"
                        effect = click_error[:60]
                        png_after = None
                        click_ok = False
                    finally:
                        try:
                            page.remove_listener("console", _on_console)
                        except Exception:
                            pass

                    # 截图：点击后
                    after_state = None
                    try:
                        png_after = page.screenshot(full_page=False)
                        allure.attach(png_after, name=f"btn-{idx+1:02d}-after",
                                      attachment_type=allure.attachment_type.PNG)
                    except Exception:
                        pass

                    if click_ok:
                        try:
                            after_state = _interaction_snapshot(page)
                        except Exception as e:
                            after_state = {
                                "url": page.url,
                                "title": page.title(),
                                "scroll_y": page.evaluate("window.scrollY"),
                                "text_len": 0,
                                "text_sig": "",
                                "dialog_count": 0,
                                "expanded_count": 0,
                                "editor_count": 0,
                            }
                            click_error = click_error or f"状态采集异常: {str(e)[:80]}"

                    interaction = {
                        "passed": False,
                        "effect": effect or "无变化",
                        "issues": [{"severity": "error", "detail": click_error}] if click_error else [],
                    }
                    if click_ok and after_state is not None:
                        interaction = _classify_trial_image_interaction(before_state, after_state) if is_image else _classify_interaction(before_state, after_state, is_image)
                    effect = interaction["effect"]
                    interaction_passed = interaction["passed"]
                    interaction_issues = list(interaction.get("issues", []))

                    allure.attach(
                        json.dumps({
                            "text": bi["text"][:80],
                            "type": bi.get("type", "button"),
                            "passed": interaction_passed,
                            "effect": effect,
                            "before": {
                                "url": before_state.get("url"),
                                "title": before_state.get("title"),
                                "scroll_y": before_state.get("scroll_y"),
                                "dialog_count": before_state.get("dialog_count"),
                                "expanded_count": before_state.get("expanded_count"),
                                "editor_count": before_state.get("editor_count"),
                            },
                            "after": {
                                "url": (after_state or {}).get("url"),
                                "title": (after_state or {}).get("title"),
                                "scroll_y": (after_state or {}).get("scroll_y"),
                                "dialog_count": (after_state or {}).get("dialog_count"),
                                "expanded_count": (after_state or {}).get("expanded_count"),
                                "editor_count": (after_state or {}).get("editor_count"),
                            },
                            "issues": interaction_issues,
                        }, ensure_ascii=False, indent=2),
                        name=f"btn-{idx+1:02d}-状态判定",
                        attachment_type=allure.attachment_type.TEXT,
                    )

                    btn_results.append({
                        "text": bi["text"],
                        "effect": effect,
                        "type": bi.get("type", "button"),
                        "passed": interaction_passed,
                        "issues": interaction_issues,
                    })

                    for issue in interaction_issues:
                        if isinstance(issue, str):
                            detail = issue[:120]
                            sev = "warning"
                        else:
                            detail = issue.get("detail", str(issue))[:120]
                            sev = issue.get("severity", "warning")
                        if sev == "error":
                            errors.append({"severity": "error", "type": "btn_interact", "detail": detail})
                        else:
                            warnings.append({"severity": "warning", "type": "btn_interact", "detail": detail})

                    if not interaction_passed:
                        failed_count += 1

                    # 每次点击后恢复到原页面，避免后续采样受前一次状态影响
                    _restore_page_after_interaction(page, before_url)

            # 汇总
            effective = len(btn_results) - failed_count
            l1_3_summary = (
                f"采样按钮: {len(sample_btns)} 个\n"
                f"有响应: {effective} 个\n"
                f"无变化: {failed_count} 个\n"
            )
            allure.attach(l1_3_summary, name="按钮交互汇总", attachment_type=allure.attachment_type.TEXT)

            checks["buttons"] = {
                "passed": failed_count == 0,
                "detail": f"tested={len(sample_btns)}, responsive={effective}, unresponsive={failed_count}",
                "results": btn_results,
            }
            if failed_count > 0:
                errors.append({
                    "severity": "error", "type": "buttons",
                    "detail": f"{failed_count}/{len(sample_btns)} 个采样按钮点击后没有可验证状态变化",
                })

        # --- 1.4 Console 错误 ---
        with allure.step("1.4 Console 错误"):
            console_errors = page.evaluate("""() => {
                return (window.__seo_console_errors || []).slice(0, 20);
            }""")

            IGNORE = ["Hydration completed but contains mismatches", "GoogleIdentity",
                      "net::ERR_CONNECTION_TIMED_OUT", "load-script-error",
                      "Cannot read properties of null"]
            real_errors = [e for e in console_errors if not any(ign in e for ign in IGNORE)]

            if real_errors:
                c_detail = f"Console Error 共 {len(console_errors)} 条（过滤后 {len(real_errors)} 条）:\n\n"
                for i, e in enumerate(real_errors[:15]):
                    c_detail += f"[{i+1}] {e[:150]}\n"
                warnings.append({
                    "severity": "warning", "type": "console_error",
                    "detail": f"{len(real_errors)} 个 console error",
                })
            else:
                c_detail = f"无 Console Error（共 {len(console_errors)} 条，均被过滤或为无害）"

            checks["console"] = {
                "passed": len(real_errors) == 0,
                "detail": f"total={len(console_errors)}, real={len(real_errors)}",
            }
            allure.attach(c_detail, name="Console 错误详情", attachment_type=allure.attachment_type.TEXT)

            if str(device).lower() == "mobile":
                allure.attach(
                    "移动端仅执行页面可访问、资源加载、按钮交互和 console 检查；已跳过文本质量与 FAQ 细查。",
                    name="移动端跳过说明",
                    attachment_type=allure.attachment_type.TEXT,
                )
                checks["text_quality"] = {"passed": True, "detail": "skipped on mobile"}
                checks["faq"] = {"passed": True, "detail": "skipped on mobile"}
                return {
                    "errors": errors, "warnings": warnings,
                    "checks": checks, "btn_results": btn_results, "resource_stats": resource_stats,
                }

        # --- 1.5 LLM 文案审查 + 评论区视觉检测 ---
        with allure.step("1.5 LLM 文案审查 + 评论区视觉检测"):
            # 滚到底触发评论等懒加载内容
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(3000)

            # 截取页面底部区域（评论通常在底部）
            page_height = page.evaluate("document.body.scrollHeight")
            vp_height = page.evaluate("window.innerHeight")
            # 截底部 2 屏（含评论区）
            page.set_viewport_size({"width": 1920, "height": vp_height * 2})
            page.evaluate(f"window.scrollTo(0, {max(0, page_height - vp_height * 2)})")
            page.wait_for_timeout(1500)
            bottom_png = page.screenshot(full_page=False)
            allure.attach(bottom_png, name="页面底部-含评论区",
                          attachment_type=allure.attachment_type.PNG)
            # 恢复 viewport
            page.set_viewport_size({"width": 1920, "height": vp_height})
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(1000)

            # 视觉审查：送底部截图给 LLM 看图找评论乱码
            from helpers.llm_judge import judge_screenshot_text
            vres = judge_screenshot_text(
                bottom_png,
                context="Bottom section of an SEO landing page with reviews/comments"
            )
            if vres and vres.get("found"):
                visual_issue = vres.get("issue", "visual garbled text in reviews")
                allure.attach(visual_issue, name="评论区视觉审查-发现问题",
                              attachment_type=allure.attachment_type.TEXT)
            else:
                allure.attach("未发现视觉乱码", name="评论区视觉审查-正常",
                              attachment_type=allure.attachment_type.TEXT)

            # 文本审查：提取评论文本，先去重再送给 LLM
            review_text = page.evaluate("""() => {
                var containers = document.querySelectorAll(
                    '[class*="review"], [class*="Review"], [class*="testimonial"], [class*="Testimonial"],'
                    + '[class*="comment"], [class*="Comment"], [class*="feedback"], [class*="Feedback"]'
                );
                var texts = [];
                for (var i = 0; i < containers.length; i++) {
                    var el = containers[i];
                    if (el.offsetWidth === 0 && el.offsetHeight === 0) continue;
                    var t = (el.innerText || '').trim();
                    if (t.length > 20 && t.length < 3000) texts.push(t);
                }
                // 去重：轮播会克隆 slide
                var seen = new Set();
                return texts.filter(function(t) {
                    var key = t.slice(0, 80);
                    if (seen.has(key)) return false;
                    seen.add(key);
                    return true;
                }).join('\\n---\\n');
            }""")

            full_text = _collect_text_for_review(page)[:10000]
            if review_text:
                full_text += "\n\n=== REVIEWS/COMMENTS SECTION ===\n" + review_text[:5000]
            tq_result = judge_text_quality(full_text, page.url, lang_prefix)

            # 合并视觉 + 文本审查结果
            tq_issues = tq_result.get("issues", [])
            if vres and vres.get("found"):
                tq_issues.append({"severity": "warning", "detail": vres.get("issue", ""),
                                  "location": "review section (visual)"})

            tq_passed = tq_result.get("passed", True)
            tq_summary = tq_result.get("summary", "")

            checks["text_quality"] = {
                "passed": tq_passed,
                "detail": tq_summary[:100] if tq_summary else ("OK" if tq_passed else f"{len(tq_issues)} issues"),
            }

            tq_detail = tq_summary or "OK"
            if tq_issues:
                tq_detail += "\n\n问题详情:\n"
                for i, iss in enumerate(tq_issues):
                    loc = iss.get("location", "")
                    tq_detail += f"\n  [{i+1}] [{iss.get('severity','warning')}] {iss.get('detail','')}"
                    if loc:
                        tq_detail += f"\n      位置: \"{loc[:60]}\""

            allure.attach(tq_detail, name="LLM 文案审查详情", attachment_type=allure.attachment_type.TEXT)

            for iss in tq_issues:
                if isinstance(iss, str):
                    detail = iss[:120]; sev = "warning"; loc = ""
                else:
                    detail = iss.get("detail", str(iss))[:120]
                    sev = iss.get("severity", "warning")
                    loc = f" (位置: {iss.get('location','')[:40]})"
                if sev == "error":
                    errors.append({"severity": "error", "type": "text_quality", "detail": detail + loc})
                else:
                    warnings.append({"severity": "warning", "type": "text_quality", "detail": detail + loc})

        # --- 1.6 FAQ 展开 + 截图审查 ---
        with allure.step("1.6 FAQ 展开截图审查"):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(2000)

            faq_items = _discover_faq_items(page)

            allure.attach(
                json.dumps(faq_items, ensure_ascii=False, indent=2),
                name="FAQ discovery", attachment_type=allure.attachment_type.TEXT,
            )

            faq_count = 0
            faq_issues = []
            for fi, item in enumerate(faq_items):
                question = item["text"][:60]
                kind = item.get("kind", "")
                try:
                    page_state_before = _interaction_snapshot(page)
                    before_state = _faq_probe(page, question, kind, click=False)
                    if not before_state.get("found"):
                        faq_issues.append(f"未找到 FAQ 控件: {question}")
                        continue

                    clicked = False
                    after_state = None
                    if not (before_state.get("expanded") or before_state.get("answer_visible")):
                        click_locator = None
                        if before_state.get("header_class"):
                            try:
                                click_locator = page.locator(".pk-collapse-header").filter(has_text=question).first
                            except Exception:
                                click_locator = None
                        if click_locator is not None:
                            try:
                                click_locator.scroll_into_view_if_needed(timeout=5000)
                            except Exception:
                                pass
                        for attempt in range(2):
                            if click_locator is not None:
                                try:
                                    click_locator.click(timeout=5000)
                                    clicked = True
                                except Exception:
                                    click_state = _faq_probe(page, question, kind, click=True)
                                    clicked = clicked or bool(click_state.get("clicked"))
                            else:
                                click_state = _faq_probe(page, question, kind, click=True)
                                clicked = clicked or bool(click_state.get("clicked"))
                            page.wait_for_timeout(1200 if attempt == 0 else 1500)

                    after_state = after_state or _faq_probe(page, question, kind, click=False)
                    if not (after_state.get("expanded") or after_state.get("answer_visible")):
                        try:
                            forced = page.evaluate("""(needle) => {
                                const norm = (value) => (value || '').replace(/\\s+/g, ' ').trim().toLowerCase();
                                const target = norm(needle);
                                const headers = Array.from(document.querySelectorAll('.pk-collapse-header'));
                                const header = headers.find((el) => {
                                    const text = norm(el.textContent);
                                    return text === target || text.startsWith(target.slice(0, 50)) || target.startsWith(text.slice(0, 50));
                                });
                                if (!header) return false;
                                header.classList.add('pk-collapse-active');
                                const panel = header.parentElement && header.parentElement.querySelector('.pk-collapse-panel');
                                if (panel) {
                                    panel.style.display = 'block';
                                    panel.style.overflow = 'visible';
                                    panel.style.maxHeight = panel.scrollHeight + 'px';
                                }
                                return true;
                            }""", question)
                            page.wait_for_timeout(400)
                            after_state = _faq_probe(page, question, kind, click=False)
                            if forced and (after_state.get("expanded") or after_state.get("answer_visible")):
                                warnings.append({
                                    "severity": "warning",
                                    "type": "faq_visual",
                                    "detail": f"FAQ 通过 DOM fallback 展开: {question}",
                                })
                        except Exception:
                            pass
                    page_state_after = _interaction_snapshot(page)

                    png = page.screenshot(full_page=False)
                    allure.attach(png, name=f"faq-{fi+1:02d}",
                                  attachment_type=allure.attachment_type.PNG)
                    allure.attach(
                        json.dumps({
                            "question": question,
                            "kind": kind,
                            "clicked": clicked,
                            "page_before": {
                                "url": page_state_before.get("url"),
                                "scroll_y": page_state_before.get("scroll_y"),
                                "expanded_count": page_state_before.get("expanded_count"),
                                "text_len": page_state_before.get("text_len"),
                            },
                            "page_after": {
                                "url": page_state_after.get("url"),
                                "scroll_y": page_state_after.get("scroll_y"),
                                "expanded_count": page_state_after.get("expanded_count"),
                                "text_len": page_state_after.get("text_len"),
                            },
                            "item_before": before_state,
                            "item_after": after_state,
                        }, ensure_ascii=False, indent=2),
                        name=f"faq-{fi+1:02d}-状态",
                        attachment_type=allure.attachment_type.JSON,
                    )

                    faq_count += 1

                    if page_state_after.get("url") != page_state_before.get("url"):
                        faq_issues.append(f"FAQ 点击后发生了跳转: {question}")
                        _restore_page_after_interaction(page, page_state_before.get("url", page.url))
                        continue

                    if not (after_state.get("expanded") or after_state.get("answer_visible")):
                        warnings.append({
                            "severity": "warning",
                            "type": "faq_visual",
                            "detail": f"FAQ 自动化未稳定展开: {question}",
                        })
                except Exception:
                    warnings.append({
                        "severity": "warning",
                        "type": "faq_visual",
                        "detail": f"FAQ 点击异常: {question}",
                    })

            if faq_count > 0:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)
                # 截一张 FAQ 区域全貌
                faq_full_png = page.screenshot(full_page=False)
                allure.attach(faq_full_png, name="faq-all-expanded",
                              attachment_type=allure.attachment_type.PNG)
            else:
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1500)
                faq_fallback_png = page.screenshot(full_page=False)
                allure.attach(
                    faq_fallback_png,
                    name="faq-fallback-no-items",
                    attachment_type=allure.attachment_type.PNG,
                )
                allure.attach(
                    "FAQ discovery 为空，已附加底部兜底截图，需继续排查 FAQ 结构选择器。",
                    name="FAQ discovery-空结果说明",
                    attachment_type=allure.attachment_type.TEXT,
                )

            checks["faq"] = {
                "passed": len(faq_issues) == 0,
                "detail": f"Expanded {faq_count} FAQs, {len(faq_issues)} issues"
                          if faq_issues else f"Expanded {faq_count} FAQs, all OK",
            }
            if faq_issues:
                allure.attach(
                    "\n".join(f"[{i+1}] {iss}" for i, iss in enumerate(faq_issues)),
                    name="FAQ visual review issues",
                    attachment_type=allure.attachment_type.TEXT,
                )
                for fi_issue in faq_issues:
                    errors.append({"severity": "error", "type": "faq_visual",
                                   "detail": fi_issue[:120]})

        return {
            "errors": errors, "warnings": warnings,
            "checks": checks, "btn_results": btn_results, "resource_stats": resource_stats,
        }

    # ═══════════════════════════════════════════════════════════
    # Layer 2: 自一致性检查（逐项展开 + 详情）
    # ═══════════════════════════════════════════════════════════

    def _layer2_check(self, page, url: str, page_meta: dict) -> dict:
        errors = []
        warnings = []

        from helpers.self_consistency import SelfConsistencyChecker
        sc = SelfConsistencyChecker()
        result = sc.check(page, url)
        checks = result.get("checks", {})

        # --- 2.1 语言一致性 ---
        with allure.step("2.1 语言一致性"):
            check = checks.get("lang_match", {})
            lang_detail = f"结果: {check.get('detail', '?')}"
            if check.get("issue"):
                lang_detail += f"\nSeverity: {check['issue'].get('severity','?')}"
            allure.attach(lang_detail, name="语言一致性详情", attachment_type=allure.attachment_type.TEXT)
            if not check.get("passed", True):
                issue = check.get("issue", {})
                if issue.get("severity") == "error":
                    errors.append(issue)
                else:
                    warnings.append(issue)

        # --- 2.2 Title vs H1 ---
        with allure.step("2.2 Title vs H1 相关性"):
            check = checks.get("title_h1", {})
            th_detail = (
                f"Title: {page_meta.get('title', 'N/A')[:100]}\n"
                f"H1: {page_meta.get('h1s', ['N/A'])[0][:100] if page_meta.get('h1s') else 'N/A'}\n"
                f"结果: {check.get('detail', '?')}"
            )
            allure.attach(th_detail, name="Title-H1详情", attachment_type=allure.attachment_type.TEXT)
            if not check.get("passed", True):
                issue = check.get("issue", {})
                if issue.get("severity") == "error":
                    errors.append(issue)
                else:
                    warnings.append(issue)

        # --- 2.3 Meta 标签 ---
        with allure.step("2.3 Meta 标签完整性"):
            check = checks.get("meta", {})
            desc = page_meta.get("meta_description", "")
            # 额外提取 og:title
            og_title = page.evaluate("""() => {
                var og = document.querySelector('meta[property="og:title"]');
                return og ? og.getAttribute('content') || '' : '';
            }""")
            og_desc = page.evaluate("""() => {
                var og = document.querySelector('meta[property="og:description"]');
                return og ? og.getAttribute('content') || '' : '';
            }""")

            meta_detail = (
                f"<meta description>: {desc[:150] if desc else '(缺失)'}\n"
                f"  length: {len(desc)} chars\n"
                f"<meta og:title>: {og_title[:150] if og_title else '(缺失)'}\n"
                f"<meta og:description>: {og_desc[:150] if og_desc else '(缺失)'}\n"
                f"\n结果: {check.get('detail', '?')}"
            )
            allure.attach(meta_detail, name="Meta标签详情", attachment_type=allure.attachment_type.TEXT)
            for issue in check.get("issues", []):
                if issue.get("severity") == "error":
                    errors.append(issue)
                else:
                    warnings.append(issue)

        # --- 2.4 区块完整性 ---
        with allure.step("2.4 区块完整性"):
            check = checks.get("structure", {})
            # 补充统计信息
            img_total = page.evaluate("""() => {
                return document.querySelectorAll('img').length;
            }""")
            cta_total = page.evaluate("""() => {
                var layout = document.querySelector('#__nuxt > div:first-child');
                var main = (layout && layout.children.length >= 2) ? layout.children[1] : null;
                var root = main || document;
                return root.querySelectorAll('button:not([disabled])').length;
            }""")
            has_faq = page.evaluate("""() => {
                return document.querySelectorAll('[class*="faq"], [class*="Faq"], [class*="accordion"], details').length;
            }""")

            struct_detail = (
                f"H1: {len(page_meta.get('h1s', []))} 个 → {page_meta.get('h1s', [])[:3]}\n"
                f"H2: {len(page_meta.get('h2s', []))} 个 → {[h[:60] for h in page_meta.get('h2s', [])[:5]]}\n"
                f"图片 <img>: {img_total} 个\n"
                f"CTA 按钮: {cta_total} 个\n"
                f"文件上传 input: {'有' if page.evaluate('() => document.querySelectorAll(\"input[type=file]\").length > 0') else '无'}\n"
                f"FAQ 元素: {has_faq} 个\n"
                f"\n结果: {check.get('detail', '?')}"
            )
            allure.attach(struct_detail, name="区块完整性详情", attachment_type=allure.attachment_type.TEXT)
            for issue in check.get("issues", []):
                if issue.get("severity") == "error":
                    errors.append(issue)
                else:
                    warnings.append(issue)

        # --- 2.5 图片 Alt ---
        with allure.step("2.5 图片 Alt 属性"):
            check = checks.get("img_alt", {})
            # 提取详情
            img_alts = page.evaluate("""() => {
                var layout = document.querySelector('#__nuxt > div:first-child');
                var main = (layout && layout.children.length >= 2) ? layout.children[1] : null;
                var root = main || document;
                var alts = [];
                root.querySelectorAll('img').forEach(function(img) {
                    var rect = img.getBoundingClientRect();
                    if (rect.width > 20 && rect.height > 20) {
                        alts.push({
                            alt: (img.alt || '').trim().slice(0, 80),
                            src: img.src.slice(-60)
                        });
                    }
                });
                return alts;
            }""")
            empty = sum(1 for a in img_alts if not a["alt"])
            alt_detail = f"可见图片: {len(img_alts)} 张\n缺少 alt: {empty} 张\n\n"
            for i, a in enumerate(img_alts):
                marker = " (空!)" if not a["alt"] else ""
                alt_detail += f"[{i+1}] alt=\"{a['alt'][:60]}{marker}\"\n    src=...{a['src']}\n"

            alt_detail += f"\n结果: {check.get('detail', '?')}"
            allure.attach(alt_detail, name="图片Alt详情", attachment_type=allure.attachment_type.TEXT)
            for issue in check.get("issues", []):
                if issue.get("severity") == "error":
                    errors.append(issue)
                else:
                    warnings.append(issue)

        # --- 2.6 链接语言一致性 ---
        with allure.step("2.6 内链语言前缀一致性"):
            check = checks.get("link_lang", {})
            # 统计内链
            link_info = page.evaluate("""() => {
                var layout = document.querySelector('#__nuxt > div:first-child');
                var main = (layout && layout.children.length >= 2) ? layout.children[1] : null;
                var root = main || document;
                var links = [];
                root.querySelectorAll('a[href]').forEach(function(a) {
                    var h = a.getAttribute('href');
                    var t = (a.textContent || '').trim().slice(0, 50);
                    if (h && h.startsWith('/') && !h.startsWith('//') && !t.toLowerCase().includes('home')) {
                        links.push({ href: h, text: t });
                    }
                });
                return links.length;
            }""")
            link_detail = (
                f"正文区域内链数量: {link_info} 个\n"
                f"\n结果: {check.get('detail', '?')}"
            )
            allure.attach(link_detail, name="链接语言一致性详情", attachment_type=allure.attachment_type.TEXT)
            if not check.get("passed", True):
                issue = check.get("issue", {})
                if issue.get("severity") == "error":
                    errors.append(issue)
                else:
                    warnings.append(issue)

        return {
            "errors": errors, "warnings": warnings,
            "checks": result.get("checks", {}),
            "summary": result.get("summary", ""),
            "passed": result.get("passed", True),
        }

    # ═══════════════════════════════════════════════════════════
    # Layer 3: AI 单页内容审查（逐维度展开）
    # ═══════════════════════════════════════════════════════════

    def _layer3_check(self, page_meta: dict, url: str, lang_prefix: str, name: str,
                      screenshot_path: str | None = None, focus: str = "desktop",
                      device_label: str = "PC", hints: str = "") -> dict:
        errors = []
        warnings = []

        from helpers.ai_page_review import create_reviewer
        reviewer = create_reviewer()

        if not reviewer:
            allure.attach("未配置 OPENAI_API_KEY", name="AI审查-跳过",
                          attachment_type=allure.attachment_type.TEXT)
            return {"errors": errors, "warnings": warnings, "issues": [], "summary": "", "passed": True}

        target_screenshot = screenshot_path
        if not target_screenshot:
            import glob as _glob
            screenshot_dir = os.path.join(HARNESS_ROOT, "data", "screenshots")
            pattern = os.path.join(screenshot_dir, f"*{name}*01-*.png")
            files = sorted(_glob.glob(pattern), key=os.path.getmtime, reverse=True)
            target_screenshot = files[0] if files else None

        if not target_screenshot:
            allure.attach("未找到首屏截图", name="AI审查-跳过",
                          attachment_type=allure.attachment_type.TEXT)
            return {"errors": errors, "warnings": warnings, "issues": [], "summary": "", "passed": True}

        page_info = {
            "url": url, "lang": lang_prefix,
            "title": page_meta.get("title", ""),
            "h1s": page_meta.get("h1s", []),
        }

        # 调用 AI 审查
        l3_result = reviewer.review(target_screenshot, page_info, hints=hints, focus=focus)
        l3_issues = l3_result.get("issues", [])
        l3_summary = l3_result.get("summary", "")
        l3_passed = l3_result.get("passed", True)

        # 逐维度展开
        dims = {"layout": "布局完整性", "image": "图片可见性", "text": "文案质量",
                "cta": "CTA 可辨识性", "content": "内容充足性"}
        has_any = False

        for dim_key, dim_name in dims.items():
            dim_issues = [i for i in l3_issues if i.get("dimension") == dim_key]
            with allure.step(f"{device_label} 3.{list(dims.keys()).index(dim_key)+1} {dim_name}"):
                if dim_issues:
                    dim_detail = ""
                    for di in dim_issues:
                        sev = di.get("severity", "warning")
                        dim_detail += f"[{sev.upper()}] {di.get('detail', '')}\n"
                        if sev == "error":
                            errors.append({"severity": "error", "type": f"ai_{dim_key}",
                                           "detail": di.get('detail', '')[:120]})
                        else:
                            warnings.append({"severity": "warning", "type": f"ai_{dim_key}",
                                             "detail": di.get('detail', '')[:120]})
                    allure.attach(dim_detail, name=f"AI审查-{device_label}-{dim_name}",
                                  attachment_type=allure.attachment_type.TEXT)
                    has_any = True
                else:
                    allure.attach("未发现问题", name=f"AI审查-{device_label}-{dim_name}",
                                  attachment_type=allure.attachment_type.TEXT)

        # 总览
        allure.attach(
            f"AI 审查结果: {'PASS' if l3_passed else 'ISSUES FOUND'}\n\n{l3_summary}",
            name=f"AI审查-总览-{device_label}",
            attachment_type=allure.attachment_type.TEXT,
        )

        return {"errors": errors, "warnings": warnings, "issues": l3_result.get("issues", []), "summary": l3_result.get("summary", ""), "passed": l3_result.get("passed", True)}
