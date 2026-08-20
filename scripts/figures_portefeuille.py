#!/usr/bin/env python3
"""Les visuels du portefeuille — SVG écrits à la main, une paire claire/sombre par figure.

Pourquoi du SVG écrit à la main
---------------------------------
Trois contraintes se rencontrent ici, et une seule solution les satisfait toutes.

**Le rendu est un README GitHub.** Pas de CSS, pas de JavaScript, pas d'onglets. Une figure
n'existe donc que sous forme d'image — et une image de texte est illisible à 380 px.

**La machine n'a aucune police emoji** (`fc-match emoji` → DejaVu Sans, mesuré le 20/08/2026).
Toute chaîne de rendu passant par un moteur graphique local risque donc de produire des carrés
là où le dossier attend des caractères. Le SVG déporte le rendu du texte sur le navigateur du
lecteur : c'est SA police qui s'applique, jamais celle de cette machine.

**Le lecteur peut être en thème sombre.** GitHub sert les deux, et une figure à fond blanc y
apparaît comme une tache. `<picture>` avec `prefers-color-scheme` est la seule forme que GitHub
documente comme supportée — d'où une paire de fichiers par figure plutôt qu'un fichier unique
qui tenterait sa chance avec une requête de média interne.

Ce que ces figures refusent de faire
--------------------------------------
**Aucune information n'est portée par la seule couleur.** Chaque valeur est écrite en toutes
lettres au bout de sa barre, et le seuil réglementaire est un trait annoté. Une impression en
noir et blanc, ou un lecteur daltonien, ne perdent rien — c'est la famille H de l'audit.

**Aucune grille, aucune légende, aucun axe secondaire.** Le rapport données/encre est le seul
critère de ce qui reste (famille G).

Usage : python3 scripts/figures_portefeuille.py
Sortie : reports/figures/portefeuille/*.svg  (+ copie dans le portefeuille)
"""

from __future__ import annotations

import pathlib
import shutil

RACINE = pathlib.Path(__file__).resolve().parents[1]
SORTIE = RACINE / "reports/figures/portefeuille"
PORTEFEUILLE = pathlib.Path.home() / "Portfolio/assets"

# Deux palettes, une par thème. `fond` reste transparent : GitHub peint le sien derrière.
THEMES = {
    "clair":  {"encre": "#1f2328", "attenue": "#57606a", "barre": "#0969da",
               "trait": "#d0d7de", "accent": "#1a7f37", "alerte": "#cf222e"},
    "sombre": {"encre": "#e6edf3", "attenue": "#9198a1", "barre": "#4493f8",
               "trait": "#30363d", "accent": "#3fb950", "alerte": "#f85149"},
}

def _fr(v: float, n: int = 1) -> str:
    """Décimale française — appliquée AU NOMBRE SEUL.

    Le 20/08/2026, un `.replace(".", ",")` posé sur la chaîne SVG entière a converti les
    COORDONNÉES : `x="317.4"` est devenu `x="317,4"`, valeur invalide, et les étiquettes de
    la figure V3 se sont retrouvées tronquées et déplacées. Le SVG restait bien formé, le
    navigateur l'affichait — il affichait autre chose. Trouvé par capture, pas par relecture.
    """
    return f"{v:.{n}f}".replace(".", ",")


POLICE = ("-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif")


def _entete(largeur: int, hauteur: int, titre: str) -> str:
    """Le `<title>` est lu par les lecteurs d'écran — c'est le texte alternatif interne."""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {largeur} {hauteur}" '
            f'width="{largeur}" height="{hauteur}" role="img" '
            f'font-family="{POLICE}">\n<title>{titre}</title>\n')


def barres(valeurs, titre, sous_titre, alt, c) -> str:
    """V1 — barres horizontales depuis zéro, triées, valeur écrite au bout.

    Barres et non camembert : les catégories sont nominales et c'est l'amplitude qu'on compare.
    Horizontales et non verticales : les libellés sont des mots, pas des dates.
    """
    L, marge_g, h_barre, pas = 720, 92, 30, 46
    H = 62 + pas * len(valeurs) + 16
    m = max(v for _, v in valeurs)
    piste = L - marge_g - 96
    s = [_entete(L, H, alt)]
    s.append(f'<text x="0" y="22" font-size="16" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="12.5" fill="{c["attenue"]}">{sous_titre}</text>')
    for i, (nom, v) in enumerate(sorted(valeurs, key=lambda x: -x[1])):
        y = 62 + i * pas
        larg = max(2, piste * v / m)
        s.append(f'<text x="{marge_g - 10}" y="{y + h_barre * 0.68:.0f}" font-size="13.5" '
                 f'text-anchor="end" fill="{c["encre"]}">{nom}</text>')
        s.append(f'<rect x="{marge_g}" y="{y}" width="{larg:.1f}" height="{h_barre}" rx="3" '
                 f'fill="{c["barre"]}"/>')
        # La valeur est ÉCRITE : la longueur seule ne se lit pas sur un petit écran.
        s.append(f'<text x="{marge_g + larg + 9:.0f}" y="{y + h_barre * 0.68:.0f}" font-size="13.5" '
                 f'font-weight="600" fill="{c["encre"]}">{_fr(v)}&#8239;%</text>')
    s.append("</svg>")
    return "\n".join(s)


def jalons(points, seuil, titre, sous_titre, alt, c) -> str:
    """V3 — trois points sur un axe 0-100 et un seuil annoté.

    Ni barres ni camembert : le message n'est pas l'amplitude, c'est la POSITION par rapport
    à une barre réglementaire. Trois formes distinctes portent la distinction, jamais la
    couleur seule.
    """
    L, H, marge_g, marge_d, y_axe = 720, 186, 96, 96, 104
    piste = L - marge_g - marge_d
    x = lambda v: marge_g + piste * v / 100.0
    s = [_entete(L, H, alt)]
    s.append(f'<text x="0" y="22" font-size="16" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="12.5" fill="{c["attenue"]}">{sous_titre}</text>')
    s.append(f'<line x1="{marge_g}" y1="{y_axe}" x2="{L - marge_d}" y2="{y_axe}" '
             f'stroke="{c["trait"]}" stroke-width="2"/>')
    # Le seuil d'abord, pour que les points passent au-dessus.
    xs = x(seuil)
    s.append(f'<line x1="{xs:.1f}" y1="{y_axe - 40}" x2="{xs:.1f}" y2="{y_axe + 22}" '
             f'stroke="{c["attenue"]}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    # Pas d'étiquette sur le trait : le sous-titre porte déjà « atteint à partir de 90 % ».
    # L'écrire deux fois ajoutait de l'encre sans information, et entrait en collision avec
    # l'étiquette du point voisin — le rapport données/encre tranche (famille G de l'audit).
    formes = ("cercle_vide", "losange", "cercle_plein")
    for i, (nom, v) in enumerate(points):
        xv, forme = x(v), formes[min(i, 2)]
        couleur = c["accent"] if v >= seuil else c["encre"]
        if forme == "cercle_vide":
            s.append(f'<circle cx="{xv:.1f}" cy="{y_axe}" r="8" fill="none" '
                     f'stroke="{c["alerte"]}" stroke-width="2.6"/>')
        elif forme == "losange":
            s.append(f'<path d="M {xv:.1f} {y_axe - 9} L {xv + 9:.1f} {y_axe} '
                     f'L {xv:.1f} {y_axe + 9} L {xv - 9:.1f} {y_axe} Z" fill="{c["encre"]}"/>')
        else:
            s.append(f'<circle cx="{xv:.1f}" cy="{y_axe}" r="8.5" fill="{couleur}"/>')
        haut = i % 2 == 0
        yv = y_axe - 20 if haut else y_axe + 34
        s.append(f'<text x="{xv:.1f}" y="{yv}" font-size="13.5" font-weight="600" '
                 f'text-anchor="middle" fill="{c["encre"]}">{_fr(v)}&#8239;%</text>')
        s.append(f'<text x="{xv:.1f}" y="{yv + (-17 if haut else 17)}" font-size="11.5" '
                 f'text-anchor="middle" fill="{c["attenue"]}">{nom}</text>')
    s.append("</svg>")
    return "\n".join(s)


FIGURES = {
    "v1_gain_polluants": dict(
        fn=barres,
        args=dict(
            valeurs=[("NO₂", 39.6), ("PM10", 20.2), ("O₃", 17.9), ("PM2,5", 11.8)],
            titre="Réduction de l'erreur, sans aucune observation du lieu corrigé",
            sous_titre="Échéance J+1 · station ET mois cachés · contre la prévision européenne brute",
            alt=("Réduction de l'erreur CAMS à J+1 sans observation locale : "
                 "NO₂ 39,6 %, PM10 20,2 %, ozone 17,9 % et PM2,5 11,8 %."))),
    "v3_fairmode_no2": dict(
        fn=jalons,
        args=dict(
            points=[("CAMS brut", 41.4), ("corrigé, sans observation", 87.9),
                    ("corrigé, aux stations", 96.2)],
            seuil=90,
            titre="NO₂ — part des stations qui satisfont le critère européen de qualité",
            sous_titre="Critère FAIRMODE à J+1 · atteint à partir de 90 %",
            alt=("Pour le NO₂, 41,4 % des stations satisfont le critère avec CAMS brut, "
                 "87,9 % après correction sans observation locale et 96,2 % avec l'historique "
                 "de station ; le seuil est à 90 %."))),
}


def main() -> int:
    SORTIE.mkdir(parents=True, exist_ok=True)
    PORTEFEUILLE.mkdir(parents=True, exist_ok=True)
    ecrits = []
    for nom, spec in FIGURES.items():
        for theme, couleurs in THEMES.items():
            svg = spec["fn"](c=couleurs, **spec["args"])
            f = SORTIE / f"{nom}_{theme}.svg"
            f.write_text(svg, encoding="utf-8")
            shutil.copy2(f, PORTEFEUILLE / f.name)
            ecrits.append(f)

    # Contrôle de sortie : l'artefact, jamais le code de retour (§ 0-C). Un SVG tronqué
    # s'ouvre sans erreur dans un navigateur — il n'affiche simplement rien.
    mauvais = [f.name for f in ecrits
               if not f.exists() or f.stat().st_size < 400
               or not f.read_text(encoding="utf-8").rstrip().endswith("</svg>")]
    if mauvais:
        print(f"ÉCHEC : SVG absents, trop courts ou non fermés — {mauvais}")
        return 1

    for f in ecrits:
        print(f"  {f.relative_to(RACINE)} · {f.stat().st_size} o")
    print(f"Écrit : {len(ecrits)} SVG · copiés dans {PORTEFEUILLE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
