# 编码规则与技术避坑

> 本文件只放「跨页面通用的编码与技术规则」，供所有角色写代码、探索页面前读取。
> - 项目级事实（base_url / 目录 / 登录 / 账号 / 素材 / DEBUG 环境顺序）：见 `PROJECT.md`
> - 页面专属元素与交互坑：写入对应 `page_map/<模块>/<页面>.yaml`，不在本文件堆叠
> - 角色专属执行规则：写入对应 `skills/<role>/SKILL.md`
> - 路由 / Gate / 归档：见 `artifacts/runtime/orchestrator.md`
> - 知识沉淀（哪些沉淀 / 不沉淀 / 何时询问）：见 `artifacts/runtime/common.md`「知识沉淀规则」
>
> 下面「通用经验」以 `artifacts/regression_registry.md` 当前 stable_regression 资产的实际用法为准；
> 未被当前资产背书的旧经验单独列在「待验证」，不得当作默认正确路径。

## Selector 优先级（从高到低）

1. **语义 ID / role**：`page.get_by_role("button", name="Save")`、`#firstName`
2. **稳定属性**：`[placeholder="..."]`、`[aria-label="..."]`、`[data-testid="..."]`、`[href*="/topics/"]`、`[data-tool-id="..."]`
3. **文本定位**：`page.get_by_text(...)`、`button:has-text("提交")`
4. **避免**：hash class（随构建变化的 `.css-1a2b3c`）、`:nth-child(n)`、xpath 位置索引

## 等待时机（有稳定资产背书）

- 主路径：`page.goto(..., wait_until="domcontentloaded")` 后，用 `page.wait_for_timeout(...)` 等 Vue/SPA 水合完成再操作。
- 断言用 Playwright `expect(...)`（自带自动重试），不要 `assert locator.is_visible()`。
- 浮层（下拉/菜单/弹窗）出现后再操作，必要时 `expect(locator).to_be_visible()` 卡一下。

- **后端 AI 处理态是独立等待契约，不能只等 URL**（有稳定资产背书）：上传后可能存在三种形态，
  只凭 URL 判断会抢跑或空等——① 跳转后处理态还在跑（`Thinking...` 百分比）；② 非英文站点的本地化文案（`Denke nach...`）；
  ③ **处理发生在落地页、完成后才跳转**（实测 `/tools/zoom-in-photos` 的 `Optimizing image details`、`99%`，以及
  `/tools/ai-beard-remover` 完成后才进 `/agent`）。
  - 正确判据 = 「处理指示符消失」+「URL 形态到位」+「面板/结果关键词可见」**三者都满足**，才进入后续断言；
    不要用"URL 变了/页面没报错"推断处理已完成。
  - 处理态正则至少覆盖：`Thinking\.\.\.`、`Denke nach`、`Optimizing image`、`processing ultra`、`AI model is processing`。
  - 超时预算按最长任务给足（实测单项可达 106s，正常页 6~20s）；预算过短会把慢任务误报成失败。
  - 来源：`2026-09-14_seo_main_upload_interactions`；验证：2026-09-15 该判据落地后 24/24 通过（`evidence/selfrun_v2_final2.log`）；
    教训成本：未加此判据时连续 4 轮失败（16→6→4→2 条）。

- **面板预设生效晚于面板可见（实测 200~900ms）**：进入画布后底部主面板先以通用 tab 渲染，工具预设随后才把激活 tab 切到该工具专属面板；
  面板一可见就读激活 tab 会读到过渡态，表现为"默认面板波动"。断言默认面板前必须等该页 `page_map` 记录的默认面板激活。
  来源：`2026-09-15_seo_main_upload_mobile_interactions`；验证：高频时序探针 + 修正后 24/24 ×2（`evidence/panel_timing_probe_v3.json`）。

## 组件行为（通用）

- 三点菜单 / hover 菜单：先 hover 行，再点触发图标，菜单才渲染。
- popconfirm / tooltip 经常没有 `role=dialog`，按文本或就近容器定位。

## 画布类页面的状态持久化与会话级复用（有稳定资产背书）

- **画布编辑会持久化到 `pid`**：旧画布（`/create/edit?pid=...`）的图层增删 / 属性修改会写回同一个 pid，
  上一条用例的改动会带进下一条。复用画布时不要假设“重新打开 URL = 干净初始态”。
  - 用例执行顺序固定：结构 / 属性只读组在前，新增图层组在后；会改变图层尺寸的效果（如 Reflection 倒影）排在所属组最后。
  - 会互相污染的属性组（Opacity / Adjust / Shadow / Outline / Filter / Blend）在每条用例开始前统一调 reset helper 复位到默认值。
- **模板入口有频率限制**：连续走 `/template` 首卡上传约 17 次后会触发人机校验 / 上传不跳转（原始探索脚本同样失败）。
  → 不要逐条用例走上传入口；改 session 级前置只上传 / 建任务 1 次并记录画布 URL，其余用例新开 page 打开同一 URL（不重新上传）。
- **同一 pid 复用画布时，多层同文案/同色图层会完全重叠**：画布截图看不出层数，单层参数（Opacity/Space 等）改动在合成结果里几乎不可见
  （实测差异可低至 0.0001）。需要层数的用例必须用**图层列表面板计数**（如旧画布 Left Layer 面板：`layer-choosed` / `layer-unchoosed` 行）判定，不能只看画布；
  需要像素断言的用例应在操作前**清掉历史图层**（用户授权时可删）或给新图层换区别色，否则像素断言失去鉴别力。
  来源：`2026-09-11_old_canvas_text_panel_exploration`，13/13 通过。
- **面板内多个同类控件（滑杆/色块）必须按"label 下方最近的控件"定位**：同一分区里滑杆按行排列（如 Scope/Opacity/Distance/Angle），
  若取"分区内第一个 `input[type=range]`"，改 Distance 会实际打到 Scope；`querySelector` 也要限定在**该 label 所在行/最近容器**内，而不是整个分区。
  来源：同上（旧画布文字属性面板 Reflection 分区实测现象：Scope 被改、Distance 不变）。
- **同一页面可能挂载多套隐藏复用 section**：定位面板 / 分组时只认可见节点（`is_visible()` 过滤或 `:visible`），
  命中隐藏节点会导致改值无效、前后对比 diff=0。
- 来源：`2026-09-10_old_canvas_insert_panel_exploration`，2026-09-11 复跑 24/24 通过（改造后 24 次上传 → 1 次，42min → 9.5min）。

## 画布"已渲染"的判定（有稳定资产背书）

两条画布链路 DOM 不同，判定方式必须分开，用错会整轮误判。

- **移动端是另一条链路，不能直接套 PC 判据**：移动端 SEO 页上传后多落 `/create/edit?pid=`，主面板为 `.mobile-primary-panel`
  （Trending Tools / AI Image / Background / Adjust / Insert），断言与截图须按移动端口径单独写。
  来源：`2026-09-15_seo_main_upload_mobile_interactions`；验证：24 页移动端实测（`sync.md`）。

### `/agent?pid=` 新画布：不要用 `canvas` 元素判定

- **默认编辑态下 `<canvas>` 的 `getBoundingClientRect()` 是 0×0**（它带 `absolute inset-0 h-full w-full`，但既无 intrinsic 尺寸也不被 CSS 撑开），
  用「canvas 有尺寸」当"画布已渲染"必然判死。
- **实际可见的画面是 CSS 缩放的 `<img>`**（`class="pointer-events-none select-none block max-w-none w-full h-full"`，实测约 409×546）；
  外层 absolute 容器才是真实尺寸。
- 正确判据：**有尺寸的真实 canvas（>200×150）优先，否则回退到 >300×250 的编辑器图层 `<img>`**，二者任一成立即视为画布已渲染。
- 特例：进入裁剪 / 绘制等特殊态后可能出现真实尺寸的 canvas（实测 `/tools/youtube-banner-maker` 裁剪态有 410×546 的 canvas），
  所以是"默认编辑态不要只认 canvas"，不是"`/agent` 永远没有真 canvas"。
- 来源：`2026-09-14_seo_main_upload_interactions`；验证：2026-09-15 实测 `/tools/landscape-to-portrait-converter` 等 `/agent` 页
  `canvas=0×0` + `img=410×546`（`evidence/diag_canvas_dom.log`）；修正判据后 24/24 通过。教训成本：首轮 16 条用例被 0×0 误判、
  每条白等 120s 超时。

### `/create/edit?pid=` 旧画布：等尺寸稳定，不要只看 URL

- **URL 变成 `/create/edit?pid=` 不代表编辑器就绪**：跳转后仍在异步加载，画布尺寸会继续变化。
  实测 `/tools/phone-wallpaper-maker`：跳转后约 3s 主画布仅 **300×150**（此时整页是灰底 + spinner，截图无信息量），
  约 6s 才稳定为 **696×928**。
- 正确判据：等**画布尺寸连续两次不变**且**图片图层已渲染**（存在 >200×200 的图层 `<img>`）再操作 / 断言 / 截图；
  不要用固定 `wait_for_timeout` 或"URL 已到位"来代替。
- 来源：`2026-09-14_seo_main_upload_interactions`；验证：2026-09-15 实测两档尺寸 + 用户反馈"还没等到状态稳定就截图"
  （`evidence/probe_blue_wallpaper.log`、`shots/probe_L2-014_early.png` vs `probe_L2-014_settled.png`）；修正后 24/24 通过。

- **截图前等"布局指纹"稳定，不只是画布尺寸**：等 `canvas` 数 + 工作区画布 / 选中框 / 底部面板几何**连续两次采样一致**再截图；
  旧画布可能同时挂载主编辑器画布与工具工作区画布（实测相差约 0.7s / 1.4s），过渡帧会让同一张图在视口里出现两次。
  来源：`2026-09-15_seo_main_upload_mobile_interactions`；验证：100ms 级时序证据 + 修正后 24/24（`evidence/l2_008_trace.json`）。

- **「打开了什么功能面板」≠ 底部 tab**：多数 SEO 页上传后会额外自动展开 `.mobile-feature-workspace` 工具工作区（标题=工具名），
  只断言底部 tab 会漏掉真实功能面板；功能面板断言取值以 `page_map` 的 `panels.function_panel` 为准。
  来源：`2026-09-15_seo_main_upload_mobile_interactions`；验证：24 页逐页实测（`evidence/function_panel_scan.json`）。

## 脚本复用与仓库资源路径（有稳定资产背书）

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

- **归档/复制脚本要逐个路径常量核对，且 live 与 archive 副本必须同改**：实测漏点——`TEST_IMAGE` 已改用 `_repo_root()`、
  `DATA_FILE` 仍写死 `parent.parent`；另一份整块 `TEST_IMAGES` 漏改 → 归档回归必然假失败。单副本全绿不代表另一份能跑。
  来源：`2026-09-15_seo_main_upload_mobile_interactions`（归档后修复）；验证：修正 4 个文件后逐路径实测 `.is_file()` 全 True。

- **同名测试文件不能在同一次 pytest 调用里收集**：`tests/` 与 `archive/` 下 15 个同名文件会全部报 `import file mismatch`
  （exit 2，归档用例一条都跑不到），加 `--import-mode=importlib` 也不行（会切断 basename 互导）。
  口径：归档回归单跑 `pytest archive`，live 回归单跑 `pytest`（`testpaths=tests` 已天然隔离）；两者都要就跑两条命令。
  来源：`2026-09-15_seo_main_upload_mobile_interactions`；验证：混跑实测 468 collected + 15 errors / exit 2。

- **归档资产校验口径**：`pytest archive --collect-only` 与整仓 `pytest --collect-only` 都必须 **0 error 且 exit 0**；
  收集数量变化按"覆盖缺口"处理（实测 `335 → 468`，是 import 期异常导致收集中途停止、静默少收用例，不是噪声）。
  来源：同上；验证：修复后 archive 228/0、整仓 468/0（均 exit 0）。

## 环境异常与代码回归的区分（有稳定资产背书）

- **同形态成组失败 + 本轮耗时明显异常 → 先怀疑环境，不要先改代码**。
  实测形态：多条用例同时卡在「处理态 99% `Thinking...`」或「上传后未获得任务跳转、URL 停留在落地页」，
  且整轮耗时从正常约 7 分钟涨到 **15:09**。
- 复核手段：**单页低成本探针**——对失败页面重新上传 1 次，观察是否恢复（实测复跑 7.8~7.9s 即完成跳转 → 判定为后端 AI 任务排队/限流）。
  不要因为一次成组失败就改断言 / 改等待逻辑。
- 记账口径：这类因环境排队 / 限流导致的失败属"环境类"，反复出现时按 `skipped`（环境）记录并写明证据，
  不要写成业务 `failed`，也不要通过放宽断言来"修绿"。
- 来源：`2026-09-14_seo_main_upload_interactions`；验证：2026-09-15 异常轮 `evidence/selfrun_v3_docstrings.log`（3 failed / 15:09）
  → 健康探针 `evidence/probe_env_health.log`（7.8~7.9s 恢复）→ 复跑 `evidence/selfrun_v3_final.log`（24/24 通过）。

- **网关 502/504、入口未挂载的业务处理经验已迁移**：唯一业务知识正文维护在
  `knowledge/modules/seo-landing.yaml#KB-PITFALL-0005`；本文件只保留测试执行层的重试红线与引用入口。

## 测试设计

- 所有字段都填（含非必填），所有有意义的字段都断言。
- `expected` 用有语义的值，不要用 `"0"` / `"-"` / 空字符串。
- 文本型断言用「包含子串」而非精确相等，避免格式漂移。
- **Playwright 文本断言两个坑**（有稳定资产背书）：
  - **大小写**：`expect(locator).to_contain_text(...)` 默认**区分大小写**，UI 实际渲染可能是小写（实测 `background` / `colors`），
    断言写大写会失败。统一用 `to_contain_text(keyword, ignore_case=True, timeout=...)`。
  - **不要传编译后的正则**：`to_contain_text(re.compile(...))` 会把正则对象**当成字面量文本**去匹配
    （报错里出现 `'re.compile(...)'` 字面量即为该症状）。需要忽略大小写就用 `ignore_case=True`，不要改传 `re.compile`。
  - 来源：`2026-09-14_seo_main_upload_interactions`；验证：2026-09-15 修正后 24/24 通过；教训成本：两轮失败均由此产生。

- 注释用中文。

## Vue 交互与文件选择器（有稳定资产背书）

- **点击 Vue 组件**：优先 `page.mouse.click(x, y)` 坐标点击，再回退 `dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}))`。
- **文件上传**：优先真实按钮 + `page.expect_file_chooser()` 选图；`input[type=file].set_input_files()` 只作回退，且会丢失 Vue 工具上下文。

- **SEO 落地页上传入口业务经验已迁移**：唯一业务知识正文维护在
  `knowledge/modules/seo-landing.yaml#KB-ENTRY-0001`；具体 selector 和 fallback 只以当前版本 `page_map/` 为准。
- **context 配置**：必须设 `viewport` + `locale: "en-US"`，否则 Vue 文件选择器无法被拦截（`conftest.py` 已统一兜底）。
- 滑块 / 数值型 Vue 控件：改值后用 `dispatchEvent(new Event('input'/'change', {bubbles: true}))` 触发更新。
- **提交 / 确认控件未必是 `button`**：旧画布的绘制态 Apply / Cancel 实际是 `div`。定位交互元素时不要写死标签，
  用「可见文本 + 可见性过滤」拿到中心坐标后 `page.mouse.click(x, y)`；退出判据用「该控件消失」。来源：2026-09-10 旧画布任务，24/24 通过。
- **色板 / 调色板类控件通常无 aria 与文本**：按容器内元素的 computed `backgroundColor` 精确匹配目标色，
  再点其 `div.cursor-pointer` 祖先；直接点色块可能弹出调色板 overlay，需 Escape 关闭后再继续。来源：同上。


## 视觉审查模型

- 视觉审查的模型 / API 解析以 `skills/ui-test-visual-review/SKILL.md` 与 `helpers/review_api_config.py` 为准，不在此固化。

## Windows 执行环境（有稳定资产背书）

- **不要在 import 期替换 `sys.stdout` / `sys.stderr`**：`sys.stdout = io.TextIOWrapper(sys.stdout.buffer, ...)` 会接管 pytest 的
  capture 流，收集结束时报 `ValueError: I/O operation on closed file.`，且收集中断会**静默少收用例**（实测 335 → 468）；
  需要改编码时用 `stream.reconfigure(encoding="utf-8", errors="replace")`，pytest capture 流（模块名以 `_pytest` 开头）直接跳过。
- **三引号 JS 片段里的 `\n` 会被真实转义**，注入正则时会破坏匹配（用原始字符串或 `\\n`）；GBK 控制台 print 中文会崩，先 reconfigure 再输出。
  来源：`2026-09-15_seo_main_upload_mobile_interactions`（归档后修复）；验证：修复后整仓 collect-only 468/0 exit 0、CLI 与无 buffer stdout 导入均正常。

## 待验证（无当前稳定资产背书）

以下经验来自更早的探索或未登记脚本，当前 `regression_registry.md` 的稳定资产均未使用；遇到相关场景前先实测，不要默认套用：

- `force=True` 触发 Vue 文件选择器（当前登记资产用坐标点击 / `dispatchEvent`）。
- `networkidle` 作为等待主路径（当前登记资产用 `domcontentloaded` + `wait_for_timeout`）。
- `session_page` 会话级登录复用（当前登记资产用自定义 fixture / 自建登录，或匿名可用）。
- `pytest.xfail("独立脚本已验证通过")` 绕过 pytest 环境限制（当前登记资产未使用）。

## 业务知识库边界

`rule.md` 继续作为稳定测试执行规则和技术红线的权威来源，不被业务知识库替代。页面旧入口、业务校验、账号权限和历史业务坑点可以在 `knowledge/` 建立检索切片，但必须通过 `source_refs` 引用本文件、`PROJECT.md`、`page_map/` 或 confirmed artifact；迁移前不得删除本文件中的硬规则。
