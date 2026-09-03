import os, json, base64, urllib.request

env_path = r"d:\Test\web-test\.env"
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                if k not in os.environ:
                    os.environ[k] = v

key = os.getenv("OPENAI_API_KEY", "")

img_path = r"D:\360MoveData\Users\liangjinrun\Desktop\新建文件夹\1TX~N1`@}Y7`BY_%AFS(V`O.png"
with open(img_path, "rb") as f:
    img_b64 = base64.b64encode(f.read()).decode()

prompt = (
    "You are reviewing a screenshot from an SEO landing page for quality assurance.\n\n"
    "=== REVIEW TASKS ===\n\n"
    "A) Rendering / text issues (these are bugs):\n"
    "  1. Garbled text, mojibake, unreadable characters\n"
    "  2. Question mark waterfalls where real text should be\n"
    "  3. Encoding errors, broken characters\n"
    "  4. Placeholder or dummy text visible to users\n"
    "  5. Truncated or fragmented text\n"
    "  6. HTML tags or entities leaked into visible text\n\n"
    "B) Copywriting / UX consistency (these are quality issues):\n"
    "  1. Inconsistent naming patterns (e.g. '第1步' / '步骤2' / 'Step 3' mixed in same page)\n"
    "  2. Inconsistent terminology (same concept called different names)\n"
    "  3. Mixed languages in labels that should be uniform\n"
    "  4. Inconsistent formatting of numbers, dates, or units\n"
    "  5. Typos, grammar errors, awkward phrasing\n\n"
    "Return ONLY a JSON object:\n"
    '{"found_issues": true/false,\n'
    ' "issues": [{"category": "rendering|copywriting", "detail": "describe the issue"}],\n'
    ' "summary": "one sentence"}'
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

print("Sending...")
try:
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("\n=== Response ===\n")
        print(data["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error: {e}")
