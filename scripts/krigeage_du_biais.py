#!/usr/bin/env python3
"""La famille de méthode PREV'AIR — interpoler le biais récent — contre la nôtre.

La question, et pourquoi elle est la plus équitable du dossier
----------------------------------------------------------------
Toutes nos comparaisons opposaient notre correction à un produit **brut**. Celle-ci oppose
deux **méthodes de correction** sur des entrées **identiques** :

* **famille PREV'AIR** — calculer l'écart observation−modèle aux stations sur une fenêtre
  récente, puis l'**interpoler spatialement** vers le point cible. C'est ce que décrivent
  Rouil et al. (BAMS, 2009) et les rapports LCSQA ; la formule exacte n'est pas publique,
  et leur page indique que la méthode a depuis évolué vers de l'apprentissage.
* **la nôtre** — apprendre une fonction du résidu à partir de descripteurs de site.

> Une correction par **interpolation spatiale du biais récent** transfère-t-elle mieux vers
> une station inconnue qu'une **fonction apprise de descripteurs de site** ?

⚠️ Ce que ce script n'est PAS
-------------------------------
**Ce n'est pas PREV'AIR.** Trois obstacles indépendants l'interdisent :

1. leurs CHIMERE et MOCAGE tournent en configuration **nationale** — maille plus fine,
   inventaire français, assimilation ; nous n'avons que les membres **européens à 10 km**
   de l'ensemble CAMS ;
2. leur réseau d'observations au moment de la production n'est pas reconstituable ;
3. la formule exacte et sa fenêtre ne sont pas publiées, et la méthode a changé.

C'est donc leur **famille de méthode**, sur **nos** entrées. Un résultat ici ne dit rien de
leur produit — il dit ce que cette approche vaut à armes égales avec la nôtre.

Le protocole, et ce qu'il autorise
------------------------------------
La station cible est **non instrumentée** : son propre historique est indisponible. Les
stations **voisines**, elles, existent et remontent — c'est la situation opérationnelle
réelle, et c'est ce que PREV'AIR exploite.

Le krigeage dispose donc de **plus** d'information que notre mode « sans capteur local », qui
n'utilise aucune observation. C'est assumé : c'est précisément ce qui rend la question
intéressante.

Les variantes explorées, pour pousser l'approche à son maximum
----------------------------------------------------------------
* **fenêtre** du biais récent : 3, 7, 14, 30 jours ;
* **portée** de l'interpolation : les `k` plus proches voisins, ou tous à moins de `R` km ;
* **pondération** : inverse de la distance à la puissance `p` ;
* **donneurs de même typologie** — un raffinement que la littérature ne décrit pas, mais
  que le projet a des raisons d'essayer : une station trafic se corrige mal depuis une
  station de fond distante de 400 m, ce que la typologie vaut **+8,5 points** sur NO₂.

Usage : python3 scripts/krigeage_du_biais.py --polluant PM10 --horizon 2
Sortie : reports/krigeage_biais_<polluant>_h<n>.csv
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

DECALAGE = 2  # jours — rien de plus récent que la fin de J−2, convention du projet


def matrice_distances(ids: np.ndarray) -> tuple[np.ndarray, pd.DataFrame]:
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "x_l93", "y_l93", "type_station"]).dropna(
                             subset=["x_l93", "y_l93"])
    st = st.drop_duplicates("station_id").set_index("station_id").reindex(ids)
    xy = st[["x_l93", "y_l93"]].to_numpy()
    d = np.sqrt(((xy[:, None, :] - xy[None, :, :]) ** 2).sum(-1)) / 1000.0
    np.fill_diagonal(d, np.inf)   # la station cible n'est jamais son propre donneur
    return d, st


def biais_interpole(pivot_biais: pd.DataFrame, dist: np.ndarray, k: int, rayon: float,
                    p: float, meme_typo: np.ndarray | None) -> np.ndarray:
    """Interpole le biais des stations donneuses vers chaque station, jour par jour.

    Vectorisé par jour : une matrice de poids fixe, appliquée à la matrice
    jour × station des biais récents. La boucle sur les station-jours ferait 10⁵ passages.
    """
    B = pivot_biais.to_numpy(dtype=float)          # jours × stations
    valide = np.isfinite(B)
    W = (dist <= rayon).astype(float)
    if meme_typo is not None:
        W *= meme_typo
    if k:
        # Les k plus proches parmi les donneurs admis ; au-delà, poids nul.
        for i in range(W.shape[0]):
            adm = np.flatnonzero(W[i] > 0)
            if adm.size > k:
                garde = adm[np.argsort(dist[i, adm])[:k]]
                masque = np.zeros(W.shape[1], bool)
                masque[garde] = True
                W[i, ~masque] = 0.0
    with np.errstate(divide="ignore"):
        poids = np.where(W > 0, 1.0 / np.power(dist, p), 0.0)
    num = np.nan_to_num(B) @ poids.T
    den = valide.astype(float) @ poids.T
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, num / den, np.nan)


def gain(o, c, x) -> float:
    rc = float(np.sqrt(np.mean((c - o) ** 2)))
    return 100.0 * (1 - float(np.sqrt(np.mean((x - o) ** 2))) / rc) if rc > 0 else np.nan


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
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")
    dist, st = matrice_distances(ids)
    idx = {s: i for i, s in enumerate(ids)}
    print(f"{polluant} · {len(d):,} jours-station · {len(ids)} stations · "
          f"échéance {'J0' if horizon == 1 else f'J+{horizon - 1}'}", flush=True)

    # ── Le biais par station-jour, décalé de DECALAGE et moyenné sur la fenêtre ──
    d["_biais"] = d["valeur"] - d["cams_jour"]
    piv = d.pivot_table(index="jour", columns="station_id", values="_biais",
                        aggfunc="mean").reindex(columns=ids)
    piv = piv.reindex(pd.date_range(piv.index.min(), piv.index.max(), freq="D"))

    memes = None
    if "type_station" in st:
        t = st["type_station"].fillna("?").to_numpy()
        memes = (t[:, None] == t[None, :]).astype(float)

    # ── Les variantes, pour pousser l'approche à son maximum ────────────────────
    variantes = [("fenêtre 3 j · 50 km · p=2", 3, 0, 50.0, 2.0, None),
                 ("fenêtre 7 j · 50 km · p=2", 7, 0, 50.0, 2.0, None),
                 ("fenêtre 14 j · 50 km · p=2", 14, 0, 50.0, 2.0, None),
                 ("fenêtre 30 j · 50 km · p=2", 30, 0, 50.0, 2.0, None),
                 ("fenêtre 7 j · 100 km · p=2", 7, 0, 100.0, 2.0, None),
                 ("fenêtre 7 j · 200 km · p=1", 7, 0, 200.0, 1.0, None),
                 ("fenêtre 7 j · 5 voisins", 7, 5, 500.0, 2.0, None),
                 ("fenêtre 7 j · 10 voisins", 7, 10, 500.0, 2.0, None),
                 ("fenêtre 7 j · 100 km · MÊME TYPOLOGIE", 7, 0, 100.0, 2.0, "typo"),
                 # Les trois gains observés se cumulent-ils ? Fenêtre longue (30 j > 3 j
                 # de 7,5 points), portée large (200 km > 50 km de 4,8), et même typologie
                 # (+2,3 à rayon égal). Rien ne garantit l'additivité — d'où le test.
                 ("30 j · 200 km · p=1", 30, 0, 200.0, 1.0, None),
                 ("30 j · 200 km · p=1 · MÊME TYPOLOGIE", 30, 0, 200.0, 1.0, "typo"),
                 ("30 j · 300 km · p=1 · MÊME TYPOLOGIE", 30, 0, 300.0, 1.0, "typo"),
                 ("60 j · 200 km · p=1 · MÊME TYPOLOGIE", 60, 0, 200.0, 1.0, "typo")]

    jours_d = pd.to_datetime(d["jour"]).to_numpy()
    lig_jour = pd.Index(piv.index).get_indexer(pd.DatetimeIndex(jours_d))
    col_st = d["station_id"].map(idx).to_numpy()
    o, c = d["valeur"].to_numpy(), d["cams_jour"].to_numpy()

    lignes, meilleur = [], (None, -np.inf, None)
    print(f"\n  {'variante':40s} {'gain/CAMS':>10s} {'couverture':>11s}")
    for nom, fen, k, rayon, p, typo_flag in variantes:
        roul = piv.shift(DECALAGE).rolling(fen, min_periods=max(2, fen // 3)).mean()
        interp = biais_interpole(roul, dist, k, rayon, p,
                                 memes if typo_flag else None)
        corr = interp[lig_jour, col_st]
        pred = np.where(np.isfinite(corr), c + corr, c)   # repli : CAMS brut
        g = gain(o, c, pred)
        couv = 100 * np.isfinite(corr).mean()
        print(f"  {nom:40s} {g:9.2f}% {couv:10.1f} %")
        lignes.append({"polluant": polluant, "horizon": horizon, "methode": nom,
                       "gain_pct": g, "couverture_pct": couv, "n": len(d)})
        if g > meilleur[1]:
            meilleur = (nom, g, pred)

    print(f"\n  → meilleure variante : **{meilleur[0]}** à {meilleur[1]:.2f} %")

    # ── La comparaison aux deux modes de notre approche, mêmes lignes ───────────
    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    mois = np.sort(d["mois"].unique())
    d["_krig"] = meilleur[2] - c        # la correction krigée, comme PRÉDICTEUR

    # ⚠️ Le duel opposait leur méthode POUSSÉE À SON MAXIMUM à la nôtre AMPUTÉE : seule la
    # typologie était branchée, alors que les feux valent +1,48 point et l'ensemble des
    # familles déployables +3,60 (contre +1,64 pour la typologie seule). Une comparaison
    # qui désavantage son propre camp n'est pas plus honnête qu'une qui l'avantage.
    #
    # ERA5 reste dehors : c'est une réanalyse, indisponible à l'heure d'émission. Son gain
    # est un plafond, pas une performance.
    from leviers_36mois import joindre_feux, joindre_membres  # noqa: PLC0415
    debut, fin = d["mois"].min().replace("-", ""), d["mois"].max().replace("-", "")
    familles = list(cols_typo)
    for nom_f, fn in (("feux", lambda x: joindre_feux(x, debut, fin)),
                      ("membres", lambda x: joindre_membres(x, polluant, debut, fin))):
        try:
            d, ajout = fn(d)
            familles += ajout
            couv = 100 * (1 - d[ajout].isna().all(axis=1).mean()) if ajout else 0.0
            print(f"  + {nom_f} : {len(ajout)} colonnes · couverture {couv:.0f} %",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ {nom_f} indisponible : {type(e).__name__}", flush=True)

    modes = {"nous — typologie seule": base + cols_typo,
             "nous — TOUS déployables": base + familles,
             "nous + correction krigée": base + familles + ["_krig"]}
    pred_ml = {k: np.full(len(d), np.nan) for k in modes}
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        m_test, m_train = (d["mois"] == m) & dans, (d["mois"] != m) & ~dans
        te, tr = d[m_test], d[m_train]
        if len(te) < 200 or len(tr) < 1000:
            continue
        w = np.flatnonzero(m_test.to_numpy())
        for nom, colonnes in modes.items():
            pred_ml[nom][w] = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")

    ok = np.ones(len(d), bool)
    for v in pred_ml.values():
        ok &= np.isfinite(v)
    print(f"\n{'═' * 70}\nÀ ARMES ÉGALES — mêmes {ok.sum():,} lignes, station cachée\n"
          f"{'═' * 70}")
    print(f"  {'système':38s} {'gain/CAMS':>10s}")
    # ⚠️ La liste des systèmes est DÉRIVÉE de `modes`, jamais réécrite à la main : renommer
    # un mode et oublier de le répercuter ici a fait planter le lot après 9 minutes de
    # calcul, sur un `KeyError` — au moment précis où le résultat allait s'afficher.
    systemes = [("CAMS brut", c[ok]),
                (f"krigeage du biais ({meilleur[0][:28]})", meilleur[2][ok])]
    systemes += [(nom, pred_ml[nom][ok]) for nom in modes]
    for nom, x in systemes:
        g = gain(o[ok], c[ok], x)
        print(f"  {nom:38s} {g:9.2f}%")
        lignes.append({"polluant": polluant, "horizon": horizon, "methode": f"[duel] {nom}",
                       "gain_pct": g, "n": int(ok.sum())})

    print(f"\n⚠️ Ce n'est PAS PREV'AIR : leurs modèles tournent en configuration nationale,")
    print(f"   nous avons les membres européens à 10 km. C'est leur FAMILLE de méthode,")
    print(f"   sur NOS entrées — la seule comparaison équitable du dossier.")

    sortie = RACINE / f"reports/krigeage_biais_{polluant}_h{horizon}.csv"
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
