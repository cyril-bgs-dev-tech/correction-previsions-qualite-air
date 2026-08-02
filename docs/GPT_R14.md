# Ce qui sert vraiment à Atmo Occitanie

> **Périmètre et vocabulaire.** Situation vérifiée au **2 août 2026**. Les mentions **Documenté** renvoient à une source primaire publique ; **Constat documentaire** décrit ce que le corpus public consulté permet ou non d’établir ; **Jugement** est une recommandation de candidature ; **Résultat interne** reprend les chiffres fournis dans le prompt, sans les auditer ni les présenter comme une publication d’Atmo Occitanie.

## Verdict avant les cinq questions

1. **La candidature ne devrait plus être présentée comme spontanée.** Atmo Occitanie publie actuellement une offre de **data scientist junior en CDD, basée à Toulouse, avec candidature avant le 22 août 2026**. Le poste est rattaché au pôle Partenariats et prévoit un entretien technique avec ce pôle. C’est exactement l’échéance indiquée dans le prompt. ([Atmo Occitanie, offre Data scientist junior, juillet 2026](https://www.atmo-occitanie.org/sites/default/files/2026-07/recrutement_data_scientist_junior.pdf))
2. **La correction statistique d’une prévision régionale n’est pas une idée nouvelle pour l’association.** Une offre de stage Atmo Occitanie de 2023 décrit une plateforme régionale de chimie-transport, des adaptations statistiques déjà en place, un historique de prévisions, des validations existantes et des travaux ciblant O₃, PM10, PM2.5 et le krigeage. ([Atmo Occitanie, stage « Adaptation statistique des prévisions », 2023](https://www.atmo-occitanie.org/sites/default/files/2022-11/Atmo%20Occitanie_Offre%20de%20stage%20Mod%C3%A9lisation%20Adapt%20Stat%202023.pdf))
3. **Le projet reste utile comme preuve de compétence, pas encore comme solution d’alerte.** Le double aveugle station + mois, les intervalles groupés par station et le résultat négatif sur la détection démontrent une discipline d’évaluation directement pertinente. En revanche, le gain RMSE contre **CAMS brut** ne démontre pas un gain contre la chaîne **CHIMERE + adaptation statistique + mesures + expertise** d’Atmo Occitanie. Cette dernière combinaison est publiquement documentée, mais sa configuration détaillée ne l’est pas. ([Atmo Occitanie, chaîne d’expertise ozone, 2026](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie))
4. **L’angle à défendre est :** « je sais transformer un besoin métier en protocole vérifiable, détecter les fuites, quantifier l’incertitude, documenter un résultat négatif et livrer un outil maintenable ». C’est beaucoup plus aligné sur l’offre que « j’ai trouvé une meilleure prévision que l’AASQA » : l’offre demande collecte, structuration, qualité des données, analyses, modèles simples, Python/R/SQL, indicateurs partenaires, formalisation des besoins et gouvernance des données. ([Atmo Occitanie, offre Data scientist junior, juillet 2026](https://www.atmo-occitanie.org/sites/default/files/2026-07/recrutement_data_scientist_junior.pdf))

---

## 1. Ce qu’Atmo Occitanie fait réellement

### 1.1 Missions, organisation et moyens

**Documenté — mandat.** Atmo Occitanie est l’AASQA agréée pour la région. L’arrêté national lui confie la surveillance et l’évaluation des polluants réglementés, la prévision des polluants concernés par les épisodes, l’information quotidienne des préfets et du public, l’inventaire régional des émissions et la contribution aux plans publics. La surveillance peut combiner mesures fixes ou indicatives, campagnes, modélisation et estimation objective. ([Arrêté du 16 avril 2021, art. 3, 6 et 9](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/))

**Documenté — structure.** L’association compte **56 salariés : 38 à Toulouse et 18 au siège de Montpellier/Pérols**. Le service Études et prospective comprend les pôles Partenariats, Modélisation/Géomatique et Inventaire ; s’y ajoutent Mesure et innovation, Administration-finances, Communication et Informatique. Les deux implantations publiques sont Pérols et Toulouse. ([Atmo Occitanie, « Qui sommes-nous ? »](https://www.atmo-occitanie.org/qui-sommes-nous), [mentions légales](https://www.atmo-occitanie.org/mentions-legales))

**Documenté — gouvernance.** Les membres sont répartis entre quatre collèges disposant du même pouvoir décisionnel : État, collectivités, acteurs économiques, associations et personnalités qualifiées. Cette gouvernance ne signifie pas que chaque financeur intervient dans la validation technique quotidienne ; elle organise la gouvernance associative. ([Atmo Occitanie, « Qui sommes-nous ? »](https://www.atmo-occitanie.org/qui-sommes-nous))

**Constat documentaire — budget.** Le site actuel confirme des financements multipartites, et le bilan 2025 remercie les partenaires tout en annonçant une réflexion sur le modèle économique. Je n’ai pas trouvé, dans les sources primaires publiques consultées, le **budget consolidé 2025**, sa ventilation exacte par collège, ni une répartition des ETP par activité. Ces chiffres doivent être notés **Inconnus publiquement**, et non reconstitués à partir d’anciens pourcentages. ([Atmo Occitanie, bilan régional 2025, perspectives 2026-2027](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

### 1.2 Réseau de mesure

**Documenté.** Le bilan 2025 recense **53 stations permanentes, 9 stations annuelles et 470 mesures complémentaires**. La page méthodologique indique plus de 30 polluants, des analyseurs continus avec rapatriement plusieurs fois par jour, et des prélèvements différés analysés en laboratoire pour d’autres composés. ([Atmo Occitanie, bilan régional 2025, p. 9](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf), [dispositif de mesures](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-evaluer-la-qualite-de-lair/le-dispositif-de-mesures-un-reseau-au-plus))

**Documenté.** Le réseau n’est pas un échantillon aléatoire du territoire : les stations de fond représentent l’exposition générale, tandis que les stations trafic ou industrielles visent des niveaux de proximité. Cette typologie est une raison technique de conserver des validations par station et par type de site. ([Atmo Occitanie, dispositif de mesures](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-evaluer-la-qualite-de-lair/le-dispositif-de-mesures-un-reseau-au-plus))

**Documenté.** Les données alimentent la modélisation, la prévision quotidienne et l’évaluation annuelle ; elles sont diffusées par Atmo Occitanie et vers la base nationale Géod’Air pour centralisation et rapportage européen. ([Atmo Occitanie, dispositif de mesures](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-evaluer-la-qualite-de-lair/le-dispositif-de-mesures-un-reseau-au-plus))

### 1.3 Outils de modélisation et chaîne de prévision

**Ce qui est documenté :**

- Atmo Occitanie exploite une chaîne opérationnelle comprenant le modèle de chimie-transport **CHIMERE** et des outils de préparation/validation des données. ([Atmo Occitanie, stage Modélisation, 2026](https://www.atmo-occitanie.org/sites/default/files/2026-01/stage%20mod%C3%A9lisation.pdf))
- Sa description publique récente mentionne inventaire régional des émissions, prévisions météorologiques à 72 heures, assimilation des mesures, traitement statistique et expertise humaine. ([Atmo Occitanie, chaîne d’expertise ozone, 2026](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie))
- Une adaptation statistique de la prévision régionale existait déjà en 2023 ; Atmo Occitanie disposait alors d’un historique quotidien et d’outils internes de validation. ([Atmo Occitanie, stage « Adaptation statistique », 2023](https://www.atmo-occitanie.org/sites/default/files/2022-11/Atmo%20Occitanie_Offre%20de%20stage%20Mod%C3%A9lisation%20Adapt%20Stat%202023.pdf))
- La prévision publique est produite chaque jour pour **J et J+1**, à l’échelle de toutes les communes, à partir des cartes, stations, prévisions météorologiques et de l’expertise des prévisionnistes. ([Atmo Occitanie, « La prévision de la qualité de l’air »](https://www.atmo-occitanie.org/la-prevision-de-la-qualite-de-lair))
- L’arrêté national impose l’intégration des prévisions PREV’AIR aux conditions aux limites et une évaluation annuelle du système régional — outils et expertise — selon le référentiel technique national. Le rapport doit être transmis à la DREAL et au LCSQA avant le 30 juin suivant. ([Arrêté du 16 avril 2021, art. 9](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/))

**Ce qui n’est pas établi dans le corpus public actuel :** version exacte de CHIMERE, résolution horizontale régionale, forçage météorologique opérationnel, inventaire utilisé à chaque échéance, variables et algorithme de l’adaptation statistique, cadence de réentraînement, latence des observations assimilées, et performance annuelle détaillée. La bonne formulation est **« non documenté publiquement dans les sources consultées »**, pas « inexistant ».

### 1.4 Produits et usages

| Produit public | Contenu documenté | Usage immédiat |
|---|---|---|
| Météo de l’air | indice communal J/J+1, cartes par polluant, messages d’épisode | information du public et des autorités, anticipation des procédures ([prévision Atmo Occitanie](https://www.atmo-occitanie.org/la-prevision-de-la-qualite-de-lair)) |
| Open data | mesures horaires et cartographies urbaines/régionales téléchargeables | réutilisation, transparence, analyses territoriales ([Open data Atmo Occitanie](https://www.atmo-occitanie.org/actualites/telechargez-les-donnees-de-lair-sur-lopen-data)) |
| AtmoViz / Panorama | indicateurs air-climat-énergie, émissions, concentrations, exposition, historique territorial | diagnostic et pilotage pour collectivités et citoyens ([Panorama des territoires](https://www.atmo-occitanie.org/actualites/panorama-des-territoires-les-donnees-2024-de-la-qualite-de-lair-sur-mon-territoire-sont)) |
| Bilans annuels | conformité, épisodes, cartes, émissions, études et perspectives | rapportage, information et priorisation régionale ([bilan régional 2025](https://www.atmo-occitanie.org/occitanie-evaluation-de-la-qualite-de-lair-2025)) |
| Études de scénarios | mobilité, ZFE, PPA, biomasse, industrie, infrastructures | aide à la décision avant/après action ([évaluation PPA Toulouse](https://www.atmo-occitanie.org/sites/default/files/publications/2025-03/Rapport%20Evaluation%20PPA%20-%20Tendanciel%20et%20actions_VF3.pdf)) |
| Poll’Occ | risque quotidien pour 22 plantes, réseau + météo/botanique + modèles statistiques/IA + prévisionnistes | prévention sanitaire et open data ([Poll’Occ, 20 mars 2026](https://www.atmo-occitanie.org/actualites/pollocc-decouvrez-la-prevision-pollens-made-occitanie)) |

### 1.5 Publications et thèmes récents

**Documenté.** Le programme 2025-2026 est nettement plus large que les quatre polluants du projet : seuils 2030, exposition territoriale, super-sites, particules ultrafines, carbone suie, NH₃ et précurseurs d’ozone, pollens, pesticides, perturbateurs endocriniens, PFAS, incendies, mobilité, biomasse et santé. ([Atmo Occitanie, bilan régional 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

**Exemples récents :** campagne 2023-2024 sur dix sites pour les pesticides et cinq sites pour les perturbateurs endocriniens/PFAS ; lancement de Poll’Occ en 2026 ; évaluation en urgence des incendies de l’Aude en août 2025 ; équipement des super-sites urbain de Toulouse-Mazades et rural de Peyrusse-Vieille. ([étude pesticides/PFAS, 10 octobre 2025](https://www.atmo-occitanie.org/actualites/pesticides-perturbateurs-endocriniens-et-pfas-polluants-eternels-dans-lair-les-resultats), [Poll’Occ](https://www.atmo-occitanie.org/actualites/pollocc-decouvrez-la-prevision-pollens-made-occitanie), [incendies d’août 2025](https://www.atmo-occitanie.org/impact-des-incendies-daout-2025-sur-la-qualite-de-lair-en-occitanie), [super-sites](https://www.atmo-occitanie.org/actualites/atmo-occitanie-equipe-deux-super-sites-pour-renforcer-la-surveillance-des-polluants))

---

## 2. Les difficultés techniques réellement rencontrées

### 2.1 Les cinq difficultés de premier rang

1. **Passer de points de mesure à une exposition spatiale défendable.** Les stations ne couvrent pas tout le territoire ; la nouvelle réglementation donne davantage de poids aux applications de modélisation et à la représentativité spatiale. Atmo Occitanie indique désormais un intervalle de confiance de **10 à 20 % selon le polluant** pour ses indicateurs de concentration, population et surface exposées aux seuils abaissés. ([Atmo Occitanie, bilan 2025, avertissement méthodologique](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))
2. **Prévoir les événements rares sans dégrader le régime courant.** Les épisodes locaux associent chauffage et stagnation, poussières désertiques, ozone photochimique et désormais fumées d’incendie à longue distance. Les coûts d’une fausse alerte et d’un épisode manqué ne sont pas symétriques ; une RMSE moyenne ne tranche donc pas la décision préfectorale. ([Atmo Occitanie, épisodes 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf), [arrêté du 7 avril 2016](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954/))
3. **Maintenir une chaîne quotidienne auditable.** Les cartes, observations, météo, inventaires, traitements statistiques et expertise doivent rester cohérents malgré retards de données, invalidations, changements de modèles et incidents. L’obligation porte sur la performance du système complet, évaluée chaque année, et non sur un modèle ML isolé. ([Arrêté du 16 avril 2021, art. 9](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/))
4. **Actualiser les émissions et les scénarios locaux.** Trafic, chauffage, agriculture, industrie et incendies n’évoluent ni à la même cadence ni avec la même observabilité. Les modèles doivent servir à la fois à la prévision, à l’exposition annuelle et aux scénarios de politiques publiques ; ces trois usages n’ont ni le même horizon ni le même protocole de validation. ([Atmo Occitanie, modélisation](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-evaluer-la-qualite-de-lair/la-modelisation-une-cartographie-pour))
5. **Absorber une hausse de la charge réglementaire avec des moyens finis.** Le bilan 2025 prévoit d’évaluer les investissements et le fonctionnement liés à la nouvelle directive, d’optimiser la plateforme régionale, de produire une modélisation haute définition et de sécuriser les besoins SI/IA ; il annonce simultanément une réflexion sur le modèle économique. ([Atmo Occitanie, perspectives 2026-2027](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

### 2.2 Ce que leurs documents publics ne disent pas

**Constat documentaire, à utiliser comme questions d’entretien :**

- le seul PRSQA régional complet retrouvé publiquement est celui de **2017-2021** ; le bilan 2025 conserve ses cinq axes et donne des perspectives 2026-2027, mais je n’ai pas trouvé un PRSQA public portant explicitement une nouvelle période ; ([PRSQA 2017-2021](https://www.atmo-occitanie.org/sites/default/files/imports/pdf/Bulletin_2_PRSQA_BD.pdf), [bilan 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))
- la configuration opérationnelle datée de CHIMERE et de son adaptation statistique n’est pas publiée avec assez de précision pour reproduire la chaîne ;
- le rapport annuel de performance de la prévision est réglementairement transmis à la DREAL et au LCSQA, mais je n’en ai pas trouvé une publication récente sur le site public ; l’arrêté impose la transmission, pas explicitement sa publication sur le site ; ([Arrêté du 16 avril 2021, art. 9](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/))
- le budget courant, le coût par bloc de surveillance et la répartition des ETP ne sont pas exposés dans les pages primaires consultées ;
- les règles internes d’arbitrage du prévisionniste, les seuils d’intervention humaine et la journalisation des corrections ne sont pas documentés publiquement.

**Jugement.** Ces absences ne sont pas des reproches à formuler. Elles fournissent cinq questions légitimes : « Quelle est votre baseline corrigée ? », « Quel est le point de coupure opérationnel des observations ? », « Quelles métriques déclenchent une revue ? », « Comment versionnez-vous la chaîne ? », « Où est aujourd’hui le coût principal : données, calcul, validation, expertise ou diffusion ? »

### 2.3 Programme régional et priorités effectives

**Documenté.** Le PRSQA 2017-2021 structurait l’action autour de cinq axes : mission d’intérêt général, transversalité air-climat-énergie-santé, impact des activités et aménagements, innovation, information/sensibilisation. Le bilan 2025 reprend ces cinq axes dans ses perspectives 2026-2027. ([PRSQA 2017-2021](https://www.atmo-occitanie.org/sites/default/files/imports/pdf/Bulletin_2_PRSQA_BD.pdf), [bilan 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

**Priorités 2026-2027 documentées et directement liées au projet :** rapport d’évaluation de la prévision, optimisation de la plateforme régionale, modélisation régionale haute définition, cartographies NO₂ des quatre grandes agglomérations, renforcement PM2.5, PPA Toulouse/Montpellier/Nîmes/Perpignan, plateforme transversale d’indicateurs, sécurisation du SI et de l’IA. ([Atmo Occitanie, bilan 2025, « Perspectives 2026-2027 »](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

### 2.4 Directive 2024/2881 et décision 2026/1208 : charge concrète

| Échéance | Obligation documentée | Travail probable pour l’AASQA — **extrapolation** |
|---|---|---|
| 11 décembre 2026 | transposition nationale de la directive | refaire la matrice réglementaire, adapter métadonnées, procédures, systèmes de diffusion et plans ([directive 2024/2881, art. 30](https://eur-lex.europa.eu/legal-content/FR/ALL/?uri=CELEX%3A32024L2881)) |
| 2026-2029 | si les niveaux dépassent les valeurs 2030, feuille de route au plus tard deux ans après l’année du constat, sauf justification par scénario de référence | scénarios d’émissions/concentrations, attribution sectorielle, mesures, trajectoires et consultation publique ([directive 2024/2881, art. 19 §4 et annexe VIII](https://eur-lex.europa.eu/legal-content/FR/ALL/?uri=CELEX%3A32024L2881)) |
| 30 juin 2028 | application de la décision technique sur modélisation et représentativité | validation des applications, cartes de représentativité, traçabilité des entrées, revue des cas mesure/modèle contradictoires ([décision 2026/1208, art. 2 à 11](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)) |
| 31 décembre 2028 | feuille de route exigée pour demander certains reports de délai | projections démontrées, financement, information sanitaire et dossier à la Commission ([directive 2024/2881, art. 18](https://eur-lex.europa.eu/legal-content/FR/ALL/?uri=CELEX%3A32024L2881)) |
| 1er janvier 2030 | nouvelles valeurs limites et cibles applicables | surveillance plus dense, exposition à plus basse concentration, plans et suivi des actions ([directive 2024/2881, annexe I](https://eur-lex.europa.eu/legal-content/FR/ALL/?uri=CELEX%3A32024L2881)) |

**Documenté.** La décision 2026/1208 ne demande pas seulement une meilleure RMSE : elle exige une résolution capable de représenter la variabilité pertinente, des données d’émissions et météo adaptées, une évaluation du modèle, une méthode de représentativité spatiale et une revue lorsqu’un modèle contredit certaines situations mesurées. Pour la représentativité par modèle, elle retient une tolérance de 15 % ou un minimum absolu selon le polluant ; elle s’applique à partir du 30 juin 2028. ([Décision d’exécution (UE) 2026/1208, art. 2, 3, 7, 10 et 11](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj))

### 2.5 Attentes du public et limites techniques

**Documenté.** Le public reçoit une carte communale simple, un indice et des recommandations ; la production sous-jacente assemble pourtant modèles, mesures et expertise. Atmo Occitanie avertit que ses cartes représentent le fond modélisé, peuvent différer d’une mesure ponctuelle et comportent une incertitude. ([Météo de l’air](https://www.atmo-occitanie.org/cours), [prévision](https://www.atmo-occitanie.org/la-prevision-de-la-qualite-de-lair))

**Jugement.** La tension opérationnelle centrale est donc : communiquer une information claire et actionnable sans donner une illusion de précision locale. Un candidat utile sait présenter simultanément une estimation, son domaine de validité, son incertitude et la décision qu’elle peut — ou ne peut pas — soutenir.

---

## 3. Où le projet peut s’insérer — et où il ne le peut pas encore

### 3.1 Carte d’insertion réaliste

| Point d’insertion | Propriétaire métier probable | Apport possible du projet | Conditions minimales avant usage |
|---|---|---|---|
| **Banc d’évaluation de la prévision** | Modélisation/Géomatique + prévisionnistes | plis station + mois, intervalles groupés, métriques par régime, comparaison versionnée | rejouer exactement les sorties opérationnelles, utiliser le point de coupure réel, reproduire le référentiel LCSQA ; c’est l’insertion la plus crédible ([arrêté du 16 avril 2021, art. 9](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/)) |
| **Correction après CHIMERE** | Modélisation/Géomatique | résidu LightGBM, covariables territoriales, estimation d’incertitude | benchmark contre leur adaptation locale, météo disponible à l’émission, latence/invalidations, dérive des versions, tests de panne et retour arrière ([stage adaptation statistique 2023](https://www.atmo-occitanie.org/sites/default/files/2022-11/Atmo%20Occitanie_Offre%20de%20stage%20Mod%C3%A9lisation%20Adapt%20Stat%202023.pdf)) |
| **Cartographie annuelle d’exposition** | Modélisation/Géomatique + Inventaire | variables de paysage, transfert vers sites non vus, diagnostic des zones mal représentées | recalibrage annuel distinct de la prévision, validation spatiale réglementaire et incertitude sur population/surface ([bilan 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf)) |
| **Indicateurs et livrables partenaires** | Pôle Partenariats | pipeline de qualité, tableaux reproductibles, analyses et visualisations | besoin métier écrit, provenance, version, règles d’accès, documentation et transfert — meilleur alignement avec l’offre 2026 ([offre Data scientist junior](https://www.atmo-occitanie.org/sites/default/files/2026-07/recrutement_data_scientist_junior.pdf)) |
| **Couche probabiliste d’épisode** | Prévisionnistes + direction technique ; préfet pour les mesures | probabilité et incertitude comme aide à l’expertise | calibration hors temps/hors station, POD/FAR/CSI, budget de fausses alertes, stabilité par régime, protocole de responsabilité ; non démontré actuellement ([arrêté du 7 avril 2016](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954/)) |

**Jugement.** Le meilleur premier livrable n’est pas un modèle en production : c’est un **harness d’évaluation reproductible** branchable sur leurs sorties historiques, qui compare brut, adaptation actuelle, alternative ML et expertise finale avec les mêmes coupures et les mêmes événements.

### 3.2 Qui a autorité sur quoi

**Documenté.** Atmo Occitanie produit l’évaluation et la prévision, informe quotidiennement les préfets et met en œuvre la communication prévue par les arrêtés départementaux. Lors d’une alerte, les mesures de réduction sont décidées ou mises en œuvre par l’autorité préfectorale ; un algorithme candidat n’a donc aucune autorité réglementaire autonome. ([Arrêté du 16 avril 2021, art. 3 et 9](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/), [Atmo Occitanie, prévision et épisodes](https://www.atmo-occitanie.org/la-prevision-de-la-qualite-de-lair))

**Jugement.** En entretien, parler de « couche d’aide à l’expertise » et de « validation par le métier », jamais de « déclenchement automatique de l’alerte ».

### 3.3 Valeur ajoutée au-delà de PREV’AIR — et au-delà de leur propre correction

**Documenté.** PREV’AIR fournit les conditions aux limites obligatoires à la prévision régionale ; Atmo Occitanie possède en plus son inventaire, son réseau, sa modélisation locale, une adaptation statistique et l’expertise des prévisionnistes. Comparer le projet uniquement à CAMS brut répond donc à une question scientifique, pas encore à la question opérationnelle « bat-il le système utilisé ? ». ([Arrêté du 16 avril 2021, art. 9](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/), [Atmo Occitanie, adaptation statistique 2023](https://www.atmo-occitanie.org/sites/default/files/2022-11/Atmo%20Occitanie_Offre%20de%20stage%20Mod%C3%A9lisation%20Adapt%20Stat%202023.pdf))

**Ce qui peut rester différenciant — à vérifier sur leurs données :**

1. validation simultanément hors station et hors mois, plutôt qu’une validation seulement temporelle ou seulement sur stations connues ;
2. incertitude bootstrapée par unité indépendante pertinente, et non par ligne horaire ;
3. audit explicite des régimes rares et publication du résultat négatif ;
4. variables territoriales détaillées pour le transfert vers des sites non vus ;
5. protocole de comparaison et de suivi de dérive réutilisable, indépendamment de LightGBM.

**Jugement.** Ne pas déclarer ces cinq points « nouveaux chez Atmo Occitanie » : leur protocole interne n’est pas public. Les présenter comme des capacités que le candidat sait apporter et qu’il propose de confronter à l’existant.

### 3.4 Réponse franche : un gain de RMSE sans gain démontré sur la détection a-t-il une utilité ?

**Oui, mais pas celle qu’il faut sur-vendre.**

- **NO₂ : utilité potentielle forte pour les champs continus et l’exposition.** Le gain interne annoncé de **36,7 %** peut intéresser la cartographie de proximité trafic et les futurs seuils, surtout si la généralisation spatiale tient. Il ne prouve rien contre la cartographie opérationnelle locale d’Atmo. En 2025, les dépassements actuels restent concentrés près du trafic dans les grandes agglomérations, tandis que les valeurs 2030 élargissent fortement les populations concernées. ([Atmo Occitanie, bilan des quatre agglomérations 2025](https://www.atmo-occitanie.org/actualites/montpellier-nimes-perpignan-et-toulouse-quelle-qualite-de-lair-en-2025-en-occitanie))
- **PM10 : utilité moyenne pour la concentration, non démontrée pour l’alerte.** Le gain RMSE interne de **13,3 %** peut améliorer un fond quotidien ou certains indicateurs. Mais au budget d’alerte ×1,18, l’intervalle incluant zéro signifie que le projet n’a pas démontré une meilleure détection. Le résultat significatif à ×1,82 lorsque le mois est connu ne remplace pas une validation réellement prospective.
- **O₃ et PM2.5 : utilité marginale à confirmer.** Des gains internes de **6,9 %** et **4,5 %** peuvent être réels, mais ils sont de l’ordre de grandeur où la stabilité par saison, site, version amont et choix de baseline devient décisive. L’ozone régional reste précisément un problème de régimes météorologiques et de transport, pas seulement de biais moyen. ([Atmo Occitanie, exposition à l’ozone et chaîne d’expertise, 2026](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie))

**Conclusion de décision.** Pour l’information continue, les cartes, l’exposition et le contrôle qualité, un meilleur RMSE peut être utile. Pour déclarer « meilleure anticipation des épisodes », la preuve manque. La phrase de dossier honnête est :

> « Le modèle améliore la concentration moyenne hors station et hors mois, surtout pour le NO₂. Je n’ai pas démontré de gain robuste au budget d’alerte réaliste ; j’ai donc séparé l’objectif de cartographie de celui de détection et documenté la limite. »

### 3.5 Comment une contribution externe non sollicitée serait reçue

**Constat : ce cas n’est probablement plus le bon.** Au 2 août 2026, l’offre de data scientist junior est publique et correspond à l’échéance. Le dossier doit répondre à cette offre et à ses missions, pas se présenter comme un produit apporté de l’extérieur. ([Atmo Occitanie, recrutement](https://www.atmo-occitanie.org/recrutement), [offre Data scientist junior](https://www.atmo-occitanie.org/sites/default/files/2026-07/recrutement_data_scientist_junior.pdf))

**Jugement.** Une proposition externe serait crédible si elle commence par le besoin, reconnaît leur correction existante, demande la baseline locale et propose un pilote borné. Elle serait fragile si elle arrive comme démonstration de supériorité contre CAMS brut, avec demande de mise en production, dépendances non maîtrisées ou confusion entre score moyen et responsabilité d’alerte.

---

## 4. Ce qu’il faut montrer dans le dossier

### 4.1 Compétences explicitement demandées

**Documenté.** L’offre junior demande : collecte/structuration/préparation de données internes et partenaires ; analyses exploratoires, statistiques et prédictives ; mise en qualité ; modèles simples ; scripts Python/R/SQL ; indicateurs, rapports et livrables partenaires ; formalisation des besoins ; valorisation ; qualité, sécurité et gouvernance ; travail en binôme, communication et vulgarisation. ([Atmo Occitanie, offre Data scientist junior, juillet 2026](https://www.atmo-occitanie.org/sites/default/files/2026-07/recrutement_data_scientist_junior.pdf))

**Conséquence.** Le projet CAMS doit prouver au moins six choses dans cet ordre :

1. pipeline d’appariement et contrôles qualité ;
2. protocole anti-fuite et séparation des usages ;
3. choix d’une baseline pertinente ;
4. incertitude et analyse des erreurs ;
5. traduction en décision et limites ;
6. documentation permettant à une ingénieure référente de reprendre le travail.

Le nom « LightGBM » vient après ces six points.

### 4.2 Ce qui distingue un projet appliqué d’un exercice académique

| Projet appliqué | Signal académique insuffisant |
|---|---|
| entrées disponibles à l’heure réelle d’émission | ERA5 final ou observations futures utilisées sans analyse de disponibilité |
| baseline opérationnelle locale et expertise finale | seule comparaison à CAMS brut |
| découpage correspondant au déploiement : temps, stations et changements de chaîne | split aléatoire ligne par ligne |
| métriques moyenne + extrêmes + catégories + événements + calibration | un unique pourcentage de RMSE |
| données, code, configuration, dépendances et versions traçables | notebook manuel non rejouable |
| surveillance de dérive, repli, coût et latence | score hors ligne sans scénario d’exploitation |
| limites écrites et responsabilité humaine | promesse d’automatisation de la décision |

**Jugement.** Le double aveugle station + mois et les intervalles groupés sont les meilleurs signaux du dossier. Ils doivent être visibles avant la liste des covariables.

### 4.3 Les résultats négatifs : atout ou handicap ?

**Atout s’ils ferment une mauvaise décision.** Montrer que l’amélioration moyenne ne suffit pas à l’alerte prouve que le candidat sait falsifier sa propre hypothèse, séparer les objectifs et éviter une communication abusive. Cette posture est compatible avec une organisation auditée par le LCSQA et soumise à une évaluation annuelle de la prévision. ([Arrêté du 16 avril 2021, art. 9 et 23](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000043388197/))

**Handicap seulement si :** le candidat cache le résultat dans une annexe, le présente comme un échec général, ou propose tout de même l’outil pour l’alerte. Le bon récit tient en trois phrases : hypothèse, test sévère, décision prise à partir du test.

### 4.4 Format à joindre et à montrer

**Documenté.** L’offre demande un CV et passe par une préqualification RH puis un entretien technique avec le pôle Partenariats ; aucun portfolio lourd n’est demandé. ([Atmo Occitanie, offre Data scientist junior](https://www.atmo-occitanie.org/sites/default/files/2026-07/recrutement_data_scientist_junior.pdf))

**Jugement — dossier optimal :**

- **CV :** une ligne résultat + une ligne protocole + une ligne outillage ;
- **lettre :** partir des missions du pôle Partenariats et de la directive, puis utiliser le projet comme preuve ;
- **pièce jointe facultative de 2 pages PDF :** besoin, données, validation, quatre résultats, limite épisodes, ce que l’on comparerait chez Atmo ;
- **entretien : 6 diapositives maximum :** problème métier, chaîne de données, pièges évités, résultats, falsification, plan des 30 premiers jours ;
- **sur demande :** dépôt reproductible avec README, dictionnaire de données, configuration, tests, model card et journal des expériences ; ne pas envoyer un ZIP volumineux sans demande.

### 4.5 Erreurs de posture à éviter

1. Dire ou laisser entendre que PREV’AIR/Atmo Occitanie ne corrige pas statistiquement ses prévisions.
2. Comparer LightGBM à CAMS brut puis conclure à une supériorité sur la chaîne AASQA.
3. Vendre un gain RMSE comme un gain d’alerte alors que le test au budget réaliste est non significatif.
4. Mettre « IA » au centre avant qualité, traçabilité, besoin partenaire et transfert.
5. Parler d’automatiser le prévisionniste ou la décision préfectorale.
6. Présenter les covariables ERA5 comme opérationnelles sans démontrer leur équivalent disponible à l’émission.
7. Omettre dérive de CAMS, changement de cycle, indisponibilité des entrées et coût de maintenance.
8. Arriver avec une solution figée au lieu de demander leur baseline, leurs erreurs coûteuses et leurs contraintes de délai.
9. Traiter les mesures comme une vérité homogène sans typologie de station, validation et représentativité.
10. Affirmer connaître l’organisation interne à partir du seul site public : plusieurs paramètres essentiels restent **à vérifier en entretien**.

### 4.6 Formulation de positionnement recommandée

> « Je ne viens pas proposer de remplacer votre chaîne CHIMERE, vos adaptations statistiques ou l’expertise des prévisionnistes. Mon projet démontre une façon de construire et d’auditer un pipeline prédictif : données versionnées, validation hors station et hors période, incertitude groupée, comparaison par régime et résultat négatif assumé sur l’alerte. Je voudrais appliquer cette discipline à vos besoins partenaires et, si elle est utile, comparer proprement une alternative à votre baseline réelle. »

---

## 5. Les enjeux propres à l’Occitanie

### 5.1 Problématiques territoriales spécifiques

| Enjeu | Ce que le territoire rend particulier | Conséquence pour la donnée ou le modèle |
|---|---|---|
| **NO₂ trafic** | dépassements actuels encore localisés près du trafic à Montpellier, Toulouse et Perpignan ; enjeux 2030 dans les quatre grandes agglomérations | résolution urbaine, trafic réel, rues et transfert hors stations ([Atmo Occitanie, quatre agglomérations 2025](https://www.atmo-occitanie.org/actualites/montpellier-nimes-perpignan-et-toulouse-quelle-qualite-de-lair-en-2025-en-occitanie)) |
| **PM2.5 et PM10** | concentrations stagnantes et contribution importante du chauffage au bois résidentiel ; enjeu étendu avec les seuils 2030 | émissions temporelles du chauffage, météo stable, taille des particules et exposition ([même bilan 2025](https://www.atmo-occitanie.org/actualites/montpellier-nimes-perpignan-et-toulouse-quelle-qualite-de-lair-en-2025-en-occitanie)) |
| **Ozone** | objectif de qualité santé et végétation non respecté sur tout le territoire en 2025 ; forte sensibilité à chaleur, rayonnement, transport et chimie | validation par saison et régime, précurseurs, météo et transport longue distance ([Atmo Occitanie, ozone 2025](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie)) |
| **Poussières désertiques** | apports sahariens fréquents, particulièrement visibles sur le massif pyrénéen ; station de Bolquère maintenue pour les détecter | classification de régime/source, profils verticaux, PM10/PM2.5, trajectoires et traitement réglementaire des sources naturelles ([bilan 2025, perspectives](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf)) |
| **Incendies** | feux locaux et transport des fumées depuis la péninsule Ibérique, le Canada ou d’autres régions | émissions quasi temps réel, panaches, PM2.5/PM10, incertitude et dispositifs d’urgence ([incendies d’août 2025](https://www.atmo-occitanie.org/impact-des-incendies-daout-2025-sur-la-qualite-de-lair-en-occitanie)) |
| **Agriculture/viticulture** | région décrite par Atmo comme première viticole et deuxième agricole de France ; pesticides, ammoniac et particules secondaires | mesures ciblées, calendriers agricoles, données non réglementées et multi-exposition ([Atmo Occitanie, « Qui sommes-nous ? »](https://www.atmo-occitanie.org/qui-sommes-nous), [campagne pesticides/PFAS](https://www.atmo-occitanie.org/actualites/pesticides-perturbateurs-endocriniens-et-pfas-polluants-eternels-dans-lair-les-resultats)) |
| **Littoral, ports et industrie** | Sète, Thau, unités de valorisation, cimenteries, carrières et zones industrielles font l’objet de suivis partenaires | inventaires fins, mesures différées, panaches locaux, scénarios et communication riverains ([bilan 2025, perspectives](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf)) |
| **Pollens et santé** | diversité biogéographique régionale ; prévision de 22 taxons avec réseau, météo, botanique, statistique/IA et expertise | produit quotidien déjà opérationnel, fort besoin de qualité de données et vulgarisation ([Poll’Occ](https://www.atmo-occitanie.org/actualites/pollocc-decouvrez-la-prevision-pollens-made-occitanie)) |

### 5.2 Zones réglementaires, PPA et ZFE

**Documenté.** L’open data régional distingue les zones administratives de surveillance suivantes : zones à risques de Toulouse et Montpellier, zones à risques de Nîmes et Perpignan, et zone régionale. ([Atmo Occitanie, Open data](https://www.atmo-occitanie.org/actualites/telechargez-les-donnees-de-lair-sur-lopen-data))

**Documenté.** Les perspectives 2026-2027 prévoient la contribution aux révisions des PPA de Toulouse et Montpellier, le suivi du PPA de Nîmes et les réflexions sur un projet de PPA de Perpignan. Le travail attendu couvre émissions, scénarios, exposition et évaluation d’actions, pas seulement la prévision du lendemain. ([Atmo Occitanie, bilan 2025, perspectives](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

**Documenté.** Pour Toulouse, Atmo Occitanie a évalué le PPA avec un scénario tendanciel et des actions ; la modélisation intègre notamment des données de trafic fournies par l’AUAT et la ZFE. En 2025, le partenariat avec Toulouse Métropole portait aussi sur l’évolution du parc depuis la ZFE, le 30 km/h et un suivi NO₂ multisites. ([évaluation PPA Toulouse](https://www.atmo-occitanie.org/sites/default/files/publications/2025-03/Rapport%20Evaluation%20PPA%20-%20Tendanciel%20et%20actions_VF3.pdf), [bilan Toulouse Métropole 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/ETU_2026_124_%C3%89valuation%20de%20la%20qualit%C3%A9%20de%20l%E2%80%99air%20en%202025%20sur%20le%20territoire%20de%20Toulouse%20M%C3%A9tropole.pdf))

**Prudence.** Les règles d’accès aux ZFE ont connu des évolutions politiques et juridiques rapides. Le rôle techniquement stable d’Atmo Occitanie est d’évaluer émissions, concentrations et exposition selon des scénarios ; ne pas centrer le dossier sur une règle Crit’Air susceptible de changer.

### 5.3 Épisodes notables des trois dernières années complètes

- **2023 :** 34 procédures, 18 journées et 8 départements ; 29 procédures PM10. Onze journées de particules étaient liées aux poussières sahariennes, cinq à des situations hivernales et deux associaient poussières désertiques et écobuages ; trois journées concernaient l’ozone. ([Atmo Occitanie, bilan régional 2023](https://www.atmo-occitanie.org/sites/default/files/publications/2024-05/ATMO-BILAN-ANNUEL-2023-BD.pdf))
- **2024 :** le bilan 2025 donne **36 procédures** sur l’année. Les 7-8 avril, une masse de poussières désertiques a conduit à une alerte par persistance en Ariège et dans les Pyrénées-Orientales ; l’épisode d’octobre a également fortement touché les Pyrénées. ([Atmo Occitanie, bilan 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf), [communiqué du 8 avril 2024](https://www.atmo-occitanie.org/sites/default/files/epipol/pdf/communique_20240408.pdf))
- **2025 :** 48 procédures sur 23 journées, dans 12 départements ; 36 procédures PM10 et 12 procédures ozone sur 8 journées. L’année combine chauffage/stagnation en janvier, poussières désertiques, fumées des incendies du Canada et de l’Aude, et incendies ibériques. ([Atmo Occitanie, bilan régional 2025, p. 13](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

**Actualité 2026 à ne pas ignorer.** En juillet 2026, Atmo Occitanie a publié des procédures liées à des poussières désertiques puis aux fumées d’incendies de Gironde et du Tarn transportées vers plusieurs départements. Cela confirme que les régimes « feux » et « poussières » ne sont pas des cas anecdotiques pour une future couche de détection. ([épisode du 13 juillet 2026](https://www.atmo-occitanie.org/alerte-pollution/2026-07-13%7C66), [épisode du 27 juillet 2026](https://www.atmo-occitanie.org/en/alerte-pollution/2026-07-27%7C12))

**Gestion documentée.** Atmo prévoit J/J+1, informe les préfets et diffuse une communication spécifique. Une procédure d’information est déclenchée au seuil correspondant ; une persistance ou un seuil d’alerte peut conduire à une alerte et à des mesures préfectorales. ([Atmo Occitanie, prévision](https://www.atmo-occitanie.org/la-prevision-de-la-qualite-de-lair), [arrêté du 7 avril 2016](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954/))

### 5.4 Collaborations et programmes visibles

**Documenté.** Le bilan 2025 cite ou programme des collaborations avec : DREAL et LCSQA pour le dispositif réglementaire ; collectivités et intercommunalités pour PPA/PCAET/scénarios ; ARS et CREAI-ORS pour les évaluations d’impact sanitaire ; CHU de Toulouse et Montpellier pour les liens pollution-pathologies ; Météo-France parmi les adhérents ; aéroports, port de Sète, Tisséo et acteurs industriels pour des suivis ciblés. ([Atmo Occitanie, bilan régional 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf))

**Documenté.** Poll’Occ a été développé depuis 2022 avec l’ARS Occitanie et des acteurs scientifiques et médicaux ; il constitue un exemple concret de produit data où le modèle ne suffit pas — réseau, données botaniques, expertise et diffusion sont intégrés. ([Atmo Occitanie, Poll’Occ](https://www.atmo-occitanie.org/actualites/pollocc-decouvrez-la-prevision-pollens-made-occitanie))

### 5.5 Sujets de communication actuels et traduction pour la candidature

| Sujet public 2025-2026 | Ce que le candidat devrait en retenir |
|---|---|
| seuils 2030 et populations exposées | l’enjeu se déplace vers la cartographie fiable à basse concentration et l’incertitude, pas seulement les pics |
| ozone persistant malgré la baisse de certains précurseurs | raisonner par mécanisme et régime, éviter le récit « plus de données = problème résolu » |
| poussières et incendies | créer des indicateurs de régime/source avant de demander à un modèle unique d’absorber tous les cas |
| Poll’Occ et santé | démontrer la capacité à travailler avec experts, partenaires et produit public |
| pesticides, PFAS, perturbateurs endocriniens, PUF et carbone suie | montrer que les compétences data sont transférables au-delà de CAMS et des polluants réglementés |
| mobilité et scénarios | relier les modèles aux décisions et indicateurs territoriaux, cœur du pôle Partenariats |

Sources : [bilan régional 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/A.ATMO-BILAN-ANNUEL-2025-2-BD.pdf), [ozone 2026](https://www.atmo-occitanie.org/actualites/pollution-atmospherique-lozone-les-realites-de-la-qualite-de-lair-en-occitanie), [Poll’Occ](https://www.atmo-occitanie.org/actualites/pollocc-decouvrez-la-prevision-pollens-made-occitanie), [pesticides/PFAS](https://www.atmo-occitanie.org/actualites/pesticides-perturbateurs-endocriniens-et-pfas-polluants-eternels-dans-lair-les-resultats).

---

## Synthèse directement actionnable pour le dossier

### Les trois messages à faire passer

1. **« Je sais évaluer sans fuite et quantifier ce qui généralise. »** Preuve : double aveugle station + mois, bootstrap par station, résultats par polluant.
2. **« Je ne confonds pas performance moyenne et décision rare. »** Preuve : résultat PM10 non significatif au budget réaliste, conservé et interprété comme limite.
3. **« Je peux servir les besoins du pôle Partenariats, pas seulement entraîner un modèle. »** Preuve à montrer : qualité et gouvernance des données, pipeline reproductible, indicateurs, rapport clair et traduction en besoin métier — compétences explicitement demandées par l’offre. ([Atmo Occitanie, offre Data scientist junior](https://www.atmo-occitanie.org/sites/default/files/2026-07/recrutement_data_scientist_junior.pdf))

### Les trois revendications à ne pas faire

1. « J’améliore la prévision d’Atmo Occitanie » — **non démontré**, car la comparaison porte sur CAMS brut et non sur leur chaîne corrigée.
2. « J’améliore la détection des épisodes » — **non démontré** au budget d’alerte réaliste.
3. « Ma correction apporte une fonction qui n’existe pas » — **faux comme formulation générale**, une adaptation statistique régionale existait déjà en 2023. ([Atmo Occitanie, adaptation statistique 2023](https://www.atmo-occitanie.org/sites/default/files/2022-11/Atmo%20Occitanie_Offre%20de%20stage%20Mod%C3%A9lisation%20Adapt%20Stat%202023.pdf))

### La proposition de valeur en une phrase

> **Un data scientist capable de reprendre des données hétérogènes, construire une évaluation réellement hors échantillon, expliciter l’incertitude et les échecs, puis transformer le résultat en outil et en livrable compréhensible par les partenaires et les experts métier.**

### Ce qui reste à vérifier en entretien

- baseline exacte de l’adaptation statistique régionale et différence avec PREV’AIR corrigé ;
- version/résolution/configuration CHIMERE et forçage météo ;
- disponibilité réelle des observations et variables au moment d’émission ;
- définition interne d’un événement et budget de fausses alertes ;
- protocole LCSQA effectivement utilisé dans le rapport annuel ;
- point de douleur prioritaire du pôle Partenariats : qualité, automatisation, indicateurs, visualisation ou gouvernance ;
- outils internes, formats, orchestration, CI/CD et contraintes de sécurité ;
- budget, ETP et capacité de maintenance d’un nouveau composant.
