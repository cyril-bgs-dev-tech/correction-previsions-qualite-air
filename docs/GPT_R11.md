# R11 — Les quatre murs mesurés

## Verdict synthétique

- **Mesuré dans le projet** — Avec des stations **et** des mois exclus, les gains NO₂ sont robustes (+27,8 %, puis +36,7 % avec la typologie), tandis que O₃ et PM2.5 restent instables. Ce protocole est plus sévère que les évaluations publiées retrouvées ; leurs pourcentages ne constituent donc pas des seuils de réussite directement comparables.
- **Établi** — La PM2.5 n'est pas systématiquement le polluant le moins corrigeable : deux études européennes rapportent encore 22–37 % de baisse de RMSE, mais sur des stations déjà vues ou avec une séparation spatiale sans bloc temporel conjoint ([Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; [Riccio et Chianese, 2024, DOI 10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024)).
- **Jugement** — Le résultat « les paramètres par défaut gagnent » est crédible sous changement spatio-temporel : il indique que la procédure de réglage optimisait une tâche plus facile que la tâche cible. Il ne prouve pas une loi générale en faveur des paramètres par défaut.
- **Établi** — La typologie de station encode une information physiquement pertinente de représentativité. La décision européenne 2026/1208 formalise désormais des *spatial representativeness areas* (SRA) dépendant du polluant, de la métrique, du type de station, de sa localisation et de ses sources ; elle s'appliquera le 30 juin 2028 ([décision d'exécution (UE) 2026/1208, art. 7 et annexe I](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).
- **Inconnu** — Aucune fraction générale, publiée et transférable à l'Occitanie, des dépassements PM10 attribuables aux poussières sahariennes n'a été trouvée. Un exemple français documenté retire 11 des 38 jours de dépassement observés en 2022 à Marseille-Rabatau, soit 28,9 %, mais il ne doit pas être généralisé ([INERIS/CAMS, 2024, étude de cas France, diapositives 8–15](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/CAMS-8th%20PUW/04.CAMS_28Feb2024_NatDust_FR.pdf)).

## 1. Pourquoi PM2.5 résiste-t-elle ?

### 1.1 Les gains publiés sont-ils réellement plus faibles ?

**Réponse : parfois, mais pas assez systématiquement pour parler d'une propriété générale.** La comparaison la plus honnête est la suivante :

| Étude et protocole | Variable évaluée | RMSE brute → corrigée | Gain | Comparabilité avec le projet |
|---|---:|---:|---:|---|
| Bertrand et al. (2023), CAMS Europe, apprentissage local sur 2018 ou global sur les 3 jours précédents, test 2019 ; mêmes sites accessibles à l'apprentissage | PM2.5 horaire, Europe, premières 24 h (D+0 dans l'article) | 8,6 → 6,7 µg/m³ | 22 % | Station vue ; non comparable au double aveugle |
| Même étude | PM2.5 moyenne journalière, Europe, premières 24 h | 6,6 → 4,2 µg/m³ | 37 % | Station vue |
| Même étude | O₃ horaire, Europe, premières 24 h | 22,6 → 16,0 µg/m³ | 29 % | Station vue |
| Même étude | NO₂ horaire, Europe, premières 24 h | 12,6 → 8,4 µg/m³ | 33 % | Station vue |
| Riccio et Chianese (2024), CAMS Europe, 10 % de stations italiennes exclues, apprentissage global glissant sur les 3 jours précédents, mais séparation temporelle conjointe non indiquée | PM2.5 journalière, Italie, jour suivant | 7,91 → 5,74 µg/m³ | 27,4 % | Spatialement exclu, mois non bloqués |
| Même étude | PM10 journalière, Italie, jour suivant | 12,21 → 7,96 µg/m³ | 34,8 % | Spatialement exclu, mois non bloqués |
| Même étude | O₃ MDA8, Italie, jour suivant | 19,97 → 13,99 µg/m³ | 29,9 % | Spatialement exclu, mois non bloqués |
| Même étude | NO₂ maximum horaire, Italie, jour suivant | 26,59 → 19,02 µg/m³ | 28,5 % | Spatialement exclu, mois non bloqués |

Sources : [Bertrand et al., 2023, *Atmospheric Chemistry and Physics*, sections 2–5 et tableau 2, DOI 10.5194/acp-23-5317-2023](https://acp.copernicus.org/articles/23/5317/2023/acp-23-5317-2023.pdf) ; [Riccio et Chianese, 2024, *Atmospheric Chemistry and Physics*, section 3.2 et tableau 2, DOI 10.5194/acp-24-1673-2024](https://acp.copernicus.org/articles/24/1673/2024/acp-24-1673-2024.pdf).

**Établi** — Ces publications montrent que PM2.5 peut être corrigée substantiellement lorsque le modèle dispose de l'historique du site, ou lorsque seule la station est exclue. **Elles ne montrent pas** le gain attendu sur une station et une période simultanément nouvelles.

**Jugement** — Votre +4,5 %, avec sept plis négatifs et σ = 11,1 points, doit être présenté comme « absence de gain généralisable démontré », pas comme preuve que PM2.5 est intrinsèquement incorrigible. Le passage de 18 à 36 mois qui réduit légèrement la moyenne (+5,14 → +4,47) mais la dispersion (12,2 → 11,1) suggère davantage une amélioration de stabilité qu'une amélioration d'exactitude ; l'écart de 0,67 point est inférieur à votre bruit déclaré de ±2,02 points.

**Rien de probant** n'a été trouvé pour une hiérarchie universelle « PM2.5 plus difficile que O₃ et NO₂ » sous validation station × période exclues.

### 1.2 Le résidu PM2.5 est-il dominé par des sources inobservables ?

**Non démontré.** Il faut distinguer les sources absentes, les sources mal quantifiées et les processus mal représentés :

- **Transport secondaire** — À Paris, une année de source-apportionment attribue plus de la moitié de la masse annuelle PM2.5 aux aérosols secondaires continentaux de moyenne ou longue distance, contre environ un quart aux sources locales. Ce résultat est propre à Paris et à la période étudiée ([Bressi et al., 2014, *Atmospheric Chemistry and Physics*, DOI 10.5194/acp-14-8813-2014](https://doi.org/10.5194/acp-14-8813-2014)).
- **Compensation d'erreurs** — Une évaluation CHIMERE sur l'Europe a montré qu'un biais moyen PM2.5 de +16 % pouvait masquer des compensations entre composantes locales et advectées ; les auteurs identifient notamment les émissions de chauffage au bois et la formation d'aérosol organique secondaire comme sources d'incertitude ([Petetin et al., 2014, *Geoscientific Model Development*, DOI 10.5194/gmd-7-1483-2014](https://doi.org/10.5194/gmd-7-1483-2014)).
- **Chauffage au bois** — En Occitanie, le résidentiel représente 64,4 % des **émissions inventoriées** de PM2.5 et la biomasse 98,8 % des émissions PM2.5 du résidentiel ; ces parts d'émissions ne sont pas des parts de concentration ambiante ([DREAL Occitanie, page publiée le 2 avril 2026, chiffres régionaux](https://www.occitanie.developpement-durable.gouv.fr/chauffage-au-bois-a27232.html)).
- **Remise en suspension** — Elle affecte surtout la fraction grossière et ne peut pas être déclarée dominante dans PM2.5 sans spéciation locale. **À vérifier** pour les sites du projet.

**Jugement** — Une part du résidu est donc difficile à prédire avec des variables statiques, mais elle n'est pas nécessairement « inobservable » : inventaires, composition chimique, champs de transport, humidité, stabilité, observations amont et mémoire récente de la station en portent des signaux partiels.

### 1.3 Variables ayant un effet publié et testables sans achat

| Variable ou construction | Effet publié | Protocole et limite | Test faisable en 48 h |
|---|---|---|---|
| Chauffage au bois modulé par la température | À Temuco, épisodes PM2.5 correctement prévus : 45 % → 71 % tous horizons confondus | CTM 2 km, hiver 2014, J+1 à J+3 ; seuil d'épisode 80 µg/m³ sur 24 h ; Chili, pas MOS français | Multiplier les émissions résidentielles PM2.5 d'Atmo Occitanie par une fonction de demande de chauffage issue de la température prévue |
| Effet week-end sur les émissions | POD d'épisodes : 67→72 % à Santiago, 64→69 % à Rancagua, 57→63 % à Talca et 63→67 % à Chillán | Même étude ; ajustement d'émissions CTM, pas ablation LightGBM | Interaction jour × chauffage × stabilité |
| Hauteur de couche limite, AOD, feux et concentrations récentes | Variables importantes dans des modèles arbres à 24 h sur 19 stations ; **aucun ΔRMSE isolé publié** | Importance/permutation, vallée d'Aburrá ; une importance n'est pas un effet causal | Ablation PBL seule ; ne pas revendiquer de gain avant le test |
| Variables météo élargies, dont PBL | Le jeu élargi ne surpasse généralement pas le jeu compact | CAMS Europe, stations vues, J+1 ; PBL non isolée | Confirme que l'accumulation de variables météo n'est pas automatiquement rentable |

Sources : [Saide et al., 2016, *Journal of Geophysical Research: Atmospheres*, DOI 10.1002/2015JD023949](https://doi.org/10.1002/2015JD023949) ; [Pérez-Carrasquilla et al., 2023, *Advances in Statistical Climatology, Meteorology and Oceanography*, DOI 10.5194/ascmo-9-121-2023](https://doi.org/10.5194/ascmo-9-121-2023) ; [Bertrand et al., 2023, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

Pour un proxy français gratuit, l'inventaire Atmo Occitanie est téléchargeable en données ouvertes, mais ses années disponibles sont antérieures à la prévision ; il faut donc l'utiliser comme **structure spatiale**, puis la moduler par une météo opérationnelle ([Atmo Occitanie, portail open data, consulté le 2 août 2026](https://www.atmo-occitanie.org/actualites/telechargez-les-donnees-de-lair-sur-lopen-data)). Les données logement INSEE à l'IRIS sont également ouvertes, mais la modalité de chauffage regroupe le bois avec d'autres énergies dans certaines tables : ce n'est pas un indicateur bois propre ([INSEE, logement 2021 à l'IRIS, publié en 2024](https://www.insee.fr/fr/statistiques/8268838)).

### 1.4 La couche limite vaut-elle un test isolé ?

**Oui, comme ablation peu coûteuse ; non, comme promesse de gain.** La physique justifie son rôle dans la dilution, et des études la retiennent parmi les variables importantes, mais les sources retrouvées ne fournissent pas un gain marginal reproductible en double aveugle. **Rien de probant** ne permet d'annoncer à l'avance « +x % ».

**Test prioritaire 48 h** — Ajouter seulement `PBLH`, minimum et quantiles des 24–48 h précédentes/prévues, gradient nocturne-diurne et interaction `émissions résidentielles × froid × faible PBLH`, sans changer les plis. Accepter la variable uniquement si la moyenne progresse, si le nombre de plis négatifs baisse et si l'intervalle bootstrap par station exclut zéro. Cette règle est un **jugement méthodologique**, pas une norme publiée.

## 2. Pourquoi les paramètres par défaut gagnent-ils ?

### 2.1 Ce résultat est-il documenté sous validation spatiale ?

**Établi** — Des partitions aléatoires peuvent sous-estimer fortement l'erreur spatiale. Dans une étude écologique comparant validation spatiale et non spatiale, l'optimisme moyen de l'AUROC atteignait 0,167 pour un GAM et 0,213 pour une forêt aléatoire, soit environ 24 % et 30 % relativement aux scores spatiaux ; l'étude montre aussi qu'une cinquantaine d'itérations suffisait à stabiliser le réglage dans **ce jeu précis** ([Schratz et al., 2019, *Ecological Modelling*, DOI 10.1016/j.ecolmodel.2019.06.002](https://doi.org/10.1016/j.ecolmodel.2019.06.002)).

**Établi** — La sélection hyperparamétrique peut elle-même sur-apprendre une estimation de validation finie et bruitée ; l'écart induit peut être du même ordre que les différences annoncées entre algorithmes ([Cawley et Talbot, 2010, *JMLR* 11, 2079–2107](https://www.jmlr.org/papers/v11/cawley10a.html)). Les blocs doivent reproduire le mode d'extrapolation visé, spatial, temporel ou hiérarchique ([Roberts et al., 2017, *Ecography*, DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)).

**Débattu** — La littérature retrouvée ne documente pas une règle « les paramètres LightGBM par défaut gagnent en spatial ». Elle documente plutôt trois mécanismes compatibles avec votre observation : fuite par proximité, critère de sélection trop bruité et capacité excessive pour le déplacement de domaine.

### 2.2 Une régularisation plus forte est-elle théoriquement attendue ?

**Partiellement.** Une borne classique relie l'erreur cible à l'erreur source, à la divergence entre domaines et à la complexité de la classe d'hypothèses ; elle justifie de contrôler simultanément capacité et écart de distribution, mais n'implique pas que chaque augmentation de régularisation améliore chaque problème ([Ben-David et al., 2010, *Machine Learning* 79, DOI 10.1007/s10994-009-5152-4](https://doi.org/10.1007/s10994-009-5152-4)). En classification par groupes, Sagawa et al. obtiennent avec Group DRO, régularisation L2 et arrêt précoce des gains de 10 à 40 points de précision du pire groupe sur plusieurs jeux d'images et de texte ; c'est une preuve d'existence, pas une loi pour LightGBM ni pour la pollution ([Sagawa et al., 2020, ICLR, arXiv:1911.08731](https://arxiv.org/abs/1911.08731)).

**Jugement** — Votre renversement est donc cohérent : le split aléatoire récompense les interactions fines réutilisables dans des voisins spatio-temporels ; le double aveugle récompense une fonction plus lisse et plus transportable. Il faut le formuler comme hypothèse soutenue par l'expérience, non comme explication démontrée.

### 2.3 Protocole de tuning adapté

1. **Geler les plis externes station × mois.** Ils ne servent qu'une fois à l'estimation finale ; aucune décision de paramètre ne doit utiliser leur résultat.
2. **Tuner dans des plis internes construits de la même façon.** Une validation interne aléatoire répondrait à une autre question ([Roberts et al., 2017](https://doi.org/10.1111/ecog.02881)).
3. **Critère principal : moyenne RMSE des plis internes.** Conserver le pire pli comme contrainte ou diagnostic, mais ne pas minimiser naïvement son minimum observé : avec dix plis très dispersés, cet estimateur est particulièrement bruité. Ce choix est un **jugement** fondé sur le risque de surapprentissage du critère décrit par [Cawley et Talbot (2010)](https://www.jmlr.org/papers/v11/cawley10a.html).
4. **Espace de recherche restreint et orienté régularisation.** Tester autour du défaut : profondeur/nombre de feuilles, `min_data_in_leaf`, `feature_fraction`, `bagging_fraction`, L1/L2 et arrêt précoce. Ne pas relancer 200 essais avant qu'un petit pilote n'ait montré un signal reproductible.
5. **Comparer explicitement au défaut.** Ne retenir un réglage que si son gain se répète sur plusieurs partitions internes et dépasse l'incertitude bootstrap externe ; sinon, conserver le défaut comme choix parcimonieux.

**Combien d'essais ?** Il n'existe pas de nombre universel publié. Cinquante était un point de saturation dans l'étude de Schratz et al., mais pas une prescription. Pour ce projet, **20 à 50 essais contraints** constituent une allocation rationnelle de calcul ; c'est une recommandation, pas une valeur réglementaire.

### 2.4 Existe-t-il des contre-exemples où le tuning aide malgré le changement de domaine ?

**Oui.** Un critère intégrant la divergence entre domaines a amélioré la sélection de 7 algorithmes sur 12 sur PACS, 8 sur 12 sur VLCS et 9 sur 12 sur Colored-MNIST, avec des gains allant jusqu'à 5,4 points, tout en dégradant certains autres cas ([Lyu et al., 2023, ICASSP, DOI 10.1109/ICASSP49357.2023.10094659](https://doi.org/10.1109/ICASSP49357.2023.10094659)). Ces résultats sont en classification visuelle : ils montrent que le tuning peut aider **si son critère représente le déplacement cible**, pas qu'il aidera ici.

**Conclusion testable** — Une expérience de 48 h utile est un mini-tuning imbriqué de 20–30 essais autour du défaut, comparé au défaut sur les mêmes plis internes. Un nouveau grand Optuna sur split aléatoire n'apporterait aucune information pertinente à la tâche cible.

## 3. Que cache exactement la typologie de station ?

### 3.1 Relation avec les *spatial representativeness areas*

**Établi** — La typologie européenne distingue le type de zone — urbaine, périurbaine, rurale — et l'influence dominante — trafic, industrielle ou fond ([AEE, *Monitoring station classifications and criteria*, consulté le 2 août 2026](https://www.eea.europa.eu/en/topics/in-depth/air-pollution/monitoring-station-classifications-and-criteria/)). Le guide français de 2017 en fait un référentiel national pour la conception et la classification des stations ([LCSQA, *Guide méthodologique pour la conception, l'implantation et le suivi des stations françaises*, approuvé en février 2017](https://www.lcsqa.org/fr/rapport/2016/imt-ld-ineris/guide-methodologique-stations-francaises-surveillance-qualite-air)).

**Établi, à venir** — La décision (UE) 2026/1208 impose à partir du 30 juin 2028 une détermination plus formelle des SRA. Pour NO₂, une maille appartient à la SRA si la concentration modélisée reste dans une tolérance de ±15 % autour de la station, ou au moins ±2 µg/m³ lorsque cette valeur est plus grande ; le calcul doit notamment considérer type, localisation, sources et métrique du polluant ([décision 2026/1208, art. 7, annexe I, tableau 1](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).

**Interprétation** — Vos quatre colonnes sont un encodage grossier, stable et disponible d'une SRA latente. Le gain NO₂ de +8,9 points est physiquement plausible, car le gradient trafic–fond est fort, mais il ne prouve pas que le modèle a appris une aire de représentativité conforme à la méthode européenne. L'effet nul en validation temporelle est cohérent avec une information surtout spatiale ; l'effet nul sur O₃ et PM2.5 montre qu'elle n'est pas une clé universelle.

### 3.2 Descripteurs géographiques publiés et échelle utile

| Étude LUR | Polluant, protocole | Descripteurs et rayons candidats | Résultat quantifié |
|---|---|---|---|
| Eeftens et al. (2012) | PM2.5 annuelle, 20 zones européennes, environ 20 sites/zone, LOOCV | Trafic : 25, 50, 100, 300, 500, 1 000 m ; occupation/population : 100, 300, 500, 1 000, 5 000 m | R² médian 71 % (35–94 %) ; R² LOOCV en moyenne 8–11 points plus bas ; trafic retenu dans 18/20 modèles PM2.5 |
| Beelen et al. (2013) | NO₂ annuel, 36 zones européennes, 40–80 sites/zone, LOOCV | Intensité de trafic et charge sur routes proches, population/ménages, occupation du sol | R² médian 82 % (55–92 %) ; retirer l'intensité locale de trafic réduit le R² d'environ 10 points dans les zones concernées |

Sources : [Eeftens et al., 2012, *Environmental Science & Technology*, DOI 10.1021/es301948k](https://doi.org/10.1021/es301948k) ; [Beelen et al., 2013, *Atmospheric Environment*, DOI 10.1016/j.atmosenv.2013.02.037](https://doi.org/10.1016/j.atmosenv.2013.02.037).

**Limite décisive** — Ces chiffres concernent des moyennes annuelles LUR et une LOOCV de stations, pas des erreurs de prévision J+1 sous mois cachés. Ils justifient les familles et les échelles à tester, pas un gain attendu de RMSE.

**Ce qui est probant** — La charge de trafic à petite échelle et la densité de population/ménages sont les variables les plus récurrentes et les mieux quantifiées pour NO₂. **Rien de probant** n'a été trouvé, dans un protocole comparable au vôtre, pour un rayon universel de hauteur bâtie, de canyon urbain ou de *sky-view factor*.

### 3.3 Données gratuites directement exploitables en France

- **BD TOPO** — Routes hiérarchisées, bâtiments et autres objets vectoriels, précision métrique, mise à jour trimestrielle, Licence Ouverte 2.0 ([IGN/data.gouv.fr, fiche BD TOPO](https://www.data.gouv.fr/datasets/bd-topo-r)). À agréger aux rayons LUR publiés plutôt qu'à un rayon unique choisi après inspection du test.
- **OCS GE** — Couverture et usage des sols à grande échelle, deux millésimes nationaux achevés en octobre 2025, mise à jour prévue tous les trois ans ([IGN, OCS GE](https://www.ign.fr/institut/occupation-du-sol-francais)). La résolution/unité minimale exacte du millésime téléchargé doit être vérifiée dans sa documentation locale.
- **CORINE Land Cover 2018** — Raster de 100 m et vecteur, mais unité minimale de cartographie de 25 ha et largeur minimale de 100 m : adapté au contexte régional, trop grossier pour distinguer une station trafic d'une station de fond à 400 m ([Copernicus Land Monitoring Service, CLC 2018, DOI raster 10.2909/960998c1-1870-4e82-8051-6485205ebbac](https://land.copernicus.eu/en/products/corine-land-cover/clc2018?tab=metadata%2A)).
- **Copernicus Urban Atlas 2021** — Vecteur limité aux 790 aires urbaines fonctionnelles de plus de 50 000 habitants ; unité minimale de 0,25 ha pour 19 classes urbaines et de 1 ha pour 9 classes rurales ([CLMS, Urban Atlas](https://land.copernicus.eu/en/products/urban-atlas?tab=land_coverland_use)). Il est plus fin que CORINE, mais ne couvre pas uniformément les stations rurales isolées.
- **GHSL** — `GHS-BUILT-S` fournit la surface bâtie à 100 m et 1 km sur la série 1975–2030, plus une couche observée à 10 m pour 2018 ; `GHS-BUILT-H` fournit la hauteur bâtie 2018 à 100 m ([JRC, GHS-BUILT-S R2023A, DOI 10.2905/9F06F36F-4B11-47EC-ABB0-4F8B7B1D72EA](https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php) ; [JRC, GHS-BUILT-H R2023A](https://human-settlement.emergency.copernicus.eu/ghs_buH2023.php)). Ce sont des descripteurs bâtis cohérents nationalement, pas une mesure de canyon ou de facteur de vue du ciel.
- **OpenStreetMap** — Objets vectoriels sans résolution nominale unique, sous licence ODbL avec attribution et partage à l'identique des bases dérivées concernées ([OpenStreetMap Foundation, licence](https://www.openstreetmap.org/copyright)). Couverture et attributs varient selon les contributeurs ; pour un test français reproductible, BD TOPO est la source routière prioritaire, OSM une analyse de sensibilité.
- **INSEE Filosofi carroyé** — 34 variables au carreau de 200 m ([INSEE, données carroyées Filosofi 2021](https://www.insee.fr/fr/statistiques/7655475?sommaire=7655515)). Une forte part des carreaux est imputée pour secret statistique ; il faut conserver l'indicateur d'imputation et éviter une fausse précision locale ([INSEE, documentation Filosofi 2021](https://www.insee.fr/fr/statistiques/fichier/8735106/documentation_donnees-carroyees_filosofi2021.pdf)).
- **Métadonnées EEA/Geod'air** — Type et zone de station, distance à la voie, hauteur de prélèvement et autres métadonnées selon disponibilité ([AEE, téléchargement des métadonnées de stations](https://www.eea.europa.eu/en/datahub/datahubitem-view/778ef9f5-6293-4846-badd-56a29c70880d?activeAccordion=1087599) ; [Geod'air, API avec inscription](https://www.geodair.fr/donnees/api)). Les champs manquants doivent être audités avant usage.

Les produits CLMS, dont CORINE et Urban Atlas, sont disponibles gratuitement en accès complet et ouvert sous réserve d'attribution de la source ([Copernicus Land Monitoring Service, politique de données](https://land.copernicus.eu/en/data-policy)).

### 3.4 Test à plus fort rendement

**Jugement** — Pour NO₂, le meilleur test de 48 h n'est pas d'ajouter des dizaines de couches : construire trois familles interprétables aux rayons publiés — charge de trafic 25–1 000 m, population/bâti 100–5 000 m, puis interactions avec la typologie — et sélectionner les rayons uniquement dans les plis internes groupés. Le gain de +8,9 points fixe déjà une baseline forte ; toute variable géographique doit démontrer un gain **au-delà** de cette typologie et non la remplacer silencieusement.

## 4. PM10, poussières sahariennes et signal précoce

### 4.1 Quelle part des dépassements méditerranéens est attribuable aux poussières ?

**Inconnu à l'échelle demandée.** Aucune estimation publiée, pluriannuelle et transférable à l'ensemble de l'Occitanie ou de la façade méditerranéenne française n'a été retrouvée.

**Exemple documenté, non généralisable** — À Marseille-Rabatau en 2022, 38 jours dépassaient 50 µg/m³ de PM10 avant déduction et 27 après déduction de la contribution naturelle : 11 jours, soit 28,9 % des jours initialement en dépassement, ont donc été retirés ([INERIS/CAMS, 2024, diapositives 8–15](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/CAMS-8th%20PUW/04.CAMS_28Feb2024_NatDust_FR.pdf)). Ce chiffre est station-, année- et méthode-dépendant.

**Oui, la déduction est appliquée en France.** L'étude de cas ci-dessus montre son application au rapportage français ; elle ne signifie pas qu'une AASQA retire automatiquement chaque journée identifiée comme saharienne.

### 4.2 Méthode de déduction au titre de l'article 20

**Établi réglementairement** — L'article 20 permet de ne pas compter les dépassements imputables à des sources naturelles si l'État fournit à la Commission les informations nécessaires et la preuve de l'origine naturelle ([directive 2008/50/CE, art. 20](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32008L0050)). La méthode européenne de 2011 détaille la chaîne suivante :

1. identifier les jours de transport désertique par convergence de trajectoires, modèles de poussières, satellite et, si possible, spéciation ;
2. déterminer une concentration de fond sans poussière à une station rurale régionale, par une statistique glissante après exclusion des jours affectés ;
3. estimer la contribution naturelle comme la différence entre PM10 mesurée au fond régional et ce fond sans poussière ;
4. soustraire cette contribution aux stations affectées et documenter chaque jour, chaque site, la méthode et les preuves.

Source : [Commission européenne, 2011, *Guidelines for demonstration and subtraction of exceedances attributable to natural sources*, SEC(2011) 208 final, sections 3.1–3.5](https://www.lcsqa.org/system/files/media/documents/ue_eval_sources_naturelles_2011.pdf). La présentation française de 2023 décrit opérationnellement l'identification par réanalyse CAMS, le fond régional par médiane glissante et la soustraction ([France/FAIRMODE, 2023](https://knowledge4policy.ec.europa.eu/sites/default/files/fairmode/events/20231004_WG8_France.pdf)).

**Prudence** — Cette procédure est une attribution a posteriori ; ce n'est pas une règle de prévision d'épisode ni un seuil automatique PM10/PM2.5. Aucun seuil universel du ratio PM10/PM2.5 n'est prescrit par ces textes.

### 4.3 CAMS capture-t-il correctement les événements ?

**Établi** — Le produit régional CAMS Europe fournit à 0,1° des prévisions horaires, dont la poussière minérale et les fractions PM ; les échéances 0–48 h sont annoncées vers 06:45 UTC et 49–96 h vers 08:30 UTC ([CAMS, fiche du jeu de données européen, consultée le 2 août 2026](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)). La poussière a été intégrée aux fractions PM régionales à partir de 2019 ([documentation CAMS Europe](https://confluence.ecmwf.int/spaces/CKB/pages/202173092/CAMS%2BRegional%2BEuropean%2Bair%2Bquality%2Banalysis%2Band%2Bforecast%2Bdata%2Bdocumentation)).

**Établi mais limité** — Dans l'exercice français 2022, la réanalyse régionale CAMS était jugée plus adaptée que la globale pour identifier les jours de poussières sur la France continentale. Cette conclusion porte sur une **réanalyse** et une procédure d'attribution, pas sur la RMSE d'une prévision disponible à 03 h ([INERIS/CAMS, 2024](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/CAMS-8th%20PUW/04.CAMS_28Feb2024_NatDust_FR.pdf)).

**Rien de probant** n'a été trouvé pour quantifier, en France, le biais propre aux prévisions CAMS de poussières sahariennes à J+1, avec score de détection du panache et erreur d'amplitude au sol publiés séparément.

**Incertitude publiée** — Lors d'un épisode saharien extrême en Europe occidentale, le maximum PM10 de l'ensemble régional était proche de 650 µg/m³ tandis que certains membres approchaient 2 000 µg/m³ : l'accord sur le panache ne garantit donc pas son amplitude de surface ([CAMS, analyse de l'épisode de mars 2022](https://atmosphere.copernicus.eu/historical-saharan-dust-episode-western-europe-cams-predictions-accurate)).

**Conclusion** — CAMS est une source pertinente pour la trajectoire et le timing à grande échelle, mais l'impact au sol demeure membre-, site- et météorologie-dépendant. Si la variable CAMS locale ne contient aucun signal de panache, un correcteur supervisé purement local ne peut pas l'inventer de façon fiable ; il faut lui apporter un signal global, amont ou observé. Cette dernière phrase est une **inférence**.

### 4.4 Sources utilisables gratuitement à 03 h pour une prévision J+1

| Source | Disponibilité réellement documentée | Usage possible à 03 h | Limite |
|---|---|---|---|
| CAMS Europe, cycle régional précédent | Prévisions 0–48 h vers 06:45 UTC, puis 49–96 h vers 08:30 UTC | Oui : à 03 h, utiliser le cycle diffusé la veille et son échéance J+1 | Le cycle du jour n'est pas encore disponible |
| CAMS global | Cycles 00 et 12 UTC, poussières/AOD par classes de taille | **À vérifier** : le catalogue ne garantit pas une livraison avant 03 h | Résolution plus grossière, impact au sol incertain |
| Barcelona Dust Forecast Center | Cartes 0,1°, toutes les 3 h jusqu'à 72 h | Cartes consultables ; automatisation courante **à vérifier** | Les fichiers numériques publics ne sont ouverts qu'après deux jours ; l'accès temps réel requiert une demande institutionnelle ([FAQ BDFC](https://dust.aemet.es/faq/how-can-i-access-and-download-numerical-data-of-the-dust-forecasts)) |
| Observations PM10/PM2.5 de stations amont | Temps réel selon le réseau | Oui si le flux Geod'air/EEA est disponible | Signal de confirmation, pas prévision autonome ; latence et disponibilité à auditer |
| Satellite/AOD/RGB et lidar | Proche temps réel selon capteur | Confirmation du panache déjà présent | Nuages, nuit et conversion AOD→PM de surface ; disponibilité exacte à 03 h **à vérifier** |

Sources complémentaires : [CAMS global, fiche du jeu de données](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts?tab=overview) ; [BDFC, guide utilisateur](https://dust.aemet.es/products/overview/user-guide).

### 4.5 Quel indicateur précoce les organismes utilisent-ils ?

**Pas un indice unique.** Le protocole français de gestion des épisodes mobilise PREV'AIR, les observations AASQA, la composition issue de CARA/MERA et des informations CAMS/ACTRIS ; il rappelle que les panaches sahariens peuvent arriver par l'Espagne et les Pyrénées ou par la Méditerranée et rester en altitude avant d'affecter le sol ([INERIS, *Protocole de gestion des épisodes de pollution particulaire*, version disponible en 2026](https://www.ineris.fr/sites/default/files/contribution/Documents/Protocole_gestion%20des%20%C3%A9pisodes.v4.1_1.pdf)). La méthode portugaise publiée combine elle aussi satellite, rétrotrajectoires et modèles de poussières avant d'estimer le fond par percentile glissant ([Gama et al., 2020, *Atmosphere* 11, 134, DOI 10.3390/atmos11020134](https://doi.org/10.3390/atmos11020134)).

**Prototype 48 h recommandé** — Construire un indicateur transparent, sans prétendre qu'il s'agit d'un standard :

1. poussière de surface et fraction poussière de PM10 du dernier cycle CAMS Europe disponible ;
2. poussière/AOD CAMS global et gradient amont Espagne–Méditerranée, si le flux est effectivement reçu avant l'heure d'émission ;
3. médiane et maximum PM10–PM2.5 des stations rurales amont pendant 6–24 h ;
4. direction de trajectoire/vent et persistance du panache ;
5. drapeau de confirmation satellite ou lidar, sans le rendre obligatoire.

Le terme PM10–PM2.5 est un proxy de fraction grossière, **pas un seuil saharien validé**. Le test doit comparer CAMS seul à CAMS + indicateur, sur les plis station × mois inchangés et séparément sur les jours identifiés comme poussiéreux selon la méthode réglementaire.

## Actions classées pour les prochaines 48 heures

1. **PM2.5 — ablation PBL/inversion isolée.** Coût faible, résultat interprétable, aucun besoin de nouvelle donnée si ERA5/IFS est déjà disponible. Attendu publié : **Inconnu**.
2. **PM2.5 — proxy chauffage dynamique.** Inventaire résidentiel PM2.5 × froid × faible PBLH × calendrier. La littérature montre un gain de POD sur épisodes dans un contexte chilien, mais le gain RMSE français est **Inconnu**.
3. **PM10 — drapeau poussières multimodal.** Cycle CAMS précédent + signal global/amont ; mesurer séparément jours poussiéreux et non poussiéreux. C'est le test le plus directement lié aux sept plis négatifs si ceux-ci coïncident avec des événements sahariens.
4. **NO₂ — enrichissement SRA compact.** Charge de trafic aux rayons publiés, densité bâtie/population et interactions avec typologie ; validation imbriquée groupée. Ne conserver que le gain incrémental sur le modèle typologique.
5. **Hyperparamètres — mini-tuning imbriqué.** 20–30 essais proches du défaut et orientés régularisation ; abandon immédiat si le signal interne n'est pas stable. Ne pas investir dans un nouveau balayage 200 essais.

## Ce qui demeure inconnu

- Le gain PM2.5 attendu sous une validation simultanément aveugle aux stations et aux mois : aucune étude directement comparable n'a été trouvée.
- Le gain marginal de la PBL, du chauffage au bois ou de la morphologie bâtie dans ce protocole précis.
- Un rayon universel de représentativité d'une station : la SRA est polluant-, métrique-, site- et modèle-dépendante.
- Une fraction générale des dépassements PM10 méditerranéens français imputable au Sahara.
- Une métrique publique de performance prévisionnelle CAMS-dust en France à 03 h et J+1, séparant détection du panache et amplitude au sol.
- La latence garantie du cycle CAMS global 00 UTC avant 03 h et l'accès automatisé temps réel au BDFC pour un candidat non institutionnel.
