# Performance des prévisions CAMS — la barre à battre

Périmètre **metropole** · source `cams-europe-air-quality-forecasts` (ensemble de 9 à 11 modèles, maille 0,1°).

Ce sont des **prévisions**, pas la réanalyse : la réanalyse assimile les observations EEA, donc la cible même qu'on cherche à prédire, et la comparer à ces observations lui prêterait un avantage qu'elle n'a pas en exploitation.

> ⚠️ Les paramètres d'incertitude FAIRMODE utilisés pour le MQI sont repris de mémoire et **doivent être vérifiés contre le Guidance Document en vigueur** avant toute publication. Le seuil de conformité MQI ≤ 1 en dépend directement.

| Polluant | Horizon | Typologie | n | RMSE | Biais | R² | MQI |
|---|---|---|---|---|---|---|---|
| NO2 | J+1 | toutes | 3,986,229 | 12.87 | -5.83 | +0.125 | 0.61 |
| NO2 | J+1 | background | 2,689,434 | 8.88 | -3.13 | +0.321 | 0.43 |
| NO2 | J+1 | industrial | 295,199 | 6.58 | -1.33 | +0.326 | 0.33 |
| NO2 | J+1 | traffic | 1,001,596 | 20.85 | -14.39 | -0.468 | 0.89 |
| NO2 | J+2 | toutes | 3,978,608 | 12.95 | -5.87 | +0.114 | 0.61 |
| NO2 | J+2 | background | 2,684,274 | 8.97 | -3.17 | +0.308 | 0.44 |
| NO2 | J+2 | industrial | 294,617 | 6.68 | -1.37 | +0.307 | 0.34 |
| NO2 | J+2 | traffic | 999,717 | 20.94 | -14.44 | -0.480 | 0.89 |
| NO2 | J+3 | toutes | 3,970,924 | 13.09 | -5.92 | +0.096 | 0.62 |
| NO2 | J+3 | background | 2,679,073 | 9.12 | -3.22 | +0.284 | 0.45 |
| NO2 | J+3 | industrial | 294,033 | 6.81 | -1.43 | +0.280 | 0.34 |
| NO2 | J+3 | traffic | 997,818 | 21.08 | -14.50 | -0.499 | 0.90 |
| O3 | J+1 | toutes | 3,225,341 | 16.97 | +6.01 | +0.584 | 0.46 |
| O3 | J+1 | background | 3,143,566 | 16.92 | +5.95 | +0.584 | 0.46 |
| O3 | J+1 | industrial | 81,775 | 18.75 | +8.33 | +0.571 | 0.51 |
| O3 | J+2 | toutes | 3,219,292 | 17.33 | +6.23 | +0.567 | 0.47 |
| O3 | J+2 | background | 3,137,636 | 17.28 | +6.17 | +0.567 | 0.47 |
| O3 | J+2 | industrial | 81,656 | 19.12 | +8.50 | +0.554 | 0.52 |
| O3 | J+3 | toutes | 3,213,212 | 17.84 | +6.51 | +0.541 | 0.49 |
| O3 | J+3 | background | 3,131,675 | 17.79 | +6.45 | +0.541 | 0.49 |
| O3 | J+3 | industrial | 81,537 | 19.59 | +8.78 | +0.532 | 0.53 |
| PM25 | J+1 | toutes | 2,644,281 | 5.86 | +0.05 | +0.299 | 0.65 |
| PM25 | J+1 | background | 1,954,651 | 5.79 | +0.23 | +0.309 | 0.65 |
| PM25 | J+1 | industrial | 155,739 | 5.98 | -0.25 | +0.251 | 0.67 |
| PM25 | J+1 | traffic | 533,891 | 6.09 | -0.50 | +0.263 | 0.65 |
| PM25 | J+2 | toutes | 2,639,434 | 5.96 | +0.04 | +0.276 | 0.66 |
| PM25 | J+2 | background | 1,951,066 | 5.88 | +0.21 | +0.287 | 0.66 |
| PM25 | J+2 | industrial | 155,452 | 6.05 | -0.28 | +0.234 | 0.67 |
| PM25 | J+2 | traffic | 532,916 | 6.21 | -0.50 | +0.236 | 0.66 |
| PM25 | J+3 | toutes | 2,634,616 | 6.10 | -0.00 | +0.243 | 0.68 |
| PM25 | J+3 | background | 1,947,508 | 6.02 | +0.17 | +0.254 | 0.68 |
| PM25 | J+3 | industrial | 155,167 | 6.16 | -0.34 | +0.206 | 0.69 |
| PM25 | J+3 | traffic | 531,941 | 6.37 | -0.53 | +0.197 | 0.68 |
