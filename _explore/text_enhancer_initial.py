# -*- coding: utf-8 -*-
"""Safe read-only exploration for /tools/ai-image-text-enhancer."""
import json
import pathlib
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(r"D:\Test\web-test")
OUT = ROOT / "artifacts" / "2026-08-26_pokecut_text_enhancer"
OUT.mkdir(parents=True, exist_ok=True)
URL = "http://10.17.1.66:3001/tools/ai-image-text-enhancer"

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    page.goto(URL, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(8000)
    page.screenshot(path=str(OUT / "explore_desktop_initial.png"), full_page=True)

    meta = page.evaluate("""({
      url: location.href,
      title: document.title,
      lang: document.documentElement.lang
    })""")
    body_text = page.evaluate("document.body.innerText")

    headings = page.evaluate("""Array.prototype.map.call(
      document.querySelectorAll('h1,h2,h3'),
      function(el) {
        var r = el.getBoundingClientRect();
        return {tag: el.tagName.toLowerCase(), text: (el.innerText || el.textContent || '').trim(), x: r.x, y: r.y, width: r.width, height: r.height};
      }
    ).filter(function(x) { return x.width > 0 && x.height > 0; })""")

    interactive = page.evaluate("""Array.prototype.filter.call(
      document.querySelectorAll('button,a,input,textarea,select,label,[role="button"],[role="checkbox"],[role="radio"],[tabindex]'),
      function(el) {
        var r = el.getBoundingClientRect();
        var s = window.getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.display !== 'none' && s.visibility !== 'hidden';
      }
    ).map(function(el) {
      var r = el.getBoundingClientRect();
      var attrs = {};
      ['id','name','type','placeholder','aria-label','aria-disabled','disabled','href','data-testid'].forEach(function(k) {
        var v = el.getAttribute(k);
        if (v !== null) attrs[k] = v;
      });
      return {tag: el.tagName.toLowerCase(), text: (el.innerText || el.textContent || '').trim().slice(0,300), attrs: attrs,
              rect: {x: Math.round(r.x), y: Math.round(r.y), width: Math.round(r.width), height: Math.round(r.height)}};
    })""")

    file_inputs = page.evaluate("""Array.prototype.map.call(document.querySelectorAll('input[type=file]'), function(el) {
      var r = el.getBoundingClientRect();
      return {id: el.id, name: el.name, accept: el.accept, multiple: el.multiple,
              visible: r.width > 0 && r.height > 0};
    })""")

    images = page.evaluate("""Array.prototype.filter.call(document.querySelectorAll('img'), function(el) {
      var r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0;
    }).map(function(el) {
      var r = el.getBoundingClientRect();
      return {src: el.currentSrc || el.src, alt: el.alt, x: Math.round(r.x), y: Math.round(r.y),
              width: Math.round(r.width), height: Math.round(r.height), naturalWidth: el.naturalWidth, naturalHeight: el.naturalHeight};
    })""")

    data = dict(meta)
    data.update({
        "bodyText": body_text,
        "headings": headings,
        "interactive": interactive,
        "fileInputs": file_inputs,
        "images": images,
    })
    with open(OUT / "explore_desktop_initial.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    with open(OUT / "explore_desktop_initial.txt", "w", encoding="utf-8") as f:
        f.write(body_text)
    print(json.dumps({"meta": meta, "headings": headings, "fileInputs": file_inputs,
                      "interactiveCount": len(interactive), "bodyPreview": body_text[:4000]},
                     ensure_ascii=False, indent=2))
    browser.close()
