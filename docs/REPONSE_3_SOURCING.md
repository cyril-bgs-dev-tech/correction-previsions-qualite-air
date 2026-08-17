# Sourcing Chine/Inde — réponse au brief

> Réponse à `docs/BRIEF_3_SOURCING_KIMI.md`. Convention de preuve, puisque le brief
> l'exige : **✅ = vérifié le 17/08/2026** (Crossref/DOI ou page source, citée) ·
> **🟡 = de mémoire, à vérifier avant citation** · je n'affirme rien au-delà.

---

## ⓪ Ce qui ne correspond à aucune de vos sections — et que je mets en tête

**Votre dichotomie PARTOUT / AUX STATIONS cache un troisième périmètre, et c'est
exactement celui où vivent les méthodes que vous me demandez.**

La contrainte fondatrice est « aucune observation *au point cible* ». Mais à l'heure
d'émission, **les ~470 stations du réseau existent et publient** — le flux E2a est
quasi temps réel, et votre règle J−2 est *volontairement plus stricte que le produit
officiel* (votre § 7). Le **champ résiduel national** — l'erreur de CAMS mesurée ce
matin partout *sauf* au point cible — est une information disponible à l'inférence qui
ne viole pas votre contrainte : ce n'est pas une observation *du point*, c'est le
*contexte* du jour. C'est le terrain du krigeage officiel (AS-CHI), et votre § 10
quinquies l'a déjà mesuré en passant : « **+ les deux** » gagne encore (−0,30 à +0,90
pt, 3/4 positif) avec la mention *« une piste, pas un résultat acquis — pas soumise au
double aveugle »*.

Pourquoi c'est en tête : **c'est la seule source d'information *fraîche* que votre
contrainte autorise**, toutes les autres pistes de ce brief (émissions, satellite,
régimes) ajoutent de l'information *statique ou lente*. Et c'est la réponse honnête à
votre question de fond (§ 4) : la pratique chinoise ne répond pas à « prédire sans
observation locale » en raffinant le modèle — elle **densifie** (micro-stations) ou elle
**fusionne** (champ résiduel krigé, satellite). Votre PARTOUT pur est un créneau que la
pratique contourne, et le vôtre le couvre déjà mieux que la chaîne officielle. Ce qui
reste sur la table est l'hybride : PARTOUT + champ résiduel du réseau, soumis au double
aveugle. Coûté ci-dessous (piste P4).

---

## § 2 — La queue de distribution et le coût d'un épisode manqué

### 2.1 Méthodes chinoises visant la queue — la réponse qui déçoit, honnêtement

Ce que la littérature chinoise aligne sur les épisodes lourds, c'est
essentiellement **du rééchantillonnage et de la perte asymétrique** (sur-échantillonner
les jours de 重污染, coût majoré sur la classe rare) — c'est-à-dire exactement la
famille que votre § 8 a déjà mesurée et écartée : *« ce qui décide est l'ordre des jours
par risque, pas la fonction de perte »*. Je n'ai rien trouvé qui contredise votre
mesure. **Ce que la Chine a et que vous n'avez pas n'est pas une perte — c'est une
structure de décision** (2.3) et une **évaluation orientée décision** (§ 5.6).

### 2.2 Existe-t-il un coût citable d'un épisode manqué ? — Non, et mieux : un cadre qui *dissout* votre faiblesse

**Aucun rapport de coût publié**, ni dans la pratique chinoise ni indienne — les paliers
d'alerte impliquent une asymétrie sans la chiffrer. Mais le cadre citable qui règle
votre problème est plus vieux et occidental :

✅ **Richardson, D. S. (2000), *Skill and relative economic value of the ECMWF ensemble
prediction system*, Q. J. R. Meteorol. Soc. 126, 649–667** (DOI 10.1002/qj.49712656313)
— le modèle **coût–perte** : un utilisateur agit si la probabilité prévue dépasse son
ratio C/L (coût de l'action / perte de l'inaction), et **la valeur d'un système est sa
courbe sur tous les C/L**. Conséquence pour votre dossier : le seuil *n'appartient pas
au modélisateur*. « Nous avons choisi » cesse d'être une faiblesse si vous présentez la
valeur **en fonction du ratio coût/perte du service** — et c'est *déjà* ce que fait
votre § 8 (rappel à budget de fausses alertes ≤ 10/20/30/40 %). Une ligne de citation
suffit : *« le point de fonctionnement appartient au service ; nous publions la courbe »*
(Richardson 2000). Ne rien calculer de neuf.

### 2.3 Votre règle des deux jours est-elle connue ? — **Oui : elle est dans le déclencheur officiel chinois**

✅ Le système d'alerte quatre couleurs (lancé 2013, révisé 2016, harmonisé entre villes)
conditionne chaque niveau à une **persistance en jours consécutifs** : jaune = pollution
lourde **3 jours de suite** (ou dangereuse le lendemain) ; orange = alternance
lourd/dangereux **3 jours** ; rouge = lourd **4 jours**, dangereux **2 jours**, ou AQI >
500 un jour. La persistance n'est pas un empiriquement vôtre — **elle est
institutionnelle là-bas aussi**, pour la même raison que chez vous : la décision (arrêts,
restrictions) ne se prend pas sur un jour isolé. Votre « gain sec » est donc
**indépendamment confirmé par la conception d'un système national** — citable comme tel
(source grand public vérifiable : l'article Wikipedia « Pollution in China », section
« Four-color alert system », qui renvoie aux textes du MEE ; pour le dossier, citer le
texte du MEE lui-même — 🟡 je n'ai pas vérifié le numéro du document).

**Ce qui reste gratuit et pas encore pris** — deux propriétés de la même structure :

1. **La gradation de l'épisode** : jaune/orange/rouge n'indexent pas seulement le niveau
   mais la **durée attendue**. Votre § 15 traite la persistance comme un filtre ; la
   structure chinoise la traite comme une *sortie* — annoncer « épisode de classe
   orange » (3 jours) plutôt qu'un booléen. C'est une présentation, pas un calcul.
2. **La cohérence régionale** (联防联控) : l'alerte se déclenche sur un **ensemble de
   villes**, pas ville par ville — voir § 5.1.

---

## § 2 bis — Vos trois faits inexpliqués

### A. Typologie ×30 sur NO₂ vs O₃ — votre mécanisme est le bon, et il y a un meilleur descripteur, **statique**

Votre lecture est la lecture standard de la littérature : l'erreur NO₂ d'un CTM à 0,1°
est dominée par la **représentativité sous-maille** du site (canyon, trafic), constante
dans le temps — d'où typologie utile *spatialement* seulement. Je n'ai pas trouvé de
quantification chinoise *de cette part-là* proprement — 🟡 — mais la réponse à « un
meilleur descripteur que l'étiquette déclarée » existe, et il échappe à votre problème
de latence parce qu'il est **statique** :

- ✅ **CAMS-REG** (Kuenen et al., 2022, *ESSD* 14, 491–519, DOI 10.5194/essd-14-491-2022)
  — l'inventaire d'émissions européen maillé (0,1° × 0,05°, par secteur : trafic
  routier, résidentiel, industrie…). La **densité d'émission NOₓ routière autour de la
  station** est ce que votre étiquette « trafic » essaie d'être. Annuel → aucune
  latence → compatible PARTOUT.
- ✅ **Climatologie TROPOMI NO₂** — vous avez écarté TROPOMI pour la *prévision*
  (latence OFFL J−3), justement ; mais une **moyenne pluriannuelle de la colonne NO₂
  troposphérique** à l'emplacement de la station est un attribut fixe, disponible à
  l'inférence, qui mesure la charge locale mieux qu'une étiquette déclarée. La
  littérature satellite-NO₂-surface est entièrement construite là-dessus (✅ ex. Ma et
  al. 2014 *ES&T* 48, 7436 ; Wei et al. 2020 *ACP* 20, 3273).

**Piste P1 formalisée plus bas.**

### B. La bande 50-100 dégradée sur l'ozone — oui, la littérature a un nom pour le régime qui la produit

Votre hypothèse est la bonne famille : la bande médiane mélange deux **régimes chimiques
de production d'ozone** — limité-NOₓ (fond régional) et limité-COV (cœurs urbains,
titration) — dont l'erreur de CAMS a des **signes opposés**. La preuve macro que ce
régime pilote l'ozone : après 2013, la Chine a réduit NOₓ sans réduire les COV, et
l'ozone urbain a **augmenté** — ✅ **Li et al. (2019), *PNAS* 116, 422–427** (DOI
10.1073/pnas.1812168116 : la baisse des PM2,5 a en outre réduit le puits de radicaux
HOₓ). C'est aussi la source du **weekend effect** (l'ozone monte le week-end en zone
limitée-COV alors que NOₓ baisse) — massivement documenté en Chine.

L'instrument publié pour diagnostiquer le régime est le **ratio HCHO/NO₂** (FNR) :
✅ **Ren & Xie (2022), *ACP* 22, 15035–15047** (DOI 10.5194/acp-22-15035-2022 — les
seuils de transition **varient d'une région chinoise à l'autre** : les valeurs ne
s'importent pas, la méthode oui) ; ✅ Vohra et al. font la même chose sur dix villes
indiennes (TROPOMI oversamplé). Et le point décisif pour vous : **CAMS produit HCHO et
NO₂** — l'indicateur de régime est calculable *depuis vos entrées*, sans satellite, sans
observation au point cible. (Nuance honnête : c'est alors le régime *vu par le modèle* —
mais votre question est précisément « quand CAMS se croit dans tel régime, son erreur
change-t-elle ? ».)

**Le test à coût nul avant tout ça** : votre calendrier est déjà dans la pile — stratifiez
la bande 50-100 par **week-end × type de station** sur `predictions.parquet`. Si la
dégradation de −12,7 % se concentre dans les cellules urbaines de week-end, l'hypothèse
de titration tient ; si elle est uniforme, elle meurt. **Piste P2 formalisée plus bas.**

### C. Un traceur particulaire qui informe un gaz — oui : c'est la notion de **masse d'air**, et sa version opérationnelle est la trajectoire

Votre mécanisme (composition = proxy du régime de masse d'air) est exactement la
lecture qu'en fait la littérature source-récepteur. La notion opérationnelle construite
*depuis les champs de modèle* (votre contrainte) existe : le **clustering de
rétro-trajectoires** (HYSPLIT sur champs météo — exécutable sur des *prévisions* IFS,
pas seulement des réanalyses) et ses dérivés PSCF/CWT — 🟡 pratique standard, omniprésente
dans les papiers chinois d'épisodes (霾过程), pas un article unique à citer. Verdict
honnête pour vous : vos sept traceurs *sont déjà* les étiquettes de masse d'air
(poussière = advection saharienne, carbone élémentaire + feux = combustion, sel marin =
flux marin) — la permutation conditionnelle l'a établi. Ce que la littérature ajoute
serait une **généalogie** (d'où vient l'air), pas une composition (ce qu'il contient) :
coût réel (pipeline HYSPLIT+IFS), bénéfice incertain au-delà de ce que les traceurs
portent déjà. **À ne pas faire en cinq jours.**

---

## § 3 — Les données

### 3.1 AOD : la question qui décide d'abord — **oui, il reste de l'information, mais pas là où vous en avez besoin**

L'existence même du champ « PM2,5 depuis satellite » est la preuve que l'AOD brut garde
de l'information après assimilation par un modèle : ✅ Wei et al. 2020 (1 km, R² = 0,89
hors station, Chine), Ma et al. 2014, Xiao et al. 2017. Le résidu vient de trois brèches
: (a) l'assimilation contraint l'**analyse** de colonne, pas la **prévision** qui s'en
éloigne ; (b) l'allocation verticale colonne→surface relève de la physique du modèle
(hauteur de couche limite) ; (c) le masquage nuageux retire l'observation *dans certains
épisodes*.

**Mais pour votre usage** (corriger l'erreur de *prévision* en France) : l'analyse CAMS
sur l'Europe est bonne, vos charges d'aérosol sont faibles (rapport signal/bruit
dégradé — votre intuition § 3.1 est juste), et vos sept traceurs couvrent déjà la
composition. Le résidu utile se concentre aux **bords** : épisodes de poussière (timing
et position du panache plus que magnitude) et brume hivernale sous nuage. **La cadence
géostationnaire change la *nature* du prédicteur pour la poussière** (détecter le début
de l'advection à l'heure près — SEVIRI IR le fait jour/nuit ; 🟡 AERUS-GEO/Carrer et al.
pour l'AOD MSG, plutôt journalier) **et seulement sa disponibilité pour le fond**.
Recommandation nette : *hors fenêtre de cinq jours* — notez l'exception poussière dans
le dossier comme prolongement, ne la testez pas maintenant.

### 3.2 Jeux connus là-bas, peu ici — le seul qui compte pour vous est **européen**

| jeu | couverture | verdict pour vous |
|---|---|---|
| ✅ **CAMS-REG** (Kuenen 2022) | Europe | **le trou d'inventaire d'émissions — comblez-le** (P1) |
| 🟡 MEIC (Tsinghua, équipe Q. Zhang) | Chine | non transposable ; méthode citable |
| ✅ CHAP / ChinaHighPM₂,₅ (Wei et al. 2020) | Chine | non transposable ; preuve que le résidu AOD existe |
| 🟡 OpenAQ | monde | observations — vous avez déjà mieux (EEA+LCSQA) |
| ✅ Climatologie TROPOMI NO₂ (statique) | monde | descripteur de site — voir § 2 bis A |

L'absence d'inventaire d'émissions dans votre pile est bien un trou — et le comblement
est *statique*, donc compatible PARTOUT et sans latence.

### 3.3 Inde et poussières — une ligne, honnêtement

L'analogue indien (poussières du Thar, brûlage de résidus du Pendjab) apporte surtout un
enseignement **de calendrier** : le brûlage est saison-piloté, donc traité par des
prédicteurs à fenêtre fixe. Vos intrusions sahariennes ne sont pas calendaires — la
transposition directe échoue ; votre traceur `dust` CAMS + GFAS couvre déjà le mécanisme.
🟡 Aucune méthode de détection spécifiquement indienne que je puisse citer avec
confiance.

---

## § 4 — La liste tranchée

| méthode | information ou réécriture ? | pourquoi, en une phrase | rang |
|---|---|---|---|
| Kolmogorov-Zurbenko | réécriture *comme correction* ; **diagnostic** à 1 h | un arbre profond apprend déjà les interactions d'échelle ; mais *décomposer votre biais par échelle* est une mesure que vous n'avez pas | 3 |
| Quantile mapping / transport | réécriture | préserve le rang par construction ; votre recalage saisonnier a déjà mesuré que le rang est tout | 5 |
| Valeurs extrêmes (POT/GPD) | réécriture *pour votre usage* | change la perte, pas l'information ; votre § 8 a tranché : c'est l'ordre qui porte la décision | 6 |
| **Prédiction conforme** | **ni l'un ni l'autre : ce n'est pas du skill, c'est le produit manquant** | intervalles sans hypothèse distributionnelle ; voir ci-dessous | 2 |
| **Hiérarchique bayésien spatial** | **information** | la covariance spatiale du résidu est la seule chose que vos features n'encodent pas | 1 |
| Ensemble d'analogues | réécriture | un GBM *est* un chercheur d'analogues pondéré ; votre GNN à +0,28 borne l'espoir | 4 |

### Retenue n° 1 — le modèle hiérarchique à effet spatial, avec sa vraie frontière

✅ **Berrocal, Gelfand & Holland (2010), *A Spatio-Temporal Downscaler for Output From
Numerical Models*, JABES 15, 176–197** (DOI 10.1007/s13253-009-0004-z) et ✅ **Fuentes &
Raftery (2005), *Biometrics* 61, 36–45** — la fusion bayésienne sortie-de-modèle +
observations, faite pour *exactement* votre question (prédire en un point non
instrumenté). L'information ajoutée est réelle (structure spatiale du résidu — votre
§ 11 mesure sa portée : 150 km sur O₃). **La frontière honnête** : le champ résiduel
exige les observations *récentes du réseau* → ce n'est pas PARTOUT au sens strict, c'est
le troisième périmètre du ⓪ ; et votre mesure GNN (+0,28 pt) suggère un plafond modeste.
Coût d'un prototype honnête (INLA/SPDE) : **au-delà des cinq jours** — piste
d'après-dossier, pas d'avant-jury.

### Retenue n° 2 — la conforme sous dépendance : ce qui tient, ce qui ne tient pas

✅ **Barber, Candès, Ramdas & Tibshirani (2021), *jackknife+*, Ann. Statist. 49(1),
486–507** (DOI 10.1214/20-AOS1965) — n'exige pas l'échangeabilité i.i.d., seulement la
*stabilité* de l'algorithme ; la variante **leave-one-out par groupe** (stations) est la
forme adaptée à votre aveugle spatial. 🟡 **Tibshirani et al., NeurIPS 2019** (conforme
sous *covariate shift*, arXiv:1904.06019 — citation de principe, à vérifier) pour le
décalage train/test. **Vérité qui fâche** : sous double aveugle station × mois, aucune
garantie de couverture exacte publiée ne s'applique telle quelle — vous publieriez des
intervalles *à garantie approximative*, à dire ainsi. Coût : ~1 jour sur vos OOF
existants. C'est le trou admis, à moindre coût — mais **ça ne change aucun score**, donc
pas prioritaire à cinq jours.

### La question de fond — « prédire en un point jamais observé », ou « on met un capteur » ?

Réponse honnête : **les deux, et le marché a tranché en votre faveur en Europe.** La
réponse dominante chinoise est la densification (micro-stations, § 5.4) plus la fusion
satellite ; mais la fusion satellite se dégrade précisément là où les charges sont
faibles — **l'Europe**. Votre approche par correction de modèle tient en France
*parce que* le signal AOD y est pauvre. Ce n'est pas un besoin que la pratique contourne
: c'est le besoin que la pratique *ne peut pas* traiter autrement à vos latitudes. Dites-
le au jury ainsi — c'est plus fort que « personne d'autre ne le fait ».

---

## § 5 — Vos six hypothèses, corrigées ou confirmées

**5.1 联防联控 — vrai, avec la définition que vous cherchez.** Les unités régionales
(京津冀 + « 2+26 » villes, plaine de Fenwei, delta du Yangtsé) sont un **compromis
administratif informé par les couloirs de transport** — le Plan d'action de 2013
désigne explicitement des « corridors de transmission » ouest-est (✅ mentionné dans la
source Wikipedia ci-dessus, renvoyant au Plan). La méthode publiée pour tracer les
frontières *depuis les données* est le clustering de trajectoires + matrices de
transport inter-villes par modèle (🟡 pratique, pas un papier unique). **Votre version à
vous, calculable demain** : cluster hiérarchique sur la **corrélation des résidus**
inter-stations — vous l'avez déjà mesurée (§ 11 : portées 75-150 km) — et des zones-
décision qui ne doivent plus rien au découpage départemental. Piste P3 ci-dessous.

**5.2 Horizon utile — partiellement vrai, et votre réponse est déjà bonne.** Les mesures
d'urgence exigent du préavis, les alertes portent sur des épisodes *de plusieurs jours*
prévus (✅ structure 2.3), et les prévisions opérationnelles chinoises vont à 72 h et
au-delà. Un « délai d'action » formalisé *dans une fonction de coût* : 🟡 pas à ma
connaissance publié. Le cadre coût-perte (Richardson 2000 ✅, § 2.2) est la bonne
formalisation : la valeur à *horizon donné* se lit sur la courbe. Votre constat « nos
leviers ne se dégradent pas avec l'échéance » est, vu d'ici, l'un de vos arguments les
plus forts — l'exact inverse du krigeage officiel qui s'effondre à J+2 (votre § 10 ter
le cite déjà).

**5.3 Le prévisionniste dans la boucle — vrai comme pratique, non vérifié comme corpus.**
Les prévisions urbaines publiées sont bien ajustées par des prévisionnistes ; que les
*deltas* soient archivés et étudiés comme cible d'apprentissage : 🟡 je crois me le
rappeler, je ne l'ai pas vérifié — ne le citez pas. **L'analogue français existe** et il
est chez vous : les déclarations de vigilance des AASQA sont la sortie *experte* — vous
les utilisez comme vérité terrain (§ 14). Leur delta contre PREV'AIR est la version
française de ce corpus ; il est petit (52 épisodes).

**5.4 Micro-stations — vrai, et la notion de proximité rejoint votre mesure.** Des
dizaines de milliers de capteurs, co-localisation tournante contre le réseau de
référence, transfert d'étalonnage conditionné à la **similarité d'usage du sol** plutôt
qu'à la distance — 🟡 sur la pratique détaillée, mais votre résultat (typologie utile en
spatial, nulle en temporel) est *exactement* ce que cette littérature prédit : la bonne
notion de voisinage est **typologique**, pas géographique. Vos deux mesures se
confirment mutuellement — c'est citable comme cohérence externe.

**5.5 一城一策 — vrai, et sa leçon vous sert.** Programme national de 2017 : une équipe
de recherche par ville des « 2+26 ». Ce qui en est ressorti (🟡 synthèses publiques du
programme) : la part locale vs régionale du PM2,5 **varie d'une ville à l'autre** — le
diagnostic est local par construction. La frontière généralisable/non-généralisable que
vous cherchez y est : les *mécanismes* se généralisent, les *partages* non. C'est
précisément votre résultat NO₂-local / O₃-régional. Pas une objection de fond à votre
approche : une confirmation que la *généralisation* ne porte pas sur les mêmes choses
selon les polluants.

**5.6 Évaluation — la métrique décisionnelle que vous n'avez pas nommée existe.** La
pratique opérationnelle chinoise évalue les prévisions en **exactitude de classe AQI**
(级别准确率 — la classe prévue égale la classe réalisée) avec une comptabilité *séparée
des jours de pollution lourde* — 🟡 la pratique est certaine, le numéro de norme non
vérifié, ne pas le citer. C'est votre « détection par classe d'indice » lue côté
décision : **évaluer par classe administrative avec compte à part pour les épisodes**
est une convention nationale chez eux — votre choix de page « Détection » a donc un
precedent institutionnel, dites-le.

**5.7 Présentation — gardez votre posture, adaptez l'ordre.** Devant un jury chinois,
l'attente dominante est : mécanisme d'abord, supériorité sur le système *opérationnel*
ensuite, limites en une phrase assumée sans développement — l'aveu étendu des échecs y
lirait comme un doute sur le résultat plutôt que comme de la rigueur. Devant un jury
indien, la couverture et le coût de déploiement dominent la méthode. 🟡 — jugement
d'expérience, pas une mesure. Pour *votre* jury : ne changez rien.

---

## § 5.8 — Les questions non cadrées

1. **Ce qui m'a surpris** : que vous évaluiez contre des *déclarations préfectorales*
   en sachant que même la vérité parfaite n'en attrape que 21/33 — sans tirer la
   conclusion complète : **la cible est administrative, pas physique**. Votre modèle
   prédit une concentration ; la procédure décide sur (niveau × persistance × étendue ×
   calendrier). Votre règle des deux jours a prouvé le gain d'aligner la *forme* ; la
   suite logique est de prédire la **décision** (ou sa probabilité) comme variable —
   pas seulement la concentration qui l'alimente. C'est le pont entre votre § 14 et
   votre § 15, et personne ne le fait.
2. **Le découpage absent ici** : le **cycle de vie de l'épisode** — déclenchement /
   accumulation / transport / dissipation (la littérature chinoise découpe tout épisode
   ainsi, 过程). Vous découpez par polluant × échéance × zone ; eux par *phase*. Votre
   règle des deux jours est déjà, sans le nommer, un prédicteur de phase
   « persistance ».
3. **La métaphore concurrente** : chez eux, deux cadrages coexistent — *corriger le
   modèle* (comme chez vous) et *reconstruire le champ* (fusion : le modèle n'est qu'une
   source parmi l'observation, le satellite, la climatologie). Le second cadrage change
   ce que « double aveugle » veut dire : on ne cache pas une station au modèle, on cache
   une *source* au champ. Votre § 13 (GEOS-CF, « seule information venue de
   l'extérieur ») est déjà écrit dans ce cadrage sans le dire.
4. **Ce qui a été essayé et a échoué** : (a) l'estimation satellite de PM2,5 **se
   dégrade précisément dans les épisodes lourds** (masquage nuageux, saturation) — le
   besoin et la donnée sont anti-corrélés (✅ c'est la limite documentée de toute la
   filière Wei et al.) ; (b) la réduction de NOₓ seul a **fait monter l'ozone urbain**
   (✅ Li et al. 2019) — l'échec de politique le plus documenté de la décennie, et la
   raison d'être de la littérature de régimes qui vous sert en § 2 bis B ; (c) les
   modèles purement profonds sur séries de stations n'ont pas déplacé les chaînes
   physico-statistiques en opérationnel — cohérent avec votre mesure « la capacité n'est
   pas le goulot ».
5. **Le débat vif** : l'attribution de la hausse d'ozone 2013-2019 (météo vs émissions
   vs puits HOₓ des aérosols — le mécanisme de Li 2019 discuté et raffiné depuis) —
   c'est la controverse où l'hypothèse « régime » est devenue mesurable, et où vos
   entrées CAMS vous placent déjà.
6. **À votre place, cinq jours** : jour 1 — P2 (coût nul, défend un chiffre exposé) ;
   jours 2-3 — P1 (le seul ajout de prédicteur que je risque) ; jour 4 — P3 *ou* la
   conforme par groupes si le jury est statisticien ; jour 5 — rien de nouveau, écrire.
   Jamais P4 dans la fenêtre : c'est un deuxième projet.

---

## Les pistes, au format demandé

## Piste — P1 · Descripteurs physiques de site (CAMS-REG + climatologie TROPOMI NO₂)
**Mécanisme** : votre typologie administrative vaut +9,7 pt sur NO₂ en spatial pur —
c'est une étiquette déclarée qui *proxie* une densité d'émission ; la densité mesurée
doit la contenir et la dépasser, station inconnue comprise.
**Source** : ✅ Kuenen et al. 2022, *ESSD* 14, 491–519 (10.5194/essd-14-491-2022) ;
✅ Wei et al. 2020, *ACP* 20, 3273 (10.5194/acp-20-3273-2020) pour la colonne-climatologie.
**Transposabilité** : totale — CAMS-REG est *l'inventaire européen*, rien ne casse.
**Coût** : ½–1 j (téléchargement ADS/ECCAD + extraction aux 476 stations + relance
double aveugle NO₂/O₃) · **Remplace** : rien ; candidat à *absorber* l'apport de la
famille `typologie` — mesurable par votre machinerie d'ablation.
**Test qui la réfute** : pile complète ± descripteurs d'émission, mêmes plis de double
aveugle. Seuil fixé à l'avance : **retenu si ≥ +0,5 pt au-delà de la pile complète** sur
NO₂ *ou* si l'ablation de `typologie` devient indolore (les deux signes disent la même
chose).
**Si le test échoue, on écrit** : « la densité d'émissions maillée n'ajoute rien à
l'étiquette administrative à l'échelle 0,1° — la part sous-maille utile est déjà
capturée par la typologie déclarée ».

## Piste — P2 · Diagnostic de régime du creux ozone 50-100 (FNR calculée de CAMS + test week-end)
**Mécanisme** : la bande 50-100 mélange fond régional (limité-NOₓ) et titration urbaine
(limité-COV) ; si CAMS porte une erreur de signe opposé dans les deux, une correction
moyenne y perd. Le week-end effect en est la signature gratuite.
**Source** : ✅ Ren & Xie 2022, *ACP* 22, 15035 (seuils FNR *régionaux* — méthode à
réétalonner, jamais à importer) ; ✅ Li et al. 2019, *PNAS* 116, 422 (pourquoi le
régime pilote l'ozone urbain).
**Transposabilité** : les *seuils* chinois ne voyagent pas (Ren & Xie le montrent entre
régions chinoises) ; la méthode si. FNR depuis CAMS = régime *vu par le modèle* — c'est
précisément la bonne question ici.
**Coût** : 1-2 h pour le test week-end × typologie sur le parquet existant ; +½ j pour
HCHO/NO₂ CAMS · **Remplace** : rien ; *explique* un chiffre publié et affiché sans
explication.
**Test qui la réfute** : stratifier la bande 50-100 par {week-end, typologie, FNR-CAMS
si dispo} ; l'hypothèse meurt si la dégradation (−12,7 %) est **uniforme** — aucun
stratificant ne la concentre.
**Si le test échoue, on écrit** : « la dégradation de la bande médiane ne se concentre
dans aucun régime accessible depuis nos entrées ; elle reste mesurée et inexpliquée » —
la formulation que votre dossier sait déjà porter.

## Piste — P3 · Zones de décision par clustering des résidus
**Mécanisme** : votre agrégation de zone est « à moitié un artefact » faute de stations
par département ; or la bonne unité est le **groupe de stations dont l'erreur de CAMS
co-varie** — mesuré chez vous (§ 11, portées 75-150 km).
**Source** : la pratique des couloirs de transport (✅ structurelle) ; la méthode
(clustering de corrélation) est standard, 🟡 sans papier unique à citer.
**Transposabilité** : sans objet — c'est *vos* données.
**Coût** : ~1 j · **Remplace** : le découpage départemental du § 15 comme unité de
décision.
**Test qui la réfute** : clusters stables entre moitiés du corpus **et** le gain
« −33 % de fausses alertes » de la règle de persistance *conservé* sur ces zones ; mort
si les clusters sont instables ou si le silence sélectif des zones creuses persiste.
**Si le test échoue, on écrit** : « les frontières de co-variation des résidus ne sont
pas stables dans le temps — l'unité de décision reste administrative, et nous disons
pourquoi ».

## Piste — P4 · PARTOUT + champ résiduel national (le troisième périmètre du ⓪)
**Mécanisme** : à l'heure d'émission, le réseau a *déjà mesuré l'erreur de CAMS du jour*
partout sauf au point cible ; interpoler ce champ résiduel ajoute l'information
**fraîche** que vos variables statiques ne peuvent pas contenir.
**Source** : ✅ Berrocal et al. 2010, *JABES* 15, 176-197 (10.1007/s13253-009-0004-z) ;
✅ Fuentes & Raftery 2005, *Biometrics* 61, 36-45 ; côté adversaire, votre § 10
quinquies (« + les deux » : −0,30 à +0,90 pt, non soumis au double aveugle).
**Transposabilité** : c'est la méthode *de* la chaîne officielle — l'adopter déplace
votre avantage de « krigeage vs apprentissage » vers « apprentissage + krigeage ».
**Coût** : **> 5 jours** (flux E2a temps réel à verrouiller, double aveugle à refaire) ·
**Remplace** : rien — crée le périmètre de production réel.
**Test qui la réfute** : double aveugle, PARTOUT + champ krigé J−1 vs PARTOUT seul ;
retenu si ≥ +1 pt sur 3 polluants sur 4.
**Si le test échoue, on écrit** : « le champ résiduel du réseau n'ajoute rien au-delà de
la pile — l'information fraîche est déjà absorbée par `tendance` ». **Ne pas lancer
cette semaine** : c'est le projet d'après, et le dire au jury est une force.

---

**La seule piste que je testerais en premier à votre place : P2.** Effet/coût imbattable
— une heure sur des données déjà là, zéro téléchargement sur une machine qui tombe — et
elle défend le seul chiffre que votre démo affiche sans pouvoir l'expliquer : si un
juré demande « pourquoi ça dégrade au milieu ? », vous aurez soit le mécanisme, soit la
phrase qui le tue proprement. P1 ensuite, parce que c'est le seul **prédicteur nouveau**
de tout ce brief qui attaque votre question la plus forte (la typologie) sans toucher à
votre contrainte fondatrice.
