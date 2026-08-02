#!/usr/bin/env python3
"""« Station exclue » ne veut pas dire « information exclue » — mesurer l'écart.

Le défaut de validation que ce script existe pour chiffrer
----------------------------------------------------------
Tout le projet valide par **stations entièrement exclues**, avec des plis construits par
``i % n_plis`` sur l'identifiant de station trié. C'est arbitraire, et surtout **non bloqué
spatialement**. Mesuré sur les 813 stations de métropole :

* plus proche voisin : **médiane 2,4 km**, premier quartile 1,0 km ;
* **79 %** des stations ont une voisine à moins de 10 km ;
* **72 %** ont leur plus proche voisine **dans un autre pli**.

La maille CAMS fait **8 × 11 km**. Une station de test à 2,4 km d'une station d'entraînement
partage donc la même maille de prévision, presque le même relief, le même trafic et la même
météo. Le modèle n'a pas besoin de généraliser : il lui suffit de reconnaître le voisin.

Cela n'invalide aucune **comparaison** — tous les produits sont évalués sur les mêmes plis —
mais cela rend le chiffre **absolu** optimiste pour l'usage qui est la revendication propre du
projet : *prédire là où rien ne mesure*.

Les trois protocoles comparés
-----------------------------
1. ``i % n_plis`` — le protocole actuel, référence.
2. **blocs spatiaux** — les stations sont regroupées par k-moyennes sur leurs coordonnées
   Lambert-93, puis des **grappes entières** partent en test. Une station de test n'a alors
   aucune voisine proche dans l'entraînement.
3. **blocs à distance garantie** — variante plus dure : on retire de l'entraînement toute
   station à moins de ``rayon`` km d'une station de test (*buffered leave-location-out*).
   C'est le protocole que la littérature spatiale recommande, et le seul qui réponde
   exactement à la question posée.

Ce que le résultat voudra dire
------------------------------
L'écart entre 1 et 3 **est** l'optimisme du protocole actuel. S'il est petit, la validation
du projet tient et on peut le dire avec ce chiffre en main. S'il est grand, le nombre publié
décrit une interpolation entre stations voisines, pas une extrapolation à un lieu neuf — et
il faut alors publier les deux.

Usage : python3 scripts/validation_bloquee.py [--polluant O3] [--plis 3] [--rayon 25]
Sortie : reports/validation_bloquee_{polluant}.csv
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

from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402

from aq.ingest.controle import ControleEchec, exiger_colonnes  # noqa: E402

GRAINE = 20260731


def modele():
    """Le moteur unique du projet — voir `aq.models.moteur`.

    ⚠️ **Deux affirmations de ce docstring étaient fausses**, corrigées le 02/08/2026 :

    * « le projet a mesuré XGB ≈ CatBoost ≈ LightGBM à ±0,3 point » — **aucune mesure de ce
      type n'existe dans le dépôt**. Le seul banc, `comparaison_algorithmes_O3.csv`, oppose
      LightGBM, Ridge et forêt aléatoire ; XGBoost n'y figure pas. L'affirmation circulait
      de docstring en docstring sans source ;
    * « les hyperparamètres sont ceux de `REGLE`, traduits terme à terme » — la traduction
      **jetait `num_leaves=255`**, le paramètre de capacité, et le remplaçait par un
      `max_depth=10` écrit en dur. Ce n'est pas le même modèle.

    Le choix du moteur **porte** d'ailleurs le résultat, mesuré en double aveugle sur
    l'ozone : la capacité y dégrade le gain de façon monotone, de +3,31 % à 400 arbres
    jusqu'à −1,07 % à 3 000.
    """
    return modele_mos(graine=GRAINE)


def coordonnees(ids: np.ndarray) -> pd.DataFrame:
    """Les coordonnées projetées des stations, en kilomètres."""
    s = pd.read_parquet(RACINE / "data/processed/stations.parquet")
    exiger_colonnes(s, ["station_id", "x_l93", "y_l93"], "stations")
    s = s.drop_duplicates("station_id").set_index("station_id")
    manquantes = [i for i in ids if i not in s.index]
    if manquantes:
        raise ControleEchec(
            f"{len(manquantes)} stations sans coordonnées ({manquantes[:4]}) — un pli "
            "spatial construit sur des positions incomplètes ne bloque rien")
    c = s.loc[ids, ["x_l93", "y_l93"]] / 1000.0
    if c.isna().any().any():
        raise ControleEchec("coordonnées manquantes après jointure")
    return c


def plis_alternes(ids: np.ndarray, n_plis: int) -> np.ndarray:
    """Le protocole actuel : `i % n_plis` sur l'identifiant trié."""
    return np.array([i % n_plis for i in range(len(np.sort(ids)))])[
        np.argsort(np.argsort(ids))]


def plis_spatiaux(c: pd.DataFrame, n_plis: int) -> np.ndarray:
    """Grappes géographiques équilibrées : des régions entières partent en test."""
    from sklearn.cluster import KMeans

    # Beaucoup de petites grappes, réparties ensuite entre les plis : un k-moyennes à
    # `n_plis` grappes donnerait trois blocs énormes et déséquilibrés (le Nord contre le Sud),
    # ce qui mesurerait la différence entre régions plutôt que la généralisation spatiale.
    n_grappes = max(n_plis * 8, 24)
    km = KMeans(n_clusters=n_grappes, random_state=GRAINE, n_init=10).fit(c.to_numpy())
    tailles = pd.Series(km.labels_).value_counts()
    # Remplissage glouton du pli le moins peuplé — équilibre les effectifs sans casser
    # la contiguïté des grappes.
    pli_de_grappe, charge = {}, np.zeros(n_plis)
    for grappe, taille in tailles.items():
        p = int(np.argmin(charge))
        pli_de_grappe[grappe] = p
        charge[p] += taille
    return np.array([pli_de_grappe[g] for g in km.labels_])


def evaluer(d: pd.DataFrame, predicteurs: list[str], groupe: np.ndarray,
            c: pd.DataFrame | None = None, rayon_km: float = 0.0,
            retrait_aleatoire: int = 0, graine: int = GRAINE) -> dict:
    """Ajuste pli par pli et rend les scores.

    ``rayon_km`` creuse un fossé autour du test. ``retrait_aleatoire`` retire à la place
    **n stations d'entraînement au hasard** : c'est le témoin indispensable du fossé. Un
    fossé de 150 km retire environ 70 % du jeu d'apprentissage ; sans ce témoin, on ne sait
    pas si la chute de gain vient de la fuite supprimée ou de la famine de données.
    """
    ids = d["station_id"].to_numpy()
    par_station = dict(zip(c.index, range(len(c)))) if c is not None else {}
    xy = c.to_numpy() if c is not None else None
    g_station = pd.Series(groupe, index=c.index) if c is not None else None

    pred = np.full(len(d), np.nan)
    exclus_total = 0
    for p in sorted(set(groupe)):
        stations_test = g_station[g_station == p].index if c is not None else None
        masque_test = np.isin(ids, stations_test)
        if retrait_aleatoire > 0:
            rng = np.random.default_rng(graine + p)
            candidats = np.array([s for s in c.index if s not in set(stations_test)])
            n = min(retrait_aleatoire, max(len(candidats) - 20, 0))
            retirees = set(rng.choice(candidats, n, replace=False)) if n else set()
            exclus_total += len(retirees)
            masque_train = ~np.isin(ids, list(set(stations_test) | retirees))
        elif rayon_km > 0:
            it = [par_station[s] for s in stations_test]
            dist = np.hypot(xy[:, None, 0] - xy[None, it, 0],
                            xy[:, None, 1] - xy[None, it, 1]).min(axis=1)
            proches = set(c.index[dist < rayon_km]) - set(stations_test)
            exclus_total += len(proches)
            masque_train = ~np.isin(ids, list(set(stations_test) | proches))
        else:
            masque_train = ~masque_test
        m = modele()
        m.fit(d.loc[masque_train, predicteurs],
              d.loc[masque_train, "valeur"] - d.loc[masque_train, "cams_jour"])
        pred[masque_test] = np.clip(
            d.loc[masque_test, "cams_jour"].to_numpy()
            + m.predict(d.loc[masque_test, predicteurs]), 0, None)

    ok = np.isfinite(pred)
    obs, cams = d["valeur"].to_numpy()[ok], d["cams_jour"].to_numpy()[ok]
    rc = float(np.sqrt(np.mean((cams - obs) ** 2)))
    rm = float(np.sqrt(np.mean((pred[ok] - obs) ** 2)))
    haut = obs >= np.quantile(obs, 0.9)
    return {"rmse_cams": rc, "rmse_mos": rm, "gain_pct": 100 * (1 - rm / rc),
            "rmse_decile_haut": float(np.sqrt(np.mean((pred[ok][haut] - obs[haut]) ** 2))),
            "n_evalue": int(ok.sum()),
            "stations_ecartees_par_fosse": exclus_total}


def main(polluant: str, n_plis: int, rayon: float) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    d = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    d = d.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    ids = np.sort(d["station_id"].unique())
    c = coordonnees(ids)
    print(f"{polluant} · {len(d):,} jours-station · {len(ids)} stations · "
          f"{len(predicteurs)} prédicteurs", flush=True)

    # Le diagnostic qui motive tout le script, recalculé ici pour qu'il figure au journal.
    xy = c.to_numpy()
    dist = np.hypot(xy[:, None, 0] - xy[None, :, 0], xy[:, None, 1] - xy[None, :, 1])
    np.fill_diagonal(dist, np.inf)
    pp = dist.min(axis=1)
    print(f"  plus proche voisin : médiane {np.median(pp):.1f} km · "
          f"part < 10 km {np.mean(pp < 10):.0%}", flush=True)

    g_alt = pd.Series(plis_alternes(ids, n_plis), index=ids)
    g_spa = pd.Series(plis_spatiaux(c, n_plis), index=c.index)
    for nom, g in (("i % n", g_alt), ("blocs spatiaux", g_spa)):
        voisin = dist.argmin(axis=1)
        fuite = float((g.to_numpy() != g.to_numpy()[voisin]).mean())
        print(f"  {nom:16s} · voisin dans un autre pli : {fuite:.0%} · "
              f"effectifs {list(g.value_counts().sort_index())}", flush=True)

    protocoles = [
        ("1 · i % n (protocole actuel)", g_alt, None, 0.0),
        ("2 · blocs spatiaux", g_spa, c, 0.0),
        (f"3 · blocs + fossé {rayon:.0f} km", g_spa, c, rayon),
    ]
    lignes = []
    for nom, g, coords, r in protocoles:
        if coords is None:
            coords_util, g_util = c, pd.Series(g.to_numpy(), index=c.index)
        else:
            coords_util, g_util = coords, g
        s = evaluer(d, predicteurs, g_util.to_numpy(), coords_util, r)
        lignes.append({"protocole": nom} | s)
        print(f"  {nom:30s} gain {s['gain_pct']:+6.2f} % · RMSE {s['rmse_mos']:6.3f} · "
              f"décile haut {s['rmse_decile_haut']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    # Le témoin, dimensionné sur le retrait moyen par pli réellement opéré par le fossé.
    retire_par_pli = int(round(lignes[-1]["stations_ecartees_par_fosse"] / max(len(set(g_spa)), 1)))
    if retire_par_pli > 0:
        s = evaluer(d, predicteurs, g_spa.to_numpy(), c, 0.0,
                    retrait_aleatoire=retire_par_pli)
        lignes.append({"protocole": f"4 · blocs + retrait ALÉATOIRE de {retire_par_pli} "
                                    f"stations (témoin)"} | s)
        print(f"  {lignes[-1]['protocole']:30s} gain {s['gain_pct']:+6.2f} % · "
              f"RMSE {s['rmse_mos']:6.3f} · décile haut {s['rmse_decile_haut']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    t = pd.DataFrame(lignes)
    ref, dur = t.iloc[0], t.iloc[2]
    ecart = ref["gain_pct"] - dur["gain_pct"]
    print(f"\n{'─' * 84}")
    print(f"Optimisme du protocole actuel : **{ecart:+.2f} point de gain** "
          f"({ref['gain_pct']:+.2f} % → {dur['gain_pct']:+.2f} %)")
    if abs(ecart) < 1.0:
        print("  → La validation du projet TIENT : bloquer l'espace ne change presque rien.\n"
              "    Le chiffre publié décrit bien une généralisation, pas une interpolation\n"
              "    entre stations voisines. À dire avec ce chiffre en main.")
    else:
        print(f"  → Le chiffre publié est OPTIMISTE de {ecart:.1f} point pour l'usage "
              f"« prédire là\n    où rien ne mesure ». Publier les deux : le protocole actuel "
              f"pour comparer des\n    produits entre eux, le protocole bloqué pour annoncer "
              f"une performance en un lieu neuf.")

    sortie = RACINE / f"reports/validation_bloquee_{polluant}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {time.time() - depart:.0f}s")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--plis", type=int, default=3)
    a.add_argument("--rayon", type=float, default=25.0,
                   help="rayon du fossé autour des stations de test, en km")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.plis, n.rayon))
