# R13 — Comprendre, pas seulement mesurer

## Lecture d’ensemble

Vos résultats racontent une histoire cohérente : le post-traitement corrige très bien les composantes **stables, locales et observables dans les covariables** — surtout le contraste sous-maille du NO₂ — mais beaucoup moins les erreurs **synoptiques, chimiques et événementielles** de l’ozone et des particules. Ce mécanisme est plausible ; il ne transforme toutefois pas chaque importance de variable LightGBM en relation causale.

Les chiffres du projet sont traités ici comme des mesures internes non reproduites. Chaque comparaison externe précise sa portée ; lorsqu’aucune amplitude publiée n’est directement comparable au double aveugle station × mois, je l’indique.

---

## A. Expliquer les résultats mesurés

### A1 — Pourquoi le NO₂ est-il beaucoup plus corrigeable ?

**Établi.** Votre mécanisme principal est le bon. Le NO₂ urbain est fortement lié aux sources proches — notamment le trafic — et présente des gradients rapides que la moyenne d’une maille CAMS de 0,1° ne peut reproduire à l’emplacement exact d’une station. Les évaluations européennes constatent que les modèles régionaux manquent particulièrement les maxima de NO₂ près des villes pendant les situations stagnantes et les couches limites stables ([Vautard et al., 2009, DOI 10.1016/j.atmosenv.2008.09.083](https://doi.org/10.1016/j.atmosenv.2008.09.083) ; [CAMS, documentation du jeu régional 0,1°](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).

La correction apprend donc surtout une **fonction de représentativité** : écart persistant entre concentration moyenne de maille et micro-environnement de la station, auquel s’ajoutent les biais d’émissions, de profil horaire, de mélange vertical et de chimie. Elle ne « recrée » pas physiquement une rue ; elle estime l’écart statistique attendu pour un site ayant tel trafic, relief, usage du sol et type de station ([Vitali et al., 2023, DOI 10.5194/gmd-16-6029-2023](https://doi.org/10.5194/gmd-16-6029-2023)).

O₃ et une grande partie des PM₂.₅ ont des composantes secondaires et transportées : leurs erreurs dépendent davantage du rayonnement, du transport, des précurseurs, de la thermodynamique des aérosols, des conditions aux limites et des épisodes. CHIMERE documente ces couplages et leur sensibilité à la météorologie et aux options de chimie ([Menut et al., 2024, DOI 10.5194/gmd-17-5431-2024](https://doi.org/10.5194/gmd-17-5431-2024)).

**Jugement.** `+36,7 %` sur NO₂ est attendu qualitativement, mais son amplitude reste à comparer sur les mêmes stations, dates et horizon. Une partie peut aussi venir d’un CAMS brut particulièrement biaisé sur votre sélection ; séparer `gain par correction du biais moyen`, `gain spatial` et `gain temporel` évitera de tout attribuer à la résolution.

### A2 — Pourquoi la typologie aide-t-elle le NO₂ mais pas O₃/PM₂.₅ ?

**Établi.** Les catégories trafic/fond/industriel et urbain/rural sont des proxys directs de l’intensité et de la proximité des émissions de NOₓ ; leur rendement sur NO₂ est donc attendu. Pour l’ozone, le NO fraîchement émis consomme localement O₃ (`NO + O₃ → NO₂ + O₂`), particulièrement la nuit et en hiver, tandis que la production nette d’O₃ se produit plus loin et dépend du régime NOₓ–COV et du rayonnement ([EEA/Climate-ADAPT, *Ground-level ozone*](https://climate-adapt.eea.europa.eu/en/observatory/topics/health-impacts/ground-level-ozone/ground-level-ozone) ; [Monks et al., 2015, DOI 10.5194/acp-15-8889-2015](https://doi.org/10.5194/acp-15-8889-2015)).

Un effet négatif de la typologie trafic est donc physiquement plausible, mais **un effet marginal nul n’est pas contradictoire**. CAMS contient déjà NOₓ, O₃, météo et cycle horaire ; les variables de paysage et le CAMS peuvent absorber le contraste que la typologie résume. Une étiquette trafic/fond est aussi trop grossière pour coder distance, débit, direction du vent, hauteur des bâtiments et régime chimique.

Pour PM₂.₅, « trafic » ne sépare pas correctement primaire, nitrate/ammonium secondaire, chauffage et transport longue distance. **Test causal prudent :** estimer l’effet ajouté de la typologie avec et sans covariables routières/CAMS, puis son interaction avec saison, heure et NO₂ CAMS ; ne pas lire l’importance LightGBM comme une contribution atmosphérique.

### A3 — Sous-estimation de 11,6 µg/m³ du NO₂ urbain de fond

La résolution et le mélange vertical sont les causes les plus probables : une maille mélange zones routières et peu émises, lisse les panaches et représente imparfaitement les couches stables qui concentrent le NO₂ près du sol. Les inventaires et profils temporels peuvent ajouter un biais, mais votre seule série résiduelle ne permet pas de répartir ces causes ([Vautard et al., 2009](https://doi.org/10.1016/j.atmosenv.2008.09.083) ; [Menut et al., 2024](https://doi.org/10.5194/gmd-17-5431-2024)).

La hauteur de prélèvement peut contribuer à l’écart de représentativité, sans expliquer à elle seule un biais national homogène. La chimie nocturne et la conversion NO/NO₂ importent pour le cycle horaire ; sur une cible journalière, elles sont partiellement moyennées.

**Résultat publié directement comparable à `−11,6 µg/m³` : inconnu.** Les rapports CAMS publient biais/RMSE par station, typologie, saison et période, mais je n’ai pas trouvé une moyenne « France, urbain de fond, mêmes 36 mois, J+1 journalier ». Il faut donc présenter `−11,6` comme votre mesure, puis la décomposer par saison, heure/agrégat, densité urbaine et niveau observé plutôt que l’adosser à une amplitude non comparable ([CAMS, rapports EQC régionaux](https://atmosphere.copernicus.eu/regional-services)).

### A4 — Pourquoi la pluie porte-t-elle tout le gain météo du NO₂ ?

Le lessivage direct du NO₂ gazeux n’est pas l’explication à privilégier : sa constante de Henry est faible par rapport aux espèces très solubles, et le dépôt humide de l’azote concerne aussi les produits transformés, nitrate et ammonium ([Sander, 2023, DOI 10.5194/acp-23-10901-2023](https://doi.org/10.5194/acp-23-10901-2023) ; [Zhang et al., 2021, DOI 10.1016/j.ecoenv.2021.112180](https://doi.org/10.1016/j.ecoenv.2021.112180)).

La pluie est vraisemblablement un **marqueur de régime** : passage frontal, vent et turbulence, couche limite renouvelée, forte nébulosité et surfaces humides ; elle peut aussi covarier avec une baisse d’activité routière. Si vent/couche limite sont mal spécifiés ou redondants, le modèle choisit la pluie comme variable-synthèse.

**Test en 48 h.** Remplacer `pluie` par : occurrence, intensité, cumul antérieur, heures depuis la pluie et indicateurs de front ; ajouter vent, pression, hauteur de couche limite et jour de semaine. Faire une permutation conditionnelle de la pluie à l’intérieur de classes `vent × saison × jour`, puis comparer avant/pendant/après l’averse. Un effet qui disparaît après conditionnement est un proxy ; une chute supplémentaire pendant la pluie, à régime comparable, serait compatible avec un mécanisme direct ou une activité modifiée, pas encore une preuve causale.

### A5 — Pourquoi les pires plis O₃ sont-ils hivernaux ?

En hiver, la production photochimique locale est faible ; le signal de surface dépend davantage du transport de fond, du mélange vertical et de la titration par NO. Une petite erreur de vent, de couche stable ou de NOₓ peut alors inverser le résidu local, et un modèle entraîné surtout sur la relation chaude/ensoleillée généralise mal ([EEA/Climate-ADAPT](https://climate-adapt.eea.europa.eu/en/observatory/topics/health-impacts/ground-level-ozone/ground-level-ozone) ; [Monks et al., 2015](https://doi.org/10.5194/acp-15-8889-2015)). Une intrusion stratosphérique est possible mais ne doit pas être invoquée sans profils, traceurs ou analyse synoptique.

**Votre résultat est notable, pas absurde.** Une dégradation de 24–35 % dans deux mois peut signaler un changement de cycle CAMS, une distribution saisonnière mal pondérée, peu d’observations valides ou quelques épisodes dominants. Vérifier n, RMSE brute, biais, stations contributrices et cycle CAMS avant une explication chimique.

L’ozone hivernal garde un intérêt sanitaire et scientifique ; il n’est pas correct de dire qu’il est inutile. En revanche, le protocole français d’évaluation des épisodes O₃ à 180 µg/m³ travaille d’avril à septembre, et la valeur cible européenne de santé est fondée sur la MDA8 ([LCSQA, RTN évaluation applicable au 01/01/2022](https://www.lcsqa.org/system/files/media/documents/LCSQA%20-%20RTN-%20Evaluation_pr%C3%A9vision_vapplicable01012022.pdf) ; [directive (UE) 2024/2881, annexe I](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)). Présentez donc deux évaluations : annuelle pour la qualité générale, avril–septembre pour l’usage épisode.

### A6 — Feux utiles, sol inutile

Les feux de végétation peuvent injecter PM₂.₅, carbone organique et carbone suie, puis affecter la France par feux locaux ou panaches ibériques et plus lointains. L’incendie de l’Aude d’août 2025 a eu un impact régional mesuré par Atmo Occitanie, ce qui confirme le mécanisme sans établir une part moyenne annuelle de 3 % ([Atmo Occitanie, *Impact des incendies d’août 2025*](https://www.atmo-occitanie.org/impact-des-incendies-daout-2025-sur-la-qualite-de-lair-en-occitanie)).

Il faut séparer **feux de végétation**, brûlages agricoles/écobuages et chauffage résidentiel au bois. Dans les Hautes-Pyrénées, Atmo Occitanie a précisément combiné traceurs de biomasse et surfaces brûlées satellitaires pour attribuer les particules ([Atmo Occitanie, campagne Hautes-Pyrénées 2023](https://www.atmo-occitanie.org/hautes-pyrenees-caracterisation-des-sources-de-particules-2023)).

La remise en suspension locale et les poussières minérales contribuent surtout à la fraction grossière, donc davantage aux PM₁₀ ; une fraction fine existe, notamment lors d’intrusions désertiques. Un type de sol statique ne contient ni vent de friction, ni humidité du sol, ni couverture végétale, ni activité agricole : son absence de gain n’invalide pas les poussières, elle invalide ce proxy isolé. CHIMERE traite d’ailleurs les poussières comme une émission météodépendante, pas comme une simple classe géologique ([Menut et al., 2024](https://doi.org/10.5194/gmd-17-5431-2024)).

### A7 — Dispersion inutile comme variable, utile comme régime de fiabilité

C’est un comportement plausible d’un ensemble multi-modèles. Les membres CAMS partagent une partie des forçages et des inventaires, donc leur dispersion n’est ni indépendante ni automatiquement calibrée ; un spread faible peut coexister avec une erreur commune. Les travaux européens montrent un spread NO₂ souvent trop faible, et une origine du spread O₃ variable selon région : émissions/terrain près des villes et montagnes, conditions aux limites sur les façades maritimes ([Vautard et al., 2009](https://doi.org/10.1016/j.atmosenv.2008.09.083)).

Une forte divergence signale que les formulations de chimie, aérosols, dépôt, émissions et mélange répondent différemment au régime courant. Elle peut donc **stratifier l’erreur** sans ajouter d’information marginale à un modèle qui reçoit déjà les sept concentrations membres.

Le facteur `6,6×` ne signifie pas encore que la correction « profite » causalement du spread : son gain relatif peut mécaniquement être plus grand là où CAMS brut est mauvais. Publiez, par décile de spread, RMSE brute, RMSE corrigée, gain absolu, effectif et couverture saisonnière ; testez ensuite si le spread prédit l’erreur absolue hors échantillon. La relation spread–skill est l’outil adapté ([Delle Monache et al., 2020, DOI 10.1175/WAF-D-19-0148.1](https://doi.org/10.1175/WAF-D-19-0148.1)).

### A8 — Aucune météo explicite en production

Ce n’est pas surprenant. CAMS traduit déjà une prévision météorologique en transport, mélange, chimie, émissions naturelles et dépôt ; ses concentrations encodent donc indirectement température, vent, rayonnement, pluie et couche limite. Ajouter la météo n’aide que pour les erreurs résiduelles que le CTM traduit imparfaitement ou pour des interactions sous-maille ([CAMS, système régional](https://atmosphere.copernicus.eu/regional-air-quality-production-systems) ; [Menut et al., 2024](https://doi.org/10.5194/gmd-17-5431-2024)).

Le `+7,8 %` d’ERA5 est un **plafond rétrospectif**, car ERA5 assimile des observations futures relativement à l’émission. L’expérience opérationnelle doit employer les champs IFS disponibles au run CAMS, avec leurs vrais cycles et échéances. Petetin et al. ont comparé HRES et ERA5 dans un MOS O₃ et trouvé des résultats proches dans leur protocole ibérique, sans garantir que ce sera vrai sous votre double aveugle ([2022, DOI 10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022)).

---

## B. Le régime de pollution en Occitanie

### B1 — Régimes caractéristiques

- **Ozone méditerranéen estival.** Chaleur, rayonnement, émissions de précurseurs, transport et recirculation littorale produisent un enjeu régional durable ; en 2025, l’objectif de qualité santé et végétation n’était respecté sur aucun territoire régional selon Atmo Occitanie ([Atmo Occitanie, bilan 2025](https://www.atmo-occitanie.org/actualites/bilan-de-la-qualite-de-lair-en-2025-quen-est-il-des-emissions-de-polluants)).
- **NO₂ de proximité dans les grandes agglomérations.** Toulouse et Montpellier concentrent trafic, population et enjeux ZFE/PPA ; les niveaux stagnent encore près des grands axes en 2025 ([Atmo Occitanie, bilan 2025](https://www.atmo-occitanie.org/occitanie-evaluation-de-la-qualite-de-lair-2025)).
- **Particules hivernales de vallée.** Chauffage au bois, brûlages et couches stables peuvent s’accumuler dans les vallées pyrénéennes ; l’attribution exige des traceurs, pas seulement PM₁₀/PM₂.₅ ([Atmo Occitanie, Hautes-Pyrénées 2023](https://www.atmo-occitanie.org/hautes-pyrenees-caracterisation-des-sources-de-particules-2023)).
- **Poussières désertiques.** Les intrusions sahariennes se combinent parfois aux émissions locales ; leur déduction réglementaire demande un faisceau de preuves et une quantification ([Atmo Occitanie, hiver 2020–2021](https://atmo-occitanie.org/sites/default/files/publications/2023-06/Rapport%20ETU-2022-126_Bilan%20de%20la%20pollution%20aux%20particules_hiver%2020-21.pdf) ; [directive 2008/50/CE, art. 20](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32008L0050)).

La différence avec la France moyenne est donc moins un polluant exclusif qu’une combinaison : façade méditerranéenne favorable à l’O₃, relief pyrénéen, apports désertiques, grands corridors et métropoles, avec une forte hétérogénéité entre ouest toulousain, littoral et vallées.

### B2 — Circulations locales et maille de 10 km

La brise de mer peut transporter un panache côtier vers l’intérieur le jour, puis favoriser sa recirculation lors de l’inversion du flux ; Atmo Occitanie relie les niveaux plus élevés de l’est régional aux interactions terre–mer ([Atmo Occitanie, bilan ozone 2020, pp. 16–17](https://atmo-occitanie.org/sites/default/files/publications/2021-06/ETU-2021-078%20Pollution%20%C3%A0%20l%27ozone%202020.pdf)). Les circulations de vallée et le drainage nocturne contrôlent l’accumulation et le découplage vertical ; une maille 0,1° lisse pentes, fonds de vallée et fronts de brise.

Tramontane/cers ventilent souvent le littoral occidental, tandis que l’autan organise le transport au sud-est de Toulouse ; leur effet sur la pollution dépend toutefois de la source en amont et de la stabilité. **À vérifier** avec une étude régionale datée avant de leur attribuer systématiquement « air propre » ou « accumulation ».

Les cas les plus susceptibles d’être mal représentés à 10 km sont le front de brise, les vallées étroites, les inversions peu profondes, les panaches routiers/industriels et le mélange côtier. Ce sont précisément des situations où un modèle méso-échelle ou une descente d’échelle physique apporte davantage qu’une correction statique.

### B3 — Spécificités d’émission

L’agriculture régionale émet de l’ammoniac précurseur de nitrate/ammonium secondaire ; la viticulture motive une surveillance spécifique des pesticides, sans valeur réglementaire dans l’air ambiant à ce jour ([Atmo Occitanie, campagne pesticides 2023–2024](https://www.atmo-occitanie.org/occitanie-surveillance-des-pesticides-dans-lair-ambiant-2023-2024)). Toulouse combine trafic, chauffage, aéronautique/industrie et incinération ; sur Toulouse Métropole, Atmo Occitanie indiquait que 71 % des émissions de NOₓ de 2022 provenaient du transport ([Atmo Occitanie, campagne SETMI 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2025-09/Rapport%20ETU-2025-145_Evaluation%20de%20la%20qualite%20de%20l%27air%20dans%20l%27environnement%20de%20l%27UVE%20du%20Mirail%20%28SETMI%29%20-%20Campagne%20%C3%A0%20l%27%C3%A9cole%20Georges%20Bastide%20.pdf)).

Le couloir rhodanien, l’étang de Berre, le transport maritime et la péninsule Ibérique peuvent contribuer aux conditions aux limites de l’est et du sud régional. Leur contribution chiffrée à un épisode donné est **à vérifier par rétrotrajectoires, spéciation et simulations de sensibilité** ; la proximité géographique ne suffit pas à l’attribution.

### B4 — Études régionales à connaître

Les cinq dossiers les plus utiles avant entretien sont : le [bilan régional 2025](https://www.atmo-occitanie.org/occitanie-evaluation-de-la-qualite-de-lair-2025), le [bilan ozone 2025](https://www.atmo-occitanie.org/occitanie-evaluation-de-lexposition-lozone-2025), la [caractérisation des particules des Hautes-Pyrénées](https://www.atmo-occitanie.org/hautes-pyrenees-caracterisation-des-sources-de-particules-2023), le [bilan des particules de l’hiver 2020–2021](https://atmo-occitanie.org/sites/default/files/publications/2023-06/Rapport%20ETU-2022-126_Bilan%20de%20la%20pollution%20aux%20particules_hiver%2020-21.pdf) et l’[impact des incendies d’août 2025](https://www.atmo-occitanie.org/impact-des-incendies-daout-2025-sur-la-qualite-de-lair-en-occitanie).

Ajoutez les diagnostics PPA de [Toulouse](https://prod.atmo-occitanie.org/sites/default/files/publications/2025-03/Rapport%20Evaluation%20PPA%20-%20Tendanciel%20et%20actions_VF3.pdf) et [Perpignan](https://www.atmo-occitanie.org/perpignan-evaluation-du-ppa-diagnostic-initial-des-emissions-et-de-la-qualite-de-lair-2024) : ils montrent comment l’association relie inventaire, scénario, concentration et exposition — une mission différente du MOS.

### B5 — Enjeux actuels de l’association

Les publications 2025–2026 font ressortir : adaptation du réseau à la nouvelle directive, PPA de Toulouse/Perpignan et évaluations territoriales, suivi des politiques de mobilité/ZFE par mesures NO₂ et scénarios, ozone régional, chauffage biomasse, pesticides/perturbateurs endocriniens/PFAS, pollens Poll’Occ, environnements industriels et air intérieur ([Atmo Occitanie, bilan 2025](https://www.atmo-occitanie.org/occitanie-evaluation-de-la-qualite-de-lair-2025) ; [Toulouse Métropole 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/ETU_2026_124_%C3%89valuation%20de%20la%20qualit%C3%A9%20de%20l%E2%80%99air%20en%202025%20sur%20le%20territoire%20de%20Toulouse%20M%C3%A9tropole.pdf) ; [Poll’Occ 2026](https://www.atmo-occitanie.org/actualites/pollocc-decouvrez-la-prevision-pollens-made-occitanie)).

Pour votre profil, les angles immédiatement utiles sont la validation spatiale/temporelle des prévisions, l’incertitude des cartes et scénarios, l’anticipation des épisodes O₃/PM et la traçabilité d’une chaîne reproductible. La correction CAMS n’est qu’un composant de cette chaîne.

---

## C. L’horizon réglementaire

### C1 — Valeurs 2030 et conséquences

Les principales valeurs limites de santé à atteindre au **1er janvier 2030** sont :

| Polluant | 2030 | Droit antérieur repris jusqu’en 2026 |
|---|---:|---:|
| PM₂.₅ annuel | 10 µg/m³ | 25 µg/m³ |
| PM₂.₅ journalier | 25 µg/m³, ≤18 dépassements/an | pas de limite journalière équivalente |
| PM₁₀ annuel | 20 µg/m³ | 40 µg/m³ |
| PM₁₀ journalier | 45 µg/m³, ≤18/an | 50 µg/m³, ≤35/an |
| NO₂ annuel | 20 µg/m³ | 40 µg/m³ |
| NO₂ journalier | 50 µg/m³, ≤18/an | pas de limite journalière équivalente |
| NO₂ horaire | 200 µg/m³, ≤3/an | 200 µg/m³, ≤18/an |

Source de toutes les valeurs : [directive (UE) 2024/2881, annexe I, tableaux 1 et 2](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881). Pour O₃, la valeur cible santé reste 120 µg/m³ en MDA8 mais passe à au plus 18 jours/an en moyenne sur trois ans, contre 25 avant 2030 ([annexe I, section 2](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).

La transposition doit intervenir au plus tard le **11 décembre 2026** ; les normes 2030 peuvent déclencher des feuilles de route dès 2026–2029 dans les zones au-dessus des futures valeurs ([directive, art. 19 et 30](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)). Conséquence AASQA : davantage de zones proches/dépassant les seuils d’évaluation, réexamen des points, super-sites, cartes de représentativité, modèles validés, trajectoires et information publique. La configuration française définitive est **à vérifier dans les textes de transposition publiés**, pas dans le seul projet de décret.

### C2 — Prévisions et information du public

L’article 22 impose une information adéquate et en temps utile, un indice de qualité de l’air mis à jour **chaque heure** couvrant au moins SO₂, NO₂, PM₁₀, PM₂.₅ et O₃ lorsqu’ils sont surveillés, ainsi que des informations sanitaires adaptées aux populations sensibles ([directive, art. 22](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).

L’annexe X impose des données horaires par point, les données issues de modèles lorsqu’elles sont disponibles, et une information en temps utile sur les dépassements observés **ou prévus** des seuils d’information/alerte. La prévision doit indiquer la zone attendue pour l’après-midi ou les jours suivants, l’évolution probable et ses raisons, puis les conseils sanitaires et actions ([directive, annexe X, points 1–3](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).

Cela renforce la pertinence de votre sujet, mais n’impose ni LightGBM, ni un POD minimal, ni l’emploi de CAMS. L’obligation porte sur le service, l’information et la qualité documentée.

### C3 — Polluants émergents : statuts différents

Dans les super-sites urbains et ruraux, PM₁₀, PM₂.₅, UFP et black carbon sont des mesures fixes ; NO₂/O₃ le sont aussi, et l’ammoniac est fixe dans les super-sites ruraux. Le potentiel oxydant des PM est **recommandé** en mesure fixe ou indicative, de même que certains autres composés lorsqu’ils ne sont pas déjà requis ([directive, annexe VII, tableaux 1–3](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).

En plus des super-sites, les UFP doivent être mesurées à des lieux de forte concentration à raison d’au moins un point par cinq millions d’habitants, avec au moins un point pour les États plus petits ([directive, annexe III, D](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)). Il n’existe pas pour autant de valeur limite UFP/BC/NH₃/potentiel oxydant dans l’annexe I : obligation de connaissance ne signifie pas norme de conformité.

### C4 — OMS 2021 versus droit européen

Les lignes directrices OMS 2021 sont sanitaires et non juridiquement contraignantes : PM₂.₅ annuel 5 µg/m³, PM₁₀ annuel 15, NO₂ annuel 10 et O₃ de saison de pointe 60 µg/m³ ; elles proposent aussi des valeurs de court terme ([OMS, *Global Air Quality Guidelines*, 2021](https://www.who.int/publications/i/item/9789240034228)).

Les limites UE 2030 — 10, 20 et 20 µg/m³ respectivement pour PM₂.₅, PM₁₀ et NO₂ annuels — réduisent l’écart sans atteindre les guides OMS. La directive fixe un objectif de long terme d’alignement et prévoit une révision périodique, mais le droit opposable reste celui de l’UE transposé nationalement ([directive (UE) 2024/2881, art. 1 et annexe I](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).

### C5 — Décision d’exécution (UE) 2026/1208

Le texte du 9 juin 2026 rend opérationnelle la représentativité spatiale : exigences minimales sur résolution, émissions, météo, fond, phénomènes locaux, assurance qualité et validation des modèles ; méthodologie pour relier un point aux zones ayant des concentrations similaires ; cartes et révision lors des changements du réseau, des sources ou de la météorologie ([décision 2026/1208, art. 2–10](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)).

Pour une détermination par modèle, la zone similaire utilise une tolérance de **±15 %** autour de la valeur centrale ou un minimum de l’annexe I si celui-ci est plus large. Les cartes emploient une année des cinq dernières années, éventuellement plusieurs si la méthode d’intervariabilité est démontrée ; la directive exige la publication de la représentativité au moins tous les cinq ans ([décision, art. 7–8](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj) ; [directive, annexe IV D](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).

**Date importante : la décision s’applique à partir du 30 juin 2028**, pas dès sa publication ([décision 2026/1208, art. 11](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)). Pour une AASQA, cela transforme la modélisation en pièce explicite de conception et d’évaluation du réseau ; pour votre projet, cela valorise la généralisation spatiale et l’incertitude, mais une prédiction aux stations ne suffit pas à cartographier une aire de représentativité.

---

## D. Ce que fait une AASQA au quotidien

### D1 — Missions

Les AASQA mettent en œuvre, pour le compte de l’État, la surveillance de la qualité de l’air : mesures, modélisation, inventaires, prévision, information du public et appui aux autorités. Elles contribuent aussi à l’amélioration des connaissances et à l’évaluation des actions publiques ([Code de l’environnement, art. L.221-3](https://www.legifrance.gouv.fr/codes/article_lc/LEGIARTI000033034471) ; [arrêté du 19 avril 2017 relatif au dispositif national](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000034441401)).

La répartition exacte des effectifs et budgets d’Atmo Occitanie par mission n’est pas publiée sous une forme directement exploitable ici : **à vérifier dans le rapport d’activité et en entretien**. Ne réduisez pas l’association à une équipe de prévision ; inventaire, métrologie, études, partenariats territoriaux, communication et administration occupent une part substantielle de l’activité.

### D2 — AASQA, LCSQA, INERIS et PREV’AIR

Les AASQA exploitent les réseaux régionaux, valident les observations, produisent/expertisent les prévisions locales et informent les autorités régionales. Le LCSQA est le laboratoire national de référence : coordination technique, assurance qualité, référentiels, gestion de GEOD’air et appui au ministère/AASQA ([LCSQA, présentation](https://www.lcsqa.org/fr)).

L’INERIS est l’un des membres du LCSQA et coordonne PREV’AIR avec Météo-France, le CNRS et le LCSQA. PREV’AIR exécute CHIMERE/MOCAGE, collecte les observations quasi réelles, produit analyses, prévisions brutes et adaptations statistiques nationales ; les produits corrigés servent de base à l’expertise, pas de décision automatique ([LCSQA/INERIS, *Performances PREV’AIR 2023*](https://www.lcsqa.org/system/files/media/documents/LCSQA2024-Performances_prevair_2023%20V0.pdf)).

La procédure est préfectorale : l’AASQA caractérise et prévoit, transmet à l’autorité et à l’ARS, tandis que le préfet déclenche la procédure et les mesures applicables selon le dispositif local ([arrêté du 7 avril 2016, art. 7–14](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954)).

### D3 — Chaîne d’un épisode

La chaîne pratique est : observations temps réel + modèles bruts/corrigés → contrôle et expertise → évaluation du seuil et des critères de surface/population/persistance → information au préfet et à l’ARS au moins quotidiennement → décision préfectorale d’information-recommandation ou d’alerte → communication et mesures d’urgence → suivi et retour d’expérience ([arrêté du 7 avril 2016, art. 2, 7 et 10–14](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376954)).

Le RTN français structure J0/J1, la disponibilité, la traçabilité des sources, les corrections expertes et le bilan annuel ([LCSQA, RTN traçabilité, 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)). Les heures limites exactes et l’organisation d’astreinte d’Atmo Occitanie sont **à vérifier** : elles ne se déduisent pas du texte national.

### D4 — Compétences attendues d’un profil données/modélisation

Le socle crédible est : Python/R et SQL ; formats NetCDF/GRIB, CSV/Parquet et SIG ; xarray, pandas, géotraitements et cartographie ; séries temporelles, géostatistique, validation croisée groupée, incertitude et métriques réglementaires ; Linux, Git, tests, automatisation et traçabilité. S’y ajoutent la compréhension des CTM, de la météo, des inventaires d’émissions, de la métrologie et des textes.

Ce tableau est une **synthèse de pratique**, pas une liste statutaire opposable. Les outils exacts d’Atmo Occitanie sont à vérifier dans la fiche de poste. Ce qui différencie un bon candidat n’est pas une bibliothèque ML supplémentaire, mais la capacité à relier un résultat au processus atmosphérique, à son incertitude et à la décision.

### D5 — Limites reconnues et place utile du projet

Les limites publiées sont : résolution insuffisante pour rues et vallées, émissions et profils temporels incertains, conditions aux limites pour O₃/poussières/feux, couche limite et météo locale, faible nombre d’extrêmes, rupture lors des changements de cycle, dépendance aux observations récentes et représentativité des stations ([Menut et al., 2024](https://doi.org/10.5194/gmd-17-5431-2024) ; [Petetin et al., 2022](https://doi.org/10.5194/acp-22-11603-2022) ; [Vitali et al., 2023](https://doi.org/10.5194/gmd-16-6029-2023)).

Votre utilité potentielle est précise : quantifier quelles composantes sont corrigeables, garantir une validation réellement spatiale et temporelle, produire des probabilités calibrées et des diagnostics d’échec, et raccorder la sortie aux métriques LCSQA/FAIRMODE. Elle ne consiste pas à remplacer CHIMERE/PREV’AIR, ni à présenter une RMSE meilleure comme une meilleure alerte.

### Formulation de clôture pour l’entretien

> « Le résultat NO₂ vient surtout d’un écart de représentativité stable entre une maille régionale et un site local ; l’ozone et les particules restent davantage gouvernés par des régimes transportés et épisodiques. Mon modèle est donc un complément diagnostique et probabiliste à la chaîne physique. Je sais où il gagne, où il échoue — notamment aux seuils rares — et je l’évalue avec les unités de décision, la saison et les contraintes réglementaires de l’AASQA. »
