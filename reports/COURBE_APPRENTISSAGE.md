# Combien d'historique faut-il ? — et la correction survit-elle à l'année suivante ?

## La question, et pourquoi elle se pose maintenant

Le premier résultat du projet était un échec : entraînée sur trois mois d'hiver et
testée sur l'été, la correction faisait **−19 %** — pire que CAMS brut. L'explication
allait de soi mais restait une hypothèse : le modèle n'avait jamais vu le régime qu'on
lui demandait de prédire.

L'archive CAMS glissante de trois ans permet de la trancher. Deux expériences, qui
répondent à deux questions distinctes.

## Ce qui a rendu l'expérience possible — un défaut corrigé d'abord

La première exécution n'a produit que **trois points de courbe**. La cause n'était pas
le calcul mais les données : le chargement déduisait la fenêtre d'observations du **nom**
des fichiers de prévision, avec une expression ancrée à droite. Sur les six fichiers
groupés `..._202308_202309.parquet`, elle ne capturait que le second mois, et le premier
disparaissait au recollement.

**11 mois retenus sur 17. 2,09 M de paires au lieu de 3,23 M — 35 % du jeu perdu, sans
la moindre erreur levée.** Le même motif se trouvait dans `benchmark_cams.py`. Les deux
lisent désormais leurs bornes dans les données ; le chargement annonce sa couverture
(*« N mois appariés sur M prévus »*) et nomme les mois sans observation.

Tous les chiffres ci-dessous portent sur le jeu complet.

## 1. La courbe d'apprentissage

Ozone, J+1, **période de test fixe** — les six derniers mois, 950 553 paires. Sans cette
fixation, chaque point serait évalué sur une période différente et l'on ne saurait pas
d'où vient la variation. L'entraînement prend les mois **les plus récents avant le
test** : c'est ce qu'on ferait en exploitation.

| Mois appris | n entraînement | RMSE CAMS | RMSE MOS | Gain |
|---|---|---|---|---|
| 1 | 192 000 | 18,57 | 19,04 | **−2,6 %** |
| 2 | 377 548 | 18,57 | 18,28 | +1,5 % |
| 3 | 569 796 | 18,57 | 18,13 | +2,3 % |
| 6 | 1 130 004 | 18,57 | 16,09 | +13,3 % |
| 9 | 1 705 309 | 18,57 | 15,21 | +18,1 % |
| 12 | 2 274 788 | 18,57 | **15,16** | **+18,3 %** |

**Un mois d'historique dégrade la prévision.** Le modèle apprend une correction valable
pour la saison qu'il a vue et l'applique à contretemps ; c'est le résultat à −19 %,
retrouvé sous une forme atténuée.

**Le rendement décolle entre 3 et 6 mois**, +2,3 → +13,3. Il **sature entre 9 et 12** :
trois mois supplémentaires ne rapportent que 0,2 point.

La forme de cette courbe est le résultat, plus que ses valeurs. Elle dit qu'il existe un
**seuil**, situé autour de deux saisons, en deçà duquel la méthode ne fonctionne pas —
et qu'au-delà d'un cycle annuel, allonger l'historique n'est plus le levier utile.

## 2. La validation inter-annuelle

Le point à 12 mois **est** cette validation : appris sur **2023-08 → 2024-07**, testé sur
**2024-08 → 2025-01**, six mois entièrement postérieurs.

| | RMSE | R² | Biais |
|---|---|---|---|
| CAMS brut | 18,57 | — | — |
| **MOS corrigé** | **15,16** | **+0,671** | +3,13 |

**+18,3 % sur une période que le modèle n'a jamais vue.**

C'est le protocole d'exploitation réel — entraîner sur le passé, prédire l'avenir — et
il est plus exigeant qu'un mois exclu à l'intérieur d'une année, où le modèle avait
toujours vu la saison voisine.

### Mois par mois — la partie qui compte

Un gain moyen peut recouvrir un mois catastrophique compensé par cinq bons. Ventilation :

| Mois testé | n | RMSE CAMS | RMSE MOS | Gain | Biais MOS |
|---|---|---|---|---|---|
| 2024-08 | 192 879 | 16,63 | 13,59 | +18,3 % | +0,67 |
| 2024-09 | 185 790 | 16,75 | 15,17 | +9,5 % | −0,64 |
| **2024-10** | 192 506 | 19,59 | 16,26 | **+17,0 %** | +3,94 |
| **2024-11** | 186 864 | 20,41 | 16,45 | **+19,4 %** | +8,10 |
| 2024-12 | 192 252 | 19,11 | 14,19 | +25,8 % | +3,59 |
| 2025-01 | 262 | 25,28 | 18,45 | +27,0 % | +11,81 |

**Aucun mois négatif.** Le plus faible, septembre à +9,5 %, reste un gain.

Les deux mois où le déplacement amont s'installe — octobre et novembre 2024, ceux-là mêmes
où le biais de CAMS brut double — tiennent à **+17,0 %** et **+19,4 %**. Le biais résiduel
du MOS y monte pourtant à +3,94 puis **+8,10** : la correction absorbe l'essentiel de la
dérive amont, **sans l'annuler**. C'est la mesure de sa robustesse, et de sa limite.

Le dernier mois ne compte que 262 paires — les observations s'arrêtent au 1er janvier
2025. Son +27,0 % n'a pas de valeur statistique et ne doit pas être cité.

## Ce que ce test mesure vraiment — et qu'il ne faut pas surestimer

**La période de test contient la rupture d'octobre 2024** (voir `RUPTURE_CAMS.md` : le
biais de CAMS brut y passe de +4,47 à +12,43 entre novembre 2023 et novembre 2024).

La documentation CAMS donne un changement dans le bon mois : la mise à niveau **U9** est
déployée le **13 novembre 2024**, avec les émissions CAMS_REG.v7 et l'adaptation au cycle
**cy49r1**, lui-même basculé le **12 novembre 2024**
([ECMWF, 4 décembre 2024](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219) ;
[CAMS, DOI 10.24380/bhen-j48m](https://doi.org/10.24380/bhen-j48m)). Une étape **U8b** est
par ailleurs datée de juin 2024, sans détail publié.

**Mais l'attribution ne tient pas.** Un détecteur journalier construit depuis
(`DERIVE_CAMS.md`) date le déplacement au **24 octobre 2024 pour l'ozone**, et entre le
24 octobre et le 4 novembre pour les trois polluants — soit **huit à dix-neuf jours avant
la bascule**. Le déplacement avait déjà commencé. Le découpage mensuel ne pouvait pas
distinguer ces dates ; j'avais une rupture dans le bon mois, un changement documenté dans
le même mois, et j'ai conclu trop vite. **La cause n'est pas établie.**

Ce que l'on peut dire sans excéder les données : le test porte sur une période où
**quelque chose a changé en amont**, et le changement est antérieur à la seule
explication documentée dont on dispose. Cette expérience ne mesure donc pas la seule
généralisation temporelle : elle mesure **la robustesse à un déplacement du modèle
amont**, et les deux effets **ne sont pas séparables** dans ce découpage.

C'est une limite réelle, et c'est aussi ce qui rend le résultat intéressant : la
correction tient à travers une évolution non annoncée du modèle qu'elle corrige. Mais la
formulation honnête est **« robuste à un changement amont »**, pas « généralise à une
année nouvelle ».

Ce que la littérature dit du dispositif propre — exécutions parallèles ancien/nouveau
système, rétroprévisions produites sous cycle constant — n'est pas à notre portée ici :
CAMS a comparé e-suite et o-suite pendant environ six mois avant cy49r1, et l'archive de
prévisions conserve les productions opérationnelles successives plutôt que de les
recalculer.

## Ce qu'il faudrait pour lever l'ambiguïté

1. **Étiqueter chaque observation par le cycle amont** (U7b / U8 / U8b / U9) et publier
   les scores de part et d'autre de chaque bascule. Les dates sont connues pour U8 et U9 ;
   celle d'U8b reste **à vérifier**.
2. **Comparer fenêtre courte, fenêtre longue et pondération décroissante** sur les pertes
   qui comptent — classe ATMO et détection de seuil — et non sur le seul RMSE moyen.
3. **Surveiller la dérive en continu** : comparer l'erreur de CAMS brut à sa distribution
   historique aurait signalé la rupture au moment où elle s'est produite, pas dix mois
   plus tard.

## Ce que cela change pour l'exploitation

La saturation à 9-12 mois et l'existence de ruptures amont pointent dans la même
direction : **un réentraînement glissant sur un historique d'environ un an**, plutôt
qu'un modèle figé sur toute l'archive. C'est la pratique documentée en post-traitement
météorologique, où une fenêtre plus courte est préférée en opération précisément pour
limiter l'effet des changements de modèle
([Vannitsem et al., 2021, DOI 10.1175/BAMS-D-19-0308.1](https://doi.org/10.1175/BAMS-D-19-0308.1)).

Il n'existe pas de fréquence universelle publiée : les fenêtres opérationnelles vont de
15 jours (IMPROVER) à 60 jours (EMOS), et le MOS CAMS européen de Bertrand et al. se
réentraîne quotidiennement sur les jours récents — mais en mutualisant des milliers de
stations, ce qui fournit vite la diversité qu'un historique local doit aller chercher dans
le temps ([Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).

**Ce projet est dans le cas local :** 270 stations, un an d'historique nécessaire. La
courbe ci-dessus le montre plutôt qu'elle ne le suppose.
