#!/usr/bin/env python3
"""Curadoria do acervo de artes oficiais dos provedores para o kit visual dos sites.

Lê o acervo em ACERVO (padrão: projetos/artes-cassino/acervo na raiz da Orquestra) e grava
versões web em assets/acervo/<chave>/ com papéis fixos:
  bg-1600.webp / bg-800.webp       fundo de cenário (paisagem), sem texto sempre que possível
  banner-1200.webp / banner-600.webp  arte 1200x630 (pode ter logo do jogo)
  logo.webp                        logotipo do jogo (transparente), versão PT quando existir
  char-1.webp, char-2.webp ...     personagens recortados (transparentes), até 900 px de altura
O resultado vai para data/acervo.json (papéis, tamanhos e caminho de origem de cada arquivo).
Rodar da raiz do repositório: python3 tools/curar_acervo.py
"""
import glob, json, os, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACERVO = os.environ.get("ACERVO", os.path.join(os.path.dirname(os.path.dirname(ROOT)), "projetos/artes-cassino/acervo"))
EXTRA_TIGER = os.environ.get("TIGER_DIR", "/tmp/pgtiger/Promotion Pack")
OUT = os.path.join(ROOT, "assets/acervo")
PG = os.path.join(ACERVO, "PG Soft")
PP = os.path.join(ACERVO, "Pragmatic Play/Biblioteca do site")

def pg(game, sub):
    return os.path.join(PG, game, sub)

# chave: {papel: [padrões glob em ordem de preferência]}
PICKS = {
    "fortune-tiger": {
        "bg": [EXTRA_TIGER + "/Background/*landscape1*", EXTRA_TIGER + "/Background/*landscape*"],
        "logo": [EXTRA_TIGER + "/Logotype Multilanguages/*_pt.png", EXTRA_TIGER + "/Logotype/*.png"],
    },
    "fortune-ox": {
        "bg": [pg("Fortune Ox", "Promotion Pack/Promotion Pack/Background/*landscape.jpg"), pg("Fortune Ox", "Promotion Pack/Promotion Pack/Background/*landscape*")],
        "banner": [pg("Fortune Ox", "Promotion Pack/Promotion Pack/Web Banners/*")],
        "logo": [pg("Fortune Ox", "Promotion Pack/Promotion Pack/Logotype Multilanguage/*_pt.png")],
        "char": [pg("Fortune Ox", "Promotion Pack/Promotion Pack/Characters/*.png")],
    },
    "fortune-rabbit": {
        "bg": [pg("Fortune Rabbit", "Promotion Pack/Promotion Pack/Background/*landscape*"), pg("Fortune Rabbit", "Promotion Pack/Promotion Pack/Background/*")],
        "banner": [pg("Fortune Rabbit", "Promotion Pack/Promotion Pack/Web Banner/*")],
        "logo": [pg("Fortune Rabbit", "Promotion Pack/Promotion Pack/Logotype Multilanguages/*_pt.png")],
        "char": [pg("Fortune Rabbit", "Promotion Pack/Promotion Pack/Characters/*.png")],
    },
    "fortune-dragon": {
        "bg": [pg("Fortune Dragon", "Promotion Pack/Promotion Pack/Background/*landscape*"), pg("Fortune Dragon", "Promotion Pack/Promotion Pack/Background/*")],
        "banner": [pg("Fortune Dragon", "Promotion Pack/Promotion Pack/Web Banners/*")],
        "logo": [pg("Fortune Dragon", "Promotion Pack/Promotion Pack/Logotype Multilanguage/*_pt.png")],
        "char": [pg("Fortune Dragon", "Promotion Pack/Promotion Pack/Characters/*.png")],
    },
    "fortune-snake": {
        "bg": [pg("Fortune Snake", "Promotion Pack/EN/Promotion Pack/Background/*landscape*"), pg("Fortune Snake", "Promotion Pack/EN/Promotion Pack/Background/*")],
        "banner": [pg("Fortune Snake", "Promotion Pack/EN/Promotion Pack/Web Banners/*")],
        "logo": [pg("Fortune Snake", "Promotion Pack/EN/Promotion Pack/Logotype Multilanguage/*_pt_br.png"), pg("Fortune Snake", "Promotion Pack/EN/Promotion Pack/Logotype Multilanguage/*_pt.png")],
        "char": [pg("Fortune Snake", "Promotion Pack/EN/Promotion Pack/Characters/*.png")],
    },
    "wild-bandito": {
        "bg": [pg("Wild Bandito", "Promotion Packs/Promotion Pack/Backgrounds/*landscape1*")],
        "banner": [pg("Wild Bandito", "Promotion Packs/Promotion Pack/Web Banner/*")],
        "logo": [pg("Wild Bandito", "Promotion Packs/Promotion Pack/Logotype Multilanguages/*_pt.png")],
        "char": [pg("Wild Bandito", "Promotion Packs/Promotion Pack/Characters/*.png")],
    },
    "cash-mania": {
        "bg": [pg("Cash Mania", "Promotion Pack/EN/promotion packs/Backgrounds/*background1*")],
        "banner": [pg("Cash Mania", "Promotion Pack/EN/promotion packs/Web Banner/*")],
        "logo": [pg("Cash Mania", "Promotion Pack/EN/promotion packs/Logotype Multilanguages/*_pt.png")],
        "char": [pg("Cash Mania", "Promotion Pack/EN/promotion packs/Characters/*.png")],
    },
    "gates-of-olympus": {
        "bg": [PP + "/Gates Of Olympus/Gates-of-Olympus-Background.jpg"],
        "banner": [PP + "/Gates Of Olympus/Gates-of-Olympus_1200x630_BR.jpg"],
        "square": [PP + "/Gates Of Olympus/Gates-of-Olympus_1000x1000.jpg"],
    },
    "gates-of-olympus-1000": {
        "banner": [PP + "/Gates Of Olympus 1000/*1200x630_BR.jpg"],
        "square": [PP + "/Gates Of Olympus 1000/*1000x1000.jpg"],
    },
    "gates-of-olympus-super-scatter": {
        "banner": [PP + "/Gates Of Olympus Super Scatter/*WithoutFooter*", PP + "/Gates Of Olympus Super Scatter/*1200x630_BR*", PP + "/Gates Of Olympus Super Scatter/*"],
    },
    "sweet-bonanza": {
        "square": [PP + "/Diversos 2023/Sweet-Bonanza_900x900.jpg"],
        "banner": [PP + "/Sweet Bonanza Super Scatter/*WithoutFooter*"],
    },
    "sweet-bonanza-1000": {
        "banner": [PP + "/Diversos 2026/Sweet-Bonanza-1000_1200x630_BR.jpg"],
    },
    "sweet-bonanza-super-scatter": {
        "banner": [PP + "/Sweet Bonanza Super Scatter/*WithoutFooter*"],
    },
    "big-bass-splash": {
        "banner": [PP + "/Big Bass Splash/Big-Bass-Splash_1200x630_BR.jpg"],
        "square": [PP + "/Big Bass Splash/Big-Bass-Splash_900x900.jpg"],
        "bg": [PP + "/Big Bass Splash/Big-Bass-Splash-EN.jpg"],
    },
    "sugar-rush": {
        "banner": [PP + "/Sugar Rush/Sugar-Rush_1200x630_BR.jpg"],
        "square": [PP + "/Sugar Rush/Sugar-Rush_900x900.jpg"],
    },
    "starlight-princess": {
        "banner": [PP + "/Starlight Princess Super Scatter/*WithoutFooter*", PP + "/Starlight Princess Super Scatter/*1200x630*", PP + "/Starlight Princess Super Scatter/*"],
    },
    "the-dog-house": {
        "banner": [PP + "/The Dog House Megaways 1000/*1200x630*", PP + "/The Dog House Megaways 1000/*"],
    },
    "spaceman": {
        "bg": [PP + "/Spaceman/Spaceman_Background.jpg"],
        "banner": [PP + "/Spaceman/spaceman_without-footer.jpg"],
        "char": [PP + "/Spaceman/Spaceman_Fly_Pose.png"],
    },
    "jetx": {
        "square": [os.path.join(ACERVO, "Smartsoft/Jogos (capas)/New Era of JetX*"), os.path.join(ACERVO, "Smartsoft/Jogos (capas)/*jet_for_web*")],
    },
    "coyote-crash": {"square": [os.path.join(ACERVO, "Habanero/Jogos (capas)/Coyote Crash/*.png")]},
    "flying-high": {"square": [os.path.join(ACERVO, "Habanero/Jogos (capas)/Flying High/*.png")]},
}

IMG_EXT = (".png", ".jpg", ".jpeg", ".webp")

def candidates(patterns):
    for p in patterns:
        fs = sorted(f for f in glob.glob(p) if f.lower().endswith(IMG_EXT) and os.path.getsize(f) > 2000)
        if fs:
            return fs
    return []

def has_alpha(im):
    if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
        a = im.convert("RGBA").getchannel("A")
        return a.getextrema()[0] < 250
    return False

def save(im, path, w=None, h=None, q=74):
    im = im.copy()
    if w and im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    if h and im.height > h:
        im = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
    if im.mode not in ("RGB", "RGBA"):
        im = im.convert("RGBA" if has_alpha(im) else "RGB")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.save(path, "WEBP", quality=q, method=6)
    return {"arquivo": os.path.relpath(path, ROOT), "w": im.width, "h": im.height, "kb": round(os.path.getsize(path) / 1024)}

def open_ok(f):
    try:
        im = Image.open(f); im.load(); return im
    except Exception:
        return None

def main():
    data = {}
    for key, roles in PICKS.items():
        d = os.path.join(OUT, key); rec = {}
        for role, pats in roles.items():
            fs = candidates(pats)
            if not fs:
                continue
            if role == "char":
                # personagens transparentes, maiores primeiro, até 3
                ims = [(f, open_ok(f)) for f in fs]
                ims = [(f, im) for f, im in ims if im is not None and has_alpha(im)]
                ims.sort(key=lambda t: -(t[1].width * t[1].height))
                out = []
                for i, (f, im) in enumerate(ims[:3], 1):
                    bbox = im.convert("RGBA").getchannel("A").getbbox()
                    if bbox:
                        im = im.crop(bbox)
                    r = save(im, os.path.join(d, f"char-{i}.webp"), h=900, q=80); r["origem"] = os.path.relpath(f, ACERVO); out.append(r)
                if out:
                    rec["char"] = out
                continue
            # demais papéis: o maior arquivo válido do primeiro padrão que casar
            best = None
            for f in fs:
                im = open_ok(f)
                if im is None:
                    continue
                if best is None or im.width * im.height > best[1].width * best[1].height:
                    best = (f, im)
            if not best:
                continue
            f, im = best
            if role == "bg":
                rec["bg"] = [save(im, os.path.join(d, "bg-1600.webp"), w=1600, q=68), save(im, os.path.join(d, "bg-800.webp"), w=800, q=66)]
            elif role == "banner":
                rec["banner"] = [save(im, os.path.join(d, "banner-1200.webp"), w=1200, q=74), save(im, os.path.join(d, "banner-600.webp"), w=600, q=72)]
            elif role == "square":
                rec["square"] = [save(im, os.path.join(d, "square-800.webp"), w=800, q=74), save(im, os.path.join(d, "square-400.webp"), w=400, q=72)]
            elif role == "logo":
                bbox = im.convert("RGBA").getchannel("A").getbbox() if has_alpha(im) else None
                if bbox:
                    im = im.crop(bbox)
                rec["logo"] = [save(im, os.path.join(d, "logo.webp"), w=640, q=82)]
            for r in rec[role]:
                r["origem"] = os.path.relpath(f, ACERVO)
        if rec:
            data[key] = rec
            print(key, ", ".join(f"{k}:{len(v)}" for k, v in rec.items()))
        else:
            print(key, "SEM ARTE")
    json.dump({"acervo": "projetos/artes-cassino/acervo", "jogos": data}, open(os.path.join(ROOT, "data/acervo.json"), "w"), ensure_ascii=False, indent=1)
    tot = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, fs in os.walk(OUT) for f in fs)
    print(f"ok: {len(data)} jogos, {tot/1e6:.1f} MB em assets/acervo")

if __name__ == "__main__":
    main()
