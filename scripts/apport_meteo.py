#!/usr/bin/env python3
"""Ce que la météo apporterait — et pourquoi ce chiffre est un plafond, pas un gain.

La question
-----------
Le modèle n'utilise **aucune** variable météorologique : ses 53 prédicteurs sont la sortie
CAMS, le paysage, le relief, le trafic et le calendrier. Ce n'est pas un oubli — c'était une
précaution contre la fuite d'information. Mais deux mesures indépendantes désignent cette
absence comme la limite réelle du projet :

- en **prédiction**, les PM2,5 ne se prédisent pas par le paysage (+2 %) et leur R² de
  climatologie est de 0,139 : leur variance est météorologique ;
- en **surveillance**, le moniteur de résidu bute sur un bruit de 3,87 µg/m³ qui est de la
  variabilité synoptique en mode commun — donc irréductible sans conditionnement météo.

**Ce que ce script mesure est un plafond, jamais un gain déployable.** ERA5 est une réanalyse :
elle n'existe pas à l'heure d'émission. Une chaîne opérationnelle emploierait les **prévisions**
IFS, disponibles elles, et en obtiendrait moins — d'autant moins que l'échéance est lointaine.
Le résultat borne donc ce qu'une météo prévue pourrait apporter ; il ne le livre pas.

Trois jeux de variables, et la seconde comparaison est la plus intéressante
--------------------------------------------------------------------------
1. **base** — les 53 prédicteurs actuels ;
2. **+ météo moyenne** — les 8 variables ERA5, agrégées au jour par leur moyenne, comme tous
   les autres prédicteurs le sont déjà ;
3. **+ météo enrichie** — les mêmes, plus des statistiques journalières **choisies pour leur
   sens physique** : maximum de température (le forçage photochimique est un maximum), minimum
   de couche limite (la dilution la plus faible de la journée décide de l'accumulation), et le
   vent décomposé en sinus/cosinus — une direction en degrés est **circulaire**, et 359° y est
   voisin de 1° alors qu'un arbre les sépare.

L'écart entre 2 et 3 rejoue, du côté des **prédicteurs**, la thèse que ce projet établit du
côté de la cible : le choix de la statistique d'agrégation décide du résultat.

Critère d'arrêt du projet : retenir seulement si le gain atteint **0,3 µg/m³** avec IC95 au
dessus de zéro, **sans** dégrader le RMSE du décile haut de plus de 0,3 ni le CSI.

Usage : python3 scripts/apport_meteo.py [--polluant O3]
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

from aq.eval import comparaison as cmp  # noqa: E402
from aq.eval.critere import cribler, seuil  # noqa: E402
from aq.models.moteur import modele_mos  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402
from modele_final import REGLE  # noqa: E402
from scores_episodes import scores  # noqa: E402

METEO = ["precipitation_mm", "rayonnement_w_m2", "temperature_c", "point_rosee_c",
         "pression_hpa", "couche_limite_m", "vent_direction_deg", "vent_vitesse_m_s"]
# Le critère de rétention vit désormais dans `aq.eval.critere` : il est
# **relatif au RMSE de base**, donc comparable entre polluants.
SEUIL_O3 = 120.0


def meteo_journaliere(bornes: tuple[pd.Timestamp, pd.Timestamp]) -> pd.DataFrame:
    """Agrège ERA5 au jour-station, en deux jeux : moyennes seules, puis enrichi."""
    debut, fin = bornes
    mois = {f"{p.year}{p.month:02d}" for p in pd.period_range(debut, fin, freq="M")}
    fichiers = [f for f in sorted(glob.glob(
        str(RACINE / "data/processed/meteo/era5_metropole_*.parquet")))
        if any(m in Path(f).stem for m in mois)]
    if not fichiers:
        raise SystemExit("aucun mois ERA5 ne recouvre la période d'entraînement")

    blocs = [pd.read_parquet(f) for f in fichiers]
    m = pd.concat(blocs, ignore_index=True)
    m = m[(m["timestamp_utc"] >= debut) & (m["timestamp_utc"] <= fin)]
    m["jour"] = m["timestamp_utc"].dt.floor("D")

    # La direction du vent est **circulaire** : la moyenner en degrés fait de 359° et 1° une
    # direction sud. On projette sur le cercle avant d'agréger, jamais après.
    radians = np.deg2rad(m["vent_direction_deg"])
    m["vent_sin"] = np.sin(radians) * m["vent_vitesse_m_s"]
    m["vent_cos"] = np.cos(radians) * m["vent_vitesse_m_s"]

    moyennes = {c: (c, "mean") for c in METEO if c != "vent_direction_deg"}
    enrichi = {
        "temperature_max": ("temperature_c", "max"),
        "couche_limite_min": ("couche_limite_m", "min"),
        "couche_limite_max": ("couche_limite_m", "max"),
        "rayonnement_max": ("rayonnement_w_m2", "max"),
        "vent_sin": ("vent_sin", "mean"), "vent_cos": ("vent_cos", "mean"),
        "vent_vitesse_max": ("vent_vitesse_m_s", "max"),
        "precipitation_totale": ("precipitation_mm", "sum"),
    }
    return (m.groupby(["station_id", "jour"])
             .agg(**moyennes, **enrichi).reset_index()), list(moyennes), list(enrichi)


def evaluer(j: pd.DataFrame, predicteurs: list[str], n_plis: int) -> pd.DataFrame:
    """Validation par stations exclues, mêmes plis pour tous les jeux de variables."""

    sortie = j[["station_id", "jour", "obs_jour", "cams_jour", "groupe"]].copy()
    sortie["pred"] = np.nan
    for g in range(n_plis):
        test = j["groupe"] == g
        m = modele_mos(graine=0)
        m.fit(j.loc[~test, predicteurs], j.loc[~test, "obs_jour"] - j.loc[~test, "cams_jour"])
        sortie.loc[test, "pred"] = np.clip(
            j.loc[test, "cams_jour"] + m.predict(j.loc[test, predicteurs]), 0, None)
    return sortie


def resume(p: pd.DataFrame, polluant: str) -> dict:
    """RMSE global, RMSE du décile haut, et détection sur la fenêtre réglementaire."""
    m = cmp.metriques(p["obs_jour"], p["pred"])
    haut = p[p["obs_jour"] >= p["obs_jour"].quantile(0.9)]
    r = {"rmse": m["rmse"], "biais": m["biais"], "r2": m["r2"],
         "rmse_decile_haut": float(np.sqrt(((haut["obs_jour"] - haut["pred"]) ** 2).mean()))}
    if polluant == "O3":
        # Fenêtre LCSQA : l'ozone s'évalue d'avril à septembre.
        saison = p[pd.to_datetime(p["jour"]).dt.month.between(4, 9)]
        d = (saison["obs_jour"] >= SEUIL_O3).to_numpy()
        if d.sum() >= 20:
            r |= {k: v for k, v in scores(d, (saison["pred"] >= SEUIL_O3).to_numpy()).items()
                  if k in ("POD", "FAR", "CSI")}
    return r


def ic_difference(a: pd.DataFrame, b: pd.DataFrame, tirages: int = 400) -> tuple[float, float]:
    """IC95 sur la différence de RMSE, par bootstrap **de stations** — jamais de lignes."""
    fusion = a[["station_id", "obs_jour", "pred"]].rename(columns={"pred": "pred_a"})
    fusion["pred_b"] = b["pred"].to_numpy()
    par_station = {s: g for s, g in fusion.groupby("station_id")}
    stations = np.array(list(par_station))
    rng = np.random.default_rng(0)
    diffs = []
    for _ in range(tirages):
        ech = pd.concat([par_station[s] for s in rng.choice(stations, len(stations), True)])
        ra = np.sqrt(((ech["obs_jour"] - ech["pred_a"]) ** 2).mean())
        rb = np.sqrt(((ech["obs_jour"] - ech["pred_b"]) ** 2).mean())
        diffs.append(ra - rb)
    return tuple(np.percentile(diffs, [2.5, 97.5]))


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])
    j = agreger_journalier(jeu, colonnes, GRANDEUR_PAR_POLLUANT[polluant])
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    j["jour"] = pd.to_datetime(j["jour"])
    met, cols_moy, cols_enr = meteo_journaliere((j["jour"].min(), j["jour"].max()))
    met["jour"] = pd.to_datetime(met["jour"])
    avant = len(j)
    j = j.merge(met, on=["station_id", "jour"], how="inner")
    print(f"{polluant} · {avant:,} jours-station → {len(j):,} après jointure ERA5 "
          f"({100 * len(j) / avant:.0f} % conservés) · {j['station_id'].nunique()} stations",
          flush=True)

    stations = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations)})

    jeux = {"base (actuel)": base,
            "+ météo moyenne": base + cols_moy,
            "+ météo enrichie": base + cols_moy + cols_enr}

    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:20s} {len(predicteurs):3d} variables · "
              f"RMSE {resultats[nom]['rmse']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    t = pd.DataFrame(resultats).T
    print(f"\n{'jeu de variables':20s} {'RMSE':>7s} {'décile haut':>12s} "
          f"{'POD':>7s} {'FAR':>7s} {'CSI':>7s}")
    for nom, r in resultats.items():
        print(f"{nom:20s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f} "
              f"{r.get('POD', np.nan):7.3f} {r.get('FAR', np.nan):7.3f} "
              f"{r.get('CSI', np.nan):7.3f}", flush=True)

    print(f"\n{'─' * 74}\nContre la base, avec IC95 par bootstrap de stations :")
    reference = resultats["base (actuel)"]
    lignes = []
    for nom in ("+ météo moyenne", "+ météo enrichie"):
        gain = reference["rmse"] - resultats[nom]["rmse"]
        bas, haut = ic_difference(predictions["base (actuel)"], predictions[nom])
        cout_queue = resultats[nom]["rmse_decile_haut"] - reference["rmse_decile_haut"]
        cout_csi = reference.get("CSI", np.nan) - resultats[nom].get("CSI", np.nan)
        # Critère **relatif au RMSE de base**, jamais les 0,3 µg/m³ absolus d'autrefois :
        # ce seuil valait 2 % sur le NO₂ et 11 % sur les PM2,5, écartant ces dernières par
        # simple artefact d'unité. Voir `aq.eval.critere`.
        v = cribler(reference["rmse"], gain, bas,
                    gain_queue=-cout_queue, rmse_queue_base=reference["rmse_decile_haut"])
        retenu = v.retenu and not (cout_csi > 0)
        print(f"  {nom:20s} gain {gain:+.3f} µg/m³  IC95 [{bas:+.3f} ; {haut:+.3f}]  "
              f"queue {cout_queue:+.3f}  ΔCSI {-cout_csi:+.3f}")
        motif = v.motif if not v.retenu else "CSI dégradé"
        print(f"  {'':20s} → {'RETENU' if retenu else 'écarté : ' + motif}", flush=True)
        lignes.append({"jeu": nom, "gain": gain, "ic_bas": bas, "ic_haut": haut,
                       "cout_queue": cout_queue, "delta_csi": -cout_csi, "retenu": retenu})

    # **Le seuil de comparaison est celui du projet, pas un seuil choisi pour la circonstance.**
    # Une première version déclarait « même leçon que sur la cible » dès 0,05 µg/m³ d'écart :
    # c'était un seuil arbitraire et complaisant, qui aurait fait d'un effet huit fois plus
    # petit l'équivalent du résultat central du dossier.
    ecart = resultats["+ météo moyenne"]["rmse"] - resultats["+ météo enrichie"]["rmse"]
    print(f"\nAgrégation des PRÉDICTEURS — moyenne contre statistiques choisies : "
          f"{ecart:+.3f} µg/m³.")
    seuil_relatif = seuil(reference["rmse"])
    if ecart >= seuil_relatif:
        print("  → au-dessus du critère d'arrêt : le choix de la statistique compte aussi "
              "côté prédicteurs.")
    else:
        print(f"  → **sous le critère d'arrêt de {seuil_relatif:.3f} µg/m³ (2 % du RMSE de "
              f"base)**. Le choix de la statistique "
              f"d'agrégation\n    pèse donc bien moins sur les prédicteurs que sur la cible, "
              f"où le même changement\n    vaut ~0,68 µg/m³ sur ce polluant. Ne pas présenter "
              f"les deux comme un seul résultat.")

    t.to_csv(RACINE / f"reports/apport_meteo_{polluant}.csv")
    pd.DataFrame(lignes).to_csv(RACINE / f"reports/apport_meteo_{polluant}_ic.csv",
                                index=False)
    print(f"\n⚠️ Plafond, pas gain : ERA5 est une réanalyse. Une chaîne opérationnelle "
          f"emploierait\nles prévisions IFS et obtiendrait moins.")
    print(f"Écrit : reports/apport_meteo_{polluant}.csv · {time.time() - depart:.0f}s",
          flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
