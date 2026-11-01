# cassino-jogos

Landing pages estáticas dos principais jogos de cassino.b7bet7.bet, mobile first, com componentes Scrolltide
(Intro Loader, Focus Reveal, Lime Metrics, Expanded Cards, Reel, Step Path).

- Conteúdo: `data/games.json` (um bloco por jogo: textos, métricas, recursos, FAQ, cores, efeito do hero, personagem).
- Estilo e comportamento: `src/lp.css`, `src/lp.js` (CSS e JS entram inline no HTML: 1 requisição a menos). O banco de personagens usa também `src/personagens.js`.
- Gerar: `python3 build.py` grava em `docs/` (publicado pelo GitHub Pages) e em `dist-dominios/` (um site por jogo). No fim, o verificador confere que todo asset citado no HTML existe e que não há travessão em texto.
- Imagens: `tools_imgs.py` gera hero WebP 600/896, miniatura e OG 1200x630.
- Indexação: `site.indexar=false` coloca noindex e robots Disallow (páginas de teste). Troque para true quando houver domínio próprio e operação licenciada.
- Todos os links para a plataforma levam UTM: utm_source=lp, utm_medium=landing, utm_campaign=<jogo>, utm_content=<posição do botão>.

## Personagens

- Biblioteca: `assets/personagens/` (566 artes em WebP: `<nome>.webp` até 1000 px e `<nome>-thumb.webp` até 360 px) e o catálogo `data/personagens.json`
  (grupo, marca_ou_tema, subpasta, largura e altura do original, transparente, web, thumb, drive_nome, drive_link). Originais em alta ficam no Drive.
- Cada jogo tem em `games.json` o campo `character`:
  `{"main": caminho, "extras": [até 3 caminhos], "name": nome, "alt": texto alternativo, "bio": 2 frases, "crop": [x, y, w, h] opcional}`.
  `crop` (em px da versão web) mostra só um recorte da arte, em CSS; serve para os boards do elenco da casa, que trazem texto.
- Na landing: bloco "Conheça o personagem" logo depois das métricas (arte sem loading lazy, com fetchpriority baixo e width/height reais,
  lidos do cabeçalho do WebP; arte de fundo branco fica num cartão branco de cantos arredondados). Se a arte falhar (onerror), o cartão
  mostra a capa do jogo (`assets/img/<jogo>-thumb.webp`). As miniaturas (principal + extras, 76 px no celular, 96 px no desktop) são botões
  que trocam a arte grande; abaixo, link "Ver todos os personagens" (personagens.html; no domínio próprio, a do GitHub Pages).
  No desktop (>= 960 px), se a arte principal tiver fundo transparente, o personagem aparece sobreposto no hero com fetchpriority baixo;
  no celular a imagem nem é baixada (`<picture>` com `media`). Nesse caso o bloco abre com a primeira extra, para não repetir a arte do hero.
- Carrossel "Outros favoritos": os 3 primeiros cards sem lazy; os demais com `loading="lazy"` nativo (sem IntersectionObserver).
- Escolhas atuais: Tigrinho, Coelhinho, Tourinho, Dragãozinho e Zeus (artes dos jogos); Sweet Bonanza, Big Bass Splash e Mines não têm
  personagem adequado no catálogo, então usam o elenco da casa: Lu (arara), Capi (capivara) e Mr. Bit.
- `docs/personagens.html` (noindex): banco com todas as miniaturas, filtro por grupo e por marca/tema, busca por texto; o clique abre a versão
  grande e o link do original no Drive. Título "Personagens dos jogos"; link com esse nome no fim da grade da index.
- O build copia para `docs/` só as imagens de `assets/personagens/` que as páginas referenciam (hoje, todas, por causa do banco).

## Domínio próprio por jogo

- `site.domains` em `games.json` mapeia jogo para domínio (ex.: fortune-tiger = guiadotigrinho.win) e `site.domains_active` liga o uso.
- O build gera `dist-dominios/<dominio>/` para cada jogo: `index.html` (a landing), só os assets que ela usa, `CNAME`, `robots.txt`
  (Disallow enquanto `indexar=false`), `.nojekyll` e um `404.html` que volta para o início. A pasta é versionada.
- `domains_active=false` (hoje): canonical, og:url e og:image continuam no GitHub Pages (https://eduzeroumbet.github.io/cassino-jogos/),
  e os cards de outros jogos levam às páginas do Pages.
- `domains_active=true`: canonical, og:url e og:image passam a `https://<dominio>/`, e os cards de outros jogos (nas landings e na index)
  apontam para os domínios dos outros jogos. Links para a plataforma e UTMs não mudam.
- Publicação: `tools/publicar_dominios.sh` envia cada pasta para o repositório `eduzeroumbet/lp-<jogo>` (branch main, raiz).
  Os passos prévios (comprar domínio, DNS, criar o repositório, ativar o Pages) estão no cabeçalho do script. `DRY_RUN=1` só lista o que faria.

## Sites por domínio (.win)

Seis sites de uma página, um por domínio .win, cada um com layout, tipografia e paleta próprios (diferentes entre si e das landings):

| Domínio | Chave | Estilo | Conteúdo |
| --- | --- | --- | --- |
| guiadecassino.win | guiadecassino | Revista editorial: papel creme, títulos serifados, colunas de jornal | Capa com sumário, como começar, as 5 categorias (liga os outros guias), Pix, jogo responsável, os 8 mais jogados, FAQ. É o hub. |
| guiaslots.win | guiaslots | Dashboard grafite e verde-limão | KPIs, pódio animado, tabela ordenável com filtro por provedor (30 slots), cards com capa, glossário. |
| guiafortune.win | guiafortune | Festival oriental: vermelho laca, dourado, lanternas em CSS | Um capítulo por jogo da série Fortune com personagem, quiz de 3 perguntas, comparativo lado a lado, outros PG Soft. |
| guiapragmatic.win | guiapragmatic | Bento grid neo-brutalista: bordas pretas, sombras duras, roxo, amarelo e ciano | Bento de destaques (Zeus no Gates of Olympus), abas por mecânica, versões 1000 e Super Scatter, Pragmatic Live. |
| guiadecrash.win | guiadecrash | HUD/terminal: preto, verde e ciano neon, monoespaçada | Simulador educativo em canvas (sem dinheiro), multiplicador, saque automático, RTP, crash games e originais Galaxsys. |
| guiaaviator.win | guiaaviator | App de conversão: céu azul ao pôr do sol, avião em SVG, cartões arredondados | O que é o estilo Aviator (o Aviator da Spribe não está na plataforma), 3 passos, jogos de voo disponíveis, FAQ, CTA fixo no celular. |

- Conteúdo: `data/sites.json`. `comum` (caminhos da plataforma, textos do rodapé, nomes de provedores e correções de nomes do catálogo),
  `fichas` (RTP teórico, volatilidade, ganho máximo e grade por slug; só dados oficiais conhecidos, o resto aparece como "ver no jogo")
  e `sites` (domínio, chave, estilo, título, descrição, cores, imagem do hero, OG, listas de jogos por slug e textos de cada seção).
  Os jogos vêm de `data/catalogo-plataforma.json` (url, nome, capa); itens com `disponivel=false` (Aviator da Spribe) fazem o build parar se forem usados.
- Gerar: `python3 build_sites.py` grava `dist-sites/<dominio>/` com `index.html` (CSS e JS inline), `404.html` que volta para `/`, `CNAME`,
  `robots.txt` (Disallow), `.nojekyll` e só os assets usados. A pasta é versionada.
- Imagens (Pillow, só quando faltam; `python3 build_sites.py --imagens` refaz todas): capas leves `assets/catalogo-web/<slug>-240.webp`
  (240x280, q72), OG 1200x630 sem texto em `assets/sites/<chave>/og.jpg` e artes reduzidas de personagens em `assets/sites/<chave>/`.
- Todos os sites: noindex, canonical e og:url em `https://<dominio>/`, GA4 com evento `lp_cta` nos cliques com `data-cta`, rodapé com
  Termos, Privacidade, Jogo Responsável, Central de Ajuda, selo 18+ e a barra "Outros guias" com os outros 5 domínios.
  Links para a plataforma levam `utm_source=site&utm_medium=landing&utm_campaign=<chave>&utm_content=<posição>`.
- Verificador (no fim do build): todo asset citado existe na pasta do site, nenhum travessão no HTML, nenhum link para `oficial-spribe`,
  todo link para cassino.b7bet7.bet com `utm_campaign`, toda `<img>` com width, height e alt, imagem pré-carregada do hero abaixo de 120 KB
  e `index.html` abaixo de 150 KB.
- `build.py` não copia `assets/catalogo`, `assets/catalogo-web` nem `assets/sites` para `docs/` (são só dos sites .win).
- Publicação: `tools/publicar_sites.sh` envia cada pasta para o repositório `eduzeroumbet/site-<chave>` (branch main, raiz), no mesmo
  esquema de `tools/publicar_dominios.sh`. Os passos prévios (DNS na Cloudflare, criar o repositório, ativar o Pages) estão no cabeçalho.
  `DRY_RUN=1` só lista o que faria; `tools/publicar_sites.sh guiaslots` publica só os sites informados.
