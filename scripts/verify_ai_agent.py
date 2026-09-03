"""
验证 browser-use Agent 在当前 Pokecut 环境下能否正常工作。

用法：
    cd d:/Test/web-test
    python scripts/verify_ai_agent.py

前置条件：
    - pip install browser-use（已完成）
    - .env 中配置了有效的 OPENAI_API_KEY
"""
import sys
import asyncio
import io
from pathlib import Path

# 修复 Windows GBK 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 确保项目根在 path 中
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from helpers.ai_agent import (
    ai_run_test,
    _get_llm,
    DEFAULT_BASE_URL,
)


async def main():
    print("=" * 60)
    print("browser-use Agent 验证")
    print("=" * 60)

    # 1. 验证 LLM
    print("\n[1/3] 验证 LLM 连接...")
    try:
        llm = _get_llm()
        model_name = getattr(llm, 'model', str(llm))
        print(f"  [OK] LLM 初始化成功: {model_name}")
    except Exception as e:
        print(f"  [FAIL] LLM 初始化失败: {e}")
        return 1

    # 2. 验证浏览器启动
    print("\n[2/3] 验证浏览器启动...")
    try:
        from browser_use import Browser, BrowserProfile

        browser = Browser(
            browser_profile=BrowserProfile(
                headless=True,
                disable_security=True,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
            )
        )
        print("  [OK] Browser 对象创建成功")
        await browser.close()
    except Exception as e:
        print(f"  [FAIL] 浏览器启动失败: {e}")
        return 1

    # 3. 执行最小探索任务
    print("\n[3/3] 执行最小探索任务...")
    print(f"     目标: 打开 Pokecut 首页 {DEFAULT_BASE_URL}")
    print("     (无头模式，仅截图观察，约 30-60 秒)")

    result = await ai_run_test(
        task=(
            "Navigate to the website, observe the homepage content. "
            "Describe what main feature sections and buttons you see. "
            "Do not click anything, just observe and report what's on the page."
        ),
        base_url=DEFAULT_BASE_URL,
        headless=True,
    )

    if result["success"]:
        print(f"  [OK] Agent 任务执行成功")
        print(f"     总步数: {result['total_steps']}")
        final = result.get('final_result') or ''
        print(f"     Agent 报告:\n{str(final)[:500]}")
    else:
        print(f"  [WARN] Agent 执行失败: {result.get('error', '未知')}")
        final = result.get('final_result') or ''
        print(f"     部分结果:\n{str(final)[:500]}")

    print("\n" + "=" * 60)
    print("验证完成")
    print("=" * 60)
    return 0 if result["success"] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
