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
            f'preserveAspectRatio="xMinYMin meet" role="img" '
            f'font-family="{POLICE}">\n<title>{titre}</title>\n')


def barres(valeurs, titre, sous_titre, alt, c) -> str:
    """V1 — barres horizontales depuis zéro, triées, valeur écrite au bout.

    Barres et non camembert : les catégories sont nominales et c'est l'amplitude qu'on compare.
    Horizontales et non verticales : les libellés sont des mots, pas des dates.
    """
    L, marge_g, h_barre, pas = 700, 104, 34, 52
    H = 74 + pas * len(valeurs) + 18
    m = max(v for _, v in valeurs)
    piste = L - marge_g - 96
    s = [_entete(L, H, alt)]
    s.append(f'<text x="0" y="22" font-size="20" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="15.5" fill="{c["attenue"]}">{sous_titre}</text>')
    for i, (nom, v) in enumerate(sorted(valeurs, key=lambda x: -x[1])):
        y = 74 + i * pas
        larg = max(2, piste * v / m)
        s.append(f'<text x="{marge_g - 10}" y="{y + h_barre * 0.68:.0f}" font-size="17" '
                 f'text-anchor="end" fill="{c["encre"]}">{nom}</text>')
        s.append(f'<rect x="{marge_g}" y="{y}" width="{larg:.1f}" height="{h_barre}" rx="3" '
                 f'fill="{c["barre"]}"/>')
        # La valeur est ÉCRITE : la longueur seule ne se lit pas sur un petit écran.
        s.append(f'<text x="{marge_g + larg + 9:.0f}" y="{y + h_barre * 0.68:.0f}" font-size="17" '
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
    s.append(f'<text x="0" y="22" font-size="20" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="15.5" fill="{c["attenue"]}">{sous_titre}</text>')
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
        s.append(f'<text x="{xv:.1f}" y="{yv}" font-size="17" font-weight="600" '
                 f'text-anchor="middle" fill="{c["encre"]}">{_fr(v)}&#8239;%</text>')
        s.append(f'<text x="{xv:.1f}" y="{yv + (-17 if haut else 17)}" font-size="14" '
                 f'text-anchor="middle" fill="{c["attenue"]}">{nom}</text>')
    s.append("</svg>")
    return "\n".join(s)


def avant_apres(paires, titre, sous_titre, alt, c) -> str:
    """V4 — deux états d'une même grandeur, reliés. Le message est le SAUT, pas les niveaux."""
    L, H = 720, 200
    s = [_entete(L, H, alt)]
    s.append(f'<text x="0" y="22" font-size="20" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="15.5" fill="{c["attenue"]}">{sous_titre}</text>')
    m = max(v for _, v in paires)
    base_y, haut = 168, 96
    for i, (nom, v) in enumerate(paires):
        x = 150 + i * 300
        h = max(4, haut * v / m)
        rempli = c["barre"] if i else c["attenue"]
        s.append(f'<rect x="{x - 52}" y="{base_y - h:.0f}" width="104" height="{h:.0f}" rx="3" fill="{rempli}"/>')
        s.append(f'<text x="{x}" y="{base_y - h - 12:.0f}" font-size="23" font-weight="700" '
                 f'text-anchor="middle" fill="{c["encre"]}">{v}</text>')
        s.append(f'<text x="{x}" y="{base_y + 20}" font-size="15.5" text-anchor="middle" '
                 f'fill="{c["attenue"]}">{nom}</text>')
    # La flèche porte le facteur : c'est lui le message, pas les deux hauteurs.
    f = paires[1][1] / max(paires[0][1], 1)
    s.append(f'<path d="M 214 108 L 388 108" stroke="{c["encre"]}" stroke-width="2" '
             f'marker-end="url(#p)"/>')
    s.append(f'<defs><marker id="p" markerWidth="9" markerHeight="9" refX="8" refY="4.5" '
             f'orient="auto"><path d="M0,0 L9,4.5 L0,9 z" fill="{c["encre"]}"/></marker></defs>')
    s.append(f'<text x="301" y="98" font-size="21" font-weight="700" text-anchor="middle" '
             f'fill="{c["encre"]}">×{_fr(f)}</text>')
    s.append("</svg>")
    return "\n".join(s)


def pente(series, titre, sous_titre, alt, c) -> str:
    """V5 — deux séries sur un axe d'échéance. La PENTE est le message, pas le niveau."""
    L, H, g, d, ht, hb = 780, 210, 60, 215, 66, 168
    s = [_entete(L, H, alt)]
    s.append(f'<text x="0" y="22" font-size="20" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="15.5" fill="{c["attenue"]}">{sous_titre}</text>')
    n = len(next(iter(series.values()))[1])
    xs = [g + (L - g - d) * i / (n - 1) for i in range(n)]
    toutes = [v for _, vs in series.values() for v in vs]
    lo, hi = min(toutes) * 0.92, max(toutes) * 1.04
    y = lambda v: hb - (hb - ht) * (v - lo) / (hi - lo)
    for i, (nom, (etiq, vs)) in enumerate(series.items()):
        col = c["barre"] if i == 0 else c["alerte"]
        pts = " ".join(f"{xs[k]:.0f},{y(v):.0f}" for k, v in enumerate(vs))
        s.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.6"/>')
        for k, v in enumerate(vs):
            s.append(f'<circle cx="{xs[k]:.0f}" cy="{y(v):.0f}" r="4" fill="{col}"/>')
        s.append(f'<text x="{xs[-1] + 12:.0f}" y="{y(vs[-1]) + 4:.0f}" font-size="13" '
                 f'font-weight="600" fill="{c["encre"]}">{nom} · {etiq}</text>')
        s.append(f'<text x="{xs[0] - 10:.0f}" y="{y(vs[0]) + 4:.0f}" font-size="15.5" '
                 f'text-anchor="end" fill="{c["attenue"]}">{_fr(vs[0])}&#8239;%</text>')
    for k, lab in enumerate(("J0", "J+1", "J+2", "J+3")[:n]):
        s.append(f'<text x="{xs[k]:.0f}" y="{hb + 24}" font-size="15" text-anchor="middle" '
                 f'fill="{c["attenue"]}">{lab}</text>')
    s.append("</svg>")
    return "\n".join(s)


def etapes(pile, titre, sous_titre, alt, c) -> str:
    """V6 — ce que chaque étage AJOUTE. Barres empilées horizontalement, apport annoté.

    Ni courbe ni camembert : la grandeur est un cumul ordonné, et c'est l'apport de chaque
    étage — pas le total — qui justifie sa présence dans la pile.
    """
    L, marge_g, h, pas = 760, 212, 30, 44
    H = 76 + pas * len(pile) + 16
    m = max(v for _, v in pile)
    piste = L - marge_g - 150
    s = [_entete(L, H, alt)]
    s.append(f'<text x="0" y="22" font-size="20" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="15.5" fill="{c["attenue"]}">{sous_titre}</text>')
    prec = 0.0
    for i, (nom, v) in enumerate(pile):
        y = 74 + i * pas
        larg, base = piste * v / m, piste * prec / m
        s.append(f'<rect x="{marge_g}" y="{y}" width="{base:.1f}" height="{h}" rx="2" '
                 f'fill="{c["trait"]}"/>')
        s.append(f'<rect x="{marge_g + base:.1f}" y="{y}" width="{larg - base:.1f}" height="{h}" '
                 f'rx="2" fill="{c["barre"]}"/>')
        s.append(f'<text x="{marge_g - 10}" y="{y + h * 0.7:.0f}" font-size="15.5" '
                 f'text-anchor="end" fill="{c["encre"]}">{nom}</text>')
        delta = f' <tspan fill="{c["attenue"]}">(+{_fr(v - prec)})</tspan>' if i else ""
        s.append(f'<text x="{marge_g + larg + 10:.0f}" y="{y + h * 0.7:.0f}" font-size="15.5" '
                 f'font-weight="600" fill="{c["encre"]}">{_fr(v)}&#8239;%{delta}</text>')
        prec = v
    s.append("</svg>")
    return "\n".join(s)


def barres_signees(valeurs, titre, sous_titre, alt, c, dec=2, zero="le meilleur modèle seul") -> str:
    """V8 — des valeurs qui peuvent être NÉGATIVES : l'axe zéro doit être visible."""
    L, marge_g, h, pas = 760, 246, 32, 48
    H = 76 + pas * len(valeurs) + 26
    lo = min(0.0, min(v for _, v in valeurs))
    hi = max(v for _, v in valeurs)
    piste = L - marge_g - 108
    x0 = marge_g + piste * (0 - lo) / (hi - lo)
    s = [_entete(L, H, alt)]
    s.append(f'<text x="0" y="22" font-size="20" font-weight="600" fill="{c["encre"]}">{titre}</text>')
    s.append(f'<text x="0" y="43" font-size="15.5" fill="{c["attenue"]}">{sous_titre}</text>')
    bas = 76 + pas * len(valeurs)
    s.append(f'<line x1="{x0:.1f}" y1="56" x2="{x0:.1f}" y2="{bas}" stroke="{c["attenue"]}" stroke-width="1.4"/>')
    for i, (nom, v) in enumerate(valeurs):
        y = 74 + i * pas
        xv = marge_g + piste * (v - lo) / (hi - lo)
        gauche, larg = (min(x0, xv), abs(xv - x0))
        col = c["barre"] if v >= 0 else c["alerte"]
        s.append(f'<rect x="{gauche:.1f}" y="{y}" width="{max(larg, 2):.1f}" height="{h}" rx="2" fill="{col}"/>')
        s.append(f'<text x="{marge_g - 10}" y="{y + h * 0.7:.0f}" font-size="15.5" '
                 f'text-anchor="end" fill="{c["encre"]}">{nom}</text>')
        signe = "+" if v >= 0 else "−"
        # Une valeur négative écrite à GAUCHE de sa barre percute le libellé de catégorie :
        # la barre part du bord de la piste, il n'y a plus de place. On l'écrit donc à droite
        # de l'axe zéro, où la ligne est libre — la couleur et le signe portent déjà le sens.
        xt = (xv + 9) if v >= 0 else (x0 + 9)
        anc = "start"
        s.append(f'<text x="{xt:.1f}" y="{y + h * 0.7:.0f}" font-size="15.5" font-weight="600" '
                 f'text-anchor="{anc}" fill="{c["encre"]}">{signe}{_fr(abs(v), dec)}</text>')
    s.append(f'<text x="{x0:.1f}" y="{bas + 18}" font-size="14" text-anchor="middle" '
             f'fill="{c["attenue"]}">0 — {zero}</text>')
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
    "v4_seuil_2030": dict(
        fn=avant_apres,
        args=dict(
            paires=[("aujourd'hui", 6), ("en 2030", 109)],
            titre="Stations en dépassement — à pollution inchangée",
            sous_titre="Moyennes annuelles 2025 · 408 stations évaluées · seul le seuil réglementaire change",
            alt=("Le nombre de stations en dépassement passe de 6 aujourd'hui à 109 en 2030, "
                 "soit un facteur 18,2, sans qu'aucune émission n'ait changé."))),
    "v5_echeances": dict(
        fn=pente,
        args=dict(
            series={"NO₂": ("stable, 0,38 pt", [37.1, 37.1, 36.9, 36.7]),
                    "O₃": ("se dégrade, 2,25 pt", [9.3, 9.1, 8.5, 7.0])},
            titre="Tenue du gain avec l'échéance — l'affirmation du dossier, réfutée sur l'ozone",
            sous_titre="Réduction d'erreur, de J0 à J+3 · la dernière échéance que CAMS Europe produise",
            alt=("De J0 à J+3, le gain sur le NO₂ reste stable de 37,1 % à 36,7 % (0,38 point), "
                 "tandis que celui sur l'ozone tombe de 9,3 % à 7,0 % (2,25 points)."))),
    "v6_pile_no2": dict(
        fn=etapes,
        args=dict(
            # ⚠️ SEPT étages, pas cinq. La version du 20/08 en montrait cinq : « membres » et
            # « feux » avaient été retirés parce qu'ils ne sont plus dans la pile publiée — mais
            # leurs valeurs CUMULÉES étaient restées, si bien que GEOS-CF affichait un apport de
            # +3,1 quand le sien vaut +2,33. Retirer une ligne d'un cumul sans recalculer les
            # suivantes attribue à l'étage d'après ce que les précédents avaient gagné.
            pile=[("base", 26.6), ("+ typologie de station", 35.6), ("+ membres", 36.1),
                  ("+ feux", 36.4), ("+ GEOS-CF", 38.7), ("+ tendance récente", 38.9),
                  ("+ spéciation", 40.2)],
            titre="NO₂ — ce que chaque étage ajoute",
            sous_titre="Double aveugle, J+1 · ordre déclaré avant la mesure · membres et feux ont depuis été retirés de la pile",
            alt=("Sur le NO₂, la pile passe de 26,6 % pour la base à 40,2 % avec la spéciation ; "
                 "la typologie de station apporte le plus gros saut, +9,0 points, GEOS-CF +2,3 "
                 "et la spéciation +1,3."))),
    "v8_routage_dimension": dict(
        fn=barres_signees,
        args=dict(
            valeurs=[("tout le multivarié (d ≥ 2)", -0.01), ("multivarié réel (d ≥ 8)", 0.03),
                     ("haute dimension (d ≥ 20)", 0.07)],
            titre="Le routage ne devient utile qu'en dimension suffisante",
            sous_titre="Gain VUS-PR du routage sur le meilleur modèle seul · protocole LODO",
            alt=("Le routage perd 0,01 sur l'ensemble du multivarié, gagne 0,03 à partir de huit "
                 "variables et 0,07 au-delà de vingt."))),
    "v7_routeur_tabulaire": dict(
        # Des barres partant de zéro sur des valeurs entre 69,8 et 78,7 rendent l'écart
        # invisible — or l'écart EST le message. Tronquer l'axe l'exagérerait. La forme juste
        # est donc de tracer la DIFFÉRENCE elle-même, contre le meilleur détecteur unique.
        fn=barres_signees,
        args=dict(
            # ⚠️ Tous les écarts viennent du MÊME fichier, `router_lodosrc_actions_strict.csv`.
            # La version précédente opposait le routeur strict (72,79) à un « meilleur détecteur
            # unique » de 69,81 qui vient d'un AUTRE protocole — le LODO standard. Deux régimes
            # dans une même figure, sans que rien ne le dise : le défaut exact que ce dossier
            # traque. Ici, la référence est l'ensemble fixe, mesuré sous le même protocole.
            # ⚠️ DEUXIÈME correction de la même figure, et le défaut était le même déguisé.
            # La version du 21/08 matin affichait +5,92 pour le plafond — mais 5,92 vaut
            # oracle − ROUTEUR, quand les deux autres barres valent « − ensemble fixe ». Trois
            # barres, deux références, un seul zéro annoncé. Depuis le zéro affiché (71,31), le
            # plafond vaut +7,40. Corriger un mélange de protocoles en laissant un mélange de
            # RÉFÉRENCES ne corrige rien : c'est le même défaut, un cran plus bas.
            valeurs=[("plafond — sélection parfaite", 7.40), ("routeur source-strict", 1.48),
                     ("spécialisation par domaine", 1.00)],
            dec=2, zero="l'ensemble fixe de 18 détecteurs (71,31)",
            titre="Choisir le détecteur rapporte — modestement, et c'est mesuré",
            sous_titre="Points d'AUROC · 502 jeux · LODO groupé par source · un seul protocole, un seul fichier",
            alt=("Contre l'ensemble fixe de 18 détecteurs, le routeur source-strict gagne 1,48 point "
                 "d'AUROC, la spécialisation par domaine 1,00, et la sélection parfaite 7,40."))),
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
