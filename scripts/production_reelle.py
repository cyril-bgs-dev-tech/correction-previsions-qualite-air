#!/usr/bin/env python3
"""Le système en **conditions d'exploitation** — origine glissante, tout l'historique.

Pourquoi ce protocole, et en quoi il diffère du double aveugle
---------------------------------------------------------------
Le double aveugle cache **station et mois** : il mesure ce que vaut le système sur un site
**non instrumenté**, jamais vu. C'est la bonne question pour la généralisation spatiale, et
c'est le chiffre honnête du dossier.

Ce n'est pas la question d'exploitation. Une AASQA prévoit pour **son propre réseau** : les
stations sont connues, elles remontent leurs mesures, et le modèle se réentraîne
périodiquement sur tout l'historique disponible. Le protocole qui reproduit cela est
l'**origine glissante** : pour le mois `M`, entraîner sur **tout ce qui précède
strictement `M`**, prédire `M`, avancer d'un mois.

| protocole | ce qu'il mesure |
|---|---|
| double aveugle | déploiement sur un site **non instrumenté** |
| **origine glissante** | déploiement sur le **réseau existant** — le cas d'usage réel |

Aucun des deux ne remplace l'autre, et confondre leurs chiffres serait la faute la plus
facile à commettre ici. Les scores d'origine glissante sont **plus élevés**, légitimement :
le système dispose de plus d'information, exactement comme en service.

Ce qui est autorisé, et pourquoi
---------------------------------
* **mémoire du site** — les observations de la station à J−2 et avant. Disponibles en
  production à une station instrumentée ; les exclure fabriquerait une contrainte que
  l'exploitation n'a pas.
* **biais krigé des voisins**, **six membres**, **typologie**, **feux**, **terrain**.
* **moyenne de sept pertes** — mesuré le 03/08 : ≈ +1,8 % de plancher d'information sur
  les quatre polluants. Sept ajustements au lieu d'un, ce qui ne pose aucun problème en
  exploitation.

Ce qui reste **exclu** : **ERA5**, réanalyse indisponible à l'heure d'émission. Le système
resterait sinon indéployable, et le chiffre serait un plafond, pas une performance.

L'échéance
------------
`--horizon 1` par défaut, c'est-à-dire **J0** (échéances 1-24 h). C'est la seule échéance
où les membres d'ensemble existent, donc la seule où la chaîne concurrente est mesurable à
armes égales — cf. la découverte du 03/08 : le parquet des membres ne porte aucun axe
d'échéance et vaut J0.

Sortie : un versement ligne à ligne, dont dépendent toutes les pages de soutenance.

Usage  : python3 scripts/production_reelle.py --polluant O3 --debut 2025-01
Sortie : data/processed/predictions/production_<polluant>_h<n>.parquet
         reports/production_reelle_<polluant>_h<n>.csv
"""

from __future__ import annotations

import argparse
import glob
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, charger, colonnes_admises,
)
from krigeage_du_biais import biais_interpole, matrice_distances  # noqa: E402
from repousser_le_plancher import VARIANTES, _modele  # noqa: E402
from tableau_comparatif import NOM_POLLUANT, classe  # noqa: E402

MEMBRES = ("chimere", "emep", "mocage", "silam", "lotos", "match")
DECALAGE = 2
KRIG_NOUS = dict(fenetre=30, rayon=200.0, p=1.0)   # nos réglages, mesurés le 03/08
KRIG_AASQA = dict(fenetre=7, rayon=50.0, p=2.0)    # les réglages usuels de la famille
MIN_ENTRAINEMENT = 5_000


def rmse(o, x) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def _krigeage(d, ancre, ids, dist, lig_source, col, reglages, typo=None):
    """Biais récent des voisins, interpolé — décalé de 2 jours, donc sans fuite."""
    tmp = d[["jour", "station_id"]].copy()
    tmp["_b"] = d["valeur"].to_numpy() - ancre
    piv = tmp.pivot_table(index="jour", columns="station_id", values="_b",
                          aggfunc="mean").reindex(columns=ids)
    piv = piv.reindex(pd.date_range(piv.index.min(), piv.index.max(), freq="D"))
    roul = piv.shift(DECALAGE).rolling(reglages["fenetre"],
                                       min_periods=max(2, reglages["fenetre"] // 3)).mean()
    interp = biais_interpole(roul, dist, 0, reglages["rayon"], reglages["p"], typo)
    lig = pd.Index(piv.index).get_indexer(pd.DatetimeIndex(d["jour"]))
    return interp[lig, col]


def main(polluant: str, horizon: int, debut: str, moyenner: bool) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")
    d = d.sort_values(["jour", "station_id"]).reset_index(drop=True)
    deb_f, fin_f = d["mois"].min().replace("-", ""), d["mois"].max().replace("-", "")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")
    familles: list[str] = list(cols_typo)

    from leviers_36mois import joindre_feux  # noqa: PLC0415
    try:
        d, aj = joindre_feux(d, deb_f, fin_f)
        familles += aj
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ feux indisponibles : {type(e).__name__}", flush=True)

    # ── Les six membres, séparément ; et CHIMERE+MOCAGE pour la chaîne concurrente ──
    fs = sorted(glob.glob(str(RACINE / f"data/processed/meteo/"
                              f"membres_metropole_{polluant.lower()}_*.parquet")))
    a_membres = False
    if fs:
        m = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
        pres = [x for x in MEMBRES if x in m.columns and m[x].notna().any()]
        m["jour"] = pd.to_datetime(m["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
        agr = "max" if grandeur in ("max_8h", "max_horaire") else "mean"
        jm = m.groupby(["station_id", "jour"])[pres].agg(agr).reset_index()
        avant = len(d)
        d = d.merge(jm, on=["station_id", "jour"], how="left")
        if len(d) != avant:
            raise SystemExit(f"jointure membres : {avant:,} → {len(d):,}")
        d["memb_etendue"] = d[pres].max(axis=1) - d[pres].min(axis=1)
        d["memb_moyenne"] = d[pres].mean(axis=1)
        familles += pres + ["memb_etendue", "memb_moyenne"]
        a_membres = all(x in pres for x in ("chimere", "mocage"))

    dist, st = matrice_distances(ids)
    t = st["type_station"].fillna("?").to_numpy()
    memes = (t[:, None] == t[None, :]).astype(float)
    col = d["station_id"].map({s: i for i, s in enumerate(ids)}).to_numpy()
    socle = d["cams_jour"].to_numpy()

    # ── Notre biais krigé, comme prédicteur ─────────────────────────────────
    kb = _krigeage(d, socle, ids, dist, None, col, KRIG_NOUS, memes)
    d["krig_biais"] = kb
    familles.append("krig_biais")

    # ── La chaîne concurrente, en DEUX lignes qu'il ne faut pas confondre ───
    #
    # `aasqa_nomme` : la stratégie explicitement nommée — CHIMERE+MOCAGE + krigeage usuel.
    # `aasqa`       : la MEILLEURE des quatre configurations que le concurrent peut
    #                 atteindre avec nos entrées, krigeage compris ou non.
    #
    # ⚠️ Pourquoi les deux. En configuration **européenne** à 0,1° sans assimilation,
    # CHIMERE+MOCAGE est très mauvais sur O₃ et PM2,5 : mesuré le 04/08 à couverture pleine,
    # −13,0 % et −30,1 % contre CAMS brut. Aucune AASQA ne déploierait une correction pire
    # que son entrée. Prendre cette ligne comme référence gonflerait notre gain de 7 à 15
    # points contre un adversaire que personne n'exploite — le miroir exact de la faute
    # que la règle 4 ter interdit. La référence de tête est donc la MEILLEURE des quatre.
    candidats = {"médiane CAMS": socle}
    if a_membres:
        cm = d[["chimere", "mocage"]].mean(axis=1).to_numpy()
        candidats["CHIMERE+MOCAGE"] = np.where(np.isfinite(cm), cm, socle)
    obs_v = d["valeur"].to_numpy()
    essais: dict[str, np.ndarray] = {}
    for nom_c, anc in candidats.items():
        essais[nom_c] = anc
        ck = _krigeage(d, anc, ids, dist, None, col, KRIG_AASQA, None)
        essais[f"{nom_c} + krigeage usuel"] = np.clip(
            np.where(np.isfinite(ck), anc + ck, anc), 0, None)
    for nom_c, x in essais.items():
        f = np.isfinite(x) & np.isfinite(obs_v)
        print(f"  candidat concurrent « {nom_c} » : RMSE {rmse(obs_v[f], x[f]):.3f}",
              flush=True)
    nom_aasqa = min(essais, key=lambda k: rmse(obs_v[np.isfinite(essais[k])],
                                               essais[k][np.isfinite(essais[k])]))
    d["aasqa"] = essais[nom_aasqa]
    nomme = ("CHIMERE+MOCAGE + krigeage usuel" if a_membres
             else "médiane CAMS + krigeage usuel")
    d["aasqa_nomme"] = essais[nomme]
    print(f"  → référence retenue : « {nom_aasqa} » · ligne nommée conservée : "
          f"« {nomme} »", flush=True)

    # ── La mémoire du site — LÉGITIME ici : la station est instrumentée ─────
    from apport_observation_veille import variables_passees  # noqa: PLC0415
    p_mem, noms_mem = variables_passees(d.rename(columns={"valeur": "obs_jour"}))
    p_mem["jour"] = pd.to_datetime(p_mem["jour"]).dt.tz_localize(None)
    avant = len(d)
    d = d.merge(p_mem, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure mémoire : {avant:,} → {len(d):,}")
    predicteurs = base + familles + noms_mem

    mois = np.sort(d["mois"].unique())
    cibles = [m for m in mois if m >= debut]
    if not cibles:
        raise SystemExit(f"aucun mois ≥ {debut} — le corpus s'arrête en {mois[-1]}")
    ech = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{NOM_POLLUANT[polluant]} · {ech} · {len(d):,} jours-station · "
          f"{len(ids)} stations")
    print(f"  corpus {mois[0]} → {mois[-1]} · évaluation {cibles[0]} → {cibles[-1]} "
          f"({len(cibles)} mois)")
    print(f"  {len(predicteurs)} prédicteurs · chaîne concurrente : {nom_aasqa}")
    print(f"  pertes : {'moyenne des ' + str(len(VARIANTES)) if moyenner else 'L2 seule'}",
          flush=True)

    pred = np.full(len(d), np.nan)
    pred_l2 = np.full(len(d), np.nan)
    for i, mc in enumerate(cibles):
        m_te = (d["mois"] == mc).to_numpy()
        m_tr = (d["mois"] < mc).to_numpy()
        if m_tr.sum() < MIN_ENTRAINEMENT or m_te.sum() < 50:
            continue
        tr, te = d[m_tr], d[m_te]
        idx = np.flatnonzero(m_te)
        ya, aa = tr["valeur"].to_numpy(), tr["cams_jour"].to_numpy()
        ae = te["cams_jour"].to_numpy()
        sorties = []
        for nom, (obj, _, vers, retour) in VARIANTES.items():
            if not moyenner and nom != "① résidu · L2 (référence)":
                continue
            cible = vers(ya, aa)
            fini = np.isfinite(cible)
            if obj in ("gamma", "tweedie"):
                fini &= cible > 0
            if fini.sum() < 1000:
                continue
            mod = _modele(obj, DEFAUT, cible[fini]).fit(tr[predicteurs][fini],
                                                        cible[fini])
            x = np.clip(retour(mod.predict(te[predicteurs]), ae), 0, None)
            sorties.append(x)
            if nom.startswith("①"):
                pred_l2[idx] = x
        if sorties:
            pred[idx] = np.mean(sorties, axis=0)
        print(f"  {mc} · entraînement {m_tr.sum():>7,d} → test {m_te.sum():>6,d} · "
              f"{(time.time() - depart) / 60:5.1f} min", flush=True)

    ok = np.isfinite(pred) & np.isfinite(d["aasqa"].to_numpy())
    if not ok.any():
        raise SystemExit("aucune prédiction produite")
    o = d["valeur"].to_numpy()[ok]
    sortie = pd.DataFrame({
        "jour": d["jour"].to_numpy()[ok], "station_id": d["station_id"].to_numpy()[ok],
        "mois": d["mois"].to_numpy()[ok], "valeur": o,
        "cams": socle[ok], "aasqa": d["aasqa"].to_numpy()[ok],
        "aasqa_nomme": d["aasqa_nomme"].to_numpy()[ok],
        "nous": pred[ok], "nous_l2": pred_l2[ok]})

    crit = classe(o, polluant) >= 3
    print(f"\n{'═' * 92}\nCONDITIONS D'EXPLOITATION · {ok.sum():,} prédictions · "
          f"origine glissante\n{'═' * 92}")
    print(f"  {'système':44s} {'RMSE':>8s} {'/CAMS':>8s} {'/AASQA':>8s} {'r':>7s}")
    lignes = []
    r_cams, r_aasqa = rmse(o, sortie["cams"]), rmse(o, sortie["aasqa"])
    for nom, c in (("CAMS brut — ensemble européen", "cams"),
                   (f"chaîne concurrente NOMMÉE — {nomme}", "aasqa_nomme"),
                   (f"chaîne concurrente au MIEUX — {nom_aasqa}", "aasqa"),
                   ("notre modèle — L2 seule", "nous_l2"),
                   ("notre modèle — moyenne des sept pertes", "nous")):
        x = sortie[c].to_numpy()
        if not np.isfinite(x).all():
            continue
        r = rmse(o, x)
        print(f"  {nom[:44]:44s} {r:8.3f} {100 * (1 - r / r_cams):7.2f}% "
              f"{100 * (1 - r / r_aasqa):7.2f}% {np.corrcoef(o, x)[0, 1]:7.4f}")
        lignes.append({"polluant": polluant, "horizon": horizon, "systeme": nom,
                       "rmse": r, "gain_vs_cams_pct": 100 * (1 - r / r_cams),
                       "gain_vs_aasqa_pct": 100 * (1 - r / r_aasqa),
                       "r": float(np.corrcoef(o, x)[0, 1]),
                       "n": int(ok.sum()), "n_critiques": int(crit.sum()),
                       "mois_debut": cibles[0], "mois_fin": cibles[-1]})

    dossier = RACINE / "data/processed/predictions"
    dossier.mkdir(parents=True, exist_ok=True)
    f = dossier / f"production_{polluant}_h{horizon}.parquet"
    sortie.to_parquet(f, index=False)
    pd.DataFrame(lignes).to_csv(
        RACINE / f"reports/production_reelle_{polluant}_h{horizon}.csv", index=False)
    print(f"\n  ⚠️ Ces chiffres NE sont PAS ceux du double aveugle : ici la station est")
    print(f"     connue et sa mémoire est utilisée. C'est le cas d'usage d'exploitation")
    print(f"     sur réseau existant, pas la généralisation à un site non instrumenté.")
    print(f"\nÉcrit : {f.relative_to(RACINE)} ({len(sortie):,} lignes) · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=1)
    a.add_argument("--debut", default="2025-01")
    a.add_argument("--sans-moyenne", action="store_true",
                   help="n'ajuster que la perte L2, sans la moyenne des sept")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.debut, not n.sans_moyenne))
