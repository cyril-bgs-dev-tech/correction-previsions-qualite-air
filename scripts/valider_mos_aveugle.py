"""Validation en double aveugle du MOS, reproductible depuis le dépôt.

Usage : python scripts/valider_mos_aveugle.py [--polluant O3] [--horizon 1]
Sorties : reports/validation_aveugle_{polluant}.csv et les prédictions hors échantillon

**Pourquoi ce script existe.** Les chiffres de validation temporelle et de double
aveugle figuraient dans les rapports sans script versionné pour les produire — ils
n'étaient donc pas recalculables depuis le dépôt. Une relecture adverse l'a relevé, à
juste titre : le chiffre le plus crédible du projet était le moins reproductible.

**Les trois épreuves, de dureté croissante.** Chacune cache au modèle quelque chose de
différent, et la dernière est la seule qui ressemble à un déploiement :

| Épreuve | Ce qui est caché | Ce qu'elle mesure |
|---|---|---|
| spatiale | des stations entières | prédire là où l'on ne mesure pas |
| temporelle | un mois entier | prédire une période non apprise |
| double aveugle | les deux à la fois | les deux difficultés cumulées |

La variabilité entre plis est calculée et publiée : un gain moyen sans dispersion ne dit
pas si le signe tient d'un pli à l'autre.
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
from aq.models import mos  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402


def _ajuster_et_predire(entrainement, test, colonnes, graine=0):
    """Apprend le résidu sur l'entraînement, l'applique au test."""
    modele = mos._modele(graine)
    modele.fit(entrainement[colonnes],
               entrainement["valeur"] - entrainement["cams"])
    return np.clip(test["cams"].to_numpy() + modele.predict(test[colonnes]), 0, None)


def epreuve(nom: str, jeu: pd.DataFrame, colonnes: list[str],
            plis: list[tuple[pd.Series, pd.Series]]) -> dict:
    """Exécute une épreuve pli par pli et renvoie moyenne **et dispersion**."""
    gains, blocs = [], []
    for masque_tr, masque_te in plis:
        entrainement = jeu[masque_tr].dropna(subset=["valeur"])
        test = jeu[masque_te].dropna(subset=["valeur"])
        if entrainement.empty or test.empty:
            continue
        predit = _ajuster_et_predire(entrainement, test, colonnes)
        m_cams = cmp.metriques(test["valeur"], test["cams"])
        m_mos = cmp.metriques(test["valeur"], predit)
        gains.append(100 * (1 - m_mos["rmse"] / m_cams["rmse"]))
        blocs.append(test.assign(corrige=predit))

    ensemble = pd.concat(blocs, ignore_index=True)
    m_cams = cmp.metriques(ensemble["valeur"], ensemble["cams"])
    m_mos = cmp.metriques(ensemble["valeur"], ensemble["corrige"])
    return {
        "epreuve": nom, "n_plis": len(gains), "n_test": len(ensemble),
        "rmse_cams": m_cams["rmse"], "rmse_mos": m_mos["rmse"],
        "r2_cams": m_cams["r2"], "r2_mos": m_mos["r2"],
        "gain_pct": 100 * (1 - m_mos["rmse"] / m_cams["rmse"]),
        "gain_min_pli": min(gains), "gain_max_pli": max(gains),
        "gain_ecart_type": float(np.std(gains)),
    }


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"]).reset_index(drop=True)
    jeu["mois"] = pd.to_datetime(jeu["timestamp_utc"]).dt.strftime("%Y%m")

    stations = np.array(sorted(jeu["station_id"].unique()))
    mois = sorted(jeu["mois"].unique())
    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · {len(stations)} stations · "
          f"mois {mois}", flush=True)
    if len(mois) < 2:
        raise SystemExit("Au moins deux mois sont nécessaires pour l'épreuve temporelle.")

    rng = np.random.default_rng(0)
    groupes = np.array_split(rng.permutation(stations), n_plis)

    # 1. Spatiale — stations entières exclues.
    plis_spatiaux = [(~jeu["station_id"].isin(g), jeu["station_id"].isin(g))
                     for g in groupes]

    # 2. Temporelle — un mois entier exclu, toutes stations confondues.
    plis_temporels = [(jeu["mois"] != m, jeu["mois"] == m) for m in mois]

    # 3. Double aveugle — le mois exclu ET un cinquième des stations exclues.
    #    C'est la seule épreuve qui ressemble à un déploiement : période nouvelle,
    #    lieux non instrumentés.
    plis_aveugles = []
    for i, m in enumerate(mois):
        exclues = groupes[i % len(groupes)]
        plis_aveugles.append((
            (jeu["mois"] != m) & (~jeu["station_id"].isin(exclues)),
            (jeu["mois"] == m) & (jeu["station_id"].isin(exclues)),
        ))

    resultats = [
        epreuve("spatiale", jeu, colonnes, plis_spatiaux),
        epreuve("temporelle", jeu, colonnes, plis_temporels),
        epreuve("double aveugle", jeu, colonnes, plis_aveugles),
    ]

    table = pd.DataFrame(resultats)
    print(f"\n{'épreuve':16s} {'n test':>9s} {'RMSE CAMS':>10s} {'RMSE MOS':>9s} "
          f"{'gain':>7s} {'étendue entre plis':>22s}")
    for r in resultats:
        print(f"{r['epreuve']:16s} {r['n_test']:>9,} {r['rmse_cams']:10.2f} "
              f"{r['rmse_mos']:9.2f} {r['gain_pct']:+6.1f} % "
              f"{r['gain_min_pli']:+8.1f} à {r['gain_max_pli']:+.1f} % "
              f"(σ {r['gain_ecart_type']:.1f})")

    sortie = RACINE / f"reports/validation_aveugle_{polluant}.csv"
    table.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.name}")
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    parseur.add_argument("--plis", type=int, default=3)
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
