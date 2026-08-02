# Ce que chaque famille de variables apporte — et ce qu'elle coûte

Ozone, J+1, 577 589 paires, 270 stations. Chaque famille est **retirée** une à une, et
l'on mesure ce qu'on perd. Retirer plutôt qu'ajouter : les variables sont corrélées entre
elles, si bien qu'ajoutées seules deux familles redondantes paraissent toutes deux
décisives, alors que retirées seules aucune ne manque. C'est la seconde lecture qui dit ce
qu'on peut abandonner.

| Jeu de variables | RMSE | R² | Perte |
|---|---|---|---|
| CAMS brut | 17,58 | +0,529 | — |
| **Toutes** | **12,58** | **+0,759** | — |
| sans calendrier | 14,50 | +0,680 | **+15,2 %** |
| sans relief | 13,08 | +0,739 | +4,0 % |
| sans coordonnées | 12,84 | +0,749 | +2,1 % |
| sans routes | 12,64 | +0,756 | +0,5 % |
| sans échéance | 12,59 | +0,759 | +0,0 % |
| **sans forêt** | **12,34** | **+0,768** | **−1,9 %** |

## Le résultat qui dérange : la forêt **dégrade** la correction

Retirer les variables forestières — chênes, conifères, feuillus, toutes échelles
confondues — **améliore** le modèle de 1,9 %. Or ce sont les variables signature du
projet, celles qui doublaient le R² de la régression sur paysage.

**Il n'y a pas de contradiction, et l'explication est physique.** Les deux modèles ne
prédisent pas la même chose :

- La **régression sur paysage** prédit une *moyenne annuelle* à partir du territoire. Les
  chênes y comptent : leurs émissions d'isoprène, précurseur d'ozone, s'intègrent sur
  l'année et façonnent le niveau de fond local.
- La **correction MOS** prédit le *résidu horaire de CAMS*. Or CAMS **modélise déjà les
  émissions biogéniques** — c'est un modèle de chimie-transport, la végétation est dans
  son inventaire. Re-fournir l'information forestière à la correction n'ajoute donc
  aucune connaissance nouvelle : seulement 24 variables corrélées entre elles, sur
  lesquelles le modèle surajuste.

**Ce que cela enseigne :** une variable utile à un modèle ne l'est pas à un autre. Ce qui
compte n'est pas ce que la variable décrit, mais **ce que le modèle qu'on corrige ignore
déjà**. Une correction n'a d'intérêt que là où le modèle physique est aveugle.

Et cela redonne du sens à la hiérarchie observée : le **relief** (+4,0 %) reste utile
parce que la maille de 8 km de CAMS ne résout pas une vallée ; les **coordonnées**
(+2,1 %) captent un reste de structure régionale ; les **routes** ne servent presque pas
sur l'ozone — cohérent, l'ozone n'est pas un polluant de proximité.

## L'avertissement : le calendrier pèse trop lourd

Le calendrier vaut **15,2 %** à lui seul, loin devant tout le reste. Avec **trois mois**
d'échantillon, `jour_annee` identifie presque le mois : le modèle apprend en partie
« quelle saison » plutôt qu'une correction transférable.

Ce n'est pas rédhibitoire — la validation temporelle (mois jamais vu) donne toujours
+18,5 % — mais c'est la raison pour laquelle il faut citer cette validation-là plutôt que
la spatiale seule, et la raison pour laquelle **étendre à une année complète est la
priorité de données du projet**.

## La question de l'employeur : le modèle national tient-il en Occitanie ?

Modèle entraîné **en excluant toute l'Occitanie**, puis évalué sur ses 29 stations. C'est
plus dur qu'une validation par stations tirées au hasard : les stations occitanes
partagent un climat méditerranéen, un relief et des essences que le modèle n'aura vus
nulle part ailleurs de façon aussi concentrée.

| | RMSE | R² |
|---|---|---|
| CAMS brut | 17,98 | +0,567 |
| **MOS entraîné hors Occitanie** | **14,61** | **+0,715** |

**Gain de +18,8 %** sur une région entièrement inconnue du modèle. C'est moins que les
+28,3 % nationaux — attendu, et c'est le chiffre honnête à citer devant ATMO Occitanie :
*un modèle qui n'a jamais vu votre région y retire tout de même un cinquième de l'erreur.*
