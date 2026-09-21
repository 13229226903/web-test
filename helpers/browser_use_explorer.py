"""
browser-use Agent 浏览器探索器 —— 对接 web-test 现有流水线

三种集成模式:

  模式 A: 探索新页面 → 自动生成 page_map YAML（替代 _explore/ 手工脚本）
  模式 B: 失败深度诊断 → 测试失败时自动进入页面探索根因
  模式 C: 独立 SEO 语义检查 → 补充 ai_page_review.py（截图审查）做不到的"页面内交互探索"

依赖:
  pip install browser-use

API Key: 使用 OPENAI_API_KEY

用法示例:

  # 模式 A: 探索页面并生成 page_map
  from helpers.browser_use_explorer import explore_and_map
  result = explore_and_map("http://10.17.1.66:3001/vi/tools/black-background-photo-editing")

  # 模式 B: 失败诊断（在 conftest 或 test teardown 中调用）
  from helpers.browser_use_explorer import diagnose_failure
  diagnosis = diagnose_failure("http://...", "页面空白，无内容渲染")

  # 模式 C: 在测试中作为补充检查层
  from helpers.browser_use_explorer import quick_seo_check
  result = quick_seo_check("http://...", expected_lang="vi")
"""

from __future__ import annotations

import asyncio
import io
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional
from urllib.parse import urlparse


def _force_utf8_stdio() -> None:
    """Windows 控制台默认 GBK，中文输出会崩；这里只重配置编码，不替换流对象。

    禁止写成 `sys.stdout = io.TextIOWrapper(sys.stdout.buffer, ...)`：在 pytest
    capture 下会接管 pytest 的临时流，收集结束时关闭它即报
    `ValueError: I/O operation on closed file.`（整仓 `pytest --collect-only` 退出码 1）。
    pytest 的 capture 流本身已是 UTF-8，故直接跳过。
    """
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None or type(stream).__module__.split(".")[0] == "_pytest":
            continue
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError, io.UnsupportedOperation, AttributeError):
            pass


if sys.platform == "win32":
    _force_utf8_stdio()


# ---------------------------------------------------------------------------
# 配置解析（复用项目 .env + Codex settings.json）
# ---------------------------------------------------------------------------
def _load_env():
    """加载项目 .env 文件（和 conftest.py 保持一致）"""
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k not in os.environ:
                        os.environ[k] = v
_load_env()


def _find_api_key() -> str | None:
    """读取 OpenAI API Key。"""
    val = os.getenv("OPENAI_API_KEY")
    return val if val and len(val) > 10 else None


def _get_llm_config() -> dict:
    return {
        "api_key": _find_api_key(),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
    }


# ---------------------------------------------------------------------------
# 浏览器生命周期管理（单例 CDP，避免反复启动）
# ---------------------------------------------------------------------------
_BROWSER_PROC: subprocess.Popen | None = None
_CDP_URL: str | None = None
_CDP_PORT = 9223


def _ensure_browser() -> str:
    """确保 Chromium CDP 可用，返回 cdp_url。已启动则复用。"""
    global _BROWSER_PROC, _CDP_URL
    if _CDP_URL:
        return _CDP_URL

    import urllib.request
    cdp = f"http://localhost:{_CDP_PORT}"

    # 已有 Chrome 在跑？
    try:
        urllib.request.urlopen(f"{cdp}/json/version", timeout=2)
        _CDP_URL = cdp
        return cdp
    except Exception:
        pass

    chrome_path = str(Path.home() / "AppData/Local/ms-playwright/chromium-1181/chrome-win/chrome.exe")
    _BROWSER_PROC = subprocess.Popen(
        [
            chrome_path,
            f"--remote-debugging-port={_CDP_PORT}",
            "--no-sandbox", "--disable-gpu", "--headless=new",
            "--disable-extensions", "--no-first-run",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    for i in range(15):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{cdp}/json/version", timeout=2)
            _CDP_URL = cdp
            return cdp
        except Exception:
            pass
    raise RuntimeError(f"Chrome CDP 启动失败 (port {_CDP_PORT})")


def _shutdown_browser():
    global _BROWSER_PROC, _CDP_URL
    if _BROWSER_PROC:
        _BROWSER_PROC.terminate()
        _BROWSER_PROC.wait()
        _BROWSER_PROC = None
    _CDP_URL = None


# ---------------------------------------------------------------------------
# 结果类型
# ---------------------------------------------------------------------------
@dataclass
class ExploreResult:
    url: str
    success: bool
    result_type: str                    # "page_map" | "diagnosis" | "seo_check"
    data: dict[str, Any] = field(default_factory=dict)
    raw_output: str = ""
    error: str = ""


# ---------------------------------------------------------------------------
# 通用 Agent 执行器
# ---------------------------------------------------------------------------
async def _run_agent(task: str, use_vision: bool = True) -> str:
    """执行单个 browser-use agent 任务，返回 final_result 文本。"""
    from browser_use import Agent
    from browser_use.llm import ChatOpenAI
    from browser_use.browser.profile import BrowserProfile

    cfg = _get_llm_config()
    if not cfg["api_key"]:
        return "[ERROR] No API key"

    llm = ChatOpenAI(
        model=cfg["model"], api_key=cfg["api_key"],
        base_url=cfg["base_url"], temperature=0, max_tokens=4096, max_retries=3,
    )

    cdp_url = _ensure_browser()

    agent = Agent(
        task=task,
        llm=llm,
        browser_profile=BrowserProfile(
            cdp_url=cdp_url, headless=True,
            disable_security=True, enable_default_extensions=False,
        ),
        use_vision=use_vision,
        max_failures=2,
        max_actions_per_step=3,
        step_timeout=120,
    )

    result = await agent.run()
    return result.final_result()


def _run_sync(task: str, use_vision: bool = True) -> str:
    """同步包装器"""
    try:
        return asyncio.run(_run_agent(task, use_vision))
    except Exception as exc:
        return f"[ERROR] {exc}"


def _parse_json(text: str, default: dict = None) -> dict:
    """从 LLM 输出中提取 JSON"""
    if default is None:
        default = {}
    txt = text.strip()
    for prefix, suffix in [("```json", "```"), ("```", "```")]:
        if prefix in txt:
            parts = txt.split(prefix, 1)
            if len(parts) > 1:
                txt = parts[1].split(suffix, 1)[0]
                break
    try:
        return json.loads(txt.strip())
    except json.JSONDecodeError:
        return default


# ═══════════════════════════════════════════════════════════════════
# 模式 A: 探索页面 → 生成 page_map YAML
# ═══════════════════════════════════════════════════════════════════

LANG_NAMES = {
    "zh": "Simplified Chinese", "zh-tw": "Traditional Chinese", "ja": "Japanese",
    "th": "Thai", "ru": "Russian", "vi": "Vietnamese", "id": "Indonesian",
    "pt": "Portuguese", "es": "Spanish", "fr": "French", "it": "Italian",
    "de": "German", "tr": "Turkish", "en": "English",
}


def explore_and_map(url: str) -> ExploreResult:
    """
    探索一个页面，生成 page_map YAML 格式的元素清单。

    这替代手工写 _explore/*.py 脚本的流程——Agent 自己滚动页面、
    识别按钮/链接/图片/表单，输出结构化 YAML。
    """
    parsed = urlparse(url)
    path = parsed.path
    lang_code = path.split("/")[1] if len(path.split("/")) > 2 else "en"
    lang_name = LANG_NAMES.get(lang_code, lang_code)

    task = f"""
Open: {url}

You are exploring this page to build a page_map YAML file for automated testing.
This page should be in {lang_name} ({lang_code}).

Do the following:
1. Wait for the page to fully load (network idle, all images loaded)
2. Scroll through the ENTIRE page slowly, from top to bottom
3. For each distinct section you find, note:
   - The section name/purpose
   - All interactive elements (buttons, links, inputs, selects, toggles, file uploads)
   - For each element: its visible text, HTML tag, type, and the most stable CSS selector
4. Pay special attention to:
   - Primary CTA buttons (Upload, Try Now, Start, etc.)
   - Navigation links and their destinations
   - Image/file upload zones
   - Modal/dialog triggers
   - Language switcher
   - Login/signup links

Return a JSON object with this structure (to be converted to YAML later):
{{
  "page_info": {{
    "url": "{url}",
    "title": "page title",
    "h1": "H1 text",
    "language": "{lang_code}",
    "tool_type": "background-remover/photo-enhancer/etc (inferred from content)"
  }},
  "sections": [
    {{
      "name": "hero/nav/features/how-to/cta/faq/footer/etc",
      "description": "what this section contains",
      "elements": [
        {{
          "label": "visible text or aria-label",
          "type": "button/link/input/select/img/upload/modal",
          "selector": "most stable CSS selector (no hash classes)",
          "action": "click/navigate/upload/toggle",
          "destination": "URL if it's a link, or null"
        }}
      ]
    }}
  ],
  "key_flows": [
    {{
      "name": "flow name (e.g. upload-image, try-sample)",
      "trigger_selector": "selector to start this flow",
      "steps_description": "what happens after triggering"
    }}
  ],
  "issues_found": ["any layout problems, broken elements, missing content"]
}}

IMPORTANT: Use stable selectors (role, aria-label, placeholder, href patterns, data attributes).
AVOID hash-based CSS classes like .css-1a2b3c.
For Vue/SPA components, prefer text-based selectors or data-tool-id attributes.
"""
    output = _run_sync(task, use_vision=True)
    data = _parse_json(output)

    # 同时生成 YAML 字符串
    yaml_str = _data_to_yaml(data, url)

    return ExploreResult(
        url=url,
        success=bool(data),
        result_type="page_map",
        data={
            "json": data,
            "yaml": yaml_str,
        },
        raw_output=output,
    )


def _data_to_yaml(data: dict, url: str) -> str:
    """将 explore 结果转为 page_map YAML 格式"""
    lines = [f"# Auto-generated by browser-use explorer", f"# URL: {url}", f"#", ""]

    info = data.get("page_info", {})
    lines.append(f"page:")
    lines.append(f"  url: \"{url}\"")
    lines.append(f"  title: \"{info.get('title', '')}\"")
    lines.append(f"  h1: \"{info.get('h1', '')}\"")
    lines.append(f"  language: \"{info.get('language', '')}\"")
    lines.append(f"  tool_type: \"{info.get('tool_type', '')}\"")
    lines.append("")

    for i, section in enumerate(data.get("sections", [])):
        name = section.get("name", f"section-{i}")
        lines.append(f"  # --- {name} ---")
        for elem in section.get("elements", []):
            label = elem.get("label", "").replace('"', "'")
            etype = elem.get("type", "button")
            selector = elem.get("selector", "")
            action = elem.get("action", "click")
            dest = elem.get("destination", "")
            lines.append(f"  - label: \"{label}\"")
            lines.append(f"    type: {etype}")
            lines.append(f"    selector: \"{selector}\"")
            lines.append(f"    action: {action}")
            if dest:
                lines.append(f"    destination: \"{dest}\"")
        lines.append("")

    lines.append(f"  key_flows:")
    for flow in data.get("key_flows", []):
        lines.append(f"    - name: \"{flow.get('name', '')}\"")
        lines.append(f"      trigger: \"{flow.get('trigger_selector', '')}\"")
        lines.append(f"      steps: \"{flow.get('steps_description', '')}\"")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 模式 B: 失败诊断
# ═══════════════════════════════════════════════════════════════════

def diagnose_failure(url: str, failure_description: str) -> ExploreResult:
    """
    当测试失败时，让 Agent 进入页面探索，诊断根因。

    典型用法（在 conftest tear-down 或 test 的 except 块中）:

        try:
            test_something(page)
        except Exception as e:
            diagnosis = diagnose_failure(url, str(e))
            allure.attach(diagnosis.raw_output, "AI Failure Diagnosis")
            raise
    """
    task = f"""
Open: {url}

This page FAILED an automated test. The failure description is:

  "{failure_description}"

Your job is to open the page and diagnose WHY it failed. Consider:
1. Is the page returning 404/500?
2. Is the page blank/empty (SPA not rendered)?
3. Are key elements missing or their selectors changed?
4. Are images/resources failing to load?
5. Is there a modal/overlay blocking interaction?
6. Is the language wrong?
7. Is there a visible error message on the page?
8. Is the page redirecting unexpectedly?

Scroll through the page, inspect elements, and return JSON:
{{
  "page_loads": true/false,
  "http_status_like": "200/404/500/unknown",
  "blank_page": true/false,
  "error_visible_on_page": true/false,
  "error_message_text": "visible error text if any",
  "root_cause": "your best guess at the root cause",
  "suggested_fix": "how to fix the test or page",
  "key_elements_found": ["list of elements found"],
  "key_elements_missing": ["elements expected but not found"]
}}
"""
    output = _run_sync(task, use_vision=True)
    data = _parse_json(output)

    return ExploreResult(
        url=url,
        success=bool(data),
        result_type="diagnosis",
        data=data,
        raw_output=output,
    )


# ═══════════════════════════════════════════════════════════════════
# 模式 C: 快速 SEO 语义检查（补充 ai_page_review.py）
# ═══════════════════════════════════════════════════════════════════

def quick_seo_check(url: str, expected_lang: str = "en", hints: str | None = None) -> ExploreResult:
    """
    快速 SEO 语义质量检查。

    和现有 ai_page_review.py 的分工:
      - ai_page_review.py: 截图 → 静态视觉审查（布局/图片/乱码/CTA可见性）
      - browser_use:      Agent 主动探索 → 交互验证（滚动/点击/页面跳转/动态内容）

    调用示例:
      from helpers.browser_use_explorer import quick_seo_check
      result = quick_seo_check(current_url, "vi")
      if result.data.get("overall") == "fail":
          issues.extend(result.data.get("top_issues", []))
    """
    lang_name = LANG_NAMES.get(expected_lang, expected_lang)

    hint_block = ""
    if hints:
        hint_block = f"""

Page hints extracted from the current DOM / spec:
{hints[:4000]}

Use these hints as clues only. Do not require exact wording matches.
"""

    task = f"""
Open: {url}

You are an SEO auditor. This page should be in {lang_name} ({expected_lang}).

Quick scan (scroll the full page) and return JSON:

{{
  "page_accessible": true/false,
  "status_like": "normal/404/500/blank",
  "title": "page <title> text",
  "meta_description": "meta description content or empty",
  "h1": "H1 text",
  "h1_count": number,
  "h2_count": number,
  "total_images": estimate,
  "images_no_alt": estimate,
  "primary_cta": "main button text",
  "language_observed": "{expected_lang}/en/mixed",
  "thin_content": true/false,
  "has_og_tags": true/false,
  "has_canonical": true/false,
  "has_jsonld": true/false,
  "overall": "pass/warn/fail",
  "top_issues": ["top 3 SEO issues"],
  "top_strengths": ["top 3 strengths"]
}}

Return only JSON, no markdown wrapping.
{hint_block}
"""
    output = _run_sync(task, use_vision=True)
    data = _parse_json(output)

    return ExploreResult(
        url=url,
        success=bool(data),
        result_type="seo_check",
        data=data,
        raw_output=output,
    )


# ═══════════════════════════════════════════════════════════════════
# 模式 D: 批量 SEO 页面深度探索（配合 test_seo_new_pages.py）
# ═══════════════════════════════════════════════════════════════════

def batch_seo_check(
    urls: list[str],
    max_pages: int = 10,
    on_progress: Callable[[int, int, str], None] = None,
) -> list[ExploreResult]:
    """
    批量 SEO 语义检查——复用在 conftest 中定义的语言推断逻辑。

    参数:
        urls: 完整 URL 列表
        max_pages: 最多检查页数（控制成本）
        on_progress: 进度回调 (done, total, current_url)

    返回: ExploreResult 列表，失败不中断
    """
    results: list[ExploreResult] = []

    # 语言代码推断（复用 rule.md 中的 13 语言列表）
    SUPPORTED_LANGS = [
        "zh", "zh-tw", "fr", "id", "de", "vi", "tr",
        "it", "pt", "es", "ru", "ja", "th",
    ]

    try:
        for i, url in enumerate(urls[:max_pages]):
            if on_progress:
                on_progress(i + 1, min(len(urls), max_pages), url)

            # 从 URL path 推断语言
            path = urlparse(url).path
            parts = [p for p in path.split("/") if p]
            lang = parts[0].lower() if parts and parts[0].lower() in SUPPORTED_LANGS else "en"

            result = quick_seo_check(url, lang)
            results.append(result)

    finally:
        _shutdown_browser()

    return results


# ---------------------------------------------------------------------------
# CLI 入口（可直接执行）
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="browser-use Explorer for web-test")
    sub = parser.add_subparsers(dest="command")

    # explore
    p_explore = sub.add_parser("explore", help="Explore page and generate page_map YAML")
    p_explore.add_argument("url")

    # diagnose
    p_diag = sub.add_parser("diagnose", help="Diagnose a test failure")
    p_diag.add_argument("url")
    p_diag.add_argument("--reason", default="Unknown failure")

    # seo
    p_seo = sub.add_parser("seo", help="Quick SEO check")
    p_seo.add_argument("url")
    p_seo.add_argument("--lang", default="en")

    # batch
    p_batch = sub.add_parser("batch", help="Batch SEO check from file")
    p_batch.add_argument("file", type=Path, help="JSON file with URLs or newline-separated list")
    p_batch.add_argument("--max", type=int, default=5)

    args = parser.parse_args()

    if args.command == "explore":
        r = explore_and_map(args.url)
        print(f"Success: {r.success}")
        print(r.data.get("yaml", r.raw_output[:2000]))

    elif args.command == "diagnose":
        r = diagnose_failure(args.url, args.reason)
        print(f"Root cause: {r.data.get('root_cause', 'unknown')}")
        print(json.dumps(r.data, indent=2, ensure_ascii=False))

    elif args.command == "seo":
        r = quick_seo_check(args.url, args.lang)
        print(f"Overall: {r.data.get('overall', 'skipped')}")
        print(json.dumps(r.data, indent=2, ensure_ascii=False))

    elif args.command == "batch":
        if args.file.suffix == ".json":
            urls = json.loads(args.file.read_text())
        else:
            urls = [l.strip() for l in args.file.read_text().splitlines() if l.strip()]
        results = batch_seo_check(urls, max_pages=args.max)
        for r in results:
            print(f"{r.url} → {r.data.get('overall', 'skipped')}")
            if r.data.get("top_issues"):
                for issue in r.data["top_issues"]:
                    print(f"  ❌ {issue}")

    _shutdown_browser()

