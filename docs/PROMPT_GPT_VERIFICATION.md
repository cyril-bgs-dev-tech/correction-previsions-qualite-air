# Prompt ChatGPT — vérifier le référentiel et la méthode, pas le récit

*À coller tel quel. Rédigé le 01/08/2026. Objectif : contrôler des affirmations vérifiables
sur pièces — textes réglementaires, documentation produit, littérature méthodologique.*

---

## Ton rôle

Tu es **relecteur méthodologique**. Ton travail n'est pas de juger si le projet est bon, mais
de vérifier si **ce qu'il affirme est exact** et si **ce qu'il fait est correctement fait**.

Quatre consignes qui prévalent :

1. **Sourcer ou s'abstenir.** Toute affirmation réglementaire doit renvoyer à un texte
   identifiable — arrêté, guide LCSQA, directive, documentation produit. « Il me semble
   que » n'a aucune valeur ici.
2. **Distinguer trois verdicts** : *confirmé*, *contredit*, *non vérifiable avec les sources
   accessibles*. Le troisième est une réponse utile, pas un échec.
3. **Ne pas reformuler ce que je t'écris.** Je le connais.
4. **Signaler les erreurs de raisonnement**, même quand le chiffre est juste. Un calcul exact
   sur une grandeur mal choisie reste faux.

---

## Le contexte technique, en bref

Post-traitement statistique des prévisions **CAMS Europe** (maille 0,1° ≈ 8 km, J+1 à J+3).
Un modèle à gradient boosté apprend le résidu `observation − CAMS` à partir de variables
disponibles à l'heure d'émission. Validation par **stations entièrement exclues**, intervalles
par bootstrap de stations, plus un test hors fenêtre temporelle sur 2025.

Comparé au post-traitement officiel de Copernicus
(`cams-europe-air-quality-forecasts-optimised-at-observation-sites`), sur les mêmes stations
et les mêmes jours.

---

## Bloc A — le référentiel français d'évaluation

### A1. La convention de calcul

Le dossier affirme qu'un rapport AASQA conforme au référentiel LCSQA calcule ainsi :

- **stations de fond seules** — urbaines, périurbaines, rurales ; trafic et industrielles
  écartées ;
- **disponibilité > 75 %** des données valides sur la période ;
- **score temporel par station, puis moyenne non pondérée des stations** ;
- **échéances séparées** (J+1, J+2, J+3) ;
- **ozone limité à la fenêtre avril–septembre**.

**À vérifier point par point.** Sources attendues : arrêté du 16 avril 2021 relatif au
dispositif national de surveillance de la qualité de l'air ambiant (article 13), guide
méthodologique LCSQA d'évaluation de la prévision approuvé le 18/03/2021, page « Évaluations »
de PREV'AIR, et au moins un bilan réglementaire d'AASQA publié sur le site du LCSQA.

Si l'une de ces règles n'existe pas telle quelle, dis laquelle et ce que dit le texte réel.

### A2. Les seuils, et lequel déclenche quoi

Le dossier distingue :

- **120 µg/m³ en maximum glissant 8 h** = valeur cible européenne pour l'ozone ;
- **180 µg/m³ en maximum horaire** = seuil d'information et de recommandation français ;
- **240 µg/m³ en maximum horaire** = seuil d'alerte ozone ;
- **200 µg/m³ en maximum horaire** = seuil d'information NO₂ ;
- **50 µg/m³ en moyenne journalière** = seuil PM10 de la procédure française.

**Vérifie chacun**, et surtout : **lequel déclenche effectivement une procédure préfectorale**,
et sur quelle base — prévision ou constat. Le dossier s'appuie sur l'arrêté du 7 avril 2016
pour affirmer que le déclenchement peut se faire **sur prévision, sans attendre la
confirmation par la mesure**. Confirme ou corrige.

Enjeu direct : le dossier annonce « 3,5 fois plus de dépassements détectés » sur le seuil de
**120 µg/m³ MDA8**. Il a mesuré qu'à **180 µg/m³ en max horaire**, sur 60 400 jours-station,
il y a 32 dépassements dont CAMS en détecte 3 et la correction 2 — donc rien d'exploitable.
**Est-ce que le premier chiffre a le droit d'être présenté à une AASQA sans le second ?**

### A3. L'indice ATMO

Le dossier a mesuré que l'indice publié suit la règle « maximum des sous-indices » à
**99,926 %** sur 47 300 enregistrements, et que l'**ozone porte l'indice 87,8 % des jours**
en Occitanie. Vérifie la règle d'agrégation contre l'arrêté du 10 juillet 2020, et le fait que
l'indice officiel est calculé sur une **modélisation spatialisée** et non depuis les stations.

---

## Bloc B — la validation spatiale

Le dossier a découvert que ses plis de validation, construits par `i % n` sur l'identifiant de
station, ne sont **pas bloqués spatialement**. Mesures :

- plus proche voisin : **médiane 2,4 km**, premier quartile 1,0 km, 79 % à moins de 10 km ;
- **79 %** des stations ont leur plus proche voisine **dans un autre pli** ;
- maille CAMS : 8 km — donc voisin et station de test partagent souvent la même valeur prévue.

Correction appliquée : regroupement des stations par k-moyennes sur coordonnées Lambert-93,
puis **grappes entières** en test (fuite ramenée à 3 %), plus un **fossé** excluant de
l'apprentissage toute station à moins de *r* km d'une station de test.

| protocole (O₃) | séparation | gain |
|---|---|---|
| `i % 3` — publié jusqu'ici | 2,4 km médiane | +28,60 % |
| blocs spatiaux | ≥ 27 km | +19,21 % |
| blocs + fossé 50 km (34 stations écartées) | ≥ 50 km | **+18,47 %** |

Optimisme mesuré : **−10,1 points** sur O₃, −7,7 sur PM2,5, −2,2 sur NO₂.

### Ce que je te demande

1. La construction est-elle **correcte** au regard de la littérature de validation croisée
   spatiale ? Nomme le protocole standard qui correspond, s'il en existe un, et dis si le
   fossé aurait dû être appliqué autrement (buffer autour de chaque point de test plutôt
   qu'autour du bloc, par exemple).
2. Un écart de **−10 points** est-il de l'ordre attendu, ou anormalement grand ? Cite des
   ordres de grandeur publiés si tu en trouves.
3. Le NO₂ résiste beaucoup mieux (−2,2 pts) que l'ozone (−10,1). L'explication proposée est
   que le signal NO₂ est très local, donc qu'un voisin à 2 km ne le renseigne pas.
   **Est-ce cohérent ?** Une explication alternative existe-t-elle ?
4. Faut-il publier les deux chiffres ou seulement le bloqué ? Argumente.

---

## Bloc C — trois choix de méthode à contrôler

### C1. L'agrégation des RMSE

Un audit a trouvé que le projet agrégeait des RMSE mensuelles par
`np.average(rmse, weights=n)` au lieu de `√(Σ nₘ·RMSEₘ² / Σ nₘ)`. Correction appliquée aux
quatre sites concernés ; les chiffres ont **monté** (O₃ au grain réglementaire : +21,5 % →
+23,4 %), parce que l'erreur minorait davantage CAMS brut, dont les mois sont plus dispersés.

Confirme la formule, et dis si le **biais**, la **corrélation** et le **MQI FAIRMODE**
s'agrègent linéairement ou non — le dossier suppose que le biais oui, les deux autres ne sont
pas tranchés.

### C2. La forme du résidu

Quatre formes comparées sur les mêmes plis, cible `observation` reconstruite depuis CAMS :

| forme | cible apprise | O₃ RMSE | décile haut | CSI |
|---|---|---|---|---|
| différence *(retenue)* | `obs − cams` | **8,350** | **10,562** | **0,439** |
| racine | `√obs − √cams` | 8,358 | 10,898 | 0,424 |
| log-additif | `log1p(obs) − log1p(cams)` | 8,548 | 11,489 | 0,405 |
| rapport | `log(obs / cams)` | 8,569 | 11,554 | 0,404 |

Les formes logarithmiques montrent un **biais négatif systématique** (−0,88 sur O₃).
L'implémentation **ne corrige pas le biais de rétro-transformation** — pas de correction de
Duan ni de terme `exp(σ²/2)`. Le dossier estime que ce biais explique environ 4 % de la
dégradation de queue et que la conclusion tient malgré tout.

**Cette estimation est-elle défendable ?** Et une implémentation correcte du rapport
changerait-elle le classement ?

### C3. Le critère de rétention

Le projet retenait une piste si elle gagnait **0,3 µg/m³**. Ce seuil absolu vaut 2,1 % du RMSE
de base sur NO₂ et **11,0 % sur PM2,5** — donc trois fois plus sévère pour les particules,
sans raison. Il a été remplacé par un critère **relatif à 2 % du RMSE de base**, justifié
ainsi : la demi-largeur des IC95 par bootstrap de stations vaut de façon stable **1,0 à 1,5 %**
du RMSE de base sur les trois polluants, donc 2 % est juste au-dessus du pouvoir de résolution,
à la même distance pour chacun.

**Ce raisonnement tient-il ?** Un critère fondé sur la largeur d'intervalle est-il circulaire ?
Existe-t-il une pratique établie en évaluation de prévision de qualité de l'air ?

---

## Bloc D — ce que je ne sais pas voir

Une question ouverte, et c'est peut-être la plus utile.

Le dossier a été audité une fois et corrigé sur quatre points en une journée : agrégation non
quadratique, fuite spatiale, endpoint mal nommé, deux périmètres confondus sur une page
publiée. Tous étaient des défauts **silencieux** — aucun ne levait d'erreur, et trois
jouaient en faveur du projet.

**Quelle catégorie de défaut de ce type reste vraisemblablement présente ?** Raisonne par
famille — appariement temporel, fuite de cible, sélection de population, dépendance entre
observations, choix de métrique — plutôt qu'en devinant un bogue précis. Pour chaque famille,
dis quel test bon marché le révélerait.

---

## Format de réponse

Quatre blocs, dans l'ordre A, B, C, D. Dans chacun, une entrée par point numéroté, avec :

- **verdict** : confirmé / contredit / non vérifiable ;
- **source** : référence précise, ou « aucune source accessible » ;
- **conséquence** : ce que le dossier doit changer, en une phrase.

Termine par une liste unique : **les corrections par ordre de gravité**, la plus grave en
premier, avec pour chacune le temps estimé pour la traiter.

Pas d'introduction, pas de résumé de ce que je viens d'écrire, pas de conclusion
d'encouragement.
