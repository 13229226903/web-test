"""完整回归测试：pytest SEO 回归 + 独立脚本验证 + Allure 报告。

用法：
    python scripts/run_full_regression.py [--headed] [--base-url URL]

流程：
    1. 清空 allure-results
    2. pytest -m regression（SEO 回归 136 条）
    3. 独立脚本验证（verify_help_vue.py 等）
    4. 清理 xfailed 结果（独立验证已覆盖）
    5. allure generate 生成报告
    6. allure open 打开报告
"""
import os, sys, subprocess, argparse


def main():
    parser = argparse.ArgumentParser(description="完整回归测试")
    parser.add_argument("--headed", action="store_true", help="浏览器可见模式")
    parser.add_argument("--base-url", default="http://10.17.1.66:3102",
                        help="测试环境 URL，默认 http://10.17.1.66:3102")
    parser.add_argument("--no-report", action="store_true", help="不生成报告")
    parser.add_argument("--no-standalone", action="store_true", help="跳过独立脚本验证")
    args = parser.parse_args()

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    python = sys.executable or "python"

    # 1. 清空
    allure_dir = os.path.join(root, "reports", "allure-results")
    allure_report = os.path.join(root, "reports", "allure-report")
    os.makedirs(allure_dir, exist_ok=True)
    for f in os.listdir(allure_dir):
        os.remove(os.path.join(allure_dir, f))

    # 2. pytest 回归
    print("\n=== 1/4 pytest SEO 回归 ===\n")
    pytest_args = [
        python, "-m", "pytest", "tests/", "-m", "regression", "-v",
        f"--base-url={args.base_url}",
        f"--alluredir={allure_dir}",
    ]
    if args.headed:
        pytest_args.append("--headed")
    r1 = subprocess.run(pytest_args, cwd=root)

    # 3. 独立脚本验证
    if not args.no_standalone:
        standalone_scripts = [
            "scripts/verify_help_vue.py",
            "scripts/verify_homepage_vue.py",
        ]
        for s in standalone_scripts:
            spath = os.path.join(root, s)
            if os.path.exists(spath):
                print(f"\n=== 2/4 独立脚本 {s} ===\n")
                subprocess.run([python, spath], cwd=root)

    # 4. 清理 xfailed
    print("\n=== 3/4 清理 xfailed ===\n")
    subprocess.run([python, os.path.join(root, "scripts", "cleanup_xfailed.py")], cwd=root)

    # 5. 生成并打开报告
    if not args.no_report:
        print("\n=== 4/4 生成 Allure 报告 ===\n")
        subprocess.run(["allure", "generate", allure_dir, "-o", allure_report, "--clean"], cwd=root)
        subprocess.run(["allure", "open", allure_report], cwd=root)
        print(f"\n报告已生成: {allure_report}/index.html")

    print("\n=== 回归测试完成 ===")


if __name__ == "__main__":
    main()
