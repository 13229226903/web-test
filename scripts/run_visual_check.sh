#!/bin/bash
export OPENAI_API_KEY="${1}"
cd "$(dirname "$0")/.."
python scripts/visual_check.py \
  --before "data/screenshots/test_change_passport_to_blue_background[chromium]_01-change-passport-blue-首屏.png" \
  --after "data/screenshots/test_change_passport_to_blue_background[chromium]_02-change-passport-blue-任务完成后.png" \
  --expectation "判断操作后的截图中，画布图层是否为蓝色背景的图" \
  --model gpt-5.6
