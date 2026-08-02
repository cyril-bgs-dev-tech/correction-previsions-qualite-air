#!/usr/bin/env python3
"""Le calendrier des signalements — trois lectures d'une même année.

Ce que la figure montre
-----------------------
Une cellule par jour de 2024, disposée en calendrier : sept lignes de jours de semaine,
cinquante-trois colonnes de semaines. La couleur porte le **nombre de stations en dépassement
ce jour-là** — la grandeur du signalement, celle qui fait qu'une journée devient un épisode et
non la concentration d'une station isolée.

Trois panneaux, **même échelle** :

1. **la vérité** — ce que les stations ont mesuré ;
2. **le MOS officiel** de Copernicus — ce que le produit gratuit annonçait ;
3. **notre correction complète** — résidu + observations à J−2 + six membres d'ensemble.

Pourquoi ce format plutôt qu'une matrice station × jour
--------------------------------------------------------
Le format station × jour donnait 98 820 cellules par panneau, soit **19 Mo** de vectoriel pour
une limite de publication de 16. Toutes les compressions envisagées dégradaient soit
l'information, soit la finesse de la couleur.

Le calendrier résout le problème par la **grandeur tracée** plutôt que par la compression :
371 cellules par panneau, couleur continue, valeurs exactes, quelques dizaines de kilooctets.
Et il pose la bonne question — *combien de stations ce jour-là*, et non *quelle valeur à cette
station*.

Ce script lit les prédictions déjà calculées par `heatmap_annuelle.py` : il ne réajuste rien.

Usage : python3 scripts/calendrier_signalements.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "scripts"))

from heatmap_annuelle import (ARRETS, GRANDEUR, NOM_POLLUANT,  # noqa: E402,F401
                             SEUIL)

JOURS_SEMAINE = ["lun", "mar", "mer", "jeu", "ven", "sam", "dim"]


def teinte(fraction: float) -> str:
    """Couleur **continue** — interpolation entre les arrêts, sans palier.

    Un jour à trois stations en dépassement et un jour à quatre ne doivent pas tomber dans le
    même aplat : la progression se lit, elle ne se catégorise pas.
    """
    positions = np.array([a for a, _ in ARRETS])
    valeurs = np.array([c for _, c in ARRETS], dtype="float64")
    x = float(np.clip(fraction, 0.0, 1.0)) * positions[-1]
    r, v, b = (np.interp(x, positions, valeurs[:, canal]) for canal in range(3))
    return f"#{int(r):02x}{int(v):02x}{int(b):02x}"


def panneau(serie: pd.Series, titre: str, sous: str, maximum: float,
            total: int, annee: int = 2024, justes: int | None = None) -> str:
    """Un panneau calendaire pour **l'année demandée**.

    ⚠️ L'année était codée en dur à 2024. Réutilisée pour 2025 et 2026, la fonction plaçait les
    cellules aux colonnes 52 à 132 d'un cadre qui n'en compte que 53 : les calendriers hors
    fenêtre étaient entièrement dessinés à côté, et les étiquettes de mois portaient les
    semaines de 2024. Une constante implicite dans une fonction réutilisée est un décalage qui
    attend son heure.
    """
    pas, marge_g, marge_h = 13, 28, 18
    debut = pd.Timestamp(annee, 1, 1)
    premier_lundi = debut - pd.Timedelta(days=debut.weekday())
    # 53 colonnes suffisent pour une année commençant un lundi ; il en faut 54 quand le
    # 1ᵉʳ janvier tombe en fin de semaine et que l'année est bissextile.
    fin = pd.Timestamp(annee, 12, 31)
    semaines = (fin - premier_lundi).days // 7 + 1
    largeur = marge_g + semaines * pas + 6
    hauteur = marge_h + 7 * pas + 4

    cellules = []
    for jour, valeur in serie.items():
        x = marge_g + ((jour - premier_lundi).days // 7) * pas
        y = marge_h + jour.weekday() * pas
        # Trois états, et il faut les distinguer : **hors couverture** (valeur négative,
        # convention du calendrier hors fenêtre), **journée sans dépassement** (zéro), et
        # **journée signalée**. Peindre les deux premiers pareil ferait lire un mois sans
        # données comme un mois calme.
        if valeur < 0:
            couleur = "#3a3a37"
        elif valeur == 0:
            couleur = "#1c1c1a"
        else:
            couleur = teinte(valeur / maximum)
        cellules.append(
            f'<rect x="{x}" y="{y}" width="{pas - 2}" height="{pas - 2}" rx="2" '
            f'fill="{couleur}"><title>{jour:%d/%m/%Y} — '
            f'{"hors couverture" if valeur < 0 else f"{int(valeur)} station(s)"}</title>'
            f'</rect>')

    # **Compter les annonces sans compter les fausses récompense le bruit.** Une première
    # version n'affichait que le total : un produit qui annonce large y paraissait meilleur
    # qu'un produit précis. Sur l'ozone 2025, le MOS officiel annonçait 108 jours-station
    # contre 70 pour nous — mais 34 des siens étaient faux, contre 2 des nôtres.
    if justes is None:
        bilan = f"{total:,} jours-station en dépassement sur l'année"
    else:
        fausses = total - justes
        bilan = (f"{total:,} annoncés · <b>{justes:,} justes</b> · {fausses:,} fausses "
                 f"alertes — précision {100 * justes / max(total, 1):.0f} %")

    reperes = [f'<text x="{marge_g - 5}" y="{marge_h + i * pas + 8}" font-size="7.5" '
               f'text-anchor="end" fill="#898781">{n}</text>'
               for i, n in enumerate(JOURS_SEMAINE) if i % 2 == 0]
    for m in range(1, 13):
        d = pd.Timestamp(annee, m, 1)
        x = marge_g + ((d - premier_lundi).days // 7) * pas
        reperes.append(f'<text x="{x}" y="{marge_h - 6}" font-size="8.5" '
                       f'fill="#c3c2b7">{d:%b}</text>')

    return (f'<div class="panneau"><div class="ptitre">{titre}</div>'
            f'<div class="psub">{sous}</div>'
            f'<svg viewBox="0 0 {largeur} {hauteur}" role="img" aria-label="{titre}">'
            + "".join(cellules) + "".join(reperes)
            + f'</svg><div class="bilan">{bilan}</div></div>')


PERIMETRES = {
    "france": ("France métropolitaine", "les stations du réseau national"),
    "occitanie": ("Occitanie", "les stations de la région, celle que vise le projet"),
}

# **Les trois seuils n'ont pas la même origine réglementaire**, et l'omettre laisserait croire
# à une symétrie qui n'existe pas. L'ozone est le seul dont le seuil retenu vienne d'une valeur
# cible européenne ; les deux autres viennent des bornes de l'indice ATMO.
ORIGINE_SEUIL = {
    "O3": ("valeur cible européenne", "120 µg/m³ en maximum journalier de la moyenne "
           "glissante 8 h — directive 2008/50/CE, à ne pas dépasser plus de 25 jours par an"),
    "NO2": ("borne « mauvais » de l'indice ATMO", "120 µg/m³ en maximum horaire — arrêté du "
            "10 juillet 2020. Le seuil d'<em>information</em> réglementaire est bien plus "
            "haut (200 µg/m³ horaire) et n'est presque jamais atteint en France"),
    "PM25": ("borne « mauvais » de l'indice ATMO", "25 µg/m³ en moyenne journalière — arrêté "
             "du 10 juillet 2020"),
    "PM10": ("seuil d'information réglementaire", "50 µg/m³ en moyenne journalière — arrêté "
             "du 7 avril 2016. C'est le <b>seul des quatre seuils qui déclenche réellement "
             "une procédure préfectorale</b> : 40 des 52 vigilances déclarées en Occitanie "
             "entre janvier 2025 et mars 2026 portent sur ce polluant. La borne « mauvais » "
             "de l'indice ATMO tombe au même endroit"),
}
# Définis dans `heatmap_annuelle`, réexportés ici : `calendrier_annee` les importe de ce
# module, et une seconde définition finirait par diverger de la première.


def selectionner(d: pd.DataFrame, perimetre: str) -> pd.DataFrame:
    """Restreint aux stations du périmètre demandé, en le disant."""
    if perimetre == "france":
        return d
    from aq.ingest import stations as st

    ref = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                          columns=["station_id", "reseau", "active"])
    garder = set(ref[(ref["reseau"] == st.RESEAU_OCCITANIE) & ref["active"]]["station_id"])
    sortie = d[d["station_id"].isin(garder)]
    if sortie.empty:
        raise SystemExit(f"aucune station du périmètre « {perimetre} » dans le jeu")
    return sortie


def main(polluant: str, perimetre: str) -> int:
    seuil = SEUIL[polluant]
    d = pd.read_csv(RACINE / f"reports/heatmap_annuelle_{polluant}.csv",
                    parse_dates=["jour"])
    avant = d["station_id"].nunique()
    d = selectionner(d, perimetre)
    nom_perimetre, description_perimetre = PERIMETRES[perimetre]
    print(f"périmètre « {nom_perimetre} » · {d['station_id'].nunique()} stations "
          f"sur {avant}", flush=True)
    produits = [("obs_jour", "La vérité", "ce que les stations ont mesuré"),
                ("officiel_mos", "Le MOS officiel de Copernicus",
                 "le produit corrigé publié, gratuit, qui utilise les observations récentes"),
                ("nous", "Notre correction complète",
                 "résidu + observations à J−2 + six membres d'ensemble · "
                 "prédite hors échantillon, sur des stations jamais vues")]
    produits = [p for p in produits if p[0] in d.columns]

    series, totaux = {}, {}
    for colonne, _, _ in produits:
        s = d[d[colonne] >= seuil].groupby("jour").size()
        index = pd.date_range("2024-01-01", "2024-12-31", freq="D")
        series[colonne] = s.reindex(index, fill_value=0)
        totaux[colonne] = int(s.sum())

    # **Même échelle sur les trois panneaux**, calée sur la vérité : sans cela, un produit qui
    # n'annonce presque rien paraîtrait aussi intense que la réalité, par simple normalisation.
    maximum = float(series["obs_jour"].max())
    n_stations = int(d["station_id"].nunique())
    origine_libelle, origine_detail = ORIGINE_SEUIL[polluant]
    print(f"{polluant} · maximum observé {maximum:.0f} stations le même jour")
    for colonne, titre, _ in produits:
        s = series[colonne]
        print(f"  {titre:34s} {totaux[colonne]:5d} jours-station · "
              f"{int((s > 0).sum()):3d} jours avec ≥1 signalement · "
              f"pic {int(s.max()):3d}", flush=True)

    # Vrais positifs par produit : une annonce n'est juste que si l'observation dépasse aussi
    # ce jour-là, à la même station. Sans ce décompte, un produit bruyant paraît meilleur.
    vrai = d["obs_jour"] >= seuil
    justes = {c: int(((d[c] >= seuil) & vrai).sum())
              for c, _, _ in produits if c != "obs_jour"}
    panneaux = "".join(panneau(series[c], t, s, maximum, totaux[c], 2024, justes.get(c))
                       for c, t, s in produits)

    # **Un panneau presque noir doit s'expliquer.** Quand aucun produit ne retrouve les
    # épisodes, le lecteur doit savoir qu'il regarde un constat et non une figure ratée — et
    # savoir d'où vient le constat : un événement trop rare pour être appris.
    reference = totaux.get("obs_jour", 0)
    meilleure = max((totaux.get(c, 0) for c, _, _ in produits if c != "obs_jour"),
                    default=0)
    avertissement = ""
    if reference and meilleure / reference < 0.10:
        avertissement = f"""<div class="alerte">
<p><b>Ce n'est pas une figure ratée : c'est le résultat.</b> Sur {reference} jours-station
réellement au-dessus du seuil, le meilleur des deux produits n'en annonce que
{meilleure}. Les panneaux de prévision sont donc presque vides.</p>
<p><b>Pourquoi.</b> L'événement est trop rare pour être appris : sur l'ensemble du corpus, le
NO₂ compte <b>270 dépassements sur 161 637 jours-station</b>, soit 0,17 % — dix fois moins que
l'ozone ou les particules. Et le pic ne dépasse jamais quatre stations le même jour : il n'y a
pas d'épisode régional de NO₂, seulement des dépassements isolés, sur des stations de proximité
qu'une maille de 8 × 11 km ne résout pas.</p>
<p><b>Ce qu'il faut en conclure</b> — et c'est utile à un service : la détection de dépassement
du NO₂ à ce grain n'est pas un problème que le post-traitement peut résoudre. Le NO₂ se surveille
en <em>niveau moyen</em> et en <em>exposition chronique</em>, pas en épisodes. C'est d'ailleurs
là que la correction apporte le plus : <b>+21,9 % de RMSE</b> avec les observations récentes,
le meilleur gain des trois polluants.</p>
</div>"""
    rampe = "".join(f'<span style="background:{teinte(f)}"></span>'
                    for f in np.linspace(0, 1, 60))
    html = f"""<title>{NOM_POLLUANT[polluant]} 2024 — signalements, {nom_perimetre}</title>
<style>
.doc{{--plane:#0d0d0d;--surface-1:#1a1a19;--text-primary:#fff;--text-secondary:#c3c2b7;
  --border:rgba(255,255,255,.12);background:var(--plane);color:var(--text-primary);
  font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.62;margin:0}}
.shell{{max-width:1000px;margin:0 auto;padding:0 clamp(14px,3vw,26px)}}
h1{{font-size:clamp(1.45rem,3.2vw,2rem);letter-spacing:-.02em;margin:1.2em 0 .2em}}
.lede{{color:var(--text-secondary);max-width:68ch;margin:0 0 1.4em}}
.panneau{{background:var(--surface-1);border:1px solid var(--border);border-radius:10px;
  padding:15px 18px;margin:14px 0}}
.ptitre{{font-weight:650;letter-spacing:-.01em;font-size:1.02rem}}
.psub{{color:var(--text-secondary);font-size:.82rem;margin:.2em 0 10px;max-width:70ch}}
svg{{display:block;width:100%;height:auto;overflow:visible}}
.bilan{{color:var(--text-secondary);font-size:.8rem;margin-top:10px;
  border-top:1px solid var(--border);padding-top:8px}}
.legende{{display:flex;align-items:center;gap:9px;margin:4px 0 26px;font-size:.76rem;
  color:var(--text-secondary)}}
.rampe{{display:flex;height:11px;width:210px;border-radius:3px;overflow:hidden}}
.rampe span{{flex:1}}
.alerte{{background:#1f1614;border:1px solid rgba(235,104,52,.4);
  border-left:3px solid #eb6834;border-radius:10px;padding:15px 18px;margin:16px 0}}
.note{{background:var(--surface-1);border:1px solid var(--border);
  border-left:3px solid #eb6834;border-radius:10px;padding:15px 18px;margin:20px 0}}
p,li{{max-width:70ch}}
footer{{color:var(--text-secondary);font-size:.77rem;border-top:1px solid var(--border);
  margin-top:30px;padding:16px 0 40px}}
</style>
<div class="doc"><div class="shell">
<h1>{NOM_POLLUANT[polluant]} 2024 — {nom_perimetre}</h1>
<p class="lede">Le calendrier des signalements sur <b>{n_stations} stations</b> —
{description_perimetre}. Une cellule par jour ; la couleur porte le <b>nombre de stations
dépassant {seuil:.0f} µg/m³</b> en {GRANDEUR[polluant]}, la grandeur qui fait qu'une journée
devient un épisode. Les trois panneaux partagent la <b>même échelle</b>, calée sur la vérité de
ce périmètre.</p>
<p class="lede" style="font-size:.84rem"><b>Origine du seuil</b> — {origine_libelle} :
{origine_detail}.</p>
<div class="legende"><span>aucune station</span><div class="rampe">{rampe}</div>
<span>{int(maximum)} stations</span></div>
{avertissement}
{panneaux}
<div class="note">
<p><b>Ce que la forme montre, et qu'un score ne dit pas.</b> Les épisodes se lisent comme des
grappes estivales. Le produit officiel en annonce une fraction : là où la vérité est rouge, il
reste sombre. Notre correction retrouve la structure — sans l'égaler.</p>
<p>Nos prédictions sont <b>hors échantillon</b> : chaque station est prédite par un modèle qui
ne l'a jamais vue. Le produit officiel, lui, utilise les observations récentes de ces mêmes
stations — la comparaison lui est favorable sur ce point.</p>
</div>
<footer><b>Périmètre :</b> cette correction utilise l'observation de la veille et n'existe donc qu'aux <b>stations instrumentées</b>. Le chiffre du dossier (+23,4 % sur l'ozone) porte sur la version <b>sans observation</b>, qui tourne partout, y compris là où aucune station ne mesure. Les deux sont publiés — ils ne décrivent pas le même produit.<br>{NOM_POLLUANT[polluant]} · seuil {seuil:.0f} µg/m³ en {GRANDEUR[polluant]} ·
données Copernicus (CAMS Europe et MOS optimisé aux sites d'observation) et EEA ·
<code>scripts/calendrier_signalements.py</code></footer>
</div></div>"""
    sortie = RACINE / f"reports/figures/calendrier_{perimetre}_{polluant.lower()}.html"
    sortie.write_text(html, encoding="utf-8")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · "
          f"{sortie.stat().st_size / 1024:.0f} Ko", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--perimetre", default="france",
                   choices=sorted(PERIMETRES))
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.perimetre))
