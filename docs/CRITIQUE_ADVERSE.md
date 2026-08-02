# CRITIQUE ADVERSE

## Position d’évaluation

Je juge ici le projet décrit dans [`LIVRABLE.md`](../LIVRABLE.md), [`CAMS_BENCHMARK.md`](../reports/CAMS_BENCHMARK.md), [`MOS.md`](../reports/MOS.md), [`INDICE_BOUT_EN_BOUT.md`](../reports/INDICE_BOUT_EN_BOUT.md), [`INDICE_ATMO.md`](../reports/INDICE_ATMO.md), [`SPATIALISATION.md`](../reports/SPATIALISATION.md) et [`ABLATION.md`](../reports/ABLATION.md). Je ne présume ni les outils internes d’Atmo Occitanie ni leur configuration : **à vérifier**.

## 1. Affirmations contestables, par gravité décroissante

### 1.1 Le projet appelle « épisodes » des franchissements de classes ATMO

**Contestation.** Le tableau présenté comme « détection des épisodes » classe des jours-station selon une classe d’indice reconstruite. Or un épisode réglementaire est défini par le dépassement ou le risque de dépassement d’un seuil d’information ou d’alerte, sous des critères de superficie ou de population. L’indice ATMO est, lui, un outil synthétique de communication à l’échelle d’une zone. Une classe « Mauvais » n’est donc pas un épisode au sens juridique. Sources : arrêté du 7 avril 2016, [articles 1 et 2](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31) ; arrêté du 10 juillet 2020, [article 1](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042164835/2026-07-21) ; résultats du projet, [`INDICE_BOUT_EN_BOUT.md`](../reports/INDICE_BOUT_EN_BOUT.md).

**Pourquoi c’est grave.** Le projet transforme une métrique de communication en métrique de déclenchement préfectoral, puis affirme qu’elle est « l’unité qui engage une AASQA ». Cette phrase attribue au résultat une portée opérationnelle qu’il n’a pas démontrée. Le propre rapport précise pourtant que l’indice est calculé en station, sur trois polluants, et non sur le champ officiel à cinq polluants. Source : [`INDICE_BOUT_EN_BOUT.md`](../reports/INDICE_BOUT_EN_BOUT.md).

**Ce qui me ferait changer d’avis.** Une table montrant que chaque cas positif correspond aux seuils, durées, surfaces ou populations de l’arrêté du 7 avril 2016, et que la cible est la procédure préfectorale observée ou reconstituée, pas une classe ATMO.

### 1.2 La « double validation aveugle » n’est pas traçable dans le code livré

**Contestation.** Le rapport annonce un gain de 13,2 % lorsque stations et mois sont cachés, mais la fonction principale visible `ajuster_par_stations_exclues` ne groupe que par station. Aucun script de validation spatio-temporelle correspondant n’est référencé dans le rapport ; les chiffres temporels et doublement aveugles apparaissent dans la documentation sans artefact de prédiction dédié. Sources : [`src/aq/models/mos.py`](../src/aq/models/mos.py), [`scripts/fit_mos.py`](../scripts/fit_mos.py), [`MOS.md`](../reports/MOS.md).

**Pourquoi c’est grave.** Le chiffre le plus crédible de la présentation est aussi le moins reproductible à partir des éléments explicitement reliés. En outre, une validation « mois jamais vu » sur seulement janvier, juillet et décembre 2024 teste trois mois isolés, pas un déploiement prospectif continu ni la dérive interannuelle. Le rapport reconnaît que le calendrier porte 15,2 % du gain et identifie presque le mois. Source : [`ABLATION.md`](../reports/ABLATION.md).

**Ce qui me ferait changer d’avis.** Un artefact versionné contenant, pour chaque pli, les stations et périodes d’apprentissage, de réglage et de test, les hyperparamètres sélectionnés sans accès au test, ainsi que les prédictions hors échantillon permettant de recalculer exactement le gain annoncé.

### 1.3 « L’erreur vient du modèle et non de la météo » ne découle pas d’un RMSE presque plat

**Contestation.** Le faible accroissement du RMSE de J+1 à J+3 montre que l’erreur totale varie peu sur cet intervalle ; il ne permet pas d’attribuer cette erreur aux émissions, à la maille ou aux paramétrisations en excluant la météorologie. Les prévisions de qualité de l’air dépendent explicitement de la météorologie, des émissions et des conditions aux limites ; des erreurs corrélées entre horizons peuvent rester presque constantes. Sources : PREV’AIR, [données d’entrée et prévisions](https://www.prevair.org/le-systeme-prevair/la-production/previsions) ; Menut et al., [CHIMERE v2023r1, 2024](https://doi.org/10.5194/gmd-17-5431-2024) ; affirmation du projet, [`CAMS_BENCHMARK.md`](../reports/CAMS_BENCHMARK.md).

**Pourquoi c’est grave.** Cette inférence sert de justification physique centrale au MOS et à la phrase « une erreur chaotique se serait effondrée à J+3 ». Le jeu ne comporte pas de décomposition d’erreur par forçage ni d’ensemble perturbé permettant cette attribution. Source : [`LIVRABLE.md`](../LIVRABLE.md).

**Ce qui me ferait changer d’avis.** Une expérience de sensibilité ou une décomposition publiée séparant erreurs météorologiques, émissions, conditions aux limites et paramétrisations, avec stabilité du résultat sur plusieurs saisons et années.

### 1.4 Le benchmark ne compare pas la correction à la chaîne que nous utilisons

**Contestation.** Le projet corrige l’ensemble CAMS Europe à 0,1° puis le présente comme une preuve de valeur pour Atmo Occitanie. Il reconnaît lui-même que CAMS n’est ni PREV’AIR ni « le système d’ATMO ». PREV’AIR exécute CHIMERE et MOCAGE, produit des prévisions jusqu’à J+5 et applique déjà une correction statistique par apprentissage aux prévisions brutes avant krigeage. Sources : [`INDICE_BOUT_EN_BOUT.md`](../reports/INDICE_BOUT_EN_BOUT.md) ; PREV’AIR, [prévisions](https://www.prevair.org/le-systeme-prevair/la-production/previsions) et [prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees).

**Pourquoi c’est grave.** Battre CAMS brut ne démontre ni un gain par rapport au produit de référence PREV’AIR corrigé, ni un gain sur la chaîne régionale réellement expertisée chaque matin. Le projet mesure une preuve de concept sur une entrée accessible, pas une amélioration opérationnelle d’Atmo Occitanie.

**Ce qui me ferait changer d’avis.** Une comparaison sur les mêmes dates, stations, échéances et critères avec les prévisions brutes et corrigées de la chaîne de référence effectivement utilisée par Atmo Occitanie, configuration et version précisées.

### 1.5 Les chiffres d’indice et de rappel reposent sur une cible non officielle

**Contestation.** L’accord de classe de 81,1 %, le rappel de 47,1 % pour « Mauvais » et le nombre de cas manqués utilisent un indice en station construit avec O₃, NO₂ et PM₂.₅. L’indice officiel agrège aussi PM₁₀ et SO₂ sur des zones couvrant l’EPCI. Le rapport l’admet, mais la présentation réemploie ensuite les chiffres comme résultats métier. Sources : arrêté du 10 juillet 2020, [articles 1 à 3 et annexes](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042164835/2026-07-21) ; [`INDICE_BOUT_EN_BOUT.md`](../reports/INDICE_BOUT_EN_BOUT.md).

**Pourquoi c’est grave.** L’absence de PM₁₀ est particulièrement problématique pour la gestion des épisodes, puisque l’arrêté du 7 avril 2016 vise O₃, NO₂ et PM₁₀ selon des seuils propres à chaque polluant. Source : arrêté du 7 avril 2016, [article 1](https://www.legifrance.gouv.fr/loda/article_lc/LEGIARTI000033073037).

**Ce qui me ferait changer d’avis.** La même évaluation sur les cinq polluants et les champs spatialisés, comparée à l’indice officiel et, séparément, aux épisodes réglementaires officiels.

### 1.6 La saisonnalité et les extrêmes sont insuffisamment échantillonnés

**Contestation.** Le MOS est évalué sur trois mois de 2024 ; le projet tire pourtant des conclusions sur la saison, la tenue jusqu’à J+3 et les épisodes. Le seuil de classe 5 ne comporte que 27 cas positifs, dont un seul est détecté après correction. Sources : [`MOS.md`](../reports/MOS.md), [`INDICE_BOUT_EN_BOUT.md`](../reports/INDICE_BOUT_EN_BOUT.md).

**Pourquoi c’est grave.** Le gain global est dominé par les régimes fréquents, tandis que la prétention opérationnelle porte sur une queue de distribution très rare. Le rapport reconnaît que le calendrier domine l’ablation et qu’une année complète est prioritaire. Source : [`ABLATION.md`](../reports/ABLATION.md).

**Ce qui me ferait changer d’avis.** Plusieurs années de prévisions archivées couvrant canicules, épisodes de poussières, hivers contrastés et changements de version, avec intervalles de confiance par seuil et par saison.

### 1.7 « La spatialisation explique le biais » est démontré trop fortement

**Contestation.** L’IDW utilise les observations de fond du jour pour interpoler un champ ensuite comparé au sous-indice officiel du même jour. Le produit officiel est lui-même issu d’une chaîne combinant mesures et modélisation : les deux objets ne sont donc pas indépendants. L’expérience ne prédit pas un champ futur et ne retire pas successivement une station ou une zone avant évaluation. Sources : [`SPATIALISATION.md`](../reports/SPATIALISATION.md) ; PREV’AIR, [cartes analysées par krigeage avec les stations de fond](https://www.prevair.org/le-systeme-prevair/la-production/analyses).

**Pourquoi c’est grave.** Passer de 42,8 % à plus de 90 % d’accord établit que l’agrégation spatiale rapproche les résultats, mais pas que l’écart initial avait une cause unique ni qu’une LUR prédictive reproduira la chaîne officielle. Le projet mentionne lui-même les sous-indices manquants comme seconde cause. Source : [`INDICE_ATMO.md`](../reports/INDICE_ATMO.md).

**Ce qui me ferait changer d’avis.** Une validation spatiale hors échantillon sur des champs prévus avant l’observation, avec cinq polluants, comparaison au produit officiel et analyse distincte des erreurs de concentration, d’interpolation et d’agrégation.

### 1.8 L’interprétation causale des variables géographiques dépasse la preuve prédictive

**Contestation.** Le relief améliore la prédiction de l’ozone moyen et la forêt dégrade le MOS horaire ; ces résultats sont compatibles avec plusieurs mécanismes corrélés. Ils ne démontrent ni que la stagnation est la cause du gain, ni que CAMS « voit déjà » toute l’information forestière utile. Sources : [`RELIEF.md`](../reports/RELIEF.md), [`ABLATION.md`](../reports/ABLATION.md).

**Pourquoi c’est grave.** L’importance LightGBM et une ablation prédictive ne constituent pas une attribution physico-chimique. Le projet reconnaît d’ailleurs une corrélation de −0,90 entre deux variables de relief, ce qui interdit l’interprétation isolée des coefficients. Source : [`LIVRABLE.md`](../LIVRABLE.md).

**Ce qui me ferait changer d’avis.** Une analyse de sensibilité physiquement contrainte, stable entre régions et saisons, ou une publication externe montrant le même mécanisme avec observations indépendantes.

### 1.9 Le MQI est présenté comme une conformité alors que ses paramètres sont déclarés non sourcés

**Contestation.** Le rapport affirme que « CAMS est formellement conforme » avec des MQI de 0,39 à 0,87, tout en signalant que les paramètres d’incertitude sont repris de mémoire et doivent être vérifiés. Une conclusion de conformité ne peut pas être plus sûre que ses paramètres. Source : [`CAMS_BENCHMARK.md`](../reports/CAMS_BENCHMARK.md).

**Pourquoi c’est grave.** Le mot « conforme » a une portée technique précise et le rapport s’en sert pour cadrer tout le discours. L’évaluation nationale des systèmes de prévision suit un référentiel technique et des rapports annuels sur les produits fournis en temps réel. Source : PREV’AIR, [évaluations](https://www.prevair.org/le-systeme-prevair/la-production/evaluations).

**Ce qui me ferait changer d’avis.** Le calcul reproduit exactement avec le Guidance Document FAIRMODE en vigueur, version et équations citées, puis rapproché du référentiel national applicable au produit évalué.

### 1.10 L’écrêtage des prévisions à zéro crée une asymétrie non discutée

**Contestation.** Le projet conserve les mesures négatives validées pour éviter un biais positif, mais écrête à zéro toutes les prévisions corrigées en affirmant qu’une concentration négative n’existe pas. Les métriques comparent alors une cible instrumentale pouvant être négative à une prédiction contrainte positive. Sources : [`QUALITE_DONNEES.md`](../reports/QUALITE_DONNEES.md), [`src/aq/models/mos.py`](../src/aq/models/mos.py).

**Pourquoi c’est grave.** L’effet est probablement concentré aux faibles niveaux, précisément là où le projet discute la frontière « Bon/Moyen ». Son ampleur n’est pas publiée.

**Ce qui me ferait changer d’avis.** Une quantification montrant que l’écrêtage ne modifie matériellement ni biais, ni RMSE, ni classes, ou une définition de cible cohérente avec le traitement métrologique officiel.

## 2. Endroits où la contribution est surestimée

### 2.1 « Correction apprise » présentée comme contribution nette

PREV’AIR applique déjà une correction statistique par machine learning à O₃, NO₂, PM₁₀ et PM₂.₅, puis spatialise les prévisions corrigées par krigeage jusqu’à J+5. La nouveauté ne peut donc pas être « corriger un CTM par ML ». Source : PREV’AIR, [prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees).

**Ce qui me ferait changer d’avis.** Une différence méthodologique ou opérationnelle précisément nommée, évaluée contre la correction existante et utile à une décision d’Atmo Occitanie.

### 2.2 « Reproduire la chaîne officielle »

L’expérience spatiale ne reproduit qu’O₃, sur 104 jours, par IDW à 2 km, avec 20 stations de fond ; le rapport indique lui-même qu’elle ne couvre ni les cinq polluants ni le modèle officiel. Source : [`SPATIALISATION.md`](../reports/SPATIALISATION.md).

**Ce qui me ferait changer d’avis.** Une chaîne cinq polluants, commune puis EPCI, prévisionnelle, versionnée et comparée aux sorties officielles.

### 2.3 « Tout l’horizon réglementaire »

Le projet mesure J+1 à J+3, tandis que PREV’AIR produit actuellement des prévisions de J−1 à J+5. Dire « tout l’horizon réglementaire » est au minimum ambigu sans article précis. Source : PREV’AIR, [prévisions](https://www.prevair.org/le-systeme-prevair/la-production/previsions) ; [`LIVRABLE.md`](../LIVRABLE.md).

**Ce qui me ferait changer d’avis.** La référence juridique qui limite exactement le besoin testé à J+3.

### 2.4 « L’ozone pilote, donc agir sur l’indice c’est agir sur l’ozone »

Le constat descriptif de 87,8 % porte sur les jours présents dans le flux officiel disponible et sur la règle du maximum des sous-indices. Il ne démontre pas qu’une action sur les précurseurs réduira l’indice de façon monotone, la chimie O₃–NOₓ–COV étant non linéaire. Sources : [`INDICE_ATMO.md`](../reports/INDICE_ATMO.md) ; Menut et al., [CHIMERE v2023r1, 2024](https://doi.org/10.5194/gmd-17-5431-2024).

**Ce qui me ferait changer d’avis.** Une analyse de sensibilité par régime chimique et scénario d’émissions, distincte de la fréquence avec laquelle O₃ est le sous-indice maximal.

## 3. Ce qu’un professionnel trouvera fragile ou trompeur

1. **Des périodes différentes sont juxtaposées comme une seule barre de comparaison.** Les baselines observationnelles portent sur 2023-2024, tandis que le benchmark CAMS et le MOS portent sur trois mois de 2024. Les RMSE ne sont comparables que sur le même échantillon. Sources : [`BASELINES.md`](../reports/BASELINES.md), [`MOS.md`](../reports/MOS.md).

   **Ce qui me ferait changer d’avis.** Une table recalculée sur l’intersection exacte des stations, heures, polluants et horizons.

2. **Les cas ne sont pas des épisodes indépendants.** Des centaines de jours-station peuvent appartenir au même événement régional ; les compter comme autant de « manqués » gonfle l’impression d’effectif. Source : format des prédictions décrit dans [`INDICE_BOUT_EN_BOUT.md`](../reports/INDICE_BOUT_EN_BOUT.md).

   **Ce qui me ferait changer d’avis.** Un décompte par événement réglementaire unique, avec durée, zone et population.

3. **Les intervalles d’incertitude sont absents.** Les gains de quelques points de classe, les 0,7 point entre moyenne et maximum IDW et les sous-groupes rares sont présentés sans variabilité entre plis, jours ou stations. Sources : [`SPATIALISATION.md`](../reports/SPATIALISATION.md), [`MOS.md`](../reports/MOS.md).

   **Ce qui me ferait changer d’avis.** Des distributions par pli ou bootstrap spatio-temporel qui montrent la stabilité du signe et de l’ordre de grandeur.

4. **La sélection et le réglage du modèle sont mêlés à l’histoire expérimentale.** Le même corpus sert à découvrir le piège de la cible directe, choisir le résidu, interpréter les bandes et publier le score final. Source : [`LIVRABLE.md`](../LIVRABLE.md).

   **Ce qui me ferait changer d’avis.** Un jeu final gelé, jamais utilisé dans ces choix.

5. **Le vocabulaire “double aveugle” est impropre.** Il s’agit d’un découpage hors échantillon, pas d’une expérience en aveugle au sens clinique ou expérimental. Source : [`MOS.md`](../reports/MOS.md).

   **Ce qui me ferait changer d’avis.** Une définition méthodologique publiée justifiant ce terme dans ce contexte.

6. **L’exploitabilité temps réel n’est pas démontrée.** Le projet documente les téléchargements et la reprise, mais pas l’heure réelle de disponibilité de chaque entrée, le temps de calcul quotidien, les données manquantes, le changement de version CAMS ni le repli en cas de panne. Sources : [`ACCES.md`](../ACCES.md), [`LIVRABLE.md`](../LIVRABLE.md).

   **Ce qui me ferait changer d’avis.** Un journal d’exécution prospectif sur une période continue montrant que chaque prédiction a été produite avec les données disponibles avant l’échéance.

## 4. Questions d’entretien qui distinguent compréhension et récitation

1. **Quelle est la différence exacte entre une classe ATMO “Mauvais” et un épisode réglementaire ?**  
   Une réponse solide cite le polluant, le seuil, la durée, la superficie ou la population, et le rôle du préfet. Source : arrêté du 7 avril 2016, [articles 1, 2 et 12](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31).  
   **Ce qui me ferait changer d’avis :** le candidat reformule spontanément ses métriques sans confondre communication et procédure.

2. **Montrez-moi où est calculé le score “stations et mois jamais vus”, pli par pli.**  
   **Ce qui me ferait changer d’avis :** il produit immédiatement le code, les partitions et les prédictions, ou reconnaît que le chiffre n’est pas encore reproductible.

3. **Pourquoi un RMSE stable entre J+1 et J+3 exclurait-il une erreur météorologique corrélée ?**  
   **Ce qui me ferait changer d’avis :** il abandonne l’attribution causale ou la soutient par une vraie expérience de sensibilité.

4. **Quelle référence opérationnelle votre modèle doit-il battre : CAMS brut, PREV’AIR brut, PREV’AIR corrigé ou la chaîne régionale expertisée ?**  
   PREV’AIR publie déjà des prévisions corrigées par apprentissage. Source : [PREV’AIR](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees).  
   **Ce qui me ferait changer d’avis :** il nomme une configuration, une version, un produit, une échéance et un usage.

5. **Pourquoi le même mois peut-il être “jamais vu” alors que `jour_annee` encode sa position ?**  
   **Ce qui me ferait changer d’avis :** il explique interpolation saisonnière, extrapolation, proximité des jours et rôle du réglage sans prétendre que l’encodage suffit.

6. **Comment avez-vous empêché les hyperparamètres, variables et seuils d’être choisis sur le jeu final ?**  
   **Ce qui me ferait changer d’avis :** il décrit une séparation apprentissage–validation–test réellement gelée et en montre la trace.

7. **Que représente un “cas manqué” : une heure, un jour-station, un EPCI-jour ou un événement préfectoral ?**  
   **Ce qui me ferait changer d’avis :** il donne le dénominateur exact et cesse de l’appeler épisode s’il ne l’est pas.

8. **Pourquoi la moyenne d’un champ IDW bat-elle le maximum officiel, et pourquoi cela ne valide-t-il pas la moyenne ?**  
   **Ce qui me ferait changer d’avis :** il distingue erreur de champ, opérateur d’agrégation et définition réglementaire, comme le reconnaît [`SPATIALISATION.md`](../reports/SPATIALISATION.md).

9. **Que devient la correction lors d’une mise à jour de CAMS, d’un changement d’inventaire ou d’une station déplacée ?**  
   **Ce qui me ferait changer d’avis :** il quantifie le risque de rupture au lieu de répondre seulement « réentraînement ».

10. **Pourquoi gardez-vous les mesures négatives mais écrêtez-vous les prédictions à zéro ?**  
    **Ce qui me ferait changer d’avis :** il chiffre l’effet de cette asymétrie sur les faibles concentrations et les classes.

11. **Quel résultat est véritablement occitan ?**  
    Le gain hors Occitanie puis testé sur 29 stations occitanes vaut 18,8 % pour O₃ J+1, mais le modèle reste entraîné sur un autre système climatique et sur trois mois. Source : [`ABLATION.md`](../reports/ABLATION.md).  
    **Ce qui me ferait changer d’avis :** il distingue preuve nationale, transfert régional et validation opérationnelle locale.

12. **Qu’est-ce que votre modèle apporte que la correction et le krigeage de PREV’AIR n’apportent pas déjà ?**  
    **Ce qui me ferait changer d’avis :** une réponse mesurée, testable et reliée à une décision d’Atmo Occitanie plutôt qu’à une métrique générique.
