# Audit logique du projet MOS

## Diagnostic préalable

La chaîne contient quatre glissements de portée qui doivent rester visibles pendant toute la lecture :

1. **Performance descriptive ≠ mécanisme causal.** La comparaison appariée décrit correctement les trois produits. Seul le factoriel à modèle et données constants identifie l’effet de la cible ; il n’explique pas automatiquement la saisonnalité du MOS officiel.
2. **Station exclue ≠ futur exclu.** La validation spatiale mesure un transfert vers d’autres stations du réseau pendant des situations temporelles déjà connues. Elle ne mesure ni un lieu quelconque, ni une année future.
3. **Mois caché ≠ prévision prospective**, sauf si toutes les dates d’entraînement précèdent le mois testé. « Double aveugle » devrait être remplacé par « blocage conjoint station–mois » : il n’y a pas d’aveugle expérimental.
4. **Dispersion intra-maille ≠ plancher d’erreur.** Elle contient différence de support, gradients réels, bruit de mesure et sélection du réseau. Elle ne devient une borne irréductible qu’après séparation de ces composantes.

# A. Audit de la chaîne inférentielle

## A1. Comparaison annuelle au MOS officiel

**La conclusion suit-elle ?** Oui, comme constat descriptif, si les trois produits sont évalués sur les mêmes couples station–jour, la même échéance et une MDA8 réglementaire correctement construite. Les données montrées établissent qu’entre le 18 janvier et le 31 décembre 2024 votre modèle a la plus faible RMSE sur les trois grandeurs réglementaires de cet échantillon.

**Explication alternative non écartée.** L’écart avec votre modèle ne peut pas être attribué au grain par cette table seule : historique d’apprentissage, covariables, fréquence de réentraînement et information disponible diffèrent. Il faut le factoriel présenté ensuite. L’écart peut aussi dépendre de la sélection des stations où le MOS existe ; la documentation CAMS indique que la liste varie avec la date et le polluant.

**Bonne portée.** « Sur les stations de fond et jours conjointement disponibles en France, du 18 janvier au 31 décembre 2024, à l’échéance étudiée. » Pas « France entière », pas « année complète », pas « système opérationnel supérieur ».

**Sources :** jeu CAMS-MOS et couverture, [doi:10.24381/2cce4067](https://doi.org/10.24381/2cce4067) ; documentation du MOS [ECMWF](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation).

## A2. Dégradation saisonnière de l’O₃ par le MOS officiel

**La conclusion suit-elle ?** Le changement de signe saisonnier suit des scores saisonniers appariés. En revanche, « dégrade huit mois sur douze » et « biais négatif chaque mois » demandent les effectifs et IC mensuels, absents de l’état fourni. Un signe ponctuel n’est pas encore une différence établie.

**Explication alternative non écartée.** Composition mensuelle variable du réseau, changement de version amont, erreur de jour civil/MDA8, et variation du nombre de dépassements. Pour trancher : intersection fixe de stations, bootstrap station×date par mois, chronologie des versions CAMS et contrôle `valid_time`.

**Bonne portée.** O₃ MDA8, France, stations desservies, J+1, 2024. Ce résultat ne démontre ni une défaillance de l’usage horaire ni une loi valable pour les années suivantes.

**Source :** l’évaluation CAMS publique traite explicitement l’O₃ MDA8 et les variations saisonnières, rapport EQC 2025, §4.6, [PDF](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf).

## A3. Effet contrôlé de la cible

**La conclusion suit-elle ?** Oui : à modèle, lignes et plis constants, les +5,8 et +6,5 points identifient l’effet total de remplacer l’apprentissage horaire puis agrégation par un apprentissage direct du maximum. Le −1,5 point PM2,5 soutient l’asymétrie maximum/moyenne.

**Explication alternative non écartée.** La cible directe et la cible horaire n’ont pas le même nombre d’exemples ni la même structure de bruit. Ce n’est pas un confondant externe : cela fait partie du changement de stratégie, mais interdit d’attribuer l’effet à la seule « non-linéarité du maximum ». Une expérience à budget d’information égal ou une courbe gain–nombre d’exemples séparerait opérateur et taille d’échantillon.

**Bonne portée.** « Pour ce boosting, ces variables, ces plis et cette période. » La réplication concorde avec Bertrand et al., mais ne prouve pas que toute architecture ou tout maximum se comporte ainsi.

**Source :** Bertrand et al. (2023), tableau 3, [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023).

## A4. Antériorité

**La conclusion suit-elle ?** Oui. Bertrand et al. testent le MOS CAMS et recommandent une cible journalière lorsque le maximum est l’usage ; votre mécanisme n’est pas nouveau.

**Explication alternative non écartée.** Votre réplication n’est pas nécessairement celle du **produit opérationnel exact** étudié dans l’article : algorithme/configuration de recherche et chaîne ADS actuelle peuvent différer. Cela ne recrée pas la nouveauté du mécanisme, seulement celle du cas opérationnel évalué.

**Bonne portée.** « Réplication sur le produit ADS 2024 et sur les grandeurs réglementaires », pas « première démonstration CAMS ».

**Sources :** Bertrand et al. (2023), [doi:10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; Petetin et al. (2022), CAMS O₃ jusqu’à la MDA8, [doi:10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022).

## A5. Généralisation spatiale +29,7 %

**La conclusion suit-elle ?** Incomplètement : le polluant, le grain, la référence et la population de plis ne sont pas indiqués dans la ligne. Si les stations sont entièrement exclues, elle établit une généralisation à d’autres stations **échantillonnées dans le même réseau et la même période**.

**Explication alternative non écartée.** Les dates sont partagées entre train et test ; le modèle peut apprendre le régime national du jour via le calendrier et CAMS. La sélection non aléatoire des stations et le fort chevauchement de covariables rendent le test plus facile qu’une région entière cachée. Mesures discriminantes : leave-region-out, distance de covariables, performance selon distance à la station d’entraînement et découpage temporel prospectif.

**Bonne portée.** « Transfert vers une station du réseau jamais vue », pas « concentration en tout lieu » ni « généralisation spatiale nationale ».

**Source :** Roberts et al. (2017), choix des blocs spatiaux et temporels, [doi:10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881).

## A6. Généralisation temporelle +6,7 %

**La conclusion suit-elle ?** Elle suit pour le protocole « mois caché », mais la moyenne positive masque une forte instabilité : cinq plis négatifs et un pire à −35,5 %. Le bon énoncé n’est pas « généralise dans le temps », mais « gain moyen faible et non robuste entre blocs mensuels ».

**Explication alternative non écartée.** Calendrier incomplet, changement de version CAMS, régimes météorologiques/chimiques absents, et éventuel entraînement sur le futur. Pour les départager : rolling-origin strict, scores par version CAMS et matrice d’erreurs par régime météo/chimique.

**Bonne portée.** Les 17 blocs disponibles entre 2023 et 2024. Pas une nouvelle année ni un cycle CAMS futur.

## A7. Blocage conjoint station–mois +1,5 %

**La conclusion suit-elle ?** Oui pour les combinaisons station–mois testées ; huit plis négatifs sur 17 montrent que l’effet moyen est fragile. L’écart moyen seul ne soutient aucune promesse de déploiement.

**Explication alternative non écartée.** Interaction station×saison, faible support de certains plis, futur encore présent dans le train, et optimisation des hyperparamètres sur un objectif spatial différent. Il faut une distribution pondérée par pli et un rolling-origin station-exclue.

**Bonne portée.** « Transfert conjoint vers certaines stations et certains blocs mensuels de la fenêtre 17 mois. » Le terme « double aveugle » doit disparaître.

## A8. Réglage spatial : +5 points spatial, −3 temporel

**La conclusion suit-elle ?** Oui si les mêmes candidats sont comparés sur des prédictions hors pli indépendantes du choix. Elle montre un conflit d’objectif, pas une propriété intrinsèque des hyperparamètres.

**Explication alternative non écartée.** Bruit de sélection (*winner’s curse*) : le meilleur réglage spatial est choisi parce qu’il a bénéficié d’une fluctuation favorable. Une validation imbriquée répétée ou la distribution de tous les candidats spatial/temps trancherait.

**Bonne portée.** Cette recherche d’hyperparamètres et ces plis ; pas « le boosting spatial ne peut pas généraliser temporellement ».

## A9. Validation janvier–juin 2025

**La conclusion suit-elle ?** Oui : après l’inférence multiway annoncée, seule la différence de RMSE avec le MOS officiel est établie, −3,22 [−4,87 ; −1,74]. L’état corrige correctement l’ancienne tentation de classer CSI et POD.

**Explication alternative non écartée.** Les 21 stations occitanes peuvent être atypiques et l’horizon janvier–juin ne couvre pas toute la saison chaude. L’écart de RMSE peut aussi venir d’un biais MOS régional particulier, pas d’une supériorité générale de votre architecture. Une autre région/année ou un modèle hiérarchique station–mois trancherait.

**Bonne portée.** O₃, 21 stations occitanes, 3 353 jours-station, premier semestre 2025. La seule conclusion comparative confirmatoire concerne la RMSE face au MOS officiel.

## A10. Classification des dépassements

**La conclusion suit-elle ?** Pas encore à partir de l’état fourni. POD 0,345→0,663 et Brier skill +0,460 ne disent pas si entraînement, calibration, choix de seuil et évaluation sont imbriqués correctement ni sur quelle fenêtre ils sont calculés.

**Explication alternative non écartée.** Fuite de calibration, changement de prévalence, seuil choisi sur le test et amélioration limitée à une poignée d’événements. Il faut diagramme de fiabilité, calibration interne au pli, Brier décomposé et IC par événement/station.

**Bonne portée.** La population et la période exactes de cette expérience doivent figurer dans toute phrase. Elle ne peut pas être fusionnée avec le résultat 2025, où POD/CSI sont non concluants.

## A11. Perte pondérée et queue haute

**La conclusion suit-elle ?** Elle suit comme frontière empirique si la perte pondérée a été choisie sans regarder les prédictions servant à annoncer +3,1 %. « RMSE global inchangé » demande aussi un IC sur la différence, pas un arrondi identique.

**Explication alternative non écartée.** Sélection a posteriori de la pondération et définition du décile sur l’échantillon de test. Une sélection en pli interne, un décile défini par les observations d’entraînement puis un score externe unique tranchent.

**Bonne portée.** Polluant, période, plis et définition du décile de cette expérience. Pas « solution générale aux extrêmes ».

## A12. Trafic hiérarchisé +13 %, population nulle

**La conclusion suit-elle ?** Une ablation établit une information prédictive conditionnelle, pas que le trafic réel est correctement représenté. « Population n’ajoute rien » signifie « après les autres variables dans ce modèle ».

**Explication alternative non écartée.** La hiérarchie routière peut proxyfier urbanité, typologie de station ou sélection du réseau ; son avantage peut venir du nombre de variables. Un modèle à dimension égale, permutation groupée, leave-city-out et interaction vent×route distingueraient trafic actif et géographie urbaine.

**Bonne portée.** NO₂, stations du réseau et période testée. Pas un effet causal du trafic ni une validité hors station.

## A13. Calendrier, variable la plus utile pour l’O₃

**La conclusion suit-elle ?** Oui comme importance prédictive par ablation. Elle ne prouve pas que le calendrier soit un mécanisme ni que cette information transporte vers une autre année.

**Explication alternative non écartée.** Le calendrier proxyfie rayonnement, température, phénologie, émissions saisonnières et même versions CAMS. Comparer calendrier seul, météo seule, calendrier+météo et leurs interactions en rolling-origin sépare ces rôles.

**Bonne portée.** O₃ et fenêtre d’apprentissage. « Retirer le calendrier augmente la RMSE de 9,1 % » est correct ; « le calendrier explique l’ozone » ne l’est pas.

## A14. « Plancher » intra-maille de 3,61 µg/m³

**La conclusion suit-elle ?** Non. Une dispersion entre stations d’une même maille quantifie un désaccord de support dans votre réseau ; elle ne prouve pas qu’aucune méthode ne puisse descendre sous 3,61. Une correction avec micro-environnement, vent et émissions peut expliquer une partie de cette dispersion.

**Explication alternative non écartée.** Gradients urbains réels, types de stations différents, bruit instrumental, désynchronisation, paires non indépendantes et hétéroscédasticité par polluant. Il faut des paires simultanées comparables, bootstrap par maille, séparation des typologies et modèle de variance conditionnelle.

**Bonne portée.** « Dispersion intra-maille observée dans cet échantillon », par polluant et grandeur. Le mot « plancher » doit être abandonné tant qu’une décomposition de variance ne l’établit pas.

**Sources :** Henne et al. (2010), [doi:10.5194/acp-10-3561-2010](https://doi.org/10.5194/acp-10-3561-2010) ; Piersanti et al. (2015), [doi:10.1016/j.apr.2015.04.005](https://doi.org/10.1016/j.apr.2015.04.005).

## A15. Gain plus fort lorsque CAMS dérive

**La conclusion suit-elle ?** L’association suit ; l’explication causale ne suit pas. Si « CAMS bon/dérive » est défini par l’erreur observée de CAMS, un gain plus grand quand l’erreur brute est grande est en partie arithmétique : il y a davantage de perte réductible.

**Explication alternative non écartée.** Régression vers la moyenne et couplage mathématique entre la variable de stratification et le gain. Avec \(e=Y-CAMS\) et correction prédite \(m(X)\),
\[
\Delta MSE = e^2-(e-m)^2 = 2em-m^2.
\]
Classer les cas par \(|e|\) sélectionne directement le premier terme. Il faut définir la dérive **ex ante** (version, désaccord d’ensemble, contrôle de processus) et tester le gain hors pli conditionnellement à ces signaux.

**Bonne portée.** « Le gain empirique covarie avec l’erreur brute » ; pas « le modèle détecte les ruptures » ni « il est robuste aux dérives ».

## A16. MQI FAIRMODE conformes

**La conclusion suit-elle ?** Oui si le code applique exactement le grain, les paramètres et la version 2026 du guide WG3. Mais trois valeurs agrégées ne montrent pas le respect par station, horizon ou saison.

**Explication alternative non écartée.** Sélection des stations et compensation entre cas faciles/difficiles ; un MQI global peut masquer des stations non conformes. Publier distribution par station, taux de conformité et sensibilité de version.

**Bonne portée.** Conformité au benchmark FAIRMODE calculé sur la population, le grain et l’horizon indiqués ; pas validation réglementaire globale ni aptitude aux alertes.

**Source :** FAIRMODE, *WG3 Forecast Guidance, version 2026*, [page officielle](https://knowledge4policy.ec.europa.eu/fairmode/quality-control-indicators-aq-forecasts-work-group-3_en).

# B. Trois incohérences apparentes

## B1. Calendrier très utile, généralisation temporelle faible

Ce sont probablement **les deux faces du même fait**, pas une contradiction. Dans une validation spatiale, toutes les stations partagent les mêmes dates : le calendrier fournit une climatologie saisonnière très efficace et le modèle voit ailleurs le même régime national. Dans un mois futur ou caché, `jour de l’année` ne dit ni si ce printemps est précoce, ni si une canicule, une inversion ou une rupture CAMS survient ; il peut même imposer une correction climatologique fausse.

Deux phénomènes restent à séparer :

- **signal saisonnier transportable** : la forme moyenne annuelle est stable ;
- **raccourci temporel** : le calendrier remplace des causes absentes et échoue lorsque leur relation change.

Mesure discriminante : quatre modèles `CAMS seul`, `CAMS+calendrier`, `CAMS+météo`, `CAMS+calendrier+météo`, évalués en rolling-origin par année/mois ; ajouter la stabilité des effets SHAP calendaires entre 2023, 2024 et 2025. Si le gain calendrier disparaît avec la météo ou change de signe, c’est un proxy. S’il reste stable hors année, c’est une climatologie utile.

## B2. Anomalies d’entrée utiles, mais mois entiers mal généralisés

Les faits sont compatibles parce qu’un détecteur de densité estime essentiellement **\(p(X)\)**, alors que l’échec temporel peut venir d’un changement de **\(p(Y\mid X)\)**. Un mois peut contenir des entrées parfaitement ordinaires — même latitude, forêt, calendrier et concentration CAMS — mais une autre relation entre CAMS et observation à cause d’un régime chimique, d’une version modèle ou d’une erreur météo invisible dans les 53 variables.

En outre, 40 des 53 variables sont statiques ou quasi statiques. IForest/ECOD peut donc surtout détecter une station paysagèrement rare, pas un état atmosphérique rare. Le fait que la correction gagne davantage sur ces cas signifie alors que le paysage corrige une erreur de support forte ; il ne dit rien sur la dérive temporelle.

Mesures discriminantes :

- anomalie calculée séparément sur variables statiques, CAMS+calendrier et variables dynamiques ;
- gain conditionné à l’anomalie **après ajustement sur l’erreur CAMS brute** ;
- discriminateur « mois d’entraînement ou mois test » et test de dérive du résidu conditionnel ;
- comparaison \(p(X)\) contre courbe de calibration de \(E[Y-CAMS\mid X]\).

Si l’anomalie cesse d’expliquer le gain après contrôle de l’erreur brute, l’effet actuel est une conséquence de difficulté, pas un indicateur de confiance.

## B3. +23,6 % quand CAMS dérive, +14,0 % quand il est bon

Les trois lectures peuvent coexister :

- **désirable** si un signal disponible avant l’observation annonce la dérive et si la correction reste calibrée ;
- **débiaisage conditionnel** si le modèle apprend \(E[Y-CAMS\mid X]\), ce qui est précisément son objectif ;
- **artefact de régression vers la moyenne** si les groupes « bon/dérive » sont définis avec l’erreur réalisée \(Y-CAMS\).

Le coefficient +0,953 en \(\Delta MSE\) est suspect de couplage mathématique : le gain partage l’erreur brute avec sa variable explicative. La mesure qui tranche est une stratification ex ante par version CAMS, dispersion inter-membres, écart aux prévisions précédentes ou contrôle de processus ne contenant pas \(Y\). Ensuite seulement, comparer biais, pente de calibration de la correction et RMSE hors pli.

L’énoncé prudent est : **« La correction retire davantage de perte sur les cas où CAMS s’avère mauvais ; nous n’avons pas montré qu’elle anticipe une dérive. »**

# C. Connaissance du domaine non mobilisée

## C1. Ce que des variables physiques peuvent réellement apporter

Le but n’est pas de refaire CHIMERE dans LightGBM. CAMS contient déjà émissions, transport, chimie, aérosols et dépôt. Les variables supplémentaires doivent indiquer **dans quel régime CAMS commet une erreur de résolution, de phase, de précurseur ou de mélange**. Une variable physiquement nommée ne devient pas causale pour autant ; elle permet surtout une stratification de l’erreur plus stable qu’un calendrier.

| Polluant / processus | Mécanisme susceptible de laisser une erreur à 8 km | Signature attendue dans le résidu | Variable observable utilisable |
|---|---|---|---|
| O₃ — production photochimique | Production non linéaire à partir de NOₓ et COV sous rayonnement ; erreur de régime NOₓ-limité/VOC-limité | Biais changeant de signe selon précurseurs, rayonnement et température ; erreur sur l’heure et l’amplitude du pic | CAMS NO₂, idéalement NO et HCHO/NMVOC ; rayonnement global/photolyse prévu ; température ; rapport HCHO/NO₂ si HCHO est disponible |
| O₃ — titration | \(NO+O_3\rightarrow NO_2+O_2\), surtout près des émissions et la nuit | O₃ trop élevé et NO₂ trop faible dans les bas O₃ urbains/nocturnes ; anticorrélation des erreurs | CAMS NO, NO₂ et O₃ ; indicateur nuit ; trafic×faible ventilation ; somme molaire \(O_x=O_3+NO_2\) |
| O₃ — dépôt sec | Dépôt stomatique/non stomatique modulé par canopée, turbulence, humidité, sécheresse et rosée | Biais saisonnier forêt×jour/nuit, changement de signe avec VPD et humidité de surface | LAI dynamique, VPD, humidité du sol, pluie/rosée, vitesse de friction ou vent, rayonnement |
| O₃ — mélange vertical | Entraînement depuis la couche résiduelle le matin, couche limite trop haute/basse, inversion de vallée | Erreur de phase au lever du jour, faibles O₃ nocturnes manqués, pics après rupture d’inversion | hauteur de couche limite prévue, gradient de température potentielle, nombre de Richardson, profils vent/température |
| O₃ — transport/recirculation | Panache régional, brise de mer et retour de masse d’air ; erreur de position plutôt que de chimie | Pic observé décalé de quelques heures ou seulement sur certains secteurs côtiers | trajectoire arrière, déplacement résultant/longueur du trajet, direction aux niveaux de la couche limite, dispersion d’ensemble |
| NO₂ — émission/dilution | Source primaire très locale et couche de mélange sous-maille ; profils de trafic non résolus | Biais fixe par station et fort effet heure×jour ouvré×vent ; maximum nocturne/matin mal placé | débit/vitesse trafic, hauteur de couche limite, coefficient de ventilation, direction du vent par rapport aux routes |
| NO₂ — photolyse et partition NO–NO₂–O₃ | Conversion rapide pilotée par lumière et oxydants | Erreurs couplées NO₂/O₃, surtout transitions aube/crépuscule | CAMS O₃, NO si disponible, rayonnement, angle solaire, \(O_x\), fraction \(NO_2/O_x\) |
| NO₂ — durée de vie/transport | Oxydation vers HNO₃/nitrate et export, dépendants de OH, stabilité et humidité | Biais croissant avec âge de masse d’air ; interaction avec nitrate PM2,5 | distance/temps de trajectoire, HNO₃ ou nitrate CAMS, humidité, rayonnement, vent |
| PM2,5 — nitrate d’ammonium | Partition semi-volatile \(NH_3+HNO_3\rightleftharpoons NH_4NO_3\), sensible à température, RH et mélange vertical | Sous/surestimation hivernale et nocturne ; erreur changeant rapidement au réchauffement matinal | CAMS nitrate, NH₃/NH₄⁺, HNO₃ si disponibles ; température, RH, eau liquide aérosol, stabilité |
| PM2,5 — sulfate et chimie aqueuse | Oxydation de SO₂ en phase gazeuse/nuageuse, disponibilité de NH₃ | Erreur pendant brouillard/nuages bas et masses d’air régionales | CAMS sulfate, SO₂, NH₃ ; eau nuageuse, RH, brouillard, trajectoire |
| PM2,5 — aérosol organique secondaire | Oxydation de COV anthropiques/biogéniques ; volatilité dépendant de température | Biais forêt×chaleur×rayonnement ou épisodes de fumée | CAMS OA/SOA ou NMVOC, température, rayonnement, LAI, feux GFAS, CO |
| PM2,5 — primaire et naturel | Chauffage, trafic, feux, poussière, sel marin ; panaches et sources intermittentes | Queues hautes régionales ou locales, erreur dépendant du secteur de vent | composantes CAMS poussière/sel/BC/OM, AOD, feux, émissions sectorielles, trajectoires |
| PM2,5 — dispersion et lessivage | Accumulation sous faible ventilation ; dépôt humide lors des pluies | Erreur croissante avec durée sans pluie et faible couche limite | coefficient de ventilation, cumul pluie, heures depuis pluie, PBLH, vitesse de dépôt prévue |

**Ancrage publié.** CHIMERE représente explicitement chimie gazeuse, thermodynamique des aérosols, émissions et dépôts ; les erreurs restent néanmoins sensibles à la résolution et aux entrées (Mailler et al., 2017, [doi:10.5194/gmd-10-2397-2017](https://doi.org/10.5194/gmd-10-2397-2017)). Le partitionnement du nitrate d’ammonium varie avec température, humidité et mélange vertical (Aan de Brugh et al., 2012, [doi:10.5194/acp-12-3005-2012](https://doi.org/10.5194/acp-12-3005-2012)). Le dépôt d’O₃ dépend notamment de la canopée humide (Zhang et al., 2002, [doi:10.1016/S1352-2310(02)00567-8](https://doi.org/10.1016/S1352-2310(02)00567-8)).

## C2. Couplage NO₂–O₃ : variables à construire maintenant

Il faut travailler en **rapport de mélange molaire**, pas additionner directement des µg/m³ : O₃ et NO₂ n’ont pas la même masse molaire. Convertir les deux champs CAMS en ppb avec température et pression prévues, puis construire :

1. **Oxydant total**
   \[
   O_x=\chi(O_3)+\chi(NO_2).
   \]
   La titration redistribue rapidement O₃ vers NO₂ tout en conservant approximativement \(O_x\) à court terme. Un O₃ faux mais un \(O_x\) correct pointe vers la partition locale ; un \(O_x\) faux pointe vers production, transport ou dépôt.
2. **Fraction de partition**
   \[
   f_{NO_2}=\frac{\chi(NO_2)}{\chi(O_3)+\chi(NO_2)+\varepsilon},
   \qquad
   r=\log\frac{\chi(NO_2)+\varepsilon}{\chi(O_3)+\varepsilon}.
   \]
   Ce sont des indicateurs de titration/urbanité, pas des diagnostics NOₓ-/VOC-limited.
3. **Résumé nocturne** : moyenne et maximum NO₂ entre coucher et lever du soleil, minimum O₃, covariance horaire O₃–NO₂, heure du minimum O₃ et du maximum NO₂.
4. **Résumé diurne** : MDA8 O₃ CAMS, maximum NO₂, amplitude diurne des deux, heure du pic, \(NO_2\times\) rayonnement et \(NO_2/VC\).
5. **Si CAMS NO est accessible** : potentiel de titration \(NO\times O_3\), maximum nocturne de NO et rapport \(NO/NO_2\).
6. **Si HCHO est accessible** : \(FNR=HCHO/NO_2\), avec seuils validés localement. Les seuils de la littérature ne sont pas universels et une colonne satellite n’est pas équivalente à une concentration de surface.

**Effet attendu.**

- Gain le plus probable : **faibles O₃ nocturnes**, stations urbaines/traffic-influenced, transitions aube–crépuscule et maxima horaires NO₂.
- Gain possible mais moins certain : MDA8 O₃ urbaine et sous le vent, par meilleure identification du régime de précurseurs.
- Gain peu justifié avec NO₂ seul : maxima régionaux photochimiques en milieu rural, car COV, rayonnement et transport restent absents.

La littérature utilise \(O_x=O_3+NO_2\) pour séparer le niveau d’oxydant de sa partition locale (Clapp & Jenkin, 2001, [doi:10.1016/S1352-2310(01)00378-8](https://doi.org/10.1016/S1352-2310(01)00378-8)). Le rapport HCHO/NO₂ est un indicateur publié de sensibilité de production, mais sa zone de transition varie selon domaine et méthode (Liu et al., 2021, [doi:10.1021/acs.est.0c07506](https://doi.org/10.1021/acs.est.0c07506)).

## C3. Grandeurs météorologiques dérivées

Les champs doivent provenir d’une **prévision archivée disponible à l’émission** pour un résultat déployable. ERA5 peut uniquement établir un plafond rétrospectif.

### 1. Coefficient de ventilation

\[
VC = H_{\mathrm{PBL}}\ \overline{U}_{\mathrm{PBL}}
\quad [m^2\,s^{-1}],
\]

où \(\overline{U}_{\mathrm{PBL}}\) est idéalement le vent moyen dans la couche mélangée, et non seulement le vent à 10 m. Faible \(VC\) indique accumulation probable de NO₂/PM ; pour O₃, l’effet dépend aussi de la production et du dépôt. Définition publiée : Lu et al. (2012), [doi:10.1007/s11771-012-1047-9](https://doi.org/10.1007/s11771-012-1047-9).

### 2. Stabilité par nombre de Richardson bulk

\[
Ri_b(z)=
\frac{g}{\theta_v(0)}
\frac{\left[\theta_v(z)-\theta_v(0)\right]z}
{u(z)^2+v(z)^2}.
\]

Un \(Ri_b\) positif élevé indique une stratification stable relativement au cisaillement ; calculer maximum nocturne, durée au-dessus d’un seuil et heure de rupture. La valeur critique dépend de la méthode de PBL et ne doit pas être figée sans validation. Formulation et discussion : Zhang et al. (2014), [doi:10.5194/gmd-7-2599-2014](https://doi.org/10.5194/gmd-7-2599-2014).

### 3. Indice de stagnation

Version européenne courante : jour stagnant si les trois conditions sont réunies :

\[
U_{10m}<3.2\ m\,s^{-1},\qquad
U_{500hPa}<13\ m\,s^{-1},\qquad
P_{24h}<1\ mm.
\]

Conserver aussi les trois composantes continues : le booléen jette de l’information. Garrido-Perez et al. trouvent des hausses d’O₃ et PM10 pendant les stagnations euro-méditerranéennes, sans que ces pourcentages soient transférables à votre RMSE ([doi:10.1016/j.scitotenv.2018.07.238](https://doi.org/10.1016/j.scitotenv.2018.07.238)).

### 4. Recirculation et chemin de masse d’air

Sur une fenêtre \(T\), avec vents \(\vec u_i\) et pas \(\Delta t\) :

\[
S=\sum_i\|\vec u_i\|\Delta t,\qquad
D=\left\|\sum_i\vec u_i\Delta t\right\|,\qquad
R=1-\frac{D}{S}.
\]

\(S\) faible décrit la stagnation ; \(R\) proche de 1 un trajet revenant près de son origine. En terrain complexe, ce sont des indices de vent local, pas de vraies trajectoires de panache. Source : Allwine & Whiteman (1994), [doi:10.1016/1352-2310(94)90048-5](https://doi.org/10.1016/1352-2310(94)90048-5).

### 5. Exposition le long d’une rétro-trajectoire

Pour une trajectoire arrière \(x(-\tau)\), construire par secteur source \(s\) :

\[
E_s=\int_0^T q_s(x(-\tau))\,e^{-\tau/\tau_s}\,d\tau,
\]

où \(q_s\) est émission, feu, poussière, mer, forêt ou zone urbaine rencontrée, et \(\tau_s\) une durée de pondération déclarée. Tester plusieurs trajectoires/altitudes ou utiliser la dispersion d’ensemble : une trajectoire unique sous-estime l’incertitude.

### 6. Potentiel photochimique

- cumul de rayonnement court pendant les huit heures précédant le pic ;
- température maximale et nombre d’heures au-dessus d’un seuil défini sur le train ;
- interaction rayonnement×NO₂ et rayonnement×HCHO/NO₂ ;
- angle solaire et durée du jour, plus physiques que le seul jour de l’année.

Il n’existe pas une formule réglementaire unique : ce sont des prédicteurs construits, à valider hors temps.

### 7. Humidité de surface et volatilité

Déficit de pression de vapeur :

\[
VPD=e_s(T)\left(1-\frac{RH}{100}\right),
\quad
e_s(T)\approx0.6108\exp\left(\frac{17.27T}{T+237.3}\right)\ {\rm kPa}.
\]

Le VPD porte mieux que RH seule la demande évaporative et la fermeture stomatique ; pour PM2,5, utiliser séparément température, RH, point de rosée, durée au-dessus de la déliquescence et interaction avec nitrate/NH₃ CAMS.

### 8. Lessivage et mémoire hydrométéorologique

- cumul \(P_{1h},P_{6h},P_{24h}\) ;
- heures depuis \(P>0.2\) ou \(1\) mm ;
- pluie cumulée le long de la trajectoire ;
- indicateur brouillard/nuage bas et eau liquide nuageuse.

Ces variables distinguent dépôt humide, chimie aqueuse et simple humidité élevée.

### 9. Dispersion d’ensemble

À chaque heure/polluant : médiane, IQR, MAD, étendue robuste P90–P10, fraction de membres au-dessus du seuil ; pour le vent, dispersion circulaire de direction. Agréger ensuite ces quantités au grain réglementaire. Une forte dispersion est un indicateur d’incertitude de transport/phase, pas une correction signée.

## C4. Métrologie et représentativité spatiale

La littérature ne traite pas la représentativité comme un rayon fixe universel. Elle est :

- **spécifique au polluant** : NO₂ primaire varie à bien plus courte échelle qu’O₃ ou PM2,5 régional ;
- **spécifique à la statistique** : heure, moyenne annuelle et MDA8 n’ont pas la même aire ;
- **dépendante du régime** : secteur de vent, saison et stabilité changent la zone représentée ;
- **liée au but** : vérification d’un CTM, exposition de population et alerte n’exigent pas le même support.

Les approches publiées utilisent :

1. similitude des séries et cycles temporels pour classer objectivement les sites — Joly & Peuch (2012), [doi:10.1016/j.atmosenv.2011.11.025](https://doi.org/10.1016/j.atmosenv.2011.11.025) ;
2. hétérogénéité des émissions/occupation du sol autour du site — Righini et al. (2014), [doi:10.1016/j.atmosenv.2014.08.015](https://doi.org/10.1016/j.atmosenv.2014.08.015) ;
3. champs CTM et critères de similitude concentrationnelle pour construire une aire, non un cercle — Piersanti et al. (2015), [doi:10.1016/j.apr.2015.04.005](https://doi.org/10.1016/j.apr.2015.04.005) ;
4. classes fond/urbain/altitude fondées sur la topographie, l’occupation du sol et les concentrations — Henne et al. (2010), [doi:10.5194/acp-10-3561-2010](https://doi.org/10.5194/acp-10-3561-2010).

### Comment exploiter cette connaissance

- Décomposer la cible en **erreur commune maille–date** et **écart station–maille**. Le premier terme relève du CTM ; le second du micro-environnement et du changement de support.
- Estimer une variance de représentativité \(\sigma^2_{\rm rep}(polluant,type,saison)\) et l’utiliser pour des IC/poids hétéroscédastiques, pas pour soustraire arbitrairement 3,61 de la RMSE.
- Évaluer séparément stations de fond comparables à CAMS et stations influencées ; ne pas les exclure, mais annoncer deux estimands.
- Utiliser les classes objectives ou un embedding de cycles pour stratifier les plis et vérifier que chaque type est représenté.
- Construire une rose de résidu par station et secteur de vent : une signature fixe indique un support local que le CTM 8 km ne peut résoudre seul.

### Le nombre 3,61 µg/m³

Il est **d’un ordre de grandeur plausible**, mais aucune valeur publiée universelle ne permet de le valider sans connaître polluant, grain, typologies et formule. Une étude de conception de réseaux urbains trouve que le choix d’implantation peut déplacer le NO₂ jusqu’à environ 10 µg/m³ dans des conditions réalistes (Janssen et al., 2015, [doi:10.1016/j.atmosenv.2014.12.067](https://doi.org/10.1016/j.atmosenv.2014.12.067)). Cela rend 3,61 crédible comme dispersion, pas comme borne.

Le bon énoncé est : **« Dans notre réseau et selon notre appariement intra-maille, l’écart station–station vaut 3,61 µg/m³ ; il mélange gradient sous-maille et incertitudes et représente 26 % de la RMSE considérée. »**

# D. Ce qu’il faut arrêter de faire

## 1. Arrêter le détecteur d’anomalies comme mécanisme de repli

Il est aveugle aux deux ruptures documentées (48e et 55e percentiles) et aucune politique ne bat « corriger toujours » ; s’abstenir ajoute 2,60 µg/m³ et un modèle dédié 1,37. Il a rempli son rôle de falsification. Le conserver comme résultat négatif est utile ; continuer à l’optimiser ne porte pas son coût.

## 2. Arrêter de présenter le moniteur de résidu comme alarme opérationnelle

Avec une fausse alarme attendue tous les 20 jours et 10 à 28 jours nécessaires pour accumuler un signal, il est trop lent pour piloter une prévision quotidienne. La moyenne de 259 stations ne réduit pas le mode synoptique commun. Conservez-le comme diagnostic rétrospectif de rupture mensuelle, pas comme brique de déploiement.

## 3. Arrêter d’optimiser le modèle principal sur la validation spatiale

Le réglage spatial gagne 5 points spatialement et en perd 3 temporellement ; le blocage station–mois ne donne que +1,5 %, avec 8 plis négatifs sur 17. Le résultat spatial reste une capacité intéressante, mais ce n’est pas l’objectif de sélection si le produit doit fonctionner demain. Toute sélection finale doit être temporelle/prospective, avec la station exclue comme contrainte secondaire.

## 4. Arrêter l’enrichissement de prédicteurs statiques

Quarante variables environ décrivent déjà paysage et relief ; la généralisation spatiale est forte, la temporelle faible. Le goulot n’est plus une essence forestière ou un rayon supplémentaire, mais l’état atmosphérique absent : copolluants, stabilité, transport et mémoire. Une nouvelle variable statique augmente surtout la complexité et le risque de raccourci spatial.

## 5. Arrêter le critère universel « 0,3 µg/m³ »

Le RMSE varie d’un facteur cinq entre polluants ; une baisse absolue identique n’a ni la même taille d’effet ni la même valeur décisionnelle. Remplacez-le par deux portes conjointes :

- effet normalisé préspécifié, par exemple \(\Delta RMSE/RMSE_{\rm brut}\), avec IC95 > 0 ;
- non-infériorité sur queue et CSI avec marges propres au polluant et au nombre d’événements.

Jusqu’à fixation de ces marges, le critère actuel ne doit plus tuer ni promouvoir une expérience.

# Conclusion

Le projet démontre solidement trois choses : une correction spatiale importante au sein du réseau, un effet de cible sur les maxima reproduisant Bertrand et une meilleure RMSE que le MOS officiel sur 21 stations occitanes au premier semestre 2025. Il ne démontre pas encore une généralisation temporelle robuste, une anticipation des dérives CAMS, ni que le calendrier ou le paysage représentent les mécanismes invoqués.

L’angle scientifique le plus juste n’est pas « davantage de machine learning », mais **séparer trois erreurs** :

\[
\text{résidu observé}
=
\text{erreur d’état/transport du CTM}
+
\text{erreur chimique conditionnelle}
+
\text{changement de support station–maille}
+
\text{bruit de mesure}.
\]

Vos variables statiques expliquent surtout le troisième terme ; le calendrier absorbe une partie des deux premiers sans les identifier. Les copolluants, les régimes de stabilité/ventilation et la dispersion d’ensemble sont les variables qui permettraient enfin de tester cette décomposition.
