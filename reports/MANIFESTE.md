# Manifeste de reproductibilité

Gelé le **2026-07-30 18:44 UTC**. Ce fichier enregistre l'état exact qui a produit les chiffres cités dans `LIVRABLE.md` et la présentation.

## Versions

| Composant | Version |
|---|---|
| python | 3.12.13 |
| lightgbm | 4.6.0 |
| sklearn | 1.6.1 |
| pandas | 2.3.3 |
| numpy | 2.4.6 |
| pyarrow | 23.0.1 |
| xgboost | 3.2.0 |
| catboost | 1.2.10 |

## Données d'entrée

| Fichier | Taille | Empreinte | Modifié |
|---|---|---|---|
| `data/processed/panel_metropole_ds2.parquet` | 380.2 Mo | `e08da9e17a0cd082` | 2026-07-28 13:58 |
| `data/processed/stations.parquet` | 0.1 Mo | `111c630338af4913` | 2026-07-28 13:42 |
| `data/processed/geo_features_metropole.parquet` | 0.2 Mo | `1626103b237a7090` | 2026-07-28 20:41 |
| `data/processed/relief_features_metropole.parquet` | 0.0 Mo | `c2437ea0208e1648` | 2026-07-28 23:33 |
| `data/processed/trafic_population_metropole.parquet` | 0.1 Mo | `f6e1122e6d747ea0` | 2026-07-29 17:44 |

## Chaîne de production — et sa fraîcheur

Un rapport **antérieur** au script qui le produit est périmé : le script a été modifié sans être relancé.

| Script | Empreinte | Rapport | État |
|---|---|---|---|
| `scripts/modele_final.py` | `73102d38c6ddbcf2` | `reports/modele_final.csv` | ✅ à jour |
| `scripts/cible_journaliere.py` | `bdeaaa4dc7ef6876` | `reports/cible_journaliere_O3.csv` | ✅ à jour |
| `scripts/tuning_borne.py` | `310ab0319af3578c` | `reports/tuning_borne_O3.csv` | ✅ à jour |
| `scripts/classification_depassement.py` | `1cdefb3ea7c6a0f2` | `reports/classification_depassement_O3.csv` | ✅ à jour |
| `scripts/front_pareto_queue.py` | `c25713513582dac0` | `reports/front_pareto_O3.csv` | ✅ à jour |
| `scripts/intervalles_bloques.py` | `999bf657d7c5a8d4` | `reports/intervalles_bloques_O3_J1.csv` | ✅ à jour |
| `scripts/diagnostic_residuel.py` | `aec3e540fd76bdc3` | `reports/diagnostic_residuel_O3_J1.csv` | ✅ à jour |
| `scripts/temoin_sans_apprentissage.py` | `70ad52781b7da4f4` | `reports/temoin_sans_apprentissage_O3.csv` | ✅ à jour |
| `scripts/comparer_algorithmes.py` | `7be25b05d5be4e90` | `reports/comparaison_algorithmes_O3.csv` | 🟡 écart **assumé** (voir ci-dessous) |
| `scripts/benchmark_cams.py` | `c4ce7f0bdf8b43a7` | `reports/cams_benchmark.csv` | ✅ à jour |
| `scripts/comparer_mos_officiel_annee.py` | `b12fc6bc9f960968` | `reports/comparaison_mos_officiel_annee_O3.csv` | ✅ à jour |
| `scripts/test_hors_echantillon_2025.py` | `c0be4e629664ec4b` | `reports/test_hors_echantillon_2025_detail_O3.csv` | ✅ à jour |
| `scripts/seuil_decision.py` | `57176259d9248b34` | `reports/seuil_decision_O3.csv` | ✅ à jour |
| `scripts/intervalles_2025.py` | `3da662cac15ad33f` | `reports/intervalles_2025_O3.csv` | ✅ à jour |
| `scripts/mqi_bon_grain.py` | `c33cfd774b487d49` | `reports/mqi_bon_grain.csv` | ✅ à jour |
| `scripts/metriques_episodes_ts.py` | `a288a590e07294dc` | `reports/metriques_episodes_ts_O3.csv` | ✅ à jour |
| `scripts/double_aveugle_journalier.py` | `61d4883563dd8dc2` | `reports/double_aveugle_journalier_O3.csv` | ✅ à jour |
| `scripts/verite_dossier.py` | `e4e099dbc455d338` | `reports/VERITE_DOSSIER.md` | ✅ à jour |
| `src/aq/models/mos.py` | `69db22ab5156422b` | *(module)* | — |
| `src/aq/eval/comparaison.py` | `a9b85d8328f2b465` | *(module)* | — |

## Comment régénérer le résultat principal

```bash
python3 scripts/modele_final.py --polluants O3,NO2,PM25 --horizons 1,2,3 --plis 3
```

Durée mesurée : **1 519 s**. La graine est fixée dans `aq.models.mos` ; à versions identiques, le tableau doit se reproduire poste à poste.

## Écarts assumés

**`reports/comparaison_algorithmes_O3.csv`** — Le script a été étendu à XGBoost, CatBoost, RealMLP et TabM après la production du CSV. L'évaluation de ces candidats a été **délibérément arrêtée** : trois bibliothèques de boosting tiennent en 0,3 point, et RealMLP a été interrompu après 32 min sur échantillon réduit contre 20-30 s pour les autres. Le CSV reflète les trois candidats retenus ; les quatre autres n'ont été mesurés qu'en passe unitaire.

