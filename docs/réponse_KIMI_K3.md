# Revue de design — réponse au brief `BRIEF_DESIGN_KIMI.md`

Revue menée sur la pièce elle-même (`presentation_atmo.html`, ses six fragments injectés,
`injecter_pages.py`, `exporter_pdf.py`) **et sur l'artefact final** — le PDF a été régénéré
et son contenu textuel compté. Trois faits mesurés modifient les prémisses du brief avant
toute question de goût.

---

## Ce que la mesure change dans le brief

### 🔴 Fait 1 — Le PDF actuel est tronqué, et aucun contrôle ne peut le voir

Le contrôle d'`exporter_pdf.py` mesure le débordement **du document** (et répond
correctement : 718 ≤ 718, échelle 1:1). Mais il ne mesure pas l'écrêtage **à l'intérieur**
des conteneurs `overflow-x: auto`. Or, à la largeur imprimable, la colonne utile fait
~615 px et :

| élément | contenu | visible | perdu au PDF |
|---|---|---|---|
| `#p4-tab` (le tableau des gains, page 04) | 805 px | 615 px | **le bloc de droite entier** |
| `#p5-persist` (page 05) | 833 px | 615 px | ~les deux dernières colonnes (« écart », « rappel ») |
| `.p5-pf` | 640 px | 615 px | ~25 px |
| `.p6-tab-part` | 640 px | 607 px | ~33 px |
| `#p4-bande` | 620 px | 615 px | ~5 px |

Vérification sur l'artefact, pas sur le rendu : le texte extrait de la page 36 du PDF
s'arrête à la colonne « NOUS (contre CAMS brut) ». **La colonne que le document lui-même
appelle « la colonne qui se cite » — notre gain contre la chaîne en service, avec le gain
contre sa version réglée — n'existe nulle part dans le tableau imprimé.** Ses valeurs
(+22,64 %, +16,75 %…) n'apparaissent dans le PDF que dans la prose et les figcaptions. La
page imprimée annonce « À droite, séparée par un filet, la colonne qui se cite » — et le
filet et la colonne sont hors champ.

C'est la § 2 quinquies de `CLAUDE.md` à l'identique : le seuil regarde du côté où le défaut
ne pousse pas. Et c'est le seul point de cette revue qui rende l'artefact **faux**, pas
seulement fatigant.

### 🔴 Fait 2 — Les pages 07 et 08 sont un second système de design, non raccordé

- `--bord` n'est **défini nulle part** dans le dossier (il l'est dans `vue_territoires.html`,
  un autre document). Dans p7/p8, `var(--bord,#d3dbe1)` tombe donc *toujours* sur son
  repli — en clair ça passe inaperçu (#d3dbe1 ≈ `--trait`), **en sombre les filets des
  tableaux restent gris clair** sur fond #0D1E22. La contrainte 4 est violée *aujourd'hui*,
  pas en risque.
- Couleurs littérales en dur dans `_p7_style.css` : `#b4342b` (un rouge qui n'est pas
  `--refute`), `#2f6f8f` (un bleu qui n'est pas `--accent`), `#eef4f8`. Aucune variante
  sombre.
- **`.reserve` n'a aucun style.** Le seul sélecteur existant est `.regle .reserve` — il ne
  s'applique pas aux blocs `.reserve` de p7/p8, qui ne sont pas dans un `.regle`. Le
  dispositif éditorial censé porter les réserves (question ⑤) **n'existe pas sur les deux
  pages construites autour des réserves**. Elles s'impriment comme des paragraphes
  ordinaires.
- Incohérence de frappe : p7/p8 en `rem` (`.p7-tab` à .94rem ≈ 15 px) contre 13,2 px
  partout ailleurs ; tableaux en **point décimal** (`11.11`, `-32.3 %`) quand la prose du
  même dossier écrit `−10,5 %` avec virgule.
- Et `validate_palette.js`, cité par deux commentaires CSS comme autorité de validation,
  **n'existe plus dans le dépôt**. Un contrôle qu'on ne peut pas rejouer est une croyance.

### 🟠 Fait 3 — La « monospace dominante » est vraie en déclarations, fausse en lecture

Le compte 79:8 porte sur les *déclarations*. La matière lue — chapeaux, corps, réserves,
limites — est en **sans-serif de 13,5 à 17,5 px** ; le monospace porte l'appareil
(étiquettes, tableaux, chiffres). En revanche il y a **43 tailles de police distinctes**
dans le document : ce n'est pas une hiérarchie, c'est une accumulation. Et le texte le plus
fin (figcaptions 10 px mono en `--encre-3`, ≈ 3,9:1 de contraste — sous le plancher WCAG
AA de 4,5:1) est précisément celui qui porte le protocole que la contrainte 5 refuse de
retirer. **La nuance que vous refusez de supprimer est composée pour disparaître.**

---

## Réponses aux cinq questions

### ① Densité — le problème n'est pas où vous le cherchez

60 pages à corps réel 13,5–14,5 px (soit **10–11 pt imprimés**, confortable) : ce n'est pas
de la densité excessive pour un dossier technique. Le « 10 px monospace » du brief n'existe
pas comme expérience de lecture. Plancher défendable en A4 : **12 px CSS (9 pt)** pour du
texte suivi ; 10 px seulement pour des étiquettes non essentielles — vos figcaptions y
sont, et elles sont essentielles.

La lecture à deux niveaux **existe déjà** : eyebrow → h1-phrase → chapeau → `.these`
forment la couche parcourable, et elle est bonne. Ce qui manque n'est pas un dispositif
nouveau mais : (a) la couche de preuve doit être *lisible* (figcaptions et réserves plus
sombres et plus grandes) ; (b) sur 60 pages papier, **aucun folio ni titre courant** — un
jury qui annote ne peut pas écrire « page 34 ». La monospace partout : ni atout ni fatigue,
puisqu'elle n'est pas partout ; là où elle porte du texte suivi (figcaptions, `.pourquoi`
en capitales mono), elle fatigue *et* grise — basculer ces passages en sans-serif, garder
le mono pour les nombres et les étiquettes.

### ② Tableaux

Les conventions sont déjà les bonnes (alignement droit, `tabular-nums`, unité en tête,
espace fine pour les milliers) — les écrire comme règle du générateur, pas comme habitude :

- **Alignement décimal** : en monospace tabulaire, alignement à droite **+ même nombre de
  décimales par colonne** suffit. C'est tenu sauf que…
- **…la locale n'est pas unifiée** : les scripts formatent en point (`nf() → toFixed`), la
  prose en virgule. *Un seul séparateur décimal dans tout le document : la virgule.* Règle
  mécanisable sur les `nf()` des six scripts.
- **Marquage « nous »** : il y a aujourd'hui **quatre traitements différents** pour la même
  sémantique — texte accent + graisse (`.planchers`), fond `accent-pale` sur la ligne (p5,
  p6), fond sur la colonne + filet (p4), graisse seule (p7). Une règle : *fond
  `accent-pale` + graisse 600, partout, et rien d'autre* — le texte vert par-dessus le fond
  vert est un double emploi qui « suggère une conclusion ».
- **Comparable d'un coup d'œil** sans sur-colorer : la colonne d'écart (signe + couleur
  `pos`/`neg`, déjà présente) doit être **adjacente à ses deux opérandes**, ce que le filet
  de la page 04 fait bien à l'écran — quand elle n'est pas coupée.
- **Quand un tableau devient une figure** : un tableau répond à « combien, précisément » ;
  une figure à « où », « quelle forme », « quel signe partout ». La pratique actuelle est
  déjà juste (cartes, bande) — il faut la formaliser pour le générateur : *plus de deux
  dimensions de comparaison, ou un motif de signes qui prime sur les valeurs → figure*.

### ③ Les SVG — recadrage d'abord

Il n'y a pas 25 figures : il y a **17 pictogrammes** (index visuel de la page Sources, coût
quasi nul, à garder) et **7 figures de données**. Critères de tri, dans l'ordre : (1) elle
montre un mécanisme qu'un tableau ne peut pas montrer (forme, répartition, signe) ; (2) une
phrase du texte s'y réfère ; (3) son titre est une conclusion, pas une étiquette.
Appliqués honnêtement : **aucune des 7 ne décore** — la figure d'ablation (la plus fragile)
se justifie parce que l'asymétrie ajout/retrait *est* une forme. Ne supprimez rien ; la
vraie discipline est ailleurs : deux figures de la page 04 disent « nous battons CAMS » à
deux grains différents — légitime, mais leurs titres doivent porter le grain, sinon elles
se doublonnent aux yeux du lecteur rapide.

### ④ Écran contre papier

Ce qui doit se différencier davantage, en règles :

1. **Aucun élément plus large que la colonne imprimable** — un tableau qui dépasse **se
   scinde en deux tableaux empilés**, jamais en scroll. Pour p4, le document lui-même donne
   la justification : « les deux blocs de colonnes ne se lisent pas ensemble » — alors
   qu'ils soient deux tableaux, ce qui est *fidèle au contenu*, pas une concession au
   papier.
2. **Les contrôles interactifs disparaissent à l'impression** (`.seg`, `.infob-aide`
   s'impriment aujourd'hui, morts, sur le papier), et l'état du filtre courant est écrit
   dans le sous-titre de la figure (partiellement fait via `.p4-eff`).
3. **Folios** : une ligne dans `exporter_pdf.py` (`display_header_footer` +
   `footerTemplate` avec `pageNumber`) — côté générateur, donc pérenne.
4. **Contraste** : `--encre-3` à ≈ 3,9:1 est sous le plancher pour le petit texte ; le
   remonter à ≈ 4,5:1 (un cran plus sombre) est un changement de **jeton**, donc une règle.
   Les teintes pâles (`accent-pale`, `refute-pale`, `ambre-fond`) s'impriment correctement ;
   le fond `--fond` #EEF3F3 passe au laser sans drame.

### ⑤ La voix — elle est soutenue dans les titres, abandonnée dans les réserves

Les titres-phrases et les `.these` fonctionnent. Mais l'aveu de limite a **quatre habitats
typographiques** : `.limites` (fond rouge pâle), `.note` (filet ambre), `.regle .reserve`
(filet tireté), `.reserve` hors `.regle` (**rien**), `.p0-pied` (paragraphe gras). Dont un
qui n'existe pas. Règle proposée : **un seul composant** pour « réserve / limite /
non-preuve » — bordure gauche sobre (pas de fond coloré : l'aplat rouge lit « alarme », et
le jeton `--refute` signifie *mesuré puis écarté*, pas *limite de portée* — confondre les
deux est une faute de vocabulaire visuelle), avec une **étiquette mono en capitales qui
porte le statut** (« Réserve — mesurée » / « Réserve — de périmètre » / « Non prouvé
ici »). Le statut est porté par le mot, jamais par la couleur : c'est ce qui le rend ni
anxiogène ni invisible.

---

## Les quatre changements, par effet décroissant

1. **Réparer la troncature papier et son contrôle.** Règle de composition : *aucun tableau
   plus large que la colonne ; s'il dépasse, il se scinde*. Règle de contrôle :
   `_JS_COUPABLES` d'`exporter_pdf.py` mesure aussi l'écrêtage interne (`scrollWidth >
   clientWidth` dans un conteneur à défilement) et nomme l'élément — l'infrastructure
   actuelle le fait déjà pour le document, c'est la même règle un niveau plus bas.
2. **Raccorder p7/p8 au système de jetons** — règle : *zéro couleur littérale hors `:root`,
   zéro `var()` avec repli de secours* (le repli est ce qui a caché le défaut), vérifiable
   mécaniquement sur les `_p*.css`. Le sombre redevient juste, et les deux pages cessent de
   dater d'une autre époque du projet.
3. **Unifier le statut des réserves** (question ⑤) : un composant, une étiquette, quatre
   habitats actuels convergent. Effet démesuré pour le jury, parce que c'est la posture
   entière du dossier qui devient visible — y compris sur p7/p8 où elle est aujourd'hui
   invisible.
4. **Resserrer la couche de preuve** : échelle de 6–7 tailles en jetons au lieu de 43
   valeurs, figcaptions en sans-serif 11,5–12 px `--encre-2`, virgule décimale partout.

**S'il n'en reste qu'un : le premier.** Les trois autres sont du confort et de la cohérence ;
celui-là est de la vérité d'artefact. Le document que le jury annote ne contient pas le
chiffre que le dossier désigne comme citable, et le contrôle qui devait protéger
l'impression regarde ailleurs.

*Mesures rejouables : la méthode est dans `/tmp/opencode/mesure_print.py`, et la
vérification « la colonne est-elle dans le PDF » tient en dix lignes de `pypdf`.*

---

## Calendrier

Les changements 2, 3, 4 sont des retouches de jetons et de classes — une journée. Le
changement 1 (scinder `#p4-tab` et `#p5-persist` en deux tableaux empilés) touche les
scripts de génération p4/p5 — un jour et demi avec re-vérification du PDF. Les quatre
tiennent dans les cinq jours.
