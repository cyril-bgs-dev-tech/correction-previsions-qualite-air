# CHIMERE ET PREV’AIR — FICHE SOURCE

## 1. Ce qui est établi et ce qui reste à vérifier

**Établi.** CHIMERE est un modèle eulérien tridimensionnel de chimie-transport, développé depuis 1999 et co-développé institutionnellement par des équipes CNRS/IPSL et l’Ineris pour l’analyse et la prévision de la composition atmosphérique. La publication de référence de la branche 2023 est Menut et al., *The CHIMERE chemistry-transport model v2023r1*, *Geoscientific Model Development*, 17, 5431-5457, 2024. Sources : [Menut et al., 2024](https://doi.org/10.5194/gmd-17-5431-2024) ; [site officiel CHIMERE](https://www.lmd.polytechnique.fr/chimere/).

**Établi.** La version publique courante annoncée par le site officiel est `v2023r3`, publiée en mars 2025. La documentation distribuée est intitulée `CHIMEREdoc_v2023.pdf`. Sources : [site officiel et historique des versions](https://www.lmd.polytechnique.fr/chimere/) ; [documentation v2023](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf).

**À vérifier.** La version exacte de CHIMERE, le jeu d’options, les inventaires, la météorologie, les conditions aux limites, les domaines et résolutions utilisés aujourd’hui dans chaque production PREV’AIR ou Atmo Occitanie ne sont pas déduits de la version publique la plus récente. Une version disponible n’est pas nécessairement la version opérationnelle.

## 2. Équation de continuité et partage des processus

Pour une espèce chimique \(i\), CHIMERE résout numériquement une équation de bilan de masse dont la forme conceptuelle est :

\[
\frac{\partial C_i}{\partial t}
=
-\nabla \cdot (\mathbf{u} C_i)
+ \nabla \cdot (K \nabla C_i)
+ P_i(C,T,J)
- L_i(C,T,J)
+ E_i
- D_i^{sec}
- D_i^{hum}
\]

où \(C_i\) est la concentration, \(\mathbf{u}\) le vent, \(K\) la diffusion turbulente, \(P_i\) et \(L_i\) les productions et pertes chimiques, \(E_i\) les émissions et \(D_i^{sec}\), \(D_i^{hum}\) les dépôts sec et humide. Cette écriture est une synthèse conceptuelle ; l’équation, les coordonnées verticales et les discrétisations exactes doivent être lues dans la documentation de la version exécutée. Sources : [documentation CHIMERE v2023](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf) ; Menut et al., [v2020r1, 2021](https://doi.org/10.5194/gmd-14-6781-2021) et [v2023r1, 2024](https://doi.org/10.5194/gmd-17-5431-2024).

CHIMERE peut intégrer les processus par bilan production/perte ou par séparation d’opérateurs. La publication v2020r1 indique que l’approche production/perte évite l’erreur liée à l’ordre des processus mais impose le pas de temps le plus contraignant ; la séparation d’opérateurs permet des pas distincts et accélère le calcul, au prix d’une dépendance à l’ordre des processus. Source : Menut et al., [2021, section 10.2](https://gmd.copernicus.org/articles/14/6781/2021/gmd-14-6781-2021.html).

## 3. Processus physiques et chimiques représentés

### 3.1 Advection

L’advection horizontale et verticale transporte chaque espèce avec les champs de vent. Les versions récentes proposent plusieurs schémas ; v2020r1 a introduit une stratégie verticale visant à réduire la diffusion numérique excessive, et v2023r1 a actualisé les schémas de transport. Sources : Menut et al., [2021](https://doi.org/10.5194/gmd-14-6781-2021) ; Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024).

**Complément possible.** Une correction apprise peut traiter un biais résiduel spatial ou temporel observé après transport. Elle ne permet pas d’identifier si ce biais vient du vent, du schéma d’advection, des conditions aux limites ou des émissions sans expérience de sensibilité.

### 3.2 Diffusion turbulente et convection

Le mélange turbulent vertical représente les échanges non résolus dans la couche limite ; la convection profonde peut également transporter les traceurs. La formulation de turbulence et le dépôt sec ont été révisés dans v2023r1. Source : Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024).

**Complément possible.** Des variables décrivant relief, stabilité ou hauteur de couche limite peuvent aider une post-correction si le champ météorologique ne représente pas certains effets locaux. Ce gain doit être démontré hors échantillon ; une importance de variable ne prouve pas le mécanisme.

### 3.3 Chimie gazeuse et photolyse

CHIMERE représente plus d’une centaine de réactions et des espèces gazeuses incluant notamment O₃, NO, NO₂ et SO₂ dans les configurations décrites par PREV’AIR. Les mécanismes et options exacts dépendent de la version et de la configuration : **à vérifier** avant de citer un nombre d’espèces ou de réactions pour une production opérationnelle donnée. Sources : PREV’AIR, [fiche CHIMERE](https://www.prevair.org/le-systeme-prevair/des-modeles-de-la-qualite-de-lair/modele-chimere) ; [documentation CHIMERE v2023](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf).

Les taux de photolyse et la chimie O₃–NOₓ–COV sont couplés aux conditions radiatives et météorologiques. Une relation empirique entre forêt, température et ozone ne remplace donc pas le régime chimique complet.

**Complément possible.** Un MOS conditionné par saison, heure et prévision brute peut corriger une erreur systématique de sortie. Il ne doit pas être interprété comme une correction identifiable du mécanisme chimique.

### 3.4 Aérosols

CHIMERE simule des particules primaires et secondaires, avec des espèces inorganiques telles que sulfate, nitrate et ammonium, des aérosols organiques secondaires et des contributions naturelles comme sels marins et poussières minérales. Les distributions en taille, équilibres thermodynamiques, nucléation, coagulation, condensation/évaporation et eau des aérosols dépendent des options de version. Sources : PREV’AIR, [fiche CHIMERE](https://www.prevair.org/le-systeme-prevair/des-modeles-de-la-qualite-de-lair/modele-chimere) ; Menut et al., [2021](https://doi.org/10.5194/gmd-14-6781-2021) ; [documentation v2023](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf).

La branche v2023 utilise une réécriture Fortran 90 d’ISORROPIA pour le partage gaz-particule des aérosols inorganiques, annoncée comme plus stable numériquement que l’ancienne implémentation tout en reproduisant ses résultats de test. Source : Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024).

**Complément possible.** Les mesures de composition chimique, la spéciation et l’apprentissage par régime peuvent aider à distinguer des erreurs compensées dans la masse totale de PM. Une correction de PM₂.₅ seule ne révèle pas quelle composante est erronée.

### 3.5 Dépôt sec

Le dépôt sec retire gaz et particules par interaction avec la surface ; il dépend notamment des propriétés de l’espèce, de la turbulence, de la surface et de la végétation. Le calcul a été révisé dans v2023r1. Sources : Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024) ; [documentation v2023](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf).

**Complément possible.** Des observations de flux, de profils ou de gradients verticaux peuvent mieux contraindre l’évaluation qu’une concentration de surface seule.

### 3.6 Dépôt humide et chimie nuageuse

Le lessivage en nuage et sous le nuage retire les espèces solubles et particulaires ; sa qualité dépend des précipitations forcées et des paramétrisations microphysiques. La formulation exacte de la version opérationnelle est **à vérifier** dans la documentation et le fichier de configuration correspondant. Source : [documentation CHIMERE v2023](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf).

**Complément possible.** L’évaluation par régimes de pluie et par composition des aérosols peut révéler un biais que la RMSE annuelle moyenne masque.

### 3.7 Émissions naturelles et pollens

CHIMERE représente des émissions biogéniques, poussières minérales, sels marins, feux et autres sources naturelles selon les options activées. v2023r1 a ajouté au code officiel l’émission, le transport et le dépôt de pollens de bouleau, ambroisie, olivier et graminées. Source : Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024).

**Complément possible.** Pour Poll’Occ, les observations phénologiques locales et les mesures régionales peuvent compléter une prévision de transport. Les 22 plantes de Poll’Occ ne sont pas toutes couvertes par les quatre types explicitement annoncés dans CHIMERE v2023r1. Sources : Atmo Occitanie, [Poll’Occ, 2026](https://www.atmo-occitanie.org/sites/default/files/publications/2026-03/Dossier%20de%20presse%20pr%C3%A9visions%20pollens%20Atmo%20Occitanie.pdf) ; Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024).

## 4. Modes de couplage météorologique

CHIMERE peut être utilisé hors ligne avec des champs météorologiques pré-calculés ou couplé en ligne avec WRF par OASIS3-MCT. Le couplage en ligne permet notamment de représenter des rétroactions radiatives directes et indirectes des aérosols ; il augmente aussi la dépendance aux choix de configuration. Sources : Menut et al., [v2020r1, 2021](https://doi.org/10.5194/gmd-14-6781-2021) ; Menut et al., [étude du couplage et du nudging, 2024](https://doi.org/10.5194/gmd-17-3645-2024).

PREV’AIR indique que CHIMERE peut être alimenté par ARPEGE, AROME, IFS, WRF ou d’autres modèles. Le forçage effectivement utilisé dans la production consultée est **à vérifier** au niveau de la configuration datée. Source : PREV’AIR, [fiche CHIMERE](https://www.prevair.org/le-systeme-prevair/des-modeles-de-la-qualite-de-lair/modele-chimere).

## 5. Entrées requises

| Famille | Contenu minimal | Point de vigilance |
|---|---|---|
| Météorologie | vent 3D, température, humidité, pression, turbulence/couche limite, nuages, rayonnement, précipitations | résolution, fréquence, biais et cohérence avec le relief ; source exacte **à vérifier** |
| Émissions anthropiques | flux par espèce, secteur, maille et temps | millésime, facteurs, profils temporels, spéciation et projections |
| Émissions naturelles | biogéniques, poussières, sels marins, feux, foudre selon options | forte dépendance à la météo, au sol, à la végétation et aux paramètres |
| Conditions initiales et aux limites | champs chimiques 3D couvrant les espèces requises | transport longue distance et compatibilité des mécanismes |
| Surface | occupation du sol, végétation/LAI, rugosité, sol, topographie | agrégation sous-maille et cohérence temporelle |
| Paramètres chimiques et numériques | mécanisme, photolyse, aérosols, dépôts, schémas et pas de temps | configuration reproductible et versionnée |

Sources générales : [documentation CHIMERE v2023](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf) ; PREV’AIR, [émissions](https://www.prevair.org/le-systeme-prevair/les-donnees-d-entree/emissions) et [conditions aux limites](https://www.prevair.org/le-systeme-prevair/les-donnees-d-entree/conditions-aux-limites).

PREV’AIR indique utiliser, selon les domaines, CAMS-REG à environ 8 km et l’Inventaire national spatialisé à 1 km, avec une description horaire des émissions. Ces chiffres décrivent la page PREV’AIR consultée ; le millésime et les traitements temporels de la production exacte restent **à vérifier**. Source : PREV’AIR, [émissions](https://www.prevair.org/le-systeme-prevair/les-donnees-d-entree/emissions).

## 6. Origine institutionnelle et versions

| Repère | Établi |
|---|---|
| Développement continu | depuis 1999 |
| v2013 | description de référence d’un modèle régional multi-processus : Menut et al., 2013 |
| v2017 | extension des échelles, transport et processus naturels : Mailler et al., 2017 |
| v2020r1 | couplage WRF–CHIMERE, nouvelles options d’aérosols, émissions naturelles, variabilité sous-maille et transport vertical : Menut et al., 2021 |
| v2023r1 | architecture, XIOS, turbulence, dépôt sec, advection, pollens, feux et ISORROPIA : Menut et al., 2024 |
| v2023r3 | version publique courante annoncée en mars 2025 |

Sources : Menut et al., [CHIMERE 2013](https://doi.org/10.5194/gmd-6-981-2013), Mailler et al., [CHIMERE-2017](https://doi.org/10.5194/gmd-10-2397-2017), Menut et al., [v2020r1](https://doi.org/10.5194/gmd-14-6781-2021), Menut et al., [v2023r1](https://doi.org/10.5194/gmd-17-5431-2024), [site officiel CHIMERE](https://www.lmd.polytechnique.fr/chimere/).

L’étiquette institutionnelle doit rester précise : la page PREV’AIR parle d’un co-développement CNRS–Ineris ; la publication v2023r1 associe LMD, LISA, CEREA et LSCE ; le site officiel indique un outil national de l’INSU. Ces formulations ne sont pas interchangeables sans contexte. Sources : PREV’AIR, [fiche CHIMERE](https://www.prevair.org/le-systeme-prevair/des-modeles-de-la-qualite-de-lair/modele-chimere) ; Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024) ; [site officiel](https://www.lmd.polytechnique.fr/chimere/).

## 7. PREV’AIR : rôle, production et horizons

PREV’AIR est la plateforme nationale de prévision et de cartographie de la qualité de l’air. Elle exécute quotidiennement CHIMERE et MOCAGE et calcule des champs horaires d’O₃, NOₓ et particules sur des maillages France et Europe. Source : PREV’AIR, [production des prévisions](https://www.prevair.org/le-systeme-prevair/la-production/previsions).

La plateforme indique actuellement produire des jours J−1 à J+5 et plus d’une douzaine de prévisions quotidiennes, dont près d’une dizaine sur la France. La résolution précise de chaque chaîne actuelle est **à vérifier** : la page de production ne la publie pas avec une configuration datée. Source : PREV’AIR, [prévisions](https://www.prevair.org/le-systeme-prevair/la-production/previsions).

PREV’AIR ne diffuse pas seulement les sorties brutes :

- une correction statistique par apprentissage est appliquée aux prévisions brutes d’O₃, NO₂, PM₁₀ et PM₂.₅ ;
- cette adaptation combine modèle déterministe et information statistique aux stations jusqu’à J+5 ;
- les valeurs aux stations sont spatialisées par krigeage pour produire des cartes horaires ou journalières ;
- les analyses de la veille combinent CHIMERE et stations de fond par krigeage avec dérive.

Sources : PREV’AIR, [prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees) et [analyses](https://www.prevair.org/le-systeme-prevair/la-production/analyses).

**Conséquence pour un candidat.** Un projet de MOS sur CAMS brut est un prototype pertinent pour montrer une méthode, mais il n’est pas une comparaison avec l’état de l’art opérationnel français tant qu’il n’est pas évalué contre PREV’AIR corrigé ou la chaîne régionale effectivement utilisée.

## 8. Limites structurelles publiées, formulées comme compléments possibles

### 8.1 Échelles sous-maille

Les CTM régionaux tels que CHIMERE ne résolvent pas explicitement les processus physiques et chimiques sous l’échelle de leur maille ; Menut et al. indiquent que les modèles régionaux ne résolvent pas les processus sous 1 km². Source : Menut et al., [2021](https://doi.org/10.5194/gmd-14-6781-2021).

**Complément possible.** Une descente d’échelle, une LUR ou des modèles de rue peuvent représenter les gradients de proximité, à condition d’être validés sur des stations et zones non vues.

### 8.2 Diffusion numérique du transport

Les schémas d’advection introduisent une diffusion numérique ; la branche v2020r1 a ajouté un schéma vertical antidiffusif et rapporte une réduction de l’excès de diffusion verticale ainsi qu’une amélioration du biais d’ozone au sol. Source : Menut et al., [2021](https://doi.org/10.5194/gmd-14-6781-2021).

**Complément possible.** Des profils verticaux, lidars et ozonesondes évaluent mieux ce point que les seules stations de surface.

### 8.3 Dépendance aux forçages

Les résultats dépendent de la météorologie, des émissions et des conditions initiales et aux limites. La validation v2023r1 montre que les scores diffèrent selon le forçage ECMWF, WRF hors ligne ou WRF couplé. Source : Menut et al., [2024](https://doi.org/10.5194/gmd-17-5431-2024).

**Complément possible.** Ensembles multi-forçages, analyses de sensibilité et propagation d’incertitude permettent de séparer robustesse du modèle et robustesse d’une configuration.

### 8.4 Inventaires et profils temporels

PREV’AIR construit des émissions horaires à partir d’inventaires spatialisés et met régulièrement à jour les données anthropiques selon les déclarations annuelles. Toute erreur d’activité, facteur, spéciation ou profil se transmet à la concentration. Source : PREV’AIR, [émissions](https://www.prevair.org/le-systeme-prevair/les-donnees-d-entree/emissions).

**Complément possible.** Données locales de trafic, chauffage, industrie et agriculture, ainsi que contrôles de cohérence avec l’inventaire régional, peuvent réduire les incertitudes là où elles sont documentées. Une correction des concentrations n’attribue pas à elle seule l’erreur à l’inventaire.

### 8.5 Conditions aux limites et transport longue distance

Un domaine régional reçoit des masses d’air dont la composition est fournie par un modèle à plus grande échelle. PREV’AIR utilise largement des prévisions globales Copernicus pour ces conditions. Source : PREV’AIR, [conditions aux limites](https://www.prevair.org/le-systeme-prevair/les-donnees-d-entree/conditions-aux-limites).

**Complément possible.** Ensembles de conditions aux limites et observations de profils ou de télédétection sont particulièrement utiles pour ozone, poussières désertiques et feux.

### 8.6 Compromis précision–coût numérique

La séparation d’opérateurs accélère le calcul mais introduit une dépendance à l’ordre des processus ; le bilan production/perte est plus coûteux mais évite cette erreur de séparation. Source : Menut et al., [2021, section 10.2](https://gmd.copernicus.org/articles/14/6781/2021/gmd-14-6781-2021.html).

**Complément possible.** Une configuration rapide pour la prévision peut être accompagnée d’analyses de référence plus coûteuses afin de quantifier le compromis.

### 8.7 Évaluation de surface et représentativité des stations

PREV’AIR évalue ses prévisions contre les mesures des AASQA avec biais, RMSE et corrélation ; pour les évaluations publiées sur la page consultée, seules les stations de fond avec plus de 75 % de données valides sont retenues. Source : PREV’AIR, [évaluations](https://www.prevair.org/le-systeme-prevair/la-production/evaluations).

**Complément possible.** Une évaluation par typologie, régime, concentration, saison, horizon et zone, assortie d’intervalles d’incertitude, évite qu’un score global masque une faiblesse opérationnelle.

### 8.8 Sortie déterministe et décision

Les champs d’un membre de modèle sont déterministes conditionnellement à leur configuration, tandis que PREV’AIR exploite plusieurs modèles et sources afin d’apprécier l’incertitude des jours à venir. Source : PREV’AIR, [prévisions](https://www.prevair.org/le-systeme-prevair/la-production/previsions).

**Complément possible.** Ensembles, calibration probabiliste et probabilités de dépassement peuvent mieux représenter le risque. Leur qualité doit être évaluée par calibration et score probabiliste, pas seulement par RMSE.

## 9. Points à ne pas affirmer devant un expert

- « PREV’AIR est à 2 km » : **à vérifier** pour le domaine, la date et le produit exacts.
- « PREV’AIR utilise telle version de CHIMERE » : **à vérifier** dans une fiche de configuration datée.
- « CHIMERE a exactement N espèces et M réactions » : **à vérifier** selon mécanisme et options.
- « Une erreur presque constante entre J+1 et J+3 vient nécessairement du modèle et non de la météo » : non établi par cette seule observation.
- « Le MOS est nouveau dans PREV’AIR » : faux au niveau du principe ; PREV’AIR publie déjà des prévisions corrigées par apprentissage. Source : [PREV’AIR](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees).
- « Une classe ATMO Mauvais est un épisode » : faux juridiquement. Sources : [arrêté du 10 juillet 2020](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042164835/2026-07-21) et [arrêté du 7 avril 2016](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31).
- « Une importance de variable prouve un mécanisme physique » : non établi.
- « La version publique la plus récente est la version opérationnelle » : **à vérifier**.

## 10. Références primaires à connaître

1. Menut, L. et al. (2013), *CHIMERE 2013: a model for regional atmospheric composition modelling*, *Geosci. Model Dev.*, 6, 981-1028. [DOI](https://doi.org/10.5194/gmd-6-981-2013).
2. Mailler, S. et al. (2017), *CHIMERE-2017: from urban to hemispheric chemistry-transport modeling*, *Geosci. Model Dev.*, 10, 2397-2423. [DOI](https://doi.org/10.5194/gmd-10-2397-2017).
3. Menut, L. et al. (2021), *The CHIMERE v2020r1 online chemistry-transport model*, *Geosci. Model Dev.*, 14, 6781-6811. [DOI](https://doi.org/10.5194/gmd-14-6781-2021).
4. Menut, L. et al. (2024), *The CHIMERE chemistry-transport model v2023r1*, *Geosci. Model Dev.*, 17, 5431-5457. [DOI](https://doi.org/10.5194/gmd-17-5431-2024).
5. CHIMERE (2025), *CHIMERE Chemistry-Transport Model v2023*, documentation de la branche incluant v2023r3. [PDF](https://www.lmd.polytechnique.fr/chimere/docs/CHIMEREdoc_v2023.pdf).
6. PREV’AIR, pages institutionnelles sur [CHIMERE](https://www.prevair.org/le-systeme-prevair/des-modeles-de-la-qualite-de-lair/modele-chimere), les [prévisions](https://www.prevair.org/le-systeme-prevair/la-production/previsions), les [prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees), les [analyses](https://www.prevair.org/le-systeme-prevair/la-production/analyses) et les [évaluations](https://www.prevair.org/le-systeme-prevair/la-production/evaluations).
