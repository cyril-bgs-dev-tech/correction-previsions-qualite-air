# Q1 — Hypothèses implicites

Les amplitudes ci-dessous sont des ordres de grandeur de triage **[jugement de praticien]**, pas des effets publiés transférables au projet.

| Rang | Hypothèse implicite | Pourquoi elle peut être fausse | Effet attendu | Symptôme observable dans les données |
|---:|---|---|---|---|
| 1 | Une observation ponctuelle et la maille CAMS représentent le même objet | La station voit une rue, une clairière, une vallée ou un panache ; CAMS représente un volume d’environ 0,1°. Le modèle apprend donc à la fois le biais CAMS et l’**erreur de représentativité** du site [publié, S1]. | **Fort : 5–30 µg/m³ localement**, surtout NO₂ et faibles O₃ [jugement] | Le résidu garde le même signe par station, dépend fortement de la distance à la route et du secteur de vent, et varie davantage entre stations d’une même maille CAMS qu’entre mailles voisines |
| 2 | Le résidu futur est suffisamment décrit sans état récent du système | Ni le biais CAMS de la veille, ni la concentration observée récente, ni la persistance d’un épisode n’entrent dans le modèle. Le MOS officiel CAMS emploie des observations de fond comme prédicteurs [documentation officielle, S2]. | **Fort : 3–15 µg/m³** et potentiellement davantage pendant les transitions [jugement] | Autocorrélation positive des résidus à 1, 6, 24 et 48 h ; le résidu de J−1 prédit encore l’erreur après contrôle des 52 variables |
| 3 | Une correction additive sous perte quadratique convient sur toute l’échelle | Le LightGBM apprend surtout une moyenne conditionnelle ; les erreurs sont vraisemblablement hétéroscédastiques et parfois multiplicatives. Les cas centraux dominent les très faibles valeurs et les dépassements. | **Moyen à fort : 3–15 µg/m³ dans les queues** [jugement] | Forme en éventail de `résidu_corrigé` contre CAMS, biais de signe opposé dans les déciles extrêmes, couverture des intervalles qui chute aux faibles et fortes concentrations |
| 4 | Les lignes station–heure/jour peuvent être traitées comme indépendantes | Les erreurs partagent dates, masses d’air et stations. Le score moyen peut rester correct, mais les incertitudes deviennent trop étroites. Le projet a déjà mesuré un élargissement d’environ 1,7× avec un bootstrap spatio-temporel. | **Faible sur RMSE, fort sur la certitude statistique** | L’IC s’élargit nettement en bloquant simultanément stations et dates ; la taille d’échantillon effective est bien inférieure au nombre de lignes |
| 5 | Les contrastes de paysage sont fixes pendant 17 mois | La géométrie l’est presque, mais son **activité** ne l’est pas : trafic, chauffage, épandage, végétation, humidité du sol, travaux et usage industriel évoluent. Une longueur de route ou une forêt statique n’est qu’une capacité d’émettre ou de déposer. | **Moyen : 2–15 µg/m³ ; fort certains jours** [jugement] | Interaction paysage×saison ou paysage×météo beaucoup plus forte que l’effet principal ; signe de SHAP qui change entre hiver/été ou jours ouvrés/vacances |
| 6 | ERA5 décrit l’information disponible à l’émission | ERA5 est une réanalyse ; elle incorpore des observations futures par rapport à l’heure de prévision. Le modèle est un *perfect-prognosis* rétrospectif, non une chaîne opérationnelle. | **Inconnu**, probablement plus visible aux épisodes et J+2/J+3 | Le score baisse lorsque les champs ERA5 sont remplacés par des prévisions archivées ; l’écart croît avec l’horizon et lors des erreurs de vent/couche limite |
| 7 | La station fournit une vérité sans erreur ni changement de support | Maintenance, changement d’instrument, données provisoires, dérive et règles de validation ajoutent une erreur de cible. | **Faible à moyen : 1–5 µg/m³**, parfois rupture franche [jugement] | Sauts de résidu propres à une station sans changement des voisines ; séries plates, valeurs répétées, changement simultané de taux de données manquantes |
| 8 | Écrêter à zéro est neutre | L’écrêtage crée une masse ponctuelle à zéro et rend les probabilités/quantiles incohérents près de la borne. Mais le projet n’écrête que 0,043 % des lignes : ce n’est pas une explication importante du RMSE global. | **Négligeable globalement ; <0,1 % des cas mesurés** | Toutes les erreurs imputables à l’écrêtage sont concentrées dans les prédictions pré-écrêtage négatives ; aucun effet hors de ce sous-ensemble |
| 9 | Les 476 stations échantillonnent la France comme un plan aléatoire | Le réseau est conçu pour la surveillance, avec surreprésentation des zones peuplées ou à risque. « Station inconnue » signifie nouvelle station du même réseau, pas lieu quelconque. | **Fort pour la portée géographique**, RMSE interne inchangée | Les distances au domaine d’apprentissage et les covariables des zones sans station dépassent les quantiles vus ; les performances chutent par région entière cachée |

**Sources.**

- **[S1, publié]** Henne et al. (2010), hétérogénéité de surface et représentativité des stations, *Atmospheric Chemistry and Physics*, DOI : [10.5194/acp-10-3561-2010](https://doi.org/10.5194/acp-10-3561-2010). Voir aussi Piersanti et al. (2015), DOI : [10.1016/j.apr.2015.04.005](https://doi.org/10.1016/j.apr.2015.04.005).
- **[S2, documentation officielle]** CAMS, [prévisions européennes optimisées aux stations](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts-optimised-at-observation-sites?tab=overview) : le MOS combine prévision CAMS, météo ECMWF et observations de fond.
- **[Publié]** Roberts et al. (2017), nécessité de validations adaptées aux dépendances spatiales et temporelles, *Ecography*, DOI : [10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881).

# Q2 — Les cinq énigmes

## E1 — Retirer la forêt améliore légèrement l’ozone

**Explication la plus probable.** « Forêt » mélange des mécanismes de signes opposés. Elle peut fournir des précurseurs biogéniques lorsque lumière, température, état foliaire et régime NOₓ le permettent, mais elle est aussi un puits d’ozone par dépôt stomatique et non stomatique. Humidité, rosée, pluie, turbulence, LAI et sécheresse modulent ce puits [publié, S3]. Un pourcentage forestier statique sans interaction chimique ni phénologique ajoute donc un proxy ambigu ; CAMS représente déjà une partie de ces mécanismes, ce qui favorise aussi le double comptage.

- **Effet attendu : faible globalement**, cohérent avec le −1,0 % observé ; **5–15 µg/m³ localement** dans certains régimes [jugement].
- **Symptôme décisif :** l’effet de la forêt change de signe. Résidu positif les journées chaudes, ensoleillées, feuillées et riches en NOₓ ; résidu négatif la nuit ou lorsque la canopée est humide. Un SHAP de forêt stable et monotone réfuterait cette explication.
- **Variable manquante :** LAI/FCover dynamique, humidité du sol/canopée et copolluants CAMS NOₓ/COV ou indicateur de régime chimique.

## E2 — Le type officiel de station n’ajoute rien

**Explication la plus probable.** Le type est une classe administrative grossière appliquée à une réalité continue. Deux stations « urbaines de fond » peuvent avoir des géométries, vents dominants, hauteurs de rue et sources très différentes. Les variables paysagères reconstruisent ces gradients sans imposer de frontière catégorielle. La littérature constate que les catégories de sites ne sont pas appliquées uniformément et décrivent moins bien la géométrie de représentativité [publié, S1].

- **Effet attendu : nul à faible après paysage**, exactement ce qui est observé.
- **Symptôme décisif :** variance des résidus **intra-type** supérieure à la variance entre moyennes de types ; forte prédictibilité du type à partir du paysage, mais aucune information conditionnelle résiduelle.
- **Test contraire :** si le type devient utile quand tout le paysage est retiré, il n’est pas mauvais ; il est simplement redondant.

## E3 — Terrain et interpolation du résidu se dégradent ensemble

**Explication la plus probable.** Le modèle de terrain a déjà absorbé la composante spatiale prévisible ; le résidu restant contient surtout un effet date, du bruit de mesure et une covariance météo non stationnaire. Un krigeage isotrope ou moyenné sur 17 mois réinjecte alors du bruit. Les hybrides RF–krigeage ne dominent pas systématiquement leurs composants [publié, S4]. Une seconde possibilité, plus grave, est que le variogramme ou les résidus interpolés soient ajustés en échantillon plutôt que sur résidus strictement hors pli.

- **Effet attendu : les 3 points déjà mesurés** ; davantage aux stations isolées [jugement].
- **Symptômes :** Moran’s I proche de zéro après le modèle terrain ; portée/sill du variogramme instables par mois ; dégradation croissante avec la distance à la station d’apprentissage la plus proche ; poids de krigeage négatifs ou dominés par des sites sous une autre masse d’air.
- **Variable/formulation manquante :** covariance **anisotrope orientée par le vent** et variable dans le temps, ou effet spatial conjoint dans un seul modèle plutôt qu’une somme séquentielle.
- **Falsification prioritaire :** kriger uniquement les résidus OOF, ajuster le variogramme dans le pli d’entraînement, puis tracer le gain par distance et régime de vent.

## E4 — Cible directe utile pour le maximum, nuisible pour la moyenne

**Explication la plus probable.** La moyenne est linéaire : moyenner 24 prévisions horaires annule une partie des erreurs de signe opposé et exploite beaucoup plus d’exemples d’apprentissage. Le maximum est un opérateur non linéaire, sensible à l’atténuation du pic et au décalage de son heure ; optimiser toutes les heures sous MSE ne cible pas l’ordre statistique extrême. L’apprentissage direct du maximum peut donc récupérer amplitude et classement, tandis que l’apprentissage direct de la moyenne jette de l’information intrajournalière.

- **Effet attendu : 5–6 points sur les maxima et petite perte sur les moyennes**, conforme à la mesure du projet mais non universel.
- **Symptômes :** pour la moyenne, covariance négative entre erreurs horaires qui s’annulent ; pour le maximum, pic horaire trop aplati ou décalé dans le modèle horaire. Le bénéfice direct doit croître avec l’amplitude intrajournalière et l’erreur de phase.
- **Référence :** Bertrand et al. trouvent également une asymétrie entre cibles horaires et journalières, mais pas nécessairement dans le même sens ; cela réfute toute loi universelle [publié], DOI : [10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

## E5 — Échec massif sur les très faibles concentrations d’ozone

**Explication la plus probable.** Ce n’est pas seulement « la titration nocturne », déjà identifiée : c’est l’impossibilité du modèle à savoir **où et quand elle domine**, faute de NO/NO₂, d’état récent et de structure verticale locale. Une maille CAMS conserve un fond régional alors que la station peut être enfermée sous une couche stable très mince, au contact d’un puits local ou d’une canopée humide. La régression sous MSE ramène ensuite ces cas rares vers le centre.

- **Effet attendu : très fort dans le décile bas**, ici +28 µg/m³ brut et +16 corrigé ; effet faible sur le RMSE global si ces cas sont rares.
- **Symptôme chimique :** biais positif maximal lorsque NO/NO₂ observé ou CAMS est élevé, vent faible et rayonnement nul ; dépendance au rapport O₃/NO₂ plus forte qu’au type de station.
- **Symptôme de couche limite/support :** concentration faible propre aux stations de vallée, trafic ou sous couvert, tandis que les stations voisines/background restent plus hautes ; erreurs maximales sous inversion, brouillard/rosée et faible mélange. Les modèles de couche limite peuvent mal représenter profil vertical et couche résiduelle [publié, S5].
- **Symptôme statistique :** courbe de calibration qui plafonne — toutes les prévisions corrigées restent proches d’un plancher supérieur à 15,9 — et très peu de faibles valeurs dans l’apprentissage de chaque pli.
- **Variables manquantes :** NO et NO₂ prévus/récents, gradient vertical de température, stabilité, couche résiduelle/ceilomètre, brouillard et humidité de canopée.

**Sources complémentaires.**

- **[S3, publié]** Zhang et al. (2002), dépôt sec d’ozone et canopées humides, *Atmospheric Environment*, DOI : [10.1016/S1352-2310(02)00567-8](https://doi.org/10.1016/S1352-2310(02)00567-8).
- **[S4, publié]** Fox, Ver Hoef et Olsen (2020), comparaison RF, modèles spatiaux et RF–krigeage, *PLOS ONE*, DOI : [10.1371/journal.pone.0229509](https://doi.org/10.1371/journal.pone.0229509).
- **[S5, publié]** Liu et al. (2023), hauteur de couche limite et profil vertical d’ozone, *Geoscientific Model Development*, DOI : [10.5194/gmd-16-5493-2023](https://doi.org/10.5194/gmd-16-5493-2023).

# Q3 — Processus structurellement invisibles

Les plages sont des **[jugements de praticien]** destinés à classer les essais. Elles ne doivent pas être citées comme résultats de littérature.

| Rang | Processus invisible | Ampleur attendue | Symptôme à rechercher |
|---:|---|---:|---|
| 1 | **Mémoire récente de l’atmosphère et du biais modèle** : concentration et résidu aux heures/jours précédents | **5–20 µg/m³** ; plus en épisode | ACF des résidus significative à 1–48 h ; un simple `résidu J−1` améliore fortement le modèle à variables identiques |
| 2 | **Régime chimique multivarié** : NO, NO₂, O₃, COV et aérosols ne sont pas des problèmes séparés | **5–30 µg/m³** pour O₃/NO₂ dans les régimes extrêmes | Biais conditionné par CAMS NO/NO₂, rapport NO₂/O₃, température et rayonnement ; signe différent en régimes NOₓ-saturé et NOₓ-limité |
| 3 | **Émissions réellement actives**, par opposition aux capacités statiques : congestion, chauffage, épandage, démarrage industriel | **3–20 µg/m³**, pointes supérieures près des sources | Résidu par secteur de vent et heure ouvrée ; ruptures jours fériés/vacances/froid ; pics communs à une zone sans équivalent dans CAMS |
| 4 | **Structure verticale et stabilité locale** : inversion, couche résiduelle, jet de basse couche, pente/valley flow, brouillard bas | **5–25 µg/m³** | Erreur groupée la nuit et au lever du jour, vent ERA5 faible, grand gradient thermique vertical ; stations de vallée divergent des stations de plateau |
| 5 | **État dynamique de la végétation et des surfaces** : LAI, sécheresse, stomates, rosée, sol humide | **2–10 µg/m³** pour O₃ ; effet épisodique | Interaction forêt×LAI×rayonnement×humidité ; signe saisonnier du résidu ; jours de rosée distincts des jours simplement humides |
| 6 | **Direction et incertitude du transport**, pas seulement le vent moyen : erreurs de trajectoire et dispersion inter-membres | **3–20 µg/m³** lors des fronts/panaches | Les membres CAMS encadrent l’observation mais la médiane se trompe ; erreur forte quand la direction prévue est proche d’une frontière source/non-source |
| 7 | **Micro-environnement du prélèvement** : hauteur d’entrée, canyon, recul à la chaussée, végétation immédiate, travaux | **2–20 µg/m³** selon polluant | Biais fixe propre à la station, surtout pour un secteur de vent ; deux stations proches divergent durablement malgré paysage en tampon similaire |
| 8 | **Évolution du modèle amont** | **Inconnu**, mais potentiellement >10 µg/m³ sur un mois | Rupture simultanée sur de nombreuses stations à la date d’un cycle CAMS ; changement de relation résidu–CAMS plutôt que simple changement de moyenne |

Le test à rendement maximal est une matrice de résidus conditionnels, sans réentraîner : polluant × saison × heure × quantile CAMS × vent × stabilité × station. Elle dira si les processus manquants ont une signature cohérente ou si les anomalies sont propres à quelques stations.

**Sources.**

- **[Publié]** Huang et al. (2017) montrent qu’une correction analogique peut réduire la variabilité et manquer des extrêmes à émissions inhabituelles, *Weather and Forecasting*, DOI : [10.1175/WAF-D-16-0118.1](https://doi.org/10.1175/WAF-D-16-0118.1).
- **[Publié]** Righini et al. (2014), représentativité spatiale et inventaires d’émissions, *Atmospheric Environment*, DOI : [10.1016/j.atmosenv.2014.08.015](https://doi.org/10.1016/j.atmosenv.2014.08.015).
- **[Publié]** Visser et al. (2021), partition diurne des voies de dépôt d’ozone en forêt, *Atmospheric Chemistry and Physics*, DOI : [10.5194/acp-21-18393-2021](https://doi.org/10.5194/acp-21-18393-2021).

# Q4 — Données existantes mais absentes

| Priorité | Source | Information réellement nouvelle | Latence/profondeur annoncée | Utilisable à l’émission ? | Symptôme qui justifie de l’intégrer |
|---:|---|---|---|---|---|
| 1 | **Geod’air temps réel / flux AASQA interne** [documentation officielle] | Dernières observations du polluant et des copolluants ; état initial et biais récent | Transmission « au fil de l’eau » ; archive nationale via API [S6] | **Oui pour J/J+1**, sous réserve de QC et d’heure de coupure | ACF résiduelle et gain d’un simple biais glissant ; si nul, cette source est moins prioritaire |
| 2 | **Membres individuels et dispersion CAMS Europe** [documentation officielle] | Incertitude du modèle amont, désaccord de transport/chimie, indicateur de sortie de domaine | Quotidien ; 0–48 h vers 06:45 UTC, 49–96 h vers 08:30 UTC ; archive glissante 3 ans [S7] | **Oui**, mais le second lot arrive tard pour un bulletin matinal | Erreur absolue croissante avec l’écart interquartile/dispersion des membres |
| 3 | **CAMS MOS optimisé aux stations** [documentation officielle] | Comparateur déjà corrigé, observations de fond, météo prévue ECMWF | Horaire, quotidien, couverture depuis le 17 janvier 2024 [S2] | **Oui** | Si le projet ne bat pas ce MOS sur les mêmes stations/dates, son angle de contribution doit changer |
| 4 | **AROME/ARPEGE prévus** [documentation officielle] | Vent, stabilité et profils réellement disponibles en exploitation ; AROME résout mieux les régimes locaux qu’ERA5 grossière | Rétention publique 14 jours ; taux de disponibilité non communiqué [S8] | **Oui prospectivement**, non pour refaire directement 17 mois | Dégradation ERA5→prévision et erreur concentrée dans les vallées/vents faibles |
| 5 | **Trafic DATEX II** du réseau national et flux locaux [documentation officielle] | Débit, vitesse, congestion effectifs au lieu d’une hiérarchie de routes | Fichier national agrégé toutes les 6 min [S9] ; historique homogène à vérifier | **Oui pour l’état initial**, couverture routière incomplète | Résidu NO₂/PM corrélé à débit×faible vent ; aucun gain hors proximité des points de comptage implique abandon |
| 6 | **Meteosat/EUMETSAT** : nuages bas, brouillard, rayonnement observé [documentation officielle] | État nuageux réel à haute fréquence, souvent mal résumé par la météo de grille | Imagerie mise à jour toutes les 15 min ; accès produit et latence exacte selon service [S10] | **Oui pour J0**, utile comme état initial ; pas comme météo future seule | E5 et erreurs O₃ regroupées sous nuages bas/brouillard observés mais absents de la prévision |
| 7 | **E-PROFILE ceilomètres/lidars** [documentation officielle] | Profil vertical d’aérosols, mélange et couche résiduelle | Produits opérationnels en temps réel ; disponibilité française/station par station à vérifier [S11] | **Oui si une station voisine alimente le flux** | Résidus associés à couche résiduelle ou transport en altitude que la hauteur de couche limite ERA5 ne détecte pas |
| 8 | **CLMS LAI, FAPAR, FCover** [documentation officielle] | Végétation réellement feuillée et son évolution, au lieu de « forêt oui/non » | 300 m, mise à jour tous les 10 jours en quasi-temps réel ; historique depuis 2014 [S12] | **Oui**, dernière composite disponible | Interaction forêt dynamique attendue en E1 ; absence d’interaction mesurable permet d’abandonner |
| 9 | **Inventaires annuels AASQA/Atmo Data/Citepa** [documentation officielle] | Localisation et secteur des émissions ; bien meilleur proxy spatial que population seule | Annuel et retardé ; millésime courant rarement disponible | **Oui comme covariable structurelle**, non pour une anomalie du jour | Résidu stable par secteur source et vent ; gain surtout NO₂/PM, peu attendu sur transitions quotidiennes |

**Ce que le métier utilise mais qui s’intègre mal à un backtest public :** flux internes validés plus tôt que Geod’air, appels d’exploitants, signalements locaux, connaissance d’un chantier, d’un feu dirigé ou d’un instrument douteux. [jugement de praticien] Leur valeur doit être journalisée prospectivement ; sans trace horodatée, ils ne peuvent pas servir de preuve rétrospective.

**Sources.**

- **[S6]** LCSQA/data.gouv.fr, [données temps réel des polluants réglementés](https://www.data.gouv.fr/datasets/donnees-temps-reel-de-mesure-des-concentrations-de-polluants-atmospheriques-reglementes-1) et [API Geod’air](https://www.geodair.fr/api-ext/swagger).
- **[S7]** CAMS, prévisions européennes 0,1°, DOI de jeu de données : [10.24381/a4005cee](https://doi.org/10.24381/a4005cee).
- **[S2]** CAMS, MOS optimisé aux stations, DOI de jeu de données : [10.24381/2cce4067](https://doi.org/10.24381/2cce4067).
- **[S8]** Météo-France/data.gouv.fr, [API ARPEGE et données PNT](https://dev.data.gouv.fr/dataservices/api-modele-arpege), rétention 14 jours.
- **[S9]** transport.data.gouv.fr, [circulation en temps réel du réseau routier national non concédé](https://transport.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede/).
- **[S10]** EUMETSAT, [Earth View](https://www.eumetsat.int/real-time-imagery/earth-view) et [accès aux données](https://user.eumetsat.int/data-access).
- **[S11]** EUMETNET, réseau [E-PROFILE](https://www.eumetnet.eu/activities/observations-programme/current-activities/e-profile/). La couverture directement accessible en Occitanie et la latence d’API sont **Inconnu**.
- **[S12]** Copernicus Land Monitoring Service, [LAI/FAPAR/FCover 300 m](https://land.copernicus.eu/en/products/vegetation?tab=technical_summary), composites décennaux en quasi-temps réel.

# Q5 — Savoir de terrain d’un prévisionniste

Cette section est **[jugement de praticien]**. Elle formule des habitudes plausibles à faire confirmer par Atmo Occitanie, pas le témoignage direct d’un salarié de l’association.

| Rang | Savoir tacite probable | Effet attendu | Symptôme vérifiable |
|---:|---|---:|---|
| 1 | Une valeur isolée n’est jamais lue sans la station voisine, la veille et les copolluants | **5–20 µg/m³** | Les erreurs graves deviennent évidentes avec un tableau « observation récente + voisins + NO/NO₂ », mais restent imprévisibles avec les 52 variables |
| 2 | Chaque station a ses secteurs de vent « honnêtes » et « trompeurs » | **5–30 µg/m³ localement** | Rose des résidus par station : lobes stables, absents dans l’analyse nationale agrégée |
| 3 | Dans une vallée, la question n’est pas seulement la hauteur de couche limite mais l’heure de rupture de l’inversion | **5–25 µg/m³** | Décalage de 1–3 h entre baisse/hausse observée et prévue ; erreur de maximum liée à cette phase plutôt qu’à son amplitude |
| 4 | Les régimes d’autan, cers et tramontane ne sont pas des catégories binaires : leur établissement, leur sortie et les zones d’ombre comptent | **3–20 µg/m³** | Erreur maximale près des changements de direction/vitesse et dans quelques sous-régions récurrentes, pas au cœur du régime |
| 5 | Nuages bas, rosée et brouillard du matin sont des signaux de mauvais mélange et de dépôt que le champ de pluie ne remplace pas | **3–15 µg/m³**, surtout faibles O₃ | E5 regroupé les matins humides sans pluie ; satellite/visibilité explique le résidu après humidité ERA5 |
| 6 | Une rupture simultanée de tous les sites est d’abord suspectée comme changement de modèle, de flux ou de mesure avant d’être interprétée physiquement | **Peut sauver une journée entière** | Saut national sans cohérence avec vent ou observations indépendantes ; dispersion/métadonnées CAMS changent le même jour |
| 7 | Un épisode atypique demande une inspection de cartes, pas seulement un score : position du panache, fronts, heure d’arrivée et modèles individuels | **Fort sur quelques épisodes** | Médiane fausse mais un ou plusieurs membres corrects ; erreur principalement spatiale ou temporelle, pas d’amplitude |
| 8 | Le calendrier administratif réel bat parfois le calendrier générique : vacances scolaires locales, vendanges, épandage, chauffage au premier froid, grands chantiers | **2–15 µg/m³** | Résidus reproductibles sur ces fenêtres et près des sources correspondantes ; pas d’effet ailleurs |
| 9 | Certaines « erreurs modèle » sont des données provisoires qui seront invalidées | **1–10 µg/m³**, exceptionnellement plus | Valeur plate, saut impossible, copolluants incohérents, donnée ensuite qualifiée ou supprimée |

Le meilleur moyen d’acquérir ce savoir n’est pas de demander une liste : montrer au prévisionniste dix journées où le modèle se trompe et lui demander de commenter **avant** de révéler l’observation. Les motifs qu’il identifie correctement plusieurs fois deviennent des variables candidates ; les anecdotes non reproductibles restent des annotations.

# Q6 — La question anormalement absente

## « Par rapport à quel produit réellement disponible, pour quelle décision et à quelle heure ? »

C’est la question absente la plus grave. Le dispositif démontre qu’un LightGBM bat **CAMS brut aux stations**. Or l’utilisateur professionnel dispose potentiellement :

- des observations récentes et de leurs voisines ;
- du MOS CAMS déjà optimisé aux stations ;
- de PREV’AIR corrigé ;
- de plusieurs membres et cartes ;
- d’une expertise humaine ;
- d’une décision zonale J/J+1 à rendre avant une heure précise.

**Effet attendu : potentiellement éliminatoire pour l’originalité**, même si les +30 % restent vrais.  
**Symptôme :** une persistance observationnelle, un biais glissant de sept jours ou le MOS CAMS égale le LightGBM sur les stations existantes. Si oui, le projet résout surtout un problème artificiellement privé de l’information que possède l’AASQA.

Le benchmark minimal doit donc être : CAMS brut, biais fixe, biais glissant avec données disponibles à l’émission, persistance, CAMS MOS/produit corrigé accessible, puis LightGBM. Les comparaisons doivent employer la même heure de coupure et les mêmes stations/dates.

Il faut toutefois choisir le scénario avant le test. Si le produit vise réellement une **station nouvelle sans aucun historique**, persistance, biais glissant et MOS à cette station ne sont pas des concurrents admissibles ; la validation par station exclue est alors cohérente. S’il vise les stations qu’une AASQA exploite déjà chaque matin, les exclure de l’information récente crée un problème artificiel. Le même modèle ne peut pas revendiquer simultanément les deux usages.

## Angle mort du cadrage : confondre correction aux points et prévision du champ

Une station exclue valide une **interpolation vers une autre station du même réseau**. Elle ne produit pas automatiquement une concentration partout, une surface exposée ni une décision d’épisode zonale. Les 38 variables paysagères peuvent même apprendre la sélection des sites réglementaires plutôt que le champ atmosphérique.

**Effet attendu : fort sur l’usage, nul sur le RMSE station.**  
**Symptômes :**

- prédictions plausibles aux stations mais discontinues ou extrêmes dans des pixels sans analogues ;
- forte distance de covariables hors réseau ;
- classement des communes instable entre modèles pourtant équivalents aux stations ;
- échec quand une région entière, et non quelques stations dispersées, est cachée.

## Cadrage alternatif

Le produit le plus défendable n’est peut-être pas « une nouvelle concentration corrigée », mais une **fusion probabiliste** :

1. CAMS et ses membres fournissent le fond, le transport et l’incertitude ;
2. les observations récentes mettent à jour l’état et le biais ;
3. paysage et émissions traitent l’erreur de représentativité ;
4. le système produit probabilité d’épisode, intervalle et indicateur de confiance ;
5. il revient au produit opérationnel lorsque le cas est hors domaine.

**Effet attendu : Inconnu sur RMSE, fort sur la cohérence opérationnelle.**  
**Symptôme qui justifie ce recadrage :** la correction ponctuelle améliore la moyenne mais dégrade la cohérence spatiale, les extrêmes ou les mois après changement CAMS. Si aucun de ces symptômes n’existe après tests honnêtes, le cadrage actuel peut être conservé.

# Trois éléments les plus importants

1. **Comparer au vrai concurrent opérationnel, pas à CAMS brut.** Ajouter observations récentes, biais glissant et CAMS MOS peut faire disparaître ou, au contraire, préciser la contribution. C’est le test qui peut changer tout le dossier.
2. **Séparer biais CAMS et erreur de représentativité station–maille.** Les forts gains du paysage et l’inutilité du type officiel indiquent que le modèle corrige probablement beaucoup le support spatial, pas seulement la chimie du CTM.
3. **Rendre visibles chimie et structure verticale.** Copolluants NO/NO₂, état récent, stabilité/ceilomètre et canopée dynamique offrent une explication testable commune à E1 et E5.

# Points classés Inconnu

- Gain exact de l’ajout d’observations récentes dans ce protocole à stations exclues.
- Dégradation réelle lors du passage d’ERA5 à une météo prévue.
- Part du gain actuel attribuable au biais CAMS, à l’erreur de représentativité et à la sélection du réseau.
- Régime chimique responsable de E1 sans NOₓ/COV et végétation dynamique.
- Cause dominante de E5 tant que l’heure, le type de grandeur et les copolluants des cas <15,9 µg/m³ ne sont pas ventilés.
- Cause de E3 tant que variogramme, Moran’s I, résidus OOF et gain par distance ne sont pas publiés.
- Disponibilité et latence exploitables d’E-PROFILE à proximité des stations d’Occitanie.
- Complétude station/polluant du MOS CAMS sur la période commune depuis le 17 janvier 2024 et comparabilité exacte de ses heures d’émission.
- Amplitude transférable des plages en µg/m³ proposées ici : elles sont des priorités de test, non des résultats publiés.
