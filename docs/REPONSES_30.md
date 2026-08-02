# Réponses aux 30 questions

## 1. Que fait exactement la correction statistique de PREV’AIR ?

**Savoir vérifié.** PREV’AIR corrige les prévisions brutes de CHIMERE pour O₃, NO₂, PM₁₀ et PM₂,₅ par apprentissage sur les jours ou années antérieurs, puis spatialise les valeurs corrigées aux stations par krigeage ; les produits peuvent être horaires ou journaliers et vont jusqu’à J+5 ([PREV’AIR, « Prévisions corrigées »](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
La description technique publique la plus précise trouvée utilise, par station et indicateur, une régression linéaire multiple alimentée par les observations de la veille, les concentrations et variables météo CHIMERE et le type de jour ([LCSQA, note PREV’AIR-Urgence, 2014](https://www.lcsqa.org/system/files/media/documents/drc-14-144377-12853a_modelisation_note_prevair_urgence_vf.pdf)).  
L’évaluation annuelle porte sur les stations de fond ayant plus de 75 % de données valides et publie biais, RMSE et corrélation ; le rapport 2021 montre par exemple une amélioration nette du NO₂ par l’adaptation statistique ([PREV’AIR, « Évaluations »](https://www.prevair.org/le-systeme-prevair/la-production/evaluations) ; [LCSQA, performances 2021](https://www.lcsqa.org/system/files/media/documents/LCSQA2022-Performances%20Prev%27air%202021-v2.pdf)).  
**À vérifier.** L’algorithme exact actuellement déployé selon le domaine, la fenêtre d’apprentissage et la fréquence de réentraînement ne sont pas publiés avec assez de précision ; la page actuelle mentionne du *machine learning*, tandis que la note détaillée de 2014 décrit la chaîne historique.

## 2. Le krigeage de PREV’AIR est-il ordinaire ou à dérive externe ?

**Réponse décisive :** c’est un **krigeage à dérive externe**, pas un krigeage ordinaire ; la dérive documentée est le champ CHIMERE, combiné aux prévisions statistiques calculées aux stations ([LCSQA, note PREV’AIR-Urgence, 2014](https://www.lcsqa.org/system/files/media/documents/drc-14-144377-12853a_modelisation_note_prevair_urgence_vf.pdf) ; [LCSQA, note de voisinage, 2016](https://www.lcsqa.org/system/files/media/documents/n_drc-16-152350-00345a_voisinage_krigeage_corrige.pdf)).  
La page PREV’AIR consacrée aux analyses confirme une dérive fournie par le modèle déterministe, et celle des prévisions corrigées confirme la spatialisation par krigeage ([PREV’AIR, « Analyses »](https://www.prevair.org/le-systeme-prevair/la-production/analyses) ; [PREV’AIR, « Prévisions corrigées »](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
**Point crucial :** « dérive externe » ne signifie donc pas ici « altitude + occupation du sol + émissions » ; ces covariables de terrain ont été étudiées, mais une note de 2005 disait explicitement qu’elles n’étaient pas opérationnelles dans PREV’AIR à cette date ([LCSQA, travaux PREV’AIR 2005](https://www.lcsqa.org/system/files/media/documents/Etude16_Travaux_relatifs_PREVAIR2005_vfinale.pdf)).  
**Conclusion prudente.** L’angle « ajouter des covariables locales et kriger les résidus » ne s’effondre pas au vu des sources publiques ; l’existence d’une configuration récente non publiée qui les emploierait reste **à vérifier directement auprès d’INERIS/PREV’AIR**.

## 3. Quelles AASQA publient leur méthode de prévision ?

Airparif décrit ESMERALDA, plateforme CHIMERE interrégionale utilisée avec Atmo Normandie, Atmo Hauts-de-France, Air Breizh, Air Pays de la Loire et Lig’Air, ainsi que l’assimilation horaire des observations ([Airparif, « La modélisation »](https://www.airparif.fr/la-modelisation)).  
Atmo Auvergne-Rhône-Alpes publie la chaîne CHIMERE corrigée géostatistiquement puis couplée à SIRANE à 10 m, et publie aussi une explication de son évaluation prévisionnelle ([Atmo AuRA, étude ZFE Lyon 2022](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf) ; [Atmo AuRA, évaluation des prévisions](https://www.atmo-auvergnerhonealpes.fr/actualite/comment-evalue-t-les-performances-de-prevision-de-la-qualite-de-lair)).  
AtmoSud documente AIRES Méditerranée/AZUR et ouvre des API OGC ; ATMO Grand Est décrit Prev’Est et l’expertise quotidienne, mais sans tous les paramètres internes ([AtmoSud, API prévision](https://api.atmosud.org/prevision/) ; [ATMO Grand Est, « Modélisation »](https://www.atmo-grandest.eu/modelisation)).  
**Jugement documenté, non classement officiel.** Airparif/ESMERALDA est la chaîne publiquement la plus structurée et traçable trouvée ; Atmo AuRA est la plus explicite sur le couplage régional–rue. L’exhaustivité des méthodes internes reste **à vérifier**, car le référentiel impose des documents dont certains sont réservés ([LCSQA, référentiel national](https://www.lcsqa.org/fr/node/1057/printable/print)).

## 4. Existe-t-il une comparaison publique PREV’AIR corrigé–CAMS sur la France ?

**Recherche vérifiée, conclusion négative provisoire.** Je n’ai pas trouvé d’étude publique nationale faisant un face-à-face homogène entre le produit PREV’AIR corrigé et l’ensemble CAMS, sur les mêmes stations, dates, horizons et règles de validation.  
PREV’AIR publie annuellement ses performances contre les stations AASQA, avec CHIMERE, MOCAGE et adaptation statistique ([PREV’AIR, « Évaluations »](https://www.prevair.org/le-systeme-prevair/la-production/evaluations) ; [LCSQA, performances PREV’AIR 2021](https://www.lcsqa.org/system/files/media/documents/LCSQA2022-Performances%20Prev%27air%202021-v2.pdf)).  
CAMS publie un produit européen quotidien à 0,1°, dont seuls NO, NO₂, SO₂, O₃, PM₂,₅, PM₁₀ et poussières sont régulièrement validés, mais il s’agit de sa propre chaîne d’évaluation ([CAMS, European air-quality forecasts](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).  
**À vérifier.** Une comparaison peut exister dans un livrable contractuel ou un espace AASQA/LCSQA restreint ; en l’état, construire ce benchmark reproductible reste une contribution défendable.

## 5. Que proposent généralement les candidats, et qu’est-ce qui est déjà résolu ?

**Savoir vérifié.** Débiaser CAMS/CHIMERE aux stations, intégrer les observations récentes, produire une carte continue et mesurer biais/RMSE/corrélation sont déjà des fonctions opérationnelles de PREV’AIR ([PREV’AIR, correction](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees) ; [PREV’AIR, évaluation](https://www.prevair.org/le-systeme-prevair/la-production/evaluations)).  
La fusion modèle–mesures, les plateformes régionales CHIMERE, l’expertise humaine et la descente à la rue avec SIRANE/ADMS existent aussi dans plusieurs AASQA ([Airparif, modélisation](https://www.airparif.fr/la-modelisation) ; [Atmo AuRA, étude ZFE Lyon 2022](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf)).  
**Hypothèse fondée sur ces systèmes, pas statistique de recrutement :** les propositions banales sont « XGBoost bat le modèle brut », une carte plus fine et un tableau de RMSE ; elles ne démontrent ni nouveauté opérationnelle ni aptitude aux épisodes.  
La contribution encore crédible est une comparaison hors échantillon spatial et temporel, centrée sur la classe ATMO, les seuils, les faux négatifs et une chaîne reproductible ; son caractère réellement nouveau chez Atmo Occitanie est **à vérifier en entretien**.

## 6. Définition et prévision d’un épisode de pollution

Un épisode est un dépassement constaté ou prévu d’un seuil d’information ou d’alerte, sous les critères de l’article 2 : au moins 100 km², ou 10 % de la population d’un département de plus de 500 000 habitants, ou 50 000 habitants dans un département plus petit, ou une situation locale particulière ([arrêté du 7 avril 2016, art. 1–2](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Seuils français : O₃ 180/240 µg·m⁻³ horaire ; NO₂ 200/400 µg·m⁻³ horaire avec règles de persistance ; PM₁₀ 50/80 µg·m⁻³ journalier ; SO₂ 300/500 µg·m⁻³ horaire, ce dernier seuil d’alerte devant durer trois heures ([Code de l’environnement, art. R.221-1](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000022964539)).  
Pour PM₁₀ et O₃, l’épisode est persistant si le seuil d’information est prévu aujourd’hui et demain ; sans modèle, il faut deux jours constatés sur station de fond ([arrêté du 7 avril 2016, art. 1](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
L’AASQA informe préfet et ARS au moins quotidiennement ; la prévision concerne J0 et J+1 dans la chaîne opérationnelle, et les mesures préfectorales ordinaires prennent effet le lendemain ([arrêté, art. 7 et 14](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31) ; [référentiel prévision LCSQA, 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).

## 7. Procédure de déduction des sources naturelles

L’État membre, non l’AASQA seule, transmet chaque année à la Commission la liste des zones concernées, les concentrations, les sources et les preuves ; la déduction n’est admise que si la contribution naturelle est démontrée ([directive 2008/50/CE, art. 20](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32008L0050)).  
Le cadre probatoire est le guide de la Commission SEC(2011) 208 final : cohérence spatio-temporelle, quantification de la contribution, causalité et caractère naturel doivent être documentés ([Commission européenne, SEC(2011) 208](https://www.lcsqa.org/system/files/media/documents/ue_eval_sources_naturelles_2011.pdf)).  
En pratique française, l’AASQA fournit mesures et expertise, le LCSQA/INERIS consolide les méthodes, puis l’État assure le rapportage européen ; Geod’air est la base nationale mandatée pour ce rapportage ([LCSQA, données nationales](https://www.lcsqa.org/fr/les-donnees-nationales-de-qualite-de-lair)).  
La déduction se fait année par année et zone par zone, avec dossier traçable ; l’autorité signataire exacte et le circuit de validation interne pour l’Occitanie sont **à vérifier auprès de la DREAL/LCSQA**.

## 8. Comment distinguer un apport saharien d’un épisode local ?

La méthode établie combine une station rurale de fond, l’anomalie de PM, la cohérence temporelle et géographique, les trajectoires/modèles ou images satellitaires, puis si possible la composition chimique crustale ([LCSQA, synthèse CARA 2012](https://www.lcsqa.org/system/files/media/documents/lcsqa_2012_metrologie_pm_cara_synthese2012.pdf) ; [Commission, SEC(2011) 208](https://www.lcsqa.org/system/files/media/documents/ue_eval_sources_naturelles_2011.pdf)).  
Al, Fe, Si, Ca, Mg, K et carbonates servent à estimer la fraction minérale ; la méthode et les facteurs stœchiométriques doivent être explicités, pas improvisés ([LCSQA, CARA Martinique 2018](https://www.lcsqa.org/system/files/media/documents/LCSQA2019-CARA_Martinique%202018.pdf)).  
Un ratio PM₂,₅/PM₁₀ plus faible est bien observé lors des brumes de sable, donc la fraction grossière est un indice utile ([LCSQA, analyse Martinique 2000–2018](https://www.lcsqa.org/system/files/media/documents/LCSQA2019-v2.0_PM_Martinique_evolution_concentrations.pdf)).  
**Mais aucun seuil universel français du ratio n’a été trouvé dans le guide réglementaire :** employer 0,5, 0,6 ou autre comme critère décisif serait **à vérifier** et insuffisant sans transport, fond régional et chimie.

## 9. Ce que la directive (UE) 2024/2881 impose en 2030

Au 1er janvier 2030, les limites annuelles deviennent 10 µg·m⁻³ pour PM₂,₅, 20 pour PM₁₀ et 20 pour NO₂ ; les limites journalières sont 25 pour PM₂,₅ et 45 pour PM₁₀, chacune avec 18 dépassements admis, et NO₂ ajoute 50 journalier (18) et 200 horaire (3) ([directive 2024/2881, annexe I](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
La directive doit être transposée au plus tard le 11 décembre 2026 ; elle renforce aussi modélisation, représentativité spatiale, supersites et plans/feuilles de route ([directive 2024/2881, art. 8–10 et 30](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
Aux concentrations modélisées de 2025, toute la population de Montpellier, Toulouse et Perpignan, et 98 % de Nîmes, dépasserait 10 µg·m⁻³ de PM₂,₅ ; des secteurs dépasseraient aussi les futures limites NO₂ et PM₁₀ ([Atmo Occitanie, bilan métropoles 2025](https://www.atmo-occitanie.org/actualites/montpellier-nimes-perpignan-et-toulouse-quelle-qualite-de-lair-en-2025-en-occitanie)).  
Ce sont des projections d’exposition sur quatre métropoles, pas une déclaration juridique de dépassement pour toutes les zones administratives ; la délimitation réglementaire complète 2030 reste **à vérifier** après transposition et rapportage.

## 10. Les objectifs de qualité des données créent-ils un plancher utile ?

**Non.** L’annexe V fixe des incertitudes maximales pour les mesures et un rapport maximal entre incertitude de modélisation et incertitude des mesures ; ce sont des critères d’aptitude réglementaire, pas une preuve qu’une erreur plus faible serait inutile ([directive 2024/2881, annexe V.A](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
La directive donne par exemple, pour les moyennes annuelles, des couples absolu/relatif et des rapports propres à PM₂,₅, PM₁₀ et NO₂ ; l’acte d’exécution 2026 ajoute des détails techniques de modélisation ([directive, annexe V](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881) ; [décision d’exécution (UE) 2026/1208](https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=OJ:L_202601208)).  
Une amélioration sous ces plafonds peut encore changer une classe ATMO, une probabilité de dépassement, une population exposée ou un faux négatif : ces usages sont distincts de la seule conformité MQO ([arrêté indice ATMO du 10 juillet 2020](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042164835)).  
**Interprétation :** le bon arrêt n’est pas « sous le DQO », mais « gain décisionnel non démontré par rapport au coût » ; ce seuil économique est à définir avec l’AASQA.

## 11. Paramètres exacts du MQI FAIRMODE

**Document authentifié disponible :** *Guidance Document on Modelling Quality Objectives and Benchmarking*, version 3.2, JRC120649, 2020, DOI [10.2760/30226](https://doi.org/10.2760/30226) ([notice JRC](https://publications.jrc.ec.europa.eu/repository/handle/JRC120649)).  
Il définit \(MQI=RMSE/(\beta\,RMS_U)\), \(\beta=2\), un objectif \(MQI\leq1\), à satisfaire à 90 % des stations ; \(U(O)\) dépend de \(U_r(RV)\), \(RV\) et \(\alpha\) propres au polluant ([JRC, version 3.2](https://publications.jrc.ec.europa.eu/repository/handle/JRC120649)).  
Une spécification CEN/TS 18275:2026 couvre désormais davantage de polluants et d’agrégations, mais je n’ai pas accès à son texte normatif complet ([CEN/TS 18275:2026, notice](https://www.austrian-standards.at/en/shop/onr-cen-ts-18275-2026-02-15~p4719567)).  
**Donc je ne fournis pas de tableau “en vigueur” de mémoire.** Les valeurs exactes par polluant et période doivent être recopiées du Guidance/CEN réellement adopté par l’AASQA : **à vérifier auprès du LCSQA ou dans le document acheté**.

## 12. Comment compter les épisodes ?

Le droit français compte dans le bilan annuel les dépassements observés, ceux prévus et les fausses alertes, sans imposer une métrique scientifique unique « événement régional » ([arrêté du 7 avril 2016, art. 15](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Un jour-station mesure la détection locale ; un jour-département colle davantage aux procédures ; un événement régional fusionne des jours et zones contigus. Ces dénominateurs ne sont pas interchangeables, comme le montre la dépendance des scores POD/FAR/CSI à la définition de l’événement ([US EPA, *Air Quality Forecasting Guidance*, 2003](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=2000F0ZT.TXT)).  
**Convention recommandée pour comparer :** publier les deux niveaux — jours-stations pour la compétence statistique, et événements uniques définis avant calcul par polluant, seuil, continuité temporelle et union spatiale.  
Le rappel n’est comparable entre études que si unité, horizon, masque de stations, règle de fusion et traitement des épisodes multi-polluants sont identiques ; sinon il faut écrire **non comparable**.

## 13. Quelles métriques une AASQA regarde-t-elle réellement ?

PREV’AIR publie biais moyen, RMSE et corrélation, par polluant, échéance, région et station de fond ; il exige plus de 75 % de données valides pour l’évaluation ([PREV’AIR, « Évaluations »](https://www.prevair.org/le-systeme-prevair/la-production/evaluations)).  
Pour l’opérationnel épisode, le bilan légal sépare dépassements observés, dépassements prévus et dépassements prévus non confirmés, soit les ingrédients du rappel et des fausses alertes ([arrêté du 7 avril 2016, art. 15](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Pour les bilans réglementaires, taux de données valides, moyennes, maxima, percentiles et nombres de dépassements suivent le guide national de calcul ([LCSQA, guide statistiques 2024](https://www.lcsqa.org/fr/rapport/guide-methodologique-calcul-des-statistiques-relatives-la-qualite-de-lair-2024)).  
**À vérifier.** Les seuils chiffrés internes d’acceptation, tableaux de bord d’astreinte et pondérations métier d’Atmo Occitanie ne sont pas tous publics ; ajouter exactitude de classe ATMO, matrice de confusion, POD/FAR/CSI et calibration répond au projet mais ne doit pas remplacer les métriques réglementaires.

## 14. Validation croisée acceptée et fuites de données

Une validation crédible sépare les dépendances correspondant à l’usage : bloc temporel/année future pour prévoir le futur, station laissée de côté ou blocs spatiaux pour généraliser à un site non vu, et idéalement leur combinaison ([Roberts et al., 2017, DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)).  
Le bloc spatial ou le tampon autour des points tests réduit l’optimisme dû à l’autocorrélation ([Valavi et al., 2019, DOI 10.1111/2041-210X.13107](https://doi.org/10.1111/2041-210X.13107)).  
Fuites typiques : partage aléatoire de lignes d’une même station/date, calcul des normalisations ou covariables agrégées sur tout le jeu, interpolation utilisant la station test, choix d’hyperparamètres sur le test, ou observation de J utilisée alors qu’elle n’était pas disponible à l’heure d’émission.  
Cette dernière liste est une **application méthodologique** des principes de blocage ; chaque variable doit être auditée avec son horodatage de disponibilité, pas seulement son horodatage physique.

## 15. Combien d’années faut-il pour une correction stable ?

**Il n’existe pas de règle admise trouvée du type “trois” ou “cinq ans”.** PREV’AIR indique seulement un apprentissage sur jours ou années précédents, sans minimum universel ([PREV’AIR, correction](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
Le besoin dépend du polluant, du nombre d’épisodes rares, des changements de stations, des versions CAMS/CHIMERE, des émissions et du climat ; CAMS avertit que ses systèmes connaissent des mises à niveau et recommande une réanalyse pour une série cohérente ([CAMS, prévisions globales](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts?tab=overview)).  
Pour les cartes stratégiques, les AASQA utilisent cinq ans afin de lisser la météorologie, mais cela ne constitue pas une règle d’apprentissage prévisionnel ([Atmo France, cartographie](https://www.atmo-france.org/article/la-cartographie)).  
**Critère défendable :** tracer les performances et leurs intervalles en fonction de la profondeur d’archive, avec tests par année et par épisode ; tant que rappel et calibration varient fortement, la stabilité n’est pas démontrée.

## 16. KED ou gradient boosting sur covariables ?

**Aucun vainqueur universel.** Sur les PM₂,₅ nationales américaines, le krigeage universel et un *downscaler* ont eu des RMSE plus faibles et corrélations plus fortes que la forêt aléatoire, mais le résultat dépend du contexte et de la validation ([Berrocal et al., 2020, DOI 10.1007/s13253-020-00400-0](https://pmc.ncbi.nlm.nih.gov/articles/PMC7451200/)).  
D’autres travaux trouvent un gain du random forest sur une LUR, ou du modèle hybride XGBoost–krigeage, ce qui indique une complémentarité entre non-linéarité et résidu spatial ([Bi et al., 2022, DOI 10.1021/acs.est.1c02653](https://doi.org/10.1021/acs.est.1c02653) ; [Wong et al., 2021, DOI 10.1016/j.envpol.2021.116846](https://doi.org/10.1016/j.envpol.2021.116846)).  
Le KED explicite la covariance spatiale et une variance conditionnelle ; le boosting représente des interactions non linéaires mais ne modélise pas automatiquement un résidu spatial ([Berrocal et al., 2020, DOI 10.1007/s13253-020-00400-0](https://doi.org/10.1007/s13253-020-00400-0) ; [Wong et al., 2021, DOI 10.1016/j.envpol.2021.116846](https://doi.org/10.1016/j.envpol.2021.116846)).  
**Conclusion :** comparer KED, boosting et boosting + krigeage des résidus sous validation station et temps ; proclamer le boosting supérieur sur un découpage aléatoire serait techniquement faible.

## 17. Quelles méthodes descendent un CTM sous le kilomètre ?

Les familles publiées sont : emboîtement dynamique à maille fine, modèles de rue/dispersion (SIRANE, ADMS), LUR ou ML fusionné au CTM, et krigeage/régression des résidus ; Atmo AuRA couple par exemple CHIMERE corrigé et SIRANE à 10 m ([Atmo AuRA, étude ZFE Lyon](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf)).  
Une fusion CTM–LUR par ML a produit du NO₂ à environ 100 m à Toronto ([Zalzal et al., 2024, DOI 10.1021/acs.est.4c03725](https://doi.org/10.1021/acs.est.4c03725)); une autre étude descend les PM₂,₅ et leurs sources avec covariables LUR ([Atmospheric Environment, 2023, DOI 10.1016/j.atmosenv.2023.119967](https://doi.org/10.1016/j.atmosenv.2023.119967)).  
CHIMERE dispose aussi d’une méthode de descente d’échelle en ligne sous-kilométrique publiée pour les pesticides ([Atmospheric Environment, 2024, DOI 10.1016/j.atmosenv.2023.120092](https://doi.org/10.1016/j.atmosenv.2023.120092)).  
**Hypothèse de faisabilité en quelques semaines :** une fusion statistique hors ligne sur covariables déjà prêtes ; SIRANE/ADMS, l’inventaire routier détaillé ou une nouvelle simulation CHIMERE demandent des entrées et validations que ce délai ne garantit pas.

## 18. Les GNN ont-ils été appliqués aux stations de qualité de l’air ?

Oui. AGATNet corrige des prévisions CMAQ de PM₂,₅ sur 183 stations sud-coréennes ; l’étude annonce une baisse moyenne de RMSE de 51,56 % en 2021 et un indice d’accord de 0,67 à 0,96 à +1 h, face à MLP, LSTM et PM₂,₅-GNN ([Dimri et al., 2024, DOI 10.1029/2024JH000244](https://doi.org/10.1029/2024JH000244)).  
Un GNN hétérogène a aussi été testé en Espagne sur quatre mois de données horaires provenant de 633 stations, avec occupation du sol, source dominante, mobilité et météo ; il dépasse la référence annoncée pour certains polluants et horizons, sans établir une supériorité universelle ([Terroso-Saenz et al., 2024, DOI 10.1145/3637492](https://doi.org/10.1145/3637492)).  
Une approche guidée par advection-diffusion a aussi été publiée pour la prévision multi-pas de PM₂,₅ ([Wang et al., 2022, DOI 10.1016/j.envpol.2021.118569](https://doi.org/10.1016/j.envpol.2021.118569)).  
**À vérifier avant transfert :** nombre et hétérogénéité des stations occitanes, disponibilité temps réel des covariables et gain face à persistance, correction par station, gradient boosting et CTM sous découpage temporel et station.

## 19. Prévision probabiliste calibrée pour une alerte asymétrique

Produire soit \(P(Y>s\mid X)\) directement, soit une distribution conditionnelle par régression quantile/ensemble, puis calibrer hors échantillon par isotonic/Platt ou quantiles conformalisés ([Romano et al., 2019, DOI 10.48550/arXiv.1905.03222](https://doi.org/10.48550/arXiv.1905.03222)).  
Vérifier fiabilité et netteté par diagrammes de fiabilité, Brier/Brier Skill Score, PIT ou couverture des quantiles ; la calibration d’ensemble a déjà été appliquée aux dépassements d’ozone ([Garaud et al., 2011, DOI 10.1029/2011JD015780](https://doi.org/10.1029/2011JD015780) ; [Gneiting et al., 2007, DOI 10.1111/j.1467-9868.2007.00587.x](https://doi.org/10.1111/j.1467-9868.2007.00587.x)).  
La décision devient « alerter si \(p>p^\*\) », où \(p^\*\) dépend du coût d’une alerte et de la perte évitée ; l’évaluation asymétrique doit rester une règle de décision, sans déformer la probabilité annoncée ([Ivarsson, 2020, DOI 10.1175/WAF-D-19-0013.1](https://doi.org/10.1175/WAF-D-19-0013.1)).  
**Prérequis à vérifier avec l’AASQA :** coûts relatifs faux négatif/fausse alerte, horizon de décision, définition spatiale de l’événement et assez de dépassements pour estimer la calibration de queue.

## 20. Pratique de météo-normalisation et pièges

La pratique publiée consiste à ajuster concentration sur météo, saisonnalité et temps — souvent par random forest — puis à rééchantillonner les conditions météo pour estimer une série « dé-météorisée » et des tendances/interventions ([Grange & Carslaw, 2019, DOI 10.1016/j.scitotenv.2018.10.344](https://doi.org/10.1016/j.scitotenv.2018.10.344)).  
Cette méthode sert à isoler une tendance des variations météo ; elle ne remplace pas la météo prévue dans un système de prévision ([Grange & Carslaw, 2019, DOI 10.1016/j.scitotenv.2018.10.344](https://doi.org/10.1016/j.scitotenv.2018.10.344)).  
Pièges documentés ou déduits de la validation structurée : fuite temporelle, extrapolation hors régimes appris, changements de station, émissions concomitantes et interprétation causale d’un modèle associatif ([Roberts et al., 2017, DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881) ; [Grange & Carslaw, 2019](https://doi.org/10.1016/j.scitotenv.2018.10.344)).  
**Exigence :** validation par blocs temporels, diagnostics de domaine de validité et analyses de sensibilité avec/sans tendance ; toute causalité attribuée à une politique reste **à vérifier** par un dessin contrefactuel adapté.

## 21. Zones d’Occitanie en dépassement ou proches des limites

En 2025, les dépassements de la limite annuelle actuelle de NO₂ sont confinés près du trafic : jusqu’à 550 habitants à Montpellier, 500 à Toulouse et 300 à Perpignan ; Nîmes déclare zéro personne au-dessus des valeurs limites actuelles ([Atmo Occitanie, bilan métropoles 2025](https://www.atmo-occitanie.org/actualites/montpellier-nimes-perpignan-et-toulouse-quelle-qualite-de-lair-en-2025-en-occitanie) ; [Atmoviz, PPA Nîmes](https://atmo-occitanie.org/datavis/30/3001)).  
L’objectif de qualité PM₂,₅ et l’objectif ozone ne sont pas respectés beaucoup plus largement ; la synthèse Toulouse donne aussi 1 456 300 habitants de Haute-Garonne au-dessus de l’objectif ozone en 2025 ([Atmo Occitanie, Toulouse 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/ETU_2026_124_%C3%89valuation%20de%20la%20qualit%C3%A9%20de%20l%E2%80%99air%20en%202025%20sur%20le%20territoire%20de%20Toulouse%20M%C3%A9tropole.pdf)).  
Avec les limites 2030, les quatre métropoles deviennent largement concernées par PM₂,₅, plus des corridors NO₂ et PM₁₀ autour des axes ([Atmo Occitanie, bilan métropoles 2025](https://www.atmo-occitanie.org/actualites/montpellier-nimes-perpignan-et-toulouse-quelle-qualite-de-lair-en-2025-en-occitanie)).  
Hors de ces quatre métropoles, la cartographie exhaustive par zone et polluant doit être extraite d’Atmoviz/Geod’air : **à vérifier**, plutôt que d’extrapoler les bilans urbains à toute la région.

## 22. Où en sont les ZFE de Toulouse et Montpellier ?

Toulouse a mis sa ZFE en vigueur le 1er mars 2022 ; Montpellier le 1er juillet 2022 et a étendu son périmètre à toutes les communes métropolitaines au 1er juillet 2026 ([Toulouse Métropole, qualité de l’air](https://metropole.toulouse.fr/mon-environnement/nature-et-climat/qualite-de-lair) ; [Montpellier Métropole, ZFE](https://www.montpellier.fr/vie-quotidienne/vivre-ici/se-deplacer/je-me-deplace-en-voiture/circuler-dans-la-zone-a-faibles-emissions)).  
La tentative parlementaire de suppression nationale a été censurée en mai 2026 ; les pages officielles locales restent donc la référence pratique à la date de ce document ([Légifrance, loi 2026-403, art. 27 déclaré non conforme par la décision 2026-903 DC](https://www.legifrance.gouv.fr/jorf/article_jo/JORFARTI000054131772) ; [Montpellier, page ZFE](https://www.montpellier.fr/vie-quotidienne/vivre-ici/se-deplacer/je-me-deplace-en-voiture/circuler-dans-la-zone-a-faibles-emissions)).  
À Toulouse, Atmo évalue l’évolution du parc, les aides mobilité, l’abaissement à 30 km/h et réalise un suivi multi-sites NO₂ ; la campagne 2024–2025 vérifie aussi les cartes en périphérie ([Atmo Occitanie, Toulouse 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/ETU_2026_124_%C3%89valuation%20de%20la%20qualit%C3%A9%20de%20l%E2%80%99air%20en%202025%20sur%20le%20territoire%20de%20Toulouse%20M%C3%A9tropole.pdf) ; [suivi NO₂ 2024](https://www.atmo-occitanie.org/sites/default/files/publications/2025-12/ETU-2025-189%20-Suivi_concentrations_NO2_Toulouse_M%C3%A9tropole_2024_VF.pdf)).  
À Montpellier, le dispositif associe stations, inventaire, modélisation et mesures renforcées près des axes ; l’évaluation causale propre de la ZFE, séparée des autres tendances, reste **à vérifier** ([Atmo Occitanie, dispositif Montpellier](https://atmo-occitanie.org/actualites/communique-de-presse-evaluer-la-qualite-de-lair-une-mission-au-service-de-tous)).

## 23. Que contiennent les PPA d’Occitanie ?

La DREAL recense des PPA approuvés pour Montpellier, Nîmes et Toulouse ; Perpignan est en élaboration après les dépassements NO₂ de 2021–2022 ([DREAL Occitanie, PPA](https://www.occitanie.developpement-durable.gouv.fr/plan-de-protection-de-l-atmosphere-ppa-a27236.html) ; [DREAL, PPA Perpignan](https://www.occitanie.developpement-durable.gouv.fr/lancement-de-l-elaboration-du-ppa-de-perpignan-a27178.html)).  
Le PPA de Nîmes 2025–2030 comporte 23 actions : 8 transport, 6 activités économiques, 6 intersectorielles et 3 chauffage au bois ([DREAL, PPA Nîmes](https://www.occitanie.developpement-durable.gouv.fr/le-plan-de-protection-de-l-atmosphere-a27140.html)).  
Le troisième PPA toulousain prévoit 30 mesures sur transport, résidentiel-tertiaire, activités économiques et actions transversales, sur 113 communes ([DREAL, révision PPA Toulouse](https://www.occitanie.developpement-durable.gouv.fr/revision-du-plan-de-protection-de-l-atmosphere-de-a27060.html)).  
Montpellier 2026–2030 dispose de documents approuvés et d’un suivi 2026 ; les listes détaillées, pilotes, indicateurs et état d’avancement doivent être lus dans chaque cahier d’actions, pas résumés comme un seul plan régional ([DREAL, PPA Montpellier 2026–2030](https://www.occitanie.developpement-durable.gouv.fr/revision-du-plan-de-protection-de-l-atmosphere-r9783.html)).

## 24. Campagnes spécifiques d’Atmo Occitanie

Pesticides : suivi d’octobre à septembre, passé à dix sites en 2023–2024, avec prélèvements des phases gazeuse et particulaire et 192 substances recherchées dans la campagne élargie ([Atmo Occitanie, surveillance 2023–2024](https://www.atmo-occitanie.org/occitanie-surveillance-des-pesticides-dans-lair-ambiant-2023-2024) ; [résultats 2025](https://atmo-occitanie.org/actualites/pesticides-perturbateurs-endocriniens-et-pfas-polluants-eternels-dans-lair-les-resultats)).  
Biomasse : Hautes-Pyrénées, janvier 2022–avril 2023, mesures de particules et traceurs de combustion croisées avec surfaces brûlées satellitaires ([Atmo Occitanie, caractérisation 2023](https://www.atmo-occitanie.org/hautes-pyrenees-caracterisation-des-sources-de-particules-2023)).  
Pollens : projet lancé en 2023, prévision quotidienne depuis le printemps 2025, puis Poll’Occ J+1 pour 22 plantes en 2026, combinant mesures, météo, données Copernicus et observations phénologiques ([Atmo Occitanie, prévision pollens](https://www.atmo-occitanie.org/actualites/la-prevision-des-pollens-allergisants-en-occitanie) ; [Poll’Occ 2026](https://www.atmo-occitanie.org/occitanie-dossier-de-presse-pollocc-le-dispositif-de-prevision-des-pollens-made-in-occitanie-2026)).  
Odeurs : SignalAir remplace ODO depuis le 2 janvier 2025 ; sept observatoires croisent signalements, météo, activités et parfois mesures, avec bilans trimestriels/annuels ([Atmo Occitanie, SignalAir](https://www.atmo-occitanie.org/actualites/odo-laisse-sa-place-signalair-le-nouvel-outil-pour-declarer-les-nuisances-odorantes-en) ; [observatoires citoyens](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-evaluer-la-qualite-de-lair/observatoires-citoyens-les-citoyens)).

## 25. Particularités météorologiques régionales

Tramontane/cers : flux turbulent d’ouest à nord-ouest accéléré entre Massif central et Pyrénées vers l’Aude et le Roussillon, généralement dispersif mais pouvant transporter ou assécher une masse d’air ([Météo-France, tramontane](https://meteofrance.com/actualites-et-dossiers/comprendre-la-meteo/le-vent/la-tramontane)).  
Autan : vent d’est-sud-est accéléré vers le Lauragais et Toulouse ; son effet qualité de l’air dépend de l’origine de la masse d’air, donc « autan = propre/pollué » serait **à vérifier cas par cas** ([Météo-France, autan](https://meteofrance.com/actualites-et-dossiers/comprendre-la-meteo/le-vent-dautan)).  
Sur le littoral, Atmo Occitanie relie les brises de terre/mer au transport d’ozone et de ses précurseurs entre mer et terre ; l’existence et l’intensité du mécanisme pour un épisode donné restent **à vérifier** par les observations et trajectoires ([Atmo Occitanie, bilan ozone 2020](https://atmo-occitanie.org/sites/default/files/publications/2021-06/ETU-2021-078%20Pollution%20%C3%A0%20l%27ozone%202020.pdf)).  
Dans les vallées pyrénéennes, les inversions anticycloniques piègent l’air froid et les polluants ; Atmo documente en hiver l’effet combiné du relief, du calme et des émissions de biomasse ([Météo-France, inversion en relief](https://meteofrance.com/actualites-et-dossiers/actualites/climat/relief-des-temperatures-minimales-plus-froides-dans-les-vallees) ; [Atmo Occitanie, Hautes-Pyrénées](https://www.atmo-occitanie.org/sites/default/files/publications/2022-04/PUB%202022-007%20Dossier%20de%20presse_Etude%20particules%20Hautes-Pyr%C3%A9n%C3%A9es.pdf)).

## 26. Quotidien d’un ingénieur modélisation en AASQA

Une offre Atmo Occitanie décrit : maintenir et faire évoluer les chaînes opérationnelles, automatiser les traitements, tester la sensibilité, mettre à jour les prévisions, exploiter les résultats, simuler des scénarios et rédiger les notes/rapports ([Atmo Occitanie, offre ingénieur modélisation](https://www.atmo-occitanie.org/sites/default/files/2021-01/Atmo%20Occitanie_Offre%20d%27emploi%20Ing%C3%A9nieur%28e%29%20d%27Etude%20Mod%C3%A9lisation.pdf)).  
En astreinte, le travail inclut contrôle des entrées, comparaison modèle–mesure J−1/J0, consultation météo et autres modèles, justification des corrections, bulletin et décision d’épisode ([LCSQA, référentiel prévision 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
Une part importante est donc exploitation/qualité/traçabilité, pas seulement développement : logs, incidents, archivage, check-lists et communication aux partenaires sont exigés par le même référentiel.  
**Supposition sur la répartition horaire :** elle varie selon pôle, saison et astreinte ; aucun pourcentage public fiable ne permet de dire combien de temps va au code, aux études ou aux réunions.

## 27. Compétences réellement rares ou abondantes

**Faits observables dans les offres :** Python/R/Linux, visualisation, analyse environnementale et rédaction sont demandés ; ADMS/SIRANE, maintien de chaînes et scénarisation sont explicitement recherchés ([Atmo Occitanie, offre modélisation](https://www.atmo-occitanie.org/sites/default/files/2021-01/Atmo%20Occitanie_Offre%20d%27emploi%20Ing%C3%A9nieur%28e%29%20d%27Etude%20Mod%C3%A9lisation.pdf)).  
Les postes qualité de l’air insistent aussi sur pilotage, échéances, rapports, présentation et relation partenaires ([Atmo Occitanie, offre ingénieur qualité de l’air](https://www.atmo-occitanie.org/sites/default/files/2025-07/Ing%C3%A9nieur%20qualit%C3%A9%20de%20l%27air_1.pdf)).  
**Inférence, pas statistique RH :** la combinaison rare est atmosphère + géospatial + exploitation Linux robuste + validation sans fuite + traduction réglementaire + rédaction compréhensible ; le ML générique et les notebooks isolés sont plus faciles à trouver.  
Le degré réel de rareté, les technologies en tension et l’équilibre développement/expertise chez Atmo Occitanie sont **à vérifier avec le responsable du pôle**, faute de données publiques de candidatures.

## 28. Outils et formats de fait

Python, R et Linux sont explicitement demandés par Atmo Occitanie ; ADMS et SIRANE sont cités comme modèles métier ([offre ingénieur modélisation](https://www.atmo-occitanie.org/sites/default/files/2021-01/Atmo%20Occitanie_Offre%20d%27emploi%20Ing%C3%A9nieur%28e%29%20d%27Etude%20Mod%C3%A9lisation.pdf)).  
Pour les champs atmosphériques, CAMS livre GRIB et NetCDF à pas horaire ; pour les services cartographiques, WMS/WCS/WFS et API REST sont des standards reconnus ([CAMS, produit européen](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview) ; [AtmoSud, API](https://api.atmosud.org/prevision/)).  
Pour les mesures françaises, Geod’air utilise codes ISO, fichiers ISO automatiques et XML manuel, et expose une API ; les métadonnées et statuts de validation comptent autant que la valeur ([LCSQA, référentiel constituants](https://www.lcsqa.org/fr/rapport/referentiel-des-constituants) ; [API Geod’air](https://www.lcsqa.org/fr/actualite/geodair-ouvre-son-interface-de-programmation-applicative-api)).  
**Signal de déconnexion :** ne proposer qu’Excel/CSV et un notebook sans CRS, unités, fuseau, version, logs ni déploiement ; ce jugement est une **inférence professionnelle**, pas une règle officielle d’exclusion.

## 29. Comment un jury départage deux candidats proches

Atmo Occitanie publie comme critères autonomie, rigueur, organisation, analyse/synthèse, intégration en équipe, initiative, capacité à rendre compte et qualité rédactionnelle ([offre modélisation](https://www.atmo-occitanie.org/sites/default/files/2021-01/Atmo%20Occitanie_Offre%20d%27emploi%20Ing%C3%A9nieur%28e%29%20d%27Etude%20Mod%C3%A9lisation.pdf) ; [offre qualité de l’air](https://www.atmo-occitanie.org/sites/default/files/2025-07/Ing%C3%A9nieur%20qualit%C3%A9%20de%20l%27air_1.pdf)).  
Le poste implique aussi présentation externe, échanges partenaires, respect d’échéances et rédaction/relecture, donc l’écart ne se joue pas seulement sur le score d’un modèle ([offre qualité de l’air](https://www.atmo-occitanie.org/sites/default/files/2025-07/Ing%C3%A9nieur%20qualit%C3%A9%20de%20l%27air_1.pdf)).  
**Inférence :** à technique égale, gagnera souvent celui qui reconnaît une incertitude, explique une décision reproductible, comprend l’astreinte et sait livrer un résultat auditable à un partenaire non spécialiste.  
Il n’existe pas de grille publique du jury Atmo Occitanie : pondération, exercice technique et rôle de la motivation sont **à vérifier**.

## 30. Erreur de posture la plus fréquente d’un candidat ML

**Inférence, non enquête publiée :** arriver en expliquant que le ML va « remplacer » CHIMERE ou l’expertise, avant d’avoir identifié ce que PREV’AIR corrige déjà, les contraintes de seuil, les données disponibles à l’heure de décision et la traçabilité attendue.  
Cette posture heurte une chaîne où observations, CTM, correction, météo et expertise humaine sont explicitement combinés ([LCSQA, référentiel prévision 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
La seconde erreur est de vendre une RMSE moyenne sans validation station/temps, rappel des épisodes, fausses alertes, incertitude et analyse des échecs ; PREV’AIR publie déjà biais, RMSE et corrélation, donc ce seul tableau n’est pas une contribution ([PREV’AIR, « Évaluations »](https://www.prevair.org/le-systeme-prevair/la-production/evaluations)).  
La bonne posture est « complément falsifiable et exploitable » : annoncer ce que l’on sait, ce que l’on suppose, ce qui ferait abandonner l’idée — exactement le cas du KED PREV’AIR établi à la question 2.
