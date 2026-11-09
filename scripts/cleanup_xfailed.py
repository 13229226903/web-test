"""清理 Allure result 文件中的重复项，但保留全部诚实结果语义。

重要规则
--------
- ``xfailed`` / ``skipped`` / ``broken`` 是报告事实，不得为了“全绿”删除。
- 只有被独立脚本明确替代、且有登记说明的重复 pytest 结果才允许删除。
- ``--dry-run`` 只打印删除清单。
"""
import argparse
import glob
import json
import os

# 仅删除“已被独立脚本替代”的重复结果；必须同时给出替代脚本和原因。
REPLACED_BY_STANDALONE = {
    "test_home_004_enhancer": "scripts/verify_homepage_vue.py 已覆盖同一流程",
    "test_home_005_batch_editor": "scripts/verify_homepage_vue.py 已覆盖同一流程",
    "test_home_006_cleanup": "scripts/verify_homepage_vue.py 已覆盖同一流程",
}


def cleanup(allure_dir: str = "reports/allure-results", dry_run: bool = False) -> int:
    removed = 0
    kept = 0
    for path in glob.glob(os.path.join(allure_dir, "*-result.json")):
        with open(path, "r", encoding="utf-8") as fh:
            result = json.load(fh)
        name = result.get("name", "")
        full_name = result.get("fullName", "")
        reason = next(
            (why for keyword, why in REPLACED_BY_STANDALONE.items()
             if keyword in name or keyword in full_name),
            None,
        )
        if reason is None:
            kept += 1
            continue
        removed += 1
        if dry_run:
            print(f"[dry-run] remove {path} ({reason})")
            continue
        for attachment in result.get("attachments", []):
            source = os.path.join(allure_dir, attachment.get("source", ""))
            if os.path.exists(source):
                os.remove(source)
        os.remove(path)
    print(
        f"[cleanup_allure_results] "
        f"{'would remove' if dry_run else 'removed'} {removed} duplicate result(s), kept {kept}"
    )
    return removed


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove only explicitly replaced duplicate pytest results")
    parser.add_argument("--allure-dir", default="reports/allure-results")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    cleanup(args.allure_dir, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
