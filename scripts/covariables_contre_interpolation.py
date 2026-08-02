"""Le test décisif : les covariables de paysage battent-elles l'interpolation spatiale ?

Usage : python scripts/covariables_contre_interpolation.py [--polluant O3]
Sortie : reports/COVARIABLES_VS_KRIGEAGE.md et le CSV associé

**La question à laquelle ce script répond.** PREV'AIR corrige déjà ses sorties par
apprentissage, puis les spatialise par krigeage à dérive externe — la dérive étant le
champ CHIMERE lui-même. La seule contribution que ce projet puisse encore revendiquer est
d'apporter des **covariables physiques que cette chaîne n'utilise pas** : relief,
occupation du sol, réseau routier.

Encore faut-il le démontrer. La littérature établit la complémentarité entre modèle de
chimie-transport et covariables de paysage (de Hoogh et al., 2016, DOI
10.1016/j.envres.2016.07.005), mais pas le gain marginal **face à une interpolation
spatiale des résidus** — qui est, elle, déjà en place.

**Le protocole.** Sur des stations entièrement cachées, on compare quatre prédicteurs
qui reçoivent tous exactement la même information d'entraînement :

| Prédicteur | Ce qu'il utilise |
|---|---|
| CAMS brut | rien de plus |
| CAMS + résidu interpolé | la **position** des stations d'entraînement |
| CAMS + covariables | le **terrain** autour de la station cible |
| CAMS + les deux | position et terrain |

Si l'interpolation seule fait aussi bien que les covariables, l'angle « descente
d'échelle » s'effondre et il faut le dire. Si l'hybride bat les deux, la complémentarité
est démontrée sur ce cas précis.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

from aq.eval import comparaison as cmp  # noqa: E402
from aq.models import mos, spatialisation  # noqa: E402
from fit_mos import charger, colonnes_admises  # noqa: E402

# Familles de covariables décrivant le terrain — celles dont on teste l'apport.
def _est_terrain(colonne: str) -> bool:
    return (colonne.startswith(("tpi_", "rugosite_", "chene_", "conifere_",
                                "feuillu_", "route_", "foret_"))
            or colonne in ("altitude_mnt_m", "profondeur_vallee_m", "pente_deg"))


def residu_interpole(entrainement: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Interpole le résidu moyen des stations d'entraînement vers les stations de test.

    **Le résidu est moyenné par station avant interpolation**, et non interpolé heure par
    heure. Interpoler chaque heure ferait dépendre le résultat de la disponibilité
    instantanée des voisines, ce qui mélangerait deux effets : la structure spatiale du
    biais, et les trous de mesure. C'est la structure spatiale qu'on veut isoler ici.
    """
    par_station = (entrainement.assign(residu=entrainement["valeur"] - entrainement["cams"])
                   .groupby("station_id")
                   .agg(residu=("residu", "mean"), x=("x_l93", "first"),
                        y=("y_l93", "first")))
    cible = test.groupby("station_id").agg(x=("x_l93", "first"), y=("y_l93", "first"))
    interpole = spatialisation.interpoler_idw(
        cible["x"], cible["y"], par_station["x"], par_station["y"],
        par_station["residu"],
    )
    correspondance = dict(zip(cible.index, interpole))
    return test["station_id"].map(correspondance).to_numpy(dtype="float64")


def main(polluant: str, horizon: int, n_plis: int) -> int:
    jeu = charger(polluant, horizon)
    colonnes = colonnes_admises(jeu)
    jeu[colonnes] = jeu[colonnes].replace([np.inf, -np.inf], 30_000.0)
    jeu = jeu.dropna(subset=["valeur"]).reset_index(drop=True)

    coords = pd.read_parquet(RACINE / "data/processed/stations.parquet",
                             columns=["station_id", "x_l93", "y_l93"])
    jeu = jeu.merge(coords, on="station_id", how="left").dropna(subset=["x_l93"])

    terrain = [c for c in colonnes if _est_terrain(c)]
    sans_terrain = [c for c in colonnes if not _est_terrain(c)]
    print(f"{polluant} J+{horizon} · {len(jeu):,} paires · "
          f"{jeu['station_id'].nunique()} stations", flush=True)
    print(f"{len(terrain)} variables de terrain · {len(sans_terrain)} autres\n", flush=True)

    stations = np.array(sorted(jeu["station_id"].unique()))
    rng = np.random.default_rng(0)
    groupes = np.array_split(rng.permutation(stations), n_plis)

    morceaux = []
    for groupe in groupes:
        test_masque = jeu["station_id"].isin(groupe)
        entrainement, test = jeu[~test_masque], jeu[test_masque]
        if entrainement.empty or test.empty:
            continue

        bloc = test[["station_id", "valeur", "cams"]].copy()

        # (b) résidu interpolé depuis la position des stations d'entraînement
        bloc["interpole"] = np.clip(
            test["cams"].to_numpy() + residu_interpole(entrainement, test), 0, None)

        # (c) covariables de terrain seules, plus le calendrier et CAMS
        modele_terrain = mos._modele(0)
        modele_terrain.fit(entrainement[colonnes],
                           entrainement["valeur"] - entrainement["cams"])
        bloc["covariables"] = np.clip(
            test["cams"].to_numpy() + modele_terrain.predict(test[colonnes]), 0, None)

        # (d) hybride : on ajoute le résidu interpolé comme variable d'entrée
        colonnes_hybride = colonnes + ["residu_voisins"]
        entr_h = entrainement.assign(
            residu_voisins=residu_interpole(entrainement, entrainement))
        test_h = test.assign(residu_voisins=residu_interpole(entrainement, test))
        modele_hybride = mos._modele(0)
        modele_hybride.fit(entr_h[colonnes_hybride],
                           entr_h["valeur"] - entr_h["cams"])
        bloc["hybride"] = np.clip(
            test["cams"].to_numpy() + modele_hybride.predict(test_h[colonnes_hybride]),
            0, None)

        # (e) témoin : le même modèle privé de toute variable de terrain
        modele_sans = mos._modele(0)
        modele_sans.fit(entrainement[sans_terrain],
                        entrainement["valeur"] - entrainement["cams"])
        bloc["sans_terrain"] = np.clip(
            test["cams"].to_numpy() + modele_sans.predict(test[sans_terrain]), 0, None)

        morceaux.append(bloc)

    p = pd.concat(morceaux, ignore_index=True).dropna()
    variantes = {
        "CAMS brut": "cams",
        "CAMS + résidu interpolé (position seule)": "interpole",
        "CAMS + apprentissage sans terrain": "sans_terrain",
        "CAMS + apprentissage avec terrain": "covariables",
        "CAMS + terrain + résidu interpolé": "hybride",
    }

    print(f"{'prédicteur':44s} {'RMSE':>7s} {'R²':>8s} {'gain/CAMS':>10s}")
    lignes = []
    base = cmp.metriques(p["valeur"], p["cams"])["rmse"]
    for nom, colonne in variantes.items():
        m = cmp.metriques(p["valeur"], p[colonne])
        ic = cmp.intervalle_bootstrap(p["valeur"], p["cams"], p[colonne],
                                      groupes=p["station_id"], n_tirages=250)
        lignes.append({"predicteur": nom, **m, "gain_pct": ic["gain_pct"],
                       "ic_bas": ic["borne_basse"], "ic_haut": ic["borne_haute"]})
        print(f"{nom:44s} {m['rmse']:7.2f} {m['r2']:+8.3f} "
              f"{100 * (1 - m['rmse'] / base):+9.1f} %", flush=True)

    # Le gain marginal du terrain, avec son intervalle : c'est LE chiffre.
    marginal = cmp.intervalle_bootstrap(
        p["valeur"], p["interpole"], p["covariables"],
        groupes=p["station_id"], n_tirages=400)
    print(f"\n→ terrain contre interpolation seule : {marginal['gain_pct']:+.1f} % "
          f"IC95 [{marginal['borne_basse']:+.1f} ; {marginal['borne_haute']:+.1f}] · "
          f"{100 * marginal['part_tirages_positifs']:.0f} % de tirages positifs",
          flush=True)

    pd.DataFrame(lignes).to_csv(
        RACINE / f"reports/covariables_vs_interpolation_{polluant}.csv", index=False)
    return 0


if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description=__doc__)
    parseur.add_argument("--polluant", default="O3", choices=["O3", "NO2", "PM25"])
    parseur.add_argument("--horizon", type=int, default=1, choices=[1, 2, 3])
    parseur.add_argument("--plis", type=int, default=4)
    args = parseur.parse_args()
    raise SystemExit(main(args.polluant, args.horizon, args.plis))
