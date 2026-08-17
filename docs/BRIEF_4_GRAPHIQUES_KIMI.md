# Les graphiques et le front-end — ce qu'un œil extérieur voit et que je ne vois plus

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> Ce brief ne porte ni sur les chiffres ni sur les réserves — vous avez déjà traité les deux.
> Il porte sur **la fabrique visuelle** : les formes choisies, l'échelle typographique, la
> couleur, la façon dont les figures sont construites, et ce que tout cela vaut pour un jury
> qui lit un PDF et regarde une démonstration en direct.
>
> **Pour chaque recommandation, quatre choses — et la troisième est celle qui a le mieux payé
> les fois précédentes :**
>
> 1. **la règle de composition**, pas le correctif ponctuel ;
> 2. **ce qu'elle REMPLACE** — le document ne doit pas grossir ;
> 3. **le code** — CSS, structure SVG, ou paramètres Plotly. Vos deux propositions
>    vérifiables sont devenues des gardes qui refusent l'export, et rien n'a mieux tenu ;
> 4. **le contrôle mécanique** qui empêche la régression.
>
> 🎯 **Ce que je vous demande est difficile et je l'assume : je veux savoir ce qui rendrait
> ces pièces impressionnantes, pas seulement correctes.** J'ai corrigé tout ce que vous avez
> signalé ; le résultat est honnête et probablement quelconque. Dites-moi ce qui manque pour
> passer de « rigoureux » à « remarquable » — et si votre réponse est que la rigueur suffit
> et qu'il ne faut rien ajouter, dites-le aussi clairement.
>
> ⏱️ **4 jours.** Candidature pour un poste d'ingénieur en prévision de qualité de l'air, dans
> une association agréée de surveillance. Le jury imprime le PDF et regarde la démo projetée.

---

## 1. L'inventaire mesuré — pour que vous jugiez sur des nombres, pas sur ma description

Mesuré à l'instant sur les fichiers eux-mêmes :

| | valeur | ce que j'en pense, à corriger |
|---|---:|---|
| `<figure>` dans la présentation | **10** | |
| dont **construites par script au chargement** | **5/10** | invisibles dans le HTML statique ; 40 écritures `innerHTML` |
| `<svg>` | 25 | dont icônes et jauges |
| `<table>` | 11 | probablement trop pour dix pages |
| `<img>` · `<canvas>` | **0** · 0 | tout est vectoriel — bien pour l'impression, mais peut-être aride |
| **tailles de police distinctes** | **50** | 🔴 il n'y a pas d'échelle typographique, il y a un nuage |
| graisses distinctes | 400, 600, **620, 640**, 700 | 620 et 640 sont-elles perceptibles ? |
| couleurs littérales **hors de tout bloc de thème** | **2**, 4 occurrences | ✅ mesure corrigée — voir § 4 |

**Les marques SVG réellement employées** : `rect` ×38, `circle` ×22, `path` ×60, `line` ×20,
`text` ×95. Dans la démo Streamlit, Plotly n'est appelé qu'avec `add_scatter` ×5,
`add_bar` ×2, `add_histogram` ×1, plus une carte `Scattergeo`.

**Autrement dit : tout le dossier tient en barres, lignes, nuages et tableaux.** Aucune forme
n'a été choisie pour ce qu'elle montre — elles ont été choisies parce qu'elles étaient
disponibles.

---

## 2. Ce que chaque figure doit faire dire — et la question que je vous pose sur chacune

Voici les dix figures, avec **l'affirmation qu'elles servent**. Ma question est la même pour
toutes : *la forme choisie est-elle celle qui rend cette affirmation évidente, ou seulement
celle qui la rend lisible ?*

| # | ce que la figure doit faire comprendre | forme actuelle |
|---|---|---|
| 1 | Une moyenne glissante de sept jours fait **43 %** du travail ; l'apprentissage n'ajoute que 2,7 à 5,7 points | barres groupées |
| 2 | Retirer une famille de variables coûte peu ; **aucune n'est indispensable seule** | barres horizontales |
| 3 | Le trajet source → décision : neuf étapes, deux périmètres | diagramme de flux (`rect` + `path`) |
| 4 | Notre gain, par polluant et par année, **contre deux références différentes** | tableau |
| 5 | Où chaque système gagne, **station par station** (476 points) | carte + tableau |
| 6 | Le motif **temporel** réel, et ce que chaque système en restitue | série temporelle |
| 7 | Où va l'erreur **par bande de concentration** | barres empilées |
| 8 | Les journées réellement mauvaises, **annoncées comme bénignes** | tableau |
| 9 | Exiger deux jours de suite retire **34 % des fausses alertes sans perdre un épisode** | tableau |
| 10 | Trois demandes de service, **une seule sortie** | schéma |

**Mes questions :**

1. **Lesquelles de ces dix affirmations sont mal servies par leur forme ?** Je soupçonne la 2
   (un classement d'importance en barres est le degré zéro), la 7 (des barres empilées pour
   une distribution conditionnelle), et la 9 (un gain de précision présenté en tableau alors
   que c'est un mouvement dans un plan précision–rappel). Mais je suis juge et partie.
2. **Y a-t-il une forme qu'un dossier de ce type devrait contenir et qui manque totalement ?**
   Nous n'avons ni petit multiple, ni graphique de pente, ni diagramme de Sankey, ni
   représentation de distribution autre qu'un histogramme. Est-ce un manque ou une discipline ?
3. **Faut-il moins de figures ?** Dix figures et onze tableaux sur dix pages. Quelle est la
   densité qu'un jury absorbe réellement, et qu'est-ce qui gagnerait à disparaître ?

---

## 3. 🔴 Les 50 tailles de police — le défaut que je ne sais pas réparer proprement

Vous l'aviez signalé (« 43 valeurs ») et je ne l'ai pas traité, parce que je ne savais pas
**par quoi** remplacer. J'en compte maintenant 50, de `8,2px` à `34px`, avec des voisinages
absurdes : `10,2 / 10,4 / 10,5 / 10,6 / 11 / 11,4 / 11,5 / 11,6 / 11,7 / 11,8`.

**Ce que je vous demande, très concrètement :**

1. **L'échelle** — combien d'échelons, quel rapport entre eux, quelles valeurs exactes. Je
   veux des nombres, pas un principe. Le corps de texte est à 16px, les légendes de figure
   autour de 10px, les valeurs de graphique autour de 9,4px.
2. **La correspondance** : quel échelon pour quel rôle — titre de page, titre de figure,
   corps, légende, étiquette d'axe, valeur numérique, note de bas de page, chiffre de tête.
3. **Le contrôle mécanique** : comment refuser une taille hors échelle ? Une liste blanche
   dans un test qui parcourt les `_p*.css` ? Et que faire des tailles inline dans les SVG
   générés par script, qui échappent au CSS ?
4. **Les graisses.** J'ai 400, 600, 620, 640, 700. **620 et 640 sont-elles seulement
   distinguables ?** Si non, dites-moi lesquelles garder.

---

## 4. La couleur — ma première mesure était trompeuse, la corrigée ne l'est pas

⚠️ **J'annonçais 49 littérales hors jetons. C'est faux, et la façon dont je m'en suis aperçu
vaut d'être dite** : je ne retirais que les blocs `:root`, pas les blocs `[data-theme=…]`.
En retirant **tous** les blocs de thème, il reste **2 couleurs littérales, 4 occurrences** —
et les 47 autres sont des **palettes de graphique déclarées en paires clair/sombre**, ce qui
est le comportement voulu.

Les deux restantes sont sur le même élément, le bouton de segment sélectionné :
`background: var(--accent); color: #fff` et `.faible { color: #FFE9B8 }`. Elles sont
**délibérées** — l'accent est sombre dans les deux thèmes (`#008E7F` clair, `#1FA695`
sombre), donc un premier plan clair y tient, et le faire suivre le thème le casserait.

**Autrement dit : il n'y a pas de problème de couleur à résoudre.** Les questions ci-dessous
tiennent quand même, parce qu'elles portent sur le *choix* des palettes, pas sur leur
déclaration.

Les jetons du document sont validés en contraste, et les palettes de graphique existent en
paires clair/sombre déclarées à la main.

| rôle | clair | sombre |
|---|---|---|
| accent, gain, intégré | `#008E7F` | `#1FA695` |
| réfuté, valeur négative | `#A8452F` | `#D9704E` |
| en attente | `#6C5CA6` | `#A08FE0` |
| fil réglementaire « ATMO » | `#9A6605` | `#E9B44C` |
| traits, encres | `#D3DEDE` `#0B1A1D` … | `#1B3238` `#E4EEEE` … |

Les palettes de graphique, elles, sont des littérales : `#4FB3A3`, `#00463F`, `#178A7C`,
`#6FE3CE` pour une page ; `#8674BE`, `#40307A`, `#8E79D4`, `#C7B6F5` pour une autre.

**Mes questions :**

1. **Une palette séquentielle et une palette divergente déclarées en jetons résoudraient-elles
   le problème**, ou est-ce que les graphiques ont légitimement besoin de leurs propres
   couleurs ? Je penche pour la seconde mais je n'en suis pas sûr.
2. **Comment garantir la lisibilité en impression noir et blanc ?** Un jury peut imprimer en
   monochrome, et je n'ai **aucun** contrôle là-dessus. Faut-il doubler chaque encodage
   couleur par une forme, une texture ou une position ?
3. **Le daltonisme.** Nos deux pôles sont sarcelle et brique — probablement acceptables — mais
   je ne l'ai jamais vérifié. Existe-t-il un contrôle simple, exécutable, plutôt qu'un
   simulateur en ligne ?

---

## 5. La construction par script — un choix que je n'ai jamais interrogé

**5 figures sur 10 sont vides dans le HTML** et peuplées au chargement par 40 écritures
`innerHTML`, depuis des blocs `<script type="application/json">` inlinés.

C'est ce qui a rendu possible un mode de perte que vous avez trouvé : si la capture PDF
précède la fin des scripts, le document emporte des emplacements vides que le CSS masque
lui-même. **C'est réparé** — l'export attend maintenant une condition, chaque script pose un
drapeau, et l'export refuse en nommant la page fautive (éprouvé dans les deux sens).

**Mais la question de fond demeure : fallait-il construire ces figures par script ?**

1. **Quel est l'argument pour le rendu statique** — un SVG écrit directement dans le HTML par
   le générateur Python, sans JavaScript ? Le document devient inerte, imprimable, archivable,
   et le mode de perte disparaît au lieu d'être gardé.
2. **Qu'est-ce qu'on perdrait ?** Aujourd'hui les scripts font du survol, du filtrage, et un
   redimensionnement. Est-ce que ça vaut la fragilité ?
3. Si vous recommandez de rester en script, **quelle discipline** — un rendu au premier
   affichage puis figé, une hydratation progressive, autre chose ?

---

## 6. La démo Streamlit — le front-end que je maîtrise le moins

Six pages, Plotly, thème par défaut, une fonction de mise en forme unique
(`system-ui`, 12px, fonds transparents). C'est la pièce **opérée en direct devant le jury**,
projetée depuis un ordinateur portable.

**Mes questions :**

1. **Le thème Streamlit par défaut dessert-il le propos ?** Il est neutre, ce qui est
   rassurant, mais la présentation HTML a une identité forte (fond pétrole froid, encre
   bleu-vert, accent sarcelle) et la démo n'en a aucune. **Faut-il les rapprocher, et
   jusqu'où ?** Un `config.toml` de thème coûte cinq lignes.
2. **Que faut-il changer pour une projection ?** Contraste, taille minimale de texte,
   épaisseur de trait — je n'ai jamais testé la démo sur un vidéoprojecteur, et je ne saurai
   pas avant le jour même.
3. **Les figures Plotly par défaut** portent une barre d'outils, un fond quadrillé, des
   infobulles génériques. Qu'est-ce qui doit disparaître et qu'est-ce qui doit rester ?
4. **La carte des 476 stations** est un `Scattergeo` avec une échelle divergente bornée au
   98ᵉ centile. C'est la figure la plus regardée de la démo. **Est-ce la bonne
   représentation** pour 476 points sur la France, ou faut-il autre chose — hexagones,
   agrégation par département, cartogramme ?

---

## 7. La question que je n'arrive pas à formuler seul

Ce dossier a une thèse : **une correction apprise vaut ce que vaut son protocole
d'évaluation**, et l'essentiel du travail a consisté à mesurer honnêtement plutôt qu'à
maximiser un chiffre. Le document publie ses échecs à côté de ses réussites.

**Est-ce que cette posture SE VOIT dans la forme ?** Ou est-ce que la forme dit simplement
« rapport technique soigné », pendant que la posture reste dans le texte ?

Je crois que c'est le vrai enjeu et je ne sais pas y répondre. Un document qui affirme
« voici où j'échoue » devrait peut-être **regarder différemment** d'un document qui affirme
« voici mes résultats ». Si vous voyez une réponse formelle à ça — une convention visuelle,
une hiérarchie, un traitement des chiffres négatifs — c'est ce qui m'intéresserait le plus
dans toute votre réponse.

---

## 8. Ce que je vous demande de NE PAS proposer

- **Une refonte.** Quatre jours, et le document est stable et contrôlé.
- **Une dépendance externe.** Politique de sécurité stricte à la publication : pas de CDN,
  pas de police distante, pas de script tiers. Tout est inline ou n'existe pas.
- **Une bibliothèque de graphiques.** Les SVG sont écrits à la main et c'est ce qui permet le
  contrôle d'impression ; la démo utilise Plotly, déjà installé.
- **Des conseils qui ne se vérifient pas.** Si une recommandation ne peut pas être contrôlée
  mécaniquement, dites-le explicitement — je préfère le savoir que de croire qu'elle tiendra.

---

## 9. Où lire les pièces

| pièce | ce que c'est |
|---|---|
| `reports/figures/presentation_atmo.html` | le dossier, 10 pages, exporté en PDF 61 pages, échelle 1:1 |
| `reports/figures/_p*_style.css` · `_p*_script.js` · `_p*_section.html` | les fragments injectés (pages 00, 04, 05, 06, 07, 08) |
| `app.py` | la démo Streamlit, 746 lignes, **opérée en direct** |
| `scripts/exporter_pdf.py` | trois gardes d'impression : largeur, écrêtage interne, scripts terminés |
| `reports/figures/Découverte_ATMO.html` | un second document, grand public, autre identité visuelle |
| `docs/REVUE_2_DESIGN.md` | votre revue précédente — dont j'ai appliqué le point n° 1 |
