# Reconstitution de l'indice ATMO — vérification contre l'indice officiel

> Source officielle : *Indice quotidien de qualité de l'air pour les collectivités
> territoriales en Occitanie*, portail ArcGIS d'Atmo Occitanie, **accès libre**.
> 47 300 enregistrements · 164 EPCI · généré le 2026-07-28.

---

## 1. La règle d'agrégation est vérifiée exactement

Le jeu officiel publie **les cinq sous-indices en clair**, pas seulement l'indice agrégé.
On peut donc tester la règle qui les combine **sans avoir besoin du modèle de
spatialisation** — c'est la seule vérification exacte possible.

| | |
|---|---|
| Enregistrements testables (5 sous-indices présents) | **47 300 / 47 300** |
| Conformes à « le pire des sous-indices » | **47 265** |
| **Taux de conformité** | **99,926 %** |

La règle d'agrégation de l'arrêté du 10/07/2020 est donc confirmée sur données
officielles. Les codes couleur du module correspondent également à ceux publiés
(`#F0E641` pour *Dégradé*, vérifié).

### Les 35 écarts ne sont pas du bruit

Ils se concentrent sur **quatre dates seulement** : 23/11/2025 (12 zones),
09/10/2025 (12), 15/02/2025 (10) et 23/03/2026 (1). Une anomalie qui frappe douze EPCI
le même jour n'est pas une erreur d'arrondi — c'est un incident de chaîne de production.

Sens de l'écart : **25 cas où l'indice publié est SUPÉRIEUR** au maximum de ses propres
sous-indices, 10 où il est inférieur. La prédominance du sens conservateur suggère une
surcharge délibérée (événement, procédure préfectorale) plutôt qu'un défaut de calcul.

---

## 2. L'écart de spatialisation, quantifié

Comparaison de l'indice calculé **en station de fond** avec l'indice officiel de l'EPCI
le plus proche (23 stations rattachées à moins de 15 km, 4 965 jours-station).

| | |
|---|---|
| Accord exact | **42,8 %** |
| Écart ≤ 1 classe | **84,0 %** |
| **Biais moyen (station − officiel)** | **−0,72 classe** |

**Matrice de confusion** — lignes : indice calculé en station · colonnes : officiel EPCI

| | 1 Bon | 2 Moyen | 3 Dégradé | 4 Mauvais | 5 Très mauvais |
|---|---|---|---|---|---|
| **1 Bon** | 8 | **1 621** | 551 | 104 | 0 |
| **2 Moyen** | 7 | 1 618 | 310 | 140 | 0 |
| **3 Dégradé** | 0 | 51 | 363 | 38 | 0 |
| **4 Mauvais** | 0 | 0 | 14 | 137 | 2 |
| **5 Très mauvais** | 0 | 0 | 0 | 1 | 0 |

### Le biais est systématique, et son sens est attendu — mais il n'est pas garanti

L'indice officiel est le **maximum modélisé sur tout l'EPCI**, le nôtre est une valeur
**ponctuelle**. Un maximum sur une surface est supérieur ou égal à la valeur en un point
**du même champ** — mais nos deux grandeurs ne sont pas deux lectures d'un même champ :
l'une est une **observation** en station, l'autre la sortie d'un **modèle spatialisé**.
Ce sont deux estimateurs distincts, et l'erreur du modèle peut inverser le signe
localement. Le biais de −0,72 classe est donc **attendu**, non **nécessaire** : c'est une
signature de mécanisme, pas une inégalité mathématique.

Deux causes vont dans le même sens, mais elles ne pèsent pas pareil :

1. **Spatialisation — c'est l'essentiel.** Un point ne peut pas représenter le maximum
   d'une surface, et l'officiel cherche ce maximum sur toutes les mailles de toutes les
   communes de l'EPCI.
2. **Sous-indices incomplets — marginal, et désormais chiffré.** Nous n'avons que NO₂, O₃
   et PM2.5 quand l'officiel en agrège cinq. Mais sur 94 464 lignes du flux officiel
   (2025-01 → 2026-07), **O₃ est seul sous-indice maximal dans 79,4 %** des cas, PM10 dans
   **0,30 %** et SO₂ dans **aucun**. Nos trois polluants couvrent donc l'essentiel du
   pilotage : l'absence de PM10 et de SO₂ ne peut pas porter un biais de −0,72 classe.
   Source : `docs/GPT_R4.md` §5, par interrogation directe de l'API.

**Conclusion : l'écart est bien un écart de spatialisation.** Mais le reproduire ne
suffirait pas à valider quoi que ce soit — le produit officiel assimile les **mêmes
stations** que celles dont nous partons, si bien qu'une comparaison à ce flux n'est
**pas indépendante**. Voir `docs/GPT_R4.md` §7 et la mémoire du projet.
Ce n'est pas un raffinement cartographique de fin de projet, c'est un prérequis. La
modélisation spatiale remonte donc au premier palier.

---

## 3. Le polluant responsable — un écart révélateur

| Source | O₃ | NO₂ | PM2.5 | PM10 |
|---|---|---|---|---|
| **Officiel (EPCI, 5 sous-indices)** | **87,8 %** | 7,9 % | 3,0 % | 1,3 % |
| Calculé en station de fond (3 sous-indices) | 68,2 % | 24,6 % | 7,3 % | — |

**L'ozone pilote l'indice ATMO en Occitanie dans près de 88 % des cas.** Et sa
domination est *plus forte* dans l'officiel, alors même que celui-ci compte deux
concurrents supplémentaires — l'écart n'est donc pas un artefact de sous-indices
manquants.

L'explication est spatiale : l'indice EPCI couvre de vastes zones rurales, où l'ozone
est élevé — faute de NO qui le détruise par titration — tandis que nos stations de fond
sont majoritairement urbaines, où le NO₂ reste compétitif. **Le maximum sur un EPCI va
donc chercher l'ozone rural.**

C'est un résultat directement communicable : en Occitanie, agir sur la qualité de l'air
telle que mesurée par l'indice, c'est d'abord agir sur l'ozone — donc sur ses
précurseurs (NOx et COV), et non sur les seules particules.

---

## 4. Ce qui est reproduit, ce qui ne l'est pas

| Étape | État |
|---|---|
| Bornes des sous-indices par polluant | ✅ conforme à l'arrêté, testé |
| Grandeur retenue (moyenne journalière PM / max horaire gaz) | ✅ testé |
| Règle d'agrégation | ✅ **99,926 % sur données officielles** |
| Codes couleur officiels | ✅ vérifiés |
| Critère de couverture temporelle | ✅ appliqué |
| **Spatialisation méso-échelle → commune → EPCI** | ❌ **exige leur modèle** |

L'écart mesuré (42,8 % d'accord exact, biais −0,72) **est** la valeur de cette dernière
ligne. C'est le chantier que le projet doit adresser pour prétendre reproduire, puis
prévoir, l'indicateur réglementaire.
