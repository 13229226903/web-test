"""SEO 内链校验：404 检测 + 语言前缀一致性。

用法：
    from helpers.link_checker import check_internal_links
    issues = check_internal_links(page, "http://10.17.1.66:3001", "/de/tools/some-page")
    for issue in issues:
        allure.attach(issue, name="内链问题", attachment_type=allure.attachment_type.TEXT)
    assert len(issues) == 0, f"内链问题: {issues}"
"""

import re
import time
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse

LANG_NEUTRAL_PATHS = {
    "/privacy-policy",
    "/term-of-use",
}


def _extract_lang_prefix(path: str) -> str:
    """从 URL 路径提取语言前缀,无前缀返回 ''。"""
    m = re.match(r"^/([a-z]{2})(?:-[a-z]{2})?(?:/|$)", path)
    return m.group(1) if m else ""


def _same_lang(link_path: str, prefix: str) -> bool:
    """链接前缀是否与当前页一致。

    - 有语言前缀的页面：内链必须使用相同前缀
    - 无语言前缀的页面：内链也必须无前缀
    - LANG_NEUTRAL_PATHS 中的路径视为语言无关页
    """
    if link_path in LANG_NEUTRAL_PATHS:
        return True
    lp = _extract_lang_prefix(link_path)
    return lp == prefix if prefix else not lp


def _is_internal(href: str, base_url: str) -> bool:
    """判断链接是否同域内链。"""
    parsed = urlparse(href)
    if parsed.netloc and parsed.netloc not in urlparse(base_url).netloc:
        return False
    return True


def check_internal_links(page, base_url: str, main_path: str, max_links: int = 25):
    """校验当前页面的内链。

    Args:
        page: Playwright Page 对象
        base_url: 站点根 URL（如 http://10.17.1.66:3001）
        main_path: 当前页面路径（如 /de/tools/photo-enhancer）
        max_links: 最多检查的内链数

    Returns:
        list[str]: 问题列表，空列表表示全部通过
    """
    main_lang = _extract_lang_prefix(main_path)

    # 1) 采集页面中所有 a[href] 内链（去重 + 排重）
    raw_links = page.evaluate("""() => {
        var seen = {};
        var out = [];
        document.querySelectorAll('a[href]').forEach(function(a) {
            var href = a.getAttribute('href') || '';
            // 跳过 JS 伪协议、锚点、邮件、电话
            if (!href || href.startsWith('#') || href.startsWith('javascript:') ||
                href.startsWith('mailto:') || href.startsWith('tel:')) return;
            if (!seen[href]) { seen[href] = true; out.push(href); }
        });
        return out;
    }""")

    # 2) 过滤同域内链、解析完整 URL；排除含非法字符的脏数据
    internal = []
    for href in raw_links:
        # href 中不应含 HTML 标签或控制字符（页面 HTML 格式异常导致）
        if re.search(r"[<>\"'\n\r\t]|</|/>|>", href):
            continue
        try:
            full = urljoin(base_url, href)
        except Exception:
            continue
        if _is_internal(full, base_url):
            path = urlparse(full).path
            if path and path != "/":
                # path 本身也应合法
                if re.search(r"[<>\"'\n\r\t]", path):
                    continue
                internal.append({"href": href, "full": full, "path": path})

    # 3) 取最多 max_links 条（排除资源链接 + 含非法字符的 URL）
    internal = [l for l in internal if not re.search(r"\.(png|jpg|jpeg|gif|svg|webp|ico|css|js|woff2?|ttf|pdf|xml|json)$", l["path"], re.I)]
    internal = internal[:max_links]

    issues = []
    checked = set()

    for link in internal:
        path = link["path"]
        if path in checked:
            continue
        checked.add(path)

        # ---- 404 检测 ----
        try:
            req = urllib.request.Request(link["full"], method="HEAD")
            req.add_header("User-Agent", "Mozilla/5.0")
            resp = urllib.request.urlopen(req, timeout=15)
            if resp.status >= 400:
                issues.append(f"[HTTP {resp.status}] {link['full']}")
        except urllib.error.HTTPError as e:
            issues.append(f"[HTTP {e.code}] {link['full']}")
        except Exception as e:
            # 网络错误(超时/TLS etc.)不阻断，记录为 warning 级别
            issues.append(f"[WARN 请求失败] {link['full']} ({e})")
            time.sleep(0.5)
            continue

        # ---- 语言前缀一致性 ----
        if not _same_lang(path, main_lang):
            link_lang = _extract_lang_prefix(path)
            issues.append(
                f"[语言不一致] 主页={main_lang or '(无前缀)'} 链接={link_lang or '(无前缀)'}: {link['full']}"
            )

        time.sleep(0.3)  # 节流

    return issues


def verify_seo_links(page, base_url: str, path: str, max_links: int = 15):
    """校验 SEO 页面内链 + 附加结果到 Allure。不硬断言,只记录。"""
    import allure as _allure
    issues = check_internal_links(page, base_url, path, max_links=max_links)
    result = "通过" if not issues else f"{len(issues)} 个问题"
    _allure.attach(
        "\n".join(issues) if issues else "全部内链正常 (无 404, 语言前缀一致/无前缀页保持无前缀)",
        name=f"内链校验: {result}",
        attachment_type=_allure.attachment_type.TEXT,
    )
    return issues
