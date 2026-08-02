# Hiérarchiser le trafic — le plus gros gain de variables du projet

## La question

Les variables routières initiales pondéraient les tronçons par leur **longueur seule** :
une rue de village comptait autant qu'une autoroute au mètre. C'est physiquement faux
pour le NO₂, dont l'émission suit le **trafic**, lequel varie de deux ordres de grandeur
entre une voie communale et une section autoroutière.

Question posée par Cyril : *la distance à un gros axe routier et à un centre-ville
pondéré par la population améliore-t-elle les prédictions ?*

## Comment les variables sont construites

**Quatre classes de route**, tirées de l'attribut `importance` de la BD TOPO — et non de
`nature`. Le choix s'est fait sur mesure : « Route à 1 chaussée » couvre **11 285 tronçons
sur 14 331** dans une emprise toulousaine, si bien qu'en faire un critère rangerait
presque tout le réseau dans une seule classe. `importance` se répartit au contraire
utilement : 1 → 146, 2-3 → 2 003, 4 → 1 081, 5-6 → 11 101.

`nature` ne sert plus qu'à deux choses qu'`importance` ne dit pas : reconnaître le gabarit
autoroutier, et **écarter les sentiers** — qui apportent du linéaire sans émission,
précisément là où les stations rurales devraient être basses.

**La masse est pondérée par le nombre de voies**, seul indicateur de capacité présent dans
la donnée.

**On n'invente aucun trafic.** Convertir chaque classe en véhicules par jour aurait
fabriqué une hypothèse invérifiable au cœur du modèle. On construit une variable par
classe et l'on laisse le modèle apprendre leur poids relatif — même logique que la
séparation des essences forestières.

**La population** entre par `Σ habitants × exp(−d/λ)` sur les communes d'ADMIN EXPRESS,
plus le pôle dominant et sa distance. Ce n'est pas une « distance au centre-ville » : une
distance placerait sur le même plan un village et une métropole à égale distance.

## Le résultat — NO₂, J+1, stations entièrement cachées

| Jeu de variables | n vars | RMSE | R² | Gain / CAMS |
|---|---|---|---|---|
| CAMS brut | — | 12,77 | +0,111 | — |
| Sans aucune route (**témoin bas**) | 47 | 10,37 | +0,414 | +18,8 % |
| Routes par longueur (référence) | 52 | 9,96 | +0,459 | +22,0 % |
| **Trafic hiérarchisé** | 67 | **8,80** | **+0,578** | **+31,1 %** |
| Trafic hiérarchisé + population | 72 | 8,82 | +0,576 | +31,0 % |

**Gain marginal de la hiérarchisation : +11,7 %**, IC 95 % **[+8,9 ; +14,1]**,
**100 % des tirages positifs** (bootstrap par station).

Le R² du NO₂ passe de 0,459 à **0,578** — c'était le polluant le plus faible du projet.

## Deux résultats à ne pas confondre

**La hiérarchisation apporte beaucoup.** Distinguer autoroute, principale, secondaire et
locale vaut +11,7 % par rapport à la même information agrégée en linéaire. Ce n'est pas
un effet de la multiplication des variables : le **témoin bas** montre que les routes en
général valent +3,2 points (18,8 → 22,0), et la hiérarchie en ajoute **9,1** de plus.

**La population n'apporte rien.** +31,0 % contre +31,1 %, soit un écart dans le bruit.
L'explication est immédiate : densité de population et densité de voies sont fortement
corrélées, et la seconde est déjà là — à une résolution bien plus fine que la commune.

Sans le témoin bas et sans la variante « trafic seul », on aurait attribué à la population
un gain qui vient entièrement des routes.

## Ce que cela dit du projet

C'est la **troisième fois** qu'affiner la description physique d'une source bat l'ajout
d'une source nouvelle : les essences forestières avaient doublé le R² de l'ozone, les
indices topographiques l'avaient doublé à nouveau, la hiérarchie routière fait passer le
NO₂ de 0,459 à 0,578.

À chaque fois, l'information était **déjà dans la donnée téléchargée** — il fallait
seulement cesser de l'agréger trop tôt.
