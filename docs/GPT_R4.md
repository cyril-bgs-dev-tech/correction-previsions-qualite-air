# 1. Le texte qui fait foi

**Établi.** Le texte en vigueur est l’**arrêté du 10 juillet 2020 relatif à l’indice de la qualité de l’air ambiant**, applicable depuis le 1er janvier 2021. La page consolidée de Légifrance ne signale aucune modification postérieure et indique une dernière mise à jour du texte au 1er janvier 2021 : c’est donc cette version qui fait foi à la date de consultation, le 30 juillet 2026.

**Établi.** L’article 3 impose cinq polluants — SO₂, NO₂, O₃, PM10 et PM2,5 — et définit l’indice global comme le sous-indice le plus dégradé. Les seuils sont fixés dans l’annexe I :

| Grandeur journalière (µg/m³) | Bon | Moyen | Dégradé | Mauvais | Très mauvais | Extrêmement mauvais |
|---|---:|---:|---:|---:|---:|---:|
| PM2,5, moyenne | 0–10 | 11–20 | 21–25 | 26–50 | 51–75 | > 75 |
| PM10, moyenne | 0–20 | 21–40 | 41–50 | 51–100 | 101–150 | > 150 |
| NO₂, maximum horaire | 0–40 | 41–90 | 91–120 | 121–230 | 231–340 | > 340 |
| O₃, maximum horaire | 0–50 | 51–100 | 101–130 | 131–240 | 241–380 | > 380 |
| SO₂, maximum horaire | 0–100 | 101–200 | 201–350 | 351–500 | 501–750 | > 750 |

**Établi.** L’arrêté n’impose pas une restitution exclusivement communale ou exclusivement à l’EPCI : l’article 1 exige des zones représentatives qui couvrent intégralement l’EPCI, tandis que l’article 4 laisse leur délimitation à l’AASQA. Le guide national précise que la zone ne peut dépasser l’EPCI et qu’une restitution plus fine, notamment communale, est possible.

**Sources.**

- [Arrêté du 10 juillet 2020, articles 1, 3, 4 et 9, annexe I — Légifrance](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042164835)
- [Guide de calcul de l’indice ATMO, version du 14 décembre 2020, pp. 3 et 6 — Atmo France](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)
- [Statut du guide dans le référentiel technique national — LCSQA](https://www.lcsqa.org/fr/rapport/guide-de-calcul-de-lindice-atmo)

# 2. L’ordre des opérations

**Établi.** Pour un modèle méso-échelle, le guide prescrit l’ordre suivant : (1) calculer, **en chaque point du modèle**, la grandeur journalière de chaque polluant ; (2) convertir chaque concentration en qualificatif ; (3) retenir le point dont le qualificatif est le plus dégradé dans chaque commune ; (4) retenir l’indice communal le plus élevé dans l’EPCI. Il s’agit donc d’un maximum de **classes déjà calculées**, non d’une moyenne spatiale.

**Établi.** L’annexe I de l’arrêté exprime aussi le calcul par polluant comme le « maximum » des maxima horaires journaliers pour SO₂, NO₂ et O₃, et comme le maximum des moyennes journalières pour PM10 et PM2,5. Comme les seuils sont monotones, « maximiser la concentration puis classer » et « classer chaque maille puis maximiser la classe » sont équivalents **pour un polluant donné et une même grandeur temporelle**.

**Établi.** Entre polluants, on ne moyenne pas les concentrations, qui n’ont ni la même métrique temporelle ni les mêmes seuils : on compare leurs sous-indices et l’on conserve le plus dégradé.

**Sources.**

- [Guide de calcul, règle n° 4, pp. 7–8](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)
- [Arrêté du 10 juillet 2020, article 3 et annexe I](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042164835)

# 3. La méthode de production

**Établi au niveau national.** Le guide exige préférentiellement un modèle méso-échelle couvrant le territoire ; il indique que la représentativité est soutenue par l’assimilation des stations de fond et par des prévisions statistiques. PREV’AIR documente deux chaînes distinctes : ses analyses utilisent un krigeage des observations avec CHIMERE en dérive externe ; ses prévisions corrigées appliquent un apprentissage statistique aux stations, puis les spatialisent par krigeage.

**Établi pour Atmo Occitanie, mais seulement à haut niveau.** L’association publie que sa modélisation mobilise inventaire d’émissions, stations, météo, topographie/occupation du sol, apports extérieurs et chimie, et qu’elle sert quotidiennement à prévoir aujourd’hui et demain.

**Inconnu.** Je n’ai trouvé aucune notice publique d’Atmo Occitanie donnant, pour sa chaîne quotidienne d’indice, le nom du modèle régional, la variante de krigeage ou d’assimilation, les covariables, la période d’apprentissage, les stations effectivement assimilées et les éventuelles retouches d’expert. Il serait incorrect d’attribuer automatiquement à Atmo Occitanie la méthode PREV’AIR : le guide laisse une marge de mise en œuvre à chaque AASQA, sous contrainte de représentativité du fond.

**Sources.**

- [Guide de calcul, préambule et règles n° 4–5, pp. 3 et 7–8](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)
- [PREV’AIR — prévisions corrigées](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)
- [LCSQA, *Évaluation des cartes analysées*, 2016, pp. 3–4](https://www.lcsqa.org/system/files/media/documents/lcsqa2015_evaluation_cartes_analysees_fairmode_vf-drc-16-152350-08456a_0.pdf)
- [Atmo Occitanie — principes publiés de la modélisation](https://www.atmo-occitanie.org/pour-aller-plus-loin/comment-evaluer-la-qualite-de-lair/la-modelisation-une-cartographie-pour)

# 4. La résolution

**Établi.** Aucun pas de grille chiffré n’est imposé par l’arrêté. Son article 4 impose seulement que l’agrégation spatiale soit représentative de la qualité de l’air de fond dans la zone.

**Établi.** Le guide définit qualitativement le modèle méso-échelle comme ayant une résolution « de l’ordre de quelques kilomètres » et le modèle de fine échelle comme ayant une résolution de quelques dizaines de mètres. Si une chaîne fine échelle inclut la proximité routière, seules ses mailles de fond peuvent entrer dans l’indice et l’AASQA doit documenter sa méthode comparable.

**Inconnu.** La résolution exacte du champ quotidien utilisé par Atmo Occitanie avant l’agrégation communale/EPCI n’apparaît pas dans les sources publiques identifiées. Elle ne doit donc pas être déduite de la résolution de CAMS Europe, de PREV’AIR ou d’une cartographie urbaine annuelle.

**Sources.**

- [Arrêté du 10 juillet 2020, article 4](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000042164835)
- [Guide de calcul, définitions et règle n° 4, pp. 4 et 7](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)

# 5. Le sens du biais

**Établi — cause principale plausible.** L’officiel cherche le niveau de fond maximal sur toutes les mailles de chaque commune, puis sur toutes les communes de l’EPCI ; une station ponctuelle ne couvre pas ces maxima possibles. Cela rend un biais négatif `station − EPCI` attendu **si** la station et la carte représentent correctement le même champ de fond. Ce n’est toutefois pas une inégalité mathématique garantie entre deux estimateurs différents : l’erreur du modèle spatial peut inverser localement le signe.

**Établi par requête reproductible sur la donnée officielle, non comme statistique publiée.** Dans les 94 464 lignes valides servies le 30 juillet 2026 pour le 1er janvier 2025–30 juillet 2026, O₃ est l’unique sous-indice maximal dans 74 985 cas (79,38 %), PM10 dans 286 cas (0,30 %) et SO₂ dans aucun cas. En incluant les ex æquo, O₃ participe au maximum dans 95,89 % des lignes, PM10 dans 5,68 % et SO₂ dans 0,54 %. Ces bornes sont plus honnêtes qu’un `idxmax` arbitraire lorsque plusieurs polluants ont la même classe.

**Jugement.** L’absence de PM10 et SO₂ peut créer certains désaccords, notamment lors d’intrusions sahariennes, mais ces fréquences excluent qu’elle explique à elle seule un biais moyen de −0,72 classe. La couverture spatiale — surtout pour l’ozone, très dominant — est l’explication à tester en premier.

**Établi.** Les stations ou mailles de proximité trafic ne doivent pas piloter l’indice de fond : le guide prend les stations de fond comme référence et exclut les mailles de proximité routière d’un modèle fin. Si votre comparaison emploie déjà uniquement 23 stations de fond, l’argument « les stations trafic tirent vers le haut » ne s’applique pas à cet échantillon.

**À vérifier.** Le rôle précis des PM10 sahariennes dans vos jours de désaccord doit être établi jour par jour à partir des sous-indices officiels et d’une source d’identification des intrusions ; la seule fréquence globale de PM10 ne permet pas de l’attribuer aux poussières désertiques.

**Sources.**

- [Guide de calcul, règles n° 4–5, pp. 7–8](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)
- [Jeu officiel Atmo Occitanie, profondeur, formats et API](https://www.data.gouv.fr/datasets/indice-quotidien-de-qualite-de-lair-pour-les-collectivites-territoriales-en-occitanie)
- [API ArcGIS interrogée pour les comptages](https://services9.arcgis.com/7Sr9Ek9c1QTKmbwr/arcgis/rest/services/Indice_quotidien_de_qualit%C3%A9_de_l%E2%80%99air_pour_les_collectivit%C3%A9s_territoriales_en_Occitanie/FeatureServer/0)
- [Calcul antérieur du projet et convention `idxmax`](../reports/INDICE_ATMO.md)

# 6. Prévu ou constaté

**Établi.** L’indice est conçu comme un état journalier **prévu** ; le guide exige une diffusion quotidienne et décrit au minimum le jour même et le lendemain. Il prévoit aussi un indice de la veille fondé sur des données modélisées assimilées, donc post-traitées avec les observations.

**Établi — piège majeur du jeu ouvert.** Pour une même `date_ech`, la valeur J+1 est remplacée par J0, puis éventuellement par J−1 ; le flux courant ne conserve donc pas les millésimes successifs de prévision. `date_dif` indique la diffusion de la valeur présente, pas un historique de toutes les versions écrasées.

**Jugement.** Pour évaluer honnêtement votre CAMS J+1, il faut comparer une prévision émise à D pour D+1 à l’indice officiel **J+1 archivé au même instant**. Si vous ne l’avez pas collecté au fil de l’eau, comparer à la dernière valeur publiée pour D+1 reste utile comme vérification contre une analyse finale, mais ce n’est ni une comparaison prévision-à-prévision ni une mesure indépendante de la seule spatialisation.

**Inconnu.** Les sources publiques consultées ne permettent pas d’affirmer que les champs J0 et J+1 d’Atmo Occitanie utilisent exactement le même modèle, les mêmes corrections et la même expertise humaine.

**Sources.**

- [Guide de calcul, règles n° 2, 4, 7 et exemple `date_ech`/`date_dif`, pp. 6–7, 9 et 14–15](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)
- [Atmo France — publication quotidienne du jour et du lendemain à 14 h](https://www.atmo-france.org/article/lindice-atmo)
- [Notice Atmo Data, version du 1er avril 2025](https://www.atmo-france.org/sites/federation/files/medias/documents/2025-04/notice_Atmo_Data_1eravril2025.pdf)

# 7. La circularité de l’évaluation

**Établi.** Comparer deux cartes construites avec les mêmes stations ne fournit pas une validation indépendante. Le LCSQA indique que l’évaluation d’une carte fusionnée doit employer des observations non utilisées pour sa construction et décrit trois solutions : leave-one-out, k-fold spatial et jeu de stations indépendant. Il avertit aussi que les scores dépendent de la distribution spatiale des stations.

**Établi mais distinct.** Pour l’indice ATMO, le guide national propose en outre un test de **représentativité de l’échelle** sur une année J−1 assimilée : comparer le maximum de maille à la classe modale par nombre de mailles et à la classe couvrant la plus grande surface. Ce test répond au choix de la zone de diffusion ; il ne remplace pas une validation indépendante des concentrations.

**Établi, application future.** La décision d’exécution (UE) 2026/1208 formalise le leave-one-out pour les applications intégrant modèles et mesures et exige des mesures non utilisées dans le résultat ; elle s’appliquera à partir du 30 juin 2028. Elle concerne l’évaluation réglementaire de la modélisation au titre de la directive 2024/2881, pas directement le score d’un projet de candidature, mais elle confirme la bonne direction méthodologique.

**Jugement — protocole défendable avec données ouvertes.** Produire les champs de concentration en retirant tour à tour des **groupes spatiaux entiers** de stations de fond, recalibrer toute la chaîne sans ces stations, puis évaluer concentrations et classes aux stations retirées, avec des blocs temporels séparés. Ensuite seulement, comparer les classes EPCI au flux officiel comme test de concordance externe, en l’appelant explicitement « non indépendant » si le flux a assimilé ces mêmes stations.

**À vérifier.** Des campagnes mobiles ou micro-capteurs peuvent densifier l’évaluation, mais elles ne deviennent indépendantes et crédibles qu’avec données brutes ouvertes, co-localisation/étalonnage, incertitude documentée et dates compatibles. Je n’ai pas identifié un jeu occitan ouvert satisfaisant simultanément ces conditions pour les cinq polluants et la période du projet.

**Sources.**

- [LCSQA, *Évaluation des cartes analysées*, 2016, pp. 3–4 et 16](https://www.lcsqa.org/system/files/media/documents/lcsqa2015_evaluation_cartes_analysees_fairmode_vf-drc-16-152350-08456a_0.pdf)
- [Guide de calcul, proposition méthodologique, p. 15](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)
- [Décision d’exécution (UE) 2026/1208, article 3, article 11 et annexe II](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj)
- [LCSQA, micro-capteurs et cartographie, 2019](https://www.lcsqa.org/fr/rapport/utilisation-des-donnees-de-micro-capteurs-pour-la-modelisation-et-la-cartographie-de-la)

# 8. Les données

## a) Communes et EPCI

**Établi.** Utiliser **ADMIN EXPRESS COG 2026** de l’IGN, cohérent avec le COG de l’Insee : il fournit les découpages de la commune à la région, dont les EPCI. L’édition 2026 est téléchargeable et disponible en services web ; GeoPackage est disponible, ainsi que GeoParquet et FlatGeobuf pour certains conditionnements France entière. Les données publiques de l’IGN sont diffusées sous Licence Ouverte Etalab 2.0.

**Profondeur.** Il s’agit d’un millésime géographique au 1er janvier 2026, non d’un historique quotidien. Pour comparer des indices 2025 et 2026, conserver aussi le millésime correspondant à chaque date ou documenter explicitement le rattachement de toutes les dates à la géographie 2026.

**Sources.**

- [IGN/cartes.gouv.fr — disponibilité d’ADMIN EXPRESS COG 2026 et formats](https://cartes.gouv.fr/aide/fr/partenaires/ign/generalites-ign/actualites/2026-05-admin-express-cog/)
- [IGN — politique d’ouverture sous Licence Ouverte Etalab 2.0](https://www.ign.fr/institut/des-donnees-et-logiciels-ouverts-au-service-de-la-nation)

## b) Population communale

**Établi.** La source directement exploitable est le fichier d’ensemble des **populations de référence 2023**, authentifiées par le décret n° 2025-1362 du 26 décembre 2025 et entrées en vigueur le 1er janvier 2026. L’Insee le propose en CSV UTF-8 et XLSX ; la page de téléchargement ne documente pas une API spécifique pour ce fichier.

**À vérifier.** Pour une pondération populationnelle d’indices datés de 2025, il faut décider si l’objectif est la population légale en vigueur à la date ou une géographie homogène sur toute la période. Ne pas mélanger silencieusement un contour 2025 avec un code communal 2026.

**Source.**

- [Insee — populations de référence 2023, fichier France hors Mayotte](https://www.insee.fr/fr/statistiques/8680726)

## c) Historique de l’indice ATMO par EPCI

**Établi.** Le jeu officiel d’Atmo Occitanie est récupérable en masse sans authentification : CSV, GeoJSON, GeoPackage, WFS et API ArcGIS REST. Il contient l’indice global, les cinq sous-indices, `date_ech`, `date_dif`, le code et le type de zone. La licence indiquée est ODbL.

**Établi par interrogation directe le 30 juillet 2026.** L’API servait **94 464 lignes**, du **1er janvier 2025 au 30 juillet 2026**. Cette profondeur réelle concorde avec la règle annoncée « du 01/01 de N−1 jusqu’à J+1 » ; elle est glissante et ne constitue donc pas une archive pérenne antérieure à N−1.

**Établi — limite décisive.** Le téléchargement en masse existe bien, mais il ne conserve pas les versions successives J+1/J0/J−1 d’une même échéance : la nouvelle diffusion remplace la précédente. Pour une validation prévisionnelle future, il faut donc archiver quotidiennement le flux avec son horodatage de collecte.

**Sources.**

- [Jeu officiel Atmo Occitanie sur data.gouv.fr — formats, profondeur, WFS et licence](https://www.data.gouv.fr/datasets/indice-quotidien-de-qualite-de-lair-pour-les-collectivites-territoriales-en-occitanie)
- [API ArcGIS REST du jeu](https://services9.arcgis.com/7Sr9Ek9c1QTKmbwr/arcgis/rest/services/Indice_quotidien_de_qualit%C3%A9_de_l%E2%80%99air_pour_les_collectivit%C3%A9s_territoriales_en_Occitanie/FeatureServer/0)
- [Guide de calcul, règle n° 8 et exemple de remplacement, pp. 9 et 14–15](https://www.atmo-france.org/sites/federation/files/medias/documents/2022-04/guide_calcul_nouvel_indice_ATMO_VF_version14decembre2020.pdf)
- [Atmo France — licence ODbL des données Atmo Data](https://www.atmo-france.org/article/conditions-generales-dutilisation)

# Recommandation

**Comparer autrement :** validez d’abord les concentrations et classes par retrait spatial de stations de fond, puis reproduisez le maximum maille → commune → EPCI seulement comme démonstrateur de restitution, et traitez la comparaison au flux officiel comme une concordance non indépendante — sauf si vous disposez des millésimes J+1 archivés à l’heure d’émission.

# Points classés « Inconnu »

- Modèle régional, version, résolution exacte et domaine employés quotidiennement par Atmo Occitanie pour l’indice.
- Méthode précise de fusion/assimilation ou de krigeage d’Atmo Occitanie, covariables, paramètres et fréquence de recalage.
- Liste à jour des stations réellement assimilées dans chaque sous-indice, au-delà de l’obligation de publication posée par l’article 5.
- Nature et traçabilité des corrections d’expert appliquées aux champs J0 et J+1.
- Identité complète ou non des chaînes J0 et J+1 d’Atmo Occitanie.
- Existence d’une archive interne conservant tous les millésimes J+1/J0/J−1 au lieu de la seule dernière valeur exposée.
- Jeu occitan ouvert de campagnes mobiles ou micro-capteurs, indépendant, étalonné et synchrone, couvrant les cinq polluants sur la période du projet.
