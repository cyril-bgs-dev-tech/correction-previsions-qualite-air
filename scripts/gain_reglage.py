#!/usr/bin/env python3
"""Ce que le réglage par polluant rapporte à NOTRE méthode — en CSV, plus seulement en journal.

Pourquoi ce script, alors que `optuna_mos.py` imprime déjà ces deux chiffres
------------------------------------------------------------------------------
`optuna_mos.py` termine par une « mesure finale » sur les stations jamais consultées :

    réglage lgbm déployé RMSE 8.5254 · gain vs CAMS +28.90 %
    meilleur Optuna      RMSE 8.1027 · gain vs CAMS +32.42 %

Ces deux lignes sont **imprimées, jamais enregistrées** : le CSV de l'étude ne porte que
l'objectif de validation croisée, pas la mesure finale. Pour faire entrer ce gain dans la
présentation, il faudrait le recopier à la main — et un chiffre recopié se périme en
silence (§ 2 ter : le chiffre affiché n'est pas le chiffre enregistré).

Ce script rejoue la mesure finale depuis l'étude stockée et l'**écrit**. Il ne relance aucun
essai : il relit le `.db`, retient le meilleur essai admissible, et ajuste deux fois.

Il est délibérément SÉPARÉ de `optuna_mos.py` : ce dernier est exécuté en boucle par
`lot_optuna_reglage.sh`, et modifier un script pendant qu'un lot l'appelle est le geste qui
a déjà tué un lot sur ce dépôt (§ 1 bis).

⚠️ Le gain rendu ici porte sur l'axe SPATIAL — réglage choisi par validation imbriquée sur
des groupes de stations, mesuré sur des stations jamais consultées. Le projet a mesuré
qu'un réglage gagnant en spatial peut PERDRE en temporel (+5 / −3 points). L'axe se cite
avec le chiffre.

Usage  : python3 scripts/gain_reglage.py --polluant O3
         python3 scripts/gain_reglage.py --tous
Sortie : reports/gain_reglage_<polluant>.csv
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

from optuna_mos import (  # noqa: E402
    DOSSIER, GRAINE, PART_QUEUE, PATIENCE, _params_essai, ajuster_pli, jeu_journalier,
    modele, params_reference, rmse, scores,
)


def ajuster_temporel(d: pd.DataFrame, predicteurs: list[str], params: dict,
                     algo: str) -> tuple[np.ndarray, pd.DataFrame]:
    """Ajuste sur la 1ʳᵉ moitié du calendrier, prédit sur la 2ᵈᵉ — **l'axe de LEUR protocole**.

    Pourquoi cette fonction existe
    -------------------------------
    La § 10 sexies met côte à côte deux gains de réglage qui ne sont pas la même épreuve :
    le leur est choisi et noté sur un partage du CALENDRIER, le nôtre sur un partage des
    STATIONS. Écrire « attention, ce n'est pas comparable » et publier quand même, c'est la
    réserve qui tient lieu de mesure — ce que la § 4 ter de `CLAUDE.md` interdit
    explicitement quand rendre la comparaison équitable est à portée. Ça l'est : deux
    ajustements par polluant.

    ⚠️ **Ce que cette mesure est, et ce qu'elle n'est pas.** Nos hyperparamètres restent
    choisis sur l'axe spatial ; seule l'ÉVALUATION passe sur l'axe temporel. C'est donc un
    test **non biaisé** de ce côté — la sélection n'a jamais vu ce partage — mais ce n'est
    pas la réplique exacte de leur protocole, où la sélection elle-même est temporelle.
    Un gain qui survit ici dit que le réglage n'était pas un artefact du découpage spatial.

    L'arrêt anticipé se règle sur le **dernier cinquième de la période d'entraînement**, et
    jamais sur le futur : régler le nombre d'arbres sur des jours postérieurs à la coupure
    ferait fuir la réponse dans un modèle qu'on prétend tester hors échantillon.
    """
    jours = np.sort(d["jour"].unique())
    coupe = jours[len(jours) // 2]
    entr, test = d[d["jour"] < coupe], d[d["jour"] >= coupe]
    if not len(entr) or not len(test):
        raise SystemExit(f"partage temporel vide : {len(entr)} / {len(test)} lignes")

    j_entr = np.sort(entr["jour"].unique())
    coupe_arret = j_entr[int(len(j_entr) * 0.8)]
    fit, arret = entr[entr["jour"] < coupe_arret], entr[entr["jour"] >= coupe_arret]

    m = modele(params, algo)
    cible_fit = fit["obs_jour"] - fit["cams_jour"]
    if algo == "xgb":
        m.fit(fit[predicteurs], cible_fit, verbose=False)
    else:
        import lightgbm as lgb

        m.fit(fit[predicteurs], cible_fit,
              eval_set=[(arret[predicteurs], arret["obs_jour"] - arret["cams_jour"])],
              eval_metric="rmse",
              callbacks=[lgb.early_stopping(PATIENCE, verbose=False)])
    pred = np.clip(test["cams_jour"].to_numpy() + m.predict(test[predicteurs]), 0, None)
    return pred, test

NOM = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}


def mesurer(polluant: str, algo: str = "lgbm", axe: str = "spatial") -> dict:
    import optuna

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    t0 = time.time()
    base = DOSSIER / f"mos_{polluant}_{algo}.db"
    if not base.exists():
        raise SystemExit(f"aucune étude pour {polluant} : {base} — lancer d'abord "
                         f"`bash scripts/lot_optuna_reglage.sh {polluant}`")
    etude = optuna.load_study(study_name=f"mos_{polluant}_{algo}",
                              storage=f"sqlite:///{base}")
    complets = [t for t in etude.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not complets:
        raise SystemExit(f"{polluant} : aucun essai complet dans l'étude")

    # ── La MÊME partition que l'étude : même graine, même tiers de test. Reconstruire
    # une partition différente comparerait deux mesures sur deux jeux, et l'écart
    # passerait pour un effet du réglage (§ 2 quater).
    j, predicteurs = jeu_journalier(polluant)
    stations = np.sort(j["station_id"].unique())
    melange = np.random.default_rng(GRAINE).permutation(stations)
    st_test = np.sort(melange[: len(melange) // 3])
    st_dev = np.sort(melange[len(melange) // 3:])

    # ── La sélection est celle de `optuna_mos._rapport`, à la lettre : le meilleur essai
    # SOUS CONTRAINTE DE QUEUE. Retenir le minimum global donnerait un gain plus flatteur
    # et un modèle que le dossier ne déploierait pas.
    reference = complets[0]          # l'essai amorcé sur le réglage déployé
    q_ref = reference.user_attrs.get("rmse_decile_haut", float("inf"))
    admissibles = [t for t in complets
                   if t.user_attrs.get("rmse_decile_haut", np.inf) <= q_ref * (1 + PART_QUEUE)]
    if not admissibles:
        raise SystemExit(f"{polluant} : aucun essai ne respecte la contrainte de queue")
    meilleur = min(admissibles, key=lambda t: t.value)

    epreuve = ("test {} stations jamais vues".format(len(st_test)) if axe == "spatial"
               else "2ᵈᵉ moitié du calendrier, toutes stations")
    print(f"{NOM[polluant]} · axe {axe.upper()} · {len(complets)} essais complets · "
          f"{len(admissibles)} admissibles · {epreuve}", flush=True)

    ligne = {"polluant": polluant, "algo": algo, "axe": axe,
             "essais_complets": len(complets),
             "essais_admissibles": len(admissibles), "essai_retenu": meilleur.number,
             "stations_test": len(st_test) if axe == "spatial" else None, "n": len(j)}
    brut: dict[str, pd.DataFrame] = {}
    for cle, nom, params in (("deploye", "réglage déployé", params_reference(algo)),
                             ("regle", "réglé par polluant", _params_essai(meilleur, algo))):
        if axe == "temporel":
            pred, test = ajuster_temporel(j, predicteurs, params, algo)
        else:
            pred, test, _ = ajuster_pli(j, predicteurs, st_dev, st_test, params, algo)
        r, q = scores(test["obs_jour"], pred)
        r_cams = rmse(test["obs_jour"], test["cams_jour"])
        ligne |= {f"rmse_{cle}": r, f"decile_haut_{cle}": q,
                  f"gain_cams_{cle}_pct": 100 * (1 - r / r_cams)}
        brut[cle] = pd.DataFrame({"station_id": test["station_id"].to_numpy(),
                                  "obs": test["obs_jour"].to_numpy(),
                                  "cams": test["cams_jour"].to_numpy(),
                                  "pred": np.asarray(pred)})
        print(f"  {nom:22s} RMSE {r:7.4f} · décile haut {q:7.4f} · "
              f"gain vs CAMS {100 * (1 - r / r_cams):+6.2f} %", flush=True)

    ligne["gain_reglage_pct"] = 100 * (1 - ligne["rmse_regle"] / ligne["rmse_deploye"])
    ligne["gain_reglage_pt"] = ligne["gain_cams_regle_pct"] - ligne["gain_cams_deploye_pct"]
    print(f"  → le réglage par polluant vaut {ligne['gain_reglage_pct']:+.2f} % de RMSE "
          f"({ligne['gain_reglage_pt']:+.2f} pt de gain vs CAMS) · "
          f"{(time.time() - t0) / 60:.1f} min\n", flush=True)
    return ligne, par_station(polluant, brut)


def par_station(polluant: str, brut: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Le même gain, station par station — la moyenne recouvre un facteur 2 à 3.

    ⚠️ **Les deux ajustements doivent avoir vu exactement les mêmes lignes**, sans quoi le
    gain par station comparerait deux populations et l'écart passerait pour un effet du
    réglage (§ 2 quater). Ils partagent `st_dev`/`st_test` et la graine, donc c'est vrai par
    construction — mais « vrai par construction » est précisément ce qui cesse de l'être
    quand quelqu'un touche à `ajuster_pli`. On l'exige plutôt que de l'espérer.
    """
    d, r = brut["deploye"], brut["regle"]
    if len(d) != len(r) or not np.array_equal(d["station_id"].to_numpy(),
                                              r["station_id"].to_numpy()):
        raise SystemExit(f"{polluant} : les deux ajustements ne portent pas sur les mêmes "
                         f"lignes ({len(d)} contre {len(r)}) — gain par station non calculable")

    def _rmse(s: pd.DataFrame, col: str) -> pd.Series:
        return (s[col] - s["obs"]).pow(2).groupby(s["station_id"]).mean().pow(0.5)

    t = pd.DataFrame({
        "n_jours": d.groupby("station_id").size(),
        "obs_moyenne": d.groupby("station_id")["obs"].mean(),
        "rmse_cams": _rmse(d, "cams"),
        "rmse_deploye": _rmse(d, "pred"),
        "rmse_regle": _rmse(r, "pred"),
    }).reset_index()
    t["gain_reglage_pct"] = 100 * (1 - t["rmse_regle"] / t["rmse_deploye"])
    t.insert(0, "polluant", polluant)

    # La typologie n'est pas décorative : c'est elle qui a expliqué l'ordre des plis sur NO₂.
    st = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                         columns=["station_id", "typologie_zone", "type_station"])
    t = t.merge(st, on="station_id", how="left")

    # § 2 ter : exiger nommément ce qu'on croit avoir mesuré, avant d'écrire.
    attendues = ["station_id", "rmse_deploye", "rmse_regle", "gain_reglage_pct", "type_station"]
    if manque := [c for c in attendues if c not in t.columns]:
        raise SystemExit(f"colonnes absentes du rapport par station : {manque}")
    if t["gain_reglage_pct"].isna().any():
        raise SystemExit(f"{polluant} : gain non calculé sur "
                         f"{int(t['gain_reglage_pct'].isna().sum())} station(s)")

    med, pire, part = t["gain_reglage_pct"].median(), t["gain_reglage_pct"].min(), \
        100 * (t["gain_reglage_pct"] > 0).mean()
    print(f"  par station · {len(t)} stations · médiane {med:+.2f} % · "
          f"pire {pire:+.2f} % · {part:.0f} % améliorées", flush=True)
    return t


def main(polluants: list[str], algo: str, axe: str = "spatial") -> int:
    lignes = []
    # Le suffixe sépare les deux axes dans des fichiers DISTINCTS. Les écrire au même nom
    # ferait qu'une exécution temporelle écraserait la mesure spatiale sans rien dire, et
    # le dossier citerait un chiffre pour l'autre — le défaut « une variante écrase sa
    # jumelle » déjà payé sur ce dépôt.
    suf = "" if axe == "spatial" else f"_{axe}"
    for p in polluants:
        ligne, stations = mesurer(p, algo, axe)
        lignes.append(ligne)
        # La table s'écrit APRÈS chaque polluant, jamais à la fin : sur cette machine, un
        # lot qui garde tout en mémoire jusqu'au bout perd tout à la première coupure.
        stations.to_csv(RACINE / f"reports/gain_reglage_{p}{suf}_stations.csv", index=False)
        t = pd.DataFrame(lignes)
        attendues = ["polluant", "rmse_deploye", "rmse_regle", "gain_reglage_pct"]
        if manque := [c for c in attendues if c not in t.columns]:
            raise SystemExit(f"colonnes absentes du rapport : {manque}")
        for _, l in t.iterrows():
            (pd.DataFrame([l]).to_csv(
                RACINE / f"reports/gain_reglage_{l['polluant']}{suf}.csv", index=False))
    print(f"Écrit : {len(lignes)} fichier(s) reports/gain_reglage_<polluant>{suf}.csv")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3", choices=tuple(NOM))
    a.add_argument("--algo", default="lgbm", choices=("lgbm", "xgb"))
    a.add_argument("--tous", action="store_true", help="les quatre polluants à la suite")
    a.add_argument("--axe", default="spatial", choices=("spatial", "temporel"),
                   help="spatial : stations jamais vues (défaut) · "
                        "temporel : 2ᵈᵉ moitié du calendrier, l'axe du protocole adverse")
    n = a.parse_args()
    raise SystemExit(main(list(NOM) if n.tous else [n.polluant], n.algo, n.axe))
