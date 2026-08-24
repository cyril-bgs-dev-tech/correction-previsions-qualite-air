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
| **ifs** | 2024-02 → 2026-07 · 24 mois, **6 trous** | candidat. Non promouvable avant rattrapage. Mécanisme neuf — la pile ne porte aucune météo |
| **feux** | 2023-08 → 2025-05 · 19 mois, 3 trous | expérimental. −0,09 pt, hors socle |
| **era5** | complet | plafond non déployable, jamais dans un produit |

⚠️ **v2 de GEOS-CF n'est pas huit mois à concaténer à v1 : c'est un autre prédicteur.**

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

## Ce qui reste à faire avant que ces chiffres soient définitifs

1. **enveloppe de stabilité** — 6 à 10 perturbations de corpus préenregistrées, graine
   fixe, pour borner la sensibilité de version ;
2. ~~**intervalle du plan**~~ — ✅ fait, voir ci-dessus ;
3. **recalibrer la règle de décision** — la conjonction partielle a une taille réelle de
   0,0015 pour un seuil annoncé à 0,05, soit 34 × trop sévère ;
4. **registre exhaustif des configurations**, ouvert avant le prochain criblage — le
   compte actuel ne recense que celles ayant laissé un CSV.

En attendant, ces quatre scores sont **exploratoires**, et ils le seront dit.
