"""复探：移动端首页 effect 模板卡现状（原用例找 button name='Butt'）。"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path("artifacts/2026-09-14_stable_regression_all_archived/reexplore")
MOBILE = dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
              device_scale_factor=3, locale="en-US",
              user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"))
out = {}
with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(**MOBILE)
    pg = ctx.new_page()
    pg.set_default_timeout(15000)
    pg.goto(BASE, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)
    out["img_alts"] = pg.evaluate("() => Array.from(document.querySelectorAll('img[alt]')).map(i => i.getAttribute('alt')).filter(Boolean).slice(0,80)")
    out["section_headings"] = pg.evaluate("""() => Array.from(document.querySelectorAll('h1,h2,h3,h4'))
        .map(h => (h.innerText||'').trim()).filter(Boolean).slice(0,40)""")
    out["butt_in_html"] = "Butt" in pg.content()
    # 逐步滚动收集可见卡片文案
    seen = []
    for i in range(12):
        pg.mouse.wheel(0, 800)
        pg.wait_for_timeout(900)
        vis = pg.evaluate("""() => {
            const out = [];
            document.querySelectorAll('div,a,button').forEach(el => {
                const t = (el.innerText || '').trim();
                const r = el.getBoundingClientRect();
                if (t && t.length < 40 && r.top > 60 && r.top < 800 && r.width > 60) out.push(t);
            });
            return out;
        }""")
        seen.extend(vis)
        if i in (5, 11):
            pg.screenshot(path=str(OUT / f"mobile_home_scroll_{i}.png"), full_page=False)
    out["visible_card_texts"] = sorted(set(seen))
    # effect 模板区可能的 file chooser 触发元素
    out["file_inputs"] = pg.evaluate("() => Array.from(document.querySelectorAll('input[type=file]')).map(i => ({accept: i.accept, cls: (i.className||'').slice(0,80)}))")
    (OUT / "mobile_effect_cards.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("butt in html:", out["butt_in_html"], flush=True)
    print("headings:", json.dumps(out["section_headings"], ensure_ascii=False)[:800], flush=True)
    print("img alts:", json.dumps(out["img_alts"], ensure_ascii=False)[:900], flush=True)
    print("visible card texts:", json.dumps(out["visible_card_texts"], ensure_ascii=False)[:1500], flush=True)
    print("file inputs:", json.dumps(out["file_inputs"], ensure_ascii=False)[:400], flush=True)
    ctx.close(); b.close()
print("done", flush=True)