"""
首页内链点击访问 + 404 检测（全语言，含卡片链接）

运行:
  python scripts/check_homepage_internal_links.py

关键点（用户确认）:
  - 首页内链有两种形态: 文本链接 + 卡片链接
  - 卡片是 <a href> 包裹的样式化 div, 但需要滚动页面才会懒加载出现
  - 顶部导航 "所有工具" 下拉菜单需要 hover 才渲染出工具链接
  - 英文首页用 /en（/ 会被按浏览器/地理重定向到其它语言, 不可靠）

流程（每个语言首页）:
  1. goto /{lang} (英文用 /en), 等 networkidle
  2. hover "所有工具" 菜单 → 采菜单工具链接
  3. 滚动整页触发卡片懒加载 → 采卡片链接
  4. 合并去重 → 逐个 goto 检测 404 (HTTP 状态 + 页面内容多信号)
  5. 输出 JSON 报告 + 控制台汇总
"""
import asyncio
import io
import json
import re
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)

from playwright.async_api import async_playwright

BASE_URL = "http://10.17.1.66:3001"
CDP_PORT = 9223

# 权威语言清单（来自首页 hreflang）: en, zh, zh-tw, es, pt, ru, id, th, ja, fr, it, vi, tr, de
# 英文用 /en（/ 会被重定向）
LANGUAGES = [
    ("en", "English"),
    ("vi", "Vietnamese"),
    ("zh", "Chinese Simplified"),
    ("zh-tw", "Chinese Traditional"),
    ("es", "Spanish"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("id", "Indonesian"),
    ("th", "Thai"),
    ("ja", "Japanese"),
    ("fr", "French"),
    ("it", "Italian"),
    ("tr", "Turkish"),
    ("de", "German"),
]

RESOURCE_EXT = re.compile(r"\.(png|jpg|jpeg|gif|svg|webp|ico|css|js|woff2?|ttf|pdf|xml|json|mp4|webm)$", re.I)

_BROWSER_PROC = None
_CDP_URL = None


def _ensure_browser():
    global _BROWSER_PROC, _CDP_URL
    if _CDP_URL:
        return _CDP_URL
    cdp = f"http://localhost:{CDP_PORT}"
    try:
        urllib.request.urlopen(f"{cdp}/json/version", timeout=2)
        _CDP_URL = cdp
        return cdp
    except Exception:
        pass
    chrome_path = str(Path.home() / "AppData/Local/ms-playwright/chromium-1181/chrome-win/chrome.exe")
    _BROWSER_PROC = subprocess.Popen(
        [chrome_path, f"--remote-debugging-port={CDP_PORT}", "--no-sandbox",
         "--disable-gpu", "--headless=new", "--disable-extensions", "--no-first-run", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for _ in range(15):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{cdp}/json/version", timeout=2)
            _CDP_URL = cdp
            return cdp
        except Exception:
            pass
    raise RuntimeError("Chrome CDP start failed")


async def _extract_rel_links(page) -> list[str]:
    """采集所有相对路径的 a[href]（含卡片链接，卡片即 <a href> 包裹的 div）"""
    return await page.evaluate("""() => {
        const s = new Set();
        document.querySelectorAll('a[href]').forEach(a => {
            let h = (a.getAttribute('href') || '').trim();
            if (h.startsWith('/') && h !== '/') s.add(h);
        });
        return Array.from(s);
    }""")


async def _hover_tools_menu(page):
    """hover '所有工具' 菜单触发下拉渲染。不同语言文本不同，用 href 结尾 /tools 定位。"""
    for sel in ['a[href$="/tools"]', 'a[href="/tools"]']:
        try:
            loc = page.locator(sel).first
            if await loc.count() > 0:
                await loc.hover()
                await page.wait_for_timeout(1200)
                return True
        except Exception:
            continue
    return False


async def _scroll_to_load_cards(page):
    """滚动整页触发卡片懒加载，然后回到顶部。"""
    for _ in range(15):
        await page.mouse.wheel(0, 2200)
        await page.wait_for_timeout(350)
    # 再向上滚一段，确保中部卡片也触发（IntersectionObserver 双向）
    await page.mouse.wheel(0, 500)
    await page.wait_for_timeout(300)
    # 回顶部，保证 header 菜单在可视区
    await page.evaluate("window.scrollTo(0, 0)")
    await page.wait_for_timeout(400)


def _filter_internal(rel_links: list[str]) -> list[dict]:
    """把相对 href 过滤为唯一内部链接（去资源/外链/锚点），保留 query 用于 help 联系页。"""
    out = []
    seen = set()
    for href in rel_links:
        if re.search(r"[<>\"'\n\r\t]", href):
            continue
        try:
            full = urljoin(BASE_URL, href)
        except Exception:
            continue
        parsed = urlparse(full)
        if parsed.netloc and parsed.netloc != urlparse(BASE_URL).netloc:
            continue
        path = parsed.path or "/"
        if path == "/":
            continue
        if RESOURCE_EXT.search(path):
            continue
        if path in seen:
            continue
        seen.add(path)
        out.append({"href": href, "full": full, "path": path})
    return out


def _detect_404(status, body, url):
    """多信号判断 404 / 错误页"""
    if status is not None:
        if status == 404:
            return True
        if status >= 500:
            return True
    low = body.lower()
    if re.search(r"404[^\d]|page not found|not found|找不到|未找到|页面不存在|seite nicht gefunden|ページが見つかりません|erreur 404", low):
        return True
    return False


async def main():
    print("=" * 70)
    print("Homepage Internal Links Check (All Languages, incl. cards)")
    print(f"Target: {BASE_URL}")
    print("=" * 70)

    cdp = _ensure_browser()
    report = {"target": BASE_URL, "timestamp": datetime.now().isoformat(), "languages": []}

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        for lang, name in LANGUAGES:
            home_url = BASE_URL + f"/{lang}"
            print(f"\n{'='*60}")
            print(f"[{lang}] {name}  {home_url}")
            print("=" * 60)

            try:
                resp = await page.goto(home_url, wait_until="networkidle", timeout=45000)
                status = resp.status if resp else None
            except Exception as e:
                print(f"  ERROR navigate: {e}")
                report["languages"].append({"lang": lang, "home": home_url, "home_status": -1, "links": []})
                continue

            await page.wait_for_timeout(1500)
            home_body = await page.evaluate("document.body ? document.body.innerText : ''")
            home_is_404 = _detect_404(status, home_body, home_url)
            print(f"  Home status={status}, is_404={home_is_404}")

            # 1) hover 菜单 → 采菜单链接
            hovered = await _hover_tools_menu(page)
            menu_links = await _extract_rel_links(page)

            # 2) 滚动 → 采卡片链接
            await _scroll_to_load_cards(page)
            card_links = await _extract_rel_links(page)

            merged = list(set(menu_links) | set(card_links))
            print(f"  菜单 hover={'Y' if hovered else 'N'}, 菜单链接 {len(menu_links)}, 滚动后链接 {len(card_links)}, 合并 {len(merged)}")

            internal = _filter_internal(merged)
            print(f"  内部链接去重后: {len(internal)}")

            results = []
            for link in internal:
                full = link["full"]
                try:
                    resp = await page.goto(full, wait_until="domcontentloaded", timeout=30000)
                    st = resp.status if resp else None
                except Exception as e:
                    results.append({"href": link["href"], "full": full, "status": None, "is_404": True, "note": f"nav error: {str(e)[:60]}"})
                    print(f"    [ERR] {full} ({str(e)[:50]})")
                    continue

                await page.wait_for_timeout(600)
                body = await page.evaluate("document.body ? document.body.innerText : ''")
                is_404 = _detect_404(st, body, full)
                results.append({
                    "href": link["href"], "full": full, "status": st, "is_404": is_404,
                    "title": (await page.title())[:80] if not is_404 else "",
                })
                flag = "404/ERR" if is_404 else "OK"
                print(f"    [{flag}] {st} {full}")

            ok_count = sum(1 for r in results if not r["is_404"])
            bad_count = sum(1 for r in results if r["is_404"])
            print(f"  Summary: {ok_count} OK, {bad_count} 404/err, {len(results)} total")

            report["languages"].append({
                "lang": lang, "name": name, "home": home_url,
                "home_status": status, "home_is_404": home_is_404,
                "internal_count": len(internal),
                "ok": ok_count, "bad": bad_count, "results": results,
            })

    # 汇总
    print("\n" + "=" * 70)
    print("FINAL REPORT")
    print("=" * 70)
    all_bad = []
    total_ok = total_bad = 0
    for e in report["languages"]:
        ok, bad = e["ok"], e["bad"]
        total_ok += ok
        total_bad += bad
        print(f"\n[{e['lang']}] {e['name']}: {ok} OK, {bad} 404/err, {e['internal_count']} links")
        for r in e["results"]:
            if r["is_404"]:
                all_bad.append({"lang": e["lang"], **r})
                print(f"    ❌ {r.get('full') or r.get('href')} (status={r.get('status')})")

    print(f"\n{'='*60}")
    print(f"TOTAL: {total_ok} OK, {total_bad} 404/err")
    if all_bad:
        print(f"\nAll 404/error links ({len(all_bad)}):")
        for b in all_bad:
            print(f"  [{b['lang']}] {b.get('full') or b.get('href')} -> status={b.get('status')}")

    out_dir = Path("d:/Test/reports/homepage_links")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"homepage_links_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nReport saved: {report_path}")

    global _BROWSER_PROC
    if _BROWSER_PROC:
        _BROWSER_PROC.terminate()
        _BROWSER_PROC.wait()

    return report


if __name__ == "__main__":
    asyncio.run(main())
