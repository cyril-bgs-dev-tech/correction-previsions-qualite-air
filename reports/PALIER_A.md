# Palier A — rendre les chiffres réfutables avant d'en chercher de nouveaux

*23 août 2026. Ce document n'annonce aucun gain de score : il dit ce que les chiffres
déjà publiés valent réellement, et ce que le plan d'expérience sait ou ne sait pas
trancher. Trois d'entre eux ont changé de statut.*

---

## Ce que le palier a déplacé, en une page

| | avant | après | ce qui l'a fait bouger |
|---|---|---|---|
| **28 ratios d'échelle** | ✅ tient, p_PC = 0,0006 | 🔴 **réfuté** | le `p` était bilatéral : PM10 à **−0,66 %** comptait comme une confirmation |
| **précurseurs, moyennes ET maxima** | ✅ tient, p_PC = 0,0288 | 🔴 **non confirmé** (0,1185) | le bootstrap est asymptotique sur 9 blocs ; la permutation est exacte |
| **étalon ozone CCQM.O3.2019** | inconclusif, 1 mois | **non détecté**, 12 mois, ±2,70 pt | l'archive CAMS s'est remplie ; le blocage de 2026-08-02 n'existait plus |
| **apport des 9 familles** | 9 étages cumulés | **3 démontrées, 3 sans puissance, 3 vides** | l'apport se mesure en dernière position, pas dans l'ordre d'empilement |

---

## 1. Le défaut qui a tout déclenché — un `p` qui ne regardait pas le signe

La conjonction partielle de Benjamini-Heller teste *« l'effet est présent dans au moins
deux groupes »*. Alimentée par des `p` **bilatéraux**, elle ne distingue pas un groupe
qui confirme d'un groupe qui contredit :

```
③ + ratios des 5 familles (28)
  NO2   +1,212 %   p = 0,0002      ← aide
  PM10  −0,657 %   p = 0,0002      ← NUIT, avec la même force
  → « ✅ TIENT sur deux groupes »
```

Deux groupes significatifs, oui — **de signes opposés**. La configuration allait entrer
dans la pile. Les `p` sont devenus unilatéraux : `p⁺` alimente la conjonction, `p⁻`
réfute, et **la réfutation se teste avant la conjonction**.

Le seuil de réfutation n'est pas corrigé pour la multiplicité, délibérément : ne pas
promouvoir une famille utile se répare par une mesure de plus, publier une famille qui
nuit ne se répare pas.

---

## 2. L'instrument saturait — la permutation remplace le bootstrap

En calibrant le criblage, **cinq configurations sur dix rendaient exactement 0,0003**. Ce
n'est pas un accord : c'est le plancher du bootstrap, `3 × 1/(B+1)`. Avec 8 à 12 blocs et
un effet régulier, aucun rééchantillon ne traverse zéro.

Sous H₀, le signe de l'écart d'un bloc est **échangeable**. Le test exact est donc la
permutation par retournement de signe. Le `p` y passe ; **l'IC95 reste au bootstrap**, qui
est bon à cela et que la permutation ne sait pas produire.

Une seule conclusion bascule, et elle est actionnable : *« précurseurs, moyennes ET
maxima »* (8 colonnes) tombe, *« moyennes seules »* (4 colonnes) tient sur les deux axes.
**La pile en service porte la variante à 8 colonnes.**

---

## 3. Ce que chaque famille paie vraiment

La colonne `apport_marginal_pct` mesure un apport **dans l'ordre d'empilement** : la
famille placée tôt encaisse ce qu'elle partage avec les suivantes. Le seul apport
interprétable est celui de la **dernière position** — la pile complète moins la famille.

*Mesuré sur le corpus corrigé — spéciation complète à 37 mois. Les valeurs entre
parenthèses sont celles d'avant, sur 32 mois.*

| | famille | apport | lecture |
|---|---|---|---|
| ✅ | **typologie** | +3,53 pt *(+3,39)* | démontrée |
| ✅ | **geoscf** | +0,51 pt *(+0,48)* | démontrée |
| 🟠 | **speciation** | +1,46 pt *(+1,25)* | les 4 polluants positifs |
| 🟠 | **precurseurs** | +0,76 pt *(+0,64)* | les 4 positifs |
| 🟠 | **membres** | +0,40 pt *(+0,43)* | les 4 positifs |
| 🟠 | **profil** | +0,17 pt *(+0,01)* | les 4 positifs |
| 🔴 | **fourier** | +0,13 pt *(+0,28 ✅)* | **perd son statut démontré** |
| 🔴 | **tendance** | +0,15 pt *(−0,07 réfutée)* | n'est plus réfutée |
| 🔴 | **feux** | −0,09 pt *(−0,17)* | rien |

🔴 **Cinq mois de spéciation en plus font tomber `fourier` de « démontré » à « non
confirmé », et lèvent la réfutation de `tendance`.** Deux des trois familles établies n'en
sont plus. Il ne reste que `typologie` et `geoscf`.

**🟠 n'est pas 🔴, et les confondre coûterait cher.** Sur huit blocs, aucun `p_PC` de
permutation ne peut descendre sous **0,0117**, quel que soit l'effet. La spéciation à
+1,25 pt avec quatre polluants positifs n'est pas réfutée : elle est **hors de portée de
ce plan**. La réponse est de gagner des mois, pas de retirer la famille.

---

## 4. Ce que le protocole sait résoudre — et ce qu'il ne sait pas

| grandeur | valeur | conséquence |
|---|---|---|
| résolution de l'écart apparié | **±0,36 à ±0,48 %** | un gain sous ce seuil n'est pas un petit résultat, c'est un non-résultat |
| plancher de `p_PC` à 8 blocs | **0,0117** | un effet modeste ne PEUT pas y être significatif |
| taille réelle du test | **0,0015** | la conjonction partielle est **34× plus sévère** que son seuil nominal |
| seuil calibré après criblage de 10 | **0,0974** | le criblage **ne consomme pas** le budget — c'est la sévérité du test qui écarte |

Le dernier point renverse une réserve que le dépôt portait : entre 0,05 et 0,097, un
résultat n'est pas écarté par le criblage. Il est écarté par la sévérité du test, **ce qui
n'est pas la même réserve** — et le chiffre reste un minorant, les pistes abandonnées
avant d'écrire un CSV n'étant pas comptées.

---

## 5. Les garde-fous posés, et ce qu'ils attrapent

| mécanisme | ce qu'il rend impossible |
|---|---|
| `rendre_verdict` + 9 tests | un groupe en sens inverse compté comme une confirmation |
| `ablation_jointe.py` · garde de fenêtre | conclure d'un écart entre **deux fenêtres différentes** |
| `controle_pretraitement.py` + 6 tests | une dérive du corpus, **dans les deux sens** — un plancher ne voit pas un corpus qui gonfle, et le doublon d'appariement gonflait |
| `registre.py` | une prédiction reformulée après la mesure |
| `calibrer_criblage.py` | citer un biais de criblage venu d'une autre expérience |

---

## 5 bis. Un code d'époque dans la pile publiée — et qui ne paie rien

`feux` couvre 2023-08 → 2025-05 et la fenêtre de la pile va jusqu'à 2025-12. Compté mois
par mois : **la famille est absente de 10 mois sur 29, soit 34 % de la fenêtre — et les
dix sont en 2025.**

Sous validation mois-caché, « feux absent » équivaut donc à « on est en 2025 ». Le modèle
peut apprendre la date au lieu des feux, et rien ne lève. C'est la raison d'être de la
variante *auditable* (`--support-complet`), qui écarte les familles trouées ; la variante
*comparable*, elle, les garde.

Ce qui est nouveau ici est la conjonction : **cette famille porte un code d'époque ET rend
−0,17 pt en dernière position.** L'argument d'hygiène et l'argument de score pointent dans
le même sens, et le second ne dépend pas de la résolution du premier.

| famille | couverture | absent de la fenêtre | apport |
|---|---|---|---|
| geoscf v1 | 2023-08 → 2025-12 | 0 % — **c'est elle qui borne** | +0,48 pt ✅ |
| speciation | 2024-01 → 2026-08 | 17 % (les 5 mois de 2023) | +1,25 pt 🟠 |
| **feux** | 2023-08 → 2025-05 | **34 %, tous en 2025** | **−0,17 pt** 🔴 |
| precurseurs · chimie | 2023-08 → 2026-08 | 0 % | +0,64 pt 🟠 · à mesurer |

---

## 5 ter. Ce que les ablations jointes ont tranché — ⚠️ à re-mesurer

⚠️ **Ces huit mesures datent de l'ancien corpus**, avant la complétion de la spéciation.
Elles sont en file de reprise. Le déplacement de la base ayant fait tomber `fourier` et
levé la réfutation de `tendance`, il n'y a aucune raison de croire ces conclusions stables.

Écart apparié pli à pli entre la pile complète et la pile réduite, IC95 par bootstrap,
`p` par permutation exacte. Le signe est celui du **coût** : positif, la pile perd à
retirer.

| groupe retiré | NO₂ | O₃ | PM10 | PM2,5 |
|---|---|---|---|---|
| **feux + tendance** | +0,007 | +0,352 | −0,047 | **−0,715** ✅ |
| **geoscf + membres** | **+0,545** ✅ | **+1,173** ✅ | **+0,850** ✅ | *en cours* |

**Les deux familles réfutées ne coûtent rien à perdre — et sur PM2,5 la pile y gagne
0,71 point**, IC95 [−1,324 ; −0,064]. Sur les trois autres le plan ne voit pas de
différence. Combiné aux 34 % d'absence de `feux`, score et hygiène pointent dans le même
sens.

**GEOS-CF et les membres, eux, coûtent systématiquement** — trois polluants sur trois
résolus. `membres` paraissait inutile seul (+0,43 pt, non confirmé) parce qu'il est mesuré
en présence de GEOS-CF.

⚠️ **Leur structure interne reste indécidable.** Les écarts entre le retrait joint et la
somme des retraits individuels valent 0,17 · 0,39 · 0,29 pt pour des résolutions de
0,27 · 1,06 · 0,67. Additif, redondant et substituable sont indiscernables ici — et une
première lecture avait annoncé « REDONDANTES » en comparant ces quantités à 0,05 près,
une constante devinée.

---

## 5 quater. Compléter la spéciation déplace la base

Les cinq mois de 2023 manquants ont été téléchargés. Mesuré par accident, un script ayant
refait une mesure sur le corpus corrigé :

| | 32 mois de spéciation | 37 mois |
|---|---|---|
| base NO₂ | 41,336 % | **41,508 %** |
| apport apparié des précurseurs, moyennes | −0,071 | **−0,273** |
| moyennes et maxima | +0,080 | **−0,115** |

**La base gagne ~0,17 pt et l'apport marginal des précurseurs diminue d'autant.** Ce n'est
pas du bruit : c'est la disparition d'un code d'époque — la spéciation était absente de
cinq mois entiers dans la fenêtre — qui valait de la performance apparente.

Conséquence de méthode : **toute la chaîne se régénère sur le corpus corrigé, piles de
référence d'abord.** Mesurer un apport sur une base périmée, c'est deux mesures.

---

## 5 quinquies. 0,14 % de données déplacent le chiffre publié de 0,3 point

Les quatre piles ont été refaites sur le corpus corrigé. Trois montent, l'ozone ne bouge
pas :

| | avant | après | Δ |
|---|---|---|---|
| NO₂ | 41,23 % | **41,52 %** | +0,28 |
| O₃ | 20,51 % | 20,51 % | −0,01 |
| PM10 | 21,13 % | **21,36 %** | +0,23 |
| PM2,5 | 13,65 % | **13,96 %** | +0,32 |

PM10 n'aurait pas dû bouger : sa fenêtre commence en 2024-01, où la spéciation était déjà
complète. Mesuré, l'écart d'entrée vaut **476 jours-station sur 347 956, soit 0,14 %** — le
seul 2024-01-01, qui n'existait pas avant que le fichier de 2023-12 ne soit téléchargé.
Et `n_test` est **identique sur les 24 plis**, ce qui exclut un changement de découpage.

Ce que cela dit du protocole, et c'est le point :

| | |
|---|---|
| variabilité à données **identiques** | **≤ 0,039 pt** par pli (rejeu PM2,5, 29 plis) |
| déplacement après **0,14 %** de données en plus | **jusqu'à 2,56 pt** par pli, +0,23 en agrégé |

Soit **65 fois** le bruit d'exécution pour un quatorze-millième du corpus. Le gradient
boosting n'est pas stable au sens de Lipschitz : une décision de coupe bascule, et l'écart
se propage. **Le chiffre publié est donc sensible à une perturbation de 0,1 % des données à
peu près autant qu'à la résolution du plan** (±0,36 à ±0,48 %).

Conséquence pratique : la deuxième décimale d'un gain n'a pas de sens, et la première n'est
pas robuste. Les comparaisons **appariées** — même plis, même graine, même découpage — ne
sont pas touchées : c'est précisément pour cela qu'elles portent toutes les conclusions de
ce document.

---

## 5 sexies. Ce que la fenêtre complète peut et ne peut pas dire

Écrit **avant** que ses résultats ne tombent, pour ne pas les lire de travers.

La variante `--fenetre complete --exclure geoscf,feux` porte plus de mois que la référence.
Elle n'est donc **pas comparable en score** : deux fenêtres différentes ne se soustraient
pas, et `comparer_piles.py` refusera de le faire. Restreindre les deux à leurs mois communs
ne réparerait rien — la variante aurait été *entraînée* sur des mois que la référence n'a
pas vus.

Ce qu'elle peut dire, et c'est pour cela qu'elle a été lancée : **est-ce que douze blocs
rendent testable ce que neuf ne résolvent pas ?** Trois familles échouent aujourd'hui par
puissance et non par absence d'effet — spéciation +1,25 pt, précurseurs +0,64, membres
+0,43, toutes avec les quatre polluants positifs. C'est la prédiction scellée `a2706756`.

⚠️ Et une partie de la réponse est déjà connue : le test à blanc montre que la variante
retire aussi **`membres` et `era5`**, dont la couverture est trouée. La question se réduit
donc à la spéciation et aux précurseurs — et le coût du retrait de `geoscf + membres` est
mesuré à **+0,545 à +1,393 pt** selon le polluant, tous résolus.

**Un gain de puissance qui coûte une famille démontrée n'est pas un progrès : c'est un
échange, et il se juge sur les deux plateaux.**

---

## 5 septies. Chimie et précurseurs partagent la moitié de leur variance

Les deux nouvelles familles de chimie CAMS sont mesurées **contre la même base**, celle à
huit familles. Leurs apports ne s'additionnent donc pas — et sur l'ozone la tentation
serait forte : +1,63 pt pour les précurseurs, +1,17 pour la chimie.

Mesuré sur 524 552 jours-station communs :

| variable de chimie | R² sur TOUTES les précurseurs |
|---|---|
| `chi_chocho_conc` (glyoxal) | 0,58 |
| `chi_no_conc` (monoxyde d'azote) | 0,62 |
| `chi_co_conc` (monoxyde de carbone) | 0,56 |
| `chi_hcho_conc` (formaldéhyde) | **0,42** |

Corrélation par paires maximale : **0,76**, entre le NO et les COV non méthaniques — deux
traceurs de la même combustion.

**Corrélées, donc, mais pas redondantes** : 38 à 58 % de chaque variable reste hors de
portée des précurseurs, et le formaldéhyde est la plus indépendante des quatre. Ce qui
est exclu, c'est l'addition — l'apport conjoint sera inférieur à la somme, et il se mesure
en promouvant la chimie dans la pile puis en relançant l'ablation, qui juge chaque famille
**en présence** des autres.

---

## 6. Ce qui reste ouvert

1. **Trois prédictions scellées** attendent leurs mesures — ablations jointes
   `feux+tendance` et `membres+geoscf`, en file.
2. **`precurseurs` à 4 colonnes plutôt que 8** — à mesurer, pas à décider ici : choisir
   après avoir vu les résultats est du criblage, et le score d'une pile élaguée se
   re-mesure sur des plis qui n'ont pas servi à la choisir.
3. **La propreté d'époque de la pile publiée** — le chantier que le palier a ouvert sans
   le chercher. La pile imprime son propre diagnostic à chaque exécution, et personne ne
   l'avait lu :

   ```
   precurseurs  28/29 mois · troués : 2023-08 (54 %)
   speciation   13/29 mois · troués : 2023-08 à 2023-11 (100 %) …
   membres      28/29 mois · troués : 2023-11 (97 %)
   feux         (mesuré à part) : absent de 10 mois sur 29, tous en 2025
   ⚠️ CONSERVÉES : la mesure porte un indicateur d'époque implicite.
   ```

   Trois gestes le referment, et les trois sont mesurables séparément :

   | geste | effet attendu | coût |
   |---|---|---|
   | spéciation 2023 complétée *(téléchargée, en attente)* | 13/29 → 18/29 | aucun |
   | nitrate et matière organique hors de la famille | 18/29 → **29/29** | une colonne redondante de `sia_conc` |
   | `feux` retiré | supprime 34 % d'absence | −0,17 pt, donc négatif |

   Au bout, la pile *comparable* et la pile *auditable* n'ont plus de raison de différer —
   et l'écart actuel est de **4,74 points sur l'ozone**. C'est la mesure qui tranchera si
   les chiffres publiés doivent changer.

4. **Gagner des blocs — et le chemin est identifié.** GEOS-CF v1 borne la fenêtre à
   29 mois (9 blocs, plancher de `p_PC` à 0,0059). Sans lui ni `feux`, le corpus va à
   37 mois (12 blocs, plancher 0,0007), une fois complétés les cinq mois de spéciation de
   2023 — des requêtes de surface, que le test contrôlé de ce soir montre fonctionnelles
   quand les niveaux verticaux échouent. L'arbitrage est explicite : **+0,48 pt démontrés
   contre huit mois de corpus**, et la prédiction est scellée (`a2706756`).
