from PIL import Image
import glob, sys
ks = ['fortune-tiger', 'fortune-ox', 'fortune-rabbit', 'fortune-dragon', 'gates-of-olympus', 'sweet-bonanza', 'big-bass-splash']
extra = sys.argv[1:] or ['assets/img/{k}-hero-600.webp', 'assets/sites/cards/{k}.webp']
rows = []
for k in ks:
    fs = sorted(f for f in glob.glob(f'assets/acervo/{k}/*.webp') if not any(s in f for s in ('-600', '-800', '-400')))
    fs += [x.format(k=k) for x in extra]
    ims = []
    for f in fs:
        im = Image.open(f).convert('RGBA'); bg = Image.new('RGBA', im.size, (255, 0, 255, 255)); bg.alpha_composite(im)
        im = bg.convert('RGB'); im.thumbnail((260, 220)); ims.append(im)
    W = sum(i.width + 6 for i in ims); r = Image.new('RGB', (W, 226), (30, 30, 30)); x = 0
    for i in ims: r.paste(i, (x, 0)); x += i.width + 6
    rows.append(r)
S = Image.new('RGB', (max(r.width for r in rows), 226 * len(rows)), (0, 0, 0)); y = 0
for r in rows: S.paste(r, (0, y)); y += 226
S.save('.tmp-lp/sheet.jpg', quality=80); print(S.size)
