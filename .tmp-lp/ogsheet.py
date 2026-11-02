from PIL import Image
import glob
fs = sorted(glob.glob('assets/og/*.jpg'))
S = Image.new('RGB', (1200, 315 * ((len(fs) + 1) // 2)), (0, 0, 0))
for i, f in enumerate(fs):
    im = Image.open(f).resize((600, 315)); S.paste(im, ((i % 2) * 600, (i // 2) * 315))
S.save('.tmp-lp/og.jpg', quality=80)
