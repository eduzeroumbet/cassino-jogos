#!/usr/bin/env python3
"""Gera os 6 sites dos domínios .win a partir de data/sites.json, data/catalogo-plataforma.json e data/games.json.
Cada site tem layout, tipografia e paleta próprios e é gravado em dist-sites/<dominio>/ (index.html, 404.html, CNAME,
robots.txt, .nojekyll e só os assets usados).
Imagens (Pillow, só quando faltam ou com --imagens): capas leves assets/catalogo-web/<slug>-240.webp,
OG 1200x630 sem texto e artes reduzidas em assets/sites/<chave>/.
Uso: python3 build_sites.py [--imagens]"""
import json, os, re, sys, shutil, html
from build import webp_size

R = os.path.dirname(os.path.abspath(__file__))
GJ = json.load(open(os.path.join(R, 'data/games.json'), encoding='utf-8'))
S = GJ['site']; GAMES = {g['slug']: g for g in GJ['games']}
SJ = json.load(open(os.path.join(R, 'data/sites.json'), encoding='utf-8'))
C = SJ['comum']; F = SJ['fichas']; SITES = SJ['sites']; P = C['paths']
CAT = {i['slug']: i for i in json.load(open(os.path.join(R, 'data/catalogo-plataforma.json'), encoding='utf-8'))}
BASE = S['base'].rstrip('/'); BRAND = S['brand']; GA = S.get('ga4', '')
OUT = os.path.join(R, 'dist-sites')
FORCE = '--imagens' in sys.argv
e = lambda s: html.escape(str(s), quote=True)
DASH = ('—', '–')

# ---------------------------------------------------------------- dados dos jogos

def jogo(slug):
    """Item do catálogo. Jogo indisponível (Aviator da Spribe) nunca vira link."""
    c = CAT[slug]
    assert c.get('disponivel', True), f'{slug} não está disponível na plataforma'
    return c

def nome(slug):
    return C['nomes'].get(slug, CAT[slug]['name'])

def prov(slug):
    return C['provedores'].get(CAT[slug]['provider_code'], CAT[slug]['prov'])

def ficha(slug):
    return F.get(slug, {})

def num(v, dec=2):
    return f'{v:,.{dec}f}'.replace(',', 'X').replace('.', ',').replace('X', '.')

def rtp(slug):
    f = ficha(slug)
    return f'{f.get("rtp_prefixo", "")}{num(f["rtp"])}%' if f.get('rtp') else None

def maxw(slug):
    f = ficha(slug)
    return f'{num(f["max"], 0)}x' if f.get('max') else None

def utm(s, path, pos):
    sep = '&' if '?' in path else '?'
    return f'{BASE}{path}{sep}utm_source=site&utm_medium=landing&utm_campaign={s["chave"]}&utm_content={pos}'

def play(s, slug, pos):
    return utm(s, jogo(slug)['url'], pos)

# ---------------------------------------------------------------- imagens

def pil():
    from PIL import Image, ImageDraw, ImageFilter
    return Image, ImageDraw, ImageFilter

def web(slug):
    """Capa leve (240 px, WebP q72) gerada a partir da capa do catálogo (300x350)."""
    jogo(slug)
    p = f'assets/catalogo-web/{slug}-240.webp'
    if FORCE or not os.path.exists(os.path.join(R, p)):
        Image, _, _ = pil()
        os.makedirs(os.path.join(R, 'assets/catalogo-web'), exist_ok=True)
        im = Image.open(os.path.join(R, CAT[slug]['thumb'])).convert('RGB')
        im.resize((240, 280), Image.LANCZOS).save(os.path.join(R, p), 'WEBP', quality=72, method=6)
    return p

def reduzida(src, chave, nome_arq, w):
    """Arte reduzida para a largura w (WebP q78, mantém transparência) em assets/sites/<chave>/."""
    p = f'assets/sites/{chave}/{nome_arq}.webp'
    if FORCE or not os.path.exists(os.path.join(R, p)):
        Image, _, _ = pil()
        os.makedirs(os.path.join(R, f'assets/sites/{chave}'), exist_ok=True)
        im = Image.open(os.path.join(R, src))
        im = im.convert('RGBA' if im.mode in ('RGBA', 'LA', 'P') else 'RGB')
        if im.width > w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        im.save(os.path.join(R, p), 'WEBP', quality=78, method=6)
    return p

def hexrgb(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def og_image(s):
    """OG 1200x630 sem texto: fundo em degradê da paleta, capas inclinadas e, se houver, o personagem."""
    p = f'assets/sites/{s["chave"]}/og.jpg'
    if not FORCE and os.path.exists(os.path.join(R, p)): return p
    Image, ImageDraw, ImageFilter = pil()
    W, H = 1200, 630; o = s['og']
    a, b = hexrgb(o['fundo'][0]), hexrgb(o['fundo'][1])
    g = Image.linear_gradient('L')
    mask = Image.blend(g.resize((W, H)), g.rotate(90).transpose(Image.FLIP_LEFT_RIGHT).resize((W, H)), .5)  # diagonal
    im = Image.composite(Image.new('RGB', (W, H), b), Image.new('RGB', (W, H), a), mask).convert('RGBA')
    deco = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(deco)
    for x, y, r in ((160, 90, 220), (1040, 560, 300), (700, 40, 120)):
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, 255, 255, 22))
    im = Image.alpha_composite(im, deco)
    capas = o['capas']; char = o.get('personagem')
    area = 700 if char else W
    step = (area - 120) / max(1, len(capas))
    for i, slug in enumerate(capas):
        c = Image.open(os.path.join(R, CAT[slug]['thumb'])).convert('RGBA').resize((330, 385), Image.LANCZOS)
        m = Image.new('L', c.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, c.width - 1, c.height - 1), 26, fill=255)
        c.putalpha(m)
        ang = (-7, 5, -3, 6)[i % 4]
        c = c.rotate(ang, expand=True, resample=Image.BICUBIC)
        x = int(60 + i * step + (step - c.width) / 2) if len(capas) > 1 else int((area - c.width) / 2)
        y = (H - c.height) // 2 + (18 if i % 2 else -18)
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.paste((0, 0, 0, 120), (x + 12, y + 18), c.split()[3])
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(14)))
        im.alpha_composite(c, (x, y))
    if char:
        ch = Image.open(os.path.join(R, char)).convert('RGBA')
        h = 600; ch = ch.resize((round(ch.width * h / ch.height), h), Image.LANCZOS)
        im.alpha_composite(ch, (min(W - ch.width - 20, 720), H - h))
    os.makedirs(os.path.dirname(os.path.join(R, p)), exist_ok=True)
    im.convert('RGB').save(os.path.join(R, p), 'JPEG', quality=84, optimize=True, progressive=True)
    return p

def capa(slug, alt=None, lazy=True, cls='', eager=False):
    pr = ' fetchpriority="high"' if eager else (' loading="lazy"' if lazy else '')
    c = f' class="{cls}"' if cls else ''
    return f'<img{c} src="{web(slug)}" width="240" height="280" alt="{e(alt if alt is not None else "Capa do " + nome(slug))}" decoding="async"{pr}>'

def arte(p, alt, cls='', lazy=True, eager=False):
    w, h = webp_size(os.path.join(R, p))
    pr = ' fetchpriority="high"' if eager else (' loading="lazy"' if lazy else '')
    c = f' class="{cls}"' if cls else ''
    return f'<img{c} src="{p}" width="{w}" height="{h}" alt="{e(alt)}" decoding="async"{pr}>'

# ---------------------------------------------------------------- peças comuns

BASECSS = ('*,*::before,*::after{box-sizing:border-box}html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}body{margin:0}'
           'img{max-width:100%;height:auto;display:block}a{color:inherit}h1,h2,h3,p,ol,ul,dl,dd,figure{margin:0}button{font:inherit;cursor:pointer}'
           '.sr{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}'
           '.skip{position:absolute;left:12px;top:-60px;z-index:99;padding:10px 14px;background:#000;color:#fff;border-radius:8px}.skip:focus{top:12px}'
           ':focus-visible{outline:3px solid var(--focus,#1A73E8);outline-offset:3px}'
           '@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*::before,*::after{animation:none!important;transition:none!important}}')

FOOTCSS = ('.ft{padding:40px 20px calc(40px + env(safe-area-inset-bottom));font-size:14px;line-height:1.6}.ft-in{max-width:1120px;margin:0 auto;display:grid;gap:20px}'
           '.ft-guias{display:flex;flex-wrap:wrap;gap:8px 10px;align-items:center}.ft-guias span{font-weight:700;margin-right:6px}'
           '.ft-guias a{padding:8px 12px;border-radius:999px;text-decoration:none;border:1px solid currentColor;min-height:40px;display:inline-flex;align-items:center}'
           '.ft-rg{display:flex;gap:14px;align-items:flex-start}.ft-18{flex:none;display:grid;place-items:center;width:46px;height:46px;border-radius:50%;border:2px solid currentColor;font-weight:800}'
           '.ft-docs{display:flex;flex-wrap:wrap;gap:6px 18px}.ft-docs a{min-height:40px;display:inline-flex;align-items:center}.ft-nota{opacity:.85}')

def head(s, css, preload=None, extra=''):
    url = f'https://{s["dominio"]}/'
    og = f'{url}{og_image(s)}'
    cor = list(s['cores'].values())[0]
    fav = (cor if s['estilo'] != 'revista' else s['cores']['acento']).replace('#', '%23')
    pl = f'<link rel="preload" as="image" href="{preload}" fetchpriority="high">' if preload else ''
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(s['titulo'])}</title><meta name="description" content="{e(s['descricao'])}"><meta name="robots" content="noindex,nofollow">
<meta name="theme-color" content="{cor}"><link rel="canonical" href="{url}">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:site_name" content="{e(s['nome'])}">
<meta property="og:title" content="{e(s['titulo'])}"><meta property="og:description" content="{e(s['descricao'])}">
<meta property="og:image" content="{og}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:url" content="{url}">
<meta name="twitter:card" content="summary_large_image">{pl}{extra}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='8' fill='{fav}'/%3E%3C/svg%3E">
<style>{BASECSS}{FOOTCSS}{css}</style></head>'''

def footer(s):
    k = s['chave']; r = C['rodape']
    guias = ''.join(f'<a href="https://{o["dominio"]}/">{o["dominio"]}</a>' for o in SITES if o is not s)
    docs = [('Termos', '/pagina/terms', 'termos'), ('Privacidade', '/pagina/privacy', 'privacidade'),
            ('Jogo Responsável', '/pagina/responsible-gaming', 'jogo_responsavel'), ('Central de Ajuda', '/faq', 'ajuda')]
    links = ''.join(f'<a data-cta="rodape_{c}" href="{utm(s, p, "rodape_" + c)}">{t}</a>' for t, p, c in docs)
    return f'''<footer class="ft"><div class="ft-in">
<nav class="ft-guias" aria-label="Outros guias"><span>Outros guias</span>{guias}</nav>
<div class="ft-rg"><span class="ft-18" aria-hidden="true">18+</span><p><strong>18+ Jogue com responsabilidade.</strong> {e(r['aviso'])} {e(r['rtp'])}</p></div>
<nav class="ft-docs" aria-label="Documentos da plataforma">{links}</nav>
<p class="ft-nota">{e(r['nota'])}</p></div></footer>'''

def script(js=''):
    """GA4 carregado depois da interação ou do ocioso (como em src/lp.js) e evento lp_cta nos cliques com data-cta."""
    return ('<script>(function(){var d=document,w=window,RM=w.matchMedia&&w.matchMedia("(prefers-reduced-motion: reduce)").matches;'
            'function $$(q,c){return Array.prototype.slice.call((c||d).querySelectorAll(q))}'
            'function ev(n,p){try{if(w.gtag)w.gtag("event",n,p||{})}catch(x){}}'
            '$$("[data-cta]").forEach(function(a){a.addEventListener("click",function(){ev("lp_cta",{cta:a.dataset.cta,page:d.body.dataset.page})})});'
            '$$("details").forEach(function(x){x.addEventListener("toggle",function(){if(x.open)ev("lp_faq",{q:x.querySelector("summary").textContent})})});'
            'var GA=d.body.dataset.ga;if(GA){var ok=false;function ga(){if(ok)return;ok=true;w.dataLayer=w.dataLayer||[];w.gtag=function(){w.dataLayer.push(arguments)};'
            'w.gtag("js",new Date());w.gtag("config",GA,{page_title:d.title});var t=d.createElement("script");t.async=true;'
            't.src="https://www.googletagmanager.com/gtag/js?id="+GA;d.head.appendChild(t)}'
            '["scroll","touchstart","pointerdown","keydown"].forEach(function(n){w.addEventListener(n,ga,{once:true,passive:true})});setTimeout(ga,3500)}'
            + js + '})();</script>')

def body(s):
    return f'<body data-page="{s["chave"]}" data-ga="{GA}"><a class="skip" href="#conteudo">Pular para o conteúdo</a>'

def faq(itens):
    return ''.join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in itens)

def css_min(t):
    return re.sub(r'\s*\n\s*', '', t)

ARROW = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'

# ================================================================ 1. revista editorial (guiadecassino)

CSS_REVISTA = '''
:root{--bg:#F4EDE0;--paper:#FBF7EF;--ink:#1D1A16;--soft:#5C554B;--acc:#A3231B;--rule:#CFC4B0;--focus:#A3231B}
body{background:var(--bg);color:var(--ink);font:18px/1.65 Georgia,"Times New Roman",Times,serif}
.w{max-width:1180px;margin:0 auto;padding:0 20px}
.lbl{font:700 12px/1.3 system-ui,-apple-system,"Segoe UI",sans-serif;letter-spacing:.14em;text-transform:uppercase}
.mast{border-bottom:1px solid var(--ink)}
.mast-top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--rule);color:var(--soft)}
.mast-top a{color:var(--ink);text-decoration:none;border:1px solid var(--ink);padding:8px 14px;min-height:40px;display:inline-flex;align-items:center}
.mast-top .hide-m{display:none}
.mast-name{font-size:clamp(46px,13vw,136px);line-height:.95;font-weight:700;letter-spacing:-.03em;text-align:center;padding:14px 0 10px;border-bottom:4px double var(--ink)}
.mast-name a{text-decoration:none}
.mast-nav{display:flex;gap:4px 22px;justify-content:center;flex-wrap:wrap;padding:10px 0}
.mast-nav a{text-decoration:none;color:var(--soft);min-height:40px;display:inline-flex;align-items:center}
.mast-nav a:hover{color:var(--acc)}
.capa{display:grid;gap:28px;padding:28px 0 40px;border-bottom:1px solid var(--ink)}
.cover{position:relative;background:var(--ink);box-shadow:0 18px 40px -18px rgba(29,26,22,.6);max-width:520px;width:100%;margin:0 auto}
.cover img{width:100%;aspect-ratio:600/804;object-fit:cover}
.cover-top{position:absolute;left:0;right:0;top:0;padding:16px 18px;color:#FBF7EF;background:linear-gradient(rgba(0,0,0,.65),transparent)}
.cover-top b{display:block;font-size:clamp(34px,9vw,54px);line-height:1;letter-spacing:-.02em}
.cover-lines{position:absolute;left:0;right:0;bottom:0;padding:60px 18px 18px;color:#FBF7EF;background:linear-gradient(transparent,rgba(0,0,0,.82));list-style:none}
.cover-lines li{font-size:20px;line-height:1.25;padding:6px 0;border-top:1px solid rgba(251,247,239,.35)}
.cover-lines li:first-child{border:0;color:#FFD9A0}
.kick{color:var(--acc)}
h1{font-size:clamp(34px,8.4vw,64px);line-height:1.04;letter-spacing:-.02em;margin:10px 0 14px}
.dek{font-size:21px;font-style:italic;color:var(--soft);max-width:36em}
.btn{display:inline-flex;align-items:center;gap:10px;min-height:52px;padding:0 24px;background:var(--ink);color:var(--paper);text-decoration:none;font:700 16px system-ui,-apple-system,"Segoe UI",sans-serif;margin-top:22px}
.btn:hover{background:var(--acc)}
.btn-l{background:none;color:var(--ink);border:1px solid var(--ink);margin-left:8px}
.btn-l:hover{background:var(--ink);color:var(--paper)}
.sum{margin-top:30px;border-top:3px solid var(--ink)}
.sum h2{padding:10px 0;border-bottom:1px solid var(--ink)}
.sum ol{list-style:none;padding:0}
.sum a{display:grid;grid-template-columns:56px 1fr auto;align-items:baseline;gap:10px;padding:12px 0;border-bottom:1px solid var(--rule);text-decoration:none}
.sum a:hover b{color:var(--acc)}
.sum .n{font-size:34px;line-height:1;color:var(--acc);font-weight:700}
.sum b{font-size:20px;font-weight:400}
.sum small{color:var(--soft);font:13px system-ui,sans-serif}
.mat{padding:48px 0;border-bottom:1px solid var(--ink)}
.mat-h{display:grid;gap:8px;margin-bottom:26px;max-width:860px}
.mat h2{font-size:clamp(32px,7vw,56px);line-height:1.05;letter-spacing:-.02em}
.olho{font-size:22px;font-style:italic;color:var(--soft)}
.cols{columns:1;column-gap:40px}
.cols p{margin-bottom:16px;break-inside:avoid}
.cols p b{font-variant:small-caps;letter-spacing:.04em;color:var(--acc)}
.drop::first-letter{float:left;font-size:4.4em;line-height:.82;padding:6px 10px 0 0;color:var(--acc);font-weight:700}
.box{border-top:3px solid var(--acc);background:var(--paper);padding:18px 20px;margin-top:10px;font-size:17px}
.cats{display:grid;gap:0;border-top:1px solid var(--ink)}
.cat{padding:22px 0;border-bottom:1px solid var(--rule);display:grid;grid-template-columns:54px 1fr;gap:4px 14px}
.cat-n{grid-row:span 3;font-size:44px;line-height:1;color:var(--acc);font-weight:700}
.cat h3{font-size:26px;line-height:1.15}
.cat p{color:var(--ink)}
.cat-l{display:flex;flex-wrap:wrap;gap:6px 16px;font:600 15px system-ui,sans-serif}
.cat-l a{color:var(--acc);min-height:40px;display:inline-flex;align-items:center}
.pix{display:grid;gap:30px}
.pix h3{font-size:28px;border-bottom:1px solid var(--ink);padding-bottom:6px;margin-bottom:12px}
.pix ol{padding-left:22px}.pix li{margin-bottom:10px}
.quote{font-size:clamp(26px,5.6vw,38px);line-height:1.2;font-style:italic;border-top:3px solid var(--ink);border-bottom:1px solid var(--ink);padding:18px 0;color:var(--acc)}
.rg{border:6px double var(--ink);background:var(--paper);padding:24px 20px}
.rg ul{list-style:none;padding:0;display:grid;gap:16px;margin-top:18px}
.rg li{padding-left:22px;position:relative}
.rg li::before{content:"";position:absolute;left:0;top:.55em;width:10px;height:10px;background:var(--acc)}
.rg a{color:var(--acc);font-weight:700}
.vit{display:grid;grid-template-columns:repeat(2,1fr);gap:26px 18px}
.vit a{text-decoration:none;display:block;border-top:3px solid var(--ink);padding-top:10px}
.vit img{width:100%;aspect-ratio:240/280;object-fit:cover;filter:saturate(.92)}
.vit a:hover img{filter:none}
.vit .fc{display:block;padding-top:10px}
.vit .no{color:var(--acc);font-weight:700}
.vit b{display:block;font-size:20px;line-height:1.2;margin:2px 0}
.vit small{display:block;color:var(--soft);font-size:15px;line-height:1.4}
.vit .go{display:inline-block;margin-top:6px;font:700 14px system-ui,sans-serif;color:var(--acc);text-decoration:underline}
.faq details{border-bottom:1px solid var(--rule)}
.faq summary{cursor:pointer;list-style:none;padding:18px 40px 18px 0;font-size:21px;position:relative}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";position:absolute;right:6px;top:12px;font-size:30px;color:var(--acc)}
.faq details[open] summary::after{content:"\\2212"}
.faq details p{padding:0 0 18px;color:var(--soft);max-width:44em}
.assine{background:var(--ink);color:var(--paper);padding:44px 24px;text-align:center;margin:48px 0}
.assine h2{font-size:clamp(30px,6vw,48px);line-height:1.1}
.assine p{color:#D8CFC0;margin-top:10px}
.assine .btn{background:var(--paper);color:var(--ink)}
.assine .btn:hover{background:#FFD9A0}
.assine .btn-l{background:none;color:var(--paper);border-color:var(--paper)}
.ft{background:var(--paper);border-top:4px double var(--ink);color:var(--ink)}
.ft-guias a{border-radius:0}
@media (min-width:720px){.mast-top .hide-m{display:inline}.vit{grid-template-columns:repeat(4,1fr)}.pix{grid-template-columns:1fr 1fr}.pix .quote{grid-column:1/-1}}
@media (min-width:960px){
.capa{grid-template-columns:minmax(0,5fr) minmax(0,6fr);align-items:start;gap:48px}
.cols{columns:3;column-rule:1px solid var(--rule)}
.cats{grid-template-columns:repeat(5,1fr);gap:0 22px;border:0}
.cat{grid-template-columns:1fr;border-top:3px solid var(--ink);border-bottom:0;align-content:start}
.cat-n{grid-row:auto}
.pix{grid-template-columns:1fr 1fr 1fr}.pix .quote{grid-column:auto;align-self:start}
.rg ul{grid-template-columns:1fr 1fr;gap:20px 40px}
}
'''

ROMANOS = ['I', 'II', 'III', 'IV', 'V']

def site_revista(s):
    t = s['textos']; k = s['chave']
    hero = s['hero_img']
    sec = [('comecar', t['comecar']['titulo'], 'Primeiros passos'), ('categorias', t['categorias']['titulo'], 'Guia de categorias'),
           ('pix', t['pix']['titulo'], 'Dinheiro'), ('responsavel', t['responsavel']['titulo'], 'Cuidado'),
           ('maisjogados', t['vitrine']['titulo'], 'Vitrine'), ('faq', 'Perguntas frequentes', 'Dúvidas')]
    sumario = ''.join(f'<li><a href="#{a}"><span class="n">{i + 1:02d}</span><b>{e(tt)}</b><small>{e(r)}</small></a></li>'
                      for i, (a, tt, r) in enumerate(sec))
    nav = ''.join(f'<a href="#{a}">{e(r)}</a>' for a, _, r in sec[:5])
    passos = t['comecar']['passos']
    drop = ' class="drop"'
    corpo = ''.join(f'<p{drop if i == 0 else ""}><b>{i + 1}. {e(p["t"])}.</b> {e(p["p"])}</p>' for i, p in enumerate(passos))
    cats = ''
    for i, c in enumerate(t['categorias']['itens']):
        ls = []
        if c.get('guia'):
            ls.append(f'<a href="https://{c["guia"]}/{c.get("ancora", "")}">{e(c["rotulo"])}: {e(c["guia"])}</a>')
        if c.get('extra'):
            ls.append(f'<a href="https://{c["extra"]["guia"]}/">{e(c["extra"]["rotulo"])}: {e(c["extra"]["guia"])}</a>')
        if c.get('path'):
            ls.append(f'<a data-cta="categoria_{i + 1}" href="{utm(s, c["path"], "categoria_" + str(i + 1))}">Ver na plataforma</a>')
        elif c.get('slug'):
            ls.append(f'<a data-cta="categoria_{i + 1}" href="{play(s, c["slug"], "categoria_" + str(i + 1))}">Abrir {e(nome(c["slug"]))}</a>')
        cats += (f'<article class="cat"><span class="cat-n" aria-hidden="true">{ROMANOS[i]}</span><h3>{e(c["nome"])}</h3>'
                 f'<p>{e(c["texto"])}</p><p class="cat-l">{"".join(ls)}</p></article>')
    px = t['pix']
    dep = ''.join(f'<li>{e(x)}</li>' for x in px['deposito']); saq = ''.join(f'<li>{e(x)}</li>' for x in px['saque'])
    rg = ''.join(f'<li><b>{e(x["t"])}.</b> {e(x["p"])}</li>' for x in t['responsavel']['itens'])
    vit = ''
    for i, slug in enumerate(s['jogos']):
        g = GAMES.get(slug, {})
        vit += (f'<a data-cta="vitrine_{i + 1}" href="{play(s, slug, "vitrine_" + slug)}">{capa(slug)}<span class="fc">'
                f'<span class="no lbl">Nº {i + 1}</span><b>{e(g.get("name", nome(slug)))}</b><small>{e(g.get("headline", prov(slug)))}</small>'
                f'<span class="go">Jogar no {e(BRAND)}</span></span></a>')
    chamadas = ''.join(f'<li>{e(x)}</li>' for x in [t['secao_capa']] + t['chamadas_capa'])
    reg = utm(s, P['register'], 'capa')
    return head(s, css_min(CSS_REVISTA), hero) + body(s) + f'''
<header class="mast"><div class="w">
<div class="mast-top lbl"><span>{e(t['edicao'])}</span><span class="hide-m">Leitura de 6 minutos</span><a data-cta="topo_entrar" href="{utm(s, P['login'], 'topo_entrar')}">Entrar</a></div>
<p class="mast-name"><a href="/">{e(s['nome'])}</a></p>
<nav class="mast-nav lbl" aria-label="Seções">{nav}</nav></div></header>
<main id="conteudo"><div class="w">
<section class="capa" aria-labelledby="manchete">
<figure class="cover"><img src="{hero}" width="600" height="804" alt="Ilustração de capa: tigre dourado num palco com lanternas vermelhas" fetchpriority="high" decoding="async">
<div class="cover-top" aria-hidden="true"><span class="lbl">{e(t['edicao'])}</span><b>{e(s['nome'])}</b></div>
<ul class="cover-lines">{chamadas}</ul></figure>
<div><p class="kick lbl">{e(t['secao_capa'])}</p><h1 id="manchete">{e(t['manchete'])}</h1><p class="dek">{e(t['linha_fina'])}</p>
<a class="btn" data-cta="capa_cadastro" href="{reg}">Criar conta grátis {ARROW}</a>
<nav class="sum" aria-labelledby="sumario"><h2 id="sumario" class="lbl">Nesta edição</h2><ol>{sumario}</ol></nav></div>
</section>

<article class="mat" id="comecar"><header class="mat-h"><p class="lbl kick">01 · Primeiros passos</p><h2>{e(t['comecar']['titulo'])}</h2><p class="olho">{e(t['comecar']['olho'])}</p></header>
<div class="cols">{corpo}<p class="box">{e(t['comecar']['nota'])}</p></div>
<a class="btn" data-cta="comecar_cadastro" href="{utm(s, P['register'], 'comecar')}">Começar o cadastro {ARROW}</a></article>

<section class="mat" id="categorias"><header class="mat-h"><p class="lbl kick">02 · Guia de categorias</p><h2>{e(t['categorias']['titulo'])}</h2><p class="olho">{e(t['categorias']['olho'])}</p></header>
<div class="cats">{cats}</div></section>

<section class="mat" id="pix"><header class="mat-h"><p class="lbl kick">03 · Dinheiro</p><h2>{e(px['titulo'])}</h2><p class="olho">{e(px['olho'])}</p></header>
<div class="pix"><div><h3>Depósito</h3><ol>{dep}</ol></div><div><h3>Saque</h3><ol>{saq}</ol></div><blockquote class="quote">{e(px['citacao'])}</blockquote></div></section>

<section class="mat" id="responsavel"><div class="rg"><p class="lbl kick">04 · Cuidado</p><h2>{e(t['responsavel']['titulo'])}</h2><p class="olho">{e(t['responsavel']['olho'])}</p>
<ul>{rg}</ul><p style="margin-top:18px"><a data-cta="responsavel" href="{utm(s, '/pagina/responsible-gaming', 'responsavel')}">Ferramentas de Jogo Responsável da plataforma</a></p></div></section>

<section class="mat" id="maisjogados"><header class="mat-h"><p class="lbl kick">05 · Vitrine</p><h2>{e(t['vitrine']['titulo'])}</h2><p class="olho">{e(t['vitrine']['olho'])}</p></header>
<div class="vit">{vit}</div></section>

<section class="mat faq" id="faq"><header class="mat-h"><p class="lbl kick">06 · Dúvidas</p><h2>Perguntas frequentes</h2></header>{faq(t['faq'])}</section>

<section class="assine"><h2>Pronto para o primeiro giro?</h2><p>Cadastro rápido, Pix na hora e jogos no navegador.</p>
<a class="btn" data-cta="final_cadastro" href="{utm(s, P['register'], 'final')}">Criar conta grátis {ARROW}</a><a class="btn btn-l" data-cta="final_entrar" href="{utm(s, P['login'], 'final_entrar')}">Já tenho conta</a></section>
</div></main>
{footer(s)}
{script()}
</body></html>'''

# ================================================================ 2. ranking / dashboard (guiaslots)

CSS_DASH = '''
:root{--bg:#141619;--p:#1D2024;--p2:#252930;--tx:#E8EAED;--mu:#A0A6AE;--ac:#C6F432;--ln:#2F343B;--focus:#C6F432}
body{background:var(--bg);color:var(--tx);font:16px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;font-variant-numeric:tabular-nums}
.w{max-width:1280px;margin:0 auto;padding:0 16px}
.bar{position:sticky;top:0;z-index:10;background:rgba(20,22,25,.92);backdrop-filter:blur(8px);border-bottom:1px solid var(--ln)}
.bar .w{display:flex;align-items:center;justify-content:space-between;height:60px}
.logo{display:flex;align-items:center;gap:10px;font-weight:800;letter-spacing:-.01em;text-decoration:none;font-size:18px}
.logo i{width:22px;height:22px;border-radius:6px;background:var(--ac);box-shadow:inset 0 -6px 0 rgba(0,0,0,.25)}
.logo span{color:var(--mu);font-weight:500}
.acts{display:flex;gap:8px}
.b{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:44px;padding:0 16px;border-radius:10px;font-weight:700;text-decoration:none;border:1px solid var(--ln)}
.b-ac{background:var(--ac);color:#111;border-color:var(--ac)}
.b-ac:hover{filter:brightness(1.08)}
.hide-m{display:none}
.tag{display:inline-flex;gap:8px;align-items:center;font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--ac)}
.tag::before{content:"";width:8px;height:8px;border-radius:50%;background:var(--ac);box-shadow:0 0 0 4px rgba(198,244,50,.18)}
.hero{padding:28px 0 18px}
h1{font-size:clamp(34px,8vw,60px);line-height:1.02;letter-spacing:-.03em;margin:10px 0}
.hero p.sub{color:var(--mu);max-width:44em}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:22px 0}
.kpi{background:var(--p);border:1px solid var(--ln);border-radius:14px;padding:14px}
.kpi small{display:block;color:var(--mu);font-size:12px;text-transform:uppercase;letter-spacing:.08em}
.kpi b{display:block;font-size:30px;line-height:1.15;margin-top:4px}
.kpi em{font-style:normal;color:var(--mu);font-size:13px}
.kpi.hl b{color:var(--ac)}
.pan{background:var(--p);border:1px solid var(--ln);border-radius:18px;padding:18px;margin:16px 0}
.pan-h{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:end;gap:8px 16px;margin-bottom:14px}
h2{font-size:24px;letter-spacing:-.01em}
.pan-h p{color:var(--mu);font-size:14px;max-width:52em}
.pod{max-width:720px;margin:0 auto;display:grid;grid-template-columns:1fr 1.15fr 1fr;align-items:end;gap:10px}
.pd{text-decoration:none;display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px}
.pd img{width:100%;max-width:150px;border-radius:12px;border:1px solid var(--ln)}
.pd-1 img{max-width:180px;border-color:var(--ac);box-shadow:0 0 0 3px rgba(198,244,50,.25)}
.pd b{font-size:14px;line-height:1.2}
.pd small{color:var(--mu);font-size:12px}
.blk{width:100%;border-radius:10px 10px 0 0;background:linear-gradient(var(--p2),var(--bg));border:1px solid var(--ln);border-bottom:0;display:grid;place-items:start center;padding-top:8px;font-size:28px;font-weight:900;height:var(--h);transform-origin:bottom;animation:grow .9s cubic-bezier(.2,.8,.2,1) both}
.pd-1 .blk{background:linear-gradient(var(--ac),#6E8A12);color:#111}
.pd-2 .blk{animation-delay:.15s}.pd-3 .blk{animation-delay:.3s}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.chip{min-height:40px;padding:0 14px;border-radius:999px;border:1px solid var(--ln);background:var(--p2);color:var(--tx);font-weight:600;font-size:14px}
.chip[aria-pressed="true"]{background:var(--ac);border-color:var(--ac);color:#111}
.cnt{color:var(--mu);font-size:13px}
.pan,.w,main{min-width:0}.tw{position:relative;overflow-x:auto;max-width:100%;border:1px solid var(--ln);border-radius:12px}
table{width:100%;border-collapse:collapse;min-width:720px;font-size:15px}
th,td{padding:10px 12px;text-align:left;border-bottom:1px solid var(--ln);white-space:nowrap}
th{background:var(--p2);font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--mu);position:sticky;top:0}
th button{all:unset;cursor:pointer;display:inline-flex;gap:6px;align-items:center;min-height:32px}
th button:focus-visible{outline:2px solid var(--ac);outline-offset:2px}
th button::after{content:"\\2195";opacity:.5}
th[aria-sort="ascending"] button::after{content:"\\2191";opacity:1;color:var(--ac)}
th[aria-sort="descending"] button::after{content:"\\2193";opacity:1;color:var(--ac)}
td.n{text-align:right}th.n{text-align:right}
td .nd{color:var(--mu);font-size:13px}
tr:hover td{background:rgba(255,255,255,.03)}
td:first-child{position:sticky;left:0;background:var(--p);font-weight:700}
td a{color:var(--ac);font-weight:700}
.vol{display:inline-flex;gap:3px;margin-right:6px;vertical-align:middle}.vol i{width:6px;height:12px;border-radius:2px;background:var(--ln)}.vol i.f{background:var(--ac)}
.cards{display:grid;grid-template-columns:repeat(2,1fr);gap:10px}
.cd{background:var(--p2);border:1px solid var(--ln);border-radius:12px;overflow:hidden;text-decoration:none;display:flex;flex-direction:column}
.cd:hover{border-color:var(--ac)}
.cd img{width:100%;aspect-ratio:240/280;object-fit:cover}
.cd span{padding:8px 10px 10px;font-size:14px;font-weight:700;line-height:1.25}
.cd small{display:block;color:var(--mu);font-weight:500;font-size:12px;margin-top:2px}
[hidden]{display:none!important}
.glo{display:grid;gap:10px}
.gl{background:var(--p2);border:1px solid var(--ln);border-radius:12px;padding:16px;border-left:4px solid var(--ac)}
.gl h3{font-size:17px;margin-bottom:4px}
.gl p{color:var(--mu);font-size:15px}
.fin{text-align:center;padding:32px 18px}
.fin p{color:var(--mu);margin:6px 0 16px}
.ft{border-top:1px solid var(--ln);color:var(--mu)}
.ft a{color:var(--tx)}.ft strong{color:var(--tx)}.ft-18{color:var(--ac)}
@media (min-width:720px){.kpis{grid-template-columns:repeat(4,1fr)}.cards{grid-template-columns:repeat(4,1fr)}.glo{grid-template-columns:repeat(2,1fr)}.hide-m{display:inline-flex}}
@media (min-width:1100px){.cards{grid-template-columns:repeat(6,1fr)}.glo{grid-template-columns:repeat(4,1fr)}}
'''

JS_DASH = '''
var tb=d.getElementById("tb"),rows=$$("tr",tb),chips=$$(".chip"),cards=$$(".cd"),cnt=d.getElementById("cnt");
$$("th[data-k]").forEach(function(th){th.querySelector("button").addEventListener("click",function(){
  var k=+th.dataset.k,num=th.dataset.t==="n",asc=th.getAttribute("aria-sort")!=="ascending";if(num&&th.getAttribute("aria-sort")==="none")asc=false;
  $$("th[data-k]").forEach(function(o){o.setAttribute("aria-sort","none")});th.setAttribute("aria-sort",asc?"ascending":"descending");
  rows.sort(function(a,b){var x=a.children[k].dataset.v,y=b.children[k].dataset.v;
    if(num){x=x===""?null:+x;y=y===""?null:+y;if(x===null&&y===null)return 0;if(x===null)return 1;if(y===null)return -1;return asc?x-y:y-x}
    return asc?x.localeCompare(y,"pt-BR"):y.localeCompare(x,"pt-BR")});
  rows.forEach(function(r){tb.appendChild(r)});ev("site_ordenar",{coluna:th.textContent})})});
chips.forEach(function(c){c.addEventListener("click",function(){var f=c.dataset.f,n=0;
  chips.forEach(function(o){o.setAttribute("aria-pressed",o===c?"true":"false")});
  rows.forEach(function(r){var on=!f||r.dataset.p===f;r.hidden=!on;if(on)n++});
  cards.forEach(function(r){r.hidden=!(!f||r.dataset.p===f)});
  cnt.textContent=n+" slots";ev("site_filtro",{provedor:f||"todos"})})});
'''

VOL = {'Baixa': 1, 'Média': 2, 'Alta': 3}

def site_dash(s):
    t = s['textos']; js = s['jogos']
    provs = []
    for slug in js:
        if prov(slug) not in provs: provs.append(prov(slug))
    com_rtp = [x for x in js if ficha(x).get('rtp')]; com_max = [x for x in js if ficha(x).get('max')]
    top_rtp = max(com_rtp, key=lambda x: ficha(x)['rtp']); top_max = max(com_max, key=lambda x: ficha(x)['max'])
    kpis = (f'<div class="kpi hl"><small>Slots no ranking</small><b>{len(js)}</b><em>todos jogáveis na plataforma</em></div>'
            f'<div class="kpi"><small>Provedores</small><b>{len(provs)}</b><em>{e(", ".join(provs))}</em></div>'
            f'<div class="kpi"><small>Maior RTP teórico listado</small><b>{rtp(top_rtp)}</b><em>{e(nome(top_rtp))}</em></div>'
            f'<div class="kpi"><small>Maior ganho máximo listado</small><b>{maxw(top_max)}</b><em>{e(nome(top_max))}</em></div>')
    pod = ''
    hs = {1: '120px', 2: '86px', 3: '62px'}
    for pos in (2, 1, 3):
        slug = s['podio'][pos - 1]
        pod += (f'<a class="pd pd-{pos}" data-cta="podio_{pos}" href="{play(s, slug, "podio_" + str(pos))}">{capa(slug, lazy=False, eager=pos == 1)}'
                f'<b>{e(nome(slug))}</b><small>{e(prov(slug))}{" · RTP teórico " + rtp(slug) if rtp(slug) else ""}</small>'
                f'<span class="blk" style="--h:{hs[pos]}">{pos}º</span></a>')
    chips = '<button class="chip" type="button" aria-pressed="true" data-f="">Todos</button>' + ''.join(
        f'<button class="chip" type="button" aria-pressed="false" data-f="{e(p)}">{e(p)}</button>' for p in provs)
    nd = '<span class="nd">ver no jogo</span>'
    trs = ''
    for i, slug in enumerate(js):
        f = ficha(slug); v = f.get('vol')
        vb = (f'<span class="vol" aria-hidden="true">{"".join("<i class=f></i>" if j < VOL[v] else "<i></i>" for j in range(3))}</span>{v}' if v else nd)
        trs += (f'<tr data-p="{e(prov(slug))}"><td data-v="{e(nome(slug))}">{e(nome(slug))}</td><td data-v="{e(prov(slug))}">{e(prov(slug))}</td>'
                f'<td class="n" data-v="{f.get("rtp", "")}">{rtp(slug) or nd}</td><td data-v="{VOL.get(v, "") if v else ""}">{vb}</td>'
                f'<td class="n" data-v="{f.get("max", "")}">{maxw(slug) or nd}</td>'
                f'<td><a data-cta="tabela_{i + 1}" href="{play(s, slug, "tabela_" + slug)}">Jogar<span class="sr"> {e(nome(slug))}</span></a></td></tr>')
    cols = [('Nome', 't'), ('Provedor', 't'), ('RTP teórico', 'n'), ('Volatilidade', 'n'), ('Ganho máximo', 'n')]
    ths = ''.join(f'<th scope="col" data-k="{i}" data-t="{tp}" aria-sort="none"{" class=n" if tp == "n" and i != 3 else ""}><button type="button">{c}</button></th>'
                  for i, (c, tp) in enumerate(cols)) + '<th scope="col"><span class="sr">Abrir jogo</span></th>'
    cards = ''.join(f'<a class="cd" data-p="{e(prov(slug))}" data-cta="card_{i + 1}" href="{play(s, slug, "card_" + slug)}">{capa(slug, alt="")}'
                    f'<span>{e(nome(slug))}<small>{e(prov(slug))}{" · " + rtp(slug) if rtp(slug) else ""}</small></span></a>' for i, slug in enumerate(js))
    glo = ''.join(f'<article class="gl"><h3>{e(g["t"])}</h3><p>{e(g["p"])}</p></article>' for g in t['glossario'])
    return head(s, css_min(CSS_DASH), web(s['podio'][0])) + body(s) + f'''
<header class="bar"><div class="w"><a class="logo" href="/"><i></i>guiaslots<span>.win</span></a>
<div class="acts"><a class="b" data-cta="topo_entrar" href="{utm(s, P['login'], 'topo_entrar')}">Entrar</a><a class="b b-ac hide-m" data-cta="topo_cadastro" href="{utm(s, P['register'], 'topo')}">Criar conta</a></div></div></header>
<main id="conteudo"><div class="w">
<section class="hero"><p class="tag">{e(t['rotulo'])}</p><h1>{e(t['titulo_hero'])}</h1><p class="sub">{e(t['sub_hero'])}</p>
<div class="kpis">{kpis}</div>
<a class="b b-ac" data-cta="hero_cadastro" href="{utm(s, P['register'], 'hero')}">Criar conta e jogar {ARROW}</a>
<a class="b" data-cta="hero_slots" href="{utm(s, P['slots'], 'hero_slots')}">Todos os slots da plataforma</a></section>
<section class="pan" aria-labelledby="pod-h"><div class="pan-h"><div><h2 id="pod-h">{e(t['podio_titulo'])}</h2><p>{e(t['podio_sub'])}</p></div></div><div class="pod">{pod}</div></section>
<section class="pan" id="ranking" aria-labelledby="rk-h"><div class="pan-h"><div><h2 id="rk-h">{e(t['tabela_titulo'])}</h2><p>{e(t['tabela_sub'])}</p></div><span class="cnt" id="cnt" aria-live="polite">{len(js)} slots</span></div>
<div class="chips" role="group" aria-label="Filtrar por provedor">{chips}</div>
<div class="tw" tabindex="0" role="region" aria-labelledby="rk-h"><table><caption class="sr">{e(t['tabela_titulo'])}: slots com RTP teórico, volatilidade e ganho máximo</caption>
<thead><tr>{ths}</tr></thead><tbody id="tb">{trs}</tbody></table></div></section>
<section class="pan" aria-labelledby="cd-h"><div class="pan-h"><h2 id="cd-h">{e(t['cards_titulo'])}</h2></div><div class="cards">{cards}</div></section>
<section class="pan" id="glossario" aria-labelledby="glo-h"><div class="pan-h"><h2 id="glo-h">{e(t['glossario_titulo'])}</h2></div><div class="glo">{glo}</div></section>
<section class="fin"><h2>Escolheu o seu?</h2><p>Crie a conta, deposite via Pix e abra o slot direto no navegador.</p>
<a class="b b-ac" data-cta="final_cadastro" href="{utm(s, P['register'], 'final')}">Criar conta grátis {ARROW}</a></section>
</div></main>
{footer(s)}
{script(JS_DASH)}
</body></html>'''

# ================================================================ 3. festival oriental (guiafortune)

CSS_FEST = '''
:root{--bg:#7A1414;--bg2:#4E0B0B;--au:#F2C14E;--au2:#FFE39A;--tx:#FFF4DC;--mu:#F1D4B0;--focus:#FFE39A}
body{background:var(--bg2);color:var(--tx);font:17px/1.6 system-ui,-apple-system,"Segoe UI",sans-serif}
.serif,h1,h2,h3{font-family:"Songti SC","STSong","Noto Serif",Georgia,serif;font-weight:700}
.pat{background:radial-gradient(circle at 50% 50%,rgba(242,193,78,.10) 0 18px,transparent 19px) 0 0/56px 56px,radial-gradient(circle at 50% 50%,transparent 0 26px,rgba(242,193,78,.07) 27px 28px,transparent 29px) 28px 28px/56px 56px,linear-gradient(var(--bg),var(--bg2))}
.w{max-width:1120px;margin:0 auto;padding:0 20px}
.top{position:relative;z-index:3;display:flex;justify-content:space-between;align-items:center;padding:14px 20px}
.logo{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:800;letter-spacing:.04em}
.seal{width:36px;height:36px;border-radius:8px;background:var(--au);color:var(--bg2);display:grid;place-items:center;font-family:Georgia,serif;font-size:20px;transform:rotate(-6deg)}
.bt{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:0 22px;border-radius:999px;font-weight:800;text-decoration:none;background:linear-gradient(var(--au2),var(--au));color:#4E0B0B;box-shadow:0 6px 0 #9C6A12,0 10px 24px rgba(0,0,0,.35)}
.bt:hover{filter:brightness(1.06)}
.bt-o{background:none;color:var(--au2);box-shadow:none;border:2px solid var(--au)}
.lant{position:absolute;left:0;right:0;top:0;height:0;z-index:2;pointer-events:none}
.lant i{position:absolute;top:0;width:2px;height:var(--l);background:var(--au);left:var(--x);transform-origin:top center;animation:sway 4s ease-in-out infinite alternate;animation-delay:var(--d)}
.lant i::after{content:"";position:absolute;left:-21px;bottom:-54px;width:44px;height:56px;border-radius:45%;background:radial-gradient(circle at 50% 40%,#FF8A4C,#C21E1E 70%);box-shadow:0 0 30px rgba(255,120,60,.55);border-top:5px solid var(--au);border-bottom:5px solid var(--au)}
@keyframes sway{from{transform:rotate(-4deg)}to{transform:rotate(4deg)}}
.hero{position:relative;overflow:hidden;padding:30px 0 56px;text-align:center}
.moon{width:min(78vw,380px);aspect-ratio:1;margin:56px auto 22px;border-radius:50%;overflow:hidden;border:6px solid var(--au);box-shadow:0 0 0 10px rgba(242,193,78,.18),0 30px 60px rgba(0,0,0,.45)}
.moon img{width:100%;height:100%;object-fit:cover;object-position:50% 40%}
.selo{display:inline-block;border:1px solid var(--au);color:var(--au2);padding:6px 14px;border-radius:999px;font-size:13px;letter-spacing:.12em;text-transform:uppercase}
h1{font-size:clamp(42px,11vw,92px);line-height:1;margin:14px 0 12px;color:var(--au2);text-shadow:0 4px 0 #8A1010}
.hero .sub{max-width:36em;margin:0 auto 22px;color:var(--mu);font-size:19px}
.ctas{display:flex;flex-wrap:wrap;gap:12px;justify-content:center}
.idx{display:flex;gap:8px;overflow-x:auto;padding:14px 20px;justify-content:flex-start;border-top:1px solid rgba(242,193,78,.3);border-bottom:1px solid rgba(242,193,78,.3);background:rgba(0,0,0,.18);position:sticky;top:0;z-index:5;backdrop-filter:blur(6px)}
.idx a{flex:none;text-decoration:none;padding:8px 14px;border-radius:999px;border:1px solid rgba(242,193,78,.5);font-size:14px;min-height:40px;display:inline-flex;align-items:center}
.idx a:hover{background:var(--au);color:var(--bg2)}
.cap{padding:64px 0;position:relative}
.cap:nth-of-type(even){background:rgba(0,0,0,.16)}
.cap .w{display:grid;gap:26px;align-items:center}
.cap-n{position:absolute;right:12px;top:24px;font-family:Georgia,serif;font-size:clamp(90px,22vw,200px);line-height:1;color:rgba(242,193,78,.12);font-weight:700}
.cap-k{color:var(--au);letter-spacing:.14em;text-transform:uppercase;font-size:13px;font-weight:700}
.cap h2{font-size:clamp(32px,7vw,54px);line-height:1.05;margin:8px 0 14px;color:var(--au2)}
.cap p.tx{color:var(--tx);max-width:36em}
.fx{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:20px 0}
.fx div{border:1px solid rgba(242,193,78,.45);border-radius:12px;padding:10px;background:rgba(0,0,0,.18)}
.fx dt{font-size:12px;color:var(--mu);text-transform:uppercase;letter-spacing:.06em}
.fx dd{font-weight:800;font-size:18px;color:var(--au2)}
.fx dd.nd{font-size:14px;font-weight:600;color:var(--mu)}
.art{position:relative;display:grid;place-items:center;min-height:300px}
.art::before{content:"";position:absolute;width:86%;aspect-ratio:1;border-radius:50%;background:radial-gradient(circle,rgba(255,227,154,.35),rgba(242,193,78,.08) 60%,transparent 70%)}
.art img{position:relative;max-height:420px;width:auto;filter:drop-shadow(0 20px 30px rgba(0,0,0,.4))}
.art .scroll{background:#FFF4DC;padding:14px;border-radius:18px;border:4px solid var(--au);box-shadow:0 20px 40px rgba(0,0,0,.35);transform:rotate(-2deg)}
.art .scroll img{max-height:380px;filter:none;border-radius:8px}
.art .cv{position:absolute;right:4%;bottom:0;width:104px;border-radius:12px;border:3px solid var(--au);box-shadow:0 10px 20px rgba(0,0,0,.4);transform:rotate(6deg)}
.art.solo img{max-height:380px;border-radius:16px;border:4px solid var(--au)}
.rv{opacity:1}
.js .rv{opacity:0;transform:translateY(28px);transition:opacity .7s ease,transform .7s ease}
.js .rv.on{opacity:1;transform:none}
.sec{padding:64px 0}
.sec h2{font-size:clamp(30px,6.4vw,48px);line-height:1.08;color:var(--au2);text-align:center}
.sec .lead{text-align:center;color:var(--mu);max-width:40em;margin:10px auto 28px}
.quiz{max-width:760px;margin:0 auto;display:grid;gap:18px}
.quiz fieldset{border:2px solid rgba(242,193,78,.5);border-radius:18px;padding:16px;margin:0;background:rgba(0,0,0,.2)}
.quiz legend{padding:0 8px;font-weight:800;color:var(--au2);font-size:18px}
.ops{display:flex;flex-wrap:wrap;gap:8px;margin-top:6px}
.ops label{position:relative}
.ops input{position:absolute;opacity:0;width:1px;height:1px}
.ops span{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;border-radius:999px;border:1px solid var(--au);cursor:pointer}
.ops input:checked+span{background:var(--au);color:var(--bg2);font-weight:800}
.ops input:focus-visible+span{outline:3px solid var(--focus);outline-offset:3px}
.res{border:3px solid var(--au);border-radius:22px;padding:20px;background:linear-gradient(135deg,rgba(242,193,78,.18),rgba(0,0,0,.2));display:grid;grid-template-columns:96px 1fr;gap:16px;align-items:center}
.res img{border-radius:12px}
.res h3{font-size:26px;color:var(--au2)}
.res p{color:var(--mu);margin:4px 0 12px}
[hidden]{display:none!important}
.tw{position:relative;overflow-x:auto;border-radius:16px;border:2px solid rgba(242,193,78,.5)}
table{border-collapse:collapse;width:100%;min-width:760px;background:rgba(0,0,0,.2)}
th,td{padding:12px;border-bottom:1px solid rgba(242,193,78,.25);text-align:left;vertical-align:top;font-size:15px}
thead th{color:var(--au2);font-family:"Songti SC","STSong",Georgia,serif;font-size:17px}
tbody th{color:var(--mu);font-weight:600;white-space:nowrap}
td .nd{color:var(--mu);font-size:14px}
.pg{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.pgc{text-decoration:none;border:2px solid var(--au);border-radius:16px;overflow:hidden;background:rgba(0,0,0,.25);display:flex;flex-direction:column}
.pgc:hover{box-shadow:0 0 0 4px rgba(242,193,78,.3)}
.pgc img{width:100%;aspect-ratio:240/280;object-fit:cover}
.pgc span{padding:10px 12px 14px;font-weight:800;color:var(--au2)}
.pgc small{display:block;font-weight:400;color:var(--mu);font-size:13px;line-height:1.4;margin-top:4px}
.fin{text-align:center;padding:56px 20px 64px}
.fin h2{font-size:clamp(30px,6vw,46px);color:var(--au2);margin-bottom:10px}
.fin p{color:var(--mu);margin-bottom:22px}
.ft{background:#2E0606;color:var(--mu);border-top:3px solid var(--au)}
.ft a{color:var(--au2)}.ft strong{color:var(--tx)}
@media (min-width:720px){.pg{grid-template-columns:repeat(4,1fr)}.idx{justify-content:center}}
@media (min-width:960px){.cap .w{grid-template-columns:1.1fr .9fr}.cap:nth-of-type(even) .art{order:-1}.cap-n{right:auto;left:40px}.cap:nth-of-type(odd) .cap-n{left:auto;right:40px}}
'''

JS_FEST = '''
d.documentElement.classList.add("js");
var rv=$$(".rv");if(RM||!("IntersectionObserver" in w))rv.forEach(function(x){x.classList.add("on")});
else{var io=new IntersectionObserver(function(es){es.forEach(function(x){if(x.isIntersecting){x.target.classList.add("on");io.unobserve(x.target)}})},{rootMargin:"0px 0px -12% 0px"});rv.forEach(function(x){io.observe(x)})}
var qz=d.getElementById("qz");
if(qz)qz.addEventListener("submit",function(x){x.preventDefault();var sc={},last=null,n=0;
  $$("input:checked",qz).forEach(function(i){n++;var p=JSON.parse(i.dataset.p);for(var k in p){sc[k]=(sc[k]||0)+p[k]}if(i.name==="q2")last=Object.keys(p)[0]});
  var msg=d.getElementById("qz-msg");if(n<3){msg.textContent="Responda as três perguntas para ver o resultado.";return}msg.textContent="";
  var best=null;for(var k in sc){if(best===null||sc[k]>sc[best]||(sc[k]===sc[best]&&k===last))best=k}
  $$(".res").forEach(function(r){r.hidden=r.dataset.s!==best});var r=d.querySelector('.res[data-s="'+best+'"]');
  if(r){r.focus();ev("site_quiz",{resultado:best})}});
'''

CHN = ['壹', '貳', '參', '肆', '伍', '陸']

def site_fest(s):
    t = s['textos']; k = s['chave']
    caps_idx = ''.join(f'<a href="#cap-{c["slug"]}">{i + 1}. {e(c["animal"])}</a>' for i, c in enumerate(s['capitulos']))
    caps = ''
    for i, c in enumerate(s['capitulos']):
        slug = c['slug']; f = ficha(slug)
        def dd(v): return f'<dd>{e(v)}</dd>' if v else '<dd class="nd">ver no jogo</dd>'
        grade = ' · '.join(x for x in (f.get('grade'), f.get('linhas')) if x)
        fx = (f'<dl class="fx"><div><dt>RTP teórico</dt>{dd(rtp(slug))}</div><div><dt>Ganho máximo</dt>{dd(maxw(slug))}</div>'
              f'<div><dt>Grade</dt>{dd(grade)}</div></dl>')
        if c.get('arte'):
            img = reduzida(c['arte'], k, slug, 420)
            alt = f'{c["personagem"]}, personagem do {nome(slug)}'
            if c.get('arte_fundo_claro'):
                art = f'<div class="art"><div class="scroll">{arte(img, alt)}</div>{capa(slug, alt="", cls="cv")}</div>'
            else:
                art = f'<div class="art">{arte(img, alt)}{capa(slug, alt="", cls="cv")}</div>'
        else:
            art = f'<div class="art solo">{capa(slug)}</div>'
        caps += f'''<section class="cap" id="cap-{slug}" aria-labelledby="h-{slug}"><span class="cap-n" aria-hidden="true">{CHN[i]}</span><div class="w">
<div class="rv"><p class="cap-k">Capítulo {i + 1} · {e(c['animal'])} · {e(nome(slug))}</p><h2 id="h-{slug}">{e(c['titulo'])}</h2><p class="tx">{e(c['texto'])}</p>{fx}
<a class="bt" data-cta="capitulo_{i + 1}" href="{play(s, slug, 'capitulo_' + slug)}">Jogar {e(nome(slug))} {ARROW}</a></div>
<div class="rv">{art}</div></div></section>'''
    q = s['quiz']; qs = ''
    for n, p in enumerate(q['perguntas']):
        ops = ''.join(f'<label><input type="radio" name="q{n}" value="{j}" data-p="{e(json.dumps(o["p"]))}"><span>{e(o["t"])}</span></label>' for j, o in enumerate(p['op']))
        qs += f'<fieldset><legend>{n + 1}. {e(p["q"])}</legend><div class="ops">{ops}</div></fieldset>'
    res = ''.join(f'<div class="res" data-s="{c["slug"]}" tabindex="-1" hidden>{capa(c["slug"], alt="")}<div><p class="cap-k">Seu Fortune é</p><h3>{e(nome(c["slug"]))}</h3>'
                  f'<p>{e(c["recurso"])}. {e(c["personagem"])} é o seu parceiro de festival.</p>'
                  f'<a class="bt" data-cta="quiz_{c["slug"]}" href="{play(s, c["slug"], "quiz_" + c["slug"])}">Jogar {e(nome(c["slug"]))} {ARROW}</a></div></div>'
                  for c in s['capitulos'])
    nd = '<span class="nd">ver no jogo</span>'
    cs = s['capitulos']
    def row(lbl, fn): return f'<tr><th scope="row">{lbl}</th>' + ''.join(f'<td>{fn(c) or nd}</td>' for c in cs) + '</tr>'
    comp = (f'<thead><tr><th scope="col"><span class="sr">Item</span></th>' + ''.join(f'<th scope="col">{e(nome(c["slug"]))}</th>' for c in cs) + '</tr></thead><tbody>'
            + row('Grade', lambda c: ficha(c['slug']).get('grade')) + row('Linhas', lambda c: ficha(c['slug']).get('linhas'))
            + row('Ganho máximo', lambda c: maxw(c['slug'])) + row('RTP teórico', lambda c: rtp(c['slug']))
            + row('Recurso especial', lambda c: None if c['recurso'].startswith('Confira') else e(c['recurso'])) + '</tbody>')
    outros = ''.join(f'<a class="pgc" data-cta="outros_{i + 1}" href="{play(s, slug, "outros_" + slug)}">{capa(slug, alt="")}'
                     f'<span>{e(nome(slug))}<small>{e(s["outros_textos"].get(slug, ""))}{" RTP teórico " + rtp(slug) + "." if rtp(slug) else ""}</small></span></a>'
                     for i, slug in enumerate(s['outros']))
    lant = ''.join(f'<i style="--x:{x}%;--l:{l}px;--d:-{dl}s"></i>' for x, l, dl in ((5, 40, 0), (16, 70, 1.2), (84, 56, .6), (95, 34, 2)))
    return head(s, css_min(CSS_FEST), s['hero_img']) + body(s).replace('<body ', '<body class="pat" ') + f'''
<header class="top"><a class="logo" href="/"><span class="seal" aria-hidden="true">福</span>{e(s['nome'])}</a>
<a class="bt bt-o" data-cta="topo_entrar" href="{utm(s, P['login'], 'topo_entrar')}">Entrar</a></header>
<main id="conteudo">
<section class="hero"><div class="lant" aria-hidden="true">{lant}</div><div class="w">
<div class="moon"><img src="{s['hero_img']}" width="600" height="804" alt="Dragão dourado envolto em nuvens vermelhas" fetchpriority="high" decoding="async"></div>
<span class="selo">{e(t['selo'])}</span><h1>{e(t['titulo_hero'])}</h1><p class="sub">{e(t['sub_hero'])}</p>
<div class="ctas"><a class="bt" data-cta="hero_cadastro" href="{utm(s, P['register'], 'hero')}">Criar conta e jogar {ARROW}</a><a class="bt bt-o" href="#quiz">Fazer o quiz</a></div>
</div></section>
<nav class="idx" aria-label="Capítulos">{caps_idx}<a href="#quiz">Quiz</a><a href="#comparativo">Comparativo</a></nav>
{caps}
<section class="sec" id="quiz" aria-labelledby="qz-h"><div class="w"><h2 id="qz-h">{e(q['titulo'])}</h2><p class="lead">{e(q['sub'])}</p>
<form class="quiz" id="qz">{qs}<div class="ctas"><button class="bt" type="submit" style="border:0">Ver meu Fortune</button></div><p id="qz-msg" role="status" style="text-align:center;color:var(--au2)"></p>{res}</form></div></section>
<section class="sec" id="comparativo" aria-labelledby="cp-h"><div class="w"><h2 id="cp-h">{e(t['comparativo_titulo'])}</h2><p class="lead">{e(t['comparativo_sub'])}</p>
<div class="tw" tabindex="0" role="region" aria-labelledby="cp-h"><table><caption class="sr">Comparativo da série Fortune</caption>{comp}</table></div></div></section>
<section class="sec" aria-labelledby="pg-h"><div class="w"><h2 id="pg-h">{e(t['outros_titulo'])}</h2><p class="lead">Mais jogos da PG Soft para depois do festival.</p><div class="pg">{outros}</div>
<p style="text-align:center;margin-top:22px"><a class="bt bt-o" data-cta="provedor_pg" href="{utm(s, P['pgsoft'], 'provedor_pgsoft')}">Ver todos da PG Soft</a></p></div></section>
<section class="fin"><h2>Que a sorte venha com limite</h2><p>Defina um valor por sessão e aproveite o festival.</p>
<a class="bt" data-cta="final_cadastro" href="{utm(s, P['register'], 'final')}">Criar conta grátis {ARROW}</a></section>
</main>
{footer(s)}
{script(JS_FEST)}
</body></html>'''

# ================================================================ 4. bento / neo-brutalista (guiapragmatic)

CSS_BENTO = '''
@font-face{font-family:Mont;src:url(assets/fonts/montserrat-Black.woff2) format("woff2");font-weight:900;font-display:swap}
:root{--bg:#F6F2E8;--ink:#111;--roxo:#7B3FF2;--am:#FFD23F;--ci:#2EE6D6;--rosa:#FF7AB6;--br:#fff;--focus:#7B3FF2}
body{background:var(--bg);color:var(--ink);font:500 17px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
.k{font-family:Mont,"Arial Black",system-ui,sans-serif;font-weight:900;text-transform:uppercase;letter-spacing:-.01em}
.w{max-width:1200px;margin:0 auto;padding:0 16px}
.bx{border:3px solid var(--ink);box-shadow:6px 6px 0 var(--ink);border-radius:14px}
.top{display:flex;justify-content:space-between;align-items:center;padding:16px}
.logo{background:var(--am);padding:8px 12px;text-decoration:none;font-size:18px;transform:rotate(-2deg)}
.btn{display:inline-flex;align-items:center;gap:10px;min-height:50px;padding:0 20px;text-decoration:none;font-size:16px;background:var(--br);transition:transform .12s,box-shadow .12s}
.btn:hover{transform:translate(-2px,-2px);box-shadow:8px 8px 0 var(--ink)}
.btn:active{transform:translate(4px,4px);box-shadow:2px 2px 0 var(--ink)}
.btn-r{background:var(--roxo);color:#fff}
.btn-a{background:var(--am)}
.hero{padding:10px 0 22px}
h1{font-size:clamp(40px,11vw,104px);line-height:.92;margin:12px 0}
h1 span{background:var(--ci);padding:0 .12em;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.hero p{max-width:34em;font-size:19px}
.stk{display:inline-block;background:var(--rosa);padding:6px 12px;font-size:13px;transform:rotate(-3deg)}
.ctas{display:flex;flex-wrap:wrap;gap:14px;margin-top:20px}
.bento{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:10px 0 40px}
.t{position:relative;display:flex;flex-direction:column;justify-content:space-between;gap:10px;padding:14px;text-decoration:none;overflow:hidden;min-height:200px;background:var(--c,#fff);transition:transform .12s,box-shadow .12s}
.t:hover{transform:translate(-3px,-3px);box-shadow:9px 9px 0 var(--ink)}
.t h3{font-size:20px;line-height:1}
.t p{font-size:15px;line-height:1.4}
.t img.cv{width:96px;border:3px solid var(--ink);border-radius:10px}
.t .m{display:flex;flex-wrap:wrap;gap:6px}
.t .m b{background:var(--br);border:2px solid var(--ink);border-radius:999px;padding:2px 10px;font-size:13px}
.t-big{grid-column:span 2;min-height:260px}
.t-big .cv{width:120px}
.t-zeus{grid-column:span 2;min-height:420px;padding-right:44%}
.t-zeus .zeus{position:absolute;right:-6%;bottom:-4px;width:58%;max-width:330px;filter:drop-shadow(6px 6px 0 rgba(0,0,0,.85))}
.t-cta{grid-column:span 2;background:var(--ink);color:#fff;justify-content:center;align-items:flex-start}
.t-cta h3{font-size:28px;color:var(--am)}
.sec{margin:40px 0}
.sec>h2{font-size:clamp(30px,7vw,56px);line-height:.95;margin-bottom:16px}
.tabs{display:flex;gap:10px;overflow-x:auto;padding:4px 8px 12px 2px}
.tab{flex:none;min-height:46px;padding:0 16px;background:var(--br);border:3px solid var(--ink);border-radius:999px;box-shadow:3px 3px 0 var(--ink);font-family:Mont,"Arial Black",sans-serif;font-weight:900;text-transform:uppercase;font-size:14px}
.tab[aria-selected="true"]{background:var(--am)}
.pan{padding:16px;background:var(--br)}
.pan>p{font-size:18px;margin-bottom:14px}
.grid{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}
.gc{display:flex;flex-direction:column;text-decoration:none;background:var(--bg);border:3px solid var(--ink);border-radius:12px;overflow:hidden;box-shadow:4px 4px 0 var(--ink)}
.gc:hover{background:var(--ci)}
.gc img{width:100%;aspect-ratio:240/280;object-fit:cover;border-bottom:3px solid var(--ink)}
.gc span{padding:8px 10px;font-weight:800;font-size:14px;line-height:1.25}
.gc small{display:block;font-weight:500;font-size:12px}
[hidden]{display:none!important}
.vs{display:grid;gap:16px}
.v{padding:18px;background:var(--c)}
.v h3{font-size:26px;margin-bottom:8px}
.v .pair{display:flex;gap:12px;margin-top:14px;flex-wrap:wrap}
.v .pair a{display:flex;flex-direction:column;gap:6px;text-decoration:none;font-weight:800;font-size:14px;width:130px}
.v .pair img{border:3px solid var(--ink);border-radius:10px}
.live{display:grid;gap:16px}
.lv{display:grid;grid-template-columns:110px 1fr;gap:14px;padding:14px;text-decoration:none;align-items:center;background:var(--c)}
.lv img{border:3px solid var(--ink);border-radius:10px}
.lv h3{font-size:22px}
.lv .tag{display:inline-block;background:#E8112D;color:#fff;font-size:12px;padding:2px 8px;border-radius:6px;margin-bottom:6px}
.fin{background:var(--roxo);color:#fff;padding:30px 20px;text-align:center;margin:40px 0}
.fin h2{font-size:clamp(28px,6vw,48px);line-height:1}
.fin p{margin:10px 0 18px}
.fin .btn{color:var(--ink)}
.ft{border-top:3px solid var(--ink);background:var(--am)}
.ft-guias a,.ft-18{border-width:3px;background:#fff;box-shadow:3px 3px 0 var(--ink)}
@media (min-width:720px){.grid{grid-template-columns:repeat(4,1fr)}.vs,.live{grid-template-columns:1fr 1fr}}
@media (min-width:1024px){
.bento{grid-template-columns:repeat(4,1fr);grid-auto-rows:minmax(220px,auto)}
.t-zeus{grid-column:1/3;grid-row:1/3;min-height:0}
.t-big{grid-column:span 2;min-height:0}
.t-cta{grid-column:span 3}
.grid{grid-template-columns:repeat(6,1fr)}
}
'''

JS_BENTO = '''
var tabs=$$(".tab"),gcs=$$(".gc"),desc=d.getElementById("tab-d");
function sel(b,foco){tabs.forEach(function(o){var on=o===b;o.setAttribute("aria-selected",on?"true":"false");o.tabIndex=on?0:-1});
  var i=b.dataset.i;gcs.forEach(function(c){c.hidden=(" "+c.dataset.t+" ").indexOf(" "+i+" ")<0});desc.textContent=b.dataset.d;
  d.getElementById("tab-p").setAttribute("aria-labelledby",b.id);if(foco)b.focus()}
tabs.forEach(function(b,n){b.addEventListener("click",function(){sel(b);ev("site_aba",{aba:b.textContent})});
  b.addEventListener("keydown",function(x){var j=x.key==="ArrowRight"?n+1:x.key==="ArrowLeft"?n-1:x.key==="Home"?0:x.key==="End"?tabs.length-1:null;
    if(j===null)return;x.preventDefault();sel(tabs[(j+tabs.length)%tabs.length],true)})});
if(tabs[0])sel(tabs[0]);
'''

def site_bento(s):
    t = s['textos']; k = s['chave']
    zeus = reduzida(s['hero_img'], k, 'zeus', s.get('hero_largura', 520))
    cores = ['#2EE6D6', '#FFD23F', '#FF7AB6', '#FFFFFF', '#2EE6D6', '#FFD23F', '#C9B5FF']
    def meta(slug):
        m = [f'RTP teórico {rtp(slug)}' if rtp(slug) else None, f'até {maxw(slug)}' if maxw(slug) else None, ficha(slug).get('vol') and f'Vol. {ficha(slug)["vol"].lower()}']
        return ''.join(f'<b>{e(x)}</b>' for x in m if x)
    tiles = ''
    for i, slug in enumerate(s['bento_grandes']):
        txt = s['bento_textos'].get(slug, '')
        if i == 0:
            tiles += (f'<a class="t t-zeus bx" style="--c:#C9B5FF" data-cta="bento_{slug}" href="{play(s, slug, "bento_" + slug)}">'
                      f'<div><h3 class="k" style="font-size:clamp(26px,5vw,40px)">{e(nome(slug))}</h3><p>{e(txt)}</p></div><div class="m">{meta(slug)}</div>'
                      f'{capa(slug, alt="", cls="cv", lazy=False)}{arte(zeus, "Zeus, personagem do Gates of Olympus, apontando para o alto", cls="zeus", lazy=False, eager=True)}</a>')
        else:
            tiles += (f'<a class="t t-big bx" style="--c:{cores[i]}" data-cta="bento_{slug}" href="{play(s, slug, "bento_" + slug)}">'
                      f'<div style="display:flex;gap:14px;align-items:flex-start">{capa(slug, alt="", cls="cv", lazy=False)}<div><h3 class="k">{e(nome(slug))}</h3><p>{e(txt)}</p></div></div><div class="m">{meta(slug)}</div></a>')
    for i, slug in enumerate(s['bento_menores']):
        tiles += (f'<a class="t bx" style="--c:{cores[(i + 3) % len(cores)]}" data-cta="bento_{slug}" href="{play(s, slug, "bento_" + slug)}">'
                  f'{capa(slug, alt="", cls="cv")}<h3 class="k">{e(nome(slug))}</h3><div class="m">{meta(slug)}</div></a>')
    tiles += (f'<a class="t t-cta bx" data-cta="bento_cadastro" href="{utm(s, P["register"], "bento")}"><h3 class="k">Crie a conta e gire</h3>'
              f'<p>Cadastro em cerca de um minuto, Pix na hora e todos esses slots no navegador.</p></a>')
    tabs = ''; idx = {}
    for i, a in enumerate(s['abas']):
        tabs += (f'<button class="tab" role="tab" type="button" id="tab-{i}" data-i="{i}" data-d="{e(a["texto"])}" aria-controls="tab-p" '
                 f'aria-selected="{"true" if i == 0 else "false"}" tabindex="{0 if i == 0 else -1}">{e(a["nome"])}</button>')
        for slug in a['slugs']: idx.setdefault(slug, []).append(str(i))
    gcs = ''.join(f'<a class="gc" data-t="{" ".join(v)}" data-cta="mecanica_{n + 1}" href="{play(s, slug, "mecanica_" + slug)}"{"" if "0" in v else " hidden"}>'
                  f'{capa(slug, alt="")}<span>{e(nome(slug))}<small>{e(prov(slug))}{" · RTP " + rtp(slug) if rtp(slug) else ""}</small></span></a>'
                  for n, (slug, v) in enumerate(idx.items()))
    vs = ''
    for i, v in enumerate(s['versoes']):
        pair = ''.join(f'<a data-cta="versao_{slug}" href="{play(s, slug, "versao_" + slug)}">{capa(slug, alt="")}{e(nome(slug))}</a>' for slug in v['slugs'])
        vs += f'<article class="v bx" style="--c:{("#FFD23F", "#2EE6D6")[i % 2]}"><h3 class="k">{e(v["nome"])}</h3><p>{e(v["texto"])}</p><div class="pair">{pair}</div></article>'
    live = ''.join(f'<a class="lv bx" style="--c:{("#FF7AB6", "#C9B5FF")[i % 2]}" data-cta="live_{i + 1}" href="{play(s, x["slug"], "live_" + x["slug"])}">{capa(x["slug"], alt="")}'
                   f'<div><span class="tag k">Ao vivo</span><h3 class="k">{e(x["nome"])}</h3><p>{e(x["texto"])}</p></div></a>' for i, x in enumerate(s['live']))
    font = '<link rel="preload" as="font" type="font/woff2" href="assets/fonts/montserrat-Black.woff2" crossorigin>'
    return head(s, css_min(CSS_BENTO), zeus, font) + body(s) + f'''
<header class="top"><a class="logo k bx" href="/">Guia Pragmatic</a><a class="btn bx k" data-cta="topo_entrar" href="{utm(s, P['login'], 'topo_entrar')}">Entrar</a></header>
<main id="conteudo"><div class="w">
<section class="hero"><span class="stk k bx">{e(t['selo'])}</span><h1 class="k">{e(t['titulo_hero']).replace('sem ', '<span>sem ').replace('enrolação', 'enrolação</span>')}</h1><p>{e(t['sub_hero'])}</p>
<div class="ctas"><a class="btn btn-r bx k" data-cta="hero_cadastro" href="{utm(s, P['register'], 'hero')}">Criar conta {ARROW}</a><a class="btn btn-a bx k" data-cta="hero_provedor" href="{utm(s, P['pragmatic'], 'hero_provedor')}">Todos os Pragmatic</a></div></section>
<section class="bento" aria-label="Destaques da Pragmatic Play">{tiles}</section>
<section class="sec" id="mecanicas" aria-labelledby="mc-h"><h2 class="k" id="mc-h">{e(t['abas_titulo'])}</h2>
<div class="tabs" role="tablist" aria-label="Mecânicas">{tabs}</div>
<div class="pan bx" id="tab-p" role="tabpanel" aria-labelledby="tab-0" tabindex="0"><p id="tab-d">{e(s['abas'][0]['texto'])}</p><div class="grid">{gcs}</div></div></section>
<section class="sec" id="versoes" aria-labelledby="vs-h"><h2 class="k" id="vs-h">{e(t['versoes_titulo'])}</h2><div class="vs">{vs}</div></section>
<section class="sec" id="live" aria-labelledby="lv-h"><h2 class="k" id="lv-h">{e(t['live_titulo'])}</h2><div class="live">{live}</div></section>
<section class="fin bx"><h2 class="k">Escolha a mecânica. Defina o limite.</h2><p>Os slots da Pragmatic Play rodam direto no navegador do celular.</p>
<a class="btn btn-a bx k" data-cta="final_cadastro" href="{utm(s, P['register'], 'final')}">Criar conta grátis {ARROW}</a></section>
</div></main>
{footer(s)}
{script(JS_BENTO)}
</body></html>'''

# ================================================================ 5. HUD / terminal (guiadecrash)

CSS_HUD = '''
:root{--bg:#050807;--p:#0B1210;--g:#39FF88;--c:#22E4FF;--tx:#D7FFE9;--mu:#86B9A0;--al:#FF4D6D;--ln:rgba(57,255,136,.18);--focus:#22E4FF}
body{background-color:var(--bg);color:var(--tx);font:15px/1.6 ui-monospace,"SF Mono",Menlo,Consolas,"Liberation Mono",monospace}
body{background-image:linear-gradient(rgba(57,255,136,.06) 1px,transparent 1px),linear-gradient(90deg,rgba(57,255,136,.06) 1px,transparent 1px);background-size:32px 32px}
.w{max-width:1200px;margin:0 auto;padding:0 16px}
.top{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;border-bottom:1px solid var(--ln)}
.logo{color:var(--g);text-decoration:none;font-weight:700}
.logo b{display:inline-block;width:9px;height:17px;background:var(--g);vertical-align:-3px;margin-left:4px;animation:blink 1s steps(1) infinite}
@keyframes blink{50%{opacity:0}}
.b{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:46px;padding:0 18px;border:1px solid var(--g);color:var(--g);background:transparent;text-decoration:none;font:700 14px/1 ui-monospace,Menlo,monospace;text-transform:uppercase;letter-spacing:.06em;clip-path:polygon(8px 0,100% 0,100% calc(100% - 8px),calc(100% - 8px) 100%,0 100%,0 8px)}
.b:hover{background:rgba(57,255,136,.12)}
.b-g{background:var(--g);color:#031;border-color:var(--g)}
.b-g:hover{background:#7DFFB0}
.b-c{border-color:var(--c);color:var(--c)}
.b:disabled{opacity:.4;cursor:not-allowed}
.hero{display:grid;gap:22px;padding:26px 0 30px}
.tag{color:var(--c);font-size:12px;letter-spacing:.2em}
h1{font-size:clamp(30px,7.6vw,58px);line-height:1.05;letter-spacing:-.02em;margin:10px 0;color:#fff;text-shadow:0 0 18px rgba(57,255,136,.35)}
.sub{color:var(--mu);max-width:40em}
.hl{color:var(--g)}
.astro{width:120px;float:right;margin:0 0 6px 12px;filter:drop-shadow(0 0 16px rgba(34,228,255,.45))}
.ctas{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.sim{border:1px solid var(--g);background:rgba(11,18,16,.92);box-shadow:0 0 0 1px rgba(57,255,136,.15),0 0 40px rgba(57,255,136,.12)}
.sim-h{display:flex;justify-content:space-between;gap:10px;padding:8px 12px;border-bottom:1px solid var(--ln);font-size:12px;color:var(--mu);letter-spacing:.1em}
.sim-h #st{color:var(--g)}
.scr{position:relative;aspect-ratio:16/10}
.scr canvas{width:100%;height:100%;display:block}
.mul{position:absolute;left:0;right:0;top:34%;text-align:center;font-size:clamp(40px,11vw,76px);font-weight:800;color:var(--g);text-shadow:0 0 22px rgba(57,255,136,.6)}
.mul.x{color:var(--al);text-shadow:0 0 22px rgba(255,77,109,.6)}
.mul.ok{color:var(--c)}
.ctl{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:12px;border-top:1px solid var(--ln)}
.ctl label{grid-column:1/-1;display:flex;align-items:center;justify-content:space-between;gap:10px;color:var(--mu);font-size:13px}
.ctl input{width:120px;min-height:42px;background:#000;border:1px solid var(--ln);color:var(--tx);font:inherit;padding:0 10px}
.brd{display:grid;grid-template-columns:repeat(3,1fr);border-top:1px solid var(--ln);text-align:center}
.brd div{padding:8px 4px;border-right:1px solid var(--ln)}
.brd div:last-child{border:0}
.brd small{display:block;font-size:11px;color:var(--mu);letter-spacing:.06em}
.brd b{font-size:20px;color:var(--g)}
.hist{display:flex;gap:6px;flex-wrap:wrap;list-style:none;padding:10px 12px;margin:0;border-top:1px solid var(--ln);min-height:46px}
.hist li{padding:2px 8px;border:1px solid currentColor;font-size:12px}
.hist .lo{color:var(--al)}.hist .md{color:var(--c)}.hist .hi{color:var(--g)}
.warn{padding:10px 12px;font-size:12px;color:#FFD1D9;border-top:1px solid rgba(255,77,109,.5);background:rgba(255,77,109,.08)}
.sec{padding:34px 0;border-top:1px solid var(--ln)}
h2{font-size:clamp(22px,5vw,34px);color:#fff;margin-bottom:16px}
h2::before{content:"> ";color:var(--g)}
.ex{display:grid;gap:12px}
.exc{border:1px solid var(--ln);background:var(--p);padding:16px}
.exc h3{color:var(--c);font-size:14px;letter-spacing:.14em;margin-bottom:8px}
.exc p{color:var(--tx)}
.ls{list-style:none;padding:0;margin:0;border:1px solid var(--ln)}
.ls li{border-bottom:1px solid var(--ln)}
.ls li:last-child{border:0}
.ls a{display:grid;grid-template-columns:64px 1fr auto;gap:12px;align-items:center;padding:10px 12px;text-decoration:none}
.ls a:hover{background:rgba(57,255,136,.07)}
.ls img{width:64px;border:1px solid var(--ln)}
.ls b{color:#fff;display:block}
.ls small{color:var(--mu);font-size:12px}
.ls .go{color:var(--g);font-weight:700;font-size:13px}
.og{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}
.ogc{border:1px solid var(--c);text-decoration:none;display:flex;flex-direction:column;background:var(--p)}
.ogc:hover{box-shadow:0 0 0 1px var(--c),0 0 24px rgba(34,228,255,.25)}
.ogc img{width:100%;aspect-ratio:240/280;object-fit:cover}
.ogc span{padding:10px;font-size:13px;color:var(--mu)}
.ogc b{display:block;color:var(--c);font-size:15px;margin-bottom:2px}
.fin{padding:40px 16px;text-align:center;border-top:1px solid var(--ln)}
.fin p{color:var(--mu);margin:8px 0 18px}
.ft{border-top:1px solid var(--g);color:var(--mu)}
.ft a{color:var(--g)}.ft strong{color:var(--tx)}
@media (min-width:720px){.og{grid-template-columns:repeat(5,1fr)}.ex{grid-template-columns:repeat(3,1fr)}.astro{width:150px}}
@media (min-width:1024px){.hero{grid-template-columns:5fr 6fr;align-items:center;padding:48px 0}.ls{columns:2;column-gap:0}.ls li{break-inside:avoid;border-right:1px solid var(--ln)}}
'''

JS_HUD = '''
var cv=d.getElementById("cv"),cx=cv.getContext("2d"),mul=d.getElementById("mul"),st=d.getElementById("st"),go=d.getElementById("go"),out=d.getElementById("out"),au=d.getElementById("auto"),hist=d.getElementById("hist");
var nR=0,nW=0,nL=0,run=false,t0=0,cp=1,cash=0,pts=[],raf=0;
function fmt(v){return v.toFixed(2).replace(".",",")+"x"}
function size(){var r=cv.getBoundingClientRect(),k=w.devicePixelRatio||1;cv.width=Math.round(r.width*k);cv.height=Math.round(r.height*k);draw()}
function draw(){var W=cv.width,H=cv.height,k=w.devicePixelRatio||1;cx.clearRect(0,0,W,H);cx.strokeStyle="rgba(57,255,136,.12)";cx.lineWidth=1;
  for(var x=0;x<W;x+=40*k){cx.beginPath();cx.moveTo(x,0);cx.lineTo(x,H);cx.stroke()}for(var y=0;y<H;y+=40*k){cx.beginPath();cx.moveTo(0,y);cx.lineTo(W,y);cx.stroke()}
  if(!pts.length)return;var tm=Math.max(8,pts[pts.length-1][0]),mm=Math.max(2,pts[pts.length-1][1]*1.15),pad=16*k;
  function X(t){return pad+(W-2*pad)*t/tm}function Y(m){return H-pad-(H-2*pad)*(m-1)/(mm-1)}
  cx.beginPath();cx.moveTo(X(0),Y(1));pts.forEach(function(p){cx.lineTo(X(p[0]),Y(p[1]))});
  var crashed=!run&&nR>0;cx.strokeStyle=crashed?"#FF4D6D":"#39FF88";cx.lineWidth=3*k;cx.shadowColor=cx.strokeStyle;cx.shadowBlur=12*k;cx.stroke();cx.shadowBlur=0;
  cx.lineTo(X(pts[pts.length-1][0]),Y(1));cx.closePath();cx.fillStyle=crashed?"rgba(255,77,109,.10)":"rgba(57,255,136,.10)";cx.fill();
  var l=pts[pts.length-1];cx.fillStyle="#22E4FF";cx.beginPath();cx.arc(X(l[0]),Y(l[1]),5*k,0,7);cx.fill()}
function m(t){return Math.exp(.12*t)}
function tick(now){var t=(now-t0)/1000,v=Math.min(m(t),cp),a=parseFloat((au.value||"").replace(",","."));if(!cash&&a>1&&v>=a)retira(a);
  pts.push([t,v]);mul.textContent=fmt(v);if(v>=cp){end();return}draw();raf=requestAnimationFrame(tick)}
function start(){if(run)return;run=true;cash=0;pts=[];var u=Math.random();cp=Math.max(1,Math.floor(97/(1-u))/100);
  mul.className="mul";mul.textContent="1,00x";st.textContent="EM VOO";go.disabled=true;out.disabled=false;t0=performance.now();raf=requestAnimationFrame(tick);ev("site_simulador",{acao:"decolar"})}
function retira(v){if(!run||cash)return;cash=v||m((performance.now()-t0)/1000);if(cash>cp)cash=cp;out.disabled=true;st.textContent="RETIROU EM "+fmt(cash)}
function end(){run=false;cancelAnimationFrame(raf);nR++;if(cash){nW++;mul.className="mul ok";mul.textContent=fmt(cash)}else{nL++;mul.className="mul x";mul.textContent=fmt(cp)}
  st.textContent=(cash?"RETIROU EM "+fmt(cash)+" · ":"")+"QUEDA EM "+fmt(cp);go.disabled=false;out.disabled=true;go.textContent="Nova rodada";
  d.getElementById("rn").textContent=nR;d.getElementById("rw").textContent=nW;d.getElementById("rl").textContent=nL;
  var li=d.createElement("li");li.className=cp<1.5?"lo":cp<3?"md":"hi";li.textContent=fmt(cp);hist.insertBefore(li,hist.firstChild);while(hist.children.length>10)hist.removeChild(hist.lastChild);draw()}
go.addEventListener("click",start);out.addEventListener("click",function(){retira();ev("site_simulador",{acao:"retirar"})});
w.addEventListener("resize",size);size();
'''

def site_hud(s):
    t = s['textos']; k = s['chave']
    astro = reduzida(s['hero_img'], k, 'spaceman', s.get('hero_largura', 300))
    ex = ''.join(f'<article class="exc"><h3>[{e(x["t"])}]</h3><p>{e(x["p"])}</p></article>' for x in t['explica'])
    ls = ''
    for i, c in enumerate(s['crash']):
        slug = c['slug']; nm = c.get('nome', nome(slug))
        ls += (f'<li><a data-cta="crash_{i + 1}" href="{play(s, slug, "crash_" + slug)}">{capa(slug, alt="")}<span><b>{e(nm)}</b>'
               f'<small>{e(prov(slug))} · {("RTP teórico " + rtp(slug)) if rtp(slug) else "RTP: ver no jogo"}</small></span><span class="go">JOGAR &gt;</span></a></li>')
    og = ''.join(f'<a class="ogc" data-cta="original_{i + 1}" href="{play(s, o["slug"], "original_" + o["slug"])}">{capa(o["slug"], alt="")}'
                 f'<span><b>{e(nome(o["slug"]))}</b>{e(o["texto"])}{" RTP teórico " + rtp(o["slug"]) + "." if rtp(o["slug"]) else ""}</span></a>' for i, o in enumerate(s['originais']))
    return head(s, css_min(CSS_HUD), astro) + body(s) + f'''
<header class="top"><a class="logo" href="/">&gt; guia_de_crash<b aria-hidden="true"></b></a><a class="b" data-cta="topo_entrar" href="{utm(s, P['login'], 'topo_entrar')}">[ Entrar ]</a></header>
<main id="conteudo"><div class="w">
<section class="hero">
<div>{arte(astro, "Astronauta do SpaceMan acenando", cls="astro", lazy=False, eager=True)}<p class="tag">// {e(t['selo'])}</p><h1>{e(t['titulo_hero'])}</h1><p class="sub">{e(t['sub_hero'])}</p>
<div class="ctas"><a class="b b-g" data-cta="hero_cadastro" href="{utm(s, P['register'], 'hero')}">Criar conta {ARROW}</a><a class="b b-c" data-cta="hero_crash" href="{utm(s, P['crash'], 'hero_crash')}">Crash games</a></div></div>
<div class="sim" role="group" aria-labelledby="sim-t">
<div class="sim-h"><span id="sim-t">SIMULADOR // SEM VALOR REAL</span><span id="st" role="status">PRONTO</span></div>
<div class="scr"><canvas id="cv" aria-hidden="true"></canvas><div class="mul" id="mul" aria-hidden="true">1,00x</div></div>
<div class="ctl"><label for="auto">Saque automático (opcional, ex.: 1,50)<input id="auto" inputmode="decimal" placeholder="desligado" autocomplete="off"></label>
<button class="b b-g" id="go" type="button">Decolar</button><button class="b b-c" id="out" type="button" disabled>Retirar</button></div>
<div class="brd" aria-label="Placar da simulação"><div><small>RODADAS</small><b id="rn">0</b></div><div><small>RETIROU A TEMPO</small><b id="rw">0</b></div><div><small>CAIU ANTES</small><b id="rl">0</b></div></div>
<ol class="hist" id="hist" aria-label="Últimos pontos de queda da simulação"></ol>
<p class="warn">{e(t['aviso_sim'])}</p></div>
</section>
<section class="sec" aria-labelledby="ex-h"><h2 id="ex-h">Como funciona</h2><div class="ex">{ex}</div></section>
<section class="sec" id="lista" aria-labelledby="ls-h"><h2 id="ls-h">{e(t['lista_titulo'])}</h2><ul class="ls">{ls}</ul>
<p style="margin-top:16px"><a class="b" data-cta="lista_crash" href="{utm(s, P['crash'], 'lista_crash')}">Ver categoria crash completa</a></p></section>
<section class="sec" id="originais" aria-labelledby="og-h"><h2 id="og-h">{e(t['originais_titulo'])}</h2><div class="og">{og}</div></section>
<section class="fin"><h2 style="display:inline-block">Pronto para a rodada real?</h2><p>Defina um limite e um saque automático antes de começar.</p>
<a class="b b-g" data-cta="final_cadastro" href="{utm(s, P['register'], 'final')}">Criar conta grátis {ARROW}</a></section>
</div></main>
{footer(s)}
{script(JS_HUD)}
</body></html>'''

# ================================================================ 6. app de conversão / céu (guiaaviator)

CSS_APP = '''
:root{--ceu:#1E62E0;--ceu2:#7FB6FF;--sol:#FF9A4D;--sol2:#FFC36B;--card:#fff;--ink:#10233F;--mu:#4A5C78;--cta:#C73A08;--focus:#10233F}
body{background:#EAF2FF;color:var(--ink);font:17px/1.5 ui-rounded,"SF Pro Rounded",system-ui,-apple-system,"Segoe UI",sans-serif;padding-bottom:96px}
.w{max-width:1080px;margin:0 auto;padding:0 16px}
.sky{background:linear-gradient(180deg,#1546B8 0%,var(--ceu) 58%,#E07A3E 90%,var(--sol) 100%);color:#fff;position:relative;overflow:hidden;border-radius:0 0 36px 36px}
.top{display:flex;justify-content:space-between;align-items:center;padding:14px 16px;position:relative;z-index:2}
.logo{display:inline-flex;align-items:center;gap:8px;background:rgba(255,255,255,.2);backdrop-filter:blur(6px);padding:8px 14px;border-radius:999px;font-weight:800;text-decoration:none}
.pill{display:inline-flex;align-items:center;justify-content:center;gap:8px;min-height:48px;padding:0 20px;border-radius:999px;font-weight:800;text-decoration:none}
.pill-w{background:#fff;color:var(--ink)}
.pill-c{background:var(--cta);color:#fff;box-shadow:0 10px 24px -8px rgba(226,71,15,.7)}
.pill-c:hover{filter:brightness(1.06)}
.hero{position:relative;z-index:2;padding:12px 0 40px;display:grid;gap:22px;align-items:center}
.selo{display:inline-block;background:rgba(16,35,63,.35);padding:6px 12px;border-radius:999px;font-size:13px;font-weight:700}
h1{font-size:clamp(38px,10vw,72px);line-height:1;letter-spacing:-.02em;margin:12px 0;text-shadow:0 2px 12px rgba(16,35,63,.25)}
.hero p{font-size:19px;max-width:30em;text-shadow:0 1px 6px rgba(16,35,63,.3)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:16px}
.chips span{background:rgba(255,255,255,.22);padding:6px 12px;border-radius:999px;font-size:14px;font-weight:700}
.sun{position:absolute;right:-60px;bottom:-60px;width:260px;height:260px;border-radius:50%;background:radial-gradient(circle,#FFE6A8,#FFB867 60%,rgba(255,154,77,0) 70%)}
.cl{position:absolute;background:#fff;border-radius:999px;opacity:.75;height:26px}
.cl::before{content:"";position:absolute;width:50%;height:200%;left:20%;bottom:0;background:inherit;border-radius:50%}
.plane{position:absolute;left:0;top:0;width:86px;z-index:1;offset-path:path("M -100 260 C 120 200, 260 80, 520 120 S 900 40, 1300 20");animation:fly 9s linear infinite}
@keyframes fly{from{offset-distance:0%}to{offset-distance:100%}}
@supports not (offset-path:path("M0 0")){.plane{animation:fly2 9s linear infinite;top:30%}@keyframes fly2{from{transform:translateX(-120px) rotate(-8deg)}to{transform:translateX(110vw) rotate(-8deg)}}}
@media (prefers-reduced-motion:reduce){.plane{offset-path:none;left:auto;right:120px;top:18px;width:56px}}
.phone{background:#fff;color:var(--ink);border-radius:32px;padding:16px;box-shadow:0 30px 60px -20px rgba(16,35,63,.5);max-width:360px;width:100%;justify-self:center}
.phone .scr{border-radius:22px;overflow:hidden;position:relative;background:linear-gradient(#0E1C3A,#253F78)}
.phone .scr img{width:100%;aspect-ratio:240/280;object-fit:cover;opacity:.92}
.phone .mx{position:absolute;left:12px;bottom:12px;background:#fff;color:var(--ink);border-radius:14px;padding:6px 12px;font-weight:900;font-size:22px}
.phone p{font-size:14px;color:var(--mu);margin-top:10px}
.card{background:var(--card);border-radius:28px;padding:22px;box-shadow:0 10px 30px -14px rgba(16,35,63,.35);margin:18px 0}
.card h2{font-size:clamp(24px,6vw,34px);line-height:1.1;margin-bottom:12px}
.warn{display:flex;gap:12px;align-items:flex-start;background:#FFF4E5;border:2px solid #FFC36B}
.warn svg{flex:none}
.how{display:grid;gap:10px;list-style:none;padding:0;counter-reset:h}
.how li{display:grid;grid-template-columns:44px 1fr;gap:12px;align-items:center;background:#F2F6FF;border-radius:18px;padding:12px}
.how li::before{counter-increment:h;content:counter(h);display:grid;place-items:center;width:44px;height:44px;border-radius:14px;background:var(--ceu);color:#fff;font-weight:900;font-size:20px}
.steps{display:grid;gap:12px}
.st{display:grid;grid-template-columns:56px 1fr;gap:14px;align-items:center}
.st i{display:grid;place-items:center;width:56px;height:56px;border-radius:18px;background:linear-gradient(135deg,var(--sol2),var(--sol));color:#fff}
.st h3{font-size:18px}.st p{color:var(--mu);font-size:15px}
.gl{display:grid;gap:12px}
.g{display:grid;grid-template-columns:84px 1fr;gap:14px;align-items:center;background:#fff;border-radius:24px;padding:12px;text-decoration:none;box-shadow:0 8px 24px -14px rgba(16,35,63,.4)}
.g:hover{box-shadow:0 0 0 3px var(--ceu2),0 8px 24px -14px rgba(16,35,63,.4)}
.g img{width:84px;border-radius:16px}
.g b{font-size:18px;display:block}
.g small{display:block;color:var(--mu);font-size:14px;line-height:1.35}
.g .go{display:inline-flex;margin-top:8px;background:var(--cta);color:#fff;border-radius:999px;padding:6px 14px;font-weight:800;font-size:14px}
details{border-top:1px solid #E1E8F5}
summary{cursor:pointer;padding:16px 0;font-weight:800;list-style:none}
summary::-webkit-details-marker{display:none}
summary::after{content:"+";float:right;color:var(--ceu);font-size:22px;line-height:1}
details[open] summary::after{content:"\\2212"}
details p{padding-bottom:16px;color:var(--mu)}
.dock{position:fixed;left:12px;right:12px;bottom:calc(12px + env(safe-area-inset-bottom));z-index:20;display:flex;gap:10px;align-items:center;background:rgba(16,35,63,.92);backdrop-filter:blur(8px);padding:10px 10px 10px 18px;border-radius:999px;color:#fff;box-shadow:0 10px 30px rgba(16,35,63,.4)}
.dock span{flex:1;font-size:14px;line-height:1.2}
.dock b{display:block;font-size:16px}
.ft{background:var(--ink);color:#C7D3E8;border-radius:36px 36px 0 0;margin-top:30px}
.ft a{color:#fff}.ft strong{color:#fff}
@media (min-width:720px){.steps{grid-template-columns:repeat(3,1fr)}.st{grid-template-columns:1fr}.gl{grid-template-columns:1fr 1fr}}
@media (min-width:960px){body{padding-bottom:0}.dock{display:none}.hero{grid-template-columns:1.2fr .8fr;padding:30px 0 70px}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.two .card{margin:18px 0 0}}
'''

PLANE = ('<svg class="plane" viewBox="0 0 120 60" aria-hidden="true"><path d="M8 34 L46 30 L70 8 L80 8 L66 30 L100 28 C112 28 116 32 112 36 C108 38 104 38 100 38 '
         'L66 38 L80 58 L70 58 L46 40 L8 38 L2 46 L-4 46 L2 36 Z" fill="#fff"/><path d="M100 30 C108 30 110 33 108 35" fill="none" stroke="#2F7BF5" stroke-width="2"/></svg>')
ICONES = {
    'conta': '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 4.5-6 8-6s6.5 2 8 6"/></svg>',
    'pix': '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round" aria-hidden="true"><path d="M12 2l5 5-5 5-5-5zM12 12l5 5-5 5-5-5zM2 12l5-5 5 5-5 5zM12 12l5-5 5 5-5 5z"/></svg>',
    'aviao': '<svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" aria-hidden="true"><path d="M21 16v-2l-8-5V3.5a1.5 1.5 0 0 0-3 0V9l-8 5v2l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-5.5z"/></svg>'}

def site_app(s):
    t = s['textos']; k = s['chave']
    g0 = s['jogos'][0]['slug']
    how = ''.join(f'<li>{e(x)}</li>' for x in t['oque'])
    steps = ''.join(f'<div class="st"><i>{ICONES[p["icone"]]}</i><div><h3>{e(p["t"])}</h3><p>{e(p["p"])}</p></div></div>' for p in t['passos'])
    gl = ''.join(f'<a class="g" data-cta="jogo_{i + 1}" href="{play(s, j["slug"], "jogo_" + j["slug"])}">{capa(j["slug"], alt="")}<span><b>{e(nome(j["slug"]))}</b>'
                 f'<small>{e(prov(j["slug"]))}{" · RTP teórico " + rtp(j["slug"]) if rtp(j["slug"]) else ""}</small><small>{e(j["texto"])}</small><span class="go">Jogar</span></span></a>'
                 for i, j in enumerate(s['jogos']))
    clouds = ''.join(f'<span class="cl" style="left:{x}%;top:{y}px;width:{wd}px" aria-hidden="true"></span>' for x, y, wd in ((6, 90, 90), (62, 60, 120), (40, 220, 70), (80, 300, 100)))
    info = '<svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#E2470F" stroke-width="2.2" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="10"/><path d="M12 8h.01M11 12h1v5h1"/></svg>'
    return head(s, css_min(CSS_APP), web(g0)) + body(s) + f'''
<div class="sky"><div class="sun" aria-hidden="true"></div>{clouds}{PLANE}
<header class="top"><a class="logo" href="/">✈ {e(s['nome'])}</a><a class="pill pill-w" data-cta="topo_entrar" href="{utm(s, P['login'], 'topo_entrar')}">Entrar</a></header>
<div class="w"><section class="hero">
<div><span class="selo">{e(t['selo'])}</span><h1>{e(t['titulo_hero'])}</h1><p>{e(t['sub_hero'])}</p>
<div class="chips"><span>Pix na hora</span><span>No navegador</span><span>18+</span></div>
<p style="margin-top:20px"><a class="pill pill-c" data-cta="hero_cadastro" href="{utm(s, P['register'], 'hero')}">Criar conta e decolar {ARROW}</a></p></div>
<div class="phone" aria-hidden="true"><div class="scr">{capa(g0, alt="", lazy=False, eager=True)}<span class="mx">2,37x</span></div><p>Ilustração. Multiplicador de exemplo, sem valor real.</p></div>
</section></div></div>
<main id="conteudo" class="w">
<section class="card warn" aria-label="Aviso">{info}<p><strong>Importante:</strong> {e(t['aviso_aviator'])}</p></section>
<div class="two">
<section class="card" aria-labelledby="oq-h"><h2 id="oq-h">{e(t['oque_titulo'])}</h2><ol class="how">{how}</ol></section>
<section class="card" aria-labelledby="ps-h"><h2 id="ps-h">{e(t['passos_titulo'])}</h2><div class="steps">{steps}</div>
<p style="margin-top:18px"><a class="pill pill-c" data-cta="passos_cadastro" href="{utm(s, P['register'], 'passos')}">Começar agora {ARROW}</a></p></section>
</div>
<section aria-labelledby="jg-h" style="margin-top:28px"><h2 id="jg-h" style="font-size:clamp(24px,6vw,34px);margin-bottom:14px">{e(t['jogos_titulo'])}</h2><div class="gl">{gl}</div>
<p style="margin-top:16px"><a class="pill pill-w" style="box-shadow:0 0 0 2px var(--ink) inset" data-cta="lista_crash" href="{utm(s, P['crash'], 'lista_crash')}">Ver todos os crash games</a></p></section>
<section class="card" aria-labelledby="fq-h"><h2 id="fq-h">Perguntas rápidas</h2>{faq(t['faq'])}</section>
</main>
<div class="dock"><span>Jogos de voo<b>Cadastro em 1 minuto</b></span><a class="pill pill-c" data-cta="dock_cadastro" href="{utm(s, P['register'], 'dock')}">Criar conta</a></div>
{footer(s)}
{script()}
</body></html>'''

# ---------------------------------------------------------------- saída e verificador

RENDER = {'revista': site_revista, 'dashboard': site_dash, 'festival': site_fest, 'bento': site_bento, 'hud': site_hud, 'app': site_app}

def page_404(s):
    c = list(s['cores'].values())
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Página não encontrada | {e(s['nome'])}</title><meta name="robots" content="noindex,nofollow"><meta http-equiv="refresh" content="3;url=/">
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;text-align:center;font-family:system-ui,sans-serif;background:{c[0]};color:{c[2] if s['estilo'] in ('revista', 'bento') else '#fff'};padding:24px}}a{{color:inherit;font-weight:800}}</style></head>
<body><main><h1>Página não encontrada</h1><p>Você vai voltar para o {e(s['nome'])} em instantes.</p><p><a href="/">Ir para a página inicial</a></p></main></body></html>'''

ASSET_RE = re.compile(r'assets/[A-Za-z0-9_./-]+?\.(?:webp|jpe?g|png|mp4|woff2|svg|gif)')
PLAT_RE = re.compile(re.escape(BASE) + r'[^"\'\s<>)]*')

def visible_text(t):
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', t, flags=re.S)
    return re.sub(r'<[^>]+>', ' ', t)

def check(dst, s):
    """Verificador: assets existem, sem travessão, sem link para oficial-spribe, links da plataforma com utm_campaign, index < 150 KB."""
    for f in sorted(os.listdir(dst)):
        if not f.endswith('.html'): continue
        t = open(os.path.join(dst, f), encoding='utf-8').read()
        for ref in set(ASSET_RE.findall(t)):
            assert os.path.exists(os.path.join(dst, ref)), (s['dominio'], f, 'asset ausente', ref)
        for ch in DASH:
            assert ch not in t, (s['dominio'], f, 'travessão no HTML', visible_text(t)[max(0, visible_text(t).find(ch) - 60):][:120])
        assert 'oficial-spribe' not in t, (s['dominio'], f, 'link para oficial-spribe')
        for u in PLAT_RE.findall(t):
            assert f'utm_campaign={s["chave"]}' in u, (s['dominio'], f, 'link sem utm_campaign', u)
        for tag in re.findall(r'<img\b[^>]*>', t):
            assert all(a in tag for a in (' width=', ' height=', ' alt=')), (s['dominio'], f, 'img sem width/height/alt', tag[:120])
        for pre in re.findall(r'<link rel="preload" as="image" href="([^"]+)"', t):
            kb = os.path.getsize(os.path.join(dst, pre)) / 1024
            assert kb < 120, (s['dominio'], f, 'imagem do hero pesada', pre, kb)
        kb = len(t.encode('utf-8')) / 1024
        if f == 'index.html': assert kb < 150, (s['dominio'], 'index.html com', kb, 'KB')
        print(f'dist-sites/{s["dominio"]}/{f}', f'{kb:.0f} KB')

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    for s in SITES:
        dst = os.path.join(OUT, s['dominio'])
        if os.path.exists(dst): shutil.rmtree(dst)  # só a pasta deste site, gerada por este script
        os.makedirs(dst)
        t = RENDER[s['estilo']](s)
        open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(t)
        for ref in sorted(set(ASSET_RE.findall(t))):
            src = os.path.join(R, ref)
            if not os.path.exists(src): continue  # o verificador acusa o que faltar
            os.makedirs(os.path.dirname(os.path.join(dst, ref)), exist_ok=True)
            shutil.copy2(src, os.path.join(dst, ref))
        open(os.path.join(dst, '404.html'), 'w', encoding='utf-8').write(page_404(s))
        open(os.path.join(dst, 'CNAME'), 'w').write(s['dominio'] + '\n')
        open(os.path.join(dst, '.nojekyll'), 'w').write('')
        open(os.path.join(dst, 'robots.txt'), 'w').write('User-agent: *\nDisallow: /\n')
        check(dst, s)
    print('ok:', len(SITES), 'sites em dist-sites/')
