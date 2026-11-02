import os, sys
from playwright.sync_api import sync_playwright
R = os.path.abspath('.')
pages = sys.argv[1:] or ['fortune-tiger', 'fortune-ox', 'fortune-rabbit', 'fortune-dragon', 'gates-of-olympus', 'sweet-bonanza', 'big-bass-splash', 'mines', 'index']
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, vp, mob in (('m', {'width': 390, 'height': 844}, True), ('d', {'width': 1440, 'height': 900}, False)):
        ctx = b.new_context(viewport=vp, device_scale_factor=1, is_mobile=mob, java_script_enabled=False)
        pg = ctx.new_page()
        for k in pages:
            pg.goto(f'file://{R}/docs/{k}.html'); pg.wait_for_timeout(2500)
            pg.screenshot(path=f'.tmp-lp/{k}-{name}.png')
            broken = pg.evaluate('Array.from(document.images).filter(i=>i.loading!=="lazy"&&(!i.complete||!i.naturalWidth)).map(i=>i.currentSrc||i.src)')
            if broken: print(k, name, 'imagens sem carregar:', broken)
        ctx.close()
    b.close()
print('ok')
