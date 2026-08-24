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

## Le socle — sept familles, disponibles sur toute la fenêtre

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

*Mois écartés : 2023-08 (livraison à moitié), 2023-11 et 2025-07 (membres à 3 %), 2026-08
(mois en cours). Colonnes écartées : nitrate, matière organique, carbone élémentaire total,
sel marin — absentes de mois entiers.*

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

## Ce qui reste à faire avant que ces chiffres soient définitifs

1. **enveloppe de stabilité** — ⚙️ **moitié faite** : l'axe *évaluation* est mesuré
   (14 perturbations, ci-dessus). Reste l'axe *apprentissage* — perturber ce qui est appris
   demande un réajustement par perturbation, et c'est le seul poste encore coûteux ;
2. ~~**intervalle du plan**~~ — ✅ fait, voir ci-dessus ;
3. ~~**recalibrer la règle de décision**~~ — ✅ fait : seuil calibré à **0,0950** pour 12
   configurations criblées, au lieu des 0,05 nominaux 36 × trop sévères ;
4. **registre exhaustif des configurations**, ouvert avant le prochain criblage — le
   compte actuel ne recense que celles ayant laissé un CSV.

En attendant, ces quatre scores restent **exploratoires**, et ils le seront dit. Ce qui a
changé le 24/08 : ils ont désormais une **échelle** — ± 0,5 à 1,5 pt d'enveloppe
d'évaluation, et jusqu'à 2,5 pt pour le retrait d'un seul mois. C'est ce qui rend l'arrondi
obligatoire plutôt que prudent.
