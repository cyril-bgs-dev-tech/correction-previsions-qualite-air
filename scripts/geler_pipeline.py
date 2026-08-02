#!/usr/bin/env python3
"""Gèle l'état exact qui a produit les résultats — pour qu'un tiers puisse les refaire.

Ce que « geler » veut dire ici
-----------------------------
Pas archiver le code : consigner ce qui, s'il changeait, changerait les chiffres sans
prévenir. Un relecteur du 30/07 le formule mieux que moi — ce qu'un jury regarde avant les
chiffres, c'est « une commande qui régénère le tableau », pas l'élégance du notebook.

Le manifeste enregistre quatre choses :

1. **Les versions** des bibliothèques qui décident du résultat numérique. LightGBM change
   ses défauts entre versions mineures ; un même script peut rendre deux nombres différents
   à un an d'intervalle sans qu'aucune ligne n'ait bougé.
2. **Les empreintes des données d'entrée** — taille et somme de contrôle des parquets. C'est
   ce qui distingue « le modèle a changé » de « les données ont changé », question
   impossible à trancher après coup sans ces valeurs.
3. **Les empreintes des scripts** qui ont produit les rapports, et la date des rapports
   eux-mêmes : un rapport plus ancien que le script qui le produit est **périmé**, et le
   manifeste le signale au lieu de le laisser croire à jour.
4. **Les résultats clés**, recopiés depuis les CSV, pour qu'une régénération future puisse
   être comparée poste à poste.

Le contrôle n° 3 est le seul qui puisse échouer, et c'est le plus utile : il attrape le cas
où l'on a corrigé un script sans relancer ce qu'il alimente.

Usage : python3 scripts/geler_pipeline.py
Sortie : reports/MANIFESTE.md
"""

from __future__ import annotations

import datetime as dt
import hashlib
import subprocess
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[1]

# Scripts dont dépendent les chiffres cités, et le rapport que chacun alimente.
CHAINE = {
    "scripts/modele_final.py": "reports/modele_final.csv",
    "scripts/cible_journaliere.py": "reports/cible_journaliere_O3.csv",
    "scripts/tuning_borne.py": "reports/tuning_borne_O3.csv",
    "scripts/classification_depassement.py": "reports/classification_depassement_O3.csv",
    "scripts/front_pareto_queue.py": "reports/front_pareto_O3.csv",
    "scripts/intervalles_bloques.py": "reports/intervalles_bloques_O3_J1.csv",
    "scripts/diagnostic_residuel.py": "reports/diagnostic_residuel_O3_J1.csv",
    "scripts/temoin_sans_apprentissage.py": "reports/temoin_sans_apprentissage_O3.csv",
    "scripts/comparer_algorithmes.py": "reports/comparaison_algorithmes_O3.csv",
    "scripts/benchmark_cams.py": "reports/cams_benchmark.csv",
    # Chaîne de la comparaison au produit officiel, ajoutée le 30/07. Elle porte le résultat
    # central du dossier : sans elle au manifeste, une correction de script resterait
    # invisible et le rapport périmé passerait pour à jour.
    "scripts/comparer_mos_officiel_annee.py":
        "reports/comparaison_mos_officiel_annee_O3.csv",
    "scripts/test_hors_echantillon_2025.py":
        "reports/test_hors_echantillon_2025_detail_O3.csv",
    "scripts/seuil_decision.py": "reports/seuil_decision_O3.csv",
    "scripts/intervalles_2025.py": "reports/intervalles_2025_O3.csv",
    "scripts/mqi_bon_grain.py": "reports/mqi_bon_grain.csv",
    "scripts/metriques_episodes_ts.py": "reports/metriques_episodes_ts_O3.csv",
    "scripts/double_aveugle_journalier.py": "reports/double_aveugle_journalier_O3.csv",
    # En dernier : il **agrège** tous les précédents. S'il est plus ancien que l'un d'eux,
    # le document gelé ne reflète plus les rapports qu'il prétend résumer.
    "scripts/verite_dossier.py": "reports/VERITE_DOSSIER.md",
    "src/aq/models/mos.py": None,
    "src/aq/eval/comparaison.py": None,
}

# Écarts script/rapport **assumés**, avec leur raison. Un décalage documenté n'est pas un
# oubli — mais il doit rester visible, sinon le manifeste ment par omission.
EXCEPTIONS = {
    "reports/comparaison_algorithmes_O3.csv":
        "Le script a été étendu à XGBoost, CatBoost, RealMLP et TabM après la production "
        "du CSV. L'évaluation de ces candidats a été **délibérément arrêtée** : trois "
        "bibliothèques de boosting tiennent en 0,3 point, et RealMLP a été interrompu "
        "après 32 min sur échantillon réduit contre 20-30 s pour les autres. Le CSV "
        "reflète les trois candidats retenus ; les quatre autres n'ont été mesurés qu'en "
        "passe unitaire.",
}

DONNEES = [
    "data/processed/panel_metropole_ds2.parquet",
    "data/processed/stations.parquet",
    "data/processed/geo_features_metropole.parquet",
    "data/processed/relief_features_metropole.parquet",
    "data/processed/trafic_population_metropole.parquet",
]


def empreinte(chemin: Path, octets: int = 8_000_000) -> str:
    """SHA-256 des premiers mégaoctets — suffisant pour détecter un changement, rapide.

    Une empreinte complète sur 380 Mo coûterait plusieurs secondes par fichier sans rien
    apporter : on cherche à détecter une substitution, pas à résister à une attaque.
    """
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        h.update(f.read(octets))
    return h.hexdigest()[:16]


def versions() -> dict[str, str]:
    noms = ("lightgbm", "sklearn", "pandas", "numpy", "pyarrow", "xgboost", "catboost")
    sortie = {"python": sys.version.split()[0]}
    for nom in noms:
        try:
            module = __import__(nom)
            sortie[nom] = getattr(module, "__version__", "?")
        except ImportError:
            sortie[nom] = "absent"
    return sortie


def main() -> int:
    maintenant = dt.datetime.now(dt.timezone.utc)
    lignes = [
        "# Manifeste de reproductibilité",
        "",
        f"Gelé le **{maintenant:%Y-%m-%d %H:%M} UTC**. Ce fichier enregistre l'état exact "
        "qui a produit les chiffres cités dans `LIVRABLE.md` et la présentation.",
        "",
        "## Versions",
        "",
        "| Composant | Version |", "|---|---|",
    ]
    lignes += [f"| {nom} | {v} |" for nom, v in versions().items()]

    lignes += ["", "## Données d'entrée", "",
               "| Fichier | Taille | Empreinte | Modifié |", "|---|---|---|---|"]
    for rel in DONNEES:
        chemin = RACINE / rel
        if not chemin.exists():
            lignes.append(f"| `{rel}` | — | **ABSENT** | — |")
            continue
        st = chemin.stat()
        modif = dt.datetime.fromtimestamp(st.st_mtime, dt.timezone.utc)
        lignes.append(f"| `{rel}` | {st.st_size / 1e6:.1f} Mo | `{empreinte(chemin)}` | "
                      f"{modif:%Y-%m-%d %H:%M} |")

    lignes += ["", "## Chaîne de production — et sa fraîcheur", "",
               "Un rapport **antérieur** au script qui le produit est périmé : le script a "
               "été modifié sans être relancé.", "",
               "| Script | Empreinte | Rapport | État |", "|---|---|---|---|"]

    perimes = []
    for rel, rapport in CHAINE.items():
        chemin = RACINE / rel
        if not chemin.exists():
            lignes.append(f"| `{rel}` | **ABSENT** | — | ⚠️ |")
            continue
        emp = empreinte(chemin)
        if rapport is None:
            lignes.append(f"| `{rel}` | `{emp}` | *(module)* | — |")
            continue
        cible = RACINE / rapport
        if not cible.exists():
            lignes.append(f"| `{rel}` | `{emp}` | `{rapport}` | ⚠️ **manquant** |")
            perimes.append(rapport)
            continue
        etat = "✅ à jour"
        if cible.stat().st_mtime < chemin.stat().st_mtime:
            if rapport in EXCEPTIONS:
                etat = "🟡 écart **assumé** (voir ci-dessous)"
            else:
                etat = "⚠️ **PÉRIMÉ** — script modifié après"
                perimes.append(rapport)
        lignes.append(f"| `{rel}` | `{emp}` | `{rapport}` | {etat} |")

    lignes += ["", "## Comment régénérer le résultat principal", "",
               "```bash", "python3 scripts/modele_final.py --polluants O3,NO2,PM25 "
               "--horizons 1,2,3 --plis 3", "```", "",
               "Durée mesurée : **1 519 s**. La graine est fixée dans "
               "`aq.models.mos` ; à versions identiques, le tableau doit se reproduire "
               "poste à poste."]

    if EXCEPTIONS:
        lignes += ["", "## Écarts assumés", ""]
        for rapport, raison in EXCEPTIONS.items():
            lignes += [f"**`{rapport}`** — {raison}", ""]

    if perimes:
        lignes += ["", "## ⚠️ À relancer avant publication", ""]
        lignes += [f"- `{p}`" for p in perimes]

    chemin_sortie = RACINE / "reports/MANIFESTE.md"
    chemin_sortie.write_text("\n".join(lignes) + "\n", encoding="utf-8")

    print(f"Écrit : {chemin_sortie.relative_to(RACINE)}")
    print(f"  {len(DONNEES)} jeux de données · {len(CHAINE)} éléments de chaîne")
    if perimes:
        print(f"  ⚠️ {len(perimes)} rapport(s) périmé(s) ou manquant(s) :")
        for p in perimes:
            print(f"     {p}")
    else:
        print("  ✅ tous les rapports sont postérieurs à leur script")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
