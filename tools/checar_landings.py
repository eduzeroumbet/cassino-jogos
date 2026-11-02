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
    for x in erros: print(' -', x)
    sys.exit(1 if erros else 0)
