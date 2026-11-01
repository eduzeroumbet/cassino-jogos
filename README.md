# cassino-jogos

Landing pages estáticas dos principais jogos de cassino.b7bet7.bet, mobile first, com componentes Scrolltide
(Intro Loader, Focus Reveal, Lime Metrics, Expanded Cards, Reel, Step Path).

- Conteúdo: `data/games.json` (um bloco por jogo: textos, métricas, recursos, FAQ, cores, efeito do hero).
- Estilo e comportamento: `src/lp.css`, `src/lp.js` (CSS e JS entram inline no HTML: 1 requisição a menos).
- Gerar: `python3 build.py` grava em `docs/` (publicado pelo GitHub Pages).
- Imagens: `tools_imgs.py` gera hero WebP 600/896, miniatura e OG 1200x630.
- Indexação: `site.indexar=false` coloca noindex e robots Disallow (páginas de teste). Troque para true quando houver domínio próprio e operação licenciada.
- Todos os links para a plataforma levam UTM: utm_source=lp, utm_medium=landing, utm_campaign=<jogo>, utm_content=<posição do botão>.
