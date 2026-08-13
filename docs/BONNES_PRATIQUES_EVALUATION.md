# Évaluer une prévision de qualité de l'air — douze pratiques et ce qu'elles ont coûté

*Fiche du 13/08/2026. Transférable : rien ici ne dépend de LightGBM, de CAMS ni de ce
projet. Ce sont des règles d'**évaluation**, applicables à n'importe quelle chaîne de
prévision — y compris pour répondre à l'obligation de bilan annuel de performance
(article 13 de l'arrêté du 16/04/2021).*

**Aucune de ces règles n'est théorique.** Chacune est née d'un résultat que j'ai produit,
cru, et qui était faux. Le chiffre entre parenthèses est ce que l'erreur a coûté — en points
de score, en mois de corpus, ou en conclusion publiée puis retirée.

**Et ce document applique sa propre règle : chaque chiffre porte sa source.** `§ n` renvoie à
`reports/VERITE_DOSSIER.md`, régénérable par `python3 scripts/verite_dossier.py` ; sinon le
fichier est nommé. Un chiffre sans provenance n'est pas vérifiable, donc pas citable.

---

## I. Avant de mesurer — fixer le contrat

### 1. Nommer l'épreuve, parce qu'il y en a quatre et qu'elles ne disent pas la même chose

Un post-traitement se valide **par accident** : si la station de test a servi à
l'apprentissage, le score mesure une mémorisation.

| épreuve | station | mois | ce qu'elle mesure |
|---|---|---|---|
| spatiale | **cachée** | vu | transfert vers un lieu non instrumenté |
| temporelle | vue | **caché** | tenue dans le temps |
| **double aveugle** | **cachée** | **caché** | la condition de déploiement |
| chronologique | **cachée** | **passé seul** | extrapolation réelle |

**Ce que ça coûte de ne pas choisir :** sur l'ozone, la même correction vaut **+3,31 % à
+22,94 %** selon l'épreuve et le périmètre (§ 7 ter). Ce n'est pas une incertitude, ce sont
**cinq questions différentes** — et les cinq réponses sont justes.

> **La règle :** décider de l'épreuve **avant** de voir le résultat, et l'écrire. Le choix
> après coup est indiscernable d'un choix honnête, y compris pour celui qui le fait.

### 2. Afficher le périmètre **effectif**, jamais le périmètre demandé

Une condition de disponibilité — un seuil de couverture, une exception avalée, un pli trop
petit — décide toute seule **de quoi on parle**, sans rien lever.

**Ce que ça a coûté ici :** une ligne `if colonne.notna().mean() > 0.3` faisait entrer un
système dans une comparaison. Comme les scores étaient calculés sur l'**intersection** des
systèmes disponibles, franchir ce seuil a restreint **tout** le tableau : sur PM10,
**39 % du corpus troqués contre deux lignes — 31 mois devenus 19** — sans un mot.

> **La règle :** un traitement imprime **lignes retenues, mois retenus, plis exécutés sur
> plis prévus, familles réellement jointes**. Et une condition de disponibilité soit
> **replie ligne à ligne en comptant le repli**, soit devient une **option explicite** —
> jamais un arbitrage en dur.

---

## II. Mesurer

### 3. Un RMSE global peut s'améliorer pendant que le service se dégrade

83 % des observations sont sous 80 µg/m³. Minimiser l'erreur quadratique sur une
distribution aussi asymétrique **écrase la queue** — c'est-à-dire les épisodes, seul régime
qui déclenche une décision publique.

**Ce que ça a coûté ici :** une correction gagnait **13 % de RMSE** et faisait passer la
détection des dépassements du seuil d'information de **5 sur 15 à 0 sur 15**. Le tableau de
bord était vert.

> **La règle :** ventiler toute évaluation **par bande de concentration**, calées sur les
> classes de l'indice ATMO, et publier le **nombre d'épisodes manqués en valeur absolue** —
> pas un gain de RMSE. Correctif structurel : apprendre le **résidu** `observation − modèle`
> plutôt que l'observation, pour que l'amortissement tire vers « pas de correction » au lieu
> de tirer vers la moyenne.

### 4. Rééchantillonner les **stations**, jamais les lignes

Les heures d'une même station sont fortement corrélées : en tirer 24 consécutives revient à
compter une observation vingt-quatre fois.

| bootstrap sur… | IC 95 % du gain (O₃) | largeur |
|---|---|---|
| les lignes | [+28,1 ; +28,4] | 0,3 point |
| **les stations** | **[+24,7 ; +31,7]** | **7,0 points** |

**Un facteur 23.** Le nombre d'unités indépendantes est de l'ordre du **nombre de
stations** — quelques centaines, pas quelques centaines de milliers de lignes.
*(mesure interne, figée par `test_bootstrap_par_station_bien_plus_large_que_par_ligne` ; les
IC publiés du dossier sont tous des bootstraps de stations — voir § 6.)*

> **La règle :** l'unité de rééchantillonnage est l'unité de **dépendance**. Stations pour
> les scores continus ; **jours** pour la détection, parce qu'un épisode touche des dizaines
> de stations le même jour.

### 5. L'échelle d'agrégation change le verdict — et les deux échelles comptent

La même correction **améliore** le rappel journalier (classe ≥ 4 : 0,243 → 0,471) et le
**dégrade** à l'échelle horaire (O₃ ≥ 130 µg/m³ : 0,31 → 0,19).

Ce n'est pas une contradiction : l'indice retient le **maximum des 24 heures**, ce qui
rattrape l'amortissement horaire. Or l'**indice publié est journalier**, mais une
**procédure d'alerte se déclenche sur un seuil horaire**.

> **La règle :** toute métrique de détection précise son échelle d'agrégation, et le verdict
> est vérifié aux autres échelles pertinentes. Annoncer les deux.

### 6. Un seuil sans événements ne mesure pas une incapacité

**Ce que ça a coûté ici :** j'ai conclu que le modèle « ne détectait pas » le NO₂. Au seuil
d'information horaire de 200 µg/m³, le panel unifié compte **6 dépassements sur 369 872
jours-station** (§ 8). Il n'y avait rien à détecter.

> **La règle :** compter les positifs **avant** d'interpréter un rappel. Un rappel calculé
> sur 6 événements ne mesure pas une propriété du modèle.

---

## III. Citer un résultat

### 7. Trois mots obligatoires : **périmètre · épreuve · échéance**

Sur l'ozone, la même correction vaut **+3,31 %, +9,24 %, +15,83 %, +22,47 % ou +22,94 %**
selon la ligne du tableau (§ 7 ter). Toutes justes, aucune interchangeable — et **elles
changent d'ordre** quand le corpus s'allonge.

> **La règle :** aucun pourcentage ne quitte le document source sans ses trois mots.
> Confondre deux lignes discrédite le dossier entier plus sûrement qu'un chiffre faux : un
> chiffre faux se corrige, une confusion de périmètre jette le doute sur tout le reste.

### 8. Une part élevée n'est pas une part grave

Une correction apprise ne profite pas à tout le monde. Combien de stations dégrade-t-elle ?
**De 2,1 % à 42,5 % selon l'épreuve** (§ 11 bis) — l'épreuve, pas le polluant.

Mais le chiffre seul induit en erreur : les **42,5 %** de PM2,5 en double aveugle s'adossent
à un gain médian de **+2,5 %** — la correction y est quasi neutre et le signe bascule sur du
bruit. Là où le gain est réel (NO₂ spatial, **+35,6 %** médian), la part tombe à **7,8 %**.

> **La règle :** une part de stations dégradées se lit **avec le gain médian**. Séparément,
> l'une des deux moitiés ment.

### 9. Un gain d'axe payé sur l'autre axe n'est pas une amélioration

**Ce que ça a coûté ici :** régler les hyperparamètres contre une validation **par groupes
de stations** donne, sur l'ozone (§ 10 sexies) :

| réglage | gain spatial | gain temporel | pire mois | mois négatifs |
|---|---|---|---|---|
| **réglé** sur les stations | **+29,91 %** | +6,41 % | −7,32 % | **4** |
| par défaut | +24,52 % | **+9,26 %** | −5,88 % | 2 |

**+5,39 points d'un côté coûtent −2,85 de l'autre**, et les mois négatifs doublent. Un
réglage optimise **la structure de validation qu'on lui donne**, pas « la généralisation ».

> **La règle :** annoncer un gain de réglage en **nommant l'axe** sur lequel il a été choisi,
> et vérifier l'autre axe avant de retenir la configuration. Si le service revendique les
> deux généralisations, régler contre une seule est un défaut de protocole.

---

## IV. Les défauts qui ne lèvent aucune erreur

*Les quatre suivants ne plantent pas, ne dégradent aucune métrique visible, et produisent
un résultat parfaitement plausible. C'est ce qui les rend coûteux.*

### 10. Un nom — de fichier, de variable, d'axe — n'est pas une source de vérité

- **Nom de fichier.** Une expression ancrée à droite sur `..._202308_202309.parquet`
  capturait `202309` et perdait `202308`. Résultat : **11 mois retenus sur 17, 35 % du jeu
  d'entraînement perdu en silence.** Découvert parce qu'une courbe d'apprentissage
  s'arrêtait à trois points au lieu de six.
- **Nom d'axe.** `horizon=1` a été appelé « la prévision à J+1 » pendant des semaines. La
  sortie de référence est à 00 UTC et l'échéance 0 h porte l'horodatage **du même jour** :
  c'était **J0**. Rien ne plantait, les appariements étaient corrects, les contrôles au vert.
  Seul le **nom** était faux — et c'est le nom qui allait dans le rapport.

**Le coût réel du second :** une comparaison au produit officiel construite sur un handicap
**imaginaire**. J'expliquais un rappel plus faible par « notre J+1 contre leur J0 » alors que
les deux systèmes étaient au même horizon. **J'excusais un écart au lieu de le regarder.**

> **La règle :** les bornes se lisent **dans les données** — `min()`, `max()`, liste
> effective des variables. Et l'unité d'un axe se vérifie en une ligne : prendre une valeur,
> afficher l'horodatage qu'elle porte, vérifier qu'il correspond à ce que le nom promet.
> **Corollaire :** un nom faux se propage plus loin que le code — il entre dans les figures,
> les rapports et les phrases préparées pour un oral. Le corriger dans le script ne suffit
> pas.

### 11. Le criblage — élaguer puis publier sur les mêmes plis

Mesurer l'apport de chaque famille de variables est légitime — c'est ce que fait une ablation
(§ 12 bis). **Retirer les familles à faible apport puis publier le score de la pile élaguée
sur ces mêmes plis** ne l'est pas : le gain apparent est gonflé **×2 à ×4**, mesuré sur ce
projet lors d'un balayage de variables inexploitées (§ 10 sexies le rappelle).

Le même mécanisme, vu ailleurs : sur 100 variantes de krigeage, prendre la meilleure **sur
les lignes qui la notent** rend jusqu'à **+1,67 %** ; la choisir sur la première moitié du
calendrier et la noter sur la seconde rend **+1,01 %, et négatif sur 2 polluants sur 4**
(§ 10 sexies). **L'écart entre les deux *est* le criblage.**

> **La règle :** une ablation est une **mesure**, jamais une **sélection**. Si une sélection
> doit être faite, elle se fait sur des plis qui ne serviront pas à publier le score.

### 12. Une mesure n'est pas une propriété — et un code 200 n'est pas un résultat

**Ce que ça a coûté ici :** une requête chronométrée **29 s** une fois a été citée trois
fois et a fondé un plan. Refaite : **76 s** pour cinq fois moins de données, puis un
**504 Gateway Time-out**. La première mesure bénéficiait d'un cache et d'un serveur au repos.

Le même jour, trois `curl` rendant `200, 200, 200` ont été lus comme trois services
disponibles. C'étaient trois **pages d'erreur HTML**.

> **La règle :** mesurer au moins deux fois, à des moments distincts, et extrapoler depuis la
> **pire** valeur — jamais la première. Et comparer le **volume reçu** au volume demandé :
> une réponse de 92 octets pour 1,1 Mo demandé n'est pas un téléchargement rapide.

### 13. Un seuil doit regarder du côté où le défaut pousse

**Ce que ça a coûté ici :** l'export PDF du dossier contrôlait sa sortie et exigeait
`pages >= 40`. Une régression de mise en page a fait passer le document de **54 à 49 pages** —
rien n'était perdu, le navigateur avait mis **tout le document à l'échelle 0,90**. Le défaut
**produit moins de pages** : 49 passait le contrôle exactement comme 54, et l'aurait passé
à 41.

> **La règle :** en écrivant un seuil, se demander **dans quel sens le défaut pousse le
> chiffre**. S'il le pousse du côté confortable, le seuil est décoratif — il en faut un autre,
> sur une autre grandeur. Et comparer un artefact régénéré **à sa version précédente**, pas à
> une constante.

### 14. La granularité de la mesure décide de ce qu'elle peut attribuer

**Ce que ça a coûté ici :** une rupture du modèle amont, mesurée sur des **moyennes
mensuelles**, coïncidait avec une mise à niveau documentée du fournisseur au **13 novembre
2024**. J'ai conclu à la causalité et je l'ai écrit dans deux rapports. Un détecteur
journalier l'a démenti : le déplacement est daté du **24 octobre**, soit **huit à dix-neuf
jours avant**. La maille mensuelle ne pouvait pas distinguer ces dates.

> **La règle :** trouver un événement documenté dans la même maille temporelle qu'un signal
> n'est pas une preuve — c'est une **coïncidence de granularité**. Avant d'attribuer,
> vérifier que la résolution de la mesure est plus fine que l'écart entre les causes
> candidates. **Corollaire :** si l'observation *et* la prévision se déplacent, la cause est
> extérieure au modèle ; si seule la prévision bouge, elle lui est interne.

---

## V. La règle qui commande les treize autres

> **Signaler un biais n'est pas le corriger.**
>
> Écrire « attention, cette comparaison est imparfaite » puis la publier quand même, **c'est
> la valider**. La réserve honnête sert quand on ne *peut* pas corriger — jamais quand on ne
> l'a pas *fait*.

Et cela vaut **dans les deux sens**. S'infliger un protocole plus dur que celui de la
référence n'est pas de la prudence : c'est fausser la comparaison contre soi, ce qui est
aussi peu informatif que la fausser en sa faveur.

**Un exemple des deux côtés, mesuré :** ce projet figeait les réglages de la méthode
concurrente « pour ne pas lui donner deux chances quand nous n'en prenons qu'une ».
Défendable — et **non mesuré**, donc à croire sur parole. Chiffré : la précaution leur coûte
**au plus +1,01 %**, et sur deux polluants sur quatre elle les **avantage** (§ 10 sexies).
Le coût de la mesure : trois minutes de calcul.

---

## Liste de contrôle — avant de publier un bilan de performance

**Le protocole**
- [ ] L'épreuve est nommée et a été choisie **avant** de voir le résultat
- [ ] Les stations de test n'ont jamais servi à l'apprentissage, **ni au choix des réglages**
- [ ] Le périmètre **effectif** est imprimé : lignes, mois, plis exécutés sur plis prévus
- [ ] Aucune condition de disponibilité ne change le corpus sans être comptée

**Les chiffres**
- [ ] Chaque pourcentage porte **périmètre · épreuve · échéance**
- [ ] Les intervalles sont bootstrapés sur l'unité de **dépendance** (stations, ou jours)
- [ ] Les scores sont ventilés **par bande de concentration**
- [ ] Le nombre d'**épisodes manqués en valeur absolue** est publié
- [ ] Le nombre de **positifs** est publié à côté de tout rappel
- [ ] La part de stations **dégradées** est publiée avec son **gain médian**

**Les limites**
- [ ] Les limites sont énoncées **par l'auteur**, avant qu'on les trouve
- [ ] Chaque réserve a été testée : *puis-je corriger au lieu de prévenir ?*
- [ ] Les hypothèses **réfutées** figurent au même titre que les confirmées

**Les artefacts**
- [ ] Tout chiffre publié existe dans un document source **régénérable**
- [ ] Chaque contrôle de sortie regarde **du côté où le défaut pousse**
- [ ] Les artefacts régénérés sont comparés à leur **version précédente**

---

## Ce que cette fiche ne prétend pas

Ces règles viennent d'**un** projet, sur **un** produit amont, sur trois ans de données
françaises. Elles ne sont pas un référentiel : le référentiel existe, c'est **FAIRMODE** et
la guidance du LCSQA, et il prime sur tout ce qui précède.

Ce qu'elles ajoutent est d'une autre nature : **elles disent comment on se trompe de bonne
foi.** Aucune des quatorze n'a produit d'erreur, de plantage ni de métrique dégradée. Toutes
ont rendu un résultat plausible — et trois auraient été publiées si un contrôle
supplémentaire n'avait pas été fait.

> **La question à se poser avant de laisser tourner quoi que ce soit :** *si ce traitement
> produisait un résultat incomplet ou faux, est-ce que je m'en apercevrais ?* Si la réponse
> est non, instrumenter d'abord.
