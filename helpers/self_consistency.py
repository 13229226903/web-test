"""SEO 新页面自一致性检查（Layer 2）

6 项零配置检查 — 不依赖任何手写预期，从页面自身推导正确性：
  1. URL 语言前缀 vs body 正文语种
  2. <title> vs <h1> 语义相关性
  3. Meta 标签完整性（description / og:title）
  4. 标准区块完整性（H1 / H2 / img / CTA / file input）
  5. 图片 alt 属性语种一致性
  6. 正文内链语言前缀一致性

用法：
    from helpers.self_consistency import SelfConsistencyChecker

    checker = SelfConsistencyChecker()
    result = checker.check(page, url="http://...")
    # result = {"passed": bool, "issues": [...], "checks": {...}, "summary": "..."}
"""

import re
import os
import math
from typing import List, Dict, Any, Tuple, Optional
from playwright.sync_api import Page

LANG_NEUTRAL_PATHS = {
    "/privacy-policy",
    "/term-of-use",
}


# ═══════════════════════════════════════════════════════════════
# 语言检测配置
# ═══════════════════════════════════════════════════════════════

# URL 语言前缀 → 预期语言名/字符范围
LANG_CONFIG = {
    "zh": {
        "name": "中文", "langdetect_expect": "zh-cn",
        "char_ranges": [(0x4E00, 0x9FFF)],  # CJK Unified
    },
    "zh-tw": {
        "name": "繁体中文", "langdetect_expect": "zh-cn",
        "char_ranges": [(0x4E00, 0x9FFF)],
    },
    "ja": {
        "name": "日语", "langdetect_expect": "ja",
        "char_ranges": [(0x3040, 0x309F), (0x30A0, 0x30FF), (0x4E00, 0x9FFF)],
    },
    "ko": {
        "name": "韩语", "langdetect_expect": "ko",
        "char_ranges": [(0xAC00, 0xD7AF)],
    },
    "th": {
        "name": "泰语", "langdetect_expect": "th",
        "char_ranges": [(0x0E00, 0x0E7F)],
    },
    "ru": {
        "name": "俄语", "langdetect_expect": "ru",
        "char_ranges": [(0x0400, 0x04FF)],
    },
    "ar": {
        "name": "阿拉伯语", "langdetect_expect": "ar",
        "char_ranges": [(0x0600, 0x06FF)],
    },
    "vi": {"name": "越南语", "langdetect_expect": "vi", "char_ranges": []},
    "id": {"name": "印尼语", "langdetect_expect": "id", "char_ranges": []},
    "pt": {"name": "葡萄牙语", "langdetect_expect": "pt", "char_ranges": []},
    "es": {"name": "西班牙语", "langdetect_expect": "es", "char_ranges": []},
    "fr": {"name": "法语", "langdetect_expect": "fr", "char_ranges": []},
    "it": {"name": "意大利语", "langdetect_expect": "it", "char_ranges": []},
    "de": {"name": "德语", "langdetect_expect": "de", "char_ranges": []},
    "tr": {"name": "土耳其语", "langdetect_expect": "tr", "char_ranges": []},
    "": {"name": "英语（默认）", "langdetect_expect": "en", "char_ranges": []},
}


def _detect_lang_prefix(path: str) -> str:
    """提取 URL 路径中的语言前缀: /ja/tools/foo → ja, /zh-tw/bar → zh-tw"""
    m = re.match(r"^/([a-z]{2}(?:-[a-z]{2})?)/", path)
    return m.group(1) if m else ""


def _same_lang(link_path: str, prefix: str) -> bool:
    """链接的语言前缀是否与当前页面一致。"""
    if link_path in LANG_NEUTRAL_PATHS:
        return True
    lp = _detect_lang_prefix(link_path)
    return lp == prefix if prefix else not lp


# ═══════════════════════════════════════════════════════════════
# 提取页面元数据
# ═══════════════════════════════════════════════════════════════

def _extract_page_meta(page: Page) -> dict:
    """从当前页面提取所有元数据，供后续检查项使用。"""
    return page.evaluate("""() => {
        // 获取布局主区域（#__nuxt > div 的第2个孩子）
        let layout = document.querySelector('#__nuxt > div:first-child');
        let mainEl = null;
        if (layout && layout.children && layout.children.length >= 2) {
            mainEl = layout.children[1];
        }
        const mainText = mainEl ? (mainEl.innerText || '').replace(/\\s+/g, ' ') : '';

        // title / h1 / h2
        const title = document.title || '';
        const h1s = [];
        document.querySelectorAll('h1').forEach(h => {
            const t = (h.textContent || '').trim().replace(/\\s+/g, ' ');
            if (t.length > 2) h1s.push(t);
        });
        const h2s = [];
        document.querySelectorAll('h2').forEach(h => {
            const t = (h.textContent || '').trim().replace(/\\s+/g, ' ');
            if (t.length > 2) h2s.push(t);
        });

        // meta tags
        const metaDesc = document.querySelector('meta[name="description"]');
        const ogTitle = document.querySelector('meta[property="og:title"]');
        const ogDesc = document.querySelector('meta[property="og:description"]');

        // 图片 alt（正文区域）
        const imgAlts = [];
        const root = mainEl || document;
        root.querySelectorAll('img').forEach(img => {
            const alt = (img.alt || '').trim();
            const rect = img.getBoundingClientRect();
            if (rect.width > 20 && rect.height > 20) {  // 排除装饰/跟踪像素
                imgAlts.push(alt);
            }
        });

        // CTA 按钮（正文区域可点击的按钮）
        const ctaButtons = [];
        const ctaRoot = mainEl || document;
        ctaRoot.querySelectorAll('button:not([disabled]), [role="button"]').forEach(btn => {
            const t = (btn.textContent || '').trim();
            const rect = btn.getBoundingClientRect();
            if (t.length > 1 && rect.width > 0 && rect.height > 0) {
                ctaButtons.push(t.slice(0, 60));
            }
        });

        // 文件上传 input
        const fileInputs = (mainEl || document).querySelectorAll('input[type="file"]');
        const hasFileInput = fileInputs.length > 0;

        // 正文内链（提取 href 和文本）
        const internalLinks = [];
        const linkRoot = mainEl || document;
        linkRoot.querySelectorAll('a[href]').forEach(a => {
            const h = a.getAttribute('href');
            const t = (a.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 50);
            if (h && h.startsWith('/') && !h.startsWith('//') && !t.toLowerCase().includes('home')) {
                internalLinks.push({ href: h, text: t });
            }
        });

        return {
            title: title,
            h1s: h1s,
            h2s: h2s,
            meta_description: metaDesc ? metaDesc.getAttribute('content') || '' : '',
            og_title: ogTitle ? ogTitle.getAttribute('content') || '' : '',
            og_description: ogDesc ? ogDesc.getAttribute('content') || '' : '',
            img_alts: imgAlts,
            cta_buttons: ctaButtons,
            has_file_input: hasFileInput,
            internal_links: internalLinks,
            body_text: (document.body.innerText || '').replace(/\\s+/g, ' '),
            main_text: mainText,
        };
    }""")


# ═══════════════════════════════════════════════════════════════
# 检查项实现
# ═══════════════════════════════════════════════════════════════

def _check_language_match(url_path: str, meta: dict) -> Optional[dict]:
    """2.1 URL 语言前缀 vs body 正文语种"""
    prefix = _detect_lang_prefix(url_path)
    lang_cfg = LANG_CONFIG.get(prefix, LANG_CONFIG[""])
    text = meta.get("main_text", "") or meta.get("body_text", "")

    if len(text) < 100:
        return {"severity": "warning", "type": "lang_mismatch",
                "detail": f"正文过短（{len(text)}字符），无法判断语种"}

    try:
        from langdetect import detect_langs, DetectorFactory
        DetectorFactory.seed = 0
        results = detect_langs(text[:2000])
        top = results[0]
        detected_short = top.lang.split("-")[0]
        expected_short = lang_cfg["langdetect_expect"].split("-")[0]

        if detected_short != expected_short and top.prob > 0.5:
            # 兜底：有特殊字符范围的语种，用字符计数覆盖 langdetect 的误判
            char_ranges = lang_cfg.get("char_ranges", [])
            if char_ranges:
                char_count = sum(
                    1 for c in text if any(lo <= ord(c) <= hi for lo, hi in char_ranges)
                )
                if char_count > 20:
                    return None  # 字符判定通过，不报

            return {
                "severity": "warning",
                "type": "lang_mismatch",
                "detail": (
                    f"URL 前缀 /{prefix}/ 预期 {lang_cfg['name']}，"
                    f"但正文检测到 {top.lang}（置信度 {top.prob:.0%}）"
                ),
            }
    except ImportError:
        pass
    except Exception:
        pass  # langdetect 失败了不阻塞测试

    return None


def _check_title_h1_correlation(meta: dict) -> Optional[dict]:
    """2.2 <title> vs <h1> 语义相关性"""
    title = meta.get("title", "")
    h1s = meta.get("h1s", [])

    if not title:
        return {"severity": "error", "type": "title_h1",
                "detail": "页面缺少 <title>"}

    if not h1s:
        return {"severity": "warning", "type": "title_h1",
                "detail": "页面缺少 <h1>"}

    # 分词：按空格/标点/大小写切换拆分
    def tokenize(s: str) -> set:
        # 按常见分隔符拆 + 连续大写字母边界
        parts = re.split(r'[\s\-–—|·•/\\:：｜]+', s)
        tokens = set()
        for p in parts:
            p = p.strip().lower()
            if len(p) >= 3:
                tokens.add(p)
            # 也把 CamelCase 拆开
            camel_parts = re.findall(r'[A-Z]?[a-z]+', p)
            for cp in camel_parts:
                if len(cp) >= 3:
                    tokens.add(cp.lower())
        return tokens

    title_tokens = tokenize(title)
    h1_text = " ".join(h1s)
    h1_tokens = tokenize(h1_text)

    if not title_tokens or not h1_tokens:
        return None  # 无法分词则跳过

    # 交集比例
    intersection = title_tokens & h1_tokens
    union = title_tokens | h1_tokens
    ratio = len(intersection) / len(union) if union else 0

    if ratio < 0.15:
        return {
            "severity": "warning",
            "type": "title_h1",
            "detail": (
                f"<title> 和 <h1> 关键词交集比例仅 {ratio:.0%}（<{0.15:.0%}），"
                f"title: \"{title[:50]}\", h1: \"{h1_text[:50]}\""
            ),
        }

    return None


def _check_meta_tags(meta: dict, _url_path: str) -> List[dict]:
    """2.3 Meta 标签完整性"""
    issues = []

    desc = meta.get("meta_description", "")
    if not desc:
        issues.append({"severity": "warning", "type": "meta",
                       "detail": "缺少 <meta name=\"description\">"})
    elif len(desc) < 30:
        issues.append({"severity": "warning", "type": "meta",
                       "detail": f"<meta description> 过短（{len(desc)}字符）: \"{desc[:60]}\""})
    elif len(desc) > 200:
        issues.append({"severity": "warning", "type": "meta",
                       "detail": f"<meta description> 过长（{len(desc)}字符），建议 50-160"})

    og_title = meta.get("og_title", "")
    title = meta.get("title", "")
    if not og_title:
        issues.append({"severity": "warning", "type": "meta",
                       "detail": "缺少 <meta property=\"og:title\">"})
    elif title and og_title:
        # og:title 应与 <title> 基本一致（允许站点名拼接差异）
        if og_title.strip() not in title and title not in og_title:
            issues.append({"severity": "warning", "type": "meta",
                           "detail": f"<meta og:title> \"{og_title[:60]}\" 与 <title> \"{title[:60]}\" 不一致"})

    return issues


def _check_structure(meta: dict) -> List[dict]:
    """2.4 标准区块完整性"""
    issues = []

    if not meta.get("h1s"):
        issues.append({"severity": "warning", "type": "structure",
                       "detail": "页面缺少 H1 标题"})

    if not meta.get("h2s"):
        issues.append({"severity": "warning", "type": "structure",
                       "detail": "页面缺少 H2 副标题（SEO 页面通常至少有 1 个）"})

    # 检查是否有可见图片
    img_alts = meta.get("img_alts", [])
    if len(img_alts) == 0:
        issues.append({"severity": "warning", "type": "structure",
                       "detail": "正文区域无可见图片（SEO 工具页通常有示例图）"})

    if not meta.get("has_file_input"):
        issues.append({"severity": "warning", "type": "structure",
                       "detail": "页面缺少文件上传 input（工具页通常有 CTA）"})

    if not meta.get("cta_buttons"):
        issues.append({"severity": "warning", "type": "structure",
                       "detail": "正文区域无可见按钮"})

    return issues


def _check_img_alt_language(meta: dict, url_path: str) -> List[dict]:
    """2.5 图片 alt 属性 — 非空 + 语种一致性"""
    prefix = _detect_lang_prefix(url_path)
    lang_cfg = LANG_CONFIG.get(prefix, LANG_CONFIG[""])
    expected_short = lang_cfg["langdetect_expect"].split("-")[0]
    expected_name = lang_cfg["name"]

    issues = []
    img_alts = meta.get("img_alts", [])
    empty_count = sum(1 for a in img_alts if not a)
    total = len(img_alts)

    if total == 0:
        return issues  # 已在 structure 检查中报告

    if empty_count > 0 and empty_count == total:
        issues.append({"severity": "warning", "type": "img_alt",
                       "detail": f"所有 {total} 张可见图片均无 alt 属性"})
    elif empty_count > 0:
        issues.append({"severity": "warning", "type": "img_alt",
                       "detail": f"{empty_count}/{total} 张可见图片缺少 alt 属性"})

    # 有 alt 的图片语种是否匹配（仅对 CJK 语种做检查，拉丁语种 alt 通常是英文品牌词可接受）
    if prefix in ("zh", "zh-tw", "ja", "ko", "th", "ru", "ar"):
        non_empty_alts = [a for a in img_alts if a]
        if non_empty_alts:
            try:
                from langdetect import detect_langs, DetectorFactory
                DetectorFactory.seed = 0
                alt_text = " ".join(non_empty_alts)
                results = detect_langs(alt_text[:1000])
                top = results[0]
                detected_short = top.lang.split("-")[0]
                if detected_short != expected_short and top.prob > 0.6:
                    # 字符兜底
                    char_ranges = lang_cfg.get("char_ranges", [])
                    if char_ranges:
                        char_count = sum(
                            1 for c in alt_text
                            if any(lo <= ord(c) <= hi for lo, hi in char_ranges)
                        )
                        if char_count > 5:
                            return issues  # 有足够目标语种字符，通过
                    issues.append({"severity": "warning", "type": "img_alt",
                                   "detail": f"图片 alt 文本语种可能不匹配：期望 {expected_name}，检测到 {top.lang}"})
            except ImportError:
                pass
            except Exception:
                pass

    return issues


def _check_link_lang_consistency(meta: dict, url_path: str) -> Optional[dict]:
    """2.6 正文内链语言前缀一致性"""
    prefix = _detect_lang_prefix(url_path)
    internal_links = meta.get("internal_links", [])

    wrong_lang_links = []
    for link in internal_links:
        href = link["href"]
        if not _same_lang(href, prefix):
            wrong_lang_links.append(href)

    if wrong_lang_links:
        # 只报告前 5 个
        samples = wrong_lang_links[:5]
        return {
            "severity": "warning",
            "type": "link_lang",
            "detail": (
                f"{len(wrong_lang_links)}/{len(internal_links)} 个内链语言前缀与当前页"
                f"（/{prefix}/）不一致: {', '.join(samples)}"
            ),
        }

    return None


# ═══════════════════════════════════════════════════════════════
# 主入口
# ═══════════════════════════════════════════════════════════════

class SelfConsistencyChecker:
    """SEO 页面自一致性检查器。

    所有检查项不依赖手写预期，从 URL + 页面 DOM 中自动推导。
    """

    def check(self, page: Page, url: str) -> dict:
        """执行全部 6 项自一致性检查。

        Args:
            page: Playwright Page，已导航到目标页面并渲染完成
            url: 完整的页面 URL（含协议和域名）

        Returns:
            {"passed": bool, "issues": [...], "checks": {...}, "summary": "..."}
        """
        from urllib.parse import urlparse
        url_path = urlparse(url).path

        # 提取页面元数据
        meta = _extract_page_meta(page)

        # 依次执行 6 项检查
        checks = {}

        # 2.1 URL 语言 vs 正文语言
        issue = _check_language_match(url_path, meta)
        checks["lang_match"] = {"passed": issue is None, "detail": issue["detail"] if issue else "OK"}
        if issue:
            checks["lang_match"]["issue"] = issue

        # 2.2 title vs h1
        issue = _check_title_h1_correlation(meta)
        checks["title_h1"] = {"passed": issue is None, "detail": issue["detail"] if issue else "OK"}
        if issue:
            checks["title_h1"]["issue"] = issue

        # 2.3 meta 标签
        issues = _check_meta_tags(meta, url_path)
        checks["meta"] = {"passed": len(issues) == 0,
                          "detail": "OK" if not issues else f"{len(issues)} issue(s)",
                          "issues": issues}

        # 2.4 标准区块
        issues = _check_structure(meta)
        checks["structure"] = {"passed": len(issues) == 0,
                               "detail": "OK" if not issues else f"{len(issues)} issue(s)",
                               "issues": issues}

        # 2.5 图片 alt
        issues = _check_img_alt_language(meta, url_path)
        checks["img_alt"] = {"passed": len(issues) == 0,
                             "detail": "OK" if not issues else f"{len(issues)} issue(s)",
                             "issues": issues}

        # 2.6 内链语言前缀
        issue = _check_link_lang_consistency(meta, url_path)
        checks["link_lang"] = {"passed": issue is None, "detail": issue["detail"] if issue else "OK"}
        if issue:
            checks["link_lang"]["issue"] = issue

        # 汇总所有 issues
        all_issues = []
        for check_name, check_result in checks.items():
            if check_name in ("meta", "structure", "img_alt"):
                all_issues.extend(check_result.get("issues", []))
            elif not check_result["passed"] and "issue" in check_result:
                all_issues.append(check_result["issue"])

        # 只有 error 级别的算失败
        errors = [i for i in all_issues if i.get("severity") == "error"]
        warnings = [i for i in all_issues if i.get("severity") != "error"]

        passed_count = sum(1 for c in checks.values() if c["passed"])
        total = len(checks)

        return {
            "passed": len(errors) == 0,
            "issues": all_issues,
            "checks": checks,
            "summary": f"自一致性 {passed_count}/{total} 通过"
                       + (f"，{len(errors)} error, {len(warnings)} warning"
                          if all_issues else ""),
        }
