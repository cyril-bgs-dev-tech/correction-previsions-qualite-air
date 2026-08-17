#!/usr/bin/env python3
"""À quel GROUPE de sources attribuer le gain de la spéciation — par Shapley exact.

Pourquoi pas un leave-one-out
------------------------------
Retirer une variable à la fois mesure son information **unique** conditionnellement à toutes
les autres ; le gain du bloc mesure l'information **jointe**. Avec sept traceurs corrélés,
retirer l'un ne coûte rien et retirer les sept coûte beaucoup — d'où le résultat absurde du
16/08 où ôter `ecres_conc`, la variable de l'hypothèse, **améliorait** sur 3 polluants sur 4.

Une suppression qui améliore peut aussi venir de la recherche de coupures de LightGBM : avec
`subsample=0.8` et `colsample_bytree=0.8`, un prédicteur redondant change les coupures
accessibles. **Un seul ajustement ne sépare pas redondance, nuisance et hasard algorithmique.**

Ce que fait ce script
----------------------
Trois groupes physiques, **huit** sous-ensembles, **cinq graines**. La contribution de
Shapley d'un groupe est la moyenne de son apport marginal sur les **six ordres** d'arrivée
possibles : c'est la seule attribution qui ne dépende pas d'un ordre choisi par l'analyste.

🔴 **Seuil d'attribution, fixé AVANT de lire les résultats.** On n'attribue un apport à un
groupe que si sa contribution médiane est **≥ 1,0 point**, positive dans **au moins 4 graines
sur 5**. Sinon on publie l'apport du **bloc** et on renonce à toute importance par espèce.
Et même alors, l'attribution reste **prédictive, jamais causale** : il faudrait une
spéciation observée ou une perturbation d'émissions pour identifier une source.

Usage : python3 scripts/shapley_speciation.py --polluant PM10 [--graines 5]
Sortie : reports/shapley_speciation_<polluant>.csv
"""
from __future__ import annotations

import argparse
import itertools
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from ablation_speciation import (  # noqa: E402
    GROUPES, HORIZON, charger_speciation, forme_du_total, jeu_journalier_a,
)
from aq.rapport import ecrire_rapport  # noqa: E402
from optuna_mos import params_reference, rmse  # noqa: E402

N_FILS = 4
SEUIL_ATTRIBUTION = 1.0     # points de gain — fixé avant lecture
PART_GRAINES = 0.8          # 4 graines sur 5


def main(polluant: str, n_graines: int) -> int:
    t0 = time.time()
    j, base = jeu_journalier_a(polluant, HORIZON)
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)
    j = j.merge(forme_du_total(polluant, HORIZON), on=["station_id", "jour"], how="left")
    j = j.merge(charger_speciation(), on=["station_id", "jour"], how="inner")

    forme = [c for c in ("cams_min", "cams_max", "cams_ect", "cams_p90_p10") if c in j]
    socle = base + forme
    cols = {g: [c for c in j.columns if c.startswith("spe_")
                and any(m in c for m in membres)]
            for g, membres in GROUPES.items()}
    noms = list(GROUPES)
    print(f"{polluant} · {len(j):,} lignes · socle {len(socle)} var. · "
          f"{ {g: len(v) for g, v in cols.items()} }", flush=True)

    jours = np.sort(j["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr = (j["jour"] < coupe).to_numpy()
    test = ~entr
    y = (j["obs_jour"] - j["cams_jour"]).to_numpy(dtype=np.float32)
    obs = j.loc[test, "obs_jour"].to_numpy()
    cams = j.loc[test, "cams_jour"].to_numpy()
    r_socle_ref = rmse(obs, cams)

    from lightgbm import LGBMRegressor  # noqa: PLC0415

    # ── Les huit sous-ensembles, chacun sur cinq graines ────────────────────────────────
    scores: dict[frozenset, list[float]] = {}
    sous_ensembles = [frozenset(c) for k in range(len(noms) + 1)
                      for c in itertools.combinations(noms, k)]
    for n, sous in enumerate(sous_ensembles, start=1):
        colonnes = socle + [c for g in sous for c in cols[g]]
        X = j[colonnes].to_numpy(dtype=np.float32)
        rs = []
        for g in range(n_graines):
            m = LGBMRegressor(n_estimators=400, random_state=20260817 + g, verbose=-1,
                              n_jobs=N_FILS, **params_reference("lgbm"))
            m.fit(X[entr], y[entr])
            rs.append(rmse(obs, np.clip(cams + m.predict(X[test]), 0, None)))
        scores[sous] = rs
        libelle = "∅ (socle seul)" if not sous else " + ".join(sorted(sous))
        print(f"  [{n}/8] {libelle:52s} RMSE {np.median(rs):7.4f} "
              f"(±{np.std(rs):.4f}) · {(time.time()-t0)/60:.1f} min", flush=True)

    # ── Shapley exact : moyenne de l'apport marginal sur les six ordres ────────────────
    def gain(sous: frozenset, graine: int) -> float:
        """Gain en POINTS de % contre CAMS brut — l'unité du dossier."""
        return 100 * (1 - scores[sous][graine] / r_socle_ref)

    lignes = []
    for g in noms:
        par_graine = []
        for k in range(n_graines):
            marges = []
            for ordre in itertools.permutations(noms):
                avant = frozenset(ordre[:ordre.index(g)])
                marges.append(gain(avant | {g}, k) - gain(avant, k))
            par_graine.append(float(np.mean(marges)))
        med = float(np.median(par_graine))
        part_pos = float(np.mean([x > 0 for x in par_graine]))
        attribue = med >= SEUIL_ATTRIBUTION and part_pos >= PART_GRAINES
        lignes.append({"groupe": g, "shapley_median_pt": med,
                       "shapley_min_pt": float(np.min(par_graine)),
                       "shapley_max_pt": float(np.max(par_graine)),
                       "part_graines_positives": part_pos,
                       "attribuable": attribue, "n_variables": len(cols[g])})
        print(f"  {g:24s} Shapley {med:+6.2f} pt "
              f"[{np.min(par_graine):+.2f} ; {np.max(par_graine):+.2f}] · "
              f"{100*part_pos:.0f} % de graines positives · "
              f"{'ATTRIBUABLE' if attribue else 'non attribuable'}", flush=True)

    bloc = gain(frozenset(noms), 0) - gain(frozenset(), 0)
    somme = sum(l["shapley_median_pt"] for l in lignes)
    print(f"\n  bloc complet {bloc:+.2f} pt · somme des Shapley {somme:+.2f} pt "
          f"(l'écart mesure l'interaction entre groupes)", flush=True)
    if not any(l["attribuable"] for l in lignes):
        print("  → AUCUN groupe attribuable : publier l'apport du BLOC, et renoncer à "
              "toute importance par espèce.", flush=True)

    ecrire_rapport(pd.DataFrame(lignes),
                   RACINE / f"reports/shapley_speciation_{polluant}.csv",
                   contexte={"polluant": polluant, "axe": "temporel"},
                   attendues=["groupe", "shapley_median_pt", "attribuable"])
    print(f"Écrit · {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10", choices=("O3", "NO2", "PM10", "PM25"))
    a.add_argument("--graines", type=int, default=5)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.graines))
