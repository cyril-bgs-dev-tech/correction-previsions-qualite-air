# Bloc A — référentiel français d’évaluation

## A1. Convention de calcul

- **Verdict : contredit (un opérateur est faux, le reste est confirmé avec une réserve d’échéance).**
- **Source :** le [référentiel technique national LCSQA, applicable au 01/01/2022](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf), p. 3–5 et annexe 1 p. 10–11 ; [arrêté du 16 avril 2021, art. 13](https://aida.ineris.fr/reglementation/arrete-160421-relatif-dispositif-national-surveillance-qualite-lair-ambiant) ; [PREV’AIR, « Évaluations »](https://www.prevair.org/le-systeme-prevair/la-production/evaluations) ; [Airparif, bilan des indicateurs de prévision 2022](https://www.lcsqa.org/system/files/media/documents/Bilan_Indicateurs_Pr%C3%A9vision_2022_AIRPARIF.pdf).
- Les observations sont bien celles des stations de fond, ventilées en urbaines, périurbaines et rurales ; les scores temporels sont calculés station par station puis moyennés par filtre géographique ou typologique ; O₃ est évalué sur son maximum journalier d’avril à septembre et PM10 sur sa moyenne journalière annuelle. La moyenne décrite est arithmétique, sans pondération indiquée.
- Le seuil de disponibilité est **au moins 75 %** : le pseudo-code dit `sum(idx) >= 0,75*nb_times`. La page PREV’AIR résume « supérieur à 75 % », mais ce résumé ne doit pas remplacer l’opérateur explicite du RTN. Les échéances sont séparées, toutefois les objectifs nationaux obligatoires illustrés concernent J0 et J1 ; J+2/J+3 peuvent être ajoutés sans être présentés comme une exigence de ce texte.
- **Conséquence :** remplacer partout `> 75 %` par `≥ 75 %`, qualifier J+2/J+3 d’extension, et produire en parallèle une table strictement conforme : fond, station d’abord, moyenne simple, horizon séparé, O₃ avril–septembre.

## A2. Seuils et déclenchement

- **Verdict : contredit (les valeurs sont essentiellement justes, mais deux intitulés omettent leur durée et 120 µg/m³ ne déclenche pas la procédure).**
- **Source :** [code de l’environnement, art. R. 221-1](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000022964539) ; [directive 2008/50/CE, annexe VII](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX%3A32008L0050) ; [arrêté du 7 avril 2016 consolidé, notamment art. 2 à 4](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2026-05-07) ; [RTN LCSQA, p. 7–9 et annexe 2](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf).
- O₃ 120 µg/m³ en maximum journalier de la moyenne glissante 8 h est une valeur cible, historiquement appréciée avec un nombre annuel de dépassements moyenné sur trois ans : ce n’est ni un seuil d’information ni, pris jour par jour, un déclencheur préfectoral. O₃ 180 µg/m³ horaire est le seuil d’information ; 240 µg/m³ est le premier seuil d’alerte, avec une condition de **trois heures consécutives**. NO₂ 200 µg/m³ horaire est le seuil d’information et peut aussi intervenir dans certaines conditions de persistance ; le seuil d’alerte principal est 400 µg/m³ pendant trois heures consécutives. PM10 50 µg/m³ en moyenne journalière est le seuil d’information ; 80 µg/m³ est le seuil d’alerte.
- L’arrêté de 2016 définit l’épisode comme un dépassement **constaté ou prévu** et permet, lorsque la modélisation est utilisée, de le caractériser sans attendre confirmation par mesure. Le déclenchement effectif dépend aussi des critères de superficie, de population ou de situation locale et de la procédure préfectorale applicable : une valeur à une station ne suffit pas à elle seule.
- Le « 3,5 fois plus » à 120 peut être montré comme **analyse secondaire de discrimination au niveau de la valeur cible**, jamais comme performance de détection des épisodes ou alertes. Présenté seul à une AASQA, il induirait une conclusion opérationnelle que l’endpoint ne mesure pas. Les 32 dépassements station-jour à 180, avec 3 détections brutes contre 2 corrigées, doivent apparaître immédiatement ; ils indiquent à la fois absence de gain observé et forte imprécision, pas une supériorité démontrée de CAMS.
- **Conséquence :** renommer l’indicateur à 120, ajouter durées et critères spatiaux aux seuils, et placer la table à 180 au même niveau visuel que le résultat à 120.

## A3. Indice ATMO

- **Verdict : contredit (règle du maximum confirmée ; exclusivité de la modélisation et chiffres empiriques non établis par le texte).**
- **Source :** [arrêté du 10 juillet 2020, art. 3 et 4](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000042164835/) ; [guide technique du nouvel indice ATMO, version du 14/12/2020](https://www.atmo-occitanie.org/sites/default/files/2020-12/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf) ; [Atmo Occitanie, calcul de l’indice](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-evaluer-la-qualite-de-lair/lindice-qualite-de-lair-connaitre-la) ; calculs locaux dans [`reports/INDICE_ATMO.md`](../reports/INDICE_ATMO.md).
- L’indice agrège bien cinq sous-indices et retient le plus dégradé. En revanche, l’article 3 autorise une concentration issue de la **mesure ou de la modélisation** représentative de la pollution de fond ; il n’impose pas « la modélisation et non les stations ». Le guide recommande une mise en œuvre spatialisée et Atmo Occitanie combine cartographie, stations, météo et expertise pour ses prévisions communales.
- Les valeurs 47 265 conformités sur 47 300 donnent bien `47 265 / 47 300 = 99,926 %`, mais elles ne sont vérifiables extérieurement qu’avec l’extraction officielle exacte, sa requête, sa date et son empreinte. Les 35 exceptions interdisent le mot « exactement ». Même statut pour les 87,8 % : c’est un résultat du jeu analysé, non une propriété réglementaire ni nécessairement une fréquence stable.
- **Conséquence :** écrire « conformité empirique de 99,926 % sur l’extraction archivée » et « O₃ déterminant dans 87,8 % de cet échantillon », archiver requête/horodatage/hash, et remplacer l’opposition stations–modèle par la formulation juridique mesure **ou** modélisation de fond.

# Bloc B — validation spatiale

## B1. Construction des plis et du fossé

- **Verdict : confirmé (protocole valide pour prédire en stations non vues, avec trois réserves d’implémentation).**
- **Source :** Roberts et al. (2017), *Ecography*, [doi:10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881) ; Valavi et al. (2019), *Methods in Ecology and Evolution*, [doi:10.1111/2041-210X.13107](https://doi.org/10.1111/2041-210X.13107) ; implémentation locale [`scripts/validation_bloquee.py`](../scripts/validation_bloquee.py).
- Tenir une grappe entière hors apprentissage est une **validation croisée groupée spatialement** (*spatial clustering/grouped spatial CV*). Ce n’est pas exactement un pavage en blocs réguliers : chaque pli peut réunir plusieurs grappes non contiguës, ce qui est acceptable si l’estimand est la généralisation vers de nouvelles stations et si géométrie et distances sont publiées.
- Le code calcule la distance minimale de chaque station d’apprentissage à **toutes les stations du pli test** puis exclut celles situées à moins de `r` : c’est bien l’union de buffers ponctuels décrite par la validation spatiale tamponnée. Un buffer autour du polygone enveloppant le bloc testerait un autre estimand et exclurait aussi des zones sans station test. En revanche, le rayon doit être choisi avant lecture du score, d’après la portée du variogramme des résidus ou la distance de transfert visée.
- Trois réserves : les hyperparamètres semblent issus du protocole ancien et exigent donc une sélection imbriquée spatiale ; `stations_ecartees_par_fosse` additionne des exclusions par pli et ne prouve pas « 34 stations distinctes » ; plusieurs graines et géométries de grappes sont nécessaires pour quantifier la variabilité du découpage.
- **Conséquence :** conserver ce protocole, renommer précisément le compteur, figer le rayon a priori et refaire sélection de variables/hyperparamètres dans une boucle interne spatialement bloquée.

## B2. Amplitude de l’optimisme

- **Verdict : confirmé (plausible, sans fourchette universelle permettant de le dire “attendu”).**
- **Source :** Just et al. (2020), PM2.5 journalier à 1 km, nord-est des États-Unis, *Atmospheric Environment* 239, RMSE 2,10 en CV aléatoire contre 3,11 µg/m³ en CV spatiale, [doi:10.1016/j.atmosenv.2020.117649](https://doi.org/10.1016/j.atmosenv.2020.117649) ; Ren, Mi & Georgopoulos (2020), O₃ MDA8 aux États-Unis, gains des modèles non linéaires d’environ 17 % en CV ordinaire, 6 % en validation spatiale et 11 % externe, [doi:10.1016/j.envint.2020.105827](https://doi.org/10.1016/j.envint.2020.105827).
- La littérature montre que le changement de plan peut déplacer fortement le RMSE ou le gain relatif ; les deux exemples ne sont toutefois pas directement comparables au post-traitement CAMS, aux mêmes polluants, horizons et réseaux. Il n’existe donc pas de valeur de référence qui rende −10,1 points « normal » au sens métrologique.
- Le passage O₃ de +28,60 % à +18,47 % représente 10,13 points, mais aussi une baisse relative d’environ 35 % du gain annoncé ; les deux formulations doivent être distinguées. Le résultat est crédible, mais sa stabilité doit être établie sur plusieurs partitions et rayons fixés indépendamment.
- **Conséquence :** présenter −10,1 points comme l’optimisme **mesuré dans ce jeu**, accompagné de la dispersion entre partitions, sans en faire une constante de la littérature.

## B3. Différence entre NO₂ et O₃

- **Verdict : non vérifiable avec les sources accessibles (explication physiquement cohérente, causalité non démontrée).**
- **Source :** Karner, Eisinger & Niemeier (2010), revue des gradients près des routes, *Environmental Science & Technology*, [doi:10.1021/es100008x](https://doi.org/10.1021/es100008x) ; Roberts et al. (2017), choix du bloc selon la structure et la tâche de transfert, [doi:10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881) ; résultats locaux [`reports/validation_bloquee_NO2.csv`](../reports/validation_bloquee_NO2.csv), [`reports/validation_bloquee_O3.csv`](../reports/validation_bloquee_O3.csv).
- Un signal routier NO₂ peut décroître fortement sur quelques centaines de mètres ; un voisin à 2 km peut donc peu informer la composante locale, surtout si les covariables routières l’explicitent déjà. Cela ne prouve pas que cette composante explique l’écart observé : NO₂ conserve aussi des structures météorologiques et régionales.
- Alternatives à tester : portée différente de l’autocorrélation des **résidus** ; composition trafic/fond inégale entre plis ; dénominateur du gain brut différent ; effectif ; géométrie des grappes ; dépendance aux covariables fixes. Dans l’exécution courante, le buffer NO₂ à 25 km n’exclut aucune station, donc l’absence d’effet du fossé ne renseigne pas sa robustesse à 25 km.
- **Conséquence :** remplacer l’explication causale par une hypothèse, puis comparer variogrammes/corrélogrammes des résidus, types de stations et distributions des distances à support identique entre polluants.

## B4. Chiffre à publier

- **Verdict : confirmé (publier les deux, mais avec un seul chiffre principal).**
- **Source :** Roberts et al. (2017), [doi:10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881) ; Just et al. (2020), [doi:10.1016/j.atmosenv.2020.117649](https://doi.org/10.1016/j.atmosenv.2020.117649).
- Si la promesse est « prévoir en un lieu/station absent de l’entraînement », le résultat principal doit être le bloc + buffer dont la distance correspond au cas d’usage : ici +18,47 % seulement si 50 km a été choisi a priori. Le +28,60 % ne doit plus être le résultat de généralisation principal.
- Le score ancien reste utile comme diagnostic transparent de l’optimisme et comme estimand éventuel d’interpolation près d’un réseau dense ; il doit être étiqueté comme tel, pas mis en concurrence à égalité. Le score bloqué sans buffer est une sensibilité intermédiaire pertinente.
- **Conséquence :** mettre le bloqué/tamponné dans le résumé, reléguer l’ancien protocole et l’écart dans l’audit méthodologique, et publier les distances train–test ainsi que l’incertitude entre partitions.

# Bloc C — choix de méthode

## C1. Agrégation des scores

- **Verdict : confirmé.**
- **Source :** définition de la RMSE dans le [RTN LCSQA, annexe 1](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf) ; Thunis et al. (2018), définition du MQI, *Air Quality, Atmosphere & Health*, [doi:10.1007/s11869-018-0631-z](https://doi.org/10.1007/s11869-018-0631-z).
- Pour des mois disjoints, la RMSE globale exacte est `sqrt(Σ n_m RMSE_m² / Σ n_m)`. Le biais global est `Σ n_m biais_m / Σ n_m`, à condition que chaque biais ait le même signe conventionnel et que `n_m` compte exactement les couples sous-jacents.
- Une corrélation ne s’agrège pas linéairement : il faut la recalculer sur les couples bruts, ou conserver `n, Σx, Σy, Σx², Σy², Σxy`. Une moyenne des transformations de Fisher répond à une question méta-analytique différente. Pour le rendu AASQA, le RTN demande de toute façon score temporel par station puis moyenne des stations.
- Le MQI, ratio comportant RMSE et incertitude d’observation, ne s’agrège pas par moyenne simple des MQI mensuels. Il faut recomposer séparément les sommes quadratiques du numérateur et du dénominateur selon la version FAIRMODE appliquée, puis former le ratio au grain final ; la conformité stationnelle ne doit pas être remplacée par un seul MQI groupé.
- **Conséquence :** centraliser des accumulateurs suffisants par score et interdire par test toute moyenne arithmétique de RMSE, corrélations ou MQI.

## C2. Forme du résidu et rétro-transformation

- **Verdict : contredit.**
- **Source :** Duan (1983), estimateur de *smearing*, *Journal of the American Statistical Association*, [doi:10.1080/01621459.1983.10478017](https://doi.org/10.1080/01621459.1983.10478017) ; implémentation [`scripts/forme_du_residu.py`](../scripts/forme_du_residu.py) ; résultats [`reports/forme_du_residu_O3.csv`](../reports/forme_du_residu_O3.csv).
- La reconstruction naïve d’une moyenne apprise en espace logarithmique estime une grandeur géométrique/médiane et sous-estime en général la moyenne sur l’échelle originale. Une correction `exp(σ²/2)` n’est exacte que sous hypothèses lognormales et homoscédastiques ; ici il faut estimer, dans chaque pli d’apprentissage, un facteur de smearing global ou conditionnel puis l’appliquer au pli test. La forme racine a le même problème de Jensen : le carré de l’espérance conditionnelle omet la variance conditionnelle.
- Dire que le biais global −0,88 « explique environ 4 % de la dégradation de queue » n’est pas défendable : biais moyen et RMSE du décile supérieur sont deux fonctionnelles différentes, et aucune décomposition calculée ne relie les deux. Le plan actuel ne permet pas d’attribuer ce pourcentage.
- Une implémentation correcte **peut** changer le classement : racine n’est qu’à 0,008 µg/m³ de la différence et les écarts des formes log sont petits au regard des IC consignés dans les journaux. Le sens et l’ampleur sont inconnus avant recalcul hors pli ; le plancher `max(obs, 1)` du rapport modifie en outre la cible pour les petites valeurs et demande une sensibilité.
- **Conséquence :** retirer le « 4 % », apprendre toute correction de rétro-transformation exclusivement dans le pli train, puis rerun complet en validation spatiale imbriquée avec RMSE globale, queue et CSI.

## C3. Critère de rétention

- **Verdict : contredit (bonne correction d’un biais d’unité, justification statistique insuffisante).**
- **Source :** Diebold & Mariano (1995), comparaison de pertes de prévision dépendantes dans le temps, *Journal of Business & Economic Statistics*, [doi:10.1080/07350015.1995.10524599](https://doi.org/10.1080/07350015.1995.10524599) ; Gneiting & Raftery (2007), scores propres, *JASA*, [doi:10.1198/016214506000001437](https://doi.org/10.1198/016214506000001437) ; règle locale [`src/aq/eval/critere.py`](../src/aq/eval/critere.py). Aucune règle AASQA/LCSQA accessible ne fixe un seuil de rétention à 2 %.
- Passer de 0,3 µg/m³ à un pourcentage supprime bien l’inégalité mécanique entre polluants. Mais la largeur de l’IC mesure l’incertitude de l’expérience, pas l’utilité opérationnelle : choisir 2 % parce qu’il dépasse les IC observés mélange **effet minimal pertinent** et **puissance**.
- Le raisonnement devient adaptatif — et donc optimiste — si ces mêmes essais ont servi à fixer 2 %, choisir les variables et annoncer le gain. Il n’est pas circulaire si le seuil est figé sur une étude pilote distincte puis évalué une seule fois dans une boucle externe. La condition `IC_bas > 0` ne corrige ni la multiplicité des pistes ni le biais du gagnant.
- Il faut fixer une marge pratique `δ` d’après coût, latence et endpoint décisionnel, puis demander que l’IC apparié par blocs/stations soit compatible avec cette marge dans une évaluation externe imbriquée. « Non significatif » signifie « gain non démontré », pas « gain nul ».
- **Conséquence :** présenter 2 % comme règle interne provisoire, séparer marge d’utilité et preuve statistique, et réévaluer toutes les pistes retenues dans un outer split spatial/temporal jamais utilisé pour leur sélection.

# Bloc D — défauts silencieux encore plausibles

## D1. Appariement temporel et provenance

- **Verdict : non vérifiable avec les sources accessibles.**
- **Source :** aucune preuve d’exécution ligne à ligne n’est archivée dans le dossier consulté ; les invariants ci-dessous sont des tests proposés, non le constat d’un défaut.
- Risques : confusion heure d’émission/heure valide/lead, UTC–heure locale et jours de changement d’heure, MDA8 attribuée au mauvais jour, run CAMS remplacé par une analyse ultérieure, observations provisoires mêlées aux validées, changement de cycle amont masqué.
- Test bon marché : tirer 50 lignes stratifiées par horizon et DST, reconstruire manuellement `émission + lead = validité`, essayer les décalages ±1 h et ±24 h comme test négatif, et comparer par hash le champ brut local au run CAMS daté. Ajouter un manifeste par cycle/version.
- **Conséquence :** bloquer toute publication tant qu’un audit traçable issue–valid time–run–observation n’a pas passé ces contrôles.

## D2. Fuite de cible et disponibilité opérationnelle

- **Verdict : non vérifiable avec les sources accessibles.**
- **Source :** Roberts et al. (2017), [doi:10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881), pour la dépendance ignorée par la validation ; aucune matrice locale exhaustive « variable × horodatage de disponibilité » accessible.
- Risques : ERA5 ou observation disponible après l’émission, moyenne glissante centrée, statistique de station ou normalisation ajustée avant découpage, covariable agrégée contenant le pli test, choix de variables/hyperparamètres sur les scores de test.
- Test bon marché : établir un registre `variable, timestamp de valeur, première disponibilité, source`, faire tous les `fit` dans les plis, ajouter un embargo temporel, puis permuter ou retarder les variables suspectes. Un test doit échouer volontairement si une date postérieure à l’émission entre dans la matrice.
- **Conséquence :** considérer comme non opérationnel tout gain dont chaque prédicteur ne dispose pas d’une preuve de disponibilité à l’émission.

## D3. Sélection de population et support commun

- **Verdict : contredit (une incohérence concrète est déjà visible).**
- **Source :** journaux et sorties locaux [`reports/validation_bloquee_O3.csv`](../reports/validation_bloquee_O3.csv) et [`scripts/validation_bloquee.py`](../scripts/validation_bloquee.py) ; RTN LCSQA, filtre de disponibilité et stations de fond, [annexe 1](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf).
- La médiane de voisinage 2,4 km et les 79 % à moins de 10 km décrivent dans le script un ensemble d’environ 813 stations ; l’exécution O₃ évaluée porte sur 270 stations et son journal indique une médiane proche de 14,3 km, tout en conservant environ 79 % de voisins dans un autre pli. Mettre « 2,4 km » sur la ligne O₃ mélange donc deux populations.
- Autres risques : disponibilité non aléatoire, fermetures/ouvertures de stations, types trafic/fond, score sur l’intersection des produits seulement, exclusion différenciée de jours difficiles. Test bon marché : diagramme de flux avec effectifs après chaque filtre, tableau inclus/exclus par type/région/saison, puis scores sur support propre à chaque produit et support commun.
- **Conséquence :** corriger immédiatement la distance attribuée à O₃ et versionner un tableau de populations qui alimente automatiquement toutes les pages.

## D4. Dépendance et intervalles d’incertitude

- **Verdict : non vérifiable avec les sources accessibles.**
- **Source :** Lahiri (2003), *Resampling Methods for Dependent Data*, [doi:10.1007/978-1-4757-3803-2](https://doi.org/10.1007/978-1-4757-3803-2) ; la pertinence exacte du bootstrap local dépend du code et de l’estimand.
- Bootstrapper les stations préserve la série temporelle interne de chaque station, mais ne traite pas nécessairement les jours météorologiques communs entre stations, les épisodes régionaux, ni la variabilité du découpage spatial. Les dizaines de milliers de station-jours ne sont pas autant de réplications indépendantes.
- Test bon marché : tracer ACF temporelle et variogramme des résidus, comparer IC station, jour, événement et bootstrap à deux dimensions station×jour ; refaire les plis avec plusieurs graines et rapporter le nombre de stations **et d’événements** indépendants.
- **Conséquence :** choisir l’unité de rééchantillonnage selon la prétention — nouvelle station, nouvelle période ou nouvel épisode — et publier une sensibilité à au moins deux schémas.

## D5. Métrique, grain et opérateur

- **Verdict : non vérifiable avec les sources accessibles.**
- **Source :** RTN LCSQA, grains O₃/PM10, station-first et contingence regroupée, [p. 3–12](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf) ; arrêté du 10 juillet 2020 pour l’indice ATMO, [art. 3–4](https://www.legifrance.gouv.fr/jorf/id/JORFTEXT000042164835/).
- Risques : horaire contre MDA8, `>` contre `≥`, station-jour contre événement régional/critère AMU, moyenne pondérée contre station-first, indice stationnel contre maximum spatial communal, sélection du seuil donnant le récit le plus favorable.
- Test bon marché : registre exécutable de chaque endpoint (`unité, fenêtre, opérateur, seuil, grain spatial, dénominateur`) et petits tableaux de vérité calculés à la main pour égalité au seuil, données manquantes, DST et agrégation multi-stations. Produire automatiquement une table RTN parallèle à toute table de recherche.
- **Conséquence :** interdire tout nom réglementaire dans les sorties si la définition exécutable ne pointe pas vers l’article et le test unitaire correspondants.

## D6. Identité du comparateur et dérive amont

- **Verdict : non vérifiable avec les sources accessibles.**
- **Source :** [documentation du jeu CAMS « forecasts optimised at observation sites »](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts-optimised-at-observation-sites) ; aucune preuve locale exhaustive d’identité des runs et versions dans les résultats examinés.
- Risques : comparer une correction à un CAMS brut qui n’est pas exactement celui dont elle part, révisions du produit téléchargé, cycles CAMS différents entre entraînement et test, dates ou stations communes différentes entre produit officiel et candidat.
- Test bon marché : pour chaque couple station–validité, vérifier l’égalité du prédicteur CAMS de départ, figer identifiant de run/cycle, URL, date de récupération et hash, puis calculer chaque gain contre son propre brut et sur une intersection explicitement identique.
- **Conséquence :** ne revendiquer une supériorité sur le produit Copernicus qu’après une table d’appariement un-à-un et un manifeste reproductible des versions.

# Corrections par ordre de gravité

1. **Auditer la disponibilité opérationnelle et l’appariement émission–validité–run–observation** — **0,5 à 1,5 jour** pour l’audit ciblé et les tests ; davantage si les données doivent être reconstruites.
2. **Corriger le mélange de populations dans les distances spatiales (813 stations contre 270 O₃) et régénérer toutes les pages dépendantes** — **2 à 4 heures**.
3. **Refaire sélection de variables et hyperparamètres dans une validation spatiale imbriquée, avec plusieurs partitions et rayon fixé a priori** — **1 à 2 jours de développement**, plus le temps de calcul.
4. **Recalculer les formes log/racine avec rétro-transformation apprise uniquement dans le pli train et retirer l’attribution “4 %”** — **0,5 à 1 jour**, plus calcul.
5. **Remplacer le chiffre réglementaire central à 120 par un couple explicite 120 valeur-cible / 180 procédure, avec les 32 cas visibles** — **2 à 3 heures**.
6. **Séparer marge d’utilité, intervalle de confiance et sélection multiple dans le critère de rétention** — **0,5 à 1 jour** pour la spécification et les tests, hors nouvelle campagne imbriquée.
7. **Ajouter le registre exécutable des métriques et les tests de grain, seuil, DST et agrégation** — **0,5 à 1 jour**.
8. **Réviser les formulations réglementaires : `≥ 75 %`, mesure ou modélisation de fond, durées des seuils, J+2/J+3 comme extension** — **1 à 2 heures**.
9. **Archiver provenance/hash de l’extraction ATMO et reformuler 99,926 % et 87,8 % comme résultats d’échantillon** — **2 à 4 heures**, si l’extraction est encore reproductible.
10. **Faire une sensibilité des IC au rééchantillonnage station, jour/épisode et partition spatiale** — **0,5 à 1 jour**, plus calcul.
