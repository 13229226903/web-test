# 231698 移动端回归验证（2026-09-30）

## 环境 / 视口
- URL：http://10.17.1.66:3001/it/ai-replace
- 设备：iPhone 13 仿真
- viewport：390 x 844
- DPR：3
- UA：Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1
- hasTouch：true
- 账号：随机新邮箱注册的免费账号，credits=0
- 支付：Debug「跳过真实购买（查看统计项用）」= true，未真实扣款/下单

## 流程
1. 移动端访问 `/it/ai-replace`，上传 `test_images/1K.jpg`。
2. 进入移动画布页 `/it/create/edit?pid=...`，AI 改图面板自动打开。
3. 在图片上涂抹 mask，填写描述，点击 `Genera 5`。
4. 未登录状态触发注册弹窗；使用随机邮箱 + 验证码 `123456` 注册免费账号（未点击 Send）。
5. 注册后再次点击 `Genera 5`，触发购买弹窗；关闭促销弹窗，进入购买弹窗。
6. 点击 `Iniziare` 进入支付方式页；Debug 已提前开启跳过真实购买。
7. 点击 PayPal/Stripe 区域后，完成模拟购买成功回调。

## Console 关键事件
```text
sendGaEvent 新画布改图购买出现it_ai-replace
sendGaEvent 购买界面进入
sendGaEvent 移动端画布点数用完触发购买
sendGaEvent 移动端画布AI改图功能点数用完触发购买
sendGaEvent 促销入口3_出现
sendGaEvent 总_支付弹窗出现
sendGaEvent 总_年ultra订阅购买成功
sendGaEvent 移动端画布AI改图功能点数用完触发购买年ultra成功
sendGaEvent 移动端画布点数用完触发购买年ultra成功
sendGaEvent 新画布改图年ultra购买成功it_ai-replace
sendGaEvent 促销入口3_购买成功
```

## 结论
- PASS：移动端 AI 改图购买曝光事件已上报 `新画布改图购买出现it_ai-replace`。
- PASS：移动端 AI 改图购买成功事件已上报 `新画布改图年ultra购买成功it_ai-replace`。
- 本轮捕获日志中未出现旧事件名 `画布页改图购买出现it_ai-replace` / `画布页改图年ultra购买成功it_ai-replace`。

## 证据
- `shots/mobile_231698_after_mask.png`
- `shots/mobile_231698_after_generate_anonymous.png`
- `shots/mobile_231698_after_register_submit.png`
- `shots/mobile_231698_payment_methods.png`
- `shots/mobile_231698_purchase_success.png`
