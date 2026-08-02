# Tous les modèles, sur le même échantillon

Une relecture adverse a relevé que les baselines observationnelles (Occitanie, test
2023-2024) et le benchmark CAMS (métropole, trois mois de 2024) étaient présentés comme
une progression, alors qu'ils ne portaient ni sur les mêmes stations, ni sur la même
période, ni sur la même région. **Les RMSE n'étaient donc pas comparables.**

Voici la comparaison refaite sur l'**intersection exacte** — mêmes stations, mêmes
heures, même polluant, même horizon. Ozone, J+1, **571 246 couples** (99 % de
l'échantillon MOS), 270 stations, 2024.

| Modèle | RMSE | MAE | Biais | R² |
|---|---|---|---|---|
| Persistance (J−1, même heure) | 20,74 | 15,90 | +0,04 | +0,344 |
| Climatologie horaire | 19,91 | 16,30 | +2,41 | +0,396 |
| CAMS brut | 17,59 | 12,84 | +7,16 | +0,528 |
| **CAMS corrigé** | **12,61** | **9,41** | **−0,09** | **+0,758** |

La climatologie est apprise sur **22,5 millions d'observations strictement antérieures**
au 1er janvier 2024 : aucune information de la période évaluée n'y entre.

## Ce que la comparaison honnête donne

- **−36,7 %** de RMSE face à la meilleure baseline d'observation (la climatologie).
- **−28,3 %** face à CAMS brut.

La hiérarchie annoncée est confirmée — persistance, puis climatologie, puis CAMS, puis
correction — mais elle repose désormais sur une comparaison qui tient.

## Ce que cela apprend au passage

**La persistance est un mauvais concurrent sur l'ozone** (RMSE 20,74, R² 0,344), alors
qu'elle est redoutable sur des polluants à forte inertie. L'ozone se reforme chaque jour
par photochimie : la valeur d'hier à la même heure n'en dit pas grand-chose.

**La climatologie fait à peine mieux** (19,91), ce qui situe la difficulté du problème :
connaître le cycle diurne et la saison d'une station ne suffit pas. C'est la
variabilité **jour à jour** — donc météorologique et chimique — qu'il faut capter, et
c'est précisément ce que CAMS apporte.

**Le biais départage plus nettement que le RMSE.** La persistance est non biaisée par
construction (+0,04) mais imprécise ; CAMS est précis mais fortement biaisé (+7,16) ; la
correction obtient les deux (−0,09 pour un RMSE de 12,61). Pour un usage réglementaire
où l'on compare à des seuils, un biais de +7 µg/m³ n'est pas un détail.
