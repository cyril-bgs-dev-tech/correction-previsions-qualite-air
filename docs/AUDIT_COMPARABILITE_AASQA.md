# Audit de comparabilité avec la méthode AASQA/LCSQA

_Audit du 31 juillet 2026. Les constats « publié » reposent sur les sources citées ; les conclusions sur le projet proviennent du code et des rapports locaux. Aucun résultat source n'a été modifié pendant cet audit._

## Verdict

Les résultats actuels sont utiles pour comparer trois produits sur une population de couples station–temps, mais **le tableau principal n'est pas encore une évaluation conforme à la convention AASQA/LCSQA**. Le classement général de la correction reste plausible ; plusieurs chiffres et surtout leur libellé doivent néanmoins être recalculés avant d'être présentés comme comparables à une AASQA.

Trois corrections sont prioritaires : calculer correctement les RMSE agrégées, ajouter une vue AASQA sur stations de fond avec scores par station puis moyenne des stations, et remplacer le mot « épisode » par l'endpoint réellement mesuré — ou évaluer le vrai seuil ozone de la procédure française.

## 1. Ce que fait la méthode AASQA/LCSQA publiée

**Publié.** L'article 13 de l'arrêté du 16 avril 2021 impose à chaque AASQA une évaluation annuelle de ses outils de modélisation **et de son expertise**, selon le référentiel technique national, transmise au plus tard le 30 juin suivant ([arrêté, article 13](https://aida.ineris.fr/reglementation/arrete-160421-relatif-dispositif-national-surveillance-qualite-lair-ambiant)). Le guide d'évaluation du LCSQA, approuvé le 18 mars 2021 et applicable depuis le 1er janvier 2022, harmonise ce rapportage ([LCSQA, 2021](https://www.lcsqa.org/fr/rapport/guides-methodologiques-pour-la-prevision-de-la-qualite-de-lair)).

**Publié.** PREV'AIR retient uniquement les stations de fond urbaines, périurbaines et rurales ayant plus de 75 % de données valides sur la période ; ses indicateurs principaux sont biais, RMSE et corrélation ([PREV'AIR, « Évaluations »](https://www.prevair.org/le-systeme-prevair/la-production/evaluations)). Un rapport AASQA conforme au référentiel calcule les scores temporels à chaque station puis en fait la moyenne, et traite séparément les typologies et échéances ; le rapport Nouvelle-Aquitaine 2022 l'explicite aux pages 8–12 et 17–20 ([Atmo Nouvelle-Aquitaine, 2023](https://www.lcsqa.org/system/files/media/documents/Bilan_reglementaire_PREVAIR_A2022_v20230602.NA_.pdf)).

**Publié.** Pour les franchissements en station, le référentiel évalue l'ozone sur le maximum horaire journalier au seuil d'information de 180 µg/m³, en saison ozone, et les PM10 sur la moyenne journalière à 50 µg/m³ ; les tables de contingence cumulent les occurrences sur les stations de fond. L'évaluation AMU par surface/population exposée est un objet distinct ([Atmo Nouvelle-Aquitaine, 2023, sections 2.1.2 et 2.2.4](https://www.lcsqa.org/system/files/media/documents/Bilan_reglementaire_PREVAIR_A2022_v20230602.NA_.pdf)).

## 2. Erreur de calcul certaine : agrégation des RMSE mensuelles

`verite_dossier.py` et `comparer_mos_officiel_annee.py` font une moyenne arithmétique des RMSE mensuelles pondérée par `n`. Or une RMSE globale se calcule par

\[
\operatorname{RMSE}=\sqrt{\frac{\sum_m n_m\,\operatorname{RMSE}_m^2}{\sum_m n_m}},
\]

et non par `average(RMSE_m, weights=n_m)`. Le biais pondéré, lui, peut être moyenné linéairement.

| polluant et grain | publié : brut / officiel / nous | recalcul correct : brut / officiel / nous | gains corrects officiel / nous |
|---|---:|---:|---:|
| O3 horaire | 17,30 / 14,43 / 13,55 | 17,42 / 14,45 / 13,56 | 17,0 % / 22,1 % |
| O3 max 8 h | 12,08 / 11,85 / 9,49 | 12,45 / 11,93 / 9,53 | 4,1 % / 23,4 % |
| NO2 horaire | 7,75 / 6,45 / 7,54 | 8,04 / 6,62 / 7,60 | 17,7 % / 5,5 % |
| NO2 max horaire | 15,13 / 12,03 / 10,34 | 15,47 / 12,16 / 10,44 | 21,4 % / 32,5 % |
| PM2,5 horaire | 5,17 / 4,68 / 4,11 | 5,60 / 4,98 / 4,42 | 11,0 % / 21,1 % |
| PM2,5 moyenne jour | 3,79 / 3,22 / 2,69 | 4,17 / 3,43 / 2,91 | 17,6 % / 30,1 % |

Pour O3 max 8 h, la saison avril–septembre devient 10,31 / 12,34 / 9,27, soit −19,6 % pour le MOS officiel et +10,1 % pour nous. Hors saison : 14,41 / 11,48 / 9,81, soit +20,4 % et +31,9 %. Le renversement saisonnier subsiste ; les valeurs annuelles changent sensiblement.

## 3. Différences de population et de pondération

Le projet calcule principalement une RMSE sur toutes les lignes réunies. Cela pondère davantage une station disposant de plus d'heures valides et peut inclure des stations trafic ou industrielles. Cette métrique est pertinente comme **perte ML nationale sur couples station–temps**, mais elle ne doit pas être comparée directement à la moyenne des RMSE temporelles par station de fond d'un rapport AASQA.

Sur le seul test O3 2025 disponible, la différence reste faible mais mesurable : RMSE groupée CAMS / MOS officiel / nous = 11,04 / 13,56 / 10,33 ; moyenne non pondérée des RMSE par station = 10,85 / 13,45 / 10,25. Ce petit écart sur 21 stations ne garantit pas qu'il soit petit en France entière ou pour NO2.

**Calcul à ajouter.** Produire deux vues sans en substituer une à l'autre :

1. vue ML : RMSE groupée sur support commun, avec ventilation par typologie ;
2. vue AASQA : stations de fond uniquement, >75 % de disponibilité sur la période, métriques temporelles par station puis moyenne non pondérée des stations, par horizon ; O3 limité à avril–septembre.

## 4. Endpoint « épisode » : résultat valide, nom incorrect

Le `3,6×` est calculé sur les dépassements de **120 µg/m³ en maximum journalier de moyenne glissante 8 h**, avec un budget de FAR de 30 %. C'est un endpoint lié à la valeur cible ozone, mais **ce n'est ni la classe d'indice ATMO, ni le franchissement en station évalué par le référentiel prévision, ni à lui seul un épisode régional**.

La comparaison publiée avec Bertrand et al. n'est pas au même grain : leur expérience 20,5 % contre 32,8 % porte sur le **maximum journalier horaire**, pas le maximum 8 h ([Bertrand et al., 2023, ACP, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)). Le projet constitue donc une extension analogue, pas une réplication exacte de ce chiffre.

**Libellé défendable maintenant :** « à FAR ≤30 %, rappel des jours-station dépassant 120 µg/m³ en MDA8 : 0,656 contre 0,184 ». Éviter « 3,6 fois plus d'épisodes détectés ».

**Calcul AASQA à ajouter :** O3 maximum horaire >180 µg/m³, avril–septembre, stations de fond, par horizon ; PM10 moyenne journalière >50 µg/m³. Rapporter POD, FAR, CSI, table brute TP/FP/FN/TN et l'expertise humaine si elle est disponible. Les PM2,5 à 25 µg/m³ répondent à une autre question et ne remplacent pas les PM10 de la procédure française.

## 5. Support temporel et jour civil

Le code agrège les jours avec `floor("D")` en UTC. Pour un produit quotidien exploité par une AASQA française et pour l'indice ATMO, il faut vérifier et documenter le jour civil `Europe/Paris`, y compris les journées de 23 et 25 heures. Le module local de calcul de l'indice ATMO fait déjà cette conversion, mais les scripts MOS, seuils et épisodes ne la reprennent pas.

Deuxième problème : dans la comparaison annuelle, les séries locale et officielle sont agrégées séparément puis jointes au jour. Un maximum ou une moyenne peut donc être calculé sur des ensembles d'heures différents. De plus, `n=(datetime, size)` compte les lignes, pas le nombre de valeurs finies de chaque produit.

**Calcul à ajouter.** Fusionner d'abord observation, CAMS local, raw officiel, MOS officiel et correction à l'heure ; sélectionner le support fini commun ; convertir en heure locale ; agréger conjointement ; appliquer une règle de complétude fondée sur le nombre d'heures civiles attendu. Publier aussi la disponibilité propre à chaque produit, séparément du score sur support commun.

## 6. Les deux « CAMS bruts » ne sont pas interchangeables

En 2025, `cams_jour` et `officiel_raw` diffèrent sur les 3 353 jours-station communs : MAE 2,36, RMSE 3,28 µg/m³, biais 0,17 et corrélation 0,976. Le code annuel emploie `officiel_raw` comme dénominateur « brut » alors que notre correction a été apprise depuis le CAMS local.

Ce n'est pas une erreur de métrique, mais c'est une asymétrie expérimentale : le gain « nous vs brut officiel » ne mesure pas exclusivement l'effet de notre correction. Il faut établir la cause — cycle, heure d'émission, membre d'ensemble, extraction/interpolation ou disponibilité — avant de parler de comparaison à armes égales.

**Calcul à ajouter.** Une table 2×2 : chaque correction comparée à son propre raw, puis les deux corrections sur le même support avec un raw commun clairement défini. Conserver séparément l'écart `raw local − raw officiel` comme contrôle d'identité.

## 7. Seuils, budget de fausses alertes et incertitude

La courbe à FAR fixé répond à une vraie question opérationnelle et est plus informative qu'un CSI optimisé séparément. Toutefois :

- les scripts utilisent `>= seuil` ; pour un « dépassement », employer `> seuil` ou justifier explicitement la convention. Aucun cas exactement égal à 120 n'apparaît dans le fichier 2025, donc cela ne change pas ce test ;
- le seuil est sélectionné parmi 400 quantiles entre 50 % et 99,99 % : balayer toutes les valeurs distinctes, ou calculer directement la frontière ROC, évite une approximation inutile ;
- choisir un seuil sur 2024 puis tester 2025 est propre temporellement, mais l'intervalle final doit aussi propager l'incertitude de calibration du seuil si l'on revendique la chaîne déployée complète ;
- le bootstrap actuel à deux axes est une sensibilité utile, mais doit être complété par un bootstrap multiway ou événementiel apparié, car un épisode régional crée simultanément des dépassements dans plusieurs stations.

Pour un usage AASQA, ajouter une seconde unité : événements/jours régionaux ou critères AMU de surface et population exposées. Une table cumulée de jours-station peut surpondérer un seul épisode spatialement étendu ; le rapport AASQA distingue précisément les franchissements aux stations de l'évaluation AMU ([Atmo Nouvelle-Aquitaine, 2023](https://www.lcsqa.org/system/files/media/documents/Bilan_reglementaire_PREVAIR_A2022_v20230602.NA_.pdf)).

## 8. Indice ATMO et FAIRMODE

Le calcul local de sous-indice ATMO utilise correctement le maximum horaire pour O3 et NO2, la moyenne journalière pour PM2,5 et le jour `Europe/Paris`. Mais le résultat principal à 120 MDA8 ne l'utilise pas. Il faut donc soit évaluer effectivement le sous-indice stationnel, soit retirer la formule « évalué sur la classe ATMO ».

Une évaluation minimale utile serait : matrice de confusion ordinale, exactitude à ±1 classe, MAE de classe, macro-F1 et rappel par classe, sur O3/NO2/PM2,5 séparément. Le véritable indice communal est le maximum de cinq sous-indices spatialisés ; avec trois polluants et des stations, le résultat doit être nommé **proxy stationnel partiel**, pas indice ATMO officiel.

Le MQI FAIRMODE répond à la qualité d'une application de modélisation, pas au rapport annuel de performance prévision AASQA. Il peut rester comme diagnostic secondaire. La conformité doit être jugée station par station selon le document FAIRMODE retenu, pas seulement sur un agrégat national ; le rapport local le reconnaît déjà pour NO2. Il faut aussi geler explicitement la version, car les chiffres actuels utilisent v3.2 alors que le dossier mentionne une v4.0 de 2026 « à vérifier ».

## 9. Ce qui résiste à l'audit

- La validation par stations entièrement exclues répond correctement à la question de transfert vers une autre station du même réseau.
- Le test temporel 2025 est réellement plus exigeant que la seule validation croisée spatiale, sous réserve de documenter le changement éventuel du modèle CAMS amont.
- Le signe du renversement saisonnier O3 résiste au recalcul correct de la RMSE.
- L'apprentissage direct de la statistique journalière est une expérience pertinente ; son antériorité est correctement attribuée à Bertrand et al. (2023).
- La comparaison à FAR fixé est pertinente si elle est renommée selon son endpoint et accompagnée du vrai calcul AASQA à 180 µg/m³ horaire.

## 10. Ordre de correction recommandé

1. Corriger l'agrégation quadratique des RMSE et régénérer tous les chiffres dérivés.
2. Construire une table de support horaire commun et expliquer l'écart entre les deux raw CAMS.
3. Ajouter la vue AASQA : fond, >75 %, score par station puis moyenne, horizon séparé, O3 avril–septembre.
4. Calculer l'endpoint épisode réglementaire O3 180 max horaire et PM10 50 moyenne jour ; conserver 120 MDA8 sous son vrai nom.
5. Passer toutes les agrégations opérationnelles au jour civil français et tester les transitions DST.
6. Évaluer réellement les classes de sous-indice ATMO et propager l'incertitude de sélection des seuils.

## Limite de cet audit

Les tests unitaires existants n'ont pas pu être exécutés dans le runtime disponible (`pytest` absent). Cette limite ne concerne pas les recalculs arithmétiques ci-dessus, effectués directement depuis les CSV publiés, mais elle empêche d'affirmer que les corrections futures ne créeront pas de régression. Les tests actuels ne semblent de toute façon pas couvrir l'identité quadratique d'une RMSE agrégée, le support horaire commun, le jour local/DST ou la convention AASQA par station : ces quatre tests sont à ajouter.
