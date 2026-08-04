#!/usr/bin/env python3
"""Le chiffre principal du dossier : que vaut le meilleur système **réellement déployable** ?

Pourquoi ce script existe, et pourquoi si tard
------------------------------------------------
Toutes les mesures du projet ajoutent **une famille à la fois**. La seule qui les cumule —
`+ TOUT` dans `leviers_36mois.py` — **inclut ERA5**, une réanalyse indisponible à l'heure
d'émission : son gain est un plafond, pas une performance.

Et le levier trouvé le 03/08 — les **six membres d'ensemble donnés séparément**, +9,4 % sur
l'ozone — n'entre dans aucune configuration.

Le dossier n'avait donc pas son chiffre central : *que vaut le meilleur système que l'on
puisse réellement mettre en service ?*

Les deux périmètres, qu'il ne faut jamais confondre
-----------------------------------------------------
| périmètre | entrées | où il s'applique |
|---|---|---|
| **PARTOUT** | prévision, terrain, typologie, feux, membres, biais krigé des voisins | **n'importe quel point**, instrumenté ou non |
| **AUX_STATIONS** | tout cela **plus la mémoire du site** | uniquement là où une station existe |

Publier le second en laissant croire au premier serait la faute la plus grave du dossier :
il vaut ~10 points de plus et ne se déploie que sur 476 points de France.

Ce qui est inclus, et pourquoi
--------------------------------
* **typologie** — statique, gratuite, +8,5 pts sur NO₂ ;
* **feux** — GFAS, +1,5 pt sur PM10 ; couverture partielle (s'arrête en 2025-05) ;
* **six membres + étendue** — la médiane d'ensemble jette de l'information que le modèle
  sait reprendre : **+9,4 %** mesuré sur l'ozone ;
* **biais krigé des voisins** — la famille PREV'AIR comme *prédicteur* et non comme
  concurrent : 30 jours, 200 km, donneurs de même typologie ;
* **mémoire du site** — seulement dans `AUX_STATIONS`.

Ce qui est **exclu**, et pourquoi : **ERA5** (réanalyse), **contexte spatial du champ CAMS**
(mesuré nul), **réglage d'hyperparamètres** (10 défaites sur 10).

Usage : python3 scripts/maximum_deployable.py --polluant NO2 --horizon 2
Sortie : reports/maximum_deployable_<polluant>_h<n>.csv
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
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from krigeage_du_biais import biais_interpole, matrice_distances  # noqa: E402

MEMBRES = ("chimere", "emep", "mocage", "silam", "lotos", "match")
DECALAGE = 2
KRIG = dict(fenetre=30, rayon=200.0, p=1.0)   # réglages retenus, mesurés le 03/08


def rmse(o, x) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int) -> int:
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
    debut, fin = d["mois"].min().replace("-", ""), d["mois"].max().replace("-", "")

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")
    familles: list[str] = list(cols_typo)
    inclus = {"typologie": len(cols_typo)}

    # ── Feux ─────────────────────────────────────────────────────────────────
    from leviers_36mois import joindre_feux  # noqa: PLC0415
    try:
        d, aj = joindre_feux(d, debut, fin)
        familles += aj
        inclus["feux"] = len(aj)
    except Exception as e:  # noqa: BLE001
        print(f"  ⚠️ feux indisponibles : {type(e).__name__}", flush=True)

    # ── Les six membres, SÉPARÉMENT — le levier du 03/08 ────────────────────
    fs = sorted(glob.glob(str(RACINE / f"data/processed/meteo/"
                              f"membres_metropole_{polluant.lower()}_*.parquet")))
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
        inclus["membres"] = len(pres) + 2
    else:
        print(f"  ⚠️ pas de membres pour {polluant} — lignes 'membres' absentes", flush=True)

    # ── Le biais krigé des voisins, comme PRÉDICTEUR ────────────────────────
    dist, st = matrice_distances(ids)
    t = st["type_station"].fillna("?").to_numpy()
    memes = (t[:, None] == t[None, :]).astype(float)
    d["_b"] = d["valeur"] - d["cams_jour"]
    piv = d.pivot_table(index="jour", columns="station_id", values="_b",
                        aggfunc="mean").reindex(columns=ids)
    piv = piv.reindex(pd.date_range(piv.index.min(), piv.index.max(), freq="D"))
    roul = piv.shift(DECALAGE).rolling(KRIG["fenetre"],
                                       min_periods=KRIG["fenetre"] // 3).mean()
    interp = biais_interpole(roul, dist, 0, KRIG["rayon"], KRIG["p"], memes)
    lig = pd.Index(piv.index).get_indexer(pd.DatetimeIndex(d["jour"]))
    col = d["station_id"].map({s: i for i, s in enumerate(ids)}).to_numpy()
    d["krig_biais"] = interp[lig, col]
    familles.append("krig_biais")
    inclus["biais krigé"] = 1

    # ── La référence qui décide : la chaîne AASQA simulée ────────────────────
    # Mesurer un gain contre CAMS brut flatte tout le monde — personne n'exploite CAMS
    # brut. La chaîne en service est un modèle déterministe corrigé par interpolation du
    # biais récent des voisins. On la reconstruit ici avec ses réglages **usuels**
    # (7 jours, 50 km, p=2, tous donneurs), pas avec les nôtres : une méthode réglée par
    # son adversaire n'est pas un adversaire.
    # ⚠️ Les membres ont des trous — `notna().mean() > 0.3` en tolère jusqu'à 70 %. Une
    # ancre qui hérite de ces trous rend une RMSE `nan` que rien ne signale : la référence
    # disparaît en silence. On replie donc sur CAMS ligne à ligne, ce que ferait aussi une
    # chaîne opérationnelle privée d'un de ses modèles, et on compte le repli.
    # ⚠️ L'ancrage sur CHIMERE+MOCAGE **européens** est injuste CONTRE eux : sur l'ozone,
    # CHIMERE porte un biais de +14,9 µg/m³ en configuration européenne et la chaîne
    # simulée sort alors PIRE que CAMS brut, ce qui gonflerait mécaniquement notre gain.
    # Leur chaîne réelle tourne en version nationale assimilée, donc au moins aussi bonne
    # que le MEILLEUR de nos deux substituts. On leur donne donc les deux ancrages et on
    # retient le meilleur : fausser la comparaison en sa faveur vaut la fausser contre soi.
    socle = d["cams_jour"].to_numpy()
    candidats: dict[str, np.ndarray] = {"médiane CAMS": socle}
    dispo = [m for m in ("chimere", "mocage")
             if m in d.columns and d[m].notna().mean() > 0.3]
    if dispo:                        # la médiane de deux valeurs est leur moyenne
        brut = d[dispo].mean(axis=1).to_numpy()
        replis = ~np.isfinite(brut)
        nom = "+".join(x.upper() for x in dispo)
        if replis.any():
            nom += " (CAMS en repli)"
            print(f"  ⚠️ {replis.sum():,} lignes sans {'/'.join(dispo)} "
                  f"({100 * replis.mean():.1f} %) — repli sur CAMS", flush=True)
        candidats[nom] = np.where(replis, socle, brut)

    # Le krigeage lui-même est une **option**, pas une obligation : sur PM2,5 aux réglages
    # usuels il dégrade son ancre, et aucune AASQA ne déploierait une correction qui
    # dégrade. Le concurrent a donc quatre configurations possibles, et on retient la
    # meilleure — c'est la seule façon de le mesurer à son plein potentiel.
    obs = d["valeur"].to_numpy()
    essais: dict[str, tuple[np.ndarray, float]] = {}

    def _noter(nom_c: str, x: np.ndarray) -> None:
        fini = np.isfinite(x) & np.isfinite(obs)
        essais[nom_c] = (x, rmse(obs[fini], x[fini]))
        print(f"  candidat « {nom_c} » : RMSE {essais[nom_c][1]:.3f}", flush=True)

    for nom_c, anc in candidats.items():
        _noter(nom_c, anc)                       # le modèle nu, sans correction
        d["_ba"] = obs - anc
        piva = d.pivot_table(index="jour", columns="station_id", values="_ba",
                             aggfunc="mean").reindex(columns=ids)
        piva = piva.reindex(pd.date_range(piva.index.min(), piva.index.max(), freq="D"))
        roula = piva.shift(DECALAGE).rolling(7, min_periods=2).mean()
        ca = biais_interpole(roula, dist, 0, 50.0, 2.0, None)
        liga = pd.Index(piva.index).get_indexer(pd.DatetimeIndex(d["jour"]))
        _noter(f"{nom_c} + krigeage usuel",
               np.where(np.isfinite(ca[liga, col]), anc + ca[liga, col], anc))
    nom_ancre = min(essais, key=lambda k: essais[k][1])
    aasqa = essais[nom_ancre][0]
    print(f"  → référence AASQA retenue : « {nom_ancre} » — la meilleure des "
          f"{len(essais)} configurations que la chaîne concurrente peut atteindre avec "
          f"nos entrées", flush=True)

    # ── La mémoire du site — AUX_STATIONS seulement ─────────────────────────
    from apport_observation_veille import variables_passees  # noqa: PLC0415
    p_mem, noms_mem = variables_passees(d.rename(columns={"valeur": "obs_jour"}))
    p_mem["jour"] = pd.to_datetime(p_mem["jour"]).dt.tz_localize(None)
    avant = len(d)
    d = d.merge(p_mem, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure mémoire : {avant:,} → {len(d):,}")

    print(f"{polluant} · {len(d):,} jours-station · {len(ids)} stations · "
          f"échéance {'J0' if horizon == 1 else f'J+{horizon - 1}'}")
    print(f"  familles PARTOUT : " + " · ".join(f"{k} ({v})" for k, v in inclus.items()))
    print(f"  + mémoire du site ({len(noms_mem)}) pour AUX_STATIONS", flush=True)

    # ── Les configurations, de la plus nue à la plus complète ───────────────
    modes = {
        "① base (terrain + calendrier)": base,
        "② + typologie seule": base + cols_typo,
        "③ MAXIMUM DÉPLOYABLE — partout": base + familles,
        "④ MAXIMUM — aux stations instrumentées": base + familles + noms_mem,
    }
    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    mois = np.sort(d["mois"].unique())
    pred = {k: np.full(len(d), np.nan) for k in modes}
    for i, mm in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_spa])
        mt, mr = (d["mois"] == mm) & dans, (d["mois"] != mm) & ~dans
        te, tr = d[mt], d[mr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        idx = np.flatnonzero(mt.to_numpy())
        for nom, colonnes in modes.items():
            pred[nom][idx] = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        if not np.isfinite(v).any():
            raise SystemExit(f"le mode « {nom} » n'a rien produit")
        ok &= np.isfinite(v)
    o, c = d["valeur"].to_numpy()[ok], d["cams_jour"].to_numpy()[ok]
    a = aasqa[ok]
    # La référence doit être définie partout où les modèles le sont, sinon la colonne
    # `/AASQA` sort en `nan` sans que rien ne le signale — c'est arrivé le 03/08.
    if not np.isfinite(a).all():
        raise SystemExit(f"référence AASQA indéfinie sur "
                         f"{int((~np.isfinite(a)).sum()):,} lignes évaluées")
    r_ref, r_aasqa = rmse(o, c), rmse(o, a)
    haut = o > np.quantile(o, 0.95)

    print(f"\n{'═' * 92}\nMAXIMUM DÉPLOYABLE · {ok.sum():,} prédictions · "
          f"station ET mois cachés\n{'═' * 92}")
    print(f"  {'configuration':40s} {'RMSE':>7s} {'/CAMS':>8s} {'/AASQA':>8s} "
          f"{'σ plis':>7s} {'RMSE top 5 %':>13s}")
    lignes = []
    d_ok = d[ok]
    reperes = [("CAMS brut — ensemble européen", c),
               (f"⓪ chaîne AASQA — {nom_ancre} + krigeage usuel", a)]
    for nom, x in reperes + [(n, pred[n][ok]) for n in modes]:
        r = rmse(o, x)
        par = pd.DataFrame({"m": d_ok["mois"].to_numpy(), "e": (x - o) ** 2})
        sg = par.groupby("m")["e"].mean().pow(0.5)
        print(f"  {nom:40s} {r:7.3f} {100 * (1 - r / r_ref):7.2f}% "
              f"{100 * (1 - r / r_aasqa):7.2f}% {sg.std():7.2f} "
              f"{rmse(o[haut], x[haut]):13.3f}")
        lignes.append({"polluant": polluant, "horizon": horizon, "configuration": nom,
                       "rmse": r, "gain_vs_cams_pct": 100 * (1 - r / r_ref),
                       "gain_vs_aasqa_pct": 100 * (1 - r / r_aasqa),
                       "rmse_top5pct": rmse(o[haut], x[haut]),
                       "ecart_type_plis": float(sg.std()), "n": int(ok.sum())})

    print(f"\n  Colonne /CAMS : contre le modèle brut — flatte tout le monde, personne ne")
    print(f"  l'exploite tel quel. Colonne /AASQA : contre la ligne ⓪, la chaîne en")
    print(f"  service. C'est la seule des deux qui situe le projet face à l'existant.")
    print(f"\n  ⚠️ La ligne ④ n'est déployable QU'AUX STATIONS INSTRUMENTÉES. La publier")
    print(f"     en laissant croire à la ③ serait la faute la plus grave du dossier.")
    print(f"  ⚠️ ERA5 est EXCLU de toutes les lignes : réanalyse, indisponible à l'émission.")
    print(f"  ⚠️ La ligne ⓪ s'ancre sur des modèles en configuration **européenne**, sans")
    print(f"     assimilation. La chaîne réelle des AASQA tourne en version nationale,")
    print(f"     plus fine et assimilée : elle est donc MEILLEURE que cette simulation, et")
    print(f"     le gain /AASQA est un **majorant** de notre avance réelle.")

    sortie = RACINE / f"reports/maximum_deployable_{polluant}_h{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux))
