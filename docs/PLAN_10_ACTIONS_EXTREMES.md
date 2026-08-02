# Dix actions à plus fort levier pour mieux prévoir les extrêmes

## Réponse courte

Le principal problème n'est plus le choix de l'algorithme. Les essais du projet montrent que les gains les plus crédibles viennent de la **définition de la cible**, des **informations disponibles à l'émission**, de la **fonction de perte** et de la **séparation entre prévision de concentration et décision de dépassement**. Ajouter un réseau profond ou une nouvelle centaine de variables avant d'avoir stabilisé ces quatre éléments aurait un rendement probablement inférieur.

Les dix actions que je tenterais, dans cet ordre, sont les suivantes. Les gains indiqués comme « locaux » proviennent des fichiers du dépôt ; ce ne sont pas encore tous des gains confirmatoires parce que les protocoles d'évaluation diffèrent entre expériences.

**Statut des énoncés.** « Mesuré localement » désigne un résultat du dépôt ; « publié » désigne un résultat de la littérature citée ; les priorités, efforts et critères proposés sont mon **jugement méthodologique**, non un consensus publié.

| Rang | Action | Signal déjà observé | Portée | Effort estimé |
|---:|---|---|---|---:|
| 1 | Apprendre directement la grandeur réglementaire | O₃ : +5,80 points de gain ; NO₂ : +6,54 points | Tous les sites | 1–2 j |
| 2 | Exploiter les observations et résidus récents, avec deux produits distincts | O₃ : −0,745 µg/m³ ; NO₂ : −3,296 ; PM2,5 : −0,253 | Sites instrumentés seulement | 2–3 j |
| 3 | Ajouter la météo IFS réellement disponible à l'émission | Queue : −5,75 % O₃ ; −2,83 % NO₂ ; −6,75 % PM2,5 | Tous les sites | 2–4 j |
| 4 | Construire un compromis imbriqué entre modèle central et modèle pondéré | O₃ : queue −3,1 % → +3,1 %, gain global presque inchangé | Tous les sites | 1–2 j |
| 5 | Prédire directement la probabilité de dépassement | À 120 µg/m³ : CSI 0,407 → 0,462 ; POD 0,483 → 0,641 | Tous les sites | 2–3 j |
| 6 | Étendre l'archive et pondérer la récence / les cycles CAMS | Double aveugle actuel : seulement +1,48 %, 7 plis négatifs sur 17 | Tous les sites | 3–5 j + acquisition |
| 7 | Produire plusieurs quantiles calibrés, pas un unique quantile haut | Le q0,90 réduit la RMSE de queue de 21,9 %, mais détruit la RMSE globale | Tous les sites | 2–3 j |
| 8 | Tester un modèle à deux régimes, avec porte probabiliste | Justifié si le compromis de l'action 4 reste positif hors échantillon | Tous les sites | 3–4 j |
| 9 | Évaluer les épisodes régionaux et leur chronologie | Les scores station-jour peuvent compter plusieurs fois le même épisode | Décision AASQA | 2–4 j |
| 10 | Tester de petits blocs de prédicteurs physiques propres à chaque polluant | Les ajouts génériques déjà testés ont peu ou pas payé | Tous les sites | 3–5 j |

## Prérequis non compté : rendre les essais comparables

Avant le classement, il faut figer une expérience de référence : même cible journalière, même version de LightGBM, même jeu de variables, mêmes stations, mêmes dates et mêmes plis. La sélection doit être faite dans des plis internes ; le verdict doit venir de plis externes cachant **simultanément des stations et une période future**. Ce point est impératif : le réglage actuel gagne 29,70 % en validation spatiale, mais seulement 1,48 % en double aveugle, avec 7 plis négatifs sur 17 ([résultats locaux](../reports/double_aveugle_journalier_O3.csv)).

Il faut également annoncer deux quantités différentes :

- **Produit “sites instrumentés”** : les observations passées de la station sont autorisées, à condition d'être réellement disponibles à l'heure d'émission.
- **Produit “site sans mesure”** : aucune observation ni statistique cible propre au site de test n'est autorisée. C'est ce produit qui soutient la revendication « prévoir là où rien ne mesure ».

Tout résultat ci-dessous est à conserver seulement s'il passe le critère déjà adopté par le projet sur les prédictions appariées externes : baisse de RMSE d'au moins 0,3 µg/m³, IC95 strictement positif, sans détérioration supérieure à 0,3 µg/m³ sur la queue ni baisse du CSI. Pour les sorties probabilistes, ce filtre doit être complété par le Brier skill score, la courbe de fiabilité et l'aire sous la courbe précision-rappel.

## 1. Apprendre directement la grandeur réglementaire

**Préconisation.** Pour O₃, entraîner le modèle sur le maximum journalier des moyennes glissantes sur 8 heures ; pour NO₂, sur le maximum horaire journalier. Pour PM2,5, conserver à ce stade le modèle horaire puis agréger, car la cible est une moyenne journalière et l'essai direct est moins bon.

**Pourquoi c'est le premier levier.** Localement, le passage du modèle horaire agrégé au modèle journalier direct fait passer le gain contre CAMS de 17,50 % à 23,30 % pour O₃, soit **+5,80 points**, et de 25,56 % à 32,11 % pour NO₂, soit **+6,54 points**. Pour PM2,5, il fait au contraire baisser le gain de 27,60 % à 26,11 % ([O₃](../reports/cible_journaliere_O3.csv), [NO₂](../reports/cible_journaliere_NO2.csv), [PM2,5](../reports/cible_journaliere_PM25.csv)).

Le mécanisme est cohérent : un maximum pris après lissage horaire n'est pas équivalent à l'espérance conditionnelle du maximum. Bertrand et al. obtiennent aussi une réduction de RMSE plus forte en apprenant directement le maximum journalier d'O₃ qu'en l'extrayant de prédictions horaires ; leur grandeur est toutefois le **maximum 1 h**, pas le MDA8 du présent projet, donc leur chiffre n'est pas une comparaison directe ([Bertrand et al., 2023, *Atmospheric Chemistry and Physics*, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).

**Test exécutable.** Refaire, pour chaque horizon, les trois modèles avec les mêmes lignes et plis double aveugle : (a) horaire puis agrégation, (b) cible journalière directe, (c) moyenne simple des deux prédictions. Mesurer RMSE globale, biais du décile haut, CSI et POD/FAR aux seuils fixés avant le test.

**Décision.** Déployer la cible directe pour O₃ et NO₂ si le gain reste supérieur à 0,3 µg/m³ avec IC95 positif dans le double aveugle. L'enterrer pour un polluant si elle ne passe pas ce seuil ou dégrade le CSI. L'essai local dit déjà de ne pas la généraliser mécaniquement à PM2,5.

## 2. Exploiter les observations et résidus récents, avec deux produits distincts

**Préconisation.** Pour les stations instrumentées, ajouter l'observation la plus récente disponible, le résidu `observation − CAMS`, leurs moyennes exponentielles et écarts-types, avec âge de l'information et indicateurs de données manquantes. À J+1, le décalage doit être défini à partir de l'heure réelle d'émission ; l'essai actuel utilise J−2.

**Pourquoi c'est un levier majeur.** Le gain local attribué à l'observation passée est de **0,745 µg/m³ pour O₃**, **3,296 pour NO₂** et **0,253 pour PM2,5**, avec des IC95 positifs et une couverture de 97,7 à 98,5 % ([O₃](../reports/apport_observation_veille_O3_ic.csv), [NO₂](../reports/apport_observation_veille_NO2_ic.csv), [PM2,5](../reports/apport_observation_veille_PM25_ic.csv)). Sur O₃, le résumé détaillé indique aussi une baisse de RMSE de queue de 10,44 à 9,50 et un CSI de 0,439 à 0,484. Bertrand et al. emploient également des observations récentes dans leur MOS local, ce qui établit la pratique, mais ne mesure pas le gain marginal de ces seules variables ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)).

**Risque essentiel.** Ce gain ne vaut pas pour un lieu sans station. Une moyenne historique ou un résidu récent propre à la station de test serait une fuite dans l'estimand « site non instrumenté ». Le produit doit donc avoir deux voies explicites et un repli automatique sans observation.

**Test exécutable.** Dans les plis externes temporels, simuler l'heure d'émission et masquer toute mesure non disponible. Comparer : sans observation ; dernière observation ; résidu J−2 ; résumés 3/7 jours ; combinaison. Stratifier le résultat par fraîcheur et taux de données manquantes.

**Décision.** Retenir seulement pour le produit instrumenté si le gain double aveugle reste positif et si la performance ne s'effondre pas après 24–48 h de données manquantes. Ne jamais transférer ce chiffre à la revendication de spatialisation sans mesure.

## 3. Ajouter la météo IFS réellement disponible à l'émission

**Préconisation.** Remplacer le plafond expérimental ERA5 par les champs IFS prévus et horodatés comme disponibles à l'émission : température et point de rosée à 2 m, humidité relative calculée, composantes et vitesse du vent à 10 m, rafales, hauteur de couche limite, rayonnement solaire descendant, précipitations, nébulosité et pression. Construire des résumés correspondant à la cible : maximum, minimum, moyenne, cumul, heure du maximum et amplitude diurne.

**Signal local.** Par rapport à la base, l'IFS réduit la RMSE de queue de **5,75 % pour O₃**, **2,83 % pour NO₂** et **6,75 % pour PM2,5**. Pour O₃, il fait aussi passer le CSI de 0,324 à 0,348. Il récupère presque tout le bénéfice du plafond ERA5 ([O₃](../reports/apport_ifs_O3_tous.csv), [NO₂](../reports/apport_ifs_NO2_tous.csv), [PM2,5](../reports/apport_ifs_PM25_tous.csv)). Bertrand et al. utilisent notamment température, humidité, vent et hauteur de couche limite dans le MOS CAMS publié ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)).

**Test exécutable.** Faire des ablations imbriquées par petits blocs : thermodynamique ; vent ; couche limite ; rayonnement ; pluie/nuages. Utiliser strictement les champs du cycle IFS effectivement accessibles au moment de la prévision, et non l'analyse ou ERA5.

**Décision.** Garder le plus petit bloc dont l'IC95 du gain sur la queue est positif sans perte de CSI. Abandonner un bloc s'il ne gagne pas 0,3 µg/m³ ou s'il ne survit pas au double aveugle. Ne pas convertir automatiquement le résultat local en gain opérationnel tant que l'horodatage d'accès n'a pas été audité.

## 4. Construire un compromis imbriqué entre modèle central et modèle pondéré

**Préconisation.** Conserver un modèle MSE pour le centre et entraîner un second modèle avec pondération croissante de la concentration ou de la proximité du seuil. Combiner leurs sorties par un poids continu appris uniquement dans les plis internes. Commencer par un simple poids constant, puis tester une porte dépendant seulement de variables disponibles à l'émission : CAMS, probabilité de dépassement, IFS et saison.

**Signal local.** Sur O₃, le modèle MSE gagne 19,36 % globalement mais **perd 3,13 % dans le décile haut**. Le modèle pondéré gagne 8,54 % dans la queue mais seulement 12,42 % globalement ([comparaison des pertes](../reports/queue_O3.csv)). Une commutation exploratoire à 70 µg/m³ conserve 19,35 % de gain global et rend la queue positive à +3,10 % ([front exploratoire](../reports/front_pareto_O3.csv)). La sous-estimation des fortes concentrations par apprentissage déséquilibré et l'intérêt d'une pondération sont aussi publiés par Zhen et al. sur le MDA8 O₃ en Chine ([Zhen et al., 2025, *Atmospheric Environment*, DOI 10.1016/j.atmosenv.2024.120952](https://doi.org/10.1016/j.atmosenv.2024.120952)).

**Réserve méthodologique.** Le seuil de 70 µg/m³ a été lu sur le même front hors pli : le +3,10 % est exploratoire. De plus, une porte pilotée seulement par la prédiction MSE risque de ne jamais activer l'expert « extrême » précisément lorsque le modèle central rate un pic.

**Test exécutable.** Dans chaque pli externe, sélectionner en interne la force de pondération et le mélange. Comparer un poids constant, une transition logistique et une porte fondée sur la probabilité de dépassement. Évaluer sur toute la distribution avec RMSE, puis avec RMSE et biais de queue, CSI, Brier et précision-rappel.

**Décision.** Retenir seulement si le gain de queue reste au moins 0,3 µg/m³ avec IC95 positif et si le gain global reste à moins de 0,3 µg/m³ du modèle central. Sinon, conserver les deux sorties séparées plutôt que fabriquer un compromis instable.

## 5. Prédire directement la probabilité de dépassement

**Préconisation.** Ajouter une tête de classification `P(dépassement | informations à l'émission)` en parallèle de la régression. La concentration corrigée sert à l'information quantitative ; la probabilité calibrée sert à la décision. Le seuil de probabilité doit découler d'une fonction de coût explicite ou être sélectionné dans les plis internes, jamais sur le test.

**Signal local.** À 120 µg/m³ pour O₃, la régression seuillée obtient POD 0,483, FAR 0,281 et CSI 0,407. La classification avec seuil choisi hors du pli de station atteint POD 0,641, FAR 0,377 et CSI 0,462 ; le gain de CSI est **+0,056**, au prix de plus de fausses alertes. À 130 µg/m³, le CSI passe de 0,320 à 0,369 ([résultats locaux](../reports/classification_depassement_O3.csv)). Ces chiffres restent exploratoires tant que sélection, calibration et test ne sont pas imbriqués dans le temps et l'espace.

Les prévisions probabilistes d'événements sont une voie établie. Garaud et Mallet évaluent un ensemble européen d'O₃ par fiabilité et Brier score ; pour le seuil 120 µg/m³, leur ensemble obtient un Brier skill score de 0,327, contre 0,156 pour leur meilleur membre individuel ([Garaud et Mallet, 2011, *Journal of Geophysical Research*, DOI 10.1029/2011JD015780](https://doi.org/10.1029/2011JD015780)). Ces valeurs ne sont pas une cible directement comparable : période, réseau, modèle et définition diffèrent.

**Test exécutable.** Réentraîner dans chaque pli externe ; calibrer par régression logistique, puis isotone seulement si le nombre d'événements interne le permet ; sélectionner le seuil par coût manqué/fausse alerte préfixé. Rapporter Brier/Brier skill, diagramme de fiabilité, average precision, POD, FAR, CSI et nombre absolu d'événements.

**Décision.** Retenir si Brier skill et average precision augmentent dans le test externe, avec un gain de CSI au point de coût choisi. Une simple hausse du POD obtenue en multipliant les alertes n'est pas un succès.

## 6. Étendre l'archive et gérer explicitement la dérive du modèle amont

**Préconisation.** Ajouter en priorité les saisons d'O₃ manquantes et les épisodes rares, puis comparer trois fenêtres : courte récente, longue, et longue avec pondération exponentielle de récence. Ajouter une variable de cycle CAMS ou segmenter aux ruptures connues ; réentraîner sur fenêtre glissante.

**Pourquoi.** Le résultat le plus inquiétant du projet est le contraste entre généralisation spatiale et temporelle : +29,70 % contre +6,73 %, puis +1,48 % lorsque station et mois sont cachés ensemble ([double aveugle](../reports/double_aveugle_journalier_O3.csv)). La priorité n'est donc pas seulement d'ajouter des cas extrêmes, mais d'éviter que des années anciennes décrivent un autre système amont. Bertrand et al. montrent qu'utiliser deux étés plutôt qu'un améliore nettement leur MOS local O₃ et expliquent qu'une approche globale à apprentissage très court facilite l'adaptation aux mises à jour opérationnelles ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)). Leur résultat ne donne pas une durée universelle optimale.

**Test exécutable.** Pour chaque date de prévision externe, n'utiliser que le passé. Comparer 6, 12, 18, 24 et 36 mois lorsque disponibles, avec et sans pondération de récence, et calculer les courbes d'apprentissage séparément pour l'été O₃ et les autres polluants. Aucun sur-échantillonnage ne doit traverser une frontière d'épisode ou de pli.

**Décision.** Choisir la fenêtre la plus courte statistiquement indiscernable de la meilleure sur le test externe et plus robuste après rupture CAMS. Enterrer l'hypothèse « plus long est toujours meilleur » si la fenêtre pondérée ou courte gagne après changement de cycle.

## 7. Produire une distribution par quantiles calibrés

**Préconisation.** Entraîner au minimum les quantiles 0,10, 0,50, 0,75, 0,90 et 0,95 sur la cible journalière, corriger les croisements de quantiles, puis dériver une probabilité de franchissement du seuil. Le q0,90 ne doit pas remplacer la prévision moyenne : ce sont deux objets différents.

**Signal local.** Le modèle q0,90 réduit de 21,95 % la RMSE calculée sur le décile haut, mais sa RMSE globale est 23,13 % pire que CAMS ([résultats locaux](../reports/queue_O3.csv)). Ce n'est pas une surprise : un quantile 0,90 n'optimise pas l'erreur quadratique de la moyenne. Pérez Vasseur et Aznarte comparent dix méthodes de régression quantile pour des prévisions probabilistes de NO₂ jusqu'à 60 h ([2021, *Scientific Reports*, DOI 10.1038/s41598-021-90063-3](https://doi.org/10.1038/s41598-021-90063-3)).

**Test exécutable.** Évaluer la perte pinball de chaque quantile, la couverture, la largeur et la calibration des intervalles, ainsi qu'un score probabiliste propre agrégé. Comparer ensuite la probabilité de dépassement dérivée aux probabilités du classifieur de l'action 5.

**Décision.** Retenir si les quantiles sont calibrés hors échantillon et si la probabilité dérivée améliore Brier skill ou average precision. Abandonner si les couvertures se dégradent fortement par saison ou région, ou si le classifieur direct domine sans perte d'information utile.

## 8. Tester un modèle à deux régimes

**Préconisation.** Utiliser une porte probabiliste pour mélanger un expert « régime courant » et un expert « forte concentration ». L'expert extrême peut apprendre un résidu ou une sévérité conditionnelle, avec pondération, tandis que l'expert courant conserve la stabilité globale. La porte ne doit jamais utiliser la concentration observée du jour.

**Justification.** Les résultats locaux montrent une incompatibilité partielle entre l'optimum global et l'optimum de queue ; cela justifie un test de régime, pas encore son adoption. Des modèles de mélange ont déjà été appliqués à la prévision J+1 de pics d'O₃ à Lyon, au seuil de 180 µg/m³ ([Ambroise et Grandvalet, 2001, *Ecological Modelling*, DOI 10.1016/S0304-3800(01)00399-4](https://doi.org/10.1016/S0304-3800(01)00399-4)). Cette publication historique établit la famille de méthodes, pas un gain transférable à CAMS ou au présent réseau.

**Test exécutable.** N'ouvrir cette action que si l'action 4 est positive en test externe. Comparer : mélange lisse simple ; deux experts LightGBM ; expert de sévérité conditionnel au dépassement. Limiter le nombre de paramètres et imposer un minimum d'événements par pli.

**Décision.** Retenir seulement si le modèle bat le mélange simple de l'action 4 sur Brier/CSI et queue sans perdre en stabilité inter-plis. L'enterrer si le gain provient de deux ou trois plis riches en épisodes ou si la porte est mal calibrée.

## 9. Passer du “station-jour” à l'épisode régional

**Préconisation.** Conserver les scores station-jour pour la comparabilité LCSQA, mais ajouter une table d'événements : zone, début, fin, intensité maximale, nombre de stations ou part de population concernée. Apparier prévision et observation avec une règle temporelle et spatiale fixée avant calcul.

**Pourquoi.** Un même panache peut produire des dizaines de dépassements station-jour ; les compter comme événements indépendants surestime l'information et ne répond pas exactement à la décision régionale. Le rapport PREV'AIR publie POD, FAR, SR, FB et CSI à partir d'une table de contingence, ce qui justifie de conserver ces métriques ([LCSQA/INERIS, *Performances PREV'AIR en 2022*, 2023](https://www.lcsqa.org/fr/rapport/performances-prevair-en-2022)). Le choix de la règle d'agrégation régionale propre à ATMO Occitanie reste **à vérifier** dans le dispositif opérationnel.

**Test exécutable.** Définir avec l'utilisateur métier deux unités : station-jour et événement régional unique. Pour la seconde, mesurer détection, fausse alerte, retard d'apparition, erreur de durée et sévérité. Bootstrapper par épisode ou bloc temporel, pas par ligne.

**Décision.** Retenir cette vue si elle change une conclusion ou améliore la lisibilité décisionnelle. Si trop peu d'événements existent pour un IC informatif, publier les comptes bruts et qualifier le résultat d'exploratoire au lieu d'agréger artificiellement.

## 10. Tester des prédicteurs physiques ciblés, sans “feature soup”

**Préconisation.** Pré-enregistrer un seul petit bloc par polluant :

- O₃ : rayonnement, température maximale, hauteur de couche limite, ventilation, direction et trajectoire côtière, plus précurseurs CAMS disponibles à l'émission ;
- NO₂ : hauteur de couche limite, vent/rafales, heure et jour, proxies de trafic réellement prévisibles ;
- PM2,5 : pluie, stabilité/couche limite, composantes poussières et feux CAMS/GFAS disponibles à l'émission.

**Pourquoi ce n'est que dixième.** Les essais existants avertissent contre l'ajout opportuniste : les six membres CAMS bruts n'améliorent l'O₃ que marginalement et les résumés de dispersion le dégradent ([dispersion](../reports/apport_dispersion_O3.csv)); les copolluants CAMS réduisent légèrement la RMSE mais font baisser le CSI de 0,443 à 0,428 ([copolluants](../reports/apport_copolluants_O3.csv)). Bertrand et al. observent aussi que davantage de prédicteurs peut ne rien apporter, voire détériorer les résultats lorsque l'apprentissage est court ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)).

**Test exécutable.** Une ablation par bloc et polluant, mêmes plis et même graine, sans chercher après coup les variables individuellement favorables. Pour chaque bloc, rapporter gain global, queue, CSI, stabilité par mois et importance conditionnelle hors échantillon.

**Décision.** Garder uniquement un bloc qui passe le seuil de 0,3 µg/m³ et ne dégrade pas le CSI. Toute variable indisponible à l'émission est exclue même si elle améliore le score rétrospectif.

## Mesures de succès à utiliser

Un unique « RMSE du décile haut » ne suffit pas. Le tableau de bord minimal devrait contenir :

1. **Concentration** : RMSE et biais sur toute la distribution ; RMSE, MAE et biais au-dessus d'un seuil fixe ; courbe d'erreur par tranches de concentration.
2. **Événement** : nombres absolus de bonnes détections, fausses alertes et manqués ; POD, FAR, CSI ; précision-rappel et Brier skill.
3. **Calibration** : diagramme de fiabilité et calibration dans la plage de probabilités qui commande réellement une action.
4. **Robustesse** : distribution des gains par station, mois, région, type de station et cycle CAMS ; nombre de plis négatifs.
5. **Opérationnel** : résultat séparé à J+1, J+2 et J+3, avec uniquement les données présentes à l'heure réelle d'émission.

Il faut éviter de sélectionner seulement les jours effectivement extrêmes puis de juger une prévision probabiliste avec un score conventionnel : cela crée le « forecaster's dilemma ». L'évaluation doit rester propre sur l'ensemble des cas, puis ajouter des scores orientés vers l'extrême ([Lerch et al., 2017, *Statistical Science*, DOI 10.1214/16-STS588](https://doi.org/10.1214/16-STS588)).

## Ordre d'exécution recommandé

### Avant le gel des calculs

1. Figer le protocole commun et réserver les plis externes.
2. Confirmer la cible journalière directe.
3. Confirmer les observations récentes sur la voie instrumentée.
4. Ajouter l'IFS opérationnel.
5. Refaire, de façon imbriquée, le mélange pondéré et le classifieur de dépassement.

Ces cinq tests exploitent des leviers déjà positifs localement. Ils ont plus de chances de changer le dossier que les actions 6 à 10, qui demandent soit de nouvelles données, soit une définition métier, soit davantage d'événements.

### Ensuite, si le temps et les données le permettent

Étendre l'archive et tester la récence avant d'ajouter de la complexité ; produire ensuite les quantiles. Le modèle à deux régimes ne vient qu'après confirmation du mélange simple. L'évaluation régionale doit être conçue avec l'AASQA. Les nouveaux prédicteurs physiques arrivent en dernier et par blocs pré-enregistrés.

## Ce que je ne tenterais pas maintenant

- Un GNN, un transformeur ou un autre réseau profond : le verrou mesuré porte sur la cible, le temps et les événements rares, pas sur la capacité de l'algorithme.
- Une optimisation hyperparamétrique exhaustive : elle risque d'exploiter les mêmes plis alors que le double aveugle reste fragile.
- TROPOMI OFFL décalé de plusieurs jours : les essais actuels ne montrent pas de signal robuste. L'hypothèse que l'information soit en partie redondante avec les assimilations de CAMS reste **à vérifier** produit par produit et cycle par cycle.
- Une dispersion d'ensemble CAMS brute comme priorité : le gain local est trop faible.
- Une calibration isotone seule présentée comme amélioration du modèle : elle déplace le point POD/FAR mais ne crée pas nécessairement de discrimination.
- Une sélection de variables après lecture répétée du même test : elle transforme le test en validation et gonfle le résultat.

## Conclusion

Mon pari à plus fort rendement est un système à **deux sorties** et **deux périmètres** : une concentration journalière apprise directement plus une probabilité calibrée de dépassement ; une version avec observations récentes pour les stations instrumentées et une version sans observation pour les autres sites. Le socle commun serait enrichi par l'IFS opérationnel. Pour les extrêmes, je testerais d'abord un mélange imbriqué entre objectif central et objectif pondéré, avant tout modèle plus complexe.

Le chiffre le plus prometteur à confirmer est le passage local de la queue O₃ de −3,1 % à +3,1 % sans perte globale apparente. Le chiffre le plus important à ne pas masquer est le **+1,48 % seulement en double aveugle** : toute amélioration qui ne survit pas à cette épreuve est une amélioration de laboratoire, pas encore une amélioration de la prévision opérationnelle.

## Sources publiées citées

- J.-M. Bertrand, F. Meleux, A. Ung, G. Descombes et A. Colette (2023), « Technical note: Improving the European air quality forecast of the Copernicus Atmosphere Monitoring Service using machine learning techniques », *Atmospheric Chemistry and Physics*, 23, 5317–5333. [DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).
- H. Petetin et al. (2022), « Model output statistics (MOS) applied to Copernicus Atmospheric Monitoring Service (CAMS) O₃ forecasts: trade-offs between continuous and categorical skill scores », *Atmospheric Chemistry and Physics*, 22, 11603–11630. [DOI 10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).
- L. Zhen et al. (2025), « Data imbalance causes underestimation of high ozone pollution in machine learning models: A weighted support vector regression solution », *Atmospheric Environment*, 343, 120952. [DOI 10.1016/j.atmosenv.2024.120952](https://doi.org/10.1016/j.atmosenv.2024.120952).
- S. Pérez Vasseur et J. L. Aznarte (2021), « Comparing quantile regression methods for probabilistic forecasting of NO₂ pollution levels », *Scientific Reports*, 11, 11592. [DOI 10.1038/s41598-021-90063-3](https://doi.org/10.1038/s41598-021-90063-3).
- D. Garaud et V. Mallet (2011), « Automatic calibration of an ensemble for uncertainty estimation and probabilistic forecast: Application to air quality », *Journal of Geophysical Research: Atmospheres*, 116. [DOI 10.1029/2011JD015780](https://doi.org/10.1029/2011JD015780).
- C. Ambroise et Y. Grandvalet (2001), « Prediction of ozone peaks by mixture models », *Ecological Modelling*, 145, 275–289. [DOI 10.1016/S0304-3800(01)00399-4](https://doi.org/10.1016/S0304-3800(01)00399-4).
- S. Lerch, T. L. Thorarinsdottir, F. Ravazzolo et T. Gneiting (2017), « Forecaster's Dilemma: Extreme Events and Forecast Evaluation », *Statistical Science*, 32, 106–127. [DOI 10.1214/16-STS588](https://doi.org/10.1214/16-STS588).
- B. Raux, INERIS/LCSQA (2023), « Performances PREV'AIR en 2022 ». [Page et rapport LCSQA](https://www.lcsqa.org/fr/rapport/performances-prevair-en-2022).
