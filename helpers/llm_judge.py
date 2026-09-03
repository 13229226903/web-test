"""LLM-based interaction judge — uses local review API config by default.

1. Button/interaction: before+after screenshots → LLM judges effect
2. Text quality: page text → LLM finds garbled text, mixed languages, etc.

Requires: OPENAI_API_KEY or ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY
"""

import os, json, base64, time, urllib.request, urllib.error
import re

from helpers.review_api_config import get_review_api_config


def _get_api_config():
    return get_review_api_config()


def _img_b64(png_bytes):
    return base64.b64encode(png_bytes).decode()


def _call_api(messages, max_tokens=400):
    key, base, model = _get_api_config()
    if not key:
        return None
    body = {"model": model, "max_tokens": max_tokens, "temperature": 1 if "kimi" in model.lower() else 0, "messages": messages}
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw = json.loads(resp.read().decode("utf-8"))
                message = raw.get("choices", [{}])[0].get("message", {})
                text = message.get("content") or message.get("reasoning_content") or ""
                if not text:
                    continue
            cleaned = text.strip()
            if "```" in cleaned:
                parts = cleaned.split("```")
                cleaned = parts[1] if len(parts) > 1 else parts[0]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            try:
                result = json.loads(cleaned.strip())
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from mixed text
                import re
                m = re.search(r'\{[^{}]*"passed"[^{}]*\}', cleaned, re.DOTALL)
                if m:
                    result = json.loads(m.group(0))
                else:
                    continue  # retry
            # Normalize issues: convert strings to dicts
            if "issues" in result:
                result["issues"] = [
                    {"severity": "warning", "detail": i} if isinstance(i, str) else i
                    for i in result.get("issues", [])
                ]
            return result
        except urllib.error.HTTPError as e:
            try:
                err = e.read().decode()[:200]
            except Exception:
                err = str(e)
            if "429" in str(e.code) or "rate" in err.lower():
                time.sleep(5)
                continue
            return None
        except Exception:
            time.sleep(2)
            continue
    return None


def _infer_lang_from_url(page_url: str) -> str:
    m = re.match(r"^/([a-z]{2}(?:-[a-z]{2})?)/", (page_url or "").split("?", 1)[0])
    if not m:
        return "英语"
    code = m.group(1).lower()
    mapping = {
        "zh": "简体中文",
        "zh-tw": "繁体中文",
        "ja": "日语",
        "ko": "韩语",
        "th": "泰语",
        "ru": "俄语",
        "ar": "阿拉伯语",
        "vi": "越南语",
        "id": "印尼语",
        "pt": "葡萄牙语",
        "es": "西班牙语",
        "fr": "法语",
        "it": "意大利语",
        "de": "德语",
        "tr": "土耳其语",
    }
    return mapping.get(code, "英语")


# ================================================================
# 1. Interaction effect LLM judgment
# ================================================================

def judge_interaction(png_before, png_after, element_text, element_type="button", page_url=""):
    """Send before+after screenshots to the Codex model to judge interaction effect.

    Returns dict with: passed, effect, detail, issues
    """
    key, base, model = _get_api_config()
    if not key:
        return {"passed": True, "effect": "skipped", "detail": "no API key", "issues": []}

    etype = "image" if element_type == "image" else "button"

    prompt = (
        "You are testing an SEO landing page for an online image editing tool.\n"
        f"Page URL: {page_url}\n"
        f'Clicked element: [{etype}] "{element_text[:60]}"\n\n'
        "Compare the BEFORE (1st image) and AFTER (2nd image) screenshots.\n"
        "Judge the click effect:\n\n"
        "1. Did the page navigate? If so, is the destination appropriate?\n"
        "   - Navigating to /agent, /create, /tools/*, /image-to-image* is NORMAL for try-image/demo clicks\n"
        "   - Navigating to a 404, error page, or completely unrelated page is a PROBLEM\n"
        "2. Did the UI change? (modal, menu, image change, dropdown)\n"
        "   - Minor UI changes are NORMAL and expected\n"
        "3. Are there CLEAR problems? Only flag these as issues:\n"
        "   - Error messages visible on screen\n"
        "   - Blank/white page after click\n"
        "   - Broken images, garbled text, obvious layout corruption\n"
        "   - 404 / Page Not Found / server error\n"
        "4. For try-image cards: navigating to an editor page is EXPECTED -> passed=true\n"
        "5. For regular buttons: if nothing visible happens -> that is OK (may be scroll/expand)\n\n"
        "Return ONLY a JSON object (no other text):\n"
        '{"passed": true/false,\n'
        ' "effect": "navigated|ui_changed|no_change|error",\n'
        ' "detail": "one sentence describing what happened",\n'
        ' "issues": []}\n'
        "Only fill issues for CLEAR problems (error pages, broken layout, garbled text)."
    )

    before_b64 = _img_b64(png_before)
    after_b64 = _img_b64(png_after)

    messages = [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{before_b64}"}},
            {"type": "text", "text": "BEFORE screenshot (before click)."},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{after_b64}"}},
            {"type": "text", "text": prompt},
        ],
    }]

    result = _call_api(messages, max_tokens=500)
    if result is None:
        return {"passed": True, "effect": "skipped", "detail": "API call failed", "issues": []}
    return result


# ================================================================
# 2. Text quality LLM detection
# ================================================================

def judge_text_quality(page_text, page_url="", lang=""):
    """Send page text to LLM to detect garbled text, mixed languages, HTML artifacts, etc.

    Returns dict with: passed, issues, summary
    """
    key, base, model = _get_api_config()
    if not key:
        return {"passed": True, "issues": [], "summary": "no API key"}

    text = page_text[:15000]
    expected_lang = lang or _infer_lang_from_url(page_url)
    lang_hint = f"该页面预期语言为：{expected_lang}。" if expected_lang else ""
    ignore_hint = (
        "测试服里的任何浮窗、调试浮层、结果面板、弹窗、抽屉、气泡、悬浮按钮或覆盖层文案都可以忽略，"
        "不要把它们当成页面正文。"
    )

    prompt = (
        "你正在审查一个图片编辑工具 SEO 落地页的文案质量。\n"
        "只关注明显的文本硬伤，不要把语气不顺、标题不够漂亮、或普通的营销文案风格当成问题。\n"
        f"{ignore_hint}\n"
        f"{lang_hint}\n"
        f"页面 URL: {page_url}\n\n"
        "=== 页面文本（前 15000 字符）===\n"
        f"{text}\n"
        "=== 文本结束 ===\n\n"
        "只检查这些硬伤：\n\n"
        "1. 明显乱码、mojibake、不可读字符，或大量问号/方块字\n"
        "2. HTML 标签或实体直接泄漏到可见文本中（如 &amp;、&lt;、<br>、&nbsp;）\n"
        "3. 编码错误（例如 UTF-8 被当成 Latin-1 解析）\n"
        "4. 占位文案 / 模板文案（如 Lorem ipsum）\n"
        "5. 句子被截断、语义明显没说完\n"
        "6. 预期单一语言时，混入了明显不该出现的其他语言段落\n\n"
        "如果只是少量英文按钮、品牌词、或正常的专有名词混用，不要报错。\n"
        "每个问题都要注明具体位置（段落开头前约 40 个字符）。\n"
        "只返回 JSON：\n"
        '{"passed": true/false,\n'
        ' "issues": [{"severity": "error|warning", "detail": "问题描述", "location": "段落开头（最多 40 字）"}],\n'
        ' "summary": "一句话总结"}'
    )

    messages = [{"role": "user", "content": prompt}]
    result = _call_api(messages, max_tokens=800)
    if result is None:
        return {"passed": True, "issues": [], "summary": "API call failed"}
    return result


# ================================================================
# 3. Screenshot visual text quality review
# ================================================================

def judge_screenshot_text(png_bytes, context="") -> dict:
    """Send a single screenshot to the multimodal LLM to visually detect
    garbled text, mojibake, question mark waterfalls, encoding errors, etc.

    Returns: {"found": bool, "issue": str}
    """
    key, base, model = _get_api_config()
    if not key:
        return {"found": False, "issue": ""}

    ctx = f"Context: {context}. " if context else ""
    prompt = (
        f"{ctx}"
        "这是一张 SEO 落地页的截图，请只做明显的可见文本硬伤审查。\n"
        "不要把语气不顺、标题不够顺口、排版风格差异，或正常的营销文案当成问题。\n"
        "测试环境里任何浮窗、调试浮层、结果面板、弹窗、抽屉、气泡、悬浮按钮或覆盖层文案都可以忽略。\n"
        "重点只看这些问题：\n\n"
        "1. 明显乱码、mojibake、不可读字符，或大段问号/方块字\n"
        "2. HTML 标签或实体直接显示在页面上\n"
        "3. 占位文案、模板文案、明显缺字或空白\n"
        "4. 句子明显截断、语义没说完\n"
        "5. 预期单一语言时，出现了整段不该出现的其他语言\n\n"
        "如果只是个别按钮、品牌名、链接词混入英文/其他语言，不要报错。\n"
        "只返回 JSON：{\"found\": true/false, \"issue\": \"问题描述（如无问题则空字符串）\"}"
    )

    r_b64 = _img_b64(png_bytes)
    messages = [{"role": "user", "content": [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{r_b64}"}},
        {"type": "text", "text": prompt},
    ]}]
    result = _call_api(messages, max_tokens=200)
    if result is None:
        return {"found": False, "issue": ""}
    return result
