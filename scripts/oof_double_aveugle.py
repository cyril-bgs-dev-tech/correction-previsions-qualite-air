#!/usr/bin/env python3
"""Conserve les prédictions **hors pli** des trois épreuves — et diagnostique le rétrécissement.

Pourquoi ce script existe
--------------------------
`double_aveugle_journalier.py` accumule `obs`, `cams` et `pred` puis n'en tire qu'un
**agrégat** : les prédictions ligne à ligne sont jetées à la sortie de `epreuve()`. Or
toute question sur la **détection** — table de contingence, front précision-rappel,
courbe coût-perte, calibration — se calcule sur ces lignes-là, jamais sur un gain de RMSE.
Sans elles, chaque nouvelle question impose de réajuster 36 modèles.

Ce script les écrit une fois. Tout le reste devient une lecture de parquet.

L'hypothèse qu'il teste en priorité
------------------------------------
Notre correction gagne largement en erreur quadratique et a rendu **×0,85** en détection
sur l'axe double aveugle, contre ×1,7 à ×4,1 sur l'axe spatial seul. L'explication
candidate est **physique et non technique** :

> Un modèle ajusté sur une perte quadratique estime l'espérance conditionnelle, donc
> **rétrécit vers la moyenne**. Sur une station jamais vue, il ignore de combien elle
> s'écarte du comportement moyen, donc il rétrécit **davantage**. La correction
> améliorerait le centre de la distribution en **écrasant la queue** — précisément ce
> qu'il ne faut pas pour une alerte.

Le test est une **interaction**, pas une moyenne : le rétrécissement doit être plus fort
là où la station est inconnue. Les trois épreuves du projet fournissent exactement le plan
d'expérience nécessaire, car elles diffèrent par ce qui est caché :

| épreuve | station | mois |
|---|---|---|
| spatiale | **inconnue** | connu |
| temporelle | connue | **inconnu** |
| double aveugle | **inconnue** | **inconnu** |

Si le rétrécissement suit la colonne « station » et ignore la colonne « mois »,
l'hypothèse est soutenue. S'il ne bouge pas, elle est réfutée et il faut la retirer du
récit — c'est le point que GPT_R12 §1.1 souligne : le mécanisme est documenté ailleurs
(Petetin et al. 2022), mais le **différentiel dû à la station inconnue** ne l'est pas.

Les diagnostics écrits, et pourquoi ceux-là
--------------------------------------------
1. `sd(pred)/sd(obs)` — le ratio de dispersion. Sous 1, l'amplitude prédite est trop
   faible. C'est l'indicateur que la RMSE masque par construction.
2. **Deux** pentes, `pred ~ obs` et `obs ~ pred`. Elles ne sont pas réciproques dès qu'il
   y a du bruit, et les confondre est une erreur classique : celle qui décrit la
   compression est `pred ~ obs`.
3. Ratios des quantiles Q90/Q95/Q99 prédits sur observés — où la queue se perd.
4. Les mêmes pour CAMS brut, **sans quoi rien n'est interprétable** : si CAMS rétrécit
   déjà autant, le reproche ne s'adresse pas à la correction.

Usage : python3 scripts/oof_double_aveugle.py --polluant NO2 [--typologie]
Sorties :
  data/interim/oof/oof_<polluant>[_typo].parquet   — une ligne par prédiction hors pli
  reports/retrecissement_<polluant>[_typo].csv     — les diagnostics par épreuve
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
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster,
    charger, colonnes_admises,
)


def plans(d: pd.DataFrame, n_plis_spatiaux: int, graine: int = GRAINE,
          chronologique: bool = False):
    """Reconstruit les trois plans de découpe, à l'identique du script de référence.

    ⚠️ Les masques d'entraînement sont donnés **explicitement**, jamais par complément :
    le complément du test double aveugle contient encore le mois caché sur d'autres
    stations et les stations cachées sur d'autres mois, ce qui rendrait l'épreuve plus
    facile que les deux épreuves simples.
    """
    rng = np.random.default_rng(graine)
    stations = np.sort(d["station_id"].unique())
    groupes = np.array_split(rng.permutation(stations), n_plis_spatiaux)
    mois = np.sort(d["mois"].unique())

    spatiaux = [(f"stations-{i+1}", d["station_id"].isin(g), ~d["station_id"].isin(g))
                for i, g in enumerate(groupes)]
    # ⚠️ `mois != m` inclut les mois **postérieurs** à m. C'est une interpolation
    # temporelle : un modèle déployé n'a que le passé. `chronologique=True` restreint
    # l'entraînement à `mois < m`, ce qui est la seule condition honnête de déploiement —
    # au prix d'un jeu d'entraînement qui rétrécit vers le début du corpus, d'où l'amorce.
    def avant(m):
        return d["mois"] < m if chronologique else d["mois"] != m

    temporels = [(m, d["mois"] == m, avant(m)) for m in mois]
    doubles = []
    for i, m in enumerate(mois):
        dans = d["station_id"].isin(groupes[i % n_plis_spatiaux])
        doubles.append((f"{m}+s{i % n_plis_spatiaux + 1}",
                        (d["mois"] == m) & dans, avant(m) & ~dans))
    return d, spatiaux, temporels, doubles


def diagnostiquer(g: pd.DataFrame) -> dict:
    """Les quatre diagnostics de compression, pour la correction **et** pour CAMS."""
    o, c, p = g["valeur"].to_numpy(), g["cams_jour"].to_numpy(), g["pred"].to_numpy()
    r = {"n": len(g), "sd_obs": float(o.std())}
    for nom, x in (("mos", p), ("cams", c)):
        # Deux pentes : `x ~ o` décrit la compression, `o ~ x` est la calibration usuelle.
        # Elles ne sont pas réciproques dès qu'il y a du bruit — les confondre inverse la
        # lecture.
        r[f"sdr_{nom}"] = float(x.std() / o.std()) if o.std() > 0 else np.nan
        r[f"pente_x_sur_o_{nom}"] = float(np.polyfit(o, x, 1)[0]) if len(g) > 2 else np.nan
        r[f"pente_o_sur_x_{nom}"] = float(np.polyfit(x, o, 1)[0]) if len(g) > 2 else np.nan
        for q in (90, 95, 99):
            qo, qx = np.percentile(o, q), np.percentile(x, q)
            r[f"q{q}_ratio_{nom}"] = float(qx / qo) if qo > 0 else np.nan
        r[f"rmse_{nom}"] = float(np.sqrt(np.mean((x - o) ** 2)))
    return r


def main(polluant: str, horizon: int, n_plis_spatiaux: int, typologie: bool,
         chronologique: bool = False) -> int:
    depart = time.time()
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    predicteurs = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    if typologie:
        from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
        typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
        avant = len(d)
        d = d.merge(typo, on="station_id", how="left")
        if len(d) != avant:
            raise SystemExit(f"jointure typologie : {avant:,} → {len(d):,}")
        if d[cols_typo].isna().any().any():
            raise SystemExit("typologie manquante — ne pas imputer")
        predicteurs += cols_typo

    d, spatiaux, temporels, doubles = plans(d, n_plis_spatiaux, chronologique=chronologique)
    print(f"{polluant} · {len(d):,} jours-station · {len(predicteurs)} prédicteurs"
          f"{' · + typologie' if typologie else ''}", flush=True)

    lignes = []
    for nom, plis, station_vue, mois_vu in (
            ("spatiale", spatiaux, False, True),
            ("temporelle", temporels, True, False),
            ("double aveugle", doubles, False, False)):
        t0, n_plis = time.time(), 0
        ecartes: list[str] = []
        for etiquette, m_test, m_train in plis:
            te, tr = d[m_test], d[m_train]
            if len(te) < 200 or tr.empty:
                # `CLAUDE.md` § 2 quater — un pli écarté sort du dénominateur en silence.
                ecartes.append(f"{etiquette} (test {len(te):,})")
                continue
            p = ajuster(DEFAUT, tr, te, predicteurs, "cams_jour")
            lignes.append(pd.DataFrame({
                "epreuve": nom, "pli": etiquette,
                "station_id": te["station_id"].to_numpy(),
                "jour": te["jour"].to_numpy(),
                "valeur": te["valeur"].to_numpy(),
                "cams_jour": te["cams_jour"].to_numpy(),
                "pred": p,
                "station_vue": station_vue, "mois_vu": mois_vu}))
            n_plis += 1
        print(f"  {nom:16s} {n_plis:2d}/{len(plis):2d} plis · {time.time() - t0:4.0f}s",
              flush=True)
        if ecartes:
            print(f"    ⚠️ {len(ecartes)} pli(s) écarté(s) sur {len(plis)} pour effectif "
                  f"insuffisant : {', '.join(ecartes)}", flush=True)

    oof = pd.concat(lignes, ignore_index=True)

    # ── Contrôles avant écriture — une assertion qui échoue lève, elle n'écrit pas ────
    if oof["pred"].std() == 0:
        raise SystemExit("prédictions constantes — lecture ou ajustement fautif")
    attendu = {"spatiale", "temporelle", "double aveugle"}
    if set(oof["epreuve"]) != attendu:
        raise SystemExit(f"épreuves manquantes : {attendu - set(oof['epreuve'])}")

    # ⚠️ L'échéance DOIT figurer dans le nom. Sans elle, un lot J+1 écrase silencieusement
    # un lot J0 et l'on analyse un mélange sans le savoir — c'est la règle 4 ter appliquée
    # aux artefacts qu'on écrit soi-même, pas seulement à ceux qu'on reçoit.
    suffixe = (f"_h{horizon}" + ("_typo" if typologie else "")
               + ("_chrono" if chronologique else ""))
    (RACINE / "data/interim/oof").mkdir(parents=True, exist_ok=True)
    # Nom provisoire puis renommage : un artefact au nom définitif doit être complet.
    cible = RACINE / f"data/interim/oof/oof_{polluant}{suffixe}.parquet"
    partiel = cible.with_suffix(".parquet.partiel")
    oof.to_parquet(partiel, index=False)
    partiel.replace(cible)

    diag = pd.DataFrame([{"epreuve": e, **diagnostiquer(g)}
                         for e, g in oof.groupby("epreuve", sort=False)])
    sortie = RACINE / f"reports/retrecissement_{polluant}{suffixe}.csv"
    diag.to_csv(sortie, index=False)

    print(f"\n{'═' * 78}\nRÉTRÉCISSEMENT — sd(prédit)/sd(observé), sous 1 = amplitude écrasée"
          f"\n{'═' * 78}")
    print(f"{'épreuve':17s} {'station':>8s} {'mois':>6s} {'SDR mos':>8s} {'SDR cams':>9s} "
          f"{'pente':>7s} {'Q99 mos':>8s} {'Q99 cams':>9s}")
    for _, r in diag.iterrows():
        vue = "vue" if r["epreuve"] == "temporelle" else "CACHÉE"
        mv = "vu" if r["epreuve"] == "spatiale" else "CACHÉ"
        print(f"{r['epreuve']:17s} {vue:>8s} {mv:>6s} {r['sdr_mos']:8.3f} "
              f"{r['sdr_cams']:9.3f} {r['pente_x_sur_o_mos']:7.3f} "
              f"{r['q99_ratio_mos']:8.3f} {r['q99_ratio_cams']:9.3f}")

    print(f"\nLecture : l'hypothèse prédit un SDR **plus bas** quand la station est cachée")
    print(f"          (spatiale et double aveugle) que quand elle est vue (temporelle).")
    print(f"          Si les trois SDR sont voisins, l'hypothèse est RÉFUTÉE.")
    print(f"\nÉcrit : {cible.relative_to(RACINE)} ({len(oof):,} lignes)")
    print(f"        {sortie.relative_to(RACINE)} · {(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--horizon", type=int, default=1)
    p.add_argument("--plis-spatiaux", type=int, default=3)
    p.add_argument("--typologie", action="store_true")
    p.add_argument("--chronologique", action="store_true",
                   help="n'entraîne que sur les mois ANTÉRIEURS — condition de déploiement")
    a = p.parse_args()
    raise SystemExit(main(a.polluant, a.horizon, a.plis_spatiaux, a.typologie,
                      a.chronologique))
