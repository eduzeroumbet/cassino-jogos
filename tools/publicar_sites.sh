#!/usr/bin/env bash
# Publica cada site de dist-sites/<dominio>/ num repositório próprio do GitHub,
# eduzeroumbet/site-<chave> (branch main, raiz), para servir pelo GitHub Pages no domínio .win.
#
# Antes de rodar (uma vez por site):
#   1. Aponte o DNS do domínio (Cloudflare) para o GitHub Pages
#      (registros A 185.199.108.153, .109.153, .110.153, .111.153 e CNAME www -> eduzeroumbet.github.io).
#      Na Cloudflare, deixe esses registros como "DNS only" até o Pages emitir o certificado.
#   2. Crie o repositório vazio:  gh repo create eduzeroumbet/site-<chave> --public
#   3. Depois do primeiro envio, ative o Pages na branch main, pasta raiz:
#        gh api -X POST repos/eduzeroumbet/site-<chave>/pages -f 'source[branch]=main' -f 'source[path]=/'
#      O arquivo CNAME gerado pelo build já informa o domínio ao Pages.
#
# Uso:
#   tools/publicar_sites.sh                 publica todos os sites de data/sites.json
#   tools/publicar_sites.sh guiaslots       publica só os sites informados (pela chave)
#   DRY_RUN=1 tools/publicar_sites.sh       mostra o que seria feito, sem enviar nada
#
# O script não cria repositórios e não mexe em dist-sites/: copia cada pasta para um clone
# temporário, faz commit e push. Sites sem repositório remoto são pulados com aviso.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist-sites"
OWNER="${OWNER:-eduzeroumbet}"
BRANCH="main"
DRY_RUN="${DRY_RUN:-0}"

[ -d "$DIST" ] || { echo "dist-sites/ não existe. Rode: python3 build_sites.py" >&2; exit 1; }

# chave<TAB>dominio, lido de data/sites.json
MAPA="$(python3 -c '
import json, sys
for s in json.load(open(sys.argv[1], encoding="utf-8"))["sites"]: print(s["chave"] + "\t" + s["dominio"])
' "$ROOT/data/sites.json")"

FILTRO=" $* "
REV="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo local)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

while IFS=$'\t' read -r CHAVE DOMINIO; do
  [ -n "$CHAVE" ] || continue
  if [ $# -gt 0 ] && [[ "$FILTRO" != *" $CHAVE "* ]]; then continue; fi
  SRC="$DIST/$DOMINIO"
  REPO="$OWNER/site-$CHAVE"
  URL="https://github.com/$REPO.git"
  if [ ! -f "$SRC/index.html" ]; then echo "[$CHAVE] sem $SRC/index.html, pulando"; continue; fi
  echo "[$CHAVE] $DOMINIO -> $REPO ($BRANCH)"
  if [ "$DRY_RUN" = "1" ]; then continue; fi

  WORK="$TMP/$CHAVE"
  if git ls-remote "$URL" >/dev/null 2>&1; then  # sucesso também para repositório recém-criado e vazio
    git clone --quiet "$URL" "$WORK" 2>/dev/null
    git -C "$WORK" checkout --quiet -B "$BRANCH"
  else
    echo "[$CHAVE] repositório $REPO não encontrado ou sem acesso. Crie com: gh repo create $REPO --public" >&2
    continue
  fi

  # espelha a pasta do build na raiz do repositório (preserva só o .git do clone temporário)
  find "$WORK" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  cp -R "$SRC"/. "$WORK"/

  git -C "$WORK" add -A
  if git -C "$WORK" diff --cached --quiet; then
    echo "[$CHAVE] sem mudanças"
    continue
  fi
  git -C "$WORK" commit --quiet -m "Site $DOMINIO (cassino-jogos $REV)"
  git -C "$WORK" push --quiet origin "$BRANCH"
  echo "[$CHAVE] publicado"
done <<< "$MAPA"
