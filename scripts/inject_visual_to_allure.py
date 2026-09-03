"""将 visual-review 结果注入 Allure results，使 AI 视觉审查出现在 HTML 报告中。

用法:
  python scripts/inject_visual_to_allure.py \
    --results data/screenshots/visual_review_results.json \
    --allure-dir reports/allure-results

工作原理:
  1. 读取 visual_review_results.json（由 visual_check.py 批量产出）
  2. 遍历 reports/allure-results/*-result.json，按 test case name 匹配
  3. 为匹配的测试结果追加 allure 附件（TEXT 类型），内容为 AI 审查结论
  4. 之后运行 allure generate 即可在报告中看到每条用例的 AI 视觉审查结果
"""

import argparse, json, os, glob, sys


def find_result_file(allure_dir, case_id):
    """在 allure results 目录中找到 case_id 对应的 result JSON 文件。

    Allure result 的 name 字段形如 "TC-ADJ-004 [P1] 选红色背景"，
    通过 case_id（如 "TC-ADJ-004"）前缀匹配。
    """
    for f in glob.glob(os.path.join(allure_dir, "*-result.json")):
        try:
            with open(f, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            name = data.get("name", "")
            if case_id in name:
                return f, data
        except (json.JSONDecodeError, KeyError):
            continue
    return None, None


# 全局计数器，确保同一 case_id 的多个视觉检查生成不同的附件文件
_attachment_counter = {}


def inject_attachment(result_path, result_data, case_id, verdict, reason):
    """向 allure result JSON 中注入一条 AI 视觉审查附件。"""
    verdict_icon = {"pass": "[PASS]", "fail": "[FAIL]", "uncertain": "[?]"}.get(verdict, "[?]")

    # 同一 case_id 可能有多个视觉检查，用计数器区分
    idx = _attachment_counter.get(case_id, 0) + 1
    _attachment_counter[case_id] = idx
    suffix = f"_{idx}" if idx > 1 else ""

    attachment_name = f"AI Visual Review - {case_id}{suffix} {verdict_icon}"
    attachment_content = (
        f"Case: {case_id}\n"
        f"Verdict: {verdict}\n"
        f"Reason: {reason}\n"
        f"Model: gpt-5.6 (OpenAI Codex)\n"
    )

    # 写入附件文件
    attachment_filename = f"visual_review_{case_id}{suffix}.txt"
    attachment_path = os.path.join(os.path.dirname(result_path), attachment_filename)
    with open(attachment_path, "w", encoding="utf-8") as fp:
        fp.write(attachment_content)

    # 注册附件
    if "attachments" not in result_data:
        result_data["attachments"] = []

    result_data["attachments"].append({
        "name": attachment_name,
        "source": attachment_filename,
        "type": "text/plain",
    })

    # 写回 result JSON
    with open(result_path, "w", encoding="utf-8") as fp:
        json.dump(result_data, fp, ensure_ascii=False, indent=2)

    return attachment_name


def main():
    parser = argparse.ArgumentParser(description="注入 visual-review 结果到 Allure")
    parser.add_argument("--results", required=True, help="visual_review_results.json 路径")
    parser.add_argument("--allure-dir", default="reports/allure-results", help="Allure results 目录")
    args = parser.parse_args()

    if not os.path.exists(args.results):
        print(f"[ERROR] visual review results not found: {args.results}")
        sys.exit(1)

    # 清理旧的 visual_review 附件文件和引用（确保每次注入幂等）
    for old_txt in glob.glob(os.path.join(args.allure_dir, "visual_review_*.txt")):
        os.remove(old_txt)
    for result_file in glob.glob(os.path.join(args.allure_dir, "*-result.json")):
        try:
            with open(result_file, "r", encoding="utf-8") as fp:
                data = json.load(fp)
            old_count = len(data.get("attachments", []))
            data["attachments"] = [
                a for a in data.get("attachments", [])
                if "visual_review" not in a.get("source", "")
            ]
            if len(data["attachments"]) != old_count:
                with open(result_file, "w", encoding="utf-8") as fp:
                    json.dump(data, fp, ensure_ascii=False, indent=2)
        except (json.JSONDecodeError, KeyError):
            continue
    print(f"[CLEAN] removed old visual_review attachments")

    with open(args.results, "r", encoding="utf-8") as f:
        visual_results = json.load(f)

    injected = 0
    for vr in visual_results:
        case_id = vr.get("case_id", "?")
        verdict = vr.get("verdict", "?")
        reason = vr.get("reason", "")

        result_path, result_data = find_result_file(args.allure_dir, case_id)
        if result_path is None:
            print(f"  [SKIP] {case_id}: no matching allure result found")
            continue

        name = inject_attachment(result_path, result_data, case_id, verdict, reason)
        print(f"  [OK] {case_id} -> {name}")
        injected += 1

    print(f"\nInjected {injected}/{len(visual_results)} visual review results into {args.allure_dir}")
    print("Next: allure generate reports/allure-results -o reports/allure-report --clean")


if __name__ == "__main__":
    main()
