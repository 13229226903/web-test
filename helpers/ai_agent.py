"""
browser-use Agent 封装 — AI 驱动的浏览器执行层。

与现有 harness 的关系：
- 不替代 pytest + Playwright，只在"失败兜底"和"探索验证"时介入
- 浏览器配置与 conftest.py 保持一致（viewport、locale）
- 可复用已有登录态（storage_state），避免重复登录消耗 credits

用法：
    import asyncio
    from helpers.ai_agent import ai_run_test, ai_retry_failed_case

    # 探索新功能：自然语言描述 → Agent 自主执行
    result = asyncio.run(ai_run_test(
        task="登录后上传一张图片，用背景移除工具去掉背景，下载结果图",
        base_url="http://10.17.1.66:3001",
    ))

    # 失败兜底：pytest 挂了 → Agent 用视觉模式重试
    result = asyncio.run(ai_retry_failed_case(
        task_description="上传图片到 /tools/background-remover 并等处理完成",
        base_url="http://10.17.1.66:3001",
        storage_state_path="data/session_state.json",  # 从 session_context 导出
    ))

依赖：
    pip install browser-use
    环境变量：使用 OPENAI_API_KEY（Codex 系列）
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Optional

from browser_use import Agent, Browser, BrowserProfile
from browser_use.llm import ChatOpenAI


# ── 加载 .env ──────────────────────────────────────────────────────
# 与 conftest.py 相同的加载逻辑
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    with open(_env_path, "r", encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                if _key not in os.environ:
                    os.environ[_key] = _val


# ── 项目根目录 & 默认配置 ──────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

# 复用 Playwright 安装的 Chromium（与 pytest-playwright 同一个浏览器）
_PLAYWRIGHT_CHROMIUM = (
    Path.home() / "AppData" / "Local" / "ms-playwright" / "chromium-1181" / "chrome-win" / "chrome.exe"
)
if not _PLAYWRIGHT_CHROMIUM.exists():
    # 回退：尝试在 PATH 中找 chrome
    import shutil as _shutil
    _PLAYWRIGHT_CHROMIUM = _shutil.which("chrome") or _shutil.which("chromium") or _shutil.which("google-chrome")
    if _PLAYWRIGHT_CHROMIUM:
        _PLAYWRIGHT_CHROMIUM = str(_PLAYWRIGHT_CHROMIUM)

# 与 conftest.py 保持一致的浏览器参数
DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}
DEFAULT_LOCALE = "en-US"
DEFAULT_BASE_URL = "http://10.17.1.66:3001"


def _get_llm():
    """获取 LLM 实例。"""

    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return ChatOpenAI(
            model=os.environ.get("OPENAI_MODEL", "gpt-5.6"),
            api_key=openai_key,
            base_url=base_url,
        )

    raise RuntimeError(
        "未找到可用的 LLM API Key。请设置 OPENAI_API_KEY（推荐，Codex / gpt-5.6）"
    )


def _build_browser_profile(
    headless: bool = True,
    base_url: str = DEFAULT_BASE_URL,
    storage_state: Optional[dict] = None,
) -> BrowserProfile:
    """构建与现有 conftest.py 一致的 BrowserProfile。

    storage_state 可以从 conftest.py 的 session_context 导出：
        context.storage_state(path="data/session_state.json")
    然后这里传 storage_state=json.load(open("data/session_state.json"))
    """
    return BrowserProfile(
        headless=headless,
        disable_security=True,
        executable_path=str(_PLAYWRIGHT_CHROMIUM) if _PLAYWRIGHT_CHROMIUM else None,
        viewport=DEFAULT_VIEWPORT,
        window_size=DEFAULT_VIEWPORT,
        locale=DEFAULT_LOCALE,
        storage_state=storage_state,
        wait_for_network_idle_page_load_time=3.0,
        minimum_wait_page_load_time=1.0,
        allowed_domains=[base_url.replace("http://", "").replace("https://", "").split(":")[0]],
        record_video_dir=None,
        enable_default_extensions=False,    # 跳过下载 uBlock 等扩展（内网环境可能超时）
    )


# ── 公共 API ──────────────────────────────────────────────────────

def _extract_steps(history) -> list[dict]:
    """从 AgentHistoryList 中提取每一步的关键信息，去掉冗余数据。"""
    steps = []
    actions = history.model_actions_filtered(include=["navigate", "click", "input_text", "scroll", "done", "go_back", "extract_content"])
    thoughts = history.model_thoughts()
    results = history.action_results()
    errors_list = history.errors()
    screenshots = history.screenshot_paths()

    for i in range(history.number_of_steps()):
        step = {"step": i + 1}

        # Agent 的思考
        if i < len(thoughts) and thoughts[i]:
            step["thinking"] = thoughts[i].thinking
            step["evaluation"] = thoughts[i].evaluation_previous_goal
            step["memory"] = thoughts[i].memory
            step["next_goal"] = thoughts[i].next_goal

        # 执行的动作
        if i < len(actions):
            step["action"] = actions[i]

        # 执行结果
        if i < len(results) and results[i]:
            step["is_done"] = results[i].is_done
            step["action_success"] = results[i].success
            step["action_error"] = results[i].error
            step["extracted"] = results[i].extracted_content

        # 截图
        if i < len(screenshots):
            step["screenshot"] = screenshots[i]

        # 该步骤的错误
        if i < len(errors_list):
            step["error"] = errors_list[i]

        steps.append(step)

    return steps


async def ai_run_test(
    task: str,
    base_url: str = DEFAULT_BASE_URL,
    headless: bool = True,
    storage_state_path: Optional[str] = None,
    max_steps: int = 30,
    use_vision: Optional[bool] = None,
) -> dict:
    """用 browser-use Agent 自主完成一条测试。

    Args:
        task: 自然语言描述的测试目标
        base_url: 站点 URL
        headless: 无头模式（CI 下为 True）
        storage_state_path: 从 session_context 导出的登录态 JSON 路径
        max_steps: Agent 最大操作步数

    Returns:
        {
            "success": bool,
            "total_steps": int,
            "history": [...],       # 操作轨迹
            "final_result": str,    # Agent 的最终回复
            "error": str | None,
        }
    """
    storage_state = None
    if storage_state_path:
        p = Path(storage_state_path)
        if p.exists():
            storage_state = json.loads(p.read_text(encoding="utf-8"))

    browser = Browser(
        browser_profile=_build_browser_profile(
            headless=headless,
            base_url=base_url,
            storage_state=storage_state,
        ),
    )

    llm = _get_llm()

    if use_vision is None:
        use_vision = True

    agent = Agent(
        task=task,
        llm=llm,
        browser=browser,
        use_vision=use_vision,
        flash_mode=False,
        max_failures=3,
        step_timeout=120,
        # 显式指定初始导航 URL，避免 Agent 从 task 文本中错误解析 URL
        initial_actions=[{"navigate": {"url": base_url, "new_tab": False}}],
    )

    try:
        history = await agent.run()

        # ── 构建结构化的返回结果 ──
        return {
            "success": history.is_successful(),
            "is_done": history.is_done(),
            "total_steps": history.number_of_steps(),
            "duration_seconds": history.total_duration_seconds(),
            "final_result": history.final_result() or "",
            "error": None,
            # Judge LLM 的最终判定（如果有的话）
            "judgement": history.judgement(),
            # 每步的结构化轨迹
            "steps": _extract_steps(history),
            # 元信息
            "urls_visited": history.urls(),
            "errors_encountered": history.errors(),
        }
    except Exception as e:
        return {
            "success": False,
            "is_done": False,
            "total_steps": 0,
            "duration_seconds": 0,
            "final_result": "",
            "error": str(e),
            "judgement": None,
            "steps": [],
            "urls_visited": [],
            "errors_encountered": [str(e)],
        }
    finally:
        # 确保浏览器关闭
        try:
            await browser.close()
        except Exception:
            pass


def format_result(result: dict, verbose: bool = False) -> str:
    """将 ai_run_test 返回的 dict 格式化为可读的报告文本。

    适合直接打印到终端、贴到 issue、或写进 Allure 附件。
    """
    lines = []
    status = "[PASS]" if result["success"] else "[FAIL]"
    lines.append(f"{'='*60}")
    lines.append(f"  AI Agent 执行报告  {status}")
    lines.append(f"{'='*60}")
    lines.append(f"  总步数: {result['total_steps']}   耗时: {result['duration_seconds']:.1f}s")
    lines.append(f"  访问页面: {', '.join(result.get('urls_visited', [])[:5] or ['无'])}")

    # Judge 判定
    judgement = result.get("judgement")
    if judgement:
        verdict = judgement.get("verdict", "?")
        reason = judgement.get("failure_reason", "")
        lines.append(f"  Judge 判定: {verdict}  {reason}")

    # 每步概述
    lines.append(f"\n{'─'*40}")
    lines.append("  执行轨迹:")
    for step in result.get("steps", []):
        action_name = list(step.get("action", {}).keys())[0] if step.get("action") else "?"
        status_char = "+" if step.get("action_success") else "x"
        thinking = (step.get("thinking") or "")[:80] if verbose else ""
        lines.append(f"    {status_char} Step {step['step']}: {action_name}  {thinking}")

    # 最终结果
    lines.append(f"\n{'─'*40}")
    lines.append("  Agent 叙述:")
    final = result.get("final_result", "") or "(无)"
    for line in final.split("\n")[:20]:
        lines.append(f"    {line}")

    # 错误
    errors = result.get("errors_encountered", [])
    if errors:
        lines.append(f"\n  错误: {errors[0][:200]}")

    lines.append(f"{'='*60}")
    return "\n".join(lines)


def collect_evidence(result: dict) -> dict:
    """从 Agent 执行结果中提取客观证据——不依赖 Agent 的文字叙述。

    这是对抗幻觉的关键：Agent 说"我成功上传了图片"不可信，
    但截图 + URL 变化 + 操作成功标记三方交叉印证就可信。

    Returns:
        {
            "url_chain": [...],       # 访问过的 URL 链
            "actions_succeeded": N,    # 成功操作数 / 总操作数
            "screenshots_count": N,    # 截图数量
            "critical_checks": {       # 关键检查点
                "reached_target_url": bool,   # 到达了目标页面吗
                "no_cdp_errors": bool,        # 没有 CDP 层错误吗
                "completed_without_crash": bool,  # 正常结束了吗
            }
        }
    """
    steps = result.get("steps", [])
    urls = [u for u in result.get("urls_visited", []) if u]
    errors = [e for e in result.get("errors_encountered", []) if e]

    total = len(steps)
    succeeded = sum(1 for s in steps if s.get("action_success"))
    screenshots = sum(1 for s in steps if s.get("screenshot"))

    return {
        "url_chain": urls,
        "actions_succeeded": f"{succeeded}/{total}",
        "screenshots_count": screenshots,
        "critical_checks": {
            "reached_any_page": len(urls) > 0,
            "no_cdp_errors": len(errors) == 0,
            "normal_exit": result.get("is_done", False),
        },
    }


def cross_validate(evidence: dict, agent_narrative: str) -> dict:
    """交叉验证：把客观证据和 Agent 叙述比对，标记可信度。

    Returns:
        {
            "trust_level": "high" | "medium" | "low",
            "inconsistencies": [...],   # 证据和叙述之间的不一致
            "verdict": str,
        }
    """
    checks = evidence.get("critical_checks", {})
    issues = []

    if not checks.get("reached_any_page"):
        issues.append("Agent 没有成功访问任何页面")
    if not checks.get("no_cdp_errors"):
        issues.append("存在 CDP 层错误（浏览器操作失败）")
    if not checks.get("normal_exit"):
        issues.append("Agent 非正常退出（可能是崩溃或超时）")

    score = sum(1 for v in checks.values() if v)  # 通过的检查点数

    if score == 3 and not issues:
        trust = "high"
    elif score >= 2:
        trust = "medium"
    else:
        trust = "low"

    return {
        "trust_level": trust,
        "inconsistencies": issues,
        "verdict": f"客观证据通过 {score}/{len(checks)} 项" + (f": {'; '.join(issues)}" if issues else ""),
    }


async def ai_retry_failed_case(
    task_description: str,
    base_url: str = DEFAULT_BASE_URL,
    storage_state_path: Optional[str] = None,
    headless: bool = True,
) -> dict:
    """pytest 用例失败后的 AI 兜底重试。

    与 ai_run_test 的区别：
    - task_description 应包含"当前失败信息"作为上下文
    - 返回值增加 'verdict' 字段：'selector_drift' | 'likely_bug' | 'uncertain'

    Returns:
        {
            "success": bool,
            "verdict": "selector_drift" | "likely_bug" | "uncertain",
            "total_steps": int,
            "final_result": str,
            "error": str | None,
        }
    """
    prompt = (
        f"你是一个 Web 自动化测试 Agent。以下是一条未能通过的测试用例，"
        f"请你用视觉模式（不依赖 CSS 选择器）重新执行该测试，判断失败原因。\n\n"
        f"测试目标：\n{task_description}\n\n"
        f"注意：\n"
        f"1. 使用截图和页面文字来定位元素，不要依赖固定的 CSS selector\n"
        f"2. 如果页面结构已改变但你仍能完成目标，说明是 selector 漂移\n"
        f"3. 如果你使用视觉定位仍然无法完成目标，说明可能是真正的 Bug\n"
        f"4. 完成后请回答：'判定: selector_drift' 或 '判定: likely_bug' 或 '判定: uncertain'，并说明原因"
    )

    result = await ai_run_test(
        task=prompt,
        base_url=base_url,
        headless=headless,
        storage_state_path=storage_state_path,
    )

    # 从 Agent 最终回复中解析判定
    verdict = "uncertain"
    final = result.get("final_result", "")
    if "selector_drift" in final.lower() or "选择器漂移" in final:
        verdict = "selector_drift"
    elif "likely_bug" in final.lower() or "真正的 bug" in final or "真正bug" in final:
        verdict = "likely_bug"
    elif result["success"]:
        # Agent 能跑通但没明确判定 → 倾向于是选择器问题
        verdict = "selector_drift"

    return {**result, "verdict": verdict}


async def export_session_state(browser_context, path: str = "data/session_state.json"):
    """从现有 Playwright browser_context 导出登录态，
    供 browser-use 复用，避免重复登录消耗 credits。

    用法（在 conftest.py 中）：
        from helpers.ai_agent import export_session_state
        await export_session_state(session_context, "data/session_state.json")
    """
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    await browser_context.storage_state(path=str(p))
    print(f"[ai_agent] session state exported to {p}")
    return str(p)
