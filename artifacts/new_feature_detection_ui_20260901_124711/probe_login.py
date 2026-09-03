import asyncio, time
from playwright.async_api import async_playwright
BASE = "https://pokecut-dev.guangzhuiyuan.com"

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True)
        ctx = await b.new_context(viewport={"width":1920,"height":1080}, locale="en-US")
        pg = await ctx.new_page()
        await pg.goto(f"{BASE}/tools/nose-shape-detector", wait_until="domcontentloaded")
        await pg.wait_for_timeout(5000)
        # click Log in
        await pg.get_by_role("button", name="Log in").click()
        await pg.wait_for_timeout(2500)
        body = await pg.inner_text("body")
        print("=== LOGIN MODAL BODY ===")
        print(body[:3500])
        # dump inputs
        try:
            inputs = await pg.locator("input").evaluate_all("els => els.map(e=>({id:e.id,type:e.type,placeholder:e.placeholder,name:e.name,aria:e.getAttribute('aria-label')}))")
            print("INPUTS:", inputs)
        except Exception as e:
            print("inputs err", e)
        await pg.screenshot(path="artifacts/new_feature_detection_ui_20260901_124711/shots/login_modal.png", full_page=False)
        await b.close()

asyncio.run(main())
