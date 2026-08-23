#!/usr/bin/env python3
"""L'ozone change d'étalon le 01/07/2025 — le niveau bouge-t-il ?

Ce que ce script existe pour trancher
-------------------------------------
Le flux LCSQA fait basculer **tout** l'ozone français du code de validité 1 au code 4 le
1ᵉʳ juillet 2025. Le vocabulaire EIONET dit ce que vaut ce code :

    4 — *Valid (Ozone only) using CCQM.O3.2019*

C'est une donnée **valide** : le code ne signale pas un défaut de validation, mais le
rattachement de la mesure à l'étalon métrologique CCQM.O3.2019. La chaîne du projet, elle,
filtrait `validite == 1` et jetait donc treize mois d'ozone valide — corrigé le 01/08/2026
dans `scripts/ingerer_lcsqa.py`.

Reste la question que la correction du filtre ne répond pas : **un changement d'étalon peut
déplacer le niveau des concentrations.** La révision de la section efficace d'absorption UV
de l'ozone est de l'ordre du pour-cent — assez peu pour passer inaperçu dans un graphique,
assez pour biaiser un résidu appris sur des données d'avant et appliqué à des données
d'après. Recoller les deux périodes sans le vérifier serait exactement le défaut que
`CLAUDE.md` § 5 décrit : plausible, silencieux, coûteux.

⚠️ La première version de ce script a conclu, et elle avait tort
-----------------------------------------------------------------
Elle annonçait une « marche commune de **+17,96 %** sur 95 % des stations » et concluait que
les deux périodes ne s'agrègent pas. Trois défauts, tous silencieux :

1. **Le rapport obs/CAMS n'est pas exempt de saison.** Il vaut 0,80 en novembre et 0,97 en
   avril. Or `VERITE_DOSSIER` documente déjà un **biais ozone saisonnier** de CAMS. Comparer
   une période « toutes saisons » à une période « juillet » mesure la saison.
2. **La période « après » est un seul mois utile** — 2026-07, à 182 000 paires, contre 6 000
   pour 2025-07 et **aucune** de 2025-08 à 2026-06, faute de prévisions CAMS. La comparaison
   porte donc sur deux juillets distants de **deux ans**.
3. **Juillet 2026 a été exceptionnel** : la médiane CAMS y vaut 74,9 µg/m³ contre 63,1 en
   juillet 2024. L'écart interannuel réel est du même ordre que l'effet cherché.

**Le témoin qui a tranché** : le NO₂ n'a connu **aucun** changement d'étalon, et il montre
**+11,7 %** sur exactement la même fenêtre. La marche n'est donc pas celle de l'ozone.

Comment la question est posée
-----------------------------
Une rupture d'étalon est **multiplicative et commune à toutes les stations**. Une variation
saisonnière ne l'est pas. Le test doit donc séparer les deux, et c'est le point délicat : le
1ᵉʳ juillet tombe en plein pic d'ozone, la saison à elle seule déplacerait le niveau de
plusieurs dizaines de pour-cent.

Trois lectures, de la plus naïve à la seule concluante :

1. **Niveaux bruts de part et d'autre** — donné pour mémoire, et pour montrer précisément
   qu'il ne conclut rien : la saison y domine tout.
2. **Comparaison d'une année sur l'autre, à mois identique** — juillet 2025 contre juillet
   2024, etc. La saison est neutralisée ; restent la météo de l'année et l'étalon.
3. **Rapport à CAMS, station par station et mois par mois** — la référence est une prévision
   dont l'étalon, lui, n'a pas changé. Si l'observation saute de 1 % et pas CAMS, le rapport
   `obs / cams` saute de 1 % au même moment, à saison et à météo neutralisées. C'est la seule
   des trois qui isole l'étalon.

Ce qu'on décidera avec
----------------------
Une marche nette et commune aux stations sur la lecture 3 : les deux périodes ne s'agrègent
pas sans correction, et il faut le dire dans le dossier. Pas de marche : on agrège, et on
l'écrit — un résultat négatif se publie comme les autres.

Usage : python3 scripts/continuite_etalon_o3.py
Sortie : reports/continuite_etalon_o3.csv + le compte rendu sur la sortie standard
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RACINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RACINE / "src"))
sys.path.insert(0, str(RACINE / "scripts"))

# Le flux LCSQA est horodaté en UTC **avec fuseau explicite** : une borne naïve ne se compare
# pas à cette colonne, et pandas lève plutôt que de deviner. C'est le bon comportement.
BASCULE = pd.Timestamp("2025-07-01", tz="UTC")


def observations(polluant: str = "O3") -> pd.DataFrame:
    """Ozone horaire du flux LCSQA, tous codes de validité positifs, avec le code."""
    fichiers = sorted(glob.glob(str(RACINE / "data/interim/lcsqa/lcsqa_*.parquet")))
    if not fichiers:
        raise SystemExit("aucun mois LCSQA ingéré — lancer scripts/ingerer_lcsqa.py")
    morceaux = []
    for f in fichiers:
        t = pd.read_parquet(f, columns=["station_id", "polluant", "timestamp_utc",
                                        "valeur", "validite"])
        t = t[t["polluant"] == polluant]
        if not t.empty:
            morceaux.append(t)
    o = pd.concat(morceaux, ignore_index=True)

    # Règle 2 bis : compter le reçu contre le demandé, et nommer ce qui manque.
    o["mois"] = o["timestamp_utc"].dt.to_period("M")
    attendus = pd.period_range(pd.Period("2024-01", "M"), o["mois"].max(), freq="M")
    manquants = sorted(set(attendus) - set(o["mois"].unique()))
    if manquants:
        raise SystemExit(f"mois d'ozone absents du flux ingéré : "
                         f"{', '.join(str(m) for m in manquants)}")
    if not (o["validite"] > 0).all():
        raise SystemExit("des codes de validité négatifs ont survécu à l'ingestion")
    apres = o[o["timestamp_utc"] >= BASCULE]
    if apres.empty:
        raise SystemExit("aucune observation après le 01/07/2025 — réingestion incomplète")
    return o


def previsions(espece: str = "o3", colonne: str = "o3_conc") -> pd.DataFrame:
    """CAMS J+1 aux stations, lu **directement**, pas via le panel du projet.

    ⚠️ Une première version passait par ``fit_mos.charger``. Elle ne pouvait pas fonctionner :
    ce panel s'appuie sur les observations **EEA**, qui s'arrêtent début 2025 — donc aucune
    station n'y existe après la bascule du 01/07/2025, et la comparaison n'avait aucun point
    commun. L'erreur était visible dans le message même du chargeur (« sans observation :
    2025-02 … 2026-07 »), qui journalise sa couverture précisément pour ça.

    Cela révèle au passage un chantier ouvert : **l'ozone récupéré du flux LCSQA n'est pas
    encore fusionné dans le panel de modélisation.** Tant qu'il ne l'est pas, les 13 mois
    existent sur le disque sans être utilisables par le modèle.

    Ici on lit donc les prévisions extraites aux stations telles quelles, et on les joint aux
    observations LCSQA — les deux étiquetées par la **fin** de l'heure, en UTC.
    """
    fichiers = sorted(glob.glob(str(RACINE / "data/processed/meteo/"
                                    f"cams_prevision_metropole_{espece}_*.parquet")))
    if not fichiers:
        raise SystemExit(f"aucune prévision CAMS {espece} extraite")
    morceaux = []
    for f in fichiers:
        t = pd.read_parquet(f, columns=["station_id", "timestamp_utc", colonne,
                                        "echeance_h"])
        # J+1 : la tranche d'échéances de 24 à 47 h. Nommer la colonne par son **nom**,
        # jamais par sa position — c'est ainsi que `level`, constant à 0, s'était glissé
        # dans six colonnes de dispersion d'ensemble.
        morceaux.append(t[t["echeance_h"].between(24, 47)]
                        .rename(columns={colonne: "cams"})
                        .drop(columns="echeance_h"))
    c = pd.concat(morceaux, ignore_index=True)
    c = c.groupby(["station_id", "timestamp_utc"], as_index=False)["cams"].mean()
    print(f"CAMS J+1 · {len(c):,} lignes · {c['station_id'].nunique()} stations · "
          f"{c['timestamp_utc'].min():%Y-%m} → {c['timestamp_utc'].max():%Y-%m}")
    return c


def rapports_mensuels(polluant: str, espece: str, colonne: str) -> pd.DataFrame:
    """Rapport médian obs/CAMS par mois calendaire et par station."""
    o = observations(polluant)
    c = previsions(espece, colonne)
    d = o.merge(c, on=["station_id", "timestamp_utc"], how="inner")
    d = d[(d["cams"] > 5) & (d["valeur"] > 5)]
    if d.empty:
        raise SystemExit(f"{polluant} : aucun appariement obs/CAMS")
    d["ym"] = d["timestamp_utc"].dt.strftime("%Y-%m")
    d["mois_num"] = d["timestamp_utc"].dt.month
    d["apres"] = d["timestamp_utc"] >= BASCULE
    d["rapport"] = d["valeur"] / d["cams"]
    return d


def main() -> int:
    print("── Le protocole, et pourquoi il est en différence de différences ──────────")
    print("  Un rapport obs/CAMS porte trois effets superposés : le changement d'étalon")
    print("  (cherché), la saison (le biais de CAMS est saisonnier), et l'année (juillet")
    print("  2026 fut exceptionnel). On neutralise la saison en ne comparant QUE des mois")
    print("  calendaires identiques, et l'année par un TÉMOIN — le NO₂, qui n'a connu")
    print("  aucun changement d'étalon. Ce qui reste est propre à l'ozone.\n")

    tables = {}
    for polluant, espece, colonne in (("O3", "o3", "o3_conc"),
                                      ("NO2", "no2", "no2_conc")):
        tables[polluant] = rapports_mensuels(polluant, espece, colonne)

    # ── Les mois calendaires disponibles des deux côtés de la bascule ────────────
    o3 = tables["O3"]
    avant = set(o3.loc[~o3["apres"], "mois_num"])
    apres = set(o3.loc[o3["apres"], "mois_num"])
    communs = sorted(avant & apres)
    print(f"── Mois calendaires présents des deux côtés : {communs or 'AUCUN'} ────────")
    if not communs:
        raise SystemExit("aucun mois calendaire commun aux deux périodes — "
                         "la question ne peut pas être posée sur ce corpus")

    lignes = []
    for polluant, d in tables.items():
        for m in communs:
            g = d[d["mois_num"] == m]
            a = g.loc[~g["apres"], "rapport"]
            b = g.loc[g["apres"], "rapport"]
            if len(a) < 1000 or len(b) < 1000:
                print(f"  {polluant} mois {m:02d} · effectifs insuffisants "
                      f"({len(a)} / {len(b)}) — écarté")
                continue
            lignes.append({"polluant": polluant, "mois": m,
                           "rapport_avant": a.median(), "rapport_apres": b.median(),
                           "marche_pct": 100 * (b.median() / a.median() - 1),
                           "n_avant": len(a), "n_apres": len(b)})
    t = pd.DataFrame(lignes)
    if t.empty:
        raise SystemExit("aucun mois exploitable des deux côtés — INCONCLUSIF")
    print()
    print(t.round(4).to_string(index=False))

    # ── La différence de différences ─────────────────────────────────────────────
    print(f"\n{'─' * 78}")
    pivot = t.pivot_table(index="mois", columns="polluant", values="marche_pct")
    if "NO2" not in pivot.columns or pivot["NO2"].isna().all():
        raise SystemExit("témoin NO₂ indisponible — sans lui, un écart mesuré sur l'ozone "
                         "ne s'attribue à rien. INCONCLUSIF.")
    pivot["ozone_propre"] = pivot["O3"] - pivot["NO2"]
    print("Marche par polluant, et différence — en points de pourcentage :\n")
    print(pivot.round(2).to_string())

    n_mois = int(pivot["ozone_propre"].notna().sum())
    effet = float(pivot["ozone_propre"].mean())
    sortie = RACINE / "reports/continuite_etalon_o3.csv"
    t.to_csv(sortie, index=False)

    # 🔴 Le seuil ne s'écrit pas en dur — il se calcule sur la dispersion de CETTE
    # exécution (§ 0-A). L'ancienne version décidait sur `abs(effet) >= 3.0`, un nombre
    # qui ne regardait pas la variabilité mensuelle : avec un seul mois de chaque côté il
    # aurait fallu 3 points pour conclure alors que la résolution valait ~7, et avec douze
    # mois il en faut 3 alors que la résolution vaut ~2,7. Le même chiffre disait deux
    # choses opposées selon la taille du corpus.
    v = pivot["ozone_propre"].dropna().to_numpy()
    ec = float(np.std(v, ddof=1)) if len(v) > 1 else float("nan")
    se = ec / np.sqrt(len(v)) if len(v) > 1 else float("nan")
    demi = 1.96 * se
    # Ce que la métrologie annonce, et donc ce que le corpus doit savoir résoudre pour
    # avoir le droit d'écrire « écarté » plutôt que « non détecté ».
    ATTENDU_LITTERATURE_PCT = 1.0

    print(f"\n{'─' * 78}")
    print(f"  Effet propre à l'ozone, moyenné sur {n_mois} mois calendaire(s) : "
          f"**{effet:+.2f} points**")
    if len(v) > 1:
        print(f"  Dispersion mensuelle {ec:.2f} pt · IC95 [{effet - demi:+.2f} ; "
              f"{effet + demi:+.2f}] · RÉSOLUTION ±{demi:.2f} pt")
    if n_mois < 3:
        print("\n  → **INCONCLUSIF, et c'est le résultat.** Un seul ou deux mois")
        print("    calendaires sont disponibles des deux côtés, et l'écart interannuel")
        print("    qui les sépare est du même ordre que l'effet cherché.")
    elif abs(effet) > demi:
        print(f"\n  → MARCHE PROPRE À L'OZONE de {effet:+.2f} pt, témoin déduit — l'IC95")
        print("    exclut zéro. Documenter la rupture avant tout entraînement à cheval")
        print("    sur la date.")
    elif demi <= ATTENDU_LITTERATURE_PCT:
        print(f"\n  → ÉCARTÉ : {effet:+.2f} pt, IC95 entièrement sous le "
              f"{ATTENDU_LITTERATURE_PCT:.0f} % attendu de la")
        print("    littérature métrologique. Les deux périodes s'agrègent, et cette fois")
        print("    l'effet est bien exclu, pas seulement non vu.")
    else:
        print(f"\n  → NON DÉTECTÉ, et ce n'est PAS « écarté » : {effet:+.2f} pt, mais la")
        print(f"    résolution du corpus (±{demi:.2f} pt) reste plus large que le "
              f"{ATTENDU_LITTERATURE_PCT:.0f} % que la")
        print("    littérature métrologique attribue à CCQM.O3.2019. Un décalage de cet")
        print("    ordre passerait sous ce test sans y laisser de trace.")
        print("\n    Décision opérationnelle : agréger les deux périodes — le risque est")
        print("    borné à quelques points et ne penche pas d'un côté — en écrivant que")
        print("    la continuité est NON DÉTECTÉE à ±{:.1f} pt, jamais « vérifiée ».".format(demi))
    print(f"\nÉcrit : {sortie.relative_to(RACINE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
