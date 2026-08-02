#!/usr/bin/env python3
"""Le vent croisé à la géographie : test de criblage, sans aucun téléchargement.

L'hypothèse
-----------
Nos 28 variables de paysage et nos 5 de trafic sont **isotropes** — des distances et des
densités dans des cercles autour de la station. Or une station sous le vent d'une autoroute à
300 m n'est pas la même station lorsque le vent tourne. CAMS ne peut pas le représenter : il a
**une valeur par maille de 8 × 11 km**, et cette information est strictement sous-maille.

C'est donc, en principe, le meilleur candidat restant selon la règle que ce projet a dégagée :
une correction n'ajoute que là où le modèle amont est aveugle. Encore faut-il le vérifier.

Pourquoi ce test est un criblage, et pas la mesure
--------------------------------------------------
Les vraies géométries — réseau routier, forêt — sont obtenues en interrogeant un service WFS
**à la volée** ; elles ne sont pas sur le disque, et les variables conservées ne sont que des
sommes, sans azimut. Les récupérer par source demanderait plusieurs heures de requêtes.

On substitue donc aux sources leurs **mandataires** : les stations de typologie `traffic` et
`industrial`. Une station trafic est implantée là **parce qu'il y a une source** — c'est un
proxy imparfait, mais gratuit, et sa géométrie est déjà connue au mètre près en Lambert-93.

**Ce que le test décide.** Si l'exposition anisotrope à ces mandataires n'ajoute rien au-delà
du vent brut, réinterroger le WFS pour les vraies géométries a peu de chances de payer, et la
piste redescend dans le programme. Si elle ajoute, la dépense est justifiée et l'on saura
quoi extraire.

**Ce qu'il ne peut pas décider.** Un mandataire est plus grossier que la source : 93 points
contre 1,2 million de tronçons routiers. Un résultat nul ici ne réfute pas l'hypothèse, il la
rend seulement moins prioritaire. Un résultat positif, lui, est une borne **basse**.

⚠️ VERDICT DE LA PASSE UNITAIRE — 30/07/2026 : ce criblage n'a PAS le pouvoir de trancher
-----------------------------------------------------------------------------------------
Mesuré sur juillet 2024, 354 144 heures, 476 stations :

| échelle λ | part de valeurs nulles |
|---|---|
| 1 km — **l'échelle sous-maille visée** | **86,4 %** |
| 5 km | 54,5 % |
| 20 km | 7,3 % |

**Le mandataire est vide précisément là où l'hypothèse vit.** Quatre-vingt-treize stations
trafic réparties sur la France donnent un espacement typique de plusieurs dizaines de
kilomètres : aucune station n'a de voisine trafic à un kilomètre sous le vent. Quarante
stations sur 476 n'ont jamais la moindre exposition.

À 20 km — seule échelle où le signal existe — on ne mesure plus du sous-maille mais du
**transport régional**, que CAMS résout déjà à 8 × 11 km. Le test répondrait donc à une autre
question que celle posée.

Aucun mandataire fondé sur les stations ne peut atteindre l'échelle du kilomètre : la densité
du réseau l'interdit, quelle que soit la pondération choisie. **L'hypothèse exige les vraies
géométries** — réinterrogation du WFS en conservant distance et azimut par source, plusieurs
heures de requêtes. Le script est conservé pour ce jour-là : seule la constitution des sources
changera, la mécanique d'exposition est écrite et vérifiée.

Ce constat est le fruit d'une passe unitaire de 7 secondes. Le lot complet aurait rendu un nul
local ininterprétable et un positif régional hors sujet.

Usage : python3 scripts/apport_anisotropie.py [--polluant O3]
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

from aq.features import exposure  # noqa: E402
from aq.eval.critere import cribler, seuil  # noqa: E402
from aq.harmonize import wind  # noqa: E402
from apport_meteo import evaluer, ic_difference, meteo_journaliere, resume  # noqa: E402
from cible_journaliere import GRANDEUR_PAR_POLLUANT, agreger_journalier  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

# Échelles de décroissance : la rue canyon, le quartier, l'agglomération. Au-delà de 10 km un
# mandataire ponctuel ne représente plus grand-chose.
LAMBDAS = {"proche": 1_000.0, "moyen": 5_000.0, "loin": 20_000.0}
OUVERTURE = 45.0  # demi-ouverture du secteur au vent, en degrés
# Le critère de rétention vit dans `aq.eval.critere` : **relatif au RMSE de base**,
# donc comparable entre polluants. L'ancien 0,3 µg/m³ absolu valait 2 % sur le NO₂
# et 11 % sur les PM2,5.


def exposition_horaire(stations: pd.DataFrame, meteo: pd.DataFrame,
                       typologie: str) -> pd.DataFrame:
    """Exposition anisotrope de chaque station aux mandataires d'un type donné.

    **La géométrie ne change pas d'une heure à l'autre.** Distances et azimuts sont donc
    calculés **une fois** ; seul le poids angulaire dépend du vent. Recalculer la matrice à
    chaque pas horaire coûterait 13 000 fois plus pour un résultat identique — c'est la même
    faute que lire un fichier point par point au lieu de le charger.
    """
    sources = stations[stations["type_station"] == typologie]
    if sources.empty:
        return pd.DataFrame()

    recepteurs = stations.reset_index(drop=True)
    d = exposure.distances(recepteurs["x_l93"], recepteurs["y_l93"],
                           sources["x_l93"], sources["y_l93"])
    theta = exposure.azimuts(recepteurs["x_l93"], recepteurs["y_l93"],
                             sources["x_l93"], sources["y_l93"])
    # Une station est sa propre voisine à distance nulle : on la retire, sans quoi toute
    # station trafic aurait une exposition infinie à elle-même.
    meme = (d < 1.0)
    d = np.maximum(d, 1.0)

    index = {s: i for i, s in enumerate(recepteurs["station_id"])}
    ligne = meteo["station_id"].map(index)
    valide = ligne.notna()
    ligne = ligne[valide].astype(int).to_numpy()
    direction = meteo.loc[valide, "vent_direction_deg"].to_numpy()

    sortie = {"station_id": meteo.loc[valide, "station_id"].to_numpy(),
              "timestamp_utc": meteo.loc[valide, "timestamp_utc"].to_numpy()}
    poids_angulaire = wind.poids_secteur_au_vent(
        theta[ligne], direction[:, None], demi_ouverture_deg=OUVERTURE)
    poids_angulaire = np.where(np.isnan(direction)[:, None], 0.0, poids_angulaire)
    poids_angulaire = np.where(meme[ligne], 0.0, poids_angulaire)

    for nom, lam in LAMBDAS.items():
        decroissance = np.exp(-d[ligne] / lam)
        decroissance = np.where(meme[ligne], 0.0, decroissance)
        sortie[f"vent_{typologie}_{nom}"] = (decroissance * poids_angulaire).sum(axis=1)
        # Le pendant **isotrope**, indispensable : sans lui on ne saurait pas si le gain
        # éventuel vient de l'anisotropie ou simplement de la proximité aux points chauds,
        # que les variables actuelles ne portent pas non plus.
        sortie[f"iso_{typologie}_{nom}"] = decroissance.sum(axis=1)
    return pd.DataFrame(sortie)


def main(polluant: str, n_plis: int) -> int:
    depart = time.time()
    jeu = charger(polluant, 1)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"])

    stations = pd.read_parquet(
        RACINE / "data/processed/stations.parquet",
        columns=["station_id", "type_station", "x_l93", "y_l93", "metropole", "active"])
    stations = stations[stations["metropole"] & stations["active"]].dropna(
        subset=["x_l93", "y_l93"])

    # Le vent horaire vient d'ERA5 : c'est une réanalyse, donc ce test mesure lui aussi un
    # **plafond**, au même titre que `apport_meteo.py`.
    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo/era5_metropole_*.parquet")))
    debut, fin = jeu["timestamp_utc"].min(), jeu["timestamp_utc"].max()
    blocs = []
    for f in fichiers:
        m = pd.read_parquet(f, columns=["station_id", "timestamp_utc",
                                        "vent_direction_deg", "vent_vitesse_m_s"])
        m = m[(m["timestamp_utc"] >= debut) & (m["timestamp_utc"] <= fin)]
        if not m.empty:
            blocs.append(m)
    meteo = pd.concat(blocs, ignore_index=True)
    print(f"{polluant} · {len(meteo):,} heures de vent · "
          f"{stations['type_station'].value_counts().to_dict()}", flush=True)

    morceaux = [exposition_horaire(stations, meteo, t) for t in ("traffic", "industrial")]
    expo = morceaux[0]
    for m in morceaux[1:]:
        if not m.empty:
            expo = expo.merge(m, on=["station_id", "timestamp_utc"], how="outer")
    noms_vent = [c for c in expo.columns if c.startswith("vent_")]
    noms_iso = [c for c in expo.columns if c.startswith("iso_")]
    print(f"  {len(noms_vent)} variables anisotropes + {len(noms_iso)} isotropes · "
          f"{time.time() - depart:.0f}s", flush=True)

    jeu = jeu.merge(expo, on=["station_id", "timestamp_utc"], how="left").dropna(
        subset=noms_vent + noms_iso)
    grandeur = GRANDEUR_PAR_POLLUANT[polluant]
    j = agreger_journalier(jeu, colonnes + noms_vent + noms_iso, grandeur)
    base = [c for c in colonnes if c != "cams"] + ["cams_moy_jour", "cams_jour"]

    # La comparaison se fait **au-dessus de la météo enrichie** : le vent brut y est déjà, donc
    # tout gain supplémentaire est imputable à l'anisotropie, pas au vent.
    j["jour"] = pd.to_datetime(j["jour"])
    met, cols_moy, cols_enr = meteo_journaliere((j["jour"].min(), j["jour"].max()))
    met["jour"] = pd.to_datetime(met["jour"])
    j = j.merge(met, on=["station_id", "jour"], how="inner")
    avec_meteo = base + cols_moy + cols_enr

    stations_j = np.sort(j["station_id"].unique())
    j["groupe"] = j["station_id"].map({s: i % n_plis for i, s in enumerate(stations_j)})
    print(f"  {len(j):,} jours-station · {len(stations_j)} stations", flush=True)

    jeux = {"base + météo": avec_meteo,
            "+ points chauds (isotrope)": avec_meteo + noms_iso,
            "+ anisotropie au vent": avec_meteo + noms_iso + noms_vent}
    resultats, predictions = {}, {}
    for nom, predicteurs in jeux.items():
        p = evaluer(j, predicteurs, n_plis)
        predictions[nom] = p
        resultats[nom] = resume(p, polluant) | {"n_variables": len(predicteurs)}
        print(f"  {nom:28s} {len(predicteurs):3d} var · RMSE {resultats[nom]['rmse']:6.3f} · "
              f"{time.time() - depart:5.0f}s", flush=True)

    print(f"\n{'jeu':28s} {'RMSE':>7s} {'décile haut':>12s} {'POD':>7s} {'CSI':>7s}")
    for nom, r in resultats.items():
        print(f"{nom:28s} {r['rmse']:7.3f} {r['rmse_decile_haut']:12.3f} "
              f"{r.get('POD', np.nan):7.3f} {r.get('CSI', np.nan):7.3f}", flush=True)

    print(f"\n{'─' * 74}")
    lignes = []
    for depuis, vers in (("base + météo", "+ points chauds (isotrope)"),
                         ("+ points chauds (isotrope)", "+ anisotropie au vent")):
        gain = resultats[depuis]["rmse"] - resultats[vers]["rmse"]
        bas, haut = ic_difference(predictions[depuis], predictions[vers])
        print(f"{vers:28s} contre {depuis:28s}\n  gain {gain:+.3f} µg/m³ · "
              f"IC95 [{bas:+.3f} ; {haut:+.3f}] · "
              f"{'écart établi' if bas > 0 else 'IC contenant zéro'}")
        lignes.append({"de": depuis, "vers": vers, "gain": gain, "ic_bas": bas,
                       "ic_haut": haut})

    total = resultats["base + météo"]["rmse"] - resultats["+ anisotropie au vent"]["rmse"]
    s = seuil(reference)
    print(f"\nCriblage : {'POURSUIVRE' if total >= s else 'PISTE DÉPRIORISÉE'} — "
          f"gain total {total:+.3f} µg/m³ contre un critère de {s:.3f} "
          f"(2 % du RMSE de base).")
    print("Rappel : les mandataires sont 164 stations, pas 1,2 M de tronçons routiers.\n"
          "Un nul ne réfute pas l'hypothèse ; un positif est une borne **basse**.")

    pd.DataFrame(resultats).T.to_csv(RACINE / f"reports/apport_anisotropie_{polluant}.csv")
    pd.DataFrame(lignes).to_csv(
        RACINE / f"reports/apport_anisotropie_{polluant}_ic.csv", index=False)
    print(f"\nÉcrit : reports/apport_anisotropie_{polluant}.csv · "
          f"{time.time() - depart:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--polluant", default="O3")
    p.add_argument("--plis", type=int, default=3)
    args = p.parse_args()
    raise SystemExit(main(args.polluant, args.plis))
