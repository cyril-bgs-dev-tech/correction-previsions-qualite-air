# Réponse GPT — R16

*État des textes et des sources : 8 août 2026.*

## Avis exécutif

Le diagnostic principal n’est pas que le modèle « rate 31 épisodes PM10 sur 33 ». Le diagnostic est que ce calcul confronte deux objets différents :

- la prédiction d’une concentration à une station ;
- une procédure préfectorale déclenchée sur une prévision spatialisée, un critère de superficie ou de population, et éventuellement la persistance.

Le score 2/33 ne doit donc plus être présenté comme une performance de détection des épisodes réglementaires. Il mesure au mieux la concordance imparfaite entre un seuil aux stations et une décision zone-jour. Le bon remplacement est un double tableau : d’une part les dépassements observés aux stations de fond ; d’autre part les procédures zone-jour, évaluées sur les champs prévus et analysés qui ont réellement servi à la décision.

L’audit révèle aussi une incohérence plus grave et immédiatement vérifiable dans le dépôt :

- la tranche 25–48 h est définie comme horizon 2 dans le code, mais elle est imprimée « J+2 » par plusieurs scripts et rapports ; dans la convention déjà adoptée par le dépôt, 25–48 h est J+1 ;
- les grandeurs journalières sont groupées par jour UTC, et non par jour civil Europe/Paris ;
- un jour UTC peut donc agréger des heures issues de cycles de prévision différents si le panel contient les sorties quotidiennes successives.

Avant toute nouvelle variable PM10, il faut corriger ou retirer les libellés concernés et écrire le contrat temporel exact de chaque résultat. C’est le geste de moins d’une journée qui augmentera le plus la crédibilité du dossier.

J’emploie ci-dessous cinq registres :

- **[Droit]** : exigence explicite d’un texte opposable ;
- **[Établi]** : résultat directement documenté dans une source primaire ou institutionnelle ;
- **[Pratique]** : usage métier documenté, mais non obligation juridique ;
- **[Inférence]** : conclusion tirée des textes et des résultats disponibles ;
- **[À vérifier]** : point qui exige les bulletins, champs ou instantanés de données du projet.

## 1. Ce qui déclenche réellement une procédure préfectorale

### 1.1 Le texte national opposable

Le texte central est l’[arrêté du 7 avril 2016 relatif au déclenchement des procédures préfectorales en cas d’épisodes de pollution de l’air ambiant](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671), complété localement par les arrêtés zonaux et départementaux. La page de la [DREAL Occitanie consacrée au dispositif](https://www.occitanie.developpement-durable.gouv.fr/le-dispositif-de-gestion-des-episodes-de-pollution-a23404.html?lang=fr) renvoie notamment à l’arrêté zonal du 20 juin 2017 et aux arrêtés départementaux applicables.

**[Droit] Grandeurs et seuils actuellement applicables en France.** L’article R. 221-1 du code de l’environnement fixe :

| Polluant | Information-recommandation | Alerte |
|---|---:|---:|
| PM10 | 50 µg/m³ en moyenne journalière | 80 µg/m³ en moyenne journalière |
| Ozone | 180 µg/m³ en moyenne horaire | 240 µg/m³ en moyenne horaire, avec niveaux progressifs à 240, 300 et 360 µg/m³ |
| NO₂ | 200 µg/m³ en moyenne horaire | 400 µg/m³ pendant trois heures consécutives ; ou 200 µg/m³ sous la condition de persistance prévue par le texte |

Source : [code de l’environnement, article R. 221-1](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000022964539).

Le seuil PM10 n’est donc pas un maximum horaire. L’hypothèse « les douze cas viennent d’un seuil horaire PM10 » est à écarter.

**[Droit] Le dépassement peut être entièrement caractérisé par la modélisation.** L’article 2 de l’arrêté du 7 avril 2016 retient un épisode dès qu’un des critères suivants est satisfait :

1. une superficie totale d’au moins 100 km² est concernée dans une région ;
2. dans un département de plus de 500 000 habitants, au moins 10 % de la population est concernée ; dans un département moins peuplé, au moins 50 000 habitants le sont ;
3. une situation locale justifie le déclenchement sur un territoire plus petit, par exemple une vallée mal ventilée, une forte exposition près d’un axe routier ou un bassin industriel.

Lorsque la modélisation est disponible, il n’est pas nécessaire d’attendre la confirmation par une station. Sans modélisation, le constat à une station de fond peut caractériser le dépassement selon les modalités du même article.

**[Droit] La procédure repose sur une prévision, pas seulement sur un constat rétrospectif.** Les articles 7, 10 et 12 organisent l’information quotidienne par l’AASQA et le déclenchement sur dépassement prévu. La procédure d’alerte peut aussi être engagée pour la persistance de niveaux d’information PM10 ou ozone. La définition de la persistance donnée à l’article 1 est :

- avec modélisation : dépassement du seuil d’information prévu le jour même et le lendemain ;
- sans modélisation : dépassement mesuré deux jours consécutifs à une station de fond ; les stations peuvent différer à l’intérieur de la zone retenue.

Les articles 13 et 14 prévoient l’expertise et la mise en œuvre des mesures. L’expertise humaine existe donc, mais elle intervient dans un cadre objectivé ; ce n’est pas une catégorie libre permettant de réparer après coup n’importe quel écart.

### 1.2 Pourquoi douze épisodes PM10 peuvent n’avoir aucune station au-dessus de 50

Par ordre de probabilité :

1. **[Inférence forte] Prévision spatiale positive, observation ultérieure négative.** L’AASQA a pu prévoir plus de 50 µg/m³ sur au moins 100 km² ou sur la population requise, puis les stations sont restées sous le seuil. Ce n’est pas exceptionnel pour PM10.
2. **[Inférence forte] Dépassement entre les stations ou hors de leur support de représentativité.** Une surface ou une population exposée peut satisfaire le critère alors qu’aucun point du réseau retenu par le projet ne dépasse 50.
3. **[Inférence] Persistance prévue.** Une procédure d’alerte peut être activée parce que le seuil d’information est prévu deux jours de suite, même si le constat final du jour étudié ne le confirme pas.
4. **[À vérifier] Périmètres et dates non alignés.** Le jour civil local, la zone préfectorale, la zone de surveillance et le sous-ensemble de stations du panel ne sont pas nécessairement identiques. L’agrégation UTC du projet augmente ce risque.
5. **[Possible mais secondaire] Situation locale particulière de l’article 2.**

La possibilité 1 est la plus probable. Le [bilan PREV’AIR 2023 du LCSQA](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf), pages 33–34, donne un ordre de grandeur utile. À J0 et au seuil PM10 aux stations, MOCAGE obtient 52 vrais positifs, 253 faux positifs et un POD de 13 % ; CHIMERE 120 vrais positifs, 574 faux positifs et un POD de 31 %. Après adaptation statistique, CHIMERE atteint 131 vrais positifs, 131 faux positifs, soit un rapport de succès de 50 % et un POD de 33 %. Ce bilan montre deux choses :

- les faux dépassements PM10 prévus sont fréquents ;
- même les chaînes nationales ne récupèrent pas tous les dépassements aux stations.

Pour l’indicateur spatial AMU, la référence du bilan n’est pas une simple liste administrative : c’est l’analyse J−1 obtenue par fusion mesures-modèle. Page 34, l’adaptation statistique de CHIMERE donne 56 vrais positifs, 39 faux positifs et 29 faux négatifs, soit un POD de 65,9 % et un rapport de succès de 58,9 %. C’est le benchmark le plus proche de la question réglementaire.

Le 2/33 serait catastrophique **si** les objets étaient les mêmes. Ils ne le sont pas. La comparaison actuelle ne permet donc ni de rassurer, ni de condamner le système.

### 1.3 Comment vérifier les douze cas

Pour chaque procédure, constituer une ligne d’audit avec :

- heure de publication du bulletin et version éventuelle ;
- polluant, type de procédure et motif : seuil d’alerte ou persistance ;
- jour civil Europe/Paris visé ;
- zone administrative et zone de surveillance ;
- masque prévu au-dessus de 50 ou 80 µg/m³ ;
- superficie et population calculées ;
- stations de fond disponibles au moment de la décision ;
- observations provisoires disponibles à l’émission puis observations validées finales ;
- champ analysé J−1 utilisé comme référence rétrospective.

Les bulletins publics et la liste des procédures donnent le label de décision. Ils ne suffisent pas toujours à reconstruire la superficie ou la population exposée. Si les champs AMU historiques ne sont pas téléchargeables, il faut les demander à Atmo Occitanie. C’est une demande de données précisément formulée, non un échec méthodologique.

Un exemple récent confirme la logique : la préfecture de Haute-Garonne a décrit en juin 2026 un épisode PM10 prévu lié à des poussières désertiques et le passage à l’alerte pour persistance ([communiqué préfectoral](https://www.haute-garonne.gouv.fr/layout/set/print/Actualites/Episode-de-pollution-de-l-air-en-Haute-Garonne-mesures-d-urgence-a-partir-du-24-juin-2026)).

### 1.4 Les deux endpoints honnêtes

**Endpoint A — dépassement aux stations.** C’est le seul entièrement reconstructible avec des observations publiques :

- PM10 : station-jour de fond dont la moyenne du jour civil Europe/Paris dépasse 50 µg/m³ ;
- ozone : station-heure de fond dépassant 180 µg/m³ pour l’information réglementaire ;
- mêmes stations, mêmes heures disponibles et même statut de validation pour tous les systèmes ;
- contingence brute TP, FP, FN, TN, puis POD, FAR, rapport de succès, CSI et intervalle par bootstrap de jours ou d’épisodes.

Le nom à employer est **« dépassements de seuil aux stations »**, jamais « épisodes préfectoraux ».

**Endpoint B — épisode réglementaire spatialisé.** Il faut comparer, pour une émission donnée, le masque prévu au-dessus du seuil avec un champ analysé indépendant ou en validation croisée, puis appliquer exactement superficie et population. L’unité finale devient zone-jour ou département-jour. La liste des procédures évalue ensuite la concordance avec la décision publique, mais n’est pas à elle seule une vérité de concentration.

Pour un entretien, la formulation défendable est :

> La première version comparait un seuil ponctuel à une décision spatiale. J’ai retiré le score comme mesure réglementaire, conservé un endpoint station strictement nommé, et spécifié la reconstruction du véritable endpoint surface-population.

## 2. Les PM10 : variables physiques disponibles et décision à quinze jours

### 2.1 Ce qui est déjà présent dans CAMS

**[Établi]** Le produit régional CAMS Europe est un ensemble de onze modèles à 0,1°, horaire, avec prévisions quotidiennes jusqu’à 96 h. Sa documentation décrit notamment les poussières désertiques dans PM10, les feux, le carbone élémentaire résidentiel dans PM2,5, le sel marin sec dans PM10 depuis novembre 2023, ainsi que l’ammoniac, le nitrate, l’ammonium, le sulfate et la matière organique totale. Les conditions aux limites chimiques viennent du CAMS global. Sources :

- [documentation du produit régional CAMS](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation) ;
- [jeu de données CAMS Europe, DOI 10.24381/a4005cee](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview).

La poussière désertique est donc déjà dans la masse totale PM10 via la chaîne globale-régionale. Une variable explicite reste utile parce qu’un correcteur statistique peut apprendre que le biais de PM10 n’est pas le même pendant une intrusion minérale, un épisode de nitrate d’ammonium ou une période de chauffage. Elle apporte une **étiquette de régime**, pas une masse absente de CAMS.

La documentation CAMS n’est pas parfaitement homogène : la page du jeu de données parle de validation régulière de la poussière, tandis que la documentation technique de mars 2026 classe encore certains traceurs, dont la poussière, parmi les produits expérimentaux. Il faut donc annoncer « traceur CAMS à valider localement », pas « vérité poussière ».

### 2.2 Produits opérationnels poussière

| Produit | Résolution et échéance | Latence / accès | Licence et verdict |
|---|---|---|---|
| CAMS Europe | 0,1°, horaire, 0–96 h | 0–48 h disponibles le matin, puis 49–96 h ; archive glissante d’environ trois ans | CC BY ; meilleur choix car déjà aligné avec la chaîne |
| CAMS global | prévision globale à cinq jours, plusieurs types d’aérosols dont poussière et sel marin | téléchargement ADS ; assimilation satellitaire | libre sous conditions Copernicus ; utile comme contexte ou frontière, moins précis que le régional |
| MONARCH / WMO Barcelona Dust | 0,1°, sorties 3 horaires, 0–72 h | production quotidienne ; THREDDS et archives, mais un compte peut être nécessaire | produits indiqués CC BY 4.0 ; bon contrôle indépendant, plus de friction |

Sources :

- [CAMS global atmospheric composition forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts?tab=overview) ;
- [description MONARCH](https://dust03.bsc.es/about-us/monarch) ;
- [guide des produits Barcelona Dust](https://dust03.bsc.es/products/user-guide) ;
- [modèles et licences](https://dust03.bsc.es/about-us/list-of-models) ;
- [accès aux données](https://dust03.bsc.es/products/data-download).

La réanalyse MONARCH 2007–2016 à 0,1° et trois heures est bien documentée par Di Tomaso et al. (2022), [DOI 10.5194/essd-14-2785-2022](https://doi.org/10.5194/essd-14-2785-2022), mais elle n’est pas un prédicteur opérationnel pour 2024–2026.

### 2.3 Variables par mécanisme

**Chauffage au bois.** Les proxys à faible coût sont degrés-jours de chauffe, température, stabilité/inversion, hauteur de couche limite, vent, jour de semaine et saison. Ils décrivent l’intensité probable, pas les émissions locales exactes. Une méthode européenne de désagrégation temporelle des émissions résidentielles utilise précisément les degrés-jours de chauffe : Guevara et al. (2025), [DOI 10.5194/acp-25-2807-2025](https://doi.org/10.5194/acp-25-2807-2025). Le LCSQA estime que la combustion du bois représente souvent 15 à 25 % des PM10 hivernales, environ 30 % à Poitiers et plus de 35 % dans certaines agglomérations telles que Grenoble ou Bordeaux ([synthèse LCSQA](https://www.lcsqa.org/fr/actualite/etude-impact-combustion-biomasse-concentrations-particules-fines-pm10)). Ce sont des parts de source, pas des gains de prévision.

**Agriculture.** Les variables pertinentes sont NH₃ prévu, nitrate et ammonium CAMS, température, humidité, vent, pluie, stabilité et calendrier d’épandage régional. Un simple mois de l’année ne remplace pas les pratiques et la météorologie. L’INERIS rappelle que l’agriculture représente environ 94 % des émissions anthropiques françaises d’ammoniac et que le nitrate d’ammonium peut dépasser 50 % de PM10 lors de certains épisodes ([dossier agriculture de l’INERIS](https://www.ineris.fr/fr/risques/dossiers-thematiques/qualite-air/sources-pollution-atmospherique/agriculture)). La littérature française documente la formation printanière et les scénarios de réduction, notamment :

- Viatte et al. (2020), [DOI 10.5194/acp-20-16055-2020](https://doi.org/10.5194/acp-20-16055-2020) ;
- Fortems-Cheiney et al. (2021), [DOI 10.5194/acp-21-875-2021](https://doi.org/10.5194/acp-21-875-2021) ;
- Petetin et al. (2020), [DOI 10.5194/acp-20-577-2020](https://doi.org/10.5194/acp-20-577-2020).

**Remise en suspension routière.** Un proxy météo seul est fragile. NORTRIP utilise trafic, composition du parc, vitesse, pneus, précipitation, vent, température, rayonnement, humidité et entretien de la chaussée : Denby et al. (2019), [DOI 10.5194/acp-19-11199-2019](https://doi.org/10.5194/acp-19-11199-2019). HERMESv3 représente le rechargement de la chaussée après la pluie et le lessivage : Guevara et al. (2020), [DOI 10.5194/gmd-13-873-2020](https://doi.org/10.5194/gmd-13-873-2020). Sans trafic ni état de chaussée, pluie cumulée depuis le dernier événement, vent et sécheresse donnent seulement un indicateur qualitatif.

**Sel marin.** Le traceur de sel marin sec de CAMS régional est préférable à un proxy artisanal. À défaut, distance à la côte, direction et vitesse du vent, stabilité et humidité sont physiquement justifiés ; Ovadnevaite et al. (2019) documentent fortement la dépendance au vent et à l’état de mer, [DOI 10.5194/acp-19-4459-2019](https://doi.org/10.5194/acp-19-4459-2019).

### 2.4 Peut-on promettre un gain quantitatif ?

Non. Je n’ai trouvé aucune étude primaire qui isole, sur une correction statistique de PM10 déjà alimentée par CAMS, le gain marginal de chacune des familles « poussière explicite », « chauffage », « épandage », « sel marin » ou « remise en suspension ». Les travaux cités quantifient des contributions de sources ou des performances de modèles complets, pas les points de RMSE gagnés par l’ajout d’un traceur dans ce pipeline précis.

Il serait trompeur de convertir une contribution de 25 % de PM10 en un gain attendu de 25 % de RMSE. Les variables peuvent être redondantes avec CAMS, et les événements rares peuvent améliorer le rappel tout en dégradant la moyenne.

Le seul test raisonnable avant le dépôt est une ablation gelée :

1. ajouter en bloc les traceurs CAMS déjà alignés — poussière PM10, sel marin sec, NH₃, nitrate, ammonium, sulfate, carbone élémentaire résidentiel et feux ;
2. conserver exactement les mêmes plis doubles aveugles, hyperparamètres et périodes ;
3. publier le delta de RMSE, mais aussi POD/FAR/CSI PM10 au seuil de 50 ;
4. stratifier a priori trois régimes seulement : poussière, hiver froid, printemps ammoniacal ;
5. ne conserver le bloc que si l’intervalle de confiance par jours ne recouvre pas un effet négligeable choisi avant le calcul.

Coût estimé : quelques heures si les variables CAMS sont déjà archivées, un à deux jours sinon. MONARCH, un modèle de remise en suspension ou un calendrier agricole fin sont des travaux postérieurs au dossier.

## 3. Directive (UE) 2024/2881 : obligations et portée du projet

### 3.1 Calendrier juridique

La source faisant foi est la [directive (UE) 2024/2881 sur la qualité de l’air ambiant](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881).

- **[Droit] Article 31 :** transposition au plus tard le 11 décembre 2026.
- **[Droit] Article 19, paragraphe 4 :** lorsqu’entre le 1er janvier 2026 et le 31 décembre 2029 un niveau dépasse une valeur limite qui devra être respectée en 2030, une feuille de route doit être établie dans les deux ans, sauf démonstration d’atteinte dans les délais.
- **[Droit] Annexe I :** nouvelles valeurs limites applicables en 2030, dont PM2,5 annuel 10 µg/m³, PM10 annuel 20 µg/m³, PM10 journalier 45 µg/m³ avec 18 dépassements autorisés, et NO₂ annuel 20 µg/m³.

Au 8 août 2026, la consultation française sur la révision des normes reste un projet de transposition, pas le droit positif applicable aux procédures actuelles : [consultation du ministère](https://www.consultations-publiques.developpement-durable.gouv.fr/projet-de-decret-relatif-a-la-revision-des-normes-a3369.html).

### 3.2 Quand la modélisation devient obligatoire

**[Droit] Article 8, paragraphe 2.** Dans les zones dépassant le seuil d’évaluation, les mesures fixes restent nécessaires. La modélisation ou les mesures indicatives peuvent les compléter.

**[Droit] Article 8, paragraphe 3.** À compter de deux ans après l’adoption des actes d’exécution pertinents, les États doivent utiliser, en plus des mesures fixes, une application de modélisation ou des mesures indicatives dans toutes les zones où les niveaux dépassent une valeur limite ou cible de l’annexe I. L’objectif est d’évaluer correctement l’étendue spatiale des dépassements et les concentrations, au moins tous les cinq ans.

Les règles techniques ont été adoptées le 9 juin 2026 par la [décision d’exécution (UE) 2026/1208](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=OJ:L_202601208). La lettre de l’article 8, paragraphe 3, conduit donc au 9 juin 2028. L’article 11 de la décision prévoit cependant que ses règles techniques sont applicables à partir du 30 juin 2028. Il faut conserver ces deux dates dans le calendrier : obligation issue de la directive à compter du 9 juin, règles d’exécution applicables le 30 juin. Dans tous les cas, la transposition de décembre 2026 n’est pas l’échéance opérationnelle de cette obligation additionnelle.

**[Droit] Article 8, paragraphes 4 et 5.** Sous les seuils d’évaluation, la modélisation, les mesures indicatives ou l’estimation objective peuvent suffire ; les résultats de modélisation participent à l’évaluation réglementaire selon les règles prévues.

**[Droit] Article 8, paragraphe 6.** Si le modèle révèle un dépassement hors de la représentativité des mesures fixes, une mesure fixe ou indicative supplémentaire peut être implantée sur le point critique. Si l’État choisit de ne pas ajouter cette mesure, le dépassement modélisé est utilisé pour l’évaluation. Lorsqu’une mesure est ajoutée, le texte fixe un délai de deux années civiles pour une mesure fixe et d’une année pour une mesure indicative.

**[Droit] Annexe IV, partie D.** La conception du réseau de mesures doit être appuyée au minimum par la modélisation ou des mesures indicatives et réexaminée au moins tous les cinq ans. Il faut donc produire davantage qu’une carte illustrative : représentativité, localisation des maxima, sources et couverture du territoire entrent dans la conception du réseau.

### 3.3 Les objectifs de qualité de modélisation

L’annexe V de la directive définit des ratios maximaux de qualité de modélisation, avec une distinction entre moyennes de long et de court terme :

| Polluant | Long terme | Court terme |
|---|---:|---:|
| PM2,5 | 1,7 | 2,5 pour 24 h |
| PM10 | 1,3 | 2,2 pour 24 h |
| NO₂, SO₂, NOx | 1,4 | 3,2 pour 24 h ou 1 h |
| Ozone | — | 2,2 pour 8 h |

Le Model Quality Indicator est fondé sur la RMSE normalisée par la combinaison de l’incertitude du modèle et de l’incertitude de mesure. L’objectif est satisfait lorsque l’indicateur ne dépasse pas 1 pour au moins 90 % des points de mesure disponibles, selon les modalités de l’annexe.

La décision 2026/1208 rend le protocole concret :

- **articles 2 et 3 :** cohérence des temps de moyenne, résolution appropriée, émissions spatialisées et temporalisées avec spéciation, météorologie, fond, dispersion, relief et sources pertinentes ; contrôle qualité des entrées ;
- **article 3 :** validation dans les environnements de station pertinents ;
- **annexe II :** lorsqu’une fusion ou assimilation utilise les observations, validation leave-one-out obligatoire : retirer la station, recalculer le champ, extraire la valeur au point retiré et répéter pour toutes les stations.

Le [PDF officiel de la décision](https://eur-lex.europa.eu/legal-content/FR/TXT/PDF/?uri=OJ:L_202601208) est le document à joindre au dossier de travail.

**FAIRMODE n’est pas le texte opposable.** Le guide FAIRMODE fournit les outils et conventions scientifiques qui ont inspiré et accompagnent ces exigences. La [guidance FAIRMODE WG3 Forecast, version 2026](https://knowledge4policy.ec.europa.eu/file/fairmode-guidance-wg3-forecast-version-2026_en), JRC146007, décrit notamment un indicateur de qualité pour la prévision. Mais un MQI de prévision calculé selon ce guide n’est pas automatiquement le MQI réglementaire de l’annexe V. La version 2026 est une guidance de référence, non « la norme qui fait foi » à la place de la directive et de la décision d’exécution.

### 3.4 Prévision, information et plans à court terme

**[Droit] Article 15, paragraphes 3 et 4.** Lorsqu’un seuil d’alerte est dépassé ou devrait l’être selon une prévision fondée sur la modélisation ou un autre outil, les mesures d’urgence prévues par le plan d’action à court terme sont appliquées, le cas échéant, sans retard injustifié. Pour un seuil d’alerte ou d’information mesuré ou prévu, le public doit être informé dans les plus brefs délais et, autant que possible, en quelques heures.

**[Droit] Article 20.** Des plans d’action à court terme doivent être établis en cas de risque de dépassement d’un seuil d’alerte. Pour l’ozone, une exception demeure lorsqu’il n’existe pas de potentiel significatif de réduction. Pour les particules, lorsque le potentiel de réduction est fortement limité par la géographie, la météorologie ou le chauffage domestique, le plan peut se concentrer sur la protection et l’information. Les mesures envisagées peuvent viser transport, travaux, industrie, agriculture, produits et chauffage résidentiel.

L’annexe I de la nouvelle directive fixe à terme :

- PM2,5 : information/alerte à 50 µg/m³ en moyenne journalière ;
- PM10 : information/alerte à 90 µg/m³ en moyenne journalière ;
- ozone : information 180 µg/m³ et alerte 240 µg/m³ en moyenne horaire.

Pour les particules, le seuil d’alerte est lié à une moyenne journalière sur trois jours consécutifs, ou moins lorsque la zone représentative dépasse 100 km² ou couvre une zone plus petite entière selon le texte. Ces valeurs ne remplacent pas encore les seuils français 50/80 tant que la transposition applicable n’est pas entrée en vigueur.

### 3.5 Ce que cela implique pour une AASQA

**[Inférence opérationnelle à partir des textes]** Entre 2026 et 2030, les chantiers probables sont :

- cartographier l’étendue des dépassements, l’exposition de la population et les sources ;
- appuyer la conception et la révision du réseau par des champs et des cartes de représentativité ;
- produire une validation indépendante, notamment leave-one-out pour toute fusion ;
- documenter émissions, spéciation, météorologie, résolution, incertitudes et versions ;
- préparer feuilles de route, scénarios et projections vers les normes 2030 ;
- maintenir prévisions à court terme, indices et information publique ;
- développer les mesures des polluants supplémentaires et les super-sites prévus par la directive.

Les compétences valorisées sont donc à l’intersection de la modélisation, de la géostatistique, du contrôle qualité, de la traçabilité des données et de la communication réglementaire.

### 3.6 Où le projet a de la valeur — et où il n’en a pas encore

Le projet a une valeur directe pour :

- le post-traitement de prévisions à court terme ;
- l’estimation du risque de dépassement aux stations ;
- l’étude de la transférabilité vers des stations cachées ;
- la production rapide de champs exploratoires ;
- la mise en place de contrôles de qualité et de comparaisons de chaînes.

Il ne démontre pas encore :

- la conformité réglementaire d’un champ au sens de l’annexe V ;
- l’étendue spatiale légale d’un dépassement ;
- la représentativité d’un point de mesure ;
- un champ valable « partout » entre les stations ;
- une fusion validée indépendamment si la station sert à la fois d’ancre et de juge ;
- l’aptitude à représenter un hotspot routier NO₂ avec une maille de 0,1°.

Le post-traitement statistique est donc pertinent, mais il devient réglementairement utile seulement s’il est intégré à une chaîne documentée, avec support spatial défini, validation indépendante, incertitude et provenance. Le chiffre de 96,2 % de stations avec MQI de prévision inférieur ou égal à 1 ne doit pas être présenté comme une conformité à la directive sans démontrer l’identité de la formule, du temps de moyenne, du domaine et du protocole leave-one-out.

## 4. Valider un champ plutôt que ses seuls points d’appui

### 4.1 Protocole minimal défendable

La règle est simple : une observation utilisée pour construire un champ ne peut pas valider ce même champ.

Le protocole recommandé est :

1. choisir une station externe ;
2. la retirer de toutes les étapes : apprentissage du correcteur, calcul du biais récent, krigeage, calibration et sélection d’hyperparamètres ;
3. reconstruire le champ avec les seules stations restantes ;
4. extraire la valeur au point retiré ;
5. répéter sur toutes les stations ;
6. effectuer en plus une sensibilité par blocs spatiaux et par mois futurs, afin que les voisins immédiats et les périodes proches ne rendent pas l’épreuve artificiellement facile.

C’est désormais exactement le principe de l’annexe II de la décision 2026/1208. Le rapport LCSQA sur l’[évaluation des cartes analysées selon FAIRMODE](https://www.lcsqa.org/system/files/media/documents/lcsqa2015_evaluation_cartes_analysees_fairmode_vf-drc-16-152350-08456a_0.pdf), page 3, recommandait déjà des observations non utilisées dans la construction, un leave-one-out, des sous-ensembles indépendants ou des répétitions de validation croisée.

PREV’AIR applique une correction statistique aux stations puis spatialise notamment par krigeage pour produire les [prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees). Ses pages publiques d’[évaluation](https://www.prevair.org/prevair-plus/evaluation) publient principalement des scores aux stations. Le bilan annuel LCSQA complète cette lecture par les contingences de dépassement et l’indicateur spatial AMU.

### 4.2 Métriques utiles

**Aux stations exclues :**

- biais, MAE, RMSE et corrélation ;
- MQI réglementaire lorsque toutes ses conditions sont satisfaites ;
- couverture et largeur des intervalles de prédiction ;
- performance par typologie, densité de réseau, distance au plus proche appui, relief et région ;
- scores au seuil : POD, FAR, rapport de succès, CSI et tableaux bruts.

**Pour un champ, seulement avec une référence maillée indépendante :**

- biais de superficie au-dessus du seuil ;
- population exposée prévue contre analysée ;
- intersection sur union, CSI spatial, distance des contours ;
- FSS à plusieurs rayons pour tolérer un petit décalage spatial ;
- SAL si l’objet « panache » est physiquement identifiable et si la référence maillée est assez indépendante.

**Diagnostics, pas scores de vérité :**

- variogramme des résidus ;
- Moran I ou structure d’autocorrélation ;
- variance de krigeage.

Le FSS et SAL deviennent du folklore si la « vérité maillée » est le même champ fusionné avec les mêmes stations. Avec seulement des stations, ils ne peuvent pas mesurer une surface observée. Le variogramme aide à voir ce qui reste spatialement structuré, mais ne donne pas à lui seul une erreur en un point non instrumenté.

### 4.3 Circularité et formulation honnête

La variante ancrée peut être décrite ainsi :

> Le champ est conditionné par les observations disponibles. Sa concordance aux points d’ancrage mesure la cohérence de la fusion, pas sa capacité de généralisation. Cette dernière est estimée par retrait complet des stations et par blocs spatiaux.

Une carte opérationnelle peut légitimement utiliser toutes les stations après la validation. C’est seulement le calcul de performance qui doit reconstruire un champ sans le point jugé.

### 4.4 Le « plancher de représentativité »

Comparer deux stations d’une même commune est un bon contrôle empirique, mais pas une borne irréductible :

- une commune n’est pas une unité physique de représentativité ;
- deux stations peuvent être de typologies différentes — fond, trafic, industriel ;
- leur écart contient un gradient réel, l’incertitude de mesure et des différences de hauteur ou de micro-environnement ;
- une RMSE modèle-station et une dispersion interstations ne répondent pas au même problème.

La formulation acceptable est :

> La dispersion entre stations proches et comparables donne un ordre de grandeur de la variabilité sub-maille que le champ à 0,1° ne peut représenter ; elle n’est pas une limite théorique de toute méthode.

Pour la chiffrer correctement, apparier seulement des stations de même typologie et de sources dominantes comparables, utiliser le même jour et la même grandeur réglementaire, tracer la semi-variance en fonction de la distance, séparer autant que possible l’incertitude instrumentale et publier les quantiles par classe de distance. Une campagne mobile ou des stations temporaires aveugles restent le meilleur test d’un point non instrumenté.

La décision 2026/1208 apporte désormais une méthode harmonisée de représentation spatiale : analyse de la localisation et des sources, identification de zones de concentration similaire, cartes de représentativité pour chaque point et révision lors de changements significatifs. Elle ne définit pas la représentativité par la simple dispersion de stations d’une commune.

## 5. Microcapteurs comme ancrages : oui, sous conditions

### 5.1 Doctrine et performances réalistes

**[Établi]** La doctrine française ne classe pas un appareil comme « mesure indicative » parce qu’il est vendu comme microcapteur. L’aptitude dépend de la démonstration métrologique, du polluant, des conditions et de l’usage.

Le [premier essai national d’aptitude des microcapteurs du LCSQA](https://www.lcsqa.org/fr/rapport/premier-essai-national-daptitude-des-micro-capteurs-eamc-pour-la-surveillance-de-la-qualite) a montré une forte hétérogénéité en conditions de terrain. Même les systèmes multisenseurs pouvaient présenter pour PM2,5 une pente de 2,25 ; pour NO₂, une variabilité d’environ 41 % et des R² de 0,5 à 0,75 selon les systèmes. Ce ne sont pas des ancrages bruts acceptables.

Le [protocole LCSQA pour les microcapteurs NO₂](https://www.lcsqa.org/fr/rapport/2016/mines-douai/protocole-determination-caracteristiques-performance-metrologique-micro-cap) insiste sur la caractérisation terrain et l’incertitude. Pour les gaz, CEN/TS 17660-1:2021 fournit un cadre d’évaluation des systèmes de capteurs ([notice de la norme](https://www.dinmedia.de/en/pre-standard/din-cen-ts-17660-1/339188269)). Le NO₂ électrochimique reste plus difficile que les particules optiques à cause des interférences, de la température, de l’humidité et de la dérive.

L’avis relayé par [Atmo France sur les microcapteurs](https://www.atmo-france.org/actualite/avis-de-lanses-sur-les-microcapteurs) souligne l’hétérogénéité, la documentation parfois insuffisante des algorithmes et l’intérêt de ces outils pour la connaissance et la sensibilisation lorsqu’ils sont accompagnés. Ils complètent le réseau de référence ; ils ne déclenchent pas seuls une procédure réglementaire.

### 5.2 La méthode SESAM

La méthode nationale SESAM du LCSQA est très proche du besoin :

- prétraitement, calibration et élimination des valeurs aberrantes ;
- prise en compte de la dérive ;
- krigeage avec dérive externe combinant modèle, stations fixes et capteurs mobiles ;
- pondération par une variance d’erreur de mesure.

Sources : [note méthodologique SESAM](https://www.lcsqa.org/system/files/media/documents/LCSQA_livrable_2021_note_m%C3%A9thodo_cartographie_capteurs.pdf), pages 2 et 5–6, et [guide de cartographie à partir de capteurs](https://www.lcsqa.org/system/files/media/documents/LCSQA2020_guide_cartographie_capteurs.pdf), pages 4 et 10–11.

Dans l’expérience nantaise associant 16 stations fixes et 19 capteurs mobiles PM10, la fusion a réduit un biais d’environ 8 % pour le modèle seul à 2,5 % pour le champ fusionné. C’est un résultat réel mais local, sur PM10, et non une garantie pour le NO₂ ou les pics : Schneider et al. (2020), [DOI 10.1016/j.envint.2020.105965](https://doi.org/10.1016/j.envint.2020.105965).

### 5.3 Flux ouverts disponibles

- [Sensor.Community](https://github-wiki-see.page/m/opendata-stuttgart/meta/wiki/EN-APIs) fournit API et archives à cinq minutes, une heure ou un jour, avec position et certaines métadonnées. La calibration, l’implantation et la maintenance ne sont toutefois pas suffisamment garanties pour en faire des ancrages automatiques.
- Le projet français [CAPSULE / AERIS](https://www.aeris-data.fr/en/projects/capsule-2/) agrège Sensor.Community, PurpleAir, Polluscope, Geod’Air et d’autres sources depuis 2020, avec correction, validation et mise à disposition ; c’est le flux de recherche français le plus prometteur pour une expérimentation.
- [Atmo Data](https://www.atmo-france.org/article/atmo-data-un-acces-unique-aux-donnees-produites-par-les-aasqa) offre un accès ODbL aux données produites par les AASQA, dont indices, épisodes et émissions. Ce n’est pas en soi un réseau national homogène de capteurs citoyens calibrés.

### 5.4 Le risque symétrique : propager la dérive

Un ancrage faux peut détériorer une zone entière. Si le krigeage lui accorde un poids élevé, une dérive lente est transformée en biais spatial cohérent et paraît crédible.

Garde-fous nécessaires :

- co-localisation initiale et finale avec une référence, plus une référence mobile au milieu de la campagne ;
- calibration dépendante de température et humidité, ajustée uniquement sur des données antérieures ;
- seuils d’alerte pour rupture, dérive et incohérence entre capteurs proches ;
- variance d’erreur propre à chaque capteur et poids décroissant lorsque la qualité baisse ;
- conservation des données brutes et corrigées ;
- validation leave-one-sensor-out et leave-one-site-out ;
- aucune auto-validation sur le point ayant servi à calibrer ;
- drapeau clair « complémentaire / non réglementaire » sur toute carte publique.

### 5.5 Un partenariat crédible pour un candidat junior

Proposition raisonnable :

> Pilote de trois mois avec une collectivité et deux établissements scolaires : huit à douze capteurs PM2,5/PM10, co-localisation de deux à quatre semaines au début, à la fin et sur un site tournant, tableau de bord qualité, carte fusionnée avec incertitude, validation par retrait de site et atelier de restitution.

Livrables :

- protocole d’implantation et de consentement ;
- registre de calibration et maintenance ;
- données brutes, corrigées et métadonnées ;
- carte avec incertitude et zones non interprétables ;
- rapport comparant modèle seul, réseau réglementaire et fusion ;
- restitution aux partenaires sans promesse réglementaire.

Commencer par les particules est crédible. Promettre immédiatement une carte NO₂ quantitative à partir de capteurs électrochimiques ne l’est pas. Le [groupe FAIRMODE WG6 consacré aux capteurs et à la fusion](https://knowledge4policy.ec.europa.eu/fairmode/sensors-data-fusion-working-group-6_en) fournit un cadre européen pertinent.

## 6. Audit adverse du dossier

### 6.1 Les objections qu’un évaluateur expérimenté formulera

| Priorité | Affirmation attaquée | Motif précis | Décision |
|---|---|---|---|
| P0 | « J+2 » pour la tranche 25–48 h | contradiction avec la convention du dépôt ; le code imprime le numéro de tranche comme numéro de jour | corriger en J+1 ou écrire seulement « échéances 25–48 h » |
| P0 | grandeur journalière | agrégation UTC, pas jour civil Europe/Paris ; risque de mélange de cycles | refaire l’audit temporel avant de citer les scores |
| P0 | « 2/33 épisodes détectés » | endpoint ponctuel comparé à une décision spatiale et prévisionnelle | retirer comme score réglementaire |
| P0 | « PARTOUT » | validation à des stations réglementaires cachées, pas en tout point du territoire | remplacer par « stations non vues » ou « sans historique local » |
| P1 | champ corrigé 0,1° | absence de validation leave-one-out complète du champ ancré | présenter comme exploratoire |
| P1 | comparaison à la chaîne AASQA | version, heure de disponibilité, support spatial et usage des observations doivent être identiques | documenter un contrat de comparabilité |
| P1 | conformité FAIRMODE / directive | MQI de prévision et MQI réglementaire confondus | séparer explicitement les deux |
| P1 | gain opérationnel | les observations finales peuvent ne pas avoir été disponibles à l’heure d’émission | rejouer avec des instantanés ou déclarer l’évaluation rétrospective |
| P2 | nouveauté « ML corrige CAMS » | une chaîne CAMS-MOS opérationnelle existe déjà | revendiquer le protocole et le périmètre, pas l’idée générique |

### 6.2 La question la plus destructrice

> Pour quel instant d’émission et quel jour civil exact chaque score est-il calculé, et pouvez-vous montrer que chaque heure, observation et prédicteur était disponible à cet instant et provenait du même cycle de prévision ?

Aujourd’hui, le dépôt ne permet pas de répondre complètement « oui » :

- scripts/fit_mos.py définit 1–24, 25–48 et 49–72 h ;
- scripts/methode_maximale.py et scripts/cible_journaliere.py impriment « J+numéro de tranche » ;
- scripts/cible_journaliere.py groupe timestamp_utc par floor du jour UTC ;
- la convention documentée ailleurs appelle correctement 1–24 h J0 et 25–48 h J+1.

Si plusieurs cycles quotidiens sont concaténés, la journée UTC associée à la tranche 25–48 h peut combiner l’heure 00 issue d’une sortie plus ancienne et les heures 01–23 issues de la suivante. **[À vérifier sur les clés de données]** Il faut contrôler forecast_reference_time, valid_time, leadtime et les doublons avant d’affirmer que c’est effectivement le cas. Le passage à Europe/Paris crée en plus des jours de 23 ou 25 heures aux changements d’heure ; un seuil fixe de 18 heures valides sur 24 doit alors être redéfini proportionnellement ou selon la règle métier.

La réponse honnête en entretien est :

> J’ai trouvé ce défaut lors de l’audit final. J’ai retiré les libellés J+2, défini le produit par cycle, lead et jour civil, puis rejoué les agrégations. Les anciens chiffres ne sont pas cités tant que ce contrôle n’est pas passé.

S’il n’est pas possible de rejouer avant le dépôt, écrire « fenêtre de validité UTC 25–48 h » et retirer toute prétention de prévision d’un jour civil.

### 6.3 Les chiffres ozone peuvent-ils coexister ?

Mathématiquement oui, parce qu’ils ne portent pas sur les mêmes objets :

- facteur 3,6 : détection de dépassements selon un seuil et un budget de fausses alertes particuliers ;
- 12/12 : rappel des procédures zone-jour ozone ;
- 473 faux positifs : très faible précision à ce point de fonctionnement ;
- facteur 1,18 avec intervalle contenant zéro : absence de démonstration sous double aveugle.

Rédactionnellement, non : les placer sous une même promesse « meilleure détection d’épisodes » invite le lecteur à les fusionner. Le message honnête est :

> Sur l’échantillon rétrospectif, le modèle classe mieux certaines situations ozone, mais cet avantage n’est pas établi en transfert double aveugle et le seuil qui récupère toutes les procédures produit trop de fausses alertes pour un usage décisionnel.

Le 12/12 n’est pas un chiffre à mettre en avant avec 473 faux positifs. Le facteur 3,6 peut rester dans une annexe méthodologique si l’endpoint, le budget de fausses alertes et l’intervalle sont imprimés sur la même figure.

### 6.4 La moyenne glissante n’est pas un aveu de faiblesse

La persistance du biais est un résultat classique du post-traitement de qualité de l’air. Neal et al. (2014) ont montré qu’une correction simple par résidus récents réduisait fortement le biais opérationnel jusqu’à plusieurs jours : [DOI 10.1016/j.atmosenv.2014.09.004](https://doi.org/10.1016/j.atmosenv.2014.09.004). Petetin et al. (2022) comparent moyenne mobile, correction quantile, filtre de Kalman, analogues et gradient boosting ; les méthodes sophistiquées améliorent souvent la RMSE mais lissent les extrêmes, tandis que des corrections simples restent compétitives pour CSI et PSS : [DOI 10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

Il n’existe pas de chiffre universel pour « l’apport marginal attendu du ML au-dessus d’une moyenne glissante ». Il dépend du modèle chimie-transport, du réseau, de l’échéance, du polluant et de l’endpoint. Les +2,5 points NO₂ du projet sont donc modestes mais parfaitement publiables s’ils sont accompagnés de leur incertitude et de leur coût. Le résultat intéressant est que 42,9 points sur 44,3 viennent d’un mécanisme simple et auditable ; attribuer les 44,3 au LightGBM serait trompeur.

### 6.5 Le seul chiffre à garder

Après correction de la convention temporelle, je garderais :

> **96,2 % des stations NO₂ ont un MQI de prévision inférieur ou égal à 1 à J+1, contre 41,4 % pour CAMS brut.**

Pourquoi :

- le score est station par station, pas dominé par quelques grands sites ;
- il parle à une AASQA et peut être relié à une pratique FAIRMODE de prévision ;
- il compare explicitement au brut ;
- il est moins facile à survendre qu’un facteur de détection choisi sur un seuil ;
- il illustre la fiabilité du réseau plutôt qu’une moyenne nationale.

Conditions obligatoires sur la même ligne ou en note : **MQI de prévision, non conformité réglementaire ; protocole exact ; horizon corrigé ; disponibilité des observations ; intervalle d’incertitude**. Si l’audit temporel modifie ce chiffre, le remplacer par sa valeur rejouée. Aucun chiffre actuel ne vaut de conserver une convention erronée.

## 7. Ce qui manquait au brief

### 7.1 Angles morts supplémentaires

**Le statut temporel des observations.** Une observation validée plusieurs semaines plus tard n’était pas nécessairement disponible pour une prévision opérationnelle. Il faut distinguer temps réel provisoire, données corrigées et données validées, et idéalement conserver un instantané « as of ».

**Les changements de version en amont.** CAMS, GEOS-CF, inventaires et stations évoluent. Une amélioration apparente peut coïncider avec une rupture de version. Chaque paire doit porter version du modèle, cycle, téléchargement et statut de l’observation.

**Les déménagements et changements de station.** Un identifiant peut survivre à un changement de coordonnées, d’instrument ou de typologie. Des variables statiques jointes à la coordonnée actuelle peuvent fuiter ou fausser l’historique. Utiliser des métadonnées datées.

**Le support physique du champ.** Une maille CAMS à 0,1° décrit surtout un fond. Une station trafic NO₂ mesure un micro-environnement. Un correcteur ponctuel par typologie ne transforme pas automatiquement le champ régional en carte de rue. Il faut séparer « champ de fond » et « prédiction au site ».

**Les sources naturelles dans le droit.** Les poussières désertiques ne sont pas seulement une variable prédictive ; leur attribution documentée peut intervenir dans le traitement réglementaire des contributions naturelles. Le traceur doit donc garder provenance et incertitude.

**L’incertitude en dehors du réseau.** Une carte sans intervalle ou drapeau d’extrapolation invite le lecteur à confondre continuité graphique et connaissance. Distance au réseau, densité, typologie hors domaine et désaccord d’ensemble doivent alimenter une carte de confiance.

### 7.2 La question que j’aurais posée

> Quel produit opérationnel exact le modèle prétend-il améliorer : une prévision émise à quelle heure, disponible avec quelles données, valable sur quel jour civil, pour quel support spatial et pour quelle décision ?

Cette question précède le choix de LightGBM, du krigeage ou des variables. Sans contrat de produit, la meilleure validation statistique peut mesurer un objet qui n’existe pas en exploitation.

### 7.3 Travaux très proches à citer

Bertrand et al. (2023) est le travail le plus proche : post-traitement MOS de l’ensemble CAMS aux stations européennes pour ozone et PM10, avec méthodes linéaires pénalisées et autres modèles. Les réductions de RMSE atteignent environ 32 % pour le maximum journalier ozone et 45 % pour la moyenne journalière PM10 par rapport au CAMS brut : [DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

Il faut s’en distinguer par les éléments réellement spécifiques :

- quatre polluants en France ;
- validation station et mois cachés ensemble ;
- séparation usage avec et sans historique local ;
- comparaison à une chaîne en service, si elle est rendue strictement comparable ;
- audit de déploiement et de provenance.

Depuis, CAMS exploite lui-même une chaîne CAMS-MOS par forêt aléatoire, alimentée par modèle, météorologie et observations récentes, à des milliers de stations et jusqu’à 96 h : Garrigues et al. (2025), [DOI 10.5194/gmd-18-6835-2025](https://doi.org/10.5194/gmd-18-6835-2025). La nouveauté ne peut donc pas être « appliquer du ML à CAMS ». Elle doit être le protocole français, l’audit de transférabilité, les benchmarks et l’honnêteté sur le périmètre.

### 7.4 Le plus petit geste à plus forte valeur

Créer une page unique intitulée **Contrat de validité temporelle et spatiale**, puis corriger tous les libellés à partir de cette page. Pour chaque résultat :

| Champ | Exemple exigé |
|---|---|
| cycle d’émission | 00 UTC du 14 janvier |
| disponibilité réelle | heure de téléchargement et données présentes |
| échéances | 25–48 h |
| nom métier | J+1 seulement si le jour civil est démontré |
| jour cible | Europe/Paris, avec règle DST |
| support | station, maille de fond, zone ou département |
| vérité | provisoire disponible à l’émission ou validée finale |
| baseline | nom, version, cycle, usage éventuel d’observations |
| validation | station/mois cachés, blocs, intervalle |

Ajouter un test de dix horodatages, incluant les deux changements d’heure, qui affiche cycle, lead, UTC, heure locale et jour cible. Ce geste est plus important qu’un nouveau prédicteur PM10 avant le dépôt.

### 7.5 Le risque de ridicule maximal

Le risque n’est plus seulement d’appeler J0 « J+1 ». Sa jumelle est d’appeler **J+2 une tranche 25–48 h** tout en regroupant les valeurs par jour UTC, puis d’appeler **PARTOUT** une validation effectuée uniquement à des stations du réseau.

Trois remplacements simples :

- « J+2 » → « 25–48 h » tant que la reconstruction du jour civil n’est pas validée ;
- « PARTOUT » → « sans historique du site, évalué sur des stations non vues » ;
- « épisodes détectés » → « dépassements aux stations » ou « procédures zone-jour », selon l’objet réellement mesuré.

## Plan d’action jusqu’au dépôt

### Aujourd’hui — indispensable

1. Corriger la nomenclature 25–48 h et chercher toutes les occurrences de J+2.
2. Auditer cycle, lead, valid_time, fuseau Europe/Paris, DST et doublons.
3. Retirer 2/33 comme score de performance réglementaire.
4. Remplacer PARTOUT par un terme limité aux sites de mesure non vus.

### Prochaine journée — indispensable

5. Produire le contrat de validité sur une page.
6. Rejouer les agrégations journalières sur un cycle cohérent et le jour civil local.
7. Ajouter la contingence brute et les intervalles groupés par jour ou épisode.
8. Documenter exactement la chaîne AASQA comparée et son heure de disponibilité.

### Avant le dépôt — si les données existent

9. Examiner manuellement les 33 procédures PM10 et demander les champs AMU pour les douze cas sans station.
10. Séparer la page « stations » de la page « décision spatiale ».
11. Ajouter l’encadré directive 2024/2881 / décision 2026/1208, sans revendiquer de conformité.
12. Si le temps reste disponible, tester une seule ablation du bloc de spéciation CAMS PM10.

### Après le dépôt — utile mais non prioritaire

- validation leave-one-out complète du champ ;
- partenariat microcapteurs PM avec incertitude ;
- contrôle MONARCH indépendant ;
- reconstruction surface-population des épisodes ;
- modèle dédié de remise en suspension ou émissions agricoles.

## Conclusion

Le dossier a un résultat solide : il montre qu’une correction simple et auditable enlève une grande part du biais de CAMS, puis mesure honnêtement ce que l’apprentissage ajoute. Sa faiblesse actuelle n’est pas le manque de sophistication. C’est l’absence d’un contrat parfaitement stable entre cycle, échéance, jour civil, support spatial et endpoint.

Corriger ce contrat transforme plusieurs « mauvais résultats » en conclusions professionnelles :

- 2/33 n’est pas un échec du modèle mais un endpoint invalide ;
- 12/12 avec 473 faux positifs n’est pas un succès opérationnel ;
- +2,5 points au-dessus d’une moyenne glissante est un apport marginal crédible ;
- une station cachée n’est pas « partout » ;
- un MQI de prévision n’est pas une conformité réglementaire ;
- une carte ancrée doit être jugée avec ses ancrages retirés.

C’est précisément le type d’autocritique qu’une AASQA peut valoriser chez un candidat junior : savoir améliorer un modèle, mais surtout savoir définir ce qu’il prédit, à quelle heure, où, et avec quelle preuve.
