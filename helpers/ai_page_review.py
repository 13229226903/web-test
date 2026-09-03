"""SEO 新页面 AI 单页内容审查（Layer 3）

不依赖手写预期 — 给多模态模型一张全页截图 + 页面元信息，
用通用 prompt 检查布局/图片/文案/CTA 是否存在明显问题。

依赖：OPENAI_API_KEY 或 ANTHROPIC_AUTH_TOKEN / ANTHROPIC_API_KEY
模型：默认优先使用本地配置里的模型名

用法：
    from helpers.ai_page_review import AIPageReviewer

    reviewer = AIPageReviewer()
    result = reviewer.review(
        screenshot_path="data/screenshots/page.png",
        page_info={"url": "http://...", "lang": "ja", "title": "...", "h1": "..."}
    )
    # result = {"passed": bool, "issues": [...], "summary": "..."}
"""

import os
import json
import base64
from pathlib import Path
from typing import Optional

from helpers.review_api_config import get_review_api_config


def _detect_lang_prefix(path: str) -> str:
    import re
    m = re.match(r"^/([a-z]{2}(?:-[a-z]{2})?)/", path)
    return m.group(1) if m else ""


# 语言代码 → 中文名
LANG_NAMES = {
    "zh": "简体中文", "zh-tw": "繁体中文", "ja": "日语", "ko": "韩语",
    "th": "泰语", "ru": "俄语", "ar": "阿拉伯语", "vi": "越南语",
    "id": "印尼语", "pt": "葡萄牙语", "es": "西班牙语", "fr": "法语",
    "it": "意大利语", "de": "德语", "tr": "土耳其语", "": "英语",
}


class AIPageReviewer:
    """AI 单页内容审查器。

    使用多模态模型对 SEO 页面截图进行审查，不依赖任何手写预期。
    """

    def __init__(self):
        self.api_key, self.api_base, self.model = get_review_api_config()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    # ═══════════════════════════════════════════════════════════
    # 审查主入口
    # ═══════════════════════════════════════════════════════════

    def review(self, screenshot_path: str, page_info: dict, hints: str = "", focus: str = "desktop") -> dict:
        """审查单张全页截图。

        Args:
            screenshot_path: 截图文件路径（PNG）
            page_info: {"url": str, "lang": str, "title": str, "h1": str, "h2s": [str]}

        Returns:
            {"passed": bool, "issues": [...], "summary": "...", "detail": "..."}
        """
        if not self.enabled:
            return {
                "passed": True,
                "issues": [],
                "summary": "",
                "detail": "AI review disabled (no API key configured)",
            }

        if not os.path.exists(screenshot_path):
            return {
                "passed": True,
                "issues": [],
                "summary": "",
                "detail": f"Screenshot not found: {screenshot_path}",
            }

        prompt = self._build_prompt(page_info, hints=hints, focus=focus)
        return self._call_api(screenshot_path, prompt, focus=focus)

    # ═══════════════════════════════════════════════════════════
    # Prompt 构建
    # ═══════════════════════════════════════════════════════════

    def _build_prompt(self, page_info: dict, hints: str = "", focus: str = "desktop") -> str:
        """构造通用审查 prompt（不依赖页面类型）。"""
        url = page_info.get("url", "")
        from urllib.parse import urlparse
        url_path = urlparse(url).path if url else ""

        lang_code = page_info.get("lang", _detect_lang_prefix(url_path))
        lang_name = LANG_NAMES.get(lang_code, lang_code or "英语")

        title = page_info.get("title", "（未获取到）")
        h1 = (page_info.get("h1s", [""]) or [""])[0] if page_info.get("h1s") else "（未获取到）"

        # 从 URL 推导工具类型（最后一段路径）
        tool_segment = ""
        if url_path:
            parts = [p for p in url_path.strip("/").split("/") if p]
            if parts:
                tool_segment = parts[-1].replace("-", " ")

        is_mobile = str(focus).lower() == "mobile"

        parts = [
            "你正在审查一个在线图片编辑工具网站的 SEO 落地页截图。",
            "",
            "=== 页面信息 ===",
            f"页面 URL: {url}",
            f"页面标题 (<title>): {title}",
            f"页面 H1 标题: {h1}",
            f"预期页面语言: {lang_name} ({lang_code})",
            f"工具名称（从 URL 推断）: {tool_segment}",
        ]
        if is_mobile:
            parts.append("审查模式: mobile")
        if hints:
            parts.extend([
                "",
                "=== 页面提示 ===",
                hints,
            ])
        parts.extend([
            "",
            "=== 额外说明 ===",
            "测试服里的任何浮窗、调试浮层、结果面板、弹窗、抽屉、气泡、悬浮按钮或覆盖层文案都要忽略，"
            "不要把它们当成页面正文问题。",
        ])
        if is_mobile:
            parts.extend([
                "",
                "=== 审查任务 ===",
                "请只审查移动端整页截图是否像一个正常可用的落地页。",
                "不要检查内链、FAQ 文本、语气润色或文案是否漂亮，只看视觉和交互结果。",
                "",
                "1. 布局完整性",
                "   - 是否有大面积空白区域（占屏幕 30% 以上且无内容）？",
                "   - 是否有元素明显错位、重叠、截断或超出屏幕边界？",
                "   - 页面是否像一个正常的移动端落地页，而不是桌面页缩成一团？",
                "",
                "2. 图片与卡片可见性",
                "   - 页面中的图片、试用图、功能卡片是否都能正常显示？",
                "   - 是否存在裂图、空白占位、或明显不相关的视觉元素？",
                "",
                "3. 按钮/交互可辨识性",
                "   - 页面上的主要 CTA / 试用图是否清晰可见？",
                "   - 点击后页面态变化是否合理，没有明显错误页、白屏或异常弹层？",
                "",
                "4. 页面完整度",
                "   - 首屏和整页是否像一个完整的移动端 SEO 落地页？",
                "   - 是否存在明显渲染失败、断裂或过度空白？",
                "",
                "=== 输出格式 ===",
                "只返回一个 JSON 对象，不要包含任何其他文字：",
                '{"passed": true/false,',
                ' "issues": [{"severity": "error或warning", "dimension": "layout或image或cta或content", ',
                '"detail": "问题描述（用中文，一句话说清楚，如果没问题返回空数组）"}],',
                ' "summary": "一句话总结审查结果（中文）"}',
            ])
        else:
            parts.extend([
                "",
                "=== 审查任务 ===",
                "请从以下 5 个维度检查截图中的页面是否正常。",
                "不要按固定文案做比对，也不要寻找脚本示例；以页面自身内容是否自洽、完整、像一个正常可用的 SEO 落地页为准。",
                "如果页面提示与截图不完全一致，以截图为准，但不要要求逐字匹配。",
                "",
                "1. 布局完整性",
                "   - 是否有大面积空白区域（占屏幕 30% 以上且无内容）？",
                "   - 是否有元素明显错位、重叠、或超出屏幕边界？",
                "   - 页面整体结构是否像是一个正常的 SEO 落地页（有标题、介绍、功能展示、CTA）？",
                "",
                f"2. 图片可见性",
                f"   - 页面中的图片是否都能正常加载显示（不是裂图/空白占位）？",
                f"   - 图片内容是否与「{tool_segment}」这类工具主题相关（不是毫不相关的随机图片）？",
                "",
                "3. 文案质量",
                f"   - 是否出现明显的乱码、� 字符、或渲染失败的占位文本？",
                f"   - 是否混入了与预期语言「{lang_name}」明显不同的整段其他语言？",
                "   - 句子是否出现明显截断、缺字或占位符如 Lorem ipsum？",
                "   - 不要把语气不顺、标题不够漂亮、或测试环境里的调试字样当成问题。",
                "",
                "4. CTA 可辨识性",
                "   - 页面上是否有清晰可见的 Call-to-Action 按钮（如 Upload Image / Try Now / Start）？",
                "   - 按钮是否被遮挡、截断或不可点击？",
                "",
                "5. 内容充足性",
                "   - 页面正文区域是否有足够的内容（不是接近空白的页面）？",
                "   - H1 标题、介绍文字、功能说明等基本内容是否存在？",
                "",
                "=== 输出格式 ===",
                "只返回一个 JSON 对象，不要包含任何其他文字：",
                '{"passed": true/false,',
                ' "issues": [{"severity": "error或warning", "dimension": "layout或image或text或cta或content", ',
                '"detail": "问题描述（用中文，一句话说清楚，如果没问题返回空数组）"}],',
                ' "summary": "一句话总结审查结果（中文）"}',
            ])
        return "\n".join(parts)

    # ═══════════════════════════════════════════════════════════
    # API 调用
    # ═══════════════════════════════════════════════════════════

    def _call_api(self, screenshot_path: str, prompt: str, focus: str = "desktop") -> dict:
        """调用多模态 API，返回审查结果。"""
        import urllib.request
        import urllib.error
        import time as _time

        # 编码图片
        with open(screenshot_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode()
        mime = "image/png"
        data_uri = f"data:{mime};base64,{img_b64}"

        body = {
            "model": self.model,
            "max_tokens": 800,
            "temperature": 1 if "kimi" in self.model.lower() else 0,
            "messages": [{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}},
                    {"type": "text", "text": prompt},
                ],
            }],
        }

        req = urllib.request.Request(
            f"{self.api_base}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )

        text = None
        last_err = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    message = data.get("choices", [{}])[0].get("message", {})
                    text = message.get("content") or message.get("reasoning_content") or ""
                    if not text:
                        raise ValueError("empty model response")
                    break
            except urllib.error.HTTPError as e:
                last_err = f"API HTTP {e.code}: {e.read().decode()[:200]}"
                break
            except Exception as e:
                last_err = str(e)
                if "SSL" in last_err:
                    _time.sleep(3)
                    continue
                break

        if text is None:
            return {
                "passed": False,
                "issues": [{
                    "severity": "error",
                    "dimension": "api",
                    "detail": f"API 调用失败: {last_err}",
                }],
                "summary": "API 调用失败",
                "detail": f"API 调用失败: {last_err}",
            }

        # 解析响应
        result = self._parse_response(text)
        if focus and str(focus).lower() == "mobile":
            allowed_dims = {"layout", "image", "cta", "content", "api"}
            issues = []
            for issue in result.get("issues", []):
                if not isinstance(issue, dict):
                    continue
                dim = issue.get("dimension", "")
                if dim in allowed_dims:
                    issues.append(issue)
            result["issues"] = issues
            result["passed"] = not issues
            if issues and not result.get("summary"):
                result["summary"] = "移动端截图存在问题"
        result["detail"] = f"AI reviewed 1 screenshot"
        return result

    def _parse_response(self, text: str) -> dict:
        """解析多模态模型的 JSON 响应。"""
        cleaned = text.strip()
        if "```" in cleaned:
            parts = cleaned.split("```")
            cleaned = parts[1] if len(parts) > 1 else parts[0]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]

        try:
            result = json.loads(cleaned.strip())
        except json.JSONDecodeError:
            # 降级：从文本中尝试提取关键判断
            lower = text.lower()
            has_pass = "passed" in lower and "true" in lower
            has_fail = "passed" in lower and "false" in lower or "fail" in lower
            result = {
                "passed": not has_fail,
                "issues": [],
                "summary": text[:200],
            }

        # 规范化
        if "issues" not in result:
            result["issues"] = []
        if "summary" not in result:
            result["summary"] = ""
        if "passed" not in result:
            result["passed"] = len(result["issues"]) == 0

        return result


# ═══════════════════════════════════════════════════════════════
# 便捷函数
# ═══════════════════════════════════════════════════════════════

def create_reviewer() -> Optional[AIPageReviewer]:
    """创建 AI 审查器实例（如果 API key 未配置则返回 None）。"""
    reviewer = AIPageReviewer()
    return reviewer if reviewer.enabled else None
