# Ce que la correction change sur la **classe d'indice**

Un gain en µg/m³ n'est pas un gain pour le métier. Ce qu'une AASQA publie est une classe
de 1 à 6 : une amélioration de concentration qui ne fait franchir aucune borne ne change
rien à l'affichage, tandis qu'une petite erreur près d'une borne fait basculer la
couleur. La seule mesure qui parle est donc **l'accord de classe**.

Comparaison à règles et polluants **identiques** (O3, NO2, PM25), sur
60,522 couples (station, jour) où les trois indices sont calculables.

| | Accord exact | À une classe près | Biais de classe |
|---|---|---|---|
| **CAMS brut** | 83.9 % | 98.2 % | -0.011 |
| **MOS corrigé** | 84.6 % | 99.2 % | -0.067 |

**Gain : +0.8 points d'accord exact.**

## Détection des épisodes — le critère qui décide

Un taux d'accord traite les erreurs symétriquement. Le métier ne l'est pas : ne pas
annoncer un épisode qui survient expose la population et engage la responsabilité de
l'AASQA, alors qu'une fausse alerte coûte de la crédibilité. L'arrêté du 07/04/2016
consacre d'ailleurs cette asymétrie en autorisant le déclenchement **sur prévision**.

Le F₂ pondère le rappel quatre fois plus que la précision.

| Seuil | Modèle | n | Rappel | Précision | F₂ | Épisodes manqués |
|---|---|---|---|---|---|---|
| ≥2 | arbitre | 58,061 | **0.995** | 0.964 | 0.989 | 299 |
| ≥2 | cams | 58,061 | **0.992** | 0.965 | 0.986 | 462 |
| ≥2 | mos | 58,061 | **0.971** | 0.973 | 0.971 | 1,697 |
| ≥3 | arbitre | 8,959 | **0.557** | 0.815 | 0.595 | 3,967 |
| ≥3 | cams | 8,959 | **0.558** | 0.676 | 0.578 | 3,961 |
| ≥3 | mos | 8,959 | **0.557** | 0.817 | 0.595 | 3,967 |
| ≥4 | arbitre | 1,801 | **0.328** | 0.755 | 0.370 | 1,210 |
| ≥4 | cams | 1,801 | **0.259** | 0.431 | 0.282 | 1,334 |
| ≥4 | mos | 1,801 | **0.328** | 0.757 | 0.370 | 1,210 |
| ≥5 | arbitre | 36 | **0.000** | nan | nan | 36 |
| ≥5 | cams | 36 | **0.000** | 0.000 | nan | 36 |
| ≥5 | mos | 36 | **0.000** | nan | nan | 36 |

## Polluant qui impose l'indice, sur les concentrations observées

- **O3** : 77.1 %
- **NO2** : 15.8 %
- **PM25** : 7.0 %

## ⚠️ Ce que cette mesure n'est pas

- **Ce n'est pas l'indice officiel publié.** Celui-ci est modélisé et spatialisé par
  commune puis agrégé à l'EPCI, et porte **cinq** polluants (PM10 et SO2 en plus). Il est
  ici reconstitué **en station**, sur trois polluants. L'écart à l'officiel est un autre
  problème, chiffré dans `reports/INDICE_ATMO.md` : 42,8 % d'accord et −0,72 classe de
  biais, dus à la spatialisation.
- **Ce n'est pas le système d'ATMO.** CAMS Europe (0,1°, ~8 × 11 km) n'est pas PREV'AIR
  (CHIMERE + MOCAGE, ~2 km), qui est la chaîne réellement employée. On mesure une chaîne
  opérationnelle de même nature, pas la leur.
- La référence est l'indice **calculé depuis les mesures**, pas l'indice publié. C'est ce
  qui isole l'apport de la correction du problème de spatialisation.
