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

img1 = r"D:\360MoveData\Users\liangjinrun\Desktop\新建文件夹\file-read-216502.png"
img2 = r"D:\360MoveData\Users\liangjinrun\Desktop\新建文件夹\Snipaste_2026-07-13_14-52-48.png"

with open(img1, "rb") as f:
    b64_1 = base64.b64encode(f.read()).decode()
with open(img2, "rb") as f:
    b64_2 = base64.b64encode(f.read()).decode()

prompt = (
    "You are reviewing two screenshots from an SEO landing page for quality assurance.\n\n"
    "=== REVIEW TASKS ===\n\n"
    "A) Rendering / text bugs:\n"
    "  1. Garbled text, mojibake, unreadable characters\n"
    "  2. Question mark waterfalls where real text should be\n"
    "  3. Encoding errors, broken characters\n"
    "  4. Placeholder or dummy text visible to users\n"
    "  5. Truncated or fragmented text\n"
    "  6. HTML tags or entities leaked into visible text\n\n"
    "B) Copywriting / UX consistency:\n"
    "  1. Inconsistent naming or numbering patterns\n"
    "  2. Inconsistent terminology (same concept called different names)\n"
    "  3. Mixed languages in labels that should be uniform\n"
    "  4. Inconsistent spacing or formatting\n"
    "  5. Typos, grammar errors, awkward phrasing\n\n"
    "Compare both images — if they show different states of the same page/section, "
    "note any regressions or inconsistencies between them.\n\n"
    'Return ONLY JSON: {"found_issues": true/false, "issues": [{"category": "rendering|copywriting", "detail": "..."}], "summary": "..."}'
)

body = {
    "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
    "max_tokens": 600,
    "temperature": 0,
    "messages": [{
        "role": "user",
        "content": [
            {"type": "text", "text": "IMAGE 1:"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_1}"}},
            {"type": "text", "text": "IMAGE 2:"},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_2}"}},
            {"type": "text", "text": prompt},
        ],
    }],
}

req = urllib.request.Request(
    os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
    data=json.dumps(body).encode("utf-8"),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
)

print("Sending 2 images...")
try:
    with urllib.request.urlopen(req, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print("\n=== Response ===\n")
        print(data["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error: {e}")
