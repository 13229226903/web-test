from pathlib import Path
p=Path(r'D:\Test\web-test\tests\test_infinite_canvas_inspiration_debug.py')
s=p.read_text(encoding='utf-8')
old1='''    with allure.step(f"设置 Debug 开关：{label} -> {enabled}"):
        sw = _debug_switch(page, label)
        expect(sw).to_be_visible(timeout=10000)
        if enabled:
            sw.check(timeout=10000)
        else:
            sw.uncheck(timeout=10000)
        page.wait_for_timeout(400)
        expected_checked = "true" if enabled else None
        actual = sw.get_attribute("checked")
        if enabled:
            assert sw.is_checked(), f"{label} 未被打开"
        else:
            assert not sw.is_checked(), f"{label} 未被关闭"'''
new1='''    with allure.step(f"设置 Debug 开关：{label} -> {enabled}"):
        row = page.locator(".debug-panel-content .switch-row").filter(has_text=label)
        expect(row).to_be_visible(timeout=10000)
        row.locator(".slider").click(force=True, timeout=10000)
        page.wait_for_timeout(500)
        sw = row.locator("input[type='checkbox']")
        assert sw.is_checked() == enabled, f"{label} 开关状态不符合预期：{enabled}"'''
old2='''    with allure.step(f"切换模型到 {model_text}"):
        panel = page.locator("div.canvas-textbox-expanded-state").first
        expect(panel).to_be_visible(timeout=20000)
        current = panel.get_by_text(model_text, exact=True)
        if current.count() > 0:
            # 如果当前已经是目标模型，直接返回。
            try:
                if current.first.is_visible():
                    return
            except Exception:
                pass
        # 打开当前模型下拉。
        current_label = panel.locator("span,div").filter(has_text=True).get_by_text if False else None
        all_visible_text = panel.inner_text(timeout=5000)
        if MODELS["pro"] in all_visible_text:
            visible_current = MODELS["pro"]
        elif MODELS["basic"] in all_visible_text:
            visible_current = MODELS["basic"]
        elif MODELS["nano"] in all_visible_text:
            visible_current = MODELS["nano"]
        else:
            visible_current = MODELS["chatgpt"]
        panel.get_by_text(visible_current, exact=True).first.click(timeout=10000)
        page.wait_for_timeout(700)
        page.get_by_text(model_text, exact=True).last.click(timeout=10000)
        page.wait_for_timeout(1600)
        assert model_text in panel.inner_text(timeout=5000), f"模型未切换到 {model_text}"'''
new2='''    with allure.step(f"切换模型到 {model_text}"):
        panel = page.locator("div.canvas-textbox-expanded-state").first
        expect(panel).to_be_visible(timeout=20000)
        current_btn = panel.locator("div.relative.z-\\[15\\].h-\\[2\\.75rem\\].px-\\[0\\.75rem\\]").first
        expect(current_btn).to_be_visible(timeout=20000)
        current_btn.click(timeout=10000)
        page.wait_for_timeout(700)
        target = page.get_by_text(model_text, exact=True)
        assert target.count() > 0, f"未找到模型选项：{model_text}"
        target.last.click(timeout=10000)
        page.wait_for_timeout(1600)
        assert model_text in panel.inner_text(timeout=5000), f"模型未切换到 {model_text}"'''
if old1 not in s:
    raise SystemExit('old1 not found')
if old2 not in s:
    raise SystemExit('old2 not found')
s=s.replace(old1,new1).replace(old2,new2)
p.write_text(s,encoding='utf-8')
