"""
SEO 新页面 Layer 4: browser-use AI 交互探索（补充现有三层检测）

三层已有覆盖 → 本 layer 补充:
  Layer 1 (不变量) : 页面可访问、资源加载、按钮交互、console、内链、FAQ
  Layer 2 (自一致性): 语言/title-h1/meta/区块/图片alt/链接前缀
  Layer 3 (AI 审查) : 截图静态审查（布局/图片/乱码/CTA）   ← ai_page_review.py
  Layer 4 (AI 探索) : Agent 主动操作页面（滚动/点击/语义理解） ← **本文件**

和前几层的区别:
  - Layer 3 是"看图说话"（截图 → LLM 审查）
  - Layer 4 是"动手探索"（Agent 自己滚动、检查 DOM、验证交互逻辑）

运行方式:
  python -m pytest tests/test_seo_ai_explore.py -v -m seo_explore --alluredir=reports/allure-results
  或指定单个页面:
  python -m pytest tests/test_seo_ai_explore.py::test_ai_explore_single -v --url=/vi/tools/black-background-photo-editing
"""

import os
import json
import re
from pathlib import Path
from urllib.parse import urlparse

import pytest
import allure

HARNESS_ROOT = Path(__file__).parent.parent

from conftest import allure_screenshot, SCREENSHOT_DIR
from helpers.browser_use_explorer import (
    quick_seo_check,
    batch_seo_check,
    diagnose_failure,
    LANG_NAMES,
)
from helpers.simple_yaml import load_simple_yaml


# ═══════════════════════════════════════════════════════════════════
# 配置加载（和 test_seo_new_pages.py 保持一致）
# ═══════════════════════════════════════════════════════════════════

def _load_seo_new_pages():
    config_path = HARNESS_ROOT / "config" / "seo_new_pages.yaml"
    if not config_path.exists():
        return "", []
    data = load_simple_yaml(config_path)
    domain = os.getenv("SEO_DOMAIN", data.get("seo_domain", ""))
    pages = data.get("seo_pages", [])
    return domain, pages


SEO_DOMAIN, SEO_PAGES = _load_seo_new_pages()


def _detect_lang(path: str) -> str:
    m = re.match(r"^/([a-z]{2}(?:-[a-z]{2})?)/", path)
    return m.group(1) if m else "en"


# 仅对标记了 `ai_explore: true` 的路由执行（节省成本）
def _ai_explore_pages():
    config_path = HARNESS_ROOT / "config" / "seo_new_pages.yaml"
    if not config_path.exists():
        return []
    data = load_simple_yaml(config_path)
    domain = os.getenv("SEO_DOMAIN", data.get("seo_domain", ""))
    pages = data.get("seo_pages", [])
    return [
        p for p in pages
        if isinstance(p, dict) and p.get("ai_explore")
    ] or pages  # 如果没标记，默认全部检查


# ═══════════════════════════════════════════════════════════════════
# 测试用例
# ═══════════════════════════════════════════════════════════════════

@pytest.mark.seo_explore
class TestAISemanticExplore:
    """
    Layer 4: browser-use Agent 交互探索

    检查维度（传统脚本难做到的）:
      - 页面是否兑现了标题的承诺？（语义匹配）
      - 首屏是否包含核心信息？（标题 + 主视觉 + CTA）
      - 是否有 Thin Content（内容过少）？
      - 是否存在翻译残留（大段其他语言）？
      - OG/meta/schema/JSON-LD 标签是否完整？
      - Heading 层级是否合理（h1→h2→h3）？
      - 图片 alt 属性覆盖情况
    """

    def test_single_page_explore(self, page, base_url, request):
        """
        对单个页面执行 AI 交互探索。

        CLI 指定:
          pytest ... --url=/vi/tools/black-background-photo-editing
        """
        target_path = request.config.getoption("--url", default=None)
        if not target_path:
            pytest.skip("使用 --url=/vi/tools/... 指定要检查的页面")

        url = f"{base_url}{target_path}"
        lang = _detect_lang(target_path)
        lang_name = LANG_NAMES.get(lang, lang)

        allure.dynamic.title(f"AI Explore: {target_path}")
        allure.dynamic.description(f"URL: {url}\nLanguage: {lang_name}")

        with allure.step("AI 交互探索"):
            result = quick_seo_check(url, lang)

        # 将 AI 结果写入 Allure
        allure.attach(
            json.dumps(result.data, indent=2, ensure_ascii=False),
            name="AI Explore Result",
            attachment_type=allure.attachment_type.JSON,
        )

        # 断言
        if result.success:
            overall = result.data.get("overall", "skipped")
            if overall == "fail":
                issues = result.data.get("top_issues", [])
                pytest.fail(f"AI explore found critical issues: {'; '.join(issues[:5])}")

            # 具体检查项断言
            checks = [
                ("页面可访问", result.data.get("page_accessible") is not False),
                ("title 存在", bool(result.data.get("title"))),
                ("H1 存在", result.data.get("h1_count", 0) >= 1),
                ("非 thin content", not result.data.get("thin_content", True)),
            ]
            for label, passed in checks:
                if not passed:
                    allure.attach(
                        f"FAIL: {label}",
                        name=f"Check: {label}",
                        attachment_type=allure.attachment_type.TEXT,
                    )

            # 不强制 fail（AI 可能误判），但记录 warning
            for label, passed in checks:
                if not passed:
                    pytest.fail(f"AI 检查失败: {label}")
        else:
            pytest.skip(f"AI explore failed: {result.error}")

    def test_batch_ai_explore(self, page, base_url):
        """
        批量对新 SEO 页面执行 AI 探索（仅标记了 ai_explore 的页面）。

        在 seo_new_pages.yaml 中标记需要 AI 探索的页面:
          seo_pages:
            - path: /vi/tools/black-background-photo-editing
              ai_explore: true   # ← 加这个标记
        """
        pages = _ai_explore_pages()
        if not pages:
            pytest.skip("No pages marked for AI exploration")

        # 提取 path
        paths = []
        for p in pages:
            if isinstance(p, dict):
                paths.append(p.get("path", ""))
            else:
                paths.append(p)

        urls = [f"{base_url}{p}" for p in paths]

        allure.dynamic.title(f"AI Batch Explore ({len(urls)} pages)")
        allure.dynamic.description("Pages:\n" + "\n".join(f"- {u}" for u in urls))

        results = batch_seo_check(
            urls,
            max_pages=min(len(urls), 5),  # 一次最多 5 页，控制成本
        )

        # 汇总
        summary = {
            "total": len(results),
            "passed": sum(1 for r in results if r.data.get("overall") == "pass"),
            "warn": sum(1 for r in results if r.data.get("overall") == "warn"),
            "fail": sum(1 for r in results if r.data.get("overall") == "fail"),
            "skipped": sum(1 for r in results if r.data.get("overall") == "skipped"),
            "details": [
                {
                    "url": r.url,
                    "overall": r.data.get("overall"),
                    "top_issues": r.data.get("top_issues", []),
                    "top_strengths": r.data.get("top_strengths", []),
                }
                for r in results
            ],
        }

        allure.attach(
            json.dumps(summary, indent=2, ensure_ascii=False),
            name="AI Batch Explore Summary",
            attachment_type=allure.attachment_type.JSON,
        )

        fails = [d for d in summary["details"] if d["overall"] == "fail"]
        if fails:
            pytest.fail(
                f"AI explore found {len(fails)} pages with critical issues:\n"
                + "\n".join(f"  - {d['url']}: {d['top_issues']}" for d in fails)
            )

    def test_new_page_discovery_explore(self, page, base_url):
        """
        对完全未知的新页面执行探索——自动生成 page_map。

        用法: 在 seo_new_pages.yaml 中标记需要生成 page_map 的页面:
          seo_pages:
            - path: /vi/tools/new-tool
              generate_map: true
        """
        config_path = HARNESS_ROOT / "config" / "seo_new_pages.yaml"
        if not config_path.exists():
            pytest.skip("No config file")

        data = load_simple_yaml(config_path)

        pages_to_map = [
            p for p in data.get("seo_pages", [])
            if isinstance(p, dict) and p.get("generate_map")
        ]

        if not pages_to_map:
            pytest.skip("No pages marked with generate_map: true")

        page_map_dir = HARNESS_ROOT / "page_map" / "auto_generated"
        page_map_dir.mkdir(parents=True, exist_ok=True)

        from helpers.browser_use_explorer import explore_and_map

        for entry in pages_to_map:
            path = entry.get("path", "")
            url = f"{base_url}{path}"
            lang = _detect_lang(path)

            with allure.step(f"Explore & map: {path}"):
                result = explore_and_map(url)

                if result.success and result.data.get("yaml"):
                    # 保存生成的 page_map
                    safe_name = path.strip("/").replace("/", "_")
                    map_path = page_map_dir / f"{safe_name}.yaml"
                    map_path.write_text(result.data["yaml"], encoding="utf-8")

                    allure.attach(
                        result.data["yaml"],
                        name=f"Generated Page Map: {path}",
                        attachment_type=allure.attachment_type.YAML,
                    )

        print(f"Page maps saved to: {page_map_dir}")


# ═══════════════════════════════════════════════════════════════════
# 失败自动诊断 fixture（可在 conftest 层面使用）
# ═══════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=False)
def ai_failure_diagnosis(request, base_url):
    """
    测试失败时自动触发 AI 诊断。

    用法: 在测试函数参数中加上这个 fixture:
      def test_something(page, ai_failure_diagnosis):
          ...

    当测试失败时，browser-use Agent 会进入页面探索根因。
    """
    yield  # 先执行测试

    # 只在测试失败时触发
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        # 尝试从 request 中获取 URL
        test_url = getattr(request.node, "_test_url", None)
        if test_url:
            error_msg = str(request.node.rep_call.longrepr) if hasattr(request.node.rep_call, "longrepr") else "Unknown"
            diagnosis = diagnose_failure(test_url, error_msg[:500])

            allure.attach(
                json.dumps(diagnosis.data, indent=2, ensure_ascii=False),
                name="AI Failure Diagnosis",
                attachment_type=allure.attachment_type.JSON,
            )
