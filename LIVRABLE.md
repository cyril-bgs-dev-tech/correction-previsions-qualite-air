# Livrable — structure de présentation et état d'avancement

> **Cible :** une présentation HTML (10 pages) + une démo Streamlit.
> **Échéance :** 22 août · **Mis à jour :** 2026-07-29

## ⚠️ Réorientation décidée le 28/07 — l'ozone et la spatialisation au centre

Trois résultats mesurés imposent de réorienter, et ils convergent :

1. **La cible est un champ, pas une station.** L'indice officiel est un *maximum sur une
   surface* ; prédire des points donne structurellement **−0,72 classe** de biais. La
   spatialisation devient le problème de modélisation central, pas un rendu final.
2. **L'ozone pilote l'indice à 87,8 %.** Traiter trois polluants à parité disperse
   l'effort. Améliorer l'indice ATMO en Occitanie, c'est améliorer l'**ozone**.
3. **Le géospatial vise justement l'ozone.** Les chênes émettent l'isoprène, précurseur
   d'O₃, dont l'émission croît exponentiellement avec la température. La variable la plus
   différenciante du projet cible le polluant qui détermine l'indice.

| Avant | Après |
|---|---|
| 3 polluants à parité | **O₃ prioritaire**, NO₂ et PM2.5 en second rang |
| Prédire des concentrations en station | **Prédire un champ, agréger à l'EPCI** |
| Spatialisation en page 9 | **Au cœur, dès la page 6** |
| Géospatial = un test parmi d'autres | **Le levier principal** |
| Métrique : RMSE en station | **+ accord de classe d'indice à l'EPCI** |

**Bonus tactique :** le biais de −0,72 classe est lui-même modélisable. Apprendre la
correction point → surface est une contribution nette, mesurable et immédiatement
parlante pour le métier.
>
> Ce fichier est le **tableau de bord du projet**. Il se met à jour à chaque avancée :
> chaque page indique ce qui existe réellement, ce qui manque, et de quoi elle dépend.

**Légende :** ✅ prêt · 🟡 partiel · ⬜ à faire · 🔒 bloqué

---

## Page 1 — Présentation du projet : ATMO, rôles et responsabilités

**État : ✅ matière complète, mise en forme à faire**

| Élément | Source |
|---|---|
| Missions réglementaires d'une AASQA (art. L.221-1 à L.221-3) | `REGLEMENTAIRE.md` §8 |
| Gouvernance quadripartite, agrément ministériel | `REGLEMENTAIRE.md` §8 |
| Les 4 missions : surveiller · informer quotidiennement · calculer l'indice ATMO · inventorier les émissions · rapporter à l'UE | `REGLEMENTAIRE.md` §8 |
| Cadre : directive 2008/50/CE, arrêté du 10/07/2020, arrêté du 07/04/2016 | `REGLEMENTAIRE.md` |

**Angle :** montrer que le projet répond aux missions réelles, pas à un exercice abstrait.

---

## Page 2 — Les données disponibles

**État : ✅ le point le plus abouti du projet**

| Élément | État |
|---|---|
| Catalogue de 6 domaines, sources testées une à une | ✅ `DATA_CATALOG.md` |
| Corpus métropolitain : 430 stations, 894 séries, **94 M de lignes**, 2013-2025 | ✅ sur disque |
| Corpus occitan complet : **1999 → 2026, 27,6 ans** | ✅ sur disque |
| Rapport de qualité : couverture, capteurs gelés, négatives | ✅ `reports/QUALITE_DONNEES.md` |
| Procédures d'accès et verrous | ✅ `ACCES.md` |

**Angle fort — les découvertes, pas le catalogue :**
- Le flux temps réel O₃ est **rompu pour la France entière depuis le 01/07/2025**.
- Un rapport de couverture naïf produisait **21 faux positifs sur 22**.
- « 515 stations en France » inclut l'Outre-mer ; la métropole en compte 476.
- Le préfixe du code station n'est pas le département (`FR34051` est dans l'Indre).

---

## Page 3 — Le système prédictif actuel et ses limites

**État : 🟡 compréhension établie, à documenter**

| Élément | État |
|---|---|
| Chaîne AASQA : inventaire d'émissions + météo + CTM → concentrations → indice | 🟡 à rédiger |
| PREV'AIR (CHIMERE + MOCAGE), ~2 km, J+5 · CAMS ensemble 9-11 modèles, 0,1° | ✅ vérifié |
| **Reconstitution de l'indice ATMO et écart mesuré** | ✅ **`reports/INDICE_ATMO.md`** |
| Limites : granularité des émissions, maille urbaine, sorties déterministes | 🟡 |

**Ce qui est reproduit exactement** — la règle d'agrégation « le pire des sous-indices »
est vérifiée à **99,926 %** sur 47 300 enregistrements officiels (le jeu publie les cinq
sous-indices en clair, ce qui permet de tester la règle sans leur modèle). Bornes,
grandeurs par polluant et codes couleur : conformes et testés.

**Ce qui ne l'est pas, et c'est l'essentiel** — la spatialisation. L'indice calculé en
station s'accorde à **42,8 %** avec l'officiel de l'EPCI, avec un **biais systématique de
−0,72 classe**. Ce biais n'est pas une erreur : l'officiel est un *maximum sur une
surface*, le nôtre une *valeur ponctuelle*. **La modélisation spatiale est donc un
prérequis, pas un raffinement de fin de projet.**

**Résultat communicable** — l'ozone pilote l'indice ATMO occitan dans **87,8 %** des cas
(officiel, 5 sous-indices), contre 68,2 % vu depuis nos stations urbaines. L'écart
s'explique : le maximum sur un EPCI va chercher l'ozone **rural**, élevé faute de NO qui
le détruise par titration. Agir sur l'indice en Occitanie, c'est d'abord agir sur l'ozone.

**Limite la mieux étayée, et vérifiée :** aucun inventaire d'émissions français maintenu
ne fournit d'horaire. Tous sont annuels, au mieux communaux. L'horaire est **reconstruit**
par profils sectoriels génériques (CAMS-TEMPO, dérivés de GENEMIS, Stuttgart, années 1990).

---

## Page 4 — Résultats du système actuel

**État : ✅ la barre est posée — `reports/CAMS_BENCHMARK.md`**

| Élément | État |
|---|---|
| Accès CDS (ERA5) et ADS (CAMS) | ✅ |
| Performance de CAMS brut contre les stations, J+1 à J+3 | ✅ **mesurée** |
| Biais par typologie de station | ✅ |
| Évaluation FAIRMODE (MQI) | 🟡 calculée, **paramètres à sourcer** |
| Saisonnalité et épisodes | ⬜ un seul mois extrait pour l'instant |

**La référence est `cams-europe-air-quality-forecasts`, pas la réanalyse** — celle-ci
assimile les observations EEA, donc la cible même du projet.

### Performance mesurée (décembre 2024, 476 stations, ~240 000 paires par polluant)

| Polluant | RMSE J+1 | Biais | R² | Dégradation J+1→J+3 |
|---|---|---|---|---|
| NO₂ | 13,70 | −4,41 | +0,073 | **+1,2 %** |
| O₃ | 19,11 | **+9,45** | +0,311 | **+2,2 %** |
| PM2.5 | 8,84 | −0,04 | +0,177 | **+5,3 %** |

### Les trois enseignements qui orientent tout le reste

**1. L'erreur est structurelle, pas chaotique.** Le RMSE n'augmente quasiment pas avec
l'échéance. Une prévision limitée par la divergence de l'atmosphère verrait son erreur
croître nettement ; ici elle est déjà tout entière présente à J+1. Elle vient donc du
**modèle** — émissions, maille, paramétrisations — et non de la météo. C'est exactement
le type d'erreur qu'une correction apprise sait capter, et c'est ce qui **justifie
l'approche du projet**.

**2. Le trafic est le gisement, et il est chiffré.** Sur les stations trafic, CAMS fait
**pire que prédire la moyenne** (NO₂ : R² = −0,299, biais −11,16 µg/m³), contre R² =
+0,100 sur le fond. Une maille de 8 × 11 km ne peut pas résoudre un bord de route. Les
variables d'exposition routière sont déjà construites pour les 476 stations.

**3. Le biais de l'ozone est saisonnier — d'un facteur 3.** Mesuré sur les **17 mois**, le
biais mensuel de CAMS va de **+3,15 µg/m³ en mai à +9,85 en octobre**. Une translation
constante ne peut donc pas convenir : il faut une correction conditionnée à la saison et au
régime météo — ce que confirme l'ablation, où le **calendrier** est la famille de variables la
plus utile (la retirer coûte +9,1 % de RMSE).

**Et la correction tient mois par mois** : le biais résiduel reste entre **−0,16 et +0,22**
µg/m³ sur les douze mois calendaires. Ce n'est donc pas une compensation entre saisons qui
s'annulent en moyenne annuelle, c'est un biais réellement supprimé partout.

Il faut dire l'autre moitié : **CAMS est bien meilleur en été** (R² 0,61 contre 0,31 en
décembre), c'est-à-dire quand l'ozone compte. La marge est plus étroite dans la saison qui
pilote l'indice.

**4. L'été est le point faible du NO₂** — R² ≈ **−0,03** en juillet, à peine mieux que
prédire la moyenne. Concentration estivale basse (10,1 contre 19,3 µg/m³ en janvier),
variabilité dominée par le trafic local que la maille ne voit pas. Même diagnostic que
le point 2, par une autre voie.

### Et une honnêteté qui renforce le propos

Le **MQI reste < 1 partout** (O₃ 0,309 · NO₂ 0,606 · PM2,5 0,488 pour CAMS brut, au grain
imposé par le référentiel — max 8 h, horaire, moyenne journalière) : au sens de FAIRMODE, ces
prévisions sont
**conformes**. Le discours ne peut donc pas être « CAMS se trompe », mais : *ces
prévisions sont conformes et néanmoins porteuses d'une structure d'erreur exploitable,
corrigeable sans toucher au modèle physique.* Position bien plus solide devant un
interlocuteur qui connaît CHIMERE.

---

## Page 5 — Réflexions et pistes d'amélioration

**État : ✅ argumentaire construit**

Cinq angles, par rapport gain/effort décroissant — voir `00_KICKOFF_PROMPT.md` :
1. **Correction de biais (MOS)** des sorties CAMS/PREV'AIR — n'attaque pas leur modèle, l'améliore.
2. **Descente d'échelle géospatiale** — leur maille est à 2-10 km, la LUR descend à 100 m.
3. **Probabiliste** — leurs sorties sont déterministes, or le déclenchement d'alerte est
   asymétrique et se fait **sur prévision** (le texte l'autorise explicitement).
4. **Exposition anisotrope au vent** — rend les couches statiques spatio-temporelles.
5. **Météo-normalisation** — « la baisse vient-elle des émissions ou d'un hiver venteux ? »

⚠️ **Piège à exposer :** la réanalyse CAMS **assimile les observations EEA**, donc la cible
qu'on prédit. Bâtir une correction de biais dessus est partiellement circulaire.

---

## Page 6 — Benchmark de modèles

**État : 🟡 démarré**

| Modèle | État |
|---|---|
| Baselines : persistance H+1/24/48/72, climatologie horaire | ✅ **`reports/BASELINES.md`** |
| **CAMS brut** — la vraie référence à battre | ✅ **`reports/CAMS_BENCHMARK.md`** |
| LUR linéaire sous contrainte de signe | ✅ ajusté et validé, **à l'échelle nationale** |
| Gradient boosting + **hybridation MOS** | ✅ **`reports/MOS.md`** — CAMS battu |

### Le résultat de bout en bout — `reports/INDICE_BOUT_EN_BOUT.md`

Chaîne complète : prévision → concentrations corrigées → sous-indices → classe d'indice.
Comparaison à règles et polluants identiques, 11 225 couples (station, jour).

| | Accord exact | À une classe près | Sur-estimations |
|---|---|---|---|
| CAMS brut | 78,4 % | 95,4 % | 10,0 % |
| **MOS corrigé** | **81,1 %** | **98,2 %** | **6,7 %** |

**+2,7 points d'accord exact.** Mais le chiffre à donner en premier n'est pas celui-là.

### Détection des épisodes — le critère qui décide vraiment

Un taux d'accord traite les erreurs symétriquement ; le métier ne l'est pas. Ne pas
annoncer un épisode qui survient expose la population et engage la responsabilité de
l'AASQA — l'arrêté du 07/04/2016 consacre cette asymétrie en autorisant le déclenchement
**sur prévision**.

| Seuil | | Rappel | Précision | F₂ | Manqués |
|---|---|---|---|---|---|
| ≥ 3 « Dégradé » (n = 2 011) | CAMS | 0,530 | 0,680 | 0,554 | 946 |
| | **MOS** | **0,661** | **0,800** | **0,684** | **698** |
| ≥ 4 « Mauvais » (n = 785) | CAMS | 0,243 | 0,473 | 0,269 | 594 |
| | **MOS** | **0,471** | **0,780** | **0,513** | **442** |
| ≥ 5 « Très mauvais » (n = 27) | CAMS | 0,000 | — | — | 27 |
| | MOS | 0,037 | 0,500 | 0,045 | 26 |

**Le rappel sur les jours « Mauvais » double presque** (24,3 % → 47,1 %), et la précision
monte en même temps (47,3 % → 78,0 %) : ce n'est pas un arbitrage, les deux progressent.
**179 épisodes manqués de moins sur 785.** C'est ce chiffre-là qu'il faut annoncer — la
même mesure, dans l'unité qui engage une AASQA.

⚠️ **À dire en premier, avant qu'on le demande : les deux modèles restent médiocres en
détection.** CAMS manque 76 % des jours « Mauvais », la correction en manque encore 53 %.
Doubler un rappel qui part de 24 % ne fait pas un système d'alerte. Au seuil « Très
mauvais », CAMS détecte 0 épisode sur 27 et la correction 1 — inutilisable. Ce que le
travail démontre, c'est qu'**une part importante de cette insuffisance est apprenable**,
pas que le problème est résolu.

Seule régression : au seuil ≥ 2, le rappel recule de 98,7 % à 96,2 %. Ce seuil sépare
« Bon » de « Moyen ou pire », concerne 94 % des jours, et n'est pas un seuil d'alerte.

**Le chiffre à savoir expliquer :** pourquoi 20 % de RMSE ne font que 2,8 points ? La
correction améliore **57,9 %** des heures, mais seulement **16,2 %** changent de classe.
Le gros du gain se produit **loin des bornes** — passer de 62 à 55 µg/m³ quand la mesure
vaut 52 est une vraie amélioration qui ne change rien à l'affichage. Un gain de
concentration n'est pas un gain de service, et il ne faut pas le présenter comme tel.

### L'erreur de CAMS est structurelle — elle ne croît presque pas avec l'échéance

Barre à battre, refaite sur les 17 mois (`reports/CAMS_BENCHMARK.md`) :

| Polluant | RMSE CAMS J+1 | J+2 | J+3 | dégradation J+1 → J+3 |
|---|---|---|---|---|
| NO₂ | 12,87 | 12,95 | 13,09 | **+1,7 %** |
| O₃ | 16,97 | 17,33 | 17,84 | **+5,1 %** |
| PM2.5 | 5,86 | 5,96 | 6,10 | +4,1 % |

C'est l'argument central du projet : une erreur qui n'augmente quasiment pas de J+1 à J+3
ne vient pas de la divergence météorologique mais du **modèle lui-même** — émissions,
maille, paramétrisations. Elle laisse donc une signature stable, et c'est précisément ce
qu'une correction apprise peut capter.

⚠️ **Le gain de la correction à J+2 et J+3 reste à recalculer sur 17 mois.** Les valeurs
antérieures (+28,4 % et +29,8 %) portaient sur 11 mois et ne sont pas comparables à celles de
ce document. Elles sont retirées plutôt que réutilisées.

### ⭐ Le résultat principal — sur la grandeur réglementaire de chaque polluant

C'est ce tableau qu'il faut citer. Découpage unique, stations exclues de l'entraînement,
17 mois, hyperparamètres réglés en validation imbriquée (`reports/modele_final.csv`).

| Polluant | Grandeur réglementaire | J+1 | J+2 | J+3 |
|---|---|---|---|---|
| **NO₂** | maximum horaire | **+33,2 %** | +33,5 % | +34,2 % |
| **O₃** | maximum journalier 8 h | **+28,9 %** | +29,4 % | +30,6 % |
| **PM2.5** | moyenne journalière | **+30,0 %** | +31,0 % | +31,9 % |

**Ce niveau est celui de l'état de l'art publié.** Riccio & Chianese (2024,
doi:10.5194/acp-24-1673-2024) obtiennent 27 à 30 % sur CAMS avec des **stations exclues** ;
nous obtenons 29 à 34 % sur un protocole équivalent.

**Et le gain croît avec l'échéance**, pour les trois polluants. C'est la confirmation directe
de l'hypothèse fondatrice du projet : une erreur qui ne s'aggrave pas avec l'horizon ne vient
pas de la divergence météorologique mais du modèle lui-même, donc elle est apprenable.

Deux choix expliquent l'essentiel de ce résultat, et **aucun ne concerne les données ni
l'algorithme** :

1. **Apprendre la grandeur réglementaire directement**, au lieu de corriger l'horaire puis
   d'agréger — jusqu'à +6,5 points. Corriger l'horaire écrase les extrêmes, et un maximum
   est une statistique d'extrême.
2. **Donner au modèle la capacité qu'il réclamait** — jusqu'à +5,6 points. Le réglage
   antérieur, justifié dans le code par la crainte de mémoriser le bruit, était trop prudent.

⚠️ Les hyperparamètres ont été choisis sur **O₃ à J+1** : cette cellule rejoue donc en partie
sa propre sélection. Les preuves propres du transfert sont **NO₂ (+1,0 point) et PM2.5
(+4,1 points)**, sur lesquels aucun réglage n'a jamais été optimisé.

### Le détail horaire — 17 mois, J+1, stations exclues

| Polluant | Paires | RMSE CAMS → MOS | Gain | R² | Biais CAMS → MOS |
|---|---|---|---|---|---|
| O₃ | 3,23 M | 16,97 → **13,71** | **+19,2 %** | 0,584 → 0,728 | +6,01 → **−0,06** |
| NO₂ | 3,99 M | 12,87 → **10,30** | **+20,0 %** | 0,125 → 0,439 | −5,83 → **+0,28** |
| NO₂ *avec trafic hiérarchisé* | 3,99 M | 12,87 → **9,05** | **+29,7 %** | 0,125 → 0,567 | |
| PM2.5 | 2,64 M | 5,86 → **4,80** | **+18,1 %** | 0,299 → 0,530 | +0,05 → **+0,01** |

**Le biais est annulé sur les trois polluants** — c'est le résultat le plus régulier du
projet. CAMS surestime l'ozone de 6 µg/m³ et sous-estime le NO₂ de 5,8 ; après correction,
les trois biais tiennent sous 0,3 µg/m³.

Et le NO₂ montre ce que vaut une seule famille de variables : remplacer la pondération des
routes par leur **hiérarchie** (champ `importance` de la BD TOPO) fait passer le gain de
+20,0 à **+29,7 %**, soit **+13,0 %** de RMSE en moins, IC95 [+10,4 ; +15,5] avec 100 % de
tirages positifs sur stations exclues. La **population communale**, elle, n'apporte rien de
mesurable (+0,3 point, intervalles chevauchants) — une économie d'effort, mesurée.

PM2.5 s'améliore dans **toutes** les bandes, y compris ≥ 50 µg/m³ (51,99 → 45,96) —
le polluant qu'aucune variable géographique n'expliquait trouve enfin son levier, du
côté de la correction dynamique et non de la structure du paysage.

### Le gain, et l'axe sur lequel il tient

Correction apprise du **résidu** `observation − CAMS`, entrées limitées à ce qui existe
à l'heure de la prévision (CAMS, géographie, relief, calendrier — **aucune météo
réanalysée**, qui donnerait au modèle un futur que CAMS n'avait pas).

Mesuré sur **17 mois** d'observations appariées (août 2023 → décembre 2024), ozone à J+1,
3,23 M de paires, 270 stations.

Mesure refaite sur la **configuration retenue** — cible réglementaire du jour, capacité
réglée — et journalisée **pli par pli**, ce que la version précédente ne faisait pas. Les
deux réglages sont donnés parce que leur écart est instructif.

| Validation | Ce qui est caché | Plis | Réglage par défaut | Réglage retenu |
|---|---|---|---|---|
| **Spatiale** | stations jamais vues | 3 | +24,7 % (σ 1,8) | **+29,7 %** (σ **1,2**) |
| Temporelle | mois jamais vu | 17 | +9,9 % · pire **−28,1** · 2 plis négatifs | +6,7 % · pire **−35,5** · 5 négatifs |
| **Double aveugle** | **stations *et* mois** | 17 | +4,0 % · pire **−34,7** · 8 négatifs | **+1,5 %** · pire **−41,4** · 7 négatifs |

✅ **La généralisation spatiale est le résultat solide.** σ 1,2 sur trois plis, aucun négatif.
Prédire une station jamais instrumentée fonctionne, de façon reproductible.

❌ **La généralisation temporelle n'est pas démontrée — et une version antérieure de ce
document affirmait le contraire.** Sur sept mois, le pire pli valait +5,4 % et nous en avions
conclu qu'elle était acquise. Sur dix-sept, huit plis sur dix-sept sont négatifs en double
aveugle. Ce n'était pas une propriété du modèle mais l'effet de n'avoir pas encore testé
assez de mois. **Une absence d'échec sur peu de plis n'est pas une démonstration de
robustesse** — c'est la leçon de méthode la plus coûteuse de ce projet.

⚠️ **Et le réglage des hyperparamètres aggrave le problème qu'il prétend traiter.** Il gagne
5 points en spatial (+24,7 → +29,7) et en perd 3 en temporel (+9,9 → +6,7) comme en double
aveugle (+4,0 → +1,5), tout en portant le pire pli de −34,7 à **−41,4**. Les
hyperparamètres ont été choisis contre une validation **spatiale** ; ce qu'ils y gagnent ne
se transporte pas dans le temps. **Un réglage n'est bon que pour l'axe sur lequel il a été
choisi.**

⚠️ **Et une part du gain n'appartient pas au modèle.** Le gain de la correction suit le
défaut du forçage amont : corrélation **+0,953** en `ΔMSE`, stable en leave-one-out (+0,921 à
+0,974). En partageant les jours à la médiane du RMSE de CAMS, la correction rend **+14,0 %**
quand le forçage est bon contre **+23,6 %** quand il dérive. Deux ruptures opérationnelles
CAMS sont documentées (13/11 et 03/12/2024), et **après** chacune CAMS s'améliore tandis que
notre gain baisse. La formulation honnête est donc double : nous corrigeons une structure
d'erreur apprise **et** une régression passagère du forçage.

Ce que cela **ne dit pas** : que la correction nuirait quand le forçage est juste. Elle gagne
encore +14,0 % — elle gagne *moins*, elle ne nuit pas, sauf ponctuellement.

*(Un premier chiffre de +0,913, mesuré sur cinq paires de mois, a été retiré : son
leave-one-out descendait à +0,135. Détail dans `reports/falsification_O3.csv`.)*

Les intervalles de confiance sont désormais bloqués sur **deux** axes — stations *et* mois.
Le seul blocage par station sous-estimait la largeur d'un facteur **1,7** : le gain O₃
s'annonce **[+14,6 ; +21,6]** et non [+16,7 ; +20,8].

**La barre est posée.** Aux horizons réglementaires J+1 à J+3, la référence n'est pas la
persistance mais la **climatologie horaire** : RMSE **12,9 (NO₂) · 19,9 (O₃) · 7,6 (PM2.5)**
µg/m³, sur un test 2023-2024 strictement postérieur à l'apprentissage.

Deux enseignements exploitables en présentation :
- Le R² de la persistance devient **négatif sur les PM2.5 au-delà de 48 h** (−0,15 puis
  −0,29) : la valeur d'avant-hier est *activement trompeuse*. Cohérent avec la physique —
  les épisodes de particules suivent des bascules de régime synoptique.
- La climatologie explique mal les PM2.5 (R² 0,139) : leur variance est **météorologique**,
  pas saisonnière. C'est le polluant où l'apport de la météo sera le plus fort, et celui
  où l'absence d'ERA5 pèse le plus aujourd'hui.

### Le piège qui a failli produire un faux résultat — à raconter en entretien

La première version du MOS apprenait **l'observation** au lieu du résidu. Bilan
apparent : RMSE −13 %, R² 0,529 → 0,645. Publiable, en apparence.

En réalité, elle améliorait la bande < 40 µg/m³ (RMSE 23,5 → 12,3) et **dégradait toutes
les autres** — 120-180 : 24,5 → 41,5. Et surtout : **au seuil d'information de 180 µg/m³,
CAMS détectait 5 dépassements sur 15, la correction 0 sur 15.** Le modèle était meilleur
partout sauf là où il sert.

La cause : 83 % des observations sont sous 80 µg/m³, et minimiser l'erreur quadratique
sur une distribution aussi asymétrique pousse à écraser la queue — les épisodes, c'est-à-
dire le seul régime qui déclenche une décision publique.

**Un RMSE global ne suffit jamais à juger un modèle de qualité de l'air.** Toute
évaluation doit être ventilée par bande de concentration. Figé par un test.

**Résultat négatif, puis sa résolution — la meilleure histoire du projet.** LUR NO₂ sur
16 stations de fond occitanes : R² en apprentissage **0,853**, R² en validation par
station exclue **−1,77**, soit pire que prédire la moyenne. La *même* LUR, mêmes
variables, même protocole, sur les **476 stations métropolitaines** extraites depuis :

| Polluant | Stations de fond | R² (station exclue) | RMSE | Baseline | Gain |
|---|---|---|---|---|---|
| **NO₂** | 246 | **+0,409** | 5,10 | 6,63 | **+23,1 %** |
| **O₃** | 274 | **+0,228** | 7,70 | 8,76 | **+12,1 %** |
| PM2.5 | 176 | +0,039 | 4,95 | 5,05 | +2,0 % |

Biais nul dans les trois cas. Seul l'effectif a changé : le modèle passe d'inutilisable à
utile. C'est la démonstration chiffrée de [[strategie-entrainement-france-occitanie]].

**Et un second résultat négatif, cohérent avec les baselines :** les PM2.5 ne se
prédisent **pas** par le paysage (+2 %). Leur variance est météorologique, pas
structurelle — exactement ce que disait déjà leur R² de climatologie (0,139). Deux
méthodes indépendantes concluent pareil : c'est le polluant qui a besoin d'ERA5, pas de
géographie.

---

## Page 7 — Amélioration du meilleur modèle et tests de preprocessing

**État : 🟡 le cœur différenciant**

| Test | État |
|---|---|
| Distance simple aux objets du paysage | ✅ codé |
| Exposition pondérée `Σ masse × exp(−d/λ)`, balayage de λ sur 6 échelles | ✅ codé |
| **Séparation par essence** : chênes / autres feuillus / conifères | ✅ **signal confirmé** |
| Exposition anisotrope conditionnée au vent | ✅ codé · 🔒 activation |
| Indices topographiques (TPI, pente, profondeur de vallée) | ✅ **476 stations · `reports/RELIEF.md`** |
| Transformation logarithmique des expositions | ✅ **indispensable, démontré** |
| Étude d'ablation : sans géo / distances / pondéré / anisotrope | ⬜ |

### Le relief double le R² de l'ozone — et lui seul

| Polluant | n | Géo seul | Géo + relief | RMSE |
|---|---|---|---|---|
| **O₃** | 274 | +0,228 | **+0,452** | 7,70 → **6,48** |
| NO₂ | 246 | +0,409 | +0,415 | 5,10 → 5,07 |
| PM2.5 | 176 | +0,039 | **−0,001** | 4,95 → 5,06 |

Le contraste est celui que la physique prédit. **L'ozone est secondaire et régional** :
sa concentration dépend de la stagnation de la masse d'air, que la topographie décrit —
la nuit, sous inversion, un fond de vallée voit son ozone détruit par titration au NO,
une crête reste dans la couche résiduelle et le conserve. **Le NO₂ est primaire et
local** : les variables routières disent déjà l'essentiel. **Les PM2.5 n'ont aucun signal
structurel** — ajouter neuf variables ne fait que surajuster, et c'est la *troisième*
méthode indépendante à le conclure.

Et c'est le polluant qui pilote l'indice ATMO occitan à **87,8 %** qui gagne le plus.

**Le cas Chamonix, résolu.** Sur-prédit de 33 µg/m³ sans relief, parce que l'altitude
brute le rangeait avec les crêtes alpines. TPI à 10 km : **−1094** aux Bossons contre
**+224** au Casset. Le MNT est validé indépendamment — altitude corrélée à 0,969 avec le
référentiel, écart médian 3 m.

⚠️ **À ne pas dire :** `tpi_10000m` et `profondeur_vallee_m` corrèlent à −0,90. Le gain
prédictif est réel (validé station exclue), mais **les coefficients individuels ne sont
pas interprétables**. Présenter le gain et le mécanisme, jamais un coefficient isolé.

**L'autre résultat de prétraitement :** à λ court, l'exposition brute s'étale sur **douze
ordres de grandeur** — le modèle explose (R² = −28 595). Le logarithme le ramène à −1,77.
Le prétraitement n'est pas un détail, c'est ce qui décide si le modèle existe.

---

## Page 8 — CHIMERE et potentiels d'évolution

**État : ⬜ à documenter**

| Élément | État |
|---|---|
| Fonctionnement : advection, diffusion turbulente, chimie, aérosols, dépôt | ⬜ |
| Origine (CNRS/INERIS, fin des années 1990) et évolution par versions | ⬜ à vérifier |
| Limites structurelles : émissions, maille urbaine, absence d'apprentissage | 🟡 |
| Voie hybride : physique + correction apprise + incertitude | 🟡 |

⚠️ **À vérifier avant publication** — cette page parle d'un modèle que le recruteur connaît
mieux que nous. Toute affirmation doit être sourcée, et les limites présentées comme des
**compléments possibles**, jamais comme des défauts.

---

## Page 9 — Cartographie comparée

**État : ⬜ dépend des pages 4 et 7**

| Élément | Dépend de |
|---|---|
| Carte de référence (méthode actuelle) | 🔒 CAMS |
| Carte du meilleur modèle détecté | Page 7 |
| Carte d'écart et **d'incertitude spatialisée** | Volet probabiliste |
| Code couleur officiel de l'indice ATMO | ✅ `REGLEMENTAIRE.md` §1.3 |

---

## Page 10 — Tests d'amélioration de CHIMERE (expérimental)

**État : ⬜ à cadrer — la plus ambitieuse, et la plus risquée**

À traiter **seulement si les pages 1 à 9 sont finies**. Restons honnêtes sur ce qui est
faisable en quelques semaines : on ne modifie pas CHIMERE, on **construit une couche
au-dessus** et on mesure ce qu'elle apporte.

Pistes réalistes : correction de biais apprise par typologie et régime météo · descente
d'échelle par features géospatiales · estimation d'incertitude conforme · détection
d'anomalies sur les résidus modèle-observation.

---

## Démo Streamlit

**État : ⬜**

Pages envisagées : carte interactive de l'indice · série temporelle par station avec
bandeau d'incertitude · comparaison modèles · explorateur de variables géospatiales
(effet de λ) · simulateur de conformité sous les seuils 2030.

---

## Prochaines actions, par ordre d'importance

1. ✅ ~~Compte ECMWF~~ — obtenu le 28/07, ERA5 et CAMS téléchargent.
2. ✅ ~~Features géospatiales métropole~~ — 476 stations, 38 variables, terminé.
3. 🟡 **CAMS prévisions → page 4**, la barre à battre. Téléchargement à finir.
4. 🟡 **ERA5 2019-2024** — 144 fichiers, en cours. Débloque la météo-normalisation,
   l'exposition anisotrope, et surtout les PM2.5 que le paysage n'explique pas.
5. ⬜ **RGE ALTI** (~5,5 Go) → indices topographiques. Justifié par la mesure : les
   résidus O₃ sont corrélés à l'altitude (−0,22 ; −5,9 µg/m³ au-dessus de 500 m), alors
   que NO₂ et PM2.5 n'en montrent aucune trace. Mais l'altitude **brute** ne suffira
   pas — Chamonix, fond de vallée à 1035 m, est sur-prédit de 33 µg/m³. C'est la
   position *relative* au relief qu'il faut : TPI, profondeur de vallée, altitude
   relative à la hauteur d'inversion.
6. ⬜ **Gradient boosting** sur les variables géospatiales, puis hybridation MOS.

### Notes d'exploitation Copernicus, vérifiées à la dure

- La licence à accepter est **`cc-by` v1**, pas `licence-to-use-copernicus-products` v12.
  Le HTTP 403 ne nomme pas la licence manquante.
- **3 requêtes simultanées passent, 6 non** : au-delà, le service passe les soumissions
  à l'état `rejected` et le client échoue en HTTP 400 en cherchant leurs résultats. Le
  motif ne se lit que dans `get_jobs`.
- ERA5 livre **deux fichiers par mois** — champs instantanés et champs cumulés. Les
  demander ensemble renvoie une archive ZIP sous une extension `.nc`.
- ADS plafonne à **5000 champs** par requête (jours × échéances × espèces). Un mois de
  prévisions à trois espèces en demande 6789 : on découpe par espèce.
