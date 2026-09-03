"""SEO 检测类页面测试 — 公共工具函数。"""

import os
import glob
import json
import tempfile
import struct
import zlib
from playwright.sync_api import Page

# ═══════════════════════════════════════════════════════════════
# 测试图片选取
# ═══════════════════════════════════════════════════════════════

def _create_test_png(width=200, height=200, r=66, g=133, b=244):
    """生成一张纯色测试 PNG，返回 bytes（回退用）。"""
    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        return struct.pack(">I", len(data)) + c + crc
    header = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    raw = b""
    for y in range(height):
        raw += b"\x00"
        for x in range(width):
            raw += bytes([r, g, b])
    idat = chunk(b"IDAT", zlib.compress(raw))
    iend = chunk(b"IEND", b"")
    return header + ihdr + idat + iend


def pick_test_image():
    """从 test_images/ 选取最小的图片（加速检测处理）。"""
    img_dir = os.path.join(os.path.dirname(__file__), "..", "test_images")
    if os.path.isdir(img_dir):
        all_imgs = sorted(glob.glob(os.path.join(img_dir, "*")), key=lambda f: os.path.getsize(f))
        if all_imgs:
            return os.path.abspath(all_imgs[0])  # 取最小文件
    tmp = os.path.join(tempfile.gettempdir(), "pokecut_test_upload.png")
    with open(tmp, "wb") as f:
        f.write(_create_test_png())
    return tmp


# ═══════════════════════════════════════════════════════════════
# 导航 & 上传
# ═══════════════════════════════════════════════════════════════

def navigate_to_tool(page: Page, base_url: str, page_path: str):
    """导航到指定 SEO 工具页面并等待渲染完成。"""
    page.goto(f"{base_url}{page_path}", timeout=60000)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(3000)


def upload_image(page: Page, test_img: str):
    """上传测试图片。优先 label.click（完整触发 Vue change 事件），失败则 dispatchEvent。"""
    try:
        label = page.locator("label").first
        with page.expect_file_chooser(timeout=10000) as fc_info:
            label.click()
        fc_info.value.set_files(test_img)
    except Exception:
        with page.expect_file_chooser() as fc_info:
            page.evaluate("""() => {
                const btns = document.querySelectorAll('button');
                for (const b of btns) {
                    const r = b.getBoundingClientRect();
                    if (b.textContent.trim() && r.y > 400 && r.y < 3000 && r.width > 200) {
                        b.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                        return;
                    }
                }
            }""")
        fc_info.value.set_files(test_img)
    page.wait_for_timeout(2000)


# ═══════════════════════════════════════════════════════════════
# 等待辅助
# ═══════════════════════════════════════════════════════════════

def wait_for_body_text(page: Page, text: str, timeout: int = 120000):
    """等待页面 body 中出现指定文本。"""
    page.wait_for_function(
        f"() => document.body.innerText.includes({json.dumps(text)})",
        timeout=timeout
    )


def wait_for_body_text_gone(page: Page, text: str, timeout: int = 120000):
    """等待页面 body 中指定文本消失。"""
    page.wait_for_function(
        f"() => !document.body.innerText.includes({json.dumps(text)})",
        timeout=timeout
    )


# ═══════════════════════════════════════════════════════════════
# 区域与按钮状态检查
# ═══════════════════════════════════════════════════════════════

def section_heading_visible(page: Page, heading_text: str) -> bool:
    """检查指定栏目标题是否在页面中可见。"""
    return page.evaluate(
        """(heading) => {
            const all = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, strong, b');
            for (const el of all) {
                const t = el.textContent.trim();
                if ((t === heading || t.startsWith(heading)) && el.offsetWidth > 0 && el.offsetHeight > 0) {
                    return true;
                }
            }
            return false;
        }""",
        heading_text
    )


def text_on_page(page: Page, text: str) -> bool:
    """检查页面 body 中是否包含指定文案。"""
    return text.lower() in page.locator("body").inner_text().lower()


def button_disabled_in_section(page: Page, section_heading: str, button_text: str, require: bool = True):
    """在指定栏目内查找按钮，返回 (disabled_bool, found_bool)。
    require=True 时按钮未找到会触发断言失败。
    """
    result = page.evaluate(
        """([heading, btnText]) => {
            const all = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, strong, b');
            for (const el of all) {
                const t = el.textContent.trim();
                if ((t === heading || t.startsWith(heading)) && el.offsetWidth > 0 && el.offsetHeight > 0) {
                    let container = el;
                    for (let i = 0; i < 8; i++) {
                        container = container.parentElement;
                        if (!container) break;
                        const buttons = container.querySelectorAll('button');
                        for (const btn of buttons) {
                            if (btn.textContent.trim().includes(btnText) && btn.offsetWidth > 0) {
                                return { disabled: btn.disabled, found: true };
                            }
                        }
                    }
                }
            }
            return { disabled: null, found: false };
        }""",
        [section_heading, button_text]
    )
    disabled = result.get("disabled")
    found = result.get("found", False)
    if require:
        assert found, f"应在 '{section_heading}' 区域内找到 '{button_text}' 按钮"
    return disabled, found


def button_disabled_global(page: Page, button_text: str):
    """全局搜索按钮的 disabled 状态。返回 (disabled_bool, found_bool)。"""
    result = page.evaluate(
        """(btnText) => {
            const buttons = document.querySelectorAll('button');
            for (const btn of buttons) {
                if (btn.textContent.trim().includes(btnText) && btn.offsetWidth > 0) {
                    return { disabled: btn.disabled, found: true };
                }
            }
            return { disabled: null, found: false };
        }""",
        button_text
    )
    return result.get("disabled"), result.get("found", False)


def click_button_in_section(page: Page, section_heading: str, button_text: str):
    """在指定栏目内查找按钮并 dispatchEvent 点击（兼容 Vue）。返回是否找到并点击。"""
    return page.evaluate(
        """([heading, btnText]) => {
            const all = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, div, strong, b');
            for (const el of all) {
                const t = el.textContent.trim();
                if ((t === heading || t.startsWith(heading)) && el.offsetWidth > 0 && el.offsetHeight > 0) {
                    let container = el;
                    for (let i = 0; i < 8; i++) {
                        container = container.parentElement;
                        if (!container) break;
                        const buttons = container.querySelectorAll('button');
                        for (const btn of buttons) {
                            if (btn.textContent.trim().includes(btnText) && btn.offsetWidth > 0 && !btn.disabled) {
                                btn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                                return true;
                            }
                        }
                    }
                }
            }
            return false;
        }""",
        [section_heading, button_text]
    )


# 区域标题常量
SECTION_ORIGINAL = "Original Image"
SECTION_ANALYSIS = "Analysis Result"
SECTION_OPTIMIZED = "Optimized Result"
