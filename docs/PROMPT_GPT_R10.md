# R10 — Quels signaux existent **là où notre correction échoue** ?

Tu fais une recherche de sources. **Ne propose pas de méthodes** — le projet en a déjà écarté
beaucoup, avec mesures à l'appui. Cherche des **signaux observables**, et pour chacun réponds
aux six questions du § 4. Une source dont la latence ou la licence ne convient pas est
inutilisable ici, si brillante soit-elle.

## 1. Le système, en cinq lignes

Post-traitement statistique des prévisions **CAMS Europe** (maille 0,1°, soit ~8 km en
longitude × 11 en latitude aux latitudes françaises ; J+1 à J+3). Un modèle à gradient boosté
apprend le **résidu** `observation − CAMS` à partir de variables disponibles à l'heure
d'émission (3 h du matin), sur ~476 stations françaises. Cible : la grandeur réglementaire
journalière — maximum glissant 8 h pour O₃, maximum horaire pour NO₂, moyenne pour les
particules.

Destination : candidature à une association agréée de surveillance de la qualité de l'air
(AASQA) en Occitanie. Le cadrage est celui de l'**évaluateur**, pas du constructeur.

## 2. Où le système échoue — mesuré, pas supposé

**Ce sont ces quatre situations, et elles seules, qui définissent la recherche.**

### ① La généralisation temporelle s'effondre sur trois polluants sur quatre

Protocole « double aveugle » : station **et** mois cachés simultanément, ce qui correspond au
déploiement réel (prédire demain, à un endroit non instrumenté).

| polluant | validation spatiale | **double aveugle** | écart-type | pire pli |
|---|---|---|---|---|
| **NO₂** | +31,6 % | **+25,7 %** | 5,0 | +15,5 % |
| PM10 | +31,3 % | **+7,5 %** | 14,8 | −30,0 % |
| PM2,5 | +25,6 % | **+5,1 %** | 12,2 | −18,0 % |
| O₃ | +24,1 % | **+3,3 %** | 13,3 | −35,0 % |

Sur l'ozone, **7 à 8 plis sur 17 sont négatifs** : la correction y est *pire* que le modèle
brut. Le pire mois, novembre 2023, tombe à **−41 %**.

Le NO₂ est l'exception, et le mécanisme est compris : son résidu est **sous-maille et attaché
au site** — quatre colonnes de typologie de station (urbain/périurbain/rural × fond/trafic/
industriel) en expliquent +16,5 % — donc il se transporte d'un mois à l'autre. Le résidu de
l'ozone est **photochimique et saisonnier**.

### ② Une rupture du modèle amont, non annoncée dans les métadonnées

L'erreur propre de CAMS contre les observations montre une discontinuité vers **octobre 2024** :

| période | biais | R² |
|---|---|---|
| 2023-08 → 2024-09 | +3,2 à +8,2 | 0,40 – 0,63 |
| **2024-10 → 2024-12** | **+9,5 à +12,4** | **0,19 – 0,31** |

Aucun numéro de version dans les métadonnées : mêmes attributs, même grille, même producteur.
Et — contre-intuitif — ce sont les **meilleurs** mois pour notre correction (+11 à +15 %),
parce qu'il y a davantage à corriger. La corrélation entre biais mensuel de CAMS et notre gain
vaut **r = +0,41** : réelle, mais elle n'explique pas les cas extrêmes.

### ③ Aux extrêmes, la correction est massivement insuffisante — quand elle n'est pas nuisible

Sur les journées les plus chargées en NO₂, décomposition de Shapley à l'appui :

```
2024-01-25  Montpellier Liberté (trafic)  observé 191,3  CAMS 36,5  →  prévu 68,8
2023-12-18  Montpellier Liberté (trafic)  observé 195,6  CAMS 35,4  →  prévu 76,4
```

Sous-correction d'un **facteur trois**, et **reproductible** sur la même station.

Au seuil de procédure préfectorale français (**180 µg/m³** en maximum horaire d'ozone) :
**32 dépassements sur 60 400 jours-station**, CAMS en détecte 3, notre correction 2, et aucun
des deux à J+3. La pente de calibration vaut 1,007 — ce n'est donc **pas** un défaut de
calibration mais un **manque d'information** : rien dans les 53 prédicteurs ne distingue une
journée à 175 µg/m³ d'une journée à 185.

### ④ En double aveugle, nous passons **derrière** le produit officiel en détection

À précision égale au post-traitement officiel de Copernicus, sur la période et les stations
qu'il n'a pas vues :

| | rappel | précision | détectés | manqués |
|---|---|---|---|---|
| MOS officiel Copernicus | 0,232 | 0,610 | 144 | 477 |
| nous, score brut | 0,174 | 0,610 | 108 | 513 |
| nous, probabilité calibrée | 0,198 | 0,612 | 123 | 498 |

En validation **spatiale**, le même front nous donnait **4,1× plus** de dépassements détectés.
Le résultat s'inverse quand on ajoute l'axe temporel.

## 3. Ce qui a déjà été testé et **écarté**, avec sa mesure

Ne les repropose pas sans élément nouveau et sourcé.

| source ou piste | résultat mesuré |
|---|---|
| **TROPOMI / Sentinel-5P** (colonne NO₂, indice d'aérosols, couronnes 10-100 km, climatologie) | **nul sur 12 cases** — 2 protocoles × 3 polluants. Négatif significatif sur PM2,5 bloqué |
| Météo **ERA5** (réanalyse) | +7,9 % O₃ — mais c'est un **plafond**, elle n'existe pas à l'heure d'émission |
| Météo **IFS prévue** | récupère ~64 % du plafond ; vent, pluie et couche limite portent tout ; le point de rosée est redondant |
| Membres d'ensemble CAMS, dispersion | nulle en prédiction ; ×6,6 entre décile concordant et divergent, donc utile en **méfiance** seulement |
| Feux **GFAS** | +3,0 % sur PM2,5, mécanisme confirmé, anisotropie marginale |
| Copolluants, chimie inter-espèces | nuls — CAMS les modélise déjà |
| Sol, géologie | gains 11× sous le critère d'arrêt ; le témoin ozone réfute le mécanisme |
| Trafic, population | **R² négatif** |
| Tête de classification, perte pondérée, quantile 0,90, calibration isotone ordinale | **rien** à budget de fausses alertes égal — seul le **rang** du régresseur décide |
| Détecteurs d'anomalie sur les entrées (forêt d'isolement, ECOD) | aucun coupe-circuit exploitable ; les états inhabituels sont ceux où la correction sert **le plus** |

## 4. Ce que je te demande

**Pour chaque signal que tu proposes, réponds aux six questions.** Une réponse sans ces six
points n'est pas exploitable.

1. **Que mesure-t-il physiquement**, et par quel mécanisme serait-il informatif dans **l'une
   des quatre situations d'échec** du § 2 — pas « en général » ?
2. **Latence de mise à disposition**, mesurée ou documentée. La prévision est émise à **3 h du
   matin** ; tout ce qui arrive après est inutilisable. *(TROPOMI a été écarté en partie
   là-dessus : latence médiane du flux OFFL mesurée à 40,4 h, maximum 61,4 h.)*
3. **Résolution spatiale et temporelle**, et couverture de la France métropolitaine —
   Occitanie en particulier.
4. **Mode d'accès** : API, seau objet, téléchargement complet ? **Authentification requise ?**
   Existe-t-il un **accès partiel** — plage d'octets, COG, Zarr, Parquet partitionné ? Le
   projet refuse par principe de télécharger une archive entière quand une fenêtre suffit.
5. **Licence**, et compatibilité avec un usage par une AASQA.
6. **Profondeur d'archive** — au minimum 2023-08 → 2026-08, sans quoi on ne peut ni
   entraîner ni évaluer.

### Les cinq directions qui m'intéressent le plus

**A. Détecter une rupture du modèle amont.** Existe-t-il un flux, un journal de versions, un
fil d'annonces ou un produit de contrôle qualité par lequel Copernicus signale un changement
de configuration de CAMS Europe ? Le projet a dû le détecter **empiriquement**, ce qui est
absurde.

**B. Signaux d'anomalie synoptique disponibles à l'émission.** Indices de circulation,
typologies de temps (Hess-Brezowsky, Lamb, Weather Regimes du CEPMMT), blocages, indices
d'inversion, hauteur de couche limite prévue, stabilité. Lesquels sont **prévus** et non
diagnostiqués a posteriori ?

**C. Anomalies d'émission que l'inventaire ignore.** Épandage agricole (nitrate d'ammonium au
printemps), chauffage au bois, brûlage de déchets verts, feux d'artifice, chantiers, grèves de
transport, vacances scolaires et jours fériés. Y a-t-il des **calendriers ou des proxys
français publiés** — et non à reconstruire à la main ?

**D. Poussières sahariennes.** Elles dominent les pics de PM10 en Occitanie, et **40 des 52
vigilances** réellement déclarées y portent. Quels produits de prévision d'intrusion existent
— Barcelona Dust Regional Center, CAMS dust AOD, SDS-WAS — avec quelle latence et quelle
compétence évaluée sur le sud de la France ?

**E. Signaux de l'AASQA elle-même.** Réseaux de microcapteurs, mesures mobiles, signalements
citoyens, données de trafic en temps réel, capteurs de chantier. Que publient réellement les
AASQA françaises, en particulier Atmo Occitanie, et sous quelle latence ?

## 5. Ce que je te demande explicitement de me dire aussi

- **Ce qui n'existe pas.** Si une catégorie de signal est réputée utile dans la littérature
  mais indisponible en France en temps réel, dis-le — c'est une information de même valeur.
- **Ce qui a échoué chez d'autres.** Les publications qui ont testé une source sur la
  correction de modèles de chimie-transport et n'ont rien trouvé m'intéressent autant que
  celles qui ont trouvé.
- **Distingue** ce que tu sais publié et sourcé, de ce que tu supposes. Marque le second comme
  **à vérifier**.

## 6. La question de fond

Les quatre situations du § 2 ont-elles un **signal observable commun** — quelque chose qui
change *avant* ou *pendant* les moments où une correction statistique d'un modèle de
chimie-transport cesse de fonctionner ?

Ou bien faut-il accepter que ces moments soient, par nature, ceux où **l'information n'existe
pas** — auquel cas la bonne réponse opérationnelle n'est pas un prédicteur de plus, mais un
**indicateur de renoncement** : savoir dire « aujourd'hui, ma correction n'est pas fiable,
revenez au modèle brut » ?

Cette seconde hypothèse serait, pour une AASQA, un résultat aussi utile que la première. Je
n'ai pas de préférence entre les deux, seulement besoin de savoir laquelle est vraie.
