from pathlib import Path
p = Path('tests/test_infinite_canvas_text_layer_v2.py')
s = p.read_text(encoding='utf-8')
repls = [
("    click_button_by_text(page, \"Space\", ymin=480, ymax=820)\n    page.wait_for_timeout(1000)\n    sliders = get_section_sliders(page, \"Space\")",
 "    click_button_by_text(page, \"Space\", ymin=480, ymax=820)\n    page.wait_for_timeout(1000)\n    allure_screenshot(page, \"Space单行展开Height禁用\")\n    sliders = get_section_sliders(page, \"Space\")"),
("    make_two_line_text(page)\n    click_button_by_text(page, \"Space\", ymin=480, ymax=820)",
 "    make_two_line_text(page)\n    allure_screenshot(page, \"两行文字图层\")\n    click_button_by_text(page, \"Space\", ymin=480, ymax=820)"),
("    page.wait_for_timeout(1500)\n    after = panel_dimension_text(page)\n    assert before != after\n    assert get_section_sliders(page, \"Space\")[1][\"value\"] == \"50\"",
 "    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Space两行Height调整后\")\n    after = panel_dimension_text(page)\n    assert before != after\n    assert get_section_sliders(page, \"Space\")[1][\"value\"] == \"50\""),
("    page.wait_for_timeout(1000)\n    sliders = get_section_sliders(page, \"Reflection\")\n    assert sliders is not None and len(sliders) == 4",
 "    page.wait_for_timeout(1000)\n    allure_screenshot(page, \"Reflection展开四滑块\")\n    sliders = get_section_sliders(page, \"Reflection\")\n    assert sliders is not None and len(sliders) == 4"),
("    page.wait_for_timeout(800)\n    cls = page.evaluate(\"\"\"() => {\n        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection');",
 "    page.wait_for_timeout(800)\n    allure_screenshot(page, \"Reflection开关开启\")\n    cls = page.evaluate(\"\"\"() => {\n        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Reflection');"),
("    page.wait_for_timeout(1000)\n    assert vals == [\"20\", \"20\", \"20\", \"45\"]",
 "    page.wait_for_timeout(1000)\n    allure_screenshot(page, \"Reflection四参数调整后\")\n    assert vals == [\"20\", \"20\", \"20\", \"45\"]"),
("    before = tmp_path / \"reflection_before.png\"\n    page.screenshot(path=str(before))",
 "    allure_screenshot(page, \"Reflection关闭\")\n    before = tmp_path / \"reflection_before.png\"\n    page.screenshot(path=str(before))"),
("    page.wait_for_timeout(1500)\n    after = tmp_path / \"reflection_after.png\"\n    page.screenshot(path=str(after))",
 "    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Reflection开启效果\")\n    after = tmp_path / \"reflection_after.png\"\n    page.screenshot(path=str(after))"),
("    click_button_by_text(page, \"Background\", ymin=480, ymax=820)\n    page.wait_for_timeout(1000)\n    content = page.evaluate",
 "    click_button_by_text(page, \"Background\", ymin=480, ymax=820)\n    page.wait_for_timeout(1000)\n    allure_screenshot(page, \"Background展开三按钮\")\n    content = page.evaluate"),
("    page.wait_for_timeout(1500)\n    assert page.locator(\"input.hexInput\").is_visible()\n    page.locator(\"input.hexInput\").fill(\"#ff0000\")",
 "    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Background色盘弹窗\")\n    assert page.locator(\"input.hexInput\").is_visible()\n    page.locator(\"input.hexInput\").fill(\"#ff0000\")"),
("    page.keyboard.press(\"Enter\")\n    page.wait_for_timeout(1200)\n    assert page.locator(\"input.hexInput\").input_value() == \"#ff0000\"",
 "    page.keyboard.press(\"Enter\")\n    page.wait_for_timeout(1200)\n    allure_screenshot(page, \"Background色盘应用红色\")\n    assert page.locator(\"input.hexInput\").input_value() == \"#ff0000\""),
("    assert clicked\n    page.wait_for_timeout(1000)\n    page.mouse.click(900, 500)\n    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Background 取色应用后\")",
 "    assert clicked\n    page.wait_for_timeout(1000)\n    allure_screenshot(page, \"Background取色模式\")\n    page.mouse.click(900, 500)\n    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Background取色应用后\")"),
("    page.wait_for_timeout(800)\n    cls = page.evaluate(\"\"\"() => {\n        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');",
 "    page.wait_for_timeout(800)\n    allure_screenshot(page, \"Outline开关开启\")\n    cls = page.evaluate(\"\"\"() => {\n        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');"),
("    page.wait_for_timeout(800)\n    cls = page.evaluate(\"\"\"() => {\n        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');\n        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; return bs[1].className;}}}",
 "    page.wait_for_timeout(800)\n    allure_screenshot(page, \"Outline Types切换\")\n    cls = page.evaluate(\"\"\"() => {\n        const spans=[...document.querySelectorAll('span')].filter(s=>s.textContent.trim()==='Outline');\n        for(const sp of spans){const r=sp.getBoundingClientRect(); if(r.width>0&&r.x>=1000){const row=sp.parentElement; const content=row.nextElementSibling; if(content){const bs=[...content.querySelectorAll('button')]; return bs[1].className;}}}"),
("    page.wait_for_timeout(1500)\n    assert page.locator(\"input.hexInput\").is_visible()\n    page.keyboard.press(\"Escape\")",
 "    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Outline色盘弹窗\")\n    assert page.locator(\"input.hexInput\").is_visible()\n    page.keyboard.press(\"Escape\")"),
("    page.wait_for_timeout(800)\n    assert not page.locator(\"input.hexInput\").is_visible()",
 "    page.wait_for_timeout(800)\n    allure_screenshot(page, \"Outline色盘关闭\")\n    assert not page.locator(\"input.hexInput\").is_visible()"),
("    assert clicked\n    page.wait_for_timeout(1000)\n    page.mouse.click(900, 500)\n    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Outline 取色应用后\")",
 "    assert clicked\n    page.wait_for_timeout(1000)\n    allure_screenshot(page, \"Outline取色模式\")\n    page.mouse.click(900, 500)\n    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Outline取色应用后\")"),
("    page.wait_for_timeout(1000)\n    assert vals == [\"70\", \"20\", \"10\", \"30\"]",
 "    page.wait_for_timeout(1000)\n    allure_screenshot(page, \"Outline四滑块调整后\")\n    assert vals == [\"70\", \"20\", \"10\", \"30\"]"),
("    before = tmp_path / \"outline_before.png\"\n    page.screenshot(path=str(before))",
 "    allure_screenshot(page, \"Outline关闭\")\n    before = tmp_path / \"outline_before.png\"\n    page.screenshot(path=str(before))"),
("    page.wait_for_timeout(1500)\n    after = tmp_path / \"outline_after.png\"\n    page.screenshot(path=str(after))",
 "    page.wait_for_timeout(1500)\n    allure_screenshot(page, \"Outline开启效果\")\n    after = tmp_path / \"outline_after.png\"\n    page.screenshot(path=str(after))"),
]
for old, new in repls:
    if old not in s:
        print('MISS', old[:60])
    else:
        s = s.replace(old, new, 1)
p.write_text(s, encoding='utf-8')
print('screenshots inserted')
