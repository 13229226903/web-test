"""
browser-use 文字图层回归测试（混合模式）

运行:
  python scripts/regression_text_layer.py

策略:
  - Playwright (async) 处理 /create 页面导航和图片上传（用已知 DOM 模式）
  - browser-use Agent 处理画布上的文字图层交互（语义理解，适应 UI 变化）

流程:
  0. Playwright: 打开 /create → 关闭弹窗 → 点 "Start from a Photo" → 上传图片 → 进入 /agent
  1. browser-use: 添加文字图层 + 选中文字
  2. browser-use: 逐个验证顶栏 9 按钮
  3. browser-use: 逐个验证右侧面板 4 个 Section
  4. 输出 pass/fail 报告
"""
import asyncio
import glob as _glob
import io
import json
import os
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# Windows 编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from browser_use import Agent
from browser_use.llm import ChatOpenAI
from browser_use.browser.profile import BrowserProfile
from playwright.async_api import async_playwright

# ============================================================
# 配置
# ============================================================
BASE_URL = "http://10.17.1.66:3001"
CREATE_URL = f"{BASE_URL}/create"
CDP_PORT = 9223

# ============================================================
# API Key
# ============================================================
def _find_api_key():
    val = os.getenv("OPENAI_API_KEY")
    if val and len(val) > 10:
        return val
    raise RuntimeError("No API Key found")

# ============================================================
# 浏览器管理
# ============================================================
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
    for i in range(15):
        time.sleep(1)
        try:
            urllib.request.urlopen(f"{cdp}/json/version", timeout=2)
            _CDP_URL = cdp
            return cdp
        except Exception:
            pass
    raise RuntimeError("Chrome CDP start failed")


def _pick_test_image():
    img_dir = Path("d:/Test/web-test/test_images")
    if img_dir.is_dir():
        imgs = sorted(_glob.glob(str(img_dir / "*")), key=os.path.getsize)
        if imgs:
            return os.path.abspath(imgs[0])
    return str(img_dir)


# ============================================================
# Phase 0: Playwright async — enter canvas
# ============================================================

async def enter_canvas(test_image: str) -> str:
    """Navigate /create -> close popup -> click card -> upload -> wait for /agent"""
    cdp = _ensure_browser()
    print(f"  CDP: {cdp}")

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(cdp)
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = ctx.pages[0] if ctx.pages else await ctx.new_page()

        # 1. Navigate
        print("  Navigating to /create ...")
        await page.goto(CREATE_URL, wait_until="networkidle", timeout=30000)
        await page.wait_for_timeout(3000)

        # 2. Close popup
        print("  Closing popups ...")
        try:
            await page.keyboard.press("Escape")
            await page.wait_for_timeout(1000)
        except Exception:
            pass
        try:
            await page.evaluate("""() => {
                const btns = document.querySelectorAll('button, [role=button], .close, [class*=close]');
                for (const b of btns) {
                    const t = (b.textContent || '').trim();
                    const cls = (b.className || '') + ' ' + (b.parentElement?.className || '');
                    if (t === '\u00d7' || t === '\u2715' || t === 'X' || cls.includes('close') || cls.includes('Close')) {
                        b.click(); return 'clicked';
                    }
                }
                return 'not found';
            }""")
            await page.wait_for_timeout(1500)
        except Exception:
            pass

        # 3. Click "Start from a Photo" card + upload
        print(f"  Uploading: {test_image}")

        async with page.expect_file_chooser() as fc_info:
            await page.evaluate("""() => {
                const cards = document.querySelectorAll('[class*="cursor-pointer"]');
                for (const card of cards) {
                    if (card.textContent.includes('Start from a Photo')) {
                        card.click(); return 'clicked';
                    }
                }
                const all = document.querySelectorAll('div, button, span, p, h1, h2, h3');
                for (const el of all) {
                    if (el.textContent.trim() === 'Start from a Photo' && el.offsetParent !== null) {
                        el.click(); return 'alt-clicked';
                    }
                }
                return 'not found';
            }""")

        file_chooser = await fc_info.value
        await file_chooser.set_files(test_image)
        print("  File chosen, waiting for /agent ...")

        # 4. Wait for navigation
        await page.wait_for_timeout(12000)
        url = page.url
        print(f"  Current URL: {url}")

        if "/agent" not in url:
            print("  Waiting longer ...")
            await page.wait_for_timeout(10000)
            url = page.url
            print(f"  Final URL: {url}")

        return url


# ============================================================
# LLM / Agent
# ============================================================

def _make_llm():
    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-5.6"),
        api_key=_find_api_key(),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        temperature=0, max_completion_tokens=4096, max_retries=3,
    )


def _make_agent(task: str, available_file_paths: list[str] | None = None) -> Agent:
    return Agent(
        task=task, llm=_make_llm(),
        browser_profile=BrowserProfile(
            cdp_url=_ensure_browser(), headless=True,
            disable_security=True, enable_default_extensions=False,
        ),
        use_vision=False,
        available_file_paths=available_file_paths or [],
        max_failures=3, max_actions_per_step=3, max_steps=15, step_timeout=120,
    )


def _parse_json(text: str | None) -> dict:
    if not text:
        return {"error": "No result from agent", "raw": ""}
    t = text.strip()
    for sep in ("```json", "```"):
        if sep in t:
            t = t.split(sep, 1)[1].split("```", 1)[0]
            break
    try:
        return json.loads(t.strip())
    except json.JSONDecodeError:
        return {"raw": text[:2000]}


async def run_agent(task: str, available_file_paths: list[str] | None = None):
    agent = _make_agent(task, available_file_paths=available_file_paths)
    return await agent.run()


# ============================================================
# Phase 1: Add text layer
# ============================================================

async def step_add_text():
    print("  [browser-use] Adding text layer ...")

    task = """
You are on the Pokecut canvas editor page (URL contains /agent). An image is loaded on the canvas.

STEP 1: Add a text layer
  - Find the text tool button in the left toolbar (icon "T" or label "Text")
  - Click it to activate text mode
  - Click in the center of the canvas to create a text box
  - Type "Test" and press Enter to confirm
  - Press Escape key to exit text editing mode

STEP 2: Select the text
  - Click on "Test" on the canvas to select it
  - A toolbar with buttons should appear at the top

Return ONLY this JSON (no other text):
{
  "text_added": true/false,
  "text_selected": true/false,
  "toolbar_visible": true/false,
  "toolbar_buttons_found": ["list of button texts visible"],
  "issues": []
}

IMPORTANT:
- Use press_key with key "Escape" to exit text editing mode
- Use simple click actions, not JavaScript evaluate()
"""
    result = await run_agent(task)
    data = _parse_json(result.final_result())
    print(f"    Result: added={data.get('text_added')}, selected={data.get('text_selected')}")
    print(f"    Toolbar buttons: {data.get('toolbar_buttons_found', [])}")
    return data


# ============================================================
# Phase 2: Test toolbar buttons
# ============================================================

TOOLBAR = [
    ("\u8c03\u6574/Adjust", "Right panel opens with Basic and Adjust tabs"),
    ("\u4e0a\u79fb/Move Up", "Text moves up one layer"),
    ("\u4e0b\u79fb/Move Down", "Text moves down one layer"),
    ("\u7f6e\u9876/Bring to Front", "Text goes to top layer"),
    ("\u7f6e\u5e95/Send to Back", "Text goes to bottom layer"),
    ("\u6c34\u5e73\u7ffb\u8f6c/Flip Horizontal", "Text flips horizontally (mirror)"),
    ("\u5782\u76f4\u7ffb\u8f6c/Flip Vertical", "Text flips vertically"),
    ("\u5220\u9664/Delete", "Text layer is deleted"),
    ("\u65cb\u8f6c/Rotate", "Text rotates"),
]

async def step_test_toolbar():
    results = []
    for name, expected in TOOLBAR:
        print(f"\n  [browser-use] Testing button: {name} ...")

        task = f"""
You are on the Pokecut canvas (/agent page). A text layer "Test" is on canvas.

Test toolbar button: {name}

1. Make sure text is selected by clicking "Test" on canvas
2. Find the "{name}" button in the toolbar at the top
3. Click it
4. Observe what happens

Expected: {expected}

Return ONLY this JSON:
{{"button": "{name}", "found": true/false, "clicked": true/false, "effect_observed": "what happened", "matches_expected": true/false, "issues": []}}

NOTE: For Delete button, if text was deleted that's expected (matches_expected=true).
"""
        result = await run_agent(task)
        data = _parse_json(result.final_result())
        results.append(data)
        print(f"    found={data.get('found')}, matched={data.get('matches_expected')}")

    return results


# ============================================================
# Phase 3: Test panel sections
# ============================================================

PANEL = [
    {
        "name": "\u95f4\u8ddd/Spacing",
        "steps": """1. Click Adjust button in toolbar to open right panel
2. Find Spacing section, click dropdown arrow to expand if collapsed
3. Click Toggle to turn ON
4. Drag slider to ~70%
5. Check if text spacing changes on canvas""",
    },
    {
        "name": "\u53cd\u5c04/Reflection",
        "steps": """1. Make sure right panel is open, Adjust tab selected
2. Scroll to find Reflection section
3. Expand by clicking dropdown arrow
4. Click Toggle to turn ON
5. Drag slider to adjust
6. Check for mirror/reflection effect on text""",
    },
    {
        "name": "\u80cc\u666f/Background",
        "steps": """1. Make sure right panel is open
2. Scroll to Background section, expand it
3. NOTE: No Toggle - expand to see color picker directly
4. Click a colored swatch (not white/black/gray)
5. Check if text background color changes""",
    },
    {
        "name": "\u8f6e\u5ed3/Outline",
        "steps": """1. Make sure right panel is open
2. Scroll to Outline section, expand it
3. Click Toggle to turn ON
4. Click a color swatch
5. Drag slider to adjust thickness
6. Check for outline/stroke effect on text""",
    },
]

async def step_test_panel():
    results = []
    for section in PANEL:
        name = section["name"]
        print(f"\n  [browser-use] Testing panel: {name} ...")

        task = f"""
You are on the Pokecut canvas (/agent page). Text "Test" should be selected.

Test panel section: {name}

Steps:
{section["steps"]}

Return ONLY this JSON:
{{"section": "{name}", "section_found": true/false, "expanded": true/false, "toggle_found": true/false, "toggle_state": "on/off/no_toggle", "sliders_found": 0, "sliders_adjusted": true/false, "color_picker_found": true/false, "visual_change_observed": true/false, "issues": []}}

Vue rules:
- Expand: click dropdown arrow (small triangle icon) first, then toggle
- Toggle: rounded-full 42x24 button, gray=OFF, blue=ON
- Swatches: 30x30 or 49x49 buttons, NOT input[type=color]
- Sliders: input[type=range], drag with mouse actions
"""
        result = await run_agent(task)
        data = _parse_json(result.final_result())
        results.append(data)
        print(f"    found={data.get('section_found')}, visual_change={data.get('visual_change_observed')}")

    return results


# ============================================================
# Main
# ============================================================

async def main():
    print("=" * 70)
    print("browser-use Text Layer Regression (Hybrid Mode)")
    print(f"Target: {CREATE_URL}")
    print("=" * 70)

    report = {
        "target": CREATE_URL,
        "feature": "Infinite Canvas Text Layer Regression",
        "timestamp": datetime.now().isoformat(),
        "steps": {},
    }

    test_image = _pick_test_image()
    print(f"Test image: {test_image}")

    # Phase 0: Enter canvas via Playwright
    print("\n[Phase 0] Playwright: Enter canvas ...")
    canvas_url = await enter_canvas(test_image)
    report["steps"]["canvas_url"] = canvas_url

    if "/agent" not in canvas_url:
        print(f"FAILED: not on canvas page, URL: {canvas_url}")
        return report
    print(f"OK: entered canvas: {canvas_url}")

    # Phase 1: Add text via browser-use
    print("\n[Phase 1] browser-use: Add text layer ...")
    text_data = await step_add_text()
    report["steps"]["add_text"] = text_data

    if not text_data.get("text_selected"):
        print("FAILED: text not selected, cannot continue")
        return report

    # Phase 2: Test toolbar buttons
    print("\n[Phase 2] browser-use: Test toolbar (9 buttons) ...")
    toolbar_results = await step_test_toolbar()
    report["steps"]["toolbar"] = toolbar_results

    # Re-enter canvas after delete button removed text
    print("\n[Phase 2b] Re-enter canvas for panel tests ...")
    canvas_url2 = await enter_canvas(test_image)
    if "/agent" in canvas_url2:
        text_data2 = await step_add_text()
        report["steps"]["re_add_text"] = text_data2
    else:
        text_data2 = {"error": "re-entry failed", "url": canvas_url2}
        report["steps"]["re_add_text"] = text_data2

    # Phase 3: Test panel sections
    print("\n[Phase 3] browser-use: Test panel (4 sections) ...")
    panel_results = await step_test_panel()
    report["steps"]["panel"] = panel_results

    # Summary
    print("\n" + "=" * 70)
    print("REPORT SUMMARY")
    print("=" * 70)

    tb_pass = sum(1 for r in toolbar_results if r.get("matches_expected"))
    print(f"\nToolbar: {tb_pass}/{len(toolbar_results)} passed")
    for r in toolbar_results:
        s = "OK" if r.get("matches_expected") else "FAIL"
        print(f"  [{s}] {r.get('button', '?')}: {str(r.get('effect_observed', ''))[:80]}")

    pn_pass = sum(1 for r in panel_results if r.get("visual_change_observed"))
    print(f"\nPanel: {pn_pass}/{len(panel_results)} passed")
    for r in panel_results:
        s = "OK" if r.get("visual_change_observed") else "FAIL"
        print(f"  [{s}] {r.get('section', '?')}: issues={r.get('issues', [])}")

    # Save
    out_dir = Path("d:/Test/reports/regression_text_layer")
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(f"\nReport saved: {report_path}")

    # Cleanup
    global _BROWSER_PROC
    if _BROWSER_PROC:
        _BROWSER_PROC.terminate()
        _BROWSER_PROC.wait()

    return report


if __name__ == "__main__":
    asyncio.run(main())
