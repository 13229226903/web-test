"""visual-review 核心工具：调用 OpenAI 多模态 API 对比两张截图，判断视觉期望是否满足。

用法:
  python scripts/visual_check.py \\
    --before data/screenshots/before.png \\
    --after  data/screenshots/after.png \\
    --expectation "文字图层背景变为红色" \\
    [--model gpt-5.6] \\
    [--output -]

API key 从环境变量 OPENAI_API_KEY 读取。
"""

import argparse, base64, json, os, sys, urllib.request, urllib.error


def encode_image(path):
    """读取图片并返回 data URL。"""
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"


def build_prompt(before_b64, after_b64, expectation):
    """构建通用的提示词（文本 + 图片）。"""
    return (
        f"这是操作前的截图（作为对比基准）。\n\n"
        f"这是操作后的截图。请判断操作后截图中的视觉效果是否满足以下期望：\n"
        f"「{expectation}」\n\n"
        f"回答格式要求：只返回一个 JSON 对象，不要包含任何其他文字：\n"
        f'{{"verdict": "pass或fail或uncertain", "reason": "一句话说明判断依据（中文）"}}'
    )


def _parse_openai_response(req):
    """发送请求并解析 OpenAI 兼容格式的响应。"""
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            text = data["choices"][0]["message"]["content"]
            return _parse_verdict(text)
    except urllib.error.HTTPError as e:
        return {"verdict": "error", "reason": f"API HTTP {e.code}: {e.read().decode()[:300]}"}
    except Exception as e:
        return {"verdict": "error", "reason": str(e)}


# ── 响应解析 ────────────────────────────────────────────────

def _parse_verdict(text):
    """从模型返回的文本中解析 verdict JSON。"""
    # 去 ```json ... ``` 包裹
    cleaned = text.strip()
    if "```" in cleaned:
        parts = cleaned.split("```")
        cleaned = parts[1] if len(parts) > 1 else parts[0]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        # 降级：从文本中推断
        lower = text.lower()
        if "pass" in lower and "fail" not in lower:
            return {"verdict": "pass", "reason": text.strip()}
        elif "fail" in lower:
            return {"verdict": "fail", "reason": text.strip()}
        else:
            return {"verdict": "uncertain", "reason": f"无法解析模型输出: {text[:200]}"}


# ── CLI ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="多模态视觉断言")
    parser.add_argument("--before", required=True, help="操作前截图路径")
    parser.add_argument("--after", required=True, help="操作后截图路径")
    parser.add_argument("--expectation", required=True, help="视觉期望描述（中文）")
    parser.add_argument("--model", default="gpt-5.6", help="多模态模型 ID")
    parser.add_argument("-o", "--output", default="-", help="输出文件路径，默认 stdout")
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(json.dumps({"verdict": "error", "reason": "未设置 OPENAI_API_KEY 环境变量"}))
        sys.exit(1)

    for path in [args.before, args.after]:
        if not os.path.exists(path):
            print(json.dumps({"verdict": "error", "reason": f"截图不存在: {path}"}))
            sys.exit(1)

    print(f"[visual_check] model={args.model}", file=sys.stderr)

    before_url = encode_image(args.before)
    after_url = encode_image(args.after)
    body = {
        "model": args.model,
        "max_tokens": 300,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": before_url}},
                {"type": "text", "text": "这是操作前的截图（作为对比基准）。"},
                {"type": "image_url", "image_url": {"url": after_url}},
                {"type": "text", "text": build_prompt(None, None, args.expectation)},
            ],
        }],
    }
    req = urllib.request.Request(
        os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    result = _parse_openai_response(req)

    output = json.dumps(result, ensure_ascii=False)
    if args.output == "-":
        print(output)
    else:
        os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)


if __name__ == "__main__":
    main()
