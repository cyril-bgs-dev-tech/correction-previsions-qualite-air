#!/usr/bin/env python3
"""Trois panneaux annuels — la vérité, le produit officiel, notre correction complète.

Pourquoi une carte de chaleur plutôt qu'un score
------------------------------------------------
Un tableau de rappel dit *combien*. Il ne dit pas *où* ni *quand*, et surtout il ne montre pas
la **forme** de l'erreur : un produit peut manquer les épisodes en les lissant tous, ou n'en
manquer que certains. Trois panneaux à échelle identique rendent la différence visible d'un
coup d'œil.

Ce qui est tracé
----------------
Une ligne par station, une colonne par jour de 2024, la couleur portant le **maximum journalier
8 h** d'ozone — la grandeur qui déclenche les procédures.

Trois panneaux, mêmes stations, mêmes jours, **même échelle de couleur** :

1. **observé** — la vérité terrain ;
2. **MOS officiel** de Copernicus ;
3. **notre correction complète** — résidu + observations à J−2 + six membres d'ensemble.

L'échelle est **divergente autour du seuil réglementaire de 120 µg/m³** : bleu en dessous de
la normale, vert autour, rouge au-delà du seuil. Ce n'est pas décoratif — cela fait apparaître
les épisodes comme des bandes verticales, et un produit qui les rate reste vert là où la vérité
est rouge.

Les prédictions sont **hors échantillon** : chaque station est prédite par un modèle qui ne l'a
jamais vue.

Usage : python3 scripts/heatmap_annuelle.py [--polluant O3]
Sortie : reports/figures/heatmap_annuelle_{polluant}.html + reports/heatmap_annuelle_{polluant}.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import controle as ctl  # noqa: E402
from apport_observation_veille import variables_passees  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from comparer_mos_officiel import journalier, lire_officiel  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

MEMBRES = ["chimere", "emep", "mocage", "silam", "lotos", "match"]
# Les PM10 sont le seul polluant dont le seuil retenu soit un vrai déclencheur de procédure
# préfectorale — 50 µg/m³ en moyenne journalière, seuil d'information de l'arrêté du
# 07/04/2016 — et c'est sur elles que portent 40 des 52 vigilances réellement déclarées en
# Occitanie. La borne « mauvais » de l'indice ATMO tombe au même endroit.
SEUIL = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0, "PM10": 50.0}
PREFIXE = {"O3": "o3", "NO2": "no2", "PM25": "pm25", "PM10": "pm10"}

# Libellés partagés avec les calendriers. Ils vivent ici, dans le module le plus bas de la
# chaîne, parce que `calendrier_signalements` importe déjà `heatmap_annuelle` : les définir
# là-haut et les redescendre créerait un cycle.
NOM_POLLUANT = {"O3": "Ozone", "NO2": "Dioxyde d'azote", "PM25": "Particules PM2,5",
                "PM10": "Particules PM10"}
GRANDEUR = {"O3": "maximum journalier 8 h", "NO2": "maximum horaire",
            "PM25": "moyenne journalière", "PM10": "moyenne journalière"}
# Les observations de PM10 ne viennent pas de la même source que les trois autres — le
# crédit doit suivre le polluant, pas le script.
SOURCE_OBS = {"O3": "EEA", "NO2": "EEA", "PM25": "EEA", "PM10": "LCSQA / data.gouv.fr"}


def preparer(polluant: str, n_plis: int) -> pd.DataFrame:
    """Table jour × station portant les trois produits, sur l'année 2024."""
    depart = time.time()
    court = PREFIXE[polluant]
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/membres_metropole_{court}_*.parquet")))
    membres = []
    if fichiers:
        m = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
        ctl.exiger_colonnes(m, MEMBRES, "membres")
        ctl.exiger_variation(m, MEMBRES, "membres")
        jeu = jeu.merge(m[["station_id", "timestamp_utc"] + MEMBRES],
                        on=["station_id", "timestamp_utc"], how="inner")
        membres = MEMBRES

    j = agreger_journalier(jeu, colonnes + membres, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    j["jour"] = pd.to_datetime(j["jour"])
    passees, obs = variables_passees(j)
    j = j.merge(passees, on=["station_id", "jour"], how="left").dropna(subset=obs)

    predicteurs = base + obs + membres
    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})
    print(f"{polluant} · {len(j):,} jours-station · {len(predicteurs)} prédicteurs · "
          f"{len(membres)} membres", flush=True)


    j["nous"] = np.nan
    for g in range(n_plis):
        test = (j["groupe"] == g).to_numpy()
        m = modele_mos(graine=0)
        m.fit(j.loc[~test, predicteurs],
              j.loc[~test, "obs_jour"] - j.loc[~test, "cams_jour"])
        j.loc[test, "nous"] = np.clip(
            j.loc[test, "cams_jour"] + m.predict(j.loc[test, predicteurs]), 0, None)
        print(f"  pli {g + 1}/{n_plis} · {time.time() - depart:.0f}s", flush=True)

    # ── Le produit officiel, sur les mêmes jours-station ──────────────────────
    # Toutes les archives disponibles, pas la seule année 2024 : la page couvre désormais
    # la période entière. Le produit officiel n'existe que sur une partie de la fenêtre ;
    # son panneau portera des cellules grises, et son sous-titre le dira.
    archives = sorted((RACINE / "data/raw/cams_mos_officiel").glob(f"{court}_*.zip"))
    officiel = []
    for a in archives:
        officiel.append(journalier(lire_officiel(a), ["officiel_mos"],
                                   GRANDEUR_PAR_POLLUANT[polluant]))
    if officiel:
        o = pd.concat(officiel, ignore_index=True)
        o["jour"] = pd.to_datetime(o["jour"]).dt.tz_localize(None)
        j["jour"] = j["jour"].dt.tz_localize(None) if j["jour"].dt.tz else j["jour"]
        j = j.merge(o, on=["station_id", "jour"], how="left")

    # ⚠️ Plus de filtre annuel. Un fichier par an obligeait à ouvrir trois pages pour lire
    # une même série, et empêchait de voir ce qui compte le plus : la **répétition** des
    # épisodes d'une année sur l'autre, et la dérive éventuelle du modèle amont.
    return j[["station_id", "jour", "obs_jour", "cams_jour", "nous"]
             + (["officiel_mos"] if "officiel_mos" in j else [])]


# Échelle **continue**, ancrée au seuil réglementaire. Les couleurs sont interpolées entre ces
# arrêts, sans palier : un jour à 118 µg/m³ et un jour à 122 ne doivent pas paraître identiques
# de part et d'autre d'une frontière arbitraire, mais se distinguer progressivement.
#
# Le pivot est le **seuil**, pas la médiane : c'est lui qui décide d'une procédure, et une
# échelle centrée sur la moyenne rendrait les épisodes indiscernables du fond.
ARRETS = [
    (0.00, (30, 70, 140)),    # bleu profond — très bas
    (0.35, (60, 145, 205)),   # bleu clair
    (0.55, (120, 195, 165)),  # vert-bleu
    (0.70, (185, 215, 110)),  # vert-jaune — normal
    (0.85, (243, 214, 75)),   # jaune
    (0.95, (240, 150, 45)),   # orange — approche du seuil
    (1.00, (225, 90, 45)),    # rouge-orange — **seuil**
    (1.30, (150, 20, 25)),    # rouge sombre
    (1.80, (85, 5, 30)),      # bordeaux — épisode sévère
]
GRIS_MANQUANT = (44, 44, 42)


def couleur_continue(rapport: np.ndarray) -> np.ndarray:
    """Interpole les arrêts ci-dessus, sans discrétisation."""
    positions = np.array([a for a, _ in ARRETS])
    teintes = np.array([c for _, c in ARRETS], dtype="float64")
    r = np.clip(np.nan_to_num(rapport, nan=0.0), positions[0], positions[-1])
    sortie = np.empty(r.shape + (3,), dtype="float64")
    for canal in range(3):
        sortie[..., canal] = np.interp(r, positions, teintes[:, canal])
    return sortie


def panneau(matrice: np.ndarray, titre: str, sous_titre: str, seuil: float,
            jours: list, echelle: int = 3) -> str:
    """Un panneau **matriciel** : une ligne par station, une colonne par jour.

    Le vectoriel a été abandonné pour une raison de fond : 270 stations × 366 jours × 3
    panneaux font 296 000 cellules, soit **19 Mo** de rectangles pour une limite de 16. Les
    compressions envisagées — paliers de couleur, fusion des jours identiques — auraient toutes
    dégradé **l'information** : un jour à 118 µg/m³ et un jour à 122 seraient devenus deux
    aplats de part et d'autre d'une frontière arbitraire.

    Le rendu matriciel inverse l'arbitrage : la couleur reste **continue**, chaque jour-station
    garde sa valeur exacte, et c'est la **définition** de l'image qui baisse. Un pixel par
    jour-station, agrandi par le navigateur, pèse quelques dizaines de kilooctets.
    """
    import base64
    import io

    from PIL import Image

    rvb = couleur_continue(matrice / seuil).astype("uint8")
    rvb[~np.isfinite(matrice)] = GRIS_MANQUANT
    image = Image.fromarray(rvb, mode="RGB")
    if echelle > 1:
        # Agrandissement au plus proche voisin : garder les cellules **nettes**. Une
        # interpolation lissée inventerait des valeurs intermédiaires entre deux stations
        # voisines, qui ne sont pas voisines dans l'espace.
        image = image.resize((image.width * echelle, image.height * echelle),
                             Image.NEAREST)
    tampon = io.BytesIO()
    image.save(tampon, format="PNG", optimize=True)
    donnees = base64.b64encode(tampon.getvalue()).decode()

    # Repères mensuels, en superposition CSS plutôt que dans l'image : ils restent nets à
    # toute taille d'affichage.
    # Repères adaptés à la durée : sur trois ans, douze étiquettes mensuelles par an
    # seraient illisibles. On étiquette les **janviers** en gras avec l'année, les autres
    # débuts de mois par un simple trait — et le trimestre quand la période est longue.
    premiers = sorted({pd.Timestamp(d).replace(day=1) for d in jours})
    n_mois = len(premiers)
    pas_etiquette = 1 if n_mois <= 14 else (3 if n_mois <= 30 else 6)
    index = {pd.Timestamp(d): i for i, d in enumerate(jours)}
    reperes = []
    for d in premiers:
        if d not in index:
            continue
        pct = 100 * index[d] / len(jours)
        if d.month == 1:
            reperes.append(f'<span class="an" style="left:{pct:.3f}%">{d:%Y}</span>')
        elif (d.month - 1) % pas_etiquette == 0:
            reperes.append(f'<span class="mois" style="left:{pct:.3f}%">{d:%b}</span>')
        else:
            reperes.append(f'<span class="tick" style="left:{pct:.3f}%"></span>')

    # Sur une longue période, `width:100%` écraserait 1 100 jours dans 1 180 px — moins
    # d'un pixel par jour, et les épisodes courts disparaîtraient. On impose une largeur
    # minimale de ~2,2 px par jour et on laisse le cadre défiler horizontalement.
    largeur_min = max(680, int(len(jours) * 2.2))
    return (f'<div class="panneau"><div class="ptitre">{titre}</div>'
            f'<div class="psub">{sous_titre}</div>'
            f'<div class="defile"><div class="cadre" style="min-width:{largeur_min}px">'
            f'<img src="data:image/png;base64,{donnees}" alt="{titre}" loading="lazy">'
            f'<div class="reperes">{"".join(reperes)}</div></div></div></div>')


def main(polluant: str, n_plis: int) -> int:
    seuil = SEUIL[polluant]
    d = preparer(polluant, n_plis)
    d.to_csv(RACINE / f"reports/heatmap_annuelle_{polluant}.csv", index=False)

    # Stations triées par nombre de dépassements observés : les plus exposées en haut, ce qui
    # regroupe les bandes rouges et rend les manques visibles.
    ordre = (d.assign(dep=d["obs_jour"] >= seuil).groupby("station_id")["dep"].sum()
              .sort_values(ascending=False))
    stations = list(ordre.index)
    jours = sorted(d["jour"].unique())
    print(f"\n{len(stations)} stations · {len(jours)} jours · "
          f"{int((d['obs_jour'] >= seuil).sum())} dépassements observés", flush=True)

    produits = [("obs_jour", "Vérité terrain", "ce que les stations ont mesuré")]
    if "officiel_mos" in d:
        # ⚠️ Le produit officiel ne couvre qu'une partie de la fenêtre. Sans le dire, ses
        # cellules grises se liraient comme un échec de prévision alors qu'il s'agit d'une
        # absence d'archive.
        dispo = d.loc[d["officiel_mos"].notna(), "jour"]
        couv = (f"disponible {pd.Timestamp(dispo.min()):%b %Y} → "
                f"{pd.Timestamp(dispo.max()):%b %Y}" if len(dispo) else "aucune archive")
        produits.append(("officiel_mos", "MOS officiel Copernicus",
                         f"le produit corrigé publié, gratuit · {couv} — "
                         f"le gris est une absence d'archive, pas une erreur"))
    # Les membres d'ensemble n'existent pas pour tous les polluants — les PM10 n'en ont
    # aucun. Décrire le produit réellement tracé, pas celui du cas le plus riche.
    n_membres = sum(m in d.columns for m in MEMBRES)
    detail = "résidu + observations J−2" + (f" + {n_membres} membres d'ensemble"
                                            if n_membres else "")
    produits.append(("nous", "Notre correction complète",
                     f"{detail} · hors échantillon"))

    index_station = {s: i for i, s in enumerate(stations)}
    index_jour = {j: i for i, j in enumerate(jours)}
    ligne_idx = d["station_id"].map(index_station).to_numpy()
    col_idx = d["jour"].map(index_jour).to_numpy()

    panneaux = []
    for colonne, titre, sous in produits:
        matrice = np.full((len(stations), len(jours)), np.nan)
        matrice[ligne_idx, col_idx] = d[colonne].to_numpy()
        manques = int(np.isnan(matrice).sum())
        sous_complet = sous + (f" · {manques:,} cellules sans valeur" if manques else "")
        panneaux.append(panneau(matrice, titre, sous_complet, seuil, jours))
        print(f"  {titre:32s} {int((d[colonne] >= seuil).sum()):5d} dépassements annoncés",
              flush=True)

    # Bande d'échelle : le dégradé continu lui-même, produit par la même fonction que les
    # panneaux — pas une approximation en CSS qui pourrait diverger.
    rampe = couleur_continue(np.linspace(0, 1.8, 400)[None, :]).astype("uint8")
    import base64 as _b64
    import io as _io

    from PIL import Image as _Image

    _t = _io.BytesIO()
    _Image.fromarray(np.repeat(rampe, 14, axis=0), mode="RGB").save(_t, format="PNG")
    rampe_png = _b64.b64encode(_t.getvalue()).decode()
    graduations = "".join(
        f'<span style="left:{100 * v / 1.8:.1f}%">{v * seuil:.0f}</span>'
        for v in (0.25, 0.5, 0.75, 1.0, 1.25, 1.5))
    echelle = (f'<div class="rampe"><img src="data:image/png;base64,{rampe_png}" alt="">'
               f'<div class="grad">{graduations}</div>'
               f'<div class="seuil" style="left:{100 / 1.8:.1f}%"></div></div>')

    # Le titre, la grandeur et le nombre de panneaux étaient écrits en dur sur l'ozone : la
    # page annonçait « Ozone » et « trois lectures » quel que soit le polluant lancé, et
    # même quand le MOS officiel manquait. Ils suivent désormais ce qui est réellement tracé.
    nom = NOM_POLLUANT[polluant]
    source_obs = SOURCE_OBS[polluant]
    n_panneaux = {2: "deux", 3: "trois"}.get(len(produits), str(len(produits)))
    # Le titre annonçait « 2024 » quelle que soit la période tracée. La règle 4 ter
    # s'applique aussi aux titres : ce qui est écrit doit venir des données.
    debut, fin = pd.Timestamp(jours[0]), pd.Timestamp(jours[-1])
    n_mois_total = (fin.year - debut.year) * 12 + fin.month - debut.month + 1
    periode = f"{debut:%b %Y} → {fin:%b %Y}"
    titre_page = (f"{nom}, {periode} — {n_panneaux} lectures d'une même série")

    html = f"""<title>{titre_page}</title>
<style>
.doc{{--plane:#0d0d0d;--surface-1:#1a1a19;--text-primary:#fff;--text-secondary:#c3c2b7;
  --border:rgba(255,255,255,.12);
  background:var(--plane);color:var(--text-primary);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.6;margin:0}}
.shell{{max-width:1180px;margin:0 auto;padding:0 clamp(14px,3vw,28px)}}
h1{{font-size:clamp(1.5rem,3.4vw,2.1rem);letter-spacing:-.02em;margin:1.2em 0 .2em}}
.lede{{color:var(--text-secondary);max-width:70ch;margin:0 0 1.6em}}
.panneau{{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;
  padding:14px 16px;margin:14px 0}}
.ptitre{{font-weight:650;letter-spacing:-.01em}}
.psub{{color:var(--text-secondary);font-size:.83rem;margin:.2em 0 10px}}
.defile{{overflow-x:auto;overflow-y:hidden;padding-bottom:2px}}
.cadre{{position:relative;padding-bottom:16px}}
.cadre img{{display:block;width:100%;height:auto;image-rendering:pixelated;border-radius:3px}}
.reperes{{position:relative;height:14px;margin-top:3px}}
.mois{{position:absolute;font-size:.66rem;color:var(--text-secondary);
  transform:translateX(1px);border-left:1px solid rgba(255,255,255,.20);padding-left:3px}}
.an{{position:absolute;font-size:.74rem;font-weight:650;color:var(--text-primary);
  transform:translateX(1px);border-left:2px solid rgba(255,255,255,.55);padding-left:4px}}
.tick{{position:absolute;top:0;height:5px;width:1px;background:rgba(255,255,255,.14)}}
.rampe{{position:relative;margin:6px 0 30px;max-width:560px}}
.rampe img{{display:block;width:100%;height:13px;border-radius:3px}}
.grad{{position:relative;height:15px;font-size:.7rem;color:var(--text-secondary)}}
.grad span{{position:absolute;transform:translateX(-50%);padding-top:2px}}
.seuil{{position:absolute;top:-2px;height:17px;width:2px;background:#fff;
  box-shadow:0 0 0 1px rgba(0,0,0,.5)}}
.note{{background:var(--surface-1);border:1px solid var(--border);border-left:3px solid #eb6834;
  border-radius:10px;padding:14px 18px;margin:18px 0}}
p,li{{max-width:74ch}}
footer{{color:var(--text-secondary);font-size:.78rem;border-top:1px solid var(--border);
  margin-top:32px;padding:18px 0 40px}}
</style>
<div class="doc"><div class="shell">
<h1>{titre_page}</h1>
<p class="lede">Une ligne par station ({len(stations)} stations, les plus exposées en haut),
une colonne par jour sur <b>{n_mois_total} mois</b> ({len(jours):,} jours). La couleur porte
le <b>{GRANDEUR[polluant]}</b>,
la grandeur sur laquelle se déclenchent les procédures. Même échelle sur les {n_panneaux} panneaux,
pivotée sur le <b>seuil réglementaire de {seuil:.0f} µg/m³</b>.</p>
{echelle}
<p class="lede" style="font-size:.82rem">Échelle continue en µg/m³, sans palier. Le repère blanc marque le <b>seuil réglementaire</b> de {seuil:.0f} µg/m³.</p>
{"".join(panneaux)}
<div class="note">
<p><b>Ce que les motifs montrent, et que les scores ne disent pas.</b> Les épisodes
apparaissent en bandes verticales — ils touchent de nombreuses stations le même jour. Un
produit qui les manque reste vert ou jaune là où la vérité est rouge.</p>
<p>Les prédictions sont <b>hors échantillon</b> : chaque station est prédite par un modèle qui
ne l'a jamais vue.{" Le produit officiel, lui, utilise les observations récentes de ces mêmes stations — la comparaison lui est donc favorable sur ce point." if "officiel_mos" in d else " Le MOS officiel de Copernicus n'est pas publié pour ce polluant : le panneau correspondant est absent, il n'a pas été remplacé par une approximation."}</p>
</div>
<footer>Données Copernicus (CAMS Europe, MOS optimisé aux sites d'observation) ·
observations {source_obs} · généré par <code>scripts/heatmap_annuelle.py</code></footer>
</div></div>"""

    # Un nom par polluant : le nom fixe faisait que chaque exécution écrasait la précédente,
    # et le fichier sur disque ne portait plus que le dernier polluant lancé.
    sortie = RACINE / f"reports/figures/heatmap_annuelle_{polluant.lower()}.html"
    sortie.write_text(html, encoding="utf-8")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
