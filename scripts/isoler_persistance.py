#!/usr/bin/env python3
"""Le gain de la mémoire locale est-il autre chose que de la persistance ?

La question, et pourquoi elle précède toute publication
--------------------------------------------------------
Ajouter les observations antérieures de la station rapporte **+14,08 points sur NO₂** et
**+13,35 sur O₃** en double aveugle. C'est le levier le plus fort du projet.

Mais une ablation « sans / avec » mesure l'apport du **bloc entier**. Elle ne dit pas ce
qui revient à la persistance nue — répéter l'avant-veille — ni à une correction de biais
élémentaire, ni au modèle. Or la persistance est le témoin que FAIRMODE impose : son
`MQI_f` compare la RMSE de la prévision à celle d'une persistance dépendant de l'échéance.

Tant que ce test manque, la phrase honnête est : *« le bloc de mémoire locale apporte
14 points ; sa part au-delà d'une persistance ou d'une correction de biais élémentaire
n'est pas isolée. »*

Les six prédicteurs comparés, sur **exactement les mêmes lignes**
------------------------------------------------------------------
Le décalage est de **2 jours par rapport à la cible**, et c'est la convention de FAIRMODE
elle-même : pour l'échéance J+1, la persistance du jour `i` utilise `O[i−2]`. La prévision
couvrant le jour T est émise en T−1 ; la dernière journée complète est donc T−2.

    P0  = O[t−2]                              persistance nue — le témoin FAIRMODE
    P1  = CAMS[t] + (O[t−2] − CAMS[t−2])      dernier résidu reporté
    P3  = CAMS[t] + moyenne(O−CAMS, t−2..t−4) biais récent, 3 jours
    P7  = CAMS[t] + moyenne(O−CAMS, t−2..t−8) biais récent, 7 jours
    ML0 = modèle SANS mémoire locale
    ML1 = modèle AVEC mémoire locale

`P1`, `P3` et `P7` sont des corrections de biais **sans apprentissage** : elles ne coûtent
rien à maintenir. Si `ML1` ne les bat pas nettement, le dossier doit annoncer une moyenne
glissante, pas un modèle.

Ce que le résultat décidera
----------------------------
* `ML1 ≫ P7` — la mémoire locale sert d'entrée à un modèle qui en fait autre chose qu'un
  report de biais. Le gain est un vrai gain de modélisation.
* `ML1 ≈ P7` — le modèle n'ajoute rien à une moyenne glissante. Il faut le dire, et
  probablement livrer la moyenne glissante.
* `P0` proche de `ML1` — le gain est de la persistance déguisée. C'est le scénario que ce
  script existe pour exclure ou avouer.

⚠️ Toutes les lignes sont **restreintes à l'intersection** où les six prédicteurs
existent. Comparer sur des sous-échantillons différents avantagerait celui qui manque les
jours difficiles — c'est la faute que le référentiel LCSQA évite par sa règle de couples
valides.

Usage : python3 scripts/isoler_persistance.py --polluant NO2
Sortie : reports/persistance_<polluant>.csv
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster,
    charger, colonnes_admises,
)

DECALAGE = 2  # jours, par rapport à la CIBLE — convention FAIRMODE pour l'échéance J+1


def references(d: pd.DataFrame) -> pd.DataFrame:
    """Les quatre prédicteurs sans apprentissage, calculés par station.

    Le décalage est appliqué sur une série **réindexée au jour calendaire**. Un `shift(2)`
    sur des lignes trouées prendrait « deux enregistrements plus haut », qui peut dater de
    trois semaines si la station a été en panne.
    """
    morceaux = []
    for station, g in d.groupby("station_id", sort=False):
        g = g.set_index("jour").sort_index()
        plein = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
        obs_p = plein["valeur"].shift(DECALAGE)
        res = (plein["valeur"] - plein["cams_jour"]).shift(DECALAGE)
        out = pd.DataFrame(index=plein.index)
        out["P0"] = obs_p
        out["P1"] = plein["cams_jour"] + res
        out["P3"] = plein["cams_jour"] + res.rolling(3, min_periods=2).mean()
        out["P7"] = plein["cams_jour"] + res.rolling(7, min_periods=3).mean()
        out["station_id"] = station
        morceaux.append(out.reset_index(names="jour"))
    return pd.concat(morceaux, ignore_index=True)


def variables_memoire(d: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Le bloc de mémoire locale donné au modèle — identique à `leviers_36mois`."""
    from apport_observation_veille import variables_passees  # noqa: PLC0415
    j = d.rename(columns={"valeur": "obs_jour"})
    p, noms = variables_passees(j)
    p["jour"] = pd.to_datetime(p["jour"]).dt.tz_localize(None)
    return p, noms


def rmse(o, x) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")

    ref = references(d)
    mem, noms_mem = variables_memoire(d)
    avant = len(d)
    d = d.merge(ref, on=["station_id", "jour"], how="left")
    d = d.merge(mem, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure : {avant:,} → {len(d):,} lignes")

    # ── L'intersection : toutes les méthodes jugées sur les MÊMES lignes ───────────
    besoin = ["P0", "P1", "P3", "P7", "cams_jour", "valeur"]
    complet = d[besoin].notna().all(axis=1)
    print(f"{polluant} · {len(d):,} jours-station · "
          f"{complet.sum():,} avec les six prédicteurs ({100 * complet.mean():.1f} %)",
          flush=True)
    d = d[complet].reset_index(drop=True)

    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_spa)
    mois = np.sort(d["mois"].unique())
    plis = []
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        plis.append(((d["mois"] == m) & dans, (d["mois"] != m) & ~dans))

    pred_ml = {"ML0": np.full(len(d), np.nan), "ML1": np.full(len(d), np.nan)}
    for m_test, m_train in plis:
        te, tr = d[m_test], d[m_train]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(m_test.to_numpy())
        pred_ml["ML0"][idx] = ajuster(DEFAUT, tr, te, base + cols_typo, "cams_jour")
        pred_ml["ML1"][idx] = ajuster(DEFAUT, tr, te, base + cols_typo + noms_mem,
                                      "cams_jour")

    vus = np.isfinite(pred_ml["ML0"]) & np.isfinite(pred_ml["ML1"])
    d, o = d[vus].reset_index(drop=True), d["valeur"].to_numpy()[vus]
    c = d["cams_jour"].to_numpy()
    r_cams = rmse(o, c)

    lignes = []
    print(f"\n{'═' * 74}\nMÊMES {len(d):,} LIGNES · RMSE CAMS brut = {r_cams:.3f} µg/m³\n"
          f"{'═' * 74}")
    print(f"  {'méthode':34s} {'RMSE':>8s} {'gain/CAMS':>10s} {'apprentissage'}")
    candidats = [("CAMS brut", c, "aucun"),
                 ("P0 · persistance nue (J−2)", d["P0"].to_numpy(), "aucun"),
                 ("P1 · dernier résidu reporté", d["P1"].to_numpy(), "aucun"),
                 ("P3 · biais récent 3 jours", d["P3"].to_numpy(), "aucun"),
                 ("P7 · biais récent 7 jours", d["P7"].to_numpy(), "aucun"),
                 ("ML0 · modèle SANS mémoire", pred_ml["ML0"][vus], "LightGBM"),
                 ("ML1 · modèle AVEC mémoire", pred_ml["ML1"][vus], "LightGBM")]
    for nom, x, appr in candidats:
        r = rmse(o, x)
        g = 100 * (1 - r / r_cams)
        print(f"  {nom:34s} {r:8.3f} {g:9.2f}% {appr}")
        lignes.append({"polluant": polluant, "methode": nom, "rmse": r,
                       "gain_vs_cams_pct": g, "apprentissage": appr, "n": len(d)})

    r7, r1, r0 = (rmse(o, pred_ml["ML1"][vus]), rmse(o, pred_ml["ML0"][vus]),
                  rmse(o, d["P7"].to_numpy()))
    print(f"\n  ── Ce que la mémoire locale ajoute VRAIMENT ──")
    print(f"  ML1 contre ML0 (bloc entier)          : {100 * (1 - r7 / r1):+6.2f} %")
    print(f"  ML1 contre P7  (au-delà du biais glissant) : {100 * (1 - r7 / r0):+6.2f} %")
    print(f"  P7  contre CAMS (biais glissant seul) : {100 * (1 - r0 / r_cams):+6.2f} %")
    if r7 >= r0:
        print(f"\n  ⚠️ Le modèle NE BAT PAS la moyenne glissante. À dire tel quel.")

    sortie = RACINE / f"reports/persistance_{polluant}_h{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=1)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
