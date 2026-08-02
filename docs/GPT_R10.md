# GPT R10 — Signaux observables là où la correction échoue

> Recherche arrêtée au 2 août 2026.  
> **Publié** : contenu explicite d’une source citée. **Constat projet** : résultat fourni dans le prompt. **Jugement** : interprétation pour ce système. **À vérifier** : information non établie par une source accessible.

## Réponse courte

**Jugement.** Je n’ai trouvé aucun signal unique qui soit à la fois antérieur à 03:00, archivé depuis août 2023, couvrant toute la France, réutilisable par une AASQA et informatif pour les quatre échecs. Les échecs n’ont d’ailleurs pas une cause commune démontrée : changement du système amont, régime photochimique, émission locale sous-maille et transport de poussières sont quatre mécanismes différents.

Les deux signaux les plus proches du cahier des charges sont :

1. les **observations horaires récentes du réseau réglementaire**, transmises « au fil de l’eau » et utilisées comme prédicteur de la veille dans le MOS CAMS publié ; leur délai garanti avant 03:00 reste toutefois **à vérifier**, et elles n’observent pas directement une station cachée ([LCSQA/data.gouv.fr, API Geod’air](https://www.data.gouv.fr/dataservices/api-mesure-des-concentrations-de-polluants-atmospheriques-reglementes) ; [Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)) ;
2. la **fraction poussière dans PM10 de CAMS Europe**, horaire à 0,1°, disponible dans la même archive que les concentrations ; elle couvre exactement le mécanisme saharien, mais le run CAMS de 00 UTC n’est publié qu’après l’heure cible du projet ([CAMS Europe, DOI 10.24381/a4005cee](https://doi.org/10.24381/a4005cee)).

Le journal des versions CAMS est indispensable pour l’audit historique, mais ce n’est pas un signal temps réel : la partie U9 du 13 novembre 2024 n’a été annoncée publiquement que le 4 décembre 2024 ([annonce U9](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219)).

| Signal | Échec principalement renseigné | 03:00 | Archive 2023-08 → 2026-08 | Verdict |
|---|---|---:|---:|---|
| Journal des versions CAMS | rupture amont | non comme préalerte | oui | audit rétrospectif |
| Régimes ECMWF publiés | O3 temporel, stagnation | à vérifier | non trouvée | inutilisable ici |
| Stabilité/PBL de prévision publique | O3 et PM temporels | à vérifier | non pour IFS/AROME ouverts | déjà couvert en grande partie par l’IFS testé |
| Jours fériés/vacances | anomalie d’activité planifiée | oui | oui ou reconstructible officiellement | utilisable, signal faible et partiel |
| Activités réelles exceptionnelles | extrêmes locaux | inconnu | non trouvée | n’existe pas comme flux national exploitable |
| CAMS PM10 poussière | pics PM10 sahariens | seulement avec un run antérieur | oui, archive glissante | exploitable avec réserve temporelle |
| Barcelona Dust multi-modèle | pics PM10 sahariens | non en accès public | oui | accès restreint à négocier |
| Mesures réglementaires récentes | dérive temporelle, début d’épisode | à vérifier | oui via Geod’air | meilleur signal général disponible |
| Trafic dynamique ouvert | extrêmes NO2 de proximité | oui sur certains axes | non démontrée sur toute la période | utile seulement localement |
| Microcapteurs, mobiles, odeurs | événements locaux | à vérifier | non publique et homogène | inutilisable pour cet entraînement |

## A. Rupture du modèle amont

### Signal A1 — Journal de mises à niveau et annonces CAMS

1. **Physique et mécanisme.** Ce signal ne mesure pas l’atmosphère : il décrit une modification de l’instrument numérique amont. U8 a changé l’inventaire d’émissions ; U9 a changé l’inventaire, adapté les productions à cy49r1 et ajouté nitrate, sulfate et ammonium ; U10 a changé de nouveau l’inventaire et des modèles membres. Il renseigne directement l’échec ② et peut expliquer une partie des pertes temporelles ① et ④ ([historique officiel CAMS Regional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).
2. **Latence.** U9 a commencé le 13 novembre 2024, puis a été complété le 3 décembre ; l’annonce publique est datée du 4 décembre. Le premier changement a donc été annoncé 21 jours après son déploiement : le journal vaut comme preuve rétrospective, pas comme avertissement disponible avant 03:00 ([annonce U9](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219)). La date exacte de publication de chaque ligne du tableau Confluence est **à vérifier**.
3. **Résolution/couverture.** Le signal est un événement de configuration commun à la production européenne, sans grille spatiale ; il couvre donc la France entière mais ne localise ni le membre ni la région où l’effet sera fort ([documentation CAMS Regional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).
4. **Accès.** Tableau HTML public et annonces publiques sur le forum ; le support exige un compte ECMWF. Je n’ai pas trouvé de champ `cycle`, `upgrade` ou identifiant de configuration dans les métadonnées standard du produit, dont la fiche dit seulement « une version, avec des mises à niveau occasionnelles » ([fiche ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)). Un flux machine officiel de changements est **Inconnu**.
5. **Licence.** Les données CAMS sont sous CC-BY ; la licence de réutilisation du texte du forum et du wiki comme jeu de données dérivé est **à vérifier** ([fiche ADS, rubrique Licence](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)). La consultation et la citation par une AASQA ne posent pas de difficulté identifiée ; la redistribution automatisée est **à vérifier**.
6. **Archive.** Le tableau remonte à 2019 et couvre U7b, U8, U8b, U9 et U10, donc toute la période demandée ([historique CAMS Regional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).

**Verdict publié/jugement.** La rupture observée par le projet vers octobre 2024 ne coïncide pas avec la date officielle U9 du 13 novembre. U8b, datée seulement de juin 2024, et les changements propres aux membres ne permettent pas de dater octobre. Le journal prouve qu’une non-stationnarité amont existe, mais ne prouve pas la cause de la rupture d’octobre : **à vérifier**.

## B. Anomalie synoptique disponible à l’émission

### Signal B1 — Probabilités de régimes météorologiques ECMWF

1. **Physique et mécanisme.** Le produit ECMWF représente des probabilités quotidiennes de quatre régimes euro-atlantiques à partir du géopotentiel. Un régime persistant peut séparer les situations de ventilation, blocage et transport qui rendent le résidu O3 saisonnier dans l’échec ① ; ce lien au projet est un **jugement**, non une performance publiée sur cette correction ([ECMWF, *Weather regimes probabilities*](https://www.ecmwf.int/en/forecasts/datasets/weather-regimes-probabilities-sub-seasonal-range-forecast)).
2. **Latence.** La page identifie un produit de prévision d’ensemble, mais ne publie ni heure de mise à disposition ni garantie avant 03:00. Compatibilité temporelle : **à vérifier**.
3. **Résolution/couverture.** Probabilités journalières de quatre classes sur le domaine euro-atlantique, pas un champ local à la station ; l’Occitanie n’a pas de valeur spatiale propre dans le diagramme ([ECMWF](https://www.ecmwf.int/en/forecasts/datasets/weather-regimes-probabilities-sub-seasonal-range-forecast)).
4. **Accès.** La source accessible est un graphique dans Open Charts. Une API brute, un découpage spatial ou des fichiers Parquet/Zarr pour ce produit précis n’ont pas été identifiés : **Inconnu**.
5. **Licence.** La visualisation est ouverte ; une licence explicite pour une série brute réutilisable n’a pas été trouvée sur la fiche : **à vérifier**.
6. **Archive.** Aucun accès public documenté à une archive de prévisions couvrant août 2023–août 2026 n’a été trouvé : **Inconnu**.

**Verdict.** Signal physiquement cohérent, mais inutilisable dans le cahier des charges actuel : trois critères essentiels — heure, données brutes et archive — ne sont pas établis.

### Signal B2 — Hauteur de couche limite et stabilité dans les prévisions numériques ouvertes

1. **Physique et mécanisme.** Température, humidité, vent, mouvement vertical et géopotentiel sur niveaux de pression décrivent le mélange, la stabilité et le transport ; ils sont pertinents pour les échecs temporels O3/PM ① et les extrêmes ③. Le projet a déjà mesuré que vent, pluie et couche limite portent l’essentiel du gain IFS : c’est ici un **constat projet**, pas un résultat externe.
2. **Latence.** ECMWF publie quatre cycles IFS par jour, mais la page Open Data ne garantit pas que le cycle 00 UTC soit complet avant 03:00 ; utiliser un cycle antérieur serait une autre date d’information, **à vérifier** ([ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)).
3. **Résolution/couverture.** Le sous-ensemble IFS ouvert est global à 0,25°, avec niveaux 1000 à 10 hPa et pas de trois heures jusqu’à 144 h pour 00/12 UTC. La hauteur de couche limite n’apparaît pas dans la liste ouverte ; elle est donc **non disponible dans ce sous-ensemble**, même si pression, température, vent et humidité le sont ([ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)).
4. **Accès.** HTTPS, copies AWS/Azure/GCP et client `ecmwf-opendata`; fichiers GRIB2 sélectionnables par paramètre, échéance et cycle. L’accès ne fournit pas un Zarr historique officiel sur la période étudiée ([ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)).
5. **Licence.** ECMWF Open Data est publié sous CC-BY 4.0, compatible avec une réutilisation attribuée par une AASQA ([ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)).
6. **Archive.** Seuls les 12 derniers runs, environ deux à trois jours, sont conservés publiquement ; l’historique complet exige un accord de service. L’API AROME ouverte annonce de son côté une rétention de 14 jours. Aucun des deux accès publics ne couvre l’apprentissage 2023–2026 ([ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data) ; [API AROME, data.gouv.fr](https://www.data.gouv.fr/dataservices/api-modele-arome)).

**Verdict.** Il n’existe pas ici de nouvelle source exploitable distincte de l’IFS déjà testé. Les indices calculés a posteriori dans ERA5 ne satisfont pas l’heure d’émission ; les champs prévus satisfont la physique mais pas l’archive ouverte.

## C. Anomalies d’émission ignorées par l’inventaire

### Signal C1 — Jours fériés et vacances scolaires officiels

1. **Physique et mécanisme.** Ce sont des changements planifiés d’activité, non des émissions mesurées. Ils peuvent renseigner une variation de trafic ou de fonctionnement urbain dans les échecs ① et ③, surtout pour NO2 ; ils n’expliquent ni une rupture CAMS ni une intrusion saharienne. Le lien quantitatif aux concentrations du projet est **Inconnu**.
2. **Latence.** Calendriers connus à l’avance : ils sont disponibles avant 03:00. L’API des jours fériés expose les dates définies par le Code du travail ; le calendrier scolaire expose début et fin par académie et zone ([API jours fériés](https://www.data.gouv.fr/dataservices/jours-feries) ; [API calendrier scolaire](https://www.data.gouv.fr/dataservices/api-calendrier-scolaire)).
3. **Résolution/couverture.** Jour et zone française pour les jours fériés ; jour, académie et zone scolaire pour les vacances. Toulouse et Montpellier appartiennent à des académies explicitement interrogeables ; aucune résolution infra-journalière ([jeu officiel du calendrier scolaire](https://www.data.gouv.fr/datasets/le-calendrier-scolaire)).
4. **Accès.** API JSON/CSV/ICS ouvertes sans compte pour les jours fériés ; API Explore v2 et fichiers/ICS pour le scolaire. L’API Éducation annonce 5 000 appels anonymes par IP et par jour ([API Éducation ouverte](https://www.data.gouv.fr/dataservices/api-donnees-ouvertes-de-leducation-nationale)).
5. **Licence.** Licence Ouverte 2.0 pour les jeux officiels, compatible avec une AASQA sous attribution ([jours fériés](https://www.data.gouv.fr/dataservices/jours-feries) ; [calendrier scolaire](https://www.data.gouv.fr/datasets/le-calendrier-scolaire)).
6. **Archive.** Les jours fériés sont déterministes et disponibles pour la période. La fiche de l’API scolaire parle de l’année en cours, tandis que le jeu associé contient des ressources de plusieurs années ; la complétude exacte août 2023–août 2026 doit être **vérifiée par requête**, mais les dates sont publiées officiellement ([API calendrier scolaire](https://www.data.gouv.fr/dataservices/api-calendrier-scolaire)).

**Verdict.** Signal propre, peu coûteux et réellement disponible, mais seulement proxy de calendrier. Le projet utilise déjà des variables calendaires ; sans distinction plus fine vacances/jours fériés dans ses entrées, c’est le seul ajout clairement accessible de cette direction. Son gain est **Inconnu**.

### Signal C2 — Épandage, chauffage au bois, brûlage, feux d’artifice, chantiers et grèves réellement observés

1. **Physique et mécanisme.** Les quantités et heures réelles d’épandage, combustion ou chantier renseigneraient directement les émissions locales absentes de l’inventaire et donc les échecs ① et ③. Les calendriers réglementaires ou permis indiquent une possibilité d’activité, pas son occurrence ni son intensité : cette distinction est essentielle.
2. **Latence.** Je n’ai identifié aucun flux national ouvert donnant avant 03:00 les activités réelles de ces six catégories. Pour chacune, la latence opérationnelle est donc **Inconnue**.
3. **Résolution/couverture.** **Inconnu** pour un flux national. Les données trouvées sont hétérogènes : enquêtes régionales/annuelles sur le bois, inventaires annuels d’émissions, décisions ou événements communaux isolés ([ADEME, bilan du chauffage au bois 2020](https://librairie.ademe.fr/energies/7344-bilan-national-du-chauffage-au-bois-en-2020.html) ; [Atmo Data, émissions annuelles](https://www.data.gouv.fr/datasets/emissions-annuelles-de-polluants)).
4. **Accès.** Aucun endpoint national d’applications d’engrais, de flambées domestiques, de brûlages, de tirs pyrotechniques, de chantiers actifs ou de grèves n’a été trouvé. DATAtourisme et OpenEventDatabase publient des événements, mais leur exhaustivité et leur typage pour ces émissions sont **à vérifier** ([DATAtourisme](https://www.data.gouv.fr/datasets/donnees-touristiques-de-la-base-datatourisme) ; [OpenEventDatabase](https://www.data.gouv.fr/organizations/openeventdatabase/dataservices)).
5. **Licence.** Les inventaires Atmo sont ouverts ; le prix du bois ADEME est sous Licence Ouverte, mais aucun ne mesure l’activité horaire ([ADEME, prix du bois](https://data.ademe.fr/datasets/prix-bois-domestique)). La licence d’un éventuel flux opérationnel complet est **Inconnue**.
6. **Archive.** Aucune archive homogène couvrant août 2023–août 2026 n’a été identifiée. Les inventaires AASQA sont annuels et ne sont pas calculés chaque année, selon la fiche nationale ([Atmo Data, émissions annuelles](https://www.data.gouv.fr/datasets/emissions-annuelles-de-polluants)).

**Verdict — ce qui n’existe pas.** Dans les sources publiques examinées, il n’existe pas de « vérité d’activité » nationale, anticipée et archivée pour ces émissions. Les données disponibles décrivent surtout capacité, interdiction, permis, prix ou bilan annuel. Les traiter comme des émissions horaires serait une supposition.

## D. Poussières sahariennes

### Signal D1 — Fraction `PM10, dust` de CAMS Europe

1. **Physique et mécanisme.** La variable est la concentration massique de poussière dans la fraction PM10. Elle sépare un mécanisme naturel transporté du total PM10 et vise directement les pertes PM10 des échecs ①, ③ et ④. CAMS avertit cependant que `DUST` est un produit expérimental ; il est listé comme validé régulièrement sur la fiche générale mais comme « à utiliser avec prudence » dans la documentation détaillée ([fiche ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview) ; [documentation CAMS Regional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).
2. **Latence.** Le catalogue annonce 06:45 UTC pour 0–48 h et 08:30 UTC pour 49–96 h ; la documentation ne garantit les lots que plus tard. Le run courant n’est donc pas disponible à 03:00. Le signal n’est compatible qu’avec le même run antérieur que celui réellement utilisé par le projet ; cette identité de run est **à vérifier** ([CAMS Europe](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).
3. **Résolution/couverture.** Europe 25° O–45° E, 30–72° N, grille 0,1°, horaire, surface et niveaux ; Occitanie entièrement couverte ([CAMS Europe, DOI 10.24381/a4005cee](https://doi.org/10.24381/a4005cee)).
4. **Accès.** ADS avec inscription et API, en GRIB ou NetCDF, sélection de variable, date, échéance, niveau et sous-zone ; un WCS n’est plus fourni. Les trois derniers jours de l’ensemble sont aussi accessibles par le portail ECMWF pour les usages critiques ([documentation CAMS Regional, accès](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).
5. **Licence.** CC-BY, compatible avec une AASQA sous attribution ([fiche ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).
6. **Archive.** Archive glissante de trois ans. Au 2 août 2026, elle couvre théoriquement le début d’août 2023, mais la marge disparaît chaque jour ; CAMS recommande de conserver localement les fichiers utilisés pour la traçabilité ([documentation CAMS Regional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)). La complétude exacte du 1er août 2023 est **à vérifier immédiatement**.

**Verdict.** C’est le signal poussière le plus directement compatible avec la grille, l’archive et la licence du projet. Il n’est pas indépendant de CAMS et sa compétence spécifique sur le sud de la France n’a pas été trouvée : **Inconnu**. Son intérêt est d’exposer une composante physique déjà calculée, pas d’apporter une nouvelle observation.

### Signal D2 — WMO Barcelona Dust Regional Center / SDS-WAS multi-modèle

1. **Physique et mécanisme.** Le produit multi-modèle fournit poussière de surface et épaisseur optique des poussières à 550 nm ; sa médiane synthétise les modèles disponibles. Il vise directement les pics PM10 sahariens des échecs ①, ③ et ④ ([guide BDRC v3.6, 2025](https://dust.aemet.es/products/user-guide/%40%40download) ; [Kanngießer et al., 2024, DOI 10.1029/2023AV001042](https://doi.org/10.1029/2023AV001042)).
2. **Latence.** L’accès public ne donne que les prévisions émises depuis plus de deux jours : il est inutilisable à 03:00. L’accès restreint donne les productions récentes, sur demande examinée sous 30 jours ; l’heure de dépôt de chaque modèle n’est pas un SLA commun ([guide BDRC v3.6](https://dust.aemet.es/products/user-guide/%40%40download)).
3. **Résolution/couverture.** Domaine 25° O–60° E et 0–65° N, pas de trois heures, horizon 72 h ; la médiane est remise sur une grille 0,5°×0,5°. Toute l’Occitanie est couverte mais à une maille bien plus grossière que CAMS Europe ([Kanngießer et al., 2024](https://doi.org/10.1029/2023AV001042)).
4. **Accès.** THREDDS avec OPeNDAP, HTTPServer, WMS et NetcdfSubset ; authentification requise. NetcdfSubset et OPeNDAP permettent une extraction spatiale/variable sans télécharger l’archive complète ([catalogue THREDDS BDRC](https://dust.aemet.es/thredds/catalog/dataRoot/MULTI-MODEL/catalog.html) ; [guide BDRC](https://dust.aemet.es/products/user-guide/%40%40download)).
5. **Licence.** Le site affiche « All Rights Reserved » et le guide parle de données disponibles pour redistribution dans l’espace restreint sans publier ici une licence ouverte. Compatibilité AASQA : **à vérifier par autorisation écrite** ([page de téléchargement BDRC](https://dust.aemet.es/products/data-download)).
6. **Archive.** Le catalogue public contient des dossiers annuels depuis 2011 et couvre donc 2023–2026 ; la complétude modèle par modèle varie, et l’accès public reste retardé de deux jours ([catalogue THREDDS BDRC](https://dust.aemet.es/thredds/catalog/dataRoot/MULTI-MODEL/catalog.html)).

**Compétence publiée.** Le centre vérifie la DOD 550 nm contre AERONET sur 40 stations poussiéreuses, mais je n’ai trouvé ni score isolé pour le sud de la France ni évaluation directe des dépassements PM10 d’Occitanie ([WMO/GAW Report 322](https://www.aemet.es/documentos/es/conocermas/recursos_en_linea/publicaciones_y_estudios/publicaciones/Izana_Report/GAW-Report-No322_en.pdf)). Cette compétence régionale est donc **Inconnue**.

**Verdict.** Excellente source indépendante sur le mécanisme, mais inutilisable en accès public pour une émission à 03:00. Elle ne devient candidate que si une AASQA obtient l’accès restreint et une licence explicite.

## E. Signaux de l’AASQA et autres réseaux français

### Signal E1 — Observations réglementaires horaires récentes

1. **Physique et mécanisme.** Elles mesurent directement O3, NO2, PM10 et PM2,5 au sol. Leur niveau récent et le biais récent du CTM renseignent un changement temporel ou le début d’un épisode dans les échecs ①, ② et ③. Le MOS CAMS publié inclut les observations de la veille dans son jeu de base ; le post-traitement opérationnel britannique publié repose explicitement sur la persistance à court terme du biais modèle-observation ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023) ; [Neal et al., 2014, DOI 10.1016/j.atmosenv.2014.09.004](https://doi.org/10.1016/j.atmosenv.2014.09.004)).
2. **Latence.** Les analyseurs automatiques sont transmis « au fil de l’eau » au LCSQA, mais aucune garantie publique indiquant que l’heure 00–02 UTC est complète avant 03:00 n’a été trouvée. La latence effective par AASQA, polluant et station est **à vérifier** ([LCSQA](https://www.lcsqa.org/fr/les-donnees-nationales-de-qualite-de-lair)).
3. **Résolution/couverture.** Données horaires aux stations réglementaires françaises, six polluants, réseau national mais spatialement irrégulier. Elles couvrent l’Occitanie aux stations ; elles ne mesurent pas le lieu caché du protocole double aveugle ([jeu LCSQA](https://www.data.gouv.fr/datasets/donnees-temps-reel-de-mesure-des-concentrations-de-polluants-atmospheriques-reglementes-1)).
4. **Accès.** API Geod’air ouverte, 15 requêtes par heure, plus fichiers E2 sur stockage objet ; aucun compte n’est annoncé pour la lecture. L’API fournit moyenne horaire, moyenne journalière, maximum journalier horaire et moyenne annuelle ([API Geod’air](https://www.data.gouv.fr/dataservices/api-mesure-des-concentrations-de-polluants-atmospheriques-reglementes)). Le filtrage exact par bbox/date dans l’API doit être **vérifié dans sa documentation**.
5. **Licence.** Le jeu E2 est sous Licence Ouverte 2.0 ; le portail régional Atmo Occitanie annonce ODbL avec attribution. Les deux sont compatibles avec un usage AASQA en respectant la source ([jeu LCSQA](https://www.data.gouv.fr/datasets/donnees-temps-reel-de-mesure-des-concentrations-de-polluants-atmospheriques-reglementes-1) ; [Atmo Occitanie Open Data](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-sinformer-comment-agir/lopen-data-de-lair-un-acces-direct-aux-donnees)).
6. **Archive.** Geod’air annonce temps réel et historique ; Atmo Occitanie indique jusqu’à cinq années pour certaines données. La complétude horaire continue d’août 2023 à août 2026 et le statut provisoire/validé doivent être **vérifiés par extraction** ([Geod’air](https://www.geodair.fr/) ; [Atmo Occitanie](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-sinformer-comment-agir/lopen-data-de-lair-un-acces-direct-aux-donnees)).

**Verdict.** C’est le signal publié le plus général et le seul déjà présent dans des MOS opérationnels publiés qui puisse refléter simultanément chimie, météo et émission récente. Sa faiblesse est exactement celle du projet : il est ponctuel, parfois provisoire, et ne fournit pas la vérité d’un site non instrumenté. Il peut signaler qu’un régime régional a changé ; il ne résout pas à lui seul Montpellier Liberté cachée.

### Signal E2 — Trafic routier dynamique ouvert

1. **Physique et mécanisme.** Débit et vitesse mesurent une activité émettrice réelle, pertinente pour les extrêmes NO2 sous-maille de l’échec ③. Ce signal ne renseigne pas directement l’ozone photochimique, la rupture CAMS ou les poussières. Le résultat négatif du projet sur trafic/population porte sur des descripteurs statiques ; il ne démontre pas l’inutilité d’un débit horaire observé.
2. **Latence.** Le réseau routier national non concédé publie un fichier agrégé toutes les six minutes, donc avant 03:00 en fonctionnement nominal. La fréquence varie toutefois selon la station ([transport.data.gouv.fr](https://transport.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede?locale=fr)).
3. **Résolution/couverture.** Débits horaires et vitesses aux stations de comptage du réseau national non concédé ; états de trafic disponibles notamment autour de Toulouse et Montpellier. Ce n’est pas le réseau de rues complet ni nécessairement l’axe au droit de Montpellier Liberté ([transport.data.gouv.fr](https://transport.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede?locale=fr)). Toulouse publie aussi des comptages ponctuels d’une semaine, mis à jour semestriellement depuis 2014 ; Montpellier publie des comptages hétérogènes dont certains sont des moyennes annuelles ([Toulouse Métropole](https://www.data.toulouse-metropole.fr/explore/dataset/comptages-routiers/) ; [Montpellier Métropole](https://data.montpellier3m.fr/dataset/comptage-vehicules-particuliers-de-montpellier)).
4. **Accès.** Flux XML DATEX II et référentiel CSV sans authentification annoncée ; récupération du flux courant complet, sans API spatiale documentée. Toulouse offre export/API Opendatasoft ; Montpellier offre JSON, KML, SHP et CSV ([transport.data.gouv.fr](https://transport.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede?locale=fr)).
5. **Licence.** Licence Ouverte 2.0 pour le flux national ; ODbL pour le jeu de Montpellier. Licence toulousaine du jeu précis : **à vérifier** ([flux national](https://transport.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede?locale=fr) ; [Montpellier](https://data.montpellier3m.fr/dataset/comptage-vehicules-particuliers-de-montpellier)).
6. **Archive.** Le portail conserve des versions de ressources, mais une archive continue des débits toutes les six minutes depuis août 2023 n’est pas documentée. Toulouse a des points depuis 2014 mais non continus ; son jeu IoT 2024 ne couvre que le 13 août au 31 décembre 2024 ([Toulouse IoT 2024](https://data.toulouse-metropole.fr/explore/dataset/comptages-upcity-2024/)). Le critère d’apprentissage 2023–2026 n’est donc pas rempli publiquement.

**Verdict.** Signal causal fort pour un sous-ensemble de stations trafic, mais couverture et archive insuffisantes. Il ne constitue pas un signal commun de renoncement et ne peut pas expliquer les échecs O3/PM nationaux.

### Signal E3 — Microcapteurs, mesures mobiles et signalements citoyens

1. **Physique et mécanisme.** Les microcapteurs et campagnes mobiles peuvent observer une hétérogénéité locale ; SignalAir collecte une perception odorante géolocalisée et horodatée. Ils pourraient documenter une émission locale de l’échec ③, mais une odeur n’est pas une mesure de NO2, O3 ou PM ([Atmo Occitanie, SignalAir](https://www.atmo-occitanie.org/actualites/odo-laisse-sa-place-signalair-le-nouvel-outil-pour-declarer-les-nuisances-odorantes-en)).
2. **Latence.** Les citoyens peuvent signaler immédiatement ; aucune latence publique garantie d’accès machine aux signalements ou aux microcapteurs Atmo Occitanie n’a été trouvée : **Inconnu**.
3. **Résolution/couverture.** SignalAir est ponctuel et dépend des déclarants ; Atmo Occitanie indique six observatoires d’odeurs. Les campagnes mobiles sont, par définition, limitées aux dates et parcours publiés. La qualité métrologique des microcapteurs reste inférieure à celle des stations agréées selon la synthèse Atmo France de l’avis Anses ([SignalAir](https://www.atmo-occitanie.org/actualites/odo-laisse-sa-place-signalair-le-nouvel-outil-pour-declarer-les-nuisances-odorantes-en) ; [Atmo France/Anses](https://www.atmo-france.org/actualite/avis-de-lanses-sur-les-microcapteurs)).
4. **Accès.** Le formulaire SignalAir est public, mais l’historique brut est présenté à l’utilisateur connecté et les bilans sont publiés périodiquement ; aucune API publique brute n’a été identifiée. Les données de campagnes apparaissent surtout dans des rapports, pas dans un flux national homogène ([Atmo Occitanie, SignalAir](https://www.atmo-occitanie.org/actualites/odo-laisse-sa-place-signalair-le-nouvel-outil-pour-declarer-les-nuisances-odorantes-en)).
5. **Licence.** Licence des signalements bruts et des séries microcapteurs : **Inconnue**. La licence ODbL du portail général Atmo Occitanie ne suffit pas à prouver que ces données non publiées y sont couvertes ([Atmo Occitanie Open Data](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-sinformer-comment-agir/lopen-data-de-lair-un-acces-direct-aux-donnees)).
6. **Archive.** Des rapports rétrospectifs existent — par exemple 98 signalements ODO à Portet-sur-Garonne sur 2021–2023 — mais pas une archive brute homogène nationale couvrant 2023–2026 ([Atmo Occitanie, bilan Portet-sur-Garonne](https://www.atmo-occitanie.org/sites/default/files/publications/2025-01/ETU-2024-225%20Suivi%20de%20la%20g%C3%AAne%20olfactive%20sur%20la%20ville%20de%20Portet-sur-Garonne.pdf)).

**Verdict.** Ces réseaux sont utiles pour attribuer un cas après coup ou déclencher une investigation locale, mais aucune source ouverte trouvée ne permet de les employer comme signal national, antérieur à 03:00 et rétrospectivement testable.

## Ce qui a échoué ailleurs — résultats négatifs publiés

- **Ajouter des variables n’est pas automatiquement informatif.** Dans le MOS CAMS de Bertrand et al., quatre variables météo supplémentaires n’apportent généralement rien et peuvent dégrader la performance, notamment avec un apprentissage court et un modèle sensible au surapprentissage ([Bertrand et al., 2023, section 4](https://doi.org/10.5194/acp-23-5317-2023)). Ce résultat appuie le refus d’une liste de proxys sans mécanisme ni ablation.
- **Bon RMSE ne signifie pas bonne détection.** Petetin et al., tels que discutés par Bertrand et al., trouvent que le gradient boosting peut avoir les meilleurs RMSE/corrélations tout en détectant moins bien les dépassements que la persistance ; Bertrand et al. reproduisent cette dissociation pour certains modèles arborés ([Bertrand et al., 2023, conclusion](https://doi.org/10.5194/acp-23-5317-2023)). Cela concorde avec l’échec ④ du projet, sans en expliquer la cause.
- **L’interpolation d’un biais de station peut échouer lorsque le biais est spatialement discontinu ou le réseau rare.** Une évaluation nord-américaine récente rapporte ce défaut pour les fumées d’incendies et l’ozone nocturne ; son domaine et son système CMAQ ne sont pas directement comparables à la France ([*Gridded post-processing of air quality predictions based on the CMAQ model*, 2026, DOI 10.1016/j.atmosenv.2026.122011](https://doi.org/10.1016/j.atmosenv.2026.122011)).
- **Échec spécifique des satellites pour cette correction : Inconnu dans une publication directement comparable.** Le résultat TROPOMI nul du projet reste un résultat interne solide ; les études positives de fusion satellite–PM2,5 retrouvées traitent souvent de restitution ou d’estimation, pas de prévision CAMS J+1–J+3 sur stations et mois exclus ([Zhang et al., 2024, DOI 10.5194/amt-17-5747-2024](https://doi.org/10.5194/amt-17-5747-2024)).

## Question de fond — signal commun ou indicateur de renoncement ?

**Publié.** Les changements de CTM modifient la relation modèle–observation ; CAMS connaît un à deux changements opérationnels par an et son MOS publié utilise un apprentissage très récent pour s’y adapter. Les auteurs indiquent aussi qu’une rupture d’émissions imprévisible peut rendre une correction historique inadéquate ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)). La littérature de post-traitement météorologique identifie également les changements de modèle comme un défi structurel ([Vannitsem et al., 2021, DOI 10.1175/BAMS-D-19-0308.1](https://doi.org/10.1175/BAMS-D-19-0308.1)).

**Jugement.** Le seul signal conceptuellement commun aux quatre échecs serait une preuve que la situation courante n’est pas représentée par les informations disponibles au modèle. Or ce n’est pas une variable physique unique et le projet a déjà montré que ses détecteurs d’anomalie d’entrée ne séparent pas les jours dangereux. Les sources examinées ne fournissent pas une autre mesure universelle de cette « représentativité ».

Il faut donc accepter une réponse mixte :

- **rupture amont** : observable après coup par le journal CAMS, mais pas annoncée assez tôt de façon fiable ;
- **régime régional** : partiellement observable par les prévisions météo et les observations récentes ;
- **poussière saharienne** : observable par un produit spécialisé, sous contraintes d’heure et d’accès ;
- **émission locale soudaine** : souvent absente des flux publics avant l’épisode.

**Conclusion.** L’hypothèse « un prédicteur supplémentaire résout les quatre cas » n’est pas soutenue. L’hypothèse d’un **indicateur de renoncement** est opérationnellement défendable, mais aucun indicateur externe unique n’est validé ici. Le résultat honnête pour une AASQA est donc : certains échecs portent un signal spécifique disponible ; pour les émissions locales imprévues et certaines ruptures amont, l’information préalable publique n’existe pas ou n’arrive pas à temps. Dans ces cas, savoir revenir au produit brut est une politique de sûreté à évaluer, non la conséquence automatique d’un signal déjà trouvé.

## Inconnus à conserver explicitement

- cause exacte de la rupture empirique d’octobre 2024 ; l’U9 officiel commence le 13 novembre ;
- flux machine officiel et annonce préalable des mises à niveau CAMS Regional ;
- latence garantie des mesures E2/Geod’air avant 03:00 ;
- archive brute et licence des régimes ECMWF ;
- archive publique IFS/AROME couvrant août 2023–août 2026 ;
- flux français d’activités réelles pour épandage, bois, brûlage, feux d’artifice, chantiers et grèves ;
- licence opérationnelle du WMO Barcelona Dust Regional Center et éligibilité exacte d’une AASQA à l’accès restreint ;
- score publié du produit Barcelona Dust sur les dépassements PM10 du sud de la France ;
- archive continue 2023–2026 des débits routiers horaires aux axes pertinents ;
- API, licence et archive homogène des microcapteurs, mesures mobiles et signalements bruts d’Atmo Occitanie.
