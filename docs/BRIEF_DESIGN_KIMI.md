# Revue de design — dossier technique HTML, lu à l'écran **et** imprimé en A4

> ## 📄 Format de réponse attendu : **un fichier `.md`**
>
> Pas de prose libre : un document structuré que je puisse lire et appliquer directement,
> avec une section par question (① à ⑤) et, pour chaque recommandation :
> **le principe**, **la règle CSS ou structurelle** qui l'implémente, et **ce qu'elle
> remplace**. Une suggestion que je ne peux pas traduire en règle générable est
> inapplicable ici — voir la contrainte 3.

**Ce qu'on attend : de la critique de conception, pas du code.** Des principes applicables,
parce que la page est **générée par des scripts Python** — tout ce qui est proposé doit
survivre à une régénération, donc s'exprimer en règles, pas en retouches.

---

## 1. La pièce

Un dossier technique unique, `presentation_atmo.html` :

| | |
|---|---|
| poids | **706 Ko**, 4 773 lignes, **entièrement autonome** (0 image externe, 0 CDN) |
| structure | **11 sections**, 9 titres de niveau 1, 34 de niveau 3 |
| contenu | **10 tableaux** numériques denses, **25 SVG en ligne** faits à la main, 0 `<canvas>`, 0 `<img>` |
| sortie | export Chromium → **PDF A4 de 60 pages**, échelle 1:1 |
| thème | clair **et** sombre (`prefers-color-scheme` + `data-theme`) |

**Palette** : accent sarcelle `#008E7F` (clair) / `#1FA695` (sombre) · ambre `#9A6605` /
`#E9B44C` · violet « attente » `#6C5CA6` / `#A08FE0` · plus une échelle divergente pour les
écarts.

**Typographie** : **monospace dominante** — 79 usages contre 8 pour la sans-serif. Corps de
**9,5 à 14 px**, le plus fréquent étant **10 px**. Interlignes 1,5 à 1,6.

**Voix éditoriale** : les titres sont des phrases, pas des étiquettes —
*« Se tromper de bande, et de combien »*, *« Où la correction nuit, et de combien »*,
*« Ce que la correction apprend, et ce qu'elle a refusé d'apprendre »*. C'est délibéré et
on y tient : le document assume ses limites autant que ses résultats.

## 2. Le lecteur

Le jury d'une **agence régionale de surveillance de la qualité de l'air**. Ils modélisent
eux-mêmes — donc ils lisent une RMSE sans qu'on l'explique — mais **ils ne sont pas
spécialistes d'apprentissage automatique**, et certaines pages doivent rester lisibles par
un lecteur non technique.

Le document est lu **des deux façons** : parcouru à l'écran, et imprimé pour être annoté.

---

## 3. 🔴 CONTRAINTES NON NÉGOCIABLES

1. **Largeur de mise en page ≤ 718 px imprimables.** Au-delà, Chromium **met tout le
   document à l'échelle 0,90** au lieu de couper. Défaut réellement subi : l'ajout d'une
   page a fait passer le PDF de 54 à 49 pages, corps de texte de 9,75 à 8,75 pt, **sans
   qu'aucun contrôle ne le voie** — un plancher « au moins 40 pages » laisse passer une
   réduction. Cause trouvée : une seule entrée de sommaire portait la largeur à 772 px.
   Correctif : `flex-wrap: wrap`. **Toute proposition doit tenir sous cette largeur.**
2. **Zéro ressource externe.** Pas de CDN, pas de police distante, pas d'image liée. Tout
   en ligne, y compris les SVG.
3. **Généré par Python.** Une suggestion « déplacer ce bloc » n'est applicable que si elle
   s'exprime comme une règle que le générateur peut appliquer à *tous* les blocs du même
   type.
4. **Les deux thèmes doivent rester justes**, et le fond du `body` explicitement peint.
5. **Le contenu ne se raccourcit pas pour faire joli.** Chaque nombre porte son protocole
   (périmètre · épreuve · échéance) parce que le même polluant vaut de +3,31 % à +22,94 %
   selon l'épreuve. Retirer la nuance rendrait le chiffre faux.

---

## 4. Nos questions

### ① La densité — 60 pages A4 en monospace 10 px

C'est notre doute principal. Le choix vient d'une intention : un document **d'ingénieur**,
qui montre ses mesures plutôt qu'il ne les vend. Mais 60 pages à 10 px, est-ce que ça
sert le lecteur ou est-ce que ça l'épuise&nbsp;?

- Faut-il **hiérarchiser en deux niveaux de lecture** — une couche parcourable et une
  couche de preuve — et par quel dispositif visuel&nbsp;?
- La monospace partout est-elle un atout de crédibilité ou une fatigue&nbsp;? Où
  basculerait-on en sans-serif&nbsp;?
- 10 px imprimé, c'est ~7,5 pt. Quel corps minimum défendable en A4&nbsp;?

### ② Les tableaux numériques — le cœur du document

Dix tableaux, format typique&nbsp;:

| Polluant | Plancher chaîne AASQA | Notre plancher | Notre RMSE | Écart |
|---|---|---|---|---|
| NO₂ | 18,808 | **14,226** | 14,245 | +0,13 % |
| O₃ | 14,179 | **11,309** | 11,317 | +0,07 % |

Notre colonne est marquée par une classe `.nous`.

- Comment rendre **comparable d'un coup d'œil** sans colorier au point de suggérer une
  conclusion qu'on ne défend pas&nbsp;?
- Alignement des décimales, séparateurs, unités&nbsp;: quelles conventions en
  monospace&nbsp;?
- Quand un tableau devient-il une figure&nbsp;?

### ③ Les 25 SVG

Faits à la main, sans bibliothèque. **Question franche : lesquels mériteraient de
disparaître&nbsp;?** On préfère cinq figures qui portent un mécanisme à vingt-cinq qui
décorent. Quels critères pour trancher&nbsp;?

### ④ Écran contre papier

Le même fichier sert aux deux. Aujourd'hui&nbsp;: `page-break-after: always` par section,
`break-inside: avoid` sur les blocs, bandeau en `position: static` à l'impression.

- Que devrait-on **différencier** davantage entre les deux médias&nbsp;?
- Les couleurs de thème clair sont-elles imprimables telles quelles (aplats, contrastes,
  encre)&nbsp;?

### ⑤ La voix éditoriale

Les titres sont des phrases assumées, certaines pages disent **où la méthode échoue**. Est-ce
que la mise en forme actuelle soutient ce parti pris, ou est-ce qu'elle le noie&nbsp;? Comment
donner un **statut visuel distinct** à un aveu de limite, sans en faire un avertissement
anxiogène ni le rendre invisible&nbsp;?

---

## 5. Ce qu'on ne cherche pas

- Un thème à la mode qui daterait dans six mois.
- Des animations&nbsp;: le document est aussi lu sur papier.
- Un cadre CSS externe (contrainte 2).
- Alléger en **retirant des réserves méthodologiques** (contrainte 5).

## 6. Contrainte de calendrier

**Quatre jours.** Une refonte n'est pas jouable&nbsp;; on cherche les **trois ou quatre
changements de plus fort effet**. Si vous deviez n'en garder qu'un, lequel et pourquoi.

---

## 7. Rappel du format — **réponse en `.md`**

Une section par question (① à ⑤), et pour chaque recommandation&nbsp;:

| ce qu'il me faut | pourquoi |
|---|---|
| **le principe** | pour juger s'il s'applique |
| **la règle** — sélecteur CSS, contrainte de structure, seuil | pour l'implémenter dans le générateur Python |
| **ce qu'elle remplace** | sans quoi le document ne fait que grossir |
| **l'effet attendu sur le PDF A4** | c'est le médium contraignant, pas l'écran |

Et une **hiérarchie explicite** à la fin&nbsp;: si je n'applique qu'un seul de vos
changements, lequel.
