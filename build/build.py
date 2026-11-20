#!/usr/bin/env python3
"""Génère le site statique dans public/ à partir de content/ et _source/.

Lancer depuis la racine du dépôt :  python3 build/build.py
"""
import html, json, os, re, shutil, sys
from datetime import date
from pathlib import Path

import markdown
from PIL import Image

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "_source"
CONTENU = RACINE / "content"
STATIQUE = RACINE / "static"
SORTIE = RACINE / "public"

DOMAINE = "https://www.nathanaelfrancisco.com"
# Tant que le site est sur l'adresse provisoire, on demande aux moteurs de ne pas l'indexer.
PROVISOIRE = os.environ.get("PROVISOIRE", "1") == "1"

TEL = "+33652531832"
TEL_AFFICHE = "06 52 53 18 32"
LIEN_STAGES = "https://stages-bien-etre-drome.fr"

# Articles dans l'ordre du plan du site d'origine (adresses conservées à l'identique).
ARTICLES = """
ressources-bien-etre/gratitude-reguler-systeme-nerveux
alchimie-emotionnelle-transmutation-directe
comment-fonctionnent-les-emotions
alchimie-emotionnelle-le-scenario-de-guerison
surmonter-la-depression
difference-tristesse-fatigue-depression
perte-de-plaisir-anhedonie-depression
biais-negativite-depression-perception-realite
je-reviens-de-cuba
rsft-flexibilite-resistance-qualites-profondes
ecologie-interieure-pourquoi
il-existe-tellement-de-plaisirs-dans-la-vie
et-si-ta-deprime-ton-manque-denergie-actuels-etaient-des-cadeaux
article-massage-hawaien-lomi-lomi
integrer-seance-stage-therapeutique
fight-club
mouvement-regenerateur-katsugen-undo
creation-de-realite
mouvements-spontanes-exercices-tre-trauma-releasing-exercices
le-travail-the-work-byron-katie
therapie-et-non-dualite
ressources-bien-etre/transe-comment-entrer-en-transe
ressources-bien-etre/mission-de-vie-quete-de-sens-vide-existentiel
ressources-bien-etre/comment-trouver-therapeute-qui-me-convienne
ressources-bien-etre/pourquoi-je-mange-trop
ressources-bien-etre/dialogue-imago-guide-pratique
ressources-bien-etre/automassage-cuisses
souvenirs-ecrans
ressources-bien-etre/yoga-du-rire-emotions
ressources-bien-etre/les-5-corps-carte-experience-humaine
education-somatique
ressources-bien-etre/ecologie-interieure-trouver-ta-propre-voie
""".split()

THEMES = [
    ("emotions", "Émotions et libération émotionnelle", """comment-fonctionnent-les-emotions alchimie-emotionnelle-transmutation-directe
        alchimie-emotionnelle-le-scenario-de-guerison ressources-bien-etre/gratitude-reguler-systeme-nerveux
        ressources-bien-etre/yoga-du-rire-emotions le-travail-the-work-byron-katie ressources-bien-etre/pourquoi-je-mange-trop
        ressources-bien-etre/dialogue-imago-guide-pratique"""),
    ("deprime", "Déprime et dépression", """surmonter-la-depression difference-tristesse-fatigue-depression perte-de-plaisir-anhedonie-depression
        biais-negativite-depression-perception-realite et-si-ta-deprime-ton-manque-denergie-actuels-etaient-des-cadeaux
        il-existe-tellement-de-plaisirs-dans-la-vie"""),
    ("corps", "Corps, mouvement et massage", """mouvements-spontanes-exercices-tre-trauma-releasing-exercices mouvement-regenerateur-katsugen-undo
        education-somatique rsft-flexibilite-resistance-qualites-profondes ressources-bien-etre/automassage-cuisses
        ressources-bien-etre/transe-comment-entrer-en-transe article-massage-hawaien-lomi-lomi fight-club"""),
    ("sens", "Sens, chemin intérieur et thérapie", """ressources-bien-etre/mission-de-vie-quete-de-sens-vide-existentiel creation-de-realite
        therapie-et-non-dualite ressources-bien-etre/les-5-corps-carte-experience-humaine ecologie-interieure-pourquoi
        ressources-bien-etre/ecologie-interieure-trouver-ta-propre-voie ressources-bien-etre/comment-trouver-therapeute-qui-me-convienne
        integrer-seance-stage-therapeutique souvenirs-ecrans je-reviens-de-cuba"""),
]
TITRES = {
    "/surmonter-la-depression": "Surmonter la dépression : le guide pour en sortir, étape par étape | Nathanaël Francisco",
}
DESCRIPTIONS = {
    "/surmonter-la-depression": "Traiter et guérir la dépression : les étapes essentielles, des réflexions et des actions concrètes à appliquer dans tous les domaines de ta vie.",
}
THEME_DE = {"/" + u: (cle, nom) for cle, nom, liste in THEMES for u in liste.split()}

# Pages reprises du site d'origine, avec leurs retouches.
PAGES_SOURCE = {
    "a-propos": dict(
        h1="Bonjour, je suis Nathanaël Francisco",
        sous_titre="Thérapeute psycho-corporel, je t'accompagne pour libérer les difficultés émotionnelles et les blocages.",
        couper_avant="![](../images/67c72e044f00b_0.ProfilePicNathanael.jpg)",
    ),
    "mentions-legales": dict(
        h1="Mentions légales",
        remplacer=[
            ("Le site est hébergé par : OVH SAS", "Le site est hébergé par : Cloudflare, Inc."),
            ("SIRET : 424 761 419 00045", ""),
            ("Adresse : 2 rue Kellermann - 59100 Roubaix - France", "Adresse : 101 Townsend Street, San Francisco, CA 94107, États-Unis"),
        ],
    ),
    "politique-de-confidentialite": dict(h1="Politique de confidentialité"),
    "cgv": dict(h1="Conditions générales de vente"),
    "atelier-ecologie-interieure-die": dict(h1="Ateliers d'écologie intérieure à Die"),
    "consulting": dict(h1="Consulting"),
    "jeux-de-relations-authentiques": dict(h1="Jeux de relations authentiques"),
}

# Anciennes adresses qui ne sont plus des pages : redirection définitive (301).
REDIRECTIONS = {
    "/accompagnement-psycho-corporel": "/therapie-psycho-corporelle",
    "/seance-individuelle": "/therapie-psycho-corporelle",
    "/difficultes-emotionnelles-blocages": "/therapie-psycho-corporelle",
    "/personnes-deprimees": "/therapie-psycho-corporelle",
    "/sortir-de-la-depression": "/therapie-psycho-corporelle",
    "/trop-travail-deprime": "/therapie-psycho-corporelle",
    "/a-quoi-sattendre": "/therapie-psycho-corporelle",
    "/reserver-seance": "/contact",
    "/stages-bien-etre-ecologie-interieure-drome": "/stages",
    "/stages-bien-etre-ecologie-interieure-drome-26fev26": "/stages",
    "/stage-bien-etre-ecologie-interieure": "/stages",
    "/stages-bien-etre": "/stages",
    "/infos-stages": "/stages",
    "/paiement-acompte-stage": "/stages",
    "/merci-acompte": "/stages",
    "/guide-complet": "/ressources-bien-etre",
    "/telechargez-le-guide": "/ressources-bien-etre",
    "/accueil-backup": "/",
    "/search": "/posts",
    "/category/massage": "/posts",
    "/category": "/posts",
    "/e926ec90": "/", "/86647788": "/", "/60eaf418": "/", "/cfff1d2c": "/",
    "/33ecc55e": "/", "/447c830d": "/", "/1d7e4290": "/", "/fe7e8ab0": "/", "/cbc40fbf": "/",
}

MENU = [
    ("Séances à Die", "/les-mains-qui-soignent"),
    ("En ligne", "/therapie-psycho-corporelle"),
    ("Stages", "/stages"),
    ("Articles", "/posts"),
    ("Qui suis-je", "/a-propos"),
]

SIGLES = {"TRE", "RSFT", "IFS", "BBTRS", "RDV", "CGV", "SIRET", "OVH", "DIE", "DRÔME"}

images_utilisees = set()
TEMOIGNAGES = json.loads((Path(__file__).resolve().parent.parent / "content" / "temoignages.json").read_text(encoding="utf-8"))


def carte_temoignage(t):
    source = f' <span>· {html.escape(t["source"])}</span>' if t.get("source") else ""
    return (f'<figure class="temoignage"><blockquote><p>{html.escape(t["texte"])}</p></blockquote>'
            f'<figcaption>{html.escape(t["nom"])}{source}</figcaption></figure>')


def inserer_temoignages(texte):
    def remplace(m):
        utilises, cartes = set(), []
        for nom in m.group(1).split("|"):
            for i, t in enumerate(TEMOIGNAGES):
                if t["nom"] == nom.strip() and i not in utilises:
                    utilises.add(i); cartes.append(carte_temoignage(t)); break
        return "\n".join(cartes)
    return re.sub(r"\{\{temoignages:([^}]+)\}\}", remplace, texte)


# ---------- outils ----------
def lire_md(chemin):
    t = chemin.read_text(encoding="utf-8")
    meta = {}
    if t.startswith("---\n"):
        tete, corps = t[4:].split("\n---\n", 1)
        for ligne in tete.splitlines():
            if ":" in ligne:
                k, v = ligne.split(":", 1)
                meta[k.strip()] = v.strip()
    else:
        corps = t
    return meta, corps


def casse_phrase(texte):
    lettres = [c for c in texte if c.isalpha()]
    if not lettres or sum(c.isupper() for c in lettres) / len(lettres) < 0.7:
        return texte
    mots = []
    for i, mot in enumerate(texte.split(" ")):
        nu = re.sub(r"[^\wÀ-ÿ]", "", mot)
        if nu.upper() in SIGLES and nu.upper() not in {"DIE", "DRÔME"}:
            mots.append(mot)
        else:
            mots.append(mot.lower())
    phrase = " ".join(mots)
    phrase = re.sub(r"\b(die|drôme|lomi lomi|nathanaël|francisco|hawaïen)\b",
                    lambda m: m.group(0).title() if m.group(0) != "hawaïen" else "hawaïen", phrase)
    for i, c in enumerate(phrase):
        if c.isalpha():
            return phrase[:i] + c.upper() + phrase[i + 1:]
    return phrase


def adresse_lien(href, base_dir=""):
    if re.match(r"^(https?:|mailto:|tel:|sms:|#)", href):
        return href
    href = href.replace("../", "")
    if href.startswith("index.html#row"):
        return "/contact"
    href = re.sub(r"#row-[\w-]+$", "", href)
    if href in ("index.html", ""):
        return "/"
    href = re.sub(r"\.html$", "", href)
    href = re.sub(r"/index$", "", href)
    chemin = "/" + href.lstrip("/")
    return REDIRECTIONS.get(chemin, chemin)


def video_html(url):
    url = url.replace("\\_", "_")
    m = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})", url)
    if not m:
        return f'<p><a href="{html.escape(url)}">Voir la vidéo</a></p>'
    vertical = " vertical" if "shorts/" in url else ""
    return (f'<div class="video{vertical}"><iframe src="https://www.youtube-nocookie.com/embed/{m.group(1)}" '
            f'title="Vidéo YouTube" loading="lazy" allow="accelerometer; encrypted-media; picture-in-picture" allowfullscreen></iframe></div>')


def nettoyer_source(corps, opts=None):
    opts = opts or {}
    if opts.get("couper_avant") and opts["couper_avant"] in corps:
        corps = corps[corps.index(opts["couper_avant"]):]
    else:
        # retire le premier titre H1 (affiché dans le bandeau)
        corps = re.sub(r"\A\s*# .*\n", "", corps, count=1)
    if opts.get("couper_apres") and opts["couper_apres"] in corps:
        corps = corps[:corps.index(opts["couper_apres"])]
    for a, b in opts.get("remplacer", []):
        corps = corps.replace(a, b)
    lignes = []
    for ligne in corps.splitlines():
        if re.match(r"^\[[^\]]+\]\(#row-[\w-]+\)\s*$", ligne):
            continue  # ancres internes de systeme.io
        m = re.match(r"^(#{1,6})\s+(.*)$", ligne)
        if m:
            niveau = max(2, len(m.group(1)))
            texte = re.sub(r"\*+", "", m.group(2)).strip()
            if not texte:
                continue
            ligne = "#" * niveau + " " + casse_phrase(texte)
        lignes.append(ligne)
    corps = "\n".join(lignes)
    corps = re.sub(r"  \n(?=[a-zà-ÿ(«“\"])", " ", corps)  # retours à la ligne forcés au milieu des phrases
    corps = re.sub(r"(?m)^\s*---\s*$", "", corps)  # les bandeaux de titres remplacent les filets
    corps = re.sub(r"(?m)^(\*{2,3})([^*\n]{3,70}?)\1\s*$",
                   lambda m: m.group(0) if m.group(2).rstrip().endswith((".", ",", ";", "!", ":")) else "### " + casse_phrase(m.group(2).strip()), corps)
    corps = re.sub(r"(?m)^((?:[\U0001F300-\U0001FAFF\u2600-\u27BF]\ufe0f?)\s+[^\n.!:;]{3,60})$", r"### \1", corps)
    corps = re.sub(r"\[\[VIDEO:([^\]]+)\]\]", lambda m: video_html(m.group(1)), corps)
    corps = re.sub(r"\]\(([^)\s]+)\)", lambda m: "](" + adresse_lien(m.group(1)) + ")", corps)
    corps = re.sub(r"\(/images/", "(../images/", corps)
    corps = re.sub(r"!\[([^\]]*)\]\(\.\./images/([^)]+)\)", lambda m: image_md(m.group(1), m.group(2)), corps)
    corps = re.sub(r"\]\(\.\./d1yei2z3i6k35z\.cloudfront\.net/[^)]*/([^/)]+)\)", lambda m: "](" + chemin_image(m.group(1)) + ")", corps)
    return corps


def chemin_image(nom):
    if not (SOURCE / "images" / nom).exists():
        return "https://d1yei2z3i6k35z.cloudfront.net/6055378/" + nom
    images_utilisees.add(nom)
    stem = Path(nom).stem
    ext = Path(nom).suffix.lower()
    return f"/images/{stem}.webp" if ext in (".png", ".jpg", ".jpeg") else f"/images/{nom}"


def image_md(alt, nom):
    return f"![{alt}]({chemin_image(nom)})"


def md_vers_html(texte):
    texte = inserer_temoignages(texte)
    h = markdown.markdown(texte, extensions=["extra", "sane_lists"])
    h = h.replace("<img ", '<img loading="lazy" ')
    return h


def premiere_image(html_txt):
    m = re.search(r'<img[^>]+src="(/images/[^"]+)"', html_txt)
    return m.group(1) if m else None


def texte_brut(html_txt, n=170):
    t = re.sub(r"<[^>]+>", " ", html_txt)
    t = html.unescape(re.sub(r"\s+", " ", t)).strip()
    return (t[:n].rsplit(" ", 1)[0] + "…") if len(t) > n else t


# ---------- gabarit ----------
def gabarit(url, titre, description, corps, image=None, actif=None):
    canon = DOMAINE + (url if url != "/" else "/")
    robots = '<meta name="robots" content="noindex, nofollow">' if PROVISOIRE else ""
    menu = "".join(
        f'<li><a href="{lien}"{" aria-current=\"page\"" if actif == lien else ""}>{nom}</a></li>' for nom, lien in MENU)
    og_image = f'<meta property="og:image" content="{DOMAINE}{image}">' if image else ""
    personne = {
        "@context": "https://schema.org", "@type": "Person", "name": "Nathanaël Francisco",
        "jobTitle": "Thérapeute psycho-corporel", "url": DOMAINE, "telephone": TEL,
        "address": {"@type": "PostalAddress", "streetAddress": "Espace Barral, 7 rue des Fabriques",
                    "postalCode": "26150", "addressLocality": "Die", "addressCountry": "FR"},
        "sameAs": ["https://www.facebook.com/nathanael.francisco", LIEN_STAGES],
    }
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(titre)}</title>
<meta name="description" content="{html.escape(description)}">
{robots}
<link rel="canonical" href="{canon}">
<meta property="og:type" content="website">
<meta property="og:title" content="{html.escape(titre)}">
<meta property="og:description" content="{html.escape(description)}">
<meta property="og:url" content="{canon}">
<meta property="og:locale" content="fr_FR">
{og_image}
<meta name="theme-color" content="#ffcc00">
<link rel="icon" href="/favicon.svg" type="image/svg+xml">
<link rel="preload" href="/fonts/poppins-latin-700-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/literata-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/style.css">
<script type="application/ld+json">{json.dumps(personne, ensure_ascii=False)}</script>
</head>
<body>
<a class="aller-contenu" href="#contenu">Aller au contenu</a>
<header class="entete">
  <div class="entete-interieur">
    <a class="marque" href="/">Nathanaël Francisco<small>Thérapeute psycho-corporel, à Die et en ligne</small></a>
    <nav class="menu" aria-label="Menu principal"><ul>{menu}<li class="menu-contact"><a href="/contact">Me contacter</a></li></ul></nav>
    <details class="menu-mobile"><summary>Menu</summary><ul>{menu}<li><a href="/contact">Me contacter</a></li></ul></details>
  </div>
</header>
<main id="contenu">
{corps}
</main>
<footer class="pied">
  <div class="pied-interieur">
    <div>
      <p class="marque-pied">Nathanaël Francisco</p>
      <p>Thérapie psycho-corporelle, soins énergétiques et massage.<br>À l'Espace Barral, à Die (Drôme), et en ligne.</p>
      <p><a href="sms:{TEL}">{TEL_AFFICHE}</a>, par SMS ou WhatsApp de préférence.</p>
    </div>
    <div>
      <h2>Séances</h2>
      <ul>
        <li><a href="/les-mains-qui-soignent">Les mains qui soignent, à Die</a></li>
        <li><a href="/massage-hawaien-lomi-lomi">Massage Lomi Lomi</a></li>
        <li><a href="/therapie-psycho-corporelle">Thérapie en ligne</a></li>
        <li><a href="/stages">Stages en Drôme</a></li>
      </ul>
    </div>
    <div>
      <h2>Ressources</h2>
      <ul>
        <li><a href="/posts">Articles</a></li>
        <li><a href="/ressources-bien-etre">Rejoindre la Tribu</a></li>
        <li><a href="/temoignages">Témoignages</a></li>
        <li><a href="https://www.facebook.com/nathanael.francisco" rel="noopener">Facebook</a></li>
      </ul>
    </div>
  </div>
  <p class="legal"><a href="/mentions-legales">Mentions légales</a> · <a href="/politique-de-confidentialite">Confidentialité</a> · <a href="/cgv">CGV</a></p>
</footer>
</body>
</html>
"""


def bandeau(h1, sous_titre=None, fil=None):
    f = ""
    if fil:
        nom, lien = fil
        f = f'<p class="fil"><a href="{lien}">{html.escape(nom)}</a></p>' if lien else f'<p class="fil">{html.escape(nom)}</p>'
    s = f'<p class="sous-titre">{html.escape(sous_titre)}</p>' if sous_titre else ""
    return f'<div class="bandeau"><div class="bandeau-interieur">{f}<h1>{html.escape(h1)}</h1>{s}</div></div>'


def suite_article():
    return f"""<aside class="suite">
<h2>Envie d'aller plus loin ?</h2>
<p>Je t'accompagne en séance individuelle, en ligne ou à Die. On peut commencer par un appel découverte gratuit de 20 à 30 minutes.</p>
<div class="actions"><a class="bouton" href="/appel-decouverte">Réserver un appel découverte</a><a class="bouton bouton-clair" href="/les-mains-qui-soignent">Séances à Die</a></div>
</aside>"""


def ecrire(url, contenu_html):
    chemin = SORTIE / ("index.html" if url == "/" else url.strip("/") + ".html")
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(contenu_html, encoding="utf-8")


# ---------- construction ----------
def construire():
    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    shutil.copytree(STATIQUE, SORTIE)
    pages_sitemap = []

    # Pages écrites à la main
    for f in sorted(CONTENU.glob("*.md")):
        meta, corps = lire_md(f)
        url = meta["url"]
        fil = (meta["fil"], None) if meta.get("fil") else None
        h = bandeau(meta["h1"], meta.get("sous_titre"), fil) + f'<div class="page"><article class="contenu">{md_vers_html(corps)}</article></div>'
        actif = url if any(url == l for _, l in MENU) else None
        ecrire(url, gabarit(url, meta["titre"], meta["description"], h, actif=actif))
        pages_sitemap.append(url)

    # Pages reprises du site d'origine
    for nom, opts in PAGES_SOURCE.items():
        meta, corps = lire_md(SOURCE / "pages" / f"{nom}.md")
        url = "/" + nom
        corps_html = md_vers_html(nettoyer_source(corps, opts))
        if nom == "temoignages":
            corps_html = re.sub(r"(<p><img[^>]+></p>\s*)+", lambda m: '<div class="temoignages">' + re.sub(r"</?p>", "", m.group(0)) + "</div>", corps_html)
        h = bandeau(opts["h1"], opts.get("sous_titre"), opts.get("fil")) + f'<div class="page"><article class="contenu">{corps_html}</article></div>'
        actif = url if any(url == l for _, l in MENU) else None
        ecrire(url, gabarit(url, meta.get("titre", opts["h1"]), meta.get("description", ""), h, premiere_image(corps_html), actif))
        if nom not in ("consulting", "jeux-de-relations-authentiques", "atelier-ecologie-interieure-die"):
            pages_sitemap.append(url)

    # Page témoignages
    groupes = [("therapie", "Thérapie et accompagnement"), ("soin", "Soins à Die"), ("massage", "Massage Lomi Lomi")]
    corps_t = '<p class="chapeau">Des mots reçus après une séance, un soin ou un massage.</p>'
    for cle, titre in groupes:
        cartes = "".join(carte_temoignage(t) for t in TEMOIGNAGES if t["type"] == cle)
        corps_t += f'<h2>{titre}</h2><div class="liste-temoignages">{cartes}</div>'
    corps_t += '<div class="encadre"><h2>Et toi ?</h2><p>On peut commencer par un appel découverte gratuit, pour sentir si c\'est juste pour toi.</p><div class="actions"><a class="bouton" href="/appel-decouverte">Réserver un appel découverte</a></div></div>'
    page = bandeau("Témoignages", "Ce que disent les personnes que j'ai accompagnées.") + \
        f'<div class="page"><article class="contenu" style="max-width:var(--large)">{corps_t}</article></div>'
    ecrire("/temoignages", gabarit("/temoignages", "Témoignages – Thérapie, soins et massage Lomi Lomi | Nathanaël Francisco",
                                    "Avis et témoignages sur les séances de thérapie psycho-corporelle, les soins à Die et le massage Lomi Lomi de Nathanaël Francisco.", page))
    pages_sitemap.append("/temoignages")

    # Articles
    fiches = []
    for chemin_url in ARTICLES:
        fichier = SOURCE / "pages" / (chemin_url.replace("/", "__") + ".md")
        corrige = CONTENU / "articles" / fichier.name
        if corrige.exists():
            fichier = corrige  # version retouchée (ton harmonisé, corrections)
        meta, corps = lire_md(fichier)
        m = re.search(r"^# (.+)$", corps, re.M)
        h1 = re.sub(r"\*+", "", m.group(1)).strip() if m else meta.get("titre", chemin_url)
        h1 = casse_phrase(h1)
        corps_html = md_vers_html(nettoyer_source(corps))
        url = "/" + chemin_url
        meta["titre"] = TITRES.get(url, meta.get("titre", h1))
        desc = DESCRIPTIONS.get(url) or meta.get("description") or texte_brut(corps_html)
        img = premiere_image(corps_html)
        cle, nom_theme = THEME_DE.get(url, ("", "Articles"))
        page = bandeau(h1, None, (nom_theme, f"/posts#{cle}" if cle else "/posts")) + f'<div class="page"><article class="contenu">{corps_html}{suite_article()}</article></div>'
        ecrire(url, gabarit(url, meta.get("titre", h1), desc, page, img, actif="/posts"))
        fiches.append(dict(url=url, titre=h1, resume=desc, image=img))
        pages_sitemap.append(url)

    def liste_articles(items):
        out = []
        for a in items:
            vignette = (f'<img class="vignette" src="{a["image"]}" alt="" loading="lazy">' if a["image"]
                        else "")
            out.append(f'<li><a href="{a["url"]}">{vignette}<span class="titre-article">{html.escape(a["titre"])}</span>'
                       f'<p class="resume">{html.escape(texte_brut(a["resume"], 130))}</p></a></li>')
        return '<ul class="articles">' + "".join(out) + "</ul>"

    sommaire = "".join(f'<a class="bouton bouton-clair" href="#{cle}">{nom}</a>' for cle, nom, _ in THEMES)
    sections = ""
    for cle, nom, _ in THEMES:
        items = [f for f in fiches if THEME_DE.get(f["url"], ("",))[0] == cle]
        sections += f'<h2 id="{cle}" class="titre-theme">{nom}</h2>{liste_articles(items)}'
    sans = [f for f in fiches if f["url"] not in THEME_DE]
    if sans:
        sections += f'<h2 class="titre-theme">Autres articles</h2>{liste_articles(sans)}'
    page = (bandeau("Articles", "Émotions, corps, déprime, pratiques : ce que j'apprends en chemin, en accès libre.")
            + f'<div class="page"><div class="page-articles"><nav class="actions sommaire" aria-label="Thèmes">{sommaire}</nav>{sections}</div></div>')
    ecrire("/posts", gabarit("/posts", "Articles – Émotions, corps et bien-être | Nathanaël Francisco",
                             "Articles sur les émotions, la déprime, le corps et les pratiques de libération émotionnelle, par Nathanaël Francisco, thérapeute psycho-corporel.", page, actif="/posts"))
    pages_sitemap.append("/posts")

    # Accueil
    choix = [f for f in fiches if f["url"] in ("/comment-fonctionnent-les-emotions", "/surmonter-la-depression",
                                                 "/mouvements-spontanes-exercices-tre-trauma-releasing-exercices")]
    photo = chemin_image("67c72e044f00b_0.ProfilePicNathanael.jpg")
    accueil = f"""
<section class="ouverture">
  <div class="ouverture-interieur">
    <h1>Difficultés émotionnelles ? Blocage ?</h1>
    <p class="promesse">Je t'aide à te libérer et à te sentir bien, en passant par le corps.</p>
    <p class="lieux">À Die, dans la Drôme, et en ligne.</p>
    <div class="actions"><a class="bouton" href="/appel-decouverte">Réserver un appel découverte gratuit</a></div>
  </div>
</section>
<section class="portes" aria-labelledby="titre-portes">
  <h2 id="titre-portes">Trois façons de travailler ensemble</h2>
  <ul class="porte-liste">
    <li><a class="porte" href="/les-mains-qui-soignent"><span class="porte-titre">Les mains qui soignent, à Die</span><span class="porte-detail">1h15, prix conscient de 50 à 100 €</span><p class="porte-texte">Thérapie psycho-corporelle, soins énergétiques et massage, réunis dans une même séance à l'Espace Barral.</p></a></li>
    <li><a class="porte" href="/therapie-psycho-corporelle"><span class="porte-titre">Thérapie psycho-corporelle en ligne</span><span class="porte-detail">En visio, où que tu sois</span><p class="porte-texte">Le corps reste au centre, même à distance : sensations, respiration, mouvement. Beaucoup de personnes sont surprises par la profondeur du travail depuis chez elles.</p></a></li>
    <li><a class="porte" href="/stages"><span class="porte-titre">Stages en Drôme</span><span class="porte-detail">En week-end, en groupe</span><p class="porte-texte">Un temps plus long pour vivre ces pratiques ensemble, au cœur de la nature.</p></a></li>
  </ul>
</section>
<section class="temoin">
  <figure>
    <blockquote><p>Je traversais un moment, un état difficile dans lequel j'étais bloqué depuis plusieurs jours. La séance m'a permis de le traverser pleinement dans mon corps, d'y voir plus clair et d'en sortir. Un grand merci !</p></blockquote>
    <figcaption>Témoignage anonyme, après une séance à Die</figcaption>
  </figure>
  <div class="actions"><a class="bouton bouton-clair" href="/temoignages">Lire d'autres témoignages</a></div>
</section>
<section class="presentation" aria-labelledby="titre-presentation">
  <img src="{photo}" alt="Portrait de Nathanaël Francisco" width="300" height="300" loading="lazy">
  <div class="texte">
    <h2 id="titre-presentation">Le même chemin que toi</h2>
    <p>J'ai traversé des émotions envahissantes, le stress, l'anxiété, et une dépression qui a duré quatre ans. Je n'ai pas fait ce chemin seul : je me suis fait accompagner, et c'est en passant par le corps que quelque chose a commencé à s'apaiser.</p>
    <p>Aujourd'hui, je transmets ce que j'ai moi-même expérimenté : un chemin de guérison incarné, respectueux, où l'on réapprend à être à la fois sensible et solide.</p>
    <p><a href="/a-propos">Mon parcours et mes outils</a></p>
  </div>
</section>
<section class="derniers" aria-labelledby="titre-derniers">
  <div class="derniers-interieur">
    <h2 id="titre-derniers">À lire pour commencer</h2>
    {liste_articles(choix)}
    <div class="actions"><a class="bouton bouton-clair" href="/posts">Tous les articles</a></div>
  </div>
</section>"""
    ecrire("/", gabarit("/", "Nathanaël Francisco – Thérapie psycho-corporelle à Die (Drôme) et en ligne",
                        "Stress, anxiété, déprime, blocages émotionnels : thérapie psycho-corporelle, soins et massage à Die (Drôme) et en ligne. Appel découverte gratuit.",
                        accueil, photo))
    pages_sitemap.insert(0, "/")

    # Page 404
    page = bandeau("Cette page n'existe plus", "Elle a peut-être changé d'adresse avec le nouveau site.") + \
        '<div class="page"><div class="contenu"><div class="actions"><a class="bouton" href="/">Revenir à l\'accueil</a><a class="bouton bouton-clair" href="/posts">Voir les articles</a></div></div></div>'
    (SORTIE / "404.html").write_text(gabarit("/404", "Page introuvable | Nathanaël Francisco", "Page introuvable.", page), encoding="utf-8")

    # Images
    (SORTIE / "images").mkdir(exist_ok=True)
    for nom in sorted(images_utilisees):
        src = SOURCE / "images" / nom
        ext = src.suffix.lower()
        if ext in (".png", ".jpg", ".jpeg"):
            im = Image.open(src)
            im = im.convert("RGBA") if im.mode in ("P", "LA") else im
            if im.width > 1400:
                im = im.resize((1400, round(im.height * 1400 / im.width)))
            im.save(SORTIE / "images" / f"{src.stem}.webp", "WEBP", quality=82, method=6)
        else:
            shutil.copy2(src, SORTIE / "images" / nom)

    # Redirections, robots, plan du site
    (SORTIE / "_redirects").write_text("".join(f"{a} {b} 301\n" for a, b in REDIRECTIONS.items()), encoding="utf-8")
    if PROVISOIRE:
        (SORTIE / "robots.txt").write_text("User-agent: *\nDisallow: /\n", encoding="utf-8")
    else:
        (SORTIE / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {DOMAINE}/sitemap.xml\n", encoding="utf-8")
    aujourdhui = date.today().isoformat()
    urls = "".join(f"<url><loc>{DOMAINE}{u}</loc><lastmod>{aujourdhui}</lastmod></url>" for u in pages_sitemap)
    (SORTIE / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>', encoding="utf-8")
    print(f"{len(pages_sitemap)} pages, {len(images_utilisees)} images")


if __name__ == "__main__":
    construire()
