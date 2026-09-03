# -*- coding: utf-8 -*-
from playwright.sync_api import sync_playwright
import json, os, time, re

TASK = r"D:\Test\web-test\artifacts\task-22_feishu_mobile_home"
SHOTS = os.path.join(TASK, "shots")
os.makedirs(SHOTS, exist_ok=True)
HOME = "http://10.17.1.66:3001/"
IMG = r"D:\Test\web-test\test_images\有人脸.JPG"
DAMAGED = r"D:\Test\web-test\test_images\损坏的图.png"

R = {}

def shot(name, full=False):
    try:
        page.screenshot(path=os.path.join(SHOTS, name), full_page=full)
    except Exception as e:
        print("shot fail", name, repr(e))

def visible_buttons():
    return page.eval_on_selector_all("button", """els => els.filter(e=>{const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return r.width>0 && r.height>0 && cs.visibility!=='hidden' && cs.display!=='none';}).map(e=>(e.innerText||e.getAttribute('aria-label')||'').trim().replace(/\\n/g,' ').slice(0,80))""")

def visible_links():
    return page.eval_on_selector_all("a", """els => els.filter(e=>{const r=e.getBoundingClientRect(); const cs=getComputedStyle(e); return r.width>0 && r.height>0 && cs.visibility!=='hidden' && cs.display!=='none';}).map(e=>({t:(e.innerText||'').trim().replace(/\\n/g,' ').slice(0,80), href:e.href, target:e.target||'', rel:e.rel||''}))""")

def home(wait=6000):
    page.goto(HOME, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(wait)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width":390,"height":844}, is_mobile=True, has_touch=True, device_scale_factor=3, locale="en-US",
        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    page = ctx.new_page()
    page.set_default_timeout(15000)
    home()
    R["start"] = {"url": page.url, "title": page.title(), "ts": time.strftime("%Y-%m-%d %H:%M:%S")}

    # ---- Agent hero ----
    R["agent_hero"] = {}
    try:
        R["agent_hero"]["title"] = page.locator("#home-mobile-agent-title").inner_text().strip()
    except Exception as e:
        R["agent_hero"]["title_error"] = str(e)[:150]
    R["agent_hero"]["main_button"] = page.get_by_role("button", name="Start Creating for Free").inner_text().strip()
    try:
        R["agent_hero"]["input_placeholder"] = page.locator("textarea[aria-label]").first.get_attribute("placeholder")
    except Exception as e:
        R["agent_hero"]["input_placeholder_error"] = str(e)[:150]
    gen = page.locator("section.mobile-home-agent-hero button", has_text="Generate").first
    R["agent_hero"]["generate_disabled"] = gen.is_disabled()
    shot("01_agent_hero.png")
    url_before = page.url
    try:
        gen.click(force=True)
        page.wait_for_timeout(1200)
        R["agent_hero"]["generate_click_no_nav"] = page.url == url_before
    except Exception as e:
        R["agent_hero"]["generate_click_no_nav"] = True
        R["agent_hero"]["generate_click_note"] = str(e)[:120]
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.get_by_role("button", name="Start Creating for Free").click()
        ch = fc.value
        R["agent_hero"]["main_button_file_chooser"] = True
        ch.set_files([IMG])
        page.wait_for_timeout(5000)
        R["agent_hero"]["main_button_upload_url"] = page.url
        shot("02_agent_main_upload_canvas.png")
    except Exception as e:
        R["agent_hero"]["main_button_file_chooser"] = False
        R["agent_hero"]["main_button_error"] = str(e)[:200]

    # ---- model / ratio / resolution entries ----
    home()
    R["agent_entries"] = {}
    # identify entry buttons in hero by aria/text
    def hero_buttons():
        return page.eval_on_selector_all("section.mobile-home-agent-hero button", """els => els.map(e=>({idx:els.indexOf(e), aria:e.getAttribute('aria-label'), text:(e.innerText||'').trim(), cls:(e.className||'').slice(0,80)}))""")
    hb = hero_buttons()
    R["agent_entries"]["hero_buttons"] = hb
    # model
    for key, locator in [("model", page.locator("section.mobile-home-agent-hero button", has_text="Pokecut Pro")),
                         ("resolution", page.locator("section.mobile-home-agent-hero button[aria-label='Output Resolution:']"))]:
        home()
        before = set(visible_buttons())
        try:
            locator.first.click()
            page.wait_for_timeout(1200)
            after = set(visible_buttons())
            R["agent_entries"][key] = {"opened": True, "new_buttons": sorted(after - before)[:20]}
            shot(f"03_agent_entry_{key}.png")
        except Exception as e:
            R["agent_entries"][key] = {"opened": False, "error": str(e)[:200]}
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        page.mouse.click(200, 300)
        page.wait_for_timeout(500)
    # ratio: empty text button without aria-label in hero (not Generate)
    home()
    before = set(visible_buttons())
    ratio_clicked = page.evaluate("""() => { const bs=[...document.querySelectorAll('section.mobile-home-agent-hero button')]; const b=bs.find(e=>(e.innerText||'').trim()==='' && !e.getAttribute('aria-label') && !e.innerText.includes('Generate')); if(b){ b.click(); return true; } return false; }""")
    page.wait_for_timeout(1200)
    after = set(visible_buttons())
    R["agent_entries"]["ratio"] = {"clicked": ratio_clicked, "new_buttons": sorted(after - before)[:20]}
    shot("03_agent_entry_ratio.png")
    try:
        page.keyboard.press("Escape")
    except Exception:
        pass
    page.mouse.click(200, 300)
    page.wait_for_timeout(500)

    # ---- Function board ----
    home()
    R["function_board"] = {}
    cards = ["Remove Background", "Clothes Changer", "HD Photo Coverter", "ID Photo Maker", "Body Editor", "AI Replace"]
    R["function_board"]["cards_visible"] = []
    for c in cards:
        b = page.get_by_role("button", name=c)
        R["function_board"]["cards_visible"].append({"name": c, "visible": b.first.is_visible()})
    R["function_board"]["chooser_triggered"] = {}
    for c in cards:
        home()
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                page.get_by_role("button", name=c).first.click()
            ch = fc.value
            ch.set_files([])
            page.wait_for_timeout(1000)
            R["function_board"]["chooser_triggered"][c] = True
        except Exception as e:
            R["function_board"]["chooser_triggered"][c] = {"triggered": False, "error": str(e)[:200]}
    # representative upload: Remove Background
    home()
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.get_by_role("button", name="Remove Background").first.click()
        ch = fc.value
        ch.set_files([IMG])
        page.wait_for_timeout(6000)
        R["function_board"]["remove_bg_upload_url"] = page.url
        R["function_board"]["remove_bg_body_text"] = page.inner_text("body")[:400]
        shot("04_remove_bg_canvas.png")
    except Exception as e:
        R["function_board"]["remove_bg_upload_error"] = str(e)[:200]
    # More Pokecut Tools
    home()
    try:
        page.get_by_role("button", name="More Pokecut Tools").click()
        page.wait_for_timeout(4000)
        R["function_board"]["more_tools_url"] = page.url
    except Exception as e:
        R["function_board"]["more_tools_error"] = str(e)[:200]

    # ---- effect / AI Templates board ----
    home()
    R["effect_board"] = {}
    try:
        h2 = page.locator("h2", has_text="Create Faster")
        R["effect_board"]["heading"] = h2.inner_text().strip()
    except Exception as e:
        R["effect_board"]["heading_error"] = str(e)[:150]
    # first template = first visible button under that section that is not nav/cta
    first_template = None
    for b in visible_buttons():
        if b and b not in cards and b not in ("Start Creating for Free","Sign up","See More Creations","More Pokecut Tools","Generate") and not b.startswith(("3M+","200+","500M+","#2")):
            first_template = b
            break
    R["effect_board"]["first_template_clicked"] = first_template
    if first_template:
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                page.get_by_role("button", name=first_template).first.click()
            ch = fc.value
            ch.set_files([])
            page.wait_for_timeout(800)
            R["effect_board"]["template_file_chooser"] = True
        except Exception as e:
            R["effect_board"]["template_file_chooser"] = {"triggered": False, "error": str(e)[:200]}
    # upload via first template
    home()
    first_template2 = None
    for b in visible_buttons():
        if b and b not in cards and b not in ("Start Creating for Free","Sign up","See More Creations","More Pokecut Tools","Generate") and not b.startswith(("3M+","200+","500M+","#2")):
            first_template2 = b
            break
    if first_template2:
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                page.get_by_role("button", name=first_template2).first.click()
            ch = fc.value
            ch.set_files([IMG])
            page.wait_for_timeout(6000)
            R["effect_board"]["template_upload_url"] = page.url
            shot("05_effect_template_canvas.png")
        except Exception as e:
            R["effect_board"]["template_upload_error"] = str(e)[:200]
    # See More Creations
    home()
    try:
        page.get_by_role("button", name="See More Creations").click()
        page.wait_for_timeout(4000)
        R["effect_board"]["see_more_url"] = page.url
    except Exception as e:
        R["effect_board"]["see_more_error"] = str(e)[:200]

    # ---- Test board ----
    home()
    R["test_board"] = {}
    try:
        R["test_board"]["heading"] = page.locator("h2", has_text="Test Your Portrait").inner_text().strip()
    except Exception as e:
        R["test_board"]["heading_error"] = str(e)[:150]
    R["test_board"]["links"] = visible_links()
    R["test_board"]["navigations"] = {}
    for name in ["Pretty Scale", "Ethnicity Guesser", "Eye Color Detector", "Body Shape Detector"]:
        home()
        href = None
        try:
            href = page.get_by_role("link", name=name).first.get_attribute("href")
        except Exception:
            pass
        try:
            with page.context.expect_page(timeout=5000) as np_info:
                page.get_by_role("link", name=name).first.click()
            np_ = np_info.value
            np_.wait_for_load_state("domcontentloaded")
            R["test_board"]["navigations"][name] = {"href": href, "opened_new_tab": True, "new_url": np_.url}
            np_.close()
        except Exception as e:
            R["test_board"]["navigations"][name] = {"href": href, "opened_new_tab": False, "same_tab_url": page.url, "note": str(e)[:150]}

    # ---- Portrait board ----
    home()
    R["portrait_board"] = {}
    try:
        R["portrait_board"]["heading"] = page.locator("h2", has_text="Upgrade Portrait Details").inner_text().strip()
    except Exception as e:
        R["portrait_board"]["heading_error"] = str(e)[:150]
    R["portrait_board"]["tabs"] = []
    for tab in ["Face", "Body", "Hair", "Background"]:
        home()
        try:
            page.get_by_role("button", name=tab, exact=True).click()
            page.wait_for_timeout(1200)
            active = page.evaluate("""() => { const b=[...document.querySelectorAll('button')].find(e=>(e.innerText||'').trim()==='%s'); return b? b.className : ''; }""" % tab)
            R["portrait_board"]["tabs"].append({"tab": tab, "active_class": active[:200]})
            if tab == "Face":
                shot("06_portrait_face.png")
        except Exception as e:
            R["portrait_board"]["tabs"].append({"tab": tab, "error": str(e)[:200]})
    home()
    try:
        page.get_by_role("button", name="Face", exact=True).click()
        page.wait_for_timeout(1000)
        R["portrait_board"]["face_cards"] = visible_links()
    except Exception as e:
        R["portrait_board"]["face_cards_error"] = str(e)[:200]

    # ---- Image enhancement board ----
    home()
    R["enhance_board"] = {}
    try:
        R["enhance_board"]["heading"] = page.locator("h2", has_text="Enhance Photo Quality").inner_text().strip()
    except Exception as e:
        R["enhance_board"]["heading_error"] = str(e)[:150]
    R["enhance_board"]["buttons"] = [b for b in visible_buttons() if b in ("HD Enhance","Portrait AI","Text Enhance","Ultra Enhance")]
    R["enhance_board"]["links"] = [l for l in visible_links() if l["t"] in ("HD Enhance","Text Enhance")]
    R["enhance_board"]["chooser_triggered"] = {}
    for nm in ["Portrait AI", "Ultra Enhance"]:
        home()
        try:
            with page.expect_file_chooser(timeout=5000) as fc:
                page.get_by_role("button", name=nm).first.click()
            ch = fc.value
            ch.set_files([])
            page.wait_for_timeout(800)
            R["enhance_board"]["chooser_triggered"][nm] = True
        except Exception as e:
            R["enhance_board"]["chooser_triggered"][nm] = {"triggered": False, "error": str(e)[:200]}
    # Portrait AI upload
    home()
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.get_by_role("button", name="Portrait AI").first.click()
        ch = fc.value
        ch.set_files([IMG])
        page.wait_for_timeout(6000)
        R["enhance_board"]["portrait_ai_upload_url"] = page.url
        shot("07_portrait_ai_canvas.png")
    except Exception as e:
        R["enhance_board"]["portrait_ai_upload_error"] = str(e)[:200]

    # ---- Data display ----
    home()
    R["data_board"] = {}
    try:
        R["data_board"]["heading"] = page.locator("h2", has_text="Pokecut is Trusted").inner_text().strip()
    except Exception as e:
        R["data_board"]["heading_error"] = str(e)[:150]
    R["data_board"]["cards"] = [b for b in visible_buttons() if b.startswith(("3M+","200+","500M+","#2"))]
    ph = page.locator("a[href*='producthunt.com']").first
    R["data_board"]["product_hunt_href"] = ph.get_attribute("href") if ph.count() else None
    R["data_board"]["product_hunt_target"] = ph.get_attribute("target") if ph.count() else None
    try:
        page.get_by_role("button", name="3M+ creators").click()
        page.wait_for_timeout(800)
        cls = page.get_by_role("button", name="3M+ creators").get_attribute("class")
        R["data_board"]["selected_card_class"] = cls[:300]
        shot("08_data_selected.png")
    except Exception as e:
        R["data_board"]["selected_error"] = str(e)[:200]

    # ---- Reviews ----
    home()
    R["reviews"] = {}
    try:
        R["reviews"]["heading"] = page.locator("h2", has_text="What Users Say").inner_text().strip()
    except Exception as e:
        R["reviews"]["heading_error"] = str(e)[:150]
    R["reviews"]["username_links"] = page.eval_on_selector_all("a[href*='producthunt.com/@']", """els => els.map(e=>({t:(e.innerText||'').trim(), href:e.href, target:e.target||'', rel:e.rel||''}))""")
    R["reviews"]["images"] = page.eval_on_selector_all("img[src*='homepagerefresh']", "els => els.map(e=>e.src.split('/').pop())")
    shot("09_reviews.png")

    # ---- FAQ ----
    home()
    R["faq"] = {}
    try:
        R["faq"]["heading"] = page.locator("h2", has_text="Frequently Asked Questions").inner_text().strip()
    except Exception as e:
        R["faq"]["heading_error"] = str(e)[:150]
    R["faq"]["questions"] = page.eval_on_selector_all("h3", "els => els.map(e=>(e.innerText||'').trim())")
    try:
        q0 = page.locator("h3", has_text="What is Pokecut").first
        q0.click()
        page.wait_for_timeout(1000)
        ans = page.evaluate("""() => { const h=[...document.querySelectorAll('h3')].find(e=>e.innerText.includes('What is Pokecut')); let p=h.nextElementSibling; return p? p.innerText.slice(0,500):null }""")
        R["faq"]["first_answer_after_click"] = ans
        shot("10_faq_expanded.png")
        q0.click()
        page.wait_for_timeout(600)
        ans2 = page.evaluate("""() => { const h=[...document.querySelectorAll('h3')].find(e=>e.innerText.includes('What is Pokecut')); let p=h.nextElementSibling; return p? (p.getBoundingClientRect().height>0):null }""")
        R["faq"]["first_answer_collapsed_visible"] = ans2
    except Exception as e:
        R["faq"]["expand_error"] = str(e)[:200]
    R["faq"]["answer_links"] = page.eval_on_selector_all("a[href*='/pricing'], a[href*='/term-of-use'], a[data-submit-ticket]", "els => els.map(e=>({t:(e.innerText||'').trim(), href:e.href, submit:e.getAttribute('data-submit-ticket')}))")

    # ---- Mobile app section ----
    home()
    R["mobile_app"] = {}
    R["mobile_app"]["segment"] = page.evaluate("""() => { const t=document.body.innerText; const i=t.indexOf('Pokecut Mobile App'); return i>=0? t.slice(i, i+450) : null }""")
    R["mobile_app"]["store_links"] = page.eval_on_selector_all("a[href*='apps.apple.com'], a[href*='play.google.com']", "els => els.map(e=>({t:(e.innerText||'').trim(), href:e.href, target:e.target||''}))")
    lang = page.locator("button", has_text="Language").first
    R["mobile_app"]["language_button"] = lang.inner_text().strip() if lang.count() else None
    shot("11_mobile_app_section.png")

    # ---- Bottom fixed nav ----
    home()
    R["bottom_nav"] = {}
    R["bottom_nav"]["items"] = page.eval_on_selector_all("nav.home-mobile-bottom-nav button", "els => els.map(e=>({aria:e.getAttribute('aria-label'), label:(e.querySelector('.home-mobile-bottom-nav-label')||{}).innerText||''}))")
    try:
        page.get_by_role("button", name="Home").click()
        page.wait_for_timeout(3000)
        R["bottom_nav"]["home_url"] = page.url
    except Exception as e:
        R["bottom_nav"]["home_error"] = str(e)[:150]
    home()
    try:
        page.get_by_role("button", name="All Tools").click()
        page.wait_for_timeout(4000)
        R["bottom_nav"]["all_tools_url"] = page.url
    except Exception as e:
        R["bottom_nav"]["all_tools_error"] = str(e)[:150]
    home()
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.get_by_role("button", name="Upload").click()
        ch = fc.value
        R["bottom_nav"]["upload_chooser"] = True
        ch.set_files([IMG])
        page.wait_for_timeout(6000)
        R["bottom_nav"]["upload_url"] = page.url
        shot("12_upload_canvas.png")
    except Exception as e:
        R["bottom_nav"]["upload_chooser"] = {"triggered": False, "error": str(e)[:200]}
    home()
    R["bottom_nav"]["generate_chooser"] = False
    try:
        with page.expect_file_chooser(timeout=3000) as fc:
            page.locator("nav.home-mobile-bottom-nav button[aria-label='Generate']").click()
        ch = fc.value
        ch.set_files([])
        R["bottom_nav"]["generate_chooser"] = True
    except Exception:
        R["bottom_nav"]["generate_chooser"] = False
    page.wait_for_timeout(4000)
    R["bottom_nav"]["generate_url"] = page.url
    shot("13_generate_canvas.png")
    home()
    try:
        page.locator("nav.home-mobile-bottom-nav button[aria-label='Pricing']").click()
        page.wait_for_timeout(4000)
        R["bottom_nav"]["pricing_url"] = page.url
    except Exception as e:
        R["bottom_nav"]["pricing_error"] = str(e)[:150]

    # ---- Damaged image upload via Upload ----
    home()
    try:
        with page.expect_file_chooser(timeout=5000) as fc:
            page.get_by_role("button", name="Upload").click()
        ch = fc.value
        ch.set_files([DAMAGED])
        page.wait_for_timeout(6000)
        R["bottom_nav"]["damaged_upload_url"] = page.url
        R["bottom_nav"]["damaged_upload_body"] = page.inner_text("body")[:400]
    except Exception as e:
        R["bottom_nav"]["damaged_upload_error"] = str(e)[:200]

    with open(os.path.join(TASK, "explore_interactions.json"), "w", encoding="utf-8") as f:
        json.dump(R, f, ensure_ascii=False, indent=2)
    print("DONE")
    print(json.dumps(R, ensure_ascii=False, indent=2)[:7000])
    browser.close()
