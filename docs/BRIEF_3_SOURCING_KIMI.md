# Ce que la recherche chinoise et indienne sait que nous ignorons

> ## 📄 Réponse attendue : **un fichier `.md`**
>
> Ce brief n'est pas une revue de notre travail — c'est une demande de **sourcing**. Vous avez
> accès à une littérature, à des pratiques opérationnelles et à des jeux de données que je ne
> sais pas lire : la production scientifique chinoise sur la prévision de la qualité de l'air
> est, depuis 2013, la plus dense au monde, et je n'en connais que ce qui a été traduit.
>
> **Pour chaque piste, je vous demande cinq choses :**
>
> 1. **le mécanisme** — pourquoi ça devrait marcher *ici*, sur notre problème précis ;
> 2. **la source vérifiable** — auteur, année, revue ou système opérationnel. Un nom de
>    méthode sans référence m'est inutilisable ;
> 3. **la transposabilité** — ce qui casse quand on passe de la Chine du Nord ou de la plaine
>    indo-gangétique à la France métropolitaine (émissions, chimie, densité de réseau,
>    climat) ;
> 4. **le coût** en heures, et **ce que ça remplace** chez nous ;
> 5. 🔴 **le test qui la réfute** — et ce qu'on écrit si elle échoue.
>
> ⚠️ **Une piste citée de mémoire sans source vérifiable me coûte plus qu'elle ne rapporte.**
> L'autre relecteur m'a recommandé une clé d'API qui n'existait pas au catalogue ; vérifiée en
> trente secondes, elle aurait produit trois jours de données silencieusement incomplètes.
> **Si vous n'êtes pas sûr, dites-le : « je crois me souvenir » est une information utile,
> « il faut utiliser X » ne l'est pas.**
>
> ⏱️ **5 jours.** Je ne pourrai en tester **qu'une ou deux**. Classez par rapport
> effet/coût, et dites-moi laquelle vous testeriez en premier à ma place.

---

## 1. Le problème, en termes qui rendent la transposition évaluable

**Ce qu'on fait.** Les prévisions européennes **CAMS** (modèle de chimie-transport
d'ensemble, maille 0,1°) se trompent d'une façon qui se réapprend : leur erreur dépend du
lieu, de la saison et du type de station. On apprend le **résidu** `observation − CAMS` par
gradient boosting et on le retire. Quatre polluants : NO₂, O₃, PM10, PM2,5.

**La contrainte fondatrice, et elle élimine la moitié des méthodes chinoises publiées.** Le
produit principal est **`PARTOUT`** : le modèle doit corriger **en un point où il n'y a aucune
station**, donc **aucune observation n'entre à l'inférence** — pas même celle de la veille au
même endroit. Toute méthode d'assimilation, de nudging, de filtre de Kalman sur l'observation
locale, ou de fusion station-grille en temps réel **résout le problème en détruisant le
produit**.

> ⚠️ C'est le point que je vous demande de garder à l'esprit en permanence. Une très grande
> part de la littérature opérationnelle chinoise (融合分析, 数据同化) suppose un réseau dense
> et disponible en temps réel. Ce n'est pas notre cas d'usage — le nôtre est *la carte là où
> personne ne mesure*.

**Le réseau.** 476 stations en France métropolitaine, données horaires. C'est **deux ordres de
grandeur** de moins que le réseau chinois (~1 700 stations nationales + réseaux municipaux),
et la densité est très inégale.

**L'évaluation.** Double aveugle : le modèle est testé sur des **stations entièrement absentes
de son apprentissage**, pendant un **mois également absent**. C'est ce qui rend nos chiffres
comparables à un déploiement sur territoire non instrumenté.

---

## 2. 🔴 Notre pire résultat, et pourquoi je pense que c'est votre terrain

Voici la mesure la plus dure du dossier, et elle est publiée telle quelle :

> Sur les **33 épisodes PM10 réellement déclenchés** par les préfectures en Occitanie, notre
> système en attrape **3** (rappel 9,1 %). L'observation elle-même — c'est-à-dire un réseau
> parfait, sans aucune prévision — n'en attrape que **21** (63,6 %). La chaîne officielle en
> attrape **1**, comme CAMS brut.
>
> Autrement dit : **même en connaissant parfaitement les concentrations, on rate un tiers des
> épisodes déclenchés** — parce que la décision préfectorale intègre des critères que la
> concentration seule ne contient pas.

Et à l'échelle horaire nationale, sur l'ozone (7 050 000 heures-station, recalculé à
l'instant) :

| seuil | épisodes réels | rappel CAMS brut | rappel corrigé |
|---|---:|---:|---:|
| > 50 µg/m³ | 4 251 892 | 0,932 | **0,856** |
| > 100 µg/m³ | 391 737 | 0,491 | **0,586** |
| > 130 µg/m³ | 50 469 | 0,180 | **0,288** |

La correction **gagne 60 % de rappel en relatif** au seuil sévère — et laisse malgré tout
passer **plus de sept épisodes sur dix**. Elle en **perd** au seuil trivial, ce qui est
cohérent : elle amortit les extrêmes, ce qui coûte là où le seuil est franchi en permanence
et rapporte là où l'épisode est franc.

**Pourquoi je pense que la littérature chinoise a de l'avance ici précisément.** Le système
d'alerte chinois (预警) impose des conséquences administratives lourdes à un épisode manqué —
restrictions de circulation, arrêts industriels. La recherche sur la prévision des **épisodes
de pollution lourde** (重污染过程预报) y est donc dimensionnée par un coût asymétrique que la
recherche européenne n'a pas, et qui correspond exactement à notre besoin.

**Mes questions :**

1. **Quelles méthodes de correction de biais chinoises visent explicitement la queue de
   distribution** plutôt que l'erreur moyenne ? Nous optimisons un RMSE, ce qui pénalise
   structurellement les valeurs rares.
2. **Existe-t-il une fonction de coût CITABLE pour un épisode manqué ?** C'est ma question la
   plus concrète de toute cette section. Nous arbitrons aujourd'hui précision contre rappel
   avec un seuil que **nous avons choisi**, et dans un dossier de candidature « nous avons
   choisi » est une faiblesse : un jury peut demander pourquoi ce seuil-là. Si la pratique
   chinoise — ou un texte réglementaire — publie un rapport de coût entre une fausse alerte et
   un épisode manqué, **je préfère le citer que l'inventer**. Existe-t-il quelque chose de tel,
   même implicite dans la structure des paliers d'alerte ?
3. **Notre meilleure trouvaille sur ce sujet est une règle, pas un modèle** — et je voudrais
   savoir si elle est connue chez vous. Exiger que le dépassement soit prédit **deux jours
   consécutifs dans la même zone** retire **34 % des fausses alertes sans perdre un seul
   épisode** (12/12 conservés, 473 → 312 fausses). Ce n'est pas un arbitrage, c'est un gain
   sec. Et la raison est institutionnelle plutôt que statistique : **la procédure préfectorale
   exige elle-même une persistance, alors que notre règle de détection était instantanée.**
   Nous imitions la décision sans en copier la structure.
   **Quelles autres propriétés structurelles de la décision d'alerte** — durée, étendue
   spatiale minimale, nombre de stations concordantes, tendance — sont formalisées dans les
   procédures chinoises et pourraient être « gratuites » de la même façon ?

---

## 2 bis. 🔴 Trois faits mesurés que je ne sais pas expliquer

**C'est la section où votre valeur est la plus haute, et je l'ai comprise tard.** Je peux lire
des articles de méthode en anglais ; ce que je ne peux pas faire, c'est diagnostiquer un
comportement de la chimie atmosphérique à partir de trois chiffres. Un diagnostic juste vaut
mieux qu'une méthode de plus : il dit **où chercher**.

Ces trois faits sont mesurés, reproductibles, et publiés dans notre dossier sans explication.

### A. La typologie de station vaut trente fois plus sur le NO₂ que sur l'ozone

Apport de la variable « type de station » (trafic / urbain / périurbain / rural / industriel),
mesuré en retirant cette seule famille d'une pile complète, protocole double aveugle :

| | NO₂ | PM10 | O₃ | PM2,5 |
|---|---:|---:|---:|---:|
| apport de la typologie | **+9,73 pt** | +2,62 | +0,30 | +0,15 |

Et le fait qui complète celui-là : sur le NO₂, cette même variable rend **environ +8,5 points
en généralisation SPATIALE et rien du tout en généralisation TEMPORELLE**. Elle ne sert que
lorsque la station est inconnue.

**Ma lecture, et je voudrais savoir si elle est juste :** l'erreur de CAMS sur le NO₂ serait
essentiellement un **effet de sous-maille** — le modèle à 0,1° ne peut pas représenter un
canyon urbain ni une station trafic, et l'écart au type de site est constant dans le temps. Ce
serait moins vrai pour l'ozone, secondaire et régional, dont le champ varie plus lentement
dans l'espace.

**Mes questions :** est-ce le bon mécanisme ? La littérature chinoise sur le NO₂ — qui dispose
en plus des colonnes satellitaires — a-t-elle **quantifié** cette part sous-maille ? Et
surtout : **existe-t-il un descripteur de site meilleur que la typologie administrative ?**
La nôtre est une étiquette déclarée par l'exploitant du réseau, pas une mesure. Nous avons
essayé le relief, l'occupation du sol, la densité de routes, la population — sans que rien ne
remplace l'étiquette.

### B. La correction DÉGRADE l'ozone dans sa bande moyenne

Sur l'ozone, à l'échelle horaire, en découpant par bande de concentration observée :

| bande observée (µg/m³) | 0-50 | **50-100** | 130-240 |
|---|---:|---:|---:|
| gain de la correction | +29,4 % | **−12,7 %** | +21,9 % |

**La correction aide en bas, aide en haut, et nuit au milieu.** Aucun des trois autres
polluants ne montre ce creux. Nous l'affichons désormais dans notre démonstration parce que
c'est vrai, mais nous ne savons pas le lire.

**Mes questions :** cette forme en U inversé a-t-elle un nom, une explication publiée ? Mon
hypothèse est que la bande 50-100 mélange deux régimes — fond régional et production
photochimique naissante — que le modèle traite en moyenne. **La littérature chinoise sur
l'ozone est la plus fournie au monde** (l'ozone y a augmenté pendant que les particules
baissaient, ce qui a produit une décennie de travaux sur ses régimes). Y a-t-il là un
découpage par régime chimique — limité par les NOx contre limité par les COV — qui
expliquerait ce creux, et qui serait **calculable depuis nos entrées** ?

### C. Un traceur particulaire améliore la prévision d'un gaz

Nous venons d'intégrer sept traceurs de **composition particulaire** de CAMS (poussière,
carbone élémentaire, matière organique, aérosol inorganique secondaire, sel marin, feux). Ils
améliorent les quatre polluants, **y compris l'ozone (+2,36 pt) et le NO₂ (+1,30 pt)**, qui
sont des gaz.

Nous avons établi le mécanisme par une permutation conditionnelle — le gain vient de **l'écart
du jour à la composition habituelle du site**, et non d'un encodage de la saison ou du lieu.
Mais nous n'avons aucune explication **physique** de pourquoi la composition particulaire
informe sur l'erreur d'un gaz.

**Mes questions :** est-ce documenté ? Mon hypothèse est que la composition est un **proxy du
régime de masse d'air** — advection saharienne, épisode de combustion, air marin — et que
l'erreur de CAMS dépend de ce régime pour tous les polluants à la fois. Existe-t-il une
notion opérationnelle de « type de masse d'air » utilisée en Chine, et **construite depuis les
sorties de modèle plutôt que depuis des observations** ? Ce dernier point est décisif pour
nous : nous n'avons pas d'observation au point cible.

---

## 3. Les sources de données que nous n'exploitons pas — et celles qu'on ne connaît peut-être pas

**Ce que nous utilisons déjà :** CAMS (totaux + **7 traceurs de composition** intégrés
avant-hier), GEOS-CF (NASA, modèle indépendant), membres d'ensemble CAMS, feux GFAS, modèle
de terrain Copernicus GLO-30, occupation du sol IGN, typologie de station, tendance récente
du modèle, météo ERA5 (réanalyse, comme plafond) et IFS (prévision, partielle).

**Ce que nous avons regardé et écarté, avec la mesure :** TROPOMI (accessible en lecture
partielle, mais la latence OFFL impose J−3 — inutilisable en prévision), sol et géologie
(11× sous le critère de rétention), voisinage par graphe (+0,28 pt).

**Mes questions :**

1. **L'AOD satellitaire — et la question qui décide passe en premier.**
   🔴 **CAMS assimile déjà de l'AOD satellitaire.** Avant toute considération de méthode :
   **reste-t-il de l'information dans l'AOD brut une fois que le modèle l'a assimilée ?**
   Si la réponse est non, tout le reste est sans objet et vous m'économisez deux jours. Si
   c'est oui, d'où vient le résidu — résolution, latence d'assimilation, poids donné à
   l'observation dans l'analyse ?

   Si et seulement si la réponse est oui :
   - les orbites polaires (MODIS, VIIRS) donnent un à deux passages par jour ; l'équivalent
     géostationnaire de Himawari-8/9 existe au-dessus de l'Europe (**MSG/SEVIRI**, et MTG-I
     depuis peu), à cadence horaire. **La cadence change-t-elle la nature du prédicteur**, ou
     seulement sa disponibilité ?
   - les méthodes d'estimation surface-depuis-colonne (facteurs d'échelle de hauteur de couche
     limite, correction d'humidité relative) **se transposent-elles** hors de leur domaine de
     calibration — charges d'aérosol européennes bien plus faibles, donc rapport signal/bruit
     dégradé ?
2. **Y a-t-il des jeux de données publics, à couverture mondiale ou européenne, largement
   utilisés en Chine ou en Inde et peu connus en Europe ?** Je pense à des inventaires
   d'émissions, des produits de réanalyse, des indices de télédétection. Nous n'utilisons
   **aucun inventaire d'émissions** — c'est un trou que je constate sans savoir s'il est grave.
3. **L'Inde et les poussières.** Nos PM10 souffrent des intrusions sahariennes, et nous venons
   d'intégrer une variable `dust` de CAMS. La littérature indienne sur les poussières du Thar
   et sur les épisodes de brûlage de résidus agricoles traite de phénomènes analogues :
   **advection longue distance d'une source ponctuelle intense**. Y a-t-il des prédicteurs ou
   des schémas de détection transposables ?

---

## 4. Les approches mathématiques que nous n'employons pas

Voici ce que nous faisons, pour que vous ne le proposiez pas : gradient boosting sur le
résidu, moyenne de sept fonctions de perte, réglage bayésien (Optuna), bootstrap apparié par
blocs, attribution de Shapley, permutation conditionnelle pour établir un mécanisme.

**Ce que nous ne faisons pas, et dont je voudrais savoir si ça vaut le détour :**

1. **Décomposition d'échelles avant correction.** Le filtre de Kolmogorov-Zurbenko sépare une
   série en composantes ligne de base / saisonnière / court terme, et il est très employé dans
   la littérature chinoise sur l'ozone. **Corriger chaque échelle séparément a-t-il un sens
   ici ?** Notre biais est-il d'ailleurs le même à toutes les échelles — nous ne le savons pas.
2. **Correspondance de quantiles / transport optimal.** Nous corrigeons une espérance
   conditionnelle, donc nous **écrasons la variance** : nous avons mesuré que notre corrélation
   de rang est excellente (0,872) alors que l'amplitude n'est restituée qu'à **51 %**. Une
   correction qui apparie les distributions plutôt que les moyennes traiterait ça de front.
   ⚠️ Nous avons déjà testé un **recalage saisonnier d'amplitude** : il transforme le nombre de
   dépassements détectés mais **n'ajoute aucune information** (le rang ne change pas). Une
   proposition dans cette famille doit dire en quoi elle diffère.
3. **Théorie des valeurs extrêmes.** Modéliser la queue par un dépassement de seuil plutôt que
   par la même régression que le corps de la distribution. Est-ce employé en pratique
   opérationnelle, ou est-ce resté académique ?
4. **Prédiction conforme.** Nous publions des gains **sans intervalle de confiance** sur notre
   protocole principal — c'est un trou réel que je traite par ailleurs. La prédiction conforme
   donnerait des intervalles valides sans hypothèse distributionnelle. **Mais notre protocole
   viole l'échangeabilité** (stations et mois cachés simultanément). Existe-t-il une variante
   qui tienne sous ce type de dépendance ?
5. **Modèles hiérarchiques bayésiens à effets spatiaux.** C'est la réponse classique de la
   géostatistique au problème « prédire en un point non instrumenté », et nous ne l'avons pas
   essayée — nous comparons seulement au krigeage de la chaîne officielle. Est-ce que
   l'approche par apprentissage que nous avons choisie **laisse quelque chose sur la table**
   qu'un modèle spatial explicite capterait ?
6. **Ensemble d'analogues.** Chercher dans l'archive les situations prévues les plus proches
   de celle du jour, et corriger par leurs erreurs observées. ⚠️ **Attention à notre
   contrainte** : au point cible il n'y a pas d'observation. Une variante où les analogues
   viennent des *stations d'apprentissage* et non du point cible est-elle défendable, ou
   est-ce que ça revient à ce que notre modèle fait déjà ?

### 🔴 Ce que je vous demande de faire de cette liste — et ce n'est pas d'y répondre point par point

Une liste appelle une liste, et six réponses tièdes ne me serviront à rien. Je vous demande de
la **trancher**, avec un critère unique :

> **Est-ce que cette méthode apporte de l'INFORMATION que nos entrées ne contiennent pas, ou
> est-ce une RÉÉCRITURE de ce que le gradient boosting extrait déjà ?**

Ce critère n'est pas rhétorique : ce projet a mesuré une trentaine de leviers, et **la
majorité étaient des réécritures** — elles changeaient la forme du modèle sans rien ajouter,
et rendaient entre 0 et 0,4 point. Un arbre de décision suffisamment profond apprend déjà des
seuils, des interactions et des non-linéarités ; une méthode qui ne fait que les exprimer
autrement ne gagnera rien, quelle que soit son élégance.

**Le format que j'attends pour cette section :**

| méthode | information ou réécriture ? | pourquoi, en une phrase | rang |
|---|---|---|---|

Puis **les deux seules** que vous retiendriez, développées selon le format du § 7. Les quatre
autres méritent une ligne, pas une page.

**Et une question de fond que je préfère poser franchement :** y a-t-il, dans cette liste ou
ailleurs, une méthode qui traite spécifiquement le cas *« prédire une correction en un point
dont on n'a jamais rien observé »* — ou est-ce que ce problème est, chez vous aussi,
principalement résolu en **densifiant le réseau** plutôt qu'en raffinant le modèle ? Si la
réponse honnête est « on met un capteur », c'est une information précieuse : elle me dirait
que notre produit vise un besoin que la pratique contourne, et **je préfère le savoir
maintenant que devant un jury.**

---

## 5. 🔴 Les stratégies institutionnelles — la section pour laquelle je vous écris vraiment

C'est ici que je suis le plus démuni, et c'est ici que vous êtes le plus irremplaçable : **une
façon d'organiser le problème n'est presque jamais publiée en anglais.** Ce qui traverse, ce
sont les modèles et les métriques ; ce qui ne traverse pas, c'est *comment le problème a été
découpé* — et c'est souvent là que se trouve l'idée transposable.

Je pose ci-dessous **six hypothèses issues de ce que je crois savoir**. Je les écris pour que
vous puissiez les **corriger**, pas pour que vous les confirmiez poliment. Si l'une est
fausse, dites-le : une hypothèse fausse que je crois vraie me coûte plus qu'une ignorance
avouée.

### 5.1 L'échelle de décision — l'hypothèse que je crois la plus prometteuse

**Ce que je crois savoir :** la Chine a explicitement abandonné la ville comme unité de
gestion au profit d'ensembles régionaux (联防联控 — prévention et contrôle conjoints ;
Beijing-Tianjin-Hebei et les « 2+26 » villes), parce qu'un épisode ne respecte aucune limite
administrative.

**Pourquoi ça me parle :** notre unité de décision est aujourd'hui le **département**, choisi
parce que c'est l'échelon administratif de la procédure — pas parce qu'une mesure l'a désigné.
Et nous avons constaté que l'agrégation de zone est **à moitié un artefact** : elle ne tient
qu'en restreignant aux départements portant au moins trois stations. Autrement dit, notre
échelle de décision est contrainte par la densité du réseau, pas par la physique.

**Mes questions :** comment l'unité régionale est-elle **définie** — par bassin d'air
météorologique, par continuité d'émissions, par découpage administratif négocié ? Y a-t-il une
méthode publiée pour tracer ces frontières à partir des données ? Nous utilisons des
regroupements géographiques bruts, et je soupçonne qu'il existe mieux.

### 5.2 L'horizon utile — ce qui définit une « bonne » prévision

**Ce que je crois savoir :** le système d'alerte chinois (预警) déclenche des mesures
coûteuses — restrictions de circulation, arrêts de chantiers et d'usines — qui demandent un
préavis de **plusieurs jours** pour être mises en œuvre. La prévision utile n'est donc pas la
plus juste, c'est **la plus juste à l'horizon où la décision se prend**.

**Pourquoi ça me parle :** nous mesurons à J0 et J+1/J+2 parce que c'est ce que nos données
permettent, pas parce qu'une décision l'exige. Nous avons aussi mesuré que **nos leviers ne se
dégradent pas avec l'échéance** — le biais corrigé est une propriété du site, pas de la
prévision — ce qui suggère que nous pourrions aller plus loin sans perdre.

**Mes questions :** à quel horizon les décisions se prennent-elles réellement, et **la
recherche chinoise optimise-t-elle explicitement cet horizon-là** ? Y a-t-il une notion
formalisée de « délai d'action » qui entre dans la fonction de coût ?

### 5.3 Le forecaster dans la boucle — l'hypothèse qui pourrait être une source de données

**Ce que je crois savoir :** dans plusieurs systèmes opérationnels chinois, des prévisionnistes
humains **corrigent quotidiennement** la sortie des modèles avant publication, et ces
ajustements sont archivés.

**Pourquoi ça me parle :** si c'est exact, alors il existe un corpus de **corrections
expertes** — c'est-à-dire une cible d'apprentissage que personne en Europe n'exploite, et une
information sur *où le modèle se trompe de façon prévisible pour un humain*. C'est
exactement notre objet.

**Mes questions :** est-ce que ces archives existent ? Sont-elles étudiées ? A-t-on publié sur
**ce que l'expert corrige que le modèle statistique ne corrige pas** ? Et si oui, la structure
de ces corrections est-elle transposable, ou dépend-elle de connaissances locales
intransmissibles ?

### 5.4 Les micro-stations — le point où votre expérience dépasse la nôtre d'un ordre de grandeur

**Ce que je crois savoir :** la Chine a déployé des dizaines de milliers de capteurs à bas coût
(微型站) en complément du réseau de référence, avec une littérature considérable sur leur
**étalonnage** contre les stations de référence — et sur la façon de propager cet étalonnage
à des sites sans référence proche.

**Pourquoi ça me parle :** ce dernier point **est notre problème, mot pour mot.** Nous
corrigeons un modèle en un point sans instrument ; ils étalonnent un capteur en un point sans
référence. La structure mathématique est la même — transférer une correction apprise vers un
site non observé — et leur littérature est bien plus fournie.

**Mes questions :** quelles méthodes de **transfert d'étalonnage** sont établies ? Comment
décide-t-on qu'un site est « assez proche » d'un site de référence pour hériter de sa
correction — et cette notion de proximité est-elle géographique, typologique, ou apprise ?
Nous avons mesuré que la **typologie de station** rend +8,5 à +8,9 points sur le NO₂ en
généralisation spatiale et **rien** en généralisation temporelle : c'est un indice fort que
la bonne notion de voisinage n'est pas la distance.

### 5.5 « Une ville, une politique » — l'hypothèse d'un savoir local irréductible

**Ce que je crois savoir :** un programme national a affecté des équipes de recherche à des
villes individuelles pour y construire un diagnostic local plutôt qu'appliquer un modèle
national uniforme.

**Pourquoi ça me parle :** notre projet fait l'inverse — un modèle national évalué sur des
stations qu'il n'a jamais vues, précisément pour prouver qu'il **généralise**. Si la doctrine
chinoise dit que le savoir local est irréductible, c'est une objection de fond à notre
approche, et je préfère l'entendre.

**Ma question :** qu'a-t-on appris de ce programme sur **ce qui se généralise et ce qui ne se
généralise pas** ? Existe-t-il une frontière documentée entre les deux ?

### 5.6 Les cadres d'évaluation, et ce qu'ils rendent visible

1. **Comment un système est-il évalué en Chine et en Inde ?** Nous utilisons le RMSE,
   l'indicateur FAIRMODE (norme européenne) et un référentiel national français. **Y a-t-il
   des métriques standard chez vous qui rendraient visible quelque chose que les nôtres
   cachent ?** En particulier des métriques orientées **décision** plutôt qu'erreur.
2. **Quelles conventions de découpage pour la validation ?** Nous cachons station **et** mois
   simultanément, ce qui est plus dur que la pratique européenne courante. Fait-on autrement,
   et pourquoi ?
3. **Quelles erreurs un relecteur chinois cherche-t-il en premier** dans un article de
   correction de biais ? Nous avons notre liste, née de nos propres erreurs — les trois plus
   coûteuses ont été : un nom d'axe qui mentait (nous avons appelé « J+1 » du J0 pendant des
   semaines), une transformation ajustée sur un pli et indéfinie sur l'autre, et un gain
   mesuré sur un axe puis cité sur un autre. **Je voudrais la vôtre.**

### 5.7 La question de présentation, et elle est sérieuse

Un dossier de candidature français valorise la prudence et l'aveu des limites : le nôtre
publie ses échecs autant que ses réussites — **2 épisodes détectés sur 33** figure en toutes
lettres dans le document, à côté des gains.

**Est-ce une convention locale ou une vertu générale ?** Si ce même travail était présenté à
un jury chinois ou indien, qu'est-ce qui serait attendu autrement — dans l'ordre des
arguments, dans le traitement des limites, dans le rapport entre la méthode et le résultat ?

Cette question n'a aucun effet sur les scores. Elle en a un sur la façon dont je présente ce
travail, et je préfère savoir que supposer.

### 5.8 🔓 Les questions ouvertes — la partie la plus importante de cette section

**Les six hypothèses ci-dessus ont un défaut que je veux nommer : elles cadrent votre
réponse.** Elles couvrent ce que je sais ne pas savoir. Ce qui m'intéresse davantage, c'est ce
que je ne sais pas que j'ignore — et par construction je ne peux pas en faire une question
précise.

Alors voici des questions volontairement **non cadrées**. Répondez-y librement, y compris à
côté de ce que j'imaginais :

1. **Qu'est-ce qui vous a surpris en lisant ce brief ?** Quelle chose que nous faisons — ou
   que nous ne faisons pas — vous paraît étrange depuis votre contexte ? Un angle mort se voit
   mieux de l'extérieur, et c'est la question la plus rentable que je puisse vous poser.
2. **Quel est le découpage du problème qui vous semble évident et qui n'apparaît nulle part
   dans ce document ?** Nous découpons par polluant, par échéance, par périmètre géographique,
   par type de station. Y a-t-il une dimension que la pratique chinoise ou indienne considère
   comme première et que nous traitons comme secondaire — ou pas du tout ?
3. **Quelle métaphore ou quelle notion structurante organise le domaine chez vous ?** Chez
   nous, tout est pensé comme « corriger une erreur de modèle ». Ce cadrage a des conséquences
   invisibles : il fait du modèle physique la référence et de l'observation la vérité. Existe-t-il
   un autre cadrage — reconstruction d'un champ, fusion de sources, estimation d'exposition —
   qui produirait d'autres méthodes ?
4. **Qu'est-ce qui a été essayé en Chine et a ÉCHOUÉ ?** Les échecs se publient mal partout,
   et ce sont eux qui m'économiseraient le plus de temps. Quelles pistes paraissaient
   évidentes et n'ont rien donné ?
5. **Y a-t-il un débat vif, en cours, dans la communauté chinoise ou indienne** sur la
   prévision ou la correction de qualité de l'air ? Une controverse est un endroit où les
   hypothèses cachées deviennent visibles — et elle m'apprendrait plus qu'un consensus.
6. **Que feriez-vous à ma place ?** Pas « que devrait-on faire en général » : *vous*, avec
   cinq jours, ce dossier, cette contrainte, et ce que vous savez que je ne sais pas.

> ⚠️ **Ne vous limitez pas aux questions que j'ai su formuler.** Si la chose la plus utile que
> vous ayez à me dire ne correspond à aucune section de ce brief, mettez-la en tête de votre
> réponse — c'est probablement qu'elle vaut plus que ce que j'ai demandé.

---

## 6. Ce que je vous demande de NE PAS proposer

- **Une méthode qui exige une observation au point de prédiction.** C'est la contrainte
  fondatrice ; toute proposition qui la viole résout un autre problème que le nôtre.
- **Un réseau de neurones plus gros.** Nous avons mesuré : la capacité n'est pas le goulot,
  c'est le biais inductif. Un modèle triplé **dégrade** notre validation en double aveugle.
- **Des GNN.** Mesurés, +0,28 pt, écartés.
- **Une méthode sans source.** Voir l'avertissement en tête.
- **Une refonte.** Cinq jours. Je cherche **une** idée testable, pas un programme.

---

## 7. Le format qui me servirait le plus

Un fichier **`.md`**, structuré ainsi :

```markdown
## Piste — <nom>
**Mécanisme** : pourquoi ça devrait marcher sur CE problème
**Source** : auteur, année, revue / système opérationnel  ⟨ou : « de mémoire, à vérifier »⟩
**Transposabilité** : ce qui casse hors de son contexte d'origine
**Coût** : heures · **Remplace** : quoi chez nous
**Test qui la réfute** : le protocole exact, le seuil fixé avant de regarder
**Si le test échoue, on écrit** : la phrase
```

Puis, en dernière ligne : **la seule piste que vous testeriez en premier à ma place**, et
pourquoi celle-là plutôt qu'une autre.

**Et si votre réponse honnête est « rien de tout cela ne vous apportera plus qu'un point en
cinq jours », dites-le.** C'est une réponse utile, et elle m'éviterait de dépenser mes deux
derniers jours sur une piste au lieu de consolider ce qui tient.
