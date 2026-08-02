# Prompt ChatGPT — une semaine pour établir la barre réelle

*À coller tel quel. Rédigé le 01/08/2026. Mission de recherche, pas question ponctuelle.*

---

## Le problème que tu dois résoudre

Un projet de post-traitement statistique des prévisions **CAMS Europe** annonce des gains de
**+21,7 % à +34,7 %** de RMSE. Ces gains sont mesurés **contre la prévision CAMS brute**.

Or une AASQA — association agréée de surveillance de la qualité de l'air — **ne consomme pas
CAMS brut**. Elle reçoit **PREV'AIR** (plateforme nationale INERIS/LCSQA/Météo-France) et fait
souvent tourner son propre modèle régional. Battre CAMS brut de 23 % ne dit donc **rien** de
ce que ce travail apporterait chez elle.

**Ta mission : établir ce que PREV'AIR et les modèles régionaux d'AASQA obtiennent réellement,
dans des chiffres publiés, sur des grandeurs comparables.** Sans cela, le projet ne peut pas
répondre à la seule question qui compte : *est-ce que ça sert à quelque chose ?*

C'est une tâche de fouille documentaire longue et ingrate. Elle a une valeur énorme et
personne ne l'a faite.

---

## Où chercher — les sources sont publiques

L'**arrêté du 16 avril 2021, article 13** impose à chaque AASQA une **évaluation annuelle de
ses outils de modélisation**, transmise au plus tard le 30 juin suivant, selon le référentiel
technique national du LCSQA. Ces bilans sont **déposés et publics**.

Pistes, par ordre de rendement attendu :

1. **`lcsqa.org`** — rubrique rapports et documents. Chercher « bilan réglementaire PREV'AIR »,
   « bilan indicateurs prévision », suivi d'un millésime et d'un nom d'AASQA. Deux exemples
   connus : *Bilan_reglementaire_PREVAIR_A2022_v20230602.NA_.pdf* (Atmo Nouvelle-Aquitaine),
   *Bilan_Indicateurs_Prévision_2022_AIRPARIF.pdf*. Il en existe d'autres années et d'autres
   régions.
2. **`prevair.org`** — page « Évaluations », et les rapports d'évaluation annuels.
3. **Les sites des AASQA elles-mêmes** — Atmo Occitanie en priorité, puis Atmo
   Auvergne-Rhône-Alpes, Atmo Grand Est, Airparif, Atmo Nouvelle-Aquitaine, Atmo Sud. Chercher
   « rapport d'activité », « bilan prévision », « évaluation modélisation ».
4. **Le référentiel technique national LCSQA** applicable au 01/01/2022 — il contient les
   **objectifs de qualité chiffrés** que les AASQA doivent atteindre. Ces objectifs sont une
   barre en soi, même sans bilan régional.
5. **La littérature** — évaluations publiées de PREV'AIR ou de CHIMERE opérationnel sur la
   France, notamment dans *Atmospheric Environment*, *ACP*, *GMD*.

---

## Ce que tu dois extraire, et sous quelle forme

Pour **chaque source trouvée**, une ligne par combinaison mesurée :

| champ | contenu attendu |
|---|---|
| `source` | titre exact, organisme, année, URL |
| `modele` | PREV'AIR national, PREV'AIR régionalisé, modèle propre de l'AASQA — préciser |
| `polluant` | O₃, NO₂, PM10, PM2,5 |
| `grandeur` | **exactement** : moyenne horaire, maximum journalier horaire, maximum glissant 8 h, moyenne journalière |
| `horizon` | J0, J+1, J+2, J+3 |
| `population` | typologie retenue, nombre de stations, filtre de disponibilité |
| `periode` | année ou fenêtre, et pour O₃ si c'est avril–septembre |
| `rmse`, `biais`, `correlation` | valeurs, en µg/m³ pour les deux premières |
| `mode_agregation` | **score par station puis moyenne**, ou RMSE groupée sur toutes les lignes — c'est décisif |
| `detection` | POD, FAR, CSI et seuil, si le rapport en donne |

Quand un champ n'est pas donné, écris `non précisé`. **Ne le déduis jamais.**

---

## Les cinq pièges, et ils sont tous fatals

Ce projet a déjà perdu des journées sur chacun. Tu dois les éviter explicitement.

1. **Le grain.** Une RMSE horaire et une RMSE sur maximum journalier 8 h ne sont **pas
   comparables** : elles diffèrent d'un facteur 1,4 environ sur l'ozone. Un rapport qui ne dit
   pas son grain est inutilisable — signale-le plutôt que de supposer.
2. **Le mode d'agrégation.** « Score par station puis moyenne non pondérée » et « RMSE
   groupée » donnent des valeurs différentes, et l'écart change de signe selon le polluant : sur
   ce projet, −1,6 point sur NO₂ mais **+3,2 points sur PM2,5**. Toujours noter lequel.
3. **La population.** Stations de fond seules, ou toutes typologies ? Le NO₂ passe d'une RMSE
   de 15,5 à 5,1 µg/m³ entre urbain de fond et rural. Un chiffre sans sa population ne veut
   rien dire.
4. **La fenêtre.** L'ozone s'évalue d'avril à septembre au référentiel. Une RMSE annuelle
   d'ozone n'est pas la même grandeur — sur ce projet, l'écart entre les deux fenêtres
   **inverse le signe** d'une comparaison.
5. **La RMSE ne s'agrège pas linéairement.** Si un rapport donne des valeurs mensuelles et que
   tu veux une valeur annuelle, c'est `√(Σ nₘ·RMSEₘ² / Σ nₘ)`, jamais une moyenne. Le biais,
   lui, se moyenne bien. La corrélation, non — elle se recalcule sur les couples bruts.

---

## Les chiffres du projet, pour cadrer la comparaison

Convention AASQA — stations de fond, disponibilité ≥ 75 %, score par station puis moyenne non
pondérée, échéance J+1, O₃ limité à avril–septembre, validation par stations entièrement
exclues :

| polluant | grandeur | n stations | CAMS brut | ce projet |
|---|---|---|---|---|
| O₃ | max glissant 8 h | 254 | 10,06 | **7,88** |
| NO₂ | max horaire | 217 | 15,46 | **10,10** |
| PM2,5 | moyenne journalière | 156 | 3,94 | **2,77** |

Biais du NO₂ sur les 150 stations **urbaines de fond** : CAMS **−11,6 µg/m³**, ce projet
**−0,5**.

**La question à laquelle tu dois permettre de répondre** : PREV'AIR, sur ces mêmes grandeurs,
obtient-il **mieux ou moins bien que 7,88 / 10,10 / 2,77** ?

Si PREV'AIR fait mieux, le projet n'a pas de valeur opérationnelle et il vaut mieux le savoir
maintenant. Si PREV'AIR fait moins bien, c'est le résultat le plus important du dossier et il
n'existe pas encore.

---

## Trois questions secondaires, si le temps le permet

### S1. Les objectifs de qualité du référentiel

Le référentiel technique national fixe des **objectifs chiffrés** que les AASQA doivent
atteindre. Lesquels exactement, par polluant et par horizon ? Les chiffres du projet les
atteignent-ils ? C'est une barre absolue, indépendante de toute comparaison.

### S2. Ce que fait Atmo Occitanie précisément

Quel modèle, quelle maille, quelle chaîne, quels horizons publiés, quelle méthode de
correction ou d'assimilation si elle est documentée ? Sources : rapports d'activité, PRSQA
Occitanie, communications techniques, portail de données ouvertes.

### S3. L'antériorité, précisément

Le projet cite **Bertrand, Meleux, Ung, Descombes & Colette 2023** (*ACP* 23, 5317) comme
antériorité du post-traitement statistique de CAMS. Qu'existe-t-il d'autre ? Et surtout :
**qu'est-ce qui n'a pas été publié** ? Le projet a mesuré trois choses qu'il ne trouve nulle
part et voudrait savoir si elles sont neuves :

- le post-traitement officiel de Copernicus **dégrade** la prévision brute d'ozone au grain
  réglementaire **huit mois sur douze**, et de **−19,6 %** sur avril–septembre ;
- l'écart entre validation par plis aléatoires et **plis bloqués spatialement** vaut
  **−10 points** sur l'ozone mais seulement **−2,2** sur le NO₂ ;
- apprendre la **grandeur réglementaire** plutôt que l'horaire vaut +5 à 6 points.

---

## Comment travailler, et comment me rendre ça

C'est une mission longue. Structure-la :

**Jour 1-2 — inventaire.** Liste toutes les sources trouvées avec leur URL et ce qu'elles
contiennent, **sans encore extraire les chiffres**. Rends cette liste avant d'aller plus loin :
si elle est vide ou maigre, la suite n'a pas de sens et il faut le dire tout de suite.

**Jour 3-5 — extraction.** Le tableau ligne à ligne, au format ci-dessus. Une ligne par
combinaison, jamais de moyenne entre sources.

**Jour 6-7 — synthèse.** Trois livrables :

1. **Le tableau complet**, en CSV, avec toutes les colonnes demandées.
2. **La réponse à la question centrale** — PREV'AIR fait-il mieux ou moins bien, et sur quelles
   grandeurs la comparaison est-elle **légitime** ? Sépare clairement « comparable »,
   « comparable sous réserve », « non comparable ».
3. **Ce que tu n'as pas trouvé**, explicitement. Un « je n'ai trouvé aucun bilan postérieur à
   2022 » est une information de grande valeur : cela dirait que la comparaison est impossible
   sur pièces publiques, ce qui est en soi une réponse.

---

## Règles qui prévalent sur tout

- **Aucun chiffre sans source précise** — document, page ou section, URL. Un chiffre non
  sourcé est pire qu'une absence de chiffre : il sera cité et il sera faux.
- **Ne convertis pas entre grains.** Si un rapport donne de l'horaire et que le projet a du
  maximum 8 h, dis-le et laisse la case vide. Une conversion approximative détruirait toute la
  comparaison.
- **Distingue toujours** ce que le document affirme de ce que tu en déduis. Marque tes
  déductions comme telles.
- **« Non trouvé » est une réponse complète.** Ne comble jamais un trou par une estimation.
- Pas d'introduction, pas de résumé de cet énoncé, pas de conclusion d'encouragement.
