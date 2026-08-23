#!/usr/bin/env python3
"""La FORME du jour, appliquée aux trois autres familles horaires que l'agrégation écrase.

D'où vient cette piste — 23/08/2026
------------------------------------
`profil` a été ajoutée cette nuit à la pile complète et rend **+0,31 à +0,62 pt** à la place
la plus dure, avec une coïncidence rare : son apport cumulatif et son coût à l'ablation sont
égaux à 0,02 pt près sur les quatre polluants. Autrement dit **aucune autre famille ne porte
cette information**. Le mécanisme est donc établi : `agreger_journalier` réduit 24 valeurs
horaires à une moyenne, et la forme du jour survit à cette réduction comme information utile.

Or CAMS n'est pas la seule série horaire écrasée. Le même `{c: (c, "mean") for c in autres}`
s'applique à **trois autres familles**, et personne n'a jamais regardé leur forme :

* **les membres d'ensemble** — `joindre_membres` moyenne l'étendue horaire sur la journée. Un
  ensemble qui diverge au petit matin puis converge l'après-midi n'est pas un ensemble qui
  diverge à l'heure du pic. La dispersion **en niveau** est déjà mesurée nulle comme
  prédicteur tout en stratifiant l'erreur d'un facteur 6,6 : c'est exactement le profil d'une
  variable dont on n'a pas trouvé la bonne forme.
* **GEOS-CF** — notre seule information extérieure à CAMS (+0,82 à +1,19 pt à l'ablation),
  réduite elle aussi à un nombre par jour.
* **la spéciation** — et c'est la plus motivée des trois : l'équilibre
  NH₃ + HNO₃ ⇌ NH₄NO₃ est **semi-volatil**, donc piloté par la température et l'humidité,
  donc **diurne par construction**. Une moyenne journalière détruit précisément le mécanisme.

Ce qui est déclaré AVANT la mesure
------------------------------------
Une série par famille, quatre descripteurs chacune, **douze colonnes en tout** — et le choix
de la série est motivé, pas balayé :

| famille | série retenue | pourquoi celle-là |
|---|---|---|
| membres | `membres_etendue` horaire | c'est le **désaccord**, pas le niveau, qui informe |
| geoscf | la variable du polluant traité | même geste que pour CAMS, sur un modèle indépendant |
| speciation | `sia_conc` | la fraction semi-volatile, la seule dont la chimie est diurne |

⚠️ **La base contient DÉJÀ la pile complète**, `profil` compris : ce qui se mesure ici est ce
que la forme des trois autres familles ajoute à un système qui a déjà la forme de CAMS. Une
base plus pauvre surestimerait d'un facteur 2 à 4.

⚠️ La fenêtre est l'**intersection** des couvertures (GEOS-CF v1 ∩ spéciation), identique pour
toutes les configurations : les gains ne se comparent pas à ceux de `methode_maximale`, seuls
les écarts entre configurations le font.

Usage  : python3 scripts/apport_forme_familles.py --polluant NO2
Sortie : reports/apport_forme_familles_<polluant>_h<n>_<axe>.csv
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

from aq.rapport import ecrire_rapport, libelle_echeance  # noqa: E402
from apport_geoscf import charger_geoscf  # noqa: E402
from cible_journaliere import profil_horaire  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from leviers_36mois import _fusion, joindre_feux, joindre_membres  # noqa: E402

TAUX_MANQUE_MAX = 0.5


def forme_du_jour(t: pd.DataFrame, colonne: str, prefixe: str,
                  temps: str = "timestamp_utc") -> tuple[pd.DataFrame, list[str]]:
    """Les quatre descripteurs de FORME d'une série horaire, par station-jour.

    Généralisation de `cible_journaliere.profil_horaire`, qui fait cela pour CAMS :
    amplitude, dispersion intra-jour, **heure** du maximum, rapport pic/moyenne. Aucune
    observation n'y entre — ce sont des champs prévus, donc le périmètre reste PARTOUT.
    """
    d = t[["station_id", temps, colonne]].dropna(subset=[colonne]).copy()
    d["jour"] = pd.to_datetime(d[temps]).dt.floor("D")
    if getattr(d["jour"].dt, "tz", None) is not None:
        d["jour"] = d["jour"].dt.tz_localize(None)
    d["heure"] = pd.to_datetime(d[temps]).dt.hour
    g = d.groupby(["station_id", "jour"], sort=False)
    p = g.agg(_max=(colonne, "max"), _min=(colonne, "min"),
              _sigma=(colonne, "std"), _moy=(colonne, "mean")).reset_index()
    pic = d.loc[g[colonne].idxmax(), ["station_id", "jour", "heure"]]
    p = p.merge(pic.rename(columns={"heure": f"{prefixe}_heure_max"}),
                on=["station_id", "jour"], how="left")
    p[f"{prefixe}_amplitude"] = p["_max"] - p["_min"]
    p[f"{prefixe}_sigma"] = p["_sigma"]
    p[f"{prefixe}_pic_sur_moy"] = p["_max"] / p["_moy"].replace(0, np.nan)
    cols = [f"{prefixe}_amplitude", f"{prefixe}_sigma", f"{prefixe}_heure_max",
            f"{prefixe}_pic_sur_moy"]
    return p[["station_id", "jour"] + cols], cols


def horaire_membres(polluant: str) -> pd.DataFrame | None:
    fs = sorted(glob.glob(str(RACINE / "data/processed/meteo/"
                              f"membres_metropole_{polluant.lower()}_*.parquet")))
    if not fs:
        return None
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return t if "membres_etendue" in t.columns else None


def horaire_geoscf(polluant: str) -> tuple[pd.DataFrame | None, str | None]:
    """⚠️ v1 seulement — v1 et v2 ne sont pas le même prédicteur (+15,4 µg/m³ sur l'ozone)."""
    fs = [f for f in sorted(glob.glob(str(RACINE / "data/processed/meteo/geoscf_metropole_*.parquet")))
          if "_v2" not in f]
    if not fs:
        return None, None
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    cible = {"O3": "geoscf_o3", "NO2": "geoscf_no2", "PM25": "geoscf_pm25"}.get(polluant)
    if cible is None or cible not in t.columns:
        # PM10 n'a pas d'équivalent direct dans le flux : on prend les PM2,5, qui en sont
        # la fraction fine — et on le DIT, plutôt que de laisser croire à une mesure de PM10.
        cible = "geoscf_pm25" if "geoscf_pm25" in t.columns else None
    return (t, cible) if cible else (None, None)


def horaire_speciation() -> tuple[pd.DataFrame | None, str | None]:
    fs = sorted(glob.glob(str(RACINE / "data/processed/meteo/speciation_metropole_*.parquet")))
    if not fs:
        return None, None
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    return (t, "sia_conc") if "sia_conc" in t.columns else (None, None)


def rmse(o: np.ndarray, x: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int, axe: str) -> int:
    depart = time.time()
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    jeu = charger(polluant, horizon)
    cols = colonnes_admises(jeu)
    jeu[cols] = jeu[cols].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    prof, cols_prof = profil_horaire(jeu)
    j = agreger_journalier(jeu, cols, grandeur)
    base = [c for c in cols if c != "cams"] + ["cams_moy_jour", "cams_jour"]
    d = j.rename(columns={"obs_jour": "valeur"}).reset_index(drop=True)
    d["jour"] = pd.to_datetime(d["jour"]).dt.tz_localize(None)
    d["mois"] = d["jour"].dt.strftime("%Y-%m")

    # ── La pile complète, dans l'ordre de `methode_maximale` ────────────────────────
    from banc_preprocessing import f_tendance_cams  # noqa: PLC0415
    tend = f_tendance_cams(d)
    d = pd.concat([d, tend], axis=1)
    base += list(tend.columns)

    from optuna_mos import typologie as charger_typologie  # noqa: PLC0415
    typo, cols_typo = charger_typologie(np.sort(d["station_id"].unique()))
    d = d.merge(typo, on="station_id", how="left")
    base += list(cols_typo)

    prof["jour"] = pd.to_datetime(prof["jour"]).dt.tz_localize(None)
    avant = len(d)
    d = d.merge(prof, on=["station_id", "jour"], how="left")
    base += cols_prof

    g = charger_geoscf(grandeur, "v1")
    g["jour"] = pd.to_datetime(g["jour"]).dt.tz_localize(None)
    cols_g = [c for c in g.columns if c.startswith("geoscf_")]
    d = _fusion(d, g, "geoscf")
    base += cols_g
    couvert = d[cols_g[0]].notna()
    mois_ok = sorted(d.loc[couvert, "mois"].unique())
    d = d[d["mois"].isin(mois_ok)].reset_index(drop=True)

    from ablation_speciation import charger_speciation  # noqa: PLC0415
    spe = charger_speciation()
    cols_spe = [c for c in spe.columns if c.startswith("spe_")]
    d = d.merge(spe, on=["station_id", "jour"], how="left")
    base += cols_spe

    debut, fin = mois_ok[0].replace("-", ""), mois_ok[-1].replace("-", "")
    d, cols_mem = joindre_membres(d, polluant, debut, fin)
    d, cols_feux = joindre_feux(d, debut, fin)
    base += cols_mem + cols_feux
    if len(d) != avant and len(d) > avant:
        raise SystemExit(f"une jointure a AUGMENTÉ le compte de lignes ({avant:,} → {len(d):,})")

    # ── Les trois formes, une série par famille, déclarées plus haut ────────────────
    formes: dict[str, list[str]] = {}
    tm = horaire_membres(polluant)
    if tm is not None:
        f_mem, c_mem = forme_du_jour(tm, "membres_etendue", "fmem")
        d = d.merge(f_mem, on=["station_id", "jour"], how="left")
        formes["membres"] = c_mem
    tg, col_g = horaire_geoscf(polluant)
    if tg is not None:
        f_geo, c_geo = forme_du_jour(tg, col_g, "fgeo")
        d = d.merge(f_geo, on=["station_id", "jour"], how="left")
        formes["geoscf"] = c_geo
        print(f"  forme GEOS-CF calculée sur « {col_g} »", flush=True)
    ts, col_s = horaire_speciation()
    if ts is not None:
        f_spe, c_spe = forme_du_jour(ts, col_s, "fspe")
        d = d.merge(f_spe, on=["station_id", "jour"], how="left")
        formes["speciation"] = c_spe
    if not formes:
        raise SystemExit("aucune famille horaire disponible — rien à mesurer")

    # ── § « un mois absent est un code d'époque » : on RESTREINT la fenêtre ─────────
    toutes = [c for v in formes.values() for c in v]
    manque = {m: float(b.isna().mean(axis=0).max()) for m, b in d.groupby("mois")[toutes]}
    hors = sorted(m for m, v in manque.items() if v > TAUX_MANQUE_MAX)
    if hors:
        perdu = int(d["mois"].isin(hors).sum())
        print(f"  fenêtre restreinte : {len(hors)} mois retiré(s) — "
              + ", ".join(f"{m} ({100 * manque[m]:.0f} %)" for m in hors[:6])
              + f" · {perdu:,} jours-station sur {len(d):,}", flush=True)
        d = d[~d["mois"].isin(hors)].reset_index(drop=True)
    base = [c for c in base if c in d.columns]

    modes = {"① pile complète (avec la forme de CAMS)": base}
    for nom, cc in formes.items():
        modes[f"② + forme {nom} ({len(cc)})"] = base + cc
    modes[f"③ + les {len(formes)} formes"] = base + toutes

    mois = np.sort(d["mois"].unique())
    ids = np.sort(d["station_id"].unique())
    print(f"\n{polluant} · {libelle_echeance(horizon)} · axe {axe} · {len(d):,} jours-station"
          f" · {len(ids)} stations · {len(mois)} mois · base {len(base)} colonnes", flush=True)
    for nom, cc in formes.items():
        print(f"  couverture forme « {nom} » : {100 * d[cc].notna().all(axis=1).mean():.1f} %",
              flush=True)

    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    plis = []
    for i, mm in enumerate(mois):
        m_te, m_tr = d["mois"] == mm, d["mois"] != mm
        if axe == "double":
            dans = d["station_id"].isin(groupes[i % n_spa])
            m_te, m_tr = m_te & dans, m_tr & ~dans
        plis.append((mm, m_te, m_tr))
    ecartes = [m for m, a, b in plis if a.sum() < 200 or b.sum() < 1000]
    print(f"  périmètre effectif : {len(plis) - len(ecartes)} plis sur {len(plis)} prévus"
          + (f" · écartés : {', '.join(ecartes)}" if ecartes else ""), flush=True)

    pred = {k: np.full(len(d), np.nan) for k in modes}
    par_pli = []
    for i, (mm, m_te, m_tr) in enumerate(plis):
        if m_te.sum() < 200 or m_tr.sum() < 1000:
            continue
        te, tr = d[m_te], d[m_tr]
        idx = np.flatnonzero(m_te.to_numpy())
        o, c = te["valeur"].to_numpy(), te["cams_jour"].to_numpy()
        ligne = {"polluant": polluant, "horizon": horizon, "axe": axe, "mois": mm,
                 "n_test": len(te), "n_train": len(tr), "rmse_ancre": rmse(o, c)}
        for k, (nom, colonnes) in enumerate(modes.items()):
            p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
            pred[nom][idx] = p
            ligne[f"rmse_config{k + 1}"] = rmse(o, p)
        par_pli.append(ligne)
        if (i + 1) % 6 == 0:
            print(f"  {i + 1}/{len(plis)} plis · {(time.time() - depart) / 60:.1f} min",
                  flush=True)

    ok = np.ones(len(d), bool)
    for v in pred.values():
        ok &= np.isfinite(v)
    o = d["valeur"].to_numpy()[ok]
    r_ancre = rmse(o, d["cams_jour"].to_numpy()[ok])
    tp = pd.DataFrame(par_pli)
    ref_pli = tp["rmse_config1"].to_numpy()

    print(f"\n{'═' * 96}\nFORME DES FAMILLES HORAIRES · {polluant} · "
          f"{libelle_echeance(horizon)} · {int(ok.sum()):,} prédictions\n{'═' * 96}")
    print(f"  {'configuration':44s} {'RMSE':>8s} {'gain/CAMS':>10s} {'vs pile':>8s} "
          f"{'σ plis':>7s} {'plis>0':>8s}")
    lignes, ref_gain = [], None
    for k, nom in enumerate(modes):
        x = pred[nom][ok]
        gg = 100 * (1 - rmse(o, x) / r_ancre)
        dif = 100 * (1 - tp[f"rmse_config{k + 1}"].to_numpy() / ref_pli)
        marge = np.nan if k == 0 else gg - ref_gain
        if ref_gain is None:
            ref_gain = gg
        print(f"  {nom:44s} {rmse(o, x):8.4f} {gg:+9.2f}% "
              f"{'—' if k == 0 else f'{marge:+7.2f}'} {np.std(dif):7.3f} "
              f"{int((dif > 0).sum()):4d}/{len(dif)}")
        lignes.append({"polluant": polluant, "horizon": horizon, "axe": axe,
                       "configuration": nom, "n_colonnes": len(modes[nom]),
                       "rmse_candidat": rmse(o, x), "rmse_ancre": r_ancre, "gain_pct": gg,
                       "apport_vs_pile_pct": marge,
                       "ecart_apparie_moyen_pct": float(np.mean(dif)),
                       "ecart_apparie_sigma_pct": float(np.std(dif)),
                       "n_plis_positifs": int((dif > 0).sum()), "n_plis": len(dif),
                       "n_lignes": int(ok.sum()),
                       "fenetre": f"{mois[0]}→{mois[-1]}", "n_mois": len(mois)})

    contexte = {"polluant": polluant, "axe": axe, "echeance": libelle_echeance(horizon)}
    suff = f"{polluant}_h{horizon}_{axe}"
    ecrire_rapport(pd.DataFrame(lignes),
                   RACINE / f"reports/apport_forme_familles_{suff}.csv", contexte,
                   attendues=["gain_pct", "apport_vs_pile_pct", "ecart_apparie_moyen_pct"])
    ecrire_rapport(tp, RACINE / f"reports/apport_forme_familles_{suff}_par_pli.csv",
                   contexte, attendues=["rmse_config1", "rmse_config2"])
    print(f"\nÉcrit : reports/apport_forme_familles_{suff}.csv · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--axe", default="double", choices=("double", "temporel"))
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux, n.axe))
