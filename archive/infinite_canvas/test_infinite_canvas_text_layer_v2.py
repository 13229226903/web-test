# -*- coding: utf-8 -*-
"""画布页文字功能自动化回归测试 v2（基于 confirmed cases.md 与 page_map v2）。"""
import os
import glob
import json
import pytest
import allure
from pathlib import Path
from helpers_create_entry import dismiss_create_promo
from playwright.sync_api import Page, expect as pw_expect
from conftest import allure_screenshot

def _repo_root():
    """归档副本位于 archive/<dir>/，需按 test_images/ 上溯仓库根。"""
    cur = os.path.dirname(os.path.abspath(__file__))
    for _ in range(6):
        if os.path.isdir(os.path.join(cur, "test_images")):
            return cur
        cur = os.path.dirname(cur)
    return os.path.dirname(cur)


TEST_IMAGE = os.path.join(_repo_root(), "test_images", "低分辨率.JPG")

# ═══════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════

def dismiss_overlay(page: Page):
    page.evaluate("""() => {
        document.querySelectorAll('div[class*="fixed"]').forEach(el => {
            const r = el.getBoundingClientRect();
            if (r.width >= document.documentElement.clientWidth * 0.9 &&
                r.height >= document.documentElement.clientHeight * 0.9) {
                el.remove();
            }
        });
    }""")
    page.wait_for_timeout(1000)


def enter_canvas(page: Page, base_url: str) -> str:
    """进入无限画布：/create → Start from a Photo → 上传 test_images/低分辨率.JPG。"""
    with allure.step("进入 /create 并上传图片"):
        page.goto(base_url + "/create", timeout=120000, wait_until="domcontentloaded")
        dismiss_create_promo(page)  # 全新会话 VIP 促销/定价弹窗兜底
        page.wait_for_timeout(8000)
        dismiss_overlay(page)
        card = page.locator("div.cursor-pointer", has=page.locator("p", has_text="Start from a Photo")).first
        with page.expect_file_chooser(timeout=30000) as fc_info:
            card.click()
        fc_info.value.set_files(TEST_IMAGE)
        page.wait_for_timeout(12000)
    allure_screenshot(page, "进入画布")
    return page.url


def add_text(page: Page):
    with allure.step("点击左侧 Add Text 添加文字图层"):
        page.locator("button[data-tool-id='text']").first.click()
        page.wait_for_timeout(3000)
    allure_screenshot(page, "添加文字图层")


def click_button_by_text(page: Page, text: str, ymin: int = 430, ymax: int = 850, xmin: int = 1000) -> bool:
    """用坐标点击面板/工具栏内指定文本按钮。"""
    for loc in page.locator("button", has_text=text).all():
        try:
            box = loc.bounding_box()
            if box and box["y"] >= ymin and box["y"] <= ymax and box["x"] >= xmin:
                page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                return True
        except Exception:
            pass
    return False


def click_section_small(page: Page, section: str) -> bool:
    """点击 Reflection / Outline 等 div header 中的 12x12 下拉箭头。"""
    return page.evaluate("""(section) => {
        const spans = [...document.querySelectorAll('span')].filter(s => s.textContent.trim() === section);
        for (const sp of spans) {
            const r = sp.getBoundingClientRect();
            if (r.width > 0 && r.x >= 1000) {
                const row = sp.parentElement;
                const btns = [...row.querySelectorAll('button')];
                const small = btns.filter(b => {
                    const br = b.getBoundingClientRect();
                    return br.width > 0 && br.height > 0 && br.width <= 16 && br.height <= 16;
                });
                if (small[0]) {
                    small[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    return true;
                }
            }
        }
        return false;
    }""", section)


def click_section_toggle(page: Page, section: str) -> bool:
    """点击 Reflection / Outline 的 Toggle 开关。"""
    return page.evaluate("""(section) => {
        const spans = [...document.querySelectorAll('span')].filter(s => s.textContent.trim() === section);
        for (const sp of spans) {
            const r = sp.getBoundingClientRect();
            if (r.width > 0 && r.x >= 1000) {
                const row = sp.parentElement;
                const btns = [...row.querySelectorAll('button')];
                const toggle = btns.filter(b => {
                    const br = b.getBoundingClientRect();
                    return br.width > 0 && br.height > 0 && br.width >= 30 && br.width <= 50 && br.height <= 24;
                });
                if (toggle[0]) {
                    toggle[0].dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
                    return true;
                }
            }
        }
        return false;
    }""", section)


def set_section_sliders(page: Page, section: str, values: list):
    """用原生 setter 设置 section 内的 range 滑块值。"""
    return page.evaluate("""(opts) => {
        const spans = [...document.querySelectorAll('span')].filter(s => s.textContent.trim() === opts.section);
        for (const sp of spans) {
            const r = sp.getBoundingClientRect();
            if (r.width > 0 && r.x >= 1000) {
                const row = sp.parentElement;
                const content = row.nextElementSibling;
                if (content) {
                    const sliders = [...content.querySelectorAll('input[type=range]')];
                    const set = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set;
                    sliders.forEach((s, i) => {
                        if (i < opts.values.length) {
                            set.call(s, String(opts.values[i]));
                            s.dispatchEvent(new Event('input', {bubbles: true}));
                            s.dispatchEvent(new Event('change', {bubbles: true}));
                        }
                    });
                    return sliders.map(s => s.value);
                }
            }
        }
        return null;
    }""", {"section": section, "values": values})


def get_section_sliders(page: Page, section: str):
    return page.evaluate("""(section) => {
        const spans = [...document.querySelectorAll('span')].filter(s => s.textContent.trim() === section);
        for (const sp of spans) {
            const r = sp.getBoundingClientRect();
            if (r.width > 0 && r.x >= 1000) {
                const row = sp.parentElement;
                const content = row.nextElementSibling;
                if (content) {
                    return [...content.querySelectorAll('input[type=range]')].map(s => ({
                        value: s.value, min: s.min, max: s.max, disabled: s.disabled
                    }));
                }
            }
        }
        return None;
    }""", section)


def make_two_line_text(page: Page):
    """把文字图层改成两行内容并提交。"""
    with allure.step("双击文字层并输入两行文字"):
        page.mouse.dblclick(900, 500)
        page.wait_for_timeout(1200)
        ta = page.locator("textarea.fixed.h-px.w-px").first
        pw_expect(ta).to_be_visible(timeout=5000)
        ta.fill("line1\nline2")
        page.wait_for_timeout(1000)
        page.keyboard.press("Escape")
        page.wait_for_timeout(1000)
        # 点工具栏 Adjust 重新打开属性面板
        click_button_by_text(page, "Adjust", ymin=400, ymax=440, xmin=500)
        page.wait_for_timeout(1200)


def panel_dimension_text(page: Page):
    return page.evaluate("""() => {
        const els = [...document.querySelectorAll('div,span')];
        for (const el of els) {
            const t = (el.textContent || '').trim();
            const m = t.match(/^(\\d+)\\s*x\\s*(\\d+)$/);
            const r = el.getBoundingClientRect();
            if (m && r.width > 0 && r.height > 0 && r.x >= 1000 && r.x <= 1560 && r.y >= 430 && r.y <= 520) return t;
        }
        return null;
    }""")


# ═══════════════════════════════════════════════════════════════
# 用例实现# ═══════════════════════════════════════════════════════════════
# 用例实现（优化后：合并重复路径，6 条用例）
# ═══════════════════════════════════════════════════════════════



def pixel_diff_nonzero(path1, path2):
    from PIL import Image, ImageChops
    diff = ImageChops.difference(Image.open(path1).convert("RGB"), Image.open(path2).convert("RGB"))
    if diff.getbbox() is None:
        return 0
    return sum(1 for px in diff.getdata() if px != (0, 0, 0))


def most_distinct_pixel(path, ref_rgb, x0=700, x1=1000, y0=250, y1=800):
    """在画布区域找与参考色距离最大的像素点，确保取色颜色与色盘颜色区分明显。"""
    from PIL import Image
    img = Image.open(path).convert("RGB")
    best = None
    best_dist = -1
    for y in range(y0, y1, 2):
        for x in range(x0, x1, 2):
            r, g, b = img.getpixel((x, y))
            # 忽略接近白色/黑色的无效取色点
            if max(r, g, b) > 235 or max(r, g, b) < 20:
                continue
            dist = ((r - ref_rgb[0]) ** 2 + (g - ref_rgb[1]) ** 2 + (b - ref_rgb[2]) ** 2) ** 0.5
            if dist > best_dist:
                best_dist = dist
                best = (x, y, (r, g, b))
    return best, best_dist



def canvas_image_box(page: Page):
    """返回画布中上传图片的可见区域，用于限制取色点击在图片内部。"""
    return page.evaluate("""() => {
        const imgs = [...document.querySelectorAll('img')];
        let best = null;
        for (const img of imgs) {
            const r = img.getBoundingClientRect();
            if (r.width > 50 && r.height > 50) {
                if (!best || r.width * r.height > best.w * best.h) {
                    best = {x: r.x, y: r.y, w: r.width, h: r.height};
                }
            }
        }
        return best;
    }""")

def test_text_001_entry_and_left_tools(page: Page, base_url: str):
    allure.dynamic.title("[L6][P0] 入口上传 + 左侧工具栏 + Add Text")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    url = enter_canvas(page, base_url)
    assert "/agent?pid=" in url
    for tool in ["image", "text", "sticker", "brush", "line", "shape", "layer"]:
        assert page.locator(f"button[data-tool-id='{tool}']").count() == 1
    add_text(page)
    body = page.locator("body").inner_text()
    for text in ["Adjust", "Move Up", "Move Down", "To Top", "To Bottom", "Flip h", "Flip v", "Delete", "Rotation"]:
        assert text in body


def test_text_002_select_reopen_tabs_basic(page: Page, base_url: str):
    allure.dynamic.title("[L2][P0] 选中/收起/重开 + Tab/Alignment/Font/Fill")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    enter_canvas(page, base_url)
    add_text(page)
    # 空白收起
    page.mouse.click(900, 300)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() == 0
    # 空白后重新添加文字以恢复选中态，再用 Move Up 制造“面板关闭但工具栏保留”，验证 Adjust 重开
    add_text(page)
    click_button_by_text(page, "Move Up", ymin=400, ymax=440, xmin=500)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() == 0
    click_button_by_text(page, "Adjust", ymin=400, ymax=440, xmin=500)
    page.wait_for_timeout(1200)
    assert page.locator("button", has_text="Basic").count() >= 1
    # Tab 切换
    click_button_by_text(page, "Basic", ymin=430, ymax=500)
    page.wait_for_timeout(800)
    # Alignment 点击
    page.evaluate("""() => {
        const ps=[...document.querySelectorAll('p')].filter(p=>p.textContent.trim()==='Alignment');
        for(const p of ps){const r=p.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const box=p.parentElement; if(box){const bs=[...box.querySelectorAll('button')]; bs[0].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}
        return false;
    }""")
    page.wait_for_timeout(800)
    # Font/Fill 存在
    assert page.locator("button", has_text="Font").count() >= 1
    assert page.locator("button", has_text="Fill").count() >= 1


def test_text_003_space(page: Page, base_url: str):
    allure.dynamic.title("[L5][P0] Space 单行禁用 + 两行 Height 生效")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    enter_canvas(page, base_url)
    add_text(page)
    click_button_by_text(page, "Space", ymin=480, ymax=820)
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Space单行Height禁用")
    sliders = get_section_sliders(page, "Space")
    assert sliders[0]["disabled"] is False
    assert sliders[1]["disabled"] is True
    make_two_line_text(page)
    allure_screenshot(page, "两行文字图层")
    click_button_by_text(page, "Space", ymin=480, ymax=820)
    page.wait_for_timeout(1000)
    sliders = get_section_sliders(page, "Space")
    assert sliders[1]["disabled"] is False
    before = panel_dimension_text(page)
    set_section_sliders(page, "Space", [0, 50])
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Space两行Height调整后")
    after = panel_dimension_text(page)
    assert before != after
    assert get_section_sliders(page, "Space")[1]["value"] == "50"


def test_text_004_reflection(page: Page, base_url: str, tmp_path):
    allure.dynamic.title("[L5][P0] Reflection 四参数可调 + 实际反射效果")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    from PIL import Image, ImageChops
    enter_canvas(page, base_url)
    add_text(page)
    click_section_small(page, "Reflection")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Reflection展开四滑块")
    sliders = get_section_sliders(page, "Reflection")
    assert sliders is not None and len(sliders) == 4
    before = tmp_path / "reflection_before.png"
    page.screenshot(path=str(before))
    # 先开启开关
    assert click_section_toggle(page, "Reflection")
    page.wait_for_timeout(1000)
    cls = page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const toggles=[...row.querySelectorAll('button')].filter(b=>b.getBoundingClientRect().width>=30&&b.getBoundingClientRect().width<=50); if(toggles[0]) return toggles[0].className;}}
        return '';
    }""")
    assert "bg-[#232323]" in cls
    # 四参数调整（开关开启后）
    vals = set_section_sliders(page, "Reflection", [20, 20, 20, 45])
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Reflection四参数调整后")
    assert vals == ["20", "20", "20", "45"]
    after = tmp_path / "reflection_after.png"
    page.screenshot(path=str(after))
    allure_screenshot(page, "Reflection开启效果")
    diff = ImageChops.difference(Image.open(before).convert("RGB"), Image.open(after).convert("RGB"))
    assert diff.getbbox() is not None
    nonzero = sum(1 for p in diff.getdata() if p != (0, 0, 0))
    assert nonzero > 10000


def test_text_005_background(page: Page, base_url: str, tmp_path):
    allure.dynamic.title("[L2][P0] Background 无填充/色盘/取色")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    from PIL import Image, ImageChops
    enter_canvas(page, base_url)
    add_text(page)
    click_button_by_text(page, "Background", ymin=480, ymax=820)
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Background展开三按钮")
    content = page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){return content.innerHTML;}}}
        return '';
    }""")
    assert "edit_icon_color_picker" in content
    # 色盘弹窗：应用蓝色 #0000ff，作为后续取色的区分基准
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Background色盘弹窗")
    assert page.locator("input.hexInput").is_visible()
    page.locator("input.hexInput").fill("#0000ff")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    assert page.locator("input.hexInput").input_value() == "#0000ff"
    # 再次点击色盘按钮关闭调色弹窗（Escape 在 Enter 后无法关闭）
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)
    palette_png = page.screenshot()
    palette_path = tmp_path / "bg_palette_blue.png"
    palette_path.write_bytes(palette_png)
    allure.attach(palette_png, name="Background色盘应用蓝色", attachment_type=allure.attachment_type.PNG)
    # 取色按钮：进入取色模式
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Background');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const picker=bs[2]; if(picker){picker.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)
    mode_png = page.screenshot()
    mode_path = tmp_path / "bg_picker_mode.png"
    mode_path.write_bytes(mode_png)
    allure.attach(mode_png, name="Background取色模式", attachment_type=allure.attachment_type.PNG)
    # 断言确实进入取色状态（画面/光标与色盘应用态有差异）
    diff_mode = ImageChops.difference(Image.open(palette_path).convert("RGB"), Image.open(mode_path).convert("RGB"))
    assert diff_mode.getbbox() is not None
    nonzero_mode = sum(1 for px in diff_mode.getdata() if px != (0, 0, 0))
    assert nonzero_mode > 10000
    # 从色盘蓝色应用态中找与蓝色距离最大的画布像素作为取色目标，确保颜色明显不同
    img_box = canvas_image_box(page)
    assert img_box is not None, "未找到画布图片区域"
    target_info, target_dist = most_distinct_pixel(str(palette_path), (0, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))
    assert target_info is not None
    assert target_dist > 80, f"取色目标与色盘蓝色太接近: dist={target_dist}"
    target = (target_info[0], target_info[1])
    page.mouse.move(target[0], target[1])
    page.wait_for_timeout(300)
    page.mouse.click(target[0], target[1])
    page.wait_for_timeout(1500)
    assert page.locator(".color-picker-wrapper").count() == 0, "取色后仍未退出取色模式"
    applied_png = page.screenshot()
    applied_path = tmp_path / "bg_picker_applied.png"
    applied_path.write_bytes(applied_png)
    allure.attach(applied_png, name="Background取色应用后", attachment_type=allure.attachment_type.PNG)
    # 断言取色应用后的画面与色盘绿色应用态不同（颜色已区分）
    diff_applied = ImageChops.difference(Image.open(palette_path).convert("RGB"), Image.open(applied_path).convert("RGB"))
    assert diff_applied.getbbox() is not None
    nonzero_applied = sum(1 for px in diff_applied.getdata() if px != (0, 0, 0))
    assert nonzero_applied > 5000

def test_text_006_outline(page: Page, base_url: str, tmp_path):
    allure.dynamic.title("[L2][P0] Outline Types/色盘/取色/四滑块/描边效果")
    allure.dynamic.epic("画布页文字功能")
    allure.dynamic.feature("画布页文字功能")
    from PIL import Image, ImageChops
    enter_canvas(page, base_url)
    add_text(page)
    click_section_small(page, "Outline")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline展开")
    # 描边效果：先记录开启前后
    before = tmp_path / "outline_before.png"
    page.screenshot(path=str(before))
    assert click_section_toggle(page, "Outline")
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline开关开启")
    after = tmp_path / "outline_after.png"
    page.screenshot(path=str(after))
    diff = ImageChops.difference(Image.open(before).convert("RGB"), Image.open(after).convert("RGB"))
    assert diff.getbbox() is not None
    nonzero = sum(1 for p in diff.getdata() if p != (0, 0, 0))
    assert nonzero > 10000
    # Types 切换
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; bs[1].dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}
        return false;
    }""")
    page.wait_for_timeout(800)
    allure_screenshot(page, "Outline Types切换")
    # 四滑块
    vals = set_section_sliders(page, "Outline", [70, 20, 10, 30])
    page.wait_for_timeout(1000)
    allure_screenshot(page, "Outline四滑块调整后")
    assert vals == ["70", "20", "10", "30"]
    # 色盘弹窗
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1500)
    allure_screenshot(page, "Outline色盘弹窗")
    assert page.locator("input.hexInput").is_visible()
    # 色盘应用品红 #ff00ff，作为后续取色的区分基准
    page.locator("input.hexInput").fill("#ff00ff")
    page.keyboard.press("Enter")
    page.wait_for_timeout(1200)
    assert page.locator("input.hexInput").input_value() == "#ff00ff"
    # 再次点击色盘按钮关闭调色弹窗（Escape 在 Enter 后无法关闭）
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const pal=bs.find(b=>b.innerHTML.includes('edit_icon_color_picker')); if(pal){pal.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(800)
    outline_palette_png = page.screenshot()
    outline_palette_path = tmp_path / "outline_palette_magenta.png"
    outline_palette_path.write_bytes(outline_palette_png)
    allure.attach(outline_palette_png, name="Outline色盘应用品红", attachment_type=allure.attachment_type.PNG)
    # 取色
    page.evaluate("""() => {
        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');
        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; const picker=bs[6]; if(picker){picker.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true})); return true;}}}}
        return false;
    }""")
    page.wait_for_timeout(1000)
    outline_mode_png = page.screenshot()
    outline_mode_path = tmp_path / "outline_picker_mode.png"
    outline_mode_path.write_bytes(outline_mode_png)
    allure.attach(outline_mode_png, name="Outline取色模式", attachment_type=allure.attachment_type.PNG)
    assert pixel_diff_nonzero(str(outline_palette_path), str(outline_mode_path)) > 10000
    # 从色盘蓝色应用态中找与蓝色距离最大的画布像素作为取色目标，确保颜色明显不同
    img_box = canvas_image_box(page)
    assert img_box is not None, "未找到画布图片区域"
    target_info, target_dist = most_distinct_pixel(str(outline_palette_path), (255, 0, 255), int(img_box["x"]), int(img_box["x"] + img_box["w"]), int(img_box["y"]), int(img_box["y"] + img_box["h"]))
    assert target_info is not None
    assert target_dist > 80, f"取色目标与色盘蓝色太接近: dist={target_dist}"
    target = (target_info[0], target_info[1])
    page.mouse.move(target[0], target[1])
    page.wait_for_timeout(300)
    page.mouse.click(target[0], target[1])
    page.wait_for_timeout(1500)
    assert page.locator(".color-picker-wrapper").count() == 0, "Outline 取色后仍未退出取色模式"
    outline_applied_png = page.screenshot()
    outline_applied_path = tmp_path / "outline_picker_applied.png"
    outline_applied_path.write_bytes(outline_applied_png)
    allure.attach(outline_applied_png, name="Outline取色应用后", attachment_type=allure.attachment_type.PNG)
    assert pixel_diff_nonzero(str(outline_palette_path), str(outline_applied_path)) > 5000
