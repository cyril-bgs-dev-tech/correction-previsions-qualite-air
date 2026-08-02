#!/usr/bin/env python3
"""Quelle part du plafond météo une **prévision** récupère-t-elle ?

La question de la piste
-----------------------
Ajouter la météo ERA5 rend **+7,8 %** sur l'ozone. Mais ERA5 est une **réanalyse** : elle
n'existe pas à l'heure d'émission, et ce chiffre est donc un **plafond**, pas un gain.

L'IFS est une prévision, disponible à l'émission. La question est : *quelle fraction du plafond
survit au passage de la réanalyse à la prévision ?* Une réponse basse enterrerait la piste ;
une réponse haute en ferait le second levier du projet.

Le protocole, et ce qui le rend honnête
----------------------------------------
Les deux jeux sont comparés **sur exactement les mêmes lignes** — le mois où l'IFS est
disponible — et avec **les mêmes variables dérivées**. Comparer ERA5 sur dix-sept mois à l'IFS
sur un seul mesurerait la taille de l'échantillon, pas la qualité de la météo.

Trois jeux :

1. **base** — les 53 prédicteurs habituels ;
2. **+ ERA5** — le plafond, sur ce mois-ci ;
3. **+ IFS** — la prévision, mêmes variables, même agrégation.

**Ce que ce test ne peut pas dire.** Un seul mois d'été : le gain météo est saisonnier, et
juillet est le mois où la photochimie domine. Un résultat positif ici ne se transporte pas
tel quel à l'hiver.

Usage : python3 scripts/apport_ifs.py [--polluant O3] [--mois 202407]
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
from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.ingest import controle as ctl  # noqa: E402
from apport_meteo import evaluer, ic_difference, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

# Les six grandeurs communes aux deux sources, sous leurs noms harmonisés. On s'en tient à
# l'intersection stricte : ajouter à l'IFS ses niveaux de pression — gratuits — avantagerait
# la prévision par le nombre de variables et non par sa qualité.
COMMUNES = ["temperature_c", "point_rosee_c", "rayonnement_w_m2",
            "precipitation_mm", "vent_vitesse_m_s", "vent_direction_deg"]


def journalier(source: pd.DataFrame, prefixe: str) -> tuple[pd.DataFrame, list[str]]:
    """Agrège une source horaire au jour, avec les mêmes statistiques pour les deux."""
    ctl.exiger_colonnes(source, COMMUNES + ["station_id", "timestamp_utc"], prefixe)
    d = source.copy()
    d["jour"] = pd.to_datetime(d["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    radians = np.deg2rad(d["vent_direction_deg"])
    d["vent_sin"] = np.sin(radians) * d["vent_vitesse_m_s"]
    d["vent_cos"] = np.cos(radians) * d["vent_vitesse_m_s"]

    agr = (d.groupby(["station_id", "jour"])
            .agg(**{f"{prefixe}_temp": ("temperature_c", "mean"),
                    f"{prefixe}_temp_max": ("temperature_c", "max"),
                    f"{prefixe}_rosee": ("point_rosee_c", "mean"),
                    f"{prefixe}_ray": ("rayonnement_w_m2", "mean"),
                    f"{prefixe}_ray_max": ("rayonnement_w_m2", "max"),
                    f"{prefixe}_pluie": ("precipitation_mm", "sum"),
                    f"{prefixe}_vent": ("vent_vitesse_m_s", "mean"),
                    f"{prefixe}_vent_max": ("vent_vitesse_m_s", "max"),
                    f"{prefixe}_sin": ("vent_sin", "mean"),
                    f"{prefixe}_cos": ("vent_cos", "mean")})
            .reset_index())
    noms = [c for c in agr.columns if c.startswith(prefixe)]
    ctl.exiger_variation(agr, noms, prefixe)
    return agr, noms


def main(polluant: str, mois: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)

    # ``--mois tous`` prend tous les mois IFS disponibles. Le jeu de colonnes **varie
    # fortement d'un mois à l'autre** — 33 champs bruts en décembre 2024, 99 en novembre —
    # parce que la disponibilité des niveaux de pression change dans l'archive. Les six
    # grandeurs dérivées survivent partout sauf en **février 2024**, qui n'a ni point de
    # rosée ni rayonnement. Un mois incomplet n'est donc pas silencieusement complété : il
    # est écarté, et son nom est dit.
    if mois == "tous":
        candidats = sorted(glob.glob(str(
            RACINE / "data/processed/meteo/ifs_metropole_*.parquet")))
        retenus, ecartes = [], []
        for f in candidats:
            colonnes_f = set(pd.read_parquet(f).columns)
            (retenus if set(COMMUNES) <= colonnes_f else ecartes).append(f)
        if ecartes:
            print("  ⚠️ mois écartés, variables dérivées incomplètes : "
                  + ", ".join(Path(f).stem[-6:] for f in ecartes), flush=True)
        ctl.exiger_lignes(pd.DataFrame({"f": retenus}), 3, "mois IFS retenus")
        ifs = pd.concat([pd.read_parquet(f)[list(COMMUNES) + ["station_id", "timestamp_utc"]]
                         for f in retenus], ignore_index=True)
        etiquette = f"{len(retenus)} mois"
        motifs = [Path(f).stem[-6:] for f in retenus]
    else:
        ifs = pd.read_parquet(RACINE / f"data/processed/meteo/ifs_metropole_{mois}.parquet")
        etiquette, motifs = mois, [mois]
    ifs_j, noms_ifs = journalier(ifs, "ifs")

    fichiers = sorted(f for m in motifs for f in glob.glob(str(
        RACINE / f"data/processed/meteo/era5_metropole_{m}*.parquet")))
    if not fichiers:
        raise SystemExit(f"ERA5 absent pour {mois}")
    # Compter le reçu contre le demandé : un mois ERA5 manquant réduirait l'appariement sans
    # rien lever, et l'on croirait comparer sur la même fenêtre.
    if len(fichiers) < len(motifs):
        trouves = {m for m in motifs if any(m in f for f in fichiers)}
        raise SystemExit(f"ERA5 manquant pour {sorted(set(motifs) - trouves)}")
    era5 = pd.concat([pd.read_parquet(f) for f in fichiers], ignore_index=True)
    era5_j, noms_era5 = journalier(era5, "era5")

    avant = len(j)
    j = j.merge(ifs_j, on=["station_id", "jour"], how="inner").merge(
        era5_j, on=["station_id", "jour"], how="inner")
    ctl.exiger_lignes(j, 500, "jeu apparié")
    print(f"{polluant} · {etiquette} · {avant:,} → {len(j):,} jours-station · "
          f"{j['station_id'].nunique()} stations · {len(noms_ifs)} variables par source",
          flush=True)

    # Contrôle de cohérence entre les deux sources : une prévision à J+1 doit ressembler à la
    # réanalyse du même jour. Un écart énorme signalerait un décalage temporel, pas une erreur
    # de prévision.
    for a, b in (("ifs_temp", "era5_temp"), ("ifs_vent", "era5_vent")):
        r = float(j[[a, b]].corr().iloc[0, 1])
        ecart = float((j[a] - j[b]).mean())
        print(f"  {a} vs {b} : r = {r:+.3f} · écart moyen {ecart:+.2f}", flush=True)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})

    jeux = {"base": base, "+ ERA5 (plafond)": base + noms_era5,
            "+ IFS (prévision)": base + noms_ifs}
    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant)
        print(f"  {nom:20s} RMSE {resultats[nom]['rmse']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    print(f"\n{'jeu':20s} {'RMSE':>7s} {'décile haut':>12s}")
    for nom, r in resultats.items():
        print(f"{nom:20s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f}")

    ref = resultats["base"]["rmse"]
    plafond = ref - resultats["+ ERA5 (plafond)"]["rmse"]
    prevu = ref - resultats["+ IFS (prévision)"]["rmse"]
    print(f"\n{'─' * 74}")
    for nom, gain in (("ERA5 (plafond)", plafond), ("IFS (prévision)", prevu)):
        cle = "+ " + nom.split(" ")[0] + (" (plafond)" if "plafond" in nom else " (prévision)")
        bas, haut = ic_difference(predictions["base"], predictions[cle])
        print(f"{nom:18s} gain {gain:+.3f} µg/m³ ({100 * gain / ref:+.1f} %) · "
              f"IC95 [{bas:+.3f} ; {haut:+.3f}] "
              f"{'✅' if bas > 0 else '— IC contenant zéro'}")

    part = 100 * prevu / plafond if plafond > 0 else float("nan")
    print(f"\n**La prévision récupère {part:.0f} % du plafond de la réanalyse.**")
    if not np.isnan(part):
        if part >= 50:
            print("→ la piste tient : le conditionnement météo survit au passage en prévision.")
        else:
            print("→ **piste affaiblie** : plus de la moitié du plafond vient d'une information "
                  "que\n  la chaîne n'a pas à l'heure d'émission.")
    # L'avertissement décrit la fenêtre **réellement** mesurée. Une version antérieure
    # imprimait « un seul mois d'été » quel que soit le nombre de mois : sur neuf mois, elle
    # affirmait le contraire de ce que le script venait de calculer. Un avertissement faux
    # discrédite le résultat juste qui le précède.
    if len(motifs) == 1:
        print(f"\n⚠️ Un seul mois ({motifs[0]}) : le gain météo est saisonnier. Ne pas "
              f"transporter tel quel aux autres saisons.", flush=True)
    else:
        ete = sum(1 for m in motifs if m[4:] in ("04", "05", "06", "07", "08", "09"))
        print(f"\n⚠️ Fenêtre mesurée : {len(motifs)} mois ({motifs[0]}–{motifs[-1]}), dont "
              f"{ete} en saison photochimique (avril–septembre).\n   Le gain météo est "
              f"saisonnier : ce chiffre est une moyenne sur cette fenêtre, pas une valeur "
              f"transportable\n   mois par mois.", flush=True)

    pd.DataFrame(resultats).T.to_csv(RACINE / f"reports/apport_ifs_{polluant}_{mois}.csv")
    print(f"\nÉcrit : reports/apport_ifs_{polluant}_{mois}.csv · {time.time() - depart:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--mois", default="tous",
                   help="un mois AAAAMM, ou 'tous' pour l'ensemble disponible")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.mois, args.plis))
