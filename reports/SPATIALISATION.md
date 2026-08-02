# Spatialisation — reproduire la chaîne officielle

> Chaîne testée : **stations de fond → champ interpolé → agrégation par EPCI → sous-indice**
> Polluant : **O₃** (responsable de l'indice ATMO occitan dans 87,8 % des cas)
> 14 505 couples jour × EPCI · 104 jours · 20 stations de fond · 162 EPCI · grille 2 km
> Généré le 2026-07-28 · `reports/spatialisation_O3.csv`

---

## 1. Le résultat

| Approche | Accord exact | Écart ≤ 1 classe | Biais moyen |
|---|---|---|---|
| Indice **ponctuel** en station | 42,8 % | 84,0 % | **−0,72 classe** |
| **Champ interpolé + maximum par EPCI** | **90,9 %** | 99,9 % | **+0,043 classe** |
| Champ interpolé + moyenne par EPCI | **91,6 %** | 99,9 % | +0,016 classe |

**Le diagnostic est confirmé : l'écart au sous-indice officiel était bien la
spatialisation.** Une interpolation par distance inverse, sans aucune variable
explicative, suffit à passer de 42,8 % à plus de 90 % d'accord et à annuler un biais
systématique de près d'une classe.

**Matrice de confusion** — lignes : spatialisé par maximum · colonnes : officiel

| | 1 Bon | 2 Moyen | 3 Dégradé | 4 Mauvais |
|---|---|---|---|---|
| **1 Bon** | 46 | 12 | 0 | 0 |
| **2 Moyen** | 187 | **10 120** | 326 | 0 |
| **3 Dégradé** | 0 | 562 | **2 391** | 16 |
| **4 Mauvais** | 0 | 10 | 208 | **627** |

Les erreurs sont **strictement adjacentes** : aucune confusion à deux classes ou plus
sur 14 505 couples. C'est ce que le critère métier demande — confondre *Bon* et *Moyen*
n'a pas la gravité de confondre *Bon* et *Mauvais*.

---

## 2. Un résultat contre-intuitif : la moyenne bat le maximum

L'indice officiel est défini comme un **maximum sur la zone**. On s'attendrait donc à ce
qu'agréger par le maximum reproduise mieux. C'est l'inverse : **91,6 % pour la moyenne
contre 90,9 % pour le maximum**, et un biais plus faible (+0,016 contre +0,043).

L'explication tient à la nature du champ interpolé. Une interpolation par distance
inverse produit des **pics artificiels autour de chaque station** — la valeur y est
imposée, et le champ décroît vite alentour. Son maximum sur une zone tend donc à
retrouver la valeur de la station la plus proche, avec sa variabilité propre. Le champ
officiel, issu d'un modèle physique, est **plus lisse** : son maximum est plus proche
d'une moyenne locale que d'un pic ponctuel.

Autrement dit, **la moyenne d'un champ trop piqué approxime mieux le maximum d'un champ
lisse que ne le fait son propre maximum.** C'est une propriété de l'interpolateur, pas
de la définition réglementaire — et elle disparaîtra quand le champ IDW sera remplacé
par un champ prédit à partir des variables géospatiales.

⚠️ **À ne pas retenir comme une règle métier.** L'écart entre les deux modes est faible
(0,7 point), et adopter la moyenne serait non conforme à l'arrêté. Le résultat sert de
diagnostic sur la qualité du champ, pas de recommandation.

---

## 3. Où la méthode faiblit : les très grands EPCI

| Taille d'EPCI | n | Accord (max) | Biais (max) | Accord (moyenne) |
|---|---|---|---|---|
| < 100 km² | 448 | 90,4 % | −0,029 | 90,0 % |
| 100–500 km² | 9 579 | 91,0 % | +0,045 | 91,7 % |
| 500–1 500 km² | 4 390 | 90,9 % | +0,042 | 91,8 % |
| **> 1 500 km²** | 88 | **76,1 %** | **+0,216** | 81,8 % |

La performance chute de 15 points sur les très grands EPCI, avec un biais quatre fois
plus élevé. L'hétérogénéité interne y est mécaniquement plus forte : l'écart moyen entre
le maximum et la moyenne d'une zone passe de **0,4 µg/m³** (< 100 km²) à **2,0 µg/m³**
(> 1 500 km²).

**Ce sont ces zones que le projet doit viser.** Sur les EPCI compacts, une interpolation
naïve suffit déjà ; c'est là où le territoire est vaste et contrasté — reliefs, forêts,
littoral — que les variables géospatiales doivent apporter leur gain. Autrement dit :
**le sous-échantillon où l'IDW échoue est exactement celui où la LUR est censée exceller.**

---

## 4. Limites de l'expérience

- **104 jours seulement.** L'indice officiel n'est publié qu'en fenêtre glissante, et le
  flux temps réel O₃ est rompu depuis le 01/07/2025 : l'intersection est mince.
- **L'IDW ne peut pas extrapoler.** Elle ne produit jamais de valeur hors de l'intervalle
  des observations, alors que le modèle officiel, lui, peut dépasser le maximum mesuré.
  C'est une cause identifiée du biais résiduel, et une limite que la LUR n'a pas.
- **20 stations de fond** pour couvrir toute l'Occitanie — d'où l'importance du corpus
  national pour ajuster la relation paysage–concentration.
- Grille à **2 km**, contre 1 km visé au contrat de données. À raffiner.

---

## 5. Suite

1. Remplacer le champ IDW par un **champ prédit à partir des variables géospatiales**
   (LUR ajustée sur les 476 stations métropolitaines), et mesurer le gain **sur les
   grands EPCI en priorité** — c'est là que la marge existe.
2. Ajouter la **météo** (ERA5) : l'ozone est fortement météo-dépendant, le gain attendu
   y est maximal.
3. Étendre à NO₂ et PM2.5, puis à l'**indice agrégé** — le livrable réglementaire complet.

---

## ⚠️ Ce que cette expérience ne démontre pas — relecture du 29/07

Une relecture adverse a relevé trois limites qui bornent sérieusement la portée du
résultat. Elles sont réelles, et il vaut mieux les énoncer soi-même.

### 1. Les deux objets comparés ne sont pas indépendants

L'interpolation utilise les **observations du jour même**, et le résultat est comparé au
sous-indice officiel **du même jour**. Or ce dernier provient d'une chaîne qui combine
mesures et modélisation — PREV'AIR krige justement à partir des stations de fond. Les
deux objets partagent donc une partie de leur information d'entrée.

Passer de 42,8 % à plus de 90 % d'accord établit que **l'agrégation spatiale rapproche
les deux**, ce qui reste instructif. Cela n'établit **pas** que l'écart initial avait une
cause unique, ni qu'un modèle prédictif reproduirait la chaîne officielle.

### 2. Ce n'est pas une prévision

L'expérience interpole des observations déjà acquises. Elle ne prédit rien, et ne dit
donc rien de ce qu'on obtiendrait en spatialisant un **champ prévu** — le cas
opérationnel. Aucune station ni zone n'est retirée avant évaluation : il n'y a pas de
validation hors échantillon.

### 3. Le périmètre est étroit

Un seul polluant (O₃), 104 jours, 20 stations de fond, une interpolation par distance
inverse à 2 km. L'indice officiel en agrège **cinq** et repose sur un modèle
méso-échelle. Les sous-indices manquants sont d'ailleurs une **seconde cause** de l'écart
initial, distincte de la spatialisation — le rapport `INDICE_ATMO.md` la mentionne, et
l'expérience ne les sépare pas.

### Ce qu'il faudrait pour conclure

Une validation spatiale hors échantillon sur des **champs prévus avant l'observation**,
avec les cinq polluants, comparée au produit officiel, et distinguant trois sources
d'erreur aujourd'hui confondues : celle des concentrations, celle de l'interpolation, et
celle de l'agrégation par EPCI.

**Formulation défendable en l'état :** *l'agrégation spatiale explique une part
importante du biais de −0,72 classe, et le corriger est un prérequis — mais la
démonstration reste à faire sur des champs prévus.*
