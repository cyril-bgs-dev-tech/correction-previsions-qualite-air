# Cinquième revue — la passe `core7` a tourné, et une décision de corpus reste ouverte

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> **Ce brief est court et il ne pose que trois décisions.** Vos dix recommandations
> précédentes sont exécutées ou tranchées ; je ne vous redemande rien de ce que vous avez
> déjà traité. Pour chaque décision : **ce que vous feriez**, **le seuil**, **ce qu'on écrit
> dans les deux issues**.
>
> ⏱️ **4 jours.** Vous aviez recommandé « une passe, un intervalle, puis gel ». La passe a
> tourné. Ce qui suit sont les questions qu'elle a ouvertes, plus une décision que le porteur
> du projet a prise **contre** votre recommandation, et que j'assume de vous soumettre telle
> quelle.

---

## 0. Ce que votre revue 4 a produit, en deux lignes

**Votre trouvaille principale était juste et je l'ai reproduite.** Sur les cinq plis de 2023
où la spéciation n'existe pas, l'ajout du bloc produisait une différence non nulle — jusqu'à
**+2,64 pt de moyenne sur PM2,5**. Le modèle lisait le motif d'absence comme un indicateur
d'année, et le protocole cache les mois. C'était le défaut que le script documente lui-même
pour GEOS-CF, réintroduit par une autre porte.

**Votre seconde trouvaille était juste aussi, et elle nous flattait.** `horizon=2` couvre les
heures 25-48 : c'est **J+1**, et le dossier publiait **J+2** sept fois. Vérifié dans les
données — `horizon=1` démarre le 2023-08-01, `horizon=2` le 2023-08-02. Corrigé, **et
mécanisé** : `aq.rapport.libelle_echeance()` dérive `J+(horizon−1)` et refuse une entrée
invalide, parce que ce défaut s'était déjà produit une première fois et avait été déclaré
corrigé.

> Une vérification que j'ai faite avant de vous écrire : **les comparaisons externes, elles,
> étaient déjà correctement libellées** (`duel_prevair.py` porte `--horizon 2, help="2 = J+1"`).
> Le libellé faux était confiné à `methode_maximale`. Aucune comparaison n'était donc
> mésappariée — seulement mal nommée, et le dossier se contredisait lui-même sans que
> personne ne le voie.

---

## 1. 🔴 Décision A — quelle table publier, maintenant que j'en ai deux

La passe `core7` a tourné selon votre spécification : **2024-01 → 2025-12**, 14 colonnes,
nitrate exclu, **zéro valeur manquante** (le garde a d'abord refusé — il restait 211 à 331
lignes du **2024-01-01**, la spéciation commençant le 2 janvier ; elles sont retirées pour les
deux configurations à l'identique, et le retrait est compté).

| | corpus **publié** (29 mois, `left join`) | corpus **`core7`** (24 mois, support commun) |
|---|---|---|
| | sans spé → avec spé (apport) | sans spé → avec spé (apport) |
| **NO₂** | +38,86 → **+40,16** (+1,30) | +39,46 → **+40,72** (**+1,26**) |
| **O₃** | +15,83 → **+18,19** (+2,36) | +9,07 → **+15,41** (**+6,34**) |
| **PM10** | +17,88 → **+20,71** (+2,84) | +18,12 → **+20,44** (**+2,32**) |
| **PM2,5** | +10,03 → **+12,49** (+2,46) | +10,40 → **+12,89** (**+2,49**) |

Différences appariées par pli, sur le support commun :

| | Δ moyen | σ apparié | plis Δ>0 | σ/√n |
|---|---:|---:|---:|---:|
| NO₂ | +1,20 | **1,00** | 22/24 | 0,20 |
| O₃ | +4,41 | 8,37 | 19/24 | 1,71 |
| PM10 | +2,76 | 6,00 | 19/24 | 1,22 |
| PM2,5 | +3,63 | 4,04 | 21/24 | 0,83 |

**Ce que je lis, et je voudrais votre contrôle :**

- **l'apport survit sur les quatre** — la contamination ne l'avait pas créé, elle en déformait
  la valeur ;
- **NO₂ est remarquablement stable** (+1,30 → +1,26, σ apparié 1,00, 22/24) — ce qui affaiblit
  encore l'idée de l'élaguer ;
- **O₃ TRIPLE son apport** (+2,36 → +6,34) pendant que sa base s'effondre (+15,83 → +9,07).

### 🔴 Et c'est ce dernier point qui m'inquiète le plus, plus que le choix de table

J'allais vous écrire que le chiffre publié est sensible à la fenêtre. **J'ai mesuré les
quatre avant de le dire, et c'est faux en général — c'est vrai de l'ozone seul :**

| même configuration, 29 mois → 24 mois | O₃ | NO₂ | PM10 | PM2,5 |
|---|---:|---:|---:|---:|
| écart | **−6,76 pt** | +0,60 | +0,25 | +0,37 |

Trois polluants tiennent à **0,6 point près** quand on retire 17 % du corpus. **L'ozone
bouge de sept points.** Ce n'est donc pas un problème de précision générale : c'est une
anomalie propre à un polluant, et le dossier ne l'a jamais ni mesurée ni annoncée.

Les cinq mois retirés sont **août à décembre 2023**, dont un mois d'été. Le gain ozone se
concentre en été — le dossier a déjà mesuré que la moyenne annuelle sur O₃ masque un
**changement de signe** entre saisons.

**Mes questions :**

1. **Est-ce de la composition saisonnière, ou l'instabilité du gain lui-même ?** Retirer un
   août d'un corpus de 29 mois où le gain se concentre en été suffit-il à expliquer 6,76 pt,
   ou faut-il chercher autre chose ? Un test simple existe-t-il pour trancher — par exemple
   comparer les gains mensuels des cinq mois retirés à la médiane des autres ?
2. **Que publie-t-on pour l'ozone ?** Si son chiffre dépend à ce point de la fenêtre, un point
   unique est trompeur, quelle que soit la fenêtre choisie. Faut-il une **plage** issue d'un
   rééchantillonnage des mois, une **valeur par saison**, ou une réserve explicite ?
3. **Et combien de décimales sont défendables ?** Nous écrivons `+18,19 %`. Sur O₃, la
   deuxième décimale ne soutient manifestement rien. Existe-t-il une règle simple — arrondir
   à la précision de l'intervalle — que je puisse appliquer partout d'un coup, plutôt qu'au
   jugé chiffre par chiffre ?

**Ma question :** votre recommandation 0 disait de **remplacer** la table publiée par celle-ci.
Mais elle est sur **24 mois au lieu de 29**, donc le dossier perdrait 17 % de son corpus et
verrait son chiffre ozone passer de **+18,19 % à +15,41 %**. Trois options :

1. **remplacer** — un seul tableau, support propre, corpus plus court, et le chiffre ozone
   baisse ;
2. **publier les deux** — la table longue comme mesure principale avec la réserve de support,
   la table `core7` comme confirmation ;
3. **remplacer, et publier l'ancienne en sensibilité** — l'inverse de (2).

Je penche pour (1), parce qu'une réserve ne remplace pas une mesure juste et que ce projet a
déjà été repris là-dessus. Mais (1) affiche un chiffre plus bas sur un corpus plus court à
quatre jours de la remise, et je veux votre avis avant de le faire.

---

## 2. 🔴 Décision B — un balayage d'échéances J0 → J+3, décidé contre votre recommandation

Vous aviez écrit : *ne lancer ni RealMLP, ni `C+A`, ni Shapley à six étages, ni test de rupture
avant la remise.* **Le porteur du projet a décidé d'ajouter un balayage d'échéances**, et je
vous le soumets tel quel plutôt que de le présenter comme une idée à valider.

**Le but déclaré :** le dossier affirme que **nos leviers ne se dégradent pas avec l'échéance**
— moins d'un point entre J0, J+1 et J+2 — parce que le biais corrigé est une propriété du
**site**. C'est une prédiction, et J+3 est la seule échéance où elle peut encore être réfutée.

**Les données J+3 sont disponibles**, et gratuitement : elles étaient déjà sur le disque
(4 384 fichiers, échéances 73-96 h, couverture complète de la fenêtre d'évaluation — les
seuls jours manquants sont antérieurs au début du corpus ou postérieurs à sa fin). C'est la
dernière tranche possible : CAMS Europe régional s'arrête à 96 h, il n'existe ni J+4 ni J+5.

> ⚠️ **Je les ai retéléchargées avant de m'en apercevoir** — 63 minutes de réseau et 6,6 Go
> pour rien. La cause est instructive et je la donne parce qu'elle a valeur générale : pour
> savoir jusqu'où allait le corpus, j'ai ouvert **un seul fichier** (`f[0]` d'un `glob`), lu
> ses échéances `0 → 72`, et conclu. Or le tri plaçait les fichiers `ENS_FORECAST_J3_*` après
> les `ENS_FORECAST_2023-*` — `'2' < 'J'`. **J'ai généralisé un inventaire depuis un
> échantillon de taille un.** Le contrôle juste tenait en une ligne : compter les échéances
> *sur tout le corpus*, ce qui rend `{'J0-J2': 4715, 'J3': 4384}`.

### 🔴 Le vrai obstacle du balayage : la pile n'existe pas aux mêmes échéances

| famille | échéances disponibles | horizons couverts |
|---|---|---|
| CAMS totaux (4 espèces) | 0-96 h | J0, J+1, J+2, **J+3** ✅ |
| **spéciation (7 traceurs)** | **25-48 h uniquement** | **J+1 seulement** 🔴 |
| membres d'ensemble | à vérifier | — |
| GEOS-CF | à vérifier | — |

**La « pile complète » n'existe donc qu'à J+1.** Un balayage sur quatre horizons comparerait
des piles différentes, et l'effet d'échéance serait confondu avec la composition du modèle.

Compléter la spéciation coûte : une tranche = **89 % du plafond ADS, 32 requêtes, ~69 min,
8 Go**. Trois tranches manquantes = **~3,5 h et 24 Go**. C'est le seul coût restant, et c'est
le dernier arbitrage de ressource avant la remise.

**Mes questions :**

1. **Un balayage à pile RÉDUITE mais FIXE est-il publiable ?** Tenir la même pile restreinte
   aux quatre horizons donne une comparaison propre — elle ne répond simplement pas à « notre
   meilleure méthode se dégrade-t-elle », mais à « cette pile-ci se dégrade-t-elle ». Est-ce
   une réponse utile, ou une réponse à côté ?
2. **Ou faut-il payer les 3,5 h de téléchargement** pour un balayage à pile complète ? À
   quatre jours de la remise, c'est le dernier arbitrage de ressource.
3. **Comment pré-enregistrer la prédiction ?** Le dossier affirme « moins d'un point d'écart
   entre horizons ». Quel seuil fixer **avant de regarder** pour que le résultat soit
   publiable dans les deux sens — et sur quelle grandeur, l'apport de la correction ou le gain
   total ?
4. **Quatre horizons = quatre tests de plus.** Après votre recommandation 7 sur les familles
   d'inférence, dans quelle famille ce balayage tombe-t-il — confirmation ou sensibilité ? Et
   la correction de multiplicité porte-t-elle sur les 4 horizons, ou sur les 16 cellules
   (4 horizons × 4 polluants) ?

---

## 3. Décision C — la persistance n'est pas définissable pour notre produit principal

Le balayage demandé doit comparer notre méthode à **la persistance** et aux autres références.
Or la persistance — « demain ressemble à aujourd'hui » — **exige une observation au point de
prédiction**. Elle n'est donc définissable qu'au périmètre **AUX STATIONS**, alors que notre
chiffre phare est **PARTOUT**, où par construction aucune observation n'entre.

Le dossier a déjà utilisé la persistance une fois, et c'est un résultat fort : à J+1, CAMS
brut échoue au critère FAIRMODE sur **41,4 % des stations NO₂ — donc fait pire que la
persistance** ; corrigé, il passe sur 96,2 %.

**Mes questions :**

1. **Comment présenter un tableau comparatif où une colonne n'est pas définie pour la ligne
   principale ?** Mettre un tiret est honnête mais illisible ; mettre la persistance en face
   du seul périmètre AUX STATIONS force le lecteur à comparer deux périmètres.
2. **Existe-t-il une persistance « sans observation locale »** qui aurait un sens — par
   exemple la persistance du **champ CAMS** lui-même (la sortie d'hier comme prévision
   d'aujourd'hui) ? Ce serait définissable partout, et ce serait une référence plus dure pour
   notre étage « tendance récente ». Est-ce une référence reconnue, ou une invention qui
   n'aurait de sens que pour nous ?

---

## 4. Ce que je ne vous demande pas

Vos recommandations 1, 3, 5, 6, 7, 10 sont comprises et planifiées ou écartées faute de temps ;
la 4 est absorbée par la décision A ; la 8 est adoptée (marginal conditionnel + ablation
finale, sans Shapley à six étages) ; la 9 est ce que ce brief prolonge. Je ne les rediscute
pas.

**Une seule chose me manque de votre revue 4** : vous concluiez que le résultat U10 sur NO₂
doit être publié « comme sensibilité discordante, pas transformé en veto après lecture ». Sur
le support commun, NO₂ est le **plus stable des quatre** (σ apparié 1,00, 22/24 plis positifs).
**Cela change-t-il votre lecture de la discordance U10**, ou faut-il la publier telle quelle ?

---

## 5. Format

Un fichier **`.md`**, trois sections A/B/C. Et si une seule décision mérite votre temps,
traitez **B** — c'est celle qui engage les quatre derniers jours, et c'est la seule où je n'ai
aucune intuition fiable.
