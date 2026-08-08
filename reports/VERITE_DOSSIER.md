# La vérité du dossier — chiffres gelés

*Généré le 08/08/2026 à 23 h 39 par `scripts/verite_dossier.py`. **Toute figure, slide ou phrase du dossier doit dériver de ce document.** Un chiffre qui n'y figure pas est à retirer ou à re-mesurer — les fenêtres de 11 et 17 mois citées ailleurs sont périmées.*

## 0. Le chiffre de déploiement — station **et** mois cachés ensemble

Tous les chiffres de ce document portent sur l'axe **spatial** : stations exclues, dates connues. Ce n'est pas la condition d'un déploiement, qui demande de prédire **demain**, à un endroit **pas vu**. Le tableau ci-dessous cache les deux à la fois.

| polluant | spatial | temporel | **double aveugle** | σ | pire pli |
|---|---|---|---|---|---|
| **NO₂** | +31.57 % | +45.94 % | **+25.71 %** | 5.0 | +15.5 |
| PM10 | +27.94 % | +19.09 % | **+11.36 %** | 9.7 | -8.5 |
| PM2,5 | +25.63 % | +12.65 % | **+5.14 %** | 12.2 | -18.0 |
| O₃ | +24.10 % | +9.38 % | **+3.31 %** | 13.3 | -35.0 |

**Un seul polluant sur quatre généralise en conditions de déploiement**, et c'est celui dont le résidu est **attaché au site** : un décalage de lieu se transporte d'un mois à l'autre sans rien réapprendre, ce que la typologie de station confirme par ailleurs. Les trois autres — O₃, PM2,5, PM10 — se groupent entre +3 et +7,5 % avec un écart-type de 12 à 15. Leur ordre va dans le sens d'une composante locale décroissante, mais **l'écart total est trois fois plus petit que leur dispersion** : ne pas conclure dessus.

⚠️ **Et la capacité du modèle dégrade cet axe.** Sur l'ozone, quatre configurations, du réglage de production au meilleur candidat d'une étude Optuna de 201 essais : +3,31 % à 400 arbres, +0,46 % à 900, +0,11 % à 3 700, **−1,07 %** à 3 000 mal régularisés. Aucun réglage ne bat la production sur l'axe qui compte, et un réglage optimisé sur la validation **spatiale** est suspect par construction.

> **Formulation défendable** : « +24,1 % en validation spatiale sur l'ozone ; **+3,3 % quand la station et le mois sont cachés ensemble**, ce qui est la condition de déploiement. Sur le NO₂ les deux chiffres sont +31,6 % et **+25,7 %**. »

## 1. France, 18 janvier – 31 décembre 2024 — contre le produit officiel

**Périmètre : usage A — aux stations instrumentées, axe spatial.** Les prédicteurs comprennent les observations passées de la station, qui n'existent pas là où rien ne mesure. Pour l'usage B, voir § 7 ; pour l'axe de déploiement, voir § 0.

Comparaison à `cams-europe-air-quality-forecasts-optimised-at-observation-sites`, sur les **mêmes** stations et les **mêmes** jours. RMSE en µg/m³.

⚠️ **La fenêtre n'est pas l'année civile** : le produit officiel ne commence qu'au **18/01/2024** — vérifié dans les archives, pas déduit du catalogue. Écrire « année 2024 complète » est faux.

| polluant | grain | n | CAMS brut | MOS officiel | nous |
|---|---|---|---|---|---|
| O₃ | horaire | 2,698,299 | 17.72 | 14.96 (+15.6 %) | 14.29 (+19.4 %) |
| O₃ | **max glissant 8 h** | 110,747 | 12.53 | 12.84 (-2.5 %) | 10.04 (+19.9 %) |
| NO₂ | horaire | 1,481,913 | 8.44 | 6.93 (+17.8 %) | 8.03 (+4.8 %) |
| NO₂ | **max horaire** | 58,231 | 15.47 | 12.16 (+21.4 %) | 10.63 (+31.3 %) |
| PM2,5 | horaire | 809,770 | 5.80 | 5.25 (+9.6 %) | 4.75 (+18.1 %) |
| PM2,5 | **moyenne journalière** | 32,124 | 4.18 | 3.44 (+17.8 %) | 3.05 (+26.9 %) |

Le grain marqué en gras est celui sur lequel porte le **seuil réglementaire** du polluant.

## 2. Ozone — la moyenne annuelle masque un changement de signe

La fenêtre d'évaluation de l'ozone au référentiel LCSQA est **avril-septembre**. Sur cette fenêtre, le produit officiel se comporte à l'inverse de sa moyenne annuelle.

| fenêtre | n | CAMS brut | MOS officiel | nous |
|---|---|---|---|---|
| année entière | 110,747 | 12.53 | 12.84 (-2.5 %) | 10.04 (+19.9 %) |
| **saison ozone, avril-septembre** | 56,077 | 11.17 | 13.31 (-19.2 %) | 9.84 (+11.9 %) |
| hors saison, octobre-mars | 54,670 | 13.79 | 12.35 (+10.4 %) | 10.23 (+25.8 %) |

Le produit officiel dégrade le brut **12 mois sur 12**, au pire en 04/2025 (-55.0 %). Son biais est négatif chaque mois — il sous-estime, ce qui pénalise mécaniquement un maximum.

**Et la même lecture nous vise** : notre avantage est le plus faible précisément en saison. Citer notre gain annuel sans cette ventilation reproduirait l'erreur que nous reprochons à la moyenne annuelle du produit officiel.

## 3. Hors fenêtre d'apprentissage — Occitanie, 1ᵉʳ semestre 2025

Modèle appris jusqu'au **31/12/2024**, appliqué à une période qu'il n'a jamais vue. 3,353 jours-station · 21 stations occitanes · **163 dépassements** observés de 120 µg/m³.

C'est le seul test sans fuite possible — ni de station, ni de période. Son effectif est petit : un écart faible n'y serait pas concluant.

| produit | seuil de décision | POD | FAR | CSI |
|---|---|---|---|---|
| CAMS brut | 120 (réglementaire) | 0.331 | 0.069 | 0.323 |
| MOS officiel | 120 (réglementaire) | 0.460 | 0.312 | 0.381 |
| NOTRE correction | 120 (réglementaire) | 0.239 | 0.049 | 0.236 |
| | | | | |
| CAMS brut | **113.5** (calibré sur 2024) | 0.515 | 0.229 | 0.447 |
| MOS officiel | **105.9** (calibré sur 2024) | 0.718 | 0.543 | 0.387 |
| NOTRE correction | **111.7** (calibré sur 2024) | 0.571 | 0.212 | 0.495 |

Le seuil est cherché sur 2024 puis appliqué à 2025 **sans réajustement**, pour les trois produits également. Au seuil réglementaire brut, notre POD tombe à 0,239 : c'est un **artefact de calibration**, pas une incapacité — la régression écrase les extrêmes, l'ordre des jours est conservé mais le franchissement du seuil se perd.


### Ce que cet échantillon autorise à dire

21 stations et 163 dépassements, avec des jours corrélés au sein d'une station et d'une région : les écarts ci-dessus n'ont de sens qu'assortis d'un intervalle. Bootstrap apparié par blocs sur les **deux** axes — stations et blocs calendaires — à **trois** longueurs de bloc (3, 7 et 14 jours), 2 000 tirages. Une conclusion qui ne survivrait qu'à une longueur serait un artefact du découpage.

| comparaison | écart | IC95 (blocs de 7 j) | verdict |
|---|---|---|---|
| RMSE : nous − CAMS brut | -0.710 | [-1.645 ; +0.129] | non concluant |
| RMSE : nous − MOS officiel | -3.224 | [-4.867 ; -1.744] | **concluant** aux 3 longueurs |
| CSI : nous − CAMS brut | +0.048 | [-0.051 ; +0.144] | non concluant |
| CSI : nous − MOS officiel | +0.107 | [-0.087 ; +0.278] | non concluant |
| POD : nous − CAMS brut | +0.055 | [-0.045 ; +0.181] | non concluant |
| POD : nous − MOS officiel | -0.147 | [-0.320 ; +0.045] | instable (1/3) — descriptif |

**Une seule comparaison survit** : notre RMSE est inférieur à celui du MOS officiel de **3,22 µg/m³**, IC95 [−4,87 ; −1,74], aux trois longueurs de bloc.

Tout le reste est **descriptif**, et cela coupe dans les deux sens : notre avantage en CSI (+0,107) n'est pas démontré, mais l'avantage du produit officiel en POD (−0,147 pour nous) ne l'est pas davantage, et notre avance sur le CAMS brut en 2025 (−0,71 µg/m³) non plus.

⚠️ **Formulation imposée pour ce bloc** : « sur cet échantillon, les estimations ponctuelles indiquent… ». Ne jamais écrire que nous détectons mieux que le produit officiel en 2025 — l'intervalle ne le permet pas. Le seul énoncé ferme est celui du RMSE.

## 4. L'expérience contrôlée — seule la cible change

Les blocs précédents comparent deux **produits** qui diffèrent par le grain, les variables, l'historique et l'algorithme à la fois : ils établissent une association, pas un effet. L'expérience ci-dessous ne fait varier que la **cible d'apprentissage** — même modèle, mêmes lignes, mêmes plis par stations exclues, mêmes prédicteurs.

| polluant | grain réglementaire | horaire corrigé puis agrégé | cible directe | écart |
|---|---|---|---|---|
| O₃ | max glissant 8 h (**maximum**) | +17.50 % | +23.30 % | **+5.8 pts** |
| NO₂ | max horaire (**maximum**) | +25.56 % | +32.11 % | **+6.5 pts** |
| PM2,5 | moyenne journalière (**moyenne**) | +27.60 % | +26.11 % | **-1.5 pts** |

**Le signe s'inverse sur PM2,5**, et c'est ce qui distingue cette mesure d'une corrélation. Le mécanisme invoqué est qu'une correction horaire réduit la variabilité : cela pénalise une **statistique d'ordre** — un maximum — mais pas une **tendance centrale**. PM2,5 est le seul des trois dont le grain réglementaire est une moyenne. Le mécanisme prédit qu'il n'y gagne rien ; il n'y gagne rien.

### Antériorité — à citer, pas à revendiquer

Bertrand, Meleux, Ung, Descombes & Colette (2023), *Technical note: Improving the European air quality forecast of CAMS using machine learning techniques*, ACP 23, 5317 ([doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)) — **l'article qui décrit le produit officiel, écrit par ses auteurs** — rapporte **20,5 %** de gain en agrégeant une correction horaire contre **32,8 %** en apprenant directement le maximum journalier, et recommande explicitement « *using daily MOS instead of hourly MOS if performances must be optimized for the daily max statistics* ». Il couvre les quatre polluants, cibles en moyenne journalière comprises.

Le tableau ci-dessus est donc une **réplication indépendante** — autre algorithme (boosting contre forêt aléatoire), autre période, autre domaine — et non une découverte. Ne jamais présenter l'effet de grain comme un résultat propre au projet.

**Ce qui reste propre au projet**, une fois Bertrand retiré :

1. la mesure de ce que le produit **réellement distribué** délivre sur le grain réglementaire, par opposition à ce que son article établit comme possible ;
2. le **renversement saisonnier** du bloc 2, qu'une moyenne annuelle annule ;
3. le test **hors fenêtre 2025** avec seuils recalibrés à l'identique.

C'est un travail de vérification et de caractérisation opérationnelle. C'est moins qu'une découverte, et c'est exactement le geste attendu d'un service : mesurer ce qu'un produit rend sur le grain qui décide, et dire s'il faut le brancher.

## 5. Conformité FAIRMODE

MQI au sens de JRC120649 v3.2 (DOI 10.2760/30226), formule `RMSE / (β · RMS_U)`, β = 2, conformité à **MQI ≤ 1**. Le temps d'agrégation est celui que le tableau 6 impose **par polluant** — et non l'horaire pour les trois, comme le dossier le faisait auparavant.

| polluant | grain imposé | n | MQI CAMS brut | MQI correction | *(MQI horaire, hors cadre)* |
|---|---|---|---|---|---|
| O₃ | max journalier 8 h | 134,423 | 0.309 | **0.255** | 0.464 / 0.375 |
| NO₂ | horaire | 3,986,229 | 0.606 | **0.485** | 0.606 / 0.485 |
| PM2,5 | moyenne journalière | 109,803 | 0.488 | **0.354** | 0.651 / 0.533 |

Les six valeurs agrégées sont conformes, avec une marge large. **Aucun produit ne change de côté du seuil** entre les deux grains : l'énoncé de conformité déjà publié tenait, seul le chiffre cité était le mauvais.

⚠️ **Mais l'agrégat masque une non-conformité sur le NO₂.** Station par station (842 couples mesurés) : **100 %** des stations conformes en O₃ et en PM2,5, mais **98,5 %** seulement en NO₂ — pire MQI **1,24**, et 95 % de conformité sur les stations **trafic**. Le MQI national ne doit donc pas être cité comme une conformité station par station pour le NO₂ ; c'est exactement la compensation entre cas faciles et difficiles qu'un agrégat peut cacher.

Le MQI horaire était **pessimiste** — l'agrégation journalière réduit la variance de l'erreur davantage que celle de l'incertitude de mesure, qui dépend surtout du niveau observé. L'erreur jouait donc contre nous, ce qui explique qu'elle n'ait rien déclenché. Elle rendait néanmoins l'énoncé infondé, et un jury FAIRMODE l'aurait vue.

**Deux paramètres à connaître si la question vient** : l'α de PM2,5 vaut **0,30** et celui de PM10 **0,13** — les intervertir sur-estime le MQI de PM2,5 de 2 à 20 %, et c'est une erreur qui a été commise dans ce projet puis corrigée. La v4.0 du référentiel (mai 2026) refond les β par polluant ; les chiffres ci-dessus sont en **v3.2**, et le dossier le dit plutôt que de laisser deviner.

## 6. Le plafond de la météo — ce que le modèle se refuse

Le modèle évalué dans tout ce document n'utilise **aucune variable météorologique** : ses 53 prédicteurs sont tous disponibles à l'heure d'émission. Le tableau ci-dessous mesure ce que coûte ce choix, en ajoutant les variables ERA5 au même protocole — mêmes plis par stations exclues, mêmes hyperparamètres.

| polluant | RMSE base | gain | relatif | IC95 (bootstrap de stations) | décile haut |
|---|---|---|---|---|---|
| O₃ | 8.806 | **+0.699** | **+7.9 %** | [+0.597 ; +0.807] | -0.54 *(meilleur)* |
| NO₂ | 15.402 | **+0.614** | **+4.0 %** | [+0.434 ; +0.828] | -1.65 *(meilleur)* |
| PM2,5 | 3.074 | **+0.155** | **+5.0 %** | [+0.097 ; +0.204] | -0.41 *(meilleur)* |

Les trois intervalles sont strictement positifs et **le décile haut s'améliore partout** : il n'y a pas d'arbitrage entre erreur moyenne et épisodes, ce qui est rare dans ce projet.

⚠️ **C'est un plafond, jamais un gain.** ERA5 est une **réanalyse** : elle n'existe pas à l'heure d'émission. Une chaîne opérationnelle emploierait les prévisions IFS et en récupérerait une part inconnue, décroissante avec l'échéance. Ne jamais citer ces chiffres comme une performance du modèle — ils mesurent ce dont il se prive pour rester opérationnellement propre.

### Un défaut de notre propre critère d'arrêt

Le critère du projet — « retenir si le gain atteint **0,3 µg/m³** » — est en unités **absolues**, appliqué à des polluants dont le RMSE varie d'un facteur 5. Pour PM2,5 (RMSE ≈ 3) ce seuil vaut 10 % ; pour NO₂ (RMSE ≈ 15) il vaut 2 %. Il **écarte** donc PM2,5 à +6,7 % relatifs tout en **retenant** NO₂ à +2,7 %.

Ce n'est pas un arbitrage scientifique, c'est un artefact d'unité. Le critère doit devenir relatif, ou être fixé par polluant. Le défaut n'est apparu que parce que la mesure a porté sur les trois polluants à la fois.

## 7. Deux périmètres, et il ne faut jamais citer l'un pour l'autre

Une observation passée n'existe **qu'aux stations instrumentées**. L'ajouter aux prédicteurs scinde le projet en deux usages qui n'ont ni les mêmes entrées ni la même revendication.

| usage | entrées | ce qu'on peut prétendre |
|---|---|---|
| **A — corriger aux stations** | + observations à J−2 | comparable au MOS officiel **sur son terrain**, qui les utilise aussi |
| **B — prédire là où rien ne mesure** | sans | **la seule revendication propre du projet** |

Règle de disponibilité retenue, volontairement conservatrice : **rien de plus récent que la fin de J−2**, soit au moins 24 h de marge sur l'heure d'émission. Plus strict que le produit officiel ; si le gain existe sous cette contrainte, il existe *a fortiori* sous une règle plus permissive. Couverture **97,7 à 98,5 %**, fraîcheur médiane 2 jours.

| polluant | usage B (sans) | usage A (avec) | gain | relatif | IC95 | décile haut |
|---|---|---|---|---|---|---|
| O₃ | 8.758 | **7.949** | +0.809 | **+9.2 %** | [+0.646 ; +1.017] | -1.10 |
| NO₂ | 15.370 | **11.871** | +3.498 | **+22.8 %** | [+3.038 ; +4.037] | -6.00 |
| PM2,5 | 3.089 | **2.802** | +0.287 | **+9.3 %** | [+0.227 ; +0.343] | -0.47 |

Les trois intervalles sont strictement positifs et **le décile haut s'améliore partout**. Sur le NO₂ le gain atteint **+21,9 %**, et la queue s'améliore de 5,5 µg/m³ — cohérent avec un polluant dominé par des sources très locales que CAMS résout mal à 8 × 11 km.

**C'est le plus fort levier mesuré du projet, et le seul qui soit déployable** : il ne demande aucune réanalyse, aucun téléchargement, et le MOS officiel de Copernicus s'en sert déjà — sa documentation le dit.

### L'erreur de raisonnement que cela corrige

Le projet excluait les observations récentes **au même titre** que la météo de réanalyse. Ce n'est pas le même argument : ERA5 décrit le présent depuis le futur, la mesure d'avant-hier est publiée. Une prudence appliquée par **analogie** plutôt que par examen a coûté ce levier pendant tout le projet — et elle ne levait aucune erreur, une entrée exclue à tort étant invisible.

### Ce que cela répare dans la comparaison au produit officiel

Elle était **asymétrique dans les deux sens** : à notre avantage sur le grain — nous apprenons la grandeur réglementaire, eux l'horaire — et à notre désavantage sur les entrées, puisqu'ils avaient les observations récentes et nous pas. L'usage A permet enfin la comparaison à armes égales.

## 7 ter. Les cinq familles de gains — laquelle citer, et jamais l'une pour l'autre

Ce projet produit **cinq familles de scores** qui portent des noms voisins et répondent à des questions différentes. Elles sont **toutes justes et aucune n'est interchangeable** : sur l'ozone, la même correction vaut de **+3,31 % à +22,47 %** selon l'épreuve. Confondre deux lignes de ce tableau discrédite le dossier entier plus sûrement qu'un chiffre faux — un chiffre faux se corrige, une confusion de périmètre jette le doute sur tout le reste.

**Tout pourcentage cité hors de ce document doit venir avec trois mots : périmètre · épreuve · échéance.**

| # | famille | épreuve | échéance | O₃ | NO₂ | PM10 | PM2,5 |
|---|---|---|---|---|---|---|---|
| ①a | **production, contre la chaîne en service** ⭐ | origine glissante, station **connue** | **J0** | **+22,43 %** | **+44,16 %** | **+25,90 %** | **+19,22 %** |
| ①b | production, contre CAMS brut | idem | J0 | +26,15 % | +51,24 % | +31,09 % | +19,22 % |
| ② | **maximale — AUX STATIONS** | double aveugle, pile complète **+ veille** | J+2 | +22,47 % | +46,20 % | +24,22 % | +19,68 % |
| ③ | **maximale — PARTOUT** ⭐ | double aveugle, **sans** la veille | J+2 | **+15,83 %** | **+38,86 %** | **+17,88 %** | **+10,03 %** |
| ④ | apport de la seule observation de la veille (§ 7) | usage A contre usage B | J+2 | +9,24 % | +22,76 % | — | +9,28 % |
| ⑤ | double aveugle de référence | base seule, **aucun levier** | J+2 | +3,31 % | +25,71 % | +11,36 % | +5,14 % |

**Les corpus ne coïncident pas** — **O₃** : ① 2025-01→2026-07, ②③ 2023-08→2025-12 (29 mois), ⑤ 17 plis · **NO₂** : ① 2025-01→2026-07, ②③ 2023-08→2025-12 (29 mois), ⑤ 17 plis · **PM10** : ① 2025-01→2026-07, ②③ 2024-01→2025-12 (24 mois), ⑤ 30 plis · **PM2,5** : ① 2025-01→2026-07, ②③ 2023-08→2025-12 (29 mois), ⑤ 17 plis. Les niveaux ne se comparent donc pas d'une ligne à l'autre ; seuls les écarts **internes à une même ligne** le peuvent.

### Comment les lire sans se tromper

- **① n'est comparable à aucune des autres.** Il est mesuré à **J0** et la station évaluée est **connue du modèle**. C'est l'usage « exploitation sur un réseau existant », pas une mesure de généralisation. Ne jamais l'opposer à un double aveugle.
- **③ est la seule revendication propre du projet** — prédire là où rien ne mesure. C'est le chiffre à mettre en avant, et **c'est le plus bas** : c'est précisément ce qui le rend crédible.
- **② − ③ mesure l'apport de la veille**, et ce faisant **change de périmètre**. ④ mesure la même chose sur un autre corpus : les deux se recoupent, ils ne s'additionnent pas.
- **⑤ → ③ est la démonstration de la méthode** : ce que la pile complète ajoute à une base sans levier, à protocole d'épreuve identique. La comparaison est **indicative, pas rigoureuse** — les deux lignes n'ont ni le même corpus ni le même nombre de plis. La comparaison **rigoureuse** est interne à ③ : la ligne « base » de `methode_maximale_<P>_h2.csv`, mesurée sur exactement les mêmes plis que le total.

### Les échéances ne sont pas les mêmes partout

`methode_maximale` est à **J+2** ; `detection_maximale`, `episodes_reels` et `agregation_zone` sont à **J0** (`horizon=1`) ; les bancs FAIRMODE et LCSQA à **J+1** ; les pages HTML de production à **J0**. Un jury demandera « à quelle échéance ? » et la réponse **change selon le tableau montré**. Le rassurant est mesuré — moins d'un point d'écart entre J0, J+1 et J+2 — mais cela **se dit**, jamais ne se laisse découvrir.

## 7 quater. Année par année, contre **deux dénominateurs** — la table de la page 04

**Périmètre : PARTOUT** — aucune observation passée de la station n'entre dans le modèle, donc ces chiffres valent *là où rien ne mesure*. Épreuve : **double aveugle**, station et mois cachés ensemble. Échéance **J+1** (tranche 25-48 h d'une sortie 00 UTC). Ces trois mots ne s'omettent pas : ils ne sont **pas** ceux du § 12 ni ceux du § 14.

Deux références, parce qu'elles répondent à deux questions. **Contre CAMS brut** pour *ordonner* les systèmes — dénominateur commun, mais personne n'exploite CAMS brut en l'état. **Contre la chaîne en service** pour *citer* un chiffre — le krigeage du biais récent dans ses **réglages usuels**, ce qu'une AASQA fait tourner. La dernière colonne oppose la **même méthode réglée au mieux**, adversaire plus dur.

| polluant | fenêtre | n | CAMS brut | chaîne en service | nous | /CAMS | **/service** | /service réglé |
|---|---|---|---|---|---|---|---|---|
| O₃ | 2023 | 10,554 | 11.11 | 14.78 | 10.76 | +3.19 % | +27.24 % | +26.84 % |
| O₃ | 2024 | 31,681 | 12.16 | 13.85 | 10.76 | +11.53 % | +22.29 % | +19.64 % |
| O₃ | 2025 | 27,649 | 13.03 | 14.99 | 11.39 | +12.59 % | +24.00 % | +20.50 % |
| O₃ | 2026 | 17,911 | 13.70 | 14.24 | 11.65 | +14.99 % | +18.21 % | +14.98 % |
| **O₃** | **toutes** | 87,795 | 12.65 | 14.41 | 11.14 | +11.88 % | **+22.64 %** | +19.90 % |
| NO₂ | 2023 | 13,193 | 24.59 | 22.71 | 15.54 | +36.82 % | +31.60 % | +15.90 % |
| NO₂ | 2024 | 39,151 | 21.74 | 21.21 | 13.62 | +37.34 % | +35.77 % | +20.67 % |
| NO₂ | 2025 | 35,248 | 23.29 | 22.48 | 14.59 | +37.33 % | +35.08 % | +21.74 % |
| NO₂ | 2026 | 22,043 | 23.21 | 20.52 | 14.12 | +39.16 % | +31.22 % | +15.90 % |
| **NO₂** | **toutes** | 109,635 | 22.90 | 21.68 | 14.28 | +37.64 % | **+34.13 %** | +19.53 % |
| PM10 | 2024 | 35,399 | 7.52 | 7.53 | 6.62 | +12.00 % | +12.14 % | +4.25 % |
| PM10 | 2025 | 35,822 | 7.40 | 6.94 | 5.91 | +20.16 % | +14.87 % | +3.02 % |
| PM10 | 2026 | 20,513 | 7.73 | 7.07 | 6.17 | +20.24 % | +12.80 % | +3.45 % |
| **PM10** | **toutes** | 91,734 | 7.52 | 7.20 | 6.25 | +16.94 % | **+13.26 %** | +3.65 % |
| PM10 · chaîne nommée | 2025 | 35,725 | 7.40 | 7.61 | 5.91 | +20.18 % | +22.34 % | +17.55 % |
| PM10 · chaîne nommée | 2026 | 20,513 | 7.73 | 7.67 | 6.17 | +20.24 % | +19.59 % | +15.43 % |
| **PM10 · chaîne nommée** | **toutes** | 56,238 | 7.52 | 7.63 | 6.00 | +20.20 % | **+21.32 %** | +16.75 % |
| PM2,5 | 2023 | 8,502 | 3.68 | 4.67 | 3.32 | +9.97 % | +29.04 % | +27.48 % |
| PM2,5 | 2024 | 25,881 | 4.44 | 5.26 | 3.88 | +12.57 % | +26.14 % | +28.16 % |
| PM2,5 | 2025 | 26,696 | 4.17 | 5.26 | 3.90 | +6.47 % | +25.79 % | +27.01 % |
| PM2,5 | 2026 | 15,591 | 4.10 | 5.03 | 3.75 | +8.61 % | +25.46 % | +24.72 % |
| **PM2,5** | **toutes** | 76,670 | 4.20 | 5.15 | 3.80 | +9.45 % | **+26.14 %** | +27.03 % |

⚠️ **Les deux blocs de colonnes ne se lisent pas ensemble.** Sur l'ozone, la chaîne AASQA **dégrade** CAMS brut : notre gain passe de **+11,88 %** contre CAMS à **+22,64 %** contre elle, *sans qu'aucun modèle ait changé*. C'est la référence qui a bougé — et c'est exactement pourquoi un pourcentage se cite avec ses trois mots (§ 7 ter).

⚠️ **Les PM10 sont publiés en deux variantes, et les deux sont légitimes.** Les membres d'ensemble n'existent pour ce polluant que depuis 2025-01, d'où deux tables. « PM10 » est la variante **longue — 31 mois**, chaîne réglementaire **ancrée sur CAMS** faute de membres ; « PM10 · chaîne nommée » est la variante **courte — 19 mois**, CHIMERE+MOCAGE réel. La longue est à la fois le plus grand corpus **et** le test le plus dur : son substitut atteint une RMSE de **7,20** contre **7,63** pour la chaîne nommée. **Le même modèle, sur les mêmes 19 mois, rend le même +20,2 % contre CAMS brut dans les deux tables** — seule la référence change. Ne jamais publier l'une en taisant l'autre.

⚠️ **La réserve porte sur les deux dénominateurs.** Les lignes AASQA s'ancrent sur des modèles en configuration **européenne 0,1° sans assimilation**. La chaîne réelle tourne en version nationale, plus fine et assimilée : elle est donc **meilleure** que cette simulation, et tout écart affiché ici est un **majorant** de notre avance. Le § 10 ter chiffre cet écart sur les journées de PREV'AIR réel captées.

## 8. Détection — à budget de fausses alertes égal

Un service ne choisit pas un seuil pour maximiser un score : il subit un **budget de fausses alertes**, au-delà duquel une alerte cesse d'être écoutée. La comparaison utile est donc *à taux de fausse alerte fixé, qui rappelle le plus ?* — et non « qui a le meilleur score à son propre seuil optimal ».

Le point de fonctionnement est choisi **hors échantillon**, sur d'autres stations que celles évaluées.

| budget | CAMS brut | correction | **correction + obs. passées** |
|---|---|---|---|
| ≤ 10% | *inatteignable* | 0.206 | **0.355** |
| ≤ 20% | 0.080 | 0.396 | **0.529** |
| ≤ 30% | 0.184 | 0.558 | **0.656** |
| ≤ 40% | 0.383 | 0.697 | **0.752** |

**À 30 % de fausses alertes : 0,656 contre 0,184 — 3,6 fois plus de dépassements réels détectés.** À 20 %, 6,6 fois. Et CAMS brut n'atteint jamais 10 % : quel que soit son seuil, son taux de fausse alerte reste au-dessus.

### Le facteur se reproduit hors fenêtre d'apprentissage

Modèle appris jusqu'au 31/12/2024, **seuils calibrés sur 2024**, appliqués en aveugle au 1ᵉʳ semestre 2025.

| budget | 17 mois appris | 2025, jamais vu |
|---|---|---|
| ≤ 20 % | 6,6× | **6,8×** |
| ≤ 30 % | 3,6× | **3,5×** |
| ≤ 40 % | 2,0× | **1,9×** |

Les taux de fausse alerte **constatés** sur 2025 (0,030 à 0,165) restent sous les budgets visés : les seuils calibrés sur 2024 sont conservateurs.

**La distinction que cela établit** : la précision ponctuelle généralise mal dans le temps — +1,1 % en saison ozone, prospectif strict — mais le **classement des jours par risque** généralise bien. *Le modèle sait ordonner ce qu'il ne sait pas chiffrer*, et c'est l'ordre qui décide d'une alerte.

⚠️ L'échantillon 2025 reste petit — 21 stations, ~160 dépassements. La **reproduction des facteurs** est plus informative que leur valeur.

### Les leviers s'additionnent — et aucun ne se noie dans le précédent

Rappel à **30 % de fausses alertes**, point de fonctionnement choisi hors échantillon.

| produit | O₃ | PM2,5 |
|---|---|---|
| CAMS brut | 0.192 | *budget inatteignable* |
| correction | 0.560 | 0.408 |
| + observations J−2 | 0.651 | 0.474 |
| + membres d'ensemble | 0.670 | 0.541 |
| **+ feux** | **0.679** | **0.563** |

Sur l'ozone, **3,5 fois le CAMS brut** à 30 % de budget, **5,6 fois** à 20 %. Sur PM2,5, le brut n'atteint aucun de ces budgets.

**Un résultat qui contredit le RMSE** : les six membres d'ensemble sont **nuls en RMSE sur l'ozone** — gain négatif, IC contenant zéro — et valent pourtant ici autant que les observations passées sur PM2,5 (+0,067 de rappel). *Une variable peut n'apporter rien à la précision ponctuelle et beaucoup au classement des jours à risque.* Tester en détection ce qui a été écarté sur le RMSE, et réciproquement.

### Les trois polluants ne sont pas dans la même situation

| polluant | seuil | dépassements | meilleur rappel à 30 % de fausses alertes |
|---|---|---|---|
| **O₃** | 120 µg/m³ (max 8 h) | 2 293 sur 134 423 (1,71 %) | **0,656** — 3,6× le brut |
| **PM2,5** | 25 µg/m³ (moyenne jour) | 1 844 sur 105 744 (1,74 %) | **0,485** — le brut n'atteint pas ce budget |
| **NO₂** | 120 µg/m³ (max horaire) | **270 sur 161 637 (0,17 %)** | **aucun budget ≤ 40 % atteignable** ; 0,044 à 40 % |

**Le NO₂ n'est pas détectable à ce grain**, et ce n'est pas un défaut de méthode : l'événement est dix fois plus rare que pour les deux autres. Au seuil d'information horaire de 200 µg/m³, le panel unifié ne compte que **6 dépassements** sur 368,904 jours-station (2023-06 → 2026-08, 344 stations, règle des 75 %) — le problème n'existe pas. Ce constat confirme, avec un protocole plus net, ce que le projet avait déjà mesuré (POD 0,084, Brier skill +0,017).

*Un seuil sans événements ne mesure pas une incapacité à détecter : il mesure l'absence de ce qu'on cherche. Compter les positifs avant de conclure.*

**Une différence entre polluants** : sur PM2,5 la perte pondérée **aide** (0,485 contre 0,437 pour la régression simple), alors qu'elle est neutre sur l'ozone. Le choix de la perte dépend donc du polluant, ce qu'une mesure sur l'ozone seul aurait laissé croire universel.

### Trois techniques qui n'apportent rien, une fois le seuil libre

| technique | avantage annoncé | d'où il venait |
|---|---|---|
| classification | POD 0,483 → 0,641 | la régression était seuillée à **120 µg/m³**, valeur qu'un moindre carré n'atteint presque jamais |
| perte pondérée | queue −3,1 % → +3,1 % | mesuré **à seuil fixe** |
| quantile 0,90 | écarté sur RMSE 20,90 | RMSE est un critère de prédiction **ponctuelle**, pas de détection |

Mesurées à budget de fausses alertes égal et seuil choisi hors échantillon, les trois s'effacent : 0,656 pour la régression pondérée contre 0,656 pour la régression simple, 0,573 pour le quantile, 0,622 pour la classification. **Ce qui décide est l'ordre des jours par risque, pas la fonction de perte.**

*Note* : maximiser le F1 ≡ maximiser le CSI, puisque `F1 = 2·CSI/(1+CSI)` est strictement croissante. La précision seule est un objectif dégénéré.

## 9. Les signalements, comptés — France et Occitanie

Les blocs précédents mesurent des erreurs. Celui-ci compte ce qu'un service aurait **publié** : le nombre de jours-station dépassant 120 µg/m³ en maximum journalier 8 h, sur 2024. C'est la traduction du RMSE en unité de décision.

| périmètre | produit | jours-station | jours avec ≥1 signalement | pic (stations le même jour) |
|---|---|---|---|---|
| France (270 stations) | **la vérité** | 10,803 | 285 | 204 |
| France (270 stations) | MOS officiel | 1,095 (10 %) | 64 | 163 |
| France (270 stations) | notre correction complète | 9,347 (87 %) | 214 | 222 |
| Occitanie (21 stations) | **la vérité** | 979 | 137 | 22 |
| Occitanie (21 stations) | MOS officiel | 113 (12 %) | 17 | 17 |
| Occitanie (21 stations) | notre correction complète | 824 (84 %) | 103 | 22 |

**Le produit officiel annonce 21 % des jours-station en France, et 7 % en Occitanie.** L'écart régional est cohérent avec la ventilation saisonnière du bloc 2 : il est en défaut sur la fenêtre ozone, et l'Occitanie est une région où l'ozone estival domine.

**Le pic est le chiffre le plus parlant.** La vérité monte à 106 stations le même jour en France ; le produit officiel plafonne à 26. Il ne rate pas seulement des jours, il rate l'**ampleur** de ceux qu'il détecte. Notre correction atteint 91 — elle retrouve la forme des grands épisodes.

⚠️ **La comparaison lui est favorable sur un point** : nos prédictions sont hors échantillon, chaque station prédite par un modèle qui ne l'a jamais vue, tandis que le produit officiel utilise les observations récentes de ces mêmes stations.

Figures : `reports/figures/calendrier_france.html` et `calendrier_occitanie.html`.

## 10. Le front précision–rappel — à qualité d'annonce identique

Comparer deux détecteurs par leur **nombre d'annonces** ne dit rien : un produit bruyant en émet davantage et paraît meilleur. La comparaison qui vaut est à **précision fixée**, ou à **rappel fixé**.

| | précision | rappel | fausses alertes |
|---|---|---|---|
| **2025 — Occitanie, hors échantillon** (3 183 jours-station, 160 dépassements) | | | |
| MOS officiel, seuil réglementaire | 68,5 % | 46,2 % | 34 |
| nous, seuil réglementaire | **97,1 %** | 42,5 % | **2** |
| **nous, à sa précision** | 68,7 % | **76,9 %** | 56 |
| nous, à son rappel | **94,0 %** | 49,4 % | **5** |
| **2024 — France, stations exclues** (72 372 jours-station, 918 dépassements) | | | |
| MOS officiel | 61,2 % | 15,8 % | 92 |
| nous, seuil réglementaire | 76,9 % | 47,1 % | 130 |
| **nous, à sa précision** | 61,9 % | **64,1 %** | 362 |
| nous, à son rappel | **96,7 %** | 16,1 % | **5** |

> À **qualité d'annonce identique**, nous détectons **1,7 fois plus** de dépassements hors échantillon et **4,1 fois plus** sur la France. À **rappel identique**, nous produisons **5 fausses alertes contre 92**.

Le front **domine** : à tout point de fonctionnement du produit officiel, nous sommes strictement meilleurs sur l'autre axe. C'est le seul résultat du projet qui se dise sans réserve d'axe.

**Traduction pour un service** : à 68,5 % de précision — la sienne aujourd'hui — il passerait de **46 % à 77 % des épisodes détectés**, sans dégrader la qualité de ses annonces.

⚠️ **Deux réserves.** Le seuil est balayé sur les données évaluées : c'est un front, pas un point de fonctionnement validé — la version calibrée hors échantillon figure au bloc 8. Et le produit officiel utilise les observations récentes de ces stations, ce que notre variante « usage B » ne fait pas.


### Le réentraînement continu ne comble pas l'écart

Le produit officiel est réentraîné en continu, notre modèle est figé au 31/12/2024. Réentraîné mensuellement avec tout l'historique jusqu'à J−2, le gain est de **−0,02 µg/m³** — nul. L'Occitanie n'ajoute que 2 903 jours-station à un socle de 131 097, soit 2 %. Le levier est réel en principe, **vide faute de volume** — et il le serait aussi pour une AASQA, dont le réseau régional est petit.

## 10 ter. La barre réelle — PREV'AIR, et non CAMS brut

Tout ce document compare à **CAMS brut**, que les AASQA ne consomment pas : elles reçoivent **PREV'AIR**. Le rapport *Performances Prev'air en 2024* (J. Salles Loustau, INERIS/LCSQA, publié le 08/04/2026) donne enfin cette barre.

⚠️ **Le grain n'est pas le nôtre.** Le rapport précise p. 17 : « seul le **maximum journalier** d'ozone est ainsi considéré », donc le maximum horaire et non le maximum glissant 8 h. Nos 9,53 µg/m³ ne s'y comparent pas. Il a fallu recalculer sur leur grain. Le reste des conventions concorde : stations de **fond** (288 chez eux, 254 chez nous), filtre à 75 %, fenêtre avril–septembre.

| | RMSE | biais | corrélation |
|---|---|---|---|
| MOCAGE (J0, 288 stations) | 14,6 | +0,14 | 0,70 |
| CHIMERE brut (J0) | 13,9 | +4,2 | 0,67 |
| **AS-CHI** — adaptation statistique en production | **13,3** | +3,1 | **0,74** |
| CAMS brut (J+1, 254 stations) | 11,08 | −2,02 | 0,822 |
| **notre correction** | **8,84** | **+0,05** | **0,880** |

⚠️ **Ne jamais citer 8,84 contre 13,3.** CAMS brut est déjà à 11,08 contre 13,9 pour CHIMERE brut : une part de l'écart vient de l'**amont**, et c'est attendu — CAMS Europe est une médiane d'ensemble de neuf à onze modèles dont CHIMERE lui-même.

**La seule comparaison défendable oppose chaque correction à son propre brut :**

| | brut | corrigé | gain de la correction |
|---|---|---|---|
| PREV'AIR (CHIMERE → AS-CHI) | 13,9 | 13,3 | **+4,3 %** |
| ce projet (CAMS → nous) | 11,08 | 8,84 | **+20,2 %** |

Cette lecture neutralise le confondant d'amont **et** celui des DROM, inclus dans leur moyenne France avec une RMSE avoisinant 20 mais affectant les deux lignes également. Deux écarts jouent **contre** nous, donc ne fragilisent pas la conclusion : leurs scores sont à **J0** et les nôtres à **J+1** ; et notre 8,84 vient de plis `i % 3`, optimistes — au protocole bloqué le gain descendrait vers 13-14 %, soit **encore trois fois** celui de l'adaptation statistique.

### Le motif qui se répète, et c'est le vrai résultat

> « l'amélioration apportée par l'adaptation statistique diminue au fur et à mesure des échéances, jusqu'à une légère **dégradation** des performances pour l'AS par rapport au modèle brut à partir de J2 pour la RMSE » — *Performances Prev'air en 2024*, p. 22

C'est **exactement** ce que ce dossier mesure sur le MOS de Copernicus : dégradation huit mois sur douze, −19,6 % en saison ozone. Deux post-traitements officiels, deux chaînes différentes — CHIMERE et CAMS —, le **même retournement**. Ce n'est plus l'anomalie d'un produit, c'est un motif de la famille de méthodes.

## 10 bis. Le dossier lu dans les conventions d'une AASQA

Nos scores sont des **RMSE groupées** sur tous les couples station–temps réunis. Un rapport AASQA conforme au référentiel LCSQA calcule autre chose : **stations de fond seules**, disponibilité **≥ 75 %** (opérateur large, comme le pseudo-code du référentiel technique national), score temporel **par station puis moyenne non pondérée des stations**, échéances séparées, ozone limité à **avril–septembre**. Comparer nos chiffres à un rapport d'AASQA sans ce recalcul serait comparer deux grandeurs différentes.

Recalculé sur les stations de fond passant le seuil de disponibilité, échéance J+1 :

| polluant | n stations | CAMS brut | notre correction | gain **AASQA** | gain ML groupé | écart |
|---|---|---|---|---|---|---|
| O₃ | 254 | 10,062 | **7,879** | **+21,7 %** | +21,9 % | −0,2 pt |
| NO₂ | 217 | 15,458 | **10,101** | **+34,7 %** | +36,3 % | −1,6 pt |
| PM2,5 | 156 | 3,936 | **2,772** | **+29,6 %** | +26,4 % | **+3,2 pt** |
| **PM10** | 191 | 6,349 | **4,236** | **+33,3 %** | +32,7 % | +0,6 pt |

⚠️ **Les PM10 n'apparaissent pas au tableau principal** (§ 1) : celui-ci compare au post-traitement officiel de Copernicus, que le projet n'a pas téléchargé pour ce polluant. Le chiffre ci-dessus est donc une comparaison à **CAMS brut seul**, sur 19 mois appariés (2024-01 → 2026-08) et non sur la fenêtre 2024 des trois autres — à ne pas aligner sans le dire.

Le biais y est le plus parlant : CAMS **sous-estime les PM10 de 2,08 µg/m³** en moyenne sur les stations de fond ; la correction ramène ce biais à **+0,04** et la corrélation de 0,689 à **0,866**. C'est le polluant qui porte **40 des 52 vigilances** réellement déclarées en Occitanie.

**Le changement de convention joue dans les deux sens.** L'audit supposait que la RMSE groupée nous flattait : c'est vrai pour le NO₂ (−1,6 point), **faux pour les PM2,5** où la convention AASQA nous est plus favorable de 3,2 points, et négligeable pour l'ozone. Ce n'est pas un biais systématique mais une dépendance au polluant — et elle n'était pas prévisible sans la calculer.

Le résultat le plus démonstratif du dossier apparaît dans cette convention : sur les **150 stations urbaines de fond**, CAMS sous-estime le NO₂ de **−11,6 µg/m³** en biais moyen ; notre correction ramène ce biais à **−0,5** et la RMSE de 17,7 à **11,0**.

Ventilation par zone, O₃ puis NO₂ — RMSE (biais) :

| zone | O₃ CAMS | O₃ nous | NO₂ CAMS | NO₂ nous |
|---|---|---|---|---|
| urbaine | 9,790 (+0,62) | **7,670** (+0,41) | 17,674 (**−11,59**) | **10,975** (−0,51) |
| périurbaine | 9,736 (+0,29) | **7,701** (−0,25) | 13,692 (−7,52) | **9,934** (+0,88) |
| rurale | **11,192 (−2,54)** | **8,650** (−0,43) | 5,130 (+0,45) | 5,142 (+1,22) |

Deux lectures opposées, et les deux comptent. Sur l'**ozone**, le rural est la zone la moins bien traitée — CAMS y sous-estime de 2,5 µg/m³ et la correction, qui efface ce biais, y reste la moins performante ; ce sont les stations les plus isolées, donc celles où le voisinage n'aide pas, ce que la validation par plis bloqués (§ 11) mesure par ailleurs. Sur le **NO₂ en rural**, à l'inverse, **la correction n'apporte rien** (5,142 contre 5,130) et dégrade légèrement le biais : là où CAMS est déjà juste — niveau bas, aucune source locale —, il n'y a rien à corriger.

⚠️ **Les seuils d'information français ne sont pas évaluables sur cette fenêtre.** À 180 µg/m³ en maximum horaire, l'ozone compte **32 dépassements sur 60 400 jours-station** : CAMS en détecte 3, notre correction 2 à J+1, et **aucun des deux à J+3**. Le NO₂ à 200 µg/m³ en compte **6 sur 368,904** — mesurés sur le panel unifié, et non sur la fenêtre de cette section —, aucun détecté. Un modèle entraîné **directement** sur le maximum horaire donne le même résultat qu'une transposition depuis le grain 8 h : l'échec est mécanique, pas méthodologique. **Et il n'est pas une affaire de calibration** : mesurée, la pente de régression de l'observé sur le prédit vaut **1,007** — le modèle n'est pas contracté, son échelle est juste. Une calibration isotone du score vers les bandes de l'indice, décidée au coût attendu minimal avec pénalité asymétrique, n'apporte que **+1,2 point** de rappel contre un simple abaissement de seuil à budget de fausses annonces égal — sous la barre de bruit de ±2 points. Le rang du régresseur porte déjà toute la décision disponible. Ce qui manque est de l'**information** : 53 prédicteurs qui ne contiennent rien distinguant un jour à 175 µg/m³ d'un jour à 185, et 32 événements pour l'apprendre. **Notre facteur 3,6× porte sur la valeur cible européenne (120 µg/m³, max 8 h), jamais sur le seuil de procédure.**

⚠️ **PM10 : lacune de périmètre, pas de donnée.** Le projet n'a jamais ingéré les PM10, ni en observation ni en prévision. Or sur les **52 vigilances réellement déclarées** par ATMO Occitanie entre janvier 2025 et mars 2026, **40 portent sur les PM10** et 12 sur l'ozone. Le déclenchement opérationnel se fait donc aux trois quarts sur un polluant hors de notre périmètre. Les PM2,5 à 25 µg/m³ répondent à une autre question et ne les remplacent pas.

⚠️ **Les vigilances déclarées sont une cible, jamais un prédicteur.** Mesuré : l'historique est diffusé vers 9h40 **le matin de la journée qu'il concerne** (médiane +10,0 h après l'échéance, **aucune** ligne disponible avant). L'utiliser en entrée d'une prévision J+1 serait la faute reprochée à ERA5.

## 11. Ce que la validation démontre, et ce qu'elle ne démontre pas

| propriété | mesure | verdict |
|---|---|---|
| Généralisation **spatiale** (stations exclues) | **+29,7 %**, σ 1,2, aucun pli négatif | ✅ démontrée |
| Généralisation **temporelle** (mois caché) | +6,7 %, pire pli **−35,5 %**, 5 négatifs sur 17 | ❌ non démontrée |
| **Blocage conjoint** station × mois | **+1,5 %**, pire **−41,4 %**, **8 négatifs sur 17** | ⚠️ marginale |
| **Prospectif strict** (rolling-origin) | **+6,3 %**, pire **−7,3 %**, 4 négatifs sur 16 | ⚠️ voir ci-dessous |
| Détection de dépassement, hors échantillon | CSI 0,495 (officiel 0,387) | ✅ à seuil calibré |

| Généralisation spatiale, **plis bloqués** (≥ 50 km) | **+18,5 %** contre +28,6 % non bloqué | ⚠️ chiffrée ci-dessous |

### Le blocage spatial des plis — l'optimisme, mesuré

Le protocole du projet construit ses plis par `i % n` sur l'identifiant de station. C'est arbitraire, et surtout **non bloqué spatialement**. **Les distances dépendent du polluant, et il faut donner celle de la population évaluée.** Sur les 813 stations de métropole toutes espèces confondues, le plus proche voisin est à 2,4 km en médiane ; mais la population qui mesure l'ozone n'en compte que 270, plus dispersées (**médiane 14,3 km**, 39 % sous 10 km). Pour le NO₂ : 340 stations, **4,1 km**, 66 % sous 10 km. Pour les PM2,5 : 227 stations, 12,3 km, 45 %.

En regroupant les stations par k-moyennes et en sortant des **grappes entières** — la fuite tombe de 79 % à **3 %** — puis en creusant un fossé de 50 km autour du test :

| polluant | plis `i % n` | blocs seuls | fossé 50 km | voisin médian |
|---|---|---|---|---|
| O₃ | +28,60 % | +19,21 % | **+18,47 %** | 14,3 km |
| PM2,5 | +28,37 % | — | **+20,64 %** | 12,3 km |
| NO₂ | +33,14 % | — | **+30,96 %** | 4,1 km |

### Le rayon du fossé, choisi par la donnée et non par le score

Les rayons de 25 puis 50 km avaient été **essayés**, donc choisis après avoir vu les résultats — ce qui n'est pas un protocole. Le rayon juste se lit dans la **portée de l'autocorrélation des résidus** : au-delà, une station voisine n'informe plus. Mesurée sur les couples de stations partageant au moins 120 jours :

| polluant | corrélation des résidus à 0–5 km | portée (r < 0,1) | perte au blocage |
|---|---|---|---|
| O₃ | **0,647** | **150 km** | −10,1 pts |
| PM2,5 | 0,499 | 150 km | −7,7 pts |
| NO₂ | **0,262** | 75 km | −2,2 pts |

**La perte au blocage est monotone dans cette corrélation.** L'explication n'est donc pas la densité du réseau mais la **portée** : une voisine de NO₂ à 2 km ne renseigne presque rien sur le résidu (0,26), une voisine d'ozone à 50 km en renseigne encore un tiers (0,32). Les résidus de **CAMS brut** sont bien plus corrélés (0,85 sur l'ozone) que ceux de la correction : celle-ci **absorbe** une part de la structure spatiale, ce qu'on lui demande.

### La décomposition, avec son témoin

Au rayon justifié de **150 km**, le gain ozone tombe à **+10,46 %**. Mais un fossé de 150 km retire **127 stations d'entraînement par pli sur 180** : une part de la chute est de la **famine de données**, pas de la fuite supprimée. Le témoin — retirer autant de stations **au hasard**, sans blocage — le sépare :

| protocole (O₃) | gain | ce que l'écart isole |
|---|---|---|
| `i % 3` | +28,60 % | — |
| blocs spatiaux, jeu complet | +19,21 % | **−9,4 pts de fuite** |
| blocs + retrait **aléatoire** de 127 stations | +16,20 % | **−3,0 pts de volume** |
| blocs + fossé 150 km | +10,46 % | −8,8 pts, dont 3,0 de volume |

**Corrigé du confondant de volume, le gain à indépendance spatiale réelle vaut environ +13,5 %.** Ni +18,5 % — fossé trop court — ni +10,5 % — confondu par la perte de données. C'est le premier chiffre de ce dossier qui soit décomposé.

⚠️ **L'explication par la proximité ne tient pas.** Le NO₂ a les stations les **plus serrées** (4,1 km) et c'est lui qui **résiste le mieux** au blocage ; l'ozone, trois fois plus dispersé, perd le plus. C'est l'inverse de ce qu'une explication par le voisinage prédit. Une première version du dossier affirmait ce mécanisme : il est retiré, et l'écart reste **mesuré mais inexpliqué**.

⚠️ **Cela n'invalide aucune comparaison.** Tous les produits — CAMS, MOS officiel, nos variantes — sont évalués sur les mêmes plis ; le front précision–rappel, les mesures d'apport et les ablations gardent leur valeur. Ce qui bouge est le chiffre **absolu**, et seulement pour l'usage *prédire là où rien ne mesure*. Publier les deux, en nommant l'usage de chacun.

**« Station inconnue » signifie *autre station du même réseau*, pas *lieu quelconque*.** Deux stations d'une même maille reçoivent la **même** valeur CAMS ; l'écart de leurs résidus est donc exactement l'écart de leurs observations — vérifié à l'identique dans les données. Cette divergence intra-maille vaut **3,61 µg/m³** en **médiane des écarts-types horaires par maille**, et **6,1 µg/m³** en moyenne sur paires journalières (IC95 par bootstrap de maille [5,0 ; 7,6]). La distribution est très asymétrique, d'où l'écart entre les deux résumés : **citer lequel des deux, toujours.**

⚠️ **Ce n'est pas un « plancher », et le mot a été retiré du dossier.** Trois raisons, chacune vérifiée :

1. la divergence mélange différence de support, gradients urbains réels, bruit instrumental et sélection du réseau — rien n'établit qu'aucune méthode ne descende sous cette valeur ;
2. la décomposition par strates ne trouve **qu'une seule typologie exploitable** (fond) : le réseau ne fournit presque aucune paire trafic ou industrielle dans une même maille, et l'IC reste large (~40 % de la moyenne) ;
3. l'ancienne formule « 26 % du RMSE » comparait une **médiane d'écarts-types** à un **RMSE** — deux grandeurs non commensurables. Elle est retirée.

*Nuance mesurée au passage : l'écart-type intra-maille du résidu **corrigé** dépasse souvent celui du résidu brut. C'est attendu — la correction donne des valeurs différentes à des stations que CAMS traite à l'identique — mais cela signifie aussi qu'elle peut sur-différencier.*

**Une part du gain accompagne le défaut du forçage.** En partageant les jours à la médiane du RMSE de CAMS, la correction rend **+14,0 %** quand le forçage est bon contre **+23,6 %** quand il dérive.

⚠️ **Cet écart est en partie arithmétique, et il faut le dire.** Avec `e = Y − CAMS` et `m` la correction prédite, `ΔMSE = e² − (e − m)² = 2em − m²`. Stratifier les jours par l'erreur **réalisée** de CAMS sélectionne donc directement le premier terme : un gain plus grand là où l'erreur brute est grande est en partie mécanique, puisqu'il y a davantage de perte réductible. La corrélation de **+0,953** en ΔMSE partage sa variable explicative avec le gain qu'elle explique.

L'énoncé défendable est donc : *la correction retire davantage de perte sur les cas où CAMS s'avère mauvais ; nous n'avons pas montré qu'elle **anticipe** une dérive.* Trancher exigerait une stratification **ex ante** — version de la chaîne, dispersion inter-membres, contrôle de processus — ne contenant pas l'observation.

⚠️ **Ne pas citer le +0,913** mesuré sur les deux ruptures des 13/11 et 03/12/2024 : il repose sur 5 paires de mois et son leave-one-out descend à **+0,135**. Le +0,953 en ΔMSE le remplace.

Ce que cela ne dit **pas** : que la correction nuit quand le forçage est juste. Elle gagne encore +14,0 % — elle gagne moins, elle ne nuit pas, sauf ponctuellement.

## 12. La pile complète — ce que valent tous les leviers ensemble

Double aveugle **station ET mois cachés**, J+2, fenêtre du flux GEOS-CF v1. L'ordre des étages est **déclaré avant la mesure** : le réordonner après coup flatterait un étage choisi. Deux périmètres qui ne se confondent jamais — **PARTOUT** (utilisable là où aucune station n'existe) et **AUX STATIONS** (exige l'historique du point). ERA5 figure **hors méthode** : c'est une réanalyse, elle n'existe pas quand la prévision est émise, son gain est un **plafond**.

| étage | NO₂ | O₃ | PM10 | PM2,5 |
|---|---|---|---|---|
| base (CAMS, terrain, calendrier) | +26.61 % | +7.01 % | +8.52 % | +2.07 % |
| + typologie | +35.58 % *(+8.97)* | +6.87 % *(-0.13)* | +10.12 % *(+1.61)* | +2.23 % *(+0.16)* |
| + membres | +36.12 % *(+0.54)* | +9.83 % *(+2.95)* | +14.20 % *(+4.07)* | +5.75 % *(+3.52)* |
| + feux | +36.38 % *(+0.26)* | +11.93 % *(+2.10)* | +15.09 % *(+0.89)* | +7.80 % *(+2.05)* |
| + geoscf | +38.71 % *(+2.33)* | +13.75 % *(+1.82)* | +17.43 % *(+2.34)* | +9.90 % *(+2.10)* |
| + tendance | +38.86 % *(+0.15)* | +15.83 % *(+2.08)* | +17.88 % *(+0.45)* | +10.03 % *(+0.13)* |
| ★ MAXIMALE — PARTOUT | **+38.86 %** *(+0.00)* | **+15.83 %** *(+0.00)* | **+17.88 %** *(+0.00)* | **+10.03 %** *(-0.00)* |
| ★ MAXIMALE — AUX STATIONS (+ veille) | **+46.20 %** *(+7.34)* | **+22.47 %** *(+6.64)* | **+24.22 %** *(+6.34)* | **+19.68 %** *(+9.65)* |
| plafond ERA5 (NON déployable) | +49.32 % *(+10.46)* | +26.16 % *(+10.33)* | +26.42 % *(+8.55)* | +23.15 % *(+13.12)* |

⚠️ **Les fenêtres diffèrent selon le polluant** : NO₂ 29 mois (2023-08→2025-12) · O₃ 29 mois (2023-08→2025-12) · PM10 24 mois (2024-01→2025-12) · PM2,5 29 mois (2023-08→2025-12). Seuls les **écarts entre étages** se comparent d'un polluant à l'autre, jamais les niveaux.

⚠️ Ne jamais citer le chiffre **AUX STATIONS** comme une performance de spatialisation : il exige l'historique d'observations du point, que la spatialisation n'a par définition pas.

## 13. GEOS-CF — la seule information venue de l'extérieur

Modèle de chimie-transport de la NASA, inventaire d'émissions et assimilation **indépendants** de CAMS. Tous les autres leviers du dossier réarrangent ce que CAMS contient déjà.

⚠️ **Le fournisseur a changé de flux au milieu de la fenêtre** — v1 retiré le 2 janvier 2026, v2 démarré le 5 août 2025 — et les deux ne sont **pas le même prédicteur**. Sur le mois de recouvrement, l'ozone diffère de **+15,41 µg/m³** en moyenne, soit l'ordre de grandeur de l'erreur des modèles eux-mêmes. Tout apport se mesure **par flux** ; le corpus mixte est écarté, et les chiffres publiés le 04/08 qui en venaient sont retirés.

| polluant | apport au plancher d'information | étendue (partitions) | corrélation des erreurs | n |
|---|---|---|---|---|
| O₃ | **+2.52 %** | +2.20 → +2.69 (4) | +0.660 | 75,072 |
| NO₂ | **+2.82 %** | +2.66 → +3.00 (4) | +0.807 | 93,674 |
| PM2,5 | **+1.14 %** | *une seule partition* | +0.427 | 63,132 |

**Le mélange nu ne marche jamais** : GEOS-CF seul est bien pire que CAMS partout, et leur moyenne est systématiquement pire que CAMS seul. En **variables**, le modèle apprend *où* croire le modèle étranger — ce qu'une moyenne ne sait pas faire.

> **apport ≈ décorrélation × qualité.** Sur PM2,5 GEOS-CF est plus décorrélé de CAMS que deux membres CAMS entre eux, et apporte pourtant le moins — parce qu'il y est quatre fois plus mauvais.

## 14. Les épisodes **réellement déclenchés** — la mesure la plus dure du dossier

Tout le reste de ce document compte des « épisodes » au sens **journée-station en classe ATMO ≥ 3** — des milliers d'occurrences. Un déclenchement réel est une **zone-jour sous procédure préfectorale**, et il y en a **52 en quatorze mois** en Occitanie (PM10 40 · O₃ 12 · NO₂ **0**). Vérité terrain publiée par l'AASQA elle-même. **Les deux comptes ne se comparent pas.**


**O₃** — 12 épisodes évalués, 5,161 zones-jours

| système | attrapés | rappel | fausses | précision |
|---|---|---|---|---|
| observation | 12/12 | 100.0 % | 412 | 2.8 % |
| CAMS brut | 8/12 | 66.7 % | 102 | 7.3 % |
| chaîne AASQA | 11/12 | 91.7 % | 446 | 2.4 % |
| **notre modèle** | 12/12 | 100.0 % | 473 | 2.5 % |

**PM10** — 33 épisodes évalués, 5,174 zones-jours

| système | attrapés | rappel | fausses | précision |
|---|---|---|---|---|
| observation | 21/33 | 63.6 % | 18 | 53.8 % |
| CAMS brut | 1/33 | 3.0 % | 3 | 25.0 % |
| chaîne AASQA | 1/33 | 3.0 % | 9 | 10.0 % |
| **notre modèle** | 2/33 | 6.1 % | 11 | 15.4 % |

⚠️ **Trois lectures, dans l'ordre.** (1) Le plafond n'est pas le nombre d'épisodes déclarés mais la ligne « observation » : sur PM10, douze épisodes n'ont **aucune station** au-dessus du seuil en moyenne journalière — la procédure se déclenche sur autre chose que la grandeur prédite. (2) Tous les systèmes sont quasi aveugles sur PM10, nous très légèrement moins. (3) Sur O₃ nous attrapons tout et crions au loup ~9 % des zones-jours ; CAMS brut, qui en rate le tiers, est trois fois plus précis. **À seuil physique fixé, le recalage d'amplitude joue contre nous.**

Ce tableau est pris **à seuil fixe, sans réglage**. Le § 8 montre qu'à **volume d'alertes constant** le classement s'inverse. Les deux sont vraies ; il faut dire laquelle on montre et pourquoi.

## 15. À quelle échelle décider — la persistance est gratuite, **et elle n'est pas à nous**

La décision était prise par station-jour puis agrégée par le **maximum** — « au moins une station dépasse » — c'est-à-dire l'agrégateur qui **maximise les fausses alertes**. Il n'avait pas été retenu : il avait été subi.

Exiger un dépassement prédit **deux jours de suite** retire un tiers des fausses alertes sans perdre un épisode. Voici ce que cela donne pour les **quatre** systèmes — parce que c'est une propriété de la *règle*, pas du modèle :

| système | épisodes | fausses sans | fausses avec | écart | rappel |
|---|---|---|---|---|---|
| observation | 12/12 | 412 | 254 | -38.3 % | 100.0 % *(inchangé)* |
| **notre modèle** | 12/12 | 473 | 312 | -34.0 % | 100.0 % *(inchangé)* |
| chaîne AASQA | 11/12 | 446 | 310 | -30.5 % | 91.7 % *(inchangé)* |
| CAMS brut | 8/12 | 102 | 44 | -56.9 % | **66.7 → 58.3 %** |

**−34 % de fausses alertes, zéro épisode perdu.** Ce n'est pas un arbitrage, c'est un gain sec : une fausse alerte est un accident isolé, un épisode réel est **installé**, et la procédure préfectorale exige elle-même la persistance. Notre règle était instantanée alors que la décision qu'elle imite ne l'est pas.

⚠️ **Mais elle profite à tout le monde, et davantage à l'observation qu'à nous.** La règle est gratuite pour trois systèmes sur quatre — rappel strictement inchangé — et **coûte un épisode à CAMS brut**, dont le rappel tombe. Le seul énoncé défendable est donc : *« la règle de décision vaut un tiers des fausses alertes, quel que soit le système qui l'alimente »*. Se l'attribuer serait faux.

⚠️ **L'agrégateur de zone, lui, est un arbitrage — et à moitié un artefact.** Une règle « k parmi n » ne peut pas déclencher là où le réseau porte moins de k stations : elle l'**éteint**. Le réseau occitan a une **médiane de 2 stations par département**, et 3 départements sur 9 n'en portent qu'une. La chute des fausses alertes se décompose en deux mécanismes de taille comparable — silence sélectif des zones creuses, et vrai effet d'agrégation dans les zones denses. Ne jamais présenter le premier comme une méthode.

⚠️ **À 12 épisodes d'ozone, aucun écart entre systèmes n'est significatif** : tous les intervalles de bootstrap se recouvrent. Le seul chiffre solide de cette section est la baisse de fausses alertes, parce qu'elle est **à rappel exactement identique**.

## 16. Registre — ce que ces mesures ne disent pas

Ces mesures comparent des produits, pas des équipes. Le post-traitement officiel répond à des contraintes d'exploitation — couverture européenne, réentraînement continu, publication horaire — que ce projet n'a pas, et son article recommande lui-même la cible journalière lorsque l'usage porte sur un maximum : le choix horaire du produit distribué est donc **documenté et assumé**, pas un oubli.

Le phénomène mesuré ici est **publié** — Bertrand et al. 2023 pour le grain sur CAMS, Huang et al. 2017 pour la réduction de variabilité en post-traitement. Ce travail les réplique et caractérise le produit déployé ; il ne les découvre pas.

**Interdits de formulation** : « nous battons Copernicus », « leur produit est défaillant », « nous avons découvert ». Les faits suffisent, et ils sont plus solides sans adjectif.
