#!/usr/bin/env python3
"""Quelle part des stations notre correction DÉGRADE-T-ELLE ?

Pourquoi ce script existe
-------------------------
Un ancien `REPRISE.md` annonçait « 23 % des stations dégradées ». Vérifié le 11/08 : **ce
chiffre ne trace nulle part** — ni dans un CSV, ni dans un script, ni dans `VERITE_DOSSIER`.
La réserve, elle, est réelle : une correction apprise ne peut pas améliorer tout le monde.
Le choix posé par la file d'attente était binaire — *le re-mesurer ou cesser de le chiffrer*.
Ceci le re-mesure.

Ce qu'il ne fait PAS : réajuster quoi que ce soit. Les prédictions hors-échantillon sont
déjà persistées par `oof_double_aveugle.py` avec leur `station_id` ; il n'y a qu'à les
agréger. Aucun LightGBM n'est rappelé, donc aucune exposition au défaut de plateforme.

Les trois épreuves ne répondent PAS à la même question, et le chiffre change avec elle :
  · `spatiale`       — station CACHÉE, mois vu     → déploiement sur un site non instrumenté
  · `temporelle`     — station vue, mois CACHÉ     → le régime normal d'exploitation
  · `double aveugle` — les deux cachés             → l'épreuve la plus dure du dossier
Citer « X % de stations dégradées » sans nommer l'épreuve ne veut rien dire (§ « citer un
gain exige trois mots »).
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
OOF = RACINE / "data/interim/oof"
ATTENDUES = ["polluant", "epreuve", "n_stations", "n_degradees", "part_degradees_pct",
             "gain_median_pct", "gain_median_degradees_pct", "perte_pire_pct",
             "n_min_par_station", "n_stations_ecartees", "variante"]


def rmse(err: np.ndarray) -> float:
    return float(np.sqrt(np.mean(err ** 2)))


def fichier(polluant: str, horizon: int, variante: str) -> Path | None:
    """Le fichier OOF du polluant, pour la variante DEMANDÉE — jamais devinée.

    La variante n'est pas un détail d'implémentation : c'est la moitié du protocole. Les OOF
    du 03/08 mélangeaient les options — NO2 et PM10 avec `_typo`, O3 et PM25 sans — et croiser
    ces quatre-là dans une seule table produisait quatre lignes justes et une comparaison
    fausse (« une variante écrase sa jumelle »). Elle se demande donc explicitement, et elle
    voyage jusqu'au rapport pour qu'aucune citation ne puisse s'en passer.

    Le mode `auto` reste utilisable quand une seule variante existe, et **lève dès qu'il y en
    a deux** : zéro correspondance et deux correspondances sont toutes deux des erreurs
    (§ 2 bis), et choisir à la place de l'appelant serait décider du protocole en silence.
    """
    if variante == "auto":
        cands = sorted(OOF.glob(f"oof_{polluant}_h{horizon}*.parquet"))
        if len(cands) > 1:
            raise SystemExit(
                f"{polluant} h{horizon} : {len(cands)} variantes coexistent — "
                f"{[c.name for c in cands]}. Nommer celle qu'on veut avec --variante.")
        return cands[0] if cands else None
    suffixe = "" if variante == "base" else f"_{variante}"
    f = OOF / f"oof_{polluant}_h{horizon}{suffixe}.parquet"
    return f if f.exists() else None


def mesurer(polluant: str, horizon: int, n_min: int, demandee: str) -> list[dict]:
    f = fichier(polluant, horizon, demandee)
    if f is None:
        print(f"  ⚠️ {polluant} : aucun OOF h{horizon} en variante « {demandee} » — sauté",
              flush=True)
        return []
    variante = f.stem.replace(f"oof_{polluant}_h{horizon}", "").lstrip("_") or "base"
    d = pd.read_parquet(f, columns=["epreuve", "station_id", "valeur", "cams_jour", "pred"])

    # § 2 bis — compter le reçu contre le demandé, et refuser une colonne plate.
    if d["pred"].std() == 0:
        raise SystemExit(f"{polluant} : prédictions constantes")
    manquants = d[["valeur", "cams_jour", "pred"]].isna().any(axis=1)
    if manquants.any():
        print(f"  ⚠️ {polluant} : {manquants.sum():,} ligne(s) incomplète(s) écartée(s)",
              flush=True)
        d = d[~manquants]

    print(f"  {polluant} · variante « {variante} » · {len(d):,} prédictions · "
          f"{d.station_id.nunique()} stations", flush=True)

    out = []
    for epreuve, g in d.groupby("epreuve", sort=False):
        par_st = g.groupby("station_id").apply(
            lambda s: pd.Series({
                "n": len(s),
                "rmse_cams": rmse(s["cams_jour"].to_numpy() - s["valeur"].to_numpy()),
                "rmse_nous": rmse(s["pred"].to_numpy() - s["valeur"].to_numpy())}),
            include_groups=False)

        # § 2 quater — un seuil d'effectif est une décision de protocole : il est appliqué
        # ET compté, jamais appliqué en silence.
        assez = par_st["n"] >= n_min
        ecartees = int((~assez).sum())
        if ecartees:
            print(f"    ⚠️ {epreuve:15s} {ecartees} station(s) sous {n_min} jours — écartées",
                  flush=True)
        st = par_st[assez]

        gain = 100 * (1 - st["rmse_nous"] / st["rmse_cams"])
        degr = gain < 0
        out.append({
            "polluant": polluant, "epreuve": epreuve,
            "n_stations": int(len(st)), "n_degradees": int(degr.sum()),
            "part_degradees_pct": float(100 * degr.mean()),
            "gain_median_pct": float(gain.median()),
            "gain_median_degradees_pct": float(gain[degr].median()) if degr.any() else np.nan,
            "perte_pire_pct": float(gain.min()),
            "n_min_par_station": n_min, "n_stations_ecartees": ecartees,
            "variante": variante})
    return out


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--n-min", type=int, default=100,
                   help="jours minimum par station pour qu'un RMSE de station ait un sens")
    a.add_argument("--variante", default="typo",
                   help="typo | base | auto — la MÊME pour les quatre polluants, sinon la "
                        "comparaison entre lignes ne veut rien dire")
    v = a.parse_args()

    lignes: list[dict] = []
    for p in ("O3", "NO2", "PM10", "PM25"):
        lignes += mesurer(p, v.horizon, v.n_min, v.variante)
    if not lignes:
        raise SystemExit("aucun OOF lu — rien à mesurer")

    # Le point de tout ce script : une seule variante pour les quatre. Si le lot n'a pas fini,
    # mieux vaut lever que publier une table dont les lignes ne se comparent pas.
    if (vues := set(pd.DataFrame(lignes)["variante"])) and len(vues) > 1:
        raise SystemExit(f"variantes mélangées : {sorted(vues)} — la table croiserait des "
                         f"protocoles différents. Relancer avec --variante explicite.")

    # § 2 ter — la table est construite APRÈS le dernier calcul, et les colonnes attendues
    # sont exigées nommément avant d'écrire.
    t = pd.DataFrame(lignes)
    if manque := [c for c in ATTENDUES if c not in t]:
        raise SystemExit(f"colonnes absentes du rapport : {manque}")

    ordre = ["spatiale", "temporelle", "double aveugle"]
    t["_o"] = t["epreuve"].map({e: i for i, e in enumerate(ordre)})
    t = t.sort_values(["_o", "polluant"]).drop(columns="_o").reset_index(drop=True)

    print(f"\n{'═' * 86}\nPART DES STATIONS QUE LA CORRECTION DÉGRADE · J+{v.horizon - 1} · "
          f"≥ {v.n_min} jours/station\n{'═' * 86}")
    print(f"  {'épreuve':16s} {'pol.':5s} {'stations':>8s} {'dégradées':>10s} "
          f"{'part':>7s} {'gain méd.':>10s} {'pire':>8s}")
    for e in ordre:
        for _, r in t[t["epreuve"] == e].iterrows():
            print(f"  {r.epreuve:16s} {r.polluant:5s} {r.n_stations:8d} {r.n_degradees:10d} "
                  f"{r.part_degradees_pct:6.1f}% {r.gain_median_pct:9.1f}% "
                  f"{r.perte_pire_pct:7.1f}%")

    sortie = RACINE / f"reports/stations_degradees_h{v.horizon}.csv"
    t.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {len(t)} lignes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
