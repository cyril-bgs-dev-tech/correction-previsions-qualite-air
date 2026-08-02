#!/usr/bin/env python3
"""La comparaison au MOS officiel, sur tous les mois disponibles.

Pourquoi étendre
----------------
Deux mois suffisaient à établir un soupçon, pas un résultat. Le constat central — le MOS
officiel de Copernicus **dégrade** CAMS brut sur le maximum journalier 8 h alors qu'il
l'améliore en horaire — doit tenir sur l'année pour être citable.

Ce que le script mesure, mois par mois puis en agrégé :

- l'écart entre les deux **grandeurs** (horaire et max 8 h), qui est le cœur du diagnostic ;
- notre position face au MOS officiel sur chacune ;
- la **saisonnalité** : le défaut est-il propre à l'été photochimique, ou général ?

Un résultat qui ne vaudrait qu'en juillet serait un cas particulier ; un résultat constant sur
douze mois est une propriété du produit.

Usage : python3 scripts/comparer_mos_officiel_annee.py [--polluant O3]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from comparer_mos_officiel import journalier, lire_officiel  # noqa: E402
from scores_episodes import scores  # noqa: E402

SEUILS = {"O3": 120.0, "NO2": 120.0, "PM25": 25.0}

# **La grandeur réglementaire diffère par polluant**, et c'est tout l'enjeu de la comparaison :
# le maximum 8 h pour l'ozone, le maximum horaire pour le NO₂, la moyenne journalière pour les
# particules. Un post-traitement horaire devrait pénaliser les deux premiers — statistiques
# d'ordre — et rester neutre sur le troisième, qui est une tendance centrale. C'est la
# prédiction que ce script met à l'épreuve.
GRANDEURS = {"O3": "max_8h", "NO2": "max_horaire", "PM25": "moyenne_jour"}
PREFIXES = {"O3": "o3", "NO2": "no2", "PM25": "pm25"}


def main(polluant: str, horizon: int) -> int:
    prefixe = PREFIXES[polluant]
    archives = sorted((RACINE / "data/raw/cams_mos_officiel").glob(f"{prefixe}_2024*.zip"))
    if not archives:
        print("aucune archive mensuelle", file=sys.stderr)
        return 1

    notre = pd.read_csv(RACINE / f"reports/mos_{polluant}_J{horizon}.csv",
                        parse_dates=["timestamp_utc"]).dropna(subset=["observe"])
    notre = notre.rename(columns={"timestamp_utc": "datetime"})

    lignes_h, lignes_j = [], []
    print(f"{'mois':9s} {'n horaire':>10s} │ {'RMSE horaire — brut / officiel / nous':^38s} │"
          f" {'RMSE max 8 h — brut / officiel / nous':^38s}")
    for archive in archives:
        mois = archive.stem.split("_")[1]
        off = lire_officiel(archive)

        # ── Grain horaire ─────────────────────────────────────────────────────
        h = notre.merge(off, on=["station_id", "datetime"], how="inner").dropna(
            subset=["observe", "officiel_mos", "corrige"])
        if len(h) < 1000:
            continue
        rh = {nom: cmp.metriques(h["observe"], h[c])
              for nom, c in (("brut", "officiel_raw"), ("officiel", "officiel_mos"),
                             ("nous", "corrige"))}

        # ── Grain réglementaire ───────────────────────────────────────────────
        grandeur = GRANDEURS[polluant]
        nj = journalier(notre, ["observe", "cams", "corrige"], grandeur)
        oj = journalier(off, ["officiel_mos", "officiel_raw"], grandeur)
        j = nj.merge(oj, on=["station_id", "jour"], how="inner").dropna(
            subset=["observe", "officiel_mos", "corrige"])
        rj = {nom: cmp.metriques(j["observe"], j[c])
              for nom, c in (("brut", "officiel_raw"), ("officiel", "officiel_mos"),
                             ("nous", "corrige"))} if len(j) > 100 else {}

        def _f(d, k):
            return f"{d[k]['rmse']:6.2f}" if d else "   —  "

        print(f"{mois:9s} {len(h):>10,} │ {_f(rh,'brut')} {_f(rh,'officiel')} "
              f"{_f(rh,'nous')}{'':>11s} │ {_f(rj,'brut')} {_f(rj,'officiel')} "
              f"{_f(rj,'nous')}", flush=True)

        lignes_h.append({"mois": mois, "grain": "horaire", "n": len(h),
                         **{f"rmse_{k}": v["rmse"] for k, v in rh.items()},
                         **{f"biais_{k}": v["biais"] for k, v in rh.items()}})
        if rj:
            # L'étiquette porte la **vraie** grandeur : elle diffère par polluant, et un
            # libellé figé ferait lire « max 8 h » là où l'on a calculé un max horaire (NO₂)
            # ou une moyenne journalière (PM2.5).
            lignes_j.append({"mois": mois, "grain": grandeur, "n": len(j),
                             **{f"rmse_{k}": v["rmse"] for k, v in rj.items()},
                             **{f"biais_{k}": v["biais"] for k, v in rj.items()}})

    table = pd.DataFrame(lignes_h + lignes_j)
    table.to_csv(RACINE / f"reports/comparaison_mos_officiel_annee_{polluant}.csv",
                 index=False)

    print("\n" + "=" * 78)
    for grain, sous in table.groupby("grain"):
        n = sous["n"].sum()
        # **Agrégation quadratique**, pondérée par l'effectif : une RMSE est la racine d'une
        # moyenne de carrés, donc √(Σ nₘ·RMSEₘ² / Σ nₘ). La moyenne linéaire employée
        # jusqu'au 31/07/2026 sous-estimait toutes les valeurs, et davantage celles dont les
        # mois sont dispersés — c'est-à-dire CAMS brut plus que nos corrections. Elle
        # sous-estimait donc nos gains. Jumeau du même défaut dans `verite_dossier.py`.
        poids = sous["n"].to_numpy(dtype="float64")
        moy = {k: float(np.sqrt(np.sum(poids * sous[f"rmse_{k}"].to_numpy() ** 2)
                                / poids.sum()))
               for k in ("brut", "officiel", "nous")}
        gain_off = 100 * (1 - moy["officiel"] / moy["brut"])
        gain_nous = 100 * (1 - moy["nous"] / moy["brut"])
        print(f"\n{grain.upper()} · {len(sous)} mois · {n:,} observations")
        print(f"  CAMS brut     {moy['brut']:6.2f}")
        print(f"  MOS officiel  {moy['officiel']:6.2f}  ({gain_off:+.1f} % vs brut)")
        print(f"  NOUS          {moy['nous']:6.2f}  ({gain_nous:+.1f} % vs brut)")
        if gain_off < 0:
            print(f"  → ⚠️ le MOS officiel **dégrade** le brut sur cette grandeur")

    print(f"\nÉcrit : reports/comparaison_mos_officiel_annee_{polluant}.csv", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.horizon))
