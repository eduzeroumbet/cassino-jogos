#!/usr/bin/env python3
"""Gera as landing pages estáticas a partir de data/games.json:
- docs/: site do GitHub Pages (hub, uma página por jogo e o banco de personagens)
- dist-dominios/<dominio>/: uma landing por jogo, pronta para o domínio próprio de cada jogo
Artes oficiais do acervo (data/acervo.json): fundo, logo PT e personagem no hero, cards de assets/sites/cards/ (build_sites.py)
e og:image 1200x630 em assets/og/<jogo>.jpg (Pillow, só quando falta ou com --imagens).
Uso: python3 build.py [--imagens]"""
import json, os, shutil, html, re, sys
R = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(R, 'data/games.json'), encoding='utf-8'))
S = D['site']; G = D['games']
CAT = json.load(open(os.path.join(R, 'data/personagens.json'), encoding='utf-8'))
ACJ = json.load(open(os.path.join(R, 'data/acervo.json'), encoding='utf-8'))['jogos']  # chave do jogo -> bg, banner, square, logo, char
FORCE = '--imagens' in sys.argv
OUT = os.path.join(R, 'docs')
DIST = os.path.join(R, 'dist-dominios')
CSS = open(os.path.join(R, 'src/lp.css'), encoding='utf-8').read().replace('../assets/', 'assets/')
JS = open(os.path.join(R, 'src/lp.js'), encoding='utf-8').read()
PJS = open(os.path.join(R, 'src/personagens.js'), encoding='utf-8').read()
CSS = re.sub(r'\s*\n\s*', '', CSS)
e = lambda s: html.escape(str(s), quote=True)
BASE = S['base'].rstrip('/')
PAGES = S['pages_url'].rstrip('/')
DOM = S.get('domains', {}); ACTIVE = bool(S.get('domains_active'))
TRANSP = {i['web']: i['transparente'] for i in CAT}
THUMB = {i['web']: i['thumb'] for i in CAT}
GIF = 'data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=='

def webp_size(p):
    """Largura e altura de um WebP lendo só o cabeçalho (VP8X, VP8 ou VP8L)."""
    b = open(os.path.join(R, p), 'rb').read(30)
    assert b[:4] == b'RIFF' and b[8:12] == b'WEBP', p
    ch = b[12:16]
    if ch == b'VP8X': return 1 + int.from_bytes(b[24:27], 'little'), 1 + int.from_bytes(b[27:30], 'little')
    if ch == b'VP8 ': return int.from_bytes(b[26:28], 'little') & 0x3fff, int.from_bytes(b[28:30], 'little') & 0x3fff
    v = int.from_bytes(b[21:25], 'little'); return (v & 0x3fff) + 1, ((v >> 14) & 0x3fff) + 1

# Endereços. domains_active=false: tudo no GitHub Pages, como antes. true: canonical, og e links entre jogos vão para o domínio de cada jogo.
def game_url(k):
    return f'https://{DOM[k]}/' if ACTIVE and k in DOM else f'{PAGES}/{k}.html'

def game_root(k):
    return f'https://{DOM[k]}' if ACTIVE and k in DOM else PAGES

def game_href(k, mode):
    return f'{k}.html' if mode == 'pages' and not ACTIVE else game_url(k)

def hub_href(mode):
    return './' if mode == 'pages' else f'{PAGES}/'

POS = ('header', 'hero', 'vitrine', 'final')  # utm_content: posição do link na página (o data-cta do GA4 detalha o botão)

def utm(path, key, pos):
    assert pos in POS, pos
    sep = '&' if '?' in path else '?'
    return f"{BASE}{path}{sep}utm_source=landing&utm_medium=guia&utm_campaign={key}&utm_content={pos}"

SAIDA_RE = re.compile(r'<a ((?:(?!rel=)[^>])*?href="' + re.escape(BASE) + r'[^"]*"[^>]*)>')

def saida(t):
    """Links de saída para a plataforma com rel="sponsored noopener"."""
    return SAIDA_RE.sub(r'<a \1 rel="sponsored noopener">', t)

def play_url(g):
    return f"/cassino/jogar/{g['provider_code']}/{g['slug']}"

ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z"/></svg>'

def head(title, desc, og, canonical, accent, preload=None, extra='', noindex=False, og_alt=None):
    """preload: (src, srcset, sizes) da imagem do hero."""
    robots = 'index,follow' if S.get('indexar') and not noindex else 'noindex,nofollow'
    pl = ''
    if preload:
        pl = f'<link rel="preload" as="image" href="{preload[0]}" imagesrcset="{preload[1]}" imagesizes="{preload[2]}" fetchpriority="high">'
    oa = f'<meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta property="og:image:alt" content="{e(og_alt)}">' if og_alt else ''
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><meta name="robots" content="{robots}">
<meta name="theme-color" content="#0B1430"><link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{og}">{oa}<meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image"><meta name="twitter:image" content="{og}">
<link rel="preload" as="font" type="font/woff2" href="assets/fonts/montserrat-Black.woff2" crossorigin>
<link rel="preconnect" href="{BASE}">{pl}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='9' fill='%23FF3D5A'/%3E%3C/svg%3E">
<style>{CSS}:root{{--acc:{accent}}}</style>{extra}</head>'''

def top(key, hub='./'):
    """Cabeçalho fixo (sticky): logo, "Jogos" (só no desktop), "Entrar" e "Criar conta"."""
    return (f'<header class="top"><a class="logo" href="{hub}" aria-label="{e(S["brand"])}: todos os jogos"><i></i><span>{e(S["brand"])}</span></a>'
            f'<nav class="top-nav" aria-label="Conta"><a class="top-jogos" href="{hub}">Jogos</a>'
            f'<a class="btn-sm" data-cta="topo_entrar" href="{utm("/login", key, "header")}">Entrar</a>'
            f'<a class="btn-sm btn-acc" data-cta="topo_cadastro" href="{utm(S["register"], key, "header")}">Criar conta</a></nav></header>')

def footer(key, hub='./'):
    return f'''<footer><div class="wrap"><div class="rg"><span class="age">18+</span><p>Proibido para menores de 18 anos. Jogue com responsabilidade: defina um valor por sessão, faça pausas e não trate o jogo como fonte de renda. Os valores de RTP são teóricos, informados pelos provedores, e não garantem resultado.</p></div>
<nav><a href="{hub}">Todos os jogos</a><a data-cta="rodape_cassino" href="{utm("/cassino", key, "final")}">Cassino</a><a data-cta="rodape_cadastro" href="{utm(S["register"], key, "final")}">Criar conta</a><a href="{utm("/usuario/carteira", key, "final")}">Depósito Pix</a></nav>
<nav class="docs" aria-label="Documentos da plataforma"><a href="{utm("/pagina/terms", key, "final")}">Termos e Condições</a><a href="{utm("/pagina/privacy", key, "final")}">Política de Privacidade</a><a href="{utm("/pagina/responsible-gaming", key, "final")}">Jogo Responsável</a><a href="{utm("/faq", key, "final")}">Central de Ajuda</a></nav>
<p>Página informativa de {e(S["brand"])}. Os jogos citados pertencem aos respectivos provedores.</p></div></footer>'''

def pic(k, cls='', eager=False):
    """Arte de fundo do hero sem acervo (Mines): decorativa, alt vazio e aria-hidden."""
    pr = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img class="{cls}" src="assets/img/{k}-hero-600.webp" srcset="assets/img/{k}-hero-600.webp 600w, assets/img/{k}-hero-896.webp 896w" '
            f'sizes="(min-width:1024px) 58vw, 100vw" width="896" height="1200" alt="" aria-hidden="true" {pr}>')

# ---------------------------------------------------------------- artes oficiais do acervo

def acv(k, tipo):
    """Arquivos de um tipo (bg, banner, square, logo, char) do acervo do jogo, do maior para o menor; [] se não houver."""
    return ACJ.get(k, {}).get(tipo) or []

def hero_bg(k):
    """Fundo do hero: o fundo oficial do jogo; sem ele, a arte quadrada (os banners trazem faixa legal e, no Sweet Bonanza, são de outra versão)."""
    return acv(k, 'bg') or acv(k, 'square')

HERO_SIZES = '(orientation:portrait) 140vh, 100vw'  # no celular em pé a arte larga cobre a altura da tela

def hero_preload(k):
    bg = hero_bg(k)
    if not bg: return (f'assets/img/{k}-hero-600.webp', f'assets/img/{k}-hero-600.webp 600w, assets/img/{k}-hero-896.webp 896w', '(min-width:1024px) 58vw, 100vw')
    return bg[-1]['arquivo'], ', '.join(f'{i["arquivo"]} {i["w"]}w' for i in reversed(bg)), HERO_SIZES

def hero_art(g):
    """Fundo do topo (decorativo: alt vazio e aria-hidden): arte oficial do acervo (WebP até 1600 px, carregada antes de tudo, sem lazy);
    o escurecimento vem do .hero:after. Jogo sem acervo (Mines) mantém a arte própria."""
    k = g['key']; bg = hero_bg(k)
    if not bg: return pic(k, eager=True)
    src, srcset, sizes = hero_preload(k)
    return (f'<img src="{src}" srcset="{srcset}" sizes="{sizes}" width="{bg[0]["w"]}" height="{bg[0]["h"]}" '
            f'alt="" aria-hidden="true" fetchpriority="high">')

def hero_title(g):
    """Título do hero: o logo oficial em português do acervo (alt = nome do jogo); sem logo, o nome em letras grandes.
    O h1 é texto ("<jogo>: como jogar, RTP e recursos"), logo abaixo, maior que a frase de apoio, que fica como subtítulo."""
    lg = acv(g['key'], 'logo')
    h1 = f'<h1 class="h1-txt">{e(g["name"])}: como jogar, RTP e recursos</h1>'
    if not lg: return f'<p class="hname">{h1name(g["name"])}</p>{h1}'
    l = lg[0]
    return f'<p class="h1-logo"><img src="{l["arquivo"]}" width="{l["w"]}" height="{l["h"]}" alt="{e(g["name"])}" decoding="async"></p>{h1}'

def meta_desc(g):
    """Meta description: o campo "description" do jogo (até 150 caracteres, frase completa); sem ele, nome, provedor e lede
    até 150 caracteres: no fim da última frase completa, se houver uma com pelo menos 80; senão na última palavra inteira, com ponto."""
    if g.get('description'):
        d = g['description']
        assert len(d) <= 150 and d.endswith(('.', '!', '?')), f'description de {g["key"]}: até 150 caracteres e frase completa'
        return d
    d = f'{g["name"]} ({g["provider"]}): {g["lede"]}'
    if len(d) <= 150: return d
    fim = max(d.rfind(x, 0, 150) for x in ('. ', '! ', '? '))
    if fim >= 79: return d[:fim + 1]
    c = d[:149]  # 149 + o ponto final
    if d[149] != ' ': c = c[:c.rfind(' ')]
    return c.rstrip(' ,;:.!?') + '.'

def cover_alt(g):
    """Alt das capas e artes de card: "Nome do jogo, Provedor"."""
    return f'{g["name"]}, {g["provider"]}'

def thumb(k):
    """Imagem do card: composição oficial do acervo (assets/sites/cards/<jogo>.webp, do build_sites.py); sem ela, a capa do catálogo."""
    p = f'assets/sites/cards/{k}.webp'
    return p if os.path.exists(os.path.join(R, p)) else f'assets/img/{k}-thumb.webp'

OG_FEITAS = set()  # com --imagens, cada OG é refeita uma vez por execução

def og_image(g):
    """og:image 1200x630 com as artes oficiais do acervo em assets/og/<jogo>.jpg (Pillow, só quando falta ou com --imagens).
    Com logo: fundo do jogo, escurecido à esquerda, logo PT à esquerda e personagem à direita (sem personagem, logo ao centro).
    Sem logo: composição do build_sites.py (banner sem a faixa legal ou a arte indicada em og_arte). Sem acervo (Mines): a OG antiga."""
    k = g['key']
    if k not in ACJ: return f'assets/img/{k}-og.jpg'
    p = f'assets/og/{k}.jpg'
    if (not FORCE or p in OG_FEITAS) and os.path.exists(os.path.join(R, p)): return p
    OG_FEITAS.add(p)
    from PIL import Image, ImageFilter, ImageOps
    import build_sites
    W, H = 1200, 630
    abre = lambda i: Image.open(os.path.join(R, i[0]['arquivo'])).convert('RGBA')
    bg, logo, char = hero_bg(k), acv(k, 'logo'), acv(k, 'char')
    if bg and logo:
        im = ImageOps.fit(abre(bg), (W, H), Image.LANCZOS)
        mask = Image.linear_gradient('L').rotate(90).resize((W, H))  # 255 à esquerda, 0 à direita
        dark = Image.new('RGBA', (W, H), (11, 20, 48, 255)); dark.putalpha(mask.point(lambda v: 60 + v * 150 // 255 if char else 110))
        im = Image.alpha_composite(im, dark)
        if char:
            c = abre(char); h = 600; c = c.resize((round(c.width * h / c.height), h), Image.LANCZOS)
            if c.width > 520: c = c.resize((520, round(c.height * 520 / c.width)), Image.LANCZOS)
            x = W - c.width - 50; y = H - c.height
            sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.paste((0, 0, 0, 140), (x + 14, y + 10), c.split()[3])
            im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(16)))
            im.alpha_composite(c, (x, y))
        lg = abre(logo); bw, bh = (600, 470) if char else (760, 520)
        s = min(bw / lg.width, bh / lg.height); lg = lg.resize((round(lg.width * s), round(lg.height * s)), Image.LANCZOS)
        x = (60 + (640 - lg.width) // 2) if char else (W - lg.width) // 2; y = (H - lg.height) // 2
        sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sh.paste((0, 0, 0, 160), (x, y + 8), lg.split()[3])
        im = Image.alpha_composite(im, sh.filter(ImageFilter.GaussianBlur(12)))
        im.alpha_composite(lg, (x, y))
    else:  # arte inteira (banner sem a faixa legal, ou a de og_arte) sobre ela mesma desfocada, sem cortar o logo
        t = g.get('og_arte') or next(t for t in ('banner', 'square', 'bg') if acv(k, t))
        src = abre(acv(k, t))
        if t == 'banner': src = build_sites.sem_faixa(src)
        im = ImageOps.fit(src, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(18))
        im = Image.alpha_composite(im, Image.new('RGBA', (W, H), (11, 20, 48, 90)))
        s = min(W / src.width, H / src.height); a = src.resize((round(src.width * s), round(src.height * s)), Image.LANCZOS)
        im.alpha_composite(a, ((W - a.width) // 2, (H - a.height) // 2))
    os.makedirs(os.path.dirname(os.path.join(R, p)), exist_ok=True)
    im.convert('RGB').save(os.path.join(R, p), 'JPEG', quality=84, optimize=True, progressive=True)
    return p

def words(t):
    return ' '.join(f'<span class="w" style="--i:{i}">{e(x)}</span>' for i, x in enumerate(t.split()))

def h1name(n):
    p = n.split(' ', 1)
    return e(p[0]) if len(p) == 1 else f'{e(p[0])}<em>{e(p[1])}</em>'

def metric(m):
    pre = f'<span class="pre">{e(m["prefix"])}</span>' if m.get('prefix') else ''
    if m['type'] == 'text':
        return f'<div class="m m-text"><small>{e(m["label"])}</small><strong>{e(m["text"])}</strong></div>'
    if m['type'] == 'level':
        lv = ''.join(f'<i class="{"f" if i < m["value"] else ""}"></i>' for i in range(3))
        return f'<div class="m"><small>{e(m["label"])}</small><strong>{e(m["text"])}</strong><div class="lv" aria-hidden="true">{lv}</div></div>'
    v = m['value']; txt = f'{v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.') if isinstance(v, float) else f'{v:,}'.replace(',', '.')
    sfx = e(m.get('suffix', ''))
    body = f'<strong>{pre}<span data-to="{v}">{txt}</span>{sfx}</strong>'
    bar = f'<div class="bar" aria-hidden="true"><i data-w="{v / m.get("max", 100) * 100:.1f}"></i></div>' if m['type'] == 'bar' else ''
    return f'<div class="m"><small>{e(m["label"])}</small>{body}{bar}</div>'

def rtp(g):
    """RTP do card: "RTP 96,81%" (com o prefixo da métrica, ex.: "RTP até 98,89%")."""
    m = next(m for m in g['metrics'] if 'RTP' in m['label'])
    return f'RTP {m.get("prefix", "")}{m["value"]:.2f}%'.replace('.', ',')

def card(g, href, sub, lazy=True, com_rtp=False):
    """Card de jogo: link rastreável (data-cta). lazy=False no carrossel "Outros favoritos": com lazy e decoding async,
    no desktop alguns cards apareciam só como bloco de cor. com_rtp: linha "RTP 96,81%" abaixo da grade (index)."""
    lz = 'loading="lazy" decoding="async" ' if lazy else ''
    t = thumb(g['key']); w, h = webp_size(t)
    r = f'<small class="rtp">{e(rtp(g))}</small>' if com_rtp else ''
    return (f'<a class="card" href="{href}" data-cta="card_{g["key"]}" style="--ca:{g["accent"]}"><img src="{t}" width="{w}" height="{h}" {lz}alt="{e(cover_alt(g))}">'
            f'<span>{e(g["name"])}<small>{e(sub)}</small>{r}</span></a>')

def art_view(p, crop=None):
    """Tamanho, classe da moldura, estilo da moldura e estilo da imagem da arte p.
    Com "crop" [x, y, w, h] (px da versão web), mostra só esse recorte, em CSS."""
    w, h = webp_size(p)
    if crop:
        x, y, cw, ch = crop
        return w, h, 'ch-art ch-crop', f'aspect-ratio:{cw}/{ch}', f'width:{w / cw * 100:.2f}%;left:-{x / cw * 100:.2f}%;top:-{y / ch * 100:.2f}%'
    if TRANSP.get(p): return w, h, 'ch-art cut', '', ''
    return w, h, 'ch-art', f'aspect-ratio:{w}/{h}', ''

def art_ok(p):
    """Arte de personagem válida: está no catálogo (com miniatura), o arquivo e a miniatura existem e o cabeçalho WebP é legível."""
    try:
        return bool(p) and p in THUMB and os.path.isfile(os.path.join(R, THUMB[p])) and webp_size(p)[0] > 1
    except (OSError, AssertionError):
        return False

def char_section(g, mode='pages'):
    """Bloco "Conheça o personagem". A arte grande está no HTML com src real e width/height, sem loading lazy e sem
    decoding="async": com async, o Chrome adia a decodificação de imagens fora da tela e capturas de página inteira e rolagens
    rápidas mostravam só a moldura (retângulo branco ou a mancha do fundo). Se falhar, troca pela capa do jogo.
    Sem nenhuma arte válida, o bloco fica só com o texto. Quando a arte principal já aparece no hero, o bloco abre com outra pose.
    As miniaturas são botões: ao tocar, trocam a arte grande (src/lp.js)."""
    c = g.get('character')
    if not c: return ''
    k = g['key']
    arts = [(c.get('main'), c.get('crop'), c.get('alt') or c['name'])] + [(p, None, f'{c["name"]}, outra pose') for p in c.get('extras', [])]
    arts = [a for a in arts if art_ok(a[0])]
    hc = hero_char_art(g)
    if hc and arts and hc[0] == arts[0][0] and len(arts) > 1: arts = arts[1:] + arts[:1]
    art = ''
    if arts:
        p, crop, alt = arts[0]
        w, h, cls, box, ist = art_view(p, crop)
        fb = (f"this.onerror=null;var a=this.parentNode;a.className='ch-art';a.style.aspectRatio='300/350';this.removeAttribute('style');"
              f"this.width=300;this.height=350;this.src='assets/img/{k}-thumb.webp'")
        sty = f' style="{ist}"' if ist else ''
        art = (f'<div class="{cls}" style="{box}"><img id="ch-img" src="{p}" width="{w}" height="{h}" alt="{e(alt)}" fetchpriority="low" '
               f'onerror="{fb}"{sty}></div>')
    xs = ''
    if len(arts) > 1:
        for i, (p, crop, alt) in enumerate(arts):
            w, h, cls, box, ist = art_view(p, crop); t = THUMB[p]; tw, th = webp_size(t)
            xs += (f'<button type="button" aria-pressed="{"true" if i == 0 else "false"}" aria-label="Ver {e(alt)}" data-src="{p}" data-w="{w}" data-h="{h}" '
                   f'data-alt="{e(alt)}" data-cls="{cls}" data-box="{box}" data-img="{ist}"><img src="{t}" width="{tw}" height="{th}" decoding="async" alt="" aria-hidden="true"></button>')
        xs = f'<div class="ch-x" aria-label="Outras artes do personagem">{xs}</div>'
    todos = 'personagens.html' if mode == 'pages' else f'{PAGES}/personagens.html'
    return f'''
<section class="s" id="personagem"><div class="wrap ch{"" if art else " no-art"}">
{art}
<div><p class="eyebrow">Conheça o personagem</p><h2><span class="hl">{e(c['name'])}</span></h2>
<p class="sub">{e(c['bio'])}</p>{xs}<p class="ch-all"><a href="{todos}">Ver todos os personagens</a></p></div>
</div></section>
'''

def hero_char_art(g):
    """(caminho, alt) do personagem recortado do hero: o oficial do acervo (char-1); sem ele, a arte principal do jogo
    se tiver fundo transparente (Zeus) e o personagem não tiver "hero": false; senão None (Fortune Tiger, cujo pacote não traz personagem, e os jogos do elenco da casa)."""
    ch = acv(g['key'], 'char')
    c = g.get('character') or {}
    nome = c.get('name') or 'Personagem'
    if ch: return ch[0]['arquivo'], f'{nome}, personagem oficial do {g["name"]}'
    if c and not c.get('crop') and c.get('hero', True) and TRANSP.get(c['main']): return c['main'], c['alt']
    return None

def hero_char(g):
    """Personagem em destaque no hero, em todas as telas: no celular no alto, acima do texto; no desktop (>= 960 px) à direita.
    Sem lazy (está na primeira dobra) e com width/height reais."""
    a = hero_char_art(g)
    if not a: return ''
    w, h = webp_size(a[0])
    return f'<img class="hero-ch" src="{a[0]}" width="{w}" height="{h}" alt="{e(a[1])}" decoding="async">'

FAQ_OBRIG = ('Qual o valor mínimo de aposta?', 'Como sacar?', 'Funciona no celular?', 'O que é RTP?')

def game_page(g, mode='pages'):
    k = g['key']; n = g['name']
    reg = utm(S['register'], k, 'hero'); play = utm(play_url(g), k, 'vitrine')
    title = f'{n}: como jogar, RTP e recursos | {S["brand"]}'
    desc = meta_desc(g)
    canonical = game_url(k); og = f'{game_root(k)}/{og_image(g)}'
    hub = hub_href(mode); hc = hero_char(g)
    assert 5 <= len(g['faq']) <= 6, f'FAQ de {k}: de 5 a 6 perguntas'
    falta = set(FAQ_OBRIG) - {f['q'] for f in g['faq']}
    assert not falta, f'FAQ de {k}: faltam {sorted(falta)}'
    faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f['q'], "acceptedAnswer": {"@type": "Answer", "text": f['a']}} for f in g['faq']]}, ensure_ascii=False)
    if g.get('video'):
        media = (f'<video muted loop playsinline preload="none" poster="assets/img/{k}-thumb.webp" data-src="assets/video/{g["video"]}.mp4" '
                 f'width="300" height="375" aria-label="Prévia do {e(n)}"></video>')
    else:
        media = f'<img class="kb" src="assets/img/{k}-thumb.webp" width="300" height="350" loading="lazy" decoding="async" alt="{e(cover_alt(g))}">'
    promo = ''
    if g.get('promo'):
        pr = g['promo']; note = ''
        if pr.get('note'):  # com note_url, a nota vira link (ex.: página de promoções da plataforma)
            nt = f'<a data-cta="promo_regras" href="{utm(pr["note_url"], k, "vitrine")}">{e(pr["note"])}</a>' if pr.get('note_url') else e(pr['note'])
            note = f'<small>{nt}</small>'
        promo = f'<p class="promo">{e(pr["text"])} <a data-cta="promo" href="{utm(pr["url"], k, "vitrine")}">Ver campanha</a>{note}</p>'
    feats = ''.join(f'<button class="xcard" type="button" data-k="{e(f["title"])}" aria-expanded="{"true" if i == 0 else "false"}"><span class="n">0{i + 1}</span><h3>{e(f["title"])}</h3><p>{e(f["text"])}</p></button>'
                    for i, f in enumerate(g['features']))
    others = ''.join(card(o, game_href(o['key'], mode), o['provider'], lazy=False) for o in G if o['key'] != k)
    faqs = ''.join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in g['faq'])
    style = f'<style>:root{{--acc:{g["accent"]};--acc2:{g.get("accent2", "#FF3D5A")}}}</style>'
    cls = ' has-ch' if hc else ''
    if hero_bg(k): cls += ' hero-acv'
    return saida(head(title, desc, og, canonical, g['accent'], hero_preload(k), style + f'<script type="application/ld+json">{faq_ld}</script>',
                og_alt=f'Arte oficial do {n}' if k in ACJ else f'{n}: guia do jogo') + f'''
<body data-page="{k}" data-ga="{S.get('ga4', '')}">
{top(k, hub)}
<main>
<section class="hero{cls}" aria-label="{e(n)}">
<div class="veil l" aria-hidden="true"></div><div class="veil r" aria-hidden="true"></div>
<div class="hero-art">{hero_art(g)}</div>
<div class="fx fx-{g['effect']}" aria-hidden="true"></div>{hc}
<div class="hero-in">
<span class="kicker"><b></b>{e(g['kicker'])}</span>
{hero_title(g)}
<p class="headline focus">{words(g['headline'])}</p>
<p class="lede">{e(g['lede'])}</p>
<div class="ctas"><a class="btn btn-main" data-cta="hero_cadastro" href="{reg}">Criar conta e jogar {ARROW}</a><a class="btn btn-ghost" href="#recursos">Ver como funciona</a></div>
<div class="trust"><span>Pix na hora</span><span>Joga no navegador</span><span>Sem baixar app</span></div>
</div></section>

<section class="s" id="numeros"><div class="wrap">
<p class="eyebrow">Em números</p><h2>O que esperar do <span class="hl">{e(n)}</span></h2>
<p class="sub">Dados informados pelo provedor {e(g['provider'])}. Confira sempre a tela de regras dentro do jogo.</p>
<div class="metrics">{''.join(metric(m) for m in g['metrics'])}</div>
<p class="note">RTP é uma média teórica de longo prazo, não uma previsão para a sua sessão.</p>
</div></section>
{char_section(g, mode)}
<section class="s" id="recursos"><div class="wrap">
<p class="eyebrow">Recursos</p><h2>Como o jogo <span class="hl">paga</span></h2>
<div class="xcards">{feats}</div>
</div></section>

<section class="s"><div class="wrap reel">
<div class="phone">{media}<span class="tag">{e(g['provider'])}</span></div>
<div><p class="eyebrow">Vitrine</p><h2>Feito para a <span class="hl">tela do celular</span></h2>
<p class="sub">Abre direto no navegador, em pé, com toques grandes e carregamento leve no 4G.</p>{promo}
<div class="ctas"><a class="btn btn-main" data-cta="vitrine_jogar" href="{play}">{PLAY} Jogar {e(n)}</a></div></div>
</div></section>

<section class="s"><div class="wrap">
<p class="eyebrow">Cadastro em poucos minutos</p><h2>Do cadastro ao <span class="hl">primeiro giro</span></h2>
<div class="steps"><svg viewBox="0 0 12 100" preserveAspectRatio="none" aria-hidden="true"><path d="M6 0V100"/><path class="draw" d="M6 0V100"/></svg>
<div class="step"><span class="dot">1</span><h3>Crie sua conta</h3><p>Nome, CPF, e-mail e confirmação de identidade.</p></div>
<div class="step"><span class="dot">2</span><h3>Deposite via Pix</h3><p>Escolha o valor, pague no app do banco e o saldo cai em segundos.</p></div>
<div class="step"><span class="dot">3</span><h3>Abra o {e(n)}</h3><p>Busque pelo nome ou use o botão desta página. Defina seu limite e jogue.</p></div>
</div></div></section>

<section class="s"><div class="wrap">
<p class="eyebrow">Mais jogos</p><h2>Outros <span class="hl">favoritos</span></h2>
<div class="rail">{others}</div>
</div></section>

<section class="s"><div class="wrap">
<p class="eyebrow">Dúvidas</p><h2>Perguntas <span class="hl">frequentes</span></h2>
<div class="faq">{faqs}</div>
</div></section>

<section class="final"><p class="eyebrow">Pronto para jogar</p><h2>{e(n)} está a um toque</h2>
<p class="sub" style="margin:0 auto">Crie a conta, faça o Pix e abra o jogo direto no celular.</p>
<div class="ctas"><a class="btn btn-main" data-cta="final_cadastro" href="{utm(S['register'], k, 'final')}">Criar conta grátis {ARROW}</a><a class="btn btn-ghost" data-cta="final_entrar" href="{utm('/login', k, 'final')}">Já tenho conta</a></div>
</section>
</main>
{footer(k, hub)}
<div class="sticky"><span class="sn">{e(g['provider'])}<b>{e(n)}</b></span><a class="btn btn-main" data-cta="sticky_cadastro" href="{utm(S['register'], k, 'final')}">Jogar agora {ARROW}</a></div>
<script>{JS}</script>
</body></html>''')

LZ = 'loading="lazy"'
# parágrafo abaixo de "Escolha o seu jogo" (80 a 120 palavras; o build confere)
HUB_INTRO = ('Cada guia reúne o que vale saber antes de abrir o jogo. Você encontra o RTP teórico informado pelo provedor, o ganho máximo '
             'em vezes a aposta e a volatilidade, que indica se os prêmios tendem a ser mais frequentes e menores ou mais raros e maiores. '
             'Também explicamos como o jogo paga: grade, linhas ou pagamento em qualquer posição, curingas, multiplicadores e giros grátis. '
             'No fim de cada página há um passo a passo do cadastro ao primeiro giro e respostas para dúvidas comuns, como aposta mínima, '
             'saque via Pix e uso no celular.')
assert 80 <= len(HUB_INTRO.split()) <= 120, len(HUB_INTRO.split())

def hub():
    col = ''.join(f'<img src="{thumb(g["key"])}" width="{webp_size(thumb(g["key"]))[0]}" height="{webp_size(thumb(g["key"]))[1]}" alt="" aria-hidden="true" {LZ if i >= 6 else str()} decoding="async">'
                  for i, g in enumerate(G + G[:4]))
    grid = ''.join(card(g, game_href(g['key'], 'pages'), g['kicker'].split('·')[-1].strip(), com_rtp=True) for g in G)
    title = f'Os jogos mais jogados: guias, RTP e recursos | {S["brand"]}'
    desc = 'Fortune Tiger, Gates of Olympus, Sweet Bonanza, Mines e mais: como cada jogo funciona, RTP e recursos, para jogar no celular.'
    lista = json.dumps({"@context": "https://schema.org", "@type": "ItemList", "name": "Os jogos de cassino mais jogados", "numberOfItems": len(G),
                        "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": g['name'], "url": game_url(g['key'])} for i, g in enumerate(G)]},
                       ensure_ascii=False)
    return saida(head(title, desc, f'{PAGES}/assets/img/fortune-tiger-og.jpg', f'{PAGES}/', '#F5B942',
                extra=f'<script type="application/ld+json">{lista}</script>') + f'''
<body data-page="hub" data-ga="{S.get('ga4', '')}">
{top('hub')}
<main>
<section class="hero" aria-label="Jogos">
<div class="veil l" aria-hidden="true"></div><div class="veil r" aria-hidden="true"></div>
<div class="cbox" aria-hidden="true"><div class="collage">{col}</div></div>
<div class="fx fx-coins" aria-hidden="true"></div>
<div class="hero-in"><span class="kicker"><b></b>Guia dos jogos</span>
<h1 class="h1-hub"><span class="h1-l">Os jogos de cassino</span> mais <em>jogados:</em> <span class="h1-l">guias e RTP</span></h1>
<p class="headline focus">{words('Escolha o seu e entenda o jogo antes do primeiro giro')}</p>
<p class="lede">RTP, recursos e como jogar no celular, jogo por jogo. Tudo no navegador, com depósito via Pix.</p>
<div class="ctas"><a class="btn btn-main" data-cta="hub_cadastro" href="{utm(S['register'], 'hub', 'hero')}">Criar conta {ARROW}</a><a class="btn btn-ghost" href="#jogos">Ver os jogos</a></div>
</div></section>
<section class="s" id="jogos"><div class="wrap"><p class="eyebrow">{len(G)} guias</p><h2>Escolha o <span class="hl">seu jogo</span></h2>
<p class="sub">{e(HUB_INTRO)}</p>
<div class="grid">{grid}</div><p class="note more"><a href="personagens.html">Personagens dos jogos</a></p></div></section>
<section class="final"><h2>Cadastro em poucos minutos</h2><p class="sub" style="margin:0 auto">Cadastro rápido, Pix na hora e centenas de jogos.</p>
<div class="ctas"><a class="btn btn-main" data-cta="hub_final" href="{utm(S['register'], 'hub', 'final')}">Criar conta grátis {ARROW}</a></div></section>
</main>
{footer('hub')}
<div class="sticky"><a class="btn btn-main" data-cta="sticky_cadastro" href="{utm(S['register'], 'hub', 'final')}">Jogar agora {ARROW}</a></div>
<script>{JS}</script></body></html>''')

GRUPOS = {'01-proprias': 'Próprias', '02-latam': 'LATAM', '03-zeroum': 'Zeroum', '04-oficiais-provedores': 'Oficiais dos provedores'}

def personagens():
    """Banco de personagens: grade com todas as miniaturas do catálogo, filtros, busca e visualização grande."""
    items = []; marcas = {}
    for n, i in enumerate(CAT):
        w, h = webp_size(i['thumb']); nome = os.path.splitext(i['drive_nome'])[0]
        q = ' '.join([i['grupo'], i['marca_ou_tema'], i['subpasta'], i['drive_nome']]).lower()
        marcas.setdefault((i['grupo'], i['marca_ou_tema']), 0); marcas[(i['grupo'], i['marca_ou_tema'])] += 1
        items.append(f'<li data-g="{e(i["grupo"])}" data-m="{e(i["marca_ou_tema"])}" data-q="{e(q)}"><button type="button" data-i="{n}">'
                     f'<img src="{i["thumb"]}" width="{w}" height="{h}" loading="lazy" decoding="async" alt="{e(nome)}"></button></li>')
    data = [[i['web'], *webp_size(i['web']), i['drive_link'], i['drive_nome'], i['grupo'], i['marca_ou_tema'], i['subpasta'], i['transparente']] for i in CAT]
    gopts = ''.join(f'<option value="{g}">{e(GRUPOS.get(g, g))}</option>' for g in sorted({i['grupo'] for i in CAT}))
    mopts = ''.join(f'<option value="{e(m)}" data-g="{e(g)}">{e(m)} ({c})</option>' for (g, m), c in sorted(marcas.items()))
    style = ('<style>.bank{padding:96px 0 64px}.bt{font-size:clamp(28px,7.4vw,48px);text-transform:none;letter-spacing:-.01em;margin:8px 0 14px}.bt .hl{color:var(--acc)}.bank .sub a{color:var(--acc)}.bf{display:grid;gap:10px;margin:22px 0 8px}'
             '.bf select,.bf input{font:inherit;font-size:16px;color:var(--cream);background:var(--bg2);border:1px solid rgba(255,255,255,.18);border-radius:12px;min-height:48px;padding:0 14px;width:100%}'
             '.bc{font-size:13px;color:var(--muted)}.bg{list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(104px,1fr));gap:8px;margin-top:14px}'
             '.bg button{display:block;width:100%;aspect-ratio:1;padding:4px;border:1px solid rgba(255,255,255,.08);border-radius:12px;cursor:pointer;'
             'background:repeating-conic-gradient(#1B2D5C 0 25%,#13224A 0 50%) 0 0/16px 16px}'
             '.bg img{width:100%;height:100%;object-fit:contain}.bg button:focus-visible{outline:2px solid var(--acc)}'
             'dialog{margin:auto;max-width:min(94vw,900px);max-height:94vh;padding:16px;border:1px solid rgba(255,255,255,.18);border-radius:var(--r);background:var(--bg2);color:var(--cream)}'
             'dialog::backdrop{background:rgba(7,13,34,.86)}dialog img{max-height:70vh;width:auto;height:auto;margin:0 auto;border-radius:12px;'
             'background:repeating-conic-gradient(#1B2D5C 0 25%,#13224A 0 50%) 0 0/20px 20px}'
             'dialog p{font-size:13px;color:var(--muted);margin-top:10px;word-break:break-all}.dl{display:flex;flex-wrap:wrap;gap:10px;margin-top:12px}'
             '.dl a,.dl button{font:inherit;font-weight:800;font-size:14px;min-height:44px;padding:0 16px;border-radius:12px;display:inline-flex;align-items:center;text-decoration:none;cursor:pointer}'
             '.dl a{background:var(--cta);color:#fff}.dl button{background:none;border:1.5px solid var(--cream);color:var(--cream)}'
             '@media (min-width:720px){.bf{grid-template-columns:1fr 1fr 1.4fr}.bg{grid-template-columns:repeat(auto-fill,minmax(132px,1fr))}}</style>')
    pdata = json.dumps(data, ensure_ascii=False).replace('</', '<\\/')
    title = f'Personagens dos jogos | {S["brand"]}'
    return saida(head(title, 'Biblioteca interna de artes de personagens de cassino.', f'{PAGES}/assets/img/fortune-tiger-og.jpg',
                f'{PAGES}/personagens.html', '#F5B942', extra=style, noindex=True) + f'''
<body data-page="personagens">
{top('hub')}
<main class="bank"><div class="wrap">
<p class="eyebrow">Uso interno</p><h1 class="bt">Personagens <span class="hl">dos jogos</span></h1>
<p class="sub">{len(CAT)} artes de personagens do catálogo. Toque numa miniatura para ver a versão grande e o link do arquivo original no Drive.</p>
<form class="bf" role="search" onsubmit="return false">
<label class="sr" for="fg">Grupo</label><select id="fg"><option value="">Todos os grupos</option>{gopts}</select>
<label class="sr" for="fm">Marca ou tema</label><select id="fm"><option value="">Todas as marcas e temas</option>{mopts}</select>
<label class="sr" for="fq">Buscar</label><input id="fq" type="search" placeholder="Buscar por nome, marca ou pasta" autocomplete="off">
</form>
<p class="bc" id="bc" aria-live="polite">{len(CAT)} artes</p>
<ul class="bg" id="bg">{''.join(items)}</ul>
</div></main>
<dialog id="dlg" aria-label="Arte do personagem"><img id="di" src="{GIF}" width="1" height="1" alt=""><p id="dt"></p>
<div class="dl"><a id="dd" href="#" target="_blank" rel="noopener">Abrir original no Drive</a><a id="dw" href="#" target="_blank" rel="noopener">Abrir versão web</a><button type="button" id="dx">Fechar</button></div></dialog>
<script id="pdata" type="application/json">{pdata}</script>
<script>{PJS}</script>
</body></html>''')

def domain_404(k):
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Página não encontrada | {e(S["brand"])}</title><meta name="robots" content="noindex,nofollow"><meta http-equiv="refresh" content="3;url=/">
<style>body{{margin:0;min-height:100vh;display:grid;place-items:center;text-align:center;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Arial,sans-serif;background:#0B1430;color:#F4EEE6;padding:24px}}a{{color:#F5B942;font-weight:800}}</style></head>
<body><main><h1>Página não encontrada</h1><p>Você vai voltar para o guia do {e(next(g["name"] for g in G if g["key"] == k))} em instantes.</p><p><a href="/">Ir para a página inicial</a></p></main></body></html>'''

ASSET_RE = re.compile(r'assets/[A-Za-z0-9_./-]+?\.(?:webp|jpe?g|png|mp4|woff2|svg|gif)')

def refs(t):
    """Todos os assets citados no HTML: src, srcset, href, poster, data-src, url() do CSS e o JSON do banco de personagens."""
    return set(ASSET_RE.findall(t))

IMG_TAG = re.compile(r'<img\b[^>]*>')

def visivel(t):
    """Texto visível aproximado: sem <script>, <style> e tags."""
    return re.sub(r'<[^>]+>', ' ', re.sub(r'<(script|style)\b.*?</\1>', ' ', t, flags=re.S))

def check(base, label):
    """Verificador: todo asset citado existe; nenhum travessão; toda <img> com alt; um h1 por página;
    nenhum "teste" em texto visível; nenhuma capa com loading="lazy" no carrossel "Outros favoritos"."""
    for f in sorted(os.listdir(base)):
        if f.endswith('.html'):
            t = open(os.path.join(base, f), encoding='utf-8').read()
            for ref in refs(t):
                assert os.path.exists(os.path.join(base, ref)), (label, f, ref)
            assert '—' not in t, f'travessao em {label}/{f}'
            sem_alt = [i for i in IMG_TAG.findall(t) if not re.search(r'\balt="', i)]
            assert not sem_alt, (label, f, 'img sem alt', sem_alt[:2])
            assert len(re.findall(r'<h1\b', t)) == 1, (label, f, 'deve ter um h1')
            assert not re.search(r'\bteste\b', visivel(t), re.I), (label, f, '"teste" em texto visível')
            rail = re.search(r'<div class="rail">(.*?)</div>', t, re.S)
            assert not rail or 'loading="lazy"' not in rail.group(1), (label, f, 'lazy no carrossel')
            print(f'{label}/{f}', len(t) // 1024, 'KB')

def robots(sitemap=None):
    return 'User-agent: *\n' + ('Allow: /\n' if S.get('indexar') else 'Disallow: /\n') + (f'Sitemap: {sitemap}\n' if sitemap and S.get('indexar') else '')

def sitemap():
    """sitemap.xml do docs/: a index e as landings dos jogos (o banco de personagens é noindex e fica de fora)."""
    urls = [f'{PAGES}/'] + [f'{PAGES}/{g["key"]}.html' for g in G]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')

if __name__ == '__main__':
    for g in G: og_image(g)  # antes da cópia de assets/ (as OG ficam em assets/og/)
    # limpa docs/ menos as pastas de outras demandas publicadas pelo mesmo Pages (ex.: docs/previa-r4/)
    MANTER = {'previa-r4'}
    if os.path.exists(OUT):
        for f in os.listdir(OUT):
            if f in MANTER: continue
            p = os.path.join(OUT, f)
            shutil.rmtree(p) if os.path.isdir(p) and not os.path.islink(p) else os.remove(p)
    # assets/personagens, assets/acervo e assets/sites não entram inteiros: só os arquivos que as páginas referenciam (copiados abaixo),
    # como o banco de personagens, as artes do acervo no hero e os cards de assets/sites/cards.
    # catalogo e catalogo-web são dos sites .win (build_sites.py) e não entram no docs/.
    FORA = ['personagens', 'acervo', 'catalogo', 'catalogo-web', 'sites']
    PARCIAIS = tuple(f'assets/{d}/' for d in ('personagens', 'acervo', 'sites'))
    shutil.copytree(os.path.join(R, 'assets'), os.path.join(OUT, 'assets'),
                    ignore=lambda d, names: FORA if os.path.abspath(d) == os.path.join(R, 'assets') else [])
    pages = {g['key'] + '.html': game_page(g) for g in G}
    pages['index.html'] = hub()
    pages['personagens.html'] = personagens()
    for f, t in pages.items():
        open(os.path.join(OUT, f), 'w', encoding='utf-8').write(t)
    for ref in sorted(set().union(*(refs(t) for t in pages.values()))):
        if ref.startswith(PARCIAIS):
            os.makedirs(os.path.dirname(os.path.join(OUT, ref)), exist_ok=True)
            shutil.copy2(os.path.join(R, ref), os.path.join(OUT, ref))
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')
    open(os.path.join(OUT, 'robots.txt'), 'w').write(robots(f'{PAGES}/sitemap.xml'))
    open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(sitemap())
    check(OUT, 'docs')
    # um site por jogo, para o domínio próprio (dist-dominios/<dominio>/)
    if os.path.exists(DIST): shutil.rmtree(DIST)
    for g in G:
        k = g['key']
        if k not in DOM: continue
        dst = os.path.join(DIST, DOM[k]); os.makedirs(dst)
        t = game_page(g, 'domain')
        open(os.path.join(dst, 'index.html'), 'w', encoding='utf-8').write(t)
        for ref in sorted(refs(t) | {og_image(g)}):
            src = os.path.join(R, ref)
            if not os.path.exists(src): continue  # o verificador abaixo acusa o que faltar
            os.makedirs(os.path.dirname(os.path.join(dst, ref)), exist_ok=True)
            shutil.copy2(src, os.path.join(dst, ref))
        open(os.path.join(dst, 'CNAME'), 'w').write(DOM[k] + '\n')
        open(os.path.join(dst, '.nojekyll'), 'w').write('')
        open(os.path.join(dst, 'robots.txt'), 'w').write(robots())
        open(os.path.join(dst, '404.html'), 'w', encoding='utf-8').write(domain_404(k))
        check(dst, 'dist-dominios/' + DOM[k])
