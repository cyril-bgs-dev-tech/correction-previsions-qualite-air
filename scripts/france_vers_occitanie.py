#!/usr/bin/env python3
"""Entraîné sur la France sans l'Occitanie, évalué sur l'Occitanie — la question d'Atmo.

Pourquoi ce protocole plutôt que notre double aveugle
------------------------------------------------------
Toutes nos évaluations sont **nationales**. Le destinataire est **régional**. Un gain moyen
sur 492 stations françaises ne répond pas à la question qu'une AASQA d'Occitanie se pose :
*« ce système, appliqué chez nous, que vaudrait-il ? »*

Notre double aveugle cache un tiers des stations tirées au hasard sur toute la France. Ici
on fait plus simple et plus dur :

    entraînement : les 457 stations HORS Occitanie, et hors du mois testé
    test         : les 35 stations d'Occitanie, dans le mois testé

L'indépendance spatiale est **totale par construction** — pas un tirage, une frontière. Et
le blocage temporel s'y ajoute. Aucune station d'Occitanie n'a jamais contribué à
l'apprentissage, ce qui est exactement la situation d'un système transféré.

Les quatre systèmes comparés, sur les mêmes lignes
----------------------------------------------------
| système | entrées | ce qu'il représente |
|---|---|---|
| `CAMS` | — | la prévision brute, notre référence |
| `P7` | 7 jours de résidu du site | **la solution triviale**, sans aucun apprentissage |
| `SANS_CAPTEUR` | CAMS + terrain + typologie | un lieu sans station |
| `COMPLET` | + mémoire locale du site | une station existante, jamais apprise |

`P7` n'est pas un détail : sur le corpus national, **il récupère 43 % de l'erreur du NO₂
sans modèle**, et le LightGBM complet n'ajoute que 2,7 points. Toute revendication qui
l'omet est trompeuse.

⚠️ Réserves à porter
---------------------
* Le périmètre « Occitanie » est celui de `panel_occitanie_ds2` — **35 stations**, soit
  environ deux tiers du réseau permanent d'Atmo Occitanie (53 stations en 2025). L'emprise
  couvre lat 42,7–44,4 : le nord de la région (Lot, Aveyron, Lozère) est sous-représenté.
* Nous corrigeons **CAMS Europe**, pas la chaîne CHIMERE d'Atmo Occitanie. Un gain ici ne
  démontre pas un gain contre leur produit, qui tourne plus fin, assimilé et déjà adapté
  statistiquement.
* Les stations frontalières hors région restent dans l'**entraînement** — c'est voulu :
  interdire à un modèle d'apprendre d'une station située à 20 km de la frontière
  administrative n'aurait aucun sens physique.

Usage : python3 scripts/france_vers_occitanie.py --polluant PM10 --horizon 2
Sortie : reports/france_vers_occitanie_<polluant>_h<n>.csv
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
    DEFAUT, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)

DECALAGE = 2  # jours par rapport à la cible — convention FAIRMODE pour J+1
SEUILS = {"PM10": 50.0, "PM25": 50.0, "O3": 120.0, "NO2": 200.0}


def stations_occitanie() -> set[str]:
    """Le périmètre régional, lu dans le panel du projet — pas redéfini ici."""
    f = RACINE / "data/processed/panel_occitanie_ds2.parquet"
    if not f.exists():
        raise SystemExit(f"absent : {f.name} — le périmètre régional n'est pas défini")
    s = set(pd.read_parquet(f, columns=["station_id"])["station_id"].unique())
    if not 10 <= len(s) <= 120:
        raise SystemExit(f"{len(s)} stations d'Occitanie — invraisemblable, ne pas continuer")
    return s


def biais_glissant(d: pd.DataFrame) -> pd.Series:
    """P7 — moyenne du résidu sur 7 jours, décalée de 2. Aucun apprentissage.

    Série réindexée au jour calendaire : un `shift(2)` sur des lignes trouées prendrait
    « deux enregistrements plus haut », qui peut dater de trois semaines.
    """
    morceaux = []
    for st, g in d.groupby("station_id", sort=False):
        g = g.set_index("jour").sort_index()
        plein = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="D"))
        res = (plein["valeur"] - plein["cams_jour"]).shift(DECALAGE)
        s = pd.DataFrame(index=plein.index)
        s["P7"] = plein["cams_jour"] + res.rolling(7, min_periods=3).mean()
        s["station_id"] = st
        morceaux.append(s.reset_index(names="jour"))
    return pd.concat(morceaux, ignore_index=True)


def scores(o: np.ndarray, x: np.ndarray) -> dict:
    return {"rmse": float(np.sqrt(np.mean((x - o) ** 2))),
            "biais": float(np.mean(x - o)),
            "correlation": float(np.corrcoef(o, x)[0, 1]) if o.std() and x.std() else np.nan}


def contingence(v: np.ndarray, a: np.ndarray) -> dict:
    tp, fp, fn = int((v & a).sum()), int((~v & a).sum()), int((v & ~a).sum())
    return {"TP": tp, "FP": fp, "FN": fn,
            "POD": tp / (tp + fn) if tp + fn else np.nan,
            "precision": tp / (tp + fp) if tp + fp else np.nan,
            "CSI": tp / (tp + fp + fn) if tp + fp + fn else np.nan}


def main(polluant: str, horizon: int) -> int:
    depart = time.time()
    occ = stations_occitanie()
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
    avant = len(d)
    d = d.merge(mem, on=["station_id", "jour"], how="left")
    d = d.merge(biais_glissant(d), on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure : {avant:,} → {len(d):,} lignes")

    d["en_occitanie"] = d["station_id"].isin(occ)
    n_occ = int(d["en_occitanie"].sum())
    echeance = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{polluant} · échéance **{echeance}** · {len(d):,} jours-station\n"
          f"  Occitanie : {d.loc[d.en_occitanie, 'station_id'].nunique()} stations · "
          f"{n_occ:,} jours-station ({100 * n_occ / len(d):.1f} %)\n"
          f"  hors région : {d.loc[~d.en_occitanie, 'station_id'].nunique()} stations "
          f"— **l'entraînement, jamais le test**", flush=True)
    if n_occ < 5000:
        raise SystemExit(f"{n_occ} jours-station en Occitanie — trop peu, ne pas conclure")

    # ⚠️ L'ANCRE compte autant que les prédicteurs. Ancrer sur `P7` plutôt que sur CAMS
    # revient à retirer d'abord le biais local — sans apprentissage — puis à ne demander au
    # modèle que ce que P7 ne voit pas. Mesuré nécessaire : en Occitanie, P7 seul bat le
    # modèle ancré sur CAMS de 15 % sur le NO₂ (RMSE 15,54 contre 18,28), parce qu'il
    # s'adapte par station là où le modèle transporte un biais appris ailleurs.
    modes = {"COMPLET": (base + cols_typo + noms_mem, "cams_jour"),
             "SANS_CAPTEUR": (base + cols_typo, "cams_jour"),
             "COMPLET_SUR_P7": (base + cols_typo + noms_mem, "P7")}
    pred = {k: np.full(len(d), np.nan) for k in modes}

    mois = np.sort(d["mois"].unique())
    for m in mois:
        # Test : Occitanie ∩ mois m. Entraînement : hors Occitanie ∩ hors mois m.
        m_test = d["en_occitanie"] & (d["mois"] == m)
        m_train = (~d["en_occitanie"]) & (d["mois"] != m)
        te, tr = d[m_test], d[m_train]
        if len(te) < 100 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(m_test.to_numpy())
        for nom, (colonnes, ancre) in modes.items():
            pred[nom][idx] = ajuster(DEFAUT, tr, te, colonnes, ancre)

    for k, v in pred.items():
        d[k] = v
    e = d[d["en_occitanie"]].copy()
    e = e[e[["valeur", "cams_jour", "P7", "COMPLET", "SANS_CAPTEUR",
             "COMPLET_SUR_P7"]].notna().all(axis=1)]
    o = e["valeur"].to_numpy()
    print(f"  {len(e):,} jours-station évalués · {e['mois'].nunique()} mois · "
          f"{e['station_id'].nunique()} stations", flush=True)

    r_cams = scores(o, e["cams_jour"].to_numpy())["rmse"]
    lignes = []
    print(f"\n{'═' * 74}\nENTRAÎNÉ HORS OCCITANIE, ÉVALUÉ EN OCCITANIE · {echeance}\n"
          f"{'═' * 74}")
    print(f"  {'système':16s} {'RMSE':>8s} {'gain/CAMS':>10s} {'biais':>8s} {'r':>7s} "
          f"{'apprentissage'}")
    for nom, col, appr in (("CAMS brut", "cams_jour", "aucun"),
                           ("P7 · triviale", "P7", "**aucun**"),
                           ("SANS_CAPTEUR", "SANS_CAPTEUR", "LightGBM"),
                           ("COMPLET", "COMPLET", "LightGBM"),
                           ("COMPLET sur P7", "COMPLET_SUR_P7", "LightGBM ⭐")):
        s = scores(o, e[col].to_numpy())
        g = 100 * (1 - s["rmse"] / r_cams)
        print(f"  {nom:16s} {s['rmse']:8.3f} {g:9.2f}% {s['biais']:+8.2f} "
              f"{s['correlation']:7.3f} {appr}")
        lignes.append({"polluant": polluant, "echeance": echeance, "systeme": nom,
                       "gain_pct": g, "n": len(e), **s})

    # ── Dépassements, au seuil réglementaire du polluant ──────────────────────────
    seuil = SEUILS[polluant]
    v = o > seuil
    print(f"\n  Dépassements > {seuil:.0f} µg/m³ : {int(v.sum())} sur {len(e):,} "
          f"({100 * v.mean():.2f} %)")
    if v.sum() >= 10:
        print(f"  {'système':16s} {'TP':>4s} {'FP':>4s} {'FN':>4s} {'POD':>7s} "
              f"{'précision':>10s} {'CSI':>7s}")
        for nom, col in (("CAMS brut", "cams_jour"), ("P7 · triviale", "P7"),
                         ("SANS_CAPTEUR", "SANS_CAPTEUR"), ("COMPLET", "COMPLET"),
                         ("COMPLET sur P7", "COMPLET_SUR_P7")):
            c = contingence(v, e[col].to_numpy() > seuil)
            print(f"  {nom:16s} {c['TP']:4d} {c['FP']:4d} {c['FN']:4d} {c['POD']:7.3f} "
                  f"{c['precision']:10.3f} {c['CSI']:7.3f}")
            lignes.append({"polluant": polluant, "echeance": echeance,
                           "systeme": f"{nom}_dépassements", "seuil": seuil, **c})
    else:
        print(f"  ⚠️ moins de 10 dépassements — mesuré, pas conclu.")

    # ── Par station : où le transfert marche, et où il échoue ────────────────────
    par = e.groupby("station_id").apply(
        lambda g: pd.Series({
            "n": len(g), "type": g["type_station"].iloc[0] if "type_station" in g else "?",
            "rmse_cams": scores(g["valeur"].to_numpy(), g["cams_jour"].to_numpy())["rmse"],
            "rmse_complet": scores(g["valeur"].to_numpy(),
                                   g["COMPLET"].to_numpy())["rmse"]}),
        include_groups=False)
    par["gain_pct"] = 100 * (1 - par["rmse_complet"] / par["rmse_cams"])
    print(f"\n  Par station — {int((par['gain_pct'] > 0).sum())}/{len(par)} améliorées")
    print(f"    médiane {par['gain_pct'].median():+.1f} % · "
          f"pire {par['gain_pct'].min():+.1f} % · meilleure {par['gain_pct'].max():+.1f} %")
    par.sort_values("gain_pct").to_csv(
        RACINE / f"reports/france_vers_occitanie_{polluant}_h{horizon}_stations.csv")

    sortie = RACINE / f"reports/france_vers_occitanie_{polluant}_h{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\n⚠️ Aucune station d'Occitanie n'a servi à l'apprentissage. Mais nous")
    print(f"   corrigeons CAMS Europe, pas la chaîne CHIMERE d'Atmo Occitanie.")
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="PM10")
    a.add_argument("--horizon", type=int, default=2, help="2 = J+1 réel (échéances 25-48 h)")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon))
