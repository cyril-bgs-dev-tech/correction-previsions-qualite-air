#!/usr/bin/env python3
"""L'anatomie de la correction — une section par source d'information.

Pourquoi cette page
-------------------
Le dossier explique les **résultats** ; il n'explique jamais les **pièces**. Un lecteur qui
veut savoir *de quoi la correction est faite* doit aujourd'hui reconstituer la réponse à
partir de dix mesures éparses.

Cette page prend le problème dans l'autre sens : une section par source d'information, dans
**l'ordre où elle entre** dans la correction, avec pour chacune ce qu'elle est, pourquoi elle
devrait marcher, et **ce qu'elle vaut réellement** — y compris quand la réponse est « rien ».

La dernière section porte la carte d'importance temporelle : le poids de chaque source, mois
par mois, mesuré par permutation.

Usage : python3 scripts/anatomie_methode.py
Sortie : reports/figures/anatomie_methode.html
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from heatmap_annuelle import ARRETS  # noqa: E402

# Les sources, dans l'ordre où l'information entre dans la correction. Le numéro n'est pas
# décoratif : il encode cet ordre, qui est réel.
COMPOSANTS = [
    {
        "cle": "prévision CAMS",
        "famille": "socle",
        "titre": "La prévision brute",
        "these": "On ne remplace pas le modèle de chimie-transport : on apprend son erreur.",
        "quoi": "La sortie de CAMS Europe — un ensemble de neuf à onze modèles de "
                "chimie-transport, sur une grille de 0,1°, soit environ huit kilomètres. "
                "C'est la valeur à corriger, et l'ancrage de tout le reste.",
        "pourquoi": "La cible apprise est le <b>résidu</b> <code>observation − CAMS</code>, "
                    "jamais la concentration elle-même. Une première version apprenait "
                    "l'observation : elle gagnait 13 % de RMSE et détectait <b>zéro</b> "
                    "dépassement sur quinze. Ancrer la prédiction à la physique préserve la "
                    "queue de distribution — là où se jouent les épisodes.",
        "vaut": "référence",
        "detail": "RMSE 12,08 µg/m³ sur le maximum journalier 8 h de l'ozone",
    },
    {
        "cle": "calendrier",
        "famille": "temps",
        "titre": "Le calendrier",
        "these": "La variable la plus utile de toutes — et la plus suspecte.",
        "quoi": "Heure, jour de l'année, jour de semaine, jours fériés, le tout projeté sur "
                "le cercle pour que le 31 décembre soit voisin du 1<sup>er</sup> janvier.",
        "pourquoi": "L'erreur de CAMS est saisonnière : la photochimie estivale, les profils "
                    "d'émission hebdomadaires et le chauffage hivernal ne sont pas également "
                    "bien représentés. Le calendrier les résume sans les modéliser.",
        "vaut": "+9,1 %",
        "detail": "coût de son retrait sur l'ozone — la plus forte de toutes les familles",
        "reserve": "C'est aussi ce qui rend la <b>généralisation temporelle</b> fragile : le "
                   "modèle apprend en partie <em>quelle saison</em>, ce qui ne se transporte "
                   "pas à un régime inconnu.",
    },
    {
        "cle": "relief",
        "famille": "lieu",
        "titre": "Le relief",
        "these": "Ce qu'une maille de huit kilomètres ne peut pas voir.",
        "quoi": "Neuf descripteurs : position topographique à trois échelles, pente, "
                "rugosité, encaissement, profondeur de vallée, altitude — extraits du modèle "
                "de terrain Copernicus GLO-30 lu par fenêtre, sans stocker un octet.",
        "pourquoi": "Une station de fond de vallée et une station de crête reçoivent la "
                    "<b>même</b> prévision et ne mesurent pas la même chose. L'inversion "
                    "nocturne, le drainage d'air froid et l'exposition au vent sont "
                    "strictement sous-maille.",
        "vaut": "+4,0 %",
        "detail": "coût de son retrait",
    },
    {
        "cle": "trafic et population",
        "famille": "lieu",
        "titre": "Le réseau routier hiérarchisé",
        "these": "Le plus gros gain unitaire du projet, et il vient d'un détail.",
        "quoi": "Densité de voirie pondérée par <b>l'importance</b> de chaque tronçon dans la "
                "BD TOPO — une autoroute ne compte pas comme une voie communale — plus la "
                "population résidente.",
        "pourquoi": "Le NO₂ est dominé par des sources linéaires très locales. Sur les "
                    "stations trafic, CAMS a un R² <b>négatif</b> : il fait pire que prédire "
                    "la moyenne. C'est là que la descente d'échelle a le plus à rendre.",
        "vaut": "+13,0 %",
        "detail": "sur le NO₂, contre une pondération par simple longueur · IC95 "
                  "[+10,4 ; +15,5], 100 % des tirages positifs",
        "reserve": "La <b>population</b> n'ajoute rien de mesurable (+0,3 point, intervalles "
                   "chevauchants). Tout l'apport vient de la hiérarchie routière.",
    },
    {
        "cle": "paysage",
        "famille": "lieu",
        "titre": "Le paysage et les essences",
        "these": "Un résultat négatif, et il enseigne plus que les positifs.",
        "quoi": "Vingt-huit variables : essences forestières — chênes, hêtres, résineux — "
                "distances et densités à sept rayons, de 100 mètres à 30 kilomètres.",
        "pourquoi": "Les chênes émettent de l'isoprène, précurseur d'ozone. L'hypothèse était "
                    "que la composition forestière expliquerait une part du biais estival.",
        "vaut": "−1,9 %",
        "detail": "les <b>retirer améliore</b> le modèle",
        "reserve": "CAMS <b>modélise déjà</b> les émissions biogéniques. Re-fournir la forêt "
                   "n'ajoute aucune information, seulement vingt-huit variables corrélées sur "
                   "lesquelles surajuster. C'est ce résultat qui a donné la règle du projet : "
                   "<em>une correction n'ajoute que là où le modèle amont est aveugle à "
                   "lui-même</em>.",
    },
    {
        "cle": "observation à J−2",
        "famille": "temps réel",
        "titre": "L'observation récente",
        "these": "Le plus fort levier mesuré — et il était exclu par erreur de raisonnement.",
        "quoi": "L'observation et l'erreur de CAMS à J−2, leurs moyennes sur trois et sept "
                "jours, l'écart-type de l'erreur, et une <b>fraîcheur</b> en jours : une "
                "station en panne depuis dix jours ne doit pas voir sa dernière mesure "
                "traitée comme datant d'avant-hier.",
        "pourquoi": "Le biais de CAMS à une station est persistant. La mesure d'avant-hier "
                    "le révèle sans rien coûter — et le produit officiel de Copernicus s'en "
                    "sert déjà, sa documentation le dit.",
        "vaut": "+21,9 %",
        "detail": "sur le NO₂ · +8,9 % sur l'ozone · +8,5 % sur les PM2,5 · queue meilleure "
                  "partout",
        "reserve": "Le projet l'excluait <b>au même titre</b> que la météo de réanalyse. Ce "
                   "n'est pas le même argument : une réanalyse décrit le présent depuis le "
                   "futur, la mesure d'avant-hier est publiée. Une prudence appliquée par "
                   "analogie plutôt que par examen a coûté ce levier pendant tout le projet. "
                   "Elle crée aussi <b>deux périmètres</b> : cette variable n'existe qu'aux "
                   "stations instrumentées.",
    },
    {
        "cle": "membres d'ensemble",
        "famille": "incertitude",
        "titre": "Les six modèles de l'ensemble",
        "these": "Nuls pour prédire, précieux pour savoir quand se méfier.",
        "quoi": "Les valeurs individuelles de six modèles — CHIMERE, EMEP, MOCAGE, SILAM, "
                "LOTOS-EUROS, MATCH — au lieu de leur seule médiane. Leur désaccord vaut "
                "11 µg/m³ d'écart-type médian sur l'ozone.",
        "pourquoi": "Le désaccord entre modèles est une estimation d'incertitude <b>native</b>, "
                    "disponible avant toute observation. Le projet lui avait fabriqué deux "
                    "substituts — l'écart entre échéances, un détecteur d'anomalies — alors "
                    "que la grandeur existait en amont, et n'était simplement pas téléchargée.",
        "vaut": "×6,6",
        "detail": "gain de la correction, du décile où les modèles s'accordent à celui où ils "
                  "divergent",
        "reserve": "Comme <b>prédicteur</b> de la concentration, l'apport est nul sur l'ozone "
                   "et faible ailleurs (+1,9 % sur NO₂, +2,9 % sur PM2,5). C'est en "
                   "<b>détection</b> qu'ils comptent, et en indicateur de confiance.",
    },
    {
        "cle": "exposition aux feux",
        "famille": "événement",
        "titre": "L'exposition aux feux",
        "these": "Réelle sur les particules, illusoire sur les deux autres.",
        "quoi": "La puissance radiative des feux (GFAS, 0,1°, quotidien) vue de chaque "
                "station : décroissance exponentielle à trois échelles — 50, 200 et "
                "500 kilomètres — et conditionnement au <b>secteur au vent</b>.",
        "pourquoi": "Un panache de combustion voyage sur des centaines de kilomètres et CAMS "
                    "l'ingère avec une latence d'assimilation. Un feu allumé la veille ne peut "
                    "pas figurer dans une prévision émise l'avant-veille.",
        "vaut": "+3,0 %",
        "detail": "sur les PM2,5 · le gain se concentre là où CAMS <b>sous-estime</b>, "
                  "conforme au mécanisme",
        "reserve": "Sur l'ozone le gain est <b>symétrique</b> et sur le NO₂ <b>inversé</b> — "
                   "près de trois fois plus fort là où CAMS sur-estime. Ces variables y "
                   "encodent une situation synoptique (chaud, sec, stagnant) que les feux "
                   "accompagnent sans la causer. <b>Ne revendiquer un effet des feux que sur "
                   "les particules.</b>",
    },
]

# **Chaque chiffre nomme son endpoint.** La version précédente annonçait « +23,4 % sur la
# grandeur qui déclenche les procédures » : c'était faux. Le maximum glissant 8 h à 120 µg/m³
# est la **valeur cible européenne** ; la procédure française se déclenche à 180 µg/m³ en
# maximum horaire, seuil auquel ni CAMS ni cette correction ne détectent quoi que ce soit
# d'exploitable (32 dépassements sur 60 400 jours-station, 3 et 2 détectés). Un chiffre de
# détection sans son endpoint est trompeur, même quand il est juste.
MESURES_CLES = [
    ("3,5×", "plus de dépassements détectés", "à budget de fausses alertes égal, hors "
     "fenêtre d'apprentissage — à la <b>valeur cible européenne</b>, 120 µg/m³ en max 8 h"),
    ("97 %", "de précision", "contre 69 % pour le produit officiel de Copernicus, sur 2025"),
    ("+23,4 %", "de RMSE en moins", "sur le maximum glissant 8 h de l'ozone, France 2024, "
     "stations exclues"),
    ("−11,6 → −0,5", "µg/m³ de biais", "NO₂ sur 150 stations urbaines de fond, aux "
     "conventions d'un rapport AASQA"),
    # Les PM10 sont le polluant qui déclenche réellement — 40 des 52 vigilances déclarées en
    # Occitanie. Leur absence de cette page laissait le lecteur croire que la méthode n'avait
    # pas été mesurée sur lui. Comparaison à CAMS brut seul, sur 191 stations et 19 mois
    # (2024-01 → 2026-08) : le MOS officiel de Copernicus n'existe pas pour ce polluant, et
    # la fenêtre n'est donc pas celle des trois autres (VERITE_DOSSIER § 10 bis).
    ("+33,3 %", "de RMSE en moins", "PM10 en moyenne journalière, contre CAMS brut seul, "
     "191 stations sur 2024-01 → 2026-08 — le polluant qui porte <b>40 des 52 vigilances</b> "
     "réellement déclarées en Occitanie"),
]


def teinte(fraction: float) -> str:
    positions = np.array([a for a, _ in ARRETS])
    valeurs = np.array([c for _, c in ARRETS], dtype="float64")
    x = float(np.clip(fraction, 0.0, 1.0)) * positions[-1]
    r, v, b = (np.interp(x, positions, valeurs[:, canal]) for canal in range(3))
    return f"#{int(r):02x}{int(v):02x}{int(b):02x}"


def teinte_erreur(fraction: float) -> str:
    """Rampe **distincte** pour la performance : de l'encre à l'ambre du thème.

    Ne pas réutiliser la rampe multicolore de l'importance. Les deux bandes portent des
    grandeurs opposées — un rouge d'importance est une bonne nouvelle, un rouge d'erreur une
    mauvaise — et une teinte partagée ferait lire l'une pour l'autre.
    """
    f = float(np.clip(fraction, 0.0, 1.0))
    depart, arrivee = (26, 34, 44), (255, 157, 61)
    r, v, b = (int(d + (a - d) * f) for d, a in zip(depart, arrivee))
    return f"#{r:02x}{v:02x}{b:02x}"


def bande_performance(mois: list, pas_x: int, pas_y: int, marge_g: int,
                      marge_h: int) -> tuple[str, float, float]:
    """Trois lignes de référence — CAMS brut, produit officiel, notre correction."""
    chemin = RACINE / "reports/performance_mensuelle_O3.csv"
    if not chemin.exists():
        return "", 0.0, 0.0
    p = pd.read_csv(chemin)
    ordre = ["CAMS brut", "MOS officiel Copernicus",
             "notre correction · partout", "notre correction · aux stations"]
    ordre = [o for o in ordre if o in set(p["produit"])]
    pivot = p.pivot_table(index="produit", columns="mois", values="rmse")
    valeurs = pivot.to_numpy()
    bas, haut = float(np.nanmin(valeurs)), float(np.nanmax(valeurs))

    parties = []
    for iy, produit in enumerate(ordre):
        y = marge_h + iy * pas_y
        gras = ' font-weight="600"' if produit.startswith("notre") else ""
        parties.append(
            f'<text x="{marge_g - 10}" y="{y + pas_y / 2 + 3.5}" font-size="10.5" '
            f'text-anchor="end" fill="var(--texte)"{gras}>{produit}</text>')
        for ix, m in enumerate(mois):
            v = pivot.get(m, {}).get(produit, np.nan) if m in pivot.columns else np.nan
            x = marge_g + ix * pas_x
            couleur = ("var(--panneau-2)" if not np.isfinite(v)
                       else teinte_erreur((v - bas) / max(haut - bas, 1e-9)))
            # Les mois de 2023 sont vides parce que l'archive du produit officiel commence au
            # 18/01/2024 : la comparaison se fait sur les lignes communes, jamais autrement.
            libelle = ("hors archive du produit officiel" if not np.isfinite(v)
                       else f"RMSE {v:.2f} µg/m³")
            parties.append(
                f'<rect x="{x}" y="{y}" width="{pas_x - 3}" height="{pas_y - 3}" rx="3" '
                f'fill="{couleur}"><title>{produit} · {m} — {libelle}</title></rect>')
    return "".join(parties), bas, haut


def carte_importance() -> str:
    """La carte d'importance temporelle, si la mesure existe."""
    chemin = RACINE / "reports/importance_temporelle_O3.csv"
    if not chemin.exists():
        return ('<p class="absent">La mesure d\'importance temporelle n\'a pas encore été '
                'produite — lancer <code>scripts/importance_temporelle.py</code>.</p>')
    t = pd.read_csv(chemin)
    mois = sorted(t["mois"].unique())
    blocs = [c["cle"] for c in COMPOSANTS if c["cle"] in set(t["bloc"])]
    maximum = float(t["importance"].max())

    pas_x, pas_y, marge_g, marge_h = 26, 26, 190, 30
    # La bande de référence occupe trois lignes en haut, puis un intervalle de séparation :
    # les deux grandeurs ne se lisent pas ensemble et ne doivent pas se toucher.
    perf, perf_bas, perf_haut = bande_performance(mois, pas_x, pas_y, marge_g, marge_h)
    n_perf = 4 if perf else 0
    decalage = marge_h + n_perf * pas_y + (26 if perf else 0)
    largeur = marge_g + len(mois) * pas_x + 10
    hauteur = decalage + len(blocs) * pas_y + 26
    pivot = t.pivot_table(index="bloc", columns="mois", values="importance")

    cellules, etiquettes = [], []
    if perf:
        etiquettes.append(
            f'<text x="{marge_g - 10}" y="{marge_h - 11}" font-size="9" text-anchor="end" '
            f'fill="var(--accent)" letter-spacing="1.4">ERREUR DU PRODUIT</text>')
        etiquettes.append(
            f'<text x="{marge_g - 10}" y="{decalage - 11}" font-size="9" text-anchor="end" '
            f'fill="var(--texte-doux)" letter-spacing="1.4">POIDS DE LA SOURCE</text>')
    for iy, bloc in enumerate(blocs):
        y = decalage + iy * pas_y
        etiquettes.append(
            f'<text x="{marge_g - 10}" y="{y + pas_y / 2 + 3.5}" font-size="10.5" '
            f'text-anchor="end" fill="var(--texte-doux)">{bloc}</text>')
        for ix, m in enumerate(mois):
            v = pivot.get(m, {}).get(bloc, np.nan) if m in pivot.columns else np.nan
            x = marge_g + ix * pas_x
            couleur = "#151b24" if not np.isfinite(v) else (
                "#151b24" if v <= 0 else teinte(v / maximum))
            titre = ("hors couverture" if not np.isfinite(v)
                     else f"{v:+.3f} µg/m³ de RMSE si permuté")
            cellules.append(
                f'<rect x="{x}" y="{y}" width="{pas_x - 3}" height="{pas_y - 3}" rx="3" '
                f'fill="{couleur}"><title>{bloc} · {m} — {titre}</title></rect>')

    for ix, m in enumerate(mois):
        if m.endswith(("-01", "-04", "-07", "-10")):
            x = marge_g + ix * pas_x
            etiquettes.append(f'<text x="{x + pas_x / 2}" y="{marge_h - 9}" font-size="9.5" '
                              f'text-anchor="middle" fill="var(--texte-doux)">{m[2:]}</text>')

    return (f'<svg viewBox="0 0 {largeur} {hauteur}" role="img" '
            f'aria-label="Erreur des trois produits et poids de chaque source, mois par mois">'
            + perf + "".join(cellules) + "".join(etiquettes) + "</svg>")


def section(n: int, c: dict) -> str:
    reserve = (f'<div class="reserve"><span class="etiq">Ce que ça ne dit pas</span>'
               f'<p>{c["reserve"]}</p></div>' if c.get("reserve") else "")
    return f"""<section id="c{n}">
  <div class="exergue"><span class="num">{n:02d}</span><span class="fam">{c['famille']}</span></div>
  <h2>{c['titre']}</h2>
  <p class="these">{c['these']}</p>
  <div class="grille">
    <div><span class="etiq">Ce que c'est</span><p>{c['quoi']}</p></div>
    <div><span class="etiq">Pourquoi ça devrait marcher</span><p>{c['pourquoi']}</p></div>
  </div>
  <div class="mesure"><div class="val">{c['vaut']}</div><p>{c['detail']}</p></div>
  {reserve}
</section>"""


def main() -> int:
    nav = "".join(f'<a href="#c{i}"><span>{i:02d}</span>{c["titre"]}</a>'
                  for i, c in enumerate(COMPOSANTS, start=1))
    nav += f'<a href="#carte" class="fin"><span>{len(COMPOSANTS) + 1:02d}</span>'\
           f'Quand chaque source compte</a>'
    sections = "".join(section(i, c) for i, c in enumerate(COMPOSANTS, start=1))
    cles = "".join(f'<div class="cle"><div class="v">{v}</div>'
                   f'<div class="l">{l}</div><div class="d">{d}</div></div>'
                   for v, l, d in MESURES_CLES)
    rampe = "".join(f'<span style="background:{teinte(f)}"></span>'
                    for f in np.linspace(0, 1, 50))
    rampe_err = "".join(f'<span style="background:{teinte_erreur(f)}"></span>'
                        for f in np.linspace(0, 1, 50))
    perf_csv = RACINE / "reports/performance_mensuelle_O3.csv"
    if perf_csv.exists():
        _p = pd.read_csv(perf_csv)
        bornes_err = (float(_p["rmse"].min()), float(_p["rmse"].max()))
    else:
        bornes_err = (0.0, 0.0)

    html = f"""<title>Anatomie d'une correction de prévision de qualité de l'air</title>
<style>
:root{{
  --encre:#0a0e14; --panneau:#121821; --panneau-2:#151b24;
  --texte:#e8eef5; --texte-doux:#8fa3b8; --liseré:#26313f;
  --accent:#ff9d3d; --accent-doux:rgba(255,157,61,.13);
  color-scheme:dark;
}}
@media (prefers-color-scheme:light){{:root:where(:not([data-theme="dark"])){{
  --encre:#fbfcfd; --panneau:#fff; --panneau-2:#f2f5f8;
  --texte:#0f1620; --texte-doux:#5a6b7d; --liseré:#dde4ec;
  --accent:#c56a00; --accent-doux:rgba(197,106,0,.09);
  color-scheme:light;
}}}}
:root[data-theme="light"]{{
  --encre:#fbfcfd; --panneau:#fff; --panneau-2:#f2f5f8;
  --texte:#0f1620; --texte-doux:#5a6b7d; --liseré:#dde4ec;
  --accent:#c56a00; --accent-doux:rgba(197,106,0,.09);
  color-scheme:light;
}}
:root[data-theme="dark"]{{
  --encre:#0a0e14; --panneau:#121821; --panneau-2:#151b24;
  --texte:#e8eef5; --texte-doux:#8fa3b8; --liseré:#26313f;
  --accent:#ff9d3d; --accent-doux:rgba(255,157,61,.13);
  color-scheme:dark;
}}
*{{box-sizing:border-box}}
body,.doc{{background:var(--encre);color:var(--texte);margin:0;
  font:16px/1.68 system-ui,-apple-system,"Segoe UI",sans-serif;
  -webkit-font-smoothing:antialiased}}
.mono{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace}}
.enveloppe{{display:grid;grid-template-columns:238px minmax(0,1fr);gap:0;
  max-width:1220px;margin:0 auto}}
nav{{position:sticky;top:0;align-self:start;max-height:100vh;overflow-y:auto;
  padding:38px 20px 38px 24px;border-right:1px solid var(--liseré)}}
nav .marque{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.68rem;
  letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-bottom:18px}}
nav a{{display:flex;gap:10px;align-items:baseline;padding:7px 9px;margin:0 -9px;
  border-radius:6px;color:var(--texte-doux);text-decoration:none;font-size:.855rem;
  line-height:1.35;transition:background .12s,color .12s}}
nav a span{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.72rem;
  color:var(--accent);flex:none;opacity:.75}}
nav a:hover,nav a:focus-visible{{background:var(--panneau);color:var(--texte);outline:none}}
nav a.fin{{margin-top:8px;border-top:1px solid var(--liseré);padding-top:13px}}
main{{padding:38px clamp(18px,3.4vw,44px) 80px;min-width:0}}
header h1{{font-size:clamp(1.75rem,3.9vw,2.65rem);line-height:1.12;letter-spacing:-.032em;
  margin:0 0 .32em;text-wrap:balance}}
header .chapeau{{color:var(--texte-doux);font-size:1.045rem;max-width:60ch;margin:0}}
.cles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(178px,1fr));gap:13px;
  margin:34px 0 8px}}
.cle{{background:var(--panneau);border:1px solid var(--liseré);border-radius:11px;
  padding:17px 18px}}
.cle .v{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:1.72rem;
  font-weight:600;letter-spacing:-.03em;color:var(--accent);line-height:1}}
.cle .l{{font-weight:600;margin-top:5px;font-size:.93rem}}
.cle .d{{color:var(--texte-doux);font-size:.815rem;margin-top:3px;line-height:1.5}}
section{{padding:44px 0 8px;border-top:1px solid var(--liseré);margin-top:34px;
  scroll-margin-top:20px}}
.exergue{{display:flex;align-items:center;gap:11px;
  font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.7rem;
  letter-spacing:.13em;text-transform:uppercase;margin-bottom:11px}}
.exergue .num{{color:var(--accent);font-weight:600}}
.exergue .fam{{color:var(--texte-doux);border:1px solid var(--liseré);border-radius:99px;
  padding:2.5px 9px}}
h2{{font-size:clamp(1.28rem,2.5vw,1.66rem);letter-spacing:-.022em;margin:0 0 .2em;
  line-height:1.22;text-wrap:balance}}
.these{{color:var(--accent);font-size:1.03rem;margin:0 0 22px;max-width:62ch;
  font-weight:500}}
.grille{{display:grid;grid-template-columns:repeat(auto-fit,minmax(268px,1fr));gap:22px;
  margin-bottom:20px}}
.etiq{{display:block;font-family:ui-monospace,SFMono-Regular,Menlo,monospace;
  font-size:.665rem;letter-spacing:.12em;text-transform:uppercase;
  color:var(--texte-doux);margin-bottom:5px}}
.grille p,.reserve p{{margin:0;font-size:.945rem;line-height:1.66}}
.mesure{{display:flex;align-items:baseline;gap:16px;background:var(--accent-doux);
  border:1px solid var(--liseré);border-left:2px solid var(--accent);
  border-radius:10px;padding:15px 18px;margin:22px 0}}
.mesure .val{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:1.5rem;
  font-weight:600;color:var(--accent);letter-spacing:-.03em;flex:none;line-height:1.1}}
.mesure p{{margin:0;font-size:.895rem;color:var(--texte-doux);line-height:1.55}}
.reserve{{background:var(--panneau);border:1px solid var(--liseré);border-radius:10px;
  padding:15px 18px;margin-top:16px}}
.carte{{background:var(--panneau);border:1px solid var(--liseré);border-radius:11px;
  padding:19px;margin:22px 0;overflow-x:auto}}
.carte svg{{display:block;width:100%;height:auto;min-width:660px}}
.legende{{display:flex;align-items:center;gap:10px;font-size:.79rem;
  color:var(--texte-doux);margin-top:14px;flex-wrap:wrap}}
.rampe{{display:flex;height:10px;width:168px;border-radius:3px;overflow:hidden}}
.rampe span{{flex:1}}
.absent{{color:var(--texte-doux);font-style:italic}}
.avert{{border-left:2px solid var(--liseré);padding-left:14px;color:var(--texte-doux);font-size:.9rem}}
main ul{{color:var(--texte);font-size:.945rem;line-height:1.66;padding-left:20px;max-width:66ch}}
main li{{margin-bottom:6px}}
code{{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.87em;
  background:var(--panneau-2);padding:1.5px 5px;border-radius:4px}}
footer{{color:var(--texte-doux);font-size:.79rem;border-top:1px solid var(--liseré);
  margin-top:44px;padding-top:19px;line-height:1.62}}
p,li{{max-width:66ch}}
@media (max-width:820px){{
  .enveloppe{{grid-template-columns:1fr}}
  nav{{position:static;max-height:none;border-right:0;border-bottom:1px solid var(--liseré);
    display:flex;flex-wrap:wrap;gap:3px;padding:16px}}
  nav .marque{{width:100%;margin-bottom:9px}}
  nav a{{padding:5px 9px;font-size:.79rem}}
}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
<div class="doc"><div class="enveloppe">
<nav>
  <div class="marque">Anatomie</div>
  {nav}
</nav>
<main>
<header>
  <h1>De quoi une correction de prévision est&nbsp;faite</h1>
  <p class="chapeau">Huit sources d'information, dans l'ordre où elles entrent. Pour chacune :
  ce qu'elle est, pourquoi elle devrait marcher, et <b>ce qu'elle vaut réellement</b> —
  y compris quand la réponse est « rien ».</p>
  <div class="cles">{cles}</div>
</header>
{sections}
<section id="carte">
  <div class="exergue"><span class="num">{len(COMPOSANTS) + 1:02d}</span>
    <span class="fam">synthèse</span></div>
  <h2>Quand chaque source compte</h2>
  <p class="these">Un service ne demande pas si les feux comptent en général — il demande
  s'ils comptent aujourd'hui.</p>
  <p>La carte se lit en deux bandes, et l'ordre importe.</p>
  <p><b>En haut, le résultat.</b> L'erreur mensuelle de <b>quatre</b> produits, sur la même
  grandeur et sur les <b>mêmes lignes</b>. Trois lectures s'y voient sans commentaire :</p>
  <ul>
    <li>le produit officiel <b>dégrade</b> la prévision brute <b>huit mois sur douze</b> — il
      ne gagne qu'en fin d'automne et en janvier, soit précisément hors saison
      photochimique ;</li>
    <li>nos deux lignes restent les plus sombres <b>tous les mois</b> ;</li>
    <li>l'écart entre elles est le prix du <b>périmètre</b>. « Partout » n'utilise pas
      l'observation de la veille : il tourne y compris là où aucune station ne mesure. « Aux
      stations » l'utilise, et ne vaut donc qu'au réseau instrumenté. Sur l'année :
      12,08 · 11,87 · <b>8,05</b> · <b>7,21 µg/m³</b>.</li>
  </ul>
  <p class="avert">Ces quatre RMSE servent à comparer les produits <b>entre eux</b>, sur des
  lignes identiques et les mêmes plis. Ce ne sont pas les chiffres du dossier : celui-ci suit
  un protocole gelé sur la seule année 2024 et annonce <b>+23,4 %</b> pour la version
  « partout ». Un écart de protocole n'est pas un écart de résultat — mais il ne se
  reporte pas d'une page à l'autre.</p>
  <p><b>En bas, l'explication.</b> Importance par <b>permutation</b>, mois par mois : on
  mélange les valeurs d'une source <em>à l'intérieur du mois</em> et l'on mesure de combien
  l'erreur augmente. Une source dont la permutation ne change rien n'apportait rien ce
  mois-là. Cette bande dit <em>d'où vient</em> l'écart que la première bande constate.</p>
  <div class="carte">{carte_importance()}
    <div class="legende">
      <span><b>Erreur du produit</b></span><span>{bornes_err[0]:.1f}</span>
      <div class="rampe">{rampe_err}</div><span>{bornes_err[1]:.1f} µg/m³</span>
    </div>
    <div class="legende"><span><b>Poids de la source</b></span><span>sans effet</span>
      <div class="rampe">{rampe}</div><span>déterminant</span>
      <span style="margin-left:12px">Permutation stratifiée par mois — mélanger sur l'année
      détruirait aussi la saison, et l'on mesurerait alors le calendrier partout.</span>
    </div>
  </div>
  <div class="reserve"><span class="etiq">Ce que ça ne dit pas</span>
  <p>La bande du haut est produite <b>hors station</b> : chaque mois est prédit par un modèle
  qui n'a jamais vu les stations qu'il évalue. Mais la correction complète inclut
  l'observation à J−2, donc ce chiffre vaut au <b>périmètre instrumenté</b> — pas en tout
  point d'une carte. Et le produit officiel n'a d'archive qu'à partir du 18 janvier 2024 : les
  mois de 2023 sont vides en haut, présents en bas.</p>
  <p>Deux sources porteuses de la <b>même</b> information se partagent l'importance et
  paraissent toutes deux faibles. Ces chiffres se lisent comme des contributions
  <b>marginales</b>, pas comme des parts d'un tout — le projet a mesuré que les familles météo
  sont largement redondantes entre elles.</p></div>
</section>
<footer>
  Post-traitement statistique des prévisions CAMS Europe · validation par stations entièrement
  exclues · chiffres issus de <code>reports/VERITE_DOSSIER.md</code>, source unique du dossier.<br>
  Données Copernicus (CAMS, GLO-30, GFAS), IGN BD TOPO, Agence européenne pour l'environnement.
</footer>
</main>
</div></div>"""

    sortie = RACINE / "reports/figures/anatomie_methode.html"
    sortie.write_text(html, encoding="utf-8")
    print(f"Écrit : {sortie.relative_to(RACINE)} · "
          f"{sortie.stat().st_size / 1024:.0f} Ko · {len(COMPOSANTS)} composants")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
