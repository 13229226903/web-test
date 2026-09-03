"""Send the review screenshot to gpt-5.6 for analysis."""
import os, json, base64, urllib.request

# Load .env
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k not in os.environ:
                    os.environ[k] = v

key = os.getenv("OPENAI_API_KEY", "")

# The image
img_path = r"D:\360MoveData\Users\liangjinrun\Desktop\新建文件夹\J$C%JQK6T1QP0F@~(7O@`YQ.png"
with open(img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

prompt = (
    "This is a screenshot from a comments/reviews/testimonials section of an SEO landing page "
    "for an online image editing tool (Pokecut). The expected language is Japanese.\n\n"
    "Please inspect this screenshot carefully for any text quality issues:\n"
    "1. Garbled text / mojibake / unreadable characters\n"
    "2. Encoding errors (e.g. UTF-8 bytes misinterpreted)\n"
    "3. Placeholder or dummy text that shouldn't be visible\n"
    "4. Truncated or fragmented text\n"
    "5. Repeated/duplicate content that looks like a bug\n"
    "6. ANY other text rendering anomalies\n\n"
    "Return ONLY a JSON object:\n"
    '{"found_issues": true/false, "issues": ["issue 1", "issue 2"], "summary": "one sentence"}'
)

body = {
    "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
    "max_tokens": 500,
    "temperature": 0,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
            {"type": "text", "text": prompt},
        ],
    }],
}

req = urllib.request.Request(
    os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
    data=json.dumps(body).encode("utf-8"),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
)

print("Sending image to gpt-5.6...")
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"]
        print("\n=== LLM Response ===\n")
        print(text)
except Exception as e:
    print(f"Error: {e}")
    if hasattr(e, 'read'):
        try:
            print(e.read().decode()[:500])
        except Exception:
            pass
