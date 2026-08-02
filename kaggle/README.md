# Veille Kaggle — qualité de l’air et modélisation AASQA

Inventaire réalisé le **1er août 2026**. Le périmètre couvre les deux usages demandés :

1. améliorer la correction des prévisions CAMS aux stations ;
2. identifier des briques utiles plus largement à une AASQA : cartographie, microcapteurs, contrôle qualité, émissions, satellites, feux et pollens.

## Résultat en une page

Kaggle ne fournit pas de benchmark public crédible permettant de dire qu’une architecture bat PREV’AIR, CHIMERE ou la chaîne d’une AASQA. Les tâches proches sont presque toutes des jeux communautaires, des réimportations d’autres plateformes ou des notebooks sans validation spatiale et opérationnelle suffisante.

En revanche, cinq ressources valent un travail concret :

| rang | ressource | bénéfice immédiat | usage principal |
|---:|---|---|---|
| 1 | [H2020 CAPTOR](https://www.kaggle.com/datasets/chaozhuang/h2020-project-captor-dataset) | Tester calibration, dérive, fusion de capteurs et transfert après déplacement du capteur | AASQA — microcapteurs et densification |
| 2 | [Air Quality Monitoring in European Cities](https://www.kaggle.com/datasets/yekenot/air-quality-monitoring-in-european-cities) | Banc d’essai multi-ville avec polluants, météo et occupation du sol | CAMS — validation spatiale ; AASQA — downscaling |
| 3 | [Tehran Air Quality FULL](https://www.kaggle.com/datasets/sawdi777/tehran-air-quality-full-sat-traffic-metrology) | Ablation commune stations + trafic + météo + satellite | CAMS — familles de variables ; AASQA — fusion multisource |
| 4 | [Beijing Multi-Site Air-Quality](https://www.kaggle.com/datasets/sid321axn/beijing-multisite-airquality-data-set) | Tester lags d’observation, modèles spatio-temporels et stations exclues sur quatre ans | CAMS — séquences et transfert |
| 5 | [Pollen Luxembourg 1992–2018](https://www.kaggle.com/datasets/yclaudel/pollen-luxembourg-1992-2018) | Prototyper une prévision pollen–météo et l’évaluation des pics | AASQA — service pollens |

## Ce qui est réellement réutilisable

- Le jeu CAPTOR est accompagné d’un [notebook comparant MLR, Lasso, SVR et forêt aléatoire avec fusion de capteurs](https://www.kaggle.com/code/chaozhuang/sensor-fusion-calibration-w-mlr-lasso-svr-rf). Il fournit une implémentation à reprendre, mais ses scores doivent être recalculés avec des blocs chronologiques et un test après déploiement.
- Les données européennes multi-villes permettent une expérience plus hostile que beaucoup de notebooks Kaggle : entraîner sur deux villes et tester sur la troisième, puis exclure successivement chaque station.
- Le jeu de Téhéran permet de mesurer séparément l’apport du trafic, de la météo et du satellite, au lieu d’interpréter une importance de variables comme un gain causal.
- Le jeu de Pékin permet de comparer LightGBM à RNN, GRU, LSTM et attention à lignes et information identiques. Il est particulièrement utile pour mesurer ce que valent les observations récentes quand leur disponibilité est simulée à l’heure d’émission.
- CAPTOR et le [Gas Sensor Array Drift Dataset](https://www.kaggle.com/datasets/orvile/gas-sensor-array-drift-dataset/data) permettent de construire des tests de dérive et de recalibration, un besoin distinct de la prévision CAMS.

## Avertissement principal

Le notebook Kaggle [RNN/GRU/LSTM/Bi-LSTM-attention sur Pékin](https://www.kaggle.com/code/linlinqi321/model-of-bi-lstm-multiheadatt-rnn-gru-lstm) ajuste son `MinMaxScaler` sur l’ensemble des valeurs avant la séparation 70 % entraînement / validation / test. Le prétraitement voit donc la distribution future. Il compare des architectures, mais ses scores ne sont pas une preuve transférable à notre pipeline ; il constitue surtout un excellent contre-exemple à ajouter à l’audit de fuite.

## Organisation du dossier

- [CATALOGUE.md](./CATALOGUE.md) : ressources retenues, usage, provenance, limites et décision.
- [PLAN_EXPERIENCES.md](./PLAN_EXPERIENCES.md) : expériences exécutables, classées par valeur pour CAMS et pour une AASQA.

## Décision de téléchargement

Aucun jeu n’a été téléchargé automatiquement. Plusieurs archives sont volumineuses, certaines dupliquent une source institutionnelle plus propre et aucune authentification Kaggle n’est configurée dans l’environnement. La bonne étape suivante est de télécharger seulement CAPTOR, Europe trois villes et Pékin, après avoir gelé pour chacun le test et la métrique.

