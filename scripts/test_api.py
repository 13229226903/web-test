import os, json, urllib.request

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
print("Key:", key[:40])

model = os.getenv("OPENAI_MODEL", "gpt-5.6")
body = {
    "model": model,
    "max_tokens": 30,
    "messages": [{"role": "user", "content": "Say hi"}],
}
req = urllib.request.Request(
    os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1") + "/chat/completions",
    data=json.dumps(body).encode("utf-8"),
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        print(f"  {model}: OK — {data['choices'][0]['message']['content'][:50]}")
except urllib.error.HTTPError as e:
    err = e.read().decode()[:200]
    print(f"  {model}: HTTP {e.code} — {err}")
except Exception as e:
    print(f"  {model}: {e}")
