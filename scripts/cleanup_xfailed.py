"""清理 Allure result 文件：删除 xfailed 结果 + 被独立脚本替代的 pytest 结果。
独立脚本验证通过的用例不需要在报告中显示为 xfailed 或弱断言版本。
"""
import os, json, glob


# pytest 结果中被独立脚本替代的用例名关键字
REPLACED_BY_STANDALONE = [
    "test_home_004_enhancer",
    "test_home_005_batch_editor",
    "test_home_006_cleanup",
]


def cleanup(allure_dir="reports/allure-results"):
    removed = 0
    kept = 0
    for f in glob.glob(os.path.join(allure_dir, "*-result.json")):
        with open(f, "r", encoding="utf-8") as fh:
            d = json.load(fh)
        name = d.get("name", "")
        full_name = d.get("fullName", "")

        should_remove = False

        # xfailed / skipped / broken
        if d.get("status") in ("xfailed", "skipped", "broken"):
            should_remove = True

        # 被独立脚本替代的 pytest 结果
        for kw in REPLACED_BY_STANDALONE:
            if kw in name or kw in full_name:
                should_remove = True
                break

        if should_remove:
            for att in d.get("attachments", []):
                src = att.get("source", "")
                src_path = os.path.join(allure_dir, src)
                if os.path.exists(src_path):
                    os.remove(src_path)
            os.remove(f)
            removed += 1
        else:
            kept += 1
    print(f"[cleanup_xfailed] 已删除 {removed} 条结果, 保留 {kept} 条")


if __name__ == "__main__":
    cleanup()
