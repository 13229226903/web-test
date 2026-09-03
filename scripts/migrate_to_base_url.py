"""Migrate all test files from hardcoded BASE to pytest base_url fixture."""
import os, re

TEST_DIR = os.path.join(os.path.dirname(__file__), "..", "tests")

files = [
    "test_seo_pretty_scale.py",
    "test_seo_eye_color_detector.py",
    "test_id_photo_maker.py",
]

for fname in files:
    fpath = os.path.join(TEST_DIR, fname)
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove BASE = "..." line (any URL)
    content = re.sub(r'\n?BASE\s*=\s*"http://[^"]*"\n', '', content)

    # 2. Update goto() signature: page, path -> page, base_url, path
    content = re.sub(
        r'def goto\(page: Page, path: str, lazy_scroll: bool = False\):',
        'def goto(page: Page, base_url: str, path: str, lazy_scroll: bool = False):',
        content
    )
    # Also match without type hints
    content = re.sub(
        r'def goto\(page: Page, path: str\):',
        'def goto(page: Page, base_url: str, path: str):',
        content
    )

    # 3. Update goto() body: {BASE}{path} -> {base_url}{path}
    content = content.replace('f"{BASE}{path}"', 'f"{base_url}{path}"')

    # 4. Update callers: goto(page, path, lazy_scroll=True) -> goto(page, base_url, path, lazy_scroll=True)
    content = content.replace('goto(page, path, lazy_scroll=True)', 'goto(page, base_url, path, lazy_scroll=True)')
    content = content.replace('goto(page, path)', 'goto(page, base_url, path)')
    content = content.replace('goto(sp, path)', 'goto(sp, base_url, path)')

    # 5. Add base_url to test method signatures
    # session_page only
    content = content.replace(
        'self, session_page: Page):',
        'self, session_page: Page, base_url: str):'
    )
    # page + session_page
    content = content.replace(
        'self, page: Page, session_page: Page):',
        'self, page: Page, session_page: Page, base_url: str):'
    )

    # 6. Update login_and_enter_edit or similar functions using BASE
    content = content.replace('f"{BASE}/create"', 'f"{base_url}/create"')
    content = content.replace('f"{BASE}{path}"', 'f"{base_url}{path}"')

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Migrated: {fname}")

# Also handle test_other_seo.py and test_tool_pages.py - already partially done
# Check for any remaining BASE occurrences
print("\nChecking for remaining hardcoded BASE...")
for fname in os.listdir(TEST_DIR):
    if fname.endswith(".py") and fname.startswith("test_"):
        fpath = os.path.join(TEST_DIR, fname)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        base_matches = re.findall(r'BASE\s*=\s*"http://[^"]*"', content)
        if base_matches:
            print(f"  {fname}: {base_matches}")
        # Check for hardcoded URLs in test files
        url_matches = re.findall(r'http://10\.17\.\d+\.\d+:\d+', content)
        if url_matches and fname not in ["helpers_seo.py"]:
            print(f"  {fname} has hardcoded URLs: {url_matches}")

print("\nDone!")
