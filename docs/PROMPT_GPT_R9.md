# R9 — Audit de la nuit du 1ᵉʳ au 2 août 2026

Tu es relecteur adverse. **Ton travail n'est pas de valider, c'est de trouver où je me trompe.**
Les audits précédents de cette série ont trouvé de vraies fautes — une agrégation de RMSE
linéaire au lieu de quadratique, des plis de validation non bloqués spatialement, un critère
d'arrêt en unités absolues appliqué à des polluants d'échelles différentes. Je cherche la
même chose.

## Le projet, en cinq lignes

Post-traitement statistique des prévisions **CAMS Europe** (maille 0,1° ≈ 8 km, J+1 à J+3),
pour une candidature à une association agréée de surveillance de la qualité de l'air.
Un modèle à gradient boosté apprend le **résidu** `observation − CAMS` à partir de variables
disponibles à l'heure d'émission, station par station, sur ~476 stations françaises.
Validation par **stations entièrement exclues** — la revendication est « prédire là où rien
ne mesure ». Cible agrégée au jour : max glissant 8 h pour O₃, max horaire pour NO₂, moyenne
journalière pour les PM.

Le cadrage assumé est celui de l'**évaluateur** : la méthode est publiée (Bertrand et al.
2023), ce qui a de la valeur c'est d'avoir mesuré où les produits officiels échouent.

---

## Q1 — La typologie de station vaut-elle vraiment +16,5 %, ou ai-je une fuite ?

**Le fait.** Le modèle avait 53 prédicteurs : sortie CAMS, 30 variables de forêt à rayons
emboîtés, 5 de route, 9 de relief, latitude, longitude, altitude, 6 d'horloge. J'ai découvert
que `type_station` était **explicitement sur liste noire** dans le sélecteur de variables, et
que l'axe urbain/périurbain/rural n'avait jamais été joint au panel.

J'ai ajouté 4 colonnes : `typo_densite` ordinale (urbain 0 → rural isolé 4) et trois
indicatrices fond / trafic / industriel. Mesuré sur 166 163 jours-station, 343 stations,
validation par stations exclues, IC95 par bootstrap **de stations** (400 tirages) :

| polluant | protocole `i % 3` | blocs spatiaux + fossé |
|---|---|---|
| **NO₂** | **+2,501 µg/m³ (+16,5 %)** IC95 [+1,849 ; +3,125] | **+2,052 (+12,9 %)** IC95 [+1,518 ; +2,617] |
| O₃ | −0,017 · IC95 [−0,056 ; +0,012] | +0,005 · nul |
| PM2,5 | +0,010 · IC95 [−0,017 ; +0,035] | −0,011 · nul |

Le décile haut s'améliore aussi sur NO₂ : 32,64 → 28,21 sous blocage.

**Mon raisonnement** : pas de fuite de cible, parce que la typologie d'une station nouvelle
est connue le jour de son installation — c'est un descripteur de lieu au même titre que
l'altitude. Le mécanisme : CAMS à 8 km ne distingue pas une station trafic d'une station de
fond à 400 m, et il sous-estime le NO₂ urbain de fond de 11,6 µg/m³ (mesuré par ailleurs).

**Mes questions.**
1. Y a-t-il une fuite que je ne vois pas ? En particulier : les plis sont construits par
   `i % 3` sur l'identifiant de station **trié**, ce qui n'est pas aléatoire. Les
   identifiants encodent-ils quelque chose (département, ordre d'installation) qui rendrait
   la répartition des typologies entre plis non représentative ?
2. **+16,5 % pour 4 colonnes catégorielles, est-ce plausible ?** C'est plus que le meilleur
   levier du projet (l'observation de la veille, +8,9 %). Qu'est-ce qui, dans la structure de
   ce problème, rendrait ce chiffre suspect ?
3. La nullité sur O₃ et PM2,5 conforte-t-elle le mécanisme, ou est-ce que je construis une
   explication après coup ?

---

## Q2 — Le modèle est sous-ajusté d'un facteur 8. Est-ce que je mesure bien ce que je crois ?

**Le fait.** Le modèle en production est un LightGBM à `n_estimators=400` fixe,
`learning_rate=0.05`, `num_leaves=63`, `min_child_samples=200`. En ne changeant **que** le
nombre d'arbres, sur un test de 90 stations jamais consultées (45 508 lignes, O₃ journalier) :

| arbres | RMSE | décile haut | gain vs CAMS |
|---|---|---|---|
| **400 (production)** | **8,9217** | 11,1394 | **+25,59 %** |
| 1 000 | 8,6380 | 10,8698 | +27,96 % |
| 2 000 | 8,4691 | 10,7113 | +29,37 % |
| 3 288 (arrêt anticipé) | **8,3609** | **10,5745** | **+30,27 %** |

**+4,68 points de gain, monotone, et la queue s'améliore aussi.**

**Mes questions.**
1. Une amélioration monotone sans coût sur la queue, jusqu'à 3 288 arbres à `lr=0.05` — est-ce
   normal, ou est-ce le signe d'un problème de protocole ? Je m'attendais à un retournement.
2. Le test est un **tiers des stations tiré une fois**. La monotonie pourrait-elle être un
   artefact de ce tirage particulier ? Combien de partitions faudrait-il pour l'établir ?
3. Le nombre 3 288 vient d'un arrêt anticipé réglé sur un **groupe de stations réservé**
   dans l'entraînement. Est-ce le bon dispositif, ou faut-il un arrêt par pli imbriqué ?

---

## Q3 — La validation bloquée spatialement détruit PM2,5. Le contrôle est-il le bon ?

**Le fait.** Protocole : blocs spatiaux par k-moyennes sur coordonnées Lambert-93, puis
**fossé** — toute station à moins de R km d'une station de test sort de l'entraînement. R est
fixé **a priori** par la portée du variogramme des résidus (150 km pour O₃ et PM2,5, 75 pour
NO₂), avant tout score.

| polluant | R | `i % 3` | fossé | témoin : retrait **aléatoire** du même effectif |
|---|---|---|---|---|
| O₃ | 150 km | +28,60 % | +10,46 % | +16,20 % |
| NO₂ | 75 km | +33,45 % | +29,95 % | +31,30 % |
| PM2,5 | 150 km | +28,47 % | **−9,04 %** | +7,29 % |

Sur PM2,5 le fossé écarte **333 stations** de l'entraînement. Le témoin à retrait aléatoire
de même effectif sert à séparer la **famine de données** (21,2 points) de la **fuite spatiale**
(16,3 points).

**Mes questions.**
1. Le témoin à retrait aléatoire de même effectif est-il la bonne décomposition ? Il retire le
   même **nombre** de stations mais pas la même **structure** — les stations retirées au hasard
   sont dispersées, celles du fossé sont concentrées autour du test.
2. Un gain **négatif** (−9 %) signifie que la correction est pire que CAMS brut. Est-ce un
   résultat interprétable, ou le signe que le protocole a dépassé le point où il mesure
   encore quelque chose ?
3. Faut-il publier ce chiffre, ou est-ce qu'un fossé de 150 km sur un réseau français de
   227 stations PM2,5 est simplement une question mal posée ?

---

## Q4 — TROPOMI ne sert à rien. Ai-je mal construit les variables ?

**Le fait.** J'ai extrait Sentinel-5P / TROPOMI aux 476 stations, 2023-08 → 2026-07,
1 093 jours : colonne troposphérique de NO₂ et indice d'aérosols UV, à 0,035° ≈ 3,9 km.
Couverture 84,4 % (34 % au pire jour d'hiver, 100 % en été).

Variables construites : pixel de la station décalé de **J−3** (imposé par la latence du flux
OFFL — médiane 40,4 h, max 61,4 h, mesurée sur 70 granules), moyennes glissantes 3 et 7 jours,
fraîcheur du dernier pixel valide, **couronnes** à 10/25/50/100 km, gradients centre-périphérie,
et une **climatologie** par station × mois calendaire.

Résultat, contre une base de 53 prédicteurs, IC95 par bootstrap de stations :

| jeu | NO₂ `i%n` | NO₂ bloqué | O₃ `i%n` | O₃ bloqué | PM2,5 bloqué |
|---|---|---|---|---|---|
| + pixel J−3 | +0,066 | +0,064 | +0,032 | +0,085 | **−0,175** |
| + pixel + couronnes | +0,153 | −0,032 | +0,086 | +0,033 | −0,027 |
| + climatologie | +0,093 | −0,009 | −0,003 | −0,012 | **−0,249** |
| + tout | +0,218 | +0,047 | +0,114 | +0,015 | **−0,211** |

**Aucune case retenue sur douze.** Seuil de rétention : 2 % du RMSE de base.

**Mes questions.**
1. Est-ce que je construis mal la variable ? Une **colonne troposphérique** n'est pas une
   concentration de surface — faut-il la normaliser par la hauteur de couche limite, ou par
   la colonne modélisée de CAMS, avant de l'utiliser ?
2. Le décalage J−3 est-il ce qui tue le signal ? Le flux temps quasi réel (NRTI, latence
   médiane 0,9 h) permettrait J−1 mais son archive est trouée. Quel ordre de grandeur de
   perte attendre entre J−1 et J−3 pour du NO₂ ?
3. Le seuil de qualité : les valeurs sont quantifiées (33 = nuageux, 73-74 = ciel clair,
   100 = optimal). J'ai retenu ≥ 50. La recommandation ESA « qa > 0,75 » tomberait sur 74 et
   jetterait la moitié des pixels valides. Ai-je raison de m'en écarter ?
4. **Question de fond** : y a-t-il une raison structurelle pour qu'une colonne intégrée
   n'apporte rien quand on dispose déjà de CAMS (qui assimile ces mêmes observations) ?
   Autrement dit, est-ce que je redécouvre que l'information est déjà dans le modèle amont ?

---

## Q5 — Un changement d'étalon métrologique, indécidable. Le protocole tient-il ?

**Le fait.** Le flux national français fait basculer **tout** l'ozone du code de validité 1 au
code 4 le 01/07/2025. Le vocabulaire EIONET donne : `4 — Valid (Ozone only) using CCQM.O3.2019`.
C'est une donnée **valide**, rattachée à un nouvel étalon métrologique.

Question : le changement d'étalon déplace-t-il le niveau ? Première tentative — rapport
obs/CAMS par station, avant contre après — a donné **+17,96 % sur 95 % des stations**, verdict
« marche commune ». **C'était faux** : le rapport obs/CAMS est lui-même saisonnier (0,80 en
novembre, 0,97 en avril), et la période « après » se réduit à **juillet 2026** faute de
prévisions CAMS entre 2025-08 et 2026-06.

Refait en différence de différences, mêmes mois calendaires, **NO₂ comme témoin** (aucun
changement d'étalon) :

```
polluant    NO2     O3   ozone_propre
mois 7    12.19  19.51          7.32
```

**+7,32 points sur un seul mois calendaire.** J'ai codé le verdict en « inconclusif », avec la
décision : agréger les deux périodes **en disant** que la continuité n'a pas pu être vérifiée.

**Mes questions.**
1. Une différence de différences sur **un** mois calendaire et **un** polluant témoin a-t-elle
   la moindre valeur, ou faut-il refuser de la calculer ?
2. Le NO₂ est-il un bon témoin ? Il partage le même modèle CAMS et la même météo, mais sa
   chimie est différente et sa réponse à une année exceptionnelle ne l'est peut-être pas.
3. Quelle serait la bonne façon de trancher, sachant que je n'ai pas de prévisions CAMS sur
   les onze mois qui entourent la bascule ?

---

## Q6 — Le plan d'optimisation hyperparamétrique

**Ce que je fais.** Étude Optuna stockée (SQLite), reprenable, six travailleurs sur l'étude
partagée. Imbrication : un tiers des stations en **test jamais consulté**, deux tiers en
développement avec validation croisée à 3 plis par stations entières. Objectif = RMSE moyen
des plis. Le RMSE du **décile haut** est enregistré à chaque essai et la sélection finale
n'admet que les essais qui ne dégradent pas la queue de plus de 2 %. Élagage médian.
`n_estimators` est **sorti de l'espace de recherche** au profit d'un arrêt anticipé sur un
groupe de stations réservé — pour supprimer son couplage avec le pas d'apprentissage.
Essai zéro amorcé sur le réglage **réellement en production**, pour que la référence ne soit
pas un homme de paille.

**Une contrainte mesurée que je ne sais pas résoudre.** Ce projet a établi qu'**un réglage ne
vaut que pour son axe** : le même jeu d'hyperparamètres donne **+5 points en généralisation
spatiale et −3 en généralisation temporelle**, et un gain de +3,96 pt en temporel se paie
−7,04 en spatial. Le réglage historique est le **pire des six testés** sur l'axe temporel.

**Mes questions.**
1. La contrainte de queue en post-sélection plutôt qu'en objectif multiple — est-ce
   équivalent, ou est-ce que je perds quelque chose ? J'ai choisi ainsi pour garder l'élagage,
   qu'Optuna interdit en multi-objectif.
2. **Comment arbitrer spatial contre temporel ?** L'usage réel est : prédire demain, à une
   station peut-être non instrumentée. Ni `GroupKFold` par stations ni `TimeSeriesSplit` par
   dates ne pose cette question. Faut-il un blocage **simultané** — stations exclues **et**
   derniers mois retirés — et si oui comment éviter que l'échantillon d'évaluation ne devienne
   trop petit pour dire quoi que ce soit ?
3. Six travailleurs TPE avec des graines différentes sur une étude partagée : est-ce que ça
   dégrade la qualité de l'exploration par rapport à un processus séquentiel, et de combien ?
4. Le critère de rétention est **2 % du RMSE de base**, choisi parce que la demi-largeur des
   IC95 par bootstrap de stations vaut de façon stable 1,0 à 1,5 % du RMSE de base sur les
   trois polluants. Est-ce défendable, ou est-ce une rationalisation ?

---

## Q7 — Target encoding et SHAP

**Target encoding.** Je pense que :
- sur `station_id` c'est **structurellement interdit** ici — la moyenne cible d'une station de
  test est inconnue par construction, c'est la définition de « prédire là où rien ne mesure » ;
- que le projet le fait **déjà dans sa forme honnête**, via des retards : observation de J−2,
  erreur moyenne à 3 et 7 jours, écart-type à 7 jours, fraîcheur de la dernière mesure —
  c'est-à-dire un encodage de la station **décalé dans le temps** plutôt qu'une moyenne de
  groupe, et c'est son meilleur levier (+8,9 %) ;
- que sur des catégories transportables (typologie : 15 combinaisons pour 130 000 lignes) un
  encodage hors pli n'apportera presque rien, l'arbre estimant ces moyennes directement ;
- que la seule version qui pourrait payer est l'**interaction** :
  `E[obs − cams | typologie × mois × décile de CAMS]`, que l'arbre doit sinon reconstruire
  par de nombreuses coupures.

**Question : est-ce que je me trompe sur l'un de ces quatre points ?**

**SHAP.** Je calcule des valeurs de Shapley **hors échantillon** (chaque station expliquée par
un modèle qui ne l'a jamais vue), groupées par famille de variables. Groupement par **somme**
dans la famille — pour préserver l'additivité `prédiction = base + Σφ` — et moyenne de |φ| ou
moyenne signée **sur les lignes** pour les deux lectures globales. Le groupement est
obligatoire ici : 30 colonnes de forêt à rayons emboîtés sont quasi parfaitement corrélées, et
Shapley répartit le crédit arbitrairement entre variables corrélées.

**Questions.**
1. Le groupement par somme suffit-il à rendre l'attribution robuste à la corrélation, ou
   la corrélation **entre familles** (paysage et position, par exemple) pose-t-elle le même
   problème d'un cran plus haut ?
2. Pour une association de surveillance, quelle est la présentation la plus utile — et
   surtout, quelle est celle qui induirait en erreur ?

---

## Q8 — La question ouverte

**Où est-ce que je me raconte une histoire ?**

Cette nuit j'ai réfuté trois de mes propres hypothèses par la mesure : que la latitude et la
longitude servaient à « mémoriser un lieu » (non — les retirer dégrade significativement sur
les trois polluants), qu'une climatologie satellitaire pourrait remplacer la position (non),
et qu'un changement d'étalon déplaçait le niveau de l'ozone (indécidable, et mon premier
protocole était faux). J'ai aussi trouvé quatre défauts dans mon propre code, dont un
contrôle de complétude **tautologique** qui passait toujours au vert.

Le taux d'erreur est donc élevé, et il l'était aussi les jours précédents. **Qu'est-ce que ce
taux d'erreur devrait me faire soupçonner sur ce que je n'ai pas encore vérifié ?**
