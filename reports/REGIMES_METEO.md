# Quand la correction échoue-t-elle ?

Un RMSE global ne dit pas *quand* faire confiance à un modèle. Un modèle qui se trompe de
façon diffuse et un modèle qui se trompe systématiquement dans un régime identifiable ont
la même erreur moyenne et n'ont pas la même valeur opérationnelle : le second est
prévisible, donc utilisable avec un avertissement.

Ozone J+1, 577 589 paires, appariement complet avec la météo ERA5.

> **Un usage de la réanalyse qui est légitime, et il faut dire pourquoi.** ERA5 comme
> *entrée* d'un modèle de prévision serait une fuite — elle décrit un passé que la
> prévision n'avait pas. Ici elle sert au **diagnostic a posteriori** : on ne prédit
> rien, on caractérise les conditions dans lesquelles la correction s'est trouvée bonne
> ou mauvaise. La distinction tient à l'usage, pas à la donnée.

## Vu de loin : la correction aide partout, et surtout là où CAMS est mauvais

| Régime | n | O₃ observé | RMSE CAMS | RMSE MOS | Gain |
|---|---|---|---|---|---|
| **Stagnation** (couche < 300 m, vent < 2 m/s) | 158 246 | 32,5 | 23,21 | **15,19** | **+34,6 %** |
| Ventilé | 247 502 | 44,4 | 15,34 | 11,70 | +23,7 % |
| Photochimique (rayonnement > 150 W/m²) | 115 063 | 65,9 | 14,32 | 11,02 | +23,1 % |
| Précipitations | 49 214 | 56,2 | 13,83 | 11,20 | +19,0 % |
| Intermédiaire | 7 564 | 43,7 | 16,24 | 12,85 | +20,9 % |

Le gain est **maximal sous stagnation** — précisément le régime où CAMS est le plus
mauvais (RMSE 23,21 contre 13-15 ailleurs). C'est cohérent : sous couche limite basse, la
concentration dépend fortement du volume de dilution local, que la maille de 8 km ne
résout pas, et que les variables de relief décrivent.

## Vu de près : le verdict s'inverse aux fortes concentrations

Décile supérieur des observations, croisé avec le régime :

| Régime | n | Gain |
|---|---|---|
| **Photochimique** | 31 960 | **+7,2 %** |
| Intermédiaire | 375 | +2,0 % |
| Précipitations | 5 316 | −1,0 % |
| **Ventilé** | 11 084 | **−17,0 %** |
| **Stagnation** | 9 221 | **−17,6 %** |

**Aux fortes valeurs, la correction ne conserve un gain que sous régime photochimique.**
Partout ailleurs elle dégrade, jusqu'à −17,6 %.

## Ce qu'il faut en conclure, et c'est une bonne nouvelle en demi-teinte

**Le seul régime où le gain tient aux fortes valeurs est le bon.** Un pic d'ozone estival
est, par construction, photochimique : fort rayonnement, température élevée. C'est le
régime des épisodes qui déclenchent une procédure d'information, et c'est celui où la
correction reste utile (+7,2 %).

**Mais les fortes valeurs hors photochimie sont dégradées**, et il faut le dire.
L'amortissement documenté ailleurs — le modèle tire vers le régime moyen — se manifeste
ici de façon localisée : là où la physique de CAMS produit une valeur haute pour une
raison que les covariables statiques ne décrivent pas, la correction la ramène vers le bas
à tort.

**La règle d'usage qui en découle :** un modèle corrigé devrait être accompagné d'un
indicateur de régime, et la correction **atténuée ou désactivée** aux fortes valeurs hors
photochimie. C'est une recommandation opérationnelle directement issue de la mesure — et
plus utile qu'un gain moyen.

## Ce que cela ne dit pas

Trois mois seulement, dont un seul été. Le régime photochimique est donc largement porté
par juillet 2024, et le croisement régime × décile repose sur des effectifs modestes
(375 à 32 000). Une année complète permettrait de vérifier que la règle tient — c'est
l'un des motifs de l'extension en cours.

---

## Correction : la dégradation aux fortes valeurs est propre à l'ozone

Le même diagnostic, étendu au NO₂ et aux PM2.5, contredit la généralisation qu'on aurait
pu tirer de l'ozone seul. Décile supérieur des observations :

| Régime | O₃ | NO₂ | PM2.5 |
|---|---|---|---|
| Stagnation | **−17,6 %** | **+31,4 %** | **+21,8 %** |
| Ventilé | **−17,0 %** | **+33,3 %** | **+22,6 %** |
| Photochimique | +7,2 % | +26,5 % | +10,1 % |
| Précipitations | −1,0 % | +30,1 % | +22,5 % |

Sur NO₂ et PM2.5, la correction est **meilleure aux fortes valeurs qu'en moyenne**
(+26 à +33 % contre +19 à +27 %). Seul l'ozone se dégrade.

**L'explication est physique.** Un pic de NO₂ ou de particules est un épisode
d'**accumulation** — couche limite basse, vent faible, émissions piégées. CAMS le rate
franchement parce que sa maille ne résout ni le volume de dilution local ni les sources de
proximité : il reste donc beaucoup à corriger, et les covariables de terrain décrivent
exactement ce qui manque.

Un pic d'ozone est **photochimique**. CAMS modélise correctement la production d'ozone,
qui dépend du rayonnement et de la température — des champs que sa maille résout bien. Il
reste peu à corriger, et la correction, en tirant vers le régime moyen, fait plus de mal
que de bien.

**Règle d'usage révisée.** L'atténuation aux fortes valeurs ne concerne que l'ozone hors
régime photochimique. Sur NO₂ et PM2.5, la correction doit au contraire être **maintenue,
voire privilégiée** dans les épisodes — c'est là qu'elle apporte le plus.

C'est aussi une leçon de méthode : **une règle tirée d'un seul polluant ne se généralise
pas**. La physique des trois diffère, et l'évaluation doit le refléter.
