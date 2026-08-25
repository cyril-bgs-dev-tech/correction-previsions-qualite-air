# Contrat de produit — ce que ce projet mesure, et ce qu'il ne mesure pas

*Établi le 24/08/2026, sur revue structurelle externe. Il précède toute nouvelle mesure et
ne change pas parce qu'un candidat paraît utile.*

---

## Le problème qu'il résout

Jusqu'ici, **une famille candidate définissait la fenêtre sur laquelle tout était jugé** :
GEOS-CF v1 couvre 2023-08 → 2025-12, donc l'évaluation entière tenait dans ces 29 mois. Un
candidat redéfinissait ainsi le banc d'essai sur lequel il paraissait utile, et toute autre
mesure perdait huit mois d'information pour l'accommoder.

> **Le chiffre principal ne doit pas dépendre de ce qu'on lui ajoute.**

---

## Le contrat

| | |
|---|---|
| **produit** | correction statistique des prévisions CAMS Europe à J+1 |
| **périmètre** | **PARTOUT** — aucune observation de qualité de l'air à l'inférence |
| **pile** | **auditable** — aucune famille portant un mois entièrement absent |
| **fenêtre canonique** | la fenêtre maximale propre, **indépendante des modules** |
| **métrique** | réduction de RMSE contre CAMS brut, par pli mensuel |
| **protocole** | double aveugle — station ET mois cachés simultanément |
| **plus petit effet utile** | **0,5 point**, provisoire, aligné sur la résolution mesurée ±0,36 à ±0,48 |

---

## Le socle — huit familles, disponibles sur toute la fenêtre

`base (CAMS, terrain, calendrier)` · `typologie` · `membres` · `tendance` · `speciation` ·
`profil` · `fourier` · `precurseurs` — 103 à 104 colonnes, **identiques sur les quatre
polluants**.

L'appartenance au socle se décide sur la **disponibilité**, jamais sur le score. Une
famille y entre parce qu'elle sert toutes les dates, pas parce qu'elle aide.

| polluant | fenêtre | mois | blocs de 3 | **score du socle** |
|---|---|---:|---:|---:|
| NO₂ | 2023-09 → 2026-08 | 33 | 11 | **41,09 %** |
| O₃ | 2023-09 → 2026-08 | 33 | 11 | **19,44 %** |
| PM10 | 2024-01 → 2026-08 | 32 | 10 | **23,67 %** |
| PM2,5 | 2023-09 → 2026-08 | 34 | 11 | **14,54 %** |

*Mois écartés : 2023-08 (précurseurs à 54 %), 2023-11, 2025-07 et 2026-08 (membres à 3-5 %,
le dernier étant le mois en cours). Colonnes écartées : nitrate, matière organique, carbone
élémentaire total, sel marin — absentes de mois entiers.*

⚠️ **« Cette colonne est complète » ne veut rien dire sans nommer la fenêtre.** La
qualification d'une colonne comme indicateur d'époque se décide **relativement à la fenêtre
considérée**, et c'est correct par construction : sur le support du module IFS
(2024-03 → 2026-08), seul le nitrate est écarté ; sur la fenêtre du socle
(2023-08 → 2026-08), quatre variables le sont. J'ai écrit l'inverse dans une résolution du
registre le 24/08, en lisant le journal du mauvais lot — et le registre **refuse de réécrire
une résolution scellée**, ce qui est le bon comportement : la correction vit ici, la trace de
l'erreur reste là-bas.

---

## Les modules — conditionnels, jamais dans le chiffre principal

Une famille dont la couverture est plus courte ou trouée devient un **module**. Son gain se
mesure **apparié, sur son propre support**, contre le socle restreint aux mêmes lignes. Si
elle manque à l'inférence, on retombe sur le socle — **l'absence n'entre jamais comme
variable**.

| module | couverture | statut |
|---|---|---|
| **geoscf v1** | 2023-08 → 2025-12 · 29 mois | module historique. +0,51 pt en dernière position, proche de la résolution, contre 8 mois de corpus pour toutes les autres mesures |
| **ifs** | 2024-03 → 2026-08 · **contigu** | ✅ **CONFIRMÉ** — voir ci-dessous |
| **feux** | 2023-08 → 2025-05 · 19 mois, 3 trous | expérimental. −0,09 pt, hors socle |
| **era5** | complet | plafond non déployable, jamais dans un produit |

⚠️ **v2 de GEOS-CF n'est pas huit mois à concaténer à v1 : c'est un autre prédicteur.**

---

## ✅ Le module MÉTÉO PRÉVUE est confirmé — 24/08/2026

Huit champs de surface de l'IFS, moyennes journalières, mesurés **en dernière position sur
le socle**, sur le support propre du module (2024-03 → 2026-08, 28 à 29 mois, 9 blocs).

| | écart apparié | IC95 | `p⁺` | blocs positifs |
|---|---:|---:|---:|:---:|
| NO₂ | **+0,746 pt** | [+0,447 ; +1,046] | 0,0033 | 8/9 |
| O₃ | **+0,886 pt** | [+0,339 ; +1,535] | 0,0105 | 8/9 |
| PM10 | **+1,216 pt** | [+0,477 ; +1,842] | 0,0104 | 8/9 |
| PM2,5 | **+0,830 pt** | [+0,282 ; +1,399] | 0,0140 | 7/9 |

`p_PC = 0,0312`, **stable aux trois longueurs de bloc** (0,0114 · 0,0312 · 0,0201) : le
découpage ne décide pas. Le seuil calibré vaut 0,0950 — il passe avec une marge de 3 ×.

**L'effet dépasse l'effet utile de 0,5 pt sur les quatre polluants.** C'est le premier
module à franchir les trois critères — effet, incertitude et utilité.

**Le score du produit avec module** : NO₂ 42,25 % · O₃ 20,36 % · PM10 23,53 % ·
PM2,5 15,32 %, sur 28 à 29 mois.

⚠️ **Ces valeurs ne se soustraient pas à celles du socle seul** : les fenêtres diffèrent de
trois à cinq mois. PM10 affiche −0,14 pt en poolé et **+1,216 en apparié** — c'est l'écart
de fenêtre, pas un désaccord. Seul l'apparié conclut.

**Ce qui rend ce résultat défendable** : la configuration a été inscrite au registre
prospectif AVANT exécution, deux fois — au criblage (`1121b0de`) puis à la confirmation
(`e4fdd2f0`), cette dernière portant la réserve écrite « elle peut tomber ».

**Contrat de service** : l'IFS est un flux ECMWF public, disponible à J+1 avec quelques
heures de latence. Si la source manque à l'inférence, on retombe sur le socle — l'absence
n'entre pas comme variable.

---

## Ce que ce contrat interdit

* qu'un candidat raccourcisse rétroactivement la fenêtre canonique ;
* qu'une absence de module entre dans le modèle comme variable, avec ou sans drapeau ;
* qu'un module rejoigne le socle avant couverture propre de **toute** la version suivante
  du banc d'essai ;
* qu'un chiffre plus flatteur — *comparable* ou *AUX STATIONS* — serve de titre.

---

## Les quatre chiffres à dire, et les douze autres

Le récit porte **quatre nombres arrondis**, un par polluant, sur le produit auditable
PARTOUT. Les trois autres colonnes de la matrice ne sont pas des réserves du même chiffre :
ce sont des **questions différentes**, et elles vivent en annexe.

⚠️ **La deuxième décimale disparaît du récit.** Mesuré : 0,14 % de données déplacent un pli
de 2,56 pt, contre ≤ 0,039 à données identiques. Tant que l'enveloppe de version n'est pas
calculée, on écrit **≈ 41 %**, pas 41,09 %.

---

## L'intervalle du plan — chantier ②, mesuré le 24/08

Bootstrap sur blocs de trois mois consécutifs, **sur le gain POOLÉ** — pas sur une moyenne
de gains par pli, la RMSE n'étant pas linéaire. 10 000 tirages.

| polluant | score | IC95 du plan | demi-largeur | **à dire** |
|---|---:|---:|---:|---:|
| NO₂ | 41,09 % | [40,00 ; 42,12] | ±1,06 pt | **≈ 41 %** |
| O₃ | 19,44 % | **[13,55 ; 24,44]** | **±5,45 pt** | **≈ 19 %** |
| PM10 | 22,65 % | [18,04 ; 27,79] | ±4,87 pt | **≈ 23 %** |
| PM2,5 | 14,86 % | [11,97 ; 17,36] | ±2,69 pt | **≈ 15 %** |

🔴 **L'ozone vaut entre 13,5 et 24,4 %.** Écrire « 20,51 % » n'était pas une précision,
c'était une illusion de précision : l'intervalle couvre onze points.

Cette incertitude est celle de l'**échantillonnage des mois et des stations** — « et si le
corpus avait couvert d'autres mois ? ». Elle ne couvre ni le bruit d'exécution (≤ 0,04 pt
par pli) ni la version du corpus (chantier ①).

⚠️ Elle ne s'applique PAS aux décisions de famille : celles-ci reposent sur des écarts
**appariés** — mêmes plis, même graine — qui soustraient le déplacement commun et sont un
ordre de grandeur plus serrés (±0,2 à ±1,5 pt).

*Les centres sont calculés sur les mois alignés en blocs ; PM10 en perd deux et PM2,5 un,
d'où un léger écart aux scores de la table précédente.*

---

## 🔑 Le socle démontre QUATRE familles, la pile de référence n'en démontrait qu'une

Apport **en dernière position**, c'est-à-dire en présence de toutes les autres — la mesure la
plus dure qu'un ordre d'empilement autorise.

| famille | pile de référence · 29 mois | | SOCLE · 32-34 mois | |
|---|---:|---|---:|---|
| | apport | `p_PC` | apport | `p_PC` |
| `typologie` | +3,528 | 0,0120 ✅ | **+3,457** | **0,0030 ✅** |
| `speciation` | +1,455 | 0,1089 🟠 | **+2,416** | **0,0045 ✅** |
| `precurseurs` | +0,761 | 0,0900 🟠 | **+0,966** | **0,0021 ✅** |
| `membres` | +0,404 | 0,5094 🟠 | **+0,864** | **0,0069 ✅** |
| `fourier` | +0,133 | 0,9063 🔴 | +0,113 | 0,8772 🔴 |
| `profil` | +0,166 | 0,4686 🟠 | +0,082 | **0,8943 🔴 SAUTE** |
| `tendance` | +0,152 | 0,4098 🔴 | +0,046 | 0,6660 🔴 |

*(🟠 = non confirmé par manque de puissance — l'utilité restait possible)*

**C'est le retour sur investissement du contrat.** Fixer la fenêtre par la **disponibilité**
plutôt que la laisser à un candidat fait passer **trois familles** de « peut-être utile, on ne
peut pas trancher » à **démontrée**. Prédit avant la mesure (`a2706756`, scellée le 23/08) — la
prédiction annonçait deux familles sur trois, les trois sont passées.

**Trois causes distinctes s'additionnent, et il faut les séparer :**

**① Plus de blocs, donc un plancher de `p` plus bas.** 10-11 blocs au lieu de 9. C'est l'effet
prédit.

**② `membres` DOUBLE (+0,404 → +0,864) parce que son substitut est parti.** L'ablation jointe
`geoscf`+`membres`, mesurée indépendamment le même jour, montre que les deux encodent la même
chose. Sur la pile de référence, `geoscf` masquait `membres` ; sur le socle, `membres` seule
porte l'information. **Deux mesures indépendantes qui se confirment l'une l'autre.**

**③ `profil` bascule de 🟠 vers 🔴 SAUTE.** Plus de données ont converti une **inconnue** en
**bénéfice exclu** — c'est précisément ce que la règle à trois zones existe pour produire, et
c'est une information, pas un échec.

⚠️ **Ce que cela ne dit pas.** `fourier`, `profil` et `tendance` sont jugées **une à une**.
Deux familles redondantes s'annulent à l'ablation individuelle — c'est mesuré sur ce dépôt.
Leur sort se joue au sein de **G2**, en retrait conjoint, pas ici.

Régénérable : `python3 scripts/apport_en_derniere_position.py --suffixe _sans-feux-geoscf_fenetre-complete`.

---

### Avec le module IFS : cinq familles tiennent, et trois n'en démontrent aucune

| famille | socle · 32-34 mois | socle + IFS · 28-29 mois |
|---|---:|---:|
| `typologie` | +3,457 · 0,0030 ✅ | +3,647 · 0,0063 ✅ |
| `speciation` | +2,416 · 0,0045 ✅ | +1,458 · 0,0171 ✅ |
| `membres` | +0,864 · 0,0069 ✅ | +0,954 · 0,0123 ✅ |
| **`ifs`** | — | **+0,920 · 0,0312 ✅** |
| `precurseurs` | +0,966 · 0,0021 ✅ | +0,436 · 0,0192 ✅ |
| `fourier` | +0,113 · 0,8772 🔴 | +0,106 · 0,9375 🔴 |
| `profil` | +0,082 · 0,8943 🔴 | +0,005 · 0,4935 🔴 |
| `tendance` | +0,046 · 0,6660 🔴 | −0,029 · 1,0000 🔴 |

**Contrôle de cohérence** : `ifs` rend ici `p_PC = 0,0312`, la valeur exacte de sa
confirmation — deux routes de calcul indépendantes, le même nombre.

**Trois familles sur huit ne démontrent rien, sur les deux piles** : `fourier`, `profil`,
`tendance`. Ce sont précisément celles du groupe **G2**, et c'est pourquoi leur sort se juge
en retrait **conjoint** : jugées une à une, deux familles redondantes s'annulent.

🔴 **Ce qu'il ne faut PAS lire dans ce tableau.** `speciation` passe de +2,416 à +1,458 et
`precurseurs` de +0,966 à +0,436 — il serait tentant d'y voir l'IFS qui se substitue à elles.
**La fenêtre a changé en même temps** (32-34 mois contre 28-29) : les deux colonnes ne sont pas
appariées, et l'écart mélange le module avec les mois retirés. Trancher exigerait de mesurer
les deux sur les mêmes lignes — règle M. Ce qui est établi ici, c'est que **cinq familles
tiennent sur la pile qui porte le module**, pas la cause des variations entre colonnes.

---

## 🔴 La chimie CAMS n'entre ni au socle ni en module — 24/08/2026

Formaldéhyde, glyoxal, NO, CO — quatre moyennes journalières, mesurées **en dernière position
sur le socle**. Sa couverture est **complète (37 mois)**, donc elle ne restreint pas la
fenêtre : la mesure tourne sur **exactement les mêmes plis que le socle** (33/33, 32/32,
34/34), ce qui rend la comparaison directement valide — contrairement au module IFS.

| | apport apparié | IC95 | `p⁺` | blocs positifs |
|---|---:|---:|---:|:---:|
| NO₂ | +0,225 pt | [+0,042 ; +0,408] | 0,0299 | 8/11 |
| **O₃** | **+0,027 pt** | **[−0,549 ; +0,421]** | 0,4846 | 8/11 |
| PM10 | +0,145 pt | [−0,139 ; +0,429] | 0,1977 | 7/10 |
| PM2,5 | +0,295 pt | [−0,014 ; +0,623] | 0,0593 | 6/11 |

`p_PC = 0,1779` → 🟠 **NON CONFIRMÉ, par puissance** : les quatre groupes vont dans le même
sens, mais aucun n'atteint l'effet utile.

**Sur l'ozone, il ne reste rien.** La pile historique donnait **+1,165 pt** avec neuf blocs
positifs sur neuf ; le socle donne **+0,027**, intervalle contenant zéro.

### Ce que cette mesure établit, et ce qu'elle n'établit pas

**Établi** : sur le socle, la chimie n'apporte aucun effet utile, sur aucun polluant. Elle
n'entre donc ni comme famille ni comme module — et une famille dont l'apport ne dépasse pas
0,3 pt ne se promeut pas sur l'espoir de mois supplémentaires.

**Non établi** : que l'effet ait « disparu ». Les +1,165 pt portaient sur **29 mois**, celui-ci
sur **33**, et les partitions de test de deux fenêtres différentes sont **disjointes par
construction**. Les deux nombres n'ont jamais été comparables ; le second n'annule pas le
premier, il le remplace sur le seul corpus qui définisse le produit.

### La prédiction, et ce qu'elle a coûté d'exact

Inscrite avant exécution (`92c7a20c`), **démentie**. Elle annonçait « ≈ +1 pt sur l'ozone,
rien ailleurs ». Deux enseignements que le chiffre seul ne donnerait pas :

* le verdict global — `NON CONFIRMÉ`, `p_PC` au-dessus du seuil — était **juste pour une
  raison fausse** : je le prédisais parce qu'*un seul* groupe porterait ; il tombe parce
  qu'**aucun** ne porte ;
* le **mécanisme** est contredit de biais. Je prédisais le NO₂ nul « comme prédit », étant
  lui-même un précurseur — et c'est **le seul des quatre dont l'intervalle exclut zéro**.

## ⚙️ L'enveloppe de stabilité — chantier ①, axe ÉVALUATION, 24/08

Le socle publie « NO₂ 41,09 % ». Ce nombre n'est pas une propriété du modèle : c'est une
propriété du modèle **et** d'une trentaine de décisions d'évaluation qu'un autre analyste
aurait pu prendre autrement. Tant que leur amplitude n'est pas mesurée, le chiffre n'a pas
d'échelle — et nul ne peut savoir si 0,4 pt d'écart entre deux piles veut dire quelque chose.

Quatorze perturbations préinscrites, rejouées sur les prédictions hors échantillon
enregistrées — donc **exactes et gratuites**.

| | publié | enveloppe | amplitude | jackknife par mois | ampl. |
|---|---:|---:|---:|---:|---:|
| NO₂ | 41,09 % | [40,99 ; 41,55] | **0,56 pt** | [40,92 ; 41,43] | 0,51 |
| O₃ | 19,44 % | [18,31 ; 19,85] | **1,54 pt** | [18,31 ; 19,91] | 1,60 |
| PM10 | 23,67 % | [23,29 ; 24,28] | **0,99 pt** | [22,89 ; 25,36] | 2,47 |
| PM2,5 | 14,54 % | [14,42 ; 14,91] | **0,49 pt** | [13,29 ; 14,90] | 1,61 |

**Retirer UN SEUL mois déplace le chiffre plus que toutes les perturbations
d'échantillonnage réunies** — jusqu'à 2,47 pt sur PM10. C'est la justification mesurée des
arrondis : ≈ 41 · ≈ 19 · ≈ 24 · ≈ 15 %.

Les perturbations **saisonnières** sont tenues à part : elles ne rééchantillonnent pas le
corpus, elles **changent la question**. Sur PM10, hors été 19,10 % et hors hiver 25,52 % —
6,4 pt, six fois l'amplitude de tout le reste. Le gain sur PM10 est majoritairement estival.

### 🔑 Un mois vaut 2 pt : un module qui gagne 0,75 pt est-il du bruit ?

Non — et cela se mesure sur les **mêmes lignes**, jamais s'affirme.

| | absolu, amplitude jackknife | écart apparié, amplitude | rapport |
|---|---:|---:|---:|
| NO₂ | 0,51 pt | **0,108 pt** | 4,7 × |
| O₃ | 2,15 pt | **0,335 pt** | 6,4 × |
| PM10 | 2,27 pt | **0,262 pt** | 8,7 × |
| PM2,5 | 1,90 pt | **0,536 pt** | 3,5 × |

**L'écart apparié est 3,5 à 8,7 × plus stable que le chiffre absolu** : les deux bras voient
les mêmes mois, et le déplacement commun se soustrait. C'est ce qui autorise à **arrondir
les niveaux** *et* à **conclure sur les différences**.

⚠️ **PM2,5 est le cas le moins confortable** : 0,536 pt d'amplitude appariée pour 0,655 pt
d'effet. Un mois peut y déplacer la moitié de l'effet — cohérent avec ses 7 blocs positifs
sur 9, les plus faibles des quatre.

🔴 **Le piège évité, et il n'aurait rien levé.** Comparer la pile socle et la pile module
entre **deux exécutions** ne mesure rien : le protocole cache une rotation `groupes[i % 3]`
indexée sur le rang du mois, et les deux exécutions ne commençant pas au même mois, leurs
partitions de test sont **disjointes par construction** — 16 055 lignes communes sur 90 000
pour NO₂, et **zéro pour O₃**. Le calcul inter-exécutions rendait « +1,77 à +3,33 pt » là où
l'appariement interne rend +0,78. Les deux nombres sont plausibles ; seul le second est
mesuré.

⬜ **Ce qui reste du chantier ①** : l'axe **apprentissage**. Perturber ce qui est *noté* est
gratuit ; perturber ce qui est *appris* demande un réajustement par perturbation. L'enveloppe
ci-dessus est donc un **minorant**, et elle est nommée comme tel.

Régénérable : `python3 scripts/enveloppe_stabilite.py` et `--apparie`.

---

### Onze apports sur vingt-huit ne sont pas des quantités mesurées

La même machinerie, appliquée famille par famille : l'apport de chacune sur le socle, **et
de combien cet apport bouge quand on retire un mois de l'évaluation.**

| famille | NO₂ | O₃ | PM10 | PM2,5 |
|---|---:|---:|---:|---:|
| `typologie` | **+9,682** [0,319] | +0,096 [0,139] | **+2,217** [0,281] | +0,273 [0,226] |
| `speciation` | **+1,012** [0,176] | **+3,491** [0,945] | **+2,603** [0,487] | **+1,434** [0,699] |
| `precurseurs` | +0,210 [0,116] | **+1,497** [0,243] | **+0,946** [0,277] | **+1,224** [0,304] |
| `membres` | +0,056 [0,063] | **+1,636** [0,338] | +0,353 [0,327] | **+1,300** [0,288] |
| `profil` | −0,021 [0,076] | +0,123 [0,169] | +0,109 [0,142] | +0,010 [0,198] |
| `fourier` | +0,443 [0,090] | +0,065 [0,141] | −0,158 [0,114] | −0,133 [0,218] |
| `tendance` | −0,097 [0,080] | +0,160 [0,267] | +0,150 [0,237] | −0,318 [0,643] |

*(en gras : au-dessus de l'effet utile de 0,5 pt ; entre crochets, l'amplitude au jackknife)*

**Onze des vingt-huit apports sont plus petits que leur propre amplitude.** « `tendance`
apporte −0,318 pt sur PM2,5 » a une amplitude de 0,643 : le nombre est un tirage, pas une
mesure. Publier l'un sans l'autre, c'est laisser croire à une précision qui n'existe pas.

**Une seule famille tient sur les quatre polluants : `speciation`** — et son apport dépasse
partout son amplitude. `typologie` est massive sur NO₂ (+9,68) et PM10 (+2,22), quasi nulle
ailleurs : c'est cohérent avec son mécanisme, la typologie encode l'exposition au trafic.

⚠️ **Ce sont des retraits depuis la pile COMPLÈTE, donc deux familles redondantes s'y
annulent mutuellement.** Un apport faible ne prouve pas qu'une famille est inutile — c'est
exactement ce que l'ablation **jointe** existe pour lever, et pourquoi `profil`, `fourier` et
`tendance` sont regroupées en G2 plutôt que jugées une à une.

Régénérable : `python3 scripts/enveloppe_stabilite.py --familles`.

---

### ✅ Chantier ① complet — l'axe APPRENTISSAGE, 25/08/2026

Perturber ce qui est **noté** était gratuit. Perturber ce qui est **appris** demandait un
réajustement par perturbation — et l'épinglage de fenêtre l'a rendu possible sans code neuf :
épingler sur une liste de mois **amputée** retire le mois de tout le corpus, donc de
l'apprentissage. Vingt mesures, cinq perturbations par polluant.

| | amplitude ÉVALUATION | amplitude APPRENTISSAGE | rapport |
|---|---:|---:|---:|
| NO₂ | 0,42 pt | **0,71 pt** | × 1,7 |
| O₃ | 1,54 pt | **1,50 pt** | × 1,0 |
| PM10 | 2,47 pt | **3,03 pt** | × 1,2 |
| PM2,5 | 1,61 pt | **2,04 pt** | × 1,3 |

**L'enveloppe d'évaluation était un bon minorant** : l'enveloppe complète ne la dépasse que
d'un facteur 1,0 à 1,7. Les deux axes s'accordent largement — corrélation **+0,78**, écart
médian **0,194 pt**.

**L'enveloppe complète du chiffre publié est donc de 0,7 à 3,0 pt selon le polluant.** Les
arrondis ≈ 41 · ≈ 19 · ≈ 24 · ≈ 15 % ne sont pas prudents, ils sont **obligatoires**, et
PM10 est le cas le plus exposé.

### 🔴 Deux perturbations changent de SIGNE entre les deux axes

| | mois | évaluation | apprentissage |
|---|---|---:|---:|
| O₃ | 2023-09 | **+0,414** | **−0,959** |
| PM10 | 2024-01 | **+0,181** | **−1,456** |

Retirer ces mois de la **notation** améliore le chiffre ; les retirer de l'**apprentissage**
le dégrade. Ce sont des mois que le modèle a besoin de **voir**, et sur lesquels il est
mauvais.

> **L'axe évaluation seul aurait désigné ces mois comme des gêneurs à écarter.** C'est
> exactement l'inverse : ce sont des mois porteurs pour l'apprentissage. Un jackknife
> d'évaluation ne dit rien de la valeur d'une donnée — seulement de son effet sur la note.

Régénérable : `reports/perturbations/taches.txt`, puis
`reports/enveloppe_stabilite_apprentissage.csv`.

### ✅ Chantier ④ — le compte des degrés de liberté, et pourquoi il ne décide rien

Le seuil calibré vaut **0,0874** pour les **14 configurations de criblage** réellement
inscrites (il valait 0,0950 pour 12). Tous les verdicts publiés passent : G3 0,0021 · socle
0,0021-0,0069 · IFS 0,0312 · `geoscf`+`membres` 0,0357 · G2 0,0468.

**L'objection qui restait** : les ablations de groupe sont jugées contre ce seuil sans entrer
dans son `K`. Répondre qu'elles ont été préinscrites — ce qui est vrai — serait exactement le
raisonnement qui arrange. `--k` rend donc la question **mesurable** :

| K forcé | 14 | 24 | 34 | 57 |
|---|---:|---:|---:|---:|
| seuil calibré | 0,0874 | 0,0910 | 0,0900 | 0,0874 |

**Le seuil ne se resserre pas — et il n'est même pas monotone.** La raison est mesurée, pas
supposée : sous ce plan, **`p_PC` ne peut prendre que CINQ valeurs distinctes**.

| blocs | valeurs atteignables par `p_PC` sous H₀ |
|---|---|
| 9 | 0,0059 · 0,0586 · 0,2695 · 0,7617 · 1 |
| 11 | 0,0176 · 0,0981 · 0,3398 · 0,8232 · 1 |

Quatre polluants et neuf à onze blocs ne produisent pas assez de configurations de signes pour
que la conjonction partielle soit continue. Le seuil calibré est donc une **fonction en
escalier** de `K`, pas une fonction décroissante — et entre 14 et 57 il reste sur la même
marche.

> **La conclusion ne dépend pas du périmètre de `K`.** C'est plus solide que n'importe quel
> argument sur ce qui « compte » comme criblage, parce que cela n'exige de croire personne.

⚠️ **Deux réserves.** Au-delà de 14, le nul est **rééchantillonné avec remise** parmi les
séries observées : l'estimation du resserrement est donc un **minorant**. Et la table
ci-dessus est celle du test de signe, plus grossière que la permutation par retournement
réellement employée — elle explique le mécanisme, elle ne remplace pas la calibration.

Régénérable : `python3 scripts/calibrer_decision.py [--k N]`.

## Ce qui reste à faire avant que ces chiffres soient définitifs

1. ~~**enveloppe de stabilité**~~ — ✅ **complète** : axe évaluation (14 perturbations) et
   axe apprentissage (20 mesures réajustées). Enveloppe totale **0,7 à 3,0 pt** ;
2. ~~**intervalle du plan**~~ — ✅ fait, voir ci-dessus ;
3. ~~**recalibrer la règle de décision**~~ — ✅ fait : seuil calibré à **0,0950** pour 12
   configurations criblées, au lieu des 0,05 nominaux 36 × trop sévères ;
4. **registre exhaustif des configurations**, ouvert avant le prochain criblage — le
   compte actuel ne recense que celles ayant laissé un CSV.

**Les quatre chantiers sont clos.** Le ④ a rendu davantage qu'un compte : il a montré que le
seuil calibré **ne dépend pas** du périmètre retenu, parce que la loi nulle du `p_PC` est
quantifiée à cinq valeurs. Une objection de méthode a été retirée par la mesure plutôt que
par un argument.

Les quatre scores ont désormais une **échelle mesurée sur les deux axes** — 0,7 à 3,0 pt
d'enveloppe totale. Cités **arrondis**, ils sont défendables ; cités à la deuxième décimale,
ils ne le sont pas. Et les **écarts appariés**, eux, restent 3,5 à 8,7 × plus stables que les
niveaux : c'est sur eux que les conclusions se prennent.
