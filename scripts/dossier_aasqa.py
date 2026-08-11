#!/usr/bin/env python3
"""La page destinée à une AASQA — ce que la correction change, et où elle échoue.

Pourquoi une seconde page plutôt qu'une refonte
-----------------------------------------------
``presentation.html`` reste en ligne et n'est pas touchée : elle raconte la construction du
projet, avec ses détours et ses résultats négatifs, et c'est sa valeur. Cette page-ci répond
à une autre question, celle d'un service régional : *chez moi, ça change quoi, et quand est-ce
que ça ne marche pas ?*

Elle est donc organisée en questions, pas en chapitres, et chaque réponse porte sa mesure
puis la ligne qui la borne.

La carte
--------
Le cœur de la page. Chaque station est **prédite par un modèle qui ne l'a jamais vue**.
L'échelle est **divergente** — rouge, neutre, bleu — reprise à l'identique de la démonstration
Streamlit : le zéro sépare « la correction aide » de « la correction nuit », et c'est la seule
lecture utile. **Les stations dégradées sont montrées, pas masquées.**

Projection Lambert-93, la projection légale française, celle dans laquelle les stations sont
déjà décrites. Contours intégrés au fichier — la politique de sécurité des pages publiées
interdit toute requête externe à l'affichage.

Usage : python3 scripts/dossier_aasqa.py
Sortie : reports/figures/dossier_aasqa.html
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]

NOM = {"O3": "Ozone", "NO2": "Dioxyde d'azote", "PM25": "Particules PM2,5",
       "PM10": "Particules PM10"}
GRAIN = {"O3": "maximum glissant 8 h", "NO2": "maximum horaire",
         "PM25": "moyenne journalière", "PM10": "moyenne journalière"}
# Les trois couleurs de la carte, reprises à l'identique de la démonstration Streamlit.
ROUGE, NEUTRE, BLEU = "#D03B3B", "#F0EFEC", "#2A78D6"
BORNE = 50.0  # bornes de l'échelle divergente, en points de pourcentage


def teinte_gain(gain: float) -> str:
    """Échelle divergente bornée à ±50 points, neutre à zéro."""
    f = float(np.clip(gain, -BORNE, BORNE)) / BORNE
    depart = NEUTRE if f >= 0 else NEUTRE
    arrivee = BLEU if f >= 0 else ROUGE
    t = abs(f)
    d = [int(depart[i:i + 2], 16) for i in (1, 3, 5)]
    a = [int(arrivee[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{int(x + (y - x) * t):02x}" for x, y in zip(d, a))


def carte(t: pd.DataFrame, contours: list, polluant: str) -> str:
    """Une carte SVG en Lambert-93 — stations coloriées par gain."""
    v = t[t["polluant"] == polluant]
    xs = np.concatenate([np.array([p[0] for p in a]) for a in contours])
    ys = np.concatenate([np.array([p[1] for p in a]) for a in contours])
    x0, x1 = xs.min() - 15, xs.max() + 15
    y0, y1 = ys.min() - 15, ys.max() + 15
    L, H = 760, 740
    ex = min(L / (x1 - x0), H / (y1 - y0))
    mx, my = (L - (x1 - x0) * ex) / 2, (H - (y1 - y0) * ex) / 2

    def px(x, y):
        # L'axe y du SVG descend, celui du Lambert-93 monte : l'inversion est ici, une fois.
        return mx + (x - x0) * ex, H - my - (y - y0) * ex

    traits = []
    for anneau in contours:
        pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in (px(p[0], p[1]) for p in anneau))
        traits.append(f'<polygon points="{pts}" class="terre"/>')

    # Les stations dégradées passent au-dessus : ce sont elles qu'il faut voir.
    points = []
    for _, r in v.sort_values("gain_pct", ascending=False).iterrows():
        cx, cy = px(r["x_km"], r["y_km"])
        titre = (f"{r['nom']} · {r['type_station']}\n"
                 f"RMSE {r['rmse_cams']:.1f} → {r['rmse_nous']:.1f} µg/m³ "
                 f"({r['gain_pct']:+.1f} %)\n{int(r['n_jours'])} jours évalués")
        points.append(
            f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="4.6" fill="{teinte_gain(r["gain_pct"])}"'
            f' class="st"><title>{titre}</title></circle>')

    med = float(v["gain_pct"].median())
    degradees = int((v["gain_pct"] < 0).sum())
    return (f'<svg viewBox="0 0 {L} {H}" role="img" aria-label="Carte des stations, gain de '
            f'la correction par station">{"".join(traits)}{"".join(points)}</svg>',
            len(v), med, degradees)


def main() -> int:
    t = pd.read_csv(RACINE / "reports/carte_stations.csv")
    contours = json.loads((RACINE / "reports/carte_stations_contours.json").read_text())

    cartes, onglets, resumes = [], [], {}
    for i, p in enumerate(("PM10", "O3", "NO2", "PM25")):
        svg, n, med, deg = carte(t, contours, p)
        actif = " actif" if i == 0 else ""
        cartes.append(f'<div class="vue{actif}" id="carte-{p}">{svg}</div>')
        onglets.append(f'<button class="onglet{actif}" data-p="{p}" '
                       f'aria-pressed="{"true" if i == 0 else "false"}">{NOM[p]}</button>')
        resumes[p] = (n, med, deg)
    bloc_resumes = "".join(
        f'<div class="res{" actif" if i == 0 else ""}" id="res-{p}">'
        f'<span><b>{resumes[p][0]}</b> stations</span>'
        f'<span>gain médian <b>{resumes[p][1]:+.1f} %</b></span>'
        f'<span><b>{resumes[p][2]}</b> dégradée{"s" if resumes[p][2] > 1 else ""}'
        f' ({100 * resumes[p][2] / resumes[p][0]:.0f} %)</span>'
        f'<span class="grain">{GRAIN[p]}</span></div>'
        for i, p in enumerate(("PM10", "O3", "NO2", "PM25")))

    rampe = "".join(
        f'<span style="background:{teinte_gain(g)}"></span>'
        for g in np.linspace(-BORNE, BORNE, 60))

    html = f"""<title>Corriger une prévision de qualité de l'air — ce que ça change, et où ça échoue</title>
<style>
:root{{
  --papier:#FBFCFC; --carte:#FFFFFF; --creux:#EFF3F4;
  --encre:#0D1418; --encre-doux:#44565B; --encre-tenu:#78898D;
  --liseré:#DCE4E6; --petrole:#0E6B74; --petrole-doux:#E3F0F1;
  --rouge:{ROUGE}; --bleu:{BLEU};
  --sans:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  --mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
  --mesure:66ch;
  color-scheme:light;
}}
@media (prefers-color-scheme:dark){{:root:where(:not([data-theme="light"])){{
  --papier:#0D1418; --carte:#151F23; --creux:#0A1013;
  --encre:#E7EFF0; --encre-doux:#A6BABE; --encre-tenu:#71868B;
  --liseré:#213237; --petrole:#55C6CF; --petrole-doux:#113137;
  color-scheme:dark;
}}}}
:root[data-theme="dark"]{{
  --papier:#0D1418; --carte:#151F23; --creux:#0A1013;
  --encre:#E7EFF0; --encre-doux:#A6BABE; --encre-tenu:#71868B;
  --liseré:#213237; --petrole:#55C6CF; --petrole-doux:#113137;
  color-scheme:dark;
}}
*{{box-sizing:border-box}}
body,.doc{{margin:0;background:var(--papier);color:var(--encre);
  font:16.5px/1.62 var(--sans);-webkit-font-smoothing:antialiased}}
.jauge{{position:sticky;top:0;height:3px;background:transparent;z-index:20}}
.jauge i{{display:block;height:100%;width:0;background:var(--petrole);transition:width .1s}}
.enveloppe{{max-width:53rem;margin:0 auto;padding:0 1.6rem}}
header{{padding:4.5rem 0 2.5rem}}
.chapo{{font-family:var(--mono);font-size:.7rem;letter-spacing:.14em;text-transform:uppercase;
  color:var(--petrole);margin-bottom:1.1rem}}
h1{{font-size:clamp(2rem,4.4vw,3rem);line-height:1.09;letter-spacing:-.024em;
  font-weight:600;margin:0 0 1rem;text-wrap:balance}}
header p{{color:var(--encre-doux);font-size:1.06rem;max-width:var(--mesure);margin:0}}
.chiffres{{display:grid;grid-template-columns:repeat(auto-fit,minmax(11.5rem,1fr));
  gap:1px;background:var(--liseré);border:1px solid var(--liseré);margin:2.6rem 0 0}}
.ch{{background:var(--carte);padding:1.1rem 1.2rem}}
.ch .v{{font-family:var(--mono);font-size:1.55rem;font-variant-numeric:tabular-nums;
  letter-spacing:-.025em;line-height:1.1;color:var(--petrole)}}
.ch .k{{font-size:.79rem;color:var(--encre-doux);margin-top:.42rem;line-height:1.38}}
section{{padding:3.4rem 0;border-top:1px solid var(--liseré)}}
.num{{font-family:var(--mono);font-size:.72rem;color:var(--encre-tenu);
  font-variant-numeric:tabular-nums;letter-spacing:.08em}}
h2{{font-size:clamp(1.35rem,2.7vw,1.85rem);line-height:1.2;letter-spacing:-.018em;
  font-weight:600;margin:.5rem 0 1.1rem;max-width:24ch;text-wrap:balance}}
p,ul,ol{{max-width:var(--mesure)}}
p+p{{margin-top:.85rem}}
ul{{padding-left:1.1rem}} li{{margin-bottom:.4rem}}
b,strong{{font-weight:640}}
.borne{{border-left:2px solid var(--petrole);background:var(--carte);
  padding:.95rem 1.2rem;margin:1.6rem 0;max-width:var(--mesure)}}
.borne .lab{{font-family:var(--mono);font-size:.66rem;letter-spacing:.11em;
  text-transform:uppercase;color:var(--petrole);margin-bottom:.45rem}}
.borne p{{margin:0;font-size:.94rem;color:var(--encre-doux)}}
.tbl{{overflow-x:auto;border:1px solid var(--liseré);margin:1.6rem 0;background:var(--carte)}}
table{{border-collapse:collapse;width:100%;font-size:.87rem}}
th,td{{padding:.55rem .85rem;text-align:left;border-bottom:1px solid var(--liseré)}}
thead th{{font-size:.7rem;letter-spacing:.07em;text-transform:uppercase;
  color:var(--encre-tenu);font-weight:600;background:var(--creux);white-space:nowrap}}
tbody tr:last-child td{{border-bottom:none}}
td.n,th.n{{text-align:right;font-family:var(--mono);font-variant-numeric:tabular-nums}}
tr.fort td{{background:var(--petrole-doux);font-weight:600}}

/* La carte s'échappe de la colonne et garde un fond sombre dans les deux thèmes :
   une carte se lit mieux ainsi, et c'est un choix, pas un oubli. */
.atlas{{background:#0A1216;color:#DCE7E9;margin:2.2rem 0;border:1px solid #1B2A30}}
.atlas .barre{{display:flex;flex-wrap:wrap;gap:.4rem;padding:.9rem 1.1rem;
  border-bottom:1px solid #1B2A30}}
.onglet{{font:inherit;font-size:.83rem;padding:.34rem .8rem;border-radius:2px;cursor:pointer;
  background:transparent;color:#8CA3A8;border:1px solid #24363D}}
.onglet:hover{{color:#DCE7E9}}
.onglet.actif{{background:#14262B;color:#7FDCE4;border-color:#2F4A52}}
.onglet:focus-visible{{outline:2px solid #7FDCE4;outline-offset:2px}}
.vue{{display:none}} .vue.actif{{display:block}}
.atlas svg{{display:block;width:100%;height:auto}}
.terre{{fill:#111E23;stroke:#2A3F46;stroke-width:.8}}
.st{{stroke:rgba(255,255,255,.8);stroke-width:.65}}
.st:hover{{stroke:#fff;stroke-width:1.6}}
.res{{display:none;gap:1.4rem;padding:.85rem 1.1rem;font-size:.83rem;color:#A9BFC3;
  border-top:1px solid #1B2A30;flex-wrap:wrap}}
.res.actif{{display:flex}}
.res b{{color:#DCE7E9;font-family:var(--mono);font-variant-numeric:tabular-nums}}
.res .grain{{margin-left:auto;color:#7B9196;font-family:var(--mono);font-size:.76rem}}
.legende{{display:flex;align-items:center;gap:.65rem;padding:.85rem 1.1rem;
  font-size:.78rem;color:#A9BFC3;flex-wrap:wrap;border-top:1px solid #1B2A30}}
.rampe{{display:flex;height:9px;width:190px;border-radius:2px;overflow:hidden}}
.rampe span{{flex:1}}
.tick{{font-family:var(--mono);font-size:.72rem;color:#7B9196;font-variant-numeric:tabular-nums}}
footer{{border-top:1px solid var(--liseré);padding:1.9rem 0 3.4rem;
  font-size:.79rem;color:var(--encre-tenu);line-height:1.6}}
@media (max-width:40rem){{ .res .grain{{margin-left:0;width:100%}} }}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
<div class="doc">
<div class="jauge"><i id="jauge"></i></div>
<div class="enveloppe">

<header>
  <div class="chapo">Post-traitement de prévision · candidature ATMO Occitanie</div>
  <h1>Corriger une prévision de qualité de l'air — ce que ça change, et où ça échoue</h1>
  <p>Les prévisions européennes CAMS sont produites sur une maille de huit kilomètres.
  Une méthode statistique apprend leur erreur station par station et la corrige. Cette page
  donne les gains, <b>et les quatre situations où la méthode n'apporte rien</b> — mesurées
  au même protocole.</p>
  <div class="chiffres">
    <div class="ch"><div class="v">+23,4 %</div><div class="k">d'erreur en moins sur
      l'ozone, au grain réglementaire, France 2024</div></div>
    <div class="ch"><div class="v">−11,6 → −0,5</div><div class="k">µg/m³ de biais NO₂ sur
      150 stations urbaines de fond</div></div>
    <div class="ch"><div class="v">3,5×</div><div class="k">plus de dépassements de la
      valeur cible ozone, à budget de fausses alertes égal</div></div>
    <div class="ch"><div class="v">+33,3 %</div><div class="k">sur les <b>PM10</b>, qui
      portent 40 des 52 vigilances réellement déclarées en Occitanie</div></div>
    <div class="ch"><div class="v">0 €</div><div class="k">de donnée payante — Copernicus,
      IGN, EEA, ECMWF, LCSQA ouverts</div></div>
  </div>
</header>

<section>
  <div class="num">01</div>
  <h2>Que ne voit pas une maille de huit kilomètres&nbsp;?</h2>
  <p>Une maille CAMS couvre soixante-quatre kilomètres carrés et rend <b>une seule valeur</b>.
  Deux stations situées dans la même maille reçoivent donc la même prévision, qu'elles soient
  en fond de vallée ou sur une crête, en centre-ville ou en périphérie.</p>
  <p>L'écart est mesurable. Sur les stations urbaines de fond, la prévision brute
  <b>sous-estime le dioxyde d'azote de 11,6 µg/m³</b> en biais moyen — un polluant dominé par
  des sources linéaires que huit kilomètres ne résolvent pas. Sur l'ozone, c'est en zone
  rurale que le biais est le plus marqué, à −2,5 µg/m³.</p>
  <p>Ce sont des erreurs <b>structurelles</b>, pas du bruit : elles ne croissent pas avec
  l'échéance. Une erreur qui ne croît pas avec l'horizon ne vient pas de la divergence
  chaotique de l'atmosphère — elle est donc apprenable.</p>
  <div class="borne"><div class="lab">Ce que ça ne dit pas</div>
    <p>Que le modèle de chimie-transport serait défaillant. Il répond à une contrainte de
    couverture continentale ; ce travail ajoute une couche au-dessus, il ne le remplace
    pas.</p></div>
</section>

<section>
  <div class="num">02</div>
  <h2>Où la correction agit — et où elle dégrade</h2>
  <p>Chaque point est une station, <b>prédite par un modèle qui ne l'a jamais vue</b> :
  elle est entièrement retirée de l'apprentissage avant d'être évaluée. Le bleu marque un
  gain, le rouge une dégradation.</p>
  <p><b>Les stations dégradées sont montrées, pas masquées.</b> Elles sont rares sur l'ozone
  — 4 sur 270 —, sur les PM10 — 6 sur 314 — et sur les PM2,5 — 13 sur 227. Mais sur le <b>dioxyde d'azote elles sont
  75 sur 340, soit 22 %</b>, alors que le gain médian y atteint +32 %. Une moyenne favorable
  recouvre donc, sur ce polluant, près d'une station sur quatre où la correction fait perdre.
  Comprendre pourquoi est le prolongement le plus utile de ce travail.</p>

  <div class="atlas">
    <div class="barre">{"".join(onglets)}</div>
    {"".join(cartes)}
    <div class="legende"><span>la correction <b style="color:{ROUGE}">dégrade</b></span>
      <span class="tick">−50</span><div class="rampe">{rampe}</div><span class="tick">+50</span>
      <span>la correction <b style="color:{BLEU}">améliore</b></span>
      <span style="margin-left:auto">échelle bornée à ±50 points · projection Lambert-93 ·
      survoler un point pour le détail</span></div>
    {bloc_resumes}
  </div>

  <div class="borne"><div class="lab">Ce que ça ne dit pas</div>
    <p>Ce que vaudrait la correction en un lieu <b>sans station</b>. Le gain de 28,6 %
    mesuré avec des plis arbitraires décrit une interpolation à l'intérieur d'un réseau
    dense — pas une extrapolation. En séparant réellement apprentissage et évaluation dans
    l'espace, il tombe à <b>≈ 13,5 %</b>. <b>C'est ce chiffre qu'il faut retenir pour
    couvrir un territoire non instrumenté.</b></p>
    <p style="margin-top:.6rem">Il est décomposé, ce qui est rare : sur les 15 points
    perdus, <b>9,4 sont de la fuite</b> supprimée par le blocage spatial, et le reste vient
    d'un fossé de 150 km qui retire aussi 70 % des stations d'apprentissage — un témoin à
    retrait aléatoire montre que <b>3 points</b> de la chute sont de la simple famine de
    données, pas de la fuite.</p>
    <p style="margin-top:.6rem">La cause n'est pas la densité du réseau mais la
    <b>portée</b> : les résidus d'ozone restent corrélés jusqu'à <b>150 km</b> — une voisine
    à 50 km en renseigne encore un tiers. Ceux du NO₂ décorrèlent en <b>75 km</b> et ne
    valent que 0,26 même à 2 km, ce qui explique qu'il perde à peine 2,2 points malgré des
    stations trois fois plus serrées.</p></div>
</section>

<section>
  <div class="num">03</div>
  <h2>Ce que ça vaut dans les conventions d'un rapport réglementaire</h2>
  <p>Un rapport AASQA ne calcule pas une erreur globale sur toutes les mesures réunies. Il
  retient les <b>stations de fond</b> à <b>au moins 75 %</b> de données valides, calcule un score
  <b>par station</b> puis en fait la moyenne <b>non pondérée</b>, sépare les échéances, et
  limite l'ozone à la saison avril–septembre. Les chiffres ci-dessous suivent cette
  convention.</p>
  <div class="tbl"><table>
    <caption style="text-align:left;padding:.7rem .85rem;font-size:.78rem;
      color:var(--encre-tenu);border-bottom:1px solid var(--liseré);background:var(--creux)">
      Échéance J+1, RMSE en µg/m³, stations de fond, validation par stations exclues</caption>
    <thead><tr><th>Polluant</th><th class="n">Stations</th><th class="n">CAMS brut</th>
      <th class="n">Corrigé</th><th class="n">Gain</th></tr></thead>
    <tbody>
      <tr><td>Ozone</td><td class="n">254</td><td class="n">10,06</td>
        <td class="n">7,88</td><td class="n">+21,7 %</td></tr>
      <tr class="fort"><td>Dioxyde d'azote</td><td class="n">217</td><td class="n">15,46</td>
        <td class="n">10,10</td><td class="n">+34,7 %</td></tr>
      <tr><td>Particules PM2,5</td><td class="n">156</td><td class="n">3,94</td>
        <td class="n">2,77</td><td class="n">+29,6 %</td></tr>
      <tr class="fort"><td>Particules PM10</td><td class="n">191</td><td class="n">6,35</td>
        <td class="n">4,24</td><td class="n">+33,3 %</td></tr>
    </tbody></table></div>
  <p>Le produit officiel de post-traitement publié par Copernicus, comparé sur les mêmes
  stations et les mêmes jours, <b>dégrade la prévision brute d'ozone huit mois sur douze</b>
  et de <b>−19,6 %</b> sur la saison où l'ozone se juge. Sa moyenne annuelle positive est la
  somme de deux régimes opposés.</p>

  <h3 style="font-size:1.02rem;font-weight:640;margin:2rem 0 .7rem">Et contre la chaîne
  nationale&nbsp;?</h3>
  <p>Une AASQA ne consomme pas CAMS brut : elle reçoit <b>PREV'AIR</b>. Le rapport
  <i>Performances Prev'air en 2024</i> du LCSQA donne cette barre — mais au
  <b>maximum journalier horaire</b>, pas au maximum glissant 8 h. Recalculé sur leur grain,
  sur stations de fond et en saison ozone :</p>
  <div class="tbl"><table>
    <thead><tr><th>chaîne</th><th class="n">brut</th><th class="n">corrigé</th>
      <th class="n">gain de la correction</th></tr></thead>
    <tbody>
      <tr><td>PREV'AIR — CHIMERE → adaptation statistique, <b>sur l'ozone</b></td>
        <td class="n">13,9</td>
        <td class="n">13,3</td><td class="n">+4,3 %</td></tr>
      <tr class="fort"><td>ce projet — CAMS → notre correction</td><td class="n">11,08</td>
        <td class="n">8,84</td><td class="n">+20,2 %</td></tr>
    </tbody></table></div>
  <p><b>Chaque correction est comparée à son propre modèle amont</b>, jamais les RMSE
  absolues entre elles : CAMS brut bat déjà CHIMERE brut de 2,8 µg/m³ pour des raisons
  d'amont — c'est une médiane d'ensemble de neuf à onze modèles, dont CHIMERE. Cette lecture
  neutralise aussi les DROM, inclus dans leur moyenne nationale.</p>
  <p>Deux écarts jouent <b>contre</b> nous et ne fragilisent donc pas la conclusion : leurs
  scores sont à J0 quand les nôtres sont à J+1, et notre 8,84 vient de plis non bloqués —
  au protocole strict le gain descendrait vers 13-14&nbsp;%.</p>

  <div class="borne"><div class="lab">🔴 Ce tableau est un tableau d'ozone — ne pas le lire
    comme un classement des deux méthodes</div>
    <p>Le même rapport donne les trois autres polluants à J0, et l'ordre s'y inverse&nbsp;:
    leur adaptation statistique gagne <b>+32,9&nbsp;%</b> sur le NO₂ (16,7 → 11,2),
    <b>+52,5&nbsp;%</b> sur les PM10 (9,9 → 4,7) et <b>+60,1&nbsp;%</b> sur les PM2,5
    (7,65 → 3,05). <b>Sur ces trois-là, leur correction gagne davantage que la nôtre sur
    l'ozone.</b> Le résultat n'est pas « nous faisons cinq fois mieux » — c'est que
    <b>l'ozone est le polluant où l'adaptation statistique paie le moins, pour eux comme
    pour nous</b>.</p>
    <p><b>Et la différence de nature compte plus que l'écart de score.</b> AS-CHI est un
    <b>krigeage</b>&nbsp;: le résidu mesure moins modèle est calculé <i>aux stations</i>,
    puis interpolé — krigeage à dérive externe depuis 2010. Il lui faut donc des
    <b>observations au moment de la correction</b>, et il se dégrade là où le réseau est
    lâche. Notre correction apprend ce résidu à partir de variables disponibles à l'heure
    d'émission&nbsp;: elle existe <b>là où aucune station n'existe</b> — les 43 EPCI sans
    station à moins de 30 km, les 4 départements d'Occitanie sans station retenue. C'est
    aussi ce qui explique que leur avantage s'annule dès J2&nbsp;: un champ d'innovations
    est un instantané, quand un biais de site ne l'est pas.</p>
  </div>
  <div class="borne"><div class="lab">Le motif qui se répète</div>
    <p>Le rapport du LCSQA écrit, page 22, que <i>« l'amélioration apportée par l'adaptation
    statistique diminue au fur et à mesure des échéances, jusqu'à une légère dégradation des
    performances pour l'AS par rapport au modèle brut à partir de J2 »</i>. C'est exactement
    ce que ce travail mesure sur le produit de Copernicus. <b>Deux post-traitements
    officiels, deux chaînes différentes, le même retournement</b> — ce n'est plus l'anomalie
    d'un produit.</p></div>
  <div class="borne"><div class="lab">Ce que ça ne dit pas</div>
    <p>Que la méthode serait nouvelle. Le post-traitement statistique des sorties CAMS est
    publié — notamment par les auteurs du produit officiel eux-mêmes. Ce travail réplique et
    caractérise, il ne découvre pas.</p></div>
</section>

<section>
  <div class="num">04</div>
  <h2>Les quatre situations où elle n'apporte rien</h2>
  <ul>
    <li><b>Au seuil qui déclenche une procédure.</b> Le seuil d'information et de
      recommandation pour l'ozone est de <b>180 µg/m³ en maximum horaire</b> ; le seuil
      d'alerte est de 240 µg/m³ <b>pendant trois heures consécutives</b>. À 180, sur
      60 400 jours-station, on compte 32 dépassements : CAMS en détecte 3, la correction 2,
      et aucun des deux à J+3. Le facteur 3,5× porte, lui, sur la <b>valeur cible
      européenne</b> — 120 µg/m³ en maximum glissant 8 h, appréciée sur un nombre annuel de
      dépassements moyenné sur trois ans. Ce n'est ni un seuil d'information ni, jour par
      jour, un déclencheur préfectoral, et le déclenchement réel dépend en outre de critères
      de superficie et de population : <b>une valeur à une station ne suffit pas</b>.</li>
    <li><b>Sur la vérification par un tiers.</b> Les PM10 — qui portent 40 des 52
      vigilances réellement déclarées — n'ont été ajoutées qu'au 1<sup>er</sup> août 2026 et
      n'ont pas encore été confrontées au post-traitement officiel de Copernicus, faute
      d'avoir téléchargé ce produit pour ce polluant. Leur gain de <b>+33,3 %</b> est donc
      mesuré contre <b>CAMS brut seul</b>, sur une fenêtre différente des trois autres
      (janvier 2024 – août 2026).</li>
    <li><b>Là où la prévision est déjà juste.</b> Sur le NO₂ en zone rurale, la correction ne
      gagne rien (5,14 contre 5,13 µg/m³) et dégrade légèrement le biais : niveau bas, aucune
      source locale, rien à corriger.</li>
    <li><b>Loin de toute station.</b> Le gain chute d'un tiers dès qu'on impose une vraie
      séparation spatiale entre apprentissage et évaluation.</li>
  </ul>
  <div class="borne"><div class="lab">Pourquoi cette section existe</div>
    <p>Un prévisionniste vérifiera le seuil de déclenchement en une minute. Mieux vaut que
    la limite soit énoncée ici que découverte là.</p></div>
</section>

<section>
  <div class="num">05</div>
  <h2>Ce qu'il faudrait pour l'exploiter</h2>
  <p>La chaîne tourne sur des données ouvertes et ne demande aucun abonnement. Trois choses
  manquent pour un usage quotidien :</p>
  <ul>
    <li><b>Les observations récentes à l'émission.</b> Le levier le plus fort mesuré
      (+8,9 % sur l'ozone, +21,9 % sur le NO₂) est l'observation de l'avant-veille. Elle
      n'existe qu'aux stations instrumentées — elle scinde donc le produit en deux
      périmètres qu'il ne faut jamais confondre.</li>
    <li><b>La météo prévue.</b> Lisible par plage d'octets sur un seau public ECMWF, elle
      rend entre +2,2 % et +5,5 % selon le polluant. Trois champs suffisent : vent,
      rayonnement et pluie — le point de rosée est redondant.</li>
    <li><b>Une décision d'exploitation.</b> Qui opère la bascule si une source manque à
      3 h du matin, et quel mode dégradé s'applique alors. C'est une question de service,
      pas de modèle.</li>
  </ul>
</section>

<footer>
  Validation par stations entièrement exclues · chiffres issus de
  <code>reports/VERITE_DOSSIER.md</code>, source unique du dossier · page générée par
  <code>scripts/dossier_aasqa.py</code>.<br>
  Données Copernicus (CAMS, GLO-30, GFAS), ECMWF, IGN BD TOPO, Agence européenne pour
  l'environnement, ATMO Occitanie.
</footer>
</div></div>
<script>
(function(){{
  var j=document.getElementById('jauge');
  addEventListener('scroll',function(){{
    var h=document.documentElement,m=h.scrollHeight-h.clientHeight;
    j.style.width=(m>0?100*h.scrollTop/m:0)+'%';
  }},{{passive:true}});
  document.querySelectorAll('.onglet').forEach(function(b){{
    b.addEventListener('click',function(){{
      var p=b.dataset.p;
      document.querySelectorAll('.onglet').forEach(function(o){{
        var a=o===b; o.classList.toggle('actif',a); o.setAttribute('aria-pressed',a);
      }});
      document.querySelectorAll('.vue').forEach(function(v){{
        v.classList.toggle('actif',v.id==='carte-'+p);
      }});
      document.querySelectorAll('.res').forEach(function(r){{
        r.classList.toggle('actif',r.id==='res-'+p);
      }});
    }});
  }});
}})();
</script>"""

    sortie = RACINE / "reports/figures/dossier_aasqa.html"
    sortie.write_text(html, encoding="utf-8")
    print(f"Écrit : {sortie.relative_to(RACINE)} · {sortie.stat().st_size / 1024:.0f} Ko")
    for p in ("PM10", "O3", "NO2", "PM25"):
        n, med, deg = resumes[p]
        print(f"  {NOM[p]:18} {n:4d} stations · médiane {med:+5.1f} % · "
              f"{deg:3d} dégradée(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
