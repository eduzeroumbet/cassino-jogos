#!/usr/bin/env python3
"""Confere os sites .win gerados em dist-sites/ (rodar depois de python3 build_sites.py).

Para cada dist-sites/<dominio>/*.html:
  - todo src, href, srcset e url() local aponta para um arquivo que existe dentro da pasta do próprio site
  - toda <img> tem alt preenchido, width e height
  - nenhum texto contém 'Tigrinho' nem 'ver no jogo'
  - index.html tem noindex, og:image e twitter:card, e og.jpg existe na raiz do site (1200x630)
E robots.txt bloqueia tudo.
Sai com código 1 e lista os problemas se algo falhar.
Uso (da raiz do repositório): python3 tools/checar_sites.py
"""
import glob, os, re, sys
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist-sites')
PROIBIDOS = ('tigrinho', 'ver no jogo')

ATTR_RE = re.compile(r'\b(?:src|href)="([^"]*)"')
SRCSET_RE = re.compile(r'\bsrcset="([^"]*)"')
URL_RE = re.compile(r'url\(\s*["\']?([^"\')]+)["\']?\s*\)')
IMG_RE = re.compile(r'<img\b[^>]*>')

def local(ref):
    """Caminho local de uma referência, ou None se for externa, âncora, data:, mailto:, tel: ou a raiz /."""
    ref = ref.strip()
    if not ref or ref.startswith(('#', 'data:', 'mailto:', 'tel:', 'javascript:', '//')): return None
    u = urlparse(ref)
    if u.scheme or u.netloc: return None
    p = unquote(u.path).lstrip('/')
    return p or None

def texto(t):
    t = re.sub(r'<(script|style)\b.*?</\1>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<[^>]+>', ' ', t)
    return re.sub(r'\s+', ' ', t)

def checar(site):
    erros = []
    nome = os.path.basename(site)
    for f in sorted(glob.glob(os.path.join(site, '*.html'))):
        rel = f'{nome}/{os.path.basename(f)}'
        t = open(f, encoding='utf-8').read()
        refs = ATTR_RE.findall(t) + URL_RE.findall(t)
        for ss in SRCSET_RE.findall(t):
            refs += [x.strip().split(' ')[0] for x in ss.split(',')]
        for r in refs:
            p = local(r)
            if p and not os.path.isfile(os.path.join(site, p)):
                erros.append(f'{rel}: arquivo local inexistente: {r}')
        for tag in IMG_RE.findall(t):
            if not re.search(r'\balt="[^"]+"', tag): erros.append(f'{rel}: <img> sem alt descritivo: {tag[:100]}')
            if not (re.search(r'\bwidth="\d+"', tag) and re.search(r'\bheight="\d+"', tag)):
                erros.append(f'{rel}: <img> sem width/height: {tag[:100]}')
        tx = texto(t).lower(); bruto = t.lower()
        for w in PROIBIDOS:
            if w in tx or w in bruto: erros.append(f'{rel}: contém "{w}"')
        if os.path.basename(f) == 'index.html':
            for need in ('name="robots" content="noindex', 'property="og:image"', 'name="twitter:card"'):
                if need not in t: erros.append(f'{rel}: falta {need}')
    og = os.path.join(site, 'og.jpg')
    if not os.path.isfile(og):
        erros.append(f'{nome}: falta og.jpg')
    else:
        try:
            from PIL import Image
            if Image.open(og).size != (1200, 630): erros.append(f'{nome}: og.jpg não é 1200x630')
        except ImportError:
            pass
    rb = os.path.join(site, 'robots.txt')
    if not os.path.isfile(rb) or 'Disallow: /' not in open(rb).read().split('\n'):
        erros.append(f'{nome}: robots.txt não bloqueia tudo')
    return erros

if __name__ == '__main__':
    sites = sorted(d for d in glob.glob(os.path.join(DIST, '*')) if os.path.isdir(d))
    if not sites:
        sys.exit('nenhum site em dist-sites/: rode python3 build_sites.py antes')
    erros = []
    for s in sites:
        e = checar(s); erros += e
        print(f'{os.path.basename(s)}: {"ok" if not e else str(len(e)) + " problema(s)"}')
    for x in erros: print(' -', x)
    sys.exit(1 if erros else 0)
