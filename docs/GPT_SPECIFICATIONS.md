# Spécifications exécutables — post-traitement CAMS Europe

## Deux corrections de cadrage avant les livrables

La lecture « une correction n’ajoute de valeur que là où le modèle amont est aveugle à lui-même » est utile comme règle d’allocation de l’effort, mais trop absolue comme conclusion scientifique. Le résultat nul des co-polluants et des transformations chimiques signifie seulement qu’ils n’ajoutent pas d’information **conditionnellement aux variables, à la cible, à la perte et aux 17 mois testés** ; il ne démontre pas que CAMS connaît toutes ses erreurs chimiques. En revanche, les deux directions retenues — erreur du forçage météorologique et différence de support station–maille — sont bien les deux priorités empiriquement justifiées par les ablations.

Deux formulations de la mission doivent aussi être corrigées :

1. l’IFS temps réel ouvert n’est pas une archive historique ADS/CDS : l’ECMWF ne conserve publiquement que les 12 derniers runs, soit environ 2–3 jours ; l’archive opérationnelle historique est dans MARS et requiert un droit d’accès ou un Service Agreement ([ECMWF Open Data, consulté le 30 juillet 2026](https://www.ecmwf.int/en/forecasts/datasets/open-data), [ECMWF, accès aux archives](https://www.ecmwf.int/en/forecasts/accessing-forecasts/order-historical-datasets)) ;
2. aucune décomposition sur le seul réseau réglementaire ne peut prouver un plancher absolu « qu’aucune méthode ne franchira ». Elle peut seulement estimer un **plancher conditionnel à un jeu d’information, à un type de station et à une métrique**, après retrait explicite de l’incertitude de mesure.

# Livrable 1 — Jeu météorologique IFS opérationnel

## 1. Contrat de disponibilité et convention temporelle

La chaîne utilise le run IFS déterministe dont `reference_time` est le plus récent tout en étant **antérieur ou égal à l’heure réelle d’émission CAMS**. Elle refuse un champ si son `reference_time`, son `valid_time`, son `step`, son unité ou son cycle IFS manque. Les champs ouverts sont en GRIB2 à 0,25° ; les runs 00/12 UTC offrent des pas de 3 h jusqu’à 144 h, donc couvrent J+1 à J+3 ([catalogue ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)). L’accès historique 2023–2024 est un prérequis séparé : MARS, convention de diffusion, ou copie opérationnelle déjà conservée.

La journée réglementaire est `[00:00, 24:00[` en heure locale `Europe/Paris`. Elle contient 23, 24 ou 25 heures aux changements d’heure ; aucune duplication artificielle n’est faite. Les instants IFS restent en UTC, sont interpolés bilinéairement à la station, puis convertis en temps local. Les grandeurs instantanées à 3 h sont intégrées par morceaux linéaires ; les cumuls IFS sont d’abord désaccumulés entre deux pas successifs du **même run**, puis répartis sur leur intervalle. Une différence de cumul comprise entre `−1e-6` et `0` est ramenée à zéro ; une valeur plus négative invalide le jour. Cette précaution suit la documentation ECMWF sur les paramètres accumulés et leurs petits artefacts numériques ([ECMWF, conversion des variables accumulées, 2026](https://confluence.ecmwf.int/spaces/CKB/pages/197702790/Conversion%2Btable%2Bfor%2Baccumulated%2Bvariables%2Btotal%2Bprecipitation%2Bfluxes)).

Pour O₃, NO₂ et PM2,5, les agrégats météo couvrent la journée civile de la cible. Pour O₃, on ajoute les mêmes agrégats sur la fenêtre de 8 h qui réalise le maximum glissant CAMS brut ; c’est une information disponible à l’émission, non une fenêtre choisie avec l’observation. Si plusieurs fenêtres CAMS sont ex æquo, retenir la première.

## 2. Champs directs à extraire

Tous les champs de cette table existent en prévision déterministe IFS à J+1–J+3 dans le catalogue ouvert au 30 juillet 2026 ; aucun champ ERA5 n’entre dans la chaîne.

| champ produit | nom IFS / identifiant | niveau | agrégation quotidienne exacte | polluant(s) | mécanisme porté |
|---|---|---:|---|---|---|
| `t2m_mean`, `t2m_min`, `t2m_max`, `t2m_tmax` | `2t` / 167 | surface, 2 m | moyenne pondérée par le temps, minimum, maximum, heure locale du premier maximum | O₃, PM2,5, NO₂ | photochimie, volatilité, chauffage et couche stable ; le maximum et son heure priment pour O₃ |
| `td2m_mean`, `td2m_min` | `2d` / 168 | surface, 2 m | moyenne et minimum pondérés par le temps | PM2,5, O₃ | humidité disponible ; utilisé surtout pour VPD et humidité relative |
| `u10_mean`, `v10_mean`, `ws10_mean`, `ws10_p10`, `ws10_max` | `10u` / 165, `10v` / 166 | surface, 10 m | moyennes vectorielles de `u,v`; moyenne, 10e centile pondéré et maximum de `sqrt(u²+v²)` | tous | transport moyen, stagnation et dispersion des sources locales |
| `u100_mean`, `v100_mean`, `ws100_mean` | `100u` / 228246, `100v` / 228247 | surface, 100 m | mêmes règles que pour 10 m | tous | cisaillement bas et transport au-dessus de la rugosité |
| `tp_sum`, `tp_max3h`, `wet_hours` | `tp` / 228 | surface | cumul désaccumulé en mm, maximum sur 3 h, durée des intervalles avec taux ≥ 0,1 mm h⁻¹ | PM2,5, NO₂ | lessivage et remise à zéro de l’accumulation |
| `ssrd_sum`, `ssrd_max3h`, `ssrd_t50` | `ssrd` / 169 | surface | cumul désaccumulé en MJ m⁻², maximum du flux moyen sur 3 h en W m⁻², heure où 50 % du cumul est atteint | O₃, PM2,5 | photolyse et chauffage convectif ; le cumul porte la dose, le maximum l’intensité |
| `tcc_mean`, `tcc_min` | `tcc` / 164 | surface | moyenne et minimum, bornés à `[0,1]` | O₃ | atténuation radiative non parfaitement résumée par le cumul journalier |
| `sp_mean` | `sp` / 134 | surface | moyenne en Pa | tous | conversion humidité et sélection des niveaux réellement au-dessus du sol |
| `t_p`, `q_p`, `u_p`, `v_p`, `z_p` | `t`/130, `q`/133, `u`/131, `v`/132, `z`/129 | 1000, 925, 850, 700 et 500 hPa | aucun agrégat direct : calcul instantané des profils, puis agrégation des diagnostics | tous | stabilité, hauteur de mélange approximée, ventilation et vent libre |

`blh` n’est **pas** dans le sous-ensemble IFS Open Data listé par l’ECMWF. Il ne doit donc pas être demandé silencieusement. Si un contrat ECMWF donne accès au paramètre 159, une variante contrôlée peut remplacer la hauteur dérivée ci-dessous, mais elle constitue un autre produit et doit être réévaluée séparément.

## 3. Variables dérivées obligatoires

### 3.1 Humidité relative et déficit de pression de vapeur

Pour chaque instant, avec `T` et `Td` en °C :

```text
e_s(T)  = 0.6108 × exp(17.27 T  / (T  + 237.3))   [kPa]
e_a     = 0.6108 × exp(17.27 Td / (Td + 237.3))   [kPa]
RH      = 100 × e_a / e_s(T)                      [%]
VPD     = max(0, e_s(T) − e_a)                    [kPa]
```

Produire `rh_mean`, `rh_max`, `vpd_mean` et `vpd_max`; pour O₃, produire aussi `vpd_mean_cams_mda8`. La formule est celle de FAO-56 ([Allen et al., 1998, FAO Irrigation and Drainage Paper 56](https://www.fao.org/4/X0490E/x0490e07.htm)). Échec d’implémentation si `RH` sort de `[0,105] %` avant la seule tolérance numérique ou si `VPD < 0`.

### 3.2 Hauteur de mélange par Richardson bulk

Ce diagnostic est une approximation opérationnelle rendue nécessaire par l’absence de `blh` dans le flux ouvert. À chaque pas :

```text
θv,k = Tk × (100000 / pk)^(Rd/cp) × (1 + 0.61 qk)
RiB,k = (g / θv,s) × (θv,k − θv,s) × (zk − zs)
        / ((uk − u10)² + (vk − v10)² + 0.1)
```

avec `Rd/cp = 0,2854`, `g = 9,80665 m s⁻²`, pressions en Pa, températures en K, `q` en kg kg⁻¹ et hauteurs géopotentielles en m (`z/g` si le GRIB contient un géopotentiel). Le niveau de surface virtuel est calculé avec `2t`, `2d`, `sp`, `10u`, `10v`. Ignorer tout niveau où `p ≥ 0,98 sp`. `Hmix` est l’altitude relative de la première traversée linéaire de `RiB = 0,25`; ce seuil est le choix fixé pour le protocole, cohérent avec la valeur critique courante et avec les valeurs 0,24–0,39 publiées selon le régime par Zhang et al. ([2014, DOI 10.5194/gmd-7-2599-2014](https://doi.org/10.5194/gmd-7-2599-2014)).

Si aucune traversée n’apparaît avant 700 hPa, fixer `Hmix = z700 − zs` et `hmix_censored = 1`; si moins de deux niveaux sont valides, mettre le diagnostic manquant, sans imputation. Produire `hmix_min`, `hmix_mean`, `hmix_max` et `hmix_at_06_local`. Échec si une hauteur non censurée est ≤ 0 ou si l’interpolation utilise un niveau sous le sol.

### 3.3 Coefficient de ventilation

À chaque pas, calculer la vitesse moyenne dans la couche `[zs, zs + Hmix]` par intégration trapézoïdale des profils `u,v`, incluant le point 10 m :

```text
Ubar = (1 / Hmix) × ∫[0,Hmix] sqrt(u(z)² + v(z)²) dz   [m s⁻¹]
VC   = Hmix × Ubar                                      [m² s⁻¹]
```

Produire `vc_min`, `vc_p10`, `vc_mean` et `vc_at_06_local`. Le produit hauteur de mélange × vent moyen de couche est la définition publiée du coefficient de ventilation ([Sujatha et al., 2016, DOI 10.1080/23311843.2015.1125284](https://doi.org/10.1080/23311843.2015.1125284)). Cibles : PM2,5 et NO₂ en priorité, O₃ en second. Échec si `VC < 0`, si des hauteurs censurées sont mélangées aux non censurées sans indicateur, ou si le vent 10 m seul est présenté comme vent moyen de couche.

### 3.4 Stabilité basse couche

Produire trois diagnostics :

```text
Δθv_925 = θv,925 − θv,s                         [K]
shear_10_925 = sqrt((u925−u10)²+(v925−v10)²)
RiB_925 = formule de la section 3.2 au niveau 925 hPa
```

Agrégats : maximum nocturne sur `[20:00, 08:00[` local, moyenne diurne et nombre d’heures où `RiB_925 ≥ 0,25`. Si 925 hPa est sous le sol, utiliser 850 hPa et suffixer la variable `_850`; ne jamais imputer 925 par 850 sous le même nom. Cibles : NO₂ et PM2,5 ; O₃ pour la destruction nocturne et la remise en mélange matinale.

### 3.5 Stagnation

Un jour est stagnant si les trois conditions sont vraies :

```text
mean(ws10) < 3,2 m s⁻¹
mean(ws500) < 13 m s⁻¹
tp_sum < 1,0 mm
```

Produire `stagnant_day ∈ {0,1}` et `stagnant_run`, nombre de jours stagnants consécutifs se terminant au jour cible, plafonné à 7. Ces seuils sont ceux appliqués et vérifiés pour l’Europe par Garrido-Pérez et al. ([2018, DOI 10.1016/j.scitotenv.2018.07.238](https://doi.org/10.1016/j.scitotenv.2018.07.238)). Cibles : PM2,5 et NO₂, puis O₃. Au démarrage sans historique, `stagnant_run` est manquant, pas zéro.

### 3.6 Temps sec et accumulation depuis la dernière pluie

Un intervalle est « mouillé » si son taux moyen atteint `0,1 mm h⁻¹`. À chaque émission, maintenir un état versionné `last_wet_valid_time` alimenté uniquement par les runs IFS déjà disponibles. Produire :

```text
dry_hours = min(168, valid_day_end − last_wet_valid_time)   [h]
dry_load  = Σ exp(−Δt/72 h) × max(0, 0.1 − rain_rate) × Δt
```

où la somme porte sur les 168 h précédant la fin du jour cible et `rain_rate` est en mm h⁻¹. `dry_load` est un indice sans unité après division par `0,1 mm`; il donne davantage de poids aux 72 dernières heures. Les seuils `0,1 mm h⁻¹`, 72 h et 168 h sont des **choix de conception à valider**, non des constantes publiées. Cibles : PM2,5 d’abord, NO₂ ensuite. Si l’état historique couvre moins de 168 h, produire `dry_history_hours` et laisser `dry_load` manquant tant que la couverture est < 72 h.

### 3.7 Directions : aucune moyenne d’angle

Conserver `u` et `v`; ne jamais moyenner des degrés. Pour tout axe de relèvement `α` mesuré dans le sens horaire depuis le nord, définir :

```text
along(α) = u sin(α) + v cos(α)
cross(α) = u cos(α) − v sin(α)
```

Les agrégats sont pondérés par la vitesse : `Σ ws × projection / Σ ws`; si `Σ ws < 1 m s⁻¹` sur le jour, les projections sont manquantes et `calm_day = 1`.

- `onshore`: prendre `αsea`, relèvement station→point côtier le plus proche, puis `onshore = −along(αsea)` ; positif signifie un flux venant de la mer. Cible : O₃ et PM2,5.
- `valley_along`, `valley_cross`: utiliser l’axe de vallée non orienté ; fournir `abs(along)` et `abs(cross)`. Cibles : NO₂ et PM2,5.
- `road_crosswind`: pour la route principale la plus proche d’axe `αroad`, utiliser `abs(cross(αroad))` — de façon équivalente, `abs(along(αroad + 90°))` ; ajouter `station_downwind = 1` lorsque le vecteur vent transporte l’air de la route vers la station. Cible : NO₂.

Les axes statiques doivent être calculés une fois, stockés en degrés avec leur méthode et leur version. Échec si une direction est moyennée en degrés, si les vents calmes reçoivent arbitrairement un angle, ou si le signe « onshore » n’est pas testé sur quatre vents cardinaux.

## 4. Les six variables à implémenter d’abord

Ordre imposé pour l’ablation :

1. `t2m_max` ;
2. `ssrd_sum` ;
3. `vpd_max` ;
4. `vc_p10` ;
5. `stagnant_day` ;
6. `dry_hours`.

Il s’agit de six **sorties scalaires**, même si leur calcul requiert plusieurs champs IFS. L’hypothèse de planification est qu’elles récupèrent **70 % du plafond O₃ de +7,8 %, soit +5,5 points de gain relatif de RMSE**. Ce 70 % est un jugement de conception, pas une valeur publiée. Il est invalidé si l’ablation prospective, sur les mêmes lignes et plis que le modèle sans météo, donne un gain inférieur à `+3,9 points` (50 % du plafond) ou un IC95 par bootstrap station × blocs temporels qui contient zéro.

La comparaison ERA5–IFS doit enfin porter sur les mêmes six sorties et les mêmes lignes. Si l’IFS récupère moins de la moitié de l’ablation ERA5, la première cause à examiner est l’écart **prévision–réanalyse**, pas le gradient boosting.

# Livrable 2 — Décomposition de la dispersion intra-maille

## 1. Estimand et population

Le protocole estime, séparément par polluant et grandeur réglementaire, l’écart-type journalier entre deux stations comparables d’une même maille CAMS 0,1° qui demeure après retrait des effets observables et de l’incertitude de mesure. Il ne mélange jamais O₃ max 8 h, NO₂ max horaire et PM2,5 moyenne journalière.

L’analyse primaire porte sur les stations de fond, séparées en trois strates : urbaines, suburbaines et rurales. Les stations trafic et industrielles sont exclues du primaire et analysées dans des annexes distinctes. Cette séparation suit la classification réglementaire EEA des stations ([EEA, classification des stations, consultée le 30 juillet 2026](https://www.eea.europa.eu/en/topics/in-depth/air-pollution/monitoring-station-classifications-and-criteria/)).

## 2. Constitution des paires comparables

Une paire `(i,j)` est admissible si toutes les conditions suivantes sont vraies :

1. même polluant, même grandeur et même date locale, avec le même critère de complétude ;
2. même identifiant de maille CAMS obtenu par indexation, pas par arrondi des coordonnées ;
3. même strate fond urbain/suburbain/rural ;
4. distance horizontale entre `0,5 et 12 km` ;
5. différence d’altitude absolue ≤ `50 m` ;
6. aucune relocalisation de l’une des stations pendant la période ;
7. au moins `60` jours simultanés, couvrant au moins `4` mois civils et au moins `15` jours par saison météorologique présente.

Les valeurs 0,5 km, 12 km, 50 m, 60 jours et 15 jours sont des **choix de protocole préenregistrés**, non des normes publiées. Les sensibilités obligatoires sont : altitude 25/100 m, distance maximale 8 km, et suppression du filtre de typologie. Si moins de 30 mailles contiennent une paire primaire, le protocole conclut « effectif insuffisant » et n’emploie pas le mot plancher.

## 3. Modèle statistique explicite

Pour la station `s`, la maille `c` et le jour `t` :

```text
y_cst = μ_ct + X_st β + a_cs + q_cst + ε_cst

a_cs ~ N(0, σ_site²)
q_cst = ρ q_cs,t−1 + η_cst
Cov(η_cst, η_cs't) = σ_dyn² × exp(−d_ss' / ℓ)
ε_cst ~ N(0, u_cst²)
```

- `μ_ct` est l’état commun maille–jour et est absorbé par un effet fixe `maille × date`.
- `X_st` contient seulement des différences observables préenregistrées : altitude, densité de bâti, distance et hiérarchie routière, population, relief, forêt, `onshore`, `valley_cross`, stabilité et ventilation IFS.
- `a_cs` est l’effet stationnaire de micro-environnement non expliqué.
- `q_cst` est l’écart sous-maille variable dans le temps, AR(1) et corrélé spatialement.
- `ε_cst` est l’erreur de mesure, avec variance `u_cst²` fournie par des duplications/co-localisations ou par la chaîne métrologique de la station.

Le modèle est ajusté par maximum de vraisemblance restreint ; les effets fixes sont appris en validation croisée leave-one-cell-out. La quantité annoncée est :

```text
σ_support = sqrt(σ_site² + σ_dyn²)                   [µg m⁻³]
σ_obs     = sqrt(σ_site² + σ_dyn² + median(u²))      [µg m⁻³]
```

Le diagnostic non paramétrique obligatoire vérifie le modèle avec les différences de paires :

```text
d_ijt = y_cit − y_cjt
σ_pair = sqrt( 0.5 × Var(d_ijt − ΔX_ijt β) )
```

`σ_pair` et `σ_support` doivent différer de moins de 20 % ; sinon la décomposition est déclarée instable.

### Limite d’identifiabilité

Sans duplications/co-localisations ou budget d’incertitude station–jour, `σ_dyn²` et `u²` ne sont pas identifiables séparément. Dans ce cas, publier seulement `σ_support+mesure`, une **borne supérieure** du support, et interdire le mot plancher. Les objectifs réglementaires d’incertitude maximale ne doivent pas être substitués à la variance instrumentale réellement observée.

## 4. Rééchantillonnage et incertitude

Employer un bootstrap hiérarchique à 2 000 réplications :

1. tirer les mailles avec remise ;
2. dans chaque maille tirée, conserver toutes ses stations et toutes ses paires ;
3. tirer avec remise des blocs calendaires contigus de 7 jours, communs à toutes les mailles, jusqu’à reconstituer la période ;
4. réajuster intégralement le modèle, y compris la sélection de `β`.

La maille, et non la paire, est l’unité spatiale primaire ; le bloc synoptique de 7 jours est l’unité temporelle. Rapporter médiane, IC95 percentile, distribution par saison et par strate. Une réplication qui perd une strate ou ne converge pas est invalide ; si plus de 5 % des réplications sont invalides, aucune conclusion de plancher n’est admise.

## 5. Décision sur le mot « plancher »

Le terme autorisé ne peut être que :

> **plancher conditionnel de représentativité, pour une station de fond de type X, une maille de 0,1°, ce polluant, cette grandeur et les prédicteurs disponibles**.

Il est autorisé seulement si les quatre critères sont simultanément vérifiés :

1. la borne basse IC95 de `σ_support` est strictement positive ;
2. elle varie de moins de 20 % dans toutes les sensibilités distance/altitude ;
3. un modèle enrichi préenregistré avec météo directionnelle et covariables fines ne réduit pas `σ_support` de plus de 10 % en leave-one-cell-out ;
4. `σ_support` est reproduit, à ±20 %, sur une seconde année ou sur 2025 Occitanie gelé.

Le mot est interdit pour ce dossier si l’erreur de mesure n’est pas séparée, si l’une des sensibilités réduit l’estimation de plus de 20 %, si l’IC95 inclut zéro, ou si la validation externe ne reproduit pas l’ordre de grandeur. Il est interdit **définitivement pour la valeur 3,61 µg m⁻³ actuelle** dès lors que cette valeur mélange les types de stations ou ne corrige pas la dépendance des paires ; une nouvelle estimation pourrait seulement établir un plancher conditionnel différent.

## 6. Comparaison bibliographique

Il n’existe pas une valeur européenne universelle en µg m⁻³ pour la représentativité d’une station de fond. L’intercomparaison FAIRMODE/AQUILA conclut précisément à l’absence d’une définition et d’une méthode unifiées ([JRC, 2017, DOI 10.2760/60611](https://doi.org/10.2760/60611)). Les comparaisons publiées portent surtout sur des **aires** ou sur des seuils de similarité :

- Piersanti et al. trouvent, sur une grille de 4 × 4 km en Italie, environ **1 440 km²** pour un exemple O₃ rural de vallée, **800 km²** et **224 km²** pour deux exemples PM2,5 ruraux ; ces valeurs sont des exemples dépendant du site et du polluant, pas des seuils européens ([2015, DOI 10.1016/j.apr.2015.04.005](https://doi.org/10.1016/j.apr.2015.04.005)).
- En Espagne, la surface représentative des stations rurales varie fortement avec le polluant, le seuil réglementaire et l’année ; environ **50 %** des stations rurales O₃ se recouvrent sur au moins **80 %** de leur aire représentative ([Martín et al., 2014, DOI 10.5094/APR.2014.087](https://doi.org/10.5094/APR.2014.087)).
- Henne et al. identifient six groupes de stations de fond européennes ; ces groupes expliquent **50 à 80 %** de la variabilité inter-stations des médianes et écarts-types de NO₂ et O₃, ce qui montre l’importance de la typologie plutôt qu’un bruit additif unique ([2010, DOI 10.5194/acp-10-3561-2010](https://doi.org/10.5194/acp-10-3561-2010)).
- Pour le PM2,5 dans un petit domaine urbain, Yatkin et al. utilisent un écart de **25 %** et montrent qu’une station peut ne pas représenter de nombreux sites voisins ([2020, DOI 10.1016/j.apr.2019.10.004](https://doi.org/10.1016/j.apr.2019.10.004)).

Conclusion : **3,61 µg m⁻³ est plausible comme dispersion descriptive**, mais sa cohérence ne peut pas être affirmée ou infirmée par ces publications, qui n’emploient ni le même estimand ni toujours la même grandeur temporelle. Le présenter comme valeur européenne publiée serait faux ; le présenter comme estimation brute propre au réseau et à la période est défendable.

# Livrable 3 — `rolling-origin` strict

## 1. Plis temporels

La période disponible va d’août 2023 à décembre 2024. Fixer un échauffement de **12 mois complets** pour couvrir un cycle saisonnier, puis évaluer cinq origines mensuelles :

| origine | entraînement croissant | test |
|---|---|---|
| 1 | 2023-08-01 → 2024-07-28 | août 2024 |
| 2 | 2023-08-01 → 2024-08-28 | septembre 2024 |
| 3 | 2023-08-01 → 2024-09-27 | octobre 2024 |
| 4 | 2023-08-01 → 2024-10-28 | novembre 2024 |
| 5 | 2023-08-01 → 2024-11-27 | décembre 2024 |

Le retrait de trois jours avant le mois test est un embargo conservateur couvrant J+3 et une latence d’observation non documentée. Si chaque ligne possède `available_at`, remplacer cet embargo par la règle exacte `available_at <= issue_time`; ne jamais faire les deux. Le modèle est figé pour tout le mois test. Cette évaluation à origine roulante suit le principe d’évaluation hors échantillon temporelle de Tashman ([2000, DOI 10.1016/S0169-2070(00)00065-0](https://doi.org/10.1016/S0169-2070(00)00065-0)).

## 2. Stations cachées sans perte finale d’effectif

Construire une seule fois cinq plis de stations, séparément par polluant, avec un algorithme glouton déterministe équilibrant : région, typologie, altitude en quartiles et nombre de jours valides. Une station appartient au même pli pour les cinq mois et les trois échéances.

Pour chaque mois `m` et pli station `k` :

- entraîner sur les dates antérieures admissibles et les stations des quatre autres plis ;
- prédire le mois `m` pour toutes les stations du pli `k` ;
- concaténer les cinq plis : chaque ligne test reçoit exactement une prédiction hors station et hors temps.

Ainsi, les stations sont entièrement inconnues du modèle qui les prédit, mais l’évaluation mensuelle finale conserve toutes les stations éligibles. Les hyperparamètres et la liste de variables sont gelés avant les cinq mois. Si un réglage reste nécessaire, il utilise une validation interne temporelle située entièrement dans la fenêtre d’entraînement.

## 3. Assertions automatiques bloquantes

Pour chaque ajustement :

```text
assert max(train.valid_time) < min(test.valid_time)
assert max(train.available_at) <= model_issue_time
assert set(train.station_id).isdisjoint(set(test.station_id))
assert set(train.row_id).isdisjoint(set(test.row_id))
assert train.feature_schema_hash == test.feature_schema_hash
assert all(feature_available_at <= forecast_issue_time)
assert test_prediction_count == test_expected_row_count
assert test_prediction_row_id.is_unique
```

En l’absence de `available_at`, l’assertion de remplacement est :

```text
assert max(train.valid_date) <= first_day(test_month) − 3 days
```

Un seul échec arrête tout le benchmark ; aucune prédiction partielle n’est agrégée.

## 4. Statistiques de synthèse

Calculer sur les prédictions concaténées :

```text
gain_RMSE = 100 × (RMSE_CAMS − RMSE_corrigé) / RMSE_CAMS
ΔSE_i = (y_i − CAMS_i)² − (y_i − corrigé_i)²
```

Rapporter :

1. gain RMSE global par polluant et échéance ;
2. les cinq gains mensuels, sans les moyenner silencieusement ;
3. médiane, minimum, maximum et nombre de mois à gain négatif ;
4. distribution par type de station et par décile de concentration observée ;
5. IC95 par bootstrap à 2 000 réplications, stations puis blocs calendaires de 7 jours.

Le résultat primaire est le gain global OOF, et non la moyenne non pondérée des cinq RMSE.

Le `+1,5 %` actuel ne peut pas être testé contre ce résultat à partir de deux scalaires issus de plis différents. Il faut **rejouer l’ancien protocole sur exactement les mêmes lignes test**, produire `ΔSE_old` et `ΔSE_new`, puis bootstrapper par station × blocs de 7 jours la différence moyenne `mean(ΔSE_new − ΔSE_old)`. Le rolling-origin est supérieur si l’IC95 de cette différence est strictement positif ; sinon, conclure « différence non établie ».

## 5. Nombre d’ajustements

Avec cinq mois, cinq plis station et un modèle par polluant, l’échéance restant un prédicteur comme aujourd’hui :

```text
5 mois × 5 plis × 3 polluants = 75 ajustements
```

La comparaison stricte avec l’ancien protocole porte le total à **150 ajustements**. Si un modèle séparé est finalement entraîné pour J+1, J+2 et J+3, multiplier par trois : **225**, ou **450** avec le comparateur. Tout réglage de paramètres ajoute ses propres ajustements et doit être compté séparément ; il n’est pas inclus ici.

# Livrable 4 — Pratiques établies absentes du projet

| pratique | référence | ce qu’elle changerait ici | coût | pourquoi elle pourrait ne rien donner dans ce cas |
|---|---|---|---|---|
| Observation récente et biais récent : dernière mesure disponible, moyenne des 6/12/24 h précédentes et erreur CAMS du jour précédent | Neal et al., 2014, correction opérationnelle fondée sur la persistance du biais, [DOI 10.1016/j.atmosenv.2014.09.004](https://doi.org/10.1016/j.atmosenv.2014.09.004) ; CAMS MOS emploie aussi les observations de la veille ([documentation CAMS, 2025](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation)) | Ajouter des variables disponibles à l’émission et un drapeau de fraîcheur ; ablation séparée par J+1/J+2/J+3 | faible : jointure temps réel et gestion des absences | nul aux stations réellement nouvelles ; le gain peut chuter à J+3 et l’observation rapide peut être non validée |
| Réentraînement quotidien sur fenêtre récente | Bertrand et al., 2023, [DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023) ; la production CAMS retient actuellement 3 jours | Comparer fenêtre croissante à 30, 90 et 365 jours, modèles reconstruits chaque jour ; choix sur rolling-origin interne | moyen à élevé : nombre de fits multiplié par les jours | 270 stations peuvent ne pas fournir assez d’exemples en 3–30 jours, surtout avec stations cachées ; la saisonnalité peut l’emporter sur la dérive |
| Ensemble analogique de situations CAMS + météo, avec moyenne comme prévision et quantiles empiriques | Delle Monache et al., 2020, O₃ et PM2,5 CMAQ aux États-Unis, [DOI 10.1175/WAF-D-19-0148.1](https://doi.org/10.1175/WAF-D-19-0148.1) ; Solazzo et al., 2021, WRF-CAMx en Grèce, [DOI 10.1016/j.atmosenv.2021.118439](https://doi.org/10.1016/j.atmosenv.2021.118439) | Ajouter un correcteur concurrent non paramétrique et des quantiles ; mêmes plis stations et temps | moyen : index des analogues, normalisation apprise dans chaque pli | 17 mois donnent peu d’analogues pour les extrêmes et les stations exclues ; risque de retrouver seulement la saison et la météo déjà données au boosting |
| Prévision probabiliste par quantiles du résidu, calibrée sur plis prospectifs | La littérature analogique ci-dessus fournit directement des ensembles probabilistes ; le besoin de calibration multivariée est synthétisé pour le post-traitement météo par Vannitsem et al., 2021, [DOI 10.1175/BAMS-D-19-0308.1](https://doi.org/10.1175/BAMS-D-19-0308.1) | Entraîner les quantiles 0,1/0,5/0,9 avec la même architecture de boosting ; vérifier couverture, largeur et score de pinball | faible à moyen : trois fits par cible et calibration isotone éventuelle | peut améliorer la décision d’épisode sans réduire la RMSE du point ; 17 mois donnent des quantiles hauts instables |
| Modèles ou poids par régime météorologique prévisionnel, définis avant apprentissage | Les analogues reposent précisément sur la proximité de situations prévues ; Bertrand et al. montrent aussi l’intérêt d’un modèle global exposé à une diversité rapide de régimes ([2023](https://doi.org/10.5194/acp-23-5317-2023)) | Ajouter régime `stagnant / ventilé / marin / autre` et interactions avec polluant, sans changer le booster | faible après le livrable météo | le boosting peut déjà apprendre ces interactions ; découper 17 mois peut dégrader les régimes rares et les extrêmes |

Trois pratiques sont volontairement **écartées** :

- réinjecter les autres espèces CAMS ou des rapports chimiques : déjà testé, nul dans ce protocole ;
- kriger le biais stationnel : déjà testé et battu par les covariables de terrain ; la méthode est néanmoins publiée dans Neal et al. (2014) ;
- corriger l’horaire puis agréger : l’ablation propre au projet montre une perte de 5,8 points par rapport à l’apprentissage direct de la grandeur réglementaire.

# Critères globaux de réception par l’agent implémenteur

Le travail est conforme seulement si :

1. chaque ligne de prédicteurs porte `forecast_reference_time`, `valid_time`, `available_at`, cycle IFS, pas, unité et provenance ;
2. aucune donnée ERA5 ne figure dans un entraînement présenté comme opérationnel ;
3. le benchmark météo refuse de démarrer sans archive IFS historique homogène ou sans déclaration explicite des ruptures de cycle ;
4. les diagnostics sous-maille séparent les strates de stations et n’appellent jamais « plancher » une dispersion brute ;
5. chaque prédiction rolling-origin satisfait simultanément l’antériorité temporelle et l’exclusion complète de la station ;
6. tous les gains comparés sont recalculés sur les mêmes `row_id`, avec des intervalles respectant les dépendances station et temps.
