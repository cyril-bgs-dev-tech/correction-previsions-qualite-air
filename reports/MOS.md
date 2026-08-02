# Correction apprise des prévisions CAMS (MOS) — ozone

Gradient boosting appliqué au **résidu** `observation − CAMS`, sur les prévisions J+1
(échéances 1 à 24 h). Trois mois : janvier, juillet et décembre 2024. 637 494 paires,
286 stations, 52 variables.

Code : `src/aq/models/mos.py`, `scripts/fit_mos.py`.

## Ce que le modèle a le droit de voir

**Uniquement ce qui existe à l'heure où la prévision est publiée** :

- la prévision CAMS elle-même ;
- les variables géographiques et topographiques, statiques par nature ;
- des variables calendaires, connues d'avance.

**Aucune météo.** ERA5 est une *réanalyse* : l'utiliser donnerait au modèle une
connaissance du futur que CAMS n'avait pas, et le gain mesuré ne voudrait rien dire
en exploitation. Ajouter de la météo supposera d'utiliser des *prévisions* météo.

## Le résultat, sous trois validations de dureté croissante

| Validation | Ce qui est caché au modèle | RMSE CAMS | RMSE MOS | Gain | R² CAMS → MOS |
|---|---|---|---|---|---|
| **Spatiale** | stations jamais vues | 17,58 | 12,61 | **+28,3 %** | 0,529 → 0,758 |
| **Temporelle** | mois jamais vu | 19,11 | 15,57 | **+18,5 %** | 0,311 → 0,543 |
| **Double aveugle** | stations **et** mois | 18,39 | 15,97 | **+13,2 %** | 0,332 → 0,496 |

Le gain décroît à mesure que l'épreuve durcit — c'est attendu, et c'est ce qui rend le
chiffre final crédible. **Même en double aveugle**, sur des stations jamais vues et un
mois jamais vu, la correction retire 13 % du RMSE et fait passer le R² de 0,33 à 0,50.

Le biais est également ramené de **+7,17 à −0,08 µg/m³** en validation spatiale.

## Le piège qui a failli produire un faux résultat

La première version apprenait **l'observation** directement plutôt que le résidu. Bilan
apparent : RMSE en baisse de 13 %, R² de 0,529 à 0,645. Résultat publiable, en apparence.

En réalité :

| O₃ observé | n | RMSE CAMS | RMSE MOS (obs. directe) | |
|---|---|---|---|---|
| < 40 | 232 671 | 23,48 | 12,26 | ✅ |
| 40-80 | 294 629 | 10,90 | 15,12 | ❌ |
| 80-120 | 44 617 | 14,87 | 24,34 | ❌ |
| 120-180 | 2 825 | 24,53 | 41,48 | ❌ |
| **> 180** | 15 | 55,94 | **81,41** | ❌ |

**Détection du seuil d'information de 180 µg/m³ : CAMS en trouvait 5 sur 15, la
correction 0 sur 15.** Le modèle était meilleur partout sauf là où il sert.

La cause : 83 % des observations sont sous 80 µg/m³. Minimiser l'erreur quadratique sur
une distribution aussi asymétrique pousse à bien traiter le gros de la masse et à
**écraser la queue** — précisément les épisodes, c'est-à-dire le seul régime qui
déclenche une décision publique.

Apprendre le résidu ancre la prédiction à la physique de CAMS : l'amortissement du
gradient boosting tire alors vers « pas de correction » plutôt que vers la moyenne. La
queue est préservée (RMSE 55,94 → 55,52 au-delà de 180). Figé par le test
`test_la_correction_ne_doit_pas_ecraser_la_queue`.

**Ce que cet épisode enseigne** : un RMSE global ne suffit jamais à juger un modèle de
qualité de l'air. Toute évaluation doit être ventilée par bande de concentration.

## Limites, à énoncer avant qu'on les trouve

- **Trois mois seulement** (janvier, juillet, décembre 2024). Le modèle n'a jamais vu ni
  printemps ni automne.
- **Quinze dépassements du seuil de 180 µg/m³** dans tout l'échantillon. Les chiffres de
  détection (CAMS 5/15, MOS 3/15 avec 5 fausses alertes contre 30) sont trop peu nombreux
  pour conclure. Une évaluation sérieuse des épisodes demande plusieurs étés.
- **Ozone seul** pour l'instant. NO₂ et PM2.5 restent à traiter.
- Les variables calendaires pèsent **25 %** des importances. Avec trois mois, elles
  identifient presque le mois : c'est pour cela que la validation temporelle ci-dessus
  était indispensable, et c'est elle qu'il faut citer, pas la validation spatiale seule.

## Ce que cela permet de dire

La correction ne touche pas au modèle physique : elle apprend la structure de son
erreur, à partir d'informations disponibles au moment de prévoir. C'est cohérent avec le
constat du benchmark — l'erreur de CAMS ne croît quasiment pas avec l'échéance, donc
elle est structurelle et non chaotique, donc apprenable.

Et le levier est celui qui compte : l'ozone pilote l'indice ATMO occitan dans **87,8 %**
des cas.


## Correctif du 29/07 — cibles manquantes écartées de l'entraînement

Le panneau conserve des lignes horaires **sans mesure valide** : 11 % de l'échantillon,
et 49 couples (station, polluant) entièrement vides. Ces cibles NaN étaient transmises au
gradient boosting, qui les absorbait sans se plaindre — et la correction apprise s'en
trouvait amortie.

| | Avant | Après |
|---|---|---|
| RMSE O₃ | 12,96 | **12,61** |
| Biais O₃ | +0,62 | **−0,08** |
| R² O₃ | 0,744 | **0,758** |
| Rappel « Mauvais » | 0,437 | **0,471** |
| Épisodes manqués en moins | 152 | **179** |

L'erreur allait dans le sens **pessimiste** — les chiffres publiés jusque-là sous-estimaient
le gain. C'est précisément ce qui la rendait difficile à voir : rien ne semblait anormal.
Figé par `test_cibles_manquantes_ecartees_de_l_entrainement`.

## La prédiction se vérifie : le gain tient jusqu'à J+3

Le benchmark établissait que l'erreur de CAMS est **structurelle** — elle ne croît pas
avec l'échéance. Cette lecture engageait une prédiction testable : si l'erreur vient du
modèle et non de la divergence chaotique de l'atmosphère, la correction doit tenir aussi
bien à J+3 qu'à J+1.

| Horizon | RMSE CAMS | RMSE corrigé | Gain | Biais corrigé | R² corrigé |
|---|---|---|---|---|---|
| J+1 | 17,58 | **12,61** | +28,3 % | −0,08 | 0,758 |
| J+2 | 17,95 | **12,85** | +28,4 % | −0,17 | 0,749 |
| J+3 | 18,70 | **13,12** | **+29,8 %** | −0,18 | 0,740 |

Le gain ne s'érode pas : il **augmente légèrement**, parce que l'erreur brute de CAMS se
dégrade un peu avec l'horizon tandis que la part corrigeable reste la même. Une erreur
chaotique aurait fait s'effondrer la correction à J+3.

C'est la vérification directe de l'hypothèse qui fonde tout le projet — et elle a une
conséquence opérationnelle : la correction couvre **tout l'horizon réglementaire**, pas
seulement le lendemain.

## ⚠️ Correction du 29/07 — la validation temporelle ne tient pas

Une relecture adverse a relevé que les chiffres de validation temporelle et de double
aveugle n'étaient pas reproductibles depuis le dépôt : ils venaient d'un script de
brouillon. En les réimplémentant proprement (`scripts/valider_mos_aveugle.py`), le
résultat change — et pas dans le bon sens.

| Épreuve | Annoncé | **Mesuré** | Étendue entre plis |
|---|---|---|---|
| spatiale | +26,3 % | **+29,1 %** | +27,0 à +31,4 % (σ 1,8) |
| temporelle | +18,5 % | **+3,4 %** | **−19,0 à +18,3 %** (σ 15,7) |
| double aveugle | +13,2 % | **+1,8 %** | **−19,8 à +17,4 %** (σ 15,3) |

### Pourquoi, pli par pli

| Mois testé | Appris sur | Observé | Gain |
|---|---|---|---|
| Janvier | juillet + décembre | 41,2 | +7,4 % |
| **Juillet** | **janvier + décembre** | **60,0** | **−19,0 %** |
| Décembre | janvier + juillet | 38,1 | +18,3 % |

Le « +18,5 % » annoncé était **un découpage unique et favorable** : décembre testé alors
que janvier — même saison — restait dans l'apprentissage. Quand l'**été** est caché et
que le modèle n'a vu que de l'hiver, la correction fait **19 % pire que CAMS brut**.

### Ce qu'il faut en conclure

- **La généralisation spatiale est solide** (+29,1 %, σ 1,8) : prédire une station jamais
  vue fonctionne. C'est le chiffre à citer.
- **La généralisation temporelle n'est pas démontrée** — elle est réfutée pour le cas
  estival. Le modèle interpole entre régimes vus, il n'extrapole pas.
- Cela rejoint l'ablation, où le calendrier pèse **15,2 %** : ce que le modèle apprend
  est en partie *quelle saison*, pas une correction transférable.
- **Étendre à une année complète n'est pas une amélioration souhaitable mais un
  prérequis** avant tout usage opérationnel.

La correction est consignée plutôt que le chiffre remplacé en silence : une moyenne sans
dispersion cachait un pli à −19 %, et c'est précisément ce que la publication des
étendues sert à empêcher.

## Intervalles de confiance — et pourquoi l'unité de rééchantillonnage décide

| Polluant | Gain | IC 95 % (bootstrap par station) |
|---|---|---|
| O₃ | +28,3 % | **[+24,7 ; +31,7]** — 270 stations |
| NO₂ | +25,0 % | **[+22,5 ; +27,0]** — 342 stations |
| PM2.5 | +19,5 % | **[+16,5 ; +22,4]** — 233 stations |

Le rééchantillonnage porte sur les **stations**, pas sur les lignes. Comparaison sur
l'ozone :

| Bootstrap sur… | IC 95 % | Largeur |
|---|---|---|
| les lignes | [+28,1 ; +28,4] | 0,3 point |
| **les stations** | **[+24,7 ; +31,7]** | **7,0 points** |

Un facteur **23**. Les heures d'une même station sont fortement corrélées : en tirer 24
consécutives revient à compter une seule observation vingt-quatre fois. Le nombre
d'unités effectivement indépendantes est de l'ordre du **nombre de stations** — 270, et
non 577 589 lignes.

Publier l'intervalle par ligne aurait annoncé une précision de ±0,15 point là où elle est
de ±3,5. Figé par `test_bootstrap_par_station_bien_plus_large_que_par_ligne`.

Les trois intervalles restent franchement positifs : **le gain spatial est robuste**, à
la différence du gain temporel réfuté plus haut.

## Vérification : le gain tient-il sur la fenêtre réellement disponible ?

**Le défaut possible.** La prévision CAMS Europe a pour base **00 h UTC** mais n'est mise
à disposition qu'à **06 h 45 UTC** pour les échéances 0-48 h (documentation ADS). Les
échéances 1 à 6 de la fenêtre « J+1 » sont donc **déjà écoulées** quand un prévisionniste
reçoit le fichier : les évaluer revient à créditer le modèle d'heures qu'aucun utilisateur
n'aurait pu exploiter.

**La mesure.**

| Fenêtre d'échéances | n | RMSE CAMS | RMSE corrigé | Gain |
|---|---|---|---|---|
| J+1 complet (1-24 h) | 554 193 | 17,55 | 12,54 | **+28,5 %** |
| Après publication, 06 h 45 (7-24 h) | 409 949 | 17,14 | 12,21 | **+28,8 %** |
| Décision à 9 h locale (9-24 h) | 361 733 | 16,91 | 12,16 | +28,1 % |
| Échéances déjà passées (1-6 h) | 144 244 | 18,66 | 13,45 | +27,9 % |

**Conclusion : le gain ne dépend pas de la fenêtre.** Les quatre valeurs sont
indistinguables à moins d'un point. Le résultat n'est pas un artefact d'heures déjà
écoulées, et il vaut sur la fenêtre opérationnellement exploitable.

Deux remarques quand même. CAMS est **un peu moins bon sur les premières heures**
(RMSE 18,66 contre 16,91 en fin de fenêtre), ce qui est contre-intuitif pour une prévision
— l'écart tient probablement au cycle nocturne de l'ozone, mal reproduit sous inversion.
Et le fait de devoir vérifier ce point rappelle une règle générale : **une évaluation doit
préciser le run, l'échéance et l'heure de mise à disposition**, faute de quoi elle mesure
une capacité que personne ne peut utiliser.

---

## ✅ La validation temporelle passe — l'archive étendue à sept mois

La correction annoncée plus haut — validation temporelle réfutée, un pli à −19 % — est
elle-même dépassée. En portant l'échantillon de **trois à sept mois** de 2024 :

| Épreuve | 3 mois | **7 mois** |
|---|---|---|
| Spatiale | +29,1 % · σ 1,8 | **+24,6 %** · σ 1,8 |
| **Temporelle** | +3,4 % · **−19,0 à +18,3** · σ 15,7 | **+15,5 %** · **+5,4 à +23,6** · σ **5,8** |
| **Double aveugle** | +1,8 % · **−19,8 à +17,4** · σ 15,3 | **+11,0 %** · **+0,5 à +22,9** · σ 6,8 |

**Aucun pli n'est plus négatif.** Le pire passe de −19,0 % à **+5,4 %** en temporel, et de
−19,8 % à **+0,5 %** en double aveugle. La dispersion est divisée par près de trois.

### Ce que cela établit

Le −19 % initial venait d'un **domaine hors apprentissage**, pas d'une limite intrinsèque
de l'ozone : avec trois mois dont un seul été, cacher juillet privait le modèle de tout
régime estival. Avec sept mois, il a vu assez de régimes pour extrapoler.

**La généralisation temporelle est donc démontrée**, ce qui était la faiblesse la plus
citable du projet.

### Ce qui baisse, et pourquoi c'est normal

Le gain global passe de 28,3 % à **24,2 %**, et le gain spatial de 29,1 % à 24,6 %.
L'échantillon couvre désormais des conditions plus variées — printemps, automne, régimes
de transition — donc plus difficiles. **Un chiffre plus bas sur un échantillon plus
représentatif vaut mieux qu'un chiffre élevé sur trois mois choisis.**

C'est le chiffre à citer. *(Corrigé une troisième fois ci-dessous — voir « 17 mois ».)*

## Correctif du 29/07 — 17 mois au lieu de 11 : le gain descend à +19,2 %

**Un tiers du jeu d'entraînement manquait.** Le chargement déduisait la fenêtre
d'observations du **nom** des fichiers de prévision, par une expression ancrée à droite.
Sur les six fichiers groupés `..._202308_202309.parquet`, seul le second mois était
retenu ; août, octobre, février, avril, août et octobre disparaissaient au recollement.
**2,09 M de paires au lieu de 3,23 M**, sans qu'aucune erreur ne soit levée.

Le défaut a été trouvé par une conséquence indirecte : une courbe d'apprentissage qui
s'arrêtait à trois points au lieu de six. Corrigé aux deux endroits où le motif
apparaissait, figé par `test_fenetres_temporelles.py`, et le chargement annonce désormais
sa couverture — *« N mois appariés sur M prévus »*, avec le nom des manquants.

Ozone J+1, **3 562 416 paires · 286 stations · 17 mois**, stations entièrement exclues :

| | Avant (11 mois) | **Après (17 mois)** |
|---|---|---|
| RMSE CAMS | 17,10 | 16,97 |
| RMSE MOS | 12,96 | **13,71** |
| R² MOS | 0,762 | **0,728** |
| Biais MOS | +0,62 | **−0,06** |
| **Gain** | +24,2 % | **+19,2 %** |

**Le gain baisse pour la troisième fois, et pour la troisième fois c'est la bonne
nouvelle.** Les six mois récupérés sont ceux qui manquaient au cycle : ils apportent des
régimes que le modèle ne voyait pas, et le chiffre honnête est plus bas. La progression
28,3 → 24,2 → **19,2** mesure surtout la représentativité croissante de l'échantillon.

**+19,2 % est le chiffre à citer.**

### Ce que révèle la ventilation par bande, une fois l'année complète

| Bande | n | RMSE CAMS | RMSE MOS | |
|---|---|---|---|---|
| 0-40 | 960 595 | 25,09 | **16,45** | mieux |
| 40-80 | 1 777 231 | 11,15 | 11,57 | **pire** |
| 80-120 | 456 594 | 13,30 | 14,32 | **pire** |
| 120-180 | 22 064 | 24,07 | **23,07** | mieux |
| ≥180 | 57 | 56,39 | 56,61 | **pire** |

Presque tout le gain vient de la **bande basse** : CAMS y surestime massivement
(RMSE 25,09 pour des valeurs sous 40 µg/m³), et la correction du biais de +6,01 à −0,06
efface cette erreur. Sur les bandes moyennes, la correction **dégrade légèrement**.

Ce profil n'apparaissait pas sur 11 mois. Il confirme que le RMSE global est le mauvais
juge unique — et il renforce la pertinence de la perte pondérée mesurée dans
`PRESERVER_LA_QUEUE.md` : −6,8 points de gain global pour +13,4 points sur la queue est
un arbitrage qui, à la lumière de ce tableau, **doit être intégré à la production**, pas
laissé en variante.

### Le NO₂ sur la même fenêtre : +20,0 %

**4 571 352 paires · 367 stations · 17 mois.**

| | RMSE | MAE | Biais | R² |
|---|---|---|---|---|
| CAMS brut | 12,87 | 7,78 | **−5,83** | +0,125 |
| **MOS corrigé** | **10,30** | 6,89 | +0,28 | **+0,439** |

**Le biais de CAMS est ici négatif** — le modèle *sous-estime* le NO₂ de 5,8 µg/m³, là où
il *surestime* l'ozone de 6,0. C'est cohérent avec la physique : le NO₂ est une émission
locale que la maille de 8 km dilue, tandis que l'ozone se forme à l'échelle régionale et
se détruit près des sources, que le modèle ne résout pas.

| Bande | n | RMSE CAMS | RMSE MOS | |
|---|---|---|---|---|
| 0-20 | 3 068 052 | 5,65 | 6,74 | **pire** |
| 20-40 | 661 759 | 18,42 | **11,90** | mieux |
| 40-90 | 225 826 | 36,89 | **27,30** | mieux |
| 90-200 | 5 008 | 77,57 | **63,76** | mieux |
| ≥200 | 3 | 258,03 | **245,15** | mieux |

**Le profil est l'inverse de celui de l'ozone**, et il est bien plus favorable : la
correction gagne sur **toutes les bandes hautes**, y compris au-delà de 90 µg/m³ où elle
retire 14 µg/m³ d'erreur. Elle ne dégrade que la bande la plus basse, celle où une erreur
n'a aucune conséquence.

C'est le polluant sur lequel la correction est la plus défendable devant une AASQA — et
c'est aussi celui où la hiérarchie routière apportait le plus (`TRAFIC_POPULATION.md`).

### Les PM2,5 : +18,1 %, et le seul profil sans contrepartie

**3 001 896 paires · 241 stations · 17 mois.**

| | RMSE | Biais | R² |
|---|---|---|---|
| CAMS brut | 5,86 | +0,05 | +0,299 |
| **MOS corrigé** | **4,80** | +0,01 | **+0,530** |

| Bande | n | RMSE CAMS | RMSE MOS | |
|---|---|---|---|---|
| 0-10 | 1 964 272 | 3,59 | **2,86** | mieux |
| 10-20 | 506 995 | 6,27 | **4,82** | mieux |
| 20-25 | 63 908 | 9,89 | **8,26** | mieux |
| 25-50 | 70 032 | 17,10 | **14,07** | mieux |
| **≥50** | 6 007 | 54,42 | **47,90** | mieux |

**Aucune bande dégradée** — le seul des trois polluants dans ce cas. Et le biais de CAMS
y était déjà nul (+0,05) : le gain ne vient donc pas d'un recentrage mais d'une véritable
réduction de la dispersion, ce que le R² confirme (0,299 → 0,530).

### Les trois polluants sur la même fenêtre

| Polluant | n paires | Stations | RMSE CAMS → MOS | Gain | R² |
|---|---|---|---|---|---|
| O₃ | 3 562 416 | 286 | 16,97 → 13,71 | **+19,2 %** | 0,584 → 0,728 |
| NO₂ | 4 571 352 | 367 | 12,87 → 10,30 | **+20,0 %** | 0,125 → 0,439 |
| PM2,5 | 3 001 896 | 241 | 5,86 → 4,80 | **+18,1 %** | 0,299 → 0,530 |

**Une cohérence à 18-20 % sur trois polluants aux physiques différentes** est un argument
plus fort que les chiffres dispersés de 20,9 à 24,2 % mesurés sur sept mois. Le resserrement
n'est pas un hasard : il vient de ce que l'échantillon couvre maintenant tous les régimes,
et non une sélection de mois.

**Mais les profils par bande diffèrent radicalement, et c'est ce qu'il faut dire :**

| Polluant | Où la correction gagne | Où elle perd |
|---|---|---|
| O₃ | la bande basse, massivement (25,09 → 16,45) | **les bandes moyennes et la queue** |
| NO₂ | **toutes les bandes hautes**, jusqu'à −14 µg/m³ au-delà de 90 | la bande la plus basse seulement |
| PM2,5 | **toutes les bandes** | aucune |

Le gain global, presque identique, recouvre trois comportements distincts. Sur l'ozone il
faut annoncer la contrepartie ; sur le NO₂ et les PM2,5 il n'y en a pratiquement pas.

### La saisonnalité domine désormais les variables utilisées

| Variable | Part |
|---|---|
| `jour_annee_cos` | **17,4 %** |
| `jour_annee_sin` | **13,5 %** |
| `jour_semaine` | 6,7 % |
| `cams` | 6,6 % |
| `lat_wgs84` | 5,8 % |

Les deux harmoniques annuelles pèsent **31 % à elles seules**. Avec un cycle complet dans
l'échantillon, ce que le modèle apprend d'abord est la **forme saisonnière du biais de
CAMS** — ce qui explique directement pourquoi la courbe d'apprentissage ne décolle qu'au
sixième mois (voir `COURBE_APPRENTISSAGE.md`).

### La cause de tout cela

L'archive CAMS Europe couvre **trois ans**, pas trois mois. Ma limite était
**auto-imposée** — et masquée par un bug qui faisait échouer toutes les requêtes portant
sur un mois de moins de 31 jours, ce que j'attribuais à une panne du service. Une fois
corrigé : **neuf requêtes en vingt minutes**.

La leçon n'est pas sur les données, elle est sur le diagnostic : **j'ai accepté « le
service est en panne » comme explication pendant des heures sans la tester**, alors que la
vérification prenait trente secondes.
