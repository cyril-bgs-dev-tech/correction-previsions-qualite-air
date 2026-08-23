#!/usr/bin/env python3
"""Leur méthode exacte, à LEUR point de départ — CHIMERE brut, pas la médiane CAMS.

La question, et ce qu'elle ajoute à `krigeage_du_biais.py`
-----------------------------------------------------------
Ce script-là oppose déjà leur **famille de méthode** — interpoler spatialement le biais
récent — à la nôtre, sur **nos** entrées (la médiane de l'ensemble CAMS). Il manquait la
moitié de la question : PREV'AIR ne part pas de CAMS, **il part de CHIMERE**.

Or CHIMERE est un **membre de l'ensemble CAMS**, et ce dépôt archive les membres aux
stations. On peut donc rejouer leur chaîne complète — *CHIMERE brut → krigeage du biais* —
et la comparer à la nôtre sur **exactement les mêmes lignes**.

Ce que cela permet de séparer, et qu'aucune comparaison antérieure ne séparait :

| | ce qui change | ce que ça isole |
|---|---|---|
| CHIMERE brut → CAMS médiane | le **point de départ** | l'apport de l'ensemblisme |
| brut → + krigeage | la **méthode**, à départ égal | l'apport du krigeage |
| krigeage → notre correction | la **méthode**, à départ égal | l'apport de l'apprentissage |
| notre correction → + krigeage | le **cumul** | ce que le voisinage ajoute encore |

⚠️ CE N'EST PAS PREV'AIR, et la nuance est décisive
-----------------------------------------------------
Leur CHIMERE tourne en configuration **nationale** : maille plus fine, inventaire français,
assimilation de données. Le nôtre est le membre **européen à 10 km** de l'ensemble CAMS.
Un score obtenu ici ne dit rien de leur produit — il dit ce que leur **chaîne de méthode**
vaut sur les entrées dont nous disposons. Toute citation doit porter cette réserve.

⚠️ Le grain est celui de la CIBLE, obtenu par les mêmes helpers que `agreger_journalier` —
max 8 h pour l'ozone, max horaire pour le NO₂, moyenne pour les particules. Réagréger
CHIMERE à la main ferait diverger deux grains qui doivent être identiques, et l'écart
passerait pour un écart de modèle.

Usage : python3 scripts/duel_chimere_krigeage.py --polluant O3 --horizon 2
Sortie : reports/duel_chimere_<polluant>_h<horizon>.csv
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

from cible_journaliere import (  # noqa: E402
    GRANDEUR_PAR_POLLUANT, _agregation, _preparer, agreger_journalier,
)
from double_aveugle_journalier import DEFAUT, ajuster, charger, colonnes_admises  # noqa: E402
from krigeage_du_biais import DECALAGE, biais_interpole, gain, matrice_distances  # noqa: E402
from leviers_36mois import _charger_famille, joindre_feux, joindre_membres  # noqa: E402

# La variante retenue est celle qui a GAGNÉ le balayage de `krigeage_du_biais` sur PM10
# (fenêtre 30 j, portée 200 km, p=1, donneuses de même typologie). La figer plutôt que la
# re-balayer ici est délibéré : re-choisir la meilleure variante SUR CHAQUE départ
# donnerait à leur méthode deux chances et à la nôtre une seule.
VARIANTE = {"nom": "30 j · 200 km · p=1 · MÊME TYPOLOGIE",
            "fenetre": 30, "k": 0, "rayon": 200.0, "p": 1.0, "typo": True}


def chimere_journalier(polluant: str, grandeur: str, debut: str, fin: str) -> pd.DataFrame | None:
    """CHIMERE brut au grain de la cible, depuis les membres de l'ensemble CAMS."""
    t = _charger_famille(f"membres_metropole_{polluant.lower()}_*.parquet", None, debut, fin)
    if t is None or "chimere" not in t.columns:
        return None
    t = t.dropna(subset=["chimere"]).sort_values(["station_id", "timestamp_utc"]).copy()
    t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.floor("D").dt.tz_localize(None)
    # Mêmes helpers que `agreger_journalier` : la préparation horaire (moyenne glissante
    # 8 h pour l'ozone) PUIS l'agrégation du jour.
    t["_prep"] = _preparer(t, "chimere", grandeur)
    agr = (t.groupby(["station_id", "jour"])["_prep"].agg(_agregation(grandeur))
             .reset_index().rename(columns={"_prep": "chimere_jour"}))
    return agr


def krige(d: pd.DataFrame, colonne_base: str, piv_index, ids, dist, memes) -> np.ndarray:
    """La prévision krigée par LEUR méthode : base + biais récent interpolé, par ligne.

    ⚠️ `biais_interpole` rend une matrice **jours × stations**, pas un vecteur de lignes.
    La remettre en lignes n'est pas un détail de forme : sans `champ[lig, col]`, la
    soustraction lève (mesuré) — ou pire, diffuserait silencieusement si les tailles
    coïncidaient par hasard.

    Et le repli est **compté, jamais tu** (§ 2 quater) : le krigeage ne rend rien là où
    aucune station donneuse n'est disponible dans la fenêtre. Replier sur le brut conserve
    le périmètre ; laisser des NaN le rétrécirait en silence, et l'écart mesuré porterait
    alors sur d'autres lignes que celles annoncées.
    """
    base = d[colonne_base].to_numpy(dtype=float)
    biais = d["valeur"].to_numpy(dtype=float) - base
    piv = (pd.DataFrame({"jour": d["jour"], "station_id": d["station_id"], "_b": biais})
           .pivot_table(index="jour", columns="station_id", values="_b", aggfunc="mean")
           .reindex(columns=ids).reindex(piv_index))
    roul = piv.shift(DECALAGE).rolling(
        VARIANTE["fenetre"], min_periods=max(2, VARIANTE["fenetre"] // 3)).mean()
    champ = biais_interpole(roul, dist, VARIANTE["k"], VARIANTE["rayon"], VARIANTE["p"],
                            memes if VARIANTE["typo"] else None)
    lig = pd.Index(piv.index).get_indexer(pd.DatetimeIndex(d["jour"].to_numpy()))
    col = d["station_id"].map({s: i for i, s in enumerate(ids)}).to_numpy()
    if (lig < 0).any() or pd.isna(col).any():
        raise SystemExit(f"krigeage {colonne_base} : {int((lig < 0).sum())} jours et "
                         f"{int(pd.isna(col).sum())} stations hors du pivot — "
                         f"l'appariement ligne↔champ est faux, pas incomplet")
    corr = champ[lig, col.astype(int)]
    replis = ~np.isfinite(corr)
    print(f"  krigeage sur {colonne_base:13s} · couverture {100 * (~replis).mean():5.1f} %"
          + (f" · {replis.sum():,} lignes repliées sur le brut" if replis.any() else ""),
          flush=True)
    return np.where(replis, base, base + corr)


def main(polluant: str, horizon: int, n_spa: int) -> int:
    t0 = time.time()
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    # Jamais `strftime` sur une colonne de dates ici : c'est le chemin qui tombe sur cette
    # machine (CLAUDE.md). Arithmétique entière, puis formatage d'un petit tableau unique.
    ym = d["jour"].dt.year.to_numpy() * 100 + d["jour"].dt.month.to_numpy()
    d["mois"] = pd.Series(ym, index=d.index).map(lambda v: f"{v // 100}-{v % 100:02d}")

    debut, fin = str(ym.min()), str(ym.max())
    ch = chimere_journalier(polluant, grandeur, debut, fin)
    if ch is None:
        raise SystemExit(f"CHIMERE introuvable dans les membres de {polluant} — "
                         f"ce duel exige la colonne `chimere`")
    avant = len(d)
    d = d.merge(ch, on=["station_id", "jour"], how="left")
    couv = 100 * d["chimere_jour"].notna().mean()
    print(f"{polluant} · {avant:,} jours-station · CHIMERE couvre {couv:.1f} %", flush=True)
    # Le duel se joue sur les lignes où LES DEUX départs existent, sinon on comparerait
    # deux corpus. Le nombre de lignes perdues est imprimé, jamais tu (§ 2 quater).
    d = d.dropna(subset=["chimere_jour"]).reset_index(drop=True)
    print(f"  → {len(d):,} lignes communes aux deux départs "
          f"({100 * len(d) / avant:.1f} % du corpus)", flush=True)

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    ids = np.sort(d["station_id"].unique())
    typo, cols_typo = charger_typologie(ids)
    d = d.merge(typo, on="station_id", how="left")
    dist, st = matrice_distances(ids)
    memes = None
    if "type_station" in st:
        tt = st["type_station"].fillna("?").to_numpy()
        memes = (tt[:, None] == tt[None, :]).astype(float)

    piv_index = pd.date_range(d["jour"].min(), d["jour"].max(), freq="D")
    # Les deux krigeages voyagent comme COLONNES de `d`, jamais comme tableaux à côté :
    # les jointures qui suivent peuvent réordonner ou dupliquer des lignes, et un tableau
    # gardé à part se désalignerait sans rien lever — le score resterait plausible.
    d["_krig_cams"] = krige(d, "cams_jour", piv_index, ids, dist, memes) - d["cams_jour"].to_numpy()
    d["_krig_chimere"] = krige(d, "chimere_jour", piv_index, ids, dist, memes)
    print(f"  krigeage ({VARIANTE['nom']}) calculé sur les deux départs", flush=True)

    familles = list(cols_typo)
    for nom_f, fn in (("feux", lambda x: joindre_feux(x, debut, fin)),
                      ("membres", lambda x: joindre_membres(x, polluant, debut, fin))):
        avant_jointure = len(d)
        try:
            d, ajout = fn(d)
            familles += ajout
            print(f"  + {nom_f} : {len(ajout)} colonnes", flush=True)
        except Exception as e:  # noqa: BLE001
            print(f"  ⚠️ {nom_f} indisponible : {type(e).__name__} — {e}", flush=True)
        if len(d) != avant_jointure:
            raise SystemExit(f"la jointure {nom_f} a changé le nombre de lignes "
                             f"({avant_jointure:,} → {len(d):,}) : le duel ne porterait "
                             f"plus sur les mêmes lignes")

    rng = np.random.default_rng(20240801)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    mois = np.sort(d["mois"].unique())
    modes = {"nous — tous leviers déployables": base + familles,
             "nous + correction krigée": base + familles + ["_krig_cams"]}
    pred = {k: np.full(len(d), np.nan) for k in modes}
    faits, prevus = 0, 0
    for i, m in enumerate(mois):
        prevus += 1
        dans = d["station_id"].isin(groupes[i % n_spa])
        m_te, m_tr = (d["mois"] == m) & dans, (d["mois"] != m) & ~dans
        te, tr = d[m_te], d[m_tr]
        if len(te) < 200 or len(tr) < 1000:
            continue
        faits += 1
        w = np.flatnonzero(m_te.to_numpy())
        for nom, colonnes in modes.items():
            pred[nom][w] = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
    print(f"  plis : {faits} exécutés sur {prevus} prévus", flush=True)

    ok = np.ones(len(d), bool)
    for v in pred.values():
        ok &= np.isfinite(v)
    o = d["valeur"].to_numpy()[ok]
    c_cams = d["cams_jour"].to_numpy()[ok]
    c_chim = d["chimere_jour"].to_numpy()[ok]

    systemes = [
        ("CHIMERE brut (membre européen 10 km)", c_chim, "chimere"),
        ("CHIMERE + krigeage du biais  ← LEUR CHAÎNE", d["_krig_chimere"].to_numpy()[ok], "chimere"),
        ("CAMS médiane brute", c_cams, "cams"),
        ("CAMS + krigeage du biais", (d["cams_jour"].to_numpy() + d["_krig_cams"].to_numpy())[ok], "cams"),
        ("CAMS + notre correction", pred["nous — tous leviers déployables"][ok], "cams"),
        ("CAMS + notre correction + krigeage", pred["nous + correction krigée"][ok], "cams"),
    ]
    print(f"\n{'═' * 84}\nÀ ARMES ÉGALES — mêmes {ok.sum():,} lignes, station cachée · "
          f"{polluant} J+{horizon - 1}\n{'═' * 84}")
    print(f"  {'système':44s} {'RMSE':>7s} {'/CHIMERE':>9s} {'/CAMS':>8s}")
    lignes = []
    for nom, x, depart in systemes:
        rmse = float(np.sqrt(np.mean((x - o) ** 2)))
        print(f"  {nom:44s} {rmse:7.2f} {gain(o, c_chim, x):8.2f}% {gain(o, c_cams, x):7.2f}%")
        lignes.append({"polluant": polluant, "horizon": horizon, "systeme": nom,
                       "depart": depart, "rmse": rmse,
                       "gain_vs_chimere_pct": gain(o, c_chim, x),
                       "gain_vs_cams_pct": gain(o, c_cams, x), "n": int(ok.sum()),
                       "variante_krigeage": VARIANTE["nom"]})

    print("\n⚠️ CE N'EST PAS PREV'AIR : leur CHIMERE est NATIONAL (maille fine, inventaire")
    print("   français, assimilation) ; le nôtre est le membre EUROPÉEN à 10 km de CAMS.")
    print("   C'est leur chaîne de MÉTHODE sur les entrées dont nous disposons.")

    sortie = RACINE / f"reports/duel_chimere_{polluant}_h{horizon}.csv"
    pd.DataFrame(lignes).to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} · {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    v = vars(a.parse_args())
    raise SystemExit(main(v["polluant"], v["horizon"], v["plis_spatiaux"]))
