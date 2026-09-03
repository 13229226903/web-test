"""首屏文案 AI 审查 — 检查 SEO 页面翻译质量、未翻译 key 等。

用法：
    from helpers.visual_text_check import check_page_text

    # 多语言页面：检查是否翻译为对应语言
    check_page_text(page, locale="zh-tw", locale_name="繁体中文")

    # EN/ZH 页面：只检查未翻译 key
    check_page_text(page, locale="en", locale_name="English")
    check_page_text(page, locale="zh", locale_name="中文")
"""

import os, json, base64, urllib.request, urllib.error
import allure

from helpers.review_api_config import get_review_api_config


def check_page_text(page, locale: str = "en", locale_name: str = "English",
                    fail_on_error: bool = True, custom_prompt: str = ""):
    """发送截图到多模态 API 审查。

    Args:
        page: Playwright Page 对象
        locale: 语言代码（如 'zh-tw', 'de', 'en', 'zh'）
        locale_name: 语言显示名（如 '繁体中文', 'Deutsch'）
        fail_on_error: True=审查不通过直接 assert fail; False=返回 dict
        custom_prompt: 自定义审查提示词，覆盖默认的翻译检查。需包含 pass/fail 判断标准

    Returns:
        dict: {"verdict": "pass|fail|skipped|error", "reason": "..."}
    """
    api_key, api_base, model = get_review_api_config()
    if not api_key:
        result = {"verdict": "skipped", "reason": "未设置可用的审查 API 配置"}
        allure.attach(json.dumps(result, ensure_ascii=False, indent=2),
                      name=f"AI 文案审查 [{locale_name}]",
                      attachment_type=allure.attachment_type.JSON)
        if fail_on_error:
            assert False, "AI 文案审查跳过: 未设置可用的审查 API 配置"
        return result

    png_b64 = base64.b64encode(page.screenshot(full_page=False)).decode()

    if custom_prompt:
        check_items = custom_prompt
    else:
        # 通用排除规则（适用于所有语言）
        exclusion_rules = (
            f"注意：页面中出现的倒计时/限时优惠文案（如 '$1 USD offer ending soon23:59:19'）"
            f"中 'soon' 紧接时间数字是前端倒计时组件的正常渲染结果，"
            f"**不要**将其判定为格式异常或未翻译 key。这类文案请直接忽略，不影响审查结论。"
        )

        # EN/ZH 检查项少，只查未翻译 key；多语言加语言匹配检查
        if locale in ("en", "zh"):
            check_items = (
                f"这是一个 {locale_name} 的 SEO 页面首屏截图。请检查："
                f"1) 页面中是否存在未翻译的 key，例如以 'text.' 开头的字符串"
                f"（如 text.pageFeedbackPopTitle、text.pageFeedbackPopContent 等）；"
                f"2) 正文介绍文案是否完整、语义通顺、无截断或乱码。"
                f"{exclusion_rules}"
                f"如果以上全部满足则返回 pass，任一项不满足则返回 fail。"
            )
        else:
            check_items = (
                f"这是一个 {locale_name}（语言代码: {locale}）的 SEO 工具介绍页首屏截图。"
                f"请逐项检查："
                f"1) 所有可见文字（标题、正文、按钮、导航等）是否已正确翻译为 {locale_name}，"
                f"而不是显示英文原文或其他语言；"
                f"2) 页面中是否不存在未翻译的 key，例如以 'text.' 开头的字符串"
                f"（如 text.pageFeedbackPopTitle、text.pageFeedbackPopContent 等）；"
                f"3) 正文介绍文案是否完整、语义通顺、无截断或乱码。"
                f"{exclusion_rules}"
                f"如果以上三项全部满足则返回 pass，任一项不满足则返回 fail。"
            )

    body = {
        "model": model,
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{png_b64}"}},
                {"type": "text", "text": (
                    check_items +
                    "回答格式：只返回一个 JSON 对象，不要包含任何其他文字："
                    '{"verdict": "pass或fail", "reason": "一句话说明判断依据（中文）"}'
                )},
            ]
        }]
    }

    req = urllib.request.Request(
        f"{api_base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
    except Exception as e:
        result = {"verdict": "error", "reason": f"API 调用失败: {e}"}
        allure.attach(json.dumps(result, ensure_ascii=False, indent=2),
                      name=f"AI 文案审查 [{locale_name}]",
                      attachment_type=allure.attachment_type.JSON)
        return result

    # 解析
    cleaned = text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else parts[0]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        result = json.loads(cleaned.strip())
    except json.JSONDecodeError:
        lower = text.lower()
        if "pass" in lower and "fail" not in lower:
            result = {"verdict": "pass", "reason": text.strip()}
        elif "fail" in lower:
            result = {"verdict": "fail", "reason": text.strip()}
        else:
            result = {"verdict": "uncertain", "reason": f"无法解析: {text[:200]}"}

    allure.attach(
        json.dumps(result, ensure_ascii=False, indent=2),
        name=f"AI 文案审查 [{locale_name}]",
        attachment_type=allure.attachment_type.JSON,
    )

    if fail_on_error and result["verdict"] == "fail":
        assert False, f"AI 文案审查未通过 [{locale_name}]: {result.get('reason', result)}"

    return result
