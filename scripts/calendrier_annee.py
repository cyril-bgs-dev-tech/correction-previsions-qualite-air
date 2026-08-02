#!/usr/bin/env python3
"""Le calendrier des signalements pour une année **hors fenêtre d'apprentissage**.

Ce que ce script fait de plus que `calendrier_signalements.py`
---------------------------------------------------------------
Celui-ci prédit 2024, l'année sur laquelle le modèle a été ajusté — par stations exclues, donc
sans fuite spatiale, mais dans la période apprise. Pour 2025 et 2026, le modèle doit être
entraîné **strictement jusqu'au 31/12/2024** puis appliqué sans réajustement. C'est le seul
protocole honnête hors période.

Les limites de couverture, à afficher et non à masquer
------------------------------------------------------
| | 2025 | 2026 |
|---|---|---|
| prévisions CAMS | **janvier → juin** | **juillet seulement** |
| observations métropolitaines | **aucune** — flux rompu fin 2024 | aucune |
| observations occitanes | 12 mois NO₂ et PM2,5 · **O₃ s'arrête en juillet** | NO₂ et PM2,5 |
| MOS officiel | O₃ jusqu'en juin · rien pour NO₂ ni PM2,5 | aucun |

**Le piège que ce script évite.** Un jour sans prévision et un jour sans épisode se ressemblent
si l'on peint les deux en sombre. Les journées hors couverture reçoivent donc une teinte
**distincte** et sont comptées à part : une année à six mois de données ne doit pas se lire
comme une année à six mois calmes.

Usage : python3 scripts/calendrier_annee.py --annee 2025 --polluant O3
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
from calendrier_signalements import (GRANDEUR, NOM_POLLUANT, ORIGINE_SEUIL,  # noqa: E402
                                     PERIMETRES, panneau, selectionner, teinte)
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from comparer_mos_officiel import journalier, lire_officiel  # noqa: E402
from fit_mos import ESPECES, TRANCHES, charger, colonnes_admises  # noqa: E402
from heatmap_annuelle import MEMBRES, PREFIXE, SEUIL  # noqa: E402
from modele_final import REGLE  # noqa: E402


def charger_annee(polluant: str, annee: int, horizon: int = 1) -> pd.DataFrame:
    """Prévisions CAMS et observations occitanes de l'année demandée."""
    court = next(c for c, (p, _) in ESPECES.items() if p == polluant)
    colonne = ESPECES[court][1]
    bas, haut = TRANCHES[horizon]

    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_{annee}*.parquet")))
    if not fichiers:
        raise SystemExit(f"aucune prévision CAMS pour {annee}")
    blocs = []
    for f in fichiers:
        d = pd.read_parquet(f, columns=["station_id", "timestamp_utc", "echeance_h", colonne])
        blocs.append(d[d["echeance_h"].between(bas, haut)])
    prev = pd.concat(blocs, ignore_index=True)
    prev = prev[prev["timestamp_utc"].dt.year == annee]

    obs = pd.read_parquet(
        RACINE / "data/processed/panel_occitanie_complet.parquet",
        filters=[("timestamp_utc", ">=", prev["timestamp_utc"].min()),
                 ("timestamp_utc", "<=", prev["timestamp_utc"].max()),
                 ("polluant", "==", polluant)],
        columns=["station_id", "timestamp_utc", "valeur"]).dropna(subset=["valeur"])

    jeu = prev.merge(obs, on=["station_id", "timestamp_utc"]).rename(columns={colonne: "cams"})
    ctl.exiger_lignes(jeu, 1000, f"appariement {annee}")
    ctl.exiger_couverture(jeu, "valeur", 0.5, f"appariement {annee}")

    for nom in ("geo_features_metropole", "relief_features_metropole",
                "trafic_population_metropole"):
        jeu = jeu.merge(pd.read_parquet(RACINE / f"data/processed/{nom}.parquet"),
                        on="station_id", how="left")
    jeu = jeu.merge(pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station", "lat_wgs84", "lon_wgs84", "altitude"]),
        on="station_id", how="left")

    from aq.models import mos as _mos
    return pd.concat([jeu, _mos.variables_calendaires(jeu["timestamp_utc"])], axis=1)


def joindre_membres(d: pd.DataFrame, court: str, annee: int | None) -> tuple[pd.DataFrame, list]:
    motif = (f"membres_metropole_{court}_*.parquet" if annee is None
             else f"membres_metropole_{court}_{annee}*.parquet")
    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo" / motif)))
    if not fichiers:
        return d, []
    m = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    ctl.exiger_colonnes(m, MEMBRES, "membres")
    return d.merge(m[["station_id", "timestamp_utc"] + MEMBRES],
                   on=["station_id", "timestamp_utc"], how="inner"), MEMBRES


def main(polluant: str, annee: int, perimetre: str) -> int:
    depart = time.time()
    court = PREFIXE[polluant]
    seuil = SEUIL[polluant]
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]

    # ── Apprentissage : strictement jusqu'au 31/12/2024 ───────────────────────
    appris = charger(polluant, 1)
    colonnes = colonnes_admises(appris)
    appris[colonnes] = appris[colonnes].replace([np.inf, -np.inf], 30_000.0)
    appris = appris.dropna(subset=["valeur"])
    appris = appris[appris["timestamp_utc"].dt.year <= 2024]
    appris, membres = joindre_membres(appris, court, None)
    ja = agreger_journalier(appris, colonnes + membres, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    ja["jour"] = pd.to_datetime(ja["jour"])
    passees_a, obs = variables_passees(ja)
    ja = ja.merge(passees_a, on=["station_id", "jour"], how="left").dropna(subset=obs)

    predicteurs = base + obs + membres
    print(f"appris sur {len(ja):,} jours-station jusqu'au {ja['jour'].max():%Y-%m-%d} · "
          f"{len(predicteurs)} prédicteurs", flush=True)


    modele = modele_mos(graine=0)
    modele.fit(ja[predicteurs], ja["obs_jour"] - ja["cams_jour"])

    # ── Application à l'année demandée ────────────────────────────────────────
    d = charger_annee(polluant, annee)
    d[colonnes] = d[colonnes].replace([np.inf, -np.inf], 30_000.0)
    d = d.dropna(subset=["valeur"])
    d, membres_a = joindre_membres(d, court, annee)
    j = agreger_journalier(d, colonnes + membres_a, grandeur)
    j["jour"] = pd.to_datetime(j["jour"])
    passees_r, _ = variables_passees(j)
    j = j.merge(passees_r, on=["station_id", "jour"], how="left")

    # **Dégrader proprement plutôt qu'échouer** — mais en le disant, et en réapprenant sans les
    # variables absentes. Appliquer un modèle entraîné avec les membres d'ensemble à une année
    # qui ne les a pas produirait soit une erreur, soit — pire — des prédictions fondées sur
    # des colonnes remplies par défaut.
    manquants = [c for c in predicteurs if c not in j.columns]
    if manquants:
        print(f"⚠️ absentes de {annee} : {manquants[:8]} — le modèle est **réappris sans "
              f"elles**, et la comparaison à 2024 n'est donc pas à variables égales.",
              flush=True)
        predicteurs = [c for c in predicteurs if c not in manquants]
        modele = modele_mos(graine=0)
        modele.fit(ja[predicteurs], ja["obs_jour"] - ja["cams_jour"])
    complet = j.dropna(subset=predicteurs)
    j["nous"] = np.nan
    j.loc[complet.index, "nous"] = np.clip(
        complet["cams_jour"] + modele.predict(complet[predicteurs]), 0, None)

    archives = sorted((RACINE / "data/raw/cams_mos_officiel").glob(f"{court}_{annee}*.zip"))
    if archives:
        o = pd.concat([journalier(lire_officiel(a), ["officiel_mos"], grandeur)
                       for a in archives], ignore_index=True)
        o["jour"] = pd.to_datetime(o["jour"]).dt.tz_localize(None)
        j["jour"] = j["jour"].dt.tz_localize(None) if j["jour"].dt.tz else j["jour"]
        j = j.merge(o, on=["station_id", "jour"], how="left")

    # **Normaliser le fuseau ici, pas dans une branche.** Une première version ne ramenait
    # `jour` en naïf que si une archive officielle existait ; sans elle — PM2,5 en 2026 — la
    # comparaison avec l'index de dates échouait sans lever, et **toutes** les journées
    # passaient pour hors couverture. Un défaut qui ne se manifeste que dans une branche est
    # celui qu'on découvre le plus tard.
    if getattr(j["jour"].dt, "tz", None) is not None:
        j["jour"] = j["jour"].dt.tz_localize(None)
    j = selectionner(j, perimetre)
    j.to_csv(RACINE / f"reports/calendrier_{annee}_{polluant}.csv", index=False)

    # ── Le rendu ──────────────────────────────────────────────────────────────
    produits = [("obs_jour", "La vérité", "ce que les stations ont mesuré"),
                ("officiel_mos", "Le MOS officiel de Copernicus",
                 "le produit corrigé publié, qui utilise les observations récentes"),
                ("nous", "Notre correction complète",
                 f"appris jusqu'au 31/12/2024, appliqué à {annee} **sans réajustement** — "
                 "aucune fuite ni de station ni de période")]
    produits = [p for p in produits if p[0] in j.columns and j[p[0]].notna().any()]

    index = pd.date_range(f"{annee}-01-01", f"{annee}-12-31", freq="D")
    couverts = set(pd.to_datetime(j["jour"].unique()))
    series, totaux = {}, {}
    for colonne, _, _ in produits:
        s = j[j[colonne] >= seuil].groupby("jour").size().reindex(index, fill_value=0)
        # **Les jours sans donnée deviennent NaN, pas zéro.** Un mois sans prévision peint en
        # sombre se lirait comme un mois calme : c'est exactement l'erreur que la couverture
        # partielle de 2025 rendrait invisible.
        series[colonne] = s.where(pd.Series(index, index=index).isin(couverts))
        totaux[colonne] = int(s[pd.Series(index, index=index).isin(couverts)].sum())

    maximum = max(1.0, float(np.nanmax(series["obs_jour"].to_numpy())))
    n_couverts = len(couverts)
    nom_perimetre, description = PERIMETRES[perimetre]
    origine, detail = ORIGINE_SEUIL[polluant]
    print(f"\n{polluant} {annee} · {nom_perimetre} · {j['station_id'].nunique()} stations · "
          f"{n_couverts} jours couverts sur {len(index)}")
    for colonne, titre, _ in produits:
        s = series[colonne]
        print(f"  {titre:34s} {totaux[colonne]:5d} jours-station · "
              f"{int((s > 0).sum()):3d} jours signalés · pic {int(np.nanmax(s.to_numpy())):3d}",
              flush=True)

    # Vrais positifs par produit : une annonce n'est juste que si l'observation dépasse aussi
    # ce jour-là, à la même station. Sans ce décompte, un produit bruyant paraît meilleur.
    vrai = j["obs_jour"] >= seuil
    justes = {c: int(((j[c] >= seuil) & vrai).sum())
              for c, _, _ in produits if c != "obs_jour"}
    panneaux = "".join(panneau(series[c].fillna(-1), t, s, maximum, totaux[c], annee, justes.get(c))
                       for c, t, s in produits)
    rampe = "".join(f'<span style="background:{teinte(f)}"></span>'
                    for f in np.linspace(0, 1, 60))
    absents = len(index) - n_couverts
    html = f"""<title>{NOM_POLLUANT[polluant]} {annee} — {nom_perimetre}</title>
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
.legende{{display:flex;align-items:center;gap:9px;margin:4px 0 8px;font-size:.76rem;
  color:var(--text-secondary);flex-wrap:wrap}}
.rampe{{display:flex;height:11px;width:200px;border-radius:3px;overflow:hidden}}
.rampe span{{flex:1}}
.puce{{width:13px;height:13px;border-radius:3px;display:inline-block;vertical-align:-2px}}
.alerte{{background:#1f1614;border:1px solid rgba(235,104,52,.4);
  border-left:3px solid #eb6834;border-radius:10px;padding:15px 18px;margin:16px 0}}
p,li{{max-width:70ch}}
footer{{color:var(--text-secondary);font-size:.77rem;border-top:1px solid var(--border);
  margin-top:30px;padding:16px 0 40px}}
</style>
<div class="doc"><div class="shell">
<h1>{NOM_POLLUANT[polluant]} {annee} — {nom_perimetre}</h1>
<p class="lede">Le calendrier des signalements sur <b>{j['station_id'].nunique()} stations</b>
— {description}. Une cellule par jour ; la couleur porte le <b>nombre de stations dépassant
{seuil:.0f} µg/m³</b> en {GRANDEUR[polluant]}.</p>
<p class="lede" style="font-size:.84rem"><b>Origine du seuil</b> — {origine} : {detail}.</p>
<div class="alerte">
<p><b>Couverture partielle : {n_couverts} jours sur {len(index)}.</b> Les
{absents} journées sans prévision CAMS ou sans observation sont peintes en
<span class="puce" style="background:#3a3a37"></span> <b>gris</b>, distinct du noir des
journées sans dépassement. Un mois sans donnée ne doit pas se lire comme un mois calme.</p>
<p><b>Ce test est plus dur que celui de 2024.</b> Le modèle est appris strictement jusqu'au
31/12/2024 et appliqué à {annee} <b>sans réajustement</b> : ni fuite de station, ni fuite de
période.</p>
</div>
<div class="legende"><span>aucune station</span><div class="rampe">{rampe}</div>
<span>{int(maximum)} stations</span>
<span style="margin-left:14px"><span class="puce" style="background:#3a3a37"></span>
 hors couverture</span></div>
{panneaux}
<footer><b>Périmètre :</b> cette correction utilise l'observation de la veille et n'existe donc qu'aux <b>stations instrumentées</b>. Le chiffre du dossier (+23,4 % sur l'ozone) porte sur la version <b>sans observation</b>, qui tourne partout, y compris là où aucune station ne mesure. Les deux sont publiés — ils ne décrivent pas le même produit.<br>{NOM_POLLUANT[polluant]} · seuil {seuil:.0f} µg/m³ en {GRANDEUR[polluant]} ·
données Copernicus et ATMO Occitanie · <code>scripts/calendrier_annee.py</code></footer>
</div></div>"""
    sortie = (RACINE / "reports/figures"
              / f"calendrier_{annee}_{perimetre}_{polluant.lower()}.html")
    sortie.write_text(html, encoding="utf-8")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {sortie.stat().st_size / 1024:.0f} Ko · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--annee", type=int, default=2025)
    p.add_argument("--perimetre", default="occitanie", choices=sorted(PERIMETRES))
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.annee, args.perimetre))
