"""临时诊断：确认 canvas_stats 购买链路依赖的 0-credit 账号当前 credits 态。"""
import re
from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
EMAIL = "autotest202609171333@qq.com"
CODE = "123456"

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    ctx = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    pg = ctx.new_page()
    pg.goto(BASE, wait_until="domcontentloaded")
    pg.wait_for_timeout(6000)
    try:
        pg.get_by_text("Log in", exact=True).first.click(timeout=8000)
    except Exception as exc:
        print("login entry:", exc)
    pg.wait_for_timeout(2500)
    try:
        pg.locator('input[type="email"]').first.fill(EMAIL)
        pg.locator('input[placeholder*="Verification" i], input[placeholder*="Code" i]').first.fill(CODE)
        pg.evaluate("""() => {
            const bs = [...document.querySelectorAll('button')];
            const t = bs.find(b => b.textContent.trim() === 'Log in' && b.offsetWidth > 200) || bs.find(b => b.textContent.trim() === 'Log in');
            if (t) t.dispatchEvent(new MouseEvent('click', {bubbles: true}));
        }""")
    except Exception as exc:
        print("fill:", exc)
    pg.wait_for_timeout(9000)
    print("URL:", pg.url)
    info = pg.evaluate("""() => {
        const hits = [];
        document.querySelectorAll('*').forEach(el => {
            if (el.children.length) return;
            const t = (el.textContent || '').trim();
            if (!t || t.length > 24) return;
            if (/^\\d+\\s*\\/\\s*\\d+$/.test(t) || /credit/i.test(t) || /^\\d{1,6}$/.test(t)) {
                const r = el.getBoundingClientRect();
                const style = getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || r.width === 0) return;
                hits.push({t, cls: el.className && el.className.toString().slice(0, 60), x: Math.round(r.x), y: Math.round(r.y)});
            }
        });
        return hits.slice(0, 25);
    }""")
    for h in info:
        print("  ", h)
    pg.screenshot(path="artifacts/2026-10-12_stable_regression_registry/shots/zero_credit_account_probe.png")
    b.close()
