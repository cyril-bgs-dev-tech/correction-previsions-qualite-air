# Correction statistique des prévisions de qualité de l'air

Post-traitement des prévisions **CAMS Europe** aux stations de mesure françaises. Le modèle
apprend le **résidu** `observation − CAMS` à l'échéance **J0** (échéances 1-24 h ; le J+1 réel est 25-48 h) et le retranche.

Corpus : **36 mois**, 476 stations, observations réglementaires LCSQA, cible journalière.

---

## Le résultat, et sa réserve

Évaluation avec **station et mois cachés simultanément** — la condition de déploiement :
une station nouvelle, une date future.

| polluant | CAMS brut | biais glissant 7 j *(sans apprentissage)* | modèle complet |
|---|---|---|---|
| NO₂ | référence | **+43,1 %** | +44,6 % |
| PM10 | référence | **+18,2 %** | +22,9 % |
| O₃ | référence | **+15,9 %** | +20,4 % |

**Le résultat le plus important de ce dépôt n'est pas le score du modèle.** C'est que
l'essentiel de l'erreur corrigeable de CAMS aux stations est un **biais local persistant**,
qu'une moyenne glissante du résidu sur sept jours récupère sans modèle, sans
réentraînement et sans maintenance. Le modèle appris ajoute **2,7 à 5,7 points** au-delà.

Et ce n'est pas de la persistance : répéter l'observation de l'avant-veille est **pire que
CAMS** sur l'ozone (−42,5 %) et les PM10 (−22,5 %).

### Ce que ce dépôt ne démontre pas

- **Aucun gain de détection d'épisode** sur l'axe déployable : ×1,18 sur PM10 au seuil de
  50 µg/m³, intervalle de confiance contenant zéro. L'avantage est significatif quand le
  mois est connu (×1,82), pas quand il est caché.
- **Aucune supériorité sur une chaîne opérationnelle d'AASQA.** La comparaison porte sur
  CAMS brut. PREV'AIR et les AASQA appliquent déjà une adaptation statistique.
- Au seuil réglementaire ozone de 180 µg/m³, **3 dépassements détectés sur 32**.

Ces limites sont documentées au même titre que les résultats favorables — voir
`reports/`.

---

## Installation

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # socle + tests
pip install -e ".[dev,grib,demo]"  # + décodage GRIB et démonstration
```

`cfgrib` est optionnel car il dépend de la bibliothèque système `eccodes`. Il n'est requis
que par les scripts d'ingestion IFS.

## Vérifier l'installation

```bash
pytest -q                        # ~250 tests, sans réseau ni données
```

## Trois commandes qui produisent les résultats du tableau

```bash
# 1. Prédictions hors pli des trois épreuves + diagnostic de compression
python3 scripts/oof_double_aveugle.py --polluant NO2 --typologie

# 2. Isoler ce que le modèle ajoute au-delà d'une moyenne glissante
python3 scripts/isoler_persistance.py --polluant NO2

# 3. Contribution de chaque famille de prédicteurs, corpus complet
python3 scripts/leviers_36mois.py --polluant NO2
```

Chacune écrit dans `reports/` et affiche ses contrôles. Une assertion qui échoue **lève**
et n'écrit rien.

---

## Protocole d'évaluation

Quatre cellules, selon ce qui est caché du modèle :

| épreuve | station | mois | ce qu'elle mesure |
|---|---|---|---|
| spatiale | **cachée** | vu | transfert vers un lieu non instrumenté |
| temporelle | vue | **caché** | tenue dans le temps |
| **double aveugle** | **cachée** | **caché** | **la condition de déploiement** |
| chronologique | **cachée** | **caché**, passé seul | extrapolation réelle |

Les masques d'entraînement sont donnés **explicitement**, jamais par complément : le
complément du test double aveugle contient encore le mois caché sur d'autres stations et
les stations cachées sur d'autres mois, ce qui rendrait l'épreuve plus facile que chacune
des deux prises séparément.

L'incertitude est estimée par bootstrap de l'**unité de dépendance** — stations pour les
scores continus, jours pour la détection — jamais par ligne.

---

## Organisation

| chemin | contenu |
|---|---|
| `src/aq/` | bibliothèque — ingestion, contrôles, modèles, évaluation |
| `scripts/` | expériences, une par question |
| `reports/` | résultats, journaux et notes de synthèse |
| `tests/` | ~250 tests, sans accès réseau |
| `docs/` | échanges de recherche documentaire, prompts et réponses |
| `CLAUDE.md` | **les règles nées des erreurs commises** — à lire en premier |
| `REPRISE.md` | état du projet, ce qui reste, ce qui a été écarté |

`CLAUDE.md` n'est pas une documentation d'architecture : il consigne les erreurs déjà
faites et la règle qui empêche chacune de revenir. Il vaut d'être lu avant d'écrire du code
d'entrée/sortie ou de lancer un traitement long.

---

## Sources et attribution

- **CAMS Europe** — Copernicus Atmosphere Monitoring Service, ECMWF
- **ERA5** — Copernicus Climate Change Service *(réanalyse : plafond, non déployable)*
- **Observations** — LCSQA / Geod'air, données ouvertes
- **Relief** — Copernicus DEM GLO-30 · **Paysage** — IGN
- **Indice publié** — Atmo Occitanie, données ouvertes

Les données ne sont pas versionnées dans ce dépôt. Les scripts d'ingestion les
reconstituent depuis leurs sources.
