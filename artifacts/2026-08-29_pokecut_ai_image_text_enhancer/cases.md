---
task_id: 2026-08-29_pokecut_ai_image_text_enhancer
agent: test-case-design
phase: final_after_sync
status: confirmed
inputs:
  - D:\Test\web-test\飞书文档_ 文字画质增强实验优化(安国)-AI分析后的CheckBox.md
  - artifacts/2026-08-29_pokecut_ai_image_text_enhancer/sync.md
  - page_map/pokecut/ai_image_text_enhancer_v3.yaml
outputs:
  case_count: 18
  priority_breakdown: {P0: 3, P1: 13, P2: 2}
next_agent: test-writing
created_at: 2026-08-29 18:10:00 +08:00
---

# 测试用例 — 文字画质增强实验页（AI Image Text Enhancer）精简版

> 阶段 final_after_sync。脚本入口 `tests/test_ai_image_text_enhancer_experiment.py`（18 条）。
> 环境：测试服 http://10.17.1.66:3001 默认；登录/生成/账号态类先切预部署再登录。PC 1920x1080 en-US，移动端 iPhone 13。
> 默认上传素材 `test_images/文字测例.jpg`（1080x1440）；分辨率边界仍用 `1K.jpg / 4K.jpg / 4K.png / 8K.jpg`；异常用 `损坏的图.png`。
> 账号：会员 450832596@qq.com，单项购买 03201449879@qq.com，免费随机邮箱；验证码 123456。

## 用例矩阵

| ID | 层 | 标题 | 状态 | 关键断言 |
|---|---|---|---|---|
| TC-TEXT-L2-001 | L2 | 上传后页内处理 + 默认勾选态（含 L1 结构） | 通过 | H1/上传入口；上传不跳转；效果区/分辨率区/点数区存在；仅 Enhance Text 默认选中 |
| TC-TEXT-L2-005 | L2 | 分辨率区显隐与无效果置灰（选择态） | 通过 | 无效果置灰；仅非增强模式隐藏分辨率区 |
| TC-TEXT-L2-002 | L2 | 结果态：非 Enhance Text 结果不展示分辨率信息 | 跳过 | 生成非增强结果后 before/after 且无 2k/4k/8k；当前非增强生成超时 |
| TC-TEXT-L4-001 | L4 | 多选组合点数实时刷新与普通账号点数规则 | 通过 | 2k/4k/8k 点数；四效果组合；去勾选刷新 |
| TC-TEXT-L2-003 | L2 | 四个 tooltip 文案 | 通过 | 四条 tooltip 文案精确命中 |
| TC-TEXT-L4-002 | L4 | 免费试用额度态：按钮显示 Free | 通过 | cost_state=free 时显示 Free |
| TC-TEXT-L4-003 | L4 | 会员账号 Free icon 与点数规则 | 跳过 | 预部署登录后仍显示免费档 2/2/6，会员权益未生效 |
| TC-TEXT-L4-004 | L4 | 单项购买账号点数规则 | 通过 | 2k/4k=2、8k=6、四效果=14 |
| TC-TEXT-L5-001..004 | L5 | 分辨率边界 | 通过 | 自动选下一档、灰显低档、8K 非 highest |
| TC-TEXT-L3-001 | L3 | 损坏图片上传异常 | 通过 | 可见错误提示，页面不崩 |
| TC-TEXT-L3-002 | L3 | 免费账号购买拦截（预部署） | 通过 | 免费额度用尽时出现购买弹窗 |
| TC-TEXT-L6-001 | L6 | 生成到结果态 + 下载 + 继续增强 | 通过 | 结果态信号、下载文件名、继续增强 |
| TC-TEXT-L2-004 | L2 | 结果态 Edit More 进入编辑链路 | 通过 | 点击后进入编辑/画布链路 |
| TC-TEXT-L4-005 | L4 | 移动端上传后模式与点数区域 | 通过 | 横向模式、点数区、视觉审查 |
| TC-TEXT-L3-003 | L3 | 真 8K highest clarity 缺口 | 跳过 | 缺 fixture/后端 trace |

## 本轮修正的两个问题
1. L2-002 原为「选择态分辨率显隐」，需求实为「结果态非 Enhance Text 结果不展示分辨率信息」。已改为结果态用例（需真实生成）。但排查发现：预部署下 remove_glare 单模式生成超过 180s 仍未出结果（enhance_text 约 10s 即出结果），故该条按环境/后端问题跳过，证据 `investigate_l2_002b_v3.json`。
2. L4-003 原未真正登录会员（测试服登录 authToken 空），误把匿名免费态当成会员。已改为预部署登录并断言登录成功。排查发现：预部署下该账号虽能登录，但显示免费档 2k/4k/8k=2/2/6，而非需求 Pro/Ultra 的 Free/Free/4；故按环境/账号数据问题跳过，证据 `investigate_member_v3.json`。

## 待用户确认
1. 会员账号 450832596@qq.com 在预部署是否有有效 Pro/Ultra 订阅；若无，需要产品提供预部署可用会员账号。
2. 非增强模式（去反光/去摩尔纹/文本扫描）生成是否当前环境慢或失败，需后端确认。
