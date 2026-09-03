import io
p = r"page_map\pokecut\mobile_home_v1.yaml"
s = io.open(p, encoding="utf-8").read()
s = s.replace(
"""        action_result: 唤起文件选择器；完整抠图流程探索阶段未执行（可能消耗 credits）
        explore_status: skipped
        notes: 文件选择器触发已覆盖；抠图成功/失败/点数不足留待用例阶段用指定账号验证。""",
"""        action_result: 唤起文件选择器；匿名态上传有效图打开注册/获取点数弹层，不进入抠图；损坏图不进入画布
        explore_status: covered
        notes: 抠图成功/抠图失败/点数不足需登录且具备对应 credits 的账号态，留待用例阶段。"""
)
io.open(p, "w", encoding="utf-8").write(s)
print("patched page_map")
