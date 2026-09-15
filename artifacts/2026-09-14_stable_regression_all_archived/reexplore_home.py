"""复探：移动端首页模型入口/effect 模板入口 + PC 首页模型入口现状。"""
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://10.17.1.66:3001"
OUT = Path("artifacts/2026-09-14_stable_regression_all_archived/reexplore")
OUT.mkdir(parents=True, exist_ok=True)
MOBILE = dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
              device_scale_factor=3, locale="en-US",
              user_agent=("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"))
out = {}

with sync_playwright() as p:
    b = p.chromium.launch()

    # ---------- 移动端首页 ----------
    ctx = b.new_context(**MOBILE)
    pg = ctx.new_page()
    pg.set_default_timeout(15000)
    pg.goto(BASE, wait_until="domcontentloaded", timeout=60000)
    pg.wait_for_timeout(6000)

    hero_btns = []
    for i in range(pg.locator("section.mobile-home-agent-hero button").count()):
        el = pg.locator("section.mobile-home-agent-hero button").nth(i)
        hero_btns.append({
            "text": (el.inner_text() or "").strip(),
            "aria": el.get_attribute("aria-label"),
            "cls": el.get_attribute("class"),
            "html": (el.evaluate("e => e.outerHTML") or "")[:300],
        })
    out["hero_buttons"] = hero_btns

    # 点击模型入口（hero 内第一个可点开模型列表的按钮）
    popup_before = pg.locator("body").inner_text()
    clicked = None
    for i in range(pg.locator("section.mobile-home-agent-hero button").count()):
        el = pg.locator("section.mobile-home-agent-hero button").nth(i)
        txt = (el.inner_text() or "").strip()
        if txt in ("Auto", "Pokecut Pro") or "Auto" in txt:
            el.click()
            clicked = txt
            break
    pg.wait_for_timeout(1500)
    pg.screenshot(path=str(OUT / "mobile_hero_model_popover.png"), full_page=False)
    body_after = pg.locator("body").inner_text()
    out["model_entry_clicked"] = clicked
    out["model_options_present"] = {k: (k in body_after) for k in
        ["Pokecut Pro", "ChatGPT Image 2.0", "Nano Banana", "Nano Banana 2", "Seedream4.0", "Auto"]}
    # 弹层结构
    out["popup_candidates"] = pg.evaluate("""() => {
        const out = [];
        document.querySelectorAll('div,ul').forEach(el => {
            const t = (el.innerText || '').trim();
            if (t.includes('Nano Banana') && t.length < 600) {
                const r = el.getBoundingClientRect();
                out.push({tag: el.tagName, cls: el.className, w: Math.round(r.width), h: Math.round(r.height), txt: t.slice(0, 240)});
            }
        });
        return out.slice(0, 12);
    }""")

    # 全页搜 Butt
    out["butt_hits"] = pg.evaluate("""() => {
        const hits = [];
        document.querySelectorAll('*').forEach(el => {
            if (el.children.length === 0) {
                const t = (el.innerText || el.textContent || '').trim();
                if (/butt/i.test(t) && t.length < 60) hits.push({tag: el.tagName, txt: t, cls: el.className});
            }
        });
        return hits.slice(0, 20);
    }""")
    out["butt_button_names"] = pg.evaluate("""() => Array.from(document.querySelectorAll('button'))
        .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim())
        .filter(t => /butt/i.test(t)).slice(0, 20)""")
    out["mobile_tool_buttons"] = sorted({t.strip() for t in pg.locator("button").all_inner_texts() if t.strip()})
    (OUT / "mobile_home_reexplore.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print("MOBILE hero buttons:", json.dumps([b["text"] for b in hero_btns], ensure_ascii=False), flush=True)
    print("MOBILE clicked entry:", clicked, "| options:", out["model_options_present"], flush=True)
    print("MOBILE popup candidates:", json.dumps(out["popup_candidates"], ensure_ascii=False)[:900], flush=True)
    print("MOBILE butt hits:", json.dumps(out["butt_hits"], ensure_ascii=False)[:600], flush=True)
    ctx.close()

    # ---------- PC 首页 ----------
    out2 = {}
    ctx2 = b.new_context(viewport={"width": 1920, "height": 1080}, locale="en-US")
    pg2 = ctx2.new_page()
    pg2.set_default_timeout(15000)
    pg2.goto(BASE, wait_until="domcontentloaded", timeout=60000)
    pg2.wait_for_timeout(5000)
    out2["prompt_settings_exists"] = pg2.locator("button[aria-label='Prompt settings']").count()
    out2["buttons_in_hero"] = pg2.evaluate("""() => {
        const out = [];
        document.querySelectorAll('button').forEach(b => {
            const r = b.getBoundingClientRect();
            const t = (b.innerText || '').trim();
            if (r.top < 900 && r.width > 0 && t) out.push({t: t.slice(0, 60), aria: b.getAttribute('aria-label'), cls: (b.className||'').slice(0,80), y: Math.round(r.top)});
        });
        return out.slice(0, 40);
    }""")
    pg2.screenshot(path=str(OUT / "pc_home_hero.png"), full_page=False)
    # 文本域
    tb = pg2.get_by_role("textbox").count()
    out2["textbox_count"] = tb
    out2["model_labels"] = pg2.evaluate("""() => Array.from(document.querySelectorAll('button'))
        .map(b => (b.innerText||'').trim()).filter(t => /Pokecut Pro|Auto|Nano Banana|Seedream|ChatGPT/i.test(t)).slice(0, 20)""")
    (OUT / "pc_home_reexplore.json").write_text(json.dumps(out2, ensure_ascii=False, indent=2), encoding="utf-8")
    print("PC prompt settings:", out2["prompt_settings_exists"], "| textboxes:", tb, flush=True)
    print("PC hero buttons:", json.dumps(out2["buttons_in_hero"], ensure_ascii=False)[:1200], flush=True)
    print("PC model labels:", json.dumps(out2["model_labels"], ensure_ascii=False)[:600], flush=True)
    ctx2.close()
    b.close()
print("done", flush=True)