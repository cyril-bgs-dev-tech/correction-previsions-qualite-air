# Trois matinées d'astreinte, rejouées

*Occitanie, 25 au 27 juillet 2026 · PM2,5 · seuil du sous-indice ATMO « mauvais » : 25 µg/m³
· `scripts/trois_matins.py`*

Deux relectures indépendantes ont fait le même reproche, dans les mêmes termes : *« beaucoup de
RMSE, encore peu de matins rejoués sur vos épisodes »* et *« montrez-moi trois jours d'Occitanie
où vous m'évitez une bêtise »*. Ce document y répond avec les trois seules journées de
juillet 2026 où l'Occitanie a connu un dépassement PM — pas trois journées choisies.

**Ce que ce rejeu ne peut pas dire.** L'épisode du 25/07 était un dépassement **PM10**, que le
projet ne modélise pas. On rejoue les PM2,5, corrélées mais distinctes. Et le modèle n'a pas
tourné en direct ce jour-là : on montre ce qu'il aurait produit avec les entrées de l'époque.

Trois produits sont comparés : **CAMS brut**, la correction **actuelle** du dossier, et la
correction **avec observation de la veille** — le prédicteur mesuré le 30/07 à +8,9 % sur O₃
et +21,9 % sur NO₂, jamais encore éprouvé sur un cas réel.

---

## Samedi 25 juillet — personne ne voit rien

| station | observé | CAMS | correction actuelle | + observation |
|---|---|---|---|---|
| FR12095 | **51,2** | 6,4 | 8,0 | 8,2 |
| FR50060 | 33,5 | 7,5 | 8,9 | 9,8 |
| FR08714 | 27,8 | 6,7 | 8,6 | 9,4 |

**Maximum régional** : observé **51,2** · CAMS 7,7 · correction 14,4 · avec observation 13,0.
**Sept stations** dépassent réellement 25 µg/m³. **Aucun produit n'en annonce une seule.**

C'est l'échec complet, et il faut le dire en premier. L'épisode arrive sur des journées calmes —
l'observation de la veille n'aide donc pas non plus : il n'y avait rien à persister. Une
prévision à J+1 fondée sur un modèle qui annonce 7 µg/m³ là où l'air en portera 51 ne se rattrape
par aucun post-traitement.

> **Décision à 10 h** : rien ne serait publié. La journée serait constatée le lendemain, comme
> elle l'a été.

---

## Dimanche 26 juillet — le jour où la correction actuelle aurait fait perdre l'alerte

| station | observé | CAMS | correction actuelle | + observation |
|---|---|---|---|---|
| **FR12095** | **46,8** | 28,4 → **alerte** | 22,6 → **rien** | 25,2 → **alerte** |
| FR50060 | 32,6 | 48,5 → alerte | 37,3 → alerte | 43,6 → alerte |
| FR12053 | 25,8 | 49,6 → alerte | 37,6 → alerte | 44,7 → alerte |
| FR08016 | 30,9 | 24,7 | 23,1 | 22,7 |

**Stations annoncées au-dessus du seuil** : réel 6 · CAMS 3 · **correction actuelle 2** ·
avec observation 3.

C'est le cas qui compte. Sur la station la plus chargée, **CAMS annonçait correctement un
dépassement à 28,4 ; la correction actuelle le ramène à 22,6 et fait disparaître l'alerte.**
La correction ne se contente pas d'être inutile ce jour-là : elle **détruit une alerte juste**.

Avec l'observation de la veille — FR12095 avait mesuré 51,2 la veille — la prévision remonte à
25,2 et l'alerte est conservée.

Ce cas justifie, sur une journée réelle, deux choses que le projet avançait jusqu'ici sur des
mesures agrégées : la **règle d'abstention** — ne pas corriger à la baisse quand le forçage
annonce déjà un dépassement — et l'apport de l'**observation récente**.

> **Décision à 10 h** : avec CAMS seul ou avec observation, on gradue. Avec la correction
> actuelle **seule**, on ne le fait pas — et c'est une erreur que l'outil aurait causée.

---

## Lundi 27 juillet — la moitié du chemin

| station | observé | CAMS | correction actuelle | + observation |
|---|---|---|---|---|
| FR12095 | **44,8** | 15,1 | 14,2 | **23,4** |
| FR50225 | 27,0 | 12,2 | 14,9 | 16,3 |

**Maximum régional** : observé 44,8 · CAMS 15,1 · correction 15,7 · **avec observation 23,4**.
Deux stations dépassent réellement ; aucun produit n'en annonce.

L'observation de la veille comble **plus de la moitié** de l'écart sur la station critique —
de 15,1 à 23,4 pour 44,8 observés — sans franchir le seuil. C'est un progrès réel qui ne change
pas la décision.

> **Décision à 10 h** : rien n'est publié dans les trois cas. Mais l'écart affiché passe de
> « le modèle ne voit rien » à « le modèle voit quelque chose sans oser le dire », ce qui n'est
> pas le même message pour un prévisionniste.

---

## Ce que ces trois matins établissent

1. **Sur une sous-estimation brutale et soudaine, rien ne rattrape** (25/07). Le
   post-traitement ne crée pas d'information ; il redistribue celle du modèle amont.
2. **La correction actuelle peut détruire une alerte juste** (26/07). Ce n'est plus une
   hypothèse tirée d'un front de Pareto : c'est arrivé, sur la station la plus chargée du jour
   le plus chargé.
3. **L'observation de la veille est le seul des trois produits à ne jamais nuire** sur ces
   journées, et le seul à récupérer une alerte perdue.

Et le motif qui les relie : la correction rattrape les **sur-estimations** de CAMS — elle sauve
FR50060 et FR12053 le 26/07 — et échoue sur les **sous-estimations locales persistantes**, qui
sont précisément celles qu'une observation récente signale.

## Ce qu'il faudrait pour aller plus loin

- **Modéliser les PM10**, puisque c'est le polluant qui a déclenché l'épisode du 25/07.
- **Rejouer davantage de journées** : trois matins ne font pas une évaluation, ils font une
  illustration honnête. Les scores agrégés restent la mesure ; ceci en est la traduction.
- **Trancher la règle d'abstention en exploitation** : sur le 26/07 elle aurait préservé
  l'alerte, mais elle a un coût mesuré ailleurs (+0,02 µg/m³ de RMSE global, FAR dégradé). Ce
  n'est pas un arbitrage technique, c'est un arbitrage de service.
