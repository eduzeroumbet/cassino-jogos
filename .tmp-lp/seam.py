import os
from playwright.sync_api import sync_playwright
R = os.path.abspath('.')
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1440, 'height': 900})
    pg.goto(f'file://{R}/docs/fortune-ox.html'); pg.wait_for_timeout(2500)
    for n, css in (('nofilter', '.hero-ch{filter:none!important}'), ('nomask', '.hero-ch{-webkit-mask-image:none!important;mask-image:none!important}'),
                   ('noch', '.hero-ch{display:none!important}')):
        h = pg.add_style_tag(content=css); pg.wait_for_timeout(300)
        pg.screenshot(path=f'.tmp-lp/seam-{n}.png', clip={'x': 1100, 'y': 60, 'width': 340, 'height': 440})
        pg.evaluate('e => e.remove()', h)
    b.close()
