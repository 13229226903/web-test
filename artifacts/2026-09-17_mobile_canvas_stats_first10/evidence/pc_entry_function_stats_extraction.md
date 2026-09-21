# PC 画布统计入口与功能映射提取

来源：`D:/Test/my_project/testcases/v3.2_testcases_source/04_版本统计优化.md`
提取时间：2026-09-18
用途：修正“从首页 /create 直接开始”的错误入口假设；后续 PC 相关统计必须从对应功能介绍页进入。

## 1. 提供的介绍页 URL -> 画布功能

| 介绍页 URL | 介绍页功能 | 进入画布后对应功能/统计语义 |
|---|---|---|
| `http://10.17.1.66:3001/tools/photo-enhancer` | 画质增强功能介绍页 | 画质增强 / Enhance |
| `http://10.17.1.66:3001/tools/background-remover` | 去除背景 | 背景移除 / Remove BG / 抠图 |
| `http://10.17.1.66:3001/ai-replace/ai-clothes-changer` | 换装 | AI换装 / Clothes Changer |
| `http://10.17.1.66:3001/tools/magic-eraser-with-ai-detection` | AI消除 | AI消除 / Erase |
| `http://10.17.1.66:3001/ai-background` | AI背景 | AI背景 / AI Background |
| `http://10.17.1.66:3001/ai-replace` | 改图 | AI改图 / AI Replace |
| `http://10.17.1.66:3001/tools/ai-image-extender` | 扩图 | AI扩图 / Expand |

统一入口操作：

1. 打开上述介绍页。
2. 点击首屏上传/开始按钮。
3. 在文件选择弹窗选择 `test_images/` 下的图片。
4. 进入 PC 无限画布页。
5. 提交对应功能；如有购买弹窗，使用 Debug“跳过真实购买（查看统计项用）”，不要真实付款。
6. Console 搜索“统计”，核对 `sendGaEvent <事件名>` 与 `debug 统计：<事件名>` 是否成对出现。

## 2. 非移动端统计中涉及这些功能的条目

### 2.1 无限画布页通用功能统计（无 `xx_yy` 入口维度）

| 原文序号 | 原文标题 | 涉及功能 | 预期事件格式 |
|---:|---|---|---|
| 12 | 无限画布页xx功能点数用完触发注册 | 画质增强、背景移除、AI消除、AI扩图、AI改图、AI背景、AI换装等 | `无限画布页xx功能点数用完触发注册` |
| 13 | 无限画布页xx功能点数用完触发注册成功 | 同上 | `无限画布页xx功能点数用完触发注册成功` |
| 14 | 无限画布页xx功能点数用完触发购买yy成功 | 同上；`yy` 为月/年套餐或 credits 包 | `无限画布页xx功能点数用完触发购买yy成功` |
| 15 | 无限画布页xx功能图片下载保存 | 同上 | `无限画布页xx功能图片下载保存` |

### 2.2 新画布购买统计（必须从 xx_yy 介绍页进入）

以下统计明确写明“从 xx_yy 页面进入 PC 端无限画布页”，因此本次不能再从 `/create` 直进后判定。  
本次实际语言可代入 `xx=en`；`yy` 应代入对应介绍页路径。

| 原文序号 | 原文标题 | 对应介绍页 | 本次可代入事件示例 |
|---:|---|---|---|
| 16 | 新画布增强购买出现xx_yy | `/tools/photo-enhancer` | `新画布增强购买出现en_/tools/photo-enhancer` |
| 17 | 新画布增强zz购买成功xx_yy | `/tools/photo-enhancer` | `新画布增强年ultra购买成功en_/tools/photo-enhancer` |
| 18 | 新画布抠图购买出现xx_yy | `/tools/background-remover` | `新画布抠图购买出现en_/tools/background-remover` |
| 19 | 新画布抠图zz购买成功xx_yy | `/tools/background-remover` | `新画布抠图年ultra购买成功en_/tools/background-remover` |
| 20 | 新画布消除购买出现xx_yy | `/tools/magic-eraser-with-ai-detection` | `新画布消除购买出现en_/tools/magic-eraser-with-ai-detection` |
| 21 | 新画布消除zz购买成功xx_yy | `/tools/magic-eraser-with-ai-detection` | `新画布消除年ultra购买成功en_/tools/magic-eraser-with-ai-detection` |
| 22 | 新画布改图购买出现xx_yy | `/ai-replace` | `新画布改图购买出现en_/ai-replace` |
| 23 | 新画布改图zz购买成功xx_yy | `/ai-replace` | `新画布改图年ultra购买成功en_/ai-replace` |
| 24 | 新画布扩图购买出现xx_yy | `/tools/ai-image-extender` | `新画布扩图购买出现en_/tools/ai-image-extender` |
| 25 | 新画布扩图zz购买成功xx_yy | `/tools/ai-image-extender` | `新画布扩图年ultra购买成功en_/tools/ai-image-extender` |
| 38 | 新画布AI背景购买出现xx_yy | `/ai-background` | `新画布AI背景购买出现en_/ai-background` |
| 39 | 新画布AI背景zz购买成功xx_yy | `/ai-background` | `新画布AI背景年ultra购买成功en_/ai-background` |

### 2.3 换装的特殊情况

`/ai-replace/ai-clothes-changer` 对应“AI换装”。需求中没有单独的“新画布换装购买出现xx_yy”标题，AI换装只出现在无限画布页通用功能清单中：

- 无限画布页xx功能点数用完触发注册
- 无限画布页xx功能点数用完触发注册成功
- 无限画布页xx功能点数用完触发购买yy成功
- 无限画布页xx功能图片下载保存

因此换装页不应套用“新画布换装”事件；应重点核对无限画布页通用功能事件是否带出 `AI换装`。

### 2.4 需要确认的换背入口

需求中另有：

- 新画布换背购买出现xx_yy
- 新画布换背zz购买成功xx_yy

但本次提供的 URL 列表只标明 `/ai-background` 为“AI背景”，没有单独给出“换背”介绍页。若 `/ai-background` 的首屏流程实际进入“换背”而非“AI背景”，需要重新映射；否则不能仅凭 URL 名称确认“换背”的入口。

## 3. 对已采集第 16-20 条的影响

此前从 `/create` -> `Start from a Photo` 进入画布后采集的：

- 新画布增强购买出现
- 新画布增强购买成功
- 新画布抠图购买出现
- 新画布抠图购买成功
- 新画布消除购买出现

入口不符合需求中的“从 xx_yy 页面进入”。因此这些结果不能直接用来判定上述 `新画布...xx_yy` 统计为 gap；应先用介绍的对应页面重跑，再根据 `xx=en`、`yy=介绍页路径` 的实际 `sendGaEvent/debug 统计` 事件判定。
