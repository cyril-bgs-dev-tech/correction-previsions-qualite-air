#!/usr/bin/env python3
"""Trois leviers criblés le 04/08 et jamais implémentés — mesurés au protocole du dossier.

Ce qui est repris, et d'où viennent les chiffres à battre
----------------------------------------------------------
`[[balayage-des-variables-inexploitees]]` a trouvé trois gisements dans des données **déjà
sur le disque**, les a chiffrés au criblage — saison et station neutralisées — puis les a
laissés là :

| levier | criblage contrôlé du 04/08 | pourquoi il existe |
|---|---|---|
| **climatologie CAMS du point** | +1,25 % | se calcule sans aucune observation, donc en tout point de la grille |
| **ensemble décalé** (sorties plus anciennes du même jour) | +0,73 % | `paires_cams_observations` filtre `echeance_h` et jette 2 prévisions sur 3 |
| **forme du profil horaire CAMS** | +0,51 % | `agreger_journalier` écrase 24 valeurs en 2 nombres |

Ces trois nombres viennent d'un criblage, pas d'une épreuve. Ce script les rejoue **au
double aveugle** — station ET mois cachés —, sur les quatre polluants, contre une base qui
porte déjà la dynamique de CAMS.

Pourquoi `tendance` est DANS la base, et pas à côté
-----------------------------------------------------
`f_tendance_cams` donne déjà au modèle la prévision de la **veille pour la veille**, ses
moyennes glissantes et sa volatilité. L'ensemble décalé donne autre chose — une **sortie
plus ancienne pour le MÊME jour** — mais les deux parlent de latence. Mesurer le second
contre une base qui n'aurait pas le premier surestimerait son apport : c'est exactement le
biais de criblage de ×2 à ×4 que ce dépôt a mesuré. La base porte donc `tendance`.

Ce que ce script NE dit pas
-----------------------------
Il mesure contre la **base**, pas au sommet de la pile complète — celle-ci restreint la
fenêtre à la couverture GEOS-CF (24 mois sur 37) et ferait payer aux trois leviers un
corpus amputé avant même de savoir s'ils valent quelque chose. Un levier qui survit ici
**doit** ensuite être remesuré en dernière position de `methode_maximale.py`, là où il
n'hérite que de ce que les autres n'ont pas pris. Un gain lu ici est un **majorant**.

Les cinq configurations sont déclarées avant la mesure, et chacune se compare à la base —
jamais entre elles : retenir après coup la gagnante puis publier son score sur ces mêmes
plis serait le criblage que ce fichier prétend éviter.

Usage  : python3 scripts/apport_leviers_gratuits.py --polluant NO2
Sortie : reports/apport_leviers_gratuits_<polluant>_h<n>_<axe>.csv
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

from aq.eval.critere import exiger_couverture_de_reference  # noqa: E402
from aq.rapport import ecrire_rapport, libelle_echeance  # noqa: E402
from cible_journaliere import profil_horaire  # noqa: E402
from double_aveugle_journalier import (  # noqa: E402
    DEFAUT, GRAINE, GRANDEUR_PAR_POLLUANT, agreger_journalier, ajuster, charger,
    colonnes_admises,
)
from fit_mos import TRANCHES, paires_cams_observations  # noqa: E402

# Au-delà de ce taux de manque sur un mois, une famille code l'ÉPOQUE plutôt que le
# phénomène — et le protocole cache justement les mois. Seuil repris de
# `methode_maximale.py`, où il sépare nettement les cas mesurés.
TAUX_MANQUE_MAX = 0.5

CLIMATO = ["clim_moyenne", "clim_sigma", "clim_p95", "clim_z_du_jour"]


def ensemble_decale(polluant: str, horizon: int) -> tuple[pd.DataFrame, list[str]]:
    """Les sorties CAMS **plus anciennes** visant le même jour — jetées depuis le début.

    Pour un jour cible D, la tranche `horizon` est la sortie de D−(horizon−1). Les tranches
    suivantes visent le MÊME jour depuis une sortie **plus ancienne** : autant de prévisions
    indépendantes du même instant, produites avec moins d'information initiale. Leur écart à
    la sortie fraîche mesure combien l'analyse a déplacé la prévision — un désaccord entre
    deux âges de la même chaîne, là où les six membres mesurent un désaccord entre modèles.

    Aucune observation n'entre ici : ces sorties existent en tout point de la grille.
    """
    blocs, cols = [], []
    for h in (horizon + 1, horizon + 2):
        if h not in TRANCHES:
            continue
        p = paires_cams_observations(polluant, h)
        p["jour"] = p["timestamp_utc"].dt.floor("D").dt.tz_localize(None)
        nom = f"cams_age{h - horizon}j"
        agr = p.groupby(["station_id", "jour"], sort=False)["cams"].mean().rename(nom)
        blocs.append(agr)
        cols.append(nom)
    if not blocs:
        raise SystemExit("aucune tranche plus ancienne disponible")
    return pd.concat(blocs, axis=1).reset_index(), cols


def climatologie(ref: pd.DataFrame, bloc: pd.DataFrame) -> tuple[pd.DataFrame, float]:
    """Climatologie CAMS du point, ajustée sur `ref` — **jamais sur le pli d'apprentissage**.

    § 0-L, et le défaut qui l'a produite : le protocole cache la station, donc une statistique
    ajustée par station sur le pli d'apprentissage est introuvable côté test, replie sur une
    constante, et les deux blocs se retrouvent sur des échelles différentes sans qu'aucune
    exception ne lève. `ref` est donc **toutes les stations, mois de test exclu** — ce que la
    production peut faire, puisqu'en un point non instrumenté l'archive CAMS existe et que
    seul le futur n'existe pas.
    """
    g = ref.groupby("station_id")["cams_jour"]
    st = pd.DataFrame({"clim_moyenne": g.mean(), "clim_sigma": g.std(),
                       "clim_p95": g.quantile(0.95)})
    part = exiger_couverture_de_reference(st.index, bloc["station_id"].unique(),
                                          "climatologie du point", part_max=0.1)
    out = st.reindex(bloc["station_id"]).reset_index(drop=True)
    out["clim_z_du_jour"] = ((bloc["cams_jour"].to_numpy() - out["clim_moyenne"])
                             / out["clim_sigma"].replace(0, np.nan))
    out.index = bloc.index
    return out, part


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

    # ── `tendance` entre dans la BASE (cf. docstring) ────────────────────────────────
    from banc_preprocessing import f_tendance_cams  # noqa: PLC0415
    tend = f_tendance_cams(d)
    if collision := [c for c in tend.columns if c in d.columns]:
        raise SystemExit(f"colonnes de tendance déjà présentes : {collision}")
    d = pd.concat([d, tend], axis=1)
    base = base + list(tend.columns)

    # ── Les deux familles jointes une fois pour toutes ──────────────────────────────
    avant = len(d)
    prof["jour"] = pd.to_datetime(prof["jour"]).dt.tz_localize(None)
    d = d.merge(prof, on=["station_id", "jour"], how="left")
    dec, ages = ensemble_decale(polluant, horizon)
    d = d.merge(dec, on=["station_id", "jour"], how="left")
    if len(d) != avant:
        raise SystemExit(f"jointure : {avant:,} → {len(d):,} lignes — doublons de clé")

    for c in ages:
        d[f"{c}_ecart"] = d["cams_jour"] - d[c]
    cols_dec = list(ages) + [f"{c}_ecart" for c in ages]

    # ⚠️ Le mois de BORD n'est pas une donnée manquante, c'est un code d'époque. Les
    # sorties visant J+2 et J+3 du dernier mois du corpus n'ont pas encore toutes été
    # archivées : sur ce mois-là, « la famille est absente » vaut exactement « nous sommes
    # en ce mois-là », et le protocole cache les mois. On RESTREINT donc la fenêtre — pour
    # les CINQ configurations à l'identique, puisque le filtre précède la construction des
    # plis, ce qui laisse la comparaison appariée intacte. Le repli est compté (§ 2 quater).
    manque_mois = {m: float(b.isna().mean(axis=0).max())
                   for m, b in d.groupby("mois")[cols_dec]}
    hors = sorted(m for m, v in manque_mois.items() if v > TAUX_MANQUE_MAX)
    if hors:
        perdu = int(d["mois"].isin(hors).sum())
        print(f"  fenêtre restreinte : {len(hors)} mois retiré(s) — "
              + ", ".join(f"{m} ({100 * manque_mois[m]:.0f} % absent)" for m in hors)
              + f" · {perdu:,} jours-station sur {len(d):,}", flush=True)
        d = d[~d["mois"].isin(hors)].reset_index(drop=True)

    print(f"\n{polluant} · {libelle_echeance(horizon)} · axe {axe} · {len(d):,} jours-station"
          f" · {d['station_id'].nunique()} stations · {d['mois'].nunique()} mois", flush=True)
    for nom, cc in (("profil", cols_prof), ("décalé", cols_dec)):
        print(f"  couverture « {nom} » : "
              f"{100 * d[cc].notna().all(axis=1).mean():.1f} % des lignes", flush=True)

    # ── § « un mois absent est un code d'époque » ────────────────────────────────────
    for nom, cc in (("profil", cols_prof), ("décalé", cols_dec)):
        vides = [m for m, bloc in d.groupby("mois")[cc]
                 if float(bloc.isna().mean(axis=0).max()) > TAUX_MANQUE_MAX]
        if vides:
            raise SystemExit(
                f"famille « {nom} » : {len(vides)} mois manquants à plus de "
                f"{100 * TAUX_MANQUE_MAX:.0f} % ({', '.join(vides[:5])}) — « absente » y "
                f"vaut « nous sommes en ce mois-là », et le protocole cache les mois.")
    print(f"  ✅ aucune famille n'a de mois absent au-delà de "
          f"{100 * TAUX_MANQUE_MAX:.0f} %", flush=True)

    modes = {
        "① base (CAMS, terrain, calendrier, tendance)": base,
        "② + climatologie du point (4)": base + CLIMATO,
        "③ + forme du profil horaire (4)": base + cols_prof,
        f"④ + ensemble décalé ({len(cols_dec)})": base + cols_dec,
        "⑤ + les trois": base + CLIMATO + cols_prof + cols_dec,
    }

    ids = np.sort(d["station_id"].unique())
    mois = np.sort(d["mois"].unique())
    rng = np.random.default_rng(GRAINE)
    groupes = np.array_split(rng.permutation(ids), n_spa)
    plis = []
    for i, mm in enumerate(mois):
        m_te, m_tr = d["mois"] == mm, d["mois"] != mm
        if axe == "double":
            dans = d["station_id"].isin(groupes[i % n_spa])
            m_te, m_tr = m_te & dans, m_tr & ~dans
        plis.append((mm, m_te, m_tr))
    ecartes = [(m, int(a.sum()), int(b.sum())) for m, a, b in plis
               if a.sum() < 200 or b.sum() < 1000]
    if ecartes:
        print(f"  ⚠️ {len(ecartes)} pli(s) écarté(s) sur {len(plis)} : "
              + ", ".join(f"{m}({a}/{b})" for m, a, b in ecartes), flush=True)
    print(f"  périmètre effectif : {len(plis) - len(ecartes)} plis exécutés sur "
          f"{len(plis)} prévus", flush=True)

    pred = {k: np.full(len(d), np.nan) for k in modes}
    par_pli, replis = [], []
    for i, (mm, m_te, m_tr) in enumerate(plis):
        if m_te.sum() < 200 or m_tr.sum() < 1000:
            continue
        te, tr = d[m_te].copy(), d[m_tr].copy()
        # référence = TOUTES les stations, le mois de test exclu (§ 0-L)
        ref = d[d["mois"] != mm]
        for bloc in (tr, te):
            c, part = climatologie(ref, bloc)
            bloc[CLIMATO] = c[CLIMATO]
            replis.append(part)
        idx = np.flatnonzero(m_te.to_numpy())
        o, c = te["valeur"].to_numpy(), te["cams_jour"].to_numpy()
        ligne = {"polluant": polluant, "horizon": horizon, "axe": axe, "mois": mm,
                 "n_test": len(te), "n_train": len(tr),
                 "n_stations_test": int(te["station_id"].nunique()),
                 "rmse_ancre": rmse(o, c)}
        for k, (nom, colonnes) in enumerate(modes.items()):
            p = ajuster(DEFAUT, tr, te, colonnes, "cams_jour")
            pred[nom][idx] = p
            ligne[f"rmse_config{k + 1}"] = rmse(o, p)
        par_pli.append(ligne)
        if (i + 1) % 6 == 0:
            print(f"  {i + 1}/{len(plis)} plis · {(time.time() - depart) / 60:.1f} min",
                  flush=True)
    print(f"  repli de la climatologie : max {100 * max(replis):.2f} % des stations d'un bloc",
          flush=True)

    ok = np.ones(len(d), bool)
    for nom, v in pred.items():
        if not np.isfinite(v).any():
            raise SystemExit(f"le mode « {nom} » n'a rien produit")
        ok &= np.isfinite(v)
    o = d["valeur"].to_numpy()[ok]
    r_ancre = rmse(o, d["cams_jour"].to_numpy()[ok])
    tp = pd.DataFrame(par_pli)
    ref_pli = tp["rmse_config1"].to_numpy()

    print(f"\n{'═' * 96}")
    print(f"LEVIERS GRATUITS · {polluant} · {libelle_echeance(horizon)} · axe {axe} · "
          f"{int(ok.sum()):,} prédictions")
    print(f"{'═' * 96}")
    print(f"  {'configuration':46s} {'RMSE':>8s} {'gain/CAMS':>10s} {'vs base':>9s} "
          f"{'σ plis':>7s} {'plis>0':>8s}")
    lignes, ref_gain = [], None
    for k, nom in enumerate(modes):
        x = pred[nom][ok]
        g = 100 * (1 - rmse(o, x) / r_ancre)
        dif = 100 * (1 - tp[f"rmse_config{k + 1}"].to_numpy() / ref_pli)
        marge = np.nan if k == 0 else g - ref_gain
        if ref_gain is None:
            ref_gain = g
        print(f"  {nom:46s} {rmse(o, x):8.4f} {g:+9.2f}% "
              f"{'—' if k == 0 else f'{marge:+8.2f}'} {np.std(dif):7.3f} "
              f"{int((dif > 0).sum()):4d}/{len(dif)}")
        lignes.append({"polluant": polluant, "horizon": horizon, "axe": axe,
                       "configuration": nom, "n_colonnes": len(modes[nom]),
                       "rmse_candidat": rmse(o, x), "rmse_ancre": r_ancre, "gain_pct": g,
                       "apport_vs_base_pct": marge,
                       "ecart_apparie_moyen_pct": float(np.mean(dif)),
                       "ecart_apparie_sigma_pct": float(np.std(dif)),
                       "n_plis_positifs": int((dif > 0).sum()), "n_plis": len(dif),
                       "n_plis_prevus": len(plis), "n_plis_ecartes": len(ecartes),
                       "n_lignes": int(ok.sum()),
                       "fenetre": f"{mois[0]}→{mois[-1]}", "n_mois": len(mois)})

    contexte = {"polluant": polluant, "axe": axe, "echeance": libelle_echeance(horizon)}
    suff = f"{polluant}_h{horizon}_{axe}"
    ecrire_rapport(pd.DataFrame(lignes),
                   RACINE / f"reports/apport_leviers_gratuits_{suff}.csv", contexte,
                   attendues=["gain_pct", "apport_vs_base_pct", "ecart_apparie_moyen_pct"])
    ecrire_rapport(tp, RACINE / f"reports/apport_leviers_gratuits_{suff}_par_pli.csv",
                   contexte, attendues=["rmse_config1", "rmse_config5"])
    for k, nom in list(enumerate(modes))[1:]:
        sortie = RACINE / f"reports/predictions_levier{k + 1}_{polluant}_{axe}.parquet"
        pd.DataFrame({"station_id": d["station_id"].to_numpy()[ok],
                      "jour": d["jour"].to_numpy()[ok], "obs": o,
                      "pred_reference": pred[list(modes)[0]][ok],
                      "pred_candidat": pred[nom][ok]}).to_parquet(sortie, index=False)
    print(f"\nÉcrit : reports/apport_leviers_gratuits_{suff}.csv · "
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
