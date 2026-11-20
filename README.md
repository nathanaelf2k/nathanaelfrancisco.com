# nathanaelfrancisco.com

Site de Nathanaël Francisco, thérapeute psycho-corporel à Die (Drôme) et en ligne.

- `content/` : pages écrites à la main (Markdown avec en-tête).
- `_source/` : contenu récupéré de l'ancien site (référence, non publié).
- `static/` : feuille de style, polices, favicon.
- `build/build.py` : génère le site dans `public/`.
- `public/` : site publié par Cloudflare (ne pas modifier à la main).

Pour reconstruire : `pip install markdown pillow` puis `python3 build/build.py`.
Quand le site passera sur le vrai domaine : `PROVISOIRE=0 python3 build/build.py` (autorise l'indexation par Google).
