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
Sortie : reports/apport_<lot>_<polluant>_h<n>_<axe>.csv
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

# ── Les lots mesurables par ce script, ouverts le 23/08/2026 ──────────────────────────
#
# Le script mesurait les quatre gaz précurseurs. Sa mécanique — charger un lot extrait aux
# stations, agréger au jour en moyenne ET maximum, l'empiler en DERNIÈRE position sur la
# pile complète — ne doit rien à ces gaz-là. Elle est donc paramétrée plutôt que clonée :
# une copie de 321 lignes aurait dupliqué, avec le code, les cinq garde-fous qu'il porte
# (fenêtre restreinte, jointure comptée, couverture imprimée, colonnes attendues, § 4 bis).
#
# Les noms sont ceux que CAMS LIVRE, jamais ceux demandés à l'API — contrôlés sur fichier.
#
# 🔴 Les POLLENS sortent de la famille mesurable — mesuré le 23/08/2026, avant de lancer
# les quatre exécutions qui les auraient consommés. Le fichier `chimie_*` porte six
# variables ; le contrôle de couverture mois par mois en écarte deux :
#
#   hcho_conc, chocho_conc, no_conc, co_conc   0,00 % manquant · 100 % sur les 37 mois ✅
#   bpg_conc                                   2023-08, 09, 10 VIDES · 2023-11 à 30 %
#   gpg_conc                                   2023-10 VIDE · 2023-09 à 3 %, 2023-11 à 30 %
#
# Un mois entièrement absent est un **code d'époque** : sous validation mois-caché,
# « famille absente » équivaut à « on est dans ces mois-là », et le modèle peut apprendre
# la date au lieu de la chimie. Les pollens sont donc un lot SÉPARÉ, à mesurer sur sa
# propre fenêtre contiguë — ils avaient d'ailleurs été acquis comme assurance, l'archive se
# refermant, et non comme piste prioritaire.
CHIMIE = ["hcho_conc", "chocho_conc", "no_conc", "co_conc"]
POLLENS = ["bpg_conc", "gpg_conc"]

# ── Le criblage IFS, ouvert le 23/08/2026 ─────────────────────────────────────────────
#
# La pile ne porte AUCUNE météo — l'objection ERA5 ne s'y applique pas, mais la question de
# ce qu'une météo PRÉVUE (donc déployable, contrairement à la réanalyse) apporterait reste
# ouverte. Mesurée le 31/07 sur une pile bien plus faible : +2,2 % NO₂, +5,5 % O₃,
# +4,7 % PM2,5 — et sur PM2,5 l'IFS BAT ERA5.
#
# 🔴 Onze mois sont extraits (2024-02 → 2024-12) et les 104 colonnes ne se valent pas.
# Couverture comptée mois par mois :
#
#   t2m · tp · u10 · v10 · temperature_c · precipitation_mm · vent_vitesse_m_s ·
#   vent_direction_deg                                   100 % sur les 11 mois ✅
#   d2m · point_rosee_c · rayonnement_w_m2 · ssrd        absentes de 2024-02, 100 % ensuite
#   les ~60 champs en niveaux de pression                25 à 90 % selon le MOIS, nulles
#                                                        en 2024-12 — code d'époque pur
#   mn2t3 · mx2t3 · mucape · q200 · q500 · sot           SEULEMENT en 2024-11 et 12
#
# La famille criblable est donc les huit champs de surface complets, et c'est précisément
# ce que le dépôt a déjà mesuré comme porteur : « pluie, vent, rayonnement portent la
# météo », et « sur NO₂ tout vient de la pluie ».
#
# ⚠️ Onze mois font trois blocs de trois : le criblage DIMENSIONNE l'effet, il ne le
# démontre pas. Sa seule fonction est de décider si l'acquisition des 26 mois manquants
# vaut d'être lancée.
# ⚠️ Et la restriction est devenue OBLIGATOIRE le 23/08/2026, pas seulement prudente :
# ramener la tolérance de regroupement des plages de 20 Mo à 1 Mo a cessé de tirer les
# champs superflus voisins, donc de les décoder. Les mois téléchargés AVANT portent
# 104 colonnes, ceux d'APRÈS en portent 39. Le schéma dépend désormais de la date de
# téléchargement — un code d'époque d'un genre nouveau, créé par une optimisation.
#
# Les huit champs ci-dessous sont présents des deux côtés, à 100 %. Toute colonne prise
# hors de cette liste séparerait les mois anciens des récents.
IFS_SURFACE = ["t2m", "tp", "u10", "v10", "temperature_c", "precipitation_mm",
               "vent_vitesse_m_s", "vent_direction_deg"]

LOTS_MESURABLES = {
    # lot : (variables, préfixe de colonne, libellé humain)
    "precurseurs": (GAZ, "pre", "précurseurs"),
    "chimie": (CHIMIE, "chi", "chimie"),
    # ⚠️ « pollens » lit les mêmes fichiers `chimie_*` : le lot de TÉLÉCHARGEMENT et le lot
    # de MESURE ne sont pas la même chose, et les confondre ferait chercher des fichiers
    # `pollens_metropole_*` qui n'existent pas.
    "pollens": (POLLENS, "pol", "pollens"),
    "ifs": (IFS_SURFACE, "ifs", "météo prévue IFS (surface)"),
}

# Le fichier extrait dont un lot de mesure tire ses colonnes, quand ce n'est pas son nom.
FICHIER_SOURCE = {"pollens": "chimie"}


def charger_lot(lot: str) -> tuple[pd.DataFrame, list[str], list[str]]:
    """Les variables d'un lot au grain journalier — moyenne ET maximum.

    La moyenne décrit le niveau du jour, le maximum l'épisode : un pic d'ammoniac de six
    heures après un épandage n'est pas un fond élevé, et leur moyenne les confond. La
    spéciation garde déjà les deux pour la même raison.

    ⚠️ **Concaténer AVANT d'agréger** : le fichier d'un mois déborde sur le suivant, donc le
    2 de chaque mois est servi par deux fichiers. Agréger par fichier puis concaténer
    produirait deux lignes partielles pour ce jour-là, et une jointure qui rend plus de
    lignes qu'elle n'en reçoit.
    """
    variables, prefixe, libelle = LOTS_MESURABLES[lot]
    source = FICHIER_SOURCE.get(lot, lot)
    fs = sorted(glob.glob(str(RACINE / f"data/processed/meteo/{source}_metropole_*.parquet")))
    if not fs:
        raise SystemExit(f"aucun mois du lot « {lot} » extrait — lancer "
                         f"scripts/extraire_speciation.py --lot {source}")
    t = pd.concat([pd.read_parquet(f) for f in fs], ignore_index=True)
    manque = [c for c in variables if c not in t.columns]
    if manque:
        raise SystemExit(f"variables absentes des parquets « {lot} » : {manque}")
    t["jour"] = pd.to_datetime(t["timestamp_utc"]).dt.tz_localize(None).dt.floor("D")
    g = t.groupby(["station_id", "jour"])[variables].agg(["mean", "max"])
    g.columns = [f"{prefixe}_{a}_{b}" for a, b in g.columns]
    g = g.reset_index()
    moyennes = [c for c in g.columns if c.endswith("_mean")]
    maxima = [c for c in g.columns if c.endswith("_max")]
    print(f"  {libelle} : {len(fs)} mois · {len(t):,} lignes horaires → {len(g):,} "
          f"jours-station · {len(variables)} variables", flush=True)
    return g, moyennes, maxima


def rmse(o: np.ndarray, x: np.ndarray) -> float:
    return float(np.sqrt(np.mean((x - o) ** 2)))


def main(polluant: str, horizon: int, n_spa: int, axe: str,
         retirer: tuple[str, ...] = (), lot: str = "precurseurs") -> int:
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

    # ── Le lot mesuré, la seule chose que ce script mesure ──────────────────────────
    libelle_lot = LOTS_MESURABLES[lot][2]
    pre, moyennes, maxima = charger_lot(lot)
    avant_pre = len(d)
    d = d.merge(pre, on=["station_id", "jour"], how="left")
    if len(d) != avant_pre:
        raise SystemExit(f"jointure du lot « {lot} » : {avant_pre:,} → {len(d):,} lignes")
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
             f"② + {libelle_lot}, moyennes ({len(moyennes)})": base + moyennes,
             f"③ + {libelle_lot}, moyennes et maxima ({len(toutes)})": base + toutes}

    mois = np.sort(d["mois"].unique())
    ids = np.sort(d["station_id"].unique())
    print(f"\n{polluant} · {libelle_echeance(horizon)} · axe {axe} · {len(d):,} jours-station"
          f" · {len(ids)} stations · {len(mois)} mois · base {len(base)} colonnes", flush=True)
    print(f"  couverture du lot « {lot} » : "
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

    # 🔴 Le titre nommait « PRÉCURSEURS GAZEUX » quel que soit le lot mesuré — et il l'a
    # fait, en clair, sur une exécution `--lot chimie`. Une étiquette qui affirme une
    # identité survit à la généralisation ; ce qu'elle affirme, non (§ 0-H).
    print(f"\n{'═' * 96}\nAPPORT · {libelle_lot.upper()} · {polluant} · "
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
                   RACINE / f"reports/apport_{lot}_{suff}.csv", contexte,
                   attendues=["gain_pct", "apport_vs_pile_pct", "ecart_apparie_moyen_pct"])
    ecrire_rapport(tp, RACINE / f"reports/apport_{lot}_{suff}_par_pli.csv",
                   contexte, attendues=["rmse_config1", "rmse_config2"])
    print(f"\nÉcrit : reports/apport_{lot}_{suff}.csv · "
          f"{(time.time() - depart) / 60:.1f} min")
    return 0


if __name__ == "__main__":
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--polluant", default="NO2")
    a.add_argument("--horizon", type=int, default=2)
    a.add_argument("--plis-spatiaux", type=int, default=3)
    a.add_argument("--axe", default="double", choices=("double", "temporel"))
    a.add_argument("--lot", default="precurseurs", choices=sorted(LOTS_MESURABLES),
                   help="quel lot de variables CAMS empiler en dernière position")
    a.add_argument("--retirer", default="",
                   help="familles à retirer de la base, séparées par des virgules "
                        "— « geoscf » élargit la fenêtre en gardant la concurrence ; "
                        "tout retirer rend la mesure ININTERPRÉTABLE (substitution). "
                        "Le nom de l'artefact porte la liste.")
    n = a.parse_args()
    # 🔴 `--lot` avait été ajouté à l'analyseur mais PAS à l'appel — 23/08/2026. Argparse
    # l'acceptait, `main` gardait son défaut, et le script refaisait la mesure des
    # précurseurs en écrasant leur fichier. Rien n'a levé : le lot demandé n'existe que
    # dans le nom de l'artefact attendu, et c'est la file qui l'a vu.
    #
    # Passer par mot-clé plutôt que par position : une signature qui s'allonge ne peut
    # alors plus perdre un argument en silence.
    raise SystemExit(main(polluant=n.polluant, horizon=n.horizon,
                          n_spa=n.plis_spatiaux, axe=n.axe, lot=n.lot,
                          retirer=tuple(x for x in n.retirer.split(',') if x)))
