"""无限画布页 - 背景移除功能测试。

测试流程:
1. 登录 → /create 页
2. 关闭定价弹窗 → 点击 "Start from a Photo"
3. 通过文件选择器上传测试图片 → 进入 /agent?pid=... 无限画布页
4. 触发背景移除 → 等待 AI 处理完成
5. 验证结果图生成 → 下载结果图到本地

页面区分:
- 原画布页: /tools/background-remover 上传后进入的编辑器
- 无限画布页: /create 点击 "Start from a Photo" 进入的 /agent 页面
"""

import os
import base64
import glob
from playwright.sync_api import Page, expect


# ── 测试图片选取 ──────────────────────────────────────────────

def pick_test_image():
    """从 test_images/ 目录选取一张测试图片，返回绝对路径。
    优先使用小文件（<1MB）以加快上传速度。
    """
    img_dir = os.path.join(os.path.dirname(__file__), "..", "test_images")
    all_imgs = glob.glob(os.path.join(img_dir, "*"))
    if not all_imgs:
        raise FileNotFoundError(f"test_images/ 目录中没有图片: {img_dir}")

    # 按文件大小排序，优先用小图
    all_imgs.sort(key=lambda f: os.path.getsize(f))
    # 取第 3 张（中等偏小，避免极小的异常文件）
    idx = min(2, len(all_imgs) - 1)
    return os.path.abspath(all_imgs[idx])


# ── 辅助: 关闭创建页定价弹窗 ──────────────────────────────────

def dismiss_pricing_overlay(page: Page):
    """移除 /create 页面的定价弹窗遮罩（JS 强制删除）。"""
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(o => {
            const bg = window.getComputedStyle(o).backgroundColor;
            if (bg && bg.includes('rgba') && (bg.includes('0.3') || bg.includes('0.5'))) {
                o.remove();
            }
        });
    }""")
    page.wait_for_timeout(1000)


# ── Fixture: 进入无限画布页 ────────────────────────────────────

def enter_infinite_canvas(page: Page, test_img: str):
    """从 /create 页进入无限画布页: 点击 Start from a Photo + 上传图片。
    返回进入后的 page（URL 已变为 /agent?pid=...）。
    """
    # 关闭定价弹窗
    dismiss_pricing_overlay(page)

    # 点击 "Start from a Photo" → 触发文件选择器
    with page.expect_file_chooser() as fc_info:
        page.evaluate("""() => {
            const cards = document.querySelectorAll('[class*="cursor-pointer"]');
            cards.forEach(card => {
                if (card.textContent.includes('Start from a Photo')) {
                    card.click();
                }
            });
        }""")

    fc_info.value.set_files(test_img)
    page.wait_for_timeout(10000)  # 等待跳转到 /agent?pid=...

    # 确认已进入无限画布页
    assert "/agent" in page.url, f"未进入无限画布页，当前 URL: {page.url}"
    return page


# ── 测试用例 ──────────────────────────────────────────────────

def test_enter_infinite_canvas(logged_in_page: Page, base_url: str):
    """从 /create 点击 Start from a Photo 上传图片后应进入无限画布页。"""
    page = logged_in_page
    test_img = pick_test_image()
    print(f"\n  测试图片: {os.path.basename(test_img)} ({os.path.getsize(test_img) / 1024:.0f} KB)")

    # 确保在 /create 页（登录后自动跳转）
    page.goto(f"{base_url}/create")
    page.wait_for_timeout(4000)

    enter_infinite_canvas(page, test_img)

    # 断言: URL 包含 /agent
    assert "/agent" in page.url, f"URL 应为 /agent?pid=...，实际: {page.url}"

    # 断言: 页面标题包含 Infinite Canvas
    title = page.title()
    assert "Infinite Canvas" in title, f"标题应包含 Infinite Canvas，实际: {title}"

    # 断言: 编辑工具栏可见
    expect(page.locator("button:has-text('Remove BG'):visible").first).to_be_visible(timeout=10000)
    expect(page.locator("button:has-text('Chat To Edit')").first).to_be_visible()
    expect(page.locator("button:has-text('Crop')").first).to_be_visible()


def test_bg_remove_process_and_result(logged_in_page: Page, base_url: str):
    """在无限画布中触发背景移除，应生成结果图（blob URL）。"""
    page = logged_in_page
    test_img = pick_test_image()
    print(f"\n  测试图片: {os.path.basename(test_img)} ({os.path.getsize(test_img) / 1024:.0f} KB)")

    page.goto(f"{base_url}/create")
    page.wait_for_timeout(4000)
    enter_infinite_canvas(page, test_img)

    # 点击 Remove BG 触发处理
    page.locator("button:has-text('Remove BG'):visible").first.click()
    page.wait_for_timeout(3000)

    # 等待处理完成: "Thinking" 文字消失
    page.wait_for_function(
        "() => !document.body.innerText.includes('Thinking')",
        timeout=60000
    )

    # 断言: 结果图出现（alt 包含 "Remove BG"）
    result_img = page.locator("img[alt*='Remove BG']").first
    expect(result_img).to_be_visible(timeout=30000)

    # 断言: 结果图 src 为 blob URL
    src = result_img.get_attribute("src")
    assert src and src.startswith("blob:"), f"结果图 src 应为 blob URL，实际: {src}"


def test_bg_remove_download_result(logged_in_page: Page, base_url: str):
    """无限画布背景移除完成后，应能下载结果图到本地。"""
    page = logged_in_page
    test_img = pick_test_image()
    img_name = os.path.splitext(os.path.basename(test_img))[0]
    print(f"\n  测试图片: {os.path.basename(test_img)} ({os.path.getsize(test_img) / 1024:.0f} KB)")

    page.goto(f"{base_url}/create")
    page.wait_for_timeout(4000)
    enter_infinite_canvas(page, test_img)

    # 触发背景移除
    page.locator("button:has-text('Remove BG'):visible").first.click()
    page.wait_for_timeout(3000)

    # 等待处理完成
    page.wait_for_function(
        "() => !document.body.innerText.includes('Thinking')",
        timeout=60000
    )

    # 确认结果图存在
    result_img = page.locator("img[alt*='Remove BG']").first
    expect(result_img).to_be_visible(timeout=30000)

    # 通过 blob URL 下载结果图
    src = result_img.get_attribute("src")
    blob_data = page.evaluate("""async (src) => {
        const response = await fetch(src);
        const blob = await response.blob();
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve(reader.result);
            reader.readAsDataURL(blob);
        });
    }""", src)

    # 保存结果，文件名关联原始图片名
    os.makedirs("data/downloads", exist_ok=True)
    download_path = f"data/downloads/{img_name}_bg_removed.png"
    assert blob_data and blob_data.startswith("data:image"), \
        f"下载数据格式异常: {str(blob_data)[:80]}"
    base64_part = blob_data.split(",")[1]
    with open(download_path, "wb") as f:
        f.write(base64.b64decode(base64_part))

    # 断言: 文件已保存且不为空
    assert os.path.exists(download_path), f"下载文件未生成: {download_path}"
    file_size = os.path.getsize(download_path)
    assert file_size > 0, f"下载文件为空: {download_path}"
    print(f"  结果已保存: {download_path} ({file_size / 1024:.0f} KB)")


def test_bg_remove_credits_consumed(logged_in_page: Page, base_url: str):
    """无限画布背景移除处理后，credits 应被扣除。"""
    page = logged_in_page
    test_img = pick_test_image()
    print(f"\n  测试图片: {os.path.basename(test_img)} ({os.path.getsize(test_img) / 1024:.0f} KB)")

    page.goto(f"{base_url}/create")
    page.wait_for_timeout(4000)

    # 记录处理前的 credits
    credits_before = page.evaluate("""() => {
        const match = document.body.innerText.match(/Credits:(\\d+)/);
        return match ? parseInt(match[1]) : null;
    }""")
    assert credits_before is not None, "无法读取初始 credits"

    enter_infinite_canvas(page, test_img)

    # 读取进入画布后的 credits（可能在进入时已消耗）
    credits_after_enter = page.evaluate("""() => {
        const match = document.body.innerText.match(/Credits:(\\d+)/);
        return match ? parseInt(match[1]) : null;
    }""")

    # 触发背景移除
    page.locator("button:has-text('Remove BG'):visible").first.click()
    page.wait_for_timeout(3000)

    # 等待处理完成
    page.wait_for_function(
        "() => !document.body.innerText.includes('Thinking')",
        timeout=60000
    )

    # 读取处理后的 credits
    credits_after = page.evaluate("""() => {
        const match = document.body.innerText.match(/Credits:(\\d+)/);
        return match ? parseInt(match[1]) : null;
    }""")

    assert credits_after is not None, "无法读取处理后 credits"
    assert credits_after <= (credits_after_enter or credits_before), \
        f"Credits 应被消耗: enter={credits_after_enter}, after={credits_after}"
    print(f"  Credits: {credits_before} → {credits_after_enter} → {credits_after}")
