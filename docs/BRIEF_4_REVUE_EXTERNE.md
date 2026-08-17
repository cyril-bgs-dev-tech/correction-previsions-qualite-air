# Quatrième revue — je publie des chiffres dont je n'ai aucun intervalle

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> Une section par numéro. Pour chaque recommandation : **le test exact**, **le seuil de
> décision fixé avant de regarder**, **le coût en heures**, **ce qu'on écrit si le test
> échoue**, et **ce que la proposition REMPLACE** dans le dossier.
>
> ⏱️ **5 jours** (échéance 22/08). Machine à 17 paniques noyau et corruption mémoire
> matérielle avérée : **tout lot doit être reprenable** (§ 7).
>
> 🎯 **Ce dont j'ai le plus besoin n'est pas une méthode, c'est un verdict.** Les données
> sont dans ce fichier ; si vous pouvez conclure directement plutôt que m'indiquer quoi
> calculer, faites-le — chaque aller-retour coûte une demi-journée sur cinq.

---

## 0. Le contexte en dix lignes, pour que rien de ce qui suit ne soit deviné

Correction apprise des prévisions européennes **CAMS** de qualité de l'air. Le modèle apprend
le **résidu** `observation − CAMS` et le retire. Quatre polluants : NO₂, O₃, PM10, PM2,5.

**La contrainte fondatrice, qui invalide la moitié des idées naturelles** : le produit
principal est **`PARTOUT`** — aucune observation de la station n'entre à l'inférence, pas même
celle de la veille. Le but est de corriger **là où il n'y a aucune station**. Toute proposition
d'assimilation résout le problème en détruisant le produit.

**Pistes déjà mesurées et écartées — ne pas les reproposer :** GNN de voisinage (+0,28 pt),
réglage d'hyperparamètres (mirage d'axe : **+5 pts en spatial, −3 en temporel**), régression
quantile, pondération par classe, classification directe au lieu de la régression, capteur
d'anomalie sur les entrées, compression, sol et géologie (11× sous le critère de rétention),
dérivées d'ensemble (asymétrie, aplatissement : +0,05 à +0,40 %), RealMLP (+2,65 % PM10,
−0,89 % NO₂, non bootstrappé, non intégré). Adoptées : typologie de station, membres
d'ensemble, feux, GEOS-CF, tendance récente de CAMS, moyenne de sept pertes, spéciation.

---

## 1. Ce que vos trois revues précédentes ont produit

| votre recommandation | ce qu'elle a valu |
|---|---|
| échelle de falsification `C` / `R` / `F` / **permutation conditionnelle** | **la clé du dossier.** La permutation dans (station × mois) efface **100 %** du gain de la spéciation, 4/4 → ni encodeur site×saison, ni proxy de régime |
| Shapley plutôt qu'ablation un-à-un | l'ablation un-à-un était bien inutilisable ; le seuil de renoncement (1,0 pt, 4/5 graines) a fait **renoncer** à attribuer le secondaire sur PM2,5 |
| bootstrap **apparié** plutôt que barre absolue | adopté sur l'axe temporel ; aucun tirage négatif |
| **stabilité U9/U10** | a produit une réserve que je n'aurais pas trouvée seul (§ 3) |
| clé ADS `pm2.5_anthropogenic_total_carbon` | ⚠️ **n'existe pas** au catalogue ADS. Vérifiée sur `form.json` avant lancement ; la vraie clé est `total_elementary_carbon`. Lancée telle quelle, elle produisait exactement le défaut que vous veniez de signaler — le service sert le reste sans lever |

> La dernière ligne n'est pas un reproche, c'est le mode d'emploi que j'en tire : **vous avez
> eu raison 3/3 sur ce que vous aviez mesuré dans le dépôt, et tort sur ce que vous citiez de
> mémoire.** Ce brief est donc écrit pour vous mettre les données sous les yeux.

---

## 2. 🔴 Le trou principal : quatre chiffres publiés sans intervalle

Ce matin la spéciation CAMS est entrée au dossier. Les chiffres phares ont changé :

| polluant | sans spéciation | **avec** | apport | σ inter-plis du gain | plis où le gain baisse | mois |
|---|---:|---:|---:|---:|---:|---:|
| NO₂ | +38,86 % | **+40,16 %** | **+1,30 pt** | 3,77 | 0/29 | 29 |
| O₃ | +15,83 % | **+18,19 %** | +2,36 pt | 10,84 | 0/29 | 29 |
| PM10 | +17,88 % | **+20,71 %** | +2,84 pt | 10,90 | 1/24 | 24 |
| PM2,5 | +10,03 % | **+12,49 %** | +2,46 pt | 9,25 | 3/29 | 29 |

### Le protocole, en toutes lettres — c'est là que se joue votre réponse

```python
rng = np.random.default_rng(GRAINE)
ids = np.sort(d["station_id"].unique())
groupes = np.array_split(rng.permutation(ids), n_spa)   # n_spa = 3 groupes de stations
plis = []
for i, mm in enumerate(mois_ok):                        # un pli par MOIS du corpus
    dans = d["station_id"].isin(groupes[i % n_spa])     # le groupe tourne, i mod 3
    plis.append((mm,
                 (d["mois"] == mm) & dans,              # TEST  : ce mois × ce groupe
                 (d["mois"] != mm) & ~dans))            # TRAIN : autres mois × autres groupes
```

Points qui me semblent décisifs pour choisir l'estimateur :

- **Il y a 24 à 29 plis, mais seulement 3 groupes de stations.** Le groupe 0 sert de test aux
  mois 0, 3, 6, 9… Deux plis distants de 3 mois **testent exactement les mêmes stations**.
- Chaque pli est **fortement déséquilibré** : le train contient tous les autres mois **et**
  les deux autres tiers des stations, soit ~2/3 × (n−1)/n du corpus.
- La granularité de l'observation est le **jour-station**, pas le pli : chaque pli agrège des
  centaines à des milliers de jours-station.
- Les deux configurations comparées partagent **les mêmes plis, les mêmes lignes, la même
  graine LightGBM** et ne diffèrent que par **16 colonnes** ajoutées.

### 🔴 Ce que la mesure des plis vient de corriger dans ma propre question

Le σ du tableau ci-dessus est la dispersion du **gain**, pas celle de la **différence
appariée**. Je viens d'instrumenter le script pour écrire un CSV par pli, et **les deux
quantités n'ont pas le même ordre de grandeur** :

| | Δ moyen | Δ médian | **σ apparié** | *(σ du gain, pour mémoire)* | plis Δ > 0 | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|
| NO₂ | +1,32 | +1,50 | **1,28** | *3,77* | **26/29** | −1,95 | +3,97 |
| O₃ | +2,17 | +1,21 | **2,76** | *10,84* | **24/29** | −4,84 | +7,10 |
| PM10 | +3,16 | +2,46 | **6,33** | *10,90* | **21/24** | −13,43 | +24,60 |
| PM2,5 | +3,57 | +3,38 | **5,15** | *9,25* | **22/29** | −3,77 | +18,01 |

**Et cela invalide une question que j'allais vous poser.** J'allais vous demander ce que vaut
« 0 pli négatif sur 29 » — mais ce 0/29 portait sur le **gain de la configuration**, pas sur la
différence. La différence appariée est négative sur **3, 5, 3 et 7 plis** respectivement. Le
raisonnement en 2⁻²⁹ n'a jamais eu lieu d'être, et je préfère le dire que de vous laisser
répondre à une question fausse.

**L'erreur-type naïve σ/√n** vaut 0,24 · 0,51 · 1,29 · 0,96 — soit des rapports Δ/erreur de
5,5 · 4,3 · 2,4 · 3,7. **Mais elle suppose les plis indépendants, ce qu'ils ne sont pas**
(rotation `i mod 3` ci-dessus). C'est exactement là que j'ai besoin de vous.

Dernier point : le Δ moyen des plis diffère de l'apport agrégé du premier tableau (NO₂ +1,32
contre +1,30, PM10 +3,16 contre +2,83). L'agrégat met toutes les lignes de test dans un seul
RMSE, la moyenne des plis leur donne un poids égal par mois. **Lequel des deux faut-il
publier ?**

**Ce que je sais déjà, pour que vous ne me le disiez pas :** un bootstrap naïf sur les plis
les traiterait comme indépendants, ce qui est faux ; et le dossier possède déjà un bootstrap
apparié par **blocs mensuels × 20 groupes KMeans de stations**, tirés sur le produit
cartésien — mais il a été construit pour l'axe **temporel**, et je ne sais pas s'il se
transpose à ce protocole-ci.

### Mes questions

1. **Quel estimateur d'incertitude, exactement ?** Rééchantillonner les **mois** ? les
   **3 groupes de stations** (n = 3, dérisoire) ? le **produit** ? Ou descendre au
   jour-station avec un bootstrap par blocs, et lesquels ? Donnez-moi la forme qui tient
   compte de la rotation `i mod 3`.
2. **Que vaut « 26 plis positifs sur 29 » ?** Un test de signe binomial donne p ≈ 5 × 10⁻⁵
   sous H₀, mais il suppose l'indépendance des 29 plis — fausse par la rotation `i mod 3` et
   par le recouvrement des jeux d'apprentissage (deux plis partagent ~93 % de leur train).
   **De combien la dépendance dégrade-t-elle ce raisonnement ?** Y a-t-il un nombre effectif
   de plis indépendants qu'on puisse estimer, ou faut-il abandonner le test de signe ?
   Et sur PM10, **21/24 avec un min à −13,43 pt** : la queue négative est-elle un signal
   (des mois où la spéciation nuit réellement) ou du bruit d'estimation ?
3. **Et le chiffre phare lui-même ?** Je publie **+40,16 %** sans aucun intervalle, et c'est
   vrai depuis le début du projet, pas seulement depuis ce matin. Le gain **total** de la pile
   mérite-t-il un intervalle, ou est-ce que l'intervalle n'a de sens que sur les **écarts**
   entre configurations — le seul objet apparié ?

---

## 3. 🔴 Votre contrôle U9/U10 a produit une réserve, et je ne sais pas la formuler

Exécuté, 8 lots, 5 graines chacun. **Le mécanisme tient partout** : sur les **12** mesures de
la permutation conditionnelle `X` (4 polluants × 3 fenêtres), la part du gain reproduite va de
**−0,0 % à 23,6 %**, jamais près du seuil de 50 % fixé avant lecture.

### Le test décisif, en code — parce que toute la thèse du dossier repose dessus

Si `X` est mal implémenté, la conclusion « le mécanisme est établi » tombe. Voici la
permutation conditionnelle telle qu'elle tourne, et la métrique de lecture :

```python
def permuter_dans_blocs(j, spe, graine):
    """Permute les colonnes de spéciation À L'INTÉRIEUR de chaque (station, mois-calendaire).

    Les lignes gardent leur station, leur mois et leur cible ; seule l'association au JOUR
    est détruite. Les composantes sont permutées ENSEMBLE, d'un seul tirage par bloc : les
    permuter séparément casserait aussi la cohérence entre composantes, et le test ne
    saurait plus laquelle des deux structures il vient de détruire.
    """
    rng = np.random.default_rng(graine)
    mois = pd.to_datetime(j["jour"]).dt.month.to_numpy()
    ordre = np.arange(len(j))
    bloc = pd.Series(ordre).groupby([j["station_id"].to_numpy(), mois])
    for _, positions in bloc.groups.items():
        p = np.asarray(positions)
        ordre[p] = rng.permutation(p)          # tirage neuf par graine ET par bloc
    return pd.DataFrame(j[spe].to_numpy()[ordre], columns=spe, index=j.index)

# La lecture : part du gain de la spéciation que la configuration K reproduit.
# T = socle + forme du total CAMS ; S = socle + forme + spéciation brute.
part(K) = (gain(K) − gain(T)) / (gain(S) − gain(T))
# gain(·) = 100 × (1 − RMSE / RMSE_CAMS_brut), médiane sur 5 graines.
```

**Trois choses que je vous demande de regarder, parce que je ne peux pas les voir moi-même :**

- le bloc est **(station, mois-calendaire)**, pas (station, mois-de-l'année) : janvier 2024 et
  janvier 2025 sont dans le **même** bloc. Est-ce le bon choix ? Il rend le test **plus dur**
  (il préserve moins de structure) mais il mélange deux années ;
- l'ajustement du modèle qui suit la permutation utilise la **même graine LightGBM** que la
  configuration `S`. Faut-il au contraire faire varier les deux indépendamment ?
- `part(X)` peut être **négatif** (−0,0 % sur NO₂, −2,7 % pour `C`, −15,2 % pour `C` sur O₃).
  Un ratio dont le dénominateur est lui-même estimé — est-ce un problème d'interprétation, et
  faut-il publier la différence brute plutôt que la part ?

**Mais l'apport, lui, n'est pas stable :**

| apport S − T (points de %) | PM10 | PM2,5 | O₃ | NO₂ |
|---|---:|---:|---:|---:|
| corpus entier | +9,42 | +5,88 | +4,11 | +2,78 |
| **U9** — 2024-11-13 → 2025-11-12 | +10,09 | +9,75 | +6,12 | +2,53 |
| **U10** — depuis 2025-11-13 | +14,44 | +5,49 | +16,28 | **−0,69** |

Effectifs : U9 retient 37-38 % du corpus (79 752 à 115 475 lignes selon le polluant), U10
28-29 % (60 725 à 85 788). Chaque époque est ensuite coupée en deux moitiés temporelles pour
l'apprentissage et le test.

**Ce que j'ai écrit dans le dossier**, et dont je veux savoir si c'est défendable :

> L'étage de spéciation reste dans la pile, parce qu'il est mesuré positivement au protocole
> du dossier sur le corpus entier. Mais **son apport ne doit pas être cité pour le NO₂** :
> sur ce polluant, il n'est pas établi qu'il se reproduise.

**Mes questions :**

1. **Est-ce défendable, ou est-ce un compromis bâtard ?** Garder un étage dont on refuse de
   citer l'apport ressemble à un aveu. L'alternative — retirer la spéciation **pour le NO₂
   seul** — donne un modèle dont la liste de variables dépend du polluant, plus difficile à
   défendre, et coûte 1,30 pt sur le chiffre le plus visible du dossier.

   **Un fait qui pèse sur cette question, et que j'ai mesuré en écrivant ce brief.** L'apport
   réel de chaque étage (MAXIMALE − son ablation, donc hors effet d'ordre) est :

   | apport, points de % | typologie | membres | feux | GEOS-CF | tendance | **spéciation** |
   |---|---:|---:|---:|---:|---:|---:|
   | NO₂ | **+9,73** | +0,22 | +0,18 | +1,23 | +0,19 | +1,30 |
   | O₃ | +0,31 | +0,77 | **−0,14** | +0,98 | +0,42 | **+2,36** |
   | PM10 | +2,61 | +0,61 | +0,66 | +1,04 | +0,44 | **+2,83** |
   | PM2,5 | +0,15 | +0,70 | **−0,28** | +0,69 | **−0,18** | **+2,46** |

   Deux lectures en découlent :

   - **la spéciation est le plus gros apport sur trois polluants sur quatre**, mesurée à la
     position la plus dure de la pile ;
   - **le dossier conserve DÉJÀ des étages d'apport négatif sur certains polluants** — les
     feux sur O₃ et PM2,5, la tendance sur PM2,5 — au nom de l'uniformité du modèle. Ma
     posture sur le NO₂ n'est donc pas une exception inventée pour l'occasion : c'est la
     règle en vigueur. **Est-ce que cela la sauve, ou est-ce que cela révèle que la règle
     elle-même est mauvaise et qu'il faudrait élaguer par polluant ?**
2. **Deux sous-corpus de 28-38 % suffisent-ils à déclarer une instabilité ?** L'apport NO₂
   est le plus petit des quatre. Un −0,69 pt sur un tiers du corpus est-il une instabilité ou
   du bruit d'estimation sur-interprété ? Comment trancher **sans** ajouter un troisième
   découpage post-hoc, ce qui serait du criblage ?
3. **Le NO₂ a un mécanisme connu qui pourrait expliquer sa singularité**, et je ne sais pas
   si c'est une explication ou une rationalisation : sur ce polluant, le dossier a établi que
   le résidu est attaché **au site** et non à la dynamique — la typologie de station y rend
   +8,5 à +8,9 pts en spatial et **rien** en temporel, et la tendance récente de CAMS y est le
   seul étage perdant des quatre. Un polluant dont l'erreur est presque entièrement un effet
   de site aurait peu à gagner d'une information de **composition du jour**. **Est-ce
   testable, ou est-ce une histoire qui arrive après le résultat ?**
4. ⚠️ **Une réserve sur vos dates de version, que je n'ai pas pu lever.** J'ai tenté de les
   vérifier dans nos propres données : le saut normalisé des composantes à la date annoncée
   (|z| médian **0,38** au 2025-11-13) est **indiscernable** de celui d'une date témoin
   arbitraire (**0,37** au 2025-03-15) — à mi-novembre, une fenêtre de 45 jours compare
   octobre à décembre, et le cycle saisonnier écrase tout pas de version. Inconclusif : ni
   confirmation ni réfutation. **Existe-t-il un test qui sépare un pas de version d'un cycle
   saisonnier sur ces données ?** J'ai pensé à comparer les mêmes dates calendaires d'une
   année sur l'autre, mais c'est confondu par la météo de l'année.

---

## 4. Un renversement mesuré, et une explication qui me paraît trop commode

Le mécanisme dit que seule l'**anomalie journalière** de composition porte l'information.
J'en ai tiré une piste : remplacer chaque composante par son écart à la climatologie
station × mois.

| | axe **temporel** *(mêmes stations des deux côtés)* | **double aveugle** *(station ET mois cachés)* |
|---|---|---|
| O₃ | +8,94 → **+10,06 %** *(+1,12 pt)* | +18,19 → **+17,14 %** *(−1,04 pt)* |
| PM2,5 | +11,55 → **+12,18 %** *(+0,63)* | +12,49 → **+11,64 %** *(−0,85)* |
| PM10 | — | +20,71 → **+20,01 %** *(−0,70)* |
| NO₂ | — | +40,16 → **+39,66 %** *(−0,50)* |

**Le signe s'inverse, 4/4.** Mon explication : sur l'axe temporel les stations sont les mêmes
des deux côtés, donc le modèle connaît déjà chaque site et le **niveau** de composition y est
redondant ; en double aveugle la station est inconnue, et ce niveau est justement ce qui dit
*quel type de lieu c'est*.

**Mes questions :**

1. **Cette explication est-elle testable, ou est-ce une histoire ?** Elle est plausible et
   elle arrive **après** le résultat — exactement la position où ce projet s'est déjà trompé
   deux fois.
2. **Le test que j'ai en tête, et son seuil.** Si mon explication est juste, donner au modèle
   **la climatologie ET l'anomalie séparément** devrait égaler ou battre la valeur brute en
   double aveugle : l'information est la même, mieux séparée. Si elle est fausse, ça ne
   changera rien ou dégradera. Est-ce le bon test ? Quel seuil fixer avant de le lancer, et
   **qu'est-ce que je conclus si le résultat est « ni l'un ni l'autre » — égalité stricte ?**
3. **Un défaut traversé pour arriver là, au cas où il vous suggère un garde plus général.**
   J'avais d'abord ajusté la climatologie sur le **pli d'apprentissage** — le geste correct
   partout ailleurs. Faux ici : le protocole cache la station, donc **les stations de test en
   sont absentes par construction** ; leur climatologie n'existait pas, chaque ligne repliait
   sur la moyenne globale, et le modèle apprenait sur des anomalies centrées pour prédire sur
   des valeurs brutes décalées d'une constante. **Deux échelles de part et d'autre du modèle,
   aucune exception levée, un CSV d'allure parfaitement normale.** C'est devenu une règle
   mécanisée du dépôt. **Y a-t-il d'autres transformations d'un pipeline de ce type exposées
   au même défaut ?** Je pense aux encodages de cible, aux normalisations par groupe, aux
   moyennes glissantes par station — mais je préfère votre liste à la mienne.

---

## 5. Deux questions que je n'avais pas posées, et qui me semblent plus graves

### 5.1 La multiplicité — combien de tests ai-je réellement faits ?

Ce dépôt compte **483 rapports CSV** et a mesuré une trentaine de leviers. Rien que sur la
spéciation, cette semaine : 5 configurations × 4 polluants × 3 fenêtres (60 ajustements de
décision), plus 8 sous-ensembles × 5 graines de Shapley sur 2 polluants, plus 5 ablations une
à une, plus les contrôles `T`, `P`, et la variante anomalie sur 4 polluants.

Les seuils ont été **fixés avant lecture** dans chaque cas, et je le documente. Mais fixer un
seuil avant lecture ne protège pas de la multiplicité : c'est une garantie **par test**, pas
**par famille**.

**Mes questions :**

1. **Quelle correction de multiplicité s'applique ici, et sur quelle famille ?** Corriger sur
   les 60 tests de la semaine ? Sur les 483 rapports ? Aucune des deux ne me paraît juste : la
   première est arbitraire, la seconde punirait tout travail exploratoire.
2. **La conclusion « le mécanisme est établi » survit-elle à une correction ?** Elle repose
   sur 12 mesures de `X` toutes du même côté d'un seuil, ce qui est robuste par construction —
   mais je veux le savoir plutôt que le croire.
3. **Et le biais de criblage sur les GAINS ?** Le dossier a déjà mesuré que balayer des
   variables inexploitées produit un biais de sélection de **×2 à ×4** sur le gain apparent
   d'un levier retenu. Les six familles de la pile ont été **sélectionnées parmi une
   trentaine mesurées** : ce sont celles qui ont gagné. **Le total de +40,16 % est-il inflaté
   par cette sélection, et de combien ?** C'est peut-être la question la plus importante de ce
   brief, et je ne l'avais jamais posée.

### 5.2 L'ordre de la pile — l'apport marginal est-il le bon objet à publier ?

Les six familles sont empilées **dans un ordre déclaré avant la mesure**, et chaque étage
rapporte son apport marginal *une fois les précédents en place*. La spéciation est placée
**en dernier** — la position la plus dure, celle où elle n'hérite que de ce que les cinq
autres n'ont pas pris.

Conséquence : **son apport publié (+1,30 à +2,84 pt) est un minorant par construction**, et
l'apport de chaque étage dépend de sa place. Le premier étage capte tout ce qu'il partage avec
les suivants.

**Mes questions :**

1. **Faut-il publier un Shapley sur les six étages** plutôt que des marginaux cumulatifs ?
   64 sous-ensembles × 24-29 plis × 4 polluants — le coût est-il justifié par ce que ça change
   dans la lecture ?
2. Si non, **quelle est la formulation honnête d'un marginal en dernière position** ? Aujourd'hui
   j'écris « ce que la famille ajoute à une pile déjà complète », mais un lecteur pressé lit
   « ce que la famille vaut ».
3. **Est-ce que l'ordre déclaré avant mesure suffit** à me protéger du reproche d'avoir choisi
   l'ordre qui arrange ? Je peux prouver la déclaration (elle est en commentaire dans le code,
   versionnée), mais pas l'absence d'intention.

---

## 6. L'arbitrage final — et l'option « ne rien mesurer de plus »

| chantier | état |
|---|---|
| spéciation au protocole du dossier | **mesurée, publiée, sans intervalle** (§ 2) |
| mécanisme de la spéciation | **établi et robuste**, 12/12 |
| stabilité par époque | **faite** — réserve sur NO₂ (§ 3) |
| anomalie de composition | **réfutée** en double aveugle, 4/4 (§ 4) |
| attribution par groupes (Shapley) | faite sur PM10 et PM2,5 ; **O₃ et NO₂ non passés** |
| RealMLP | mesuré, non bootstrappé, non intégré |
| multiplicité et biais de criblage | **jamais traités** (§ 5.1) |
| démo interactive | 6 défauts corrigés ce matin, dont un **verdict inversé** |

**Ma question, et c'est la vraie :** avec cinq jours, un dossier cohérent et un mécanisme
établi, **la bonne décision n'est-elle pas d'arrêter de mesurer ?**

Chaque nouvelle mesure peut ouvrir une réserve — celle de la § 3 est arrivée exactement comme
ça, et celle de la § 5.1 pourrait affaiblir le chiffre phare. Un dossier qui gagne un point et
perd une certitude est-il meilleur ? Je penche pour « non », mais je suis juge et partie :
c'est mon travail que je jugerais.

**Si vous pensez qu'il faut encore mesurer, dites-moi LA seule chose à faire, et ce qu'elle
remplace.** Si vous pensez qu'il faut s'arrêter, dites-le aussi clairement — c'est une réponse
utile, et personne d'autre ne peut me la donner.

---

## 7. Contraintes matérielles, à intégrer dans vos estimations de coût

- **Corruption mémoire matérielle avérée.** i9-13900KF (Raptor Lake, microcode 0x12B déjà
  appliqué), **4 DIMM issus de deux kits différents** — configuration hors spécification.
  Signature : des valeurs qui atterrissent dans le mauvais emplacement d'argument.
  `TypeError: 'UTC' object cannot be interpreted as an integer` le 08/08, et **ce matin**
  `SystemError: more argument specifiers than keyword list entries` — **au même site**
  (`pandas/_libs/tslibs/vectorized.pyx → ints_to_pydatetime`). Environ **un échec sur deux**
  sur les gros chargements. Vérifié : quand un calcul aboutit, il rend **le même chiffre à la
  décimale** — les pannes sont bruyantes, pas silencieuses.
  → **Tout lot doit être reprenable** ; un lot qui repart de zéro n'aboutit jamais.
- **32 cœurs, RTX 5090 (34 Go), 68 Go de RAM.** LightGBM borné à `n_jobs=4` : trois
  ajustements en `n_jobs=-1` s'effondrent d'un **ordre de grandeur** — la contention porte sur
  la bande passante mémoire, pas sur les cœurs. On fait donc tourner 4 voies × 4 fils.
- Un lot `methode_maximale` complet coûte **35 à 40 min** par polluant, soit ~40 min sur
  4 voies. Un lot `mecanisme_speciation` (7 configurations × 5 graines) coûte **13 min**.

---

## 8. Les données brutes — différences appariées, pli par pli

Un pli = un **mois** × un **tiers des stations**, ces stations étant absentes de l'apprentissage de ce pli. `Δ gain` = `gain(pile complète) − gain(pile sans la spéciation)`, les deux configurations partageant exactement les mêmes lignes, la même graine et le même découpage.

⚠️ **Rappel du protocole, décisif pour l'estimateur :** les stations sont réparties en **3 groupes** et le groupe de test tourne (`i mod 3`). Deux plis distants de 3 mois testent donc **exactement les mêmes stations**.

### NO2 — 29 plis · différence appariée `gain(avec) − gain(sans)`, en points

| mois | n_test | stations | RMSE CAMS | RMSE sans | RMSE avec | **Δ gain (pt)** |
|---|---:|---:|---:|---:|---:|---:|
| 2023-08 | 3,168 | 111 | 20.504 | 14.351 | 14.751 | **-1.95** |
| 2023-09 | 3,218 | 111 | 27.831 | 16.442 | 16.781 | **-1.22** |
| 2023-10 | 3,368 | 112 | 28.124 | 16.954 | 16.383 | **+2.03** |
| 2023-11 | 3,142 | 109 | 25.502 | 16.136 | 15.700 | **+1.71** |
| 2023-12 | 3,329 | 111 | 23.728 | 13.601 | 13.596 | **+0.02** |
| 2024-01 | 3,430 | 112 | 24.325 | 14.520 | 14.477 | **+0.17** |
| 2024-02 | 3,164 | 111 | 25.459 | 15.594 | 15.212 | **+1.50** |
| 2024-03 | 3,376 | 110 | 24.302 | 13.491 | 13.362 | **+0.53** |
| 2024-04 | 3,137 | 108 | 22.608 | 12.107 | 12.157 | **-0.22** |
| 2024-05 | 3,285 | 109 | 21.244 | 13.466 | 13.029 | **+2.06** |
| 2024-06 | 3,176 | 109 | 18.262 | 11.618 | 11.537 | **+0.45** |
| 2024-07 | 3,246 | 107 | 18.211 | 10.558 | 10.353 | **+1.13** |
| 2024-08 | 3,312 | 110 | 20.607 | 13.971 | 13.666 | **+1.48** |
| 2024-09 | 3,230 | 110 | 20.115 | 11.965 | 11.572 | **+1.95** |
| 2024-10 | 3,205 | 107 | 20.038 | 11.543 | 11.314 | **+1.14** |
| 2024-11 | 3,164 | 110 | 22.533 | 14.573 | 13.679 | **+3.97** |
| 2024-12 | 3,325 | 111 | 22.093 | 14.664 | 13.795 | **+3.93** |
| 2025-01 | 3,295 | 110 | 23.060 | 13.881 | 13.448 | **+1.88** |
| 2025-02 | 2,944 | 107 | 25.302 | 16.057 | 15.697 | **+1.42** |
| 2025-03 | 3,416 | 112 | 26.689 | 16.104 | 15.689 | **+1.55** |
| 2025-04 | 3,074 | 105 | 23.214 | 12.790 | 12.648 | **+0.61** |
| 2025-05 | 3,220 | 107 | 22.088 | 13.985 | 13.504 | **+2.18** |
| 2025-06 | 3,225 | 111 | 21.633 | 13.557 | 13.478 | **+0.36** |
| 2025-07 | 3,117 | 105 | 17.873 | 10.581 | 10.235 | **+1.94** |
| 2025-08 | 3,225 | 107 | 24.116 | 15.686 | 15.298 | **+1.61** |
| 2025-09 | 3,271 | 112 | 19.060 | 12.064 | 11.672 | **+2.06** |
| 2025-10 | 3,155 | 104 | 20.162 | 11.255 | 10.955 | **+1.49** |
| 2025-11 | 3,100 | 106 | 25.528 | 15.195 | 14.794 | **+1.57** |
| 2025-12 | 3,357 | 112 | 21.991 | 14.166 | 13.528 | **+2.90** |

**26/29 plis positifs** · médiane **+1.50** · moyenne **+1.32** · écart-type **1.28** · min **-1.95** · max **+3.97** · erreur-type naïve (σ/√n) **0.24**

### O3 — 29 plis · différence appariée `gain(avec) − gain(sans)`, en points

| mois | n_test | stations | RMSE CAMS | RMSE sans | RMSE avec | **Δ gain (pt)** |
|---|---:|---:|---:|---:|---:|---:|
| 2023-08 | 2,579 | 89 | 11.380 | 9.979 | 10.529 | **-4.84** |
| 2023-09 | 2,563 | 88 | 10.809 | 10.797 | 10.667 | **+1.21** |
| 2023-10 | 2,659 | 88 | 11.129 | 10.064 | 9.702 | **+3.26** |
| 2023-11 | 2,675 | 90 | 10.514 | 10.383 | 10.387 | **-0.04** |
| 2023-12 | 2,684 | 88 | 11.018 | 10.010 | 9.765 | **+2.22** |
| 2024-01 | 2,774 | 90 | 13.205 | 11.008 | 10.151 | **+6.49** |
| 2024-02 | 2,504 | 88 | 11.116 | 10.795 | 10.006 | **+7.10** |
| 2024-03 | 2,687 | 89 | 7.882 | 8.015 | 7.775 | **+3.04** |
| 2024-04 | 2,655 | 90 | 9.100 | 8.083 | 8.025 | **+0.64** |
| 2024-05 | 2,684 | 87 | 9.741 | 9.143 | 8.832 | **+3.20** |
| 2024-06 | 2,530 | 87 | 10.146 | 9.844 | 9.726 | **+1.16** |
| 2024-07 | 2,745 | 90 | 11.239 | 10.120 | 10.055 | **+0.58** |
| 2024-08 | 2,621 | 86 | 11.755 | 9.917 | 9.777 | **+1.19** |
| 2024-09 | 2,624 | 89 | 9.811 | 9.669 | 9.584 | **+0.86** |
| 2024-10 | 2,736 | 90 | 15.518 | 10.576 | 10.438 | **+0.89** |
| 2024-11 | 2,554 | 87 | 18.270 | 11.398 | 10.406 | **+5.43** |
| 2024-12 | 2,673 | 89 | 13.857 | 10.481 | 9.932 | **+3.96** |
| 2025-01 | 2,556 | 86 | 14.687 | 12.288 | 11.806 | **+3.28** |
| 2025-02 | 2,252 | 84 | 15.132 | 11.303 | 10.716 | **+3.88** |
| 2025-03 | 2,490 | 82 | 9.099 | 8.764 | 8.997 | **-2.56** |
| 2025-04 | 2,453 | 84 | 10.300 | 9.094 | 9.130 | **-0.35** |
| 2025-05 | 2,483 | 82 | 11.793 | 10.193 | 10.097 | **+0.81** |
| 2025-06 | 2,370 | 84 | 15.822 | 13.162 | 13.247 | **-0.54** |
| 2025-07 | 2,625 | 87 | 12.713 | 11.400 | 11.254 | **+1.15** |
| 2025-08 | 2,659 | 87 | 12.908 | 10.995 | 10.978 | **+0.13** |
| 2025-09 | 2,466 | 85 | 10.698 | 8.396 | 8.011 | **+3.60** |
| 2025-10 | 2,638 | 87 | 14.793 | 10.498 | 9.580 | **+6.21** |
| 2025-11 | 2,534 | 87 | 12.676 | 10.201 | 9.427 | **+6.11** |
| 2025-12 | 2,599 | 85 | 13.086 | 11.577 | 10.926 | **+4.97** |

**24/29 plis positifs** · médiane **+1.21** · moyenne **+2.17** · écart-type **2.76** · min **-4.84** · max **+7.10** · erreur-type naïve (σ/√n) **0.51**

### PM10 — 24 plis · différence appariée `gain(avec) − gain(sans)`, en points

| mois | n_test | stations | RMSE CAMS | RMSE sans | RMSE avec | **Δ gain (pt)** |
|---|---:|---:|---:|---:|---:|---:|
| 2024-01 | 3,173 | 105 | 8.479 | 7.313 | 7.279 | **+0.40** |
| 2024-02 | 2,770 | 100 | 7.168 | 6.430 | 6.293 | **+1.91** |
| 2024-03 | 2,997 | 101 | 12.271 | 11.948 | 11.332 | **+5.02** |
| 2024-04 | 3,009 | 105 | 5.231 | 5.927 | 4.640 | **+24.60** |
| 2024-05 | 2,959 | 100 | 4.601 | 3.973 | 3.710 | **+5.71** |
| 2024-06 | 2,802 | 96 | 6.984 | 5.218 | 4.798 | **+6.01** |
| 2024-07 | 3,045 | 103 | 6.336 | 4.136 | 3.997 | **+2.19** |
| 2024-08 | 2,968 | 99 | 5.578 | 4.048 | 4.008 | **+0.72** |
| 2024-09 | 2,817 | 98 | 6.864 | 5.781 | 5.657 | **+1.81** |
| 2024-10 | 3,080 | 103 | 5.532 | 4.546 | 4.231 | **+5.68** |
| 2024-11 | 2,853 | 100 | 9.232 | 6.494 | 6.392 | **+1.10** |
| 2024-12 | 2,926 | 102 | 8.524 | 6.933 | 6.815 | **+1.38** |
| 2025-01 | 3,079 | 104 | 8.669 | 7.624 | 7.362 | **+3.02** |
| 2025-02 | 2,725 | 101 | 8.156 | 6.622 | 6.399 | **+2.73** |
| 2025-03 | 3,067 | 104 | 6.977 | 6.159 | 5.508 | **+9.32** |
| 2025-04 | 2,954 | 102 | 6.114 | 5.736 | 6.558 | **-13.43** |
| 2025-05 | 3,047 | 102 | 6.587 | 4.378 | 4.179 | **+3.03** |
| 2025-06 | 2,966 | 103 | 9.463 | 5.696 | 5.853 | **-1.66** |
| 2025-07 | 3,011 | 101 | 6.369 | 4.330 | 4.123 | **+3.25** |
| 2025-08 | 3,024 | 101 | 7.201 | 5.428 | 4.748 | **+9.45** |
| 2025-09 | 2,908 | 102 | 4.887 | 3.216 | 3.178 | **+0.79** |
| 2025-10 | 3,021 | 102 | 4.989 | 4.080 | 3.985 | **+1.92** |
| 2025-11 | 2,956 | 102 | 9.535 | 7.861 | 7.582 | **+2.92** |
| 2025-12 | 3,064 | 101 | 8.034 | 6.664 | 6.837 | **-2.14** |

**21/24 plis positifs** · médiane **+2.46** · moyenne **+3.16** · écart-type **6.33** · min **-13.43** · max **+24.60** · erreur-type naïve (σ/√n) **1.29**

### PM25 — 29 plis · différence appariée `gain(avec) − gain(sans)`, en points

| mois | n_test | stations | RMSE CAMS | RMSE sans | RMSE avec | **Δ gain (pt)** |
|---|---:|---:|---:|---:|---:|---:|
| 2023-08 | 2,043 | 73 | 2.457 | 2.161 | 2.026 | **+5.49** |
| 2023-09 | 2,082 | 72 | 2.975 | 2.500 | 2.325 | **+5.86** |
| 2023-10 | 2,098 | 70 | 3.595 | 2.910 | 3.032 | **-3.40** |
| 2023-11 | 2,089 | 75 | 4.173 | 4.150 | 3.953 | **+4.73** |
| 2023-12 | 2,215 | 74 | 5.149 | 4.587 | 4.559 | **+0.54** |
| 2024-01 | 2,155 | 73 | 7.041 | 6.368 | 6.435 | **-0.95** |
| 2024-02 | 2,126 | 76 | 4.192 | 4.215 | 3.959 | **+6.11** |
| 2024-03 | 2,213 | 75 | 4.892 | 4.629 | 4.359 | **+5.52** |
| 2024-04 | 2,069 | 71 | 2.769 | 2.411 | 2.274 | **+4.95** |
| 2024-05 | 2,253 | 76 | 2.055 | 2.158 | 1.903 | **+12.40** |
| 2024-06 | 2,149 | 74 | 2.570 | 3.081 | 2.683 | **+15.46** |
| 2024-07 | 2,043 | 69 | 2.409 | 2.247 | 2.203 | **+1.83** |
| 2024-08 | 2,219 | 75 | 2.492 | 2.226 | 2.230 | **-0.17** |
| 2024-09 | 2,147 | 74 | 3.011 | 3.069 | 2.967 | **+3.38** |
| 2024-10 | 2,155 | 71 | 3.272 | 2.550 | 2.543 | **+0.22** |
| 2024-11 | 2,144 | 75 | 7.208 | 4.699 | 4.745 | **-0.63** |
| 2024-12 | 2,230 | 76 | 6.317 | 5.316 | 5.174 | **+2.26** |
| 2025-01 | 2,222 | 76 | 6.714 | 5.851 | 5.583 | **+3.99** |
| 2025-02 | 2,128 | 78 | 5.869 | 5.578 | 5.378 | **+3.42** |
| 2025-03 | 2,289 | 76 | 4.200 | 4.616 | 4.479 | **+3.26** |
| 2025-04 | 2,139 | 74 | 3.399 | 3.483 | 3.611 | **-3.77** |
| 2025-05 | 2,316 | 77 | 2.344 | 2.282 | 2.072 | **+8.93** |
| 2025-06 | 2,132 | 75 | 4.959 | 4.476 | 4.639 | **-3.29** |
| 2025-07 | 2,195 | 74 | 2.295 | 2.122 | 2.041 | **+3.53** |
| 2025-08 | 2,296 | 77 | 2.569 | 2.621 | 2.158 | **+18.01** |
| 2025-09 | 2,226 | 76 | 2.113 | 1.706 | 1.691 | **+0.74** |
| 2025-10 | 2,219 | 74 | 3.250 | 2.429 | 2.407 | **+0.70** |
| 2025-11 | 2,252 | 77 | 4.325 | 3.471 | 3.501 | **-0.68** |
| 2025-12 | 2,288 | 76 | 4.833 | 4.953 | 4.700 | **+5.24** |

**22/29 plis positifs** · médiane **+3.38** · moyenne **+3.57** · écart-type **5.15** · min **-3.77** · max **+18.01** · erreur-type naïve (σ/√n) **0.96**


**C'est la matière de la § 2.** Avec elle vous pouvez conclure vous-même plutôt que m'indiquer une méthode — et c'est ce qui me servirait le plus.

---

## 9. Réponse attendue

Un fichier **`.md`**, une section par numéro ci-dessus. Et si une seule de ces neuf sections
mérite votre temps, dites-moi laquelle et traitez-la à fond plutôt que les neuf à moitié.
