#!/usr/bin/env python3
"""Le test final : hors fenêtre d'apprentissage, contre le MOS officiel.

La réserve qu'il lève
---------------------
Nous devançons le MOS officiel de Copernicus sur l'année 2024 — mais notre modèle a **vu**
2024. Sa validation par stations exclues garantit qu'il n'a jamais vu *ces stations*, pas
qu'il ignorait *cette période* : les autres stations lui ont montré les régimes météo, les
épisodes, l'état du forçage.

Le MOS officiel, lui, est réentraîné en continu. La comparaison de 2024 pouvait donc
l'avantager comme nous désavantager — impossible de trancher sans sortir de la période.

Le premier semestre **2025** le permet :

- notre modèle est appris jusqu'au **31/12/2024** — 2025 lui est strictement inconnu ;
- l'ozone occitan reste mesuré jusqu'en **juin 2025** (23 stations, ~15 000 valeurs par mois),
  la rupture du flux EEA n'intervenant qu'en juillet ;
- le MOS officiel couvre la période.

Si l'avantage tient là, aucune objection méthodologique ne subsiste : ni fuite temporelle, ni
station connue, ni période partagée.

**Ce que le test ne dit pas.** L'échantillon devient occitan et bien plus petit (23 stations
contre 239). Un écart faible n'y serait pas concluant ; seul un écart net l'est.

Usage : python3 scripts/test_hors_echantillon_2025.py
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

from aq.eval import comparaison as cmp  # noqa: E402
from aq.models import mos  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import agreger_journalier, moyenne_glissante_8h  # noqa: E402
from comparer_mos_officiel import lire_officiel  # noqa: E402
from fit_mos import ESPECES, TRANCHES, charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from scores_episodes import scores  # noqa: E402


def charger_2025(polluant: str, horizon: int) -> pd.DataFrame:
    """Jeu du 1ᵉʳ semestre 2025, apparié au panel **occitan** — seul à couvrir la période."""
    court = next(c for c, (p, _) in ESPECES.items() if p == polluant)
    colonne = ESPECES[court][1]
    bas, haut = TRANCHES[horizon]

    fichiers = sorted(glob.glob(str(
        RACINE / f"data/processed/meteo/cams_prevision_metropole_{court}_2025*.parquet")))
    if not fichiers:
        raise SystemExit("prévisions 2025 absentes")

    blocs = []
    for f in fichiers:
        d = pd.read_parquet(f, columns=["station_id", "timestamp_utc", "echeance_h", colonne])
        blocs.append(d[d["echeance_h"].between(bas, haut)])
    prev = pd.concat(blocs, ignore_index=True)
    prev = prev[prev["timestamp_utc"] < pd.Timestamp("2025-07-01", tz="UTC")]

    obs = pd.read_parquet(
        RACINE / "data/processed/panel_occitanie_complet.parquet",
        filters=[("timestamp_utc", ">=", prev["timestamp_utc"].min()),
                 ("timestamp_utc", "<", pd.Timestamp("2025-07-01", tz="UTC")),
                 ("polluant", "==", polluant)],
        columns=["station_id", "timestamp_utc", "valeur"],
    ).dropna(subset=["valeur"])

    jeu = prev.merge(obs, on=["station_id", "timestamp_utc"]).rename(
        columns={colonne: "cams"})

    # **Pas d'ERA5 ici, et ce n'est pas un oubli.** Le modèle est entraîné par
    # `fit_mos.charger`, qui ne charge aucune variable météorologique : ses 53 prédicteurs
    # sont la sortie CAMS, le paysage, le relief, le trafic et le calendrier. Les colonnes
    # ERA5 chargées auparavant ici n'entraient donc dans aucun `colonnes_admises` — elles
    # étaient lues, jointes, puis ignorées.
    #
    # Le défaut n'était pas seulement du gaspillage : il imposait un `SystemExit` si ERA5
    # 2025 manquait, bloquant un test qui n'en a pas besoin, et il donnait à lire une chaîne
    # qui semblait consommer une **réanalyse** — donc une information indisponible à l'heure
    # d'émission. C'est exactement l'objection la plus grave qu'on puisse faire à un travail
    # de prévision, et elle était ici fabriquée par du code mort.
    for nom, cols in (("geo_features_metropole", None), ("relief_features_metropole", None),
                      ("trafic_population_metropole", None)):
        jeu = jeu.merge(pd.read_parquet(RACINE / f"data/processed/{nom}.parquet"),
                        on="station_id", how="left")
    jeu = jeu.merge(pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station", "lat_wgs84", "lon_wgs84", "altitude"]),
        on="station_id", how="left")

    from aq.models import mos as _mos

    return pd.concat([jeu, _mos.variables_calendaires(jeu["timestamp_utc"])], axis=1)


def main(polluant: str, horizon: int) -> int:
    depart = time.time()

    # ── Apprentissage : strictement jusqu'à décembre 2024 ──────────────────────
    appris = charger(polluant, horizon)
    colonnes = colonnes_admises(appris)
    appris[colonnes] = appris[colonnes].replace([np.inf, -np.inf], 30_000.0)
    appris = appris.dropna(subset=["valeur"])
    ja = agreger_journalier(appris, colonnes, "max_8h")
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]


    # ⚠️ Les hyperparamètres étaient écrits EN DUR ici (900 arbres, 255 feuilles traduites
    # en max_depth=10) — donc invisibles à toute recherche portant sur `REGLE`, et figés
    # même quand le réglage de référence changeait. Remplacés par le moteur unique.
    modele = modele_mos()
    modele.fit(ja[predicteurs], ja["obs_jour"] - ja["cams_jour"])
    print(f"appris sur {len(ja):,} jours-station, jusqu'au "
          f"{ja['jour'].max():%Y-%m-%d}\n", flush=True)

    # ── Application : 1ᵉʳ semestre 2025, jamais vu ─────────────────────────────
    d = charger_2025(polluant, horizon)
    d[colonnes] = d[colonnes].replace([np.inf, -np.inf], 30_000.0)
    d = d.dropna(subset=["valeur"])
    j = agreger_journalier(d, colonnes, "max_8h")
    j["corrige"] = np.clip(j["cams_jour"] + modele.predict(j[predicteurs]), 0, None)
    print(f"2025 · {len(j):,} jours-station · {j['station_id'].nunique()} stations "
          f"occitanes · {j['jour'].min():%Y-%m-%d} → {j['jour'].max():%Y-%m-%d}", flush=True)

    # ── Le MOS officiel sur la même période ───────────────────────────────────
    archives = sorted((RACINE / "data/raw/cams_mos_officiel").glob("o3_2025*.zip"))
    if not archives:
        print("\n⚠️ MOS officiel 2025 absent — comparaison limitée à CAMS brut")
        officiel_j = None
    else:
        off = pd.concat([lire_officiel(a) for a in archives], ignore_index=True)
        off = off.sort_values(["station_id", "datetime"])
        off["jour"] = off["datetime"].dt.floor("D")
        for c in ("officiel_mos", "officiel_raw"):
            off[c + "_8h"] = moyenne_glissante_8h(off, c, temps="datetime")
        officiel_j = (off.groupby(["station_id", "jour"])
                        .agg(officiel_mos=("officiel_mos_8h", "max"),
                             officiel_raw=("officiel_raw_8h", "max"),
                             n=("datetime", "size")).reset_index())
        officiel_j = officiel_j[officiel_j["n"] >= 18].drop(columns="n")
        j = j.merge(officiel_j, on=["station_id", "jour"], how="left")

    seuil = 120.0
    comparables = j.dropna(subset=["obs_jour", "cams_jour", "corrige"])
    if officiel_j is not None:
        comparables = comparables.dropna(subset=["officiel_mos"])
    print(f"  jours-station comparables : {len(comparables):,}\n", flush=True)

    depasse = (comparables["obs_jour"] >= seuil).to_numpy()
    print(f"{'produit':28s} {'RMSE':>7s} {'biais':>7s} {'R²':>8s} {'POD':>6s} {'CSI':>6s}")
    lignes = []
    candidats = [("CAMS brut", "cams_jour"), ("NOTRE correction", "corrige")]
    if officiel_j is not None:
        candidats.insert(1, ("MOS OFFICIEL Copernicus", "officiel_mos"))
    for nom, col in candidats:
        m = cmp.metriques(comparables["obs_jour"], comparables[col])
        s = (scores(depasse, (comparables[col] >= seuil).to_numpy())
             if depasse.sum() >= 20 else {})
        print(f"{nom:28s} {m['rmse']:7.2f} {m['biais']:+7.2f} {m['r2']:+8.3f} "
              f"{s.get('POD', np.nan):6.3f} {s.get('CSI', np.nan):6.3f}", flush=True)
        lignes.append({"produit": nom, **m, **{f"s_{k}": v for k, v in s.items()}})

    pd.DataFrame(lignes).to_csv(
        RACINE / f"reports/test_hors_echantillon_2025_{polluant}.csv", index=False)

    # Le **détail** jour-station, et pas seulement les agrégats. Le POD ponctuel dépend
    # d'un seuil ; les métriques de rang, elles, n'en emploient aucun et se recalculent
    # depuis les valeurs. Ne garder que les agrégats interdisait cette seconde lecture et
    # obligeait à réapprendre le modèle pour l'obtenir.
    colonnes_detail = ["station_id", "jour", "obs_jour", "cams_jour", "corrige"]
    if officiel_j is not None:
        colonnes_detail += ["officiel_mos", "officiel_raw"]
    comparables[colonnes_detail].to_csv(
        RACINE / f"reports/test_hors_echantillon_2025_detail_{polluant}.csv", index=False)

    print(f"\n{int(depasse.sum())} dépassement(s) de {seuil:.0f} µg/m³ observé(s)")
    print(f"Écrit : reports/test_hors_echantillon_2025_detail_{polluant}.csv "
          f"({len(comparables):,} lignes)")
    print(f"Écrit : reports/test_hors_echantillon_2025_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
