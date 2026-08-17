#!/usr/bin/env python3
"""Par quel MÉCANISME la spéciation gagne-t-elle — et l'histoire des sources survit-elle ?

La question, posée par la revue externe
----------------------------------------
`ablation_speciation.py` établit un fait : la composition rend +4,9 à +12,1 % au-delà de la
forme du total. Il n'établit **aucun mécanisme**. Deux explications le produisent également :

* **(source)** le modèle apprend un biais qui dépend de la composition du jour ;
* **(proxy)** une composante encode une variable latente absente du socle — la saison, le
  site, le régime météorologique — et le gain n'a rien à voir avec la composition.

Le signal qui rend le doute sérieux : **l'ozone gagne autant que les particules avec des
traceurs exclusivement particulaires.** Une histoire de sources n'explique pas cela.

L'échelle de falsification — cinq configurations, une décision par test
------------------------------------------------------------------------
Toutes sur **les mêmes lignes**, **les mêmes plis**, **les mêmes hyperparamètres**, et
comparées à `S` (spéciation brute) et `T` (forme du total seule), qui bornent l'intervalle.

| conf. | ce qu'on donne au modèle | si ≈ S, alors |
|---|---|---|
| **C** | la **climatologie** station × mois de chaque composante *(ajustée sur le pli d'apprentissage)* | le gain est un encodeur site×saison — **l'histoire des sources meurt** |
| **R** | l'**anomalie** journalière : composante − sa climatologie | le gain est de l'information du jour — l'histoire des sources survit |
| **F** | la **composition relative** : composante ÷ somme des composantes | c'est la composition, pas la masse |
| **X** | la spéciation **permutée à l'intérieur de chaque station × mois** | 🔴 le gain ne tient pas au jour — c'est C par un autre chemin |
| **P** | pas de spéciation, mais les **totaux CAMS des trois autres polluants** | le gain est un proxy de régime, disponible sans rien télécharger |

`C` et `R` se lisent ensemble : brut = climatologie + anomalie, donc leurs deux gains se
partagent celui de `S`. Le partage **est** la réponse.

`X` est le test le plus dur, et le seul qui ne change pas la distribution marginale : la
permutation conditionnelle conserve exactement l'histogramme de chaque composante par
station et par mois, et ne détruit que l'appariement au **jour**. Un gain qui survit à `X`
n'est pas un gain d'information journalière, quelle que soit l'élégance de l'explication
qu'on lui trouve.

`P` est le contrôle que la revue n'avait pas demandé et qui coûte le moins : les totaux des
autres polluants sont **déjà sur le disque**. S'ils suffisent, le téléchargement de
spéciation était une dépense inutile, et il faut l'écrire.

🔴 Le seuil de décision, fixé AVANT lecture des résultats
----------------------------------------------------------
On note `part(K) = (gain(K) − gain(T)) / (gain(S) − gain(T))`, la part du gain de la
spéciation que la configuration `K` reproduit.

* `part(X) ≥ 0,5` → **le gain est climatologique** : retirer toute formulation « biais par
  source » du dossier, et présenter la spéciation comme un encodeur site×saison.
* `part(C) ≥ 0,7` → même conclusion, par le second chemin.
* `part(R) ≥ 0,7` **et** `part(X) < 0,3` → l'information est journalière ; la formulation
  « le modèle exploite la composition du jour » devient défendable — sans pour autant
  nommer une source.
* `part(P) ≥ 0,7` → **écrire que la spéciation est superflue**, les totaux suffisent.

Aucun de ces seuils ne dépend du polluant, et ils sont écrits ici avant le premier ajustement.

⚠️ Ce que ce script ne peut pas faire : identifier une source. Il faudrait une spéciation
**observée** ou une perturbation d'inventaire. Voir `shapley_speciation.py`, dont
l'attribution reste prédictive.

Usage : python3 scripts/mecanisme_speciation.py --polluant PM10 [--graines 5]
Sortie : reports/mecanisme_speciation_<polluant>.csv
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

from ablation_speciation import (  # noqa: E402
    HORIZON, charger, charger_speciation, forme_du_total, jeu_journalier_a,
)
from aq.rapport import ecrire_rapport  # noqa: E402
from optuna_mos import params_reference, rmse  # noqa: E402

N_FILS = 4
AUTRES = {"O3": ("NO2", "PM10", "PM25"), "NO2": ("O3", "PM10", "PM25"),
          "PM10": ("O3", "NO2", "PM25"), "PM25": ("O3", "NO2", "PM10")}

# ⚠️ Dates de mise en production des systèmes CAMS, **citées par la revue externe et NON
# vérifiées**. Tentative de vérification par nos propres données le 17/08 : le saut normalisé
# des composantes à la date annoncée (|z| médian 0,38 au 2025-11-13) est **indiscernable**
# de celui d'une date témoin arbitraire (0,37 au 2025-03-15) — à mi-novembre, une fenêtre de
# 45 jours compare octobre à décembre et le balancement saisonnier écrase tout pas de version.
# Le test est donc inconclusif, ni confirmation ni réfutation. Il l'est d'autant plus que la
# même revue a déjà cité de mémoire une clé d'API qui n'existait pas (§ 1 ter : un excellent
# relecteur reste une source à vérifier).
#
# Ce que ce découpage vaut **indépendamment de l'exactitude des dates** : deux sous-corpus
# temporels disjoints. Un mécanisme qui ne tient pas sur les deux ne tient pas (règle E).
EPOQUES = {"U9": ("2024-11-13", "2025-11-12"), "U10": ("2025-11-13", "2026-12-31")}

SEUILS = {"X": 0.5, "C": 0.7, "R": 0.7, "P": 0.7}     # fixés avant lecture


def climatologie(j: pd.DataFrame, spe: list[str], entr: np.ndarray) -> tuple[pd.DataFrame, dict]:
    """Moyenne station × mois-calendaire de chaque composante, AJUSTÉE SUR LE PLI D'APPRENTISSAGE.

    Une climatologie calculée sur tout le jeu ferait fuiter le pli de test dans le pli
    d'apprentissage : la configuration `C` gagnerait pour une raison qui n'est pas la sienne.
    Les couples (station, mois) absents du pli d'apprentissage replient sur la moyenne de la
    station, puis sur la moyenne globale — et **chaque repli est compté** (§ 2 quater).
    """
    cle = pd.DataFrame({"station_id": j["station_id"].to_numpy(),
                        "mois": pd.to_datetime(j["jour"]).dt.month.to_numpy()})
    src = j.loc[entr, spe]
    par_sm = src.groupby([cle.loc[entr, "station_id"], cle.loc[entr, "mois"]]).mean()
    par_s = src.groupby(cle.loc[entr, "station_id"]).mean()
    globale = src.mean()

    idx = pd.MultiIndex.from_arrays([cle["station_id"], cle["mois"]])
    out = par_sm.reindex(idx)
    manque_sm = out[spe[0]].isna().to_numpy()
    secours = par_s.reindex(cle["station_id"])
    out = out.to_numpy()
    sec = secours.to_numpy()
    out[manque_sm] = sec[manque_sm]
    manque_s = np.isnan(out[:, 0])
    out[manque_s] = globale.to_numpy()
    replis = {"station_mois_absent": int(manque_sm.sum()), "station_absente": int(manque_s.sum())}
    return pd.DataFrame(out, columns=spe, index=j.index), replis


def permuter_dans_blocs(j: pd.DataFrame, spe: list[str], graine: int) -> pd.DataFrame:
    """Permute les colonnes de spéciation À L'INTÉRIEUR de chaque (station, mois-calendaire).

    Les lignes gardent leur station, leur mois et leur cible ; seule l'association au JOUR
    est détruite. Les composantes sont permutées **ensemble**, d'un seul tirage par bloc :
    les permuter séparément casserait aussi la cohérence entre composantes, et le test ne
    saurait plus laquelle des deux structures il vient de détruire.
    """
    rng = np.random.default_rng(graine)
    mois = pd.to_datetime(j["jour"]).dt.month.to_numpy()
    ordre = np.arange(len(j))
    bloc = pd.Series(ordre).groupby([j["station_id"].to_numpy(), mois])
    for _, positions in bloc.groups.items():
        p = np.asarray(positions)
        ordre[p] = rng.permutation(p)
    return pd.DataFrame(j[spe].to_numpy()[ordre], columns=spe, index=j.index)


def totaux_des_autres(polluant: str, horizon: int, j: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Les prévisions CAMS totales des trois AUTRES polluants, déjà sur le disque."""
    out, noms = j[["station_id", "jour"]].copy(), []
    for autre in AUTRES[polluant]:
        try:
            t, _ = jeu_journalier_a(autre, horizon)
        except Exception as e:                        # jamais silencieux (§ 2 bis)
            print(f"    ⚠️ totaux {autre} indisponibles : {type(e).__name__} — {e}", flush=True)
            continue
        t = t[["station_id", "jour", "cams_jour"]].rename(columns={"cams_jour": f"cams_{autre}"})
        t["jour"] = pd.to_datetime(t["jour"]).dt.tz_localize(None)
        out = out.merge(t, on=["station_id", "jour"], how="left")
        noms.append(f"cams_{autre}")
    return out[noms], noms


def main(polluant: str, n_graines: int, epoque: str) -> int:
    t0 = time.time()
    j, base = jeu_journalier_a(polluant, HORIZON)
    j["jour"] = pd.to_datetime(j["jour"]).dt.tz_localize(None)
    j = j.merge(forme_du_total(polluant, HORIZON), on=["station_id", "jour"], how="left")
    avant = len(j)
    j = j.merge(charger_speciation(), on=["station_id", "jour"], how="inner").reset_index(drop=True)
    if epoque != "tout":
        d0, d1 = EPOQUES[epoque]
        avant_ep = len(j)
        j = j[j["jour"].between(d0, d1)].reset_index(drop=True)
        print(f"  époque {epoque} : {d0} → {d1} · {len(j):,} lignes sur {avant_ep:,} "
              f"({100 * len(j) / avant_ep:.0f} %)", flush=True)
        if len(j) < 5000:
            raise SystemExit(f"époque {epoque} : {len(j)} lignes, trop peu pour conclure")
    forme = [c for c in ("cams_min", "cams_max", "cams_ect", "cams_p90_p10") if c in j]
    spe = sorted(c for c in j.columns if c.startswith("spe_"))
    socle = base + forme
    print(f"{polluant} · {len(j):,} lignes sur {avant:,} · socle {len(socle)} var. · "
          f"spéciation {len(spe)} var. · {n_graines} graines", flush=True)

    jours = np.sort(j["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr = (j["jour"] < coupe).to_numpy()
    test = ~entr
    y = (j["obs_jour"] - j["cams_jour"]).to_numpy(dtype=np.float32)
    obs = j.loc[test, "obs_jour"].to_numpy()
    cams = j.loc[test, "cams_jour"].to_numpy()
    r_cams = rmse(obs, cams)

    # ── Les blocs de variables de chaque configuration ─────────────────────────────────
    clim, replis = climatologie(j, spe, entr)
    ano = pd.DataFrame(j[spe].to_numpy() - clim.to_numpy(), columns=spe, index=j.index)
    somme = j[spe].sum(axis=1).replace(0, np.nan)
    rel = j[spe].div(somme, axis=0)
    autres, noms_autres = totaux_des_autres(polluant, HORIZON, j)
    print(f"  climatologie : {replis['station_mois_absent']:,} lignes repliées sur la station, "
          f"{replis['station_absente']:,} sur la moyenne globale · "
          f"proxy de régime : {noms_autres}", flush=True)

    configs = {
        "T — forme du total seule":                    None,
        "S — spéciation brute":                        j[spe],
        "C — climatologie station × mois":             clim,
        "R — anomalie journalière":                    ano,
        "F — composition relative":                    rel,
        "X — permutation dans station × mois":         "permutation",
        "P — totaux CAMS des autres polluants":        autres,
    }

    from lightgbm import LGBMRegressor  # noqa: PLC0415

    lignes, gains = [], {}
    for nom, bloc in configs.items():
        rs = []
        for g in range(n_graines):
            if isinstance(bloc, str):                 # X : un tirage neuf par graine
                bloc_g = permuter_dans_blocs(j, spe, 20260817 + g)
            else:
                bloc_g = bloc
            X = (j[socle] if bloc_g is None
                 else pd.concat([j[socle], bloc_g], axis=1)).to_numpy(dtype=np.float32)
            m = LGBMRegressor(n_estimators=400, random_state=20260817 + g, verbose=-1,
                              n_jobs=N_FILS, **params_reference("lgbm"))
            m.fit(X[entr], y[entr])
            rs.append(rmse(obs, np.clip(cams + m.predict(X[test]), 0, None)))
        med = float(np.median(rs))
        gains[nom[0]] = 100 * (1 - med / r_cams)
        lignes.append({"configuration": nom, "code": nom[0], "n_variables": X.shape[1],
                       "rmse_median": med, "rmse_min": float(np.min(rs)),
                       "rmse_max": float(np.max(rs)), "gain_pct": gains[nom[0]]})
        print(f"  {nom:44s} {len(socle) if bloc is None else X.shape[1]:3d} var. · "
              f"RMSE {med:7.4f} (±{np.std(rs):.4f}) · gain {gains[nom[0]]:+6.2f} % · "
              f"{(time.time()-t0)/60:.1f} min", flush=True)

    # ── La lecture, contre les seuils écrits en tête de fichier ────────────────────────
    etendue = gains["S"] - gains["T"]
    print(f"\n  L'apport de la spéciation vaut {etendue:+.2f} pt "
          f"(T {gains['T']:+.2f} → S {gains['S']:+.2f}). Part reproduite :", flush=True)
    verdicts = []
    for code in ("C", "R", "F", "X", "P"):
        part = (gains[code] - gains["T"]) / etendue if etendue else np.nan
        seuil = SEUILS.get(code)
        franchi = seuil is not None and part >= seuil
        verdicts.append({"code": code, "part_du_gain": part, "seuil": seuil,
                         "seuil_franchi": franchi})
        marque = "🔴" if franchi and code in ("C", "X", "P") else ("✓" if franchi else " ")
        print(f"    {marque} {code} : {100*part:5.1f} %"
              + (f"  (seuil {100*seuil:.0f} %)" if seuil else ""), flush=True)

    v = {d["code"]: d for d in verdicts}
    if v["X"]["seuil_franchi"] or v["C"]["seuil_franchi"]:
        print("\n  🔴 CONCLUSION : le gain est CLIMATOLOGIQUE. Retirer du dossier toute "
              "formulation « biais par source » ; écrire « encodeur site × saison ».", flush=True)
    elif v["P"]["seuil_franchi"]:
        print("\n  🔴 CONCLUSION : les totaux des autres polluants suffisent — la spéciation "
              "est superflue, et le téléchargement était une dépense inutile.", flush=True)
    elif v["R"]["seuil_franchi"] and v["X"]["part_du_gain"] < 0.3:
        print("\n  ✅ CONCLUSION : l'information est JOURNALIÈRE. « Le modèle exploite la "
              "composition du jour » est défendable — sans nommer de source.", flush=True)
    else:
        print("\n  ⚠️ CONCLUSION : aucun seuil franchi. Le mécanisme reste indéterminé ; "
              "publier l'apport du bloc et s'abstenir de toute explication.", flush=True)

    t = pd.DataFrame(lignes).merge(pd.DataFrame(verdicts), on="code", how="left")
    t["polluant"], t["n_graines"], t["n_lignes"] = polluant, n_graines, len(j)
    t["replis_station"] = replis["station_mois_absent"]
    t["epoque"] = epoque
    suff = "" if epoque == "tout" else f"_{epoque}"
    ecrire_rapport(t, RACINE / f"reports/mecanisme_speciation_{polluant}{suff}.csv",
                   contexte={"polluant": polluant, "axe": "temporel"},
                   attendues=["configuration", "gain_pct", "part_du_gain", "seuil_franchi"])
    print(f"Écrit · {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10", choices=("O3", "NO2", "PM10", "PM25"))
    a.add_argument("--graines", type=int, default=5)
    a.add_argument("--epoque", default="tout", choices=("tout", "U9", "U10"),
                   help="restreindre à une époque CAMS — deux sous-corpus temporels "
                        "disjoints, pour éprouver la STABILITÉ du verdict (règle E)")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.graines, n.epoque))
