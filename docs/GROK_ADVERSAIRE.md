# 1. L’objection fatale

> **« Quel gain reste en saison ozone quand, pour chaque prédiction, le modèle n’a vu que des dates antérieures, aucune station du pli test, et que variables comme hyperparamètres sont choisis sans jamais consulter la période évaluée ? »**

**Verdict : réparable, mais rédhibitoire pour la présentation A tant que la réponse n’est pas en première page.** Les plis par stations exclues testent un transfert spatial pendant des situations calendaires que l’apprentissage connaît déjà ; ils ne démontrent pas la capacité à corriger le prochain été. Le test « 2025 » annoncé ne remplace pas un protocole prospectif si des décisions de modèle ont été prises après consultation de ses résultats.

Le dossier remis ne donne pas cette réponse. Le dépôt en contient pourtant une, défavorable au récit principal : le rolling-origin strict donne **+6,3 % en moyenne**, mais seulement **+1,13 % pendant avril–septembre**, avec **4 mois négatifs sur 7** ([`reports/RAPPORT_AGENT.md`](../reports/RAPPORT_AGENT.md)). Le +21,7 % O₃ n’est donc pas actuellement une estimation crédible du gain obtenu « l’été prochain ».

Ce n’est pas fatal à la candidature : c’est fatal à la promesse de produit. En entretien, la bonne réponse est de montrer cette chute spontanément et de dire que le résultat solide est aujourd’hui un diagnostic de généralisation spatiale et un banc d’évaluation, pas une correction prête à brancher.

# 2. Explication innocente du −19,6 %

**Trouvée : le produit est optimisé pour une autre fonction objectif.** La documentation opérationnelle indique que le MOS est reconstruit quotidiennement sur les **trois derniers jours**, apprend sur observations et prédicteurs **horaires**, puis fournit 0–96 h de concentrations horaires. Il privilégie ainsi adaptation rapide aux mises à jour CAMS, couverture de plusieurs polluants et usages horaires ; rien ne promet l’optimalité de la MDA8 ([documentation ECMWF/CAMS, mise à jour 2024](https://confluence.ecmwf.int/spaces/CKB/pages/384140005/CAMS%2BRegional%2BEuropean%2BAir%2BQuality%2BForecast%2BOptimised%2Bat%2BObservation%2BSites%2Bdata%2Bdocumentation), [jeu ADS, DOI 10.24381/2cce4067](https://doi.org/10.24381/2cce4067)).

Bertrand et al. avaient déjà mesuré le compromis : pour leur configuration CAMS, agréger une sortie horaire au maximum journalier améliore moins le RMSE qu’entraîner directement sur ce maximum ; ils recommandent la cible journalière lorsque c’est l’usage. Leur maximum est horaire, pas la MDA8, mais le mécanisme attendu est le même ([Bertrand et al., 2023, tableau 3 et conclusion, DOI 10.5194/acp-23-5317-2023](https://doi.org/10.5194/acp-23-5317-2023)). Dire « le produit dégrade la MDA8 sur cet échantillon » peut être exact ; suggérer que Copernicus a raté son propre objectif est faux tant que cet objectif reste horaire et multi-usage.

Les explications de cycle et de population sont en grande partie neutralisées **si** le brut utilisé est bien `raw` dans la même archive ADS et si le score est calculé sur l’intersection ligne à ligne : le jeu fournit précisément brut et MOS dans le même format. Le code local fait cette intersection. Je n’ai trouvé aucune preuve d’un décalage de cycle expliquant le signe.

Il reste toutefois trois artefacts innocents non éliminés :

- `rolling(8)` travaille sur les huit **enregistrements** précédents sans réindexation horaire ; une lacune peut donc faire traverser plus de huit heures à la fenêtre. L’EQC exige au moins six valeurs dans chacune des huit heures ([CAMS EQC 2025, §3.3 et §4.6](https://atmosphere.copernicus.eu/sites/default/files/custom-uploads/EQC-regional/CAMS283_2024SC1_D83bis.5.1.1-2025_202507_v1.pdf)).
- le jour est découpé à minuit UTC sans test publié contre la convention réglementaire et les changements d’heure ; le résultat doit être reproduit après calendrier horaire complet et attribution explicite de chaque moyenne à son heure de fin ;
- la population MOS varie selon date et polluant. Une intersection par ligne rend chaque comparaison locale équitable, mais pas nécessairement la différence entre mois ; il faut une sensibilité sur intersection fixe de stations.

Enfin, la formule narrative est fausse : les mois dégradés sont **février à septembre**, soit huit mois de l’archive, mais la saison LCSQA avril–septembre n’en compte que six. Écrire : « dégradation pendant huit mois consécutifs, dont les six mois de la saison ozone ; −19,6 % sur avril–septembre ». Le produit n’existe que depuis le 17 janvier 2024 : « année 2024 complète » serait également faux ([fiche ADS](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts-optimised-at-observation-sites)).

# 3. Cadrage

**C — « J’ai construit un banc de recette qui vérifie qu’une correction améliore la grandeur utilisée pour décider, pas seulement sa cible d’apprentissage. »**  
Il applique ce banc au MOS CAMS et à un prototype personnel, expose les échecs temporels et ne transforme pas une incompatibilité d’objectifs en accusation institutionnelle.  
C’est B rendu utile et reproductible ; A ressemble encore à un concours de RMSE contre un système que l’AASQA n’utilise pas seul.

# 4. Besoin réel d’une AASQA

**Oui pour la compétence ; non démontré pour ce produit précis.** Au 1er août 2026, Atmo Occitanie recrute un **responsable de projets IA** chargé de définir une stratégie pour l’ensemble de ses activités, recueillir les besoins métiers, rédiger les cahiers des charges, conduire expérimentation, tests et mise en œuvre, développer des outils internes et arbitrer selon budget et ressources ([offre Atmo Occitanie, avril 2026](https://www.atmo-occitanie.org/sites/default/files/2026-04/recrutement_responsable_projets_IA%20%281%29.pdf)). Le besoin d’évaluation rigoureuse, d’automatisation et de ML est donc réel et actuel.

Mais l’offre dit aussi pourquoi le dossier est trop étroit : elle demande une capacité **transversale de traduction des besoins**, pas un meilleur score CAMS. Atmo Occitanie travaillait déjà explicitement sur l’adaptation statistique de sa plateforme régionale dans une offre de stage antérieure ; le candidat n’arrive donc pas dans un désert méthodologique ([offre « Modélisation Adapt Stat », 2023](https://www.atmo-occitanie.org/sites/default/files/2022-11/Atmo%20Occitanie_Offre%20de%20stage%20Mod%C3%A9lisation%20Adapt%20Stat%202023.pdf)).

Les recrutements récents d’autres AASQA demandent surtout modèles de dispersion et scénarios, HYSPLIT/ADMS/SIRANE, cartographie QGIS, PostgreSQL, automatisation Python/R, rédaction et astreinte événementielle ; ils ne se réduisent pas au post-traitement d’une prévision européenne ([Atmo Hauts-de-France, offre publiée le 26/11/2025](https://jobs.makesense.org/en/jobs/atmo-hauts-de-france-ingenieure-modelisation-cdi-wnllTN4dveYRVVNppzOn), [Atmo Grand Est, offre publiée le 11/06/2026](https://www.atmo-grandest.eu/node/533601)). Le rapport Atmo France 2025 recense **628 stations** et **30 plateformes de modélisation**, ce qui confirme un métier combinant mesure, données et modèles plutôt qu’un seul algorithme ([rapport d’activité Atmo France 2025, publié en mai 2026](https://www.atmo-france.org/sites/federation/files/medias/documents/2026-05/ATMO_rapport2025_VF.pdf)).

En Occitanie, le futur PPA de Perpignan demande déjà inventaire des émissions, concentrations mesurées et modélisées, scénarios d’action et évaluation de leurs impacts ([DREAL Occitanie, 2 avril 2026](https://www.occitanie.developpement-durable.gouv.fr/lancement-de-l-elaboration-du-ppa-de-perpignan-a27178.html)). À valeur immédiate égale, une chaîne reproductible **inventaire → scénario → carte → exposition → rapport** ou un contrôle qualité automatisé de la production quotidienne répond plus directement à une obligation territoriale qu’une baisse de RMSE aux stations.

Le projet a donc une bonne valeur de **preuve de méthode** : audit, traçabilité, évaluation adversariale, automatisation. Sa valeur comme produit est faible tant qu’il ne produit ni carte communale, ni critère AMU, ni résultat contre la plateforme régionale, ni aide démontrée à l’astreinte. Le besoin le plus crédible n’est pas « remplacer leur correction », mais industrialiser des recettes d’acceptation communes aux modèles, cartes et futurs projets IA.

# 5. Trois actions bon marché

1. **Fermer le procès du −19,6 % par un test d’invariance — 0,5 à 1 jour.** Reconstituer une grille horaire complète, calculer la MDA8 par heure de fin dans le fuseau explicitement retenu, comparer `raw` et `mos` de la même archive, imposer une intersection fixe de stations, puis bootstrapper la différence de RMSE par station×jour. Livrable : une table qui dit quels contrôles changent ou non le signe.

2. **Promouvoir le vrai test prospectif au rang de résultat principal — 0,5 à 1 jour hors recalcul.** Refaire ou figer un rolling-origin imbriqué, stations exclues, avec sélection interne des hyperparamètres ; publier séparément avril–septembre, les mois négatifs et l’IC multiway. Si le +1,13 % actuel subsiste, abandonner le slogan « +23 % sur O₃ » comme promesse opérationnelle et le conserver comme estimand spatial.

3. **Transformer l’étude en recette exécutable d’acceptation — 1 à 2 jours.** Une commande doit produire couverture, provenance des runs, convention LCSQA, station-first, horizon, MDA8/maximum/moyenne, biais, RMSE, POD/CSI, dérive mensuelle et drapeaux d’échec. Une page de cas Occitanie montre ensuite la décision rendue possible. Cela ressemble exactement aux étapes « besoin, cahier des charges, expérimentation, test, mise en œuvre » de l’offre IA actuelle ; une nouvelle variante LightGBM ne le ferait pas.

# 6. Ce sur quoi je n’ai pas d’avis fiable

- Les priorités internes réelles d’Atmo Occitanie, son budget, sa dette technique et l’usage quotidien exact de sa plateforme régionale ne sont pas publics ; les offres d’emploi ne suffisent pas à les classer.
- La cause quantitative complète du −19,6 % est inconnue : la cible horaire est une explication publiée et cohérente, mais elle ne permet pas d’attribuer les 19,6 points sans expérience factorielle sur la chaîne opérationnelle exacte.
- Je n’ai pas trouvé un journal public exhaustif des mises à niveau du MOS et de chacun des membres CAMS pendant 2024 permettant d’exclure toute rupture au milieu de la période.
- Sans les requêtes ADS archivées, leur horodatage et les fichiers d’origine, je ne peux pas certifier que chaque archive locale correspond au même cycle et à la même échéance, même si le code lit bien le couple brut/MOS fourni ensemble.
- Je ne peux pas dire si l’AASQA décrocherait le téléphone sur cette candidature précise : l’offre actuelle vise un responsable capable de fédérer et piloter, dimensions que le dépôt technique seul ne prouve pas.
