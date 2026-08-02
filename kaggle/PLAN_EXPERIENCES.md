# Plan d’expériences tiré de la veille Kaggle

## 1. Voie correction CAMS

| priorité | expérience | ressource Kaggle | protocole minimal | décision attendue |
|---:|---|---|---|---|
| 1 | **Observations récentes disponibles à l’émission** | [Pékin multi-stations](https://www.kaggle.com/datasets/sid321axn/beijing-multisite-airquality-data-set) | LightGBM fixe ; bras sans lags puis lags 1/3/6/12/24 h ; masquer tout retard non disponible ; test année future × stations exclues | Mesure la valeur de l’auto-régression sans fuite. Dans le projet France, cette expérience doit être rejouée avec l’heure d’émission réelle de l’AASQA. |
| 2 | **Gradient boosting contre séquentiel/attention** | [notebook d’architectures](https://www.kaggle.com/code/linlinqi321/model-of-bi-lstm-multiheadatt-rnn-gru-lstm) | Mêmes lignes, variables, historiques et plis pour LightGBM, GRU/LSTM et modèle attention ; scaler ajusté dans chaque pli seulement | Conserver le réseau uniquement si son IC de gain exclut zéro et si le coût/latence reste acceptable. |
| 3 | **Transfert géographique dur** | [trois villes européennes](https://www.kaggle.com/datasets/yekenot/air-quality-monitoring-in-european-cities) | Trois plis leave-one-city-out, puis stations exclues dans la ville d’entraînement ; métriques par station et sur queue | Quantifie l’écart entre « nouvelle station du même réseau » et « nouveau territoire ». |
| 4 | **Ablation terrain–trafic–satellite** | [Téhéran multi-source](https://www.kaggle.com/datasets/sawdi777/tehran-air-quality-full-sat-traffic-metrology) | Modèle et lignes constants : météo seule ; +trafic ; +satellite ; +interactions. Imputation et sélection apprises dans chaque pli | Écarter toute famille dont le gain spatial ou temporel est instable. Ne pas transférer le gain numérique à la France. |
| 5 | **Extremes et perte asymétrique** | Pékin + Europe trois villes | MSE, Huber, pondération du décile supérieur, quantile ; seuil choisi sur validation, test externe intact ; RMSE globale + queue + POD/FAR/CSI | Vérifie si le remède au tassement des pics survit hors France avant d’alourdir le pipeline principal. |
| 6 | **GNN de stations contre voisinage tabulaire** | Pékin multi-stations | Graphe fixé sans les cibles du test ; GNN contre LightGBM avec lags agrégés des voisins ; station entièrement retirée du graphe d’apprentissage | Un gain nul confirme que la densité/volume ne justifie pas un GNN ; un gain positif motive seulement une réplication France. |

### Garde-fous obligatoires

1. Aucun `fit_transform` avant la création des plis.
2. Imputation, sélection, normalisation et réglage des hyperparamètres sont réappris dans chaque pli.
3. Séparer quatre questions : date future, station future, région future et changement de version du modèle amont.
4. Ne jamais comparer un AQI, une moyenne horaire, une MDA8 et un maximum horaire comme s’il s’agissait d’une même cible.
5. Les résultats Kaggle ne servent qu’à décider quelles expériences lancer ; les chiffres France restent les seuls résultats du projet.

## 2. Voie amélioration d’une AASQA

| priorité | brique opérationnelle | ressource | prototype proposé | valeur métier possible |
|---:|---|---|---|---|
| 1 | **Calibration et dérive des microcapteurs** | [CAPTOR](https://www.kaggle.com/datasets/chaozhuang/h2020-project-captor-dataset) | Calibration courte, test après déplacement, dérive par semaine, recalibration glissante, comparaison capteur unique/fusion ; O₃ moyen et pics séparés | Densifier l’observation sans confondre sensibilisation et mesure réglementaire. |
| 2 | **Détection automatique de défauts** | [Gas Sensor Drift](https://www.kaggle.com/datasets/orvile/gas-sensor-array-drift-dataset/data) + [Offset Faults](https://www.kaggle.com/competitions/offset-faults-detection) | Injecter offsets, dérive, blocage, bruit et pertes ; évaluer délai de détection, faux retraits et disponibilité | QA/QC plus rapide et drapeaux de confiance pour cartes temps réel. |
| 3 | **Fusion réseau de référence + microcapteurs + modèle** | CAPTOR + Europe trois villes | Krigeage/modèle hiérarchique avec incertitude par source ; cacher des nœuds et des zones ; comparer aux références seules | Cartographie plus dense avec incertitude explicite et repli lorsque les capteurs dérivent. |
| 4 | **Audit d’inventaire par satellite** | [TROPOMI NO₂](https://www.kaggle.com/datasets/muhammadbilal77511/pakistan-nitrogen-dioxide) + [DS4G](https://www.kaggle.com/competitions/ds4g-environmental-insights-explorer/overview) | Pipeline qualité/nuages, agrégation autour de sources, comparaison jours ouvrés/week-ends et vents ; appliquer ensuite aux produits originaux France | Repérer des incohérences spatiales d’émissions ou des panaches à investiguer, sans convertir directement la colonne en concentration au sol. |
| 5 | **Prévision pollens** | [Luxembourg 1992–2018](https://www.kaggle.com/datasets/yclaudel/pollen-luxembourg-1992-2018) | Baseline saisonnière, gradient boosting météo+lages, quantiles et probabilité de classe ; validation année future | Prototype de service d’anticipation des pics ; exige ensuite données phénologiques et capteurs régionaux Occitanie. |
| 6 | **Module événementiel feux/poussières** | Jeux NASA FIRMS/TROPOMI présents sur Kaggle ; le jeu Fireworks sert seulement de test logiciel | Construire des variables distance au front, vent projeté, AOD/NO₂ et régime ; évaluer sur épisodes nommés et jours témoins | Aide à l’expertise des épisodes naturels/exceptionnels ; les jeux Kaggle ne remplacent pas FIRMS, CAMS GFAS ni les observations locales. |
| 7 | **Contrôle indépendant des agrégats réglementaires** | [EPA Historical Air Quality](https://www.kaggle.com/datasets/epa/epa-historical-air-quality) | Tests de propriété sur MDA8, complétude, fuseaux, DST, maxima et agrégation par station avec un second corpus volumineux | Réduit le risque d’erreur silencieuse dans la chaîne de calcul, même si les règles finales restent européennes/LCSQA. |

## 3. Séquence recommandée

### Semaine courte — valeur immédiate

1. Télécharger CAPTOR et reproduire le notebook MLR/SVR/RF.
2. Remplacer son découpage par : calibration initiale → déploiement → retour en co-localisation.
3. Ajouter fusion des quatre capteurs, dérive hebdomadaire, erreur sur pics et drapeau d’incertitude.
4. En parallèle, porter dans les tests du projet la règle « aucun prétraitement ajusté avant le pli » révélée par l’audit du notebook Pékin.

### Itération suivante — système CAMS

1. Télécharger le jeu européen trois villes.
2. Écrire un adaptateur vers le schéma `station_id, valid_time, pollutant, y, meteo, land_use`.
3. Exécuter leave-one-city-out avec LightGBM ; aucune recherche d’hyperparamètres sur la ville test.
4. Tester ensuite seulement GRU/LSTM/GNN si le benchmark tabulaire est stable.

### Itération AASQA — fusion multisource

1. Reproduire l’ablation Téhéran trafic/météo/satellite.
2. Ne conserver que les transformations dont le mécanisme est transférable.
3. Refaire l’expérience avec les sources institutionnelles Occitanie/France et les heures de disponibilité réelles.

## 4. Critères d’arrêt

- **Architecture profonde :** arrêt si elle ne bat pas LightGBM sur test temporel × station exclue ou si son gain disparaît sans fuite de normalisation.
- **Satellite :** arrêt comme prédicteur quotidien direct si les trous nuageux, le délai ou l’heure de survol suppriment le gain hors échantillon ; conserver éventuellement comme variable climatologique/inventaire.
- **Microcapteur :** ne pas cartographier comme mesure quantitative si l’erreur sur les épisodes ou la dérive après déplacement dépasse le niveau défini avec le métrologue.
- **Transfert Kaggle → Occitanie :** aucun gain numérique n’est transféré. Seuls un mécanisme, du code auditable et un protocole peuvent l’être.

