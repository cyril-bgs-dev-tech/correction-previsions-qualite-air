# Thèse et cadrage — ce que ce projet démontre réellement

> **En une phrase.** Le gain d'une correction apprise **n'est pas uniforme** : il se concentre
> là où le forçage dérive, reste positif mais réduit quand le forçage est juste, et devient
> **négatif certains jours** — une dépendance mesurable, stable, et traitable par une règle
> d'abstention appliquée au jour.

> ### ⚠️ Version 2 — après falsification (30/07, `docs/GPT_FALSIFICATION.md`)
>
> La version 1 affirmait que la correction « **nuit** quand le forçage est juste ». **C'est
> faux** : sur les mois où CAMS est bon, elle gagne encore **+14,0 %** (contre +23,6 % quand
> il est mauvais). Elle gagne moins, elle ne nuit pas.
>
> Et le noyau du mécanisme est **déjà publié** — *non-stationnarité de l'erreur du modèle
> amont* : Demaeyer & Vannitsem 2020 (doi:10.5194/npg-27-307-2020), Hamill 2017
> (doi:10.1175/MWR-D-17-0067.1), Huang et al. 2017 (doi:10.1175/WAF-D-16-0118.1). CAMS
> reconstruit d'ailleurs son propre MOS à chaque changement de membre. **On cite, on ne
> revendique pas.**
>
> Ce qui reste propre au projet : la **quantification** sur CAMS Europe, et la règle
> d'abstention qui en découle.

Ce document remplace la juxtaposition de résultats par un fil unique. Chaque affirmation
porte les mesures qui l'étayent — toutes sur **stations exclues de l'entraînement**,
17 mois (août 2023 → décembre 2024), sauf mention contraire.

---

## 1. Le déplacement de l'objet

| | Question | Statut |
|---|---|---|
| **Au départ** | Peut-on corriger CAMS par apprentissage ? | **Déjà répondue** — PREV'AIR le fait, la littérature aussi |
| **Traitée en fait** | **Quand faut-il corriger, et quand s'abstenir ?** | **Sans réponse publiée** |

Le premier objet est clos par les chiffres eux-mêmes : nos **+28,9 à +34,2 %** sur les
grandeurs réglementaires égalent Riccio & Chianese 2024 (27-30 %, stations exclues,
doi:10.5194/acp-24-1673-2024) sans les dépasser. Une performance qui rejoint l'état de l'art
ne constitue pas une contribution ; elle constitue une **preuve de maîtrise**, ce qui est
différent et suffisant pour une candidature.

Le second objet est né des échecs, pas des succès — et c'est lui qui porte la valeur.

---

## 2. Le mécanisme — ce qui survit à la falsification

**Le gain dépend de la qualité du forçage, mais ne s'inverse pas en moyenne.**

| Test | Mesure | Ce qu'il établit |
|---|---|---|
| **Métrique découplée** | `ΔMSE` (différence absolue, sans ratio) : **r = +0,953**, leave-one-out +0,921 à +0,974 | la dépendance est **réelle** — elle se renforce quand on retire le dénominateur suspect |
| **Partage à la médiane** | CAMS bon : +14,0 % · CAMS mauvais : **+23,6 %** | le gain est **1,7 fois plus fort** là où le forçage dérive |
| **Correcteur nul** | débiaisage fixe : r = +0,736 | une part est mécanique, mais le correcteur appris fait **nettement mieux** |
| **Cas ponctuel** | **26/07/2026** : CAMS 49,6, obs 46,8, corrigé **36,6** | au **jour**, la correction peut dégrader une prévision juste de 12,9 µg/m³ |

**Ce qui est tombé.** Le chiffre de +0,913 initialement cité était **instable** : son
leave-one-out va de **+0,135** à +0,913 — un seul mois retiré le fait passer de 0,14 à 0,91.
Il est remplacé par le **+0,953 en `ΔMSE`**, stable.

**L'abstraction, corrigée.** Un correcteur appris sur les erreurs d'un système apprend la
moyenne conditionnelle de ces erreurs **sur la période observée**. Il reste utile hors de
cette période, mais son bénéfice **décroît à mesure que le forçage s'améliore** — et peut
s'inverser sur des journées particulières. Ce n'est pas un défaut d'implémentation : c'est
une propriété de l'approche, connue en météorologie sous le nom de **non-stationnarité de
l'erreur du modèle amont**.

---

## 3. Quatre invariants que les mesures imposent

### 3.1 La cible pèse vingt fois plus que le modèle

| Levier | Effet mesuré |
|---|---|
| Changer la **cible** (grandeur réglementaire apprise directement) | **+5,8 pts** (O₃), **+6,5 pts** (NO₂) |
| Changer la **bibliothèque** (LightGBM / XGBoost / CatBoost) | **0,3 pt** |
| Changer la **famille** (linéaire → forêt → boosting) | +8,9 % → +14,9 % → +19,4 % |

Et le témoin qui borne le tout : un **débiaisage sans apprentissage** atteint **+7,3 %** sur
station inconnue. L'apprentissage linéaire n'ajoute presque rien (+8,9 %) ; tout le gain
vient de la capacité à capturer des interactions.

### 3.2 Tout gain sur un axe se paie sur un autre

| Décision | Gagne | Perd |
|---|---|---|
| Cible journalière + capacité triplée | spatial **+19,4 → +29,7 %** (σ 1,8 → **1,2**) | double aveugle **+8,7 → +1,5 %** |
| Perte pondérée sur la queue | queue **−3,1 → +8,5 %** | global −7 pts |
| Commutation à 70 µg/m³ | queue **−3,1 → +3,1 %** | **rien** (RMSE global identique) |

La dernière ligne est la seule domination stricte trouvée — et elle n'existe que parce qu'on
a cherché le point où l'arbitrage disparaît, au lieu de choisir un côté.

### 3.3 Mesurer mieux fait d'abord baisser les chiffres

`28,3 %` → `24,2 %` → `19,3 %` — chaque durcissement de protocole a dégradé le résultat
affiché, avant que le changement de cible ne le remonte à **28,9 %**. Et une affirmation a dû
être **retirée** : « la généralisation temporelle est démontrée », écrite sur 7 mois où le
pire pli valait +5,4 %, réfutée sur 17 mois où il tombe à **−35,5 %**.

Une courbe de performance qui ne descend jamais signale un protocole qui ne se durcit jamais.

### 3.4 L'incohérence détecte mieux que la vérification

Le bug du double aveugle n'a pas été trouvé en relisant le code, mais parce que le résultat
était **impossible** : cacher stations *et* mois donnait **+33,9 %** contre **+6,7 %** en
cachant les mois seuls. Corrigé : **+1,5 %**.

Un invariant d'ordre entre épreuves détecte ce qu'aucune relecture ne voit, parce qu'il ne
dépend pas de l'attention du relecteur.

---

## 4. Ce que la thèse génère

### 4.1 Une contribution qui n'est pas une performance

**La cartographie des conditions de légitimité** d'une correction apprise : elle vaut quand
le forçage dérive, elle nuit quand il est juste — et cette condition est **observable à
l'émission**, puisque la prévision brute annonce elle-même si elle a besoin d'être corrigée.

### 4.2 Une règle vérifiable, née d'un échec daté

> **Ne pas corriger à la baisse quand le forçage annonce déjà un dépassement.**

Le 26/07/2026, cette règle aurait évité une dégradation de 12,9 µg/m³. Les 25 et 27/07, elle
n'aurait rien changé — ni rien coûté.

### 4.3 Un produit qui change de nature

Un correcteur sans politique d'abstention n'est pas imparfait : il est **incomplet**. Le
livrable devient « un modèle qui corrige **et qui sait quand ne pas le faire** ».

### 4.4 Un récit qui résiste à la contradiction

| Énoncé | Solidité |
|---|---|
| « J'améliore une prévision de 30 % » | vrai, banal, et **en partie imputable** à une dérive du forçage (+0,953 en ΔMSE ; +14,0 % quand le forçage est bon contre +23,6 % quand il dérive) |
| « J'ai mesuré à quelles conditions une correction est légitime, et construit le garde-fou » | **se vérifie**, et ne se conteste pas en une question |

---

## 5. Les chiffres à citer

### Performance — grandeur réglementaire, stations exclues, hyperparamètres réglés

| Polluant | Grandeur | J+1 | J+2 | J+3 |
|---|---|---|---|---|
| **NO₂** | max horaire | **+33,2 %** | +33,5 % | +34,2 % |
| **O₃** | max 8 h | **+28,9 %** | +29,4 % | +30,6 % |
| **PM2.5** | moyenne journalière | **+30,0 %** | +31,0 % | +31,9 % |

⚠️ Ces valeurs sont en validation **spatiale**. En double aveugle, la même configuration ne
rend que **+1,5 %**. Ne jamais citer la première sans la seconde.

### Généralisation — les trois épreuves

| Ce qui est caché | Gain | Pire pli |
|---|---|---|
| stations jamais vues | **+29,7 %** (σ 1,2) | +27,9 % |
| mois jamais vu | +6,7 % | **−35,5 %** |
| stations **et** mois | +1,5 % | **−41,4 %** |

Et l'épreuve la plus dure, hors protocole : **rejeu de juillet 2026**, dix-neuf mois après la
fin de l'apprentissage — **+15,3 %** de gain, biais divisé par deux (−3,52 → −1,94).

### Service rendu — détection d'épisodes

| Polluant | Brier skill | POD brut → corrigé | CSI |
|---|---|---|---|
| O₃ (120 µg/m³) | **+0,460** | 0,360 → **0,663** | 0,299 → **0,464** |
| PM2.5 (25 µg/m³) | **+0,351** | 0,198 → **0,417** | 0,128 → **0,359** |
| NO₂ (120 µg/m³) | +0,017 | 0,007 → 0,084 | **inutilisable** |

Le CSI d'ozone de **0,464** dépasse la fourchette publiée par Bertrand et al. (0,30-0,40),
sur un protocole plus sévère puisqu'il exclut les stations.

### Variables — ce qui paie et ce qui ne paie pas

| | Effet |
|---|---|
| Hiérarchie routière (`importance` BD TOPO) | **+13,0 %** sur NO₂, IC95 [+10,4 ; +15,5] |
| Population communale | **+0,3 pt** — rien de mesurable |
| Calendrier | la plus utile : **−9,1 %** si retirée |
| Typologie officielle de station | **aucune** information de biais transférable |
| Forêt, échéance | retirer les **améliore** (−1,0 % et −0,5 %) |
| Empiler terrain + krigeage du résidu | **dégrade** : 19,4 % → 16,4 % |

---

## 6. Ce qui reste non démontré — à dire avant qu'on le demande

1. **Ce n'est pas le système d'ATMO** : CAMS Europe à 8 km, pas une chaîne kilométrique avec
   prévisionniste. Formulation retenue : *une correction apprise d'un **forçage européen**,
   utile **en amont** d'une chaîne locale*.
2. **La généralisation temporelle n'est pas acquise** — pire pli −35,5 %, sept plis négatifs
   en double aveugle.
3. **Le NO₂ horaire est indétectable** : POD 0,084, Brier skill +0,017 sur 273 dépassements.
4. **Aucune météo n'entre dans le modèle** — vérifié le 30/07 : `colonnes_admises` rend
   **53 prédicteurs**, tous disponibles à l'heure d'émission (sortie CAMS, paysage, relief,
   trafic, calendrier). La limite est donc l'inverse de ce que ce document affirmait :
   ce n'est pas qu'on utilise une réanalyse, c'est qu'on **se prive** de la météo — et cela
   pèse surtout sur les PM2,5, dont la variance est météorologique (R² de climatologie 0,139)
   et que le paysage ne prédit pas (+2 %).

   ⚠️ *Ce point affirmait précédemment « la météo est ERA5, une réanalyse indisponible en
   opérationnel ». C'était faux, et c'est l'objection la plus grave qu'on puisse opposer à un
   travail de prévision : le projet la publiait contre lui-même. La cause était une jointure
   ERA5 morte dans deux scripts d'application, dont aucune colonne n'entrait dans les
   prédicteurs.*
5. **Une part du gain revient au forçage**, pas au modèle (+0,953 en ΔMSE ; +14,0 % quand le
   forçage est bon contre +23,6 % quand il dérive).
6. **Le rejeu n'a pas sauvé l'épisode manqué** : 51,2 µg/m³ observés le 25/07, 7,7 prévus,
   14,6 après correction.

---

## 7. Ce que ce cadrage change dans les livrables

- **La présentation** s'organise autour du fil « quand corriger, quand s'abstenir » plutôt
  qu'autour de dix résultats juxtaposés.
- **Le premier écran** montre un épisode réel et ce que l'outil aurait dit — pas un RMSE.
- **Chaque note faible du bilan porte son remède dans la même phrase** : une faiblesse
  auto-déclarée sans contrepartie devient l'arme qu'on vous rend.
- **Le garde-fou est un livrable**, pas un correctif à venir.
