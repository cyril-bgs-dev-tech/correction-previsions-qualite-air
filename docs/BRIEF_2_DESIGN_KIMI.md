# Deuxième revue de design — la posture est devenue le problème

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> Une section par numéro. Pour chaque recommandation, je vous demande **quatre choses**, et
> c'est la quatrième qui a le mieux payé la dernière fois :
>
> 1. la **règle de composition** — pas le correctif ponctuel, la règle qui empêche la récidive ;
> 2. ce qu'elle **REMPLACE** — sinon le dossier ne fait que grossir ;
> 3. **le code** quand il s'agit de CSS ou de structure — vos deux propositions vérifiables
>    sont devenues des gardes qui refusent l'export, et rien d'autre n'a aussi bien tenu ;
> 4. **comment la vérifier mécaniquement** — la règle qu'on ne sait pas contrôler se redéfait.
>
> ⏱️ **5 jours** (échéance 22/08). La démo est **opérée en direct devant un jury**, sur un
> ordinateur portable, projetée. Le dossier est **imprimé et annoté**.

---

## 0. Ce que votre audit a produit — pour que vous ne le ré-auditiez pas

Vous avez eu raison sur **tout ce que vous aviez mesuré dans le dépôt**. Les six défauts sont
corrigés, et deux d'entre eux changeaient un verdict :

| votre point | ce qui a été fait, et ce que ça valait |
|---|---|
| **2.1** la bannière somme des seuils **emboîtés** | 🔴 **verdict inversé.** Elle porte maintenant sur **un** seuil — le plus sévère ayant ≥ 30 épisodes — et publie l'écart par seuil **sans total**. Sur la table réelle de l'échelle journalière : l'ancienne logique annonçait « +3 618 » en comptant chaque épisode jusqu'à **quatre fois** ; la nouvelle annonce **+25 au seuil ≥ 5** (189 épisodes observés) et **montre le −573 du seuil trivial** au lieu de le noyer |
| **2.2** « jeu égal dans la queue », démenti par sa propre figure | la légende se **calcule** depuis les mêmes bandes que le graphique. Elle dit désormais « +2,7 % sur la bande basse, +17,6 % dans la queue » sur PM10, et **nomme la dégradation** sur O₃ (bande 50-100 : −12,7 %) |
| **2.4** plis non bloqués spatialement | réserve ajoutée avec son chiffre : « le modèle n'a pas vu la station, il a vu ses voisines — jusqu'à −10 points sur l'ozone » |
| **2.5** le régime servi hors de son périmètre | **verdict retiré.** Le régime redevient descriptif ; PM10 reçoit « non mesuré dans cette étude » au lieu du message vert « suivable sur les pics » |
| **2.6** étiquettes décalées, indice partiel, objet spatialisé | `>` au lieu de `>=` avec « ou pire » ; les trois non-dits affichés ; docstring corrigée |
| **3.1** « Météo non extraite » sur l'écran par défaut | index lu **dans les données**, plus dans le nom de fichier |
| **3.2** 90 s sans spinner | table **précalculée au build**, module partagé `src/aq/demo.py`, repli conservé mais **bruyant** |
| **3.3** carte écrêtée à ±50 % | borne dérivée du 98ᵉ centile — **±74,5 % sur NO₂, ±29,1 % sur PM2,5** — et le nombre de stations hors plage est annoncé |

De votre **première** revue : le jeton fantôme `var(--bord, #d3dbe1)` est corrigé
(`--bord` n'existait nulle part ; le document dit `--trait`) et **mécanisé** —
`exporter_pdf.py` refuse d'exporter sur un jeton jamais défini, garde éprouvé dans les deux
sens. La virgule décimale est faite : **33 sites d'affichage** convertis, **la géométrie SVG
épargnée nommément**, le PDF passe de **135 à 11** décimales au point. Les onze restantes
sont « ODbL 1.0 », « Licence Ouverte 2.0 » et le seuil ESA `qa > 0.75` cité littéralement —
je ne francise pas le nom d'une licence.

---

## 1. 🔴 Le vrai problème n'est pas le volume — je m'étais trompé, et la mesure me corrige

J'allais vous écrire que j'avais noyé la démo sous les réserves. **J'ai mesuré avant de vous
le dire, et c'est faux** :

| | blocs | mots | `success` + `error` *(verdicts)* | `warning` + `info` *(réserves)* | `caption` |
|---|---:|---:|---:|---:|---:|
| avant ce matin | 28 | 757 | 6 | 8 | 14 |
| après | **36** | **834** | **4** | **14** | **18** |

**+8 blocs, mais seulement +77 mots (+10 %).** Le volume n'a pas explosé — plusieurs
réserves remplacent du texte statique par du texte dérivé, souvent plus court.

**Ce qui a bougé, c'est le REGISTRE.** Les verdicts reculent (6 → 4), les réserves montent
(8 → 14). Une démo qui affirmait affiche maintenant des nuances. Et surtout : **36 blocs
répartis sur 6 pages, dans 5 habitats visuels différents**, choisis au cas par cas — donc
arbitrairement. Trois réserves de même gravité portent aujourd'hui trois couleurs.

**Mes questions :**

1. **Un jury lit-il une nuance, ou seulement un verdict ?** Une démonstration en direct dure
   quinze minutes ; le lecteur suit une voix et regarde un écran. Mon hypothèse est qu'une
   réserve écrite mais non prononcée **ne compte pas** — auquel cas la vraie question n'est
   pas la densité mais **ce qui doit rester quand personne ne lit**.
2. **Quelle est la bonne règle de choix entre les cinq habitats ?** Je veux une règle à un
   seul critère, applicable sans réfléchir. Ma tentative : *un `error` dit qu'un chiffre ne
   doit pas être cité ; un `warning` dit qu'il ne vaut que sur un périmètre ; un `caption`
   dit d'où il vient.* Est-ce le bon axe, ou faut-il découper autrement ?
3. **Faut-il descendre à deux habitats ?** Cinq niveaux dans une même page, c'est une échelle
   que personne ne mémorise en quinze minutes.

### Le texte exact des huit blocs ajoutés, pour que vous jugiez sur pièce

Ils sont tous vrais et viennent tous d'un défaut que vous aviez trouvé. C'est précisément ce
qui me rend incapable d'en retirer un.

1. **`caption`, sous le graphique des bandes** *(dérivée, longueur variable)* —
   « Le gain n'est pas uniforme : **+2,7 %** sur la bande basse (0–20), **+17,6 %** dans la
   queue (≥ 100). ⚠️ La correction **dégrade** la bande 50–100 de 12,7 % — c'est visible sur
   la figure, et c'est dit. Aucune bande n'est écrasée au profit du RMSE global : une version
   antérieure gagnait 13 % en aplatissant les épisodes. »
2. **`caption`, sous l'histogramme des stations** —
   « Sur 344 stations, en validation par **station exclue** — chacune est prédite par un
   modèle qui ne l'a jamais vue. ⚠️ Les plis ne sont **pas bloqués spatialement** : le modèle
   n'a pas vu la station, mais il a vu ses voisines. Le § 11 du dossier mesure l'optimisme
   résiduel — jusqu'à **−10 points sur l'ozone** avec un fossé de 50 km. »
3. **`caption`, sous les trois indicateurs météo** —
   « **Régime ventilé** — classé sur la **moyenne nationale des 24 heures**, pas station par
   station. Une journée ventilée à Brest et stagnante à Lyon reçoit ici une seule étiquette :
   c'est une **description du jour**, pas l'objet de l'étude des régimes. »
4. **`warning` ou `info` selon le polluant, juste en dessous** —
   *(O₃/NO₂/PM2,5)* « **Ce que l'étude des régimes dit, et sur quoi exactement.** Sur
   l'**ozone seul**, à **J+1**, par **station-heure**, sur **trois mois de 2024**, la
   correction dégrade le décile supérieur de **17 %** […]. Ces trois mots — polluant,
   échéance, objet — ne se retirent pas du chiffre. »
   *(PM10)* « **Le PM10 n'a pas été mesuré dans l'étude des régimes** […]. Aucune réserve de
   confiance par régime n'est donc publiable pour ce polluant — ni dans un sens ni dans
   l'autre. »
5. **`caption` TRIPLE, en tête de l'échelle journalière** — trois avertissements séparés par
   des `·` : le sélecteur de polluant est ignoré ; 54 % des jours retenus n'ont que trois
   polluants sur quatre et l'indice est alors **optimiste par construction** ; l'indice
   réellement publié est **spatialisé**, pas calculé station par station. **C'est le bloc
   dont je doute le plus** — sept lignes avant que le lecteur voie une seule donnée.
6. **`caption`, sous la bannière de détection** —
   « Écart par seuil, **jamais sommé** — les seuils sont **emboîtés**, un même épisode compte
   dans tous ceux qu'il dépasse : ≥ 2 : −573 · ≥ 3 : +2858 · ≥ 4 : +1308 · ≥ 5 : +25 »
7. **`caption`, sous la carte** —
   « Échelle bornée à **±74 %**, dérivée du 98ᵉ centile des gains affichés. **13 stations**
   sortent de la plage et sont peintes à la couleur de la borne — la plus dégradée est à
   **−396,9 %**. Le survol donne toujours la valeur réelle. »
8. **`caption`, en pied de la page « Prévision du jour »** *(réécrit, pas ajouté)* —
   « ⚠️ Cette page est un **prototype d'aide à la décision**, pas un outil validé. Elle porte
   sur 2023-08-01 → 2026-08-08 (37 mois) à l'échéance **J0**, au pas **horaire**, avec la pile
   de base seule — ce n'est ni l'échéance, ni le grain, ni la pile des chiffres du dossier. »

**Question franche : lesquels supprimeriez-vous, et pourquoi ?** Je ne veux pas d'un
allègement qui soit une reculade — si une réserve part, il faut que ce soit parce qu'elle est
fausse, redondante ou déplacée, jamais parce qu'elle est lourde. Mais je suis mal placé pour
juger : je viens de les écrire, et chacune répare un défaut que vous m'avez montré.

---

## 2. Votre point ④.1 — le seul de votre audit que je n'ai pas su traiter

C'est celui que vous appelez **le défaut structurel** :

> **Les trois mots** — périmètre · épreuve · échéance — plus pile et corpus : absents de
> toutes les pages sauf l'échéance (⓪).

Le problème est de fond, et le dossier en donne la preuve chiffrée : **sur l'ozone, le même
travail vaut six gains différents selon l'épreuve.** Voici la table telle qu'elle est
régénérée ce matin — chaque ligne est juste, aucune n'est interchangeable, et **l'ordre
change d'un polluant à l'autre** :

| # | épreuve | échéance | O₃ | NO₂ |
|---|---|---|---:|---:|
| ①a | production, contre la **chaîne en service**, station connue | J0 | **+22,94 %** | **+44,31 %** |
| ①b | production, contre CAMS brut | J0 | +27,19 % | +51,32 % |
| ② | maximale **aux stations**, double aveugle + veille | J+2 | +24,26 % | +46,81 % |
| ③ | **maximale PARTOUT**, double aveugle sans veille ⭐ | J+2 | **+18,19 %** | **+40,16 %** |
| ④ | apport de la seule observation de la veille | J+2 | +9,24 % | +22,76 % |
| ⑤ | double aveugle de référence, **aucun levier** | J+2 | +3,31 % | +25,71 % |

**Regardez la ligne ⑤ contre la ligne ③ :** sur l'ozone la pile fait passer de +3,31 % à
+18,19 % — les leviers font l'essentiel. Sur le NO₂ elle fait passer de +25,71 % à +40,16 % —
la base fait déjà les deux tiers. **Le même graphique raconte deux histoires opposées selon
le polluant sélectionné**, et rien à l'écran ne le signale.

Un pourcentage sans ses trois mots n'est donc pas citable — c'est écrit dans le dossier, et
la démo ne le tient pas.

**La difficulté que je vous soumets : la démo a CINQ écarts au dossier, pas trois.**

| dimension | la démo | le dossier |
|---|---|---|
| **échéance** | J0 *(échéances 1-24 h)* | J+1 à J+2 |
| **grain** | horaire | journalier *(la grandeur réglementaire)* |
| **pile** | base seule — CAMS + terrain + calendrier | 6 familles empilées |
| **épreuve** | stations exclues, **mois vus**, sans fossé spatial | double aveugle, station **et** mois cachés |
| **corpus** | 2023-08 → 2026-08 | 24 à 29 mois selon le polluant |

**Conséquence chiffrée, mesurée à l'instant sur les deux jeux :**

| | NO₂ | O₃ | PM10 | PM2,5 |
|---|---:|---:|---:|---:|
| ce que la **démo** affiche | +19,2 % | +16,5 % | +17,5 % | +14,4 % |
| ce que le **dossier** annonce | **+40,16 %** | **+18,19 %** | **+20,71 %** | **+12,49 %** |

Les deux lignes sont justes. Un juré qui compare sans les cinq mots conclut qu'une des deux
ment — et **remarquez PM2,5, où la démo est SUPÉRIEURE au dossier** : l'écart ne va même pas
toujours dans le même sens, donc aucune règle mentale simple ne sauve le lecteur.

**Cinq mots ne tiennent pas dans une signature.** Mes questions :

1. **Quelle forme pour une signature dans une application interactive**, où les chiffres
   changent avec deux sélecteurs (polluant, échelle) ? La page de synthèse du dossier a résolu
   ça en HTML statique par une ligne de trois étiquettes monospace sous les chiffres. Une
   application n'a pas la même contrainte : elle peut avoir un bandeau **persistant**, hors
   flux, toujours visible. Est-ce la bonne réponse, ou est-ce que ça devient du mobilier
   qu'on ne voit plus au bout de deux minutes ?
2. **Que garde-t-on des cinq, et où va le reste ?** Mon intuition : `pile` et `épreuve` sont
   les deux qui font le plus mal si on les oublie — mais c'est une intuition.
3. **Comment éviter que la signature devienne du bruit** en étant répétée sur six pages ?
   Faut-il qu'elle change d'aspect selon qu'elle est **conforme** ou **divergente** du
   dossier ? Une signature qui ne dit jamais rien de nouveau cesse d'être lue.
4. **Question de méthode plutôt que de forme** : faut-il *au contraire* faire converger la
   démo vers le dossier — recalculer la démo à J+1, au grain journalier, avec la pile
   complète ? Ce serait supprimer le problème au lieu de l'annoter. Le coût est réel (la
   pile complète exige six familles de données que la démo ne charge pas) mais je veux votre
   avis sur **le principe** : vaut-il mieux une démo cohérente avec le dossier et moins
   riche, ou une démo riche qui exige cinq réserves ?

---

## 3. Votre point de design n° 3, non traité — et la § 1 le rend urgent

Vous l'aviez classé **3ᵉ par effet décroissant**, avec cette justification :

> Effet démesuré pour le jury, parce que c'est la posture entière du dossier qui devient
> visible — y compris sur p7/p8 où elle est aujourd'hui invisible.

Je ne l'ai pas fait, et la § 1 montre pourquoi c'est devenu plus urgent : **36 blocs de
réserve dans 5 habitats**, sans composant pour les porter.

**Ce que je vous demande précisément — et c'est du code, pas un principe :**

- un composant unique : **nom de classe, structure HTML, règles CSS complètes**, portant une
  réserve dans les **deux** artefacts, qui ne partagent aucune feuille de style — la
  présentation HTML (jetons ci-dessous) et la démo Streamlit (thème par défaut, `st.markdown`
  avec `unsafe_allow_html=True` disponible) ;
- **au plus deux niveaux de gravité**, avec la règle explicite pour choisir entre eux ;
- **le contrôle mécanique** : comment détecter qu'une réserve a été écrite hors du composant ?
  C'est la partie qui manque toujours, et sans elle la convention se redéfait en trois jours.

Les jetons disponibles côté présentation, en clair et en sombre :

```css
--fond #EEF3F3 / #071316      --surface #FFFFFF / #0D1E22
--encre #0B1A1D / #E4EEEE     --encre-2 #41585C / #9FB4B6   --encre-3 #6F8489 / #6E8489
--trait #D3DEDE / #1B3238     --trait-fort #B4C4C5 / #2A464E
--accent #008E7F / #1FA695    --accent-pale #DCEEEB / #0E2E2E   /* gain, intégré     */
--refute #A8452F / #D9704E    --refute-pale #F5E4DF / #33201B   /* mesuré puis écarté */
--ambre  #9A6605 / #E9B44C    --ambre-fond rgba(233,163,23,.055) /* fil « ATMO »      */
--attente #6C5CA6 / #A08FE0   --attente-pale #EAE6F5 / #1E1A33  /* en cours          */
--sans / --serif / --mono     --r 3px
```

⚠️ **Contrainte non négociable** : les artefacts sont publiés sous une politique de sécurité
qui bloque **tout hôte externe** — pas de CDN, pas de police distante, pas de script tiers.
Tout est inline ou n'existe pas.

---

## 4. Le PDF — deux questions que je ne sais pas trancher

1. **61 pages.** C'est le document qu'un jury imprime et annote, pour un poste en CDD dans une
   association de surveillance de la qualité de l'air. Je n'ai **aucune intuition fiable** sur
   ce qu'un jury lit réellement. Est-ce le bon format, ou faut-il une pièce courte — 4 à 6
   pages — qui pointe vers la longue ? Et si oui, **qu'est-ce qui entre dans les six pages**,
   sachant que la posture du dossier est « voici où ça marche *et* où ça échoue » ?
2. **Y a-t-il un troisième mode de perte silencieuse à l'impression ?** Deux sont désormais
   gardés : la largeur du document (718 px imprimables, refus au-delà) et l'**écrêtage
   interne** que vous aviez trouvé (`scrollWidth > clientWidth` dans un conteneur à
   défilement — c'est celui qui avait fait disparaître du PDF la colonne que le document
   désigne comme la seule citable). Je soupçonne sans savoir : `position: sticky`, `<details>`
   fermés, contenu rendu par script après le délai d'attente de 1 800 ms, `page-break` qui
   coupe une figure en deux. **Lequel mord réellement, et quel contrôle l'attrape ?**

---

## 5. Ce que je vous demande de NE PAS proposer

- **Une refonte.** Cinq jours, le document est stable, et une régénération a déjà dégradé un
  artefact sur ce projet.
- **Une dépendance externe.** Voir la contrainte de sécurité ci-dessus.
- **De supprimer une réserve pour alléger.** Si une réserve doit partir, dites **pourquoi elle
  est fausse, redondante ou déplacée**. « C'est lourd » n'est pas une raison suffisante quand
  la lourdeur est le prix de l'honnêteté.
- **Des chiffres cités de mémoire.** La dernière fois, l'autre relecteur a recommandé une clé
  d'API qui n'existait pas au catalogue ; vérifiée en trente secondes, elle aurait produit
  trois jours de données silencieusement incomplètes. Vous avez eu raison **3/3 sur ce que
  vous aviez mesuré dans le dépôt** — c'est ce mode-là que je vous demande.

---

## 6. La structure de la démo, pour que vous conceviez sur du concret

Six pages, une barre latérale persistante, deux sélecteurs globaux (**polluant**, et sur une
page **échelle de détection**). Streamlit par défaut, pas de thème personnalisé.
`st.markdown(..., unsafe_allow_html=True)` est disponible ; les figures sont en Plotly, mises
en forme par une fonction unique (`system-ui`, 12 px, fond transparent).

| page | ce qu'elle montre | réserves qui y vivent aujourd'hui |
|---|---|---|
| **Aide à l'expertise du jour** | une journée : séries, écarts, régime météo, stations divergentes | régime descriptif *(caption)* + périmètre de l'étude *(warning ou info)* + couverture ERA5 *(info)* + prototype *(caption de pied)* |
| **Vue d'ensemble** | métriques globales, bandes de concentration, distribution par station | légende dérivée des bandes *(caption)* + plis non bloqués *(caption)* |
| **Où la correction agit** | la carte des 476 stations, les moins bien traitées | écrêtage de l'échelle *(caption)* |
| **Station par station** | une station : série, profil horaire d'erreur | ⚠️ **aucune** — les métriques y sont sur tout le corpus à côté d'un graphique d'un mois |
| **Détection des épisodes** | rappel/précision par seuil, deux échelles | bannière *(success/error/info)* + écart par seuil *(caption)* + triple non-dit journalier *(caption)* + divergence des échelles *(info)* + insuffisance absolue *(warning)* |
| **Variables du paysage** | ce que le terrain apporte | — |

**Barre latérale**, visible sur les six pages — c'est le seul emplacement déjà persistant :

> **Échéance J0** — les 24 premières heures de la sortie CAMS de 00 UTC, c'est-à-dire le jour
> même. C'est l'échéance du produit officiel de référence.

C'est **la seule des cinq dimensions** (§ 2) qui soit affirmée quelque part. Les quatre
autres — grain, pile, épreuve, corpus — ne le sont nulle part de façon persistante.

**Deux observations que je vous soumets sans savoir qu'en faire :**

1. **La page « Station par station » n'a aucune réserve**, et c'est probablement celle qui en
   aurait le plus besoin : elle affiche « RMSE CAMS / RMSE corrigé » calculés sur **tout le
   corpus**, à côté d'un graphique qui n'en montre qu'**un mois**. Un juré lit le chiffre
   comme celui du mois affiché.
2. **La page « Détection » porte cinq blocs à elle seule** — c'est aussi celle qui portait le
   verdict inversé. Corriger un défaut y a manifestement produit une accumulation.

---

## 7. Où lire les pièces

| pièce | ce que c'est |
|---|---|
| `app.py` | la démo Streamlit — **celle qui est opérée en direct**, 746 lignes |
| `reports/figures/presentation_atmo.html` | le dossier, 9 pages, exporté en PDF 61 pages |
| `reports/figures/_p*_section.html` · `_p*_style.css` · `_p*_script.js` | les fragments injectés (pages 00, 04, 05, 06, 07, 08) |
| `scripts/exporter_pdf.py` | les deux gardes d'impression, dont le vôtre |
| `scripts/injecter_pages.py` | l'assemblage — ⚠️ il **écrase** les sections injectées, une édition à la main dans le fichier assemblé est perdue |
| `reports/VERITE_DOSSIER.md` | la source unique des chiffres, régénérable |
| `docs/AUDIT_DEMO_APP.md` | votre audit précédent |
