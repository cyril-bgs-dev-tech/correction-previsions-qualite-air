# Relief : ce qu'il apporte, et à quel polluant

Indices topographiques calculés pour les **476 stations métropolitaines** depuis le
Copernicus DEM GLO-30, en 7 minutes et **sans stocker un octet** — le format COG permet
de lire la seule fenêtre utile autour de chaque station.

Code : `src/aq/features/relief.py`, `scripts/build_relief_features.py`.

## Le résultat

LUR sur moyennes annuelles pluriannuelles, stations de fond, validation par **station
exclue** (chaque station est prédite par un modèle qui ne l'a jamais vue).

| Polluant | n | Géo seul | Géo + relief | RMSE | Verdict |
|---|---|---|---|---|---|
| **O₃** | 274 | +0,228 | **+0,452** | 7,70 → **6,48** | le relief **double** le R² |
| NO₂ | 246 | +0,409 | +0,415 | 5,10 → 5,07 | négligeable |
| PM2.5 | 176 | +0,039 | **−0,001** | 4,95 → 5,06 | le relief **dégrade** |

## Pourquoi ce contraste est exactement celui qu'on attend

**L'ozone est un polluant secondaire et régional.** Sa concentration en un point dépend
de l'histoire de la masse d'air qui y arrive et de la façon dont elle stagne ou se
renouvelle. Or c'est précisément ce que décrit la topographie : la nuit, sous inversion,
un fond de vallée voit son ozone détruit par titration au NO et par dépôt sec, tandis
qu'une crête reste dans la couche résiduelle et conserve des concentrations élevées.
Deux stations à la même altitude, l'une en fond de vallée, l'autre sur un versant, ne
mesurent pas le même ozone — et seule la position *relative* les distingue.

**Le NO₂ est un polluant primaire et local.** Sa concentration est gouvernée par la
proximité des sources, que les variables routières décrivent déjà. La topographie n'a
presque rien à ajouter : +0,006 de R².

**Les PM2.5 n'ont aucun signal structurel.** Ajouter neuf variables à un modèle qui
n'expliquait déjà que 3,9 % de la variance ne fait que du surajustement : le R² validé
passe sous zéro. C'est la troisième méthode indépendante à conclure la même chose — la
variance des PM2.5 est **météorologique**, pas géographique (climatologie : R² 0,139 ;
LUR géo : +0,039 ; LUR géo + relief : −0,001).

## Le cas qui motivait tout le chantier

Chamonix, fond de vallée à 1035 m, était **sur-prédit de 33 µg/m³** par le modèle sans
relief : l'altitude brute le rangeait avec les crêtes alpines. Les indices le séparent
enfin — station des Bossons, TPI à 10 km de **−1094 m**, profondeur de vallée 1816 m,
contre **+224** pour Le Casset en haute montagne.

Validation indépendante du MNT : l'altitude qu'il donne corrèle à **0,969** avec
l'altitude déclarée au référentiel, écart médian **3 m**. Les fonds de vallée les plus
marqués détectés sont Maurienne, Bossons, La Léchère, Saint-Jean — tous alpins, tous
corrects.

## ⚠️ Ce qu'il ne faut pas conclure

Les variables `tpi_10000m` et `profondeur_vallee_m` sont corrélées à **−0,90** : elles
mesurent presque la même chose avec des conventions de signe opposées. Le modèle les
retient toutes deux avec des coefficients positifs, ce qui **paraît contradictoire** —
l'une dit « crête », l'autre dit « fond de vallée ».

Ce n'est pas un effet physique, c'est de la colinéarité : le modèle exploite leur faible
différence résiduelle. Conséquence pratique :

- **Le gain prédictif est réel** — il est mesuré hors échantillon, station par station.
- **Les coefficients individuels ne sont pas interprétables.** Ne pas présenter « le
  coefficient du TPI vaut +0,066 donc une crête ajoute tant d'ozone » : cet énoncé ne
  résisterait pas à un changement de jeu de variables.

Pour la présentation, énoncer le gain global et le mécanisme physique, pas les
coefficients. Si une lecture par variable devient nécessaire, il faudra d'abord
décorréler — une seule variable de position par échelle, ou une analyse en composantes.
