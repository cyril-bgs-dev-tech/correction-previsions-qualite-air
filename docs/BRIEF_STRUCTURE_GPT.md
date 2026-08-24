# Brief — structurer un projet où chaque correction invalide l'aval

**Ce que je te demande :** comment **organiser** ce travail pour qu'il produise le plus de
valeur, pas quelles pistes tester. Six problèmes structurels reviennent à chaque session et
me coûtent plus que n'importe quelle question scientifique. Réponds en français ; tu n'as
pas accès au dépôt, tout est ici.

---

## Le projet en dix lignes

Post-traitement statistique des prévisions CAMS Europe à J+1, quatre polluants
(NO₂, O₃, PM10, PM2,5). LightGBM sur ~110 colonnes, entraîné sur la France, évalué en
**double aveugle — station ET mois cachés simultanément**, 24 à 33 plis mensuels.

Contrainte fondatrice : le périmètre **PARTOUT** n'a **aucune observation à l'inférence**
(spatialisation là où aucune station n'existe). Un second périmètre, **AUX STATIONS**,
autorise l'historique du site.

Vitrine d'une candidature déjà envoyée ; l'objectif est maintenant la valeur scientifique
et la tenue devant un entretien technique. Un opérateur, une machine, pas de délai.

---

## Problème 1 — Chaque famille a sa propre fenêtre, et l'intersection décide

| famille | couverture | trous |
|---|---|---|
| spéciation · précurseurs · chimie | 2023-08 → 2026-08, **37 mois** | 0 |
| **geoscf v1** | 2023-08 → **2025-12**, 29 mois | 0 |
| ifs | 2024-02 → 2026-07, 24 mois | **6** |
| feux | 2023-08 → **2025-05**, 19 mois | 3 |

`geoscf` **borne l'évaluation à 29 mois** parce que sa v2 est un autre prédicteur. Chaque
famille nouvelle rétrécit l'intersection ou impose un trou — et un mois entièrement absent
est un **indicateur d'époque** sous validation mois-caché : « famille absente » équivaut à
« nous sommes dans ces mois-là ».

J'ai aujourd'hui trois stratégies possibles, et je n'arrive pas à choisir :

1. **intersection stricte** — n'admettre que les familles couvrant toute la fenêtre. Simple,
   mais `geoscf` vaut +0,51 pt démontrés et coûte 8 mois de corpus ;
2. **fenêtres multiples** — une fenêtre par sous-ensemble de familles, donc plusieurs
   chiffres non comparables entre eux ;
3. **imputation déclarée** — garder la famille, marquer l'absence, et espérer que le modèle
   ne l'utilise pas comme date. Mesuré : il l'utilise.

**Question 1.** Existe-t-il une quatrième voie ? Et si l'on doit choisir, sur quel critère —
maximiser les mois, les familles, ou la puissance du test ?

---

## Problème 2 — La chaîne de dépendances rend toute correction amont coûteuse

L'ordre est : **corpus → pile de référence → apports par famille → variantes → verdicts**.
Une correction du corpus invalide tout l'aval. Cette nuit, cinq mois de spéciation ajoutés
ont fait refaire quatre piles, quatre apports et huit ablations jointes — **trois heures de
mesures**. Et deux familles « démontrées » ont cessé de l'être.

J'ai depuis mis en place : une empreinte du corpus, une empreinte des entrées jointes, un
préflight d'intégrité qui refuse de mesurer sur une famille à trou, et un contrat de
génération qui fige le code pendant l'exécution.

**Question 2.** Est-ce la bonne architecture, ou faut-il inverser la dépendance — par
exemple mesurer les apports **relativement** à une ancre insensible au corpus, de sorte
qu'une correction amont ne les invalide plus ? Existe-t-il une forme d'apport qui soit
stable par extension du corpus ?

---

## Problème 3 — Le plan est sous-puissant, et je ne sais pas quoi en conclure

* résolution de l'écart apparié : **±0,36 à ±0,48 %** ;
* plancher de `p` atteignable à 8 blocs de trois mois : **0,0117** — un effet réel mais
  modeste ne PEUT pas y être significatif ;
* taille réelle du test de conjonction partielle : **0,0015**, soit **34 × plus sévère** que
  son seuil nominal.

Résultat : trois familles ont les quatre polluants positifs sans atteindre `p_PC < 0,05`.
Je les classe « non confirmé par PUISSANCE » — mais je ne sais pas distinguer *« l'effet
existe et le plan ne le voit pas »* de *« l'effet n'existe pas »*.

**Question 3.** Face à un plan sous-puissant, faut-il **plus de données**, **un estimand
plus grossier** (par exemple « au moins un polluant » au lieu de « au moins deux »), ou
**abandonner le test d'hypothèse** au profit d'un critère de décision explicite ? Le
protocole double aveugle est-il trop exigeant pour la taille du corpus ?

---

## Problème 4 — Les familles se recouvrent, et leurs apports ne s'additionnent pas

Mesuré entre chimie et précurseurs, sur 524 552 jours-station : R² de chaque variable de
chimie sur l'espace entier des précurseurs entre **0,42 et 0,62**, corrélation par paires
maximale **0,76**.

Leurs apports individuels sur l'ozone — +1,63 et +1,17 pt — **ne s'additionnent pas**. Et
l'ablation individuelle ment dans l'autre sens : deux familles redondantes s'annulent
mutuellement et paraissent toutes deux inutiles.

Le seul estimand que je sache défendre est l'**apport en dernière position** : la pile
complète moins la famille. Il est correct mais il coûte une exécution complète par famille,
et il ne dit rien des groupes.

**Question 4.** Comment décider quoi promouvoir dans un espace où tout se recouvre ?
Faut-il tester des **groupes** plutôt que des familles, et si oui comment les former sans
faire exploser le nombre d'exécutions ?

---

## Problème 5 — Le modèle est chaotique, et je publie des décimales

Mesuré cette nuit :

| | |
|---|---|
| variabilité à données **identiques** | **≤ 0,039 pt** par pli |
| déplacement après **0,14 %** de données en plus | jusqu'à **2,56 pt** par pli, +0,23 en agrégé |

Soit **65 × le bruit d'exécution pour un quatorze-millième du corpus**. Le gradient
boosting n'est pas stable au sens de Lipschitz. Conséquence : la deuxième décimale d'un
gain n'a pas de sens, et la première n'est pas robuste.

Je m'en tire en ne concluant que sur des écarts **appariés** — mêmes plis, même graine —
qui soustraient le déplacement commun. Mais les chiffres publiés dans le dossier, eux, sont
des gains absolus.

**Question 5.** Que publie-t-on comme chiffre principal d'un modèle chaotique ? Une
moyenne sur plusieurs graines et plusieurs perturbations du corpus ? Un intervalle plutôt
qu'un point ? Et comment le présenter à un lecteur qui attend « +41,5 % » ?

---

## Problème 6 — Quatre chiffres par polluant, et je ne sais pas lequel est LE chiffre

| | comparable PARTOUT | comparable STATIONS | auditable PARTOUT | auditable STATIONS |
|---|---|---|---|---|
| NO₂ | 41,52 | 47,94 | 39,94 | 47,35 |
| O₃ | 20,51 | 26,01 | **14,56** | 22,08 |
| PM10 | 21,36 | 27,27 | 17,79 | 25,18 |
| PM2,5 | 13,96 | 22,36 | **8,59** | 19,08 |

* **comparable / auditable** : la seconde écarte les familles portant un mois entièrement
  absent — donc sans indicateur d'époque implicite. Elle coûte jusqu'à **6 points** sur
  l'ozone ;
* **PARTOUT / STATIONS** : le premier respecte la contrainte fondatrice, le second suppose
  un réseau instrumenté.

Les quatre sont défendables, et le plus flatteur n'est pas le plus honnête.

**Question 6.** Combien de chiffres un dossier technique peut-il porter sans devenir
illisible ni suspect ? Faut-il un chiffre principal et trois réserves, une matrice
assumée, ou choisir le plus conservateur et mentionner les autres ?

---

## Problème 7 — Le criblage, et ce que j'ai le droit d'en tirer

J'ai testé une dizaine de configurations sur le même corpus. La calibration mesurée dit
que **le criblage ne consomme pas le budget** : la conjonction partielle est si sévère que
le seuil ajusté à 5 % d'erreur de famille vaut **0,0974**, donc plus lâche que 0,05.

Mais ce chiffre ne compte que les configurations **écrites en CSV**. Les pistes abandonnées
avant d'écrire un fichier ne sont pas comptées, et il y en a eu.

**Question 7.** Comment compter honnêtement un criblage dont une partie n'a laissé aucune
trace ? Faut-il un registre d'hypothèses **avant** exécution — j'en ai un pour les
prédictions d'effet — et l'étendre à toute configuration envisagée ?

---

## Ce dont je dispose

32 cœurs (un lot LightGBM à la fois, mesuré : trois concurrents s'effondrent d'un ordre de
grandeur), une acquisition réseau parallèle, ~30 min par exécution de pile et par polluant,
~10 min par criblage d'apport. Aucune contrainte de délai.

**Sois direct, et priorise.** Si l'un de ces six problèmes rend les cinq autres
secondaires, dis-le. Si l'architecture actuelle est correcte et que je cherche des
raffinements inutiles, dis-le aussi.
