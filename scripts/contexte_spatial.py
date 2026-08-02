#!/usr/bin/env python3
"""Le modèle ne voit qu'une maille — lui donner le champ CAMS autour d'elle.

Le trou que ce script comble
------------------------------
Un épisode de pollution est **spatialement cohérent par nature** : il couvre des dizaines à
des centaines de kilomètres, il arrive par un bord du domaine, il progresse. Or notre
modèle ne reçoit que la valeur CAMS de **sa propre maille de 10 km**. Il ignore
complètement que le modèle amont prévoit des valeurs élevées à 80 km au vent.

Le diagnostic du 02/08 a montré où était le problème, et ce n'est pas là où on le croyait :

    rang percentile moyen les jours de dépassement PM10
      CAMS brut       0,847      (0,500 = aucune information)
      notre modèle    0,871
    amplitude médiane prédite ces jours-là
      observé         56,4 µg/m³
      notre modèle    28,6        soit 51 % de l'observé

**Le classement est bon, l'amplitude est divisée par deux.** Une cartographie de quantiles
corrige l'amplitude — elle fait passer les détections de 39 à 103 — mais elle **déplace le
système le long de sa frontière** sans améliorer son pouvoir de discrimination.

Pour déplacer la frontière elle-même, il faut du **classement en plus**. Et le contexte
spatial est la seule information d'échelle épisodique dont nous disposons et que le modèle
n'a jamais reçue.

Ce que ce script construit
---------------------------
Pour chaque station-jour, et pour trois rayons — 50, 100 et 200 km :

* `cams_vois_moy_R`   moyenne du CAMS prévu chez les voisins, **station exclue**
* `cams_vois_max_R`   maximum chez les voisins — un épisode qui arrive se voit d'abord
                      chez le voisin le plus exposé, pas dans la moyenne
* `cams_ecart_vois_R` écart entre la station et ses voisins : positif = pic local,
                      négatif = la station est en retrait d'un épisode régional
* `cams_n_vois_R`     nombre de voisins — pour que le modèle sache quand l'information
                      est mince (stations isolées de montagne)

⚠️ **Aucune fuite possible** : toutes ces variables sont des **prévisions CAMS**, connues
au moment de l'émission au même titre que la maille de la station. Aucune observation n'y
entre.

Usage : python3 scripts/contexte_spatial.py --polluant PM10 --horizon 2
Sortie : reports/contexte_spatial_<polluant>_h<n>.csv
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
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)

RAYONS_KM = (50.0, 100.0, 200.0)
SEUILS = {"PM10": 50.0, "PM25": 50.0, "O3": 120.0, "NO2": 200.0}


def variables_voisinage(d: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Agrégats du champ CAMS autour de chaque station, par rayon.

    Le calcul est vectorisé par **jour** : on pivote en matrice jour × station, puis on
    applique les masques de voisinage. Boucler sur les station-jours ferait 10⁵ passages
    là où trois produits matriciels suffisent — c'est la règle 2 appliquée au calcul
    plutôt qu'à la lecture.
    """
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "x_l93", "y_l93"]).dropna()
    st = st[st["station_id"].isin(d["station_id"].unique())].drop_duplicates("station_id")
    st = st.sort_values("station_id").reset_index(drop=True)
    ids = st["station_id"].to_numpy()
    xy = st[["x_l93", "y_l93"]].to_numpy()
    dist = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1)) / 1000.0
    np.fill_diagonal(dist, np.inf)          # la station n'est pas sa propre voisine

    m = d.pivot_table(index="jour", columns="station_id", values="cams_jour",
                      aggfunc="mean")
    m = m.reindex(columns=ids)              # même ordre que la matrice de distances
    A = m.to_numpy(dtype=float)             # jour × station
    valide = np.isfinite(A)

    noms, morceaux = [], {}
    for R in RAYONS_KM:
        W = (dist <= R)                     # station × voisines
        n = W.sum(1)
        print(f"    rayon {R:5.0f} km · voisins par station : médiane {np.median(n):.0f} · "
              f"{int((n == 0).sum())} station(s) isolée(s)", flush=True)
        # Moyenne : somme des voisins valides ÷ nombre de voisins valides, par jour.
        S = np.nan_to_num(A) @ W.T
        C = valide.astype(float) @ W.T
        with np.errstate(invalid="ignore", divide="ignore"):
            moy = np.where(C > 0, S / C, np.nan)
        # Maximum : par station, sur ses voisines seulement.
        mx = np.full_like(A, np.nan)
        for i in range(len(ids)):
            j = np.flatnonzero(W[i])
            if j.size:
                mx[:, i] = np.nanmax(np.where(valide[:, j], A[:, j], -np.inf), axis=1)
        mx[~np.isfinite(mx)] = np.nan
        for nom, val in ((f"cams_vois_moy_{R:.0f}", moy), (f"cams_vois_max_{R:.0f}", mx),
                         (f"cams_ecart_vois_{R:.0f}", A - moy)):
            morceaux[nom] = pd.DataFrame(val, index=m.index, columns=ids)
            noms.append(nom)
        morceaux[f"cams_n_vois_{R:.0f}"] = pd.DataFrame(
            np.broadcast_to(C[0] if C.ndim == 1 else C, A.shape),
            index=m.index, columns=ids)
        noms.append(f"cams_n_vois_{R:.0f}")

    plat = None
    for nom, tab in morceaux.items():
        s = tab.stack().rename(nom).reset_index()
        s.columns = ["jour", "station_id", nom]
        plat = s if plat is None else plat.merge(s, on=["jour", "station_id"], how="outer")
    return plat, noms


def gain(o, c, p) -> float:
    rc = float(np.sqrt(np.mean((c - o) ** 2)))
    return 100.0 * (1 - float(np.sqrt(np.mean((p - o) ** 2))) / rc) if rc > 0 else np.nan


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
    from apport_observation_veille import variables_passees  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    mem, noms_mem = variables_passees(d.rename(columns={"valeur": "obs_jour"}))
    mem["jour"] = pd.to_datetime(mem["jour"]).dt.tz_localize(None)
    d = d.merge(mem, on=["station_id", "jour"], how="left")

    print(f"{polluant} · échéance {'J0' if horizon == 1 else f'J+{horizon - 1}'} · "
          f"{len(d):,} jours-station\n  contexte spatial :", flush=True)
    vois, noms_vois = variables_voisinage(d)
    avant = len(d)
    d = d.merge(vois, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure voisinage : {avant:,} → {len(d):,}")
    couv = 100 * (1 - d[noms_vois].isna().all(axis=1).mean())
    print(f"    {len(noms_vois)} variables · couverture {couv:.1f} %", flush=True)
    if couv < 90:
        raise SystemExit(f"couverture {couv:.0f} % — voisinage mal calculé, ne pas conclure")

    rng = np.random.default_rng(GRAINE)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_spa)
    mois = np.sort(d["mois"].unique())

    variantes = {"sans contexte": base + cols_typo + noms_mem,
                 "AVEC contexte spatial": base + cols_typo + noms_mem + noms_vois}
    pred = {k: np.full(len(d), np.nan) for k in variantes}
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        m_test, m_train = (d["mois"] == m) & dans, (d["mois"] != m) & ~dans
        te, tr = d[m_test], d[m_train]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(m_test.to_numpy())
        for nom, colonnes in variantes.items():
            pred[nom][idx] = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")

    ok = np.isfinite(pred["sans contexte"]) & np.isfinite(pred["AVEC contexte spatial"])
    e = d[ok].reset_index(drop=True)
    o, c = e["valeur"].to_numpy(), e["cams_jour"].to_numpy()
    S = SEUILS[polluant]
    v = o > S
    N = int(v.sum())

    print(f"\n{'═' * 74}\n{polluant} · {len(e):,} jours-station · {N} dépassements > "
          f"{S:.0f} µg/m³\n{'═' * 74}")
    print(f"  {'variante':24s} {'gain RMSE':>10s} {'rang moyen':>11s} "
          f"{'détections@N':>13s}")
    lignes = []
    for nom in variantes:
        p = pred[nom][ok]
        g = gain(o, c, p)
        # Rang moyen des jours de dépassement : mesure PURE de discrimination,
        # indépendante de l'échelle — c'est elle que le contexte spatial doit bouger.
        rang = float(pd.Series(p).rank(pct=True).to_numpy()[v].mean())
        seuil_qm = np.quantile(p, 1 - N / len(p))
        tp = int((v & (p >= seuil_qm)).sum())
        print(f"  {nom:24s} {g:9.2f}% {rang:11.4f} {tp:10d}/{N}")
        lignes.append({"polluant": polluant, "horizon": horizon, "variante": nom,
                       "gain_rmse_pct": g, "rang_moyen_depassements": rang,
                       "detections_au_budget": tp, "n_depassements": N, "n": len(e)})
    r0, r1 = lignes[0]["rang_moyen_depassements"], lignes[1]["rang_moyen_depassements"]
    t0, t1 = lignes[0]["detections_au_budget"], lignes[1]["detections_au_budget"]
    print(f"\n  Discrimination : {r0:.4f} → {r1:.4f} ({r1 - r0:+.4f})")
    print(f"  Détections à budget égal : {t0} → {t1} ({100 * (t1 / max(t0, 1) - 1):+.1f} %)")
    if r1 <= r0:
        print(f"  ⚠️ Le contexte spatial n'améliore PAS la discrimination. À dire tel quel.")

    sortie = RACINE / f"reports/contexte_spatial_{polluant}_h{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
