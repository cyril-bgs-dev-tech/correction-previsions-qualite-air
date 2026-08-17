#!/usr/bin/env python3
"""Exporte une page du dossier en PDF — la pièce jointe qui ne dépend d'aucun service.

Pourquoi ce script existe
---------------------------
`presentation_atmo.pdf` était produit **à la main**, hors dépôt. Conséquence mesurée le
10/08/2026 : la page HTML a été régénérée trois fois dans la soirée, le PDF datait de la
veille, et rien ne le signalait — un artefact périmé ne se distingue pas d'un artefact
complet (`CLAUDE.md` § 4, et [[regenerer-peut-degrader]]). Une étape de livraison qui n'est
pas un script est une étape qu'on oubliera.

Le contrôle de fin porte sur l'artefact, jamais sur le code de sortie : le PDF est rouvert,
son nombre de pages est compté et comparé au plancher attendu. Un PDF d'une page est un
échec de rendu, pas une livraison.

Et le contrôle que ce plancher NE PEUT PAS faire — mesuré le 11/08/2026
------------------------------------------------------------------------
Ajouter la page 07 a fait passer le PDF de **54 à 49 pages**. Rien n'a été perdu : le
document entier a été rendu à l'échelle **0,90**, corps de texte de 9,75 pt tombé à
8,75 pt. Cause : la 8ᵉ entrée du sommaire portait la largeur de mise en page à **772 px**
pour **718 px** imprimables (A4 moins les marges), et Chromium **réduit tout le document**
plutôt que de couper. Un plancher de pages ne verra jamais cela — il compte des pages,
et le défaut en produit **moins**, donc plus loin du plancher, tout en s'aggravant.

Le contrôle qui l'attrape est en amont du PDF : mesurer la largeur de mise en page **à la
largeur imprimable** et refuser tout débordement, en NOMMANT l'élément qui déborde (une
mesure qui dit « ça déborde » sans dire « où » envoie chercher au hasard).

Usage : python3 scripts/exporter_pdf.py [page.html] [--pages-min 40]
"""

from __future__ import annotations

import re
import argparse
import pathlib
import sys

RACINE = pathlib.Path(__file__).resolve().parents[1]
FIG = RACINE / "reports/figures"

# A4 (210 mm) moins les marges gauche+droite de 10 mm, à 96 px CSS par pouce.
# C'est la largeur que Chromium donne à la mise en page en impression — pas le viewport.
LARGEUR_IMPRIMABLE = round((210 - 2 * 10) / 25.4 * 96)   # 718 px

# Cacher un élément et regarder si le débordement retombe : ça attrape ce qu'une lecture de
# rectangles rate — pseudo-éléments, conteneurs à `overflow`, débordements indirects.
_JS_COUPABLES = """() => {
  const large = () => document.documentElement.scrollWidth;
  const base = large(), trouves = [];
  let noeuds = [...document.querySelectorAll('body > *')], prof = 0;
  while (noeuds.length && prof < 8) {
    const suivants = [];
    for (const e of noeuds) {
      const memo = e.style.display;
      e.style.display = 'none';
      const sans = large();
      e.style.display = memo;
      if (sans < base) {
        trouves.push({prof, tag: e.tagName.toLowerCase(), id: e.id || '',
                      cls: ((e.className?.baseVal ?? e.className) || '').toString().slice(0, 44),
                      sans, txt: (e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 60)});
        suivants.push(...e.children);
      }
    }
    noeuds = suivants; prof++;
  }
  return {base, trouves};
}"""

# ── La sonde qui manquait — l'écrêtage INTERNE ─────────────────────────────────────────
#
# 🔴 Mesuré le 16/08/2026, signalé par une revue externe et vérifié sur le PDF lui-même.
# Le contrôle ci-dessus détecte ce qui pousse **le document** au-delà du papier. Un contenu
# placé dans un conteneur `overflow-x: auto` ne pousse rien : il défile à l'intérieur. À
# l'écran on fait glisser ; **sur papier il est simplement absent**, et le document mesure
# toujours 718 px. Le contrôle passait donc au vert sur un artefact tronqué.
#
# Ce que ça a coûté : le tableau de la page 04 fait ~805 px pour ~615 px de colonne utile.
# La page annonce en toutes lettres « À droite, séparée par un filet, la colonne qui se
# cite » — notre gain contre la chaîne en service — et cette colonne **n'apparaît nulle
# part dans le PDF**. Le dossier imprimé ne contient pas le chiffre qu'il désigne lui-même
# comme le seul citable.
#
# C'est la § 2 quinquies à la lettre : *un seuil doit regarder du côté où le défaut pousse*.
# Ici le défaut ne pousse rien — il RETRANCHE. Aucun seuil de largeur ne peut le voir.
_JS_ECRETAGE = """() => {
  const perdus = [];
  for (const e of document.querySelectorAll('*')) {
    const s = getComputedStyle(e);
    if (!/auto|scroll|hidden/.test(s.overflowX)) continue;
    const debord = e.scrollWidth - e.clientWidth;
    if (debord > 2) perdus.push({
      tag: e.tagName.toLowerCase(), id: e.id || '',
      cls: ((e.className?.baseVal ?? e.className) || '').toString().slice(0, 40),
      contenu: e.scrollWidth, visible: e.clientWidth, perdu: debord,
      enfant: (function(){ var m = null, w = 0;
        for (const c of e.children) if (c.scrollWidth > w) { w = c.scrollWidth; m = c; }
        return m ? m.tagName.toLowerCase() + (m.id ? '#' + m.id : '') +
          (m.className ? '.' + String(m.className).split(' ')[0] : '') + ' (' + w + 'px)' : '?';
      })(),
      txt: (e.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 50)});
  }
  return perdus.sort((a, b) => b.perdu - a.perdu);
}"""


def largeur_de_mise_en_page(pg) -> tuple[int, list[dict]]:
    """La largeur réellement occupée en impression, et qui la pousse au-delà du papier."""
    pg.set_viewport_size({"width": LARGEUR_IMPRIMABLE, "height": 1400})
    pg.wait_for_timeout(400)
    r = pg.evaluate(_JS_COUPABLES)
    ecretes = pg.evaluate(_JS_ECRETAGE)
    pg.set_viewport_size({"width": 1120, "height": 1400})
    pg.wait_for_timeout(200)
    return r["base"], r["trouves"], ecretes


def jetons_fantomes(source: pathlib.Path) -> list[tuple[str, str, str]]:
    """Les `var(--jeton, repli)` dont le jeton n'est défini NULLE PART.

    Le défaut, trouvé le 17/08 par la revue de design : les pages 07 et 08 référençaient
    `var(--bord, #d3dbe1)` — **`--bord` n'existe pas**, le document nomme ce jeton `--trait`.
    Le repli s'appliquait donc à chaque bordure, et il fallait un thème **sombre** pour le
    voir : `#d3dbe1` est visuellement indiscernable du `--trait` clair. En clair la page
    paraît juste, en sombre ses bordures restent gris pâle.

    > **Un repli de secours n'est pas une prudence : c'est ce qui empêche l'erreur de se
    > voir.** Sans lui, un jeton absent rend la déclaration invalide et le défaut saute aux
    > yeux au premier rendu.

    C'est § 2 bis appliqué au style — *nommer ce qu'on lit, et compter le reçu contre le
    demandé* — et la même signature que tout ce fichier traque : rien ne plante, tout est
    plausible.
    """
    styles = "\n".join(f.read_text(encoding="utf-8") for f in sorted(FIG.glob("_p*.css")))
    page = source.read_text(encoding="utf-8")
    definis = set(re.findall(r"(--[a-z0-9-]+)\s*:", page + styles, re.I))
    fantomes = []
    for f in sorted(FIG.glob("_p*.css")):
        for jeton, repli in re.findall(r"var\(\s*(--[a-z0-9-]+)\s*,\s*([^)]+)\)",
                                       f.read_text(encoding="utf-8"), re.I):
            if jeton not in definis:
                fantomes.append((f.name, jeton, repli.strip()))
    return fantomes


def exporter(source: pathlib.Path, cible: pathlib.Path, pages_min: int) -> int:
    from playwright.sync_api import sync_playwright

    # Avant d'ouvrir un navigateur : un jeton fantôme se lit dans les fichiers, et le
    # rendu ne le trahit qu'en thème sombre — que cet export ne demande pas.
    if fantomes := jetons_fantomes(source):
        print(f"ÉCHEC : {len(fantomes)} jeton(s) de style référencé(s) et JAMAIS défini(s) — "
              f"le repli s'applique en silence et la page sort du thème :")
        for nom, jeton, repli in fantomes[:8]:
            print(f"    {nom} · var({jeton}, {repli}) → « {jeton} » n'existe nulle part")
        return 1

    erreurs: list[str] = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": 1120, "height": 1400}, color_scheme="light")
        pg.on("pageerror", lambda e: erreurs.append(str(e)))
        pg.goto(f"file://{source}")
        # 🔴 On attend une CONDITION, jamais un délai. Le `wait_for_timeout(1800)` qui vivait
        # ici était une constante en dur (règle A) et ne garantissait rien : les scripts de
        # page font jusqu'à 19 écritures `innerHTML` chacun, et si la capture les précède, le
        # PDF emporte des emplacements vides que le CSS **cache lui-même**
        # (`.p4-fr:empty { display:none }`). Le contrôle de fin ne peut pas le voir — 61 pages
        # vides de leurs chiffres font toujours 61 pages.
        #
        # La liste des pages attendues se DÉRIVE du document (les `<script data-page=…>` qu'il
        # contient), jamais d'une constante : une page ajoutée entre dans le contrôle sans
        # qu'on ait à y penser, et une page dont l'injecteur aurait oublié le drapeau se
        # signale d'elle-même.
        attendues = pg.eval_on_selector_all(
            "script[data-page]", "els => els.map(e => e.dataset.page)")
        if attendues:
            try:
                pg.wait_for_function(
                    "ps => ps.every(p => document.documentElement.dataset['pret_' + p])",
                    arg=attendues, timeout=20_000)
            except Exception:
                absentes = pg.evaluate(
                    "ps => ps.filter(p => !document.documentElement.dataset['pret_' + p])",
                    attendues)
                print(f"ÉCHEC : {len(absentes)} script(s) de page n'ont pas fini — "
                      f"{absentes}. Le PDF aurait porté des emplacements VIDES, que le CSS "
                      f"masque et qu'aucun compte de pages ne peut voir.")
                b.close()
                return 1
            print(f"scripts de page : {len(attendues)}/{len(attendues)} terminés "
                  f"({', '.join(attendues)})")
        pg.wait_for_timeout(300)           # laisser la mise en page se poser après le rendu
        pg.emulate_media(media="print")
        largeur, coupables, ecretes = largeur_de_mise_en_page(pg)
        pg.pdf(path=str(cible), format="A4", print_background=True,
               margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})
        pg.close()
        b.close()

    if not cible.exists():
        print(f"AUCUN fichier écrit : {cible}")
        return 1
    # Compter les pages sans dépendance : le nombre d'objets /Type /Page du PDF.
    brut = cible.read_bytes()
    pages = brut.count(b"/Type /Page") - brut.count(b"/Type /Pages")
    nom = cible.relative_to(RACINE) if cible.is_relative_to(RACINE) else cible
    print(f"Écrit : {nom} · {len(brut) / 1024:.0f} ko · "
          f"{pages} pages" + (f" · erreurs de console : {erreurs}" if erreurs else ""))

    # ── L'écrêtage interne : un contenu perdu à l'impression, sans rien pousser ────────
    if ecretes:
        print(f"ÉCHEC : {len(ecretes)} conteneur(s) écrêté(s) à l'impression — le contenu "
              f"déborde À L'INTÉRIEUR, donc il DÉFILE à l'écran et DISPARAÎT sur papier :")
        for e in ecretes[:6]:
            print(f"   {e['tag']}{'#' + e['id'] if e['id'] else ''}"
                  f"{'.' + e['cls'].split()[0] if e['cls'] else ''} · "
                  f"{e['contenu']} px de contenu pour {e['visible']} px visibles — "
                  f"**{e['perdu']} px perdus**")
            print(f"      plus large enfant : {e.get('enfant', '?')}")
            print(f"      « {e['txt']} »")
        print("   Un tableau plus large que la colonne se SCINDE en deux tableaux "
              "empilés ; il ne défile pas.")
        return 1

    if largeur > LARGEUR_IMPRIMABLE:
        print(f"ÉCHEC : mise en page {largeur} px pour {LARGEUR_IMPRIMABLE} px imprimables — "
              f"Chromium a réduit TOUT le document à {LARGEUR_IMPRIMABLE / largeur:.0%}, "
              f"ces {pages} pages sont en plus petit. Ce qui déborde :")
        for c in coupables[-6:]:
            print(f"   {'  ' * c['prof']}{c['tag']}"
                  f"{'#' + c['id'] if c['id'] else ''}"
                  f"{'.' + c['cls'] if c['cls'] else ''}   « {c['txt']} »")
        if not coupables:
            print("   (aucun élément isolé — le débordement vient du corps lui-même)")
        return 1
    print(f"Mise en page : {largeur} px ≤ {LARGEUR_IMPRIMABLE} px imprimables — échelle 1:1")

    if pages < pages_min:
        print(f"ÉCHEC : {pages} pages pour un plancher de {pages_min} — rendu incomplet")
        return 1
    return 1 if erreurs else 0


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("page", nargs="?", default="presentation_atmo.html")
    a.add_argument("--pages-min", type=int, default=40,
                   help="plancher de pages attendu ; le dossier en faisait 53 le 09/08")
    n = a.parse_args()
    source = FIG / n.page
    if not source.exists():
        print(f"introuvable : {source}")
        return 1
    return exporter(source, source.with_suffix(".pdf"), n.pages_min)


if __name__ == "__main__":
    sys.exit(main())
