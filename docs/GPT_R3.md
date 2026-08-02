# GPT R3 — Ruptures CAMS, historique, variables territoriales et cadre réglementaire

> État des sources : 29 juillet 2026.  
> **Publié** désigne ce que dit explicitement une source citée ; **jugement** désigne l’interprétation proposée pour ce projet.  
> Période examinée : juillet 2023 à juin 2025 inclus.

## 1. Le modèle CAMS Europe a-t-il changé entre juillet 2023 et juin 2025 ?

**Publié — oui.** L’archive commence sous U7b, adaptation régionale à CAMS 48r1 ; le cycle global 48r1 était opérationnel depuis le 27 juin 2023 ([ECMWF, 27 juin 2023](https://confluence.ecmwf.int/spaces/COPSRV/pages/315580957/Implementation%2Bof%2BIFS%2Bcycle%2B48r1%2Bfor%2BCAMS)).  
U8 a été déployé le **21 novembre 2023** : ajout de matière organique totale PM2,5 et sel marin sec PM10 ; la documentation associe aussi U8 aux émissions CAMS-REG-v6.1, année 2022 ([annonce ECMWF, 21 novembre 2023](https://forum.ecmwf.int/t/upgrade-u8-to-the-cams-european-air-quality-products/1540) ; [historique CAMS Regional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).  
U8b est daté de **juin 2024** et décrit seulement comme des « améliorations dans les modèles individuels » ; le jour exact et le détail par membre sont **à vérifier** ([historique CAMS Regional](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).  
U9 a introduit CAMS_REG.v7 (année 2023) et l’adaptation à cy49r1 le **13 novembre 2024**, puis nitrate, sulfate et ammonium PM2,5 le **3 décembre 2024** ([annonce ECMWF, 4 décembre 2024](https://forum.ecmwf.int/t/upgrade-u9-to-the-cams-european-air-quality-products/8219)).  
Le cycle global cy49r1 avait basculé le **12 novembre 2024** ; il modifie notamment partition inorganique des aérosols, pH aérosols-nuages-précipitations, poussières et sel marin ([CAMS, octobre 2024, DOI 10.24380/bhen-j48m](https://doi.org/10.24380/bhen-j48m)).

## 2. Le découpage 2023-24 / 2024-25 confond-il année et modèle amont ?

**Publié.** Les changements fréquents d’un modèle déterministe changent ses erreurs et imposent de recalibrer le MOS ; Bertrand et al. signalent un à deux changements CAMS par an et opposent un MOS local, qui demande une série homogène longue, à un modèle européen mutualisé réentraînable sur 3, 7 ou 14 jours ([Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).  
**Jugement — oui, fortement.** L’entraînement contient surtout U7b/U8 et éventuellement la fin d’U8b, tandis que le test contient U8b puis U9 ; l’effet « année future » n’est donc pas identifiable séparément de l’effet « système amont ».  
La pratique publiée consiste à exploiter des exécutions parallèles ancien/nouveau système et des rétroprévisions homogènes lorsqu’elles existent ; CAMS a ainsi comparé e-suite et o-suite pendant environ six mois avant cy49r1 ([CAMS, octobre 2024, DOI 10.24380/bhen-j48m](https://doi.org/10.24380/bhen-j48m)).  
**Pour ce projet :** conserver le test chronologique, mais étiqueter U7b/U8/U8b/U9, publier les scores avant/après chaque rupture et faire des tests glissants intra-cycle. Sans cela, parler de « généralisation à une année nouvelle » serait trop fort.

## 3. Les archives CAMS sont-elles rétro-reprocessées ?

**Publié.** Le produit *CAMS European air quality forecasts* est une archive glissante de trois ans, annoncée comme ayant « une seule version, avec des mises à niveau occasionnelles » ([ADS, fiche du produit consultée en 2026](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).  
Les réanalyses sont un produit distinct : l’intermédiaire de l’année Y paraît en mai Y+1 et la validée en novembre Y+2 ([documentation des réanalyses CAMS Regional, mise à jour 24 juin 2026](https://confluence.ecmwf.int/spaces/CKB/pages/228864840/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Breanalyses%2Bdata%2Bdocumentation)).  
**Interprétation prudente.** Tout indique que l’archive de prévisions conserve les productions opérationnelles successives plutôt que de les recalculer sous le dernier cycle ; elle n’est donc pas une rétroprévision homogène.  
La fiche ne formule toutefois pas une garantie explicite d’immutabilité fichier par fichier : la conservation exacte des runs et de leurs métadonnées est **à vérifier auprès du support CAMS**, puis localement par les en-têtes GRIB/NetCDF et les sommes de contrôle.

## 4. Quelle quantité d’historique est publiée comme nécessaire ?

**Publié.** Pour le MOS CAMS, Bertrand et al. indiquent qu’une approche locale demande typiquement au moins une année de formulation amont constante ; leur expérience locale entraîne sur 2017-2018 et teste 2019 ([Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).  
Le même article obtient une adaptation européenne mutualisée avec des fenêtres de 3, 7 et 14 jours, car le grand nombre de stations fournit rapidement une diversité météorologique et spatiale ([Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)).  
Une étude GEOS-CF multi-villes conclut à un optimum de réentraînement annuel dans son protocole, sans en faire une loi générale ([Atmospheric Environment, 2026, DOI 10.1016/j.atmosenv.2026.121995](https://doi.org/10.1016/j.atmosenv.2026.121995)).  
**Conclusion publiée disponible :** il existe des comparaisons de fenêtres, mais pas de seuil universel ni de courbe de saturation transférable à CAMS Occitanie.  
**Jugement :** avec 24 mois et plusieurs cycles, la stabilité doit être démontrée par une courbe d’apprentissage temporelle, non revendiquée à partir du seul nombre de mois.

## 5. Le réentraînement glissant est-il la référence, et à quelle fréquence ?

**Publié.** La revue de référence sur le post-traitement météorologique indique qu’en opération une fenêtre glissante plus petite est typiquement préférée, notamment pour limiter l’effet des changements de modèle ([Vannitsem et al., 2021, DOI 10.1175/BAMS-D-19-0308.1](https://doi.org/10.1175/BAMS-D-19-0308.1)).  
Dans le MOS CAMS de Bertrand et al., le modèle européen peut être réentraîné quotidiennement sur les jours récents et s’adapter en quelques jours aux changements du CTM ([Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)).  
Les fenêtres opérationnelles publiées varient cependant selon produit et variable : 15 jours dans IMPROVER, 60 jours dans une étude EMOS citée par Wessel et al. ([Wessel et al., 2024, DOI 10.1002/qj.4701](https://doi.org/10.1002/qj.4701)).  
**Réponse :** fenêtre glissante, oui comme pratique établie ; fréquence universelle, non. Recalcul quotidien des coefficients et révision périodique de l’architecture sont deux décisions différentes.

## 6. Comment arbitrer historique long et dérive du modèle amont ?

**Publié.** Les longues archives couvrent mieux climatologie et événements rares, mais le MOS classique suppose que la relation modèle-observation reste stable ; NOAA précise qu’un changement NWP oblige à reformuler les équations sur un nouvel échantillon ([NOAA/MDL, page MOS consultée en 2026](https://vlab.noaa.gov/web/mdl/mos)).  
Les réponses documentées sont : rétroprévisions produites avec un cycle constant, exécutions ancien/nouveau cycle en parallèle, fenêtres glissantes, ou mutualisation spatiale permettant de raccourcir la fenêtre ([Vannitsem et al., 2021](https://doi.org/10.1175/BAMS-D-19-0308.1) ; [Bertrand et al., 2023](https://doi.org/10.5194/acp-23-5317-2023)).  
**Jugement pour 24 mois :** employer une validation glissante, une variable catégorielle de cycle, et comparer fenêtre courte, fenêtre longue et pondération décroissante.  
Le choix doit être fait sur les pertes hors échantillon, en particulier classe ATMO et détection de seuil, non sur le seul RMSE moyen. Un apprentissage pré-U9 appliqué à U9 mesure aussi la robustesse au changement amont ; il faut le nommer ainsi.

## 7. Existe-t-il des poids de référence entre classes de routes ?

**Publié — non dans les références LUR européennes examinées.** ESCAPE emploie l’intensité réelle de trafic, la distance et la charge de trafic — somme de `trafic × longueur de segment` dans un tampon — puis estime les coefficients par régression ([Beelen et al., 2013, DOI 10.1016/j.atmosenv.2013.02.037](https://doi.org/10.1016/j.atmosenv.2013.02.037) ; [Hennig et al., 2016, DOI 10.3390/atmos7030048](https://doi.org/10.3390/atmos7030048)).  
Dans ESCAPE, retirer l’intensité locale de trafic dégrade sensiblement les modèles NO2 ; cela ne fournit toutefois aucun ratio universel autoroute/départementale/locale ([Beelen et al., 2013](https://doi.org/10.1016/j.atmosenv.2013.02.037)).  
**Jugement :** des poids fixés à la main entre classes seraient des hypothèses, pas une référence. Il faut soit joindre des comptages, soit laisser le modèle estimer des effets de classe et vérifier stabilité, monotonie et validation spatiale.  
Tout ratio numérique proposé sans territoire, période, parc et définition des classes doit être marqué **« à vérifier »**.

## 8. Sous quelle forme la population entre-t-elle dans les LUR ?

**Publié.** Dans les modèles européens ESCAPE, la population ou les ménages apparaissent généralement comme un nombre d’habitants ou une densité calculée dans plusieurs tampons autour du point ([Beelen et al., 2013, DOI 10.1016/j.atmosenv.2013.02.037](https://doi.org/10.1016/j.atmosenv.2013.02.037)).  
Un exemple documenté définit explicitement la densité comme le nombre d’habitants dans le tampon ; le même article distingue cette variable de la charge routière `intensité × longueur` ([Hennig et al., 2016, DOI 10.3390/atmos7030048](https://doi.org/10.3390/atmos7030048)).  
La pondération inverse de la distance n’est donc pas la forme de référence unique publiée : taille de tampon et transformation sont sélectionnées dans le protocole LUR.  
**Jugement :** ne pas confondre population comme prédicteur de concentration et population utilisée après modélisation pour pondérer l’exposition ; ce sont deux opérations et deux interprétations différentes.

## 9. `importance` et `nombre_de_voies` de la BD TOPO ont-ils servi de proxy ?

**Publié.** L’IGN définit `importance` comme une hiérarchie liée à l’importance des tronçons pour le trafic, mais ce champ n’est pas un comptage de véhicules ([IGN, *BD TOPO v2 — descriptif de contenu*, octobre 2008](https://geoservices.ign.fr/sites/default/files/2022-11/DC_BDTOPO_2_08.pdf)).  
Une thèse française sur l’impact routier a effectivement utilisé les niveaux BD TOPO 3–5 pour affecter des trafics moyens à de petites routes dépourvues de mesures : c’est un précédent de proxy, pas une calibration nationale ([thèse IFSTTAR, 2014](https://mocopo.ifsttar.fr/fileadmin/contributeurs/Mocopo/Documents/Other_documents/THESE_-_Modelisation_de_l_impact_du_trafic_routier_sur_la_pollution_de_l_air_et_des_eaux_de_ruissellement.pdf)).  
À Paris, un travail récent emploie plutôt BD TOPO pour largeur de rue et hauteur du bâti, tandis que les émissions routières viennent d’Airparif ([Maison et al., 2025, DOI 10.5194/acp-25-93-2025](https://doi.org/10.5194/acp-25-93-2025)).  
**Recherche non concluante :** je n’ai pas trouvé de publication française de qualité de l’air utilisant conjointement `importance` et `nombre_de_voies` comme substitut quantitatif du trafic ; absence générale **à vérifier**.  
**Jugement :** ces champs sont de bonnes variables de secours ou de jointure, pas l’équivalent démontré d’un TMJA.

## 10. Quelles données ouvertes de trafic réel sont disponibles ?

**Publié.** Le jeu national TMJA fournit, par section et année, trafic tous véhicules, part de poids lourds et type de comptage permanent/temporaire, sous Licence Ouverte ([ministère de la Transition écologique, mise à jour 18 août 2025](https://www.data.gouv.fr/datasets/trafic-moyen-journalier-annuel-sur-le-reseau-routier-national)).  
Le réseau routier national non concédé diffuse aussi débit horaire et vitesse en temps réel au format DATEX II, fichier agrégé toutes les six minutes, sous Licence Ouverte 2.0 ([Point d’accès national, consulté le 29 juillet 2026](https://transport.data.gouv.fr/datasets/etat-de-circulation-en-temps-reel-sur-le-reseau-national-routier-non-concede?locale=fr)).  
Les collectivités publient des jeux hétérogènes : Toulouse propose 3 735 comptages ponctuels, tubes pneumatiques pendant une semaine, TMJO depuis 2014, mise à jour semestrielle ([Toulouse Métropole, consulté le 29 juillet 2026](https://www.data.toulouse-metropole.fr/explore/dataset/comptages-routiers/)).  
Le Cerema normalise a minima valeur, localisation, date et type de mesure, mais ne transforme pas cet ensemble en couverture exhaustive de chaque rue ([Cerema, mise à jour 5 septembre 2022](https://trafic-routier.data.cerema.fr/comptages-a155.html)).  
La licence exacte du jeu toulousain et la disponibilité d’historiques horaires complets sont **à vérifier sur la ressource exportée** avant redistribution.

## 11. Tableau exact des paramètres FAIRMODE accessible

**Publié — le `β = 2` unique n’est plus le tableau courant.** Le guide FAIRMODE **v4.0, mai 2026**, tableau 6, donne les paramètres ci-dessous ; il précise qu’ils sont encore revus par CEN/WG43 et qu’une mise à jour est attendue fin 2026 ([JRC/FAIRMODE, v4.0, tableau 6 p. 35](https://knowledge4policy.ec.europa.eu/sites/default/files/Guidance_MQO_Bench_vs4.0_FINAL_v20260513.pdf)).

| Polluant | Temps | RV (µg/m³) | Mesure fixe : Ur(RV), α, β | Mesure indicative : Ur(RV), α, β |
|---|---:|---:|---:|---:|
| NO2 | horaire | 200 | 15 %, 0,20, 3,20 | 25 %, 0,90, 1,92 |
| O3 | max journalier 8 h | 100 | 15 %, 0,79, 2,20 | 25 %, 0,80, 1,32 |
| PM10 | journalier | 45 | 25 %, 0,25, 2,20 | 50 %, 0,85, 1,10 |
| PM2,5 | journalier | 25 | 25 %, 0,50, 2,50 | 35 %, 0,83, 1,79 |
| NO2 | annuel | 20 | 30 %, 0,975, 1,40 | 40 %, 0,975, 1,05 |
| O3 | annuel | 60 | 15 %, 0,40, 1,70 | 25 %, 0,80, 2,20 |
| PM10 | annuel | 20 | 20 %, 0,60, 1,30 | 30 %, 0,80, 1,30 |
| PM2,5 | annuel | 10 | 30 %, 0,80, 1,70 | 40 %, 0,90, 1,70 |

La v3.2 utilisait encore un facteur global β = 2 et, dans son tableau 6, `Ur(RV), RV, α, Np, Nnp` : NO2 `0,24; 200; 0,20; 5,2; 5,5`, O3 `0,18; 120; 0,79; 11; 3`, PM10 `0,28; 50; 0,13; 30; 0,25`, PM2,5 `0,36; 25; 0,30; 30; 0,25` ([JRC, v3.2, 2020, DOI 10.2760/30226, tableau 6 p. 43](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC120649/mqoguidance_online.pdf)).  
**Attention :** ces MQO portent sur l’évaluation réglementaire de la qualité de l’air ; ils ne remplacent pas les scores français de prévision d’épisodes.

## 12. CEN/TS 18275:2026 remplace-t-elle le Guidance Document ?

**Publié.** CEN/TS 18275:2026 définit MQI/MQO pour les applications de modélisation utilisées en **évaluation** de la qualité de l’air ; c’est une spécification technique de 45 pages ([notice CEN/TS 18275:2026, 15 février 2026](https://www.austrian-standards.at/en/shop/onr-cen-ts-18275-2026-02-15~p4719567)).  
Une CEN/TS doit être annoncée nationalement et peut être adoptée comme norme nationale, mais son application demeure volontaire tant qu’un texte juridique ou contractuel ne la rend pas obligatoire ([CEN-CENELEC, types de livrables, consulté en 2026](https://www.cencenelec.eu/european-standardization/european-standards/types-of-deliverables/) ; [FAQ CEN-CENELEC](https://www.cencenelec.eu/bottom-navigation-pages/faqs/)).  
Le guide FAIRMODE v4.0 se présente comme un appui à CEN/WG43 et annonce encore la révision des paramètres ; il n’est donc pas simplement « abrogé » par la TS ([JRC/FAIRMODE, mai 2026](https://knowledge4policy.ec.europa.eu/sites/default/files/Guidance_MQO_Bench_vs4.0_FINAL_v20260513.pdf)).  
**France :** je n’ai pas identifié au 29 juillet 2026 de référence à CEN/TS 18275 dans l’arrêté français ni de notice AFNOR publique ; son adoption nationale exacte est **à vérifier**. Pour une prévision AASQA, le référentiel LCSQA reste directement applicable.

## 13. Documentation imposée par la directive 2024/2881

**Publié.** Lorsqu’un modèle sert à l’évaluation, les références décrivant l’application et les informations de calcul du MQO doivent être compilées ; les procédures de choix des sites et, le cas échéant, les méthodes de modélisation doivent aussi être documentées ([directive (UE) 2024/2881, annexe IV, points D et annexe V](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
La directive impose également la publication d’informations sur la représentativité spatiale des points au moins tous les cinq ans et une évaluation/communication annuelle à la Commission ([directive (UE) 2024/2881, art. 8 et 23, annexe IV](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
La France doit transposer les articles et annexes concernés au plus tard le **11 décembre 2026** ([directive (UE) 2024/2881, art. 30](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
La décision d’exécution 2026/1208 ajoute contrôle qualité des entrées, validation sur mesures indépendantes et leave-one-out pour les fusions modèle-mesures ; elle s’applique le **30 juin 2028** ([décision (UE) 2026/1208, art. 2, 3, 11 et annexe II](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202601208)).  
**Périmètre :** ces obligations visent l’évaluation réglementaire ; leur application directe à une correction de prévision opérationnelle est **à vérifier** selon l’usage final du produit.

## 14. Une AASQA doit-elle publier la performance de ses prévisions ?

**Publié — obligation de produire et transmettre.** Chaque AASQA évalue annuellement les performances de l’année précédente et adresse le rapport à la DREAL et au LCSQA avant le **30 juin** ([arrêté du 16 avril 2021, art. 13](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000043388197)).  
Elle doit publier gratuitement les résultats de ses prévisions et informer quotidiennement le public, mais l’article 18 ne dit pas explicitement que le rapport annuel de performance lui-même doit être publié sur son propre site ([arrêté du 16 avril 2021, art. 3 et 18](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000043388197)).  
Le LCSQA met en pratique un accès public aux rapports régionaux et aux bilans PREV’AIR ([LCSQA, *Performances des prévisions*, consulté en 2026](https://www.lcsqa.org/fr/performances-des-previsions)).  
**Conclusion juridique prudente :** rapportage annuel obligatoire, publication publique du rapport par chaque AASQA **non explicitement trouvée dans les articles examinés — à vérifier** dans sa convention d’agrément, ses règles de transparence et les prescriptions locales.

## 15. Existe-t-il un référentiel LCSQA opposable ?

**Publié — oui.** Le guide *Évaluation des performances des prévisions de la qualité de l’air*, applicable depuis le 1er janvier 2022, fait partie du référentiel technique national ([LCSQA, page des guides, 2022](https://www.lcsqa.org/fr/rapport/guides-methodologiques-pour-la-prevision-de-la-qualite-de-lair)).  
Les AASQA exercent leurs missions conformément aux prescriptions de ce référentiel, validé par le ministère ; ce rattachement lui donne une portée prescriptive dans le dispositif national ([arrêté du 16 avril 2021, art. 4, 6, 13 et 16](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000043388197)).  
Le guide impose au rapport : système et disponibilité, prévisions brutes et corrigées, biais/RMSE/corrélation par zone, typologie, échéance et classe de concentration, puis tables de contingence et critères AMU ([LCSQA, référentiel d’évaluation, 2022, p. 1–9](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).  
Il fixe 75 % de couples disponibles et définit POD, FAR, SR, FB et CSI ; O3 est évalué en maximum journalier d’avril à septembre, PM10 en moyenne journalière annuelle, à J0 et J1 ([même référentiel, annexes 1–2](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf)).  
**Jugement :** pour la candidature, le rappel d’épisodes doit au minimum être raccordé au POD et complété par FAR/CSI ; une métrique de classe ATMO est utile mais ne remplace pas ce socle. Le traitement normatif de NO2 et PM2,5 en prévision dans une version plus récente est **à vérifier**.

## Conclusion opérationnelle

**Jugement.** L’angle du projet ne s’effondre pas, mais son affirmation centrale doit changer : avec ces 24 mois, il évalue une correction **sous changements opérationnels CAMS**, pas une généralisation annuelle pure.  
La priorité est de reconstruire une variable `cams_regional_upgrade` avec au minimum U7b, U8, U8b et U9, d’inscrire le 21 novembre 2023, le jour U8b **à vérifier**, le 13 novembre 2024 et le 3 décembre 2024, puis de publier les performances par régime.  
Le résultat le plus utile pour ATMO Occitanie serait de montrer simultanément : gain sur le référentiel LCSQA, stabilité autour des ruptures CAMS, et délai de récupération après changement de cycle.
