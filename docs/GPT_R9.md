# R9 — Audit adverse du 2 août 2026

## 1. La typologie de station vaut-elle vraiment +16,5 % ?

### Verdict

Le gain est **plausible pour le NO₂**, mais il ne démontre pas encore la performance « là où rien ne mesure ». La typologie trafic/fond/industriel décrit précisément la proximité d'une source dominante ; l'EEA définit notamment une station trafic par sa proximité avec une route majeure et une station industrielle par sa proximité avec une source industrielle. Une forte correction du défaut de représentativité d'une maille de 0,1° est donc cohérente avec le sens de la variable ([EEA, classification des stations, consulté en 2026](https://www.eea.europa.eu/en/topics/in-depth/air-pollution/monitoring-station-classifications-and-criteria/)). **Jugement :** +16,5 % n'est pas aberrant ; il est trop grand pour être accepté sans réplication.

### Ce qui fuit — ou change la question

1. **Pas de fuite de cible directe démontrée.** La classe est une métadonnée déclarée séparément des concentrations. En revanche, elle encode le *plan de surveillance* : une station est implantée et classée trafic parce qu'elle vise cette influence. Elle est disponible pour une **nouvelle station déjà conçue et classée**, pas pour un pixel arbitraire sans station. L'usage démontré est donc « station non vue à l'apprentissage dont on connaît la classe », non « endroit où rien ne mesure ».
2. Les identifiants triés ne doivent pas être traités comme aléatoires. Le droit européen exige un code national de station et une classification par source dominante ; il ne garantit aucune randomisation de ces codes (décision 2011/850/UE, annexe II, données D, champs 4 et 22 : [EUR-Lex](https://eur-lex.europa.eu/legal-content/FR/ALL/?uri=CELEX:32011D0850)). **À vérifier sur le panel :** tableau croisé `pli × type × zone × AASQA`, cartes des plis et distances au voisin le plus proche. Plusieurs permutations de `GroupKFold`, puis un découpage par région/AASQA, sont nécessaires.
3. Le +16,5 % et le +12,9 % ont été produits avec XGBoost dans [`apport_tropomi.py`](../scripts/apport_tropomi.py), alors que la production annoncée est LightGBM. Le code traduit `min_child_samples` en `min_child_weight`, abandonne `num_leaves` et fixe `max_depth=10`; [`optuna_mos.py`](../scripts/optuna_mos.py) reconnaît explicitement que ce XGBoost n'a jamais été réglé. La comparaison paire reste informative **pour ce XGBoost**, mais le chiffre n'est pas encore celui du modèle de production.
4. Un bootstrap de stations tient compte de la répétition des jours dans une station, mais pas des chocs calendaires communs à toutes les stations. Les 400 tirages donnent en outre seulement une dizaine de réalisations dans chaque queue à 2,5 %. **Jugement :** refaire avec au moins 2 000–5 000 tirages et un bootstrap à deux voies station × blocs de dates ; l'inférence multiway est motivée par Cameron, Gelbach & Miller (2011), *JBES*, [DOI 10.1198/jbes.2010.07136](https://doi.org/10.1198/jbes.2010.07136).

La nullité sur O₃ et PM₂.₅ est un **contrôle négatif utile mais faible** : elle écarte une amélioration universelle due à quatre colonnes supplémentaires, sans confirmer à elle seule le mécanisme NO₂. La confirmation forte serait une permutation de la typologie **à l'intérieur des blocs spatiaux**, une réplication sur plusieurs partitions, puis une analyse trafic–fond au sein d'une même maille CAMS. L'explication actuelle reste en partie post hoc.

## 2. 3 288 arbres : sous-ajustement ou protocole trompeur ?

### Verdict

Une baisse monotone jusqu'à 3 288 arbres à `learning_rate=0.05` n'est pas en soi anormale : avec shrinkage, fortes contraintes de feuille et 57 prédicteurs, le retournement peut survenir après la borne explorée ou ne pas être visible sur ce partage. En revanche, « sous-ajusté d'un facteur huit » est faux : 3 288/400 est un rapport de nombres d'arbres, pas un facteur de sous-ajustement ni de capacité. La formulation défendable est : **« le budget de 400 arbres est sous-optimal de 0,561 RMSE et 4,68 points de gain sur cette partition »**.

### Les trois défauts décisifs

1. Le test de 90 stations n'est plus « jamais consulté » : il a servi à constater la monotonie et à préférer 3 288 à 400. Il est désormais un **jeu de validation**. Toute mesure finale doit employer un nouveau test gelé, ou une validation externe temporelle/spatiale. Réutiliser un test pour choisir un modèle produit le biais de sélection décrit par Cawley & Talbot (2010), *JMLR* 11, [article](https://www.jmlr.org/papers/v11/cawley10a.html).
2. Une seule partition ne permet pas d'établir la monotonie comme propriété générale. Il n'existe pas un nombre magique de partitions : faire au minimum 10–20 répétitions groupées donne une distribution, mais la précision doit être décidée par l'IC de la différence appariée. La partition finale, elle, ne doit être lue qu'une fois. Une validation imbriquée est nécessaire dès que le score de validation choisit le modèle (Varma & Simon, 2006, *BMC Bioinformatics*, [DOI 10.1186/1471-2105-7-91](https://doi.org/10.1186/1471-2105-7-91)).
3. L'arrêt anticipé sur un groupe de stations interne à chaque pli est raisonnable pour la généralisation spatiale, mais pas suffisant pour « demain » : il voit les mêmes dates que l'ajustement. Il faut, dans chaque pli externe, réserver une origine temporelle future **et** des stations, ou séparer les quatre cases `station vue/non vue × date passée/future`.

L'arrêt anticipé ne « supprime » pas le couplage `learning_rate × n_estimators`; il choisit conditionnellement le second. Une borne à 4 000 peut censurer les petits pas d'apprentissage : il faut rapporter la part des essais qui touchent cette borne. Enfin, [`shap_familles.py`](../scripts/shap_familles.py) prétend expliquer le modèle à déployer mais fixe **2 000 arbres**, ni 400 ni 3 288 : l'explication ne correspond à aucun des deux modèles comparés.

## 3. Validation spatiale et PM₂.₅ à −9,04 %

### Verdict

Le −9,04 % est un **résultat de stress test interprétable**, mais la décomposition « famine 21,2 points + fuite 16,3 points » n'est pas identifiée causalement. Elle dépend d'un seul chemin et d'un seul retrait aléatoire. La littérature recommande d'adapter le blocage à la dépendance et à la tâche de prédiction, non de considérer automatiquement le plus grand fossé comme vérité universelle (Roberts et al., 2017, *Ecography*, [DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)).

### Erreurs de qualification trouvées dans le code

1. **« 333 stations écartées » est impossible comme nombre distinct** sur un réseau de 227 stations. [`validation_bloquee.py`](../scripts/validation_bloquee.py) additionne les exclusions des trois plis dans `exclus_total`; une même station peut être comptée dans plusieurs entraînements. Le témoin emploie ensuite la moyenne, soit environ 111 exclusions par pli. Le rapport doit donner, pour chaque pli, `n_train`, `n_test`, `n_buffer`, leur union distincte et la distribution des distances.
2. Le rayon n'est pas la « portée du variogramme ». [`portee_residus.py`](../scripts/portee_residus.py) calcule un **corrélogramme binned** de résidus, puis retient la première tranche dont la corrélation moyenne passe sous un seuil arbitraire de 0,10. La valeur 150 km est la borne d'une tranche, pas une portée estimée avec incertitude.
3. Ce rayon n'est pas indépendant du corpus final : le docstring indique que 25 puis 50 km avaient déjà été essayés après lecture des scores, et le corrélogramme est estimé sur les mêmes résultats hors pli. Il peut servir à concevoir une prochaine étude, pas à rendre celle-ci « a priori » rétroactivement.
4. Le retrait aléatoire a le même **effectif**, pas le même support spatial, les mêmes typologies, régions, distances au test ou covariables. Son écart avec le fossé mélange perte de volume, extrapolation géographique, covariate shift et composition régionale. Il n'est répété qu'une fois par pli.

Publier le −9,04 % comme : **« dans un scénario extrême sans station d'apprentissage à moins de 150 km, sur les plis où il reste N stations, la correction devient inférieure à CAMS »**. Ne pas le présenter comme la performance générale à une station nouvelle. Pour décomposer : répéter des retraits appariés par région, typologie et covariables, construire une courbe d'apprentissage à géométrie contrôlée, et donner la distribution sur plusieurs réalisations. Même alors, les composantes seront descriptives et dépendantes de l'ordre, pas additives au sens causal.

## 4. TROPOMI : signal absent ou variables mal posées ?

### Verdict

Le résultat nul est crédible, mais le test n'est pas encore propre : le filtre qualité NO₂ est trop permissif, la climatologie est transductive, et la prémisse « CAMS assimile ces mêmes observations » confond CAMS global et CAMS régional.

1. **Filtre QA : le code doit être corrigé avant toute conclusion.** Le Readme officiel NO₂ v02.05.00 recommande `qa_value > 0.75` pour la colonne troposphérique et précise que ce filtre retire notamment nuages, neige/glace et récupérations problématiques ([S5P-MPC-KNMI-PRF-NO2, issue 2.4, 16 mars 2023, p. 7](https://sentinels.copernicus.eu/documents/247904/3541451/Sentinel-5P-Nitrogen-Dioxide-Level-2-Product-Readme-File)). Dans le COG quantifié, 73–74 correspond vraisemblablement à 0,73–0,74 — **à vérifier dans la spécification du COG** — et doit donc être écarté, même si cela réduit fortement la couverture. [`extraire_tropomi.py`](../scripts/extraire_tropomi.py) applique `QA_MIN=50` à NO₂ **et à l'indice d'aérosols** ; une recommandation propre au produit NO₂ ne peut pas être transférée sans le manuel AER_AI.
2. Une colonne troposphérique ne devient pas une concentration de surface en la divisant simplement par la hauteur de couche limite. Il faut au minimum profil vertical, noyau d'averaging/AMF, pression-température et traitement de la fraction libre-troposphérique. La comparaison publiée CAMS–TROPOMI reconstruit la colonne avec les profils CAMS, ce qui montre le bon sens de l'opérateur d'observation (Douros et al., 2023, *GMD* 16, 509–534, [DOI 10.5194/gmd-16-509-2023](https://doi.org/10.5194/gmd-16-509-2023)). Tester `TROPOMI_column − CAMS_simulated_column` ou leur rapport est plus défendable qu'une division par PBLH.
3. **J−3 peut tuer le signal urbain de NO₂, mais l'ordre de grandeur est inconnu pour ce corpus.** Aucun coefficient universel J−1→J−3 n'est transférable entre saisons et sites. Il faut le mesurer sur les jours où OFFL et NRTI coexistent, avec le même masque QA et les mêmes plis, sans annoncer de valeur de littérature non comparable.
4. CAMS Europe est une médiane de onze modèles régionaux. Ses analyses combinent les modèles et des observations EEA de surface selon les systèmes ; le produit officiel ne dit pas que chaque prévision régionale assimile directement TROPOMI ([CAMS European air-quality forecasts, fiche ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)). Le système **global** assimile des satellites et fournit des conditions aux limites ; Douros et al. indiquent que TROPOMI NO₂ est opérationnel dans le global depuis octobre 2021, tandis que TROPOMI sert aussi à évaluer le régional. Dire « la même observation est déjà assimilée » est donc trop fort.
5. La climatologie de [`apport_tropomi.py`](../scripts/apport_tropomi.py) est calculée station × mois sur **toute la fenêtre évaluée**, y compris des dates futures par rapport à chaque prédiction. Elle ne fuit pas la cible au sol, mais elle viole l'information disponible à la date d'émission et encode le lieu avec des données futures. Il faut une climatologie gelée avant chaque origine ou un archive antérieure fixe.
6. `0,035° ≈ 3,9 km` décrit le pas du raster COG reprojeté, pas une résolution carrée native prouvée. Le produit L2 NO₂ est un pixel de fauchée d'environ **5,5 × 3,5 km** depuis août 2019 ([ESA, IODD Sentinel-5P issue 18.0.0, 1er septembre 2023, p. 192](https://sentinels.copernicus.eu/documents/d/sentinel/s5p-knmi-l2-0009-sd-s5p_level_2_input_output_data_definition-18-0-0-20230901)). Les moyennes de pixels du COG peuvent donc compter des cellules rééchantillonnées comme des observations indépendantes ; il faut documenter la méthode de reprojection et travailler idéalement sur les polygones L2 natifs.

Conclusion provisoire : **« aucune valeur ajoutée opérationnelle démontrée avec OFFL J−3 et ce construit de variables »**, non « TROPOMI ne sert à rien » ni « un réseau convolutif ne trouvera rien ». Les couronnes moyennes ne testent ni texture, ni direction du vent, ni forme de panache ; leur nullité ne falsifie donc pas une architecture spatiale.

## 5. Changement CCQM.O3.2019

### Verdict

La différence de différences calculée n'identifie pas l'effet métrologique. Le +7,32 doit être retiré du récit quantitatif, sauf comme démonstration de l'insuffisance du corpus.

**Publié.** La valeur CCQM.O3.2019 de la section efficace est environ 1,23 % plus basse que la valeur historique, avec une incertitude réduite ; l'impact exact dépend de la valeur et des arrondis implantés dans chaque photomètre ([BIPM, déclaration du 12 avril 2021](https://www.bipm.org/documents/20126/40127429/CCQM%2BO3%2BXS%2BChange%2BInternet%2BStatement%2Bv0.3.pdf/bb64eb4d-e7ad-e242-0ff6-0e5cbbcb7e47), [Rapport BIPM 2024/03, DOI 10.59161/Rapport202403](https://doi.org/10.59161/Rapport202403)). Un effet estimé à +7,32 points sur un mois est donc surtout le signe que le dessin ne résout pas l'effet cherché.

**Audit du protocole.** [`continuite_etalon_o3.py`](../scripts/continuite_etalon_o3.py) prend la médiane de millions de rapports horaires, sans d'abord équilibrer les stations : disponibilité et densité du réseau pondèrent le résultat. Les seuils de 1 000 lignes traitent des heures corrélées comme des réplications. Puis le code soustrait deux changements relatifs de médianes O₃ et NO₂ : ce n'est pas une DiD standard sur un outcome commun. NO₂ n'est pas un contrôle crédible de l'ozone pour les variations interannuelles photochimiques, et il n'existe aucun groupe O₃ non traité contemporain.

Le basculement simultané du **code de validité** ne prouve pas que tous les analyseurs français ont physiquement changé d'étalon à minuit. **À vérifier :** consigne LCSQA/AASQA, dates effectives de raccordement de chaque chaîne, rapports de calibration, éventuels mesurages parallèles et règle de génération du code 4. La première source de vérité est métrologique, pas CAMS.

Sans les onze mois CAMS, on peut encore :

- analyser les observations O₃ continues des mêmes stations avec météo, saisonnalité et ruptures par station, puis comparer les dates estimées aux dates de calibration ;
- utiliser des stations étrangères proches dont le changement documentaire n'a pas eu lieu au même moment comme contrôles, après vérification des métadonnées ;
- récupérer une analyse/réanalyse CAMS homogène uniquement comme covariable de sensibilité, sans la confondre avec les prévisions historiques ;
- surtout, exploiter les certificats et comparaisons d'étalons. Le BIPM donne un ordre de grandeur proche de 1 %, bien inférieur au bruit interannuel visible ici.

La décision « agréger en disant que la continuité n'est pas vérifiée » n'est acceptable qu'avec une **analyse de sensibilité** : indicateur pré/post, modèles séparés, scores de chaque période et exclusion de la période postérieure si le résultat change matériellement.

## 6. Plan Optuna

### Verdict

L'architecture imbriquée est bonne dans son principe, mais le plan actuel possède quatre défauts : test déjà consulté, contrainte de queue non utilisée par le sampler, SQLite déconseillé avec six processus et objectif spatial non aligné avec l'usage spatio-temporel.

1. **Contrainte de queue.** Post-sélectionner le minimum moyen parmi les essais admissibles résout bien le problème mathématique `min RMSE sous contrainte queue`, mais ce n'est pas équivalent à une recherche multi-objectif : TPE et l'élagage ne savent pas quels essais sont infaisables et peuvent concentrer le budget dans la mauvaise zone. Optuna 4.9 expose `TPESampler(constraints_func=...)`; une valeur positive marque une violation, et `constant_liar=True` est recommandé en distribué ([documentation TPESampler 4.9](https://optuna.readthedocs.io/en/stable/reference/samplers/generated/optuna.samplers.TPESampler.html)). Garder un objectif unique contraint permet de conserver l'élagage, lequel n'est actuellement prévu que pour le mono-objectif ([Optuna, pruners](https://optuna.readthedocs.io/en/stable/reference/pruners.html)).
2. **Spatial contre temporel.** Il faut rapporter les quatre cases : station vue/date passée, station exclue/date passée, station vue/futur, station exclue/futur. L'usage revendiqué correspond à la quatrième. Faire plusieurs origines glissantes de 3–6 mois croisées avec plusieurs blocs spatiaux, avec entraînement uniquement antérieur et fossé uniquement autour du bloc test. L'étude ozone 2026 de Jalilian et al. illustre précisément des blocs spatiaux avec buffer croisés avec des fenêtres temporelles, *Environmetrics*, [DOI 10.1002/env.70076](https://doi.org/10.1002/env.70076). Si l'échantillon devient petit, c'est une limite de l'estimand à déclarer, pas une raison de revenir à une question plus facile.
3. **Six TPE.** La perte de qualité par rapport au séquentiel est **inconnue** : elle dépend de la durée des essais et de la redondance des suggestions. Optuna recommande `constant_liar=True` pour éviter les configurations voisines. Plus grave, sa FAQ dit explicitement ne jamais recommander SQLite pour l'optimisation parallèle et propose `JournalStorage`, PostgreSQL ou MySQL ([Optuna FAQ 4.9](https://optuna.readthedocs.io/en/stable/faq.html#how-can-i-solve-the-error-that-occurs-when-performing-parallel-optimization-with-sqlite3)). Augmenter le timeout ne corrige pas les limites de concurrence ni `SELECT … FOR UPDATE` absent.
4. **Seuil 2 %.** Une demi-largeur d'IC n'est ni un effet minimal utile ni un contrôle du risque de faux positif. Le bootstrap de stations sous-estime potentiellement l'incertitude temporelle commune et le criblage répété de nombreux leviers crée de la multiplicité. Fixer le seuil à partir du coût opérationnel/épisode manqué, puis évaluer la différence appariée avec bootstrap station × bloc temporel et jeu confirmatoire gelé. Sinon, appeler 2 % une **heuristique de criblage**, pas une preuve statistique.

Enfin, `learning_rate` reste couplé au nombre d'arbres, et [`optuna_mos.py`](../scripts/optuna_mos.py) peut réexécuter `_rapport` après extension de l'étude : chaque nouveau regard sur les 90 stations transforme davantage le test en validation.

## 7. Target encoding et SHAP

### Target encoding — quatre réponses

1. **`station_id` :** correct pour un vrai site sans historique ; son encodage cible n'existe pas au déploiement. Il peut être licite dans un second produit destiné aux stations déjà instrumentées, avec estimation hors pli et shrinkage, mais ce n'est plus le même usage.
2. **Retards :** ce ne sont pas du target encoding ; ce sont des prédicteurs autorégressifs. Ils sont honnêtes seulement s'ils sont strictement disponibles à l'émission. Surtout, observation J−2 et erreur récente sont impossibles « là où rien ne mesure ». Le +8,9 % appartient à la route **station instrumentée mais exclue de l'apprentissage**, pas à la route **lieu non instrumenté**. C'est la contradiction de cadrage la plus importante du dossier.
3. **Quinze catégories :** l'arbre peut apprendre des moyennes et interactions, mais l'effectif effectif est plus proche de 343 stations que de 130 000 lignes indépendantes. Un encodage lissé peut encore aider les combinaisons rares. Son gain est **inconnu** avant une estimation imbriquée par stations et dates.
4. **Interaction typologie × mois × décile CAMS :** proposition testable, pas a priori supérieure. Les bornes de déciles, moyennes et lissage doivent être appris dans chaque pli interne ; les combinaisons rares et dérivantes sont un risque. L'encodage impose une structure par morceaux que LightGBM peut souvent reconstruire, mais parfois avec davantage de données.

### SHAP — ce que la somme résout et ne résout pas

La somme familiale préserve exactement l'additivité locale. Elle **ne rend pas l'attribution robuste à la corrélation** : paysage, position, typologie et trafic restent substituables entre familles, et la définition marginale/path-dependent de la valeur conditionnelle change le crédit. Les explications peuvent être trompeuses quand les variables dépendent entre elles (Aas, Jullum & Løland, 2021, *Artificial Intelligence* 298, [DOI 10.1016/j.artint.2021.103502](https://doi.org/10.1016/j.artint.2021.103502)). Il faut tester la stabilité par pli, graine et ablation ; pour une vraie coalition, employer GroupShapley/Owen values plutôt que sommer a posteriori (Jullum, Redelmeier & Aas, 2021, [arXiv:2106.12228](https://arxiv.org/abs/2106.12228)).

Deux sorties de [`shap_familles.py`](../scripts/shap_familles.py) sont trompeuses :

- `part_ampleur_pct = mean(|φ_famille|) / Σ mean(|φ|)` est une part **normalisée d'amplitude d'attribution**, pas « x % de la prédiction » : les valeurs absolues ne sont pas additives ;
- concaténer les contributions de trois modèles hors pli mélange des valeurs de base et des distributions d'entraînement différentes. Présenter les résultats par pli puis leur stabilité, non comme un modèle unique.

Pour une AASQA : cascade locale `CAMS → correction → prévision`, familles signées, intervalles/stabilité entre plis, et une ablation de performance en regard. Éviter les pourcentages causaux, le vocabulaire « la forêt produit/réduit l'ozone », et les classements fins de variables corrélées. SHAP explique le modèle, pas l'atmosphère ni la valeur opérationnelle d'une famille.

## 8. Où le projet se raconte encore une histoire

### Les cinq risques à traiter avant tout nouveau levier

1. **Deux produits sont confondus.** Les observations passées rendent le modèle performant pour une station instrumentée ; la typologie rend possible un transfert vers une station classée ; ni l'un ni l'autre ne prouve une carte « là où rien ne mesure ». Il faut deux chaînes, deux jeux de variables et deux scores.
2. **Le modèle annoncé n'est pas le modèle mesuré.** Plusieurs résultats de leviers et la validation bloquée utilisent le XGBoost mal traduit, la production annoncée utilise LightGBM 400 arbres, l'expérience choisit 3 288 et SHAP en explique 2 000. Tant que ces quatre objets ne sont pas unifiés, les gains ne sont ni additionnables ni attribuables au système présenté.
3. **Le test n'est plus un test.** Les 90 stations ont servi au choix du nombre d'arbres ; les mêmes corpus ont servi à choisir rayons, variables, seuil de 2 % et récits. Les IC conditionnelles à une partition ne mesurent pas ce surapprentissage de recherche.
4. **Des mots plus forts que les calculs.** « Variogramme », « portée », « 333 stations », « falsifie un CNN », « CAMS assimile les mêmes observations » et « sous-ajusté d'un facteur huit » ne décrivent pas les opérations réellement codées. De même, une grille CAMS de 0,1° n'est pas une maille carrée fixe de 8 km : la fiche officielle l'arrondit à environ 10 km ([CAMS ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)), et 0,1° de longitude varie avec la latitude.
5. **Les interfaces sont désormais plus suspectes que les algorithmes.** Le taux d'erreur observé pointe vers horaires d'émission, UTC/heure locale et DST, agrégation max 8 h, disponibilité réelle J−2/J−3, unités et versions CAMS, cardinalité des jointures, échantillon commun avant/après ajout d'une variable, version des métadonnées station et divergence entre scripts. Ce sont des hypothèses jointes que les scores globaux ne révèlent pas.

### Audit minimal avant l'entretien

- Geler une cohorte sentinelle de 20–30 station-jours et vérifier manuellement, colonne par colonne, provenance, unité, timestamp source, timestamp de disponibilité et cible.
- Produire une matrice unique `résultat → fichier de prédictions → modèle exact → hash des données → split → variables → commit`, puis interdire tout chiffre sans cette lignée.
- Recalculer les résultats centraux avec **un seul moteur et un seul réglage**, sur plusieurs partitions de développement ; réserver ensuite un vrai bloc spatio-temporel jamais consulté.
- Ajouter des contrôles négatifs : typologie permutée dans les blocs, dates décalées, IDs aléatoires, satellite futur volontairement injecté que le test doit refuser, duplication de jointure que le contrôle doit détecter.
- Séparer explicitement les résultats « station instrumentée » et « lieu sans observation ». Le premier peut employer les retards ; le second ne peut utiliser que CAMS, météo disponible et covariables transportables.

**Conclusion adverse.** La découverte la plus importante de la nuit n'est ni +16,5 % ni 3 288 arbres. C'est que le projet sait désormais détecter des erreurs locales, mais ne possède pas encore un **contrat d'évaluation immuable**. Sans ce contrat, chaque nouvelle correction augmente simultanément le modèle et la probabilité d'avoir adapté le protocole au corpus. La prochaine amélioration rentable est donc un test spatio-temporel gelé et une chaîne unique reproductible, avant Optuna, SHAP ou un nouveau prédicteur.
