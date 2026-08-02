# Réponses aux 30 questions — contribution restante

## 1. Les covariables de paysage ajoutent-elles quelque chose à la dérive CHIMERE ?

**Réponse courte : oui, potentiellement pour le contraste local ; ce n’est pas démontré pour la prévision occitane.** CHIMERE apporte le fond spatio-temporel, mais une maille kilométrique ne résout pas directement distance aux routes, canyon urbain ou relief très local ([uEMEP, 2022, DOI 10.5194/gmd-15-449-2022](https://doi.org/10.5194/gmd-15-449-2022)).  
À l’échelle ouest-européenne, ajouter satellite et CTM à une LUR locale porte le \(R^2\) PM₂,₅ d’environ 0,33–0,38 à environ 0,60 ; pour NO₂, le CTM le porte de 0,47–0,51 à 0,58 ([de Hoogh et al., 2016, DOI 10.1016/j.envres.2016.07.005](https://doi.org/10.1016/j.envres.2016.07.005)).  
Dans une comparaison de seize algorithmes, les variables de trafic restent parmi les prédicteurs majeurs du NO₂ même avec un modèle de dispersion ; les \(R^2\) externes restent toutefois proches, 0,49–0,51 ([Chen et al., 2019, DOI 10.1016/j.envint.2019.104934](https://doi.org/10.1016/j.envint.2019.104934)).  
Ces résultats prouvent une **complémentarité CTM–covariables**, pas le gain marginal de vos covariables par rapport au KED PREV’AIR actuel, ni leur intérêt pour O₃.  
**Test décisif :** comparer CHIMERE/KED, covariables seules et hybride sur stations entièrement cachées, puis cartographier où le gain apparaît ; sans gain hors station, abandonner l’angle « descente d’échelle ».  
**À vérifier :** résolution et covariables exactes de la chaîne Atmo Occitanie ; les documents PREV’AIR publics identifient CHIMERE comme dérive, pas une liste actuelle exhaustive ([LCSQA, note PREV’AIR 2014](https://www.lcsqa.org/system/files/media/documents/drc-14-144377-12853a_modelisation_note_prevair_urgence_vf.pdf)).

## 2. À quelle résolution une AASQA a-t-elle réellement besoin de descendre ?

Il n’existe pas une résolution réglementaire universelle : elle doit être adaptée à l’usage et à la variabilité du polluant ([directive 2024/2881, art. 8 et annexe IV](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
Pour une ZFE ou un axe routier, Atmo AuRA couple CHIMERE à SIRANE sur une grille de 10 m afin d’estimer émissions, concentrations et populations exposées ([Atmo AuRA, étude ZFE Lyon 2022](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf)).  
Pour l’exposition annuelle, des surfaces hybrides européennes à 100 m sont publiées et validées ; cette maille vise l’affectation d’exposition, non la prévision d’un trottoir ([de Hoogh et al., 2018, DOI 10.1016/j.envint.2018.07.036](https://doi.org/10.1016/j.envint.2018.07.036)).  
Pour l’indice ATMO, le produit représente une situation de fond communale ou intercommunale, éloignée des sources spécifiques : une grille de 10 m n’ajoute donc pas automatiquement une décision ([Atmo France, indice ATMO](https://www.atmo-france.org/article/lindice-atmo)).  
Pour contentieux ou conformité, la priorité est la qualité démontrée, la représentativité et l’incertitude, pas le nombre de pixels ([décision d’exécution (UE) 2026/1208](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj/eng)).  
**Action :** annoncer une résolution par produit — 10–100 m pour exposition trafic si les entrées le permettent, kilométrique pour fond/alerte — et refuser toute « haute résolution » non validée.

## 3. Où un modèle statistique léger peut-il battre une chaîne lourde ?

Le créneau le plus crédible est la **reconstitution annuelle à 100 m** ou l’estimation de sites non mesurés à partir d’un CTM, du trafic et de l’occupation du sol ; des LUR hybrides ont atteint 59 % de variance expliquée pour NO₂ en Europe occidentale ([de Hoogh et al., 2018, DOI 10.1016/j.envint.2018.07.036](https://doi.org/10.1016/j.envint.2018.07.036)).  
Une méthode légère de descente CTM vers l’échelle urbaine a précisément été publiée pour réduire le coût d’une nouvelle simulation dynamique ([Maiheu et al., 2023, DOI 10.1016/j.envsoft.2023.105692](https://doi.org/10.1016/j.envsoft.2023.105692)).  
En revanche, la microéchelle de rue exige géométrie, trafic et dispersion ; l’exemple opérationnel français utilise SIRANE à 10 m, pas une simple interpolation paysagère ([Atmo AuRA, étude ZFE Lyon 2022](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf)).  
Pour la prévision d’épisode, la chaîne lourde fournit chimie, transport et météo future ; le modèle léger est plutôt un complément de calibration qu’un substitut ([PREV’AIR, production](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
**Hypothèse prioritaire :** un outil léger peut gagner en délai, reproductibilité et couverture historique, même sans battre SIRANE là où celui-ci est déjà disponible.  
**À vérifier avec Atmo Occitanie :** quel territoire ou millésime n’a aujourd’hui ni carte urbaine validée ni budget pour une nouvelle simulation.

## 4. Que vaut une bonne prédiction sur une station jamais instrumentée ?

C’est un besoin réel lorsque l’AASQA doit évaluer l’exposition entre stations, rattacher un lieu à une zone représentative ou concevoir son réseau ([LCSQA, représentativité des stations](https://www.lcsqa.org/system/files/media/documents/Represent_Stations_Mesures_Repro.pdf)).  
La directive 2024/2881 exige que la conception du réseau s’appuie au moins sur de la modélisation ou des mesures indicatives et que la représentativité spatiale soit documentée ([directive 2024/2881, annexe IV.D](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
La décision d’exécution 2026/1208 formalise désormais l’usage de modèles pour déterminer les aires de représentativité et leur cartographie ([décision (UE) 2026/1208](https://eur-lex.europa.eu/eli/dec_impl/2026/1208/oj/eng)).  
Mais « station cachée » teste une localisation du réseau existant, pas une rue ou une vallée hors domaine ; l’extrapolation géographique reste **à vérifier**.  
La valeur métier apparaît si l’incertitude permet de choisir une campagne, détecter un angle mort ou estimer une population, pas si le résultat reste un score global.  
**Livrable utile :** carte erreur attendue/couverture, liste de trois zones à mesurer et critère explicite disant quelle mesure ferait changer la carte.

## 5. Comment décide-t-on d’implanter une nouvelle station ?

Le choix doit couvrir les niveaux les plus élevés et l’exposition générale, respecter les critères macro/micro d’implantation et être documenté par cartes, coordonnées et environnement du site ([directive 2024/2881, annexe IV.B–D](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
Le réseau doit aussi satisfaire des nombres minimaux de points selon population, polluant et régime de concentration ([directive 2024/2881, annexe III](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32024L2881)).  
En France, campagnes indicatives, inventaires et modélisation complètent les mesures fixes pour évaluer la représentativité et réorganiser le réseau ([LCSQA, représentativité](https://www.lcsqa.org/system/files/media/documents/Represent_Stations_Mesures_Repro.pdf)).  
Un modèle existe donc déjà comme aide ; la nouveauté serait une optimisation transparente de l’information marginale, pas l’idée générale de « proposer un site ».  
**Contribution possible :** classer les cellules par incertitude, population, proximité du seuil et distance aux stations, puis vérifier les premières par campagne mobile.  
**À vérifier :** règle de pondération, contraintes foncières/électricité/sécurité et projets de réseau d’Atmo Occitanie ; aucune source publique ne donne sa grille interne complète.

## 6. Quelles archives de prévisions sont accessibles sur plusieurs années ?

CAMS Europe fournit gratuitement via ADS des analyses/prévisions horaires à 0,1°, mais seulement dans une archive glissante de trois ans ; les prévisions vont à 96 h ([CAMS, jeu européen](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).  
CAMS global conserve des prévisions depuis 2015, à résolution plus grossière ; c’est l’option publique la plus longue pour de vrais *hindcasts* issus de prévisions ([CAMS, prévisions globales](https://ads.atmosphere.copernicus.eu/datasets/cams-global-atmospheric-composition-forecasts?tab=overview)).  
Les réanalyses CAMS Europe remontent plus loin, mais elles assimilent des observations et ne doivent pas être présentées comme les prévisions disponibles le jour J ([CAMS, catalogue et distinction analyse/prévision](https://confluence.ecmwf.int/pages/viewpage.action?pageId=554144435)).  
PREV’AIR+ annonce des données historiques, mais l’accès public à plusieurs années de **champs bruts émis à chaque échéance**, avec version et heure de mise à disposition, est **à vérifier** ([PREV’AIR](https://www.prevair.org/)).  
Il n’y a pas de redevance CAMS annoncée ; le coût réel est stockage, transfert et préparation, dont le volume dépend de l’emprise, des niveaux, polluants et échéances demandés.  
**Action immédiate :** télécharger une semaine Occitanie, mesurer octets/jour et temps de traitement, puis multiplier par 1 095 ; ne pas promettre un coût avant ce test.

## 7. Combien de mois faut-il pour généraliser à une saison cachée ?

**Aucun minimum universel publié n’a été trouvé.** PREV’AIR indique un apprentissage sur les jours ou années antérieurs, sans règle fixe en mois ([PREV’AIR, correction](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees)).  
Trois mois ne contiennent pas un cycle annuel : une validation où l’été est entièrement absent mesure donc une extrapolation saisonnière, pas une généralisation ordinaire.  
**Déduction minimale, non norme :** douze mois donnent au moins un exemple de chaque saison ; ils ne donnent qu’un été et ne suffisent pas à estimer la variabilité interannuelle ou les épisodes rares.  
Les modèles européens peuvent être stables à grande échelle d’une année à l’autre tout en l’étant moins aux petites échelles ([de Hoogh et al., 2018, DOI 10.1016/j.envint.2018.07.036](https://doi.org/10.1016/j.envint.2018.07.036)).  
La profondeur requise se décide par une courbe d’apprentissage par année/saison et des intervalles sur rappel, fausses alertes et calibration, pas par un nombre rond.  
**Décision actuelle :** présenter −19 % comme diagnostic honnête de domaine non couvert, et ne revendiquer aucune robustesse estivale avant une archive incluant au moins un été d’entraînement indépendant.

## 8. Quelles variables météo de prévision sont accessibles gratuitement ?

AROME est ouvert sur la France à 1,3 km ; les paquets 0,025° fournissent des pas horaires jusqu’à 51 h en GRIB2 ([Météo-France, modèles](https://meteofrance.com/actualites-et-dossiers/comprendre-la-meteo/les-modeles-de-prevision-meteo) ; [data.gouv.fr, AROME 0,025°](https://www.data.gouv.fr/datasets/paquets-arome-resolution-0-025deg)).  
Les API Météo-France donnent aussi ARPEGE à 0,1° ou 0,25°, avec sous-domaines, paramètres, niveaux et échéances sélectionnables ; la rétention PNT annoncée est de 14 jours ([data.gouv.fr, API ARPEGE](https://dev.data.gouv.fr/dataservices/api-modele-arpege)).  
ECMWF ouvre un sous-ensemble IFS à 0,25°, jusqu’à 15 jours, mais ne garde en accès direct que les douze derniers cycles, environ deux à trois jours ([ECMWF Open Data](https://www.ecmwf.int/en/forecasts/datasets/open-data)).  
Variables utiles : vent \(u/v\), température, humidité, pression/couche limite, précipitations, rayonnement et nébulosité ; leur présence exacte varie par paquet et doit être vérifiée dans le catalogue de chaque API.  
Pour une évaluation honnête, il faut archiver le *run* réellement disponible à l’heure d’émission ; ERA5 ou l’analyse AROME introduiraient une information future.  
**Action :** commencer par AROME vent/température/couche limite/pluie sur J0–J+1 et conserver `run_time`, `valid_time`, échéance et version dans chaque ligne.

## 9. Comment valider des données spatio-temporelles corrélées ?

Le découpage doit reproduire l’usage : blocs temporels pour une date future, stations laissées dehors pour un site nouveau, et combinaison des deux si les deux généralisations sont revendiquées ([Roberts et al., 2017, DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)).  
Un bloc ou tampon spatial limite la fuite due à l’autocorrélation ; sa taille doit correspondre à la portée empirique, pas être choisie après lecture des scores ([Valavi et al., 2019, DOI 10.1111/2041-210X.13107](https://doi.org/10.1111/2041-210X.13107)).  
Pour la prévision, toutes les variables doivent être rejouées avec leur disponibilité opérationnelle : observation J−1 permise, observation future interdite.  
Le prétraitement, la sélection de variables et l’optimisation doivent être ajustés dans chaque pli d’entraînement, jamais sur l’ensemble.  
Publier au minimum : année/saison cachée, stations cachées, rayon du tampon, nombre d’épisodes, et métriques par pli plutôt qu’une moyenne seule.  
**Protocole conseillé :** test final été intact + CV glissante temporelle pour réglage + leave-location-out pour la contribution spatiale ; ne pas mélanger les conclusions.

## 10. Quelles erreurs disqualifient immédiatement un travail ?

Utiliser une observation postérieure à l’heure d’émission, ou une analyse/réanalyse à la place de la prévision disponible, invalide la revendication opérationnelle ([LCSQA, référentiel prévision 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
Interpoler avec la station test puis annoncer une performance « site inconnu » est une fuite spatiale ([Roberts et al., 2017, DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)).  
Choisir hyperparamètres, seuil ou covariables sur le test, ou partager des heures voisines entre apprentissage et test, produit un score optimiste.  
Confondre analyse, prévision brute et correction ; omettre run, horizon, fuseau, unités, version et statut de validation détruit la traçabilité exigée en exploitation ([LCSQA, référentiel prévision 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
Une RMSE seule, sans biais, seuils, rappel/fausses alertes, saison et stations, ne répond pas à la décision réglementaire ([arrêté du 7 avril 2016, art. 15](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Enfin, cacher le −19 % serait plus disqualifiant que l’échec : le présenter avec sa cause testable et la limite de portée montre une validation réelle.

## 11. Quelle part des dépassements PM₁₀ vient du Sahara ?

**Aucun pourcentage public consolidé sur dix ans pour toute l’Occitanie n’a été trouvé.** Il faut donc répondre **à vérifier**, et non agréger à la main des communiqués incomplets.  
Atmo Occitanie publie des épisodes explicitement attribués aux poussières nord-africaines, par exemple le 18 juin 2022 sur les quatre départements pyrénéens ([Atmo Occitanie, épisode 18 juin 2022](https://www.atmo-occitanie.org/episodes-pollution/2022-06-18%7C66)).  
Elle documente encore un épisode PM₁₀ saharien dans les Pyrénées-Orientales le 13 juillet 2026, annoncé comme susceptible de s’étendre plusieurs jours ([Atmo Occitanie, 13 juillet 2026](https://www.atmo-occitanie.org/alerte-pollution/2026-07-13%7C66)).  
Mais un « jour-département », un « jour-station » et un événement régional ne donnent pas le même dénominateur ; aucun taux n’est comparable sans convention.  
La déduction réglementaire exige chaque année zones, concentrations, sources et preuves, ce qui rend les dossiers État/LCSQA plus adaptés que les seules pages d’actualité ([directive 2008/50/CE, art. 20](https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32008L0050)).  
**Action :** demander au LCSQA/DREAL la série annuelle des contributions naturelles rapportées, puis publier deux taux : événements uniques et jours-départements.

## 12. Le chauffage au bois est-il quantifié en Occitanie ?

Oui. En 2018, le bois représentait 14 % de l’énergie de chauffage régionale mais 98 % des PM₂,₅ émises par le chauffage résidentiel-tertiaire ([Atmo Occitanie, bilan décennal](https://www.atmo-occitanie.org/sites/default/files/publications/2022-01/Pollution%20atmosph%C3%A9rique%20et%20GES%20-%20bilan%20de%20dix%20ann%C3%A9es%20d%27observation.pdf)).  
Ce 98 % est une part **dans le secteur chauffage**, pas dans toutes les émissions régionales ; le confondre avec une contribution ambiante serait faux.  
Dans la vallée du Lot, l’attribution chimique hivernale 2013–2014 estimait 61 % de la masse particulaire au chauffage au bois, contre 32 % à Toulouse et 39 % sur le site rural étudié ([Atmo Occitanie, caractérisation 2013–2014](https://www.atmo-occitanie.org/sites/default/files/imports/pdf/Caracterisation_chimique_des_particules_en_trois_sites_de_Midi_Pyrenees_.pdf)).  
Les zones documentées incluent Lourdes/Tarbes, vallée du Lot, Lozère et Pyrénées catalanes ; leurs campagnes et années diffèrent, donc les pourcentages ne s’additionnent pas.  
Des fonds Air Bois sont évalués à Tarbes–Lourdes et les PPA de Nîmes/Montpellier/Toulouse comportent des actions chauffage ([Atmo Occitanie, fonds Air Bois](https://www.atmo-occitanie.org/communaute-dagglomeration-tarbes-lourdes-pyrenees-evaluation-de-limpact-de-la-prime-fonds-air-bois) ; [DREAL, PPA](https://www.occitanie.developpement-durable.gouv.fr/plan-de-protection-de-l-atmosphere-ppa-a27236.html)).  
**Besoin modèle :** relier émissions, météo de stagnation et traceurs mesurés ; une simple covariable « bâti » ne sépare pas bois, brûlage végétal et particules secondaires.

## 13. Quelles vallées sont problématiques et instrumentées ?

Les cas publics les mieux documentés sont Lourdes/Tarbes et Argelès-Gazost, la vallée du Lot, les Vallées des Gaves et Bolquère dans les Pyrénées catalanes ([Atmo Occitanie, campagne Hautes-Pyrénées](https://www.atmo-occitanie.org/actualites/quelles-sont-les-sources-de-pollution-aux-particules-dans-lair-dans-les-hautes-pyrenees) ; [vallée du Lot](https://www.atmo-occitanie.org/sites/default/files/imports/pdf/Caracterisation_chimique_des_particules_en_trois_sites_de_Midi_Pyrenees_.pdf)).  
À Bolquère et Lourdes, les PM₂,₅ présentent en période froide un second maximum entre 18 h et 3 h, attribué notamment au chauffage au bois ([Atmo Occitanie, Bolquère 2023–2024](https://atmo-occitanie.org/sites/default/files/publications/2025-01/ETU-2024-224_Evaluation%20de%20la%20qualit%C3%A9%20de%20l%27air%20-%20PNR%20Pyr%C3%A9n%C3%A9es%20Catalanes%20-%20Commune%20de%20Bolqu%C3%A8re%20-%202023%20%C3%A0%202024.pdf)).  
La campagne 2022–2023 a renforcé les mesures à Tarbes, Lourdes et Argelès-Gazost pour distinguer chauffage, feux pastoraux et poussières désertiques ([Atmo Occitanie, sources Hautes-Pyrénées](https://www.atmo-occitanie.org/actualites/dou-proviennent-les-particules-presentes-dans-lair-des-hautes-pyrenees)).  
Ces campagnes ne signifient pas que chaque vallée possède une station réglementaire pérenne ; le statut fixe/mobile et les périodes doivent être lus site par site.  
Pour le Massif central occitan, la Lozère montre une forte empreinte résidentielle bois, mais une liste publique exhaustive des vallées à inversion n’a pas été trouvée ([Atmo Occitanie, bilan Lozère 2018](https://atmo-occitanie.org/sites/default/files/publications/2019-06/ATMO%20OCCITANIE%20RA%202018%20LOZERE.pdf)).  
**À vérifier :** inventaire actuel des sites, hauteurs de couche limite et profils verticaux ; une carte topographique seule ne prouve pas une inversion polluée.

## 14. Comment la brise de mer affecte-t-elle l’ozone ?

Atmo Occitanie décrit l’alternance brise de terre/brise de mer comme un mécanisme transportant ozone et précurseurs entre littoral, mer et intérieur ([Atmo Occitanie, bilan ozone 2020](https://atmo-occitanie.org/sites/default/files/publications/2021-06/ETU-2021-078%20Pollution%20%C3%A0%20l%27ozone%202020.pdf)).  
Elle peut décaler spatialement et temporellement le maximum : le bon prédicteur n’est donc pas seulement la température locale, mais aussi vent directionnel, historique de masse d’air et émissions.  
Les CTM méditerranéens reproduisent la chimie/transport à grande échelle, mais une comparaison de cinq modèles montre pour l’O₃ des corrélations annuelles de 0,38 à 0,69 selon le modèle ([Im et al., 2023, DOI 10.5194/acp-23-1825-2023](https://doi.org/10.5194/acp-23-1825-2023)).  
Cette étude méditerranéenne ne mesure pas spécifiquement l’erreur de brise sur le littoral occitan : affirmer que CHIMERE la traite mal serait **à vérifier**.  
**Diagnostic utile :** stratifier l’erreur par régime de vent terre/mer, heure, distance au littoral et station, puis examiner trajectoires et déphasage du pic.  
Une covariable fixe de paysage ne corrige pas seule un front de brise mal phasé ; il faut au minimum la météo de prévision et des variables temporelles cohérentes.

## 15. Quels épisodes marquants et lesquels furent mal anticipés ?

Les archives publiques montrent des épisodes sahariens multi-départements en juin 2022, un épisode lié à l’incendie de l’Aude et à l’ozone en août 2025, puis plusieurs épisodes O₃/PM₁₀ en juillet 2026 ([Atmo Occitanie, 2022](https://www.atmo-occitanie.org/episodes-pollution/2022-06-18%7C66) ; [2025](https://www.atmo-occitanie.org/episodes-pollution/2025-08-08%7C11) ; [2026](https://www.atmo-occitanie.org/episodes-pollution/2026-07-09%7C65)).  
Ils illustrent trois régimes distincts : poussières désertiques, fumées d’incendie et ozone photochimique ; les regrouper dans une seule erreur moyenne masquerait le mécanisme.  
Le bilan réglementaire doit compter dépassements observés, prévus et prévus non confirmés, ce qui permettrait d’identifier épisodes manqués et fausses alertes ([arrêté du 7 avril 2016, art. 15](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
**Aucune série publique occitane complète reliant chaque épisode au bulletin émis la veille et au modèle fautif n’a été trouvée : à vérifier auprès d’Atmo Occitanie.**  
Il serait donc non fondé de nommer publiquement un épisode « mal anticipé » à partir du seul constat final.  
**Action :** reconstituer dix cas avec bulletin J−1, observations finales, type de masse d’air et erreur par modèle ; ce petit atlas vaut davantage qu’un classement non sourcé.

## 16. Comment conduit-on techniquement une évaluation de ZFE ?

La collectivité commande généralement l’évaluation à l’AASQA ; elle fournit scénario réglementaire, parc, trafic et calendrier, tandis que l’AASQA transforme émissions puis concentrations et exposition ([Atmo AuRA, étude ZFE Lyon 2022](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf)).  
La chaîne publiée à Lyon combine calcul des émissions, CHIMERE régional, correction géostatistique et SIRANE à 10 m, puis croisement avec population et établissements sensibles ([Atmo AuRA, étude ZFE Lyon 2022](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf)).  
Le contrefactuel doit comparer un scénario avec ZFE à une référence au même horizon, avec hypothèses identiques hors mesure ; comparer simplement avant/après confond météo, parc et autres politiques.  
À Toulouse, Atmo suit aussi parc, aides, limitation à 30 km/h et NO₂ multi-sites, ce qui montre que la ZFE n’est pas évaluée isolément ([Atmo Occitanie, bilan Toulouse 2025](https://www.atmo-occitanie.org/sites/default/files/publications/2026-06/ETU_2026_124_%C3%89valuation%20de%20la%20qualit%C3%A9%20de%20l%E2%80%99air%20en%202025%20sur%20le%20territoire%20de%20Toulouse%20M%C3%A9tropole.pdf)).  
Atmo Occitanie publie désormais des intervalles de confiance d’exposition de 10 à 20 % selon le polluant ; leur méthode détaillée pour chaque ZFE reste **à vérifier** ([Atmo Occitanie, Panorama 2024](https://www.atmo-occitanie.org/actualites/panorama-des-territoires-les-donnees-2024-de-la-qualite-de-lair-sur-mon-territoire-sont)).  
**Question à poser :** l’objectif est-il une différence de concentrations, une conformité 2030, des habitants sortis du dépassement ou l’attribution causale observée ? Ce ne sont pas le même calcul.

## 17. Quels indicateurs figurent dans un PPA ?

Un PPA part d’un diagnostic émissions–concentrations–exposition, fixe des actions par secteur, des pilotes, une échéance et des indicateurs de suivi ([Code de l’environnement, art. L.222-4 à L.222-7](https://www.legifrance.gouv.fr/codes/section_lc/LEGITEXT000006074220/LEGISCTA000006176484/)).  
Les indicateurs de moyens comptent par exemple appareils bois remplacés, kilomètres aménagés ou flottes renouvelées ; ils ne prouvent pas seuls un gain de concentration.  
Les indicateurs de résultat suivent émissions par polluant, concentrations aux stations/cartes, surfaces ou populations exposées et respect des valeurs réglementaires ([DREAL Occitanie, portail PPA](https://www.occitanie.developpement-durable.gouv.fr/plan-de-protection-de-l-atmosphere-ppa-a27236.html)).  
Le PPA Nîmes 2025–2030 répartit 23 actions entre transport, activités économiques, transversal et chauffage au bois, chacune détaillée dans son cahier d’actions ([DREAL, PPA Nîmes](https://www.occitanie.developpement-durable.gouv.fr/le-plan-de-protection-de-l-atmosphere-a27140.html)).  
L’atteinte se mesure contre un état initial et une trajectoire, mais l’effet propre d’une action exige un contrefactuel ; le bilan administratif d’avancement n’est pas automatiquement une attribution causale.  
**Action :** pour chaque action, afficher entrée → activité → émissions → concentration → exposition, et marquer « à vérifier » dès qu’un maillon n’est pas mesuré.

## 18. Sur quelles bases le préfet déclenche-t-il une procédure ?

L’AASQA qualifie le dépassement constaté ou prévu selon seuil, surface ou population exposée et persistance définis par l’arrêté national ([arrêté du 7 avril 2016, art. 1–2](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Elle informe le préfet et l’ARS au moins quotidiennement et transmet polluant, zone, durée, évolution et recommandations ([arrêté du 7 avril 2016, art. 7](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Le préfet déclenche l’information-recommandation ou l’alerte et choisit les mesures prévues par l’arrêté-cadre zonal/départemental ; les mesures ordinaires prennent effet le lendemain ([arrêté, art. 12–14](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Sa marge porte sur les mesures graduées, leur périmètre et leur adaptation aux circonstances, pas sur la réécriture des seuils nationaux.  
En cas d’urgence ou de situation particulière, l’arrêté prévoit une réaction adaptée, mais l’articulation exacte dépend de l’arrêté préfectoral local applicable.  
**À vérifier pour l’entretien :** qui, chez Atmo Occitanie, signe l’expertise, à quelle heure tombe le dernier arbitrage et quelles mesures locales sont automatiques ou discrétionnaires.

## 19. Que se passe-t-il quand l’AASQA se trompe ?

Une fausse alerte apparaît dans le bilan annuel comme dépassement prévu non confirmé ; un épisode manqué ressort de l’écart entre dépassements observés et prévus ([arrêté du 7 avril 2016, art. 15](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
Concrètement, la première conséquence est opérationnelle : information tardive ou mesures préfectorales inutiles, puis analyse de l’écart, traçabilité et révision éventuelle de la chaîne ([LCSQA, référentiel prévision 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
Le référentiel exige procédures, contrôles, archivage et retour d’expérience ; l’erreur isolée n’est donc pas traitée comme la preuve automatique d’une faute individuelle.  
**Aucune sanction nationale automatique par faux négatif ou fausse alerte n’a été trouvée dans l’arrêté : à vérifier** dans conventions, audits et arrêtés locaux.  
La conséquence institutionnelle la plus plausible est une perte de confiance si les erreurs se répètent sans explication, non le simple fait qu’une prévision probabiliste échoue.  
**Outil utile :** fiche d’incident avec run disponible, décision prise, observation finale, cause probable, impact et action corrective — sans réentraîner opportunément sur le cas avant audit.

## 20. Comment l’incertitude est-elle communiquée ?

Au public, Atmo Occitanie diffuse surtout une classe, une carte, une tendance et un commentaire expert ; l’indice ATMO est une représentation simplifiée du fond communal ([Atmo France, indice ATMO](https://www.atmo-france.org/article/lindice-atmo)).  
Les avis d’épisode emploient des formulations d’évolution et de probabilité, puis indiquent départements, polluant et niveau de procédure ([Atmo Occitanie, épisode du 9 juillet 2026](https://www.atmo-occitanie.org/episodes-pollution/2026-07-09%7C65)).  
Aux autorités, la chaîne conserve davantage d’éléments : comparaison modèles–mesures, expertise, justification des corrections et traçabilité ([LCSQA, référentiel prévision 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
Pour l’exposition annuelle, Atmo Occitanie publie depuis 2026 un intervalle de confiance de 10 à 20 % selon le polluant ([Atmo Occitanie, Panorama 2024](https://www.atmo-occitanie.org/actualites/panorama-des-territoires-les-donnees-2024-de-la-qualite-de-lair-sur-mon-territoire-sont)).  
**À vérifier :** existence d’une probabilité calibrée de dépassement communiquée en interne ; aucune page publique trouvée ne l’affiche systématiquement.  
Le bon diagnostic candidat serait donc double : probabilité et scénarios pour l’expert, formulation courte orientée action pour le public, avec cohérence vérifiée entre les deux.

## 21. La prédiction conforme est-elle employée ?

**Aucun usage opérationnel public de prédiction conforme par PREV’AIR ou Atmo Occitanie n’a été trouvé : à vérifier en interne.**  
CAMS Europe fournit en revanche onze systèmes et utilise leur dispersion comme estimation de l’incertitude de prévision ([CAMS, prévisions européennes](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).  
PREV’AIR confronte CHIMERE et MOCAGE, mais les pages publiques présentent surtout champs et scores déterministes, pas des intervalles calibrés ([PREV’AIR, évaluations](https://www.prevair.org/le-systeme-prevair/la-production/evaluations)).  
Les quantiles conformalisés donnent une couverture marginale sous hypothèses d’échangeabilité ; une dépendance temporelle et un changement de saison exigent une calibration adaptée ([Romano et al., 2019, DOI 10.48550/arXiv.1905.03222](https://doi.org/10.48550/arXiv.1905.03222)).  
Pour l’alerte, la sortie utile est \(P(Y>s)\) calibrée, contrôlée par diagramme de fiabilité et score de Brier ; les ensembles ozone ont déjà été calibrés statistiquement ([Garaud et al., 2011, DOI 10.1029/2011JD015780](https://doi.org/10.1029/2011JD015780)).  
**Conseil :** ne pas vendre « conformal » ; livrer une courbe de fiabilité et une couverture par saison, puis comparer à la dispersion CAMS et à des quantiles empiriques simples.

## 22. Quelle météo-normalisation employer pour isoler une ZFE ?

La pratique publiée ajuste la concentration sur météo, saison et calendrier, souvent par forêt aléatoire, puis rééchantillonne la météo afin d’estimer une série normalisée ([Grange & Carslaw, 2019, DOI 10.1016/j.scitotenv.2018.10.344](https://doi.org/10.1016/j.scitotenv.2018.10.344)).  
Pour une ZFE, utiliser un modèle pré-intervention, prédire le contrefactuel post-intervention sous météo observée et comparer à l’observation ; ajouter sites témoins ou séries de contrôle renforce l’attribution.  
La normalisation météo seule ne sépare pas renouvellement naturel du parc, prix de l’énergie, travaux, télétravail ou autres politiques concomitantes.  
Une forêt entraînée sur toute la période peut absorber une partie de l’effet recherché ; variables, fenêtre et date d’intervention doivent être fixées avant lecture du résultat.  
Les blocs temporels sont nécessaires, et toute extrapolation vers des conditions météo absentes de l’apprentissage doit être signalée ([Roberts et al., 2017, DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)).  
**Livrable crédible :** effet avec intervalle sous plusieurs spécifications, placebo sur dates antérieures et résultat « non identifiable » si les scénarios ne se séparent pas.

## 23. Comment traiter les stations trafic qu’un CTM ne résout pas ?

Une station trafic mesure une micro-situation que la moyenne de maille CTM ne représente pas ; l’indice ATMO, lui, vise explicitement le fond hors sources spécifiques ([Atmo France, indice ATMO](https://www.atmo-france.org/article/lindice-atmo)).  
Pour évaluer le CTM régional, séparer fond et trafic évite de qualifier de biais un écart d’échelle ; PREV’AIR évalue publiquement ses produits sur stations de fond ([PREV’AIR, évaluations](https://www.prevair.org/le-systeme-prevair/la-production/evaluations)).  
Pour prévoir la rue, utiliser un modèle dédié alimenté par trafic, géométrie et météo ; Atmo AuRA emploie CHIMERE corrigé puis SIRANE à 10 m ([Atmo AuRA, étude ZFE Lyon 2022](https://www.atmo-auvergnerhonealpes.fr/sites/aura/files/medias/documents/2023-10/Etude%20r%C3%A9glementaire%20ZFE%20-%20Extension%20VP%20-%20M%C3%A9tropole%20de%20Lyon%20-%202022.pdf)).  
Une correction statistique par station peut prévoir ce capteur, mais elle n’apprend pas automatiquement le transfert vers une autre rue.  
L’exclusion n’est donc légitime que pour l’évaluation du produit de fond ; elle ne supprime pas le besoin d’exposition trafic.  
**Architecture recommandée :** tête « fond » commune + module trafic séparé, avec scores et domaines d’usage distincts ; mélange des deux seulement si une validation hors rue le justifie.

## 24. Que valent aujourd’hui les capteurs bas coût ?

Ils densifient fortement l’échantillonnage, mais leur qualité métrologique reste généralement inférieure aux stations agréées et varie selon polluant, appareil et environnement ([Anses via Atmo France, avis 2022](https://www.atmo-france.org/actualite/avis-de-lanses-sur-les-microcapteurs)).  
Les essais AIRLAB 2023 sur 59 appareils ont confirmé cette variabilité et de meilleures performances particules dans l’environnement plus chargé de Bangkok que dans le site français ([Atmo France, challenge AIRLAB 2023](https://www.atmo-france.org/actualite/laureats-2023-du-challenge-airlab-microcapteurs)).  
CEN/TS 17660-1:2021 cadre les gaz et CEN/TS 17660-2:2024 les particules, avec essais laboratoire/terrain et classes de performance ([AFNOR, CEN/TS 17660-1](https://www.boutique.afnor.org/en-gb/standard/xp-cen-ts-176601/air-quality-performance-evaluation-of-air-quality-sensor-systems-part-1-gas/fa187310/319508) ; [CEN/TS 17660-2](https://www.nen.nl/en/cen-ts-17660-2-2024-en-332358)).  
Ils peuvent cartographier ou repérer des gradients après colocalisation, correction, suivi de dérive et contrôle qualité ; ils ne remplacent pas automatiquement une mesure de référence.  
Le LCSQA a développé SESAM pour fusionner capteurs fixes/mobiles et modèle par KED, en tenant compte progressivement de leur incertitude ([LCSQA, SESAM 2021](https://www.lcsqa.org/system/files/media/documents/LCSQA_livrable_2021_note_m%C3%A9thodo_cartographie_capteurs.pdf)).  
**Usage candidat :** campagne ciblée de validation des zones d’erreur du modèle, jamais « vérité terrain » non calibrée.

## 25. Quelles données d’émissions sont ouvertes ?

Atmo Data diffuse gratuitement sous licence ODbL les émissions des AASQA aux échelles région et EPCI, par API et WFS, avec obligation d’attribution ([Atmo France, Atmo Data](https://www.atmo-france.org/article/atmo-data-un-acces-unique-aux-donnees-produites-par-les-aasqa)).  
Atmo Occitanie ouvre inventaires, cartes et expositions ; les millésimes disponibles sont mis à jour annuellement et les formats incluent services ArcGIS/OGC ([Atmo Occitanie, Open Data](https://www.atmo-occitanie.org/actualites/telechargez-les-donnees-de-lair-sur-l-open-data)).  
Le Citepa publie séries nationales sectorielles, émissions communales et grilles EMEP ; la méthode OMINEA décrit activités et facteurs d’émission ([Citepa, données Air et Climat](https://www.citepa.org/donnees-air-climat/) ; [grilles EMEP](https://www.citepa.org/donnees-air-climat/polluants-atmospheriques/emep-gridded-emissions-lps/)).  
Ces agrégats ne suffisent pas à une rue : horaires de trafic, composition du parc, hauteur de cheminée ou géométrie peuvent relever de partenaires et conventions.  
On peut exploiter les données ouvertes sans accord individuel sous leur licence, mais il faut respecter attribution, partage à l’identique éventuel et conditions du jeu concerné.  
**Action :** construire d’abord un dictionnaire polluant–secteur–année–géographie–licence ; marquer « indisponible » plutôt que désagréger artificiellement un EPCI en pixels.

## 26. Comment présenter honnêtement une méthode redécouverte ?

Dire : « J’ai reproduit indépendamment le schéma correction aux stations + spatialisation, puis j’ai découvert que PREV’AIR l’industrialise déjà » ; la similarité est documentée par PREV’AIR et le LCSQA ([PREV’AIR, correction](https://www.prevair.org/le-systeme-prevair/la-production/previsions-corrigees) ; [LCSQA, note 2014](https://www.lcsqa.org/system/files/media/documents/drc-14-144377-12853a_modelisation_note_prevair_urgence_vf.pdf)).  
La valeur n’est plus l’invention de la famille de méthode, mais la capacité à la reconstruire, identifier son antériorité et redéfinir honnêtement la contribution.  
Présenter ensuite trois apports séparés : test marginal des covariables locales, évaluation épisodes/hors station, et diagnostics d’erreur utilisables.  
Montrer le résultat négatif été −19 % comme preuve que la validation a détecté un domaine non appris, non comme une performance à excuser.  
Éviter « j’ai amélioré PREV’AIR » tant que la comparaison directe, les mêmes données et les mêmes horizons n’existent pas.  
**Formule juste :** « prototype de benchmark et de diagnostic complémentaire, dont une hypothèse spatiale reste à falsifier ».

## 27. Qu’est-ce qui distingue la compréhension métier du bon code ?

Les offres Atmo Occitanie demandent maintien de chaînes, automatisation, scénarios, analyse, rapports et capacité à rendre compte, pas seulement développement d’un modèle ([Atmo Occitanie, offre ingénieur modélisation](https://www.atmo-occitanie.org/sites/default/files/2021-01/Atmo%20Occitanie_Offre%20d%27emploi%20Ing%C3%A9nieur%28e%29%20d%27Etude%20Mod%C3%A9lisation.pdf)).  
Le candidat métier sait quelle donnée était disponible à l’heure H, distingue fond/route et analyse/prévision, et rattache chaque score à une décision.  
Il prévoit logs, reprise après incident, versions, contrôle des entrées, astreinte et explication d’une correction manuelle ([LCSQA, référentiel prévision 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
Il accepte qu’un modèle légèrement moins performant mais stable, auditable et livrable puisse avoir davantage de valeur opérationnelle.  
**Inférence de recrutement, pas grille officielle :** le bon code devient probant quand le candidat montre un incident, son diagnostic, sa décision et sa communication.  
La meilleure démonstration serait un rapport automatique d’une page sur un épisode, accompagné du notebook reproductible et de la provenance des données.

## 28. Quelles questions poser en entretien ?

« Quel produit dois-je améliorer : indice communal, épisode J+1, carte annuelle ou exposition trafic ? » — chacun a une résolution et une validation différentes ([Atmo France, indice ATMO](https://www.atmo-france.org/article/lindice-atmo) ; [arrêté du 7 avril 2016](https://www.legifrance.gouv.fr/loda/id/JORFTEXT000032376671/2021-05-31)).  
« Quelle chaîne et quelles covariables sont déjà opérationnelles, notamment après le KED PREV’AIR, et quels diagnostics manquent aux prévisionnistes ? »  
« Quelles données sont réellement archivées par run et échéance, et quelles restrictions de licence ou de partenaire s’appliquent ? »  
« Comment sont organisés l’astreinte, le dernier arbitrage quotidien, la correction experte et le retour sur fausse alerte ? » — ce sont des éléments du référentiel national ([LCSQA, référentiel 2022](https://www.lcsqa.org/system/files/media/documents/LCSQA_RTN-qualit%C3%A9_tra%C3%A7abilit%C3%A9_prevision_vapplicable01012022.pdf)).  
« Quel échec à trois mois vous ferait arrêter mon approche, et quel livrable serait utile même si elle ne bat pas la référence ? »  
« Puis-je voir un exemple anonymisé de bulletin, d’incident de chaîne et de validation annuelle ? » — la réponse révélera mieux le poste que le nom d’un algorithme.

## 29. Jusqu’où pousser l’autocritique ?

La rigueur consiste à nommer la limite, montrer la preuve, borner la conclusion et proposer le test qui tranche : ici, archive courte, été caché et −19 %.  
Le manque de confiance commence quand le candidat transforme une limite locale en jugement global — « mon travail ne vaut rien » — ou énumère des faiblesses sans décision.  
Les qualités publiées par Atmo Occitanie incluent autonomie, rigueur, analyse/synthèse, initiative et capacité à rendre compte ([Atmo Occitanie, offre modélisation](https://www.atmo-occitanie.org/sites/default/files/2021-01/Atmo%20Occitanie_Offre%20d%27emploi%20Ing%C3%A9nieur%28e%29%20d%27Etude%20Mod%C3%A9lisation.pdf)).  
Une formulation solide suit quatre temps : résultat, limite, conséquence, prochaine décision — sans excuse ni superlatif.  
**Exemple :** « Le modèle gagne en interpolation, mais perd 19 % sur un été non vu ; je ne revendique donc pas la généralisation saisonnière et je priorise l’archive multi-saison. »  
Le candidat doit aussi défendre ce qui reste vrai : pipeline reproductible, test sans fuite et diagnostics peuvent être utiles même si l’hypothèse paysagère échoue.

## 30. Que faire pendant les trois semaines restantes ?

**Une seule priorité : construire un benchmark falsifiable sur le meilleur jeu multi-saison accessible, avec un rapport d’épisode exploitable.**  
Semaine 1 : sécuriser CAMS Europe sur sa fenêtre glissante de trois ans, observations horodatées et météo de prévision ; conserver run, horizon, version et disponibilité ([CAMS, archive européenne](https://ads.atmosphere.copernicus.eu/datasets/cams-europe-air-quality-forecasts?tab=overview)).  
Semaine 2 : comparer brut, correction sans paysage et correction avec paysage sous blocs temporels et stations cachées ; ne régler aucun choix sur le test ([Roberts et al., 2017, DOI 10.1111/ecog.02881](https://doi.org/10.1111/ecog.02881)).  
Semaine 3 : produire rappel/fausses alertes, matrice de classe ATMO, erreurs par régime météo et trois études de cas, avec un bouton ou script de reproduction.  
Le critère de décision doit être écrit avant calcul : conserver les covariables seulement si elles gagnent hors station sans dégrader été/épisodes ; sinon recentrer le discours sur l’évaluation et le diagnostic.  
Pourquoi ce choix : il répond simultanément à la faiblesse démontrée, tranche la question 1 et livre quelque chose d’utile même en cas de résultat négatif — alors qu’une nouvelle architecture ne réparerait pas l’absence de saisons.
