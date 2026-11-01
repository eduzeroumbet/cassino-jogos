#!/usr/bin/env python3
"""Gera as landing pages estáticas em dist/ a partir de data/games.json.
Uso: python3 build.py   (sem dependências externas)"""
import json, os, shutil, html, re
R = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(R, 'data/games.json'), encoding='utf-8'))
S = D['site']; G = D['games']
OUT = os.path.join(R, 'docs')
CSS = open(os.path.join(R, 'src/lp.css'), encoding='utf-8').read().replace('../assets/', 'assets/')
JS = open(os.path.join(R, 'src/lp.js'), encoding='utf-8').read()
CSS = re.sub(r'\s*\n\s*', '', CSS)
e = lambda s: html.escape(str(s), quote=True)
BASE = S['base'].rstrip('/')
PAGES = S['pages_url'].rstrip('/')

def utm(path, key, cta):
    sep = '&' if '?' in path else '?'
    return f"{BASE}{path}{sep}utm_source=lp&utm_medium=landing&utm_campaign={key}&utm_content={cta}"

def play_url(g):
    return f"/cassino/jogar/{g['provider_code']}/{g['slug']}"

ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12h14M13 6l6 6-6 6"/></svg>'
PLAY = '<svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M8 5.5v13a1 1 0 0 0 1.5.86l10.5-6.5a1 1 0 0 0 0-1.72L9.5 4.64A1 1 0 0 0 8 5.5z"/></svg>'

def head(title, desc, og, canonical, accent, preload=None, extra=''):
    robots = 'index,follow' if S.get('indexar') else 'noindex,nofollow'
    pl = ''
    if preload:
        pl = (f'<link rel="preload" as="image" href="{preload}-600.webp" imagesrcset="{preload}-600.webp 600w, {preload}-896.webp 896w" '
              f'imagesizes="(min-width:1024px) 58vw, 100vw" fetchpriority="high">')
    return f'''<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{e(title)}</title><meta name="description" content="{e(desc)}"><meta name="robots" content="{robots}">
<meta name="theme-color" content="#0B1430"><link rel="canonical" href="{canonical}">
<meta property="og:type" content="website"><meta property="og:locale" content="pt_BR"><meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}"><meta property="og:image" content="{og}"><meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preload" as="font" type="font/woff2" href="assets/fonts/montserrat-Black.woff2" crossorigin>
<link rel="preconnect" href="{BASE}">{pl}
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='9' fill='%23FF3D5A'/%3E%3C/svg%3E">
<style>{CSS}:root{{--acc:{accent}}}</style>{extra}</head>'''

def top():
    return (f'<header class="top"><a class="logo" href="./" aria-label="{e(S["brand"])}: todos os jogos"><i></i>{e(S["brand"])}</a>'
            f'<a class="btn-sm" data-cta="topo_entrar" href="{utm("/login", "topo", "entrar")}">Entrar</a></header>')

def footer(key):
    return f'''<footer><div class="wrap"><div class="rg"><span class="age">18+</span><p>Proibido para menores de 18 anos. Jogue com responsabilidade: defina um valor por sessão, faça pausas e não trate o jogo como fonte de renda. Os valores de RTP são teóricos, informados pelos provedores, e não garantem resultado.</p></div>
<nav><a href="./">Todos os jogos</a><a data-cta="rodape_cassino" href="{utm("/cassino", key, "rodape")}">Cassino</a><a data-cta="rodape_cadastro" href="{utm(S["register"], key, "rodape")}">Criar conta</a><a href="{utm("/usuario/carteira", key, "rodape")}">Depósito Pix</a></nav>
<nav class="docs" aria-label="Documentos da plataforma"><a href="{utm("/pagina/terms", key, "rodape")}">Termos e Condições</a><a href="{utm("/pagina/privacy", key, "rodape")}">Política de Privacidade</a><a href="{utm("/pagina/responsible-gaming", key, "rodape")}">Jogo Responsável</a><a href="{utm("/faq", key, "rodape")}">Central de Ajuda</a></nav>
<p>Página informativa de {e(S["brand"])}. Os jogos citados pertencem aos respectivos provedores.</p></div></footer>'''

def pic(k, alt, cls='', eager=False):
    pr = 'fetchpriority="high"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img class="{cls}" src="assets/img/{k}-hero-600.webp" srcset="assets/img/{k}-hero-600.webp 600w, assets/img/{k}-hero-896.webp 896w" '
            f'sizes="(min-width:1024px) 58vw, 100vw" width="896" height="1200" alt="{e(alt)}" {pr}>')

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

def card(g, href, sub):
    return (f'<a class="card" href="{href}" style="--ca:{g["accent"]}"><img src="assets/img/{g["key"]}-thumb.webp" width="300" height="350" loading="lazy" decoding="async" alt="{e(g["name"])}">'
            f'<span>{e(g["name"])}<small>{e(sub)}</small></span></a>')

def game_page(g):
    k = g['key']; n = g['name']
    reg = utm(S['register'], k, 'hero'); play = utm(play_url(g), k, 'vitrine')
    title = f'{n}: como jogar, RTP e recursos | {S["brand"]}'
    desc = f'{n} ({g["provider"]}): {g["lede"]}'[:158]
    canonical = f'{PAGES}/{k}.html'; og = f'{PAGES}/assets/img/{k}-og.jpg'
    faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": f['q'], "acceptedAnswer": {"@type": "Answer", "text": f['a']}} for f in g['faq']]}, ensure_ascii=False)
    if g.get('video'):
        media = (f'<video muted loop playsinline preload="none" poster="assets/img/{k}-thumb.webp" data-src="assets/video/{g["video"]}.mp4" '
                 f'width="300" height="375" aria-label="Prévia do {e(n)}"></video>')
    else:
        media = f'<img class="kb" src="assets/img/{k}-thumb.webp" width="300" height="350" loading="lazy" decoding="async" alt="Capa do {e(n)}">'
    promo = ''
    if g.get('promo'):
        note = f'<small>{e(g["promo"]["note"])}</small>' if g['promo'].get('note') else ''
        promo = f'<p class="promo">{e(g["promo"]["text"])} <a data-cta="promo" href="{utm(g["promo"]["url"], k, "promo")}">Ver campanha</a>{note}</p>'
    feats = ''.join(f'<button class="xcard" type="button" data-k="{e(f["title"])}" aria-expanded="{"true" if i == 0 else "false"}"><span class="n">0{i + 1}</span><h3>{e(f["title"])}</h3><p>{e(f["text"])}</p></button>'
                    for i, f in enumerate(g['features']))
    others = ''.join(card(o, f'{o["key"]}.html', o['provider']) for o in G if o['key'] != k)
    faqs = ''.join(f'<details><summary>{e(f["q"])}</summary><p>{e(f["a"])}</p></details>' for f in g['faq'])
    style = f'<style>:root{{--acc:{g["accent"]};--acc2:{g.get("accent2", "#FF3D5A")}}}</style>'
    return head(title, desc, og, canonical, g['accent'], f'assets/img/{k}-hero', style + f'<script type="application/ld+json">{faq_ld}</script>') + f'''
<body data-page="{k}" data-ga="{S.get('ga4', '')}">
{top()}
<main>
<section class="hero" aria-label="{e(n)}">
<div class="veil l" aria-hidden="true"></div><div class="veil r" aria-hidden="true"></div>
<div class="hero-art">{pic(k, "Arte do " + n, eager=True)}</div>
<div class="fx fx-{g['effect']}" aria-hidden="true"></div>
<div class="hero-in">
<span class="kicker"><b></b>{e(g['kicker'])}</span>
<h1>{h1name(n)}</h1>
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
<p class="eyebrow">Comece em 1 minuto</p><h2>Do cadastro ao <span class="hl">primeiro giro</span></h2>
<div class="steps"><svg viewBox="0 0 12 100" preserveAspectRatio="none" aria-hidden="true"><path d="M6 0V100"/><path class="draw" d="M6 0V100"/></svg>
<div class="step"><span class="dot">1</span><h3>Crie sua conta</h3><p>Nome, CPF e e-mail. Leva menos de um minuto.</p></div>
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
{footer(k)}
<div class="sticky"><span class="sn">{e(g['provider'])}<b>{e(n)}</b></span><a class="btn btn-main" data-cta="sticky_cadastro" href="{utm(S['register'], k, 'sticky')}">Jogar agora {ARROW}</a></div>
<script>{JS}</script>
</body></html>'''

LZ = 'loading="lazy"'

def hub():
    col = ''.join(f'<img src="assets/img/{g["key"]}-thumb.webp" width="300" height="350" alt="" {LZ if i >= 6 else str()} decoding="async">' for i, g in enumerate(G + G[:4]))
    grid = ''.join(card(g, f'{g["key"]}.html', g['kicker'].split('·')[-1].strip()) for g in G)
    title = f'Os jogos mais jogados: guias, RTP e recursos | {S["brand"]}'
    desc = 'Fortune Tiger, Gates of Olympus, Sweet Bonanza, Mines e mais: como cada jogo funciona, RTP e recursos, para jogar no celular.'
    return head(title, desc, f'{PAGES}/assets/img/fortune-tiger-og.jpg', f'{PAGES}/', '#F5B942') + f'''
<body data-page="hub" data-ga="{S.get('ga4', '')}">
{top()}
<main>
<section class="hero" aria-label="Jogos">
<div class="veil l" aria-hidden="true"></div><div class="veil r" aria-hidden="true"></div>
<div class="collage" aria-hidden="true">{col}</div>
<div class="fx fx-coins" aria-hidden="true"></div>
<div class="hero-in"><span class="kicker"><b></b>Guia dos jogos</span>
<h1>Os mais<em>jogados</em></h1>
<p class="headline focus">{words('Escolha o seu e entenda o jogo antes do primeiro giro')}</p>
<p class="lede">RTP, recursos e como jogar no celular, jogo por jogo. Tudo no navegador, com depósito via Pix.</p>
<div class="ctas"><a class="btn btn-main" data-cta="hub_cadastro" href="{utm(S['register'], 'hub', 'hero')}">Criar conta {ARROW}</a><a class="btn btn-ghost" href="#jogos">Ver os jogos</a></div>
</div></section>
<section class="s" id="jogos"><div class="wrap"><p class="eyebrow">{len(G)} guias</p><h2>Escolha o <span class="hl">seu jogo</span></h2>
<div class="grid">{grid}</div></div></section>
<section class="final"><h2>Tudo pronto em 1 minuto</h2><p class="sub" style="margin:0 auto">Cadastro rápido, Pix na hora e centenas de jogos.</p>
<div class="ctas"><a class="btn btn-main" data-cta="hub_final" href="{utm(S['register'], 'hub', 'final')}">Criar conta grátis {ARROW}</a></div></section>
</main>
{footer('hub')}
<div class="sticky"><a class="btn btn-main" data-cta="sticky_cadastro" href="{utm(S['register'], 'hub', 'sticky')}">Jogar agora {ARROW}</a></div>
<script>{JS}</script></body></html>'''

if __name__ == '__main__':
    if os.path.exists(OUT): shutil.rmtree(OUT)
    shutil.copytree(os.path.join(R, 'assets'), os.path.join(OUT, 'assets'))
    for g in G:
        open(os.path.join(OUT, g['key'] + '.html'), 'w', encoding='utf-8').write(game_page(g))
    open(os.path.join(OUT, 'index.html'), 'w', encoding='utf-8').write(hub())
    open(os.path.join(OUT, '.nojekyll'), 'w').write('')
    open(os.path.join(OUT, 'robots.txt'), 'w').write('User-agent: *\n' + ('Allow: /\n' if S.get('indexar') else 'Disallow: /\n'))
    # verificação mínima
    for f in os.listdir(OUT):
        if f.endswith('.html'):
            t = open(os.path.join(OUT, f), encoding='utf-8').read()
            for ref in re.findall(r'(?:src|href|data-src|poster)="(assets/[^"]+)"', t):
                assert os.path.exists(os.path.join(OUT, ref)), (f, ref)
            assert '—' not in t, f'travessao em {f}'
            print(f, len(t) // 1024, 'KB')
