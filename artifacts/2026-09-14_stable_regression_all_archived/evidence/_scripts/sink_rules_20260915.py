# -*- coding: utf-8 -*-
"""2026-09-15 三处沉淀：rule.md 新增 + orchestrator 归档 gate 子条 + test-writing SKILL 第 39 条改写。"""
from pathlib import Path

log = []

# 1) rule.md 新增一节（沿用现有「来源：task_id + 验证」格式）
p = Path("rule.md"); s = p.read_text(encoding="utf-8")
section = '''## 脚本复用与仓库资源路径（有稳定资产背书）

- **脚本被复制到别处运行时，仓库资源必须逐级上溯，不要用 `parents[N]` 写死层级**：
  `tests/` 下 `parents[1]` 是仓库根，但复制到 `archive/<模块>/` 后 `parents[1]` 变成 `archive/`，
  素材会被解析成 `archive/test_images/...` → `FileNotFoundError`（实测 7 个归档副本整轮回归误报失败）。
  - 统一写法：逐级上溯，取具备 `test_images/`、`data/`、`page_map/` 的目录作为仓库根（`_repo_root()`）。
  - 该坑同时覆盖 `test_images/` 素材、`data/*.yaml`、`page_map/*.yaml`——三者都要按仓库根解析。
- **跨 `tests/` 与 `archive/` 共用的公共 helper 放仓库根**：靠 root `conftest.py` 让仓库根进入 `sys.path`；
  不要在 `archive/<模块>/` 放同名副本（多份副本必然漂移，改一处漏一处）。
- **禁止在 `archive/` 下新增 `conftest.py`**：同名模块会遮蔽 root `conftest.py`，
  归档用例 `from conftest import allure_screenshot` 直接 ImportError（实测已回退该做法）。
- 来源：`2026-09-14_stable_regression_all_archived`；验证：7 个归档副本素材 / 数据路径整改 + helper 上收仓库根后
  `pytest --collect-only` = 106 tests / 0 error（2026-09-15）。

'''
anchor = "## 测试设计"
if "脚本复用与仓库资源路径" in s:
    log.append("rule.md 已存在该节，跳过")
elif anchor in s:
    s = s.replace(anchor, section + anchor, 1); p.write_text(s, encoding="utf-8"); log.append("rule.md 新增「脚本复用与仓库资源路径」")
else:
    log.append("!! rule.md 锚点缺失")

# 2) orchestrator.md 归档 gate 第 7 条追加子条
p = Path("artifacts/runtime/orchestrator.md"); s = p.read_text(encoding="utf-8")
old = "暂不归档：写 archive.md `skipped_by_user`，可 completed；未引用中间产物仍按本条清理。"
new = old + "\n   - **归档副本可独立复跑校验**（复制脚本到 `archive/` 时必做）：核对脚本引用的公共模块是否在仓库根、路径常量（`test_images/`、`data/`、`page_map/`）是否逐级上溯仓库根；不满足则先整改再归档，否则归档副本会在下轮回归里假失败（2026-09-14 实测：7 个副本素材路径报错，误判整轮失败）。"
if "归档副本可独立复跑校验" in s:
    log.append("orchestrator 已存在该子条，跳过")
elif old in s:
    s = s.replace(old, new, 1); p.write_text(s, encoding="utf-8"); log.append("orchestrator 归档 gate 追加「归档副本可独立复跑校验」")
else:
    log.append("!! orchestrator 锚点缺失")

# 3) test-writing SKILL 第 39 条改写
p = Path("skills/ui-test-test-writing/SKILL.md"); s = p.read_text(encoding="utf-8")
old = "5. 测试目录统一 `tests/`。"
new = "5. 测试**用例文件**统一 `tests/`；跨 `tests/` 与 `archive/` 复用的公共 helper / 驱动模块放**仓库根**，不要在归档目录留副本（详见 `rule.md`）。"
if new in s:
    log.append("test-writing 第 39 条已改写，跳过")
elif old in s:
    s = s.replace(old, new, 1); p.write_text(s, encoding="utf-8"); log.append("test-writing SKILL 第 39 条改写（用例文件 vs 公共模块）")
else:
    log.append("!! test-writing 锚点缺失")

print("\n".join(log))