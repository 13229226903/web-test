# 剩余统计测试清单（URL入口 / 触发交互 待补充模板）

来源：`D:/Test/my_project/testcases/v3.2_testcases_source/04_版本统计优化.md`

生成时间：2026-09-18

说明：已确认通过的不再列入“未测”；第 12/13 条已标记 bug_candidate，单列在末尾；第 15 条已按“结果图下载”复核通过。

## 未测统计

| 序号 | 状态 | 原文标题 | 功能 | URL入口 | 触发交互 |
|---:|---|---|---|---|---|
| 11 | 未测 | 移动端画布页_xx弹窗下载 | 移动端画布功能弹窗下载 | 待补充；移动端画布功能结果弹窗入口 | 移动端画布功能结果弹窗 -> 点击下载 icon -> 确认下载 -> Console 搜“统计” |
| 26 | 已测通过（本批） | 新画布脸部购买出现xx_yy | 脸部 | /ai-replace/add-smile-to-photo | 待补充；进入脸部相关功能介绍页 -> 首屏上传 -> 画布 -> 使用脸部功能 -> 触发购买 |
| 27 | 已测通过（本批） | 新画布脸部zz购买成功xx_yy | 脸部 | /ai-replace/add-smile-to-photo | 待补充；沿用 26，Debug 跳过真实购买验证成功事件 |
| 28 | 已测通过（本批） | 新画布身材购买出现xx_yy | 身材 | /body-editor | 进入身材相关功能介绍页 -> 首屏上传 -> 画布 -> 使用身材功能 -> 触发购买 |
| 29 | 已测通过（本批） | 新画布身材zz购买成功xx_yy | 身材 | /body-editor | 沿用 28，Debug 跳过真实购买验证成功事件 |
| 30 | 已测通过（本批） | 新画布发型购买出现xx_yy | 发型 | /hair-editor/virtual-hair-color-try-on | 待补充；进入发型相关功能介绍页 -> 首屏上传 -> 画布 -> 使用发型功能 -> 触发购买 |
| 31 | 已测通过（本批） | 新画布发型zz购买成功xx_yy | 发型 | /hair-editor/virtual-hair-color-try-on | 待补充；沿用 30，Debug 跳过真实购买验证成功事件 |
| 32 | 未测 | 新画布AI滤镜购买出现xx_yy | AI滤镜 | 跳过 | 待补充；进入 AI滤镜 功能介绍页 -> 首屏上传 -> 画布 -> 使用 AI滤镜 -> 触发购买 |
| 33 | 未测 | 新画布AI滤镜zz购买成功xx_yy | AI滤镜 | 跳过 | 待补充；沿用 32，Debug 跳过真实购买验证成功事件 |
| 34 | 未测 | 新画布图生图购买出现xx_yy | 图生图 | 待补充；候选：/image-to-image-ai | 进入图生图功能介绍页 -> 首屏上传 -> 画布 -> 使用图生图 -> 触发购买 |
| 35 | 未测 | 新画布图生图zz购买成功xx_yy | 图生图 | 待补充；候选：/image-to-image-ai | 沿用 34，Debug 跳过真实购买验证成功事件 |
| 36 | 未测 | 新画布文生图购买出现xx_yy | 文生图 | 待补充；候选：/ai-image-generator | 进入文生图功能介绍页 -> 首屏上传/生成入口 -> 画布 -> 使用文生图 -> 触发购买 |
| 37 | 未测 | 新画布文生图zz购买成功xx_yy | 文生图 | 待补充；候选：/ai-image-generator | 沿用 36，Debug 跳过真实购买验证成功事件 |
| 38 | 已测通过（本批） | 新画布AI背景购买出现xx_yy | AI背景 | /ai-background | 进入 AI背景功能介绍页 -> 首屏上传 -> 画布 -> 使用 AI Background -> 触发购买 |
| 39 | 已测通过（本批） | 新画布AI背景zz购买成功xx_yy | AI背景 | /ai-background | 沿用 38，Debug 跳过真实购买验证成功事件 |
| 40 | 已测通过（本批） | 新画布背景模糊购买出现xx_yy | 背景模糊 | /tools/gaussian-blur | 进入背景模糊功能介绍页 -> 首屏上传 -> 画布 -> 使用 BG Blur -> 触发购买 |
| 41 | 已测通过（本批） | 新画布背景模糊zz购买成功xx_yy | 背景模糊 | /tools/gaussian-blur | 沿用 40，Debug 跳过真实购买验证成功事件 |
| 42 | 已测通过（复核） | 新画布照片修复购买出现xx_yy | 照片修复 | /tools/photo-restoration（已知相关 SEO 页） | 进入照片修复功能介绍页 -> 首屏上传 -> 画布 -> Old Photo Mode/Photo Restore -> 触发购买 |
| 43 | 已测通过（复核） | 新画布照片修复zz购买成功xx_yy | 照片修复 | /tools/photo-restoration（已知相关 SEO 页） | 沿用 42，Debug 跳过真实购买验证成功事件 |
| 44 | 未测 | 新画布贴纸购买出现xx_yy | 贴纸 | /tools/add-hearts-to-photo | 登录免费账号->进入贴纸功能介绍页 -> 首屏上传 -> 画布 -> Sticker -> 按住鼠标左键全选画布图层->点击下载会触发购买（需要添加带VIP icon的贴纸，进入画布页后左侧会弹出贴纸弹窗，选中第二个分类Valentine2，下面第二个有VIP贴纸） |
| 45 | 未测 | 新画布贴纸zz购买成功xx_yy | 贴纸 | /tools/add-hearts-to-photo（已知相关 SEO 页，确认是否贴纸入口） | 沿用 44，Debug 跳过真实购买验证成功事件 |
| 46 | 未测 | 新画布换背购买出现xx_yy | 换背 | /tools/background-changer | 进入换背功能介绍页 -> 首屏上传 -> 画布 -> Change BG -> 触发购买 |
| 47 | 未测 | 新画布换背zz购买成功xx_yy | 换背 | /tools/background-changer | 沿用 46，Debug 跳过真实购买验证成功事件 |

## 已测但未通过（bug_candidate，暂不算未测）

| 序号 | 状态 | 原文标题 | 功能 | URL入口 | 触发交互 |
|---:|---|---|---|---|---|
| 12 | bug_candidate | 无限画布页xx功能点数用完触发注册 | 画质增强ultra | /create -> Start from a Photo（原入口，需正确入口复核） | Enhance -> Ultra HD Mode -> Enhance -> 出现注册弹窗 |
| 13 | bug_candidate | 无限画布页xx功能点数用完触发注册成功 | 画质增强ultra | /create -> Start from a Photo（原入口，需正确入口复核） | 注册弹窗 -> 随机邮箱 + 123456 -> Sign up |
| 15 | 已测通过（结果图下载复核） | 无限画布页xx功能图片下载保存 | 画质增强ultra | /create -> Start from a Photo -> test_images/1K.jpg -> /agent?pid=* | Enhance -> Standard Mode -> 生成成功 -> 选中 Enhanced 结果图层 -> 点击结果图下载；实际 `无限画布页画质增强ultra功能图片下载保存` |

## 统计次数唯一性断言（所有统计适用）

单次目标动作内，目标统计必须满足：

- `sendGaEvent <事件名>` 出现 1 次
- `debug 统计：<事件名>` 出现 1 次
- 稳定窗口内不再次新增同一事件

0 次为漏报 bug；>=2 次为多报 bug；无法隔离单次动作的标记为 `frequency_pending_revalidation`，不能按通过处理。

## 通用触发交互模板（新画布购买类 16-47）

| 类型 | 触发交互 |
|---|---|
| 购买出现 | 正确功能介绍页 -> 点击首屏上传按钮 -> 文件选择 `test_images/1K.jpg` -> 进入 `/agent?pid=*` -> 使用对应功能并提交/生成 -> 触发购买弹窗 -> Console 搜索“统计”核对 `新画布xxx购买出现xx_yy` |
| 购买成功 | 购买出现链路 -> 购买面板 -> 先开启 DEBUG“跳过真实购买（查看统计项用）” -> checkout 点击 `Debug: 跳过真实购买` -> Console 搜“统计”核对 `新画布xxx年ultra购买成功xx_yy` |

## 仍需你补充的信息

- 未填写的 URL入口：脸部、身材、发型、AI滤镜、图生图、文生图、背景模糊、换背，以及贴纸入口是否使用 `/tools/add-hearts-to-photo`。

- 对应功能介绍页的首屏按钮文案/selector：英文或对应语言下的首屏上传按钮。

- 进入画布后要点击的功能入口：如 Face / Body / Hair / Filter / Image to Image / Text to Image / BG Blur / Sticker / Change BG。

- 是否需要沿用本次 `年ultra + Debug: 跳过真实购买` 作为所有购买成功的统一抽测套餐。



