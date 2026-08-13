#!/usr/bin/env python3
"""Ce que le RÉGLAGE par polluant vaut à leur méthode — sur LEUR départ, pas seulement le nôtre.

La question, et d'où elle vient
---------------------------------
`duel_chimere_krigeage.py` fige la variante de krigeage à celle qui a gagné le balayage de
`krigeage_du_biais.py` **sur PM10**, et le dit ainsi :

> « re-choisir la meilleure variante SUR CHAQUE départ donnerait à leur méthode deux
>   chances et à la nôtre une seule. »

C'est une précaution défendable, mais c'est une **affirmation non mesurée** : elle suppose
que le réglage par polluant leur donnerait un avantage, sans dire lequel. Or il se chiffre,
et il se chiffre sans apprentissage — le krigeage est du numpy.

> **Avant d'écrire « attention, cette comparaison est imparfaite », se demander : est-ce
> que je peux la rendre équitable ?** (`CLAUDE.md` § 4 ter)

Ce script répond. Il balaie les 100 variantes sur **les deux départs** — CHIMERE, celui de
leur chaîne, et la médiane CAMS, le nôtre — sur exactement les lignes du duel.

Les trois chiffres, et pourquoi il en faut trois
--------------------------------------------------
Prendre la meilleure de 100 variantes **sur les lignes qui la notent** n'est pas une
performance : c'est le biais de criblage, mesuré **×2 à ×4** sur ce dépôt. Le script rend
donc trois valeurs par départ, et la troisième est la seule citable :

1. **figée** — la variante du duel (30 j · 200 km · p=1 · même typologie). L'état publié.
2. **meilleure en aveugle de rien** — le minimum des 100 RMSE, choisi *et* noté sur les
   mêmes lignes. C'est un **majorant**, pas un score : il dit ce que le réglage pourrait
   donner au mieux si l'on trichait.
3. **choisie sur la 1ʳᵉ moitié du calendrier, notée sur la 2ᵈᵉ** — le réglage tel qu'on
   pourrait réellement le faire, sans connaître l'avenir. C'est **l'estimation honnête**,
   et l'écart entre ② et ③ mesure l'optimisme de la sélection.

⚠️ Aucun apprentissage ici — uniquement du krigeage. Le script est léger et peut tourner à
côté d'un lot LightGBM sans le concurrencer.

Usage  : python3 scripts/optimisation_krigeage.py --polluant O3 --horizon 2
Sortie : reports/optimisation_krigeage_<polluant>_h<n>.csv
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
    GRANDEUR_PAR_POLLUANT, agreger_journalier, charger, colonnes_admises,
)
from duel_chimere_krigeage import VARIANTE, chimere_journalier  # noqa: E402
from krigeage_du_biais import DECALAGE, biais_interpole, matrice_distances  # noqa: E402

FENETRES = (3, 7, 14, 30, 60)
RAYONS = (25.0, 50.0, 100.0, 200.0, 400.0)
PUISSANCES = (1.0, 2.0)
NOM = {"O3": "O₃", "NO2": "NO₂", "PM10": "PM10", "PM25": "PM2,5"}


def nom_variante(f: int, rayon: float, p: float, ty: str) -> str:
    return f"{f} j · {rayon:.0f} km · p={p:.0f} · {ty}"


def rmse(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.sqrt(np.mean((a - b) ** 2)))


def main(polluant: str, horizon: int) -> int:
    t0 = time.time()

    # ── Les lignes du duel, obtenues par le MÊME chemin que `duel_chimere_krigeage` ──
    # Réagréger autrement ferait diverger deux grains qui doivent être identiques, et
    # l'écart passerait pour un écart de méthode (§ 4 ter : un axe se lit dans les données).
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, cols, grandeur)
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    # Jamais de `strftime` sur une colonne de dates : c'est le chemin qui tombe sur cette
    # machine. Arithmétique entière, puis formatage d'un petit tableau unique.
    ym = d["jour"].dt.year.to_numpy() * 100 + d["jour"].dt.month.to_numpy()

    ch = chimere_journalier(polluant, grandeur, str(ym.min()), str(ym.max()))
    if ch is None:
        raise SystemExit(f"CHIMERE introuvable dans les membres de {polluant} — "
                         f"ce balayage exige la colonne `chimere`")
    avant = len(d)
    d = d.merge(ch, on=["station_id", "jour"], how="left").dropna(
        subset=["chimere_jour"]).reset_index(drop=True)
    ech = "J0" if horizon == 1 else f"J+{horizon - 1}"
    print(f"{NOM[polluant]} · {ech} · {len(d):,} lignes communes aux deux départs "
          f"({100 * len(d) / avant:.1f} % du corpus) · "
          f"{len(FENETRES) * len(RAYONS) * len(PUISSANCES) * 2} variantes × 2 départs",
          flush=True)

    # ⚠️ `ym` ci-dessus datait le corpus AVANT la jointure CHIMERE ; la fusion retire des
    # lignes, et le masque resterait à l'ancienne taille. numpy a levé — c'est le bon cas.
    # Le recalculer ICI, après la seule opération qui change le nombre de lignes.
    ym = d["jour"].dt.year.to_numpy() * 100 + d["jour"].dt.month.to_numpy()

    ids = np.sort(d["station_id"].unique())
    dist, st = matrice_distances(ids)
    tt = st["type_station"].fillna("?").to_numpy()
    memes = (tt[:, None] == tt[None, :]).astype(float)
    piv_index = pd.date_range(d["jour"].min(), d["jour"].max(), freq="D")
    lig = pd.Index(piv_index).get_indexer(pd.DatetimeIndex(d["jour"].to_numpy()))
    col = d["station_id"].map({s: i for i, s in enumerate(ids)}).to_numpy()
    if (lig < 0).any() or pd.isna(col).any():
        raise SystemExit("appariement ligne↔champ faux : jours ou stations hors du pivot")
    col = col.astype(int)

    y = d["valeur"].to_numpy(dtype=float)

    # La coupure du calendrier en deux moitiés — le réglage se choisit sur la première et
    # se note sur la seconde. Un réglage choisi sur l'avenir n'est pas un réglage.
    ordre = np.sort(np.unique(ym))
    charniere = ordre[len(ordre) // 2]
    tot, apr = ym < charniere, ym >= charniere
    print(f"  charnière de sélection : {charniere // 100}-{charniere % 100:02d} · "
          f"{tot.sum():,} lignes avant · {apr.sum():,} après", flush=True)

    lignes = []
    for depart, colonne in (("CHIMERE", "chimere_jour"), ("CAMS médiane", "cams_jour")):
        base = d[colonne].to_numpy(dtype=float)
        piv = (pd.DataFrame({"jour": d["jour"], "station_id": d["station_id"],
                             "_b": y - base})
               .pivot_table(index="jour", columns="station_id", values="_b",
                            aggfunc="mean")
               .reindex(columns=ids).reindex(piv_index))
        roulantes = {f: piv.shift(DECALAGE).rolling(f, min_periods=max(2, f // 3)).mean()
                     for f in FENETRES}
        print(f"\n  ── départ {depart} · RMSE brut {rmse(base, y):.3f}", flush=True)
        for f in FENETRES:
            for rayon in RAYONS:
                for p in PUISSANCES:
                    for ty, nom_ty in ((None, "tous"), (memes, "même typo")):
                        champ = biais_interpole(roulantes[f], dist, 0, rayon, p, ty)
                        c = champ[lig, col]
                        # Repli COMPTÉ sur le brut : laisser des NaN rétrécirait le
                        # périmètre en silence et l'écart porterait sur d'autres lignes.
                        x = np.where(np.isfinite(c), base + c, base)
                        lignes.append({
                            "polluant": polluant, "horizon": horizon, "depart": depart,
                            "fenetre_j": f, "rayon_km": rayon, "puissance": p,
                            "donneurs": nom_ty,
                            "variante": nom_variante(f, rayon, p, nom_ty),
                            "rmse": rmse(x, y),
                            "rmse_avant": rmse(x[tot], y[tot]),
                            "rmse_apres": rmse(x[apr], y[apr]),
                            "couverture_pct": 100 * float(np.isfinite(c).mean()),
                            "n": len(d)})
            print(f"     fenêtre {f:2d} j · {time.time() - t0:5.1f} s", flush=True)

    m = pd.DataFrame(lignes)
    fige = nom_variante(VARIANTE["fenetre"], VARIANTE["rayon"], VARIANTE["p"],
                        "même typo" if VARIANTE["typo"] else "tous")
    if (m["variante"] == fige).sum() != 2:
        raise SystemExit(f"la variante figée du duel « {fige} » n'est pas dans la grille "
                         f"— la comparaison n'a pas de point de référence")

    print(f"\n{'═' * 88}\nCE QUE LE RÉGLAGE PAR POLLUANT RAPPORTE — {NOM[polluant]}, {ech}"
          f"\n{'═' * 88}")
    print(f"  {'départ':14s} {'figée':>8s} {'②majorant':>10s} {'③honnête':>9s}   "
          f"variante choisie sur la 1ʳᵉ moitié")
    bilan = []
    for depart in ("CHIMERE", "CAMS médiane"):
        s = m[m["depart"] == depart]
        r_fige = float(s.loc[s["variante"] == fige, "rmse"].iloc[0])
        # ② majorant : le minimum sur les lignes qui le notent — ce n'est pas un score.
        r_maj = float(s["rmse"].min())
        # ③ honnête : choisie AVANT la charnière, notée APRÈS.
        gagnante = s.loc[s["rmse_avant"].idxmin()]
        r_fige_apr = float(s.loc[s["variante"] == fige, "rmse_apres"].iloc[0])
        r_hon_apr = float(gagnante["rmse_apres"])
        g_maj = 100 * (1 - r_maj / r_fige)
        g_hon = 100 * (1 - r_hon_apr / r_fige_apr)
        print(f"  {depart:14s} {r_fige:8.3f} {r_maj:10.3f} {r_hon_apr:9.3f}   "
              f"{gagnante['variante']}")
        print(f"  {'':14s} {'—':>8s} {g_maj:9.2f}% {g_hon:8.2f}%   "
              f"(③ noté sur la 2ᵈᵉ moitié, figée = {r_fige_apr:.3f})")
        bilan.append({"polluant": polluant, "horizon": horizon, "depart": depart,
                      "variante_figee": fige, "rmse_figee": r_fige,
                      "rmse_meilleure_majorant": r_maj, "gain_majorant_pct": g_maj,
                      "variante_choisie_1re_moitie": str(gagnante["variante"]),
                      "rmse_figee_2de_moitie": r_fige_apr,
                      "rmse_choisie_2de_moitie": r_hon_apr,
                      "gain_honnete_pct": g_hon, "charniere": int(charniere),
                      "n": len(d)})

    b = pd.DataFrame(bilan)
    print(f"\n  ⚠️ ② est un MAJORANT — variante choisie sur les lignes qui la notent, "
          f"c'est le biais de criblage.\n     Le chiffre citable est ③.")

    # Rule 2 ter : la table s'écrit en dernier, et on exige nommément ses colonnes.
    sortie = RACINE / f"reports/optimisation_krigeage_{polluant}_h{horizon}.csv"
    attendues = ["depart", "rmse_figee", "gain_majorant_pct", "gain_honnete_pct"]
    if manque := [c for c in attendues if c not in b.columns]:
        raise SystemExit(f"colonnes absentes du bilan : {manque}")
    m.to_csv(RACINE / f"reports/optimisation_krigeage_{polluant}_h{horizon}_grille.csv",
             index=False)
    b.to_csv(sortie, index=False)
    print(f"\nÉcrit : {sortie.relative_to(RACINE)} (+ la grille des "
          f"{len(m)} variantes) · {(time.time() - t0) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="O3", choices=("O3", "NO2", "PM10", "PM25"))
    a.add_argument("--horizon", type=int, default=2)
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon))
