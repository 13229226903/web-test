"""Run visual check for TC-TOOL-010 (change-passport-to-blue-background)."""
import os, sys, subprocess

key = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("OPENAI_API_KEY")
if not key:
    print("请传入 API Key: python scripts/run_visual_check.py <your-key>")
    sys.exit(1)

os.environ["OPENAI_API_KEY"] = key
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)

result = subprocess.run([
    sys.executable, os.path.join(script_dir, "visual_check.py"),
    "--before", os.path.join(project_dir, "data/screenshots/test_change_passport_to_blue_background[chromium]_01-change-passport-blue-首屏.png"),
    "--after", os.path.join(project_dir, "data/screenshots/test_change_passport_to_blue_background[chromium]_02-change-passport-blue-任务完成后.png"),
    "--expectation", "判断操作后的截图中，画布图层是否为蓝色背景的图",
    "--model", os.environ.get("OPENAI_MODEL", "gpt-5.6"),
], capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print(result.stderr, file=sys.stderr)
sys.exit(result.returncode)
