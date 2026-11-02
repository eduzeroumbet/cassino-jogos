#!/usr/bin/env python3
"""Confere as landings dos jogos geradas em docs/ e dist-dominios/ (rodar depois de python3 build.py).

Para cada docs/*.html e dist-dominios/<dominio>/*.html:
  - todo src, href, srcset, poster, data-src e url() local aponta para um arquivo que existe dentro da própria pasta publicada
  - toda <img> tem alt, width e height; nas landings, as imagens com arte (logo, personagem, cards) têm alt preenchido
    (alt vazio só nas decorativas, com aria-hidden="true", como o fundo do hero)
  - só a arte do topo e o logo/personagem do hero ficam sem loading="lazy"; nenhum <img> depende de JS para aparecer (data-src)
  - nas landings e na index, nenhum texto visível nem alt/aria-label/title/meta contém os diminutivos
    (Tigrinho, Tourinho, Coelhinho, Dragãozinho, Ratinho); nomes de arquivo e de domínio não contam
  - as landings têm og:image (arquivo 1200x630 existente na pasta), twitter:card e robots igual ao de site.indexar,
    aviso 18+ e UTMs em todos os links para a plataforma
  - em src/lp.css, o texto auxiliar cinza (--muted e hex cinza em color:) tem contraste >= 4,5 sobre os fundos escuros
Sai com código 1 e lista os problemas se algo falhar.
Uso (da raiz do repositório): python3 tools/checar_landings.py
"""
import glob, json, os, re, sys
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from checar_sites import local, texto, ATTR_RE, SRCSET_RE, URL_RE, IMG_RE

D = json.load(open(os.path.join(ROOT, 'data/games.json'), encoding='utf-8'))
S = D['site']; KEYS = {g['key'] for g in D['games']}
BASE = S['base'].rstrip('/'); PAGES = S['pages_url'].rstrip('/')
PROIBIDOS = ('tigrinho', 'tourinho', 'coelhinho', 'dragãozinho', 'ratinho')
EXTRA_RE = re.compile(r'\b(?:poster|data-src)="([^"]*)"')
ROTULO_RE = re.compile(r'\b(?:alt|aria-label|title|content)="([^"]*)"')
PLAT_RE = re.compile(re.escape(BASE) + r'[^"\'\s<>)]*')
OG_RE = re.compile(r'<meta property="og:image" content="([^"]+)"')

def og_local(url, pasta):
    """Arquivo local da og:image (URL absoluta do Pages ou do domínio do jogo)."""
    p = urlparse(url).path
    if url.startswith(PAGES): p = url[len(PAGES):]
    return os.path.join(pasta, unquote(p).lstrip('/'))

def checar_arquivo(f, pasta, rel, landing):
    erros = []
    t = open(f, encoding='utf-8').read()
    refs = ATTR_RE.findall(t) + URL_RE.findall(t) + EXTRA_RE.findall(t)
    for ss in SRCSET_RE.findall(t) + re.findall(r'\bimagesrcset="([^"]*)"', t):
        refs += [x.strip().split(' ')[0] for x in ss.split(',')]
    for r in refs:
        p = local(r)
        if p and (p.endswith('/') or os.path.isdir(os.path.join(pasta, p))): p = os.path.join(p, 'index.html')  # "./" = a index
        if p and not os.path.isfile(os.path.join(pasta, p)):
            erros.append(f'{rel}: arquivo local inexistente: {r}')
    for tag in IMG_RE.findall(t):
        if not re.search(r'\balt="', tag): erros.append(f'{rel}: <img> sem alt: {tag[:100]}')
        if not (re.search(r'\bwidth="\d+"', tag) and re.search(r'\bheight="\d+"', tag)):
            erros.append(f'{rel}: <img> sem width/height: {tag[:100]}')
        if 'data-src=' in tag: erros.append(f'{rel}: <img> que depende de JS para carregar: {tag[:100]}')
        if landing and ('assets/acervo/' in tag or 'assets/sites/cards/' in tag) and re.search(r'\balt=""', tag) and 'aria-hidden="true"' not in tag:
            erros.append(f'{rel}: arte sem alt descritivo: {tag[:100]}')
        if landing and 'fetchpriority="high"' in tag and 'loading="lazy"' in tag:
            erros.append(f'{rel}: arte do topo com loading="lazy": {tag[:100]}')
    if landing or rel.endswith('/index.html'):  # o banco de personagens (uso interno) mostra os nomes dos arquivos originais
        visivel = (texto(t) + ' ' + ' '.join(ROTULO_RE.findall(t))).lower()
        for w in PROIBIDOS:
            if w in visivel: erros.append(f'{rel}: texto visível com "{w}"')
    if landing:
        hero = t.split('<div class="hero-in">', 1)[0]
        for tag in IMG_RE.findall(hero):
            if 'loading="lazy"' in tag: erros.append(f'{rel}: imagem do hero com loading="lazy": {tag[:100]}')
        robots = 'index,follow' if S.get('indexar') else 'noindex,nofollow'
        for need in (f'name="robots" content="{robots}"', 'name="twitter:card" content="summary_large_image"', 'class="age">18+<'):
            if need not in t: erros.append(f'{rel}: falta {need}')
        m = OG_RE.search(t)
        if not m:
            erros.append(f'{rel}: falta og:image')
        else:
            og = og_local(m.group(1), pasta)
            if not os.path.isfile(og):
                erros.append(f'{rel}: og:image inexistente: {m.group(1)}')
            else:
                try:
                    from PIL import Image
                    if Image.open(og).size != (1200, 630): erros.append(f'{rel}: og:image não é 1200x630')
                except ImportError:
                    pass
        for u in PLAT_RE.findall(t):
            if u.rstrip('/') != BASE and 'utm_campaign=' not in u: erros.append(f'{rel}: link da plataforma sem UTM: {u}')
    return erros

HEX_RE = re.compile(r'#[0-9A-Fa-f]{6}\b')

def lum(h):
    """Luminância relativa (WCAG) de uma cor #RRGGBB."""
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in c]
    return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]

def razao(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + .05) / (lb + .05)

def mistura(a, b, p):
    """color-mix(in srgb, a p, b)."""
    return '#' + ''.join(f'{round(int(a[i:i + 2], 16) * p + int(b[i:i + 2], 16) * (1 - p)):02X}' for i in (1, 3, 5))

def checar_contraste():
    """Texto auxiliar cinza de src/lp.css (--muted e os hex cinza usados em color:) sobre os fundos escuros
    (--bg, --bg2, --bg3 e o cartão de promoção da index, com 22% de roxo): razão mínima de 4,5 (WCAG AA)."""
    css = open(os.path.join(ROOT, 'src/lp.css'), encoding='utf-8').read()
    var = dict(re.findall(r'--([\w-]+):(#[0-9A-Fa-f]{6})\b', re.search(r':root\{[^}]*\}', css).group(0)))
    roxo = re.search(r'\.promos-hub\{[^}]*--acc2:(#[0-9A-Fa-f]{6})', css)
    fundos = {f'--{k}': var[k] for k in ('bg', 'bg2', 'bg3')}
    if roxo: fundos['cartão de promoção da index'] = mistura(roxo.group(1), var['bg3'], .22)
    cinzas = {'--muted': var['muted']}
    for h in set(HEX_RE.findall(' '.join(re.findall(r'(?<![\w-])color:([^;}]*)', css)))):
        c = [int(h[i:i + 2], 16) for i in (1, 3, 5)]
        if max(c) - min(c) <= 40 and h.upper() != '#FFFFFF': cinzas[h] = h  # cinza: pouca saturação
    erros = []
    for nc, c in sorted(cinzas.items()):
        for nf, f in fundos.items():
            r = razao(c, f)
            if r < 4.5: erros.append(f'src/lp.css: contraste {r:.2f} de {nc} ({c}) sobre {nf} ({f}), mínimo 4,5')
    return erros

def checar(pasta, nome, landings):
    erros = []
    for f in sorted(glob.glob(os.path.join(pasta, '*.html'))):
        b = os.path.basename(f)
        erros += checar_arquivo(f, pasta, f'{nome}/{b}', b in landings)
    rb = os.path.join(pasta, 'robots.txt')
    esperado = 'Allow: /' if S.get('indexar') else 'Disallow: /'
    if not os.path.isfile(rb) or esperado not in open(rb).read().split('\n'):
        erros.append(f'{nome}: robots.txt sem "{esperado}"')
    return erros

if __name__ == '__main__':
    alvos = [(os.path.join(ROOT, 'docs'), 'docs', {f'{k}.html' for k in KEYS})]
    alvos += [(d, 'dist-dominios/' + os.path.basename(d), {'index.html'})
              for d in sorted(glob.glob(os.path.join(ROOT, 'dist-dominios', '*'))) if os.path.isdir(d)]
    if not os.path.isdir(alvos[0][0]):
        sys.exit('docs/ não existe: rode python3 build.py antes')
    erros = []
    for pasta, nome, landings in alvos:
        e = checar(pasta, nome, landings); erros += e
        print(f'{nome}: {"ok" if not e else str(len(e)) + " problema(s)"}')
    e = checar_contraste(); erros += e
    print(f'contraste do texto auxiliar: {"ok" if not e else str(len(e)) + " problema(s)"}')
    for x in erros: print(' -', x)
    sys.exit(1 if erros else 0)
