# Encadrer le gain météorologique sans archive IFS complète

## Résultat décisif

Le diagnostic « aucune archive IFS historique ouverte » était trop large. L’archive opérationnelle ECMWF complète reste soumise à des droits d’accès, mais **TIGGE diffuse librement les prévisions d’ensemble ECMWF archivées**, dont le contrôle non perturbé, depuis octobre 2006 ([ECMWF, fiche TIGGE](https://www.ecmwf.int/en/forecasts/datasets/tigge-global-medium-range-ensemble-forecasts-multiple-nwp-centres-2006)). TIGGE contient les variables de surface et de pression nécessaires à cinq des six diagnostics prioritaires ; la hauteur de couche limite n’y est pas fournie directement, mais peut être approximée par le profil de Richardson déjà spécifié ([ECMWF, liste des paramètres TIGGE](https://confluence.ecmwf.int/spaces/TIGGE/pages/40109884/Parameters)).

Il existe également une archive ouverte des prévisions **GFS 0,25°**, depuis janvier 2015, contenant directement température, point de rosée, vent, précipitation, rayonnement, pression et hauteur de couche limite ([NSF NCAR GDEX d084001, DOI 10.5065/D65D8PWK](https://gdex.ucar.edu/datasets/d084001/)). Elle ne reproduit pas le forçage IFS de CAMS, mais constitue un véritable substitut prévisionnel et un contrôle indépendant.

Conséquence : la dégradation synthétique d’ERA5 reste utile comme expérience immédiate sans téléchargement, mais elle ne doit plus porter seule la décision. Le test décisif devient `ERA5 → TIGGE-IFS → GFS`, sur les mêmes jours, stations et plis.

# Livrable 1 — Expérience d’encadrement sans nouveau téléchargement

## 1. Ce qu’elle peut et ne peut pas établir

Ni la persistance, ni la climatologie, ni un ERA5 bruité ne fournissent une borne mathématique du gain obtenu avec IFS. Une prévision peut battre la persistance sur la température et perdre sur une pluie locale ; une perturbation gaussienne peut reproduire une RMSE marginale tout en conservant trop bien la phase, la covariance spatiale ou les extrêmes.

L’expérience doit donc être nommée **test de résistance**, pas « estimation du gain IFS ». Elle répond à deux questions :

1. la valeur des variables météo survit-elle à une perte contrôlée d’information synoptique ?
2. à quel niveau de dégradation le gain de +7,8 % disparaît-il ?

Un résultat positif sous forte dégradation renforce la piste. Un résultat négatif ne peut pas, seul, prouver qu’IFS échouera.

## 2. Quatre bras obligatoires

Les quatre bras utilisent exactement les mêmes lignes, plis de stations, hyperparamètres et graines. Ils sont exécutés séparément pour J+1, J+2 et J+3.

### Bras A — plafond réanalyse

Utiliser les six variables déjà retenues, calculées avec ERA5 du jour cible :

```text
t2m_max, ssrd_sum, vpd_max, vc_p10, stagnant_day, dry_hours
```

Ce bras doit reproduire l’ablation existante : O₃ `+7,8 %`, PM2,5 `+6,7 %`, NO₂ `+2,7 %`, à la tolérance numérique près. S’il ne la reproduit pas, arrêter l’expérience.

### Bras B — persistance dépendante de l’échéance

Pour une journée cible `D` et une échéance `L ∈ {1,2,3}`, remplacer **tout le bloc horaire météorologique** de `D` par celui de `D−L jours`, puis le ré-étiqueter aux heures de `D` :

```text
Xpers,L(D, heure locale) = XERA5(D − L jours, même heure locale)
```

Le 29 février utilise le 28 février de l’année concernée. Aux changements d’heure, apparier d’abord en UTC ; une heure inexistante reste absente et une heure répétée conserve ses deux instants UTC. `dry_hours` est calculé sur les 168 h se terminant à `D−L`, puis reporté à `D` ; il ne faut pas recomposer son historique avec des heures du jour cible.

Cette transformation est préférable à un simple bruit blanc : elle préserve des champs physiquement cohérents, leur cycle diurne, leurs covariances entre température, humidité, rayonnement, vent, pluie et couche limite, ainsi que leur cohérence spatiale entre stations. Son erreur croît naturellement de J+1 à J+3.

Elle est **conservative comme scénario de gestion**, car elle enlève toute prévision de l’évolution synoptique. Elle n’est pas une borne garantie : un régime persistant peut rendre J−1 artificiellement excellent, et un front rendre J−1 artificiellement mauvais.

### Bras C — climatologie locale leave-one-year-out

La climatologie est construite séparément pour chaque station et heure UTC. Pour une cible de jour de l’année `d` :

```text
Xclim(s,d,h) = médiane de XERA5(s,d′,h)
               pour |distance_cyclique(d′,d)| ≤ 15 jours
               et année(d′) ≠ année(cible)
```

La fenêtre contient donc 31 jours par année disponible. Pour le vent, calculer séparément les médianes de `u` et `v`, jamais une médiane de direction. Pour pluie, rayonnement et hauteur de couche limite, appliquer la médiane dans leur espace physique après contrôle des unités. Calculer ensuite les six variables dérivées avec les mêmes fonctions que dans les autres bras.

Ce bras représente l’absence d’information synoptique, tout en conservant saison, lieu et cycle diurne. Il est identique pour J+1, J+2 et J+3 ; si son score varie avec l’échéance, il existe une erreur de jointure.

### Bras D — ERA5 perturbé par erreurs multivariées de persistance

Ce bras est celui qui imite le mieux une erreur de prévision **sans disposer de prévisions**, à condition de conserver les erreurs sous forme de blocs et non d’ajouter un bruit indépendant.

Pour chaque cible `D`, échéance `L` et réplication `b` :

1. choisir un jour donneur `R` dans une autre année, à ±30 jours calendaires du jour de l’année de `D` ;
2. former, pour toutes les stations, heures et variables, le bloc d’erreur de persistance :

```text
E_L(R) = XERA5(R − L jours) − XERA5(R)
```

3. appliquer **le même jour donneur** à toutes les variables et stations afin de préserver la covariance spatiale, temporelle et multivariée ;
4. construire :

```text
Xdeg,L,b(D) = XERA5(D) + aL,v × E_L(R)
```

Les transformations sont additives pour `T`, `Td`, pression, `u` et `v`; elles sont effectuées dans `log1p(x)` pour précipitation, rayonnement et hauteur de couche limite. Après retour à l’espace physique : borner pluie, rayonnement et couche limite à zéro, puis imposer `Td ≤ T`. Une correction physique appliquée à plus de 1 % des heures invalide la réplication.

Exécuter 20 réplications. Les mêmes jours donneurs sont utilisés pour le modèle de référence et le modèle enrichi afin que la comparaison soit appariée.

## 3. Calibrage de la dégradation

### Scores IFS directement exploitables

Le rapport ECMWF d’évaluation 2024 publie des courbes pour l’Europe, runs 00 UTC, septembre 2023–juin 2024. Les valeurs suivantes sont des **lectures arrondies de la figure 33**, et non un tableau numérique :

| variable | J+1 | J+2 | J+3 | domaine et référence |
|---|---:|---:|---:|---|
| température 2 m | ≈ 2,2 K | ≈ 2,3 K | ≈ 2,5 K | Europe, RMSE, IFS HRES, Haiden 2024 |
| point de rosée 2 m | ≈ 2,3 K | ≈ 2,5 K | ≈ 2,7 K | même protocole |
| vitesse du vent 10 m | ≈ 2,1 m s⁻¹ | ≈ 2,2 m s⁻¹ | ≈ 2,3 m s⁻¹ | même protocole |

Source : Thomas Haiden, *Evaluation of ECMWF forecasts*, ECMWF, 2024, figure 33 ([rapport PDF](https://www.ecmwf.int/sites/default/files/elibrary/092024/81582-evaluation-of-ecmwf-forecasts.pdf)). Ces scores sont vérifiés sur l’Europe entière, pas spécifiquement sur les stations françaises du projet ; ils ne doivent pas être présentés avec plus d’un chiffre décimal.

Je n’ai pas trouvé de tableau publié, homogène et directement comparable donnant à J+1/J+2/J+3 sur les terres européennes :

- la RMSE de hauteur de couche limite ;
- la RMSE du rayonnement descendant ;
- une RMSE exploitable de précipitation journalière ;
- la covariance des erreurs entre ces champs.

Ces valeurs sont donc **Inconnu**. L’étude de Lavers et al. porte sur la hauteur de couche limite au-dessus des océans et ne doit pas être transférée aux stations françaises ([2019, DOI 10.1029/2019JD030454](https://doi.org/10.1029/2019JD030454)).

### Coefficients à appliquer

Pour température, point de rosée et vent, calculer dans les 69 mois l’erreur quadratique moyenne brute du bloc `E_L`, puis :

```text
aL,v = RMSE_IFS_publié(L,v) / RMSE(E_L,v)
```

Pour les autres champs, faute de score comparable, fixer `aL,v = 1`. Ils reçoivent donc l’erreur complète de persistance. Cette combinaison n’est pas une reproduction d’IFS ; elle constitue le scénario de résistance préenregistré.

Ajouter une sensibilité à `0,75 × a`, `1,00 × a` et `1,25 × a`. Le facteur 1,25 est un choix prudent de conception, non une valeur publiée. L’ordre des gains doit être monotone en moyenne :

```text
gain(0,75a) ≥ gain(1,00a) ≥ gain(1,25a)
```

Une inversion supérieure à un point de gain impose de publier la non-monotonicité et interdit de résumer l’expérience par une seule « borne ».

## 4. Statistiques et critères de décision

Pour chaque polluant et échéance, rapporter :

```text
gain_rel = 100 × (RMSE_sans_météo − RMSE_avec_météo) / RMSE_sans_météo
gain_abs = RMSE_sans_météo − RMSE_avec_météo
rétention = gain_rel_dégradé / gain_rel_ERA5
```

Les intervalles sont obtenus par 2 000 réplications de bootstrap station × blocs calendaires de 7 jours. Pour le bras D, le bootstrap englobe les 20 réalisations météorologiques.

### Ce qui est permis sous 48 h

- Si le bras persistance conserve un gain positif avec borne basse IC95 > 0 à J+3, écrire : « la valeur météo résiste même à une dégradation plus forte qu’une prévision numérique usuelle ».
- Si le bras D à `1,25a` conserve au moins `+3,9 points` sur O₃, écrire : « le seuil de résistance préenregistré est franchi sous perturbation synthétique ».
- Dans tous les autres cas, écrire seulement : « la réanalyse établit un plafond ; la transférabilité doit être mesurée sur une archive de prévisions ».

### Ce qui enterre réellement la piste

**Aucun résultat de persistance ou d’ERA5 bruité ne suffit logiquement à enterrer le mécanisme.** Le critère d’arrêt doit être appliqué à TIGGE-IFS ou, à défaut, GFS :

- abandonner la revendication opérationnelle à l’échéance `L` si la borne **supérieure** IC95 du gain météo est inférieure à `+3,9 points relatifs` sur O₃ **ou** si la borne supérieure du gain absolu est inférieure à `0,3 µg m⁻³` ;
- abandonner toute la piste seulement si ce critère échoue déjà à J+1 sur TIGGE-IFS et sur GFS ;
- un échec uniquement à J+3 limite la promesse à J+1/J+2, il n’invalide pas le conditionnement météo.

# Livrable 2 — Archives de prévisions réellement ouvertes

## 1. Tableau de décision

| source | modèle | emprise | profondeur d’archive vérifiée | variables utiles | mode d’accès | décision / blocage |
|---|---|---|---|---|---|---|
| **ECMWF TIGGE** | ECMWF ENS : contrôle non perturbé et membres perturbés | global | octobre 2006 → présent ; couvre intégralement août 2023–décembre 2024 | `2t`, `2d`, `10u`, `10v`, pression, précipitation, rayonnement solaire net, profils `t/q/u/v/z` | ECMWF Data Store / CDS API, sous-région France, licence TIGGE ; DOI 10.21957/8511726f | **priorité 1** ; vraie prévision IFS historique, mais pas HRES. Pas de BLH direct, maille/temps plus grossiers, rayonnement net plutôt que descendant |
| **NSF NCAR GDEX d084001** | NCEP GFS opérationnel 0,25° | global | 15 janvier 2015 → présent ; couvre intégralement la période | température, point de rosée, vent, pluie, rayonnement court, pression, **hauteur de couche limite**, profils | GDEX, GRIB2, sélection temporelle/spatiale ; CC BY 4.0 ; DOI 10.5065/D65D8PWK | **priorité 2** ; toutes les familles utiles, mais modèle différent du forçage CAMS |
| Météo-France API PNT | AROME / ARPEGE | France / Europe / monde selon produit | **14 jours** | champs de surface et pression, selon paquet | API Météo-France, compte gratuit | écarté pour 2023–2024 |
| paquets Météo-France / meteo.data.gouv.fr | AROME 0,01° ou 0,025°, ARPEGE | France / Europe | fichiers courants et rétention PNT 14 jours ; un extrait exceptionnel couvre février–mars 2024 | nombreux champs horaires | téléchargement GRIB2, Licence Ouverte 2.0 | écarté : pas de continuité août 2023–décembre 2024 |
| Open-Meteo AWS | AROME, ARPEGE, ICON, GFS, IFS | selon modèle | prévisions AROME/ARPEGE/ICON/GFS depuis **15 décembre 2023**, IFS depuis **3 février 2024** ; runs publics individuels conservés trois mois | nombreux champs de surface et pression | S3, format `.om`, sans compte | utile en complément, mais ne couvre pas août–14 décembre 2023 et l’archive longue « rolling time series » ne conserve pas nécessairement l’identité de chaque run/échéance |
| AWS `mf-nwp-models` par OpenMeteoData | AROME / ARPEGE | France / Europe / global | profondeur historique longue non documentée dans le registre | dizaines de champs | S3 anonyme | écarté tant que l’antériorité 2023 et la conservation des runs ne sont pas prouvées |
| CAMS Europe ADS | ensemble régional de qualité de l’air | Europe | analyses/prévisions régionales depuis octobre 2015 | espèces chimiques et aérosols | ADS, API | les sorties publiques ne livrent pas le forçage météo commun sous forme de champs téléchargeables avec le produit régional |
| CAMS MOS aux stations | CAMS corrigé avec météo IFS | Europe, stations | produit disponible depuis janvier 2024 | concentrations brutes/corrigées ; la chaîne interne utilise `T2m`, RH, `u/v`, BLH | ADS, CSV | les prédicteurs météo internes ne sont pas inclus dans le fichier distribué ; inutilisable comme archive météo |
| ERA5T / ERA5 à courte latence | IFS de réanalyse | global | 1940 → présent, délai de quelques jours | toutes les variables ERA5 retenues | CDS | pas une prévision ; utile au contrôle rétrospectif, jamais comme entrée déclarée opérationnelle |

Sources principales : [ECMWF TIGGE](https://www.ecmwf.int/en/forecasts/datasets/tigge-global-medium-range-ensemble-forecasts-multiple-nwp-centres-2006), [paramètres TIGGE](https://confluence.ecmwf.int/spaces/TIGGE/pages/40109884/Parameters), [licence TIGGE](https://ecds.ecmwf.int/licences/tigge-licence), [GFS GDEX](https://gdex.ucar.edu/datasets/d084001/), [Météo-France — rétention 14 jours](https://www.data.gouv.fr/fr/dataservices/api-modele-arome/), [Open-Meteo AWS](https://github.com/open-meteo/open-data), [documentation CAMS MOS](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation).

## 2. Requête TIGGE à spécifier à l’agent

Le premier essai doit demander uniquement le contrôle ECMWF pour limiter le volume :

```text
origin          = ecmf
type            = cf
time            = 00:00
date            = 2023-08-01 / to / 2024-12-31
step            = 24 / 30 / 36 / ... / 96
area            = 51.5 / -5.5 / 41.0 / 10.0
levtype=sfc     = 2t / 2d / 10u / 10v / sp / msl / tp / ssr
levtype=pl      = t / q / u / v / z
levelist        = 1000 / 925 / 850 / 700 / 500
format          = grib2
```

Les pas exacts disponibles doivent être interrogés dans le formulaire ECDS avant lancement ; ne pas supposer un pas horaire. Les cumuls doivent être désaccumulés à l’intérieur d’un même run. La date de base, l’échéance, le type `cf/fc`, le cycle et l’identifiant du centre doivent survivre jusqu’à la table de variables.

Le contrôle TIGGE n’est pas nécessairement le même champ natif que celui ingéré par tous les membres CAMS : il faut écrire « prévision IFS archivée et alignée en centre/cycle », pas « forçage exact de CAMS ». Depuis le cycle 49r1, contrôle ENS et HRES ont été rapprochés, mais cette identité ne doit pas être rétroprojetée sans vérification sur toute la période ([ECMWF TIGGE, historique des mises à niveau](https://confluence.ecmwf.int/spaces/TIGGE/pages/53523308/Model%2Bupgrades)).

## 3. Requête GFS de contrôle

Utiliser un seul run 00 UTC par date et les échéances correspondant aux jours CAMS. Extraire à la volée la sous-région France et les seules variables nécessaires ; ne pas télécharger les grilles globales complètes. L’archive fournit quatre runs quotidiens, des pas de 3 h jusqu’à 240 h, et contient explicitement température, point de rosée, vent, précipitation, rayonnement, pression et hauteur de couche limite ([GDEX d084001, DOI 10.5065/D65D8PWK](https://gdex.ucar.edu/datasets/d084001/)).

Le résultat GFS ne mesure pas le gain IFS. Sa valeur est expérimentale : si deux systèmes de prévision différents conservent une part comparable du plafond ERA5, la piste est robuste au fournisseur météo ; s’ils divergent, le résultat dépend du modèle de prévision et doit être annoncé comme tel.

# Livrable 3 — Ce que la littérature a déjà établi

## 1. La comparaison exacte HRES–ERA5 existe déjà pour CAMS O₃

Petetin et al. ont corrigé les prévisions CAMS O₃ sur la péninsule Ibérique en 2018–2019, à J+1–J+4, avec plusieurs MOS dont analogues et gradient boosting. Ils ont répété les méthodes météo-dépendantes avec la prévision ECMWF HRES et avec ERA5, en utilisant notamment température, vent, pression, couverture nuageuse, rayonnements, BLH et géopotentiel 500 hPa. Ils concluent à des performances **relativement similaires avec les deux entrées météorologiques** ; les RMSE des prévisions O₃ corrigées passent, selon métrique et échéance, d’environ 20–40 % à 10–30 %, mais ce résultat agrège l’effet complet du MOS et n’isole pas un « gain météo » en points.

Source : Petetin et al., 2022, *Atmospheric Chemistry and Physics*, [DOI 10.5194/acp-22-11603-2022](https://doi.org/10.5194/acp-22-11603-2022), notamment sections 2.1.3 et 3.4 / figure G6.

**Implication :** l’hypothèse que le +7,8 % ERA5 s’effondrera nécessairement avec une prévision n’est pas soutenue par le précédent le plus proche ; la littérature fournit au contraire un motif raisonnable de poursuivre. Elle ne permet toutefois pas de prédire que les 7,8 points seront conservés avec votre cible, vos stations exclues et vos six variables.

## 2. Le CAMS MOS opérationnel utilise déjà la météo prévue

Bertrand et al. entraînent un MOS global européen sur les prévisions CAMS avec température 2 m, humidité relative, composantes du vent et hauteur de couche limite issues de **prévisions IFS**, plus les observations récentes. Le système reconstruit quotidiennement un modèle avec une fenêtre courte ; il traite O₃, NO₂, PM10 et PM2,5 et évalue aussi les dépassements.

Source : Bertrand et al., 2023, *Atmospheric Chemistry and Physics*, [DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023), et [documentation opérationnelle CAMS MOS, 2025](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation).

**Implication :** « ajouter une météo prévue à CAMS » n’est pas une nouveauté. La valeur propre de la piste doit être formulée comme l’évaluation française sur stations entièrement exclues, l’apprentissage direct des grandeurs réglementaires, les variables sous-maille et l’analyse des extrêmes.

## 3. Un second système très proche confirme le conditionnement, sans ablation météo isolée

Riccio et Chianese corrigent et désagrègent CAMS sur l’Italie pour PM10, PM2,5, NO₂ et O₃, avec les mêmes agrégats réglementaires, 750 stations et une validation laissant 82 stations de côté. Les prédicteurs temporels incluent précipitation, température, vent et hauteur de couche limite provenant du système opérationnel ECMWF. Les auteurs attribuent un rôle important aux variables de conditionnement, mais ne publient pas l’ablation qui séparerait proprement la seule contribution météo.

Source : Riccio et Chianese, 2024, *Atmospheric Chemistry and Physics*, [DOI 10.5194/acp-24-1673-2024](https://doi.org/10.5194/acp-24-1673-2024).

**Implication :** le mécanisme est crédible et déjà opérationnalisable ; la question encore utile n’est pas « la météo aide-t-elle ? », mais « quelle part du gain reste hors station, sur le maximum réglementaire et avec une météo réellement disponible à chaque échéance ? ».

# Formulation recommandée dans le dossier sous 48 h

> L’ajout de variables ERA5 améliore la correction de 7,8 % sur l’ozone ; cette valeur est un plafond rétrospectif, non un gain opérationnel. La littérature CAMS rapporte toutefois des performances proches lorsque les méthodes météo-dépendantes utilisent HRES ou ERA5 (Petetin et al., 2022). Le programme proposé mesurera la perte de transfert sur une archive de prévisions IFS issue de TIGGE, puis vérifiera sa robustesse avec l’archive GFS. Le gain sera considéré transférable s’il conserve au moins 3,9 points relatifs et 0,3 µg m⁻³ avec un intervalle de confiance excluant zéro.

Cette formulation est plus forte que « les prévisions IFS sont disponibles dans l’ADS/CDS », parce qu’elle nomme une archive réellement accessible, distingue plafond et résultat, et fixe à l’avance le critère qui peut invalider la piste.
