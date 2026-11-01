#!/usr/bin/env bash
# Publica cada landing de dist-dominios/<dominio>/ num repositório próprio do GitHub,
# eduzeroumbet/lp-<jogo> (branch main, raiz), para servir pelo GitHub Pages no domínio do jogo.
#
# Antes de rodar (uma vez por jogo):
#   1. Compre o domínio e aponte o DNS para o GitHub Pages
#      (registros A 185.199.108.153, .109.153, .110.153, .111.153 e CNAME www -> eduzeroumbet.github.io).
#   2. Crie o repositório vazio:  gh repo create eduzeroumbet/lp-<jogo> --public
#   3. Depois do primeiro envio, ative o Pages na branch main, pasta raiz:
#        gh api -X POST repos/eduzeroumbet/lp-<jogo>/pages -f 'source[branch]=main' -f 'source[path]=/'
#      O arquivo CNAME gerado pelo build já informa o domínio ao Pages.
#   4. Quando os domínios estiverem no ar, troque site.domains_active para true em data/games.json
#      e rode python3 build.py de novo (canonical, og e links entre jogos passam a usar os domínios).
#
# Uso:
#   tools/publicar_dominios.sh                 publica todos os jogos de site.domains
#   tools/publicar_dominios.sh fortune-tiger   publica só os jogos informados
#   DRY_RUN=1 tools/publicar_dominios.sh       mostra o que seria feito, sem enviar nada
#
# O script não cria repositórios e não mexe em dist-dominios/: copia cada pasta para um clone
# temporário, faz commit e push. Pastas sem repositório remoto são puladas com aviso.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$ROOT/dist-dominios"
OWNER="${OWNER:-eduzeroumbet}"
BRANCH="main"
DRY_RUN="${DRY_RUN:-0}"

[ -d "$DIST" ] || { echo "dist-dominios/ não existe. Rode: python3 build.py" >&2; exit 1; }

# jogo<TAB>dominio, lido de site.domains em data/games.json
MAPA="$(python3 -c '
import json, sys
s = json.load(open(sys.argv[1], encoding="utf-8"))["site"]
for k, d in s.get("domains", {}).items(): print(k + "\t" + d)
' "$ROOT/data/games.json")"

FILTRO=" $* "
REV="$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo local)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

while IFS=$'\t' read -r JOGO DOMINIO; do
  [ -n "$JOGO" ] || continue
  if [ $# -gt 0 ] && [[ "$FILTRO" != *" $JOGO "* ]]; then continue; fi
  SRC="$DIST/$DOMINIO"
  REPO="$OWNER/lp-$JOGO"
  URL="https://github.com/$REPO.git"
  if [ ! -f "$SRC/index.html" ]; then echo "[$JOGO] sem $SRC/index.html, pulando"; continue; fi
  echo "[$JOGO] $DOMINIO -> $REPO ($BRANCH)"
  if [ "$DRY_RUN" = "1" ]; then continue; fi

  WORK="$TMP/$JOGO"
  if git ls-remote "$URL" >/dev/null 2>&1; then  # sucesso também para repositório recém-criado e vazio
    git clone --quiet "$URL" "$WORK" 2>/dev/null
    git -C "$WORK" checkout --quiet -B "$BRANCH"
  else
    echo "[$JOGO] repositório $REPO não encontrado ou sem acesso. Crie com: gh repo create $REPO --public" >&2
    continue
  fi

  # espelha a pasta do build na raiz do repositório (preserva só o .git do clone temporário)
  find "$WORK" -mindepth 1 -maxdepth 1 ! -name .git -exec rm -rf {} +
  cp -R "$SRC"/. "$WORK"/

  git -C "$WORK" add -A
  if git -C "$WORK" diff --cached --quiet; then
    echo "[$JOGO] sem mudanças"
    continue
  fi
  git -C "$WORK" commit --quiet -m "Landing $DOMINIO (cassino-jogos $REV)"
  git -C "$WORK" push --quiet origin "$BRANCH"
  echo "[$JOGO] publicado"
done <<< "$MAPA"
