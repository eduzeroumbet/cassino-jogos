from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, json
D='../../projetos/new-bet/demandas/aaa9acd7/'
F='../../projetos/new-bet/demandas/1ece930a/fontes/'
games = {'fortune-tiger':('hero-fortune-tiger','pgsoft-126','Fortune Tiger','#F5B942'),
 'fortune-rabbit':('hero-fortune-rabbit','pgsoft-1543462','Fortune Rabbit','#FF7AA8'),
 'fortune-ox':('hero-fortune-ox','pgsoft-98','Fortune Ox','#FF5A3D'),
 'fortune-dragon':('hero-fortune-dragon','pgsoft-1695365','Fortune Dragon','#FF3D5A'),
 'gates-of-olympus':('hero-gates-olympus','pragmatic-vs20olympgate','Gates of Olympus','#C9A2FF'),
 'sweet-bonanza':('hero-sweet-bonanza','pragmatic-vs20fruitsw','Sweet Bonanza','#FF6FB5'),
 'big-bass-splash':('hero-big-bass','pragmatic-vs10txbigbass','Big Bass Splash','#3DD6C4'),
 'mines':('hero-mines','galaxsys-original-12540','Turbo Mines','#FF3D5A')}
os.makedirs('assets/img', exist_ok=True)
for k,(hero,slug,title,acc) in games.items():
    im = Image.open(D+hero+'.png').convert('RGB')
    for w in (896, 600):
        im.resize((w, round(1200*w/896)), Image.LANCZOS).save(f'assets/img/{k}-hero-{w}.webp', 'WEBP', quality=68, method=6)
    # desktop wide: blurred extension
    th = Image.open(D+'assets_src/'+slug+'.webp').convert('RGB')
    th.save(f'assets/img/{k}-thumb.webp','WEBP',quality=80, method=6)
    # OG 1200x630
    og = Image.new('RGB',(1200,630),(11,20,48))
    bg = im.resize((1200,1607)).crop((0,300,1200,930)).filter(ImageFilter.GaussianBlur(2))
    og.paste(bg,(0,0))
    ov = Image.new('RGBA',(1200,630),(0,0,0,0)); d=ImageDraw.Draw(ov)
    for x in range(1200):
        a = int(235*max(0,1-x/760)); d.line([(x,0),(x,630)], fill=(11,20,48,a))
    og = Image.alpha_composite(og.convert('RGBA'), ov)
    d = ImageDraw.Draw(og)
    fb = ImageFont.truetype(F+'Montserrat-Black.ttf', 76); fs = ImageFont.truetype(F+'Montserrat-SemiBold.ttf', 30)
    words = title.split(); lines = [' '.join(words[:1]), ' '.join(words[1:])] if len(title)>12 else [title]
    y=170
    d.rounded_rectangle((70,100,70+330,146), 23, fill=acc)
    d.text((92,108),'GUIA DO JOGO', font=fs, fill=(11,20,48))
    for ln in lines:
        d.text((70,y), ln.upper(), font=fb, fill=(255,255,255)); y+=88
    d.text((70,y+20),'RTP, recursos e como jogar no celular', font=fs, fill=(244,238,230))
    og.convert('RGB').save(f'assets/img/{k}-og.jpg','JPEG',quality=82, optimize=True)
    print(k, os.path.getsize(f'assets/img/{k}-hero-896.webp')//1024, os.path.getsize(f'assets/img/{k}-hero-600.webp')//1024, 'KB')
json.dump(games, open('games_map.json','w'))
