#!/usr/bin/env python3
"""Les précurseurs gazeux de CAMS — quatre variables que le modèle n'a jamais vues.

D'où vient cette famille — 23/08/2026
---------------------------------------
Le catalogue ADS expose **28 variables** ; ce dépôt en tirait douze. Six autres ont été
téléchargées cette nuit, choisies chacune pour un mécanisme nommé AVANT la mesure. Le
comptage mois par mois — § 2 bis, *compter le reçu contre le demandé* — a montré que deux
d'entre elles (`pm2p5_nh4_conc`, `pm2p5_so4_conc`) n'existent qu'à partir de **décembre
2024**, comme le nitrate avant elles. Elles sont donc écartées d'ici : sur seize mois,
« la variable est absente » vaudrait « nous sommes avant décembre 2024 », et le protocole
cache les mois.

Restent **quatre gaz, couverts sur les 37 mois du corpus** :

| variable | mécanisme, écrit avant de mesurer |
|---|---|
| `nh3_conc` | l'ammoniac d'épandage — précurseur du nitrate d'ammonium, qui fait les épisodes de particules du printemps |
| `so2_conc` | le précurseur gazeux du sulfate : industrie, maritime |
| `pans_conc` | les nitrates de peroxyacyle — réservoir d'azote transporté, qui sépare l'ozone importé de l'ozone produit sur place |
| `nmvoc_conc` | les COV non méthaniques — le second précurseur de l'ozone, et rien dans nos variables ne dit si l'on est en régime COV-limité ou NOx-limité |

⚠️ **La base est la pile complète à huit familles**, `profil` et `fourier` compris. Ce qui se
mesure ici est ce que les précurseurs ajoutent à un système qui possède déjà les masses
totales, la composition particulaire et la forme du jour. Une base plus pauvre surestimerait
d'un facteur 2 à 4.

⚠️ Contrairement à la spéciation, cette famille **ne restreint pas la fenêtre** : c'est tout
l'intérêt d'avoir téléchargé 37 mois plutôt que 32.

Usage  : python3 scripts/apport_precurseurs.py --polluant NO2
Sortie : reports/apport_precurseurs_<polluant>_h<n>_<axe>.csv
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


GAZ = ["nh3_conc", "so2_conc", "pans_conc", "nmvoc_conc"]


def charger_precurseurs(grandeur: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Les quatre gaz au grain journalier — moyenne ET maximum.

    La moyenne décrit le niveau du jour, le maximum l'épisode : un pic d'ammoniac de six
    heures après un épandage n'est pas un fond élevé, et leur moyenne les confond. La
    spéciation garde déjà les deux pour la même raison.

    ⚠️ **Concaténer AVANT d'agréger** : le fichier d'un mois déborde sur le suivant, donc le
    2 de chaque mois est servi par deux fichiers. Agréger par fichier puis concaténer
    produirait deux lignes partielles pour ce jour-là, et une jointure qui rend plus de
    lignes qu'elle n'en reçoit.
    """
    fs = sorted(glob.glob(str(RACINE / "data/processed/meteo/precurseurs_metropole_*.parquet")))
    if not fs:
        raise SystemExit("aucun précurseur extrait — lancer "
                         "scripts/extraire_speciation.py --lot precurseurs")
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    manque = [c for c in GAZ if c not in t.columns]
    if manque:
        raise SystemExit(f"variables absentes des parquets : {manque}")
    t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.tz_localize(None).dt.floor("D")
    g = t.groupby(["station_id", "jour"])[GAZ].agg(["mean", "max"])
    g.columns = [f"pre_{a}_{b}" for a, b in g.columns]
    g = g.reset_index()
    moyennes = [c for c in g.columns if c.endswith("_mean")]
    maxima = [c for c in g.columns if c.endswith("_max")]
    print(f"  précurseurs : {len(fs)} mois · {len(t):,} lignes horaires → {len(g):,} "
          f"jours-station · {len(GAZ)} gaz", flush=True)
    return g, moyennes, maxima


def rmse(o: np.ndarray, x: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int, axe: str,
         retirer: tuple[str, ...] = ()) -> int:
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

    from ablation_speciation import charger_speciation as _cs  # noqa: PLC0415
    spe_mois = sorted({str(x)[:7] for x in
                       pd.to_datetime(_cs()["jour"]).dt.strftime("%Y-%m")})

    if {'geoscf', 'speciation', 'membres', 'feux'} <= set(retirer):
        # ⚠️ Base délibérément plus PAUVRE, et c'est le but. GEOS-CF restreint la fenêtre à
        # 29 mois, la spéciation à 32 ; leur intersection tombe à 24-28 plis, où le test de
        # signe ne peut presque plus conclure — PM10 y était à p = 0,064. Les précurseurs,
        # eux, couvrent les **37 mois** : on les remesure sur le corpus entier, contre une
        # base qui garde tout ce qui ne troue pas la fenêtre — terrain, calendrier,
        # typologie, tendance, profil, Fourier.
        #
        # 🔴 Ce chiffre n'est PAS comparable à celui de la base complète : mesuré contre
        # moins de concurrence, c'est un MAJORANT. Ce qu'il tranche est le SIGNE et sa
        # reproductibilité sur quatre polluants, jamais l'amplitude.
        print("  base MINCE : ni GEOS-CF ni spéciation ni membres ni feux — fenêtre "
              "entière, apport MAJORANT", flush=True)
    else:
        if "geoscf" in retirer:
            # 🔴 Le cas qui décide, ouvert le 23/08 à 07 h 45. Retirer TOUT (base mince)
            # rend la mesure ininterprétable : les précurseurs y remplacent n'importe quel
            # champ de concentration corrélé, et le NO₂ passe de −0,08 à +2,78 % — alors
            # qu'il ne devait rien gagner. Ne retirer que GEOS-CF garde la spéciation, les
            # membres et les feux en concurrence, et ne coûte que la restriction de fenêtre
            # qui privait le test de sa puissance : ~32 plis au lieu de 24.
            # ⚠️ Retirer GEOS-CF lève SA restriction de fenêtre, pas celle de la
            # spéciation — qui n'existe pas avant 2024-01 et reste dans la base. Sans
            # cette ligne, cinq mois porteraient seize colonnes entièrement vides, et
            # « la spéciation est absente » vaudrait « nous sommes en 2023 » : le
            # protocole cache les mois, donc c'est une fuite, dans les DEUX bras.
            # Trouvé au compte de plis — 36 au lieu des 32 attendus.
            mois_spe = set(spe_mois)
            mois_ok = sorted(m for m in d["mois"].unique() if m in mois_spe)
            avant_f = len(d)
            d = d[d["mois"].isin(mois_ok)].reset_index(drop=True)
            print(f"  GEOS-CF retiré ; fenêtre bornée par la SPÉCIATION : "
                  f"{len(mois_ok)} mois ({mois_ok[0]} → {mois_ok[-1]}) · "
                  f"{avant_f - len(d):,} jours-station retirés", flush=True)
        else:
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

    # ── Fourier entre aussi dans la base : la pile en compte huit familles ──────────
    from apport_fourier_profil import harmoniques  # noqa: PLC0415
    fou, cols_fou = harmoniques(jeu)
    fou["jour"] = pd.to_datetime(fou["jour"]).dt.tz_localize(None)
    d = d.merge(fou, on=["station_id", "jour"], how="left")
    base += cols_fou

    # ── Les précurseurs, la seule chose que ce script mesure ────────────────────────
    pre, moyennes, maxima = charger_precurseurs(grandeur)
    avant_pre = len(d)
    d = d.merge(pre, on=["station_id", "jour"], how="left")
    if len(d) != avant_pre:
        raise SystemExit(f"jointure des précurseurs : {avant_pre:,} → {len(d):,} lignes")
    toutes = moyennes + maxima

    # ── § « un mois absent est un code d'époque » : on RESTREINT la fenêtre ─────────
    manque = {m: float(b.isna().mean(axis=0).max()) for m, b in d.groupby("mois")[toutes]}
    hors = sorted(m for m, v in manque.items() if v > TAUX_MANQUE_MAX)
    if hors:
        perdu = int(d["mois"].isin(hors).sum())
        print(f"  fenêtre restreinte : {len(hors)} mois retiré(s) — "
              + ", ".join(f"{m} ({100 * manque[m]:.0f} %)" for m in hors[:6])
              + f" · {perdu:,} jours-station sur {len(d):,}", flush=True)
        d = d[~d["mois"].isin(hors)].reset_index(drop=True)
    base = [c for c in base if c in d.columns]

    modes = {"① pile complète — huit familles": base,
             f"② + précurseurs, moyennes ({len(moyennes)})": base + moyennes,
             f"③ + précurseurs, moyennes et maxima ({len(toutes)})": base + toutes}

    mois = np.sort(d["mois"].unique())
    ids = np.sort(d["station_id"].unique())
    print(f"\n{polluant} · {libelle_echeance(horizon)} · axe {axe} · {len(d):,} jours-station"
          f" · {len(ids)} stations · {len(mois)} mois · base {len(base)} colonnes", flush=True)
    print(f"  couverture des précurseurs : "
          f"{100 * d[toutes].notna().all(axis=1).mean():.1f} % des lignes", flush=True)

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

    print(f"\n{'═' * 96}\nAPPORT DES PRÉCURSEURS GAZEUX · {polluant} · "
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
    if retirer:
        suff += "_sans-" + "-".join(sorted(retirer))
    ecrire_rapport(pd.DataFrame(lignes),
                   RACINE / f"reports/apport_precurseurs_{suff}.csv", contexte,
                   attendues=["gain_pct", "apport_vs_pile_pct", "ecart_apparie_moyen_pct"])
    ecrire_rapport(tp, RACINE / f"reports/apport_precurseurs_{suff}_par_pli.csv",
                   contexte, attendues=["rmse_config1", "rmse_config2"])
    print(f"\nÉcrit : reports/apport_precurseurs_{suff}.csv · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--axe", default="double", choices=("double", "temporel"))
    a.add_argument("--retirer", default="",
                   help="familles à retirer de la base, séparées par des virgules "
                        "— « geoscf » élargit la fenêtre en gardant la concurrence ; "
                        "tout retirer rend la mesure ININTERPRÉTABLE (substitution). "
                        "Le nom de l'artefact porte la liste.")
    n = a.parse_args()
    raise SystemExit(main(n.polluant, n.horizon, n.plis_spatiaux, n.axe,
                          tuple(x for x in n.retirer.split(',') if x)))
