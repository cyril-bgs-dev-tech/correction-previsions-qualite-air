# Réponses — nouveaux outils

## A. Dispersion de l’ensemble

### 1. Quelle statistique avec six membres ?

**Réponse.** Utiliser en variable principale la médiane et le **MAD** (médiane des écarts absolus à la médiane), en conservant aussi les six valeurs pour une ablation. Le MAD résiste à un membre aberrant ; avec seulement six valeurs, son estimation reste toutefois très discrète et bruitée. L’écart-type échantillonnal estime la variance sans biais sous l’hypothèse i.i.d., hypothèse fausse pour six modèles déterministes apparentés ; l’étendue est très dépendante de l’effectif, et l’IQR dépend fortement de la convention d’interpolation.  
**Jugement méthodologique.** Il n’existe pas de « correction petit \(n\) » universelle pour un ensemble multi-modèle non échangeable. Rapporter MAD, écart-type et étendue en sensibilité, mais ne pas les interpréter comme une distribution d’incertitude à six tirages. Le MAD est une proposition robuste générale, non une norme CAMS ([Rousseeuw & Croux, 1993, DOI](https://doi.org/10.1080/01621459.1993.10476408)).

### 2. Que capture une dispersion multi-modèle ?

**Réponse.** Elle capture les différences entre formulations présentes : transport, chimie, aérosols, dépôts, résolution et paramétrisations. Dans CAMS, les modèles partagent une partie des forçages — météorologie, émissions et conditions aux limites — de sorte que leur dispersion ne contient ni l’incertitude commune de ces entrées ni les familles de modèles absentes ([Douros et al., 2023, DOI](https://doi.org/10.5194/gmd-16-509-2023) ; [Colette et al., 2025, DOI](https://doi.org/10.5194/gmd-18-6835-2025)).  
Un ensemble perturbé cherche au contraire à échantillonner l’incertitude d’un même système, notamment celle des conditions initiales. **Conclusion :** la dispersion CAMS est un indicateur de désaccord structurel conditionnel aux entrées communes, pas une variance prédictive totale.

### 3. Relation empirique dispersion–erreur

**Réponse.** La littérature CAMS montre que l’observation ne tombe pas systématiquement dans l’enveloppe des membres et que l’amplitude de la dispersion varie fortement selon saison, espèce et couche ; elle n’établit pas une relation universelle assez forte pour convertir directement le spread en erreur locale ([Douros et al., 2023, DOI](https://doi.org/10.5194/gmd-16-509-2023)). Le système CAMS présente d’ailleurs le spread comme une information **possible** sur l’incertitude, non comme un intervalle calibré ([Colette et al., 2025, DOI](https://doi.org/10.5194/gmd-18-6835-2025)).  
**Inconnu :** coefficient de corrélation publié, en France, pour O₃ horaire aux stations et pour ces six membres précis. Il faut donc mesurer la relation hors pli avant de qualifier la variable.

### 4. Comment tester la relation ?

**Réponse.** Produire, hors échantillon : (1) des classes de spread avec RMSE ou MAE moyen par classe ; (2) le ratio spread–skill ; (3) un diagramme de rang, puis couverture et largeur d’intervalles après calibration ; (4) une régression monotone entre spread et erreur absolue, apprise seulement dans les plis d’entraînement. Les diagnostics de rang et de fiabilité sont des outils établis pour vérifier dispersion et calibration ([Gneiting et al., 2007, DOI](https://doi.org/10.1111/j.1467-9868.2007.00587.x)).  
Ne pas se contenter d’une corrélation point par point : elle confond niveau de pollution, saison et hétéroscédasticité. Comparer aussi au prédicteur trivial « concentration médiane seule ».

### 5. Diagnostiquer et corriger la sous-dispersion

**Réponse.** Un diagramme de rang en U, une couverture inférieure au niveau nominal et un RMSE de la moyenne supérieur au spread signalent la sous-dispersion ; l’inverse signale la surdispersion ([Gneiting et al., 2007, DOI](https://doi.org/10.1111/j.1467-9868.2007.00587.x)). Les dépendances entre modèles et les biais communs peuvent produire une confiance artificielle dans un multi-modèle ([JRC, *Pauci ex tanto numero*, 2013](https://publications.jrc.ec.europa.eu/repository/handle/JRC78182)).  
**Jugement.** Pour une simple covariable LightGBM, il n’est pas nécessaire de corriger d’abord le spread : sa transformation peut être apprise. Pour annoncer une incertitude probabiliste, une calibration hors pli — régression d’ensemble, EMOS ou quantiles conformes — est indispensable.

### 6. Six membres sur onze

**Réponse.** Il n’y a pas de direction mathématique garantie : retirer des membres extrêmes rétrécit le spread, retirer des membres centraux peut l’élargir. Avec des modèles redondants et non échangeables, un facteur \(\sqrt{11/6}\) ou analogue serait sans fondement. La littérature souligne justement que la sélection de sous-ensembles dépend de leur indépendance et de leur performance, pas du seul nombre ([JRC, 2013](https://publications.jrc.ec.europa.eu/repository/handle/JRC78182)).  
**Test requis.** Sur une période où les onze sorties sont disponibles, calculer les spreads 6 et 11, leur biais conditionnel par saison et concentration, puis figer éventuellement une calibration. Sans ce chevauchement : **inconnu**.

### 7. Six valeurs brutes ou résumés ?

**Réponse.** Tester trois blocs emboîtés : médiane seule ; médiane + MAD ; enfin six membres centrés par leur médiane, avec identité des modèles conservée. Les valeurs brutes permettent au boosting d’exploiter des biais propres aux membres, mais multiplient des variables fortement corrélées et peuvent apprendre des classements instables. CAMS retient opérationnellement la médiane pour sa robustesse aux membres aberrants ([Colette et al., 2025, DOI](https://doi.org/10.5194/gmd-18-6835-2025)).  
**Jugement.** Avec 16 mois, autoriser les six seulement sous régularisation et si leur gain passe une validation temporelle **et** par stations exclues. Min/max ajoutent peu après les valeurs brutes.

### 8. Distinguer biais d’un membre et désaccord instantané

**Réponse.** Décomposer \(x_{m,t}-\mathrm{médiane}_t\) en (a) une anomalie moyenne propre au membre, estimée hors pli par saison et horizon, et (b) un résidu instantané centré. Ajouter le rang du membre et la stabilité temporelle de ce rang. La première composante décrit un biais persistant ; le MAD des résidus décrit le désaccord du jour.  
**Jugement méthodologique.** Cette décomposition n’est pas un produit CAMS normalisé. Elle doit être ajustée dans chaque pli pour éviter que le biais saisonnier de la période de test ne soit connu à l’avance.

### 9. La dispersion comme signal ex ante de dérive

**Réponse.** C’est un candidat légitime parce qu’elle est disponible à l’émission et ne contient pas l’observation future. Mais elle ne devient un signal de dérive qu’en prédisant, hors pli, une dégradation de CAMS ou un bénéfice accru du correcteur. Le spread CAMS n’est publié que comme information potentielle d’incertitude ([Colette et al., 2025, DOI](https://doi.org/10.5194/gmd-18-6835-2025)).  
Tester une interaction pré-enregistrée `spread × correction` ou comparer le gain dans des quantiles de spread définis sur l’entraînement. Ne pas former les groupes sur l’erreur réalisée et ne pas sélectionner leur seuil sur le test : cela recréerait le couplage que l’on veut éviter.

### 10. Incertitude commune ignorée : de combien ?

**Réponse.** Les modèles CAMS partagent suffisamment d’entrées pour que la dispersion ne représente pas l’incertitude totale ; des biais et redondances communs sont documentés ([Douros et al., 2023, DOI](https://doi.org/10.5194/gmd-16-509-2023) ; [JRC, 2013](https://publications.jrc.ec.europa.eu/repository/handle/JRC78182)).  
**Inconnu :** aucun facteur multiplicatif publié et transportable vers O₃, France, J+1–J+3, stations exclues. Le rapport dépend du polluant, de la saison et de la définition du spread. L’estimer localement par couverture et spread–skill ; ne pas annoncer un pourcentage emprunté à une autre configuration.

### 11. Risque de fuite par assimilation

**Réponse.** L’assimilation d’observations disponibles **avant l’heure d’émission** fait partie de la prévision opérationnelle et n’est pas une fuite. La fuite apparaît si l’on utilise une analyse, un run révisé ou des observations postérieures au cutoff que l’utilisateur opérationnel n’aurait pas eues. CAMS distingue analyses assimilées et prévisions, et réserve environ un tiers des stations lors de certaines évaluations de l’assimilation ([Colette et al., 2025, DOI](https://doi.org/10.5194/gmd-18-6835-2025)).  
Archiver `forecast_reference_time`, cycle, échéance et date de disponibilité. Vérifier, membre par membre, que le champ téléchargé est bien `forecast`, jamais `analysis`.

### 12. Poids appris ou médiane ?

**Réponse.** CAMS diffuse la médiane, robuste aux modèles aberrants. Des poids optimisés existent expérimentalement : le système décrit par Colette et al. les estime sur les sept jours passés, uniformément dans l’espace, mais souligne le caractère expérimental de cette pondération ([Colette et al., 2025, DOI](https://doi.org/10.5194/gmd-18-6835-2025)).  
**Jugement.** Garder la médiane comme référence forte. N’accepter des poids appris que s’ils sont non négatifs, régularisés, recalculés sans le test et supérieurs sur plusieurs blocs temporels ; sinon leur variance sur 16 mois risque de dépasser leur bénéfice.

## B. Les feux comme sources ponctuelles

### 13. Quelle grandeur GFAS ?

**Réponse.** Pour expliquer PM2.5, le flux GFAS de PM2.5 est le prédicteur le plus direct. Le FRP est le plus proche de la mesure satellitaire ; GFAS convertit ensuite le FRP en matière sèche brûlée, puis applique des facteurs d’émission par biome pour obtenir les espèces, dont PM2.5 ([Kaiser et al., 2012, DOI](https://doi.org/10.5194/bg-9-527-2012) ; [documentation GFAS](https://confluence.ecmwf.int/pages/viewpage.action?pageId=129128405)).  
Donc FRP ajoute moins d’hypothèses mais est moins spécifique au polluant ; le flux PM2.5 ajoute les hypothèses de conversion et de facteur d’émission. Tester PM2.5 principal, FRP en sensibilité, sans les additionner naïvement.

### 14. Échelle de distance

**Réponse.** Lors des feux européens de 2003, les plus fortes augmentations de PM2.5 de surface étaient surtout dans un rayon d’environ 200 km, avec des effets allant jusqu’à 40 µg/m³ dans les zones touchées ([Hodzic et al., 2007, DOI](https://doi.org/10.5194/acp-7-4043-2007)). Des panaches grecs ont traversé la Méditerranée en moins d’une journée et autour de 2 km d’altitude ([Turquety et al., 2009, DOI](https://doi.org/10.5194/acp-9-4897-2009)).  
Il n’existe donc pas un rayon unique : quelques centaines de kilomètres conviennent à l’effet de surface fréquent, mais le transport élevé peut atteindre bien davantage. Utiliser des trajectoires et plusieurs fenêtres, pas une coupure universelle.

### 15. Hauteur d’injection

**Réponse.** La prémisse « GFAS ne la fournit peut-être pas » est fausse : GFAS fournit des estimations quotidiennes du bas et du haut du panache ainsi que des hauteurs d’injection dérivées du FRP et de la météorologie ECMWF ([fiche officielle GFAS](https://ads.atmosphere.copernicus.eu/datasets/cams-global-fire-emissions-gfas?tab=overview)).  
Employer la hauteur pour choisir la couche de vent et réduire l’exposition de surface lorsque le panache reste au-dessus de la couche limite. Ces hauteurs restent modélisées, non observées directement ; une sensibilité des PM2.5 de surface allant jusqu’à 50 % à leur traitement a été rapportée dans une étude de cas ([Majdi et al., 2019, DOI](https://doi.org/10.5194/acp-19-785-2019)).

### 16. Décroissance avec la distance

**Réponse.** Aucune exponentielle, puissance ou gaussienne scalaire n’est universellement justifiée à l’échelle régionale. Une gaussienne suppose un écoulement approximativement stationnaire et homogène ; un panache réel subit advection, cisaillement, mélange, dépôt et chimie, ce qui motive les modèles de panache/puffs ou les trajectoires ([Paugam et al., 2016, DOI](https://doi.org/10.5194/acp-16-907-2016)).  
**Inconnu :** longueur caractéristique publiée et transférable à toute la France. Comme approximation, construire plusieurs noyaux anisotropes et plusieurs temps de parcours, puis choisir leurs paramètres uniquement dans l’entraînement ; ne pas leur donner une interprétation physique exacte.

### 17. Vent de surface ou couche de transport ?

**Réponse.** Le vent à 10 m est inadéquat dès que le panache est injecté au-dessus de la couche de surface : direction et vitesse peuvent différer fortement avec l’altitude. Les revues de modélisation des panaches insistent sur l’interaction entre hauteur d’injection et profil météorologique ([Paugam et al., 2016, DOI](https://doi.org/10.5194/acp-16-907-2016)).  
Utiliser le vent IFS/AIFS au niveau le plus proche de la hauteur GFAS, ou une moyenne pondérée dans la couche du panache ; conserver le vent 10 m comme ablation. L’ERA5 à 10 m seul ne suffit pas à défendre une exposition de panache élevé.

### 18. Délai émission–station

**Réponse.** Le délai doit découler du temps de trajet le long du vent et de la hauteur, pas du seul « jour du feu ». À titre de **calcul**, 300 km parcourus à 5–15 m/s représentent environ 6–17 h ; ce n’est pas une constante publiée. Les panaches grecs observés dans l’étude Turquety et al. ont traversé la Méditerranée en moins d’un jour ([Turquety et al., 2009, DOI](https://doi.org/10.5194/acp-9-4897-2009)).  
Construire des expositions retardées 0–72 h avec trajectoires successives, agréger sur l’heure réglementaire, et déterminer les lags dans les plis. Un champ GFAS quotidien limite de toute façon la précision intrajournalière.

### 19. Éviter le simple proxy saisonnier

**Réponse.** Inclure explicitement saison, température, rayonnement et météo prévue dans le modèle de base, puis tester l’incrément GFAS à dates identiques. Comparer à l’intérieur de strates mois × région × régime météorologique et employer des jours témoins estivaux sans exposition au feu.  
**Jugement.** Le test probant est une variation directionnelle et retardée cohérente avec le vent, au-delà d’un indicateur « feu quelque part en été ». L’unité de rééchantillonnage doit être l’événement de feu, pas chaque jour-station corrélé.

### 20. Contrôle négatif pour les feux

**Réponse.** Décaler les dates GFAS d’un nombre entier de semaines — par exemple ±28 ou ±35 jours — dans la même saison, tout en recalculant l’exposition avec les vents des dates factices. Cela préserve la saisonnalité et la distribution spatiale des feux mais détruit l’alignement causal émission–transport–observation.  
Ajouter un second contrôle : retourner la direction du vent de 180°. **Jugement.** Si le vrai signal ne bat pas ces deux contrôles sur les événements tenus à l’écart, le gain doit être qualifié d’association saisonnière, pas d’information feu.

### 21. Redondance avec CAMS

**Réponse.** GFAS alimente déjà les prévisions CAMS globales et régionales ([fiche officielle GFAS](https://ads.atmosphere.copernicus.eu/datasets/cams-global-fire-emissions-gfas?tab=overview)). L’ajout au correcteur n’introduit donc pas une nouvelle source physique indépendante. Il peut néanmoins exposer explicitement une information que CAMS représente imparfaitement : sous-maille, hauteur, retard journalier, dispersion et différences d’implémentation entre membres.  
La bonne hypothèse n’est pas « CAMS ignore les feux », mais « l’erreur résiduelle dépend encore d’une exposition GFAS ». Elle se teste par le gain conditionnel après CAMS, et non par la corrélation brute GFAS–PM.

### 22. Latence réelle de GFAS

**Réponse.** GFAS est un produit quotidien proche du temps réel, mais les chaînes peuvent n’avoir que les émissions des jours précédents. Une fiche CAMS 2025 indique, pour GEM-AQ, le dernier cycle de 24 h couvrant D−2/D−1 ; un rapport CAMS explique aussi le recours aux émissions du jour précédent ([fiche GEM-AQ 2025](https://confluence.ecmwf.int/download/attachments/202173092/GEM-AQ%20Factsheet-2025.pdf?api=v2) ; [rapport CAMS](https://atmosphere.copernicus.eu/sites/default/files/2018-06/CAMS84_2015SC2_D84.1.1.9_2017JJA_v1_0.pdf)).  
Donc un feu allumé la veille **peut** entrer à J+1 s’il a été détecté et inclus dans le dernier cycle disponible, mais ce n’est pas garanti. L’heure exacte de disponibilité de votre archive : **à vérifier** par horodatage des fichiers/API.

### 23. Rareté des jours concernés

**Réponse.** **Inconnu.** Je n’ai pas trouvé de fraction publiée des jours-station français satisfaisant votre future définition d’exposition GFAS ; la valeur dépendrait du rayon, de la hauteur, du vent, du lag et du seuil. Un pourcentage d’« incendies en France » ne répondrait pas à la question des panaches atteignant les stations.  
La mesurer après avoir figé la définition ex ante, avec un intervalle de confiance par événements indépendants. Donner séparément nombre de feux, d’épisodes, de stations touchées et de jours-station.

### 24. Évaluer un effet rare

**Réponse.** Définir d’abord un sous-groupe exposé sans utiliser l’erreur future, puis rapporter : performance dans ce sous-groupe, différence d’effet exposé/non exposé, résultat global pondéré, et nombre effectif d’événements. Faire une validation « leave-one-fire-event-out » ou par blocs spatio-temporels et bootstrapper les événements.  
Conserver aussi une métrique opérationnelle — POD/CSI à FAR fixé — car un petit gain global peut masquer un grand gain sur épisodes. Ne pas conclure avec les seuls jours-station, dont la dépendance spatiale rendrait l’intervalle trop étroit.

## C. Modèle spécialiste de régime

### 25. Pourquoi un spécialiste feu réussirait-il ?

**Réponse.** Le résultat 14,70 contre 13,32 est une preuve interne qu’une partition vague des « journées anormales » ne suffit pas. Un spécialiste feu ne serait différent que si le régime est défini ex ante par une cause physique, si les relations changent réellement dans ce régime et si plusieurs événements indépendants couvrent assez de situations.  
**Jugement.** Commencer par un modèle général avec exposition GFAS et interactions. N’ouvrir la branche spécialiste que si une analyse hors pli montre un résidu structuré spécifique aux feux ; sinon il faut s’attendre au même échec par rareté et variance.

### 26. Taille minimale d’échantillon

**Réponse.** **Inconnu :** il n’existe pas de nombre universel de jours ou d’événements garantissant qu’un expert battra le généraliste. La taille utile dépend du nombre de paramètres, de la diversité des feux, du bruit et de l’ampleur de l’interaction. Des milliers de jours-station provenant de deux feux ne valent pas des milliers d’événements indépendants.  
Faire une courbe d’apprentissage par **événements**, avec intervalles bootstrap, et exiger une stabilisation sur des feux entièrement exclus. Une simulation à partir de l’effet et de la covariance observés peut ensuite donner la puissance propre à ce projet.

### 27. Deux modèles ou indicateur unique ?

**Réponse.** Un modèle unique avec exposition continue et interactions partage l’information et réduit la variance ; deux experts gagnent seulement si les fonctions conditionnelles sont réellement différentes et suffisamment alimentées. Les mélanges d’experts formalisent ce compromis via un réseau de porte et des experts spécialisés ([Jacobs et al., 1991, DOI](https://doi.org/10.1162/neco.1991.3.1.79)).  
**Jugement pour ces données rares :** modèle unique d’abord, interactions contraintes ensuite, experts en dernier. Je n’ai pas trouvé de comparaison publiée qui fixe cet arbitrage pour la correction CAMS conditionnée aux feux.

### 28. Routeur sans fuite

**Réponse.** Oui : tout routeur appris, ses variables, seuils et calibration doivent être ajustés dans chaque pli d’entraînement. Le pli externe tient à l’écart stations **et événements** ; un pli interne choisit le seuil ou les hyperparamètres. Un indicateur GFAS purement déterministe peut être calculé partout, mais son seuil ne peut pas être optimisé sur le test.  
Il faut également respecter le cutoff opérationnel de GFAS et des vents. Sinon le routeur utilise implicitement une information indisponible à l’émission.

### 29. Mélange souple ou choix dur

**Réponse.** Le mélange souple est préférable lorsque l’appartenance au régime est incertaine : \(\hat y=(1-p)\hat y_g+p\hat y_f\). Il évite une discontinuité autour d’un seuil et propage l’incertitude de routage ; le principe est celui des mélanges d’experts ([Jacobs et al., 1991, DOI](https://doi.org/10.1162/neco.1991.3.1.79)).  
Calibrer \(p\) hors pli sur une définition indépendante d’exposition ou sur un objectif probabiliste, puis vérifier fiabilité et netteté. Un poids appris directement pour minimiser l’erreur finale risque sinon de devenir un second correcteur opaque.

### 30. Décomposer les erreurs du système

**Réponse.** Calculer trois pertes sur les mêmes cas : \(L_g\), généraliste seul ; \(L_o\), oracle choisissant l’expert selon le vrai régime pré-déclaré ; \(L_r\), système réellement routé. Le potentiel de spécialisation est \(L_g-L_o\), le regret de routage \(L_r-L_o\), et le gain net \(L_g-L_r\).  
Arrêter si l’intervalle du gain net inclut zéro, si le routeur consomme le potentiel de l’oracle, ou si le FAR se dégrade. **Jugement :** cette décomposition est une spécification du projet, pas une norme publiée AASQA.

### 31. Définir le régime feu

**Réponse.** La définition opérationnelle la plus défendable est une **exposition transportée** : flux PM2.5/FRP, direction et vitesse du vent à la hauteur d’injection, délai et couche limite. Un seuil de FRP amont seul ignore le transport ; la composition d’aérosol observée à la station serait un bon label de validation mais arrive trop tard pour router une prévision. GFAS fournit flux et hauteurs nécessaires ([documentation GFAS](https://confluence.ecmwf.int/pages/viewpage.action?pageId=129128405)).  
Figer la définition avant de regarder le gain et publier une sensibilité à ses paramètres.

### 32. Gain minimal justifiant deux modèles

**Réponse.** **Inconnu :** aucune pratique publiée ne fixe un seuil universel en µg/m³ ou en pourcentage pour cette architecture. Le seuil dépend du coût d’exploitation, du nombre d’épisodes et de l’utilité au déclenchement.  
**Jugement proposé :** exiger simultanément une borne basse d’IC positive sur les événements feu, aucune perte matériellement importante sur le corpus complet, et un gain opérationnel au FAR fixé supérieur au coût convenu. Le seuil de 0,3 µg/m³ reste une règle de projet, pas une règle du domaine.

### 33. Travaux sur une correction conditionnée au feu

**Réponse.** **Inconnu.** Je n’ai pas identifié de publication évaluant précisément une correction de biais d’un modèle de qualité de l’air par deux experts, dont un routé par GFAS, avec validation sur événements exclus. Les travaux trouvés traitent surtout les émissions, l’injection, l’assimilation ou la prévision physique des fumées, pas ce post-traitement.  
Ne pas présenter l’idée comme « démontrée par la littérature ». La littérature justifie les variables physiques ([Paugam et al., 2016, DOI](https://doi.org/10.5194/acp-16-907-2016)), pas le gain de l’architecture.

## D. Modèles de fondation et prévisions neuronales

### 34. Structure d’erreur d’AIFS face à IFS

**Réponse.** Les documents ECMWF indiquent qu’AIFS Single, entraîné par erreur quadratique, est performant sur les métriques moyennes mais tend à lisser gradients et pics localisés ; AIFS ENS vise une distribution et une relation spread–error plus réalistes ([ECMWF, AIFS ensemble](https://www.ecmwf.int/en/newsletter/181/earth-system-science/data-driven-ensemble-forecasting-aifs) ; [ECMWF, cas de tempêtes](https://www.ecmwf.int/en/about/media-centre/aifs-blog/2026/severe-storms-machine-learning)). ECMWF recense aussi la sous-représentation de certains extrêmes localisés ([Known AIFS Forecasting Issues](https://confluence.ecmwf.int/display/FCST/Known%2BAIFS%2BForecasting%2BIssues)).  
**Inconnu :** biais et dispersion d’AIFS pour les variables exactes, horizons et stations françaises de ce projet. Ils doivent être mesurés, version par version.

### 35. Lissage quantifié

**Réponse.** Oui, le lissage d’une prévision déterministe optimisée en MSE est explicitement reconnu par ECMWF ; les champs ont moins d’activité et les gradients étroits sont atténués ([ECMWF, AIFS ensemble](https://www.ecmwf.int/en/newsletter/181/earth-system-science/data-driven-ensemble-forecasting-aifs) ; [ECMWF, cas de tempêtes](https://www.ecmwf.int/en/about/media-centre/aifs-blog/2026/severe-storms-machine-learning)).  
**Inconnu :** un pourcentage publié unique de perte des maxima par échéance transférable à O₃. L’évaluer sur les variables météorologiques horaires échantillonnées aux stations, en séparant moyenne, variance, quantiles 0,95/0,99 et maxima journaliers.

### 36. AIFS est-il structurellement inférieur pour un maximum ?

**Réponse.** Non : la prémisse est trop forte. Le lissage rend AIFS Single **à risque** pour les extrêmes localisés, mais une meilleure trajectoire synoptique peut malgré tout améliorer le conditionnement d’un maximum d’O₃. Les problèmes de pics sont documentés, pas une infériorité universelle ([Known AIFS Forecasting Issues](https://confluence.ecmwf.int/display/FCST/Known%2BAIFS%2BForecasting%2BIssues)).  
Comparer IFS et AIFS à même cycle et résolution, puis dériver les mêmes statistiques horaires. Si vos fichiers AIFS ne sont que toutes les 6 h, l’échantillonnage lui-même peut manquer le maximum : le séparer du biais du modèle.

### 37. Que signifie « 74 % des cibles » pour Aurora ?

**Réponse.** Dans l’article Aurora, la tâche pollution est globale à 0,4° et sur cinq jours ; la comparaison porte sur des combinaisons variable × niveau de pression × échéance, avec l’analyse CAMS comme vérité, pas sur des stations ni sur le maximum journalier glissant 8 h. Aurora améliore la RMSE de 74 % de ces cibles, tandis que CAMS reste meilleur notamment à courte échéance dans la basse atmosphère et pour certains champs d’ozone ([Bodnar et al., 2025, DOI](https://doi.org/10.1038/s41586-025-09005-y)).  
La survie de ce gain au MDA8 et aux stations : **inconnue**. Elle exige une évaluation dédiée.

### 38. Héritage des biais CAMS

**Réponse.** Un modèle entraîné et évalué contre des analyses CAMS apprend leur état conditionnel et ne peut démontrer, avec cette seule vérité, qu’il corrige leurs biais face aux stations. Aurora Air Pollution a été affiné sur CAMS et évalué contre l’analyse CAMS ([Bodnar et al., 2025, DOI](https://doi.org/10.1038/s41586-025-09005-y)).  
Tester les deux prévisions contre des observations indépendantes, par station, régime et quantile ; comparer biais moyen, variance, MDA8 et épisodes. Une erreur commune Aurora–CAMS face aux stations indiquera un héritage ou une information commune, sans en prouver seule le mécanisme.

### 39. Comparaison à armes égales

**Réponse.** Figer le même `forecast_reference_time`, les mêmes heures valides et échéances, dates, stations, variables, méthode d’interpolation, masque de disponibilité et métriques. Vérifier les versions opérationnelles et exclure tout run arrivé après le cutoff. Rééchantillonner à une grille commune seulement si nécessaire et évaluer aussi à la résolution native.  
Ne pas comparer AIFS J+1 à une analyse IFS, ni AIFS 6 h à IFS horaire sans harmoniser le calcul du maximum. Rapporter disponibilité et coût en plus de l’erreur : ce sont des propriétés opérationnelles, non des corrections statistiques.

### 40. Utiliser IFS et AIFS ensemble

**Réponse.** Oui. Chaque champ brut peut porter un signal utile, tandis que leur différence porte un signal de désaccord structurel ; réduire les entrées au seul désaccord jetterait leur niveau météorologique commun. Les systèmes ECMWF physique et appris ont des structures et objectifs distincts ([ECMWF, AIFS ensemble](https://www.ecmwf.int/en/newsletter/181/earth-system-science/data-driven-ensemble-forecasting-aifs)).  
Faire quatre ablations : IFS ; AIFS ; moyenne + différence ; IFS + AIFS bruts. Si la différence seule gagne, elle devient un indicateur d’incertitude ; sinon les deux peuvent rester des covariables distinctes sous régularisation.

### 41. Pièges propres aux modèles de fondation

**Réponse.** Auditer les dates et sources de pré-entraînement, d’affinage, de sélection d’hyperparamètres et de test. Une période dite « hors échantillon » pour votre correcteur ne l’est pas nécessairement pour le modèle de fondation ; cela n’est pas une fuite opérationnelle si le modèle était figé et disponible, mais invalide une prétention de généralisation temporelle vierge. Aurora documente des corpus et périodes distincts, qu’il faut confronter à chaque test ([Bodnar et al., 2025, DOI](https://doi.org/10.1038/s41586-025-09005-y)).  
Contrôler aussi changement de checkpoint, normalisations, source exacte des conditions initiales et avantage de résolution. Ne jamais utiliser rétroactivement un checkpoint publié après la date simulée sans le déclarer.

### 42. Aurora sans état global complet ?

**Réponse.** Non, pas dans son usage publié standard. Aurora Air Pollution requiert des champs globaux de météorologie et de chimie, des variables statiques et 13 niveaux de pression ; les rollouts partent d’un état atmosphérique complet. La documentation liste notamment `t,u,v,q,z,co,no,no2,so2,go3` et les champs d’émissions statiques ([documentation officielle des modèles Aurora](https://microsoft.github.io/aurora/models.html)).  
Des stations ou une tuile locale ne suffisent donc pas directement. La documentation indique environ 40 Go de mémoire GPU pour le modèle global 0,25° standard ([guide Aurora](https://microsoft.github.io/aurora/usage.html)); le coût exact de la variante pollution 0,4° : **à vérifier**.

## E. Protocole d’ensemble

### 43. Risque de multiplicité

**Réponse.** Trois familles × polluants × horizons × métriques × variantes créent de nombreuses occasions de retenir un gain fortuit ; les intervalles ordinaires ne corrigent pas cette sélection. Définir un critère primaire unique, une hiérarchie de tests et un test final intact ; considérer le reste comme exploratoire. Le contrôle hiérarchique ou du taux de fausses découvertes conserve davantage de puissance qu’une correction uniforme de toutes les comparaisons ([Benjamini & Hochberg, 1995, DOI](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)).  
Publier aussi tous les essais et leur ordre, y compris les résultats nuls.

### 44. Ordre des tests

**Réponse.** **Jugement fondé sur vos résultats :** (1) météo prévue IFS/AIFS, car elle operationalise le levier ERA5 déjà mesuré à +7,8 % ; (2) dispersion CAMS, ajout peu coûteux et ex ante ; (3) feux, rares et déjà partiellement absorbés par CAMS.  
Pour chaque étape, comparer `socle + bloc` au même socle sur exactement les mêmes lignes. Une fois un bloc accepté, le figer avant le suivant ; conserver en parallèle une ablation factorielle finale pour détecter redondance et interaction.

### 45. Validation gelée

**Réponse.** Oui : les plis servent à développer, un bloc temporel final et des stations exclues servent une seule fois à confirmer. Mais une période déjà examinée dans les itérations ne peut plus être qualifiée de gelée. Avec 16–17 mois, un petit bloc final risque aussi de ne contenir qu’un régime saisonnier.  
**Jugement.** Le meilleur test externe serait une nouvelle saison d’ozone complète, avec stations jamais entraînées. Si elle n’est pas disponible, utiliser une validation imbriquée spatio-temporelle et dire honnêtement « validation interne », sans sacrifier artificiellement plusieurs mois.

### 46. Critère d’arrêt relatif

**Réponse.** Employer \(\Delta_\mathrm{rel}=100(RMSE_\mathrm{socle}-RMSE_\mathrm{nouveau})/RMSE_\mathrm{socle}\), accompagné de la différence absolue et de son intervalle bootstrap par station/événement. Aucun seuil relatif universel n’est publié pour accepter une covariable de correction de CAMS : **inconnu**.  
**Jugement de projet :** exiger une borne basse d’IC positive et au moins 3–5 % relatif sur le critère primaire, plus absence de perte sur les épisodes/FAR. Le seuil peut être plus bas pour une variable gratuite et plus haut pour un second système opérationnel.

### 47. Pré-enregistrer pendant la découverte

**Réponse.** Séparer un journal exploratoire horodaté d’un protocole confirmatoire. Après contrôle de structure et de qualité — mais avant de calculer le résultat cible — figer données, exclusions, variable primaire, modèles, hyperparamètres ou procédure de sélection, plis et règle d’arrêt. Enregistrer un hash du protocole, des identifiants de données et du code.  
Toute modification ultérieure devient un amendement daté ; l’analyse correspondante est exploratoire jusqu’à réplication. Il n’est ni nécessaire ni honnête de prétendre que les choix antérieurs étaient pré-enregistrés.

### 48. Contrôle négatif systématique

**Réponse.** Préférer une permutation **par blocs station × saison** ou un décalage circulaire de dates à une variable i.i.d. aléatoire : elle conserve autocorrélation, valeurs manquantes et saisonnalité, mais détruit l’alignement causal. Adapter ensuite le contrôle à chaque bloc : dates GFAS décalées, spread permuté dans saison × échéance, météo d’un autre jour comparable.  
Le pipeline complet — sélection comprise — doit être rejoué. Le gain réel doit dépasser la distribution des contrôles, pas seulement une permutation choisie après coup.

### 49. Novembre 2023 manquant

**Réponse.** Un novembre absent n’est pas neutre : il réduit d’un tiers les observations de cette saison de transition sur une archive de 16–17 mois et peut modifier les estimations automnales. L’erreur HTTP 400 n’établit pas que la donnée source n’existe pas ; cause et disponibilité sont **à vérifier**.  
Pour toute comparaison impliquant l’ensemble, employer les 16 mois communs. Pour les analyses sans ensemble, garder novembre mais fournir une sensibilité sur les mêmes 16 mois ; l’exclure partout comme analyse principale gaspillerait de l’information sans supprimer le biais de sélection.

### 50. Une seule piste à garder

**Réponse.** **Météo prévue IFS/AIFS.** C’est la seule piste adossée à un gain déjà mesuré dans ce projet (+7,8 % avec ERA5) tout en rendant les covariables réellement disponibles à l’émission. Elle concerne tous les jours, contrairement aux feux, et apporte une information plus large que le désaccord de six modèles partageant leurs principaux forçages.  
**Jugement, non résultat publié.** Tester IFS d’abord comme remplacement causal d’ERA5, puis AIFS en ablation. Le succès est la récupération hors échantillon d’une fraction substantielle du gain ERA5 sans information postérieure au cutoff.

## Points restant inconnus ou à vérifier

- Coefficient dispersion–erreur pour O₃, France, ces six membres et ces horizons.
- Facteur reliant dispersion de six membres, dispersion des onze et incertitude totale.
- Heure exacte de disponibilité GFAS dans la chaîne et les fichiers utilisés.
- Fraction française de jours-station réellement exposés selon la future définition.
- Taille minimale et gain minimal universels d’un expert « feu » : ils n’existent pas dans les sources trouvées.
- Publication évaluant exactement une correction CAMS routée sur un régime GFAS.
- Perte quantitative universelle d’AIFS sur les maxima d’O₃ et performance d’Aurora sur MDA8 aux stations.
- Coût d’inférence exact d’Aurora Air Pollution 0,4° dans votre environnement.
- Cause du HTTP 400 de novembre 2023.
