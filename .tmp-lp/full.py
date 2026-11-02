import os
from playwright.sync_api import sync_playwright
R = os.path.abspath('.')
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True)
    for k in ('fortune-tiger', 'fortune-ox'):
        pg.goto(f'file://{R}/docs/{k}.html'); pg.wait_for_timeout(500)
        for y in range(0, 12000, 600): pg.evaluate(f'window.scrollTo(0,{y})'); pg.wait_for_timeout(120)
        pg.wait_for_timeout(800)
        print(k, pg.evaluate('Array.from(document.images).filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src)'))
        for sel in ('#personagem', '.rail'):
            pg.locator(sel).first.scroll_into_view_if_needed(); pg.wait_for_timeout(400)
            pg.locator(sel).first.screenshot(path=f'.tmp-lp/{k}-{sel.strip("#.")}.png')
    b.close()
