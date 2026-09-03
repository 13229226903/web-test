---
task_id: 2026-08-29_pokecut_canvas_photo_enhancer
agent: page-map-sync
status: pending_review
repair_scope: full_exploration
gate_exemption: false
inputs:
  - D:\Test\web-test\飞书文档_ 画质增强优化-AI分析后的CheckBox.md
  - D:\Test\web-test\artifacts\2026-08-29_pokecut_canvas_photo_enhancer\requirement_draft_v2.md
  - D:\Test\web-test\page_map\pokecut\create_ai_tools.yaml
  - D:\Test\web-test\page_map\pokecut\infinite_canvas_enhance_v1.yaml
outputs:
  scanned_pages: [/create, /agent?pid=<uuid>]
  page_map_versions: [infinite_canvas_enhance_v2]
  coverage_gates:
    create_trending_tools_start_from_photo: covered
    canvas_upload_and_toolbar: covered
    canvas_enhance_panel: covered
    prd_resolution_2k_4k_8k: bug_candidate
    prd_8k_upload_no_compress: bug_candidate
    prd_result_compare: skipped
    prd_failure_and_paywall: skipped
    prd_batch_ultra: skipped
    prd_analytics: skipped
  state_button_coverage: covered
  requirement_actual_diffs: 77
  bug_candidates: 7
  skipped:
    - 未点击 Enhance 主按钮，避免真实生成消耗 credits/免费次数
    - 结果态/失败态/Compare/购买拦截/批量 Ultra/统计埋点需要登录、生成、账号态或后端 trace，本轮不观察
  special_dependencies: [test_images/1K.jpg, test_images/4K.jpg, test_images/4K.png, test_images/8K.jpg, test_images/低分辨率.JPG, test_images/文字测例.jpg, PC 1920x1080 en-US, 测试服 http://10.17.1.66:3001]
  specs_updated: false
next_agent: test-case-design
created_at: 2026-08-29 23:10:00 +08:00
---

# sync v2 — 画质增强优化（Canvas Enhance 入口，正确需求）

## 1. 探索摘要
- /create → Trending Tools → Start from a Photo → 上传 → /agent?pid=<uuid> → 顶部 Enhance → AI Enhancer 链路可走通。
- AI Enhancer 面板实际包含 5 个互斥模式：Standard Mode / Old Photo Mode / Portrait Mode / Text Mode / Ultra HD Mode，tooltip 均已采集。
- 未发现需求「PC 无限画布新增 2K、4K、8K 选择」对应的 2K/4K/8K 分段选择器；面板只显示模式行的输入→输出固定尺寸。
- 8K 原图上传后在 Standard 行显示 3072px*4096px，长边被压到 4096，未满足「8K 图片从无限画布入口进入后不被压缩到 4096」。

## 2. 页面覆盖矩阵
| 状态 | 覆盖 | 证据 |
|---|---|---|
| /create Trending Tools 入口 | covered | explore_canvas_enhance_v1.json |
| 上传后 /agent 画布与顶部 Enhance | covered | 同上 |
| AI Enhancer 面板默认态/模式/tooltip | covered | explore_canvas_enhance_v1.json / explore_enhance_tooltips_v2.json |
| 分辨率 2K/4K/8K 选择 | bug_candidate | explore_canvas_resolution_ac.json |
| 8K 上传不压缩 | bug_candidate | 同上（8K.jpg 条目） |
| 结果态/失败态/购买/批量/埋点 | skipped | 未点击生成或非当前入口 |

## 3. 需求差异（requirement_actual_diffs）
| AC ID | 所属模块 | 用例标题 | 差异类型 | 说明 |
|---|---|---|---|---|
| HQ-01 | 画质增强工作流变更 | Ultra 模式 2K 提交使用 `pkweb_comfyui_enhance_natural` | skipped | 未在本轮真实入口观察（需登录/生成/后端 trace 或非当前入口） |
| HQ-02 | 画质增强工作流变更 | Ultra 模式 2K 结果前端 resize 到 2048 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-03 | 画质增强工作流变更 | Ultra 模式 4K 提交使用 `pkweb_comfyui_enhance_natural` | skipped | 未在本轮真实入口观察（需登录/生成/后端 trace 或非当前入口） |
| HQ-04 | 画质增强工作流变更 | Ultra 模式 8K 长边小于 4096 时走 Ultra 链式路由 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-05 | 画质增强工作流变更 | Ultra 模式 8K 长边小于 4096 时链式第一步使用 natural | skipped | 未在本轮真实入口观察（需登录/生成/后端 trace 或非当前入口） |
| HQ-06 | 画质增强工作流变更 | 8K 输入长边等于 4096 时直接走 `pkweb_realesrgan` | skipped | 需真实生成/后端 trace，验证 pkweb_realesrgan 路由 |
| HQ-07 | 画质增强工作流变更 | Normal 模式 2K 路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-08 | 画质增强工作流变更 | Portrait 模式 2K 路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-09 | 画质增强工作流变更 | Text 模式 2K 路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-10 | 画质增强工作流变更 | Normal 模式 4K 路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-11 | 画质增强工作流变更 | Portrait 模式 4K 路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-12 | 画质增强工作流变更 | Text 模式 4K 路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-13 | 画质增强工作流变更 | Portrait 4K 工作流内部替换 natural 增强节点 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-14 | 画质增强工作流变更 | Normal 模式 8K 长边小于 4096 时链式路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-15 | 画质增强工作流变更 | Portrait 模式 8K 长边小于 4096 时链式路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-16 | 画质增强工作流变更 | Text 模式 8K 长边小于 4096 时链式路由保持不变 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-17 | 画质增强工作流变更 | `pkweb_comfyui_enhance_natural` Web style 配置与元数据注入核验 [💡历史沉淀] | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-18 | PC 无限画布新增 2K、4K、8K 选择 | 单图层打开 Enhance 面板展示分辨率分段选择 | bug_candidate | 面板可打开，但无 2K/4K/8K 分段选择；实际展示固定输入→输出尺寸 |
| HQ-19 | PC 无限画布新增 2K、4K、8K 选择 | 移动端画布不新增 PC 分辨率选择改造 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-20 | PC 无限画布新增 2K、4K、8K 选择 | SEO 页面不新增 PC 分辨率选择改造 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-21 | PC 无限画布新增 2K、4K、8K 选择 | 独立 HD Photo Converter 页面不新增 PC 分辨率选择改造 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-22 | PC 无限画布新增 2K、4K、8K 选择 | 长边小于 2048 的图片默认预选 2K | bug_candidate | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 |
| HQ-23 | PC 无限画布新增 2K、4K、8K 选择 | 长边大于等于 2048 且小于 4096 的图片默认预选 4K | bug_candidate | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 |
| HQ-24 | PC 无限画布新增 2K、4K、8K 选择 | 长边等于 4096 的图片默认预选 8K 且允许选择 4K | bug_candidate | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 |
| HQ-25 | PC 无限画布新增 2K、4K、8K 选择 | 长边大于 4096 且小于 8192 的图片默认预选 8K | bug_candidate | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 |
| HQ-26 | PC 无限画布新增 2K、4K、8K 选择 | 长边等于 8192 的结果图默认预选 8K 并展示最高画质提示 | bug_candidate | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 |
| HQ-27 | PC 无限画布新增 2K、4K、8K 选择 | 切换到新的画布图层后按新图层尺寸重新推荐分辨率 | skipped | 未在本轮真实入口观察（需登录/生成/后端 trace 或非当前入口） |
| HQ-28 | PC 无限画布新增 2K、4K、8K 选择 | 增强完成后选中新结果图按结果图尺寸重新推荐 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-29 | PC 无限画布新增 2K、4K、8K 选择 | 同一模式 4K 结果图继续选择 8K 时以结果图为输入 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-30 | 增强结果与画布内对比 | 任务成功后新增结果图且不覆盖原图 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-31 | 增强结果与画布内对比 | 增强成功结果展示本次模式和分辨率 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-32 | 增强结果与画布内对比 | 有源图关联的成功结果首次点击自动进入对比态 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-33 | 增强结果与画布内对比 | 首次退出后再次选中结果图需点击 Compare 才进入对比态 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-34 | 增强结果与画布内对比 | 源图不可用的结果图不展示 Compare 入口 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-35 | 增强结果与画布内对比 | loading 状态结果不展示 Compare 入口 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-36 | 增强结果与画布内对比 | 普通失败状态结果不展示 Compare 入口 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-37 | 增强结果与画布内对比 | 审核失败状态结果不展示 Compare 入口 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-38 | 增强结果与画布内对比 | 对比态在结果图边界内叠加 Before/After | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-39 | 增强结果与画布内对比 | 对比态展示模式、分辨率和前后尺寸信息 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-40 | 增强结果与画布内对比 | 旧照片功能结果对比态不显示前后分辨率数据 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-41 | 增强结果与画布内对比 | 对比态内仅响应滑杆拖动 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-42 | 增强结果与画布内对比 | 按 Escape 退出对比态后恢复正常图层和工具栏状态 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-43 | 增强结果与画布内对比 | 点击其他功能面板按钮退出对比态后恢复正常图层和工具栏状态 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-44 | 增强结果与画布内对比 | 重新选择其他图层退出对比态后恢复正常图层和工具栏状态 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-45 | 增强结果与画布内对比 | Compare 查看态不产生处理副作用 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-46 | 失败与边界 | 输入图片无法解析沿用当前失败分支 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-47 | 失败与边界 | 积分不足沿用当前拦截分支 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-48 | 失败与边界 | Ultra 权限不足沿用当前拦截分支 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-49 | 失败与边界 | 任务提交前失败沿用当前失败分支 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-50 | 失败与边界 | 任务处理失败沿用当前失败分支 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-51 | 失败与边界 | 审核失败沿用当前审核失败分支 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-52 | 失败与边界 | 任务恢复沿用当前恢复分支 | skipped | 需真实生成/结果态/失败分支，本轮未点击生成 |
| HQ-53 | 点数抠除说明 | 通用模式 2K/4K credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-54 | 点数抠除说明 | 人像模式 2K/4K credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-55 | 点数抠除说明 | 通用模式 8K credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-56 | 点数抠除说明 | 人像模式 8K credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-57 | 点数抠除说明 | 文字模式 2K/4K credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-58 | 点数抠除说明 | 文字模式 8K credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-59 | 点数抠除说明 | Ultra 模式 2K/4K 权限和 credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-60 | 点数抠除说明 | Ultra 模式 8K 权限和 credits 扣除 | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-61 | 点数抠除说明 | 低阶画质增强 credits 不足触发每日免费预览 [💡历史沉淀] | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-62 | 点数抠除说明 | 未登录用户 credits 不足不进入低阶免费预览 [💡历史沉淀] | skipped | 需登录/账号态/真实生成或后端 trace |
| HQ-63 | 无限画布图片上传限制调整 | 8K 图片从无限画布入口进入后不被压缩到 4096 | bug_candidate | 实测 8K.jpg 原图 6144x8192，上传后 Standard 显示 3072px*4096px，长边被压到 4096，与需求不符 |
| HQ-64 | 画质增强批量编辑新增 Ultra 模式 | 批量编辑 Enhance 页展示 Ultra 模式 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-65 | 画质增强批量编辑新增 Ultra 模式 | 批量 Ultra 使用专门批量接口提交 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-66 | 画质增强批量编辑新增 Ultra 模式 | 会员使用批量 Ultra 按每张 4 credits 扣除 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-67 | 画质增强批量编辑新增 Ultra 模式 | 批量 Ultra 未登录时按现有逻辑拦截 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-68 | 画质增强批量编辑新增 Ultra 模式 | 批量 Ultra 非会员时按现有逻辑拦截 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-69 | 画质增强批量编辑新增 Ultra 模式 | 批量 Ultra 会员点数不足时按现有逻辑拦截 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-70 | 统计埋点 | 无限画布页画质增强 xK-yy 模型使用次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-71 | 统计埋点 | 无限画布页画质增强 xK-yy 模型失败次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-72 | 统计埋点 | 无限画布页画质增强 xK-yy 模型重试次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-73 | 统计埋点 | credits 用完触发注册弹窗次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-74 | 统计埋点 | credits 用完触发注册成功次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-75 | 统计埋点 | credits 用完触发购买弹窗次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-76 | 统计埋点 | credits 用完触发购买 zz 成功次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |
| HQ-77 | 统计埋点 | 无限画布页画质增强结果下载保存次数上报 | skipped | 非当前入口或需设备/埋点口径，本轮不观察 |

## 4. bug_candidates

| ID | 严重度 | 说明 | recommended_action |
|---|---|---|---|
| HQ-18 | P0/阻塞 | 面板可打开，但无 2K/4K/8K 分段选择；实际展示固定输入→输出尺寸 | blocked / file_bug，需确认当前测试服是否未部署该新功能，或该入口版本不匹配 |
| HQ-22 | P0/阻塞 | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 | blocked / file_bug，需确认当前测试服是否未部署该新功能，或该入口版本不匹配 |
| HQ-23 | P0/阻塞 | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 | blocked / file_bug，需确认当前测试服是否未部署该新功能，或该入口版本不匹配 |
| HQ-24 | P0/阻塞 | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 | blocked / file_bug，需确认当前测试服是否未部署该新功能，或该入口版本不匹配 |
| HQ-25 | P0/阻塞 | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 | blocked / file_bug，需确认当前测试服是否未部署该新功能，或该入口版本不匹配 |
| HQ-26 | P0/阻塞 | 面板无 2K/4K/8K 分段选择，无法验证默认预选/置灰规则 | blocked / file_bug，需确认当前测试服是否未部署该新功能，或该入口版本不匹配 |
| HQ-63 | P0/阻塞 | 实测 8K.jpg 原图 6144x8192，上传后 Standard 显示 3072px*4096px，长边被压到 4096，与需求不符 | blocked / file_bug，需确认当前测试服是否未部署该新功能，或该入口版本不匹配 |

## 5. 关键发现与下游注意事项
- 当前指定入口的 Enhance 面板是旧版/现有画布 AI Enhancer 行为；需求要求的 PC 分辨率 2K/4K/8K 选择未出现。
- 未点击 Enhance 主按钮，未验证生成、结果态、credits 扣除、Compare 等需要真实处理的后置状态。
- 建议先确认测试服是否已部署「画质增强优化」新版本；若已部署，上述两条 bug candidate 为真实缺口，应提 bug 后再继续。

## 6. 版本差异摘要
- page_map：infinite_canvas_enhance_v1.yaml → infinite_canvas_enhance_v2.yaml（新增分辨率/尺寸实测证据）。
- 历史 artifact 未覆盖；sync_v2 替代 sync v1 作为正确需求的对照结论。

> 本 sync 处于 pending_review，需用户确认 bug candidate 后再接力 test-case-design(final)。

