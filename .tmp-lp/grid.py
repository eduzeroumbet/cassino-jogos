from PIL import Image
import sys
suf = sys.argv[1]; w = int(sys.argv[2])
ks = ['fortune-tiger', 'fortune-rabbit', 'fortune-dragon', 'gates-of-olympus', 'sweet-bonanza', 'big-bass-splash', 'mines', 'index']
ims = [Image.open(f'.tmp-lp/{k}-{suf}.png') for k in ks]
ims = [i.resize((w, round(i.height * w / i.width))) for i in ims]
cols = 4; h = max(i.height for i in ims)
S = Image.new('RGB', (cols * (w + 6), 2 * (h + 6)))
for n, i in enumerate(ims): S.paste(i, ((n % cols) * (w + 6), (n // cols) * (h + 6)))
S.save(f'.tmp-lp/grid-{suf}.jpg', quality=82)
