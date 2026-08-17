#!/usr/bin/env python3
"""La correction se dégrade-t-elle avec l'échéance ? — J0 à J+3, pile commune et fixe.

L'affirmation testée, et elle est déjà publiée
------------------------------------------------
Le dossier affirme que **nos leviers ne se dégradent pas avec l'échéance** — moins d'un point
d'écart entre J0, J+1 et J+2 — parce que le biais corrigé est une propriété du **site**, pas
de la prévision. C'est une prédiction, et **J+3 est la seule échéance où elle peut encore
être réfutée** : CAMS Europe s'arrête à 96 h, il n'existe ni J+4 ni J+5.

🔴 Ce que ce balayage NE teste PAS, et le nom compte
-----------------------------------------------------
Il teste la stabilité **d'une pile commune**, pas celle de la meilleure pile J+1. Les
familles n'existent pas aux mêmes échéances :

* la **spéciation** n'a été téléchargée qu'aux heures 25-48, donc J+1 seulement ;
* les **membres** n'ont été demandés que pour leur tranche J+1 ;
* **GEOS-CF** est joint depuis une sortie J−1 : l'utiliser pour une cible J+2 ou J+3 serait
  une fuite d'heure d'émission ;
* les **feux** ont des mois entiers absents (14 mois sur 24).

Acheter les trois tranches de spéciation manquantes ne résoudrait donc rien — on aurait
encore quatre piles différentes. La pile retenue est celle qui existe **identique aux quatre
échéances** : `totaux CAMS + terrain/calendrier + typologie + tendance récente de CAMS`.

La tendance se calcule séparément à chaque horizon depuis les sorties antérieures **du même
horizon** ; elle ne contient aucune observation locale.

Le protocole, et pourquoi chaque contrainte
---------------------------------------------
1. **intersection des clés `station × jour`** disponibles aux quatre horizons — sinon l'écart
   entre horizons mesurerait un changement de corpus (§ 2 quater) ;
2. **mêmes groupes de stations, mêmes mois de test, même graine, mêmes hyperparamètres,
   mêmes colonnes** aux quatre ;
3. **un modèle distinct par horizon** — la relation résiduelle peut changer, mais aucun
   élément de la recette ne change ;
4. la grandeur primaire est la **plage** `R = max(G) − min(G)`, pas un gain particulier.

🔴 Seuil préenregistré, écrit avant la première mesure
-------------------------------------------------------
* **stable** si `R < 1,0` point **et** si la borne haute unilatérale à 95 % de `R` est `< 1,0`,
  avec le même verdict sous blocs de trois et de six mois ;
* si le point passe mais pas la borne haute : **indéterminé**, donc non établi ;
* si la borne **basse** dépasse 1,0 : **réfuté**.

Quatre tests — un par polluant — corrigés par Holm. Pour la phrase globale « stable sur les
quatre », il faut que les quatre passent : cette intersection ne permet pas qu'un succès
compense un échec.

Statut : `sensibilité_préenregistrée — stabilité_échéance`. J+3 n'avait jamais été consulté.

Usage  : python3 scripts/balayage_echeances.py --polluant O3
Sortie : reports/balayage_echeances_<polluant>.csv
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

from aq.rapport import ecrire_rapport, libelle_echeance  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from leviers_36mois import gain  # noqa: E402

HORIZONS = (1, 2, 3, 4)          # J0, J+1, J+2, J+3
N_PLIS_SPATIAUX = 3
SEUIL_PLAGE = 1.0                # points de % — fixé avant lecture
TIRAGES = 10000


def jeu(polluant: str, horizon: int) -> tuple[pd.DataFrame, list[str]]:
    """Le jeu journalier d'un horizon, avec la pile commune et rien d'autre."""
    jeu = charger(polluant, horizon)
    base_cols = colonnes_admises(jeu)
    jeu[base_cols] = jeu[base_cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, base_cols, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in base_cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    from banc_preprocessing import f_tendance_cams  # noqa: PLC0415
    tend = f_tendance_cams(d)
    if collision := [c for c in tend.columns if c in d.columns]:
        raise SystemExit(f"colonnes de tendance déjà présentes : {collision}")
    d = pd.concat([d, tend], axis=1)

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")

    cols = list(base) + list(tend.columns) + list(cols_typo)
    cols = [c for c in dict.fromkeys(cols) if c in d.columns]
    return d, cols


def main(polluant: str, tirages: int) -> int:
    t0 = time.time()
    jeux, colonnes = {}, None
    for h in HORIZONS:
        d, cols = jeu(polluant, h)
        jeux[h] = d
        colonnes = cols if colonnes is None else [c for c in colonnes if c in cols]
        print(f"  {libelle_echeance(h):4s} · {len(d):>8,} jours-station · "
              f"{d['mois'].nunique()} mois", flush=True)

    # ── ① L'intersection des clés, pour que l'écart entre horizons soit le SEUL écart ──
    cles = None
    for h in HORIZONS:
        k = set(map(tuple, jeux[h][["station_id", "jour"]].to_numpy()))
        cles = k if cles is None else cles & k
    for h in HORIZONS:
        m = [tuple(x) in cles for x in jeux[h][["station_id", "jour"]].to_numpy()]
        jeux[h] = jeux[h][m].sort_values(["station_id", "jour"]).reset_index(drop=True)
    n = len(jeux[HORIZONS[0]])
    print(f"\n  intersection des quatre horizons : {n:,} clés · "
          f"{jeux[HORIZONS[0]]['mois'].nunique()} mois · {len(colonnes)} colonnes communes",
          flush=True)
    for h in HORIZONS:
        if len(jeux[h]) != n:
            raise SystemExit(f"{libelle_echeance(h)} : {len(jeux[h])} clés au lieu de {n}")

    # ── ② Les plis, IDENTIQUES aux quatre — mêmes groupes, mêmes mois, même graine ──
    base = jeux[HORIZONS[0]]
    rng = np.random.default_rng(GRAINE)
    ids = np.sort(base["station_id"].unique())
    groupes = np.array_split(rng.permutation(ids), N_PLIS_SPATIAUX)
    mois_ok = sorted(base["mois"].unique())
    plis = []
    for i, mm in enumerate(mois_ok):
        dans = base["station_id"].isin(groupes[i % N_PLIS_SPATIAUX]).to_numpy()
        te = (base["mois"] == mm).to_numpy() & dans
        tr = (base["mois"] != mm).to_numpy() & ~dans
        if te.sum() >= 200 and tr.sum() >= 1000:
            plis.append((mm, te, tr))
    print(f"  {len(plis)} plis exécutés sur {len(mois_ok)} prévus\n", flush=True)

    # ── ③ Un modèle par horizon, recette inchangée ──
    lignes = []
    for h in HORIZONS:
        d = jeux[h]
        obs, cams, pred, par_pli = [], [], [], []
        for mm, te, tr in plis:
            p = ajuster(DEFAUT, d[tr], d[te], colonnes, "cams_jour")
            o, c = d.loc[te, "valeur"].to_numpy(), d.loc[te, "cams_jour"].to_numpy()
            obs.append(o); cams.append(c); pred.append(p)
            par_pli.append({"horizon": h, "echeance": libelle_echeance(h), "mois": mm,
                            "n_test": int(te.sum()),
                            "rmse_cams": float(np.sqrt(np.mean((c - o) ** 2))),
                            "rmse_corrige": float(np.sqrt(np.mean((p - o) ** 2)))})
        g = gain(np.concatenate(obs), np.concatenate(cams), np.concatenate(pred))
        rc = float(np.sqrt(np.mean((np.concatenate(cams) - np.concatenate(obs)) ** 2)))
        rm = float(np.sqrt(np.mean((np.concatenate(pred) - np.concatenate(obs)) ** 2)))
        lignes.extend(par_pli)
        print(f"  {libelle_echeance(h):4s} · RMSE CAMS {rc:6.3f} → corrigé {rm:6.3f} · "
              f"gain {g:+6.2f} % · {(time.time() - t0) / 60:.1f} min", flush=True)

    pli = pd.DataFrame(lignes)
    pli.to_csv(RACINE / f"reports/balayage_echeances_{polluant}_par_pli.csv", index=False)

    # ── ④ La plage R, et son intervalle par blocs — les quatre horizons ENSEMBLE ──
    piv_n = pli.pivot(index="mois", columns="horizon", values="n_test").sort_index()
    piv_c = pli.pivot(index="mois", columns="horizon", values="rmse_cams").sort_index()
    piv_m = pli.pivot(index="mois", columns="horizon", values="rmse_corrige").sort_index()

    def plage(idx: np.ndarray) -> float:
        gs = []
        for h in HORIZONS:
            nn = piv_n[h].to_numpy()[idx]
            rc = float(np.sqrt(np.sum(nn * piv_c[h].to_numpy()[idx] ** 2) / nn.sum()))
            rm = float(np.sqrt(np.sum(nn * piv_m[h].to_numpy()[idx] ** 2) / nn.sum()))
            gs.append(100.0 * (1.0 - rm / rc))
        return max(gs) - min(gs), gs

    k = len(piv_n)
    r_point, gains_point = plage(np.arange(k))
    res = {"polluant": polluant, "n_plis": k, "n_cles": n,
           "plage_pt": r_point}
    for h, g in zip(HORIZONS, gains_point):
        res[f"gain_{libelle_echeance(h)}"] = g

    for bloc in (3, 6):
        rng2 = np.random.default_rng(GRAINE + bloc)
        nb = int(np.ceil(k / bloc))
        ech = np.empty(tirages)
        for t in range(tirages):
            deps = rng2.integers(0, k, nb)
            idx = np.concatenate([(np.arange(d0, d0 + bloc) % k) for d0 in deps])[:k]
            ech[t], _ = plage(idx)
        haut = float(np.percentile(ech, 95))       # borne HAUTE unilatérale
        bas = float(np.percentile(ech, 5))
        res |= {f"plage_haut95_b{bloc}": haut, f"plage_bas5_b{bloc}": bas,
                f"stable_b{bloc}": bool(r_point < SEUIL_PLAGE and haut < SEUIL_PLAGE),
                f"refute_b{bloc}": bool(bas > SEUIL_PLAGE)}

    res["verdict"] = ("stable" if res["stable_b3"] and res["stable_b6"]
                      else "réfutée" if res["refute_b3"] and res["refute_b6"]
                      else "indéterminée")
    print(f"\n  gains : " + " · ".join(f"{libelle_echeance(h)} {g:+.2f} %"
                                        for h, g in zip(HORIZONS, gains_point)))
    print(f"  PLAGE R = {r_point:.2f} pt · borne haute 95 % : "
          f"{res['plage_haut95_b3']:.2f} (blocs 3) / {res['plage_haut95_b6']:.2f} (blocs 6) "
          f"· seuil {SEUIL_PLAGE}")
    print(f"  → {res['verdict'].upper()}")

    ecrire_rapport(pd.DataFrame([res]),
                   RACINE / f"reports/balayage_echeances_{polluant}.csv",
                   contexte={"polluant": polluant, "axe": "double aveugle"},
                   attendues=["polluant", "plage_pt", "verdict"])
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3", choices=("O3", "NO2", "PM10", "PM25"))
    a.add_argument("--tirages", type=int, default=TIRAGES)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.tirages))
