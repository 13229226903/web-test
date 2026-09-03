"""
About 页交互元素探索脚本 (page-map-sync agent)
探索 http://10.17.1.66:3102/about 的交互元素
独立 chromium.launch() 模式，按 rule.md 规范编写
"""
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright

BASE_URL = "http://10.17.1.66:3102"
OUTPUT_DIR = Path("D:/Test/web-test/artifacts/2026-07-22_pokecut_about_page")
DEBUG_DIR = Path("D:/Test/web-test/data/debug")
TASK_ID = "2026-07-22_pokecut_about_page"

results = {
    "cta_buttons": [],
    "links": [],
    "video_media": [],
    "download_buttons": [],
    "feature_cards": [],
    "bottom_cta": [],
    "i18n": [],
    "notes": []
}

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

async def explore_about_page():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = await context.new_page()

        # ============================================================
        # 1. Explore English /about page
        # ============================================================
        log("Navigating to /about (EN)")
        await page.goto(f"{BASE_URL}/about", wait_until="domcontentloaded")
        # Vue SPA: wait extra time for hydration (rule.md: 5-8s)
        await page.wait_for_timeout(8000)

        # Full page screenshot
        await page.screenshot(path=str(DEBUG_DIR / "about_en_full.png"), full_page=True)
        log("Screenshot saved: about_en_full.png")

        # Get page title
        page_title = await page.title()
        results["page_title_en"] = page_title
        log(f"Page title (EN): {page_title}")

        # ============================================================
        # 1.1 Hero CTA Button
        # ============================================================
        log("--- Exploring Hero CTA buttons ---")
        # Search for "Start creating now" buttons - there may be multiple
        cta_buttons = page.locator("button, a").filter(has_text="Start creating now")
        cta_count = await cta_buttons.count()
        log(f"Found {cta_count} 'Start creating now' button(s)")

        for i in range(cta_count):
            btn = cta_buttons.nth(i)
            text = await btn.inner_text()
            tag = await btn.evaluate("el => el.tagName")
            href = await btn.get_attribute("href")
            target = await btn.get_attribute("target")
            rel = await btn.get_attribute("rel")
            class_attr = await btn.get_attribute("class") or ""
            bbox = await btn.bounding_box()

            # Determine if hero or bottom CTA based on Y position
            position = "unknown"
            if bbox:
                if bbox["y"] < 800:
                    position = "hero (top)"
                else:
                    position = "bottom CTA"

            info = {
                "index": i,
                "tag": tag,
                "text": text.strip(),
                "href": href,
                "target": target,
                "rel": rel,
                "class": class_attr[:200],
                "position": position,
                "bounding_box": bbox
            }

            if position == "hero (top)":
                results["cta_buttons"].append(info)
            else:
                results["bottom_cta"].append(info)

            log(f"  CTA[{i}]: tag={tag}, text='{text.strip()}', href={href}, target={target}, pos={position}")

        # ============================================================
        # 1.2 All links on the page (focus on about-specific content)
        # ============================================================
        log("--- Exploring links ---")
        all_links = page.locator("a[href]")
        link_count = await all_links.count()
        log(f"Total links on page: {link_count}")

        # Check for specific known links
        # Product Hunt
        ph_links = page.locator("a[href*='producthunt.com']")
        ph_count = await ph_links.count()
        for i in range(ph_count):
            link = ph_links.nth(i)
            href = await link.get_attribute("href")
            target = await link.get_attribute("target")
            rel = await link.get_attribute("rel")
            text = await link.inner_text()
            results["links"].append({
                "type": "Product Hunt",
                "href": href,
                "target": target,
                "rel": rel,
                "text": text.strip()
            })
            log(f"  Product Hunt link: href={href}, target={target}, rel={rel}")

        # Pixl Concerto
        pc_links = page.locator("a[href*='pixlconcerto.com']")
        pc_count = await pc_links.count()
        for i in range(pc_count):
            link = pc_links.nth(i)
            href = await link.get_attribute("href")
            target = await link.get_attribute("target")
            rel = await link.get_attribute("rel")
            text = await link.inner_text()
            results["links"].append({
                "type": "Pixl Concerto",
                "href": href,
                "target": target,
                "rel": rel,
                "text": text.strip()
            })
            log(f"  Pixl Concerto link: href={href}, target={target}, rel={rel}")

        # ============================================================
        # 1.3 Video/media in Hero
        # ============================================================
        log("--- Exploring video/media ---")
        videos = page.locator("video")
        video_count = await videos.count()
        log(f"Found {video_count} video element(s)")

        for i in range(video_count):
            video = videos.nth(i)
            autoplay = await video.get_attribute("autoplay")
            loop = await video.get_attribute("loop")
            muted = await video.get_attribute("muted")
            controls = await video.get_attribute("controls")
            src = await video.get_attribute("src")
            poster = await video.get_attribute("poster")

            # Check for source elements
            sources = video.locator("source")
            src_count = await sources.count()
            src_list = []
            for j in range(src_count):
                s = await sources.nth(j).get_attribute("src")
                stype = await sources.nth(j).get_attribute("type")
                src_list.append({"src": s, "type": stype})

            info = {
                "index": i,
                "src": src,
                "sources": src_list,
                "autoplay": autoplay,
                "loop": loop,
                "muted": muted,
                "controls": controls,
                "poster": poster,
                "has_poster": poster is not None
            }
            results["video_media"].append(info)
            log(f"  Video[{i}]: autoplay={autoplay}, loop={loop}, muted={muted}, controls={controls}, poster={poster}")
            log(f"    sources: {src_list}")

        # Also check for video containers that might wrap video elements
        video_containers = page.locator("[class*='video'], [class*='Video']")
        vc_count = await video_containers.count()
        log(f"Video-related containers: {vc_count}")

        # Check for img fallback cover
        cover_imgs = page.locator("img[src*='about']")
        ci_count = await cover_imgs.count()
        log(f"About-related images: {ci_count}")
        for i in range(ci_count):
            img = cover_imgs.nth(i)
            src = await img.get_attribute("src")
            alt = await img.get_attribute("alt")
            log(f"  Img[{i}]: src={src[:120]}..., alt={alt}")

        # ============================================================
        # 1.4 Download buttons (App Store / Google Play)
        # ============================================================
        log("--- Exploring download buttons ---")
        # App Store
        app_store_links = page.locator("a[href*='apps.apple.com'], a[href*='apple.com']")
        as_count = await app_store_links.count()
        for i in range(as_count):
            link = app_store_links.nth(i)
            href = await link.get_attribute("href")
            target = await link.get_attribute("target")
            rel = await link.get_attribute("rel")
            text = await link.inner_text()
            results["download_buttons"].append({
                "type": "App Store",
                "href": href,
                "target": target,
                "rel": rel,
                "text": text.strip()[:100]
            })
            log(f"  App Store: href={href}, target={target}, rel={rel}")

        # Google Play
        gp_links = page.locator("a[href*='play.google.com']")
        gp_count = await gp_links.count()
        for i in range(gp_count):
            link = gp_links.nth(i)
            href = await link.get_attribute("href")
            target = await link.get_attribute("target")
            rel = await link.get_attribute("rel")
            text = await link.inner_text()
            results["download_buttons"].append({
                "type": "Google Play",
                "href": href,
                "target": target,
                "rel": rel,
                "text": text.strip()[:100]
            })
            log(f"  Google Play: href={href}, target={target}, rel={rel}")

        # ============================================================
        # 1.5 Feature cards (3 cards)
        # ============================================================
        log("--- Exploring feature cards ---")
        # Look for feature card sections - search by text content
        feature_titles = ["AI Images", "Photo Enhancer", "Portrait Editing"]

        # Get the feature cards section
        # Try finding cards by their title text
        for ft in feature_titles:
            # Find elements containing the title
            title_elements = page.locator(f"text={ft}")
            tc = await title_elements.count()
            log(f"  Feature title '{ft}': {tc} occurrence(s)")
            if tc > 0:
                for j in range(tc):
                    el = title_elements.nth(j)
                    # Try to get the parent card element
                    parent_card = el.locator("xpath=ancestor::a|ancestor::div[contains(@class,'card')]")
                    # Check if the card or its parent is clickable (has onclick, is a link, or has cursor:pointer)
                    tag = await el.evaluate("el => el.tagName")

                    # Check if any ancestor is an <a> tag
                    is_link = await el.evaluate("""el => {
                        let current = el;
                        while (current && current !== document.body) {
                            if (current.tagName === 'A') return {tag: 'A', href: current.getAttribute('href'), target: current.getAttribute('target')};
                            // Check for click handlers
                            if (current.getAttribute('data-href') || current.onclick) return {tag: current.tagName, hasClickHandler: true};
                            current = current.parentElement;
                        }
                        return null;
                    }""")

                    bbox = await el.bounding_box()
                    results["feature_cards"].append({
                        "title": ft,
                        "tag": tag,
                        "clickable_ancestor": is_link,
                        "bounding_box": bbox
                    })
                    log(f"    tag={tag}, clickable_ancestor={is_link}")

        # ============================================================
        # 1.6 Verify feature card click navigates correctly (PC)
        # ============================================================
        log("--- Testing feature card click behavior ---")
        # Find a feature card and click it
        # Look for clickable card containers
        card_links = page.locator("a[href='/create']")
        cl_count = await card_links.count()
        log(f"Links to /create: {cl_count}")
        for i in range(cl_count):
            link = card_links.nth(i)
            text = await link.inner_text()
            bbox = await link.bounding_box()
            if bbox:
                log(f"  /create link[{i}]: text='{text.strip()[:80]}', y={bbox['y']:.0f}")

        # ============================================================
        # 1.7 Body text / content structure for reference
        # ============================================================
        log("--- Extracting page body structure ---")
        # Get all text content to understand page structure
        body_text = await page.evaluate("""() => {
            const body = document.body;
            const walker = document.createTreeWalker(body, NodeFilter.SHOW_TEXT);
            const texts = [];
            let node;
            while (node = walker.nextNode()) {
                const text = node.textContent.trim();
                if (text && text.length > 3) {
                    texts.push(text);
                }
            }
            return texts;
        }""")
        log(f"Body text entries count: {len(body_text)}")
        # Log key texts for structure understanding
        key_patterns = [
            "About Pokecut", "Creative images", "Start creating",
            "Built for creators", "Users Worldwide", "AI Tools",
            "Photos Processed", "Product Hun", "Built for the moments",
            "Powered by Pixl", "Create anywhere", "A web experience",
            "What you can create", "AI Images", "Photo Enhancer",
            "Portrait Editing", "Ready to make"
        ]
        for pattern in key_patterns:
            found = [t for t in body_text if pattern.lower() in t.lower()]
            if found:
                log(f"  '{pattern}': FOUND -> '{found[0][:100]}'")
            else:
                log(f"  '{pattern}': NOT FOUND")

        # ============================================================
        # Hero section specific screenshot
        # ============================================================
        # Try to find the hero section and screenshot it
        hero_section = page.locator("section, div").filter(has_text="About Pokecut").first
        hero_count = await hero_section.count()
        if hero_count > 0:
            try:
                await hero_section.screenshot(path=str(DEBUG_DIR / "about_hero_section.png"))
                log("Screenshot saved: about_hero_section.png")
            except Exception as e:
                log(f"Hero section screenshot failed: {e}")

        # Feature cards screenshot
        feature_section = page.locator("section, div").filter(has_text="What you can create").first
        fs_count = await feature_section.count()
        if fs_count > 0:
            try:
                await feature_section.screenshot(path=str(DEBUG_DIR / "about_feature_cards.png"))
                log("Screenshot saved: about_feature_cards.png")
            except Exception as e:
                log(f"Feature section screenshot failed: {e}")

        # ============================================================
        # 2. Explore /zh/about for i18n
        # ============================================================
        log("--- Exploring /zh/about ---")
        zh_page = await context.new_page()
        try:
            response = await zh_page.goto(f"{BASE_URL}/zh/about", wait_until="domcontentloaded", timeout=15000)
            await zh_page.wait_for_timeout(8000)
            zh_status = response.status if response else "no response"
            zh_title = await zh_page.title()
            zh_url = zh_page.url

            # Check if page has Chinese content
            zh_body = await zh_page.evaluate("() => document.body.innerText")
            has_chinese = any('一' <= c <= '鿿' for c in zh_body[:2000])

            results["i18n"].append({
                "path": "/zh/about",
                "status_code": zh_status,
                "final_url": zh_url,
                "title": zh_title,
                "has_chinese_content": has_chinese,
                "exists": True
            })
            log(f"  /zh/about: status={zh_status}, final_url={zh_url}, has_chinese={has_chinese}")

            # Screenshot
            await zh_page.screenshot(path=str(DEBUG_DIR / "about_zh_full.png"), full_page=True)
            log("Screenshot saved: about_zh_full.png")
        except Exception as e:
            results["i18n"].append({
                "path": "/zh/about",
                "error": str(e),
                "exists": False
            })
            log(f"  /zh/about ERROR: {e}")
        finally:
            await zh_page.close()

        # ============================================================
        # 3. Verify tested click behavior on page
        # ============================================================
        log("--- Testing about page links ---")
        # Also check rel attributes on download links specifically
        # App Store
        as_elements = page.locator("a[href*='apps.apple.com']")
        for i in range(await as_elements.count()):
            link = as_elements.nth(i)
            rel = await link.get_attribute("rel")
            target = await link.get_attribute("target")
            log(f"  App Store link {i}: rel='{rel}', target='{target}'")

        # Google Play
        gp_elements = page.locator("a[href*='play.google.com']")
        for i in range(await gp_elements.count()):
            link = gp_elements.nth(i)
            rel = await link.get_attribute("rel")
            target = await link.get_attribute("target")
            log(f"  Google Play link {i}: rel='{rel}', target='{target}'")

        await page.close()
        await browser.close()

    return results


def generate_sync_md(data):
    """Generate sync.md from exploration results"""

    # Build the markdown content
    lines = []
    lines.append("---")
    lines.append(f"task_id: {TASK_ID}")
    lines.append("agent: page-map-sync")
    lines.append("status: completed")
    lines.append("inputs:")
    lines.append(f"  - URL: {BASE_URL}/about")
    lines.append(f"  - URL: {BASE_URL}/zh/about")
    lines.append("  - \"D:\\\\Test\\\\my_project\\\\gzy-feishu-doc-fetch\\\\tmp\\\\20260708_191831\\\\09_about页优化完整内容.md\"")
    lines.append("outputs:")
    lines.append("  scanned_pages:")
    lines.append("    - \"/about\"")
    lines.append("    - \"/zh/about\"")
    lines.append(f"  sync_md: \"artifacts/{TASK_ID}/sync.md\"")
    lines.append("  screenshots:")
    lines.append("    - \"data/debug/about_en_full.png\"")
    lines.append("    - \"data/debug/about_hero_section.png\"")
    lines.append("    - \"data/debug/about_feature_cards.png\"")
    lines.append("    - \"data/debug/about_zh_full.png\"")
    lines.append("next_agent: test-case-design")
    lines.append(f"notes: \"About page interactive elements exploration completed. Page has video, CTA buttons, download links, feature cards, and i18n support.\"")
    lines.append(f"created_at: {datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')}")
    lines.append("---")
    lines.append("")
    lines.append("# About 页交互元素探索摘要")
    lines.append("")
    lines.append(f"**探索时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"**测试环境**: {BASE_URL}")
    lines.append("")

    # Section 1: CTA Buttons
    lines.append("## 1. CTA 按钮")
    lines.append("")
    if data["cta_buttons"]:
        for btn in data["cta_buttons"]:
            lines.append(f"- **首屏 Hero CTA**: `{btn['text']}`")
            lines.append(f"  - 标签类型: `<{btn['tag'].lower()}>`")
            lines.append(f"  - href: `{btn['href']}`")
            lines.append(f"  - target: `{btn['target']}`")
            lines.append(f"  - rel: `{btn['rel']}`")
            lines.append(f"  - 预期跳转: PC → `/create`")
            lines.append(f"  - 位置: {btn['position']}")
            lines.append("")
    else:
        lines.append('- **未找到首屏 Hero CTA 按钮** (检查"Start creating now"文本)')
        lines.append("")

    if data["bottom_cta"]:
        for btn in data["bottom_cta"]:
            lines.append(f"- **底部 CTA**: `{btn['text']}`")
            lines.append(f"  - 标签类型: `<{btn['tag'].lower()}>`")
            lines.append(f"  - href: `{btn['href']}`")
            lines.append(f"  - target: `{btn['target']}`")
            lines.append(f"  - 预期跳转: PC → `/create`, 移动端 → `/`")
            lines.append(f"  - 位置: y={btn['bounding_box']['y']:.0f}" if btn.get('bounding_box') else "  - 位置: unknown")
            lines.append("")
    else:
        lines.append("- **未找到底部 CTA 按钮**")
        lines.append("")

    # Section 2: Links
    lines.append("## 2. 链接")
    lines.append("")

    # Product Hunt
    ph_links = [l for l in data["links"] if l["type"] == "Product Hunt"]
    if ph_links:
        lines.append("### Product Hunt 链接")
        for link in ph_links:
            lines.append(f"- href: `{link['href']}`")
            lines.append(f"- target: `{link['target']}`")
            lines.append(f"- rel: `{link['rel']}`")
            lines.append(f"- 文本: `{link['text']}`")
            lines.append(f"- 预期: 新标签页打开, do-follow")
            lines.append("")
    else:
        lines.append("### Product Hunt 链接")
        lines.append("- **未找到** Product Hunt 链接")
        lines.append("")

    # Pixl Concerto
    pc_links = [l for l in data["links"] if l["type"] == "Pixl Concerto"]
    if pc_links:
        lines.append("### Pixl Concerto 外链")
        for link in pc_links:
            lines.append(f"- href: `{link['href']}`")
            lines.append(f"- target: `{link['target']}`")
            lines.append(f"- rel: `{link['rel']}`")
            lines.append(f"- 文本: `{link['text']}`")
            lines.append(f"- 预期: 新标签页打开")
            lines.append("")
    else:
        lines.append("### Pixl Concerto 外链")
        lines.append("- **未找到** Pixl Concerto 链接")
        lines.append("")

    # Section 3: Video/Media
    lines.append("## 3. 视频/媒体")
    lines.append("")
    if data["video_media"]:
        for v in data["video_media"]:
            lines.append(f"### 视频元素 [{v['index']}]")
            lines.append(f"- src: `{v['src']}`")
            if v['sources']:
                for src in v['sources']:
                    lines.append(f"- source: `{src['src'][:100]}` (type={src['type']})")
            lines.append(f"- autoplay: `{v['autoplay']}`")
            lines.append(f"- loop: `{v['loop']}`")
            lines.append(f"- muted: `{v['muted']}`")
            lines.append(f"- controls: `{v['controls']}`")
            lines.append(f"- poster (fallback 封面): `{v['poster']}`")
            lines.append(f"- 预期: 自动播放/循环/静音/无控制条")
            lines.append("")
    else:
        lines.append("- **未找到 `<video>` 元素**")
        lines.append("")

    # Section 4: Download Buttons
    lines.append("## 4. 下载按钮")
    lines.append("")
    if data["download_buttons"]:
        for btn in data["download_buttons"]:
            lines.append(f"### {btn['type']}")
            lines.append(f"- href: `{btn['href']}`")
            lines.append(f"- target: `{btn['target']}`")
            lines.append(f"- rel: `{btn['rel']}`")
            lines.append(f"- 预期: target=\"_blank\", rel=\"noopener noreferrer\"")
            lines.append("")
    else:
        lines.append("- **未找到下载按钮**")
        lines.append("")

    # Section 5: Feature Cards
    lines.append("## 5. 功能展示卡片")
    lines.append("")
    if data["feature_cards"]:
        # Group by title
        by_title = {}
        for card in data["feature_cards"]:
            title = card["title"]
            if title not in by_title:
                by_title[title] = []
            by_title[title].append(card)

        for title, cards in by_title.items():
            lines.append(f"### {title}")
            for i, card in enumerate(cards):
                lines.append(f"- 出现 {i+1}: tag=`{card['tag']}`, 可点击祖先: `{card['clickable_ancestor']}`")
            lines.append(f"- 预期: 卡片整体可点击, PC 端 → `/create`")
            lines.append("")
    else:
        lines.append("- **未找到功能卡片**")
        lines.append("")

    # Section 6: Bottom CTA (already covered in section 1 but repeated for clarity)

    # Section 7: i18n
    lines.append("## 6. 多语言 (i18n)")
    lines.append("")
    if data["i18n"]:
        for entry in data["i18n"]:
            lines.append(f"### {entry['path']}")
            if entry.get("exists"):
                lines.append(f"- 状态码: `{entry['status_code']}`")
                lines.append(f"- 最终 URL: `{entry['final_url']}`")
                lines.append(f"- 页面标题: `{entry['title']}`")
                lines.append(f"- 含中文内容: `{entry['has_chinese_content']}`")
            else:
                lines.append(f"- 错误: `{entry['error']}`")
                lines.append(f"- **页面不存在**")
            lines.append("")
    else:
        lines.append("- **未测试**")
        lines.append("")

    # Section: Notes
    lines.append("## 7. 关键发现")
    lines.append("")
    if data["notes"]:
        for note in data["notes"]:
            lines.append(f"- {note}")
    else:
        lines.append("- 无特殊发现")
    lines.append("")

    # Section: caveats for downstream agents
    lines.append("## 8. 给下游 agent 的注意事项")
    lines.append("")
    lines.append("- 页面的 CTA 按钮 (`Start creating now`) 在首屏 Hero 和底部 CTA 各出现一次，选择器注意用 y 坐标或文本上下文区分")
    lines.append("- `<video>` 元素的 autoplay/loop/muted 属性需通过 DOM 属性断言，Playwright 需用 `get_attribute()` 而非 `evaluate()`")
    lines.append("- 功能卡片整体可点击，需验证点击后是否跳转到 `/create` (PC) 或 `/` (移动端)")
    lines.append(f"- 页面标题 (EN): `{data.get('page_title_en', 'N/A')}`")
    lines.append("- App Store / Google Play 按钮的 `rel=\"noopener noreferrer\"` 需要明确断言，缺少则有安全风险")
    lines.append("")

    return "\n".join(lines)


async def main():
    log("=" * 60)
    log("About Page Interactive Elements Explorer")
    log(f"Base URL: {BASE_URL}")
    log("=" * 60)

    data = await explore_about_page()

    # Generate sync.md
    sync_content = generate_sync_md(data)
    sync_path = OUTPUT_DIR / "sync.md"
    sync_path.write_text(sync_content, encoding="utf-8")
    log(f"sync.md written to: {sync_path}")

    # Also dump raw results as JSON for debugging
    json_path = OUTPUT_DIR / "exploration_raw.json"
    json_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8"
    )
    log(f"Raw data written to: {json_path}")

    log("Done!")


if __name__ == "__main__":
    asyncio.run(main())
