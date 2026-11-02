# cassino-jogos

Landing pages estáticas dos principais jogos de cassino.b7bet7.bet, mobile first, com componentes Scrolltide
(Intro Loader, Focus Reveal, Lime Metrics, Expanded Cards, Reel, Step Path).

- Conteúdo: `data/games.json` (um bloco por jogo: textos, métricas, recursos, FAQ, cores, efeito do hero, personagem).
  - `description` (opcional): meta description própria, até 150 caracteres e terminando em frase completa (o build para se não cumprir).
    Sem ela, nome, provedor e lede até 150 caracteres, no fim da última frase completa ou na última palavra inteira, com ponto.
  - `faq`: de 5 a 6 perguntas (o build para se não cumprir), incluindo "Qual o valor mínimo de aposta?", "Como sacar?", "Funciona no celular?"
    e "O que é RTP?"; vira também o JSON-LD FAQPage.
  - `site.promos`: campanhas da plataforma (`badge`, `title`, `text`, `details`, `cta`, `url` completa em cassino.b7bet7.bet), renderizadas na seção
    "Promoções ativas" (id `promocoes`): na index logo depois da seção da grade de jogos (vermelho e roxo), nas landings logo depois de "O que esperar"
    (cor do jogo). Grade de 3 colunas no desktop, carrossel com snap no celular, nota "18+ · Regras completas em cada campanha...". A pergunta
    "Quais promoções estão ativas?" de cada FAQ resume as campanhas: ao trocar `site.promos`, atualize também essa resposta nos 8 jogos.
  - `vitrine_promos` (opcional, hoje só no Fortune Tiger): link "Ver promoções ativas" na vitrine, que rola até a seção.
  - Textos descrevem a mecânica do jogo; nada de promessa de ganho.
- SEO: cada landing tem um h1 em texto ("<jogo>: como jogar, RTP e recursos") abaixo do logo, maior que a frase de apoio (subtítulo); a index tem o h1
  exatamente "Os jogos de cassino mais jogados: guias e RTP" no HTML (caixa alta e quebras em CSS), um parágrafo de 80 a 120 palavras sobre o que cada
  guia traz (o build confere), cards com RTP e JSON-LD ItemList com os jogos. Capas e cards têm alt "Nome do jogo, Provedor"; personagens, descrição curta;
  imagens decorativas (fundo do hero, colagem, miniaturas dentro de botões com aria-label), alt="" e aria-hidden="true".
  `docs/sitemap.xml` lista a index e as 8 landings.
- Cabeçalho fixo (sticky, com `scroll-margin-top` nas âncoras): logo, "Jogos" (só a partir de 960 px), "Entrar" e "Criar conta".
- Estilo e comportamento: `src/lp.css`, `src/lp.js` (CSS e JS entram inline no HTML: 1 requisição a menos). O banco de personagens usa também `src/personagens.js`.
- Gerar: `python3 build.py` grava em `docs/` (publicado pelo GitHub Pages) e em `dist-dominios/` (um site por jogo). Ao limpar `docs/`, preserva `docs/previa-r4/` (de outra demanda; lista `MANTER` no build). No fim, o verificador confere que todo asset citado no HTML existe, que não há travessão, que toda `<img>` tem alt,
  que há um h1 por página, que não há "teste" em texto visível e que o carrossel "Outros favoritos" não usa loading="lazy".
  Depois: `python3 tools/checar_landings.py` confere em `docs/` e em cada `dist-dominios/<dominio>/` que todo src/href/srcset/poster local existe,
  `<img>` com alt, width e height, hero sem lazy, nenhuma imagem dependente de JS, og:image 1200x630, twitter:card, robots, 18+, UTMs e
  nenhum diminutivo (Tigrinho, Tourinho, Coelhinho, Dragãozinho, Ratinho) em texto visível, alt ou meta das landings e da index.
- Artes oficiais do acervo (`data/acervo.json`, `assets/acervo/<jogo>/`) nas landings:
  - Hero: fundo oficial do jogo (`bg-800`/`bg-1600` em srcset, pré-carregado; sem fundo, a arte quadrada, caso do Sweet Bonanza) cobrindo o topo,
    escurecido pelo overlay do `.hero`; logo PT do acervo no lugar do nome grande (alt do logo = nome do jogo; o h1 em texto vem logo abaixo);
    personagem recortado oficial (`char-1`) em destaque, no celular no alto e no desktop à direita. Fortune Tiger: o pacote traz só fundos e logo,
    então o hero fica sem personagem recortado (o personagem atual segue no bloco "Conheça o personagem"). Mines não tem arte no acervo e mantém o hero antigo.
  - Cards de "Outros favoritos" e da index (grade e colagem do topo): `assets/sites/cards/<jogo>.webp` (360x420, do `build_sites.py`) quando existe;
    senão a capa `assets/img/<jogo>-thumb.webp`.
  - og:image 1200x630 em `assets/og/<jogo>.jpg` (Pillow, só quando falta; `python3 build.py --imagens` refaz): fundo + logo PT + personagem;
    sem logo, a arte inteira (banner sem a faixa legal, ou a indicada em `og_arte` no `games.json`) sobre ela mesma desfocada. Mines continua com `assets/img/mines-og.jpg`.
  - O build copia para `docs/` e para cada domínio só os arquivos de `assets/acervo/` e `assets/sites/` que as páginas usam.
- Imagens: `tools_imgs.py` gera hero WebP 600/896, miniatura e OG 1200x630 (hoje usados só pelo Mines e como reserva das capas).
- Indexação: `site.indexar=false` (hoje, testes; ligar só com operação licenciada): robots index,follow e robots.txt Allow (com a linha Sitemap no `docs/`); `false` coloca noindex e Disallow.
  O banco de personagens (uso interno) é sempre noindex.
- Todos os links para a plataforma levam UTM e `rel="sponsored noopener"`: utm_source=landing, utm_medium=guia, utm_campaign=<jogo> (`hub` na index),
  utm_content=<posição: header, hero, vitrine ou final; promo-<n> nos cartões de promoção>; barra fixa e rodapé contam como final. O botão exato vai no evento `lp_cta` do GA4 (`data-cta`);
  os cartões de promoção mandam também `posicao` (promo-<n>, de `data-pos`).
  `python3 tools/checar_landings.py` também confere o contraste (>= 4,5) do texto auxiliar cinza de `src/lp.css` sobre os fundos escuros.

## Personagens

- Biblioteca: `assets/personagens/` (566 artes em WebP: `<nome>.webp` até 1000 px e `<nome>-thumb.webp` até 360 px) e o catálogo `data/personagens.json`
  (grupo, marca_ou_tema, subpasta, largura e altura do original, transparente, web, thumb, drive_nome, drive_link). Originais em alta ficam no Drive.
- Cada jogo tem em `games.json` o campo `character`:
  `{"main": caminho, "extras": [até 3 caminhos], "name": nome, "alt": texto alternativo, "bio": 2 frases, "crop": [x, y, w, h] opcional}`.
  `crop` (em px da versão web) mostra só um recorte da arte, em CSS; serve para os boards do elenco da casa, que trazem texto.
- Na landing: bloco "Conheça o personagem" logo depois das métricas (arte no HTML com src real, sem loading lazy
  e sem decoding="async", com fetchpriority baixo e width/height reais, lidos do cabeçalho do WebP; sem cartão branco: fundo transparente com brilho na cor do jogo;
  só os recortes de board, com `crop`, têm moldura). Fortune Tiger usa as artes recortadas `personagens-cassino-copa-site/pg/fortune-tiger/`. Com decoding="async" o Chrome adiava a decodificação fora da tela e capturas de página inteira mostravam só a moldura
  vazia. Se a arte falhar (onerror), o cartão mostra a capa do jogo (`assets/img/<jogo>-thumb.webp`); se nenhuma arte do personagem for válida
  (fora do catálogo ou arquivo ausente), o bloco fica só com o texto, sem o espaço da imagem. As miniaturas (principal + extras, 76 px no celular, 96 px no desktop) são botões
  que trocam a arte grande; abaixo, link "Ver todos os personagens" (personagens.html; no domínio próprio, a do GitHub Pages).
  Personagem no hero (celular e desktop): o recortado oficial do acervo; sem ele, a arte principal se tiver fundo transparente (Zeus),
  a menos que o `character` tenha `"hero": false` (Fortune Tiger, para manter o hero só com fundo e logo).
  Se o hero usa a própria arte principal, o bloco abre com a primeira extra, para não repetir a arte do hero.
- Carrossel "Outros favoritos": nenhum card com lazy nem decoding async (no desktop, cards sem rolar apareciam como bloco de cor vazio).
  No celular e no tablet rola na horizontal; a partir de 1024 px vira grade de 4 colunas, com todos os cards inteiros.
- Escolhas atuais: Tigre da Sorte, Coelho da Fortuna, Touro da Sorte, Dragão da Fortuna (nomes dos logos oficiais em PT) e Zeus (artes dos jogos);
  nos textos visíveis não se usam diminutivos. Sweet Bonanza, Big Bass Splash e Mines não têm
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
  `fichas` (RTP teórico, volatilidade, ganho máximo e grade por slug; só dados oficiais conhecidos, o resto aparece como "n/d"),
  `acervo` (slug do catálogo para a chave em `data/acervo.json`), `acervo_foco` (onde cortar banners largos), `provedores_jogo`
  (provedor real quando o catálogo traz a categoria, como "Crash Games")
  e `sites` (domínio, chave, estilo, título, descrição, cores, imagem do hero, OG, listas de jogos por slug e textos de cada seção).
  Os jogos vêm de `data/catalogo-plataforma.json` (url, nome, capa); itens com `disponivel=false` (Aviator da Spribe) fazem o build parar se forem usados.
- Gerar: `python3 build_sites.py` grava `dist-sites/<dominio>/` com `index.html` (CSS e JS inline), `404.html` que volta para `/`, `CNAME`,
  `robots.txt` (Disallow), `.nojekyll` e só os assets usados. A pasta é versionada.
- Imagens (Pillow, só quando faltam; `python3 build_sites.py --imagens` refaz todas), todas locais em cada site:
  cards com as artes oficiais do acervo (`assets/sites/cards/<chave do acervo>.webp`, 360x420: fundo + personagem + logo PT, ou banner
  sem a faixa legal); jogos sem arte no acervo usam a capa leve do catálogo `assets/catalogo-web/<slug>-240.webp`; sem imagem nenhuma,
  o card vira um degradê com o nome do jogo em CSS. Arte do topo de cada site montada a partir de `hero_arte` em `sites.json`
  (`assets/sites/<chave>/capa.webp` ou `hero.webp`), OG 1200x630 sem texto em `assets/sites/<chave>/og.jpg` (copiada para `og.jpg` na raiz
  do site) e personagens reduzidos em `assets/sites/<chave>/`.
- Todos os sites: header fixo com "Criar conta" e, no celular (< 720 px), barra fixa de cadastro no rodapé (o body ganha padding-bottom;
  com JS ela some enquanto a arte do topo está na tela).
- Depois do build: `python3 tools/checar_sites.py` confere que todo src/href local existe, `<img>` com alt/width/height, og.jpg,
  noindex, robots.txt e que nenhum texto tem "Tigrinho" ou "ver no jogo".
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
