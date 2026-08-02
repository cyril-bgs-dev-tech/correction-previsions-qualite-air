# Baselines de prévision — la barre à franchir

> Occitanie · apprentissage 2013-2022 · **test 2023-2024, strictement postérieur**
> Climatologie ajustée sur le train seul (18 432 cellules station × polluant × mois × heure locale).
> Généré le 2026-07-28 · `reports/baselines_occitanie.csv`

---

## Résultats

**RMSE (µg/m³)**

| Modèle | NO₂ | O₃ | PM2.5 |
|---|---|---|---|
| Persistance H+1 | **7,30** | **8,14** | **3,03** |
| Persistance H+24 | 13,93 | 22,53 | 7,53 |
| Persistance H+48 | 15,60 | 25,09 | 8,77 |
| Persistance H+72 | 16,22 | 26,10 | 9,29 |
| **Climatologie horaire** | **12,93** | **19,90** | 7,57 |

**R²**

| Modèle | NO₂ | O₃ | PM2.5 |
|---|---|---|---|
| Persistance H+1 | 0,830 | 0,907 | 0,863 |
| Persistance H+24 | 0,380 | 0,290 | 0,155 |
| Persistance H+48 | 0,224 | 0,120 | **−0,146** |
| Persistance H+72 | 0,161 | 0,048 | **−0,285** |
| Climatologie horaire | 0,382 | 0,446 | 0,139 |

---

## Lecture

**1. À une heure, la persistance est redoutable.** R² de 0,83 à 0,91 : les concentrations
sont fortement autocorrélées, et « dans une heure comme maintenant » est déjà une très
bonne prévision. Tout modèle prétendant faire de la prévision à court terme doit être
comparé à cela, pas à zéro.

**2. Elle s'effondre avec l'horizon, et la climatologie la dépasse dès J+1.**
Aux horizons réglementaires (J+1 à J+3), la barre n'est donc **pas** la persistance mais
la **climatologie horaire** : environ **12,9 µg/m³ pour le NO₂, 19,9 pour l'O₃, 7,6 pour
les PM2.5**. La climatologie ne se dégrade pas avec l'horizon — elle ignore la météo du
jour, mais elle capture le cycle diurne et la saisonnalité, qui sont stables.

**3. Le R² de la persistance devient NÉGATIF sur les PM2.5 au-delà de 48 h** (−0,15 puis
−0,29) : la valeur d'avant-hier est *activement trompeuse*, pire que de prédire la moyenne.
C'est cohérent avec la physique — les épisodes de particules sont pilotés par des
changements de régime synoptique (arrivée d'un anticyclone, inversion thermique). Quand
le régime bascule, le passé récent pointe dans la mauvaise direction.

**4. L'ozone est le plus prévisible à court terme** (R² 0,907 à H+1), le moins à long
terme relativement. Son cycle diurne photochimique est très régulier, d'où la performance
de la climatologie (R² 0,446, le meilleur des trois).

---

## Conséquences pour la suite

- **La barre officielle du projet, aux horizons J+1 à J+3 : RMSE 12,9 / 19,9 / 7,6.**
  Un modèle qui ne fait pas mieux ne mérite pas d'être retenu.
- La faible performance de la climatologie sur les PM2.5 (R² 0,139) indique que
  **l'essentiel de leur variance est météorologique**, non saisonnier. C'est le polluant
  où l'apport des variables météo devrait être le plus fort — et celui où l'absence
  actuelle d'ERA5 pèse le plus.
- Prochaine référence à ajouter : **CAMS brut**, la vraie référence métier.

## Précautions appliquées

- **Découpage strictement temporel** — apprentissage avant 2023, test après. Un découpage
  aléatoire aurait placé des heures futures dans l'apprentissage entre deux heures de
  test séparées de 120 minutes : le modèle aurait interpolé au lieu de prévoir.
- **Climatologie estimée sur le train seul.** L'ajuster sur toutes les données ferait
  entrer de l'information future dans la prévision — invisible dans les métriques, et
  flatteur.
- **Décalage de persistance sur grille horaire continue**, pas sur les lignes : sur un
  index troué, décaler de 24 positions ne remonte pas de 24 heures.
