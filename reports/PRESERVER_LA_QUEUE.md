# Cesser d'écraser les pics — un arbitrage, pas une correction gratuite

## Le problème

Sur l'ozone, la correction gagne 28 % de RMSE global et **dégrade le décile supérieur**.
La cause est mécanique : minimiser une erreur quadratique sur une distribution asymétrique
tire les extrêmes vers la moyenne. Or c'est dans la queue que se joue le métier d'une
AASQA.

Trois remèdes testés, sans changer d'architecture — même modèle, même validation par
stations exclues, seule la **fonction de perte** change.

## Le résultat

| Variante | RMSE global | RMSE décile supérieur | Décile sup. vs CAMS |
|---|---|---|---|
| CAMS brut | 17,58 | 14,89 | — |
| **Erreur quadratique** (référence) | **12,58** | 15,54 | **−4,4 %** |
| Quantile q = 0,90 (pinball) | 18,61 | **12,91** | **+13,3 %** |
| **Quadratique pondérée par la concentration** | 13,79 | 13,55 | **+9,0 %** |
| Huber (témoin négatif) | 14,74 | 16,62 | −11,6 % |

**Le témoin négatif valide le protocole.** La perte de Huber, moins sensible aux valeurs
extrêmes, devait aggraver l'écrasement — elle le fait (−11,6 %). Le dispositif mesure donc
bien ce qu'il prétend mesurer, ce qu'un résultat positif seul n'aurait pas établi.

## L'arbitrage, chiffré

**La régression quantile sauve la queue et ruine le reste.** À q = 0,90, le modèle vise le
neuvième décile : il surestime partout ailleurs, et son RMSE global (18,61) devient **pire
que CAMS brut**. Inutilisable telle quelle.

**La pondération par la concentration est le compromis exploitable.** En faisant peser
chaque observation proportionnellement à sa valeur, une erreur sur un pic coûte autant
que plusieurs erreurs sur du fond. Bilan :

| | Gain global | Gain sur le décile supérieur |
|---|---|---|
| Erreur quadratique | **+28,4 %** | −4,4 % |
| Pondérée | +21,6 % | **+9,0 %** |

**On abandonne 6,8 points de gain global pour en gagner 13,4 sur la queue.**

## Quel choix recommander

Pour une AASQA, **la pondération**. Le RMSE global sert à un classement de modèles ; ce
qui engage l'organisme, c'est la détection des épisodes. Un modèle qui gagne 28 % en
moyenne mais dégrade les pics est moins utile qu'un modèle qui gagne 22 % et les améliore.

Et il faut noter que **21,6 % reste très supérieur** à ce que donnent les baselines
(climatologie : 19,91 de RMSE contre 13,79) — l'arbitrage ne sacrifie pas le résultat, il
le redistribue.

## Ce que cela ne règle pas

Le diagnostic par régime a montré que la dégradation de l'ozone se concentre **hors régime
photochimique**. La pondération traite le symptôme global ; une solution plus fine
consisterait en un **modèle à deux régimes** — un classifieur épisode / hors épisode, puis
un régresseur conditionnel. C'est la piste suivante, non explorée faute de temps.

Enfin, la cause première reste l'échantillon : **trois mois, dont un seul été**. La queue
de l'ozone est mal représentée, et une année complète pourrait rendre l'arbitrage moins
coûteux — c'est un motif supplémentaire d'étendre l'archive.
