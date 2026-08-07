# Prompt GPT — R16 · Les zones d'ombre, à quinze jours du dépôt

> À coller tel quel. Rédigé le **07/08/2026**. R15 (02/08) cherchait la qualité du travail ;
> celui-ci cherche **ce que je ne sais pas que j'ignore**.
>
> Depuis R15, six choses ont changé : la référence n'est plus CAMS brut mais **la chaîne
> réellement en service** ; un modèle **extérieur à Copernicus** (GEOS-CF, NASA) est entré
> dans la pile ; les quatre polluants ont tous les cinq étages d'évaluation ; le système
> produit désormais un **champ spatialisé** et non plus seulement des points ; la mesure la
> plus dure du dossier a été faite — contre les **épisodes réellement déclenchés par
> procédure préfectorale**, et elle est mauvaise ; et le poste visé s'est précisé : pôle
> **Partenariats** d'une AASQA, clôture le **22 août 2026**.
>
> **Toute la mesure est faite. Je ne cherche pas un gain de plus.** Je cherche trois choses,
> dans cet ordre : (a) ce qui, dans ce que je publie, **ne tiendrait pas** devant un
> praticien du domaine ; (b) l'information **réglementaire et opérationnelle** qui me manque
> et que je ne peux pas déduire de mes données ; (c) le **petit geste à fort rendement**,
> tenable en moins d'une journée.

---

## Ce que fait le système

Post-traitement statistique des prévisions **CAMS Europe** (ensemble régional, maille
≈ 8 × 11 km) sur **476 stations françaises**, quatre polluants — O₃, NO₂, PM10, PM2,5.
Un LightGBM apprend le **résidu `observation − CAMS`** à la maille journalière, à partir de
~60 prédicteurs : sortie CAMS et ses six membres, terrain et paysage (MNT Copernicus GLO-30,
BD TOPO, trafic hiérarchisé), typologie de station, calendrier, feux GFAS, GEOS-CF, et —
dans une variante seulement — l'historique récent de la station elle-même.

Le corpus complet va d'**août 2023 à juillet 2026** — 36 mois pour O₃, NO₂ et PM2,5.
Les **PM10 sont le parent pauvre** : leurs membres d'ensemble n'existent que depuis 2025-01,
ce qui donne deux variantes légitimes, 19 mois avec eux et 31 sans. Et la fenêtre des mesures
en double aveugle est plus courte que le corpus — 29 mois (24 pour PM10) — parce qu'elle est
bornée par la disponibilité du flux GEOS-CF v1.

Le système produit aussi, depuis peu, un **champ corrigé au pas de 0,1°** sur la France,
l'Occitanie et la Nouvelle-Aquitaine — c'est le champ du modèle affiché tel quel, sans
interpolation. Contrôle par région, en NO₂, moyenne aux stations de fond :

| | observé | CAMS brut | corrigé |
|---|---|---|---|
| Occitanie | 20,2 | **3,3** | 17,8 |
| France | 20,4 | 4,7 | 16,4 |

Le champ européen brut est **quatre à six fois trop bas** en NO₂ ; corrigé, il tombe à
0,1–4 µg/m³ du niveau réel.

---

## Les chiffres, avec leur protocole — ils ne sont **pas** interchangeables

C'est le point le plus important de ce brief. Le projet produit **cinq familles de gains**
qui portent des noms voisins et mesurent des choses différentes. Sur l'ozone elles valent
+22,43 %, +21,66 %, +13,75 %, +9,2 % et +3,31 % — toutes justes, aucune interchangeable.

| # | protocole | échéance | O₃ | NO₂ | PM10 | PM2,5 |
|---|---|---|---|---|---|---|
| ①a | **production**, origine glissante, **station connue**, contre la chaîne en service | J0 | +22,43 % | +44,16 % | +25,90 % | +19,22 % |
| ② | double aveugle **station + mois cachés**, pile complète **+ historique du site** — « AUX STATIONS » | J+2 | +21,66 % | +45,85 % | +23,76 % | +19,60 % |
| ③ | idem **sans** l'historique du site — « **PARTOUT** », le périmètre de la spatialisation | J+2 | **+13,75 %** | **+38,71 %** | +17,43 % | +9,90 % |
| ④ | apport de la **seule** observation antérieure | J+2 | +9,2 % | +22,8 % | — | +9,3 % |
| ⑤ | double aveugle **de base**, sans aucun levier | J+2 | **+3,31 %** | +25,71 % | +11,36 % | +5,14 % |

**③ est la seule revendication propre** — prédire là où rien ne mesure — et c'est la plus
basse. **⑤ → ③ est la démonstration de la méthode** : sur l'ozone, la pile fait passer le
double aveugle de +3,31 % à +13,75 %.

L'étage par étage de ③ (double aveugle, J+2) :

| étage | NO₂ | O₃ | PM10 | PM2,5 |
|---|---|---|---|---|
| base (CAMS, terrain, calendrier) | +26,61 % | +7,01 % | +8,52 % | +2,08 % |
| + typologie de station | +35,58 % | +6,88 % | +10,12 % | +2,24 % |
| + membres d'ensemble | +36,13 % | +9,83 % | +14,20 % | +5,76 % |
| + feux (GFAS) | +36,38 % | +11,93 % | +15,09 % | +7,80 % |
| + **GEOS-CF** | **+38,71 %** | **+13,75 %** | **+17,43 %** | **+9,90 %** |
| *(plafond ERA5, réanalyse, NON déployable)* | *+49,28 %* | *+25,41 %* | *+26,22 %* | *+23,61 %* |

Trois autres résultats à connaître pour répondre :

- **FAIRMODE.** MQI (JRC120649 v3.2, β = 2) au grain que le tableau 6 impose par polluant :
  O₃ 0,309 → 0,255 · NO₂ 0,606 → 0,485 · PM2,5 0,488 → 0,354, tous conformes. Mais station
  par station, **98,5 %** seulement de conformité en NO₂ (pire MQI 1,24 ; 95 % sur les
  stations trafic). Et sur l'indicateur de **prévision** `MQI_f` à J+1 : CAMS brut ne rend
  que **41,4 %** de stations conformes en NO₂ — moins bien que répéter la mesure
  d'avant-veille — contre **96,2 %** après correction.
- **Détection.** À budget de fausses alertes fixé et point de fonctionnement choisi hors
  échantillon, sur la **valeur cible européenne** d'ozone (120 µg/m³ en max 8 h) : rappel
  0,656 contre 0,184 à 30 % de budget, soit **3,6×** ; reproduit à 3,5× sur 2025 jamais vu.
  ⚠️ Mais **le même effet ne survit pas au double aveugle** : ×1,18, intervalle contenant zéro.
- **L'essentiel du gain ne demande aucun apprentissage.** Une moyenne glissante du résidu sur
  7 jours — cinq lignes — récupère **+42,9 %** sur le NO₂ à J+1 ; le LightGBM complet en
  récupère 44,3 %. L'apport propre du modèle est de **+2,5 points** (et +5,4 sur O₃).

---

## Le résultat qui me gêne le plus, et sur lequel porte la question 1

Tout le dossier compte des « épisodes » au sens **journée-station en classe ATMO ≥ 3** —
des milliers d'occurrences. Mais un déclenchement **réel** est une *zone-jour sous procédure
préfectorale*, et l'AASQA en publie la liste : **52 en quatorze mois** en Occitanie —
**PM10 40 · O₃ 12 · NO₂ 0**.

Évalué contre cette vérité terrain, sur les PM10 (33 épisodes, 5 174 zones-jours) :

| système | attrapés | rappel | fausses alertes | précision |
|---|---|---|---|---|
| l'**observation** elle-même | 21/33 | 63,6 % | 18 | 53,8 % |
| CAMS brut | 1/33 | 3,0 % | 3 | 25,0 % |
| chaîne AASQA | 1/33 | 3,0 % | 9 | 10,0 % |
| **notre modèle** | **2/33** | 6,1 % | 11 | 15,4 % |

Sur l'ozone, l'inverse : nous attrapons **12/12** mais avec 473 fausses alertes, quand CAMS
brut en rate le tiers avec 102.

⚠️ **Le fait qui me fait douter de la question elle-même :** sur les 33 épisodes PM10,
**douze n'ont aucune station au-dessus de 50 µg/m³ en moyenne journalière** — pas même les
mesures. La procédure se déclenche donc sur *autre chose* que la grandeur que je prédis.

---

## Ce qui est déjà tranché — ne pas le reproposer sans réfuter la mesure

Chacune de ces pistes a été **mesurée** puis abandonnée. Si tu veux en réactiver une, il faut
attaquer la mesure, pas proposer l'idée.

| piste | verdict mesuré |
|---|---|
| réseaux de neurones sur graphe / information de voisinage | **+0,28 point**, 7× sous le critère de rétention |
| TROPOMI (NO₂ satellite) | **nul sur 12 cases**, deux protocoles, trois polluants |
| sol, géologie | gains **11× sous** le critère d'arrêt ; le témoin ozone réfute le mécanisme |
| copolluants, chimie inter-espèces, couvert forestier | **nul** — CAMS les modélise déjà |
| détecteur d'anomalie comme coupe-circuit | **négatif** : les états inhabituels sont ceux où la correction sert le plus |
| classification, perte pondérée, régression quantile pour la détection | **rien** dès que le seuil est libre : ce qui décide est le **rang** |
| réglage d'hyperparamètres (Optuna, 201 essais) | **10 défaites sur 10** sur l'axe déployable ; le réglage **dégrade** l'axe temporel |
| hybridation avec la chaîne AASQA (empilage) | +0,02 / −0,03 / −0,32 / −1,11 |
| moyenne nue avec GEOS-CF | **pire que CAMS seul** partout — il faut l'entrer en *variable*, pas en mélange |
| dispersion d'ensemble comme prédicteur | **nulle** — utile en *méfiance* (×6,6 du décile concordant au divergent), pas en prédiction |
| réentraînement continu mensuel | **−0,02 µg/m³**, nul : le réseau régional n'ajoute que 2 % de volume |
| prolonger ERA5 | réanalyse ⇒ **plafond non déployable**, pas une méthode |
| recalage saisonnier d'amplitude | corrige un défaut réel mais **n'ajoute aucune information** |

---

## Question 1 — Le déclenchement d'un épisode : ma mesure la plus dure est peut-être **mal posée**

**Le fait.** Ci-dessus. 2 épisodes PM10 sur 33, mais l'observation elle-même n'en voit que
21, et douze n'ont aucune station au seuil journalier.

**Ce que je demande.**

1. Quel est le **texte exact** qui régit le déclenchement d'une procédure préfectorale en
   France — arrêté interministériel, arrêtés préfectoraux zonaux, guides du ministère ?
   Donne les **critères opposables** : sur quelle grandeur (max horaire ? moyenne
   journalière ? prévision ou constat ?), quel seuil, quel **critère spatial**
   (superficie minimale, population exposée, nombre de stations), quelle **durée**.
2. Un déclenchement peut-il reposer sur un **critère de surface modélisée** plutôt que sur
   des stations ? Si oui, ma comparaison station-par-station est mal posée — **comment la
   reposer** avec les seules données publiques ?
3. Comment les AASQA **évaluent-elles elles-mêmes** leur prévision d'épisode ? Existe-t-il
   des bilans publiés avec POD / FAR / taux de déclenchement justifié ? Quels **ordres de
   grandeur** — pour savoir si 2/33 est catastrophique ou banal dans le métier ?
4. Quelles explications plausibles pour « douze épisodes sans aucune station au seuil » :
   critère sur le max horaire, déclenchement anticipé sur prévision, critère de
   **persistance** (deux jours à 50 µg/m³), zonage administratif ≠ zone de surveillance,
   décision d'expertise humaine ? Laquelle est la plus probable, et **comment la vérifier** ?
5. Si l'endpoint est mal posé : quel est l'**endpoint honnête** que je peux mesurer avec des
   stations et une vérité terrain publiée — et que je puisse défendre en entretien sans
   avoir l'air de m'être choisi une épreuve facile ?

## Question 2 — Les PM10, polluant qui décide et angle mort de mes entrées

**Le fait.** **40 des 52** procédures portent sur les PM10 — le polluant sur lequel tous les
systèmes, y compris le mien, sont quasi aveugles. Or mes prédicteurs ne contiennent **aucune
information explicite** sur les moteurs connus des PM10 : intrusions sahariennes, chauffage
au bois, épandage agricole de printemps, sel marin, remise en suspension routière.

**Ce que je demande.**

1. Quels **produits opérationnels et libres** prévoient les intrusions désertiques sur la
   France — CAMS global (AOD poussière), WMO SDS-WAS, BSC-DREAM8b / MONARCH, autre ? À quelle
   latence, quelle résolution, quelle licence, et **utilisables en variable quotidienne** ?
2. La part désertique est-elle **déjà** dans CAMS régional par ses conditions aux limites ?
   Si oui, qu'apporterait une variable de poussière explicite — et est-ce mesuré quelque part ?
3. Quels **proxys** de chauffage au bois (degrés-jours de chauffe, inversion thermique,
   effet week-end) et d'épandage agricole (calendrier réglementaire, seuils de température,
   inventaires d'émissions régionaux) sont réellement utilisés dans la littérature de
   post-traitement ?
4. La **remise en suspension** et le sel marin sont-ils approchables sans modèle dédié ?
5. Existe-t-il des travaux qui **quantifient** — pas qui justifient physiquement — le gain
   d'ajouter ces familles à une correction statistique de PM10 ? Je veux des points de
   pourcentage, sinon je n'ai aucun moyen de décider si ça vaut mes quinze jours.

## Question 3 — La directive (UE) 2024/2881 : ce qu'elle exige de la **modélisation**, et quand

**Le contexte.** C'est le cadre dans lequel travaillera l'employeur pour les cinq prochaines
années, et je ne le connais pas précisément. Je sais que la refonte est entrée en vigueur fin
2024, que la transposition est due fin 2026 et que les valeurs limites changent en 2030.
Je ne sais pas ce qu'elle dit de la **modélisation**.

**Ce que je demande.**

1. Dans quels cas les **applications de modélisation** deviennent-elles obligatoires, pour
   quels usages (localisation des dépassements, plans qualité de l'air, information du
   public, prévision), et à quelles échéances ? Cite les **articles et annexes**.
2. Quels **objectifs de qualité de modélisation** deviennent opposables ? Quel est leur
   énoncé exact, et quel est le lien avec **FAIRMODE** et son MQI — la v4.0 (2026) est-elle
   celle qui fait foi ?
3. Que devient l'obligation de **prévision à court terme** et d'information du public :
   les seuils d'information et d'alerte changent-ils, les plans d'action à court terme
   sont-ils renforcés ?
4. Concrètement, pour une AASQA en 2026-2030 : quels **nouveaux livrables**, quels
   chantiers, quelles compétences deviennent recherchées ?
5. Où mon travail s'inscrit-il dans ce cadre — et **où n'a-t-il aucune valeur** au regard du
   texte ? Sois franc : si le post-traitement statistique n'est pas ce que la directive
   demande, je préfère le savoir avant l'entretien que pendant.

## Question 4 — Évaluer un **champ**, et non des points

**Le fait.** Je produis maintenant un champ corrigé à 0,1° sur trois emprises, et je le
valide… **aux stations**. Or ce sont exactement les stations qui ont servi à l'apprentissage
et, pour la variante krigée, à l'ancrage. La station est à la fois l'appui et le juge.

**Ce que je demande.**

1. Quel est le **protocole accepté** pour valider un champ spatialisé quand les seules
   mesures disponibles sont les stations qui l'ont construit — validation croisée par station
   retirée, par bloc spatial, jackknife du krigeage, réseau indépendant ?
2. Quelles **métriques spatiales** ont un sens ici — score de fraction (FSS), SAL,
   variogramme des résidus, erreur par classe de représentativité — et lesquelles sont du
   folklore importé de la météorologie sans transposer ?
3. Comment PREV'AIR et les AASQA **publient-ils** la validation de leur produit krigé ?
   Quels indicateurs, quelle fréquence, dans quels documents publics ?
4. La **circularité** station-appui / station-juge : comment les praticiens la traitent-ils,
   et quelle formulation honnête puis-je employer pour la reconnaître sans invalider le
   produit ?
5. Quelle **borne d'erreur honnête** peut-on annoncer en un point sans station ? J'avais
   comparé la dispersion entre stations d'une même commune à ma RMSE et trouvé les deux du
   même ordre, d'où l'idée d'un **plancher de représentativité** : je ne pourrais pas faire
   mieux que ce que deux stations voisines se disent l'une de l'autre. Cette mesure est
   ancienne et je ne la rejoue pas ici. **La lecture est-elle juste** ? Comment un praticien
   définit-il et publie-t-il la représentativité spatiale d'une station, et existe-t-il une
   méthode normalisée pour la chiffrer ?

## Question 5 — Les microcapteurs peuvent-ils **étendre le périmètre déployable** ?

**Le fait.** Mon levier le plus fort est l'historique récent de la station elle-même : il
vaut **+7,1 points sur NO₂ et +7,9 sur O₃** (l'écart entre ③ « PARTOUT » et ② « AUX
STATIONS »). Il n'est disponible que là où une station de référence existe — 476 points pour
la France. Les AASQA exploitent par ailleurs des réseaux de **microcapteurs** et des campagnes
citoyennes. Le poste visé est au pôle **Partenariats**, donc précisément là où ces réseaux se
montent.

**Ce que je demande.**

1. Un réseau de microcapteurs **corrigés** peut-il servir d'observation d'ancrage à une
   correction de biais ? Quelle exactitude réaliste après calibration terrain, quelle dérive,
   quelle procédure de recalage — et pour quels polluants (le NO₂ étant réputé le plus dur) ?
2. Que dit la **doctrine française** (LCSQA, Atmo France) sur l'usage des microcapteurs :
   indicatif, complémentaire, exclu du réglementaire ? Que peut-on en publier légitimement ?
3. Existe-t-il des **flux ouverts** exploitables en France — réseaux citoyens,
   Sensor.Community, campagnes AASQA — avec des métadonnées de position et de calibration
   suffisantes ?
4. Des travaux ont-ils **mesuré** le gain d'une densification par capteurs sur une correction
   de modèle de chimie-transport ? Et le risque symétrique : que se passe-t-il quand un
   capteur dérive et que le modèle s'y ancre ?
5. Côté **partenariats** : quels montages existent (collectivités, industriels,
   établissements scolaires, projets européens), quels livrables en sortent, et lequel serait
   crédible à proposer par un candidat junior sans promettre l'impossible ?

## Question 6 — Audit adverse : **attaque** ce que je publie

**Ce que je demande.** Prends les affirmations ci-dessus avec leurs protocoles et joue
l'évaluateur hostile — un ingénieur d'AASQA ou du LCSQA qui a vingt ans de métier.

1. Lesquelles de ces affirmations **refuserait-il**, et sur quel motif précis ?
2. Quelle est la **question la plus destructrice** qu'on peut me poser en entretien sur ce
   dossier — et existe-t-il une réponse honnête, ou faut-il retirer l'affirmation ?
3. Y a-t-il une **incohérence interne** entre ces chiffres que je n'aurais pas vue ? Par
   exemple : je revendique 3,6× plus de dépassements d'ozone détectés, et 12/12 épisodes
   réels attrapés — mais avec 473 fausses alertes, et un effet qui ne survit pas au double
   aveugle. Est-ce que ces trois énoncés peuvent coexister dans un même dossier ?
4. Le fait que **l'essentiel du gain vienne d'une moyenne glissante** : aveu de faiblesse, ou
   résultat connu et publié ? Que rapporte la littérature comme **apport marginal** de
   l'apprentissage au-dessus d'une correction de biais adaptative — y a-t-il un chiffre de
   référence auquel comparer mes +2,5 points ?
5. Si tu ne devais garder **qu'un seul chiffre** de tout ce dossier pour une candidature de
   data scientist junior dans une AASQA, lequel, et pourquoi celui-là plutôt que le plus
   spectaculaire ?

## Question 7 — Ce que je n'ai pas demandé

C'est la question à plus forte valeur du fichier. Les six précédentes ne peuvent porter que
sur ce que je sais déjà ignorer.

1. Au vu de ce brief, qu'est-ce qui **manque** — une donnée, un contrôle, une comparaison,
   une réserve, une convention — que je n'ai ni mesuré ni listé ?
2. Quelle question aurais-tu posée **à ma place**, et que je n'ai pas posée ?
3. Existe-t-il un travail publié **très proche** du mien que je devrais citer — ou dont je
   devrais explicitement me distinguer — et que je ne cite pas ?
4. Quel est le **plus petit geste**, tenable en moins d'une journée, qui augmenterait le plus
   la crédibilité du dossier ?
5. Quel est le plus grand **risque de ridicule** : l'erreur de vocabulaire, d'unité ou de
   convention qui ferait dire à un praticien « cette personne n'a jamais vu de données de
   qualité de l'air » ? Le projet en a déjà commis une — avoir appelé « J+1 » pendant des
   semaines des prévisions qui étaient du **J0**, parce que l'échéance 0 h d'une sortie de
   00 UTC porte l'horodatage du jour même. J'en cherche les jumelles.

---

## Contraintes de réponse

- **Cite tes sources.** Texte réglementaire avec l'article ou l'annexe, rapport avec sa page,
  article avec son année et son DOI. Une affirmation non sourcée m'est inutilisable : la
  règle du projet est que tout chiffre du dossier doit remonter à un artefact ou à une source.
- **Sur les questions 1 et 3, je veux du texte exact**, pas un résumé de principes : seuils,
  critères, articles. C'est ce que je ne peux pas déduire de mes données.
- **Distingue trois registres** : ce qui est établi et sourcé · ce qui est pratique courante
  sans être écrit · ce que tu extrapoles. Étiquette-les.
- **Si tu ne sais pas, dis-le.** Un seuil réglementaire inventé me coûterait un entretien.
  Une incertitude nommée ne me coûte rien.
- **Ne propose rien qui figure dans « déjà tranché »** sans attaquer d'abord la mesure qui l'a
  écarté.
- **Hiérarchise, et dis ce qui est du luxe.** Il reste **quinze jours** et le dépôt prime sur
  toute amélioration. Une liste de bonnes pratiques irréalisable m'est moins utile qu'un
  sous-ensemble ordonné par rendement.
- **Distingue ce qui sert le dossier de ce qui sert le poste.** Ce ne sont pas les mêmes
  gestes, et je ne les confonds plus.
- Réponds en **français**, avec la terminologie du métier.

*Réponses attendues dans `docs/GPT_R16.md`.*
