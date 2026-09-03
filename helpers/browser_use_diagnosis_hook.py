"""
browser-use 失败诊断 Hook —— 直接插入 conftest.py 使用

在 conftest.py 中添加以下代码即可启用自动失败诊断：

    # conftest.py 追加内容:
    from helpers.browser_use_diagnosis_hook import install_diagnosis_hook
    install_diagnosis_hook()

当任何测试失败时，browser-use Agent 会:
  1. 打开失败时的页面 URL
  2. 交互探索（滚动/检查 DOM/看 console）
  3. 输出根因分析和修复建议
  4. 将诊断结果写入 allure 附件

成本控制:
  - 仅在 --headed 模式下启用（调试时）
  - 或设置环境变量 AI_DIAGNOSIS=true 强制启用
  - 每轮最多诊断 3 个失败（避免 API 费用爆炸）
"""

import os
import json
from pathlib import Path
from typing import Optional


_DIAGNOSIS_COUNT = 0
_MAX_DIAGNOSIS_PER_RUN = 3

# URL 记录器 —— 和 page fixture 配合使用
_current_url: Optional[str] = None


def record_page_url(url: str):
    """记录当前页面 URL（在测试中调用）。"""
    global _current_url
    _current_url = url


def install_diagnosis_hook():
    """
    安装 pytest 失败诊断 hook。

    在 conftest.py 末尾添加:
        from helpers.browser_use_diagnosis_hook import install_diagnosis_hook
        install_diagnosis_hook()
    """
    import pytest

    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(item, call):
        outcome = yield
        report = outcome.get_result()

        # 仅在测试 call 阶段（非 setup/teardown）且失败时触发
        if report.when != "call" or not report.failed:
            return

        global _DIAGNOSIS_COUNT
        if _DIAGNOSIS_COUNT >= _MAX_DIAGNOSIS_PER_RUN:
            return

        # 检查是否启用
        enabled = (
            os.getenv("AI_DIAGNOSIS", "").lower() == "true"
            or item.config.getoption("--headed", default=False)
        )
        if not enabled:
            return

        global _current_url
        if not _current_url:
            return

        _DIAGNOSIS_COUNT += 1

        try:
            from helpers.browser_use_explorer import diagnose_failure

            failure_msg = str(report.longrepr)[:500] if hasattr(report, "longrepr") else "Unknown"

            # 在 Allure 存在时附加诊断结果
            try:
                import allure

                with allure.step(f"[AI Diagnosis #{_DIAGNOSIS_COUNT}] Analyzing: {_current_url}"):
                    result = diagnose_failure(_current_url, failure_msg)

                    allure.attach(
                        json.dumps({
                            "url": _current_url,
                            "root_cause": result.data.get("root_cause", ""),
                            "suggested_fix": result.data.get("suggested_fix", ""),
                            "key_elements_found": result.data.get("key_elements_found", []),
                            "key_elements_missing": result.data.get("key_elements_missing", []),
                        }, indent=2, ensure_ascii=False),
                        name=f"AI Diagnosis #{_DIAGNOSIS_COUNT}: {result.data.get('root_cause', 'Unknown')[:80]}",
                        attachment_type=allure.attachment_type.JSON,
                    )
            except ImportError:
                # Allure 不可用，静默跳过
                pass

        except Exception:
            # 诊断失败不应影响主测试流程
            pass


# ═══════════════════════════════════════════════════════════════════
# 便捷使用方式（无需改 conftest）
# ═══════════════════════════════════════════════════════════════════

def diagnose_current_page(page_url: str, error: str) -> dict:
    """
    在测试代码中直接调用诊断。

    Usage:
        try:
            do_something_that_might_fail(page)
        except Exception as e:
            diagnosis = diagnose_current_page(page.url, str(e))
            print(diagnosis["root_cause"])
            raise
    """
    from helpers.browser_use_explorer import diagnose_failure
    result = diagnose_failure(page_url, error)
    return result.data
