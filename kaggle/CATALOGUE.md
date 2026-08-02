# Catalogue raisonné

## A. Priorité haute

### 1. H2020 CAPTOR — ozone et microcapteurs

- **Kaggle :** [jeu de données](https://www.kaggle.com/datasets/chaozhuang/h2020-project-captor-dataset) · [notebook MLR/Lasso/SVR/RF](https://www.kaggle.com/code/chaozhuang/sensor-fusion-calibration-w-mlr-lasso-svr-rf).
- **Contenu publié :** vingt-cinq nœuds espagnols, jusqu’à quatre capteurs MOX d’O₃ par nœud, température et humidité ; co-localisations avant et après déploiement et données de stations de référence. Le jeu original documente aussi les campagnes en Espagne, Italie et Autriche ([Zhuang et al., 2021, DOI 10.1016/j.dib.2021.107127](https://doi.org/10.1016/j.dib.2021.107127)).
- **Test déjà réalisé :** le notebook compare régressions linéaires/régularisées, SVR et forêt aléatoire et teste la fusion de plusieurs capteurs. L’étude publiée sur ces capteurs rapporte, dans un exemple de calibration horaire d’O₃, une RMSE de 9,1 µg/m³ pour MLR contre 6,2 µg/m³ pour SVR ([Ripoll et al., 2019, DOI 10.1016/j.scitotenv.2018.09.257](https://doi.org/10.1016/j.scitotenv.2018.09.257)).
- **Leçon AASQA :** la non-linéarité et la fusion peuvent améliorer la calibration, mais la performance sur pics et la dérive après déplacement doivent être des critères séparés. La publication conclut que les capteurs testés ne suffisent pas, dans cette configuration, à surveiller les fortes concentrations d’un épisode.
- **Décision :** **à reproduire en premier** pour une brique microcapteurs/QA ; sans lien direct avec le score CAMS.

### 2. Air Quality Monitoring in European Cities

- **Kaggle :** [jeu de données](https://www.kaggle.com/datasets/yekenot/air-quality-monitoring-in-european-cities) ; quatre notebooks sont attachés au jeu, principalement exploratoires.
- **Contenu annoncé :** trois villes européennes, environ 2020–2023, pas horaire, résolution spatiale annoncée de 0,005°, O₃, NO₂, PM10, PM2,5, coordonnées/stations, composantes du vent, température, humidité, précipitation et variables de végétation/sol ; 54 colonnes. Le jeu cite l’archive [DOI 10.5281/zenodo.11220965](https://doi.org/10.5281/zenodo.11220965).
- **Test déjà réalisé sur Kaggle :** les quatre notebooks inspectés sont de l’EDA ou des analyses génériques ; aucun benchmark public identifié ne démontre une généralisation à une ville ou une station entièrement exclue.
- **Leçon CAMS :** l’intérêt est donc dans **notre protocole**, pas dans leurs scores : leave-one-city-out, leave-one-station-out, covariate shift et comparaison terrain contre interpolation du résidu.
- **Limite :** la provenance exacte de chaque variable et le caractère observé ou dérivé des concentrations doivent être vérifiés dans l’archive Zenodo avant d’en faire un benchmark.
- **Décision :** **à télécharger après CAPTOR** ; bon test spatial européen, pas une barre PREV’AIR.

### 3. Tehran Air Quality FULL — satellite, trafic, météo

- **Kaggle :** [jeu de données](https://www.kaggle.com/datasets/sawdi777/tehran-air-quality-full-sat-traffic-metrology).
- **Contenu annoncé :** vingt-deux stations ; mesures au sol de PM2,5, NO₂ et CO ; trafic, météo et variables satellitaires ; tables journalières et mensuelles.
- **Test déjà réalisé sur Kaggle :** un seul notebook est attaché au jeu au moment de l’inventaire ; aucun résultat publiquement indexé ne fournit un ablationnaire spatial fiable.
- **Leçon CAMS/AASQA :** le schéma de données permet le contrôle qui manque souvent : base stations+météo, puis ajout trafic, puis satellite, avec lignes et plis strictement identiques.
- **Limites :** autre climat, autre réseau, agrégation quotidienne et documentation non réglementaire française. Le satellite mesure une colonne ou un proxy et ne doit pas être assimilé à une concentration de surface.
- **Décision :** **sandbox d’ablation**, jamais source d’un gain attendu annoncé en entretien.

### 4. Beijing Multi-Site Air-Quality

- **Kaggle :** [jeu de données](https://www.kaggle.com/datasets/sid321axn/beijing-multisite-airquality-data-set) · [notebook RNN/GRU/LSTM/Bi-LSTM-attention](https://www.kaggle.com/code/linlinqi321/model-of-bi-lstm-multiheadatt-rnn-gru-lstm).
- **Contenu publié :** douze stations, données horaires de six polluants et météo associée, de mars 2013 à février 2017 ; source Beijing Municipal Environmental Monitoring Center et China Meteorological Administration ([fiche Kaggle issue du jeu UCI](https://www.kaggle.com/datasets/sid321axn/beijing-multisite-airquality-data-set)).
- **Test déjà réalisé :** Kaggle expose des notebooks RNN, GRU, LSTM et Bi-LSTM avec attention. Dans celui inspecté, la mise à l’échelle est ajustée avant la séparation temporelle 70/30 : fuite de distribution future. Aucun pli de station exclue n’est documenté dans la partie inspectée.
- **Leçon CAMS :** réutiliser les architectures, pas les scores. Refaire un factoriel identique LightGBM/LSTM/GNN, avec historique disponible à l’émission, séparation temporelle externe et station complètement absente de l’entraînement.
- **Décision :** **utile pour falsifier l’intérêt des réseaux**, à condition de reconstruire tout le protocole.

## B. Priorité moyenne — fonctions AASQA

### 5. Low-Cost Sensors for Air Pollution Monitoring — Barcelone

- **Kaggle :** [jeu](https://www.kaggle.com/datasets/chaozhuang/low-cost-sensors-for-air-pollution-monitoring).
- **Contenu annoncé :** deux nœuds CAPTOR co-localisés dans une station de référence de Barcelone pendant quatre mois en 2021, échantillonnage à 0,5 Hz, capteurs O₃/NO₂/NO, température et humidité, avec vérité de référence.
- **Apport :** tester agrégation, latence, filtrage, dépendance température–humidité et dérive courte ; intéressant pour une chaîne de contrôle temps réel.
- **Limite :** deux nœuds co-localisés ne testent ni transfert spatial ni vieillissement pluriannuel.

### 6. Gas Sensor Array Drift Dataset

- **Kaggle :** [jeu](https://www.kaggle.com/datasets/orvile/gas-sensor-array-drift-dataset/data).
- **Contenu publié :** 13 910 mesures, seize capteurs, six gaz et trente-six mois ; jeu UCI conçu pour la compensation de dérive ([DOI 10.24432/C5RP6W](https://doi.org/10.24432/C5RP6W)).
- **Apport :** banc d’essai pour détection de rupture, recalibration glissante, stabilité inter-capteurs et seuils de repli.
- **Limite :** plateforme contrôlée et classification de gaz ; pas un réseau ambiant réglementaire.

### 7. Pollen Luxembourg 1992–2018

- **Kaggle :** [jeu](https://www.kaggle.com/datasets/yclaudel/pollen-luxembourg-1992-2018).
- **Contenu annoncé :** concentrations journalières de trente-trois types de pollens depuis 1992, complétées par température minimale/maximale et précipitation ; sources `data.public.lu` et `pollen.lu`.
- **Apport AASQA :** prototype rapide d’une prévision probabiliste des classes et des pics, étude de la valeur des retards polliniques et météo.
- **Limite :** un site/pays et peu de covariables phénologiques ; transfert à l’Occitanie viticole et méditerranéenne non démontré.

### 8. Historical Air Quality — US EPA

- **Kaggle :** [jeu](https://www.kaggle.com/datasets/epa/epa-historical-air-quality).
- **Contenu annoncé :** mesures détaillées du réseau réglementaire américain AQS et agrégats horaires, huit heures, journaliers et annuels ; copie hebdomadaire du Data Mart EPA.
- **Apport :** vérifier à grande échelle les calculs MDA8, les règles de complétude, les agrégations et les intervalles par station.
- **Limite :** normes, typologies et chaîne de prévision différentes ; utile pour tester le code, pas pour comparer une RMSE française.

### 9. Sentinel-5P/TROPOMI NO₂

- **Kaggle :** exemple volumineux [Pakistan NO₂ 2025](https://www.kaggle.com/datasets/muhammadbilal77511/pakistan-nitrogen-dioxide).
- **Contenu annoncé :** pixels journaliers TROPOMI, avec qualité et géolocalisation ; un survol quotidien environ et trous nuageux. Le jeu rappelle explicitement qu’il s’agit d’une colonne troposphérique, pas d’une concentration de surface.
- **Apport AASQA :** valider une chaîne d’ingestion, de filtrage qualité et de construction d’indicateurs de panache/hotspot avant de l’appliquer aux données Copernicus sur l’Occitanie.
- **Limite :** le territoire n’est pas transférable ; il vaut mieux télécharger ensuite le produit institutionnel original sur la France.

### 10. Urban Air Pollution Challenge — réimport Zindi

- **Kaggle :** [réimport 1](https://www.kaggle.com/datasets/alfredkondoro/urban-air-pollution) · [réimport 2](https://www.kaggle.com/datasets/alexandrelemercier/urban-air-pollution-challenge).
- **Contenu annoncé :** PM2,5 au sol, météo et Sentinel-5P, plusieurs centaines de villes, fenêtre d’environ trois mois.
- **Apport :** tester le transfert entre villes peu instrumentées et l’apport marginal du satellite.
- **Limite décisive :** il s’agit de copies d’une compétition Zindi, pas d’un résultat Kaggle original. La fenêtre courte et l’échantillonnage urbain ne représentent pas un cycle saisonnier AASQA.

## C. Ressources contextuelles, à ne pas utiliser comme preuve

| ressource | intérêt limité | raison du déclassement |
|---|---|---|
| [Milan AirQuality and Weather](https://www.kaggle.com/datasets/edmos07/milan-air-quality-and-weather-dataset-daily) | Bon exemple de conversion heure locale/CET–CEST et d’agrégats quotidiens | Les champs de pollution proviennent de services modélisés CAMS/Open-Meteo ; ce n’est pas une vérité station indépendante pour corriger CAMS. |
| [Air Quality Data in India](https://www.kaggle.com/datasets/rohanrao/air-quality-data-in-india) | Gros corpus multi-station avec valeurs manquantes et nombreux notebooks | Beaucoup d’analyses visent l’AQI/EDA ; provenance et validation doivent être reprises avant tout benchmark spatial. |
| [LSTM Multivariate Air Pollution](https://www.kaggle.com/datasets/rupakroy/lstm-datasets-multivariate-univariate) | Exemple pédagogique de fenêtrage séquentiel | Jeu mono-site largement recopié ; ne teste ni stations exclues ni modèle de chimie-transport. |
| [Global Fireworks, Weather & Air Quality](https://www.kaggle.com/datasets/ikanaria/global-fireworks-weather-and-air-quality-2013-2026) | Construire des tests événementiels et calendaires | Pollution issue de CAMS/Open-Meteo et météo ERA5 : ne mesure pas un effet local indépendant et peut réinjecter le modèle à expliquer. |
| [DS4G Environmental Insights Explorer](https://www.kaggle.com/competitions/ds4g-environmental-insights-explorer/overview) | Satellite et estimation d’émissions de centrales | Challenge exploratoire sur facteurs d’émission/NO₂ satellitaire, pas prévision de concentrations au sol ni score réglementaire. |
| [Offset Faults Detection](https://www.kaggle.com/competitions/offset-faults-detection) | Idée de classifieur QA/QC pour capteurs à bas coût | Petite compétition communautaire 2026 ; cinq équipes visibles lors de l’inspection, donc aucune barre robuste à importer. |
| Jeux globaux AQI synthétiques ou « inspirés de » données publiques | Maquettes d’interface seulement | Un AQI agrégé ou synthétique détruit le grain, les unités, les stations et les extrêmes nécessaires à une validation AASQA. |

## D. Ce que Kaggle ne permet pas d’affirmer

- Aucun score Kaggle trouvé n’est directement comparable aux RMSE O₃ MDA8, NO₂ maximum horaire et PM2,5 moyenne journalière du projet.
- Aucun benchmark Kaggle trouvé n’oppose proprement CAMS brut, CAMS-MOS, PREV’AIR et une chaîne AASQA sur les mêmes stations-jours.
- Aucun résultat de notebook ne doit devenir un « gain attendu » sans reproduction avec stations exclues, temps futur gelé, prétraitement ajusté dans chaque pli et variables réellement disponibles à l’émission.
- Les votes, téléchargements et rangs Kaggle mesurent l’activité de la plateforme, pas la validité atmosphérique ou réglementaire.

