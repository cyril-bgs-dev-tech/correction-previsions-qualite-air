# Troisième revue adverse — le signal de spéciation doit d'abord être réaligné

## 1. Le gain de +11,57 % : signal de source ou proxy latent ?

### Verdict préalable : le chiffre actuel n'est pas encore un résultat J+1 citable

Le contrôle « mêmes lignes » est nécessaire, mais il ne garantit pas le **même jeu
d'information**. L'audit du code révèle un décalage plus important que la fenêtre réduite :

- [`jeu_journalier`](../scripts/optuna_mos.py#L157) appelle
  `charger(polluant, 1)` ; dans le dépôt, `horizon=1` sélectionne les échéances **1–24 h**, donc
  J0 ([`TRANCHES`](../scripts/fit_mos.py#L60)) ;
- la spéciation est téléchargée aux échéances **25–48 h**, donc J+1
  ([`ECHEANCES_J1`](../scripts/telecharger_speciation_cams.py#L78)) ;
- les deux flux ne sont ensuite réunis que sur `(station_id, jour)`
  ([jointure](../scripts/ablation_speciation.py#L98)), après perte de l'heure d'initialisation
  et de l'échéance ;
- la coupure temporelle est recalculée à la médiane **après** cette jointure
  ([partage](../scripts/ablation_speciation.py#L108)). Elle n'est donc pas nécessairement
  celle du résultat de référence.

Je ne vois pas de fuite du futur qui favoriserait la spéciation : le flux 25–48 h est au
contraire moins frais que le flux 1–24 h. Mais le test actuel mesure « base J0 + composition
J+1 plus ancienne », pas l'apport de la composition à la chaîne J+1. Les +11,57 %, +6,63 %,
+6,04 % et +4,90 % sont des **signaux exploratoires à reproduire**, pas quatre gains à
publier.

Autre correction nette : ma recommandation précédente
`pm2.5_anthropogenic_total_carbon` était erronée. Le `form.json` exécutable du catalogue est
la source de vérité ; la clé correcte est bien `total_elementary_carbon`. Le correctif est
présent dans [`telecharger_speciation_complement.py`](../scripts/telecharger_speciation_complement.py#L69).

### Recommandation 1 — imposer un contrat d'information J+1 avant toute interprétation

**Test exact.** Faire accepter `--horizon 2` à l'ablation, conserver dans les deux flux
`issue_time`, `valid_time` et `leadtime_hour`, puis joindre d'abord les données **horaires**
sur `(station_id, issue_time, leadtime_hour)`. Agréger seulement ensuite les 24 échéances
25–48 h. Pour chaque ligne agrégée, écrire dans le manifeste : date d'émission, jour cible,
liste des échéances reçues, nombre d'heures communes, source CAMS et empreinte des clés. La
coupure temporelle doit être calculée une fois sur le corpus de référence avant la jointure,
puis passée explicitement à toutes les configurations.

**Seuil de décision.** Zéro échéance hors `[25, 48]`, zéro `valid_time != issue_time +
leadtime`, zéro émission postérieure à l'instant d'émission déclaré, mêmes clés horaires
pour base et spéciation, au moins 18 heures communes par jour-station, et empreintes de clés
base/spéciation strictement identiques sur le test. Une seule violation bloque le score.
Après cette garde, poursuivre seulement les polluants dont le gain corrigé atteint encore
**2,0 %**.

**Coût : 2 h** — adaptation de l'interface et du manifeste, réagrégation, puis quatre
ajustements appariés.

**Si le test échoue, écrire exactement :**

> L'ablation initiale associait une base CAMS 1–24 h à une spéciation 25–48 h sur le seul
> jour civil. Après alignement de l'initialisation et de l'échéance J+1, son gain ne se
> reproduit pas ; les valeurs exploratoires de +4,90 % à +11,57 % sont retirées et la
> spéciation n'est pas retenue.

### Recommandation 2 — contrôler le complément sur son contenu, puis l'intégrer réellement

Le téléchargement complémentaire contrôle encore la taille du fichier avant renommage
([lignes 99–111](../scripts/telecharger_speciation_complement.py#L99)), pas les variables
livrées. L'extracteur actuel ne lit que `data/raw/cams_speciation`, ignore le répertoire
complémentaire et saute un Parquet si celui-ci est plus récent que le seul fichier source
historique ([lignes 47 et 89–92](../scripts/extraire_speciation.py#L47)). En l'état, finir le
téléchargement ne peut donc pas faire entrer sel marin et carbone total dans l'ablation.

**Test exact.** Ouvrir chacun des 32 NetCDF juste après réception ; enregistrer la liste des
`data_vars`, établir le renommage à partir du premier fichier réel, puis exiger les deux
champs livrés correspondant à `pm10_sea_salt_dry` et `total_elementary_carbon` dans les
32 fichiers. Extraire le complément sous un nom distinct et effectuer une jointure 1:1 sur
`(station_id, timestamp_utc)` avec le socle, sans dépendre du `mtime` du seul fichier
historique.

**Seuil de décision.** 32/32 fichiers ouverts, 2/2 variables dans chacun, aucun doublon de
clé, conservation de 100 % des clés du socle sur la fenêtre commune, moins de 0,1 % de
valeurs non finies par variable et variance strictement positive dans chaque époque CAMS.

**Coût : 1 h 30** après la fin du transfert.

**Si le test échoue, écrire exactement :**

> Le complément CAMS n'a pas satisfait le contrôle de schéma sur les 32 mois. Le sel marin
> et le carbone élémentaire total sont donc exclus ; le résultat reste limité aux cinq
> traceurs effectivement vérifiés et ne permet pas d'interpréter le carbone résidentiel ni
> la fraction grossière marine.

### Ce que disent — et ne disent pas — les corrélations

La corrélation d'un composant avec l'observation n'est pas le bon test. Le modèle ne prédit
pas l'observation à partir du composant seul : il prédit le résidu `observation − CAMS`
**conditionnellement au total CAMS et aux autres variables**. Un composant peut donc avoir
une corrélation marginale de 0,466 avec l'observation et néanmoins identifier, à masse totale
égale, les situations où CAMS surestime ou sous-estime cette masse.

La corrélation de 0,911 entre somme des composants et total et le ratio moyen de 0,546 disent
toutefois que les dix colonnes portent simultanément : niveau total, composition, amplitude
intra-journalière, saison, géographie et régime de modèle. Le gain de 6–7 % sur O3 et NO2 est
un avertissement utile : des traceurs particulaires peuvent partager émissions et météo avec
les gaz, mais un bénéfice de même ordre sur les quatre polluants est plus compatible avec un
**proxy de régime CAMS** qu'avec un mécanisme propre au biais de source des PM.

### Recommandation 3 — une échelle de falsification, pas une histoire de source immédiate

**Test exact.** Sur le J+1 réaligné, verrouiller six configurations LightGBM, sans nouveau
réglage :

1. `B` : base de production ;
2. `T` : `B` + forme du total CAMS (`min`, `max`, moyenne, écart-type et P90–P10 des 24
   échéances), afin que les maxima de composants ne puissent pas seulement fournir une
   amplitude du total absente de la base ;
3. `C` : `T` + médiane de chaque composant par station × mois, calculée sur le train
   uniquement ; elle conserve géographie et saison, mais pas l'événement courant ;
4. `S` : `T` + composants courants ;
5. `R` : `T` + résidus de composants après prédiction par un LightGBM de production à cinq
   plis temporels contigus dans le train ; les prédicteurs de nuisance sont le total, le
   calendrier, les variables spatiales, la typologie et l'époque CAMS. Les résidus du train
   sont hors pli et ceux du test viennent d'un modèle réajusté sur tout le train ;
6. `F` : `T` + composition relative (`somme_composants / total` et parts des composants dans
   leur somme), avec pour chaque composant un pseudo-compte égal à la moitié de sa plus
   petite valeur strictement positive dans le train.

Sur le test, effectuer aussi une permutation **jointe** de tout le vecteur de composants au
sein des strates `époque CAMS × mois × cluster spatial × décile du total CAMS`. Elle préserve
les corrélations entre composants et limite le hors-distribution, tout en détruisant
l'association fine événement–résidu. Réaliser le contraste particules–gaz sur les mêmes
prédictions : moyenne des apports PM10/PM2,5 moins moyenne des apports O3/NO2.

**Seuil de décision.** Employer l'expression « information dynamique de composition,
compatible avec un biais dépendant de la source » seulement si les cinq conditions suivantes
passent :

- `S − T` apporte au moins 2,0 points, borne basse bootstrap > 0 après Holm ;
- `S − C` apporte au moins 2,0 points, borne basse > 0 ;
- `R` ou `F` conserve au moins 50 % de `S − T` et au moins 2,0 points ;
- la permutation conditionnelle coûte au moins 2,0 points, borne basse > 0 ;
- le contraste particules–gaz est d'au moins 2,0 points, borne basse > 0.

Le signe doit en outre être identique dans les époques U9 et U10 et avec blocs temporels de
un et deux mois. Même si tout passe, « causal » reste interdit : il faudrait une spéciation
observée ou une perturbation d'émissions pour identifier causalement une source.

**Coût : 5 h** pour les variables de contrôle, les six configurations, les placebos et le
tableau de contrastes.

**Si le test échoue, écrire exactement :**

> Les résumés de composition CAMS améliorent la prédiction sur le sous-corpus rétrospectif,
> mais leur apport est largement reproduit par la forme du total, la climatologie
> spatio-saisonnière ou un régime commun aux particules et aux gaz. Nous les interprétons
> comme un proxy de régime CAMS, et non comme la preuve d'un biais propre à une source
> d'émission.

## 2. Ablation individuelle paradoxale : redondance, nuisance ou mauvais protocole ?

Le résultat n'invalide pas le bloc. Une suppression individuelle mesure l'information
**unique** d'une variable conditionnellement à toutes les autres ; le gain du bloc mesure
l'information **jointe**. Avec des champs fortement corrélés, cinq variables peuvent porter
la même frontière de régime : retirer l'une ne coûte rien, retirer les cinq coûte beaucoup.

Une suppression qui améliore peut aussi venir de la recherche de coupures de LightGBM : avec
`subsample=0.8` et `colsample_bytree=0.8`, un prédicteur redondant change les coupures
accessibles et peut dégrader le transfert temporel. Un seul ajustement ne sépare donc pas
redondance, nuisance et hasard algorithmique. L'importance native, SHAP par colonne et une
permutation marginale ordinaire seraient particulièrement trompeuses sous colinéarité.

### Recommandation 4 — remplacer le leave-one-out par une décomposition exhaustive de trois groupes

**Test exact.** Une fois le complément disponible, fixer trois groupes physiques :

- `grossier_naturel` : poussières + sel marin ;
- `combustion_organique` : EC résidentiel + EC total + matière organique + feux ;
- `secondaire` : SIA ; le nitrate reste une expérience séparée à partir de décembre 2024.

Évaluer les **huit** sous-ensembles possibles des trois groupes, sur les mêmes lignes J+1,
avec cinq graines verrouillées. Calculer pour chaque groupe sa valeur de Shapley exacte en
moyennant son apport marginal sur les six ordres possibles. Ajouter comme sensibilité la
permutation conditionnelle de toutes les colonnes du groupe, jamais d'une colonne isolée.
Conserver les prédictions par graine et par époque.

**Seuil de décision.** Attribuer un apport prédictif à un groupe seulement si sa contribution
de Shapley médiane est ≥ 1,0 point, positive dans au moins 4 graines sur 5, borne basse
appariée > 0 et signe identique en U9 et U10. Sinon, publier seulement l'apport du bloc
complet. Cette attribution reste prédictive, jamais causale.

**Coût : 3 h**, car trois groupes rendent la décomposition exhaustive peu coûteuse.

**Si le test échoue, écrire exactement :**

> Le bloc de composition CAMS apporte une information prédictive jointe, mais la colinéarité
> de ses traceurs ne permet pas d'attribuer ce gain à une famille physique particulière.
> Nous publions l'ablation du bloc et renonçons à toute importance par espèce.

### Recommandation 5 — ne qualifier `ecres_conc` de nuisance qu'après réplication

**Test exact.** Dans le groupe `combustion_organique`, comparer avec et sans
`ecres_conc`, en présence de l'EC total, sur cinq graines, séparément en U9 et U10, avec
prédictions appariées. C'est le test pertinent : sans EC total, « résidentiel » peut seulement
remplacer un carbone de combustion manquant.

**Seuil de décision.** Déclarer `ecres_conc` nuisible et l'écarter seulement si sa suppression
améliore d'au moins 0,5 point, borne basse > 0, dans les deux époques et au moins 4 graines
sur 5. Si le gain est compris entre −0,5 et +0,5 point ou change de signe, écrire
« redondant/non identifié », pas « bruité ».

**Coût : 1 h**, inclus dans les huit configurations si les prédictions sont correctement
persistées.

**Si le test échoue, écrire exactement :**

> Le carbone élémentaire résidentiel n'apporte pas d'information unique conditionnellement
> aux autres traceurs, mais sa suppression n'améliore pas la généralisation de façon stable.
> Il est classé redondant ; aucune conclusion sur la qualité physique de ce champ n'est tirée.

Si le bloc global passe mais aucun groupe ne passe, la formulation honnête dans le dossier
est donc :

> Sur une fenêtre J+1 commune, l'ajout groupé de résumés de composition CAMS améliore le
> LightGBM de production. Ces champs sont corrélés et peuvent encoder simultanément
> composition, saison, géographie et version du système ; le protocole n'identifie ni une
> espèce responsable ni un effet causal d'émission.

## 3. Corpus différent : publier sans fabriquer une addition

Une comparaison appariée `base` contre `base + spéciation` reste informative sur son support
commun, à condition de réparer l'échéance. Elle ne doit jamais être additionnée au gain du
tableau de référence : fenêtre, population, coupure et possiblement régime CAMS diffèrent.
Le 100 % de rétention PM10 et les 86–87 % des autres polluants décrivent en outre des corpus
de départ différents ; 100 % ne transforme pas PM10 en témoin des trois autres.

### Recommandation 6 — publier d'abord une annexe d'incrément sur support commun

**Test exact.** Produire, pour chaque polluant, un manifeste et une table contenant : horizon
et échéances, bornes d'initialisation et de cible, coupure fixe, époques CAMS, nombres de
lignes train/test, stations, taux de rétention, empreinte des clés, RMSE CAMS, RMSE base,
RMSE base + spéciation et intervalle apparié. La date de coupure est celle obtenue une fois
sur le corpus de référence **avant** filtrage de disponibilité ; elle n'est jamais la médiane
recalculée du sous-corpus. Les deux modèles doivent être réajustés sur le même sous-corpus.

**Seuil de décision.** Empreinte de clés base/candidat identique, zéro différence de lignes,
zéro changement d'hyperparamètres, gain ≥ 2,0 points, borne basse > 0 après Holm, même signe
avec blocs d'un/deux mois et en U9/U10. Le tableau porte obligatoirement le libellé
« expérience incrémentale sur support commun ; non additive au résultat principal ».

**Coût : 2 h** après production des prédictions corrigées.

**Si le test échoue, écrire exactement :**

> Sur le support commun où la composition CAMS est disponible, son apport ne franchit pas
> simultanément le seuil pratique, l'incertitude appariée et la stabilité entre époques. Le
> résultat principal sur fenêtre longue demeure inchangé et aucun gain de spéciation ne lui
> est ajouté.

### Recommandation 7 — ne republier toute la chaîne réduite que si la spéciation devient un composant du produit

Dans les 3,5 jours, je **ne** republierais pas tous les résultats historiques sur 32 mois.
L'annexe appariée suffit pour documenter l'expérience. En revanche, si le dossier affirme
que le produit final inclut désormais la spéciation, alors CAMS brut, base, produit final,
concurrents et métriques d'épisodes doivent tous être recalculés sur le même support.

**Test exact.** Déclencher cette republication seulement après passage des recommandations
1, 3 et 6. Rejouer le générateur du tableau final avec un filtre de clés commun, puis vérifier
automatiquement que toutes les lignes du tableau partagent horizon, coupure, stations,
fenêtre et empreinte de test.

**Seuil de décision.** 100 % des systèmes comparés sur la même empreinte ; aucun chiffre
historique transféré par copier-coller ; rang des systèmes et conclusion opérationnelle
inchangés entre U9 et U10. Sinon la spéciation reste une expérience annexe non déployée.

**Coût : 5 à 6 h.** Ce coût n'est engagé que si toutes les gardes précédentes passent.

**Si le test échoue, écrire exactement :**

> La chaîne complète n'a pas pu être comparée sur une population, une fenêtre et une
> échéance communes. La spéciation demeure une expérience de sensibilité ; elle n'est ni
> intégrée au produit annoncé ni additionnée aux gains publiés sur la fenêtre longue.

## 4. Arbitrage statistique : spéciation d'abord, RealMLP gelé

### Le bootstrap actuel doit être corrigé avant exécution

[`bootstrap_apparie.py`](../scripts/bootstrap_apparie.py) a le bon principe — différence
appariée, blocs spatiaux et temporels — mais pas encore le protocole promis :

- le KMeans est ajusté sur une table contenant une ligne par observation, donc les stations
  les plus disponibles pondèrent les centroïdes ; il faut ajuster sur les stations uniques ;
- les coordonnées latitude/longitude ne sont pas projetées ; utiliser Lambert-93 ;
- les blocs de deux mois sont non chevauchants, alors que la sensibilité annoncée était
  mobile ; utiliser des blocs mobiles/circulaires, ou à défaut les deux origines 0 et 1 ;
- les sorties d'un et deux mois ont le même nom et la seconde écrase la première ;
- le défaut est 2 000 tirages, aucune correction de Holm n'est calculée et les tirages ne
  sont pas persistés.

### Recommandation 8 — bootstrapper la spéciation réalignée avant toute autre piste

**Test exact.** Après passage des gardes de données, lancer 10 000 tirages croisés
`mois × clusters` sur les prédictions appariées J+1 de `base` et `core7`, avec 20 clusters
de stations uniques projetées. Faire l'analyse primaire avec blocs mensuels, la sensibilité
avec blocs mobiles de deux mois, enregistrer les tirages sous des noms incluant polluant,
horizon, époque, taille de bloc, graine et empreinte de prédictions. Calculer pour chacun des
quatre polluants une p-valeur unilatérale par bootstrap centré,
`(1 + nombre de (gain_bootstrap - gain_observe) >= gain_observe) / (B + 1)`, puis appliquer
Holm à la famille de quatre.

**Seuil de décision.** Gain ponctuel ≥ 2,0 points, p ajustée de Holm < 0,05, borne basse
IC95 > 0, même signe et même verdict avec blocs d'un/deux mois, et gain positif séparément
en U9 et U10. Les contrôles de mécanisme restent nécessaires pour parler de source. Le fait
d'avoir vu +11,57 % ne justifie pas de relever maintenant le seuil statistique : les gardes
d'information et les placebos sont la protection correcte contre un gros artefact.

**Coût : 3 h** — environ 1 h 30 de correction/contrôle, moins d'une heure de calcul et
30 minutes de synthèse.

**Si le test échoue, écrire exactement :**

> Après alignement strict de l'échéance J+1 et bootstrap apparié par blocs temporels et
> spatiaux, l'apport de la spéciation ne satisfait pas simultanément la pertinence pratique,
> le contrôle de multiplicité et la stabilité U9/U10. Les gains ponctuels exploratoires ne
> sont pas retenus comme amélioration généralisable.

Même si le test passe, le bloc a déjà été consulté. La phrase maximale permise est :

> Sur ce corpus rétrospectif déjà exploré, l'apport de la spéciation reste positif sous
> rééchantillonnage apparié et entre époques ; cette robustesse conditionnelle devra être
> confirmée sur une origine future gelée.

### Recommandation 9 — abandonner RealMLP pour ce dossier, pas pour toujours

Le critère d'arbitrage peut être appliqué aux résultats déjà produits : une nouvelle
architecture ne consomme le budget confirmatoire que si elle apporte au moins 2 points sur
au moins deux polluants, sans dégradation supérieure à 1 point sur un autre. RealMLP donne
−0,89 %, +0,01 %, +1,25 % et +2,66 % : un seul polluant franchit 2 points, aucun avantage
transversal n'apparaît.

**Test exact.** Figer les quatre artefacts RealMLP et vérifier leur lignée, sans nouveau
réglage ni bootstrap. Réouvrir la piste seulement sur une future origine, avec architecture
et budget fixés avant lecture.

**Seuil de décision.** Le seuil ci-dessus est manqué ; LightGBM reste le moteur. RealMLP est
classé « exploratoire non prioritaire », non « équivalent » — l'équivalence n'a pas été
testée.

**Coût : 30 min** de contrôle et rédaction ; **0 h de calcul supplémentaire**.

**Texte exact à publier :**

> À budget de réglage égal, RealMLP n'a amélioré LightGBM d'au moins 2 points que sur un des
> quatre polluants et a légèrement dégradé le NO2. Faute d'avantage transversal et compte
> tenu du délai, nous conservons LightGBM et ne consacrons pas le budget confirmatoire au
> réseau. Ce choix de priorité ne démontre pas l'équivalence des architectures.

## 5. Plan exécutable sous 3,5 jours et protocole de reprise

### Ordre ferme et budget de 28 heures

| ordre | travail | garde de sortie | plafond |
|---:|---|---|---:|
| 1 | Figer les artefacts actuels ; corriger horizon, initialisation, coupure et manifeste | contrat J+1 de la recommandation 1 | 2 h |
| 2 | Finir, contrôler et extraire le complément | 32/32 mois, schéma 2/2 | 1,5 h |
| 3 | Rejouer `base/core5/core7` sur les quatre polluants | poursuivre seulement les gains corrigés ≥ 2 % | 2 h |
| 4 | Exécuter `B/T/C/S/R/F` et les contrastes particules–gaz | verdict source/proxy préenregistré | 5 h |
| 5 | Décomposition exhaustive des trois groupes, cinq graines, U9/U10 | attribution ou renoncement explicite | 4 h |
| 6 | Corriger et lancer le bootstrap spéciation | Holm + blocs 1/2 mois + deux époques | 3 h |
| 7 | Produire l'annexe de comparabilité et intégrer le texte | aucune addition inter-corpus | 3 h |
| 8 | Régénérer et contrôler les livrables finaux | chiffres issus uniquement des manifestes validés | 4 h |
| 9 | Réserve pour reprise machine et un seul recalcul fautif | aucun élargissement scientifique | 3,5 h |
|  | **Total** |  | **28 h** |

La republication complète de la chaîne réduite, chiffrée à 5–6 h, n'entre pas dans ce budget
par défaut. Elle remplace la réserve et une partie de l'intégration uniquement si toutes les
gardes de spéciation passent et si le produit final est officiellement modifié. RealMLP ne
consomme plus de calcul.

### Recommandation 10 — faire du manifeste et de la reprise une garde de livraison

**Test exact.** Écrire atomiquement un Parquet de prédictions et une entrée JSON après chaque
`polluant × horizon × époque × configuration × graine`. Le nom contient ces cinq dimensions ;
le bootstrap ajoute la taille de bloc. Le manifeste stocke commande, commit, empreintes des
données et des clés de test, colonnes, hyperparamètres, graine, coupure, effectifs et statut
`commencé/validé`. Une reprise ne saute un calcul que si toutes les empreintes correspondent.
Chaque processus est borné à deux heures.

**Seuil de décision.** Zéro fichier partiel traité comme final, zéro collision de nom, zéro
configuration incomplète dans une moyenne, et reproduction au bit près d'un artefact choisi
au hasard avant génération du livrable. Le PDF ou tableau final ne lit que les statuts
`validé`.

**Coût : 1 h 30**, inclus dans les lignes 1 et 8 du budget.

**Si le test échoue, écrire exactement :**

> La lignée ou la reprise d'au moins un artefact scientifique n'a pas satisfait le contrôle
> d'intégrité. Aucun chiffre dépendant de cet artefact n'est livré ; le dernier manifeste
> entièrement validé demeure la source canonique.

### Décision finale

L'ordre rationnel n'est donc pas « bootstrapper le plus gros chiffre ». Il est :

1. invalider ou réparer le décalage J0/J+1 ;
2. vérifier que le complément entre effectivement dans les données ;
3. reproduire le gain sur support commun ;
4. falsifier les explications saison/géographie/forme du total ;
5. seulement alors quantifier l'incertitude et, éventuellement, attribuer un groupe.

Si toutes les gardes scientifiques échouent, la conclusion de livraison est :

> Un fort signal exploratoire de composition CAMS a été détecté, puis soumis à un contrôle
> d'échéance, de corpus, de régime et d'incertitude appariée. Il ne satisfait pas les gardes
> nécessaires à une intégration au produit. Le LightGBM de référence et ses résultats sur
> fenêtre longue restent inchangés ; ni la spéciation ni RealMLP ne sont promus dans ce
> dossier.
