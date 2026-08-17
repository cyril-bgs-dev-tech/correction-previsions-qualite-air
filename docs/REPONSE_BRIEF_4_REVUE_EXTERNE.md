# Quatrième revue adverse — une seule passe encore, puis gel

**Note de lecture.** Les seuils ci-dessous sont fixés avant la passe `core7` sur support
commun, dont les résultats ne sont pas encore connus. Ils ne sont pas présentés
rétroactivement comme préenregistrés pour les résultats déjà montrés dans le brief. Pour ces
derniers, je donne un verdict descriptif et réserve toute décision confirmatoire à cette
unique passe corrigée.

## 0. Verdict sur le contexte

Le dossier ne doit pas « arrêter de mesurer » immédiatement, mais il ne doit ouvrir **aucune
nouvelle piste**. Il reste une seule passe confirmatoire, sur la pile existante : refaire la
comparaison finale avec et sans spéciation sur un support où les champs sont réellement
disponibles, puis lui donner un intervalle apparié. Après cela : gel.

Deux constats de code rendent cette passe préalable à toute lecture du futur § 8 :

1. [`methode_maximale.py`](../scripts/methode_maximale.py#L212-L225) joint la spéciation à
   gauche, sans restreindre le corpus. O3, NO2 et PM2,5 gardent donc août–décembre 2023,
   cinq mois où **toutes** les colonnes de spéciation sont manquantes. Leur motif de
   disponibilité devient un indicateur d'époque exploitable par LightGBM. Le commentaire
   affirme que la spéciation restreint la fenêtre ; le code ne le fait pas.
2. Le même script prend toutes les colonnes `spe_*`. Il intègre donc **16 colonnes**, y
   compris les deux résumés du nitrate absent avant décembre 2024, alors que l'ablation de
   référence exclut explicitement ce traceur tardif. Le test final n'est pas le `core7`
   homogène annoncé.

Une troisième correction est éditoriale mais bloquante : la § 12 et
`p0_donnees.json` appellent `horizon=2` **J+2**, alors que le contrat du dépôt est
25–48 h = **J+1**. Le même dossier l'appelle correctement J+1 quelques lignes plus haut.

### Recommandation 0 — remplacer le tableau phare par une passe `core7` sur support commun

**Test exact.** Restreindre les quatre polluants à `2024-01-01 → 2025-12-31`, exclure
`pm2p5_no3_conc`, exiger exactement les 14 colonnes moyenne/maximum des sept traceurs
`core7`, puis rejouer uniquement `+ tendance` et `+ spéciation` dans les plis double aveugle
existants. Écrire les prédictions ou, au minimum, `n_test`, `rmse_cams`, `rmse_sans` et
`rmse_avec` par mois. Remplacer partout l'étiquette J+2 par J+1.

**Seuil fixé avant lecture.** Vingt-quatre mois pour chaque polluant ; zéro valeur manquante
dans les 14 colonnes ; zéro nitrate ; mêmes clés test avec/sans ; 24 plis exécutés sur 24 ;
empreinte de test identique dans les deux configurations. Une seule violation rend le score
non publiable.

**Coût : 2 h 30** — environ 1 h de correction et contrôles, 40 min de calcul sur quatre voies,
puis 45–50 min de vérification et intégration.

**Si le test échoue, écrire :**

> La pile publiée mélangeait des périodes où la composition CAMS était absente et incluait
> un nitrate disponible seulement depuis décembre 2024. Faute d'un support commun complet,
> les gains de +12,49 % à +40,16 % sont retirés ; le dernier tableau homogène antérieur reste
> la référence.

**Cette proposition remplace** la table de `VERITE_DOSSIER.md` § 12, les quatre gains de
`p0_donnees.json` et l'actuel lot par pli comme source de chiffres citables. Le lot en cours
reste un diagnostic utile, pas la confirmation finale.

## 1. Ce que les trois revues précédentes ont réellement produit

Le bilan est positif, mais il doit être formulé sans transformer des contrôles en preuves
plus fortes qu'eux :

- le bootstrap apparié était la bonne correction de l'ancienne « barre de bruit », mais il
  portait sur l'axe temporel, pas encore sur la pile double aveugle ;
- le Shapley par trois groupes a correctement empêché une attribution individuelle sous
  colinéarité ; son seuil est une règle d'attribution prédictive, pas une p-valeur ;
- le contrôle `X` soutient une information liée au jour sur l'axe temporel ; il n'identifie
  ni une source ni un mécanisme causal ;
- ma clé ADS mémorisée était fausse. La vérification par le `form.json` a fonctionné comme
  elle devait : elle a bloqué la mauvaise recommandation avant exécution.

Le mot **« adoptée »** reste trop fort pour la spéciation tant que la recommandation 0 et
l'intervalle de la § 2 ne passent pas. Le statut exact est « candidate intégrée à une pile
gelée, sous validation de support commun ».

### Recommandation 1 — figer une lignée de preuve, pas une liste de succès

**Test exact.** Pour chaque assertion de la § 12 à § 12 quater, ajouter une ligne de manifeste
`assertion → axe → horizon → fenêtre → variables → artefact → statut`. Les statuts possibles
sont seulement `exploratoire`, `conditionnel au corpus`, `répliqué sur sous-corpus` et
`confirmé sur bloc futur`. La spéciation ne peut dépasser `conditionnel au corpus` ici : les
blocs ont déjà été consultés.

**Seuil fixé avant lecture.** Zéro assertion sans artefact et zéro mot « établi », « adopté »
ou « robuste » associé à un statut inférieur à `répliqué sur sous-corpus`. L'étiquette
`confirmé` exige un bloc non consulté, qui n'existe pas dans ce dossier.

**Coût : 45 min.**

**Si le test échoue, écrire :**

> La lignée ne permet pas de distinguer résultats exploratoires, réplications internes et
> confirmations futures. Les assertions concernées sont retirées plutôt que promues par
> leur seule répétition dans le dossier.

**Cette proposition remplace** la liste binaire « adoptées/écartées » du contexte et les
qualificatifs sans niveau de preuve.

## 2. Intervalle des quatre chiffres et dépendance des plis

### Le `0/29` actuel ne porte pas sur la question posée

Dans [`methode_maximale.py`](../scripts/methode_maximale.py#L373-L394),
`n_plis_negatifs` compte les plis où **la configuration courante perd contre CAMS**. Il ne
compare pas `+ spéciation` à `+ tendance`. Ainsi, `0/29` signifie « la pile avec spéciation
bat CAMS dans 29 plis », pas « la spéciation améliore la pile dans 29 plis ». Le calcul
`2^-29` ne s'applique donc pas, même avant de discuter la dépendance.

Même sur les vraies différences appariées, les 29 signes ne seraient pas 29 Bernoulli
indépendants. Trois groupes de stations reviennent tous les trois mois, les mois voisins sont
corrélés et les jeux d'entraînement se recouvrent presque entièrement. À l'extrême où chaque
séquence de groupe porte un seul signe, il ne reste que trois unités : trois signes positifs
donnent une probabilité unilatérale de `1/8 = 0,125`, pas `2^-29`. Le nombre effectif ne peut
pas être identifié à partir du seul compte de signes.

Le gain total mérite lui aussi un intervalle : CAMS et la pile sont évalués sur exactement
les mêmes observations, donc leur contraste est apparié. Cet intervalle quantifie la
variabilité de l'épreuve ; il ne transforme pas une pile sélectionnée sur ce corpus en
estimation non biaisée de sa généralisation future.

### Recommandation 2 — bootstrap par cycles de rotation, apparié et pondéré

**Test exact.** Sur les sorties corrigées de la recommandation 0, ordonner les plis par mois
et utiliser le triplet de mois consécutifs comme bloc primaire : tout bloc de trois mois
contient exactement une apparition de chacun des trois groupes. Faire un bootstrap circulaire
mobile de longueur 3 mois, avec 10 000 tirages ; sensibilité obligatoire à 6 mois. À chaque
tirage, reconstruire les RMSE globales à partir des effectifs :

`RMSE_c = sqrt(sum(n_test_i × RMSE_c_i²) / sum(n_test_i))`.

Calculer deux objets appariés :

- gain total de la pile contre CAMS ;
- apport de la spéciation contre la même pile sans spéciation,
  `100 × (1 − RMSE_avec / RMSE_sans)`.

Employer la distribution centrée des tirages pour les p-valeurs unilatérales, puis Holm sur
la famille des quatre polluants. Les intervalles sont **conditionnels aux trois groupes de
stations tirés et à la pile déjà sélectionnée** : ils ne couvrent ni l'incertitude de la
recherche de variables ni une autre partition spatiale.

**Seuil fixé avant lecture.** Spéciation retenue pour un polluant si l'amélioration relative
ponctuelle est ≥ 2,0 %, borne basse IC95 > 0, p de Holm < 0,05, et même verdict avec blocs de
3 et 6 mois. Le gain total reçoit aussi un IC95, mais aucun seuil de « significativité » n'est
nécessaire pour dire que la pile bat CAMS : l'intervalle sert à quantifier, pas à sélectionner
une seconde fois.

**Coût : 1 h 30** après la passe commune ; aucun nouvel ajustement de modèle.

**Si le test échoue, écrire :**

> Sur le support commun et sous rééchantillonnage par cycles de rotation, l'apport de la
> spéciation ne franchit pas simultanément l'incertitude appariée et le seuil pratique. La
> pile reste décrite sans attribution de gain à cet étage pour ce polluant.

**Cette proposition remplace** `σ inter-plis`, `n_plis_negatifs`, tout raisonnement en
`2^-n`, et les quatre chiffres phares sans intervalle.

### Repli si seules les lignes par pli sont disponibles

Le bootstrap ci-dessus est le meilleur estimateur permis par ces agrégats. Il traite la
rotation et la dépendance temporelle, mais pas l'hétérogénéité à l'intérieur du groupe de
stations. Un bootstrap mois × 20 clusters géographiques exigerait des prédictions au grain
jour-station ; on ne peut pas recréer cette information à partir d'une RMSE de pli. Il serait
faux de prétendre que les trois groupes fournissent un intervalle spatial fiable.

## 3. Contrôle `X`, stabilité U9/U10 et décision NO2

### Audit de la permutation

Le code utilise `pd.to_datetime(j["jour"]).dt.month`. Le bloc est donc
`station × mois-de-l'année` : janvier 2024, janvier 2025 et janvier 2026 sont mélangés. Il
préserve le site et la saison moyenne, mais détruit aussi l'année, l'époque CAMS et toute
anomalie mensuelle persistante. Sur le corpus entier, `X` ne sépare donc pas parfaitement
« jour » de « version/année ».

Les exécutions U9 et U10 atténuent fortement ce défaut, car chaque fenêtre couvre environ une
année : la plupart des mois-de-l'année n'y apparaissent qu'une fois. Elles confortent le
constat dynamique sur les fenêtres où `S − T` est positif. Elles ne permettent toutefois pas
d'écrire « 12/12 » : en U10 NO2, `S − T = −0,69` point. Quand le dénominateur est négatif,
« part du gain reproduite » n'a plus de sens ; il n'y a pas de gain à répartir.

La même graine LightGBM pour `S` et `X` est le bon choix : elle rend le contraste apparié et
retire du bruit algorithmique. Faire varier les graines indépendamment affaiblirait le test.
La permutation, elle, doit rester nouvelle à chaque graine.

Les ratios négatifs ne sont pas des erreurs mathématiques. Ils signifient que le contrôle
fait moins bien que `T`. Mais un ratio est instable quand `S − T` est petit et devient
ininterprétable quand il est négatif. La différence brute `gain_X − gain_T`, avec intervalle,
doit être primaire ; la part n'est qu'un résumé secondaire lorsque `S > T`.

### Recommandation 3 — corriger le libellé du mécanisme sans ouvrir une nouvelle campagne

**Test exact.** Relire `X` uniquement sur les onze couples polluant × fenêtre où `S − T > 0`,
et publier pour chacun `S − T` ainsi que `X − T` en points. Le ratio reste secondaire. Si un
recalcul est accepté après la livraison, remplacer `.dt.month` par `.dt.to_period("M")` pour
un contrôle strict `station × AAAA-MM`, mêmes graines et mêmes lignes.

**Seuil fixé avant lecture.** Le seul seuil réellement fixé avant les résultats présents est
celui du brief : `X` reproduit moins de 50 % de l'apport. Les onze dénominateurs positifs le
franchissent ; U10 NO2 est hors domaine parce que `S − T <= 0`. `X − T` est publié sans lui
inventer un seuil rétroactif. « Source », « causal » et « les explications de régime sont
réfutées » restent interdits.

**Coût : 30 min** pour corriger tableaux et texte ; **1 h 30** supplémentaire seulement si
le contrôle `AAAA-MM` est rejoué plus tard.

**Si le test échoue, écrire :**

> La permutation conditionnelle ne sépare pas l'information du jour des effets d'année ou
> de version de façon stable. La spéciation reste un bloc prédictif ; son mécanisme est
> indéterminé.

**Cette proposition remplace** « mécanisme établi », « 12/12 » et « les explications par la
saison, le site ou le régime sont réfutées » dans `VERITE_DOSSIER.md` § 12 ter par :

> Sur l'axe temporel, casser l'association entre composition et jour retire l'essentiel de
> l'apport dans les fenêtres où cet apport est positif. Ce contrôle soutient une information
> dynamique de composition ; il n'identifie ni une source ni un effet causal.

### Décision NO2

Le seul `−0,69` point U10 ne suffit pas à déclarer une instabilité : c'est une sensibilité
sur un sous-corpus, résumée par une médiane de cinq graines, sans intervalle apparié sur des
unités de test indépendantes. En faire un veto maintenant sélectionnerait une variante après
lecture du sous-corpus le plus défavorable. Le test principal corrigé doit décider ; U10 doit
rester visible comme réserve.

Une liste de variables différente par polluant n'est pas scientifiquement gênante — les
cibles et mécanismes diffèrent déjà. Ce qui serait gênant est de l'obtenir sur les plis qui
servent ensuite à publier son score. La règle d'uniformité ne « sauve » donc pas la
spéciation ; elle évite provisoirement une nouvelle sélection dans l'échantillon.

Le caractère très attaché au site du résidu NO2 est **compatible** avec un apport dynamique
plus faible, mais il n'explique ni ne prédit quantitativement le signe U10. Comme cette
explication est mobilisée après observation du résultat, elle doit rester une hypothèse de
discussion, pas le critère de décision.

### Recommandation 4 — ne pas élaguer NO2 dans ce dossier

**Test exact.** Utiliser le résultat `core7` commun et son intervalle de la § 2. Consigner
séparément le contraste temporel U10, sans inventer de troisième découpage. Une éventuelle
pile NO2 sans spéciation est préenregistrée pour la prochaine origine future, pas renotée ici
comme nouveau produit gagnant.

**Seuil fixé avant lecture.** Citer l'apport NO2 seulement si le test double aveugle commun
passe la règle 2 % + IC + Holm. Le point U10 ne change pas ce seuil après coup : il impose la
phrase « stabilité sur la période récente indéterminée » et motive l'évaluation future déjà
préenregistrée, pas une ablation sur les données consultées.

**Coût : inclus dans la recommandation 2.**

**Si le test échoue, écrire :**

> Sur le support commun, le test principal ne franchit pas le critère de rétention. Aucun gain NO2
> n'est attribué à cet étage dans ce dossier ; une variante sans spéciation sera évaluée sur la
> prochaine origine gelée, sans sélectionner à nouveau sur les sous-corpus déjà consultés.

**Cette proposition remplace** la justification par « uniformité du modèle ». Elle conserve
la décision actuelle, mais pour la bonne raison : ne pas réutiliser le test pour sélectionner.

### Dates CAMS et causalité de version

Les dates peuvent maintenant être vérifiées sans demander aux concentrations de les révéler.
L'annonce ECMWF de U9 donne le **13 novembre 2024** pour les émissions et l'adaptation à
IFS/CAMS-Global 49r1, et le 3 décembre pour les trois nouvelles espèces
([annonce U9](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219)).
L'annonce U10 donne le **13 novembre 2025**
([annonce U10](https://forum.ecmwf.int/t/upgrade-u10-to-the-cams-european-air-quality-products/14390)).
Ces sources suffisent à nommer les époques ; un saut visible dans la série n'est pas requis.

Elles ne rendent pas causal l'écart U9/U10. Un test local linéaire de discontinuité, fenêtre
21 jours, pentes séparées, effets fixes station et placebos hebdomadaires d'octobre à
décembre pourrait détecter une marche **compatible** avec la mise en production. Il ne
séparerait pas parfaitement une rupture météorologique concomitante. Ce chantier ne change
pas la décision de pile et n'est pas à lancer avant remise.

**Ce constat remplace** la phrase « dates citées par la revue externe et non vérifiées » par
« dates de mise en production vérifiées ; effet causal de version non identifié ».

## 4. Renversement brut/anomalie et transformations exposées

L'explication « le niveau indique le type de site en double aveugle » est plausible, mais le
test proposé `climatologie + anomalie` ne la prouverait pas. À arithmétique exacte,
`brut = climatologie + anomalie` : les deux représentations portent la même information.
Pour un arbre, leur performance peut différer parce que les coupures et la régularisation ne
sont pas invariantes à cette transformation. Une égalité montrerait une équivalence de
représentation, pas le mécanisme ; une amélioration montrerait une représentation plus facile,
pas que le site est la cause.

Le contraste qui répond à l'hypothèse est l'apport de la climatologie **conditionnellement à
l'anomalie**, comparé entre axes temporel et double aveugle.

### Recommandation 5 — réserver le test `C + A` à l'après-livraison

**Test exact.** Quatre configurations sur mêmes plis : `C` seule, `A` seule, `C + A` et
`brut`. Mesurer
`I = [(C+A) − A]_double-aveugle − [(C+A) − A]_temporel` avec prédictions appariées. Pour
parler d'équivalence entre `C+A` et `brut`, utiliser un TOST et une marge de ±0,5 point ; une
égalité ponctuelle n'est pas une preuve d'équivalence.

**Seuil fixé avant lecture.** L'hypothèse « le niveau aide surtout à extrapoler vers un site
inconnu » est soutenue si `I >= 1,0` point, borne basse IC95 > 0, et `C+A` est équivalent ou
supérieur au brut. Tout autre résultat est indéterminé ou réfutatoire selon son signe.

**Coût : 2 h 30**, mais **0 h avant la remise** : ce test ne change ni le choix du bloc brut
ni l'intervalle prioritaire.

**Si le test échoue, écrire :**

> Le renversement entre axes montre que la représentation de la composition interagit avec
> la station cachée, mais le rôle du niveau climatologique n'est pas identifié. Nous
> conservons les variables brutes, qui gagnent sur l'épreuve de déploiement, sans expliquer
> ce contraste a posteriori.

**Cette proposition remplace** l'explication affirmative de la § 4 par une hypothèse future
et empêche le lancement d'un nouveau test avant le résultat principal.

### Transformations qui doivent passer la règle de couverture

La même panne d'échelle menace :

- encodages de cible, moyenne de résidu ou calibration par station/type/zone ;
- centrage, normalisation, imputation ou quantiles appris par groupe ;
- climatologies, anomalies et effets fixes soustraits ;
- moyennes glissantes, retards et historiques par station — en plus du risque de violer le
  périmètre `PARTOUT` ;
- embeddings, fréquences et catégories rares lorsqu'une catégorie du test est absente du
  train ;
- calibration conforme ou seuils appris séparément par groupe ;
- agrégats de voisinage dont les voisins admissibles changent entre train et test.

PCA, normalisation globale et imputation globale ont un autre risque — fuite si ajustées sur
tout le corpus — mais restent définies sur un groupe caché. Le garde doit donc distinguer
`fuite d'ajustement` et `référence non définie`.

### Recommandation 6 — imposer un contrat commun aux transformeurs ajustés

**Test exact.** Chaque transformeur enregistre `dimensions_ajustees`, clés couvertes, taux de
repli train/test et origine de chaque fallback. Une assertion échoue si une dimension cachée
par le protocole figure dans `dimensions_ajustees` sans référence externe disponible à
l'inférence, ou si les deux blocs n'emploient pas la même hiérarchie de fallback.

**Seuil fixé avant lecture.** Zéro fallback sur moyenne globale au-delà de 5 %, différence de
taux de fallback train/test < 2 points, et 100 % des statistiques calculées sans cible du
test. Pour `PARTOUT`, aucun historique d'observation de la station cible.

**Coût : 2 h** pour généraliser le garde existant et ajouter les tests unitaires.

**Si le test échoue, écrire :**

> La transformation n'est pas définie de la même façon sur les blocs d'apprentissage et de
> test ; sa mesure est retirée, car elle compare deux échelles plutôt que deux modèles.

**Cette proposition remplace** les contrôles ad hoc dans `anomaliser` par un contrat partagé.

## 5. Multiplicité, criblage et ordre de la pile

### 5.1 La bonne famille n'est ni 60 ni 483

Les 483 rapports sont un journal exploratoire, pas une famille d'hypothèses simultanées. Une
correction globale les traiterait à tort comme 483 affirmations publiées. À l'inverse, ne rien
corriger les quatre gains finaux parce que chaque seuil était préécrit ignore leur publication
simultanée.

Le seuil de rétention à 2 % protège contre un effet trop petit pour être utile ; il ne
contrôle aucune probabilité de faux positif et ne corrige donc pas la multiplicité.

La famille confirmatoire actuelle est : **quatre apports de spéciation dans la pile finale**.
Elle reçoit Holm. Les 12 contrôles `X` sont des réplications/sensibilités d'une même
falsification ; ils doivent être publiés ensemble, sans douze proclamations séparées. Les six
Shapley groupe × polluant sont exploratoires tant qu'ils n'ont ni intervalle ni bloc futur.

### Recommandation 7 — déclarer les familles d'inférence dans les artefacts

**Test exact.** Ajouter à chaque rapport `phase = exploration|confirmation|sensibilite`,
`famille_inference`, `hypothese_primaire` et `selection_source`. Appliquer Holm seulement aux
quatre tests de la famille finale. Une sensibilité ne crée pas une nouvelle découverte ; une
analyse exploratoire ne reçoit pas rétroactivement le mot « significatif ».

**Seuil fixé avant lecture.** 100 % des chiffres publiés avec famille et phase ; FWER 5 % sur
les quatre apports finaux ; aucune correction exigée pour les 483 fichiers non revendiqués,
mais aucun d'eux ne peut être présenté comme confirmatoire après coup.

**Coût : 1 h.**

**Si le test échoue, écrire :**

> Les expériences ont servi à explorer et sélectionner les familles de variables ; leurs
> seuils locaux ne contrôlent pas une erreur globale. Les résultats sont descriptifs et
> devront être confirmés sur une origine future gelée.

**Cette proposition remplace** toute correction mécanique sur « 60 » ou « 483 » par un
registre des familles effectivement revendiquées.

### Le biais de sélection du gain total ne peut pas être corrigé après coup

La pile a été choisie parmi une trentaine de leviers évalués sur des données qui recouvrent
l'épreuve finale. Son gain apparent est donc optimiste. Le bootstrap de la § 2 quantifie la
variation du test **conditionnellement à cette pile choisie** ; il ne rejoue pas la recherche
humaine qui l'a produite.

Le facteur ×2 à ×4 mesuré ailleurs ne peut pas être appliqué au +40,16 % : il concernait des
gains marginaux sélectionnés dans une expérience donnée, tandis que la pile contient des
effets partagés et des interactions. Il n'existe pas de coefficient honnête pour « dégonfler »
le total. Seule une sélection imbriquée entièrement reproductible ou une origine future
fermée estime ce biais. La trajectoire humaine de 483 rapports n'est pas imbriquable après
coup.

**Formulation à substituer au chiffre de généralisation :**

> La pile verrouillée réduit rétrospectivement le RMSE de X % sur l'épreuve double aveugle.
> L'intervalle décrit la variabilité de cette épreuve conditionnellement à une pile déjà
> sélectionnée ; il ne corrige pas l'optimisme dû à l'exploration antérieure des leviers.

### 5.2 Ne pas lancer un Shapley des six étages

Un Shapley à six familles répartirait le gain partagé sans dépendre d'un ordre, mais il ne
corrigerait ni le criblage, ni l'absence de test futur, ni la causalité. Avec 64 sous-ensembles
× 24 plis × 4 polluants, il consommerait l'essentiel du temps et de la fiabilité machine pour
changer une attribution, pas une décision de produit.

L'ablation de chaque famille depuis la pile complète répond déjà à la question de rétention :
« que perd le produit si je l'enlève ? ». Le chemin cumulatif répond à une autre question :
« qu'ajoute cette famille après celles qui la précèdent ? ».

Être placé en dernier ne fait **pas** de l'apport un minorant mathématique. Cette propriété
exigerait des rendements décroissants/submodulaires, qui ne sont garantis ni par LightGBM ni
par le RMSE. Synergies et effets de suppression peuvent rendre le marginal final plus grand
ou plus petit que l'apport isolé.

### Recommandation 8 — publier marginal conditionnel + ablation finale

**Test exact.** Pour chaque famille, montrer son marginal dans l'ordre préenregistré et la
perte de l'ablation depuis la pile complète. Ne retenir une conclusion de nécessité que sur
l'ablation finale ; ne pas sommer les marginaux comme des effets causaux.

**Seuil fixé avant lecture.** Une famille est « nécessaire à la pile évaluée » seulement si
son retrait dégrade d'au moins 2 % relativement à la pile, avec borne basse appariée > 0 sur
un futur bloc ou une épreuve non utilisée pour la sélectionner. Dans le dossier actuel, les
ablations restent descriptives.

**Coût : 45 min** de réécriture ; **12 à 16 h de calcul évitées** en ne lançant pas le
Shapley à six familles.

**Si le test échoue, écrire :**

> L'apport de cette famille dépend de sa position et des variables déjà présentes. Nous
> publions son marginal conditionnel et son ablation finale, sans lui attribuer une part
> intrinsèque du gain total.

**Cette proposition remplace** « minorant par construction » par « information additionnelle
conditionnelle à l'ordre préenregistré ». L'ordre versionné protège contre un réordonnancement
post-hoc ; il ne supprime ni la dépendance à l'ordre ni le biais de sélection antérieur.

## 6. Arbitrage final : la seule chose encore à faire

### Recommandation 9 — une passe commune, un intervalle, puis arrêt

**Test exact.** Fusionner les recommandations 0 et 2 en une seule exécution : `core7`, support
commun de 24 mois, deux configurations finales, quatre polluants, sorties par pli, bootstrap
circulaire 3/6 mois et Holm. Ne lancer ni RealMLP, ni `C+A`, ni Shapley à six étages, ni test
de rupture CAMS avant la remise.

**Seuil fixé avant lecture.** La passe s'arrête après quatre verdicts et quatre intervalles.
Aucun résultat ne déclenche une nouvelle variante sur le même corpus. Un échec modifie le
texte et la pile future, pas le protocole. Les données ultérieures constituent la prochaine
occasion de confirmation.

**Coût : 5 h 15**, soit 1 h 15 de garde/reprise déterministe, 2 h 30 de correction et calcul,
puis 1 h 30 de bootstrap et remplacement des livrables.

**Si le test échoue, écrire :**

> Sur une échéance et un support communs, l'ajout de la spéciation ne franchit pas notre
> critère apparié pour [polluant]. Nous retirons l'attribution de gain à cet étage et gelons
> l'analyse ; aucune variante supplémentaire n'est sélectionnée sur ce même corpus.

**Cette proposition remplace** l'option « continuer tant qu'une réserve apparaît » et le lot
actuel à 16 colonnes. Après elle, la bonne décision est effectivement d'arrêter de mesurer.

## 7. Contrainte matérielle et reprise réelle

Le résumé `.csv.partiel` est écrit après chaque configuration, mais les lignes par pli vivent
seulement en mémoire et ne sont écrites qu'à la fin
([`methode_maximale.py`](../scripts/methode_maximale.py#L330-L410)). Si la machine tombe puis
reprend, les configurations déjà présentes dans le résumé sont sautées ; leurs lignes par
pli ne sont jamais reconstruites. Le lot peut donc aboutir avec un CSV final de plis
incomplet. C'est précisément le type de panne que la reprise devait empêcher.

Deux contrôles supplémentaires contredisent le contrat matériel annoncé :

- `ajuster()` impose encore `n_jobs=8`, soit jusqu'à 32 fils pour quatre voies, et non les
  quatre voies × quatre fils du brief ;
- les doublons `+ tendance` / `− spéciation` et `+ spéciation` / `MAXIMALE`, qui portent les
  mêmes colonnes, ne sont pas identiques sur tous les plis. L'écart atteint 0,369 point sur
  O3. La graine commune ne suffit donc pas à garantir la répétabilité numérique actuelle.

La documentation LightGBM indique que `deterministic=true` stabilise les résultats CPU et
recommande de fixer aussi `force_col_wise=true` ou `force_row_wise=true` pour éviter une
instabilité numérique ([paramètres LightGBM](https://lightgbm.readthedocs.io/en/latest/Parameters.html)).

### Recommandation 10 — rendre le lot reprenable **et** déterministe

**Test exact.** Après chaque configuration, écrire atomiquement
`..._par_pli.csv.partiel`, puis marquer la configuration terminée seulement si le résumé et
les `n_plis` lignes correspondantes existent avec la même fenêtre, empreinte, code et graine.
À la reprise, toute configuration présente dans un seul des deux artefacts est rejouée. Le
nom final n'apparaît que lorsque chaque configuration attendue possède exactement 24 lignes
dans la passe commune. Fixer `n_jobs=4`, `deterministic=True` et un seul mode d'histogramme
forcé. Avant le lot, ajuster deux fois la même configuration sentinelle et comparer le hash
des prédictions pli par pli.

**Seuil fixé avant lecture.** Simuler une interruption après une configuration, reprendre,
et obtenir les mêmes fichiers qu'une exécution continue : mêmes nombres de lignes, mêmes
empreintes et mêmes valeurs à `1e-12`. Zéro configuration « reprise » sans détail par pli.

**Coût : 1 h 15**, avant la passe finale ; la mesure finale reste comprise dans le coût de la
recommandation 9.

**Si le test échoue, écrire :**

> Le lot ne reproduit pas exactement ses prédictions ou ne conserve pas tous ses plis après
> reprise. Son incertitude ne peut pas être auditée ; ses chiffres ne sont pas livrés.

**Cette proposition remplace** la reprise actuelle sur le seul résumé de configuration et le
réglage implicite à huit fils sans mode déterministe.

## 8. Lecture des différences appariées par pli

Les quatre fichiers sont complets : 16 configurations × 24 plis pour PM10, et 16 × 29 pour
les trois autres polluants. Les clés, effectifs, stations et RMSE CAMS des deux configurations
comparées coïncident sur 111/111 plis.

J'ai comparé exactement `MAXIMALE` à `− spéciation (ablation)`, reconstruit chaque RMSE global
avec `n_test × RMSE²`, puis effectué 10 000 bootstraps circulaires par blocs de trois mois.
Le bloc de six mois est la sensibilité obligatoire ; Holm porte sur les quatre apports. Les
IC portent sur l'amélioration **relative à la pile sans spéciation**, pas sur la différence
arithmétique des pourcentages du tableau.

| polluant | signes appariés | gain total avec spéciation, IC95 bloc 3 | apport relatif, IC95 bloc 3 | IC95 apport, bloc 6 | p Holm, bloc 3 |
|---|---:|---:|---:|---:|---:|
| NO2 | 26+/3− | +40,16 % [38,97 ; 41,27] | **+2,13 % [1,33 ; 2,99]** | [1,32 ; 3,07] | ≤ 0,0004 |
| O3 | 24+/5− | +18,17 % [12,28 ; 23,91] | **+2,78 % [1,35 ; 4,28]** | [1,53 ; 3,93] | ≤ 0,0004 |
| PM10 | 21+/3− | +20,71 % [15,36 ; 27,38] | **+3,46 % [1,04 ; 5,91]** | [1,51 ; 5,55] | 0,0020 |
| PM2,5 | 22+/7− | +12,49 % [7,21 ; 18,01] | **+2,73 % [1,44 ; 4,31]** | [1,76 ; 4,19] | ≤ 0,0004 |

### Verdict direct sur ces données

**Si le défaut de support n'existait pas, les quatre polluants passeraient la règle fixée en
§ 2**, NO2 compris : point ≥ 2 %, borne basse > 0, Holm < 0,05 et même décision avec blocs
de trois et six mois. Il n'y a donc aucune justification numérique pour élaguer NO2 à partir
de ce lot. Le résultat U10 doit être publié comme sensibilité discordante, pas transformé en
veto après lecture.

Les trois séquences de rotation sont toutes positives pour chaque polluant. Leurs apports
relatifs vont de 1,88 à 2,46 % pour NO2, 2,07 à 3,32 % pour O3, 2,90 à 4,08 % pour PM10 et
0,81 à 4,06 % pour PM2,5. C'est rassurant descriptivement, mais un test de signe qui réduit
les données aux trois groupes donne seulement `p = 1/8 = 0,125`. Le compte de signes n'est
donc pas la preuve ; l'intervalle par cycles, explicitement conditionnel aux groupes présents,
est l'objet utile.

### Pourquoi ce verdict reste diagnostique

Il ne peut pas encore remplacer la table publiée. Sur les cinq plis de 2023, alors que la
spéciation est absente, l'ajout du bloc produit tout de même des différences de
`−1,95 à +2,03` points pour NO2, `−4,84 à +3,26` pour O3 et `−3,40 à +5,86` pour PM2,5.
Le modèle exploite donc une configuration où disponibilité et époque sont mêlées. En outre,
les 16 colonnes incluent le nitrate tardif.

Retirer seulement les plis 2023 **après ajustement** ne répare pas le train, qui les contenait
encore. À titre diagnostique, ce filtre donne néanmoins +2,59 % NO2, +3,29 % O3, +3,46 %
PM10 et +2,81 % PM2,5 : la conclusion n'est pas portée uniquement par 2023, mais sa valeur
exacte reste contaminée. La conclusion publiable est donc : **signal apparié fort sur les
quatre polluants, chiffres en attente d'une unique réplication `core7` sur support commun**.

## 9. Texte de livraison et remplacements

Le dossier peut être livré après la seule passe des § 0, 2 et 7. Il ne doit pas attendre un
Shapley à six étages, un nouveau RealMLP, `C+A`, une rupture CAMS ou un troisième découpage
NO2.

| emplacement actuel | remplacement exigé |
|---|---|
| `VERITE_DOSSIER.md` § 12 et `p0_donnees.json` | quatre gains et IC95 issus du support commun ; horizon libellé **J+1** |
| `σ inter-plis`, `0/29`, `1/24`, `3/29` | apport relatif apparié, IC par blocs 3/6 mois et p de Holm |
| « mécanisme établi », « 12/12 » | information dynamique soutenue sur les fenêtres où `S − T > 0`, sans causalité |
| « stabilité NO2 non reproduite » | test principal favorable ou défavorable ; U10 publié séparément comme sensibilité discordante |
| « anomalie réfutée » | représentation brute retenue en double aveugle ; rôle du niveau climatologique non identifié |
| « apport minoré par construction » | marginal conditionnel à l'ordre préenregistré + ablation depuis la pile complète |
| gain présenté comme généralisation | performance rétrospective conditionnelle à une pile sélectionnée ; optimisme de criblage non corrigé |

**Texte de livraison si la passe commune confirme les quatre polluants :**

> Sur 24 plis mensuels double aveugle, la pile verrouillée réduit le RMSE de [gains avec
> IC95] par rapport à CAMS à l'échéance J+1. L'ajout des sept traceurs de composition améliore
> la pile sans spéciation de [apports relatifs avec IC95]. Les intervalles rééchantillonnent
> des cycles de trois mois, sont robustes à des blocs de six mois et restent conditionnels à
> la partition spatiale ainsi qu'à une pile sélectionnée sur ce corpus. Ils ne corrigent pas
> l'optimisme de l'exploration antérieure.

**Texte de livraison pour tout polluant qui échoue :** reprendre mot pour mot le texte de la
recommandation 9 ; ne pas lancer une variante supplémentaire sur ce corpus.

Le verdict final est donc net : **faire une seule passe corrective, puis arrêter de mesurer**.
Les données du § 8 montrent que cette passe a de bonnes chances de confirmer les quatre
apports ; elles ne dispensent pas de corriger le support qui les rend actuellement non
citables.
