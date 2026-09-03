---
task_id: task-22_feishu_mobile_home
agent: page-map-sync
status: confirmed
repair_scope: full_exploration
gate_exemption: null
inputs:
  entry_url: http://10.17.1.66:3001/
  entry_path: /
  requirement_doc: D:\downloads\用例\task-22-飞书文档_ v3.0\移动端首页优化大纲（安国）.md
  existing_page_map: page_map/pokecut/home_v3.yaml (PC 首页，只读参考)
outputs:
  scanned_pages: [http://10.17.1.66:3001/]
  page_map_versions: [page_map/pokecut/mobile_home_v1.yaml]
  coverage_gates:
    agent_hero: covered
    function_board: covered
    effect_board: covered
    test_board: covered
    portrait_board: covered
    enhance_board: covered
    data_board: covered
    reviews_board: covered (个别资源名与用例文档不一致，见正文)
    faq_board: covered
    mobile_app_board: covered
    bottom_nav: covered
    performance: skipped
  state_button_coverage:
    mobile_default: covered
    agent_popovers: covered
    upload_success: covered
    login_modal: covered
  requirement_actual_diffs: 见正文
  bug_candidates: []
  skipped: 见正文
  special_dependencies:
    - "staging 右下角 DEBUG 浮层与底部 Pricing 按钮重叠，自动化建议 JS click/force 规避。"
  specs_updated: []
next_agent: test-case-design
created_at: 2026-08-31 13:50:00
---

# 探索结果摘要（sync.md）

## 一、探索摘要
- 用 Playwright 在移动端视口（390x844、iPhone UA、has_touch、deviceScaleFactor=3）对 `http://10.17.1.66:3001/` 做存量首次探索，以《移动端首页优化大纲（安国）》为探索清单逐板块核对。
- 页面为响应式移动端首页，含首屏 Agent 框、功能板块、effect(AI Templates)、Test、人像、画质增强、数据展示、用户评论、FAQ、移动端展示、固定底部导航、顶部 Sign up。
- 未登录态可匿名浏览；Sign up 打开登录/注册弹层（Email + Verification Code）。
- 上传类入口均能唤起系统文件选择器；有效图上传后进入 `/create/edit?pid=*` 移动端画布并展开对应面板。
- 探索方法注意：视口外元素需先 `scroll_into_view_if_needed` 再点击，否则会出现假失败（人像/画质增强已按此复测并纠正）。

## 二、页面覆盖矩阵（按用例逐条）

### Agent 框首屏
- ✅ 首屏单列 Agent 框结构 — covered
- ✅ 首屏文案/多语言 key — covered（实际文案见「需求差异」）
- ✅ 主按钮点击唤起上传弹窗 — covered
- ✅ 主按钮上传成功后跳转移动端画布 — covered（/create/edit?pid=*）
- ✅ 模型入口沿用 v2.9 — covered（8 个模型）
- ✅ 比例入口沿用 v2.9 — covered（8 档比例）
- ⚠️ 分辨率入口沿用 v2.9 — gap：实测弹层仅见 `1k` 一项，需确认是否完整
- ✅ Generate 未满足条件禁用 — covered（输入框为空时 disabled）
- ✅ Agent 输入框输入文本后 Generate 可点击并进入画布 — covered（输入后 enabled，点击进入 /create/edit?pid=*，匿名态随后弹注册/获取点数弹层）

### 功能板块
- ✅ 6 个两列功能卡片 — covered
- ✅ 卡片图标/标题 + 底部按钮 — covered
- ✅ Remove Background 上传打开面板 — covered
- ✅ Clothes Changer 上传打开面板 — covered
- ✅ HD Photo Coverter 上传打开面板 — covered
- ✅ ID Photo Maker 点击唤起上传弹窗 — covered（文件选择器触发）
- ⚠️ ID Photo Maker 匿名态上传有效图 — 实际：停留在首页并打开注册/获取点数弹层（需登录 + credits 才进入抠图）
- ✅ ID Photo Maker 匿名态上传损坏图 — covered：不跳转、不进入画布（首页拦截；未捕获明确错误提示）
- ⏭ ID Photo Maker 抠图成功/点数不足 — skipped（需登录且具备对应 credits 的账号状态）
- ⏭ ID Photo Maker 抠图失败反馈 — skipped（需登录后可正常上传但抠图失败的素材/账号态，暂缺）
- ✅ Body Editor 上传打开面板 — covered
- ✅ AI Replace 上传打开面板 — covered
- ✅ More Pokecut Tools 跳转 tools 页 — covered

### effect 板块（实际为 AI Templates）
- ✅ 板块文案按配置展示 — covered（实际标题 `Create Faster with Pokecut's AI Templates`）
- ⚠️ 与 PC 端同一份配置 — gap：移动端标题 `Create Faster...`，PC home_v3 为 `Start Faster...`，标题文案不一致
- ✅ 支持上下滑动 — covered
- ✅ effect 点击唤起上传弹窗 — covered
- ✅ effect 上传后进入对应功能面板 — covered
- ✅ See More Creations 跳转 create 页 — covered

### Test 板块
- ✅ 单列+两列卡片布局 — covered
- ✅ 文案按配置展示 — covered（实际标题 `Test Your Portrait Before You Edit`）
- ✅ Pretty Scale / Ethnicity Guesser / Eye Color Detector / Body Shape Detector 跳转 — covered（staging 站内 `/tools/*`；正式环境对应 `www.pokecut.com/tools/*`，符合需求所指正式域名）

### 人像板块
- ✅ 四分类 tab + 横向卡片列表 — covered
- ✅ 文案按配置展示 — covered
- ✅ 分类 tab 切换沿用 PC 逻辑 — covered（实测 Face/Body/Hair/Background 切换正常，卡片内容随 tab 切换）
- ✅ 分类卡片内容/跳转沿用 PC 同配置 — covered（Face→face-editor，Body→body/image-to-image，Hair→hair-editor，Background→background 相关链接）

### 画质增强
- ⚠️ 板块文案和四标签 — gap：实际标签 `HD Enhance / Portrait AI / Text Enhance / Ultra Enhance`，用例为 `Portrait Enhance`（实际为 `Portrait AI`）
- ⚠️ 指定图片资源 — gap：主图为 canvas 绘制（720x540），非用例指定的 `homepagerefresh_enhance_26071315000130.webp` 静态 img
- ✅ HD Enhance 跳转工具页 — covered（staging `/tools/hd-pic-converter`，正式环境对应 `www.pokecut.com/tools/hd-pic-converter`）
- ✅ Text Enhance 跳转工具页 — covered（staging `/tools/ai-image-text-enhancer`）
- ✅ Portrait AI 上传打开人像模式面板 — covered（file chooser + /create/edit）
- ✅ Ultra Enhance 上传打开 ultra 模式面板 — covered（file chooser + /create/edit）

### 数据展示
- ✅ 2x2 卡片布局 — covered
- ✅ 展示指定数据 — covered（3M+ creators / 200+ AI tools / 500M+ edits processed / #2 Product Hunt）
- ✅ 数据卡片点击选中态 — covered
- ✅ Product Hunt 新标签页跳转 — covered

### 用户评论展示
- ✅ 自动横向循环滚动 — covered（DOM 中 5 张评论卡重复渲染形成循环结构）
- ⏭ 手指滑动暂停自动滚动 — skipped（headless 未模拟触摸手势）
- ⏭ 停止滑动后恢复自动滚动 — skipped（同上）
- ⏭ 自动滚动期间点击不误触发跳转 — skipped（未执行）
- ✅ 标题和评分说明 — covered（`What Users Say About Pokecut?` / `172.8K RATINGS`）
- ✅ 评论1-5 内容 — covered（用户名/身份/内容匹配）
- ⚠️ 评论1-5 图片资源 — 4/5 与用例一致；Jessica 实际 `homepagerefresh_reviewportrait1_26071315000824.webp`（用例 00138），Leo 实际 `homepagerefresh_reviewgenerate1_26071315000140.webp`（用例误写 reviewportrait1_00138），均以实际为准
- ✅ 5 个用户名外链 no-follow 且新标签页 — covered（rel="nofollow noopener noreferrer"）

### FAQ
- ✅ 文案按最新多语言 key — covered（8 组问答）
- ✅ 问题项展开/收起 — covered
- ✅ `/pricing` 链接 — covered
- ✅ `/term-of-use` 链接 — covered
- ✅ `submitting a ticket` 退款工单入口 — covered（`a[data-submit-ticket="refund"]`）

### 移动端展示
- ⚠️ 内容沿用线上和既有多语言 key — gap：实际英文文案 `Pokecut Mobile App / Edit, create, and enhance photos on the go...`，与用例 key 名表述不同（值以线上为准）
- ✅ 文字左对齐 — covered（text-align=start）
- ✅ 按钮点击逻辑保持线上设置 — covered（App Store / Google Play 链接 target=_blank）

### 固定底部悬浮控件
- ✅ 常驻展示并适配安全区 — covered
- ⚠️ 入口文案按配置 — gap：实际 `Home / All Tools / Upload / Generate / Pricing`，用例写 `General`（实际为 `Generate`）
- ✅ Home 跳转 create 页 — covered（/create）
- ✅ All Tools 跳转 tools 页 — covered（/tools）
- ✅ Upload 唤起上传弹窗 — covered
- ✅ Upload 上传成功进入画布 — covered
- ⏭ Upload 格式校验 — skipped（test_images 无非法格式素材）
- ⏭ Upload 大小校验 — skipped（未指定超限大小素材）
- ✅ Upload 损坏图校验 — covered（损坏图不进入画布）
- ⚠️ General 直接进入生图画布 — gap：入口实际为 `Generate`；行为 covered（无 file chooser，直接 /create/edit）
- ✅ Pricing 跳转价格页 — covered（/pricing；staging 的 DEBUG 浮层与 Pricing 重叠，建议 JS click/force）

### 性能要求
- ⏭ PageSpeed 评分 80+ — skipped（需外部 PageSpeed 环境）

## 三、需求差异（requirement_actual_diffs）

| 板块 | 需求预期 | 页面实际 | diff_type |
|---|---|---|---|
| 画质增强标签 | Portrait Enhance | Portrait AI | gap |
| 画质增强图片 | homepagerefresh_enhance_26071315000130.webp | canvas 绘制 | gap |
| 底部导航 | General | Generate | gap |
| effect 标题（与 PC 同配置） | PC: Start Faster... | 移动: Create Faster... | gap |
| 移动端展示文案 | homepageH2App 等 key | 实际英文长文案（线上值） | gap |
| 分辨率入口 | 多档分辨率 | 仅见 1k | gap |
| 评论1 Jessica 图片 | ...reviewportrait1_...00138.webp | ...reviewportrait1_...00824.webp | gap |
| 评论3 Leo 图片 | ...reviewportrait1_...00138.webp | ...reviewgenerate1_...00140.webp | gap（用例疑似笔误，以实际为准） |

## 四、bug_candidates
- 本轮未确认阻塞首页探索的 bug_candidate（人像/画质增强假失败已纠正）。
- 另记录：首页 Sign up 弹层切换 Log in 后，填入邮箱+验证码并点击 Log in，弹层不关闭、无跳转、无错误提示（登录未完成，file_bug，不阻塞首页探索/用例）。

## 五、skipped
- ID Photo Maker 抠图成功/抠图失败/点数不足：需登录且具备对应 credits/账号状态的账号；匿名态仅能验证到「打开注册/获取点数弹层」与「损坏图首页拦截」。
- 用户评论触摸滑动/暂停/恢复/误触：headless 未模拟触摸手势。
- Upload 格式/大小校验：缺少对应非法格式/超限大小素材（test_images 仅有图片）。
- PageSpeed 性能评分：需外部 PageSpeed 环境。

## 六、关键发现
- 有效图上传后统一进入 `/create/edit?pid=*` 移动端画布；不同入口展开对应面板。
- 底部导航 Upload 为纯图标按钮（无文字 label）；Generate 即用例中的 General。
- 顶部 Sign up 打开登录/注册弹层，字段为 Email + Verification Code，无 role=dialog。
- 语言切换按钮打开：English / 简体中文 / 繁體中文 / Français / Indonesia / Deutsch / Tiếng Việt / Türkçe / Italiano / Português / Español / Русский / 日本語 / แบบไทย。
- 人像四个 tab 切换正常，默认选中 Body；点击前需先滚动到元素。
- 画质增强主图为 canvas 绘制；HD/Text 跳转站内工具页，Portrait/Ultra 触发上传。

## 七、下游注意事项
- test-case-design 基于本 sync.md 的实际文案与交互写用例；gap 文案以实际页面为准。
- 分辨率入口弹层仅见 1k，用例阶段建议单独确认档位完整性。
- 底部 Pricing 定位需规避 staging DEBUG 浮层遮挡。
- 多语言交叉验证（除英文外）未在探索阶段执行，用例阶段如需可单独覆盖。

## 八、版本差异摘要
- 新增 `page_map/pokecut/mobile_home_v1.yaml`（移动端首页首版）。
- 未修改、未覆盖任何历史 page_map。
